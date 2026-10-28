"""Readability gate: OCR machine-made Warp and compare it with DejaVu Serif.

Usage:
    python tools/readability.py [--out ../proofs/warp/readability.json] [--gate]
                                [--regular R.ttf --italic I.ttf]

The tool sets a paragraph from a paper in Warp Regular and Warp Italic
at 10, 12 and 14 px (FreeType through Pillow, with the default OpenType
features, so fi and fl are ligatures), scales the image up 3 times for
Tesseract (it reads best at about 30 px x-height), runs Tesseract OCR
(English data, page mode 6) and computes the character error rate
(CER): the Levenshtein distance between the OCR text and the true text,
divided by the length of the true text, after normalising whitespace.

The reference is DejaVu Serif (Book for Regular, Italic for Italic), set
the same way.

Gate (--gate): for Regular and for Italic, the mean CER of Warp over the
three sizes must not be more than the mean CER of the reference plus
MARGIN (3 percentage points). "Clearly worse" fails.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "fonts" / "warp" / "ttf"

PARAGRAPH = (
    "We study the drawing of a thin viscous thread from a heated preform. When the "
    "draw ratio exceeds a critical value near 20.2, the steady state loses stability "
    "through a Hopf bifurcation and the radius of the fibre oscillates, a regime known "
    "as draw resonance. Writing the axial velocity as a base flow plus a small "
    "perturbation, we obtain a linear eigenvalue problem, whose spectrum we compute by "
    "Chebyshev collocation on 128 points. The leading mode depends only weakly on the "
    "capillary number; inertia and cooling, not surface tension, set the threshold."
)
COLUMNS = 64
SIZES = (10, 12, 14)
UPSCALE = 3
# Absolute CER margin over the reference. Set after the first run
# (Warp 0.1 Regular about 0.02 against 0.001 for DejaVu Serif, at any
# optical size from 9 to 12): Tesseract reads the open lower loop of g
# as a comma, f as t, and the fi and fl ligatures as h and H at 10 px.
# The margin stops a regression; it does not prove parity.
MARGIN = 0.03
REFERENCE = {
    "Regular": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "Italic": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
}


def wrap(text: str, cols: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > cols:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        lines.append(line)
    return lines


def render(font_path: str, lines: list[str], size: int) -> Image.Image:
    font = ImageFont.truetype(font_path, size)
    step = round(size * 1.45)
    width = max(int(font.getlength(line)) for line in lines) + 2 * size
    img = Image.new("L", (width, step * len(lines) + 2 * size), 255)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((size, size + i * step), line, font=font, fill=0)
    return img.resize((img.width * UPSCALE, img.height * UPSCALE), Image.Resampling.LANCZOS)


def ocr(img: Image.Image) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "in.png"
        img.save(path)
        cmd = ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "6"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout


def norm(s: str) -> str:
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff").replace("’", "'")
    return " ".join(s.split())


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1]


def cer(truth: str, read: str) -> float:
    t, r = norm(truth), norm(read)
    return levenshtein(t, r) / max(1, len(t))


def measure(font_path: str) -> dict:
    lines = wrap(PARAGRAPH, COLUMNS)
    by = {str(s): round(cer(PARAGRAPH, ocr(render(font_path, lines, s))), 4) for s in SIZES}
    return {"cer_by_px": by, "cer_mean": round(sum(by.values()) / len(by), 4)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OCR readability gate for Warp.")
    ap.add_argument("--regular", default=str(FONTS / "MachineMadeWarp-Regular.ttf"))
    ap.add_argument("--italic", default=str(FONTS / "MachineMadeWarp-Italic.ttf"))
    ap.add_argument("--out", default=str(HERE.parents[1] / "proofs" / "warp" / "readability.json"))
    ap.add_argument("--gate", action="store_true", help="Exit 1 if the gate fails.")
    args = ap.parse_args(argv)
    if shutil.which("tesseract") is None:
        print("Error: tesseract is not installed. Install tesseract-ocr.", file=sys.stderr)
        return 2
    for p in REFERENCE.values():
        if not Path(p).exists():
            print(f"Error: reference font {p} is missing. Install fonts-dejavu-core.", file=sys.stderr)
            return 2
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    warp = {"Regular": measure(args.regular), "Italic": measure(args.italic)}
    ref = {k: measure(v) for k, v in REFERENCE.items()}
    gate = {"margin": MARGIN, "checks": [], "pass": True}
    for k in ("Regular", "Italic"):
        limit = ref[k]["cer_mean"] + MARGIN
        ok = warp[k]["cer_mean"] <= limit + 1e-9
        gate["checks"].append({"style": k, "cer": warp[k]["cer_mean"], "reference_cer": ref[k]["cer_mean"],
                               "limit": round(limit, 4), "pass": ok})
        gate["pass"] &= ok
    report = {
        "about": "OCR character error rate (CER). Lower is better. See warp/tools/readability.py.",
        "tesseract": version,
        "paragraph": PARAGRAPH,
        "sizes_px": list(SIZES),
        "upscale": UPSCALE,
        "warp": {"font": "machine-made Warp 0.1 (text, opsz 10)", **warp},
        "reference": {"font": "DejaVu Serif (Book, Italic)", **ref},
        "gate": gate,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out}.")
    for c in gate["checks"]:
        print(f"  {c['style']:<8} CER {c['cer']:.4f}  DejaVu Serif {c['reference_cer']:.4f}  "
              f"limit {c['limit']:.4f}  {'pass' if c['pass'] else 'FAIL'}")
    if args.gate and not gate["pass"]:
        print("Error: the readability gate failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
