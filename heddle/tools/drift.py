"""Measure how far the variable font drifts from the engine between masters.

Usage:
    python tools/drift.py [--out ../proofs/heddle/drift.json]

For every glyph and a set of locations between the masters, the tool
takes the outline that the glyph table draws directly at that location
(loom.build.direct_outline) and the outline that the variable font
interpolates from the masters (loom.build.interpolated, the same model as
fontTools varLib). It removes overlaps from both and measures:

* shape: the area where the two differ, as a share of the ink area of the
  direct outline. Both are filled with the nonzero rule at 4 units per
  pixel (loom/raster.py); differences thinner than about 8 units (a
  one-pixel edge on either side) do not count;
* advance: the advance width difference in font units.

At the masters both are the same (up to rounding). Between masters the
width floor (W >= 2.3 S), the min() limits in some glyphs and the curved
cut levels are not linear, so the font can differ a little.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build as B  # noqa: E402
from loom import glyphs as G  # noqa: E402
from loom import raster as R  # noqa: E402

# Points between the masters: mid-cells, mid-edges and common weights.
LOCATIONS = [
    (250, 85), (250, 120), (550, 85), (550, 120), (800, 85), (800, 120),
    (250, 100), (550, 100), (800, 100), (100, 85), (400, 85), (700, 85),
    (900, 85), (100, 120), (400, 120), (700, 120), (900, 120), (300, 70),
    (500, 100), (600, 140), (850, 70),
]


def measure(name: str, wght: float, wdth: float) -> tuple[float, float]:
    """Return (shape drift, advance drift) of one glyph at one location."""
    a_cs, a_adv = B.direct_outline(name, wght, wdth)
    b_cs, b_adv = B.interpolated(name, wght, wdth)
    if not a_cs:
        return 0.0, abs(a_adv - b_adv)
    ma, mb = R.nonzero_mask(a_cs), R.nonzero_mask(b_cs)
    ink = R.count(ma)
    if ink == 0:
        return 0.0, abs(a_adv - b_adv)
    return R.mismatch(ma, mb) / ink, abs(a_adv - b_adv)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[2] / "proofs" / "heddle" / "drift.json")
    args = ap.parse_args(argv)
    names = [n for n in G.glyph_order() if n not in G.accent_names() and n != "space"]
    rows = {}
    for name in names:
        worst_s = (0.0, None)
        worst_a = (0.0, None)
        for w, d in LOCATIONS:
            s, a = measure(name, w, d)
            if s > worst_s[0]:
                worst_s = (s, (w, d))
            if a > worst_a[0]:
                worst_a = (a, (w, d))
        rows[name] = {"shape": round(worst_s[0], 4), "shape_at": worst_s[1],
                      "advance": round(worst_a[0], 1), "advance_at": worst_a[1]}
    sketch = [n for n in names if n in G.GLYPHS and G.GLYPHS[n].sketch]
    summary = {
        "locations": LOCATIONS,
        "max_shape": max(r["shape"] for r in rows.values()),
        "max_shape_sketch_glyphs": max(rows[n]["shape"] for n in sketch),
        "max_advance": max(r["advance"] for r in rows.values()),
        "max_advance_sketch_glyphs": max(rows[n]["advance"] for n in sketch),
        "median_shape": sorted(r["shape"] for r in rows.values())[len(rows) // 2],
    }
    worst = sorted(rows.items(), key=lambda kv: -kv[1]["shape"])[:12]
    out = {"note": __doc__.split("\n\n")[2].strip().replace("\n", " "),
           "summary": summary, "worst_shape": dict(worst), "glyphs": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "locations"}, indent=1))
    for n, r in worst:
        print(f"  {n:16s} shape {r['shape']:.4f} at {r['shape_at']}, advance {r['advance']} at {r['advance_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
