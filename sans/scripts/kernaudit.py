"""Measure the space between glyph pairs in machine-made Sans.

Usage:
    python sans/scripts/kernaudit.py FONT [FONT ...] [--pairs FILE] [--json OUT] [--top N]

For each pair, the script shapes the two characters with HarfBuzz (so
kerning and the default forms apply), then compares the right edge of
the first glyph with the left edge of the second glyph on horizontal
scan lines every 5 units. It reports:

- min_gap: the smallest horizontal distance between the two inks (marks
  included). Below 0 the glyphs overlap; the kerning tests use it to
  check that no kerned pair touches.
- mean_gap: the mean distance on the scan lines where both glyphs have
  ink, with each line capped at 250 units. A rough measure of optical
  space, used to find pairs that are much looser or tighter than the
  others in their group.

Without --pairs, the script uses the pair list in this file (lowercase,
uppercase with lowercase, figures, punctuation and accented pairs).
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

STEP = 5
CAP = 250

LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
FIGURES = "0123456789"
PUNCT = ".,:;’'\"“”‘-–)]}?!/"
ACCENTED_LOWER = "áàâäãåāăąćčçďéèêëěēėęğģíìîïīįĩĭǐȉȋķĺľļłńňņñóòôöõőōŕřŗśšşșťţțúùûüůűūųýÿźžż"
ACCENTED_UPPER = "ÁÀÂÄÃÅĀĂĄĆČÇĎÉÈÊËĚĒĖĘĞĢÍÌÎÏĪĮĶĹĽĻŁŃŇŅÑÓÒÔÖÕŐŌŔŘŖŚŠŞȘŤŢȚÚÙÛÜŮŰŪŲÝŸŹŽŻ"
DIAGONALS = "TVWYFPAL"


def default_pairs() -> list[str]:
    pairs = set()
    for a in LOWER:
        for b in LOWER:
            pairs.add(a + b)
    for a in UPPER:
        for b in LOWER + UPPER:
            pairs.add(a + b)
    for a in FIGURES:
        for b in FIGURES + ".,:;%-":
            pairs.add(a + b)
    for a in UPPER + LOWER + FIGURES:
        for p in PUNCT:
            pairs.add(a + p)
            pairs.add(p + a)
    for a in DIAGONALS + "ŤŦÝŸ":
        for b in ACCENTED_LOWER:
            pairs.add(a + b)
    for a in ACCENTED_UPPER:
        for b in "AOTVWYavoy.,":
            pairs.add(a + b)
            pairs.add(b + a)
    for a in "fjrty":
        for b in ACCENTED_LOWER + "’'\"”)]}?!":
            pairs.add(a + b)
    # Letters with the vertical caron on the right side.
    for a in "ďľť":
        for b in LOWER + ACCENTED_LOWER + PUNCT:
            pairs.add(a + b)
    for b in UPPER + ACCENTED_UPPER + PUNCT:
        pairs.add("Ľ" + b)
    # Cyrillic: the look-alikes kern with the Latin groups.
    cyr_upper = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    cyr_lower = "абвгдежзийклмнопрстуфхцчшщъыьэюяёўїєґђћ"
    for a in cyr_upper:
        for b in cyr_upper + cyr_lower + ".,":
            pairs.add(a + b)
    for a in cyr_lower:
        for b in cyr_lower + ".,":
            pairs.add(a + b)
    return sorted(pairs)


class EdgePen(BasePen):
    """Flatten outlines into line segments."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.segs = []
        self._start = self._cur = None

    def _moveTo(self, p):
        self._start = self._cur = p

    def _lineTo(self, p):
        self.segs.append((self._cur, p))
        self._cur = p

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur
        n = 12
        prev = p0
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            x = mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0]
            y = mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]
            self.segs.append((prev, (x, y)))
            prev = (x, y)
        self._cur = p3

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur
        n = 8
        prev = p0
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            self.segs.append((prev, (x, y)))
            prev = (x, y)
        self._cur = p2

    def _closePath(self):
        if self._cur != self._start:
            self.segs.append((self._cur, self._start))
        self._cur = self._start


