"""Build the Heddle sources: variable masters, designspace, static UFOs.

Usage:
    python -m loom.build [--out build]

Writes:
    build/master/Heddle-wWWW-dDDD.ufo   16 masters (wght 100, 400, 700, 900 x wdth 70, 85, 100, 140)
    build/Heddle.designspace            axes wght 100-900, wdth 70-140, 13 named instances
    build/static/MachineMadeHeddle-{Style}.ufo   statics, overlaps removed

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

FAMILY = "machine-made Heddle"
PS_FAMILY = "MachineMadeHeddle"
VERSION = (0, 200)  # 0.200: Heddle 0.2
COPYRIGHT = "Copyright 2026 The machine-made Heddle Project Authors (https://github.com/machine-made/type)"
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
# "machine-made Heddle" is 20 characters, and family plus style must
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
    return f"Heddle-w{int(wght):03d}-d{int(wdth):03d}"


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


def ink_bounds(name: str, wght: float, wdth: float) -> tuple[float, float, float, float]:
    contours, _ = drawn(name, wght, wdth)
    xs = [x for c in contours for x, _, _ in c]
    ys = [y for c in contours for _, y, _ in c]
    return min(xs), min(ys), max(xs), max(ys)


def ink_spans(name: str, wght: float, wdth: float, y: float) -> list[tuple[float, float]]:
    """Return the filled x intervals of a drawn glyph at height y (nonzero rule)."""
    contours, _ = drawn(name, wght, wdth)
    hits = []
    for c in contours:
        poly = R._flatten(c, 16)
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 <= y < y1) or (y1 <= y < y0):
                x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                hits.append((x, 1 if y1 > y0 else -1))
    hits.sort()
    spans, wind, start = [], 0, None
    for x, d in hits:
        before = wind
        wind += d
        if before == 0 and wind != 0:
            start = x
        elif before != 0 and wind == 0:
            spans.append((start, x))
    return spans


def top_anchor(base: str, wght: float, wdth: float) -> float:
    """x of the centre of a top mark over a base."""
    if base == "dotlessj":
        p = G.Params(wght, wdth)
        return p.sb + G.GLYPHS[base].width(p) - p.S / 2
    return ink_center(base, wght, wdth)


def bottom_anchor(base: str, wght: float, wdth: float) -> float:
    """x of the centre of a mark below a base (r: under the stem)."""
    if base == "r":
        p = G.Params(wght, wdth)
        return p.sb + p.S / 2
    return ink_center(base, wght, wdth)


def mark_width(mark: str, wght: float, wdth: float) -> float:
    """Ink width of a mark (curves flattened, so handles do not count)."""
    contours, _ = drawn(mark, wght, wdth)
    xs = [x for c in contours for x, _ in R._flatten(c, 16)]
    return max(xs) - min(xs)


def mark_height(mark: str, wght: float, wdth: float) -> float:
    contours, _ = drawn(mark, wght, wdth)
    ys = [y for c in contours for _, y in R._flatten(c, 16)]
    return max(ys) - min(ys)


def _advance(name: str, wght: float, wdth: float) -> float:
    return drawn(name, wght, wdth)[1]


def composite(name: str, wght: float, wdth: float):
    """Return ([(glyph, dx, dy)], advance) of a composite glyph.

    Marks are drawn around x = 0 with advance 0; drawn glyphs include
    their left sidebearing. See G.Comp for the places.
    """
    c = G.COMPOSITES[name]
    p = G.Params(wght, wdth)
    if c.row:
        if len(c.row) == 1 and c.row[0] in G.accent_names():
            x0, _, x1, _ = ink_bounds(c.row[0], wght, wdth)
            return [(c.row[0], p.sb - x0, 0.0)], (x1 - x0) + 2 * p.sb
        comps, x = [], 0.0
        for gname in c.row:
            comps.append((gname, x, 0.0))
            x += _advance(gname, wght, wdth)
        return comps, x
    base = c.base
    adv = _advance(base, wght, wdth)
    shift = 0.0
    # A top mark wider than a narrow base widens the glyph, so that marks
    # on neighbours do not touch; the base moves to the centre. The
    # .narrow marks (0.2) fit: ï Ï Ĩ ĺ keep the advance of their base.
    for mark, place in c.marks:
        if place in ("top", "top-asc"):
            need = mark_width(mark, wght, wdth) + 0.5 * p.sb
            shift = max(shift, (need - adv) / 2)
    shift = shift if shift > 0.5 else 0.0
    comps = [(base, shift, 0.0)]
    for mark, place in c.marks:
        if place == "top":
            comps.append((mark, top_anchor(base, wght, wdth) + shift, 0.0))
        elif place == "top-asc":
            comps.append((mark, top_anchor(base, wght, wdth) + shift, float(G.ASC - G.CAP)))
        elif place == "bottom":
            comps.append((mark, bottom_anchor(base, wght, wdth) + shift, 0.0))
        elif place == "ogonek":
            a, b = ink_spans(base, wght, wdth, 4.0)[-1]
            wo = mark_width(mark, wght, wdth)
            right = b if b - a >= wo else (a + b) / 2 + wo / 2
            comps.append((mark, right + shift, 0.0))
        elif place == "right":
            # The vertical caron: its top at the ascender (lowercase) or
            # the cap height, right of the ink it stands next to.
            top = max(ink_bounds(base, wght, wdth)[3], G.CAP if base[0].isupper() else G.ASC)
            y0 = top - mark_height(mark, wght, wdth)
            btop = ink_bounds(base, wght, wdth)[3]
            xr = max([sp[-1][1] for y in range(int(y0), int(top), 10)
                      if (sp := ink_spans(base, wght, wdth, y + 0.5))]
                     + [ink_spans(base, wght, wdth, btop - 20)[-1][1]])
            x = xr + 0.45 * p.sb + 8
            comps.append((mark, x + shift, top))
            adv = max(adv, x + mark_width(mark, wght, wdth) + 0.6 * p.sb)
        elif place == "dot":
            top = ink_bounds(base, wght, wdth)[3]
            x = ink_spans(base, wght, wdth, top - 20)[0][1] + 0.5 * p.sb + 12
            dy = (G.CAP - G.XH) / 2 if base == "L" else 0.0
            comps.append((mark, x - p.sb + shift, dy))
            adv = max(adv, x + G.dot_size(p) + p.sb)
        else:
            raise ValueError(place)
    return comps, adv + 2 * shift


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
        "Heddle is a Swiss display grotesk by machine-made, built from four "
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
    font.features.text = features()


def features() -> str:
    """OpenType feature code: frac, numr and dnom (0.2). ufo2ft adds kern."""
    figs = " ".join(G.FIGURES)
    numr = " ".join(f"{f}.numr" for f in G.FIGURES)
    dnom = " ".join(f"{f}.dnom" for f in G.FIGURES)
    return (
        "languagesystem DFLT dflt;\n"
        "languagesystem latn dflt;\n\n"
        f"@figures = [{figs}];\n"
        f"@numr = [{numr}];\n"
        f"@dnom = [{dnom}];\n\n"
        "# Fractions: figures before the slash become numerators, figures\n"
        "# after it denominators; the slash becomes the fraction slash.\n"
        "feature frac {\n"
        "    lookup FRAC_SLASH { sub slash by fraction; } FRAC_SLASH;\n"
        "    lookup FRAC_NUMR { sub @figures by @numr; } FRAC_NUMR;\n"
        "    lookup FRAC_DNOM { sub [fraction @dnom] @numr' by @dnom; } FRAC_DNOM;\n"
        "} frac;\n\n"
        "feature numr { sub @figures by @numr; } numr;\n"
        "feature dnom { sub @figures by @dnom; } dnom;\n"
    )


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


def path_segments(path) -> list[list]:
    """Return the contours of a pathops path as lists of (op, points)."""
    from fontTools.pens.recordingPen import RecordingPen

    rec = RecordingPen()
    path.draw(rec)
    out, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [("moveTo", [tuple(args[0])])]
        elif op in ("closePath", "endPath"):
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append((op, [tuple(a) for a in args]))
    return out


def snap(path) -> list[list]:
    """Round a union result to integer points, dropping degenerate segments.

    Where pathops splits curves near an intersection, two points can
    round to the same place. A line of zero length or a curve whose
    points are all one point is dropped; a contour with less than three
    distinct points (on- or off-curve) is dropped.
    """
    out = []
    for contour in path_segments(path):
        start = (rnd(contour[0][1][0][0]), rnd(contour[0][1][0][1]))
        segs, last = [], start
        for op, pts in contour[1:]:
            q = [(rnd(x), rnd(y)) for x, y in pts]
            if all(pt == last for pt in q):
                continue
            if op == "lineTo" or (op == "curveTo" and q[0] in (last, q[-1]) and q[1] in (last, q[-1])):
                segs.append(("lineTo", [q[-1]]))
            else:
                segs.append((op, q))
            last = q[-1]
        if segs and segs[-1][1][-1] == start and segs[-1][0] == "lineTo":
            segs.pop()
        if len({start} | {pt for s in segs for pt in s[1]}) >= 3:
            out.append([("moveTo", [start])] + segs)
    return out


def split_touching(contours) -> list[list]:
    """Split contours that touch themselves into simple loops.

    pathops sometimes returns one contour that runs out to a counter and
    back along a slit of zero width (where a ring is tangent to a bar,
    as in Œ). Such a contour can wind the counter the wrong way for the
    nonzero rule. Each loop between two visits of one point becomes its
    own contour; loops of no area (the slits) are dropped. orient()
    then sets the directions.
    """
    out = []
    todo = [c for c in contours]
    while todo:
        c = todo.pop()
        start = c[0][1][0]
        ends = [start] + [seg[1][-1] for seg in c[1:]]
        seen, split = {}, None
        for i, pt in enumerate(ends[:-1] if ends[-1] == start else ends):
            if pt in seen:
                split = (seen[pt], i)
                break
            seen[pt] = i
        if split is None:
            out.append(c)
            continue
        i, j = split
        segs = c[1:]
        loop = [("moveTo", [ends[i]])] + segs[i:j]
        rest_segs = segs[:i] + segs[j:]
        todo.append(loop)
        if rest_segs:
            todo.append([("moveTo", [start])] + rest_segs)
    return [c for c in out if abs(_flat_area([c])) >= 1.0]


def _poly(contour) -> list:
    return R._flatten(_seg_contours([contour])[0], 16)


def _inside(pt, poly) -> bool:
    x, y = pt
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def orient(contours) -> list[list]:
    """Wind each loop by its nesting depth: outer loops counter-clockwise,
    counters clockwise (so nonzero and even-odd fill agree)."""
    polys = [_poly(c) for c in contours]
    out = []
    for k, c in enumerate(contours):
        depth = 0
        for m, other in enumerate(polys):
            if m == k:
                continue
            votes = sum(_inside(pt, other) for pt in polys[k][::4])
            if 2 * votes > len(polys[k][::4]):
                depth += 1
        want_ccw = depth % 2 == 0
        if (_flat_area([c]) > 0) != want_ccw:
            c = _reverse_segments(c)
        out.append(c)
    return out


def _reverse_segments(contour) -> list:
    start = contour[0][1][0]
    pts = [start] + [seg[1][-1] for seg in contour[1:]]
    out = [("moveTo", [pts[-1]])]
    for k in range(len(contour) - 1, 0, -1):
        op, q = contour[k]
        prev = pts[k - 1]
        if op == "lineTo":
            out.append(("lineTo", [prev]))
        else:
            out.append((op, list(reversed(q[:-1])) + [prev]))
    if out[-1][1][-1] != pts[-1] or len(out) == 1:
        out.append(("lineTo", [pts[-1]]))
    # Drop a closing line back to the start (closePath draws it).
    if out[-1][0] == "lineTo" and out[-1][1][0] == out[0][1][0]:
        out.pop()
    return out


def _flat_area(contours) -> float:
    """Signed area of (op, points) contours, curves flattened finely."""
    total = 0.0
    for contour in contours:
        pts = [contour[0][1][0]]
        for op, q in contour[1:]:
            p0 = pts[-1]
            if op == "lineTo":
                pts.append(q[0])
            elif op == "curveTo":
                for k in range(1, 33):
                    t = k / 32
                    m = 1 - t
                    pts.append((m ** 3 * p0[0] + 3 * m * m * t * q[0][0] + 3 * m * t * t * q[1][0] + t ** 3 * q[2][0],
                                m ** 3 * p0[1] + 3 * m * m * t * q[0][1] + 3 * m * t * t * q[1][1] + t ** 3 * q[2][1]))
            elif op == "qCurveTo":
                # One or more quadratics with implied on-curve points.
                offs, end = q[:-1], q[-1]
                ons = [p0] + [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(offs, offs[1:])] + [end]
                for i, c in enumerate(offs):
                    a, b = ons[i], ons[i + 1]
                    for k in range(1, 33):
                        t = k / 32
                        m = 1 - t
                        pts.append((m * m * a[0] + 2 * m * t * c[0] + t * t * b[0],
                                    m * m * a[1] + 2 * m * t * c[1] + t * t * b[1]))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            total += x0 * y1 - x1 * y0
    return total / 2


def _draw_segments(contours, pen) -> None:
    for contour in contours:
        for op, pts in contour:
            getattr(pen, op)(*pts)
        pen.closePath()


def _seg_contours(contours) -> list:
    """(op, points) contours as loom contours [(x, y, on)] (cubics only)."""
    out = []
    for contour in contours:
        c = [(*contour[0][1][0], True)]
        for op, q in contour[1:]:
            if op == "lineTo":
                c.append((*q[0], True))
            else:
                c += [(*q[0], False), (*q[1], False), (*q[2], True)]
        if c[-1][:2] == c[0][:2] and len(c) > 1 and c[-1][2]:
            c = c[:-1]
        out.append(c)
    return out


class OverlapError(SystemExit):
    pass


def clean_union(name: str, contours) -> list:
    """Return the overlap-free outline of loom contours, with integer points.

    0.2 boolean step, no fallbacks:

    1. union with skia-pathops (nonzero fill, one path);
    2. snap: round to integers and drop the degenerate segments that
       rounding makes (see snap);
    3. split contours that touch themselves into simple loops and wind
       each loop by its nesting depth (split_touching, orient);
    4. check that the result equals the nonzero fill of the primitives
       (raster, 4 units per pixel) and that it has no overlap left: its
       signed area equals the signed area of its own union, within
       2 square units.

    Stops the build when a check fails.
    """
    ref = R.nonzero_mask(contours)
    path = union(contours)
    snapped = orient(split_touching(snap(path)))
    out = _seg_contours(snapped)
    if R.mismatch(ref, R.path_mask(_to_path(out))) != 0:
        raise OverlapError(f"Glyph {name!r}: the union differs from the nonzero fill.")
    again = _to_path(out)
    again.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    if abs(_flat_area(snapped) - _flat_area(path_segments(again))) > 2.0:
        raise OverlapError(f"Glyph {name!r}: overlaps are left after snapping.")
    return snapped


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
            _draw_segments(clean_union(name, contours), g.getPen())
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
    ap = argparse.ArgumentParser(description="Build the Heddle UFO sources.")
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
    doc.write(out / "Heddle.designspace")
    print(f"Wrote {len(masters)} masters and {out / 'Heddle.designspace'}.")
    for (w, d), font in statics.items():
        font.save(static_dir / f"{PS_FAMILY}-{ps_style(w, d)}.ufo", overwrite=True)
    if statics:
        print(f"Wrote {len(statics)} static UFOs to {static_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
