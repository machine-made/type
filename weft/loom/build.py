"""Build the Weft sources: variable masters, designspace, static UFOs.

Usage:
    python -m loom.build [--out build]

Writes:
    build/master/Weft-w{W}-f{F}.ufo   12 masters, overlapping pieces
    build/Weft.designspace            axes wght 100-900, FRAG 0-100
    build/static/Weft-{Style}.ufo     9 statics at FRAG 0, overlaps removed

Masters: wght 100, 400, 900 x FRAG 0, 15, 50, 100. Every glyph has the
same contours and points in all 12 masters (see loom/pieces.py).
Accented letters and the guillemets are components in the masters
(offsets from extended.parts(), which can depend on the stroke width),
and are decomposed in the statics. Accents above the base are drawn a
little larger at heavy weights (extended.ACCENT_SCALE).
"""

from __future__ import annotations

import argparse
import json
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
from ufoLib2.objects import Anchor as UfoAnchor
from ufoLib2.objects import Component

from loom import extended as ext
from loom import glyphs as data
from loom import pieces
from fontTools.ttLib.tables.O_S_2f_2 import intersectUnicodeRanges
from ufo2ft.util import calcCodePageRanges

from loom.outline import clean_contour, path_contours, signed_area

UPM = 1000
# 1 design unit = 62.5 font units. The 16-unit em is 1000 and the
# 12-unit advance is 750.
SCALE = UPM / data.METRICS["units_per_em"]
ADVANCE = round(data.METRICS["advance"] * SCALE)
BOX = data.METRICS["box_offset"]

FAMILY = "machine-made Weft"
PS_FAMILY = "MachineMadeWeft"
VERSION = (0, 200)  # 0.200: Weft 0.2
COPYRIGHT = "Copyright 2026 The machine-made Weft Project Authors (https://github.com/machine-made/type)"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, "
    "Version 1.1. This license is available with a FAQ at: "
    "https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"

# Line metrics in design units. 14.5 + 4.5 = 19 units: the sketch sets
# lines at 18 to 19 units. The ascender leaves room for accents.
TYPO_ASCENDER = 14.5
TYPO_DESCENDER = -4.5

WGHT_MASTERS = (100, 400, 900)
FRAG_MASTERS = pieces.F_MASTERS
DEFAULT = (400, 0)

