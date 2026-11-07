# SPDX-License-Identifier: Apache-2.0
"""Build and check the Regular/Bold variable-font experiment. Apache-2.0."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from copy import deepcopy
from itertools import pairwise
from pathlib import Path

import numpy as np
from fontmake.font_project import FontProject
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple
from fontTools.varLib.instancer import instantiateVariableFont
from ufo2ft import compileTTF

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fidelity
from compat import HARD, compare, summary
from loom import build as Bd
from loom import charset as CS
from loom import outline as O
from loom.compatible import TOPOLOGY

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/warp-vf-spike"
CHANGED = sorted(TOPOLOGY | {"iotadieresistonos", "upsilondieresistonos"})


def mark_overlaps(font):
    """Tell rasterisers which simple glyphs retain stroke overlaps."""
    for name in TOPOLOGY.intersection(font.getGlyphOrder()):
        font["glyf"][name].flags[0] |= flagOverlapSimple


class BoundaryPen(BasePen):
    """Flatten curves by a 0.01-unit control-polygon error bound."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours = []
        self.points = []

    def _moveTo(self, p):
        self.points = [p]

    def _lineTo(self, p):
        self.points.append(p)

    def _curveToOne(self, p1, p2, p3):
        self._flatten(np.array([self._getCurrentPoint(), p1, p2, p3], dtype=float))

    def _qCurveToOne(self, p1, p2):
        a, b, c = (np.array(p, dtype=float) for p in (self._getCurrentPoint(), p1, p2))
        self._flatten(np.array([a, a + (b - a) * (2 / 3), c + (b - c) * (2 / 3), c]))

    def _flatten(self, c):
        chord = c[3] - c[0]
        length = math.hypot(*chord)
        error = (
            max(math.hypot(*(p - c[0])) for p in c[1:3])
            if length == 0
            else max(
                abs(float((p[0] - c[0][0]) * chord[1] - (p[1] - c[0][1]) * chord[0]))
                / length
                for p in c[1:3]
            )
        )
        # Also split a curve whose controls extend past its chord.
        along = [float(O._dot2(p - c[0], chord)) for p in c[1:3]]
        if error <= 0.01 and all(0 <= v <= length * length for v in along):
            self.points.append(tuple(c[3]))
        else:
            left, right = O._split_at(c, 0.5)
            self._flatten(left)
            self._flatten(right)

    def _closePath(self):
        if self.points:
            self.contours.append(np.array(self.points + [self.points[0]], dtype=float))
        self.points = []

    _endPath = _closePath


def boundary(font, name):
    gs = font.getGlyphSet()
    pen = BoundaryPen(gs)
    gs[name].draw(pen)
    return pen.contours


def directed_distance(source, target):
    """Sample both directions at 0.1-unit intervals, including line ends."""
    if not source:
        return 0.0 if not target else math.inf
    if not target:
        return math.inf
    starts = np.concatenate([c[:-1] for c in target])
    ends = np.concatenate([c[1:] for c in target])
    vectors = ends - starts
    squares = O._dot2(vectors, vectors)
    squares[squares == 0] = 1
    maximum = 0.0
    for contour in source:
        for a, b in pairwise(contour):
            n = max(1, math.ceil(math.hypot(*(b - a)) * 10))
            for i in range(n + 1):
                p = a + (b - a) * (i / n)
                t = np.clip(O._dot2(p - starts, vectors) / squares, 0, 1)
                delta = starts + t[:, None] * vectors - p
                distance = math.sqrt(float(np.min(O._dot2(delta, delta))))
                maximum = max(maximum, distance)
    return maximum


def difference(instance, static, names=None):
    if instance.getGlyphOrder() != static.getGlyphOrder():
        raise ValueError("The instance and static glyph orders differ")
    maximum, worst = 0.0, None
    for name in static.getGlyphOrder() if names is None else names:
        a, b = boundary(instance, name), boundary(static, name)
        if len(a) == len(b) and all(np.array_equal(x, y) for x, y in zip(a, b)):
            continue
        d = max(directed_distance(a, b), directed_distance(b, a))
        if d > maximum:
            maximum, worst = d, name
    # A 0.1-unit sampling step can miss at most 0.05 units. Each flattened
    # boundary can differ by at most 0.01 units. Gate the upper bound.
    return {
        "max_units": maximum + 0.07,
        "sampled_max_units": maximum,
        "glyph": worst,
        "sampling_step_units": 0.1,
        "curve_flatness_units": 0.01,
    }


