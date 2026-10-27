"""Finish the compiled Warp fonts.

Usage:
    python tools/finish.py --static FONT.ttf FONT.otf ...
    python tools/finish.py --woff2 FONT.ttf ... [--woff2-dir DIR]

--static: add a STAT table that names the position of the static on the
    wght, ital and opsz axes (one value per axis, as the OpenType spec
    shows for static fonts). Text styles sit at opsz 10, Display at 60.
--woff2: write a WOFF2 copy.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom.build import DISPLAY_OPSZ, PS_DISPLAY, TEXT_OPSZ  # noqa: E402


def finish_static(path: Path) -> None:
    font = TTFont(path)
    wght = font["OS/2"].usWeightClass
    italic = bool(font["OS/2"].fsSelection & 1)
    ps = font["name"].getDebugName(6) or ""
    display = ps.startswith(PS_DISPLAY + "-")
    w = {"value": wght, "name": "Bold" if wght == 700 else "Regular", "flags": 0x2 if wght == 400 else 0}
    if wght == 400:
        w["linkedValue"] = 700
    i = {"value": 1 if italic else 0, "name": "Italic" if italic else "Roman", "flags": 0 if italic else 0x2}
    if not italic:
        i["linkedValue"] = 1
    o = {"value": DISPLAY_OPSZ if display else TEXT_OPSZ, "name": "Display" if display else "Text",
         "flags": 0 if display else 0x2}
    axes = [
        {"tag": "wght", "name": "Weight", "values": [w]},
        {"tag": "opsz", "name": "Optical size", "values": [o]},
        {"tag": "ital", "name": "Italic", "values": [i]},
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
    ap = argparse.ArgumentParser(description="Finish the compiled Warp fonts.")
    ap.add_argument("--static", nargs="*", default=[], type=Path)
    ap.add_argument("--woff2", nargs="*", default=[], type=Path)
    ap.add_argument("--woff2-dir", type=Path, help="Output folder for WOFF2 files.")
    args = ap.parse_args(argv)
    if not (args.static or args.woff2):
        ap.error("Give at least one font file.")
    for p in args.static:
        finish_static(p)
    for p in args.woff2:
        write_woff2(p, args.woff2_dir or p.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
