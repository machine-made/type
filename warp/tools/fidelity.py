"""Fidelity of the outlines: compare each font glyph with the pen sweep.

Usage:
    python tools/fidelity.py [--out ../proofs/warp/fidelity.json] [--gate]

For every drawn glyph of every style, the tool rasterises two shapes,
independently:

* the sweep: the engine's polygons (nib hulls, discs, teardrops,
  brackets), each filled on its own and combined (their union, the
  nonzero fill), with Pillow;
* the font glyph: read back from the compiled TTF (quadratic curves,
  integer points, after fontmake), its counters cleared.

Both are filled once at 2048 pixels per em (about 2 pixels per unit)
and averaged down to grey levels at 16, 32, 64 and 128 pixels per em. The difference of a glyph at one size
is the sum of the absolute grey differences divided by the ink of the
sweep. The gate checks the largest difference over all glyphs at each
size against TOLERANCE.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from loom import build as Bd  # noqa: E402
from loom import charset as CS  # noqa: E402
from loom.raster import PolyPen, fill_glyph, fill_sweep  # noqa: E402

SIZES = (16, 32, 64, 128)
# Both shapes are filled once at BASE pixels per em (about 2 pixels per
# unit) and averaged down to each size.
BASE = 2048
# Largest allowed difference (fraction of the ink) per size in pixels per em.
TOLERANCE = {16: 0.05, 32: 0.05, 64: 0.05, 128: 0.05}
FONTS = HERE.parents[1] / "fonts" / "warp" / "ttf"


def box_of(polys):
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    return min(xs), min(ys), max(xs), max(ys)


def raster(polys, box, font):
    """Fill at BASE pixels per em; returns a 0..1 array."""
    x0, y0, x1, y1 = box
    s = BASE / 1000.0
    block = BASE // min(SIZES)
    W = int((x1 - x0) * s) + 2 * block
    H = int((y1 - y0) * s) + 2 * block
    W, H = W + (-W) % block, H + (-H) % block
    tr = lambda p: ((p[0] - x0) * s + block, (y1 - p[1]) * s + block)  # noqa: E731
    out = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(out)
    if not font:
        # the sweep: every polygon is inked; their union is the nonzero fill
        fill_sweep(draw, polys, tr)
    else:
        # the font glyph has no overlaps: contours at an even nesting depth
        # are ink, at an odd depth counters, drawn from the outside in.
        # Pillow inks the boundary pixels of a polygon, so a counter keeps
        # its boundary inked: both shapes get the same half-pixel edge.
        fill_glyph(draw, polys, tr)
    return np.asarray(out, dtype=float) / 255.0


def down(a, ppem):
    k = BASE // ppem
    H, W = a.shape
    return a.reshape(H // k, k, W // k, k).mean(axis=(1, 3))


def compare(style_key: str, font: TTFont) -> dict:
    gs = font.getGlyphSet()
    out = {}
    for gl in CS.GLYPHS:
        if gl.comps or gl.variant == "notdef":
            continue
        d = Bd.drawn(style_key, gl.name)
        sweep = [[(x + d.dx, y) for x, y in poly] for poly in d.sweep.polys if len(poly) >= 3]
        if not sweep:
            continue
        pen = PolyPen(gs)
        gs[gl.name].draw(pen)
        if not pen.polys:
            out[gl.name] = {str(s): 1.0 for s in SIZES}
            continue
        bx = box_of(sweep + pen.polys)
        res = {}
        A = raster(sweep, bx, font=False)
        Bm = raster(pen.polys, bx, font=True)
        for ppem in SIZES:
            a, b = down(A, ppem), down(Bm, ppem)
            res[str(ppem)] = round(float(np.abs(a - b).sum() / max(a.sum(), 1e-9)), 5)
        out[gl.name] = res
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare the Warp outlines with the pen sweep.")
    ap.add_argument("--out", default=str(HERE.parents[1] / "proofs" / "warp" / "fidelity.json"))
    ap.add_argument("--styles", default=",".join(Bd.STYLES))
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args(argv)
    report = {"about": "Difference between each font glyph (compiled TTF) and its pen sweep, as a fraction "
                       "of the ink, at several pixels per em. See warp/tools/fidelity.py.",
              "sizes_ppem": list(SIZES), "base_ppem": BASE,
              "tolerance": {str(k): v for k, v in TOLERANCE.items()}, "styles": {}, "pass": True}
    for key in args.styles.split(","):
        st = Bd.STYLES[key]
        font = TTFont(FONTS / f"{Bd.ps_name(st)}.ttf")
        glyphs = compare(key, font)
        summary = {}
        for s in SIZES:
            vals = sorted(((v[str(s)], n) for n, v in glyphs.items()), reverse=True)
            arr = np.array([v for v, _ in vals])
            summary[str(s)] = {"max": vals[0][0], "max_glyph": vals[0][1], "mean": round(float(arr.mean()), 5),
                               "p95": round(float(np.percentile(arr, 95)), 5),
                               "pass": vals[0][0] <= TOLERANCE[s]}
            report["pass"] &= summary[str(s)]["pass"]
        report["styles"][key] = {"font": f"{Bd.ps_name(st)}.ttf", "glyphs_checked": len(glyphs),
                                 "summary": summary, "glyphs": glyphs}
        print(f"{key}: {len(glyphs)} glyphs; " + "; ".join(
            f"{s} ppem max {summary[str(s)]['max']:.4f} ({summary[str(s)]['max_glyph']}) mean {summary[str(s)]['mean']:.4f}"
            for s in SIZES))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"Wrote {out}. {'pass' if report['pass'] else 'FAIL'}")
    if args.gate and not report["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
