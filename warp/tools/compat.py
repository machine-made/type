# SPDX-License-Identifier: Apache-2.0
"""Compare the Regular and Bold outline structure. Apache-2.0."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build as Bd
from loom import charset as CS
from loom import outline as O
from loom.compatible import TOPOLOGY, contour_key, polygon

HARD = [CS.glyph_name(c) for c in "gaesß&?@ﬁﬄΞΣ∫∑√ıȷQRk"]
REPORT = Path(__file__).resolve().parents[2] / "proofs/warp/compat.json"
CAUSES = {
    "germandbls": "The lower bowl joins the stem foot and encloses a counter.",
    "f_f": "The two foot serifs join and enclose a second counter below the bar.",
    "fi": "The foot serifs of f and i join the two outer contours.",
    "fl": "The f terminal joins the l stem, joining the two outer contours.",
    "f_f_i": "The two f feet join and enclose a second counter; then the i foot joins the f feet.",
    "f_f_l": "The two f feet join and enclose a second counter; then the f terminal joins the l stem.",
    "gamma": "The loop counter falls below the 40 square unit area filter; this is not its geometric closure.",
    "kappa": "The stem and two arms enclose a counter at their junction.",
    "dieresistonos": "The tonos joins the right dot, joining two outer contours.",
    "dieresistonoscomb": "The tonos joins the right dot, joining two outer contours.",
    "u1D43F": "The foot curl joins the stem turn and encloses a counter.",
    "u1D6FE": "The loop counter falls below the 40 square unit area filter; this is not its geometric closure.",
    "u1D705": "The stem and two arms enclose a counter at their junction.",
}


def topology_measurements():
    """Locate union changes along a stated engine-parameter path.

    Scan every integer weight, then bracket each change to 1/128 weight
    unit. These are generated sweeps, not interpolated VF outlines.
    """
    from loom import engine as E
    from loom.latin_ext import mathit_def

    result = {}
    for name in sorted(TOPOLOGY):
        gl = CS.BY_NAME[name]

        def state(weight, gl=gl):
            t = (weight - 400) / 300
            params = {
                k: E.DEFAULTS[k] + t * (v - E.DEFAULTS[k]) for k, v in Bd.BOLD.items()
            }
            p = E.params(opsz=Bd.TEXT_OPSZ, **params)
            if gl.variant == "mathit":
                key = Bd.mathit_key(gl.key)
                definition = mathit_def(key)
                mods = {"p": {"bk": 0}} if definition.cap and key not in Bd.GI else {}
            else:
                definition = Bd.table_def(gl.key, False)
                mods = Bd.variant_mods(gl, p)
            sw = E.compose(definition, p, mods)
            shapes = []
            for points in O.path_polygons(O.union(sw.polys)):
                area = O.signed_area(points)
                if abs(area) < O.MIN_AREA:
                    continue
                shapes.append(
                    {
                        "winding": 1 if area > 0 else -1,
                        "area": round(area, 3),
                        "bounds": [
                            round(v, 3)
                            for v in (
                                min(float(q[0]) for q in points),
                                min(float(q[1]) for q in points),
                                max(float(q[0]) for q in points),
                                max(float(q[1]) for q in points),
                            )
                        ],
                    }
                )
            return sorted(shapes, key=lambda s: (-s["winding"], s["bounds"]))

        def signature(shapes):
            return [s["winding"] for s in shapes]

        first = previous = state(400)
        events = []
        for weight in range(401, 701):
            current = state(weight)
            if signature(current) != signature(previous):
                lo, hi = float(weight - 1), float(weight)
                left, right = previous, current
                for _ in range(7):
                    mid = (lo + hi) / 2
                    middle = state(mid)
                    if signature(middle) == signature(left):
                        lo, left = mid, middle
                    else:
                        hi, right = mid, middle
                events.append(
                    {"weight_interval": [lo, hi], "before": left, "after": right}
                )
            previous = current
        result[name] = {
            "cause": CAUSES[name],
            "policy": "a: separate overlapping stroke contours",
            "parts": (
                "Split the loop stroke at its bottom node; keep both runs and the diagonal separate"
                if name in ("gamma", "u1D6FE")
                else "Keep each source stroke, dot, terminal and bracket separate"
            ),
            "other_policies": "Policy a passes; policies b and c are not needed",
            "weight_path": "Linear engine parameters from Regular to Bold at opsz 10; integer scan, brackets at 1/128 weight unit",
            "area_filter": O.MIN_AREA,
            "contour_counts": [len(first), len(previous)],
            "endpoints": {"400": first, "700": previous},
            "transitions": events,
        }
    for name in ("iotadieresistonos", "upsilondieresistonos"):
        mark = result["dieresistonoscomb"]
        result[name] = {
            **mark,
            "policy": "a: separate mark strokes in the existing composite",
            "base": CS.BY_NAME[name].comps[0],
            "contour_counts": [n + 1 for n in mark["contour_counts"]],
            "measurement_scope": "Mark only; the base keeps its one outer contour",
        }
    return result


def contours(style, name, compatible=False, method="sample"):
    gl = CS.BY_NAME[name]
    if gl.comps:
        parts, _ = Bd.component_offsets(style, gl)
        result = []
        for base, dx, dy in Bd.flatten(style, parts):
            for contour in contours(style, base, compatible, method):
                result.append(
                    [
                        (s[0], s[1] + (dx, dy), s[2] + (dx, dy))
                        if s[0] == "line"
                        else (s[0], s[1] + (dx, dy))
                        for s in contour
                    ]
                )
        return result
    return Bd.drawn(style, name, compatible=compatible, method=method).contours


def structure(cs):
    result = []
    polygons = [polygon(c)[0] for c in cs]
    ordered = sorted(range(len(cs)), key=lambda i: contour_key(polygons[i]))
    for i, (c, points) in enumerate(zip(cs, polygons)):
        area = O.signed_area(points)
        result.append(
            {
                "order": ordered.index(i),
                "points": sum(1 if s[0] == "line" else 3 for s in c),
                "segments": [
                    [kind, sum(1 for _ in group)]
                    for kind, group in groupby(s[0] for s in c)
                ],
                "winding": 1 if area > 0 else -1 if area < 0 else 0,
            }
        )
    return result


def compare(names=None, compatible=False, method="sample"):
    rows = []
    for name in CS.ORDER if names is None else names:
        pair = [
            structure(contours(style, name, compatible, method))
            for style in ("Regular", "Bold")
        ]
        a, b = pair
        mismatch = None
        contour_ok = len(a) == len(b)
        if not contour_ok:
            mismatch = {"reason": "different contour count"}
        for i, (ca, cb) in enumerate(zip(a, b)):
            if ca["winding"] != cb["winding"]:
                contour_ok = False
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different winding or contour order",
                }
            elif ca["order"] != cb["order"]:
                contour_ok = False
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different contour order",
                }
            elif ca["points"] != cb["points"]:
                mismatch = mismatch or {"contour": i, "reason": "different point count"}
            elif ca["segments"] != cb["segments"]:
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different segment types",
                }
        rows.append(
            {
                "name": name,
                "contour_counts": [len(a), len(b)],
                "masters": dict(zip(("Regular", "Bold"), pair)),
                "contours_compatible": contour_ok,
                "point_compatible": mismatch is None,
                "first_mismatch": mismatch,
            }
        )
    return {
        "method": method if compatible else "default",
        "scope": "full" if names is None else list(names),
        "glyphs": len(rows),
        "contours_compatible": sum(r["contours_compatible"] for r in rows),
        "point_compatible": sum(r["point_compatible"] for r in rows),
        "rows": rows,
    }


def summary(report):
    return (
        f"glyphs {report['glyphs']}, contours-compatible {report['contours_compatible']}, "
        f"point-compatible {report['point_compatible']}"
    )


def write_report(path, data):
    """Keep one glyph per line so that changes in the proof can be read."""
    sections = []
    for mode, report in data.items():
        counts = {key: value for key, value in report.items() if key != "rows"}
        head = json.dumps(counts, ensure_ascii=False)[:-1]
        rows = ",\n".join(
            "  " + json.dumps(row, ensure_ascii=False) for row in report["rows"]
        )
        sections.append(f' "{mode}": {head}, "rows": [\n{rows}\n ]}}')
    path.write_text("{\n" + ",\n".join(sections) + "\n}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixed", "--compatible", action="store_true")
    ap.add_argument("--method", choices=("sample", "refit"), default="sample")
    ap.add_argument(
        "--glyphs",
        help="Comma-separated glyph names; the default is the full glyph set.",
    )
    ap.add_argument("--out", type=Path, default=REPORT)
    args = ap.parse_args(argv)
    if args.glyphs and args.out.resolve() == REPORT.resolve():
        # A subset must never replace the committed full report.
        args.out = REPORT.parents[2] / "build/compat-subset.json"
    report = compare(
        args.glyphs.split(",") if args.glyphs else None, args.fixed, args.method
    )
    print(summary(report), flush=True)
    if args.fixed and not args.glyphs:
        measurements = topology_measurements()
        for row in report["rows"]:
            if row["name"] in measurements:
                row["topology"] = measurements[row["name"]]
    data = json.loads(args.out.read_text()) if args.out.exists() else {}
    data["fixed" if args.fixed else "default"] = report
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_report(args.out, data)
    return int(args.fixed and report["point_compatible"] != report["glyphs"])


if __name__ == "__main__":
    raise SystemExit(main())
