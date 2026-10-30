"""Render the Heddle proof sheets from the compiled variable font.

Usage:
    python tools/proof.py [--font VF.ttf] [--out-dir ../proofs/heddle]

Writes (FreeType and Raqm through Pillow, no sketch code):

    heddle-charset.png           every encoded character at 3 locations
    heddle-weight-waterfall.png  wght 100 to 900 at wdth 100
    heddle-width-ladder.png      wdth 70 to 140 at wght 400 and 900
    heddle-designspace.png       a 5 x 5 grid over both axes (corners,
                                  edges, midpoints): checks interpolation
    heddle-kerning.png           kerned pairs, kerning off and on
    heddle-accents.png           accented letters, marks and symbols
    heddle-latin-ext.png         Latin Extended-A and Central European text
    heddle-symbols.png           0.2 symbols, fractions (frac off and on),
                                  the redrawn ß ð @ © ® %

With --before OLD_VF (for example Heddle 0.1 from git), it also writes
before/after sheets (old upper line, new lower line):

    heddle-before-after-accents.png   marks at Black and Regular
    heddle-before-after-counters.png  hooks and small rings at Black
    heddle-before-after-drift.png     the glyphs that drifted most near wdth 85

The sketch comparison is tools/sketch_compare.py (needs Chromium).

Apache-2.0.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build  # noqa: E402
from loom import glyphs  # noqa: E402

PAPER = 244
INK = 18
MUTED = 110
WIDTH = 1800
PAD = 32
NOTE_W = 190

KERN_LINES = [
    "AVATAR TAVERN WAVY LAYOUT",
    "To Ta Te Vo Va Wo Wa Yo Ya Po Pa Fo Fa",
    "LT LV LW LY AV AW AY AT OA OV OY",
    "T. V. W. Y. P. F, v. y, r. T- Y-",
    "vow eye yo ox ko to fo fa ro ra f. vv",
    "1958. 7. 3. 0. 7- 2027.",
]


def font_at(path: str, size: int, wght: float, wdth: float) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    names = [a["name"] if isinstance(a["name"], str) else a["name"].decode()
             for a in font.get_variation_axes()]
    values = {"Weight": wght, "Width": wdth}
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
             features: list[str] | None = None) -> None:
        h = round(size * 1.3) + 10
        img = Image.new("L", (WIDTH, h), PAPER)
        d = ImageDraw.Draw(img)
        x = PAD
        if note:
            d.text((PAD, h // 2 - 8), note, font=label_font(14), fill=MUTED)
            x = PAD + NOTE_W
        d.text((x, round(size * 0.98) + 4), s, font=font, fill=INK, anchor="ls", features=features)
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
        out.save(path, optimize=True)
        print(f"Wrote {path}.")


def encoded_chars() -> list[str]:
    return [chr(u) for u in sorted(glyphs.cmap()) if u not in (0x20, 0xA0)]


def charset(vf: str, out: Path) -> None:
    chars = encoded_chars()
    sheet = Sheet(f"machine-made Heddle 0.2: character set ({len(chars)} characters and the space)")
    size, cols = 52, 30
    for wght, wdth in ((400, 100), (900, 70), (100, 140)):
        sheet.text(f"wght {wght}, wdth {wdth}")
        font = font_at(vf, size if wdth < 140 else 44, wght, wdth)
        for i in range(0, len(chars), cols):
            sheet.line(" ".join(chars[i:i + cols]) if wdth == 140 else "".join(chars[i:i + cols]),
                       font, size)
        sheet.gap()
    sheet.save(out)


def weight_waterfall(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: weight waterfall at wdth 100 (the nine static weights)")
    for wght, style in build.WEIGHTS:
        sheet.line("Hamburgefonstiv 1958", font_at(vf, 80, wght, 100), 80, f"{wght} {style}")
    sheet.save(out)


def width_ladder(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: width ladder (wdth 70 to 140)")
    for wght in (400, 900):
        sheet.text(f"wght {wght}")
        for wdth, name, _ in build.WIDTHS:
            sheet.line("Grotesk 1958", font_at(vf, 88, wght, wdth), 88, f"{wdth} {name}")
        sheet.gap()
    sheet.save(out)


def designspace(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: designspace grid (masters at wght 100, 400, 700, 900 x wdth 70, 85, 100, 140)")
    for wdth in (70, 85, 105, 120, 140):
        sheet.text(f"wdth {wdth}")
        for wght in (100, 250, 550, 800, 900):
            sheet.line("Rag Sea 2025 Bow Kgy&", font_at(vf, 60, wght, wdth), 60, f"wght {wght}")
    sheet.save(out)


def kerning(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: kerning, off (upper line) and on (lower line), wght 700")
    for wdth in (70, 100, 140):
        sheet.text(f"wdth {wdth}")
        size = 64 if wdth < 140 else 50
        font = font_at(vf, size, 700, wdth)
        for s in KERN_LINES:
            sheet.line(s, font, size, "kern off", features=["-kern"])
            sheet.line(s, font, size, "kern on", features=["kern"])
        sheet.gap()
    sheet.save(out)


def accents(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: Latin-1 letters, marks and symbols")
    lines = [
        "ÀÁÂÃÄÅ ÇÈÉÊË ÌÍÎÏ ÑÒÓÔÕÖ ÙÚÛÜÝŸ",
        "àáâãäå çèéêë ìíîï ñòóôõö ùúûüýÿ",
        "ÆæŒœØøßÐðÞþı «Zürich» „São“ ‘Ås’",
        "€1958 © ® 25° 3·4 • … — ¡Olé! ¿Qué?",
        "#hash $25 %50 &co @mm *(x) [y] {z} <=+> ^~_ |\\",
    ]
    for wght, wdth in ((400, 100), (900, 85)):
        sheet.text(f"wght {wght}, wdth {wdth}")
        font = font_at(vf, 60, wght, wdth)
        for s in lines:
            sheet.line(s, font, 60)
        sheet.gap()
    sheet.save(out)


CE_LINES = [
    "Zażółć gęślą jaźń · Příliš žluťoučký kůň",
    "Árvíztűrő tükörfúrógép · Șirul țărilor",
    "Pijamalı hasta yağız şoföre · Đurđa čuči",
    "Glāžšķūņa rūķīši ĢĶĻŅ · Įlinkusi ąžuolų",
    "Ċirku ħabib Ġużeppi · Ĉiuĵaŭde eĥoŝanĝo",
]


def latin_ext(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: Latin Extended-A (U+0100 to U+017F), S and T with comma below, Central European text")
    chars = "".join(chr(u) for u in range(0x100, 0x180)) + "ȘșȚț"
    for wght, wdth in ((400, 100), (900, 85)):
        sheet.text(f"wght {wght}, wdth {wdth}")
        font = font_at(vf, 56, wght, wdth)
        for i in range(0, len(chars), 33):
            sheet.line(chars[i:i + 33], font, 56)
        for s_ in CE_LINES:
            sheet.line(s_, font_at(vf, 48, wght, wdth), 48)
        sheet.gap()
    sheet.save(out)


def symbols(vf: str, out: Path) -> None:
    sheet = Sheet("machine-made Heddle 0.2: new symbols, fractions (frac off, then on), redrawn germandbls eth at copyright registered percent")
    for wght, wdth in ((400, 100), (900, 100), (900, 70)):
        sheet.text(f"wght {wght}, wdth {wdth}")
        font = font_at(vf, 72, wght, wdth)
        sheet.line("¢5 £20 ¥300 §12 ¶ ±3 2×4 8÷2 −1", font, 72)
        sheet.line("½ ¼ ¾ 1/2 3/4 15/16 2027/10", font, 72, "frac off", features=["-frac"])
        sheet.line("½ ¼ ¾ 1/2 3/4 15/16 2027/10", font, 72, "frac on", features=["frac"])
        sheet.line("ß ð @ © ® % Straße ðe a@b.ch", font, 72)
        sheet.gap()
    sheet.save(out)


def before_after(old: str, vf: str, out_dir: Path) -> None:
    sets = [
        ("accents", "marks: Heddle 0.1 (upper line) and 0.2 (lower line)",
         [(900, 100), (900, 70), (400, 100)], "ïÏíÎ ÄÖÜ äöü ñÑ õÕ åÅ ÉÈ naïve"),
        ("counters", "hooks and small rings at Black: 0.1 (upper) and 0.2 (lower)",
         [(900, 100), (900, 70)], "afjst ß ð @ © ® % jet fast"),
        ("drift", "glyphs that drifted most near wdth 85: 0.1 (upper) and 0.2 (lower)",
         [(900, 85), (800, 85), (900, 78)], "J z s ä õ – a Jazz"),
    ]
    for key, title, locs, text in sets:
        sheet = Sheet(f"machine-made Heddle: before/after, {title}")
        for wght, wdth in locs:
            sheet.text(f"wght {wght}, wdth {wdth}")
            sheet.line(text, font_at(old, 80, wght, wdth), 80, "0.1")
            sheet.line(text, font_at(vf, 80, wght, wdth), 80, "0.2")
            sheet.gap()
        sheet.save(out_dir / f"heddle-before-after-{key}.png")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Heddle proof sheets.")
    ap.add_argument("--font", default="../fonts/heddle/variable/MachineMadeHeddle[wdth,wght].ttf")
    ap.add_argument("--out-dir", default="../proofs/heddle")
    ap.add_argument("--before", help="An older variable font for the before/after sheets.")
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    charset(args.font, out / "heddle-charset.png")
    weight_waterfall(args.font, out / "heddle-weight-waterfall.png")
    width_ladder(args.font, out / "heddle-width-ladder.png")
    designspace(args.font, out / "heddle-designspace.png")
    kerning(args.font, out / "heddle-kerning.png")
    accents(args.font, out / "heddle-accents.png")
    latin_ext(args.font, out / "heddle-latin-ext.png")
    symbols(args.font, out / "heddle-symbols.png")
    if args.before:
        before_after(args.before, args.font, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
