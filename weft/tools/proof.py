"""Render the Weft proof sheets from the compiled variable font.

Usage:
    python tools/proof.py [--font VF.ttf] [--out-dir ../proofs/weft]
                          [--before OLD_VF.ttf]

Writes these PNGs (FreeType through Pillow; Raqm/HarfBuzz for the lines
that need OpenType features or mark positioning):

    weft-charset.png           every encoded character, wght 400 and 900, FRAG 0
    weft-weight-waterfall.png  wght 100 to 900, FRAG 0
    weft-frag-waterfall.png    FRAG 0 to 100 at wght 400 and 900
    weft-designspace.png       a 5 x 5 grid over wght and FRAG
    weft-body-text.png         body text at 16 to 24 px (FRAG 0 and 15)
    weft-lookalikes.png        Il1| O0o rn/m cl/d 5S 2Z B8 g9q, ss01
    weft-accents.png           Latin Extended-A, Romanian, combining marks
    weft-code.png              box drawing, arrows and a code sample

With --before (the previous release, for example from
`git show weft-v0.1.0:"fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf"`):

    weft-before-after-lookalikes.png  look-alikes, previous release and now
    weft-before-after-black.png       accents and guillemets at wght 900
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build  # noqa: E402

VERSION = f"{build.VERSION[0]}.{build.VERSION[1] // 100}"

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
LOOKALIKES = "Il1| O0o rn m cl d 5S 2Z B8 g9q"


def font_at(path: str, size: int, wght: float, frag: float, *, raqm: bool = False) -> ImageFont.FreeTypeFont:
    engine = ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC
    font = ImageFont.truetype(path, size, layout_engine=engine)
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

    def line(self, s: str, font: ImageFont.FreeTypeFont, size: int, note: str = "",
             features: list[str] | None = None, tall: bool = False) -> None:
        # tall: room for the accents above capitals and the marks below.
        top = round(size * (0.55 if tall else 0.0))
        h = round(size * (1.25 + (0.85 if tall else 0.0))) + 8
        img = Image.new("L", (WIDTH, h), PAPER)
        d = ImageDraw.Draw(img)
        x = PAD
        if note:
            d.text((PAD, h // 2 - 8), note, font=label_font(14), fill=MUTED)
            x = PAD + 150
        d.text((x, top + round(size * 0.95) + 4), s, font=font, fill=INK, anchor="ls",
               features=features)
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
    sheet = Sheet(f"machine-made Weft {VERSION}: full character set ({len(build.charset()) - 1} characters, {len(build.ext.COMBINING)} of them combining marks), wght 400, FRAG 0")
    marks = set(build.ext.COMBINING)
    chars = [c for c in build.charset() if not c.isspace() and c not in marks]
    size, cols = 44, 32
    font = font_at(vf, size, 400, 0)
    for i in range(0, len(chars), cols):
        sheet.line("".join(chars[i:i + cols]), font, size, tall=True)
    sheet.text("Combining marks after o (mark feature): " + " ".join(f"U+{ord(c):04X}" for c in sorted(marks)), 14)
    sheet.line("  ".join("o" + c for c in sorted(marks)), font_at(vf, size, 400, 0, raqm=True), size, tall=True)
    sheet.gap()
    sheet.text("Same set at wght 900")
    font = font_at(vf, size, 900, 0)
    for i in range(0, len(chars), cols):
        sheet.line("".join(chars[i:i + cols]), font, size, tall=True)
    sheet.save(out)


def weight_waterfall(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: weight waterfall, FRAG 0 (the nine static instances)")
    for wght, style in build.STATICS:
        sheet.line("Weft 0042 Hamburgefonstiv", font_at(vf, 56, wght, 0), 56, f"{wght} {style}")
    sheet.save(out)


def frag_waterfall(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: FRAG waterfall (0 Clean, 15 Notched, 50 Cut, 100 Broken)")
    for wght in (400, 900):
        sheet.text(f"wght {wght}")
        for frag in (0, 8, 15, 30, 50, 62, 80, 100):
            sheet.line("Weft 0042 machine", font_at(vf, 64, wght, frag), 64, f"FRAG {frag}")
        sheet.gap()
    sheet.save(out)


def body_text(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: body text, wght 400, at FRAG 0 (left) and FRAG 15 (right)")
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
    sheet = Sheet(f"machine-made Weft {VERSION}: look-alike pairs")
    for frag in (0, 15):
        for wght in (400, 700):
            sheet.line(LOOKALIKES, font_at(vf, 52, wght, frag), 52, f"wght {wght} FRAG {frag}")
    sheet.line(LOOKALIKES, font_at(vf, 52, 400, 0, raqm=True), 52, "ss01 (dotted 0)", features=["ss01"])
    for frag in (0, 15):
        sheet.line(LOOKALIKES, font_at(vf, 20, 400, frag), 20, f"20 px FRAG {frag}")
    sheet.line("ID 0O1lI-8B5S-2Z9gq  l1I|  O0o0O  rnm  cld", font_at(vf, 16, 400, 0), 16, "16 px serial")
    sheet.save(out)


ACCENT_LINES = [
    "ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģ",
    "ĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇň",
    "ŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪū",
    "ŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽžſȘșȚțẞǾǿ",
]
SAMPLES = [
    "Łódź, Gdańsk, Częstochowa · Plzeň, Ústí, Žďár · Ľubica, Ťahanovce",
    "Győr, Kőszeg, Hódmezővásárhely · Iași, Timișoara, Brașov",
    "İstanbul, Muğla, Şanlıurfa · Rīga, Liepāja, Ķekava · Šiauliai, Kėdainiai",
]


def accents(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: Latin Extended-A, Romanian comma below, combining marks")
    for wght in (400, 900):
        sheet.text(f"wght {wght}, FRAG 0")
        for line in ACCENT_LINES:
            sheet.line(line, font_at(vf, 44, wght, 0), 44, tall=True)
    sheet.text("Place names, wght 400 and 700, 28 px")
    for wght in (400, 700):
        for line in SAMPLES:
            sheet.line(line, font_at(vf, 28, wght, 0), 28, tall=True)
    sheet.text("Combining marks (decomposed text, mark feature): precomposed | base + mark")
    pairs = ["Á", "Č", "Ő", "Ș", "Ą", "ň", "ű", "ș", "ţ", "ę", "í"]
    import unicodedata
    for wght in (400, 900):
        text = "  ".join(f"{c}{unicodedata.normalize('NFD', c)}" for c in pairs)
        text += "  j\u030C i\u0308"
        sheet.line(text, font_at(vf, 36, wght, 0, raqm=True), 36, f"wght {wght}", tall=True)
    sheet.save(out)


BOX = [
    "┌──────┬──────┐",
    "│ wght │ FRAG │",
    "├──────┼──────┤",
    "│ 400  │  15  │",
    "└──────┴──────┘",
]
CODE = [
    "if (a ≠ b) { x ← f(0O1lI); }  // ← → ↑ ↓",
    "let total = price × qty ÷ 2 − 5 ± 1;  £ ¥ € ¢ § ¶",
    "«guillemets» ‹single› „low“ ‚low‘ ½ ¼ ¾",
]


def code(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: box drawing, arrows and symbols")
    for wght in (100, 400, 900):
        sheet.text(f"wght {wght}, line height = typo ascender + descender (1188 units)")
        size = 40
        font = font_at(vf, size, wght, 0)
        step = round(size * 1.188)
        img = Image.new("L", (WIDTH, step * len(BOX) + 16), PAPER)
        d = ImageDraw.Draw(img)
        asc = round(size * 0.906)
        for i, line in enumerate(BOX):
            d.text((PAD, 8 + asc + i * step), line, font=font, fill=INK, anchor="ls")
        sheet.blocks.append(img)
        for line in CODE:
            sheet.line(line.replace(" ≠ ", " != "), font_at(vf, 32, wght, 0), 32, tall=True)
    sheet.save(out)


def designspace(vf: str, out: Path) -> None:
    sheet = Sheet(f"machine-made Weft {VERSION}: designspace, 5 x 5 (wght across, FRAG down)")
    wghts = (100, 300, 500, 700, 900)
    frags = (0, 15, 40, 70, 100)
    size = 56
    cell = (WIDTH - PAD * 2 - 120) // len(wghts)
    head = Image.new("L", (WIDTH, 28), PAPER)
    d = ImageDraw.Draw(head)
    for i, wg in enumerate(wghts):
        d.text((PAD + 120 + i * cell, 4), f"wght {wg}", font=label_font(16), fill=MUTED)
    sheet.blocks.append(head)
    for fr in frags:
        img = Image.new("L", (WIDTH, round(size * 1.3)), PAPER)
        d = ImageDraw.Draw(img)
        d.text((PAD, size // 2), f"FRAG {fr}", font=label_font(16), fill=MUTED)
        for i, wg in enumerate(wghts):
            d.text((PAD + 120 + i * cell, round(size * 1.05)), "Ąg0R", font=font_at(vf, size, wg, fr),
                   fill=INK, anchor="ls")
        sheet.blocks.append(img)
    sheet.save(out)


def before_after(vf: str, before: str, out_dir: Path) -> None:
    sheet = Sheet(f"machine-made Weft: look-alikes, previous release (top) and {VERSION} (bottom)")
    for label, path in (("before", before), (VERSION, vf)):
        for wght in (400, 700):
            sheet.line(LOOKALIKES, font_at(path, 52, wght, 0), 52, f"{label} wght {wght}")
        sheet.line(LOOKALIKES, font_at(path, 20, 400, 0), 20, f"{label} 20 px")
        sheet.gap(8)
    sheet.save(out_dir / "weft-before-after-lookalikes.png")
    sheet = Sheet(f"machine-made Weft: wght 900, previous release (top) and {VERSION} (bottom)")
    text = "ÀÉÎÕÜÅÑ «»“”\"  ÿåñ"
    for label, path in (("before", before), (VERSION, vf)):
        sheet.line(text, font_at(path, 64, 900, 0), 64, f"{label} 900", tall=True)
        sheet.line(text, font_at(path, 64, 700, 0), 64, f"{label} 700", tall=True)
    sheet.save(out_dir / "weft-before-after-black.png")





def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Weft proof sheets.")
    ap.add_argument("--font", default="../fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf")
    ap.add_argument("--out-dir", default="../proofs/weft")
    ap.add_argument("--before", help="The variable font of the previous release (before/after proofs).")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    charset(args.font, out / "weft-charset.png")
    weight_waterfall(args.font, out / "weft-weight-waterfall.png")
    frag_waterfall(args.font, out / "weft-frag-waterfall.png")
    designspace(args.font, out / "weft-designspace.png")
    body_text(args.font, out / "weft-body-text.png")
    lookalikes(args.font, out / "weft-lookalikes.png")
    accents(args.font, out / "weft-accents.png")
    code(args.font, out / "weft-code.png")
    if args.before:
        before_after(args.font, args.before, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
