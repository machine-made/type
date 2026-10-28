"""Readability gate: OCR machine-made Sans and compare it with DejaVu Sans.

Usage:
    python sans/scripts/readability.py [--out proofs/sans/readability.json] [--gate]
                                       [--before DIR]

The tool sets an English paragraph in Sans Regular and Sans Italic (the
hinted static TTF) at 10, 12 and 14 px with FreeType through Pillow,
scales the image up 3 times for Tesseract, runs Tesseract OCR (English
data, page mode 6) and computes the character error rate (CER): the
Levenshtein distance between the OCR text and the true text, divided by
the length of the true text, after normalising whitespace. The same
method as warp/tools/readability.py.

The reference is DejaVu Sans (Book for Regular, Oblique for Italic).

--before DIR measures the TTF in DIR too (for example the 0.1 fonts from
git) and writes them as "before", so a change can be compared.

Gate (--gate): for Regular and Italic, the mean CER of Sans must not be
more than the 0.1 baseline (BASELINE, measured with this script and
Tesseract 5.3.4) plus NOISE, and not more than "before" plus NOISE when
--before is given. The CER of DejaVu Sans is in the report for
comparison. Sans 0.1 is already more than 3 points above DejaVu Sans in
italic: Tesseract misses many of the narrow word spaces (170 units) and
reads Il1 and O0 as other characters. The gate stops a regression; it
does not prove parity.
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

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "fonts" / "sans" / "ttf"

PARAGRAPH = (
    "Machines read the same text many times, and people read it once. A quick brown fox "
    "jumps over the lazy dog near 1,250 metres; the jury quizzed six vexed workers about "
    "the 0.37 ratio and the 48 hour delay. Writing a function f(x) = 9y + 2z, we find "
    "that the error falls by half when the grid doubles. Illegible pairs such as Il1, O0, "
    "rn and m, cl and d must stay clear at small sizes, so the counters keep open."
)
COLUMNS = 64
SIZES = (10, 12, 14)
UPSCALE = 3
# Mean CER of machine-made Sans 0.1 (git main 7a8b6b2), measured with
# this script and Tesseract 5.3.4.
BASELINE = {"Regular": 0.0350, "Italic": 0.0439}
# Allowed change against the baseline and --before (Tesseract noise).
NOISE = 0.005
REFERENCE = {
    "Regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
}
FILES = {"Regular": "MachineMadeSans-Regular.ttf", "Italic": "MachineMadeSans-Italic.ttf"}


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
    ap = argparse.ArgumentParser(description="OCR readability gate for machine-made Sans.")
    ap.add_argument("--fonts", default=str(FONTS), help="Folder with the static TTF.")
    ap.add_argument("--before", help="Folder with the static TTF of the previous version.")
    ap.add_argument("--before-label", default="machine-made Sans 0.1")
    ap.add_argument("--label", default="machine-made Sans 0.2")
    ap.add_argument("--out", default=str(ROOT / "proofs" / "sans" / "readability.json"))
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
    sans = {k: measure(str(Path(args.fonts) / f)) for k, f in FILES.items()}
    ref = {k: measure(v) for k, v in REFERENCE.items()}
    before = {k: measure(str(Path(args.before) / f)) for k, f in FILES.items()} if args.before else None
    gate = {"baseline": BASELINE, "noise": NOISE, "checks": [], "pass": True}
    for k in FILES:
        limit = BASELINE[k] + NOISE
        if before:
            limit = min(limit, before[k]["cer_mean"] + NOISE)
        ok = sans[k]["cer_mean"] <= limit + 1e-9
        check = {"style": k, "cer": sans[k]["cer_mean"], "reference_cer": ref[k]["cer_mean"], "limit": round(limit, 4), "pass": ok}
        if before:
            check["before_cer"] = before[k]["cer_mean"]
        gate["checks"].append(check)
        gate["pass"] &= ok
    report = {
        "about": "OCR character error rate (CER). Lower is better. See sans/scripts/readability.py.",
        "tesseract": version,
        "paragraph": PARAGRAPH,
        "sizes_px": list(SIZES),
        "upscale": UPSCALE,
        "sans": {"font": f"{args.label} (hinted static TTF)", **sans},
    }
    if before:
        report["before"] = {"font": f"{args.before_label} (hinted static TTF)", **before}
    report["reference"] = {"font": "DejaVu Sans (Book, Oblique)", **ref}
    report["gate"] = gate
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out}.")
    for c in gate["checks"]:
        extra = f"  before {c['before_cer']:.4f}" if "before_cer" in c else ""
        print(f"  {c['style']:<8} CER {c['cer']:.4f}{extra}  DejaVu Sans {c['reference_cer']:.4f}  "
              f"limit {c['limit']:.4f}  {'pass' if c['pass'] else 'FAIL'}")
    if args.gate and not gate["pass"]:
        print("Error: the readability gate failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