def endpoint_difference(instance, static):
    """Bound the distance between matching master polylines.

    The distance between corresponding points on two line segments is
    at most the larger endpoint displacement. Thus the largest vertex
    displacement bounds both directed boundary distances, without a
    sampling gap. Keep 0.02 units for the two curve-flattening bounds.
    """
    if instance.getGlyphOrder() != static.getGlyphOrder():
        raise ValueError("The instance and static glyph orders differ")
    maximum, worst = 0.0, None
    for name in static.getGlyphOrder():
        a, b = boundary(instance, name), boundary(static, name)
        if len(a) != len(b) or any(x.shape != y.shape for x, y in zip(a, b)):
            raise ValueError(f"Endpoint structure differs: {name}")
        for x, y in zip(a, b):
            for delta in x - y:
                distance = math.hypot(*delta)
                if distance > maximum:
                    maximum, worst = distance, name
    return {
        "max_units": maximum + 0.02,
        "vertex_bound_units": maximum,
        "glyph": worst,
        "curve_flatness_units": 0.01,
        "method": "Corresponding vertices bound the full flattened boundaries",
    }


def fidelity_report(fonts, styles):
    result = {}
    for style, font in zip(styles, fonts):
        # The raster helper expects disjoint outlines. Resolve nonzero
        # fill on a copy read from the compiled font; keep overlaps in
        # the masters and VF. The reference remains the independent sweep.
        raster_font = deepcopy(font)
        removeOverlaps(raster_font, TOPOLOGY.intersection(font.getGlyphOrder()))
        glyphs = fidelity.compare(style, raster_font)
        maximum, name, ppem = max(
            (v, n, s) for n, row in glyphs.items() for s, v in row.items()
        )
        result[style] = {
            "max": maximum,
            "glyph": name,
            "ppem": int(ppem),
            "pass": all(
                v <= fidelity.TOLERANCE[int(s)]
                for row in glyphs.values()
                for s, v in row.items()
            ),
            "glyphs": glyphs,
        }
        print(
            f"fidelity {style}: {maximum * 100:.3f}% ({name}, {ppem} ppem)", flush=True
        )
    return result


