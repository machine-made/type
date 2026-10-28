"""OCR readability check for machine-made Heddle (a display face).

Usage:
    python tools/readability.py [--out ../proofs/heddle/readability.json]
                                [--baseline DIR] [--gate]

Heddle is a display face, not a text face, so this is not the text-face
gate of Weft and Warp. It stops regressions: the tool sets a headline
paragraph in Heddle Regular, Bold and Black at 24, 32 and 48 px
(FreeType through Pillow, default features), runs Tesseract OCR
(English, page mode 6) and computes the character error rate (CER): the
Levenshtein distance between OCR text and true text, divided by the
length of the true text, after normalising whitespace. DejaVu Sans
(Book, Bold) is the reference.

--baseline DIR: also measure the static TTFs in DIR (for example the
    Heddle 0.1 fonts from git) and record them as "before".
--gate: exit 1 if, for any style, the mean CER is more than MARGIN above
    the baseline (when given) or above the reference plus REF_MARGIN.

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
FONTS = HERE.parents[1] / "fonts" / "heddle" / "ttf"

PARAGRAPH = (
    "Swiss posters of 1958 set big words in tight grotesks. Heddle builds "
    "every letter from four parts: rect, ring, slant and vee. Quick zebras "
    "jump over the lazy dog; 27 boxes of 64 jugs weigh 3,590 kg."
)
COLUMNS = 40
SIZES = (24, 32, 48)
STYLES = {"Regular": "MachineMadeHeddle-Regular.ttf", "Bold": "MachineMadeHeddle-Bold.ttf",
          "Black": "MachineMadeHeddle-Black.ttf"}
REFERENCE = {
    "Regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Black": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
# A new version may be at most 1 point worse than the baseline.
MARGIN = 0.01
# Without a baseline: at most 5 points worse than the reference.
REF_MARGIN = 0.05


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
    step = round(size * 1.35)
    width = max(int(font.getlength(line)) for line in lines) + 2 * size
    img = Image.new("L", (width, step * len(lines) + 2 * size), 255)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((size, size + i * step), line, font=font, fill=0)
    return img


def ocr(img: Image.Image) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "in.png"
        img.save(path)
        cmd = ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "6"]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def norm(s: str) -> str:
    return " ".join(s.replace("’", "'").split())


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
    ap = argparse.ArgumentParser(description="OCR readability check for Heddle.")
    ap.add_argument("--fonts", default=str(FONTS))
    ap.add_argument("--baseline", help="Folder with the static TTFs of an older version.")
    ap.add_argument("--baseline-label", default="Heddle 0.1")
    ap.add_argument("--out", default=str(HERE.parents[1] / "proofs" / "heddle" / "readability.json"))
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args(argv)
    if shutil.which("tesseract") is None:
        print("Error: tesseract is not installed. Install tesseract-ocr.", file=sys.stderr)
        return 2
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    now = {k: measure(str(Path(args.fonts) / v)) for k, v in STYLES.items()}
    ref = {k: measure(v) for k, v in REFERENCE.items()}
    before = {k: measure(str(Path(args.baseline) / v)) for k, v in STYLES.items()} if args.baseline else None
    gate = {"margin_over_baseline": MARGIN, "margin_over_reference": REF_MARGIN, "checks": [], "pass": True}
    for k in STYLES:
        if before:
            limit = before[k]["cer_mean"] + MARGIN
            against = "baseline"
        else:
            limit = ref[k]["cer_mean"] + REF_MARGIN
            against = "reference"
        ok = now[k]["cer_mean"] <= limit + 1e-9
        gate["checks"].append({"style": k, "cer": now[k]["cer_mean"], "against": against,
                               "limit": round(limit, 4), "pass": ok})
        gate["pass"] &= ok
    report = {
        "about": "OCR character error rate (CER), lower is better. Heddle is a display face: "
                 "this stops regressions; it is not a text-face gate. See heddle/tools/readability.py.",
        "tesseract": version,
        "paragraph": PARAGRAPH,
        "sizes_px": list(SIZES),
        "heddle": {"font": "machine-made Heddle 0.2 (static TTF)", **now},
        "reference": {"font": "DejaVu Sans (Book; Bold for Bold and Black)", **ref},
        "gate": gate,
    }
    if before:
        report["before"] = {"font": args.baseline_label, **before}
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for k in STYLES:
        b = f", before {before[k]['cer_mean']}" if before else ""
        print(f"{k}: CER {now[k]['cer_mean']}{b}, reference {ref[k]['cer_mean']}")
    print("gate:", "pass" if gate["pass"] else "FAIL")
    return 0 if (gate["pass"] or not args.gate) else 1


if __name__ == "__main__":
    raise SystemExit(main())
