"""Interpolation check for the Weft piece plans.

The pieces have the same points in every master, so the masters are
compatible by construction. fontTools varLib.interpolatable also uses
heuristics: it matches contours by area and position, and reports a
"contour order" problem if drifting pieces seem to change places. This
module runs the same fontTools code on the master pairs that the
interpolatable command compares (grid neighbours and the source order
chain), so the build can choose drift values that pass it.
"""

from __future__ import annotations

import itertools

from fontTools.varLib.interpolatable import test_gen

from loom import pieces


# fontTools reports a problem below 0.95. Fontspector runs its own port
# of the check on the compiled (rounded) font, so keep a margin.
TOLERANCE = 0.99


class _Glyph:
    def __init__(self, contours):
        self.contours = contours

    def draw(self, pen):
        for c in self.contours:
            pen.moveTo(c[0])
            for p in c[1:]:
                pen.lineTo(p)
            pen.closePath()


class _GlyphSet(dict):
    def __getitem__(self, key):
        return dict.get(self, key)


def master_pairs() -> list[tuple[int, int]]:
    """Return every master index pair (index = w * 4 + f).

    The interpolatable command picks its pairs from the master order, and
    the order changes between the designspace and the compiled font. All
    66 pairs cover every order.
    """
    n = len(pieces.W_MASTERS) * len(pieces.F_MASTERS)
    return list(itertools.combinations(range(n), 2))


def problems(gp: pieces.GlyphPlan, to_font, extra_dy=None) -> list[dict]:
    """Return the interpolatable problems of one glyph plan."""
    locs = [(w, f) for w in pieces.W_MASTERS for f in pieces.F_MASTERS]
    sets = []
    for w, f in locs:
        cs = pieces.glyph_contours(gp, w, f)
        dy = extra_dy(w) if extra_dy else 0.0
        sets.append(_GlyphSet({gp.name: _Glyph(
            [[to_font((x, y + dy)) for x, y in c] for c in cs])}))
    out = []
    for a, b in master_pairs():
        for _, p in test_gen([sets[a], sets[b]], glyphs=[gp.name],
                             names=[str(locs[a]), str(locs[b])],
                             tolerance=TOLERANCE):
            out.append(p)
    return out


def make_clean(gp: pieces.GlyphPlan, to_font, max_attempts: int = 24) -> int:
    """Choose drift values that pass the check. Return the attempt used.

    Raise ValueError if no attempt passes.
    """
    for attempt in itertools.count():
        if attempt >= max_attempts:
            raise ValueError(f"Glyph {gp.name!r}: no drift plan passes the interpolation check.")
        if attempt:
            pieces.reroll_drift(gp, attempt)
        if not problems(gp, to_font):
            return attempt
    raise AssertionError("not reached")
