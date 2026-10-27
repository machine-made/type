"""Finish the compiled Heddle fonts.

Usage:
    python tools/finish.py --variable FONT.ttf
    python tools/finish.py --static FONT.ttf ...
    python tools/finish.py --woff2 FONT.ttf ... [--woff2-dir DIR]

--variable: set the OVERLAP_SIMPLE flag on every simple glyph and the
    OVERLAP_COMPOUND flag on every composite. The primitives overlap on
    purpose, and some rasterizers need the flag.
--static: add a STAT table that names the position of the static on the
    wght and wdth axes (one value per axis, as the OpenType spec shows
    for static fonts).
--woff2: write a WOFF2 copy.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import OVERLAP_COMPOUND, flagOverlapSimple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom.build import WEIGHT_NAME, WIDTHS  # noqa: E402

WIDTH_BY_CLASS = {c: (v, n) for v, n, c in WIDTHS}


def finish_variable(path: Path) -> None:
    font = TTFont(path)
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.isComposite():
            g.components[0].flags |= OVERLAP_COMPOUND
        elif g.numberOfContours > 0:
            g.flags[0] |= flagOverlapSimple
    font.save(path)
    print(f"Set the overlap flags in {path}.")


def finish_static(path: Path) -> None:
    font = TTFont(path)
    wght = font["OS/2"].usWeightClass
    wdth, wdth_name = WIDTH_BY_CLASS[font["OS/2"].usWidthClass]
    w = {"value": wght, "name": WEIGHT_NAME[wght], "flags": 0x2 if wght == 400 else 0}
    if wght == 400:
        w["linkedValue"] = 700
    d = {"value": wdth, "name": wdth_name, "flags": 0x2 if wdth == 100 else 0}
    axes = [
        {"tag": "wght", "name": "Weight", "values": [w]},
        {"tag": "wdth", "name": "Width", "values": [d]},
    ]
    buildStatTable(font, axes, elidedFallbackName=2, macNames=False)
    font.save(path)
    print(f"Added STAT to {path}.")


def write_woff2(path: Path, out_dir: Path) -> None:
    font = TTFont(path)
    font.flavor = "woff2"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (path.stem + ".woff2")
    font.save(out)
    print(f"Wrote {out}.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Finish the compiled Heddle fonts.")
    ap.add_argument("--variable", nargs="*", default=[], type=Path)
    ap.add_argument("--static", nargs="*", default=[], type=Path)
    ap.add_argument("--woff2", nargs="*", default=[], type=Path)
    ap.add_argument("--woff2-dir", type=Path, help="Output folder for WOFF2 files.")
    args = ap.parse_args(argv)
    if not (args.variable or args.static or args.woff2):
        ap.error("Give at least one font file.")
    for p in args.variable:
        finish_variable(p)
    for p in args.static:
        finish_static(p)
    for p in args.woff2:
        write_woff2(p, args.woff2_dir or p.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
