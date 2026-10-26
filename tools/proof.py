"""Render the Weft proof sheet from the compiled font.

Usage:
    python tools/proof.py [--font fonts/Weft-Regular.ttf] [--out proofs/weft-phase1-proof.png]
    python tools/proof.py --compare SKETCH_PNG   # also write the comparison

The proof uses FreeType (Pillow) on the compiled TTF. It does not use the
sketch. The --compare option reads a PNG that tools/sketch_render.js made
from the same layout spec and writes a side-by-side image and an overlay.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

PAPER = (244, 245, 243)
INK = (18, 19, 20)
MUTED = (91, 96, 100)

# Phase 1 has no '.' and no '|'. The proof drops them.
LINES = [
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "Made by machines Proven for machines",
    "Il1 O0 rn m cl d 5S 2Z B8 g9",
]


def layout(size: int) -> dict:
    s = size / 16
    cols = max(len(line) for line in LINES)
    left = round(2 * s)
    return {
        "size": size,
        "left": left,
        "top": round(15 * s),  # baseline of the first line
        "lineStep": round(19 * s),
        "width": round(left * 2 + cols * 12 * s),
        "height": round(15 * s + (len(LINES) - 1) * 19 * s + 6 * s),
        "lines": LINES,
    }


def render_font(font_path: Path, spec: dict) -> Image.Image:
    img = Image.new("RGB", (spec["width"], spec["height"]), PAPER)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(font_path), spec["size"])
    for i, line in enumerate(spec["lines"]):
        y = spec["top"] + i * spec["lineStep"]
        draw.text((spec["left"], y), line, font=font, fill=INK, anchor="ls")
    return img


def label(img: Image.Image, text: str, pad: int = 36) -> Image.Image:
    out = Image.new("RGB", (img.width, img.height + pad), PAPER)
    out.paste(img, (0, pad))
    draw = ImageDraw.Draw(out)
    draw.text((12, 8), text, font=ImageFont.load_default(18), fill=MUTED)
    return out


def ink_mask(img: Image.Image) -> Image.Image:
    return img.convert("L").point(lambda v: 255 if v < 128 else 0)


def coverage(img: Image.Image) -> Image.Image:
    """Return ink coverage per pixel (0 = paper, 255 = full ink)."""
    lo, hi = INK[0], PAPER[0]
    return img.convert("L").point(lambda v: max(0, min(255, round((hi - v) * 255 / (hi - lo)))))


def soft_iou(a: Image.Image, b: Image.Image) -> float:
    """Return sum(min) / sum(max) of two coverage maps.

    This uses the anti-aliased grey levels, so a stem edge on a half
    pixel does not count as a shape change.
    """
    lo = ImageChops.darker(a, b).histogram()
    hi = ImageChops.lighter(a, b).histogram()
    s_lo = sum(i * n for i, n in enumerate(lo))
    s_hi = sum(i * n for i, n in enumerate(hi))
    return round(s_lo / s_hi, 4) if s_hi else 1.0


def _count(m: Image.Image) -> int:
    return m.histogram()[255]


def best_shift(a: Image.Image, b: Image.Image, reach: int = 2) -> tuple[int, int]:
    """Return the pixel shift of b that gives the most shared ink.

    The canvas renderer does not snap the pen origin to pixels and
    FreeType does. A shift of 1 px or less is a raster offset, not a
    shape change.
    """
    best, best_n = (0, 0), -1
    for dx in range(-reach, reach + 1):
        for dy in range(-reach, reach + 1):
            n = _count(ImageChops.multiply(a, ImageChops.offset(b, dx, dy)))
            if n > best_n:
                best, best_n = (dx, dy), n
    return best


def compare(font_img: Image.Image, sketch_img: Image.Image, out: Path) -> dict:
    a, b = ink_mask(font_img), ink_mask(sketch_img)
    dx, dy = best_shift(a, b)
    b = ImageChops.offset(b, dx, dy)
    sketch_img = ImageChops.offset(sketch_img, dx, dy)
    both = ImageChops.multiply(a, b)
    either = ImageChops.lighter(a, b)
    only_a = ImageChops.subtract(a, b)
    only_b = ImageChops.subtract(b, a)
    count = _count
    n_both, n_either = count(both), count(either)
    stats = {
        "ink_pixels_font": count(a),
        "ink_pixels_sketch": count(b),
        "only_font": count(only_a),
        "only_sketch": count(only_b),
        "iou": round(n_both / n_either, 4) if n_either else 1.0,
        "sketch_shift_px": [dx, dy],
        "soft_iou": soft_iou(coverage(font_img), coverage(sketch_img)),
    }
    # Overlay: black where both agree, red only in the font, blue only in
    # the sketch.
    ov = Image.new("RGB", a.size, PAPER)
    ov.paste((18, 19, 20), mask=both)
    ov.paste((222, 42, 31), mask=only_a)
    ov.paste((30, 90, 220), mask=only_b)
    left = label(font_img, "Compiled font: fonts/Weft-Regular.ttf (FreeType)")
    right = label(sketch_img, "Sketch 0.1 renderer (canvas), wght 400, FRAG 0")
    bottom = label(ov, f"Overlay: black = both, red = font only, blue = sketch only. coverage IoU {stats['soft_iou']}, binary IoU {stats['iou']}")
    gap = 24
    w = left.width + right.width + gap
    sheet = Image.new("RGB", (w, left.height + bottom.height + gap), PAPER)
    sheet.paste(left, (0, 0))
    sheet.paste(right, (left.width + gap, 0))
    sheet.paste(bottom, ((w - bottom.width) // 2, left.height + gap))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Weft proof sheet.")
    ap.add_argument("--font", default="fonts/Weft-Regular.ttf")
    ap.add_argument("--out", default="proofs/weft-phase1-proof.png")
    ap.add_argument("--size", type=int, default=64)
    ap.add_argument("--spec-out", help="Write the layout spec as JSON.")
    ap.add_argument("--compare", help="Sketch PNG made from the same spec.")
    ap.add_argument("--compare-out", default="proofs/weft-phase1-vs-sketch.png")
    args = ap.parse_args(argv)
    spec = layout(args.size)
    if args.spec_out:
        Path(args.spec_out).write_text(json.dumps(spec))
    img = render_font(Path(args.font), spec)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Wrote {out}.")
    if args.compare:
        stats = compare(img, Image.open(args.compare).convert("RGB"), Path(args.compare_out))
        print(f"Wrote {args.compare_out}. {json.dumps(stats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
