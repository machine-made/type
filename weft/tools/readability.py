"""Readability gate: OCR the Weft font and compare it with a reference.

Usage:
    python tools/readability.py [--font VF.ttf] [--reference REF.ttf]
                                [--out ../proofs/weft/readability.json] [--gate]

The tool renders a fixed paragraph and a look-alike test line with
FreeType (Pillow), runs Tesseract OCR (the `tesseract` command, English
data), and computes the character error rate (CER): the Levenshtein
distance between the OCR text and the true text, divided by the length
of the true text. Whitespace is normalized first.

* Paragraph: FRAG 0, 8, 15, 50 and 100 at 16, 20 and 24 px, wght 400.
* Look-alikes: fixed lines of the characters I l 1 | O 0 r n m c l d
  5 S 2 Z B 8 g 9 q in groups of five, at 20, 24 and 32 px, at the
  text-safe FRAG values 0, 8 and 15. Tesseract
  reads it with a whitelist of only these characters, so each error is a
  confusion between look-alikes. Spaces are removed before the compare
  (Tesseract often joins the groups). Per-pair confusion counts are in
  the report.

The reference is a free monospace (default: DejaVu Sans Mono from the
distribution). It goes through the same steps.

Gate (--gate): for FRAG 0, 8 and 15 (the text-safe stages), the mean
paragraph CER of Weft must not be more than the reference plus MARGIN,
and the mean look-alike CER not more than the reference plus
LOOKALIKE_MARGIN. FRAG 8 and 15 must also stay within FRAG15_MARGIN of
FRAG 0. FRAG 50 and 100 are reported only.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PARAGRAPH = (
    "Every result a machine hands you has been checked by another machine. "
    "Weft is set on a grid by code, compiled by fontmake and checked on every "
    "pull request: 1,204 of 1,204 glyph tests pass. The quick brown fox jumps "
    "over the lazy dog; pack my box with five dozen liquor jugs (no. 37, 2026)."
)
COLUMNS = 48
SIZES = (16, 20, 24)
FRAGS = (0, 8, 15, 50, 100)
GATED_FRAGS = (0, 8, 15)
PAIRS = ["Il1|", "O0", "rnm", "cld", "5S", "2Z", "B8", "g9q"]
LOOKALIKE_SIZES = (20, 24, 32)
UPSCALE = 3        # Tesseract reads small text better at about 30 px x-height
# Absolute CER margins over the reference. The look-alike line has
# 240 characters. Weft 0.1 needed a margin of 0.06 (about 0.12 against
# 0.075): Tesseract read its l and I as 1, q as g, and confused O and 0.
# Weft 0.2 changed l, I, 1, 0 and q (see STATUS.md) and reads better
# than the reference (about 0.07 against 0.0875), so the margin is 0:
# Weft must not read worse than DejaVu Sans Mono.
MARGIN = 0.02
LOOKALIKE_MARGIN = 0.0
# FRAG 8 and 15 must read like FRAG 0 (the brief: "body text at FRAG 15
# reads the same as FRAG 0").
FRAG15_MARGIN = 0.02
SEED = "machine-made Weft readability"
DEFAULT_REFERENCE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


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


def lookalike_text() -> str:
    rnd = random.Random(SEED)
    chars = "".join(PAIRS)
    groups = ["".join(rnd.choice(chars) for _ in range(5)) for _ in range(48)]
    return "\n".join(" ".join(groups[i:i + 6]) for i in range(0, len(groups), 6))


def render(font_path: str, lines: list[str], size: int, axes: dict | None) -> Image.Image:
    font = ImageFont.truetype(font_path, size)
    if axes:
        names = [a["name"] if isinstance(a["name"], str) else a["name"].decode()
                 for a in font.get_variation_axes()]
        tags = {"Weight": "wght", "Fragmentation": "FRAG"}
        font.set_variation_by_axes([axes[tags.get(n, n)] for n in names])
    step = round(size * 1.5)
    width = max(int(font.getlength(line)) for line in lines) + 2 * size
    img = Image.new("L", (width, step * len(lines) + 2 * size), 255)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((size, size + i * step), line, font=font, fill=0)
    return img.resize((img.width * UPSCALE, img.height * UPSCALE), Image.Resampling.LANCZOS)


def ocr(img: Image.Image, whitelist: str | None = None) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "in.png"
        img.save(path)
        cmd = ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "6",
               "-c", "preserve_interword_spaces=0"]
        if whitelist:
            cmd += ["-c", f"tessedit_char_whitelist={whitelist}"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout


def norm_ws(s: str) -> str:
    return " ".join(s.split())


def levenshtein_ops(a: str, b: str) -> tuple[int, list[tuple[str, str]]]:
    """Return the edit distance and the substitution pairs (true, read)."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                          d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
    subs = []
    i, j = n, m
    while i > 0 and j > 0:
        if d[i][j] == d[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            if a[i - 1] != b[j - 1]:
                subs.append((a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif d[i][j] == d[i - 1][j] + 1:
            i -= 1
        else:
            j -= 1
    return d[n][m], subs


def cer(truth: str, read: str, *, strip_spaces: bool = False) -> tuple[float, list[tuple[str, str]]]:
    t, r = norm_ws(truth), norm_ws(read)
    if strip_spaces:
        t, r = t.replace(" ", ""), r.replace(" ", "")
    dist, subs = levenshtein_ops(t, r)
    return dist / max(1, len(t)), subs


def measure(font_path: str, axes_list: list[dict | None], label: str) -> dict:
    out: dict = {"font": label, "paragraph": {}, "lookalikes": {}}
    para_lines = wrap(PARAGRAPH, COLUMNS)
    look = lookalike_text()
    for axes in axes_list:
        key = f"FRAG {axes['FRAG']}" if axes else "static"
        per_size = {}
        for size in SIZES:
            text = ocr(render(font_path, para_lines, size, axes))
            value, _ = cer(PARAGRAPH, text)
            per_size[str(size)] = round(value, 4)
        out["paragraph"][key] = {"cer_by_px": per_size,
                                 "cer_mean": round(sum(per_size.values()) / len(per_size), 4)}
        if axes is None or axes["FRAG"] in GATED_FRAGS:
            values: dict[str, float] = {}
            confusions: dict[str, int] = {}
            for size in LOOKALIKE_SIZES:
                text = ocr(render(font_path, look.split("\n"), size, axes),
                           whitelist="".join(sorted(set("".join(PAIRS)))))
                value, subs = cer(look, text, strip_spaces=True)
                values[str(size)] = round(value, 4)
                for t, r in subs:
                    pair = next((p for p in PAIRS if t in p and r in p), "other")
                    name = f"{t}->{r}" if pair != "other" else "other"
                    confusions[name] = confusions.get(name, 0) + 1
            out["lookalikes"][key] = {
                "cer_by_px": values,
                "cer": round(sum(values.values()) / len(values), 4),
                "confusions": dict(sorted(confusions.items(), key=lambda kv: -kv[1])),
            }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OCR readability gate for Weft.")
    ap.add_argument("--font", default="../fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf")
    ap.add_argument("--reference", default=DEFAULT_REFERENCE)
    ap.add_argument("--out", default="../proofs/weft/readability.json")
    ap.add_argument("--gate", action="store_true", help="Exit 1 if the gate fails.")
    args = ap.parse_args(argv)
    if shutil.which("tesseract") is None:
        print("Error: tesseract is not installed. Install tesseract-ocr.", file=sys.stderr)
        return 2
    if not Path(args.reference).exists():
        print(f"Error: reference font {args.reference} is missing. Install fonts-dejavu-core.",
              file=sys.stderr)
        return 2
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    weft = measure(args.font, [{"wght": 400, "FRAG": f} for f in FRAGS], "machine-made Weft (variable, wght 400)")
    ref = measure(args.reference, [None], Path(args.reference).name)
    ref_para = ref["paragraph"]["static"]["cer_mean"]
    ref_look = ref["lookalikes"]["static"]["cer"]
    gate = {"margin": MARGIN, "lookalike_margin": LOOKALIKE_MARGIN,
            "frag15_margin": FRAG15_MARGIN, "reference_paragraph_cer": ref_para,
            "reference_lookalike_cer": ref_look, "checks": [], "pass": True}
    for f in GATED_FRAGS:
        key = f"FRAG {f}"
        for kind, value, limit in (
            ("paragraph", weft["paragraph"][key]["cer_mean"], ref_para + MARGIN),
            ("lookalikes", weft["lookalikes"][key]["cer"], ref_look + LOOKALIKE_MARGIN),
        ):
            ok = value <= limit + 1e-9
            gate["checks"].append({"frag": f, "test": kind, "cer": value,
                                   "limit": round(limit, 4), "pass": ok})
            gate["pass"] &= ok
    for f in GATED_FRAGS[1:]:
        for kind, k0, kf in (
            ("paragraph vs FRAG 0", weft["paragraph"]["FRAG 0"]["cer_mean"],
             weft["paragraph"][f"FRAG {f}"]["cer_mean"]),
            ("lookalikes vs FRAG 0", weft["lookalikes"]["FRAG 0"]["cer"],
             weft["lookalikes"][f"FRAG {f}"]["cer"]),
        ):
            ok = kf <= k0 + FRAG15_MARGIN + 1e-9
            gate["checks"].append({"frag": f, "test": kind, "cer": kf,
                                   "limit": round(k0 + FRAG15_MARGIN, 4), "pass": ok})
            gate["pass"] &= ok
    report = {
        "about": "OCR character error rate (CER). Lower is better. See weft/tools/readability.py.",
        "tesseract": version,
        "paragraph": PARAGRAPH,
        "sizes_px": list(SIZES),
        "upscale": UPSCALE,
        "lookalike_text": lookalike_text(),
        "weft": weft,
        "reference": ref,
        "gate": gate,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out}.")
    for c in gate["checks"]:
        print(f"  FRAG {c['frag']:>3} {c['test']:<20} CER {c['cer']:.4f} limit {c['limit']:.4f} "
              f"{'pass' if c['pass'] else 'FAIL'}")
    for f in FRAGS:
        if f not in GATED_FRAGS:
            print(f"  FRAG {f:>3} paragraph  CER {weft['paragraph'][f'FRAG {f}']['cer_mean']:.4f} (report only)")
    if args.gate and not gate["pass"]:
        print("Error: the readability gate failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
