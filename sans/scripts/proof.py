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

CHANGED = "a f g h i j k l m n p q r t u y G I K U"
WORDS = "jumpy fighting Kraut quilt Glyph Unity"
WEIGHTS = [200, 300, 400, 500, 600, 700, 800]
WEIGHT_NAMES = ["ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]

BODY = (
    "Machines read the same text many times, and people read it once. "
    "A reading face for both must keep its shapes plain at small sizes, "
    "keep the counters open, and hold an even colour on the page. "
    "This is machine-made Sans 0.1, a modified version of Plus Jakarta Sans "
    "with straight and sharp forms as the defaults. 0123456789"
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
        ("machine-made Sans 0.1, upright", VF, CHANGED, ACCENT),
        ("Upstream 2.071, upright", up, WORDS, INK),
        ("machine-made Sans 0.1, upright", VF, WORDS, ACCENT),
        ("Upstream 2.071, italic", up_it, CHANGED, INK),
        ("machine-made Sans 0.1, italic", VF_IT, CHANGED, ACCENT),
        ("Upstream 2.071, italic", up_it, WORDS, INK),
        ("machine-made Sans 0.1, italic", VF_IT, WORDS, ACCENT),
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
    text = "a f g h i j k l m n p q r t u y G I K U fi fl"
    rows = [
        ("Default (Lurus, straight; Lancip, sharp)", []),
        ("ss01  Round forms (original defaults)", ["ss01"]),
        ("ss02  Lancip: sharp a j r y", ["ss02"]),
        ("ss03  Lingkar: swirl", ["ss03"]),
        ("ss01 + ss03", ["ss01", "ss03"]),
    ]
    w, step = 1800, 104
    img, d = canvas(w, 150 + 2 * step * len(rows) + 40)
    y = title(d, "Stylistic sets", "machine-made Sans 0.1, wght 400. Upper block upright, lower block italic.")
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--upstream", type=Path, required=True, help="fonts/ directory of the pinned upstream commit.")
    ap.add_argument("--weft", type=Path, help="A machine-made Weft TTF for the shared line sheet.")
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
        ]
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
