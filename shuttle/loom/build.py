"""Build the Shuttle 0.1 sources: variable masters, designspace, static UFOs.

Usage:
    python -m loom.build [--out build]

Writes:
    build/master/Shuttle-wWWW-dDDD.ufo   12 masters (wght 100, 400, 700, 900 x wdth 70, 100, 140)
    build/Shuttle.designspace            axes wght 100-900, wdth 70-140, 13 named instances
    build/static/MachineMadeShuttle-{Style}.ufo   statics, overlaps removed

Every glyph has the same contours and points in all masters (see
loom/geom.py). The build stops if a glyph does not. Accented letters
are components in the masters and are decomposed in the statics.

The statics come from the masters by the same interpolation as the
variable font, so a static and the variable font at the same location
have the same shapes.
"""

from __future__ import annotations

import argparse
import math
import shutil
from functools import lru_cache
from pathlib import Path

import pathops
import ufoLib2
from fontTools.designspaceLib import (
    AxisDescriptor,
    AxisLabelDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.varLib.models import VariationModel, normalizeLocation
from ufoLib2.objects import Component

from loom import glyphs as G
from loom import kerning as K
from loom import raster as R
from loom.geom import Canvas, signed_area

FAMILY = "machine-made Shuttle"
PS_FAMILY = "MachineMadeShuttle"
VERSION = (0, 100)  # 0.100: Shuttle 0.1
COPYRIGHT = "Copyright 2026 The machine-made Shuttle Project Authors (https://github.com/machine-made/type)"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, "
    "Version 1.1. This license is available with a FAQ at: "
    "https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"

TYPO_ASCENDER = 950
TYPO_DESCENDER = -250
UNDERLINE_POSITION = -120

WGHT_MASTERS = G.WGHT
WDTH_MASTERS = G.WDTH
DEFAULT = (400, 100)

WEIGHTS = [
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
    (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
    (900, "Black"),
]
# Width names. usWidthClass is the OpenType class whose nominal width
# (75, 87.5, 100, 125, 150 %) is nearest. The names are short on purpose:
# "machine-made Shuttle" is 20 characters, and family plus style must
# stay within 32 (Fontspector name/family_and_style_max_length).
WIDTHS = [
    (70, "Compressed", 3), (85, "Condensed", 4), (100, "Normal", 5),
    (120, "Wide", 7), (140, "Extended", 8),
]
WIDTH_CLASS = {v: c for v, _, c in WIDTHS}
WIDTH_NAME = {v: n for v, n, _ in WIDTHS}
WEIGHT_NAME = dict(WEIGHTS)

# Static fonts: the 9 weights at width 100, and Bold at 70 and 140.
STATICS = [(w, 100) for w, _ in WEIGHTS] + [(700, 70), (700, 140)]

AXES = {"wght": (100, 400, 900), "wdth": (70, 100, 140)}
FEATURE_WRITERS = [{"class": "KernFeatureWriter"}]


def style_name(wght: float, wdth: float) -> str:
    """'Regular', 'Bold', 'Condensed', 'Condensed Bold', ..."""
    wn = WEIGHT_NAME[wght]
    if wdth == 100:
        return wn
    dn = WIDTH_NAME[wdth]
    return dn if wn == "Regular" else f"{dn} {wn}"


def ps_style(wght: float, wdth: float) -> str:
    return style_name(wght, wdth).replace(" ", "")


def master_name(wght: float, wdth: float) -> str:
    """Zero-padded, so that a sorted file list is in designspace order
    (varLib.interpolatable compares neighbours in the order it gets)."""
    return f"Shuttle-w{int(wght):03d}-d{int(wdth):03d}"


# ------------------------------------------------------------- outlines

def rnd(v: float) -> int:
    return int(math.floor(v + 0.5))


@lru_cache(maxsize=None)
def drawn(name: str, wght: float, wdth: float):
    """Return (contours, advance) of a drawn glyph or mark, in floats.

    Contours include the left sidebearing offset. Marks have no offset
    and advance 0.
    """
    p = G.Params(wght, wdth)
    g = Canvas(p.S, p.H)
    if name in G.accent_names():
        G.draw_accent(g, name)
        return tuple(tuple(c) for c in g.contours), 0.0
    gl = G.GLYPHS[name]
    W = gl.width(p)
    g.shift(p.sb, 0, lambda: gl.draw(g, W))
    return tuple(tuple(c) for c in g.contours), W + 2 * p.sb


def ink_center(name: str, wght: float, wdth: float) -> float:
    contours, adv = drawn(name, wght, wdth)
    xs = [x for c in contours for x, _, _ in c]
    return (min(xs) + max(xs)) / 2 if xs else adv / 2


def composite(name: str, wght: float, wdth: float):
    """Return ([(glyph, dx, dy)], advance) of an accented letter."""
    _, base, acc = G.COMPOSITES[name]
    _, adv = drawn(base, wght, wdth)
    dx = ink_center(base, wght, wdth)
    # A mark wider than a narrow base (i, I) widens the glyph, so that
    # marks on neighbours do not touch. The base moves to the centre.
    acc_contours, _ = drawn(acc, wght, wdth)
    xs = [x for c in acc_contours for x, _, _ in c]
    p = G.Params(wght, wdth)
    need = (max(xs) - min(xs)) + p.sb
    shift = max(0.0, (need - adv) / 2)
    return [(base, shift, 0.0), (acc, dx + shift, 0.0)], adv + 2 * shift


def structure(contours) -> tuple:
    return tuple(tuple(on for _, _, on in c) for c in contours)


def drawn_names() -> list[str]:
    return [n for n in G.glyph_order() if n not in G.COMPOSITES]


def check_compatible() -> None:
    """Stop when a glyph has a different point structure between masters."""
    for name in drawn_names():
        shapes = {structure(drawn(name, w, d)[0]) for w in WGHT_MASTERS for d in WDTH_MASTERS}
        if len(shapes) != 1:
            raise SystemExit(f"Glyph {name!r} is not compatible between masters.")


def to_pen(glyph, contours) -> None:
    pen = glyph.getPointPen()
    for c in contours:
        pen.beginPath()
        n = len(c)
        for i, (x, y, on) in enumerate(c):
            if on:
                prev_on = c[i - 1][2]
                seg = "line" if prev_on else "curve"
                pen.addPoint((rnd(x), rnd(y)), segmentType=seg)
            else:
                pen.addPoint((rnd(x), rnd(y)))
        pen.endPath()


# ----------------------------------------------------------------- info

def set_info(font: ufoLib2.Font, wght: float, wdth: float, *, static: bool) -> None:
    info = font.info
    style = style_name(wght, wdth)
    info.familyName = FAMILY
    info.styleName = style
    wn = WEIGHT_NAME[wght]
    width_part = "" if wdth == 100 else f" {WIDTH_NAME[wdth]}"
    if static and wn not in ("Regular", "Bold"):
        info.styleMapFamilyName = f"{FAMILY}{width_part} {wn}"
        info.styleMapStyleName = "regular"
    else:
        info.styleMapFamilyName = f"{FAMILY}{width_part}"
        info.styleMapStyleName = "bold" if wn == "Bold" else "regular"
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = COPYRIGHT
    info.openTypeNameLicense = LICENSE_DESCRIPTION
    info.openTypeNameLicenseURL = LICENSE_URL
    info.openTypeNameManufacturer = "machine-made"
    info.openTypeNameManufacturerURL = "https://github.com/machine-made"
    info.openTypeNameDesigner = "machine-made agents"
    info.openTypeNameDescription = (
        "Shuttle is a Swiss display grotesk by machine-made, built from four "
        "primitives, with a weight axis and a width axis."
    )
    info.postscriptFontName = f"{PS_FAMILY}-{ps_style(wght, wdth)}"
    info.postscriptIsFixedPitch = False
    info.postscriptUnderlinePosition = UNDERLINE_POSITION
    info.postscriptUnderlineThickness = rnd(G.Params(400, 100).H)
    info.openTypeOS2VendorID = "NONE"
    info.openTypeOS2WeightClass = int(wght)
    info.openTypeOS2WidthClass = WIDTH_CLASS[wdth]
    info.openTypeOS2Type = []  # installable embedding
    # Bit 7: USE_TYPO_METRICS. Bit 8: WWS (the names are WWS-conformant).
    info.openTypeOS2Selection = [7, 8]
    panose_weight = min(11, max(2, round(wght / 100) + 1))
    info.openTypeOS2Panose = [2, 0, panose_weight, 0, 0, 0, 0, 0, 0, 0]
    info.unitsPerEm = G.UPM
    info.xHeight = G.XH
    info.capHeight = G.CAP
    info.ascender = G.ASC
    info.descender = G.DESC
    info.italicAngle = 0
    info.openTypeOS2TypoAscender = TYPO_ASCENDER
    info.openTypeOS2TypoDescender = TYPO_DESCENDER
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = TYPO_ASCENDER
    info.openTypeHheaDescender = TYPO_DESCENDER
    info.openTypeHheaLineGap = 0
    font.lib["com.github.googlei18n.ufo2ft.featureWriters"] = FEATURE_WRITERS
    font.lib["public.postscriptNames"] = {}


def set_unicodes(font: ufoLib2.Font) -> None:
    for u, name in sorted(G.cmap().items()):
        font[name].unicodes = sorted(set(font[name].unicodes) | {u})


# -------------------------------------------------------------- masters

def build_master(wght: float, wdth: float) -> ufoLib2.Font:
    """Return one variable-font master (overlapping primitives, components)."""
    p = G.Params(wght, wdth)
    font = ufoLib2.Font()
    set_info(font, wght, wdth, static=False)
    if (wght, wdth) != DEFAULT:
        font.info.styleName = f"w{int(wght)} d{int(wdth)}"
    order = G.glyph_order()
    font.lib["public.glyphOrder"] = order
    for name in order:
        g = font.newGlyph(name)
        if name in G.COMPOSITES:
            comps, adv = composite(name, wght, wdth)
            g.width = rnd(adv)
            for base, dx, dy in comps:
                g.components.append(Component(base, transformation=(1, 0, 0, 1, rnd(dx), rnd(dy))))
        else:
            contours, adv = drawn(name, wght, wdth)
            g.width = rnd(adv)
            to_pen(g, contours)
    set_unicodes(font)
    font.groups.update(K.groups())
    font.kerning.update(K.kerning(p))
    return font


def win_metrics(fonts) -> tuple[int, int]:
    """Return (usWinAscent, usWinDescent) that cover every glyph of every font."""
    y_min, y_max = 0.0, 0.0
    for f in fonts:
        for glyph in f:
            b = glyph.getBounds(f)
            if b is not None:
                y_min = min(y_min, b.yMin)
                y_max = max(y_max, b.yMax)
    return max(TYPO_ASCENDER, math.ceil(y_max)), max(-TYPO_DESCENDER, math.ceil(-y_min))


# --------------------------------------------------------------- statics

def _model():
    locs = [{"wght": w, "wdth": d} for w in WGHT_MASTERS for d in WDTH_MASTERS]
    norm = [normalizeLocation(l, AXES) for l in locs]
    return locs, VariationModel(norm, axisOrder=["wght", "wdth"])


def scalars(wght: float, wdth: float) -> list[tuple[tuple[float, float], float]]:
    """Return [((wght, wdth) of a master, weight)] for a location.

    The same interpolation as the variable font (fontTools VariationModel).
    """
    locs, model = _model()
    target = normalizeLocation({"wght": wght, "wdth": wdth}, AXES)
    s = model.getMasterScalars(target)
    return [((l["wght"], l["wdth"]), v) for l, v in zip(locs, s) if v != 0]


def master_outline(name: str, wght: float, wdth: float) -> tuple[list, float]:
    """Return (decomposed contours with rounded points, advance) in one master.

    The points are rounded as in the master UFO, so that the statics
    interpolate the same numbers as the variable font.
    """
    if name in G.COMPOSITES:
        comps, adv = composite(name, wght, wdth)
        out = []
        for base, dx, dy in comps:
            cs, _ = drawn(base, wght, wdth)
            out += [[(rnd(x) + rnd(dx), rnd(y) + rnd(dy), on) for x, y, on in c] for c in cs]
        return out, rnd(adv)
    cs, adv = drawn(name, wght, wdth)
    return [[(rnd(x), rnd(y), on) for x, y, on in c] for c in cs], rnd(adv)


def direct_outline(name: str, wght: float, wdth: float) -> tuple[list, float]:
    """Return (decomposed contours, advance) straight from the glyph table.

    No masters and no rounding: what the engine draws at this location.
    tools/drift.py compares this with `interpolated`.
    """
    if name in G.COMPOSITES:
        comps, adv = composite(name, wght, wdth)
        out = []
        for base, dx, dy in comps:
            cs, _ = drawn(base, wght, wdth)
            out += [[(x + dx, y + dy, on) for x, y, on in c] for c in cs]
        return out, adv
    cs, adv = drawn(name, wght, wdth)
    return [list(c) for c in cs], adv


def interpolated(name: str, wght: float, wdth: float) -> tuple[list, float]:
    """Return (contours, advance) of a glyph at any location, from the masters."""
    parts = scalars(wght, wdth)
    acc = None
    adv = 0.0
    for (mw, md), s in parts:
        cs, a = master_outline(name, mw, md)
        adv += s * a
        if acc is None:
            acc = [[[s * x, s * y, on] for x, y, on in c] for c in cs]
        else:
            for ca, cb in zip(acc, cs):
                for pa, (x, y, _) in zip(ca, cb):
                    pa[0] += s * x
                    pa[1] += s * y
    return [[tuple(p) for p in c] for c in acc or []], adv


def _to_path(contours) -> pathops.Path:
    path = pathops.Path()
    path.fillType = pathops.FillType.WINDING
    pen = path.getPen()
    for c in contours:
        n = len(c)
        pen.moveTo(c[0][:2])
        i = 1
        while i <= n:
            p = c[i % n]
            if p[2]:
                pen.lineTo(p[:2])
                i += 1
            else:
                c1, c2, p3 = c[i % n], c[(i + 1) % n], c[(i + 2) % n]
                pen.curveTo(c1[:2], c2[:2], p3[:2])
                i += 3
        pen.closePath()
    return path


def union(contours) -> pathops.Path:
    path = _to_path(contours)
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    return path


def groups(contours) -> list[list]:
    """Split loom contours into primitives: a ring outer with its counter."""
    out = []
    for c in contours:
        if signed_area(c) < 0 and out:
            out[-1].append(c)
        else:
            out.append([c])
    return out


def robust_union(contours, reference=None) -> pathops.Path:
    """Return the union of loom contours, checked against a nonzero fill.

    pathops can drop a piece where two curves nearly coincide (the two
    rings of S at the spine). When the result differs from the nonzero
    fill of the raw contours, move each primitive by a tiny step (0.001
    unit times its index; rounding removes it) and try again. Stop when
    that fails too.
    """
    ref = R.nonzero_mask(contours) if reference is None else reference
    path = union(contours)
    if R.mismatch(ref, R.path_mask(path)) == 0:
        return path
    for eps in (1e-3, 1e-2):
        moved = [[(x + eps * k, y + 0.7 * eps * k, on) for x, y, on in c]
                 for k, grp in enumerate(groups(contours)) for c in grp]
        path = union(moved)
        if R.mismatch(ref, R.path_mask(path)) == 0:
            return path
    raise SystemExit("Overlap removal failed; the union differs from the nonzero fill.")


class _RoundPen:
    """A pen that rounds every point before it reaches the target pen."""

    def __init__(self, pen):
        self.pen = pen

    def moveTo(self, p):
        self.pen.moveTo((rnd(p[0]), rnd(p[1])))

    def lineTo(self, p):
        self.pen.lineTo((rnd(p[0]), rnd(p[1])))

    def curveTo(self, *pts):
        self.pen.curveTo(*[(rnd(x), rnd(y)) for x, y in pts])

    def qCurveTo(self, *pts):
        self.pen.qCurveTo(*[(rnd(x), rnd(y)) for x, y in pts])

    def closePath(self):
        self.pen.closePath()

    def endPath(self):
        self.pen.endPath()


def build_static(wght: float, wdth: float) -> ufoLib2.Font:
    """Return one static instance (overlaps removed, composites decomposed)."""
    font = ufoLib2.Font()
    set_info(font, wght, wdth, static=True)
    order = [n for n in G.glyph_order() if n not in G.accent_names()]
    font.lib["public.glyphOrder"] = order
    for name in order:
        g = font.newGlyph(name)
        contours, adv = interpolated(name, wght, wdth)
        g.width = rnd(adv)
        if contours:
            ref = R.nonzero_mask(contours)
            path = robust_union(contours, ref)
            # Rounding can make a new overlap: simplify again after it,
            # unless pathops gets that wrong (then keep the rounded path).
            rounded = pathops.Path()
            path.draw(_RoundPen(rounded.getPen()))
            tmp = pathops.Path()
            rounded.draw(tmp.getPen())
            tmp.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
            if R.mismatch(ref, R.path_mask(tmp)) != 0:
                tmp = rounded
                if R.mismatch(ref, R.path_mask(tmp)) != 0:
                    raise SystemExit(f"Glyph {name!r}: rounding after overlap removal changed the shape.")
            tmp.draw(_RoundPen(g.getPen()))
    set_unicodes(font)
    font.groups.update(K.groups())
    # Kerning: the same interpolation as the variable font.
    kern = {}
    for (mw, md), s in scalars(wght, wdth):
        for pair, v in K.kerning(G.Params(mw, md)).items():
            kern[pair] = kern.get(pair, 0.0) + s * v
    font.kerning.update({k: rnd(v) for k, v in kern.items() if rnd(v) != 0})
    return font


# --------------------------------------------------------- designspace

def build_designspace(masters: dict) -> DesignSpaceDocument:
    doc = DesignSpaceDocument()
    wght = AxisDescriptor()
    wght.tag, wght.name = "wght", "Weight"
    wght.minimum, wght.default, wght.maximum = AXES["wght"]
    wght.axisLabels = [
        AxisLabelDescriptor(name=n, userValue=v, elidable=(v == 400),
                            linkedUserValue=(700 if v == 400 else None))
        for v, n in WEIGHTS
    ]
    wdth = AxisDescriptor()
    wdth.tag, wdth.name = "wdth", "Width"
    wdth.minimum, wdth.default, wdth.maximum = AXES["wdth"]
    wdth.axisLabels = [
        AxisLabelDescriptor(name=n, userValue=v, elidable=(v == 100))
        for v, n, _ in WIDTHS
    ]
    doc.addAxis(wght)
    doc.addAxis(wdth)
    for (wv, dv), path in masters.items():
        s = SourceDescriptor()
        s.path = str(path)
        s.filename = f"master/{path.name}"
        s.name = master_name(wv, dv)
        s.familyName = FAMILY
        s.styleName = f"w{wv} d{dv}"
        s.location = {"Weight": wv, "Width": dv}
        doc.addSource(s)
    # Named instances: the 9 weights at width 100 and the 4 other widths
    # at Regular. A width and a weight together ("Compressed Bold") make
    # a name longer than 32 characters with the family name. STAT names
    # every width and weight, so apps that read STAT show all of them.
    named = [(wv, 100) for wv, _ in WEIGHTS] + [(400, dv) for dv, _, _ in WIDTHS if dv != 100]
    for wv, dv in named:
        inst = InstanceDescriptor()
        inst.familyName = FAMILY
        inst.styleName = style_name(wv, dv)
        inst.name = f"{FAMILY} {inst.styleName}"
        inst.postScriptFontName = f"{PS_FAMILY}-{ps_style(wv, dv)}"
        inst.location = {"Weight": wv, "Width": dv}
        doc.addInstance(inst)
    doc.lib["com.github.googlei18n.ufo2ft.featureWriters"] = FEATURE_WRITERS
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Shuttle 0.1 UFO sources.")
    ap.add_argument("--out", default="build")
    ap.add_argument("--no-static", action="store_true", help="Do not write the static UFOs.")
    args = ap.parse_args(argv)
    out = Path(args.out)
    master_dir = out / "master"
    static_dir = out / "static"
    for d in (master_dir, static_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    check_compatible()
    fonts = {(w, d): build_master(w, d) for w in WGHT_MASTERS for d in WDTH_MASTERS}
    statics = {} if args.no_static else {(w, d): build_static(w, d) for w, d in STATICS}
    metrics = win_metrics(fonts.values())
    for f in list(fonts.values()) + list(statics.values()):
        f.info.openTypeOS2WinAscent, f.info.openTypeOS2WinDescent = metrics
    masters = {}
    for (w, d), font in fonts.items():
        path = master_dir / f"{master_name(w, d)}.ufo"
        font.save(path, overwrite=True)
        masters[(w, d)] = path
    doc = build_designspace(masters)
    doc.write(out / "Shuttle.designspace")
    print(f"Wrote {len(masters)} masters and {out / 'Shuttle.designspace'}.")
    for (w, d), font in statics.items():
        font.save(static_dir / f"{PS_FAMILY}-{ps_style(w, d)}.ufo", overwrite=True)
    if statics:
        print(f"Wrote {len(statics)} static UFOs to {static_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
