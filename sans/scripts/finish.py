"""Finish the fonts that gftools builder made.

Usage:
    python sans/scripts/finish.py BUILD_OUT_DIR FONTS_DIR

BUILD_OUT_DIR has variable/, ttf/ and otf/ from gftools builder.
FONTS_DIR (fonts/sans) receives variable/, ttf/, otf/ and webfonts/.

Changes:
- PostScript names: use "MachineMadeSans" (no hyphen) in name IDs 3, 6
  and 25 and in the fvar instance PostScript names. gftools makes them
  from the family name, which has a hyphen.
- OS/2 fsSelection: set the WWS bit. The family has only weight and
  slope, so the names are WWS-conformant.
- OTF: remove the "prep" table. It is TrueType hinting data and has no
  function in a CFF font. Subroutinize the CFF again with cffsubr:
  otfautohint writes the hinted charstrings with fewer subroutines,
  and the files would be twice as large.
- Static fonts: add a STAT table (wght and ital axis values).
- Italic variable font: shorter fvar instance names where "machine-made
  Sans" plus the style name is longer than 32 characters (some versions
  of Microsoft Word shape accents wrongly with longer names). The STAT
  table still names every axis value in full (ExtraLight, SemiBold,
  ExtraBold, Italic), and the static fonts keep the full names.
- Variable fonts: write WOFF2 copies to webfonts/.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import cffsubr
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont

BAD_PS = "machine-madeSans"
GOOD_PS = "MachineMadeSans"
WWS_BIT = 1 << 8

WEIGHTS = {
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
}


# Family name plus instance style name must fit in 32 characters.
MAX_INSTANCE_NAME = 32
SHORT_STYLES = {
    "ExtraLight Italic": "XLight Italic",
    "SemiBold Italic": "SemiBd Italic",
    "ExtraBold Italic": "XBold Italic",
}


class FinishError(Exception):
    pass


def fix_ps_names(font: TTFont) -> None:
    name = font["name"]
    for rec in name.names:
        if rec.nameID in (3, 6, 25) or (rec.nameID > 255 and BAD_PS in rec.toUnicode()):
            text = rec.toUnicode()
            if BAD_PS in text:
                name.setName(text.replace(BAD_PS, GOOD_PS), rec.nameID, rec.platformID, rec.platEncID, rec.langID)
    for rec in name.names:
        if BAD_PS in rec.toUnicode() or "-" in rec.toUnicode() and rec.nameID == 25:
            raise FinishError(f"Name ID {rec.nameID} still has a bad PostScript name: {rec.toUnicode()!r}")


def set_wws(font: TTFont) -> None:
    font["OS/2"].fsSelection |= WWS_BIT


def style_of(path: Path) -> tuple[str, bool]:
    style = path.stem.split("-", 1)[1]
    italic = style.endswith("Italic")
    weight = style[: -len("Italic")] if italic else style
    return (weight or "Regular"), italic


def add_static_stat(font: TTFont, path: Path) -> None:
    weight, italic = style_of(path)
    if weight not in WEIGHTS:
        raise FinishError(f"{path.name}: unknown weight {weight}.")
    w = WEIGHTS[weight]
    wght_value = {"value": w, "name": weight}
    if weight == "Regular":
        wght_value["flags"] = 0x2
        wght_value["linkedValue"] = 700
    if italic:
        ital_value = {"value": 1, "name": "Italic"}
    else:
        ital_value = {"value": 0, "name": "Roman", "flags": 0x2, "linkedValue": 1}
    axes = [
        {"tag": "wght", "name": "Weight", "values": [wght_value]},
        {"tag": "ital", "name": "Italic", "values": [ital_value]},
    ]
    buildStatTable(font, axes, elidedFallbackName=2, macNames=False)


def shorten_instance_names(font: TTFont) -> None:
    name = font["name"]
    family = name.getDebugName(16) or name.getDebugName(1)
    used_elsewhere = set()
    if "STAT" in font:
        stat = font["STAT"].table
        used_elsewhere.add(stat.ElidedFallbackNameID)
        for axis in stat.DesignAxisRecord.Axis:
            used_elsewhere.add(axis.AxisNameID)
        for value in stat.AxisValueArray.AxisValue if stat.AxisValueArray else []:
            used_elsewhere.add(value.ValueNameID)
    for inst in font["fvar"].instances:
        style = name.getDebugName(inst.subfamilyNameID)
        if len(f"{family} {style}") <= MAX_INSTANCE_NAME:
            continue
        if style not in SHORT_STYLES:
            raise FinishError(f"Instance name {family} {style} is too long and has no short form.")
        if inst.subfamilyNameID in used_elsewhere or inst.subfamilyNameID < 256:
            raise FinishError(f"Name ID {inst.subfamilyNameID} ({style}) is shared; cannot rename.")
        for rec in name.names:
            if rec.nameID == inst.subfamilyNameID:
                name.setName(SHORT_STYLES[style], rec.nameID, rec.platformID, rec.platEncID, rec.langID)


def finish_file(src: Path, dst: Path, kind: str) -> None:
    font = TTFont(src)
    fix_ps_names(font)
    set_wws(font)
    if kind == "variable":
        shorten_instance_names(font)
    if kind == "otf" and "prep" in font:
        del font["prep"]
    if kind == "otf":
        cffsubr.subroutinize(font)
    if kind in ("ttf", "otf"):
        add_static_stat(font, src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    font.save(dst)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("build_out", type=Path)
    ap.add_argument("fonts_dir", type=Path)
    args = ap.parse_args(argv)
    for sub in ("variable", "ttf", "otf", "webfonts"):
        d = args.fonts_dir / sub
        if d.exists():
            shutil.rmtree(d)
    count = 0
    try:
        for kind, pattern in (("variable", "*.ttf"), ("ttf", "*.ttf"), ("otf", "*.otf")):
            files = sorted((args.build_out / kind).glob(pattern))
            if not files:
                raise FinishError(f"No {pattern} files in {args.build_out / kind}.")
            for src in files:
                finish_file(src, args.fonts_dir / kind / src.name, kind)
                count += 1
        for vf in sorted((args.fonts_dir / "variable").glob("*.ttf")):
            font = TTFont(vf)
            font.flavor = "woff2"
            out = args.fonts_dir / "webfonts" / (vf.stem + ".woff2")
            out.parent.mkdir(parents=True, exist_ok=True)
            font.save(out)
            count += 1
    except FinishError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Finished {count} files in {args.fonts_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
