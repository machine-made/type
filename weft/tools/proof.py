"""Render the Weft 0.1 proof sheets from the compiled variable font.

Usage:
    python tools/proof.py [--font VF.ttf] [--out-dir ../proofs/weft]

Writes five PNGs (FreeType through Pillow, no sketch code):

    weft-charset.png         every encoded character, wght 400, FRAG 0
    weft-weight-waterfall.png  wght 100 to 900, FRAG 0
    weft-frag-waterfall.png    FRAG 0 to 100 at wght 400 and 900
    weft-body-text.png         body text at 16, 18, 20, 22, 24 px (FRAG 0 and 15)
    weft-lookalikes.png        Il1| O0 rn/m cl/d 5S 2Z B8 g9 at FRAG 0 and 15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build  # noqa: E402

PAPER = 244
INK = 18
MUTED = 110
WIDTH = 1600
PAD = 32

BODY = (
    "Every result a machine hands you has been checked by another machine. "
    "Weft is set on a grid by code, compiled by fontmake and checked on every "
    "pull request: 1,204 of 1,204 glyph tests pass. Façade, naïve, Øresund, "
    "São Paulo, Zürich, 25 °C, 3/4 cup, «quotes» and “quotes” — all in one face."
)
LOOKALIKES = "Il1| O0 rn m cl d 5S 2Z B8 g9"


def font_at(path: str, size: int, wght: float, frag: float) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(path, size)
    names = [a["name"] if isinstance(a["name"], str) else a["name"].decode()
             for a in font.get_variation_axes()]
    values = {"Weight": wght, "Fragmentation": frag}
    font.set_variation_by_axes([values[n] for n in names])
    return font


def label_font(size: int = 18) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size)


class Sheet:
    def __init__(self, title: str):
        self.blocks: list[Image.Image] = []
        self.text(title, 26)

    def text(self, s: str, size: int = 18, fill: int = MUTED) -> None:
        img = Image.new("L", (WIDTH, size + 14), PAPER)
        ImageDraw.Draw(img).text((PAD, 4), s, font=label_font(size), fill=fill)
        self.blocks.append(img)

    def line(self, s: str, font: ImageFont.FreeTypeFont, size: int, note: str = "") -> None:
        h = round(size * 1.25) + 8
        img = Image.new("L", (WIDTH, h), PAPER)
        d = ImageDraw.Draw(img)
        x = PAD
        if note:
            d.text((PAD, h // 2 - 8), note, font=label_font(14), fill=MUTED)
            x = PAD + 150
        d.text((x, round(size * 0.95) + 4), s, font=font, fill=INK, anchor="ls")
        self.blocks.append(img)

    def gap(self, h: int = 16) -> None:
        self.blocks.append(Image.new("L", (WIDTH, h), PAPER))

    def save(self, path: Path) -> None:
        h = sum(b.height for b in self.blocks) + PAD
        out = Image.new("L", (WIDTH, h), PAPER)
        y = PAD // 2
        for b in self.blocks:
            out.paste(b, (0, y))
            y += b.height
        out.save(path)
        print(f"Wrote {path}.")


def wrap(text: str, cols: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > cols:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    return lines + [line] if line else lines


def charset(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft 0.1: full character set ({len(build.charset()) - 1} characters), wght 400, FRAG 0")
    chars = [c for c in build.charset() if c not in "  "]
    size, cols = 48, 32
    font = font_at(vf, size, 400, 0)
    for i in range(0, len(chars), cols):
        sheet.line("".join(chars[i:i + cols]), font, size)
    sheet.gap()
    sheet.text("Same set at wght 900")
    font = font_at(vf, size, 900, 0)
    for i in range(0, len(chars), cols):
        sheet.line("".join(chars[i:i + cols]), font, size)
    sheet.save(out)


def weight_waterfall(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Weft 0.1: weight waterfall, FRAG 0 (the nine static instances)")
    for wght, style in build.STATICS:
        sheet.line("Weft 0042 Hamburgefonstiv", font_at(vf, 56, wght, 0), 56, f"{wght} {style}")
    sheet.save(out)


def frag_waterfall(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Weft 0.1: FRAG waterfall (0 Clean, 15 Notched, 50 Cut, 100 Broken)")
    for wght in (400, 900):
        sheet.text(f"wght {wght}")
        for frag in (0, 8, 15, 30, 50, 62, 80, 100):
            sheet.line("Weft 0042 machine", font_at(vf, 64, wght, frag), 64, f"FRAG {frag}")
        sheet.gap()
    sheet.save(out)


def body_text(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Weft 0.1: body text, wght 400, at FRAG 0 (left) and FRAG 15 (right)")
    half = WIDTH // 2
    for size in (16, 18, 20, 22, 24):
        sheet.text(f"{size} px")
        cols = int((half - PAD - 20) / (size * 0.75))
        lines = wrap(BODY, cols)
        step = round(size * 1.45)
        img = Image.new("L", (WIDTH, step * len(lines) + 8), PAPER)
        d = ImageDraw.Draw(img)
        for col, frag in enumerate((0, 15)):
            font = font_at(vf, size, 400, frag)
            for i, line in enumerate(lines):
                d.text((PAD + col * half, size + i * step), line, font=font, fill=INK, anchor="ls")
        sheet.blocks.append(img)
        sheet.gap(10)
    sheet.save(out)


def lookalikes(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Weft 0.1: look-alike pairs")
    for frag in (0, 15):
        for wght in (400, 700):
            sheet.line(LOOKALIKES, font_at(vf, 52, wght, frag), 52, f"wght {wght} FRAG {frag}")
    for frag in (0, 15):
        sheet.line(LOOKALIKES, font_at(vf, 20, 400, frag), 20, f"20 px FRAG {frag}")
    sheet.save(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Weft proof sheets.")
    ap.add_argument("--font", default="../fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf")
    ap.add_argument("--out-dir", default="../proofs/weft")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    charset(args.font, out / "weft-charset.png")
    weight_waterfall(args.font, out / "weft-weight-waterfall.png")
    frag_waterfall(args.font, out / "weft-frag-waterfall.png")
    body_text(args.font, out / "weft-body-text.png")
    lookalikes(args.font, out / "weft-lookalikes.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