STATICS = [
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
    (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
    (900, "Black"),
]
FRAG_NAMES = [(0, "Clean"), (15, "Notched"), (50, "Cut"), (100, "Broken")]

# Characters in Weft. Soft hyphen (U+00AD) is not in the set on
# purpose: it is a format character, not a drawn glyph.
# The double quote of the sketch table is a compound in Weft 0.2 (two
# single quotes, see extended.COMPOUNDS).
DRAWN = {ch: st for ch, st in {**data.STROKES, **ext.STROKES_EXT}.items()
         if ch not in ext.COMPOUNDS}
CHARS = sorted(set(DRAWN) | set(ext.COMPOSITES) | set(ext.COMPOUNDS) | set(ext.COMBINING), key=ord)


def u(v: float) -> int:
    """Convert design units to font units (rounded)."""
    return round(v * SCALE)


def glyph_name(ch: str) -> str:
    return ext.GLYPH_NAMES_EXT.get(ch) or data.glyph_name(ch)


def advance(name: str) -> int:
    """Return the advance of a glyph: 750, or 0 for a combining mark."""
    return 0 if name in mark_names() else ADVANCE


@lru_cache(maxsize=None)
def mark_names() -> frozenset[str]:
    return frozenset(glyph_name(ch) for ch in ext.COMBINING)


def glyph_order() -> list[str]:
    # The zero-width marks come first, so all glyphs after them share one
    # advance and hmtx stays short.
    marks = [glyph_name(c) for c in CHARS if c in ext.COMBINING]
    names = [".notdef", "space"] + marks + [glyph_name(c) for c in CHARS if c not in ext.COMBINING]
    return names + sorted(ext.ALTERNATES) + sorted(ext.ACCENTS)


def charset() -> str:
    """Return every encoded character (space and no-break space too)."""
    return "  " + "".join(CHARS)


def drawn_names() -> list[str]:
    """Return the names of all glyphs with their own strokes."""
    return ([".notdef"] + [glyph_name(c) for c in sorted(DRAWN, key=ord)]
            + sorted(ext.ALTERNATES) + sorted(ext.ACCENTS))


def part_name(part: str) -> str:
    """Return the glyph name of a component (a char or an accent name)."""
    return part if part in ext.ACCENTS else glyph_name(part)


def strokes_of(name: str):
    if name == ".notdef":
        return data.NOTDEF
    if name in ext.ACCENTS:
        return ext.ACCENTS[name]
    if name in ext.ALTERNATES:
        return ext.ALTERNATES[name]
    for ch in DRAWN:
        if glyph_name(ch) == name:
            return DRAWN[ch]
    raise KeyError(f"Glyph {name!r} has no strokes.")


@lru_cache(maxsize=None)
def plan(name: str) -> pieces.GlyphPlan:
    """Return the fixed piece plan for a drawn glyph or an accent.

    The drift attempt comes from loom/drift_lock.json (see tools/relock.py).
    """
    gp = pieces.plan_glyph(name, strokes_of(name))
    attempt = drift_lock().get(name, 0)
    if attempt:
        pieces.reroll_drift(gp, attempt)
    return gp


@lru_cache(maxsize=None)
def drift_lock() -> dict[str, int]:
    path = Path(__file__).with_name("drift_lock.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text())["attempts"]


def contours(name: str, w: float, frag: float) -> list[list[tuple[float, float]]]:
    """Return the piece contours of a drawn glyph at (w, FRAG), design units.

    An accent that scales with weight is drawn at width w / s and scaled
    by s about (3.5, 0), so its stroke width stays w. The point structure
    is the same at every location.
    """
    return plan_contours(plan(name), w, frag)


def plan_contours(gp: pieces.GlyphPlan, w: float, frag: float) -> list[list[tuple[float, float]]]:
    """Like contours(), for a plan (interp.problems() calls this)."""
    name = gp.name
    s = ext.accent_scale(name, w) if name in ext.ACCENTS else 1.0
    cs = pieces.glyph_contours(gp, w / s, frag)
    if s == 1.0:
        return cs
    return [[(3.5 + s * (x - 3.5), s * y) for x, y in c] for c in cs]


def to_font(p: tuple[float, float]) -> tuple[int, int]:
    return (round((p[0] + BOX) * SCALE), round(p[1] * SCALE))


def draw_piece_contours(glyph, contours) -> None:
    pen = glyph.getPointPen()
    for c in contours:
        pen.beginPath()
        for p in c:
            pen.addPoint(to_font(p), segmentType="line")
        pen.endPath()


def _set_info(font: ufoLib2.Font, wght: float, style: str, *, static: bool) -> None:
    info = font.info
    info.familyName = FAMILY
    info.styleName = style
    if static and style not in ("Regular", "Bold"):
        info.styleMapFamilyName = f"{FAMILY} {style}"
        info.styleMapStyleName = "regular"
    else:
        info.styleMapFamilyName = FAMILY
        info.styleMapStyleName = "bold" if style == "Bold" else "regular"
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = COPYRIGHT
    info.openTypeNameLicense = LICENSE_DESCRIPTION
    info.openTypeNameLicenseURL = LICENSE_URL
    info.openTypeNameManufacturer = "machine-made"
    info.openTypeNameManufacturerURL = "https://github.com/machine-made"
    info.openTypeNameDesigner = "machine-made agents"
    info.openTypeNameDescription = (
        "Weft is a grid-built monospace by machine-made, with a weight axis "
        "and a fragmentation axis (FRAG)."
    )
    info.postscriptFontName = f"{PS_FAMILY}-{style}"
    info.postscriptIsFixedPitch = True
    info.postscriptUnderlinePosition = u(-2.4)
    # One underline thickness for the family (the Regular stroke).
    info.postscriptUnderlineThickness = u(data.stroke_width(400))
    info.openTypeOS2VendorID = "NONE"
    info.openTypeOS2WeightClass = int(wght)
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2Type = []  # installable embedding
    # Bit 7: USE_TYPO_METRICS. Bit 8: WWS (the names are WWS-conformant).
    info.openTypeOS2Selection = [7, 8]
    # PANOSE: family 2 (Latin text), weight from wght, proportion 9
    # (monospaced, the fourth digit).
    panose_weight = min(11, max(2, round(wght / 100) + 1))
    info.openTypeOS2Panose = [2, 0, panose_weight, 9, 0, 0, 0, 0, 0, 0]
    # Unicode ranges and code pages from the character set.
    cps = {ord(c) for c in charset()}
    info.openTypeOS2UnicodeRanges = sorted(intersectUnicodeRanges(cps))
    # Only the Windows ANSI code pages (bits 0 to 31): the box drawing
    # set is too small to claim the OEM code pages.
    info.openTypeOS2CodePageRanges = sorted(b for b in calcCodePageRanges(cps) if b < 32)
    info.unitsPerEm = UPM
    info.xHeight = u(data.METRICS["x_height"])
    info.capHeight = u(data.METRICS["cap_height"])
    info.ascender = u(data.METRICS["ascender"])
    info.descender = u(data.METRICS["descender"])
    info.italicAngle = 0
    asc, desc = u(TYPO_ASCENDER), u(TYPO_DESCENDER)
    info.openTypeOS2TypoAscender = asc
    info.openTypeOS2TypoDescender = desc
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = asc
    info.openTypeHheaDescender = desc
    info.openTypeHheaLineGap = 0
    # Feature writers: mark positioning for the combining marks and the
    # GDEF classes. Weft has no kerning. The other features (ccmp, ss01)
    # are in extended.FEATURES.
    font.lib["com.github.googlei18n.ufo2ft.featureWriters"] = FEATURE_WRITERS
    font.lib["public.openTypeCategories"] = categories()
    font.features.text = ext.FEATURES
    font.lib["public.glyphOrder"] = glyph_order()
    font.lib["public.postscriptNames"] = {}


FEATURE_WRITERS = [{"class": "MarkFeatureWriter"}, {"class": "GdefFeatureWriter"}]


def categories() -> dict[str, str]:
    """Return the GDEF classes: marks and the bases that carry anchors."""
    cats = {glyph_name(ch): "base" for ch in ext.ANCHOR_BASES}
    cats.update({name: "mark" for name in mark_names()})
    return dict(sorted(cats.items()))


def add_mark_anchors(font: ufoLib2.Font, w: float) -> None:
    """Add the mark anchors to the base letters and the combining marks."""
    for ch in ext.ANCHOR_BASES:
        g = font[glyph_name(ch)]
        for name, (x, y) in ext.base_anchors(ch, w).items():
            g.anchors.append(UfoAnchor(u(x + BOX), u(y), name=name))
    for ch in ext.COMBINING:
        name, (x, y) = ext.mark_anchor(ch, w)
        font[glyph_name(ch)].anchors.append(UfoAnchor(u(x + BOX), u(y), name=f"_{name}"))


def build_master(wght: float, frag: float) -> ufoLib2.Font:
    """Return one variable-font master (overlapping pieces, components)."""
    w = data.stroke_width(wght)
    font = ufoLib2.Font()
    style = "Regular" if (wght, frag) == DEFAULT else f"w{int(wght)}f{int(frag)}"
    _set_info(font, wght, style, static=False)
    for name in glyph_order():
        g = font.newGlyph(name)
        g.width = advance(name)
    font["space"].unicodes = [0x20, 0xA0]
    for ch in CHARS:
        font[glyph_name(ch)].unicodes = [ord(ch)]
    for name in drawn_names():
        draw_piece_contours(font[name], contours(name, w, frag))
    add_mark_anchors(font, w)
    # Composites: the parts at their offsets for this stroke width.
    for ch in list(ext.COMPOSITES) + list(ext.COMPOUNDS) + list(ext.COMBINING):
        g = font[glyph_name(ch)]
        for part, dx, dy in ext.parts(ch, w):
            g.components.append(Component(part_name(part), transformation=(1, 0, 0, 1, u(dx), u(dy))))
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
    return max(u(TYPO_ASCENDER), math.ceil(y_max)), max(-u(TYPO_DESCENDER), math.ceil(-y_min))


def set_win_metrics(fonts, metrics: tuple[int, int]) -> None:
    """Set one pair of win metrics on the whole family."""
    for f in fonts:
        f.info.openTypeOS2WinAscent, f.info.openTypeOS2WinDescent = metrics


# ------------------------------------------------------------- statics

def _union(contours) -> list[list[tuple]]:
    """Return the overlap-free union of piece contours (integer grid)."""
    path = pathops.Path()
    path.fillType = pathops.FillType.WINDING
    pen = path.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for p in c[1:]:
            pen.lineTo(p)
        pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    out = [clean_contour(c) for c in path_contours(path)]
    out = [c for c in out if len(c) >= 3 and abs(signed_area(c)) > 0]
    # Rounding to the integer grid can make new overlaps. Union again and
    # round again until the result is stable.
    for _ in range(4):
        p = pathops.Path()
        pen = p.getPen()
        for c in out:
            pen.moveTo(c[0])
            for pt in c[1:]:
                pen.lineTo(pt)
            pen.closePath()
        p.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
        new = [clean_contour(c) for c in path_contours(p)]
        new = [c for c in new if len(c) >= 3 and abs(signed_area(c)) > 0]
        if new == out:
            break
        out = new
    return out


def static_contours(name: str, wght: float, frag: float = 0) -> list[list[tuple]]:
    """Return the overlap-free contours of a glyph (composites decomposed)."""
    w = data.stroke_width(wght)
    raw: list[list[tuple]] = []

    def add(plan_name: str, dx: float, dy: float) -> None:
        # The variable font rounds component offsets to font units. Do
        # the same, so the statics match the variable font.
        ox, oy = u(dx) / SCALE, u(dy) / SCALE
        for c in contours(plan_name, w, frag):
            raw.append([((x + ox + BOX) * SCALE, (y + oy) * SCALE) for x, y in c])

    ch = composite_char(name)
    if ch is None:
        add(name, 0.0, 0.0)
    else:
        for part, dx, dy in ext.parts(ch, w):
            add(part_name(part), dx, dy)
    return _union(raw)


@lru_cache(maxsize=None)
def _composite_names() -> dict[str, str]:
    return {glyph_name(ch): ch for ch in list(ext.COMPOSITES) + list(ext.COMPOUNDS) + list(ext.COMBINING)}


def composite_char(name: str) -> str | None:
    """Return the char of a composite glyph, or None for a drawn glyph."""
    return _composite_names().get(name)


def draw_contours(glyph, contours) -> None:
    pen = glyph.getPen()
    for c in contours:
        # Start each contour at its lowest-left point for stable output.
        start = min(range(len(c)), key=lambda i: (c[i][1], c[i][0]))
        c = c[start:] + c[:start]
        pen.moveTo(c[0])
        for pt in c[1:]:
            pen.lineTo(pt)
        pen.closePath()


def build_static(wght: float, style: str) -> ufoLib2.Font:
    """Return one static instance at FRAG 0 (overlaps removed)."""
    font = ufoLib2.Font()
    _set_info(font, wght, style, static=True)
    order = [n for n in glyph_order() if n not in ext.ACCENTS]
    font.lib["public.glyphOrder"] = order
    for name in order:
        g = font.newGlyph(name)
        g.width = advance(name)
        if name != "space":
            draw_contours(g, static_contours(name, wght))
    font["space"].unicodes = [0x20, 0xA0]
    for ch in CHARS:
        font[glyph_name(ch)].unicodes = [ord(ch)]
    add_mark_anchors(font, data.stroke_width(wght))
    return font


# --------------------------------------------------------- designspace

def master_name(wght: float, frag: float) -> str:
    return f"Weft-w{int(wght)}-f{int(frag)}"


def build_designspace(master_dir: Path, masters: dict) -> DesignSpaceDocument:
    doc = DesignSpaceDocument()
    wght = AxisDescriptor()
    wght.tag, wght.name = "wght", "Weight"
    wght.minimum, wght.default, wght.maximum = 100, 400, 900
    wght.axisLabels = [
        AxisLabelDescriptor(name=n, userValue=v, elidable=(v == 400),
                            linkedUserValue=(700 if v == 400 else None))
        for v, n in STATICS
    ]
    frag = AxisDescriptor()
    frag.tag, frag.name = "FRAG", "Fragmentation"
    frag.minimum, frag.default, frag.maximum = 0, 0, 100
    frag.axisLabels = [
        AxisLabelDescriptor(name=n, userValue=v, elidable=(v == 0))
        for v, n in FRAG_NAMES
    ]
    doc.addAxis(wght)
    doc.addAxis(frag)
    # Masters: the masters from the generator, rounded points, same
    # structure. The variable font keeps the overlaps.
    for (wv, fv), path in masters.items():
        s = SourceDescriptor()
        s.path = str(path)
        s.filename = str(path.relative_to(master_dir.parent))
        s.name = master_name(wv, fv)
        s.familyName = FAMILY
        s.styleName = f"w{wv} f{fv}"
        s.location = {"Weight": wv, "Fragmentation": fv}
        doc.addSource(s)
    for wv, style in STATICS:
        inst = InstanceDescriptor()
        inst.familyName = FAMILY
        inst.styleName = style
        inst.name = f"{FAMILY} {style}"
        inst.postScriptFontName = f"{PS_FAMILY}-{style}"
        inst.location = {"Weight": wv, "Fragmentation": 0}
        doc.addInstance(inst)
    doc.lib["com.github.googlei18n.ufo2ft.featureWriters"] = FEATURE_WRITERS
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Weft UFO sources.")
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
    fonts = {(wv, fv): build_master(wv, fv) for wv in WGHT_MASTERS for fv in FRAG_MASTERS}
    statics = {} if args.no_static else {s: build_static(wv, s) for wv, s in STATICS}
    # One set of win metrics for the variable font and all statics. The
    # masters cover every location, so their bounds cover the statics.
    metrics = win_metrics(fonts.values())
    set_win_metrics(list(fonts.values()) + list(statics.values()), metrics)
    masters = {}
    for (wv, fv), font in fonts.items():
        path = master_dir / f"{master_name(wv, fv)}.ufo"
        font.save(path, overwrite=True)
        masters[(wv, fv)] = path
    doc = build_designspace(master_dir, masters)
    doc.write(out / "Weft.designspace")
    print(f"Wrote {len(masters)} masters and {out / 'Weft.designspace'}.")
    for style, font in statics.items():
        font.save(static_dir / f"{PS_FAMILY}-{style}.ufo", overwrite=True)
    if statics:
        print(f"Wrote {len(statics)} static UFOs to {static_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