def trial(method, out):
    """Compare both methods on the twenty difficult glyphs, using the fixed gate."""
    import ufoLib2

    report = compare(HARD, True, method)
    print(f"{method}: {summary(report)}", flush=True)
    fonts = []
    for style in ("Regular", "Bold"):
        ufo = ufoLib2.Font()
        Bd.set_info(ufo, Bd.STYLES[style])
        ufo.lib["public.glyphOrder"] = [".notdef", *HARD]
        for name in [".notdef", *HARD]:
            d = Bd.drawn(style, name, compatible=True, method=method)
            g = ufo.newGlyph(name)
            g.width = Bd.rnd(d.adv)
            O.draw(d.contours, g.getPen())
        font = compileTTF(ufo, removeOverlaps=False)
        mark_overlaps(font)
        fonts.append(font)
    original = CS.GLYPHS
    try:
        CS.GLYPHS = [CS.BY_NAME[n] for n in HARD]
        report["fidelity"] = fidelity_report(fonts, ("Regular", "Bold"))
    finally:
        CS.GLYPHS = original
    (out / f"trial-{method}.json").write_text(json.dumps(report, indent=1) + "\n")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--method", choices=("sample", "refit"), default="sample")
    ap.add_argument(
        "--trials",
        action="store_true",
        help="Compare both methods on the twenty hard glyphs.",
    )
    args = ap.parse_args(argv)
    os.environ["SOURCE_DATE_EPOCH"] = "1793059200"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.trials:
        for method in ("refit", "sample"):
            trial(method, out)
        return 0
    report = compare(compatible=True, method=args.method)
    print(summary(report), flush=True)
    incompatible = [r["name"] for r in report["rows"] if not r["point_compatible"]]
    ds = DesignSpaceDocument()
    ds.addAxis(
        AxisDescriptor(name="Weight", tag="wght", minimum=400, default=400, maximum=700)
    )
    ufos = [
        Bd.build_font(style, compatible=True, method=args.method)
        for style in ("Regular", "Bold")
    ]
    ascent, descent = Bd.win_metrics(ufos)
    statics = []
    for style, ufo in zip(("Regular", "Bold"), ufos):
        ufo.info.openTypeOS2WinAscent, ufo.info.openTypeOS2WinDescent = ascent, descent
        path = out / f"{style}.ufo"
        ufo.save(path, overwrite=True)
        ds.addSource(
            SourceDescriptor(
                path=str(path),
                name=style,
                familyName=Bd.FAMILY,
                styleName=style,
                location={"Weight": Bd.STYLES[style].weight},
            )
        )
        ds.addInstance(
            InstanceDescriptor(
                name=style,
                familyName=Bd.FAMILY,
                styleName=style,
                postScriptFontName=Bd.ps_name(Bd.STYLES[style]),
                location={"Weight": Bd.STYLES[style].weight},
            )
        )
        static = compileTTF(ufo, removeOverlaps=False)
        mark_overlaps(static)
        static.save(out / f"{style}.ttf")
        statics.append(static)
    report["fidelity"] = fidelity_report(statics, ("Regular", "Bold"))
    designspace = out / "Warp.designspace"
    ds.write(designspace)
    target = out / "MachineMadeWarp-Spike[wght].ttf"
    target.unlink(missing_ok=True)
    report["incompatible"] = incompatible
    report["instances"] = None
    if incompatible:
        # Do not let a compiler drop variation data for incompatible glyphs.
        # Keep both UFOs and the designspace as evidence for the next test.
        report["verdict"] = "not verified"
        report["reason"] = (
            "Contour topology differs; no complete variable font can be built by these methods."
        )
        print("incompatible glyphs: " + ", ".join(incompatible), flush=True)
        print(
            "instance 400: unavailable, instance 700: unavailable (incompatible masters)",
            flush=True,
        )
    else:
        FontProject().run_from_designspace(
            str(designspace),
            output=("variable",),
            output_path=str(target),
            remove_overlaps=False,
            check_compatibility=True,
        )
        vf = TTFont(target)
        mark_overlaps(vf)
        vf.save(target)
        report["instances"] = {}
        report["instance_reference"] = (
            "Compiled compatible static masters, all 890 glyphs"
        )
        report["default_differences"] = {}
        for weight, static in zip((400, 700), statics):
            instance = instantiateVariableFont(vf, {"wght": weight}, inplace=False)
            report["instances"][str(weight)] = endpoint_difference(instance, static)
        d1, d2 = [report["instances"][str(w)]["max_units"] for w in (400, 700)]
        print(
            f"instance 400: max difference {d1:.3f} units, instance 700: max difference {d2:.3f} units",
            flush=True,
        )
        for style, static in zip(("Regular", "Bold"), statics):
            ink = deepcopy(static)
            removeOverlaps(ink, TOPOLOGY)
            with TTFont(
                ROOT / f"fonts/warp/ttf/MachineMadeWarp-{style}.ttf"
            ) as default:
                report["default_differences"][style] = {}
                for name in CHANGED:
                    delta = difference(ink, default, [name])
                    report["default_differences"][style][name] = delta
                    print(
                        f"default {style} {name}: {delta['max_units']:.3f} units",
                        flush=True,
                    )
        passed = (
            d1 <= 1.0
            and d2 <= 1.0
            and all(r["pass"] for r in report["fidelity"].values())
        )
        report["verdict"] = "inconclusive" if passed else "not verified"
        report["reason"] = (
            "Fontspector must also pass."
            if passed
            else "Outline difference or fidelity limit exceeded."
        )
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"{report['verdict']}: {report['reason']}")
    return int(report["verdict"] == "not verified")


if __name__ == "__main__":
    raise SystemExit(main())