class Font:
    def __init__(self, path: str, location: dict | None = None):
        self.path = path
        self.tt = TTFont(path)
        self.location = location or {}
        self.glyphset = self.tt.getGlyphSet(location=self.location or None)
        blob = hb.Blob.from_file_path(path)
        self.hbfont = hb.Font(hb.Face(blob))
        if self.location:
            self.hbfont.set_variations(self.location)
        self.cmap = self.tt.getBestCmap()

    @lru_cache(maxsize=None)
    def edges(self, glyph: str) -> dict:
        pen = EdgePen(self.glyphset)
        self.glyphset[glyph].draw(pen)
        out = {}
        if not pen.segs:
            return out
        ys = [p[1] for s in pen.segs for p in s]
        y = int(min(ys) // STEP * STEP)
        top = max(ys)
        while y <= top:
            xs = []
            for (x0, y0), (x1, y1) in pen.segs:
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            if xs:
                out[y] = (min(xs), max(xs))
            y += STEP
        return out

    def shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {})
        names = [self.hbfont.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
        pos = [(p.x_advance, p.x_offset, p.y_offset) for p in buf.glyph_positions]
        return names, pos

    def kern_value(self, text: str) -> int:
        names, pos = self.shape(text)
        if len(names) != 2:
            return 0
        adv = self.tt["hmtx"][names[0]][0] if not self.location else None
        if adv is None:
            # Variable font: the default advance from HarfBuzz without kerning.
            buf = hb.Buffer()
            buf.add_str(text[0])
            buf.guess_segment_properties()
            hb.shape(self.hbfont, buf, {"kern": False})
            adv = buf.glyph_positions[0].x_advance
        return pos[0][0] - adv


def measure(font: Font, text: str) -> dict | None:
    if any(ord(c) not in font.cmap for c in text):
        return None
    names, pos = font.shape(text)
    if len(names) != 2:
        return None  # a ligature
    left, right = font.edges(names[0]), font.edges(names[1])
    offset = pos[0][0] + pos[1][1] - pos[0][1]
    dy = pos[1][2] - pos[0][2]
    gaps = []
    for y, (_, rx) in left.items():
        r = right.get(y - dy)
        if r is None:
            continue
        gaps.append(offset + r[0] - rx)
    if not gaps:
        return {"pair": text, "glyphs": names, "kern": font.kern_value(text), "min_gap": None, "mean_gap": None}
    capped = [min(g, CAP) for g in gaps]
    return {
        "pair": text,
        "glyphs": names,
        "kern": font.kern_value(text),
        "min_gap": round(min(gaps)),
        "mean_gap": round(sum(capped) / len(capped)),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("fonts", nargs="+")
    ap.add_argument("--pairs", type=Path, help="File with one pair per line.")
    ap.add_argument("--json", type=Path, help="Write every measured pair.")
    ap.add_argument("--summary", type=Path, help="Write the overlap count and the overlapping pairs per font.")
    ap.add_argument("--label", default="", help="A label for the summary (for example the version).")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args(argv)
    pairs = default_pairs()
    if args.pairs:
        pairs = [l.strip() for l in args.pairs.read_text(encoding="utf-8").splitlines() if len(l.strip()) == 2]
    report = {}
    for path in args.fonts:
        font = Font(path)
        rows = [m for m in (measure(font, p) for p in pairs) if m]
        report[Path(path).name] = rows
        touching = [r for r in rows if r["min_gap"] is not None and r["min_gap"] < 0]
        print(f"{Path(path).name}: {len(rows)} pairs, {len(touching)} overlap")
        for r in sorted(touching, key=lambda r: r["min_gap"])[: args.top]:
            print(f"  {r['pair']}  min {r['min_gap']:5}  mean {r['mean_gap']:5}  kern {r['kern']}")
    if args.summary:
        summary = {"label": args.label, "pairs": len(pairs), "about": "Pairs whose inks overlap (min_gap < 0). See sans/scripts/kernaudit.py.", "fonts": {}}
        for name, rows in report.items():
            bad = sorted((r for r in rows if r["min_gap"] is not None and r["min_gap"] < 0), key=lambda r: r["min_gap"])
            summary["fonts"][name] = {
                "overlaps": len(bad),
                "pairs": [{"pair": r["pair"], "min_gap": r["min_gap"], "kern": r["kern"]} for r in bad],
            }
        args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
