"""Build the Weft phase 1 UFO master from the stroke table.

Usage:
    python -m loom.build [--out master/Weft-Regular.ufo] [--wght 400]

Phase 1 scope: one master, wght 400, FRAG 0, Solid style.
Glyphs: .notdef, space, a-z, A-Z, 0-9.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pathops
import ufoLib2

from loom import glyphs as data
from loom.outline import clean_contour, glyph_outline, path_contours

UPM = 1000
# 1 design unit = 62.5 font units. The 16-unit em is 1000 and the
# 12-unit advance is 750.
SCALE = UPM / data.METRICS["units_per_em"]
ADVANCE = round(data.METRICS["advance"] * SCALE)

FAMILY = "machine-made Weft"
PS_FAMILY = "MachineMadeWeft"
VERSION = (0, 100)  # 0.100: phase 1
COPYRIGHT = "Copyright 2026 The machine-made Weft Project Authors (https://github.com/machine-made/type)"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, "
    "Version 1.1. This license is available with a FAQ at: "
    "https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"

# Line metrics in design units. 14 + 4.5 = 18.5 units: the sketch sets
# lines at 18 to 19 units. The ascender leaves room for accents later.
TYPO_ASCENDER = 14
TYPO_DESCENDER = -4.5


def u(v: float) -> int:
    """Convert design units to font units (rounded)."""
    return round(v * SCALE)


def phase1_chars() -> str:
    return data.PHASE1_CHARS


def glyph_contours(strokes, wght: float = 400) -> list[list[tuple[int, int]]]:
    """Return the final integer contours for one glyph."""
    width = data.stroke_width(wght)
    path = glyph_outline(strokes, width, data.MITER_LIMIT, scale=SCALE,
                         dx=data.METRICS["box_offset"], dy=0.0)
    contours = [clean_contour(c) for c in path_contours(path)]
    contours = [c for c in contours if len(c) >= 3]
    # Rounding to the integer grid can make new overlaps. Union again and
    # round again until the result is stable.
    for _ in range(3):
        p = pathops.Path()
        pen = p.getPen()
        for c in contours:
            pen.moveTo(c[0])
            for pt in c[1:]:
                pen.lineTo(pt)
            pen.closePath()
        p.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
        new = [clean_contour(c) for c in path_contours(p)]
        new = [c for c in new if len(c) >= 3]
        if new == contours:
            break
        contours = new
    return contours


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


def build_font(wght: float = 400) -> ufoLib2.Font:
    font = ufoLib2.Font()
    info = font.info
    info.familyName = FAMILY
    info.styleName = "Regular"
    info.styleMapFamilyName = FAMILY
    info.styleMapStyleName = "regular"
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = COPYRIGHT
    info.openTypeNameLicense = LICENSE_DESCRIPTION
    info.openTypeNameLicenseURL = LICENSE_URL
    info.openTypeNameManufacturer = "machine-made"
    info.openTypeNameManufacturerURL = "https://github.com/machine-made"
    info.openTypeNameDesigner = "machine-made agents"
    info.openTypeNameDescription = (
        "Weft is a grid-built monospace by machine-made. "
        "Phase 1: one master, Regular, FRAG 0."
    )
    info.trademark = None
    info.postscriptFontName = f"{PS_FAMILY}-Regular"
    info.postscriptIsFixedPitch = True
    info.postscriptUnderlinePosition = u(-2.4)
    info.postscriptUnderlineThickness = round(data.stroke_width(wght) * SCALE)
    info.openTypeOS2VendorID = "NONE"
    info.openTypeOS2WeightClass = int(wght)
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2Type = []  # installable embedding
    # Bit 7: USE_TYPO_METRICS. Bit 8: WWS (the names are WWS-conformant).
    info.openTypeOS2Selection = [7, 8]
    # PANOSE: family 2 (Latin text), proportion 9 (monospaced). The
    # proportion is the fourth digit.
    info.openTypeOS2Panose = [2, 0, 0, 9, 0, 0, 0, 0, 0, 0]
    info.openTypeOS2UnicodeRanges = [0]  # Basic Latin
    info.openTypeOS2CodePageRanges = [0]  # Latin 1

    info.unitsPerEm = UPM
    info.xHeight = u(data.METRICS["x_height"])
    info.capHeight = u(data.METRICS["cap_height"])
    info.ascender = u(data.METRICS["ascender"])
    info.descender = u(data.METRICS["descender"])
    info.italicAngle = 0

    font.glyphOrder = [".notdef", "space"] + [data.glyph_name(c) for c in phase1_chars()]

    g = font.newGlyph(".notdef")
    g.width = ADVANCE
    draw_contours(g, glyph_contours(data.NOTDEF, wght))

    g = font.newGlyph("space")
    g.width = ADVANCE
    g.unicodes = [0x20, 0xA0]  # space and no-break space

    for ch in phase1_chars():
        g = font.newGlyph(data.glyph_name(ch))
        g.width = ADVANCE
        g.unicodes = [ord(ch)]
        draw_contours(g, glyph_contours(data.STROKES[ch], wght))

    # Vertical metrics. hhea and typo match; win covers every glyph.
    y_min = 0
    y_max = 0
    for glyph in font:
        b = glyph.getBounds(font)
        if b is not None:
            y_min = min(y_min, b.yMin)
            y_max = max(y_max, b.yMax)
    asc, desc = u(TYPO_ASCENDER), u(TYPO_DESCENDER)
    info.openTypeOS2TypoAscender = asc
    info.openTypeOS2TypoDescender = desc
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = asc
    info.openTypeHheaDescender = desc
    info.openTypeHheaLineGap = 0
    info.openTypeOS2WinAscent = max(asc, math.ceil(y_max))
    info.openTypeOS2WinDescent = max(-desc, math.ceil(-y_min))

    font.lib["public.postscriptNames"] = {}
    return font


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Weft UFO master.")
    ap.add_argument("--out", default="master/Weft-Regular.ufo")
    ap.add_argument("--wght", type=float, default=400)
    args = ap.parse_args(argv)
    font = build_font(args.wght)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out, overwrite=True)
    print(f"Wrote {out} ({len(font)} glyphs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
