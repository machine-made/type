"""Compare two machine-made Sans builds.

Usage:
    python sans/scripts/compare_builds.py COMMITTED_DIR NEW_DIR

Both directories have variable/, ttf/, otf/ and webfonts/. The builds
are not byte-identical between machines, so this compares what matters:
the file set, glyph order, cmap, name table strings (without the
version string), line metrics, advance widths and outlines at the
default location. Exit status is 1 on a difference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.pens.hashPointPen import HashPointPen
from fontTools.ttLib import TTFont

SKIP_NAMES = {5}  # Version string can carry tool versions.


def summary(path: Path) -> dict:
    font = TTFont(path)
    gs = font.getGlyphSet()
    hashes = {}
    for name in font.getGlyphOrder():
        pen = HashPointPen(gs[name].width, gs)
        gs[name].drawPoints(pen)
        hashes[name] = pen.hash
    names = sorted(
        (r.nameID, r.platformID, r.langID, r.toUnicode()) for r in font["name"].names if r.nameID not in SKIP_NAMES
    )
    os2, hhea = font["OS/2"], font["hhea"]
    return {
        "order": font.getGlyphOrder(),
        "cmap": font.getBestCmap(),
        "names": names,
        "metrics": (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap, hhea.ascent, hhea.descent, hhea.lineGap, os2.usWinAscent, os2.usWinDescent, os2.fsSelection),
        "glyphs": hashes,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("committed", type=Path)
    ap.add_argument("new", type=Path)
    args = ap.parse_args(argv)
    a = {p.relative_to(args.committed) for p in args.committed.rglob("*") if p.is_file()}
    b = {p.relative_to(args.new) for p in args.new.rglob("*") if p.is_file()}
    errors = []
    if a != b:
        errors.append(f"File sets differ. Only committed: {sorted(map(str, a - b))}. Only new: {sorted(map(str, b - a))}.")
    for rel in sorted(a & b):
        sa, sb = summary(args.committed / rel), summary(args.new / rel)
        for key in sa:
            if sa[key] != sb[key]:
                if key == "glyphs":
                    diff = sorted(n for n in sa[key] if sa[key].get(n) != sb[key].get(n))
                    errors.append(f"{rel}: outlines or widths differ in {len(diff)} glyphs: {diff[:10]}")
                else:
                    errors.append(f"{rel}: {key} differs.")
    if errors:
        print("error: the build does not match the committed fonts. Run sans/scripts/build.sh and commit fonts/sans.", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"The build matches the committed fonts ({len(a)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
