"""Render the machine-made Sans proof sheets.

Usage:
    python sans/scripts/proof.py --upstream UPSTREAM_FONTS_DIR [--weft WEFT_TTF] [--out proofs/sans]

UPSTREAM_FONTS_DIR is fonts/ of the pinned upstream commit (it has
variable/PlusJakartaSans[wght].ttf). It is used only for the before and
after sheet. WEFT_TTF is a machine-made Weft font for the shared line
sheet; without it, that sheet is not made.

Sheets:
    sans-alternates-before-after.png  upstream defaults against the fork defaults
    sans-stylistic-sets.png           default, ss01, ss02, ss03
    sans-waterfall.png                weights 200 to 800, upright and italic
    sans-body-text.png                body text at 16, 18, 20 and 24 px
    sans-weft-shared-line.png         machine-made Sans and Weft on one line
    sans-italic-cyrillic.png          upright and italic Cyrillic, and the slant check
    sans-coverage.png                 Latin Extended-A and S/T comma below
    sans-kerning.png                  kerning, previous version against this one (--before)
    sans-hinting-otf.png              OTF at small sizes, previous version against this one (--before)

--before is fonts/sans of the previous version (for example from git:
git archive <commit> fonts/sans | tar -x -C /tmp/before). Without it,
the kerning and hinting sheets are not made.

The sheets use FreeType and HarfBuzz (Pillow with libraqm) on the
compiled fonts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

PAPER = (244, 245, 243)
INK = (18, 19, 20)
MUTED = (110, 114, 118)
ACCENT = (196, 64, 40)
GUIDE = (150, 190, 230)

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "fonts" / "sans"
VF = FONTS / "variable" / "MachineMadeSans[wght].ttf"
VF_IT = FONTS / "variable" / "MachineMadeSans-Italic[wght].ttf"

VERSION = "0.2"
CHANGED = "a j p q r y"
WORDS = "jumpy quarry prayer Joy"
WEIGHTS = [200, 300, 400, 500, 600, 700, 800]
WEIGHT_NAMES = ["ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]

BODY = (
    "Machines read the same text many times, and people read it once. "
    "A reading face for both must keep its shapes plain at small sizes, "
    "keep the counters open, and hold an even colour on the page. "
    "This is machine-made Sans 0.2, a modified version of Plus Jakarta Sans "
    "with the straight forms as the defaults. 0123456789"
)


class ProofError(Exception):
    pass


def font(path: Path, size: int, wght: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except OSError as e:
            raise ProofError(f"{path.name}: cannot set wght {wght}: {e}") from e
    return f


def label_font(size: int = 22, wght: int = 500) -> ImageFont.FreeTypeFont:
    return font(VF, size, wght)


def canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), PAPER)
    return img, ImageDraw.Draw(img)


def title(d: ImageDraw.ImageDraw, text: str, sub: str, x: int = 48, y: int = 56) -> int:
    d.text((x, y), text, font=label_font(34, 700), fill=INK, anchor="ls")
    d.text((x, y + 34), sub, font=label_font(20, 400), fill=MUTED, anchor="ls")
    return y + 80


def before_after(upstream_dir: Path, out: Path) -> Path:
    up = upstream_dir / "variable" / "PlusJakartaSans[wght].ttf"
    up_it = upstream_dir / "variable" / "PlusJakartaSans-Italic[wght].ttf"
    for p in (up, up_it):
        if not p.exists():
            raise ProofError(f"Upstream font not found: {p}")
    size = 64
    rows = [
        ("Upstream 2.071, upright", up, CHANGED, INK),
        (f"machine-made Sans {VERSION}, upright", VF, CHANGED, ACCENT),
        ("Upstream 2.071, upright", up, WORDS, INK),
        (f"machine-made Sans {VERSION}, upright", VF, WORDS, ACCENT),
        ("Upstream 2.071, italic", up_it, CHANGED, INK),
        (f"machine-made Sans {VERSION}, italic", VF_IT, CHANGED, ACCENT),
        ("Upstream 2.071, italic", up_it, WORDS, INK),
        (f"machine-made Sans {VERSION}, italic", VF_IT, WORDS, ACCENT),
    ]
    w, step = 1800, 118
    img, d = canvas(w, 150 + step * len(rows) + 40)
    y = title(
        d,
        "Default forms: before and after",
        "Upstream Plus Jakarta Sans (commit 18d1cd2) and machine-made Sans, same text, wght 400, no features.",
    )
    for i, (lab, path, text, colour) in enumerate(rows):
        base = y + 70 + i * step
        if i % 2 == 0 and i:
            d.line((48, base - 92, w - 48, base - 92), fill=(220, 222, 220), width=1)
        d.text((48, base - 62), lab, font=label_font(18, 500), fill=colour, anchor="ls")
        d.text((48, base), text, font=font(path, size, 400), fill=INK, anchor="ls")
    img.save(out / "sans-alternates-before-after.png")
    return out / "sans-alternates-before-after.png"


def stylistic_sets(out: Path) -> Path:
    text = "a j p q r y f g h i k l m n t u G I K U fi fl"
    rows = [
        ("Default (Lurus, straight a j p q r y; upstream forms of the other letters)", []),
        ("ss01  Round forms (original defaults)", ["ss01"]),
        ("ss02  Lancip: sharp forms", ["ss02"]),
        ("ss03  Lingkar: swirl", ["ss03"]),
        ("ss02 + ss03", ["ss02", "ss03"]),
    ]
    w, step = 1800, 104
    img, d = canvas(w, 150 + 2 * step * len(rows) + 40)
    y = title(d, "Stylistic sets", f"machine-made Sans {VERSION}, wght 400. Upper block upright, lower block italic.")
    i = 0
    for path in (VF, VF_IT):
        for lab, feats in rows:
            base = y + 66 + i * step
            d.text((48, base - 58), lab, font=label_font(18, 500), fill=ACCENT, anchor="ls")
            d.text((48, base), text, font=font(path, 56, 400), fill=INK, anchor="ls", features=feats)
            i += 1
    img.save(out / "sans-stylistic-sets.png")
    return out / "sans-stylistic-sets.png"


def waterfall(out: Path) -> Path:
    text = "machine-made Sans Hamburgefonstiv 0123"
    w, step = 1800, 76
    img, d = canvas(w, 150 + 2 * step * len(WEIGHTS) + 80)
    y = title(d, "Weight waterfall", "Variable fonts, wght 200 to 800, 52 px. Left: weight. Upper block upright, lower block italic.")
    i = 0
    for path in (VF, VF_IT):
        for wght, name in zip(WEIGHTS, WEIGHT_NAMES):
            base = y + 56 + i * step + (40 if path is VF_IT else 0)
            d.text((48, base), f"{wght} {name}", font=label_font(18, 500), fill=MUTED, anchor="ls")
            d.text((300, base), text, font=font(path, 52, wght), fill=INK, anchor="ls")
            i += 1
    img.save(out / "sans-waterfall.png")
    return out / "sans-waterfall.png"


def wrap(d: ImageDraw.ImageDraw, text: str, f, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=f) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def body_text(out: Path) -> Path:
    """Body text at true pixel sizes (1 px in the PNG = 1 CSS px at 1x)."""
    sizes = [16, 18, 20, 24]
    col = 620
    w = 48 * 2 + 2 * col + 64
    img, d = canvas(w, 1300)
    y = title(d, "Body text, 16 to 24 px", "True size at 1x. Line height 1.5. Left column upright 400, right column italic 400.")
    for path, x in ((VF, 48), (VF_IT, 48 + col + 64)):
        yy = y + 10
        for s in sizes:
            f = font(path, s, 400)
            d.text((x, yy + 16), f"{s} px", font=label_font(15, 600), fill=ACCENT, anchor="ls")
            yy += 30
            for line in wrap(d, BODY, f, col):
                yy += round(s * 1.5)
                d.text((x, yy), line, font=f, fill=INK, anchor="ls")
            yy += round(s * 1.5)
        bottom = yy
    img = img.crop((0, 0, w, max(bottom, yy) + 40))
    img.save(out / "sans-body-text.png")
    return out / "sans-body-text.png"


def shared_line(weft: Path, out: Path) -> Path:
    """machine-made Sans and Weft at one size, with both line boxes drawn."""
    from fontTools.ttLib import TTFont

    size = 72
    parts = [
        (VF, "Sans meets "),
        (weft, "Weft"),
        (VF, " on one line "),
        (weft, "0123"),
        (VF, " Hxg"),
    ]
    metrics = {}
    for p in {VF, weft}:
        t = TTFont(p)
        upm = t["head"].unitsPerEm
        o, h = t["OS/2"], t["hhea"]
        metrics[p] = {
            "typo": (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap),
            "hhea": (h.ascent, h.descent, h.lineGap),
            "xh": o.sxHeight,
            "cap": o.sCapHeight,
            "upm": upm,
        }
    if metrics[VF]["typo"] != metrics[weft]["typo"]:
        raise ProofError(f"Typo metrics differ: Sans {metrics[VF]['typo']}, Weft {metrics[weft]['typo']}.")
    asc, desc, _gap = metrics[VF]["typo"]
    k = size / metrics[VF]["upm"]
    w = 1800
    img, d = canvas(w, 520)
    y = title(
        d,
        "machine-made Sans and Weft on one line",
        f"Both fonts: typo and hhea ascender {asc}, descender {desc}, line gap 0, at 1000 UPM. {size} px. "
        f"Blue: line box. Grey: x-height and cap height of each font.",
    )
    top = y + 40
    base = top + round(asc * k)
    bottom = base - round(desc * k)
    x = 48
    d.rectangle((40, top, w - 40, bottom), outline=GUIDE, width=2)
    d.line((40, base, w - 40, base), fill=GUIDE, width=2)
    for p, text in parts:
        f = font(p, size, 400) if p != weft else ImageFont.truetype(str(p), size, layout_engine=ImageFont.Layout.RAQM)
        tw = d.textlength(text, font=f)
        for key in ("xh", "cap"):
            yy = base - round(metrics[p][key] * k)
            d.line((x, yy, x + tw, yy), fill=(200, 200, 200), width=1)
        d.text((x, base), text, font=f, fill=INK if p == VF else ACCENT, anchor="ls")
        x += tw
    note_y = bottom + 40
    for i, (p, name) in enumerate(((VF, "machine-made Sans Regular"), (weft, "machine-made Weft Regular"))):
        m = metrics[p]
        d.text(
            (48, note_y + i * 30),
            f"{name}: x-height {m['xh']}, cap height {m['cap']}, typo {m['typo']}, hhea {m['hhea']}",
            font=label_font(18, 400),
            fill=INK if p == VF else ACCENT,
            anchor="ls",
        )
    img = img.crop((0, 0, w, note_y + 70))
    img.save(out / "sans-weft-shared-line.png")
    return out / "sans-weft-shared-line.png"


# --------------------------------------------------------------------------
# Sheets added in 0.2
# --------------------------------------------------------------------------

CYR_UPPER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
CYR_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
CYR_MORE = "ЂЃЄЅІЇЈЉЊЋЌЎЏҐҮӨ ђѓєѕіїјљњћќўџґүө"
CYR_TEXT = "Съешь же ещё этих мягких французских булок, да выпей чаю."


def italic_cyrillic(out: Path) -> Path:
    """Upright and italic Cyrillic, and the check of the slant method."""
    from PIL import ImageChops

    w = 1800
    img, d = canvas(w, 1900)
    y = title(
        d,
        "Italic Cyrillic (new in 0.2)",
        "Upright (black) and italic (red). The italic Cyrillic is the upright Cyrillic slanted 8 degrees about half the x-height.",
    )
    for wght in (400, 800):
        for path, colour in ((VF, INK), (VF_IT, ACCENT)):
            for text, size in ((CYR_UPPER, 44), (CYR_LOWER, 44), (CYR_MORE, 44), (CYR_TEXT, 40)):
                y += round(size * 1.35)
                d.text((48, y), text, font=font(path, size, wght), fill=colour, anchor="ls")
        d.text((w - 48, y), f"wght {wght}", font=label_font(18, 500), fill=MUTED, anchor="rs")
        y += 30

    # The slant check: upstream italic Latin against the upright Latin
    # slanted by the same rule. Ink differences in red and blue.
    y += 40
    d.text((48, y), "Check of the method on Latin, wght 400: upstream italic glyph (grey) and slanted upright glyph", font=label_font(22, 700), fill=INK, anchor="ls")
    y += 30
    d.text((48, y), "Blue: ink only in the upstream italic. Red: ink only in the slanted upright. Number: changed pixels / ink pixels.", font=label_font(18, 400), fill=MUTED, anchor="ls")
    y += 20
    size = 220
    tan = 0.14054  # tan(8 degrees)
    xh = 536  # x-height of the wght 400 master
    letters = "HnoeasBRg"
    x = 48
    results = []
    for ch in letters:
        up = font(VF, size, 400)
        it = font(VF_IT, size, 400)
        box = (round(size * 1.2), round(size * 1.3))
        base = round(size * 1.0)

        def draw(f, shear: bool):
            g = Image.new("L", box, 0)
            gd = ImageDraw.Draw(g)
            gd.text((round(size * 0.15), base), ch, font=f, fill=255, anchor="ls")
            if shear:
                # x' = x + tan * (y_font - xh/2); y_font = (base - y) * 1000 / size
                y0 = base - xh / 2 * size / 1000
                g = g.transform(box, Image.Transform.AFFINE, (1, tan, -tan * y0, 0, 1, 0), resample=Image.Resampling.BICUBIC)
            return g.point(lambda v: 255 if v > 127 else 0).convert("1")

        a = draw(it, False)
        b = draw(up, True)

        def count(m):
            return m.convert("L").histogram()[255]

        xor = ImageChops.logical_xor(a, b)
        diff = count(xor) / max(1, count(a))
        results.append((ch, diff))
        both = ImageChops.logical_and(a, b)
        only_a = ImageChops.logical_and(a, xor)
        only_b = ImageChops.logical_and(b, xor)
        rgb = Image.new("RGB", box, (255, 255, 255))
        rgb.paste((150, 150, 150), mask=both.convert("L"))
        rgb.paste((40, 110, 200), mask=only_a.convert("L"))
        rgb.paste(ACCENT, mask=only_b.convert("L"))
        tile = rgb.resize((box[0] * 2 // 3, box[1] * 2 // 3), Image.Resampling.LANCZOS)
        img.paste(tile, (x, y + 10))
        d.text((x + tile.width // 2, y + tile.height + 34), f"{ch}  {diff * 100:.1f} %", font=label_font(18, 500), fill=INK, anchor="ms")
        x += tile.width + 12
    y += 10 + box[1] * 2 // 3 + 60
    mean = sum(r[1] for r in results) / len(results)
    d.text((48, y), f"Mean {mean * 100:.1f} %. H and n are a pure slant upstream too: their 4 % is the noise of slanting a bitmap. Round letters differ more by the optical correction of the upstream italic.", font=label_font(18, 400), fill=MUTED, anchor="ls")
    img = img.crop((0, 0, w, y + 40))
    img.save(out / "sans-italic-cyrillic.png")
    return out / "sans-italic-cyrillic.png"


def coverage(out: Path) -> Path:
    """Latin Extended-A (U+0100 to U+017F) and S/T with comma below."""
    from fontTools.ttLib import TTFont

    chars = [chr(c) for c in range(0x100, 0x180)] + ["\u0218", "\u0219", "\u021A", "\u021B"]
    new = {"\u017F", "\u0149"}
    cols, cell = 24, 78
    rows = -(-len(chars) // cols)
    w = 48 * 2 + cols * cell
    img, d = canvas(w, 150 + 2 * (rows * cell + 70) + 60)
    y = title(d, "Latin Extended-A and comma below", "U+0100 to U+017F and U+0218 to U+021B, wght 400. Red: new in 0.2 (long s, n preceded by apostrophe). Upper block upright, lower block italic.")
    for path in (VF, VF_IT):
        cmap = TTFont(path).getBestCmap()
        f = font(path, 40, 400)
        for i, ch in enumerate(chars):
            cx = 48 + (i % cols) * cell + cell // 2
            cy = y + 40 + (i // cols) * cell
            missing = ord(ch) not in cmap
            d.text((cx, cy + 10), ch if not missing else "?", font=f, fill=ACCENT if ch in new else (INK if not missing else (220, 0, 0)), anchor="ms")
            d.text((cx, cy + 34), f"{ord(ch):04X}", font=label_font(10, 400), fill=MUTED, anchor="ms")
        y += rows * cell + 70
    img.save(out / "sans-coverage.png")
    return out / "sans-coverage.png"


KERN_ROWS = [
    ("Accented i after T V W Y F f P (touched before)", "Tì Vì Wì Yì Fì fì Fî Pî Tĩ Vĩ Wĩ Yĩ", 700),
    ("L caron before T V W Y (overlapped in Bold)", "ĽT ĽV ĽW ĽY ĽUBICA ĽAVÝ", 800),
    ("Accented vowels after T V Y W (unchanged, no touch)", "Tó Vá Yō Wé Tö Ťá Ýó Vő", 400),
    ("Cyrillic look-alikes now kern as Latin", "ТАК Та То Ро Ру АТ УТ Ау", 400),
    ("Lowercase", "avoid tywny kayak vow river effort", 400),
    ("Figures and punctuation", "1,1 7.4 11:17 “A” ‘T’ (j) [j] L’ f’", 400),
]


def kerning(before: Path, out: Path) -> Path:
    b_vf = before / "variable" / "MachineMadeSans[wght].ttf"
    b_it = before / "variable" / "MachineMadeSans-Italic[wght].ttf"
    for p in (b_vf, b_it):
        if not p.exists():
            raise ProofError(f"Previous font not found: {p}")
    w, step = 1800, 196
    img, d = canvas(w, 150 + step * len(KERN_ROWS) * 2 + 40)
    y = title(d, "Kerning: before and after", "Each pair of lines: previous version (grey label), this version (red label), same text and weight, upright. Lower block italic.")
    for upright, (prev, cur) in ((True, (b_vf, VF)), (False, (b_it, VF_IT))):
        for lab, text, wght in KERN_ROWS:
            y += 42
            note = " (0.1 italic had no Cyrillic)" if not upright and "Cyrillic" in lab else ""
            d.text((48, y), f"{lab}, wght {wght}" + ("" if upright else ", italic") + note, font=label_font(18, 500), fill=INK, anchor="ls")
            for label, path, colour in (("before", prev, MUTED), (VERSION, cur, ACCENT)):
                y += 70
                d.text((48, y), label, font=label_font(16, 600), fill=colour, anchor="ls")
                d.text((150, y), text, font=font(path, 56, wght), fill=INK, anchor="ls")
            y += 14
    img = img.crop((0, 0, w, y + 40))
    img.save(out / "sans-kerning.png")
    return out / "sans-kerning.png"


def hinting(before: Path, out: Path) -> Path:
    """OTF at small sizes, rendered by FreeType with hinting, enlarged 3x."""
    prev = before / "otf" / "MachineMadeSans-Regular.otf"
    cur = FONTS / "otf" / "MachineMadeSans-Regular.otf"
    if not prev.exists():
        raise ProofError(f"Previous font not found: {prev}")
    text = "Hamburgefonstiv 0123456789 minimum"
    sizes = [9, 10, 11, 12, 13, 14]
    scale = 3
    w = 1800
    img, d = canvas(w, 200 + sum(2 * (s * 2 * scale + 4) + 10 for s in sizes))
    y = title(d, "OTF hinting: before and after", "MachineMadeSans-Regular.otf, FreeType with hinting (grayscale), 9 to 14 px, enlarged 3x without smoothing.")
    y += 10
    for s in sizes:
        for label, path, colour in (("0.1 (no hints)", prev, MUTED), (f"{VERSION} (otfautohint)", cur, ACCENT)):
            f = ImageFont.truetype(str(path), s)
            tw = int(f.getlength(text)) + 4
            small = Image.new("L", (tw, s * 2), 255)
            ImageDraw.Draw(small).text((2, round(s * 1.5)), text, font=f, fill=0, anchor="ls")
            big = small.resize((tw * scale, s * 2 * scale), Image.Resampling.NEAREST)
            d.text((48, y + s * scale + 8), f"{s} px {label}", font=label_font(16, 500), fill=colour, anchor="ls")
            img.paste(big, (330, y))
            y += s * 2 * scale + 4
        y += 10
    img = img.crop((0, 0, w, y + 30))
    img.save(out / "sans-hinting-otf.png")
    return out / "sans-hinting-otf.png"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--upstream", type=Path, required=True, help="fonts/ directory of the pinned upstream commit.")
    ap.add_argument("--weft", type=Path, help="A machine-made Weft TTF for the shared line sheet.")
    ap.add_argument("--before", type=Path, help="fonts/sans of the previous version, for the kerning and hinting sheets.")
    ap.add_argument("--out", type=Path, default=ROOT / "proofs" / "sans")
    args = ap.parse_args(argv)
    if not features.check("raqm"):
        print("error: Pillow has no libraqm. Install libraqm (and libfribidi) for shaping.", file=sys.stderr)
        return 1
    for p in (VF, VF_IT):
        if not p.exists():
            print(f"error: {p} not found. Run sans/scripts/build.sh first.", file=sys.stderr)
            return 1
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        made = [
            before_after(args.upstream, args.out),
            stylistic_sets(args.out),
            waterfall(args.out),
            body_text(args.out),
            italic_cyrillic(args.out),
            coverage(args.out),
        ]
        if args.before:
            made += [kerning(args.before, args.out), hinting(args.before, args.out)]
        else:
            print("note: no --before fonts, so the kerning and hinting sheets are not made.")
        if args.weft:
            if not args.weft.exists():
                raise ProofError(f"Weft font not found: {args.weft}")
            made.append(shared_line(args.weft, args.out))
        else:
            print("note: no --weft font, so the shared line sheet is not made.")
    except ProofError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for p in made:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
