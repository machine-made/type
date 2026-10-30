"""Weft glyph data beyond sketch 0.1 (Weft 0.1 and 0.2).

This file holds plain data only, in the same form as loom/glyphs.py:
centre-line strokes in design units, x in the 7-unit design box, y from
the baseline. The shapes follow the sketch rules: centre-line strokes,
octagonal bowls cut at 45 degrees, square shoulders, square caps.

Contents:

* New drawings: the rest of printable ASCII, the Latin-1 Supplement
  symbols and letters that are not accented forms, and the extras
  (Euro, curly quotes, ellipsis, bullet, rupee, dotless i).
* Accent components (".lc" for lowercase, ".case" for capitals).
* Weft 0.2: Latin Extended-A, S and T with comma below, single
  guillemets, low quotes, minus, box drawing and arrows.
* COMPOSITES: accented letters, spacing accents and the guillemets,
  built from components. A component offset can depend on the stroke
  width (see parts() and accent_offset()), so marks clear the base at
  every weight. Offsets are piecewise linear in the stroke width, with
  breaks at the master widths, so the variable font and the statics
  agree.

Do not trace, import or copy outlines from other fonts.

Licence: this table defines font outlines, so it is Font Software under
the SIL Open Font License 1.1 (see weft/OFL.txt), Reserved Font Name
"machine-made".
"""

from __future__ import annotations


def OCT(x0: float, x1: float, y0: float, y1: float, c: float) -> list[tuple[float, float]]:
    """Return a closed octagon centre line (first point not repeated)."""
    return [(x0, y0 + c), (x0, y1 - c), (x0 + c, y1), (x1 - c, y1),
            (x1, y1 - c), (x1, y0 + c), (x1 - c, y0), (x0 + c, y0)]


def _move(pts, dx: float = 0.0, dy: float = 0.0):
    return [(round(x + dx, 4), round(y + dy, 4)) for x, y in pts]


def _rot180(pts, cx: float, cy: float):
    """Turn points 180 degrees around (cx, cy)."""
    return [(round(2 * cx - x, 4), round(2 * cy - y, 4)) for x, y in pts]


# Small figures (2.6 wide, 4.6 high). Superiors and fractions use them.
def _n1(x0: float, y0: float):
    return [("open", _move([(0.4, 3.8), (1.4, 4.6), (1.4, 0)], x0, y0))]


def _n2(x0: float, y0: float):
    return [("open", _move([(0, 3.8), (0.8, 4.6), (1.8, 4.6), (2.6, 3.8), (2.6, 3.0),
                            (0, 0.8), (0, 0), (2.6, 0)], x0, y0))]


def _n3(x0: float, y0: float):
    return [
        ("open", _move([(0, 4.6), (1.8, 4.6), (2.6, 3.8), (2.6, 3.1), (1.8, 2.3), (0.8, 2.3)], x0, y0)),
        ("open", _move([(1.8, 2.3), (2.6, 1.5), (2.6, 0.8), (1.8, 0), (0, 0)], x0, y0)),
    ]


def _n4(x0: float, y0: float):
    return [("open", _move([(2.0, 0), (2.0, 4.6), (0, 1.4), (2.6, 1.4)], x0, y0))]


_FRACTION_SLASH = ("open", [(5.8, 10.6), (1.2, 0.4)])

# Sketch shapes reused here (same values as loom/glyphs.py).
_S_CAP = [(7, 11), (2.2, 11), (0, 8.8), (0, 7.8), (2.2, 5.6), (4.8, 5.6), (7, 3.4), (7, 2.2), (4.8, 0), (0, 0)]
_C_LC = [(6.5, 8), (2.5, 8), (0.5, 6), (0.5, 2), (2.5, 0), (6.5, 0)]
_O_CAP = OCT(0, 7, 0, 11, 2.5)
_O_LC = OCT(0.5, 6.5, 0, 8, 2)
_A_LC = [
    ("open", [(0.8, 8), (4.5, 8), (6.5, 6), (6.5, 0)]),
    ("open", [(6.5, 4.4), (2.1, 4.4), (0.5, 2.8), (0.5, 1.6), (2.1, 0), (6.5, 0)]),
]
_QUESTION = [(0.5, 9.4), (2.1, 11), (4.9, 11), (6.5, 9.4), (6.5, 7.6), (3.5, 5.2), (3.5, 3.2)]
_QUOTERIGHT = [(3.6, 11), (3.6, 10.5), (2.4, 8.5)]


def _scale(strokes, k: float, dx: float, dy: float):
    out = []
    for kind, pts in strokes:
        out.append((kind, [(round(x * k + dx, 4), round(y * k + dy, 4)) for x, y in pts]))
    return out


STROKES_EXT = {
    # ---- rest of printable ASCII ----
    '&': [
        ("open", [(7, 0), (1.5, 6.5), (1.5, 9.6), (2.9, 11), (4.1, 11), (5.5, 9.6), (5.5, 8.6),
                  (0, 4), (0, 1.8), (1.8, 0), (3.6, 0), (7, 4.6)]),
    ],
    '@': [
        ("closed", OCT(2.2, 5, 3.2, 7.2, 0.9)),
        ("open", [(5, 7.2), (5, 3.2), (7, 3.2), (7, 8.8), (4.8, 11), (2.2, 11), (0, 8.8),
                  (0, 0.7), (2.2, -1.5), (6, -1.5)]),
    ],
    '$': [
        ("open", [(7, 10), (1.8, 10), (0, 8.2), (0, 7.4), (1.8, 5.6), (5.2, 5.6), (7, 3.8),
                  (7, 2.8), (5.2, 1), (0, 1)]),
        ("open", [(3.5, 10), (3.5, 12)]),
        ("open", [(3.5, 1), (3.5, -1)]),
    ],
    '^': [
        ("open", [(1, 7.4), (3.5, 11), (6, 7.4)]),
    ],
    '{': [
        ("open", [(5, 12), (4, 12), (3, 11), (3, 5.25), (2, 4.25), (3, 3.25), (3, -2.5), (4, -3.5), (5, -3.5)]),
    ],
    '}': [
        ("open", [(2, 12), (3, 12), (4, 11), (4, 5.25), (5, 4.25), (4, 3.25), (4, -2.5), (3, -3.5), (2, -3.5)]),
    ],
    '~': [
        ("open", [(0.6, 3.9), (1.9, 5.2), (2.9, 5.2), (4.1, 4.0), (5.1, 4.0), (6.4, 5.3)]),
    ],
    # ---- Latin-1 Supplement symbols ----
    '¡': [
        ("dot", [(3.5, 8)]),
        ("open", [(3.5, 4.8), (3.5, -3)]),
    ],
    '¢': [
        ("open", _C_LC),
        ("open", [(3.5, 9.5), (3.5, -1.5)]),
    ],
    '£': [
        ("open", [(6.6, 9.6), (5.2, 11), (3.6, 11), (2.2, 9.6), (2.2, 0)]),
        ("open", [(0.4, 5.4), (5, 5.4)]),
        ("open", [(0, 0), (7, 0)]),
    ],
    '¤': [
        ("closed", [(1.6, 2.6), (1.6, 6.6), (5.4, 6.6), (5.4, 2.6)]),
        ("open", [(1.6, 2.6), (0.4, 1.4)]),
        ("open", [(5.4, 2.6), (6.6, 1.4)]),
        ("open", [(1.6, 6.6), (0.4, 7.8)]),
        ("open", [(5.4, 6.6), (6.6, 7.8)]),
    ],
    '¥': [
        ("open", [(0, 11), (3.5, 5.5), (7, 11)]),
        ("open", [(3.5, 5.5), (3.5, 0)]),
        ("open", [(1, 4.8), (6, 4.8)]),
        ("open", [(1, 2), (6, 2)]),
    ],
    '¦': [
        ("open", [(3.5, 12), (3.5, 5.6)]),
        ("open", [(3.5, 2.9), (3.5, -3.5)]),
    ],
    '§': [
        ("closed", OCT(0.8, 6.2, 3.2, 7.8, 1.2)),
        ("open", [(6.2, 11), (1.9, 11), (0.8, 9.9), (0.8, 8.9), (1.9, 7.8)]),
        ("open", [(0.8, 0), (5.1, 0), (6.2, 1.1), (6.2, 2.1), (5.1, 3.2)]),
    ],
    '©': [
        ("closed", OCT(0, 7, 1, 10, 2)),
        ("open", [(5, 7.4), (3, 7.4), (2.2, 6.6), (2.2, 4.4), (3, 3.6), (5, 3.6)]),
    ],
    'ª': _scale(_A_LC, 0.55, 1.6, 6.2) + [("open", [(1.6, 4.6), (5.4, 4.6)])],
    # « and » are composites of ‹ and › (COMPOUNDS, Weft 0.2).
    '¬': [
        ("open", [(0.8, 6), (6.2, 6), (6.2, 3.2)]),
    ],
    '®': [
        ("closed", OCT(0, 7, 1, 10, 2)),
        ("open", [(2.4, 3.4), (2.4, 7.6), (4.2, 7.6), (4.8, 7.0), (4.8, 6.2), (4.2, 5.6), (2.4, 5.6)]),
        ("open", [(3.6, 5.6), (4.8, 3.4)]),
    ],
    '°': [
        ("closed", OCT(2, 5, 8, 11, 0.8)),
    ],
    '±': [
        ("open", [(3.5, 3.6), (3.5, 9)]),
        ("open", [(0.8, 6.3), (6.2, 6.3)]),
        ("open", [(0.8, 1.4), (6.2, 1.4)]),
    ],
    '²': _n2(2.2, 6.4),
    '³': _n3(2.2, 6.4),
    'µ': [
        ("open", [(0.5, 8), (0.5, -3.5)]),
        ("open", [(0.5, 2), (2.5, 0), (6.5, 0)]),
        ("open", [(6.5, 8), (6.5, 0)]),
    ],
    '¶': [
        ("open", [(3.4, 6.2), (2, 6.2), (0.6, 7.6), (0.6, 9.6), (2, 11), (6.2, 11)]),
        ("open", [(3.4, 11), (3.4, 0)]),
        ("open", [(5.6, 11), (5.6, 0)]),
    ],
    '·': [
        ("dot", [(3.5, 4.6)]),
    ],
    '¹': _n1(2.2, 6.4),
    'º': [
        ("closed", OCT(1.8, 5.2, 6.4, 10.6, 1)),
        ("open", [(1.6, 4.6), (5.4, 4.6)]),
    ],
    '¼': _n1(0, 6.4) + [_FRACTION_SLASH] + _n4(4.4, 0),
    '½': _n1(0, 6.4) + [_FRACTION_SLASH] + _n2(4.4, 0),
    '¾': _n3(0, 6.4) + [_FRACTION_SLASH] + _n4(4.4, 0),
    '¿': [
        ("open", _rot180(_QUESTION, 3.5, 4)),
        ("dot", [(3.5, 8)]),
    ],
    '×': [
        ("open", [(1.2, 2.3), (5.8, 6.9)]),
        ("open", [(5.8, 2.3), (1.2, 6.9)]),
    ],
    '÷': [
        ("open", [(0.8, 4.6), (6.2, 4.6)]),
        ("dot", [(3.5, 7.4)]),
        ("dot", [(3.5, 1.8)]),
    ],
    # ---- Latin-1 letters that are not accented forms ----
    'Æ': [
        ("open", [(0, 0), (0, 8.5), (2.5, 11), (7, 11)]),
        ("open", [(3.6, 11), (3.6, 0), (7, 0)]),
        ("open", [(0, 5.8), (6.2, 5.8)]),
    ],
    'Ð': [
        ("closed", [(0, 0), (0, 11), (4, 11), (7, 8), (7, 3), (4, 0)]),
        ("open", [(-1.2, 5.5), (2.8, 5.5)]),
    ],
    'Ø': [
        ("closed", _O_CAP),
        ("open", [(7.4, 11.8), (-0.4, -0.8)]),
    ],
    'Þ': [
        ("open", [(0, 0), (0, 11)]),
        ("open", [(0, 8.6), (5, 8.6), (7, 6.6), (7, 4.9), (5, 2.9), (0, 2.9)]),
    ],
    'ß': [
        ("open", [(0.5, 0), (0.5, 9.6), (1.9, 11), (4.7, 11), (6.1, 9.6), (6.1, 8.4), (4.5, 6.8), (3, 6.8)]),
        ("open", [(4.5, 6.8), (6.5, 4.8), (6.5, 1.6), (4.9, 0), (2.6, 0)]),
    ],
    'æ': [
        ("open", [(0.3, 8), (2.4, 8), (3.5, 6.9), (3.5, 1.1), (2.4, 0), (1.3, 0), (0.3, 1),
                  (0.3, 3.4), (1.3, 4.4), (3.5, 4.4)]),
        ("open", [(3.5, 4.4), (6.7, 4.4), (6.7, 6.9), (5.6, 8), (4.6, 8), (3.5, 6.9)]),
        ("open", [(3.5, 1.1), (4.6, 0), (6.6, 0)]),
    ],
    'ð': [
        ("closed", OCT(0.5, 6.5, 0, 7.6, 2)),
        ("open", [(6.5, 5.6), (6.5, 9.0), (4.0, 11.5), (2.0, 11.5)]),
        ("open", [(3.2, 9.0), (6.2, 11.0)]),
    ],
    'ø': [
        ("closed", _O_LC),
        ("open", [(6.9, 9), (0.1, -1)]),
    ],
    'þ': [
        ("open", [(0.5, 11.5), (0.5, -3.5)]),
        ("open", [(0.5, 8), (4.5, 8), (6.5, 6), (6.5, 2), (4.5, 0), (0.5, 0)]),
    ],
    'ı': [
        ("open", [(1.3, 8), (3.5, 8), (3.5, 0)]),
        ("open", [(1, 0), (6, 0)]),
    ],
    # ---- extras ----
    '€': [
        ("open", [(7, 11), (3.3, 11), (0.8, 8.5), (0.8, 2.5), (3.3, 0), (7, 0)]),
        ("open", [(-0.6, 7.0), (5, 7.0)]),
        ("open", [(-0.6, 4.0), (4.4, 4.0)]),
    ],
    '’': [
        ("open", _QUOTERIGHT),
    ],
    '‘': [
        ("open", _rot180(_QUOTERIGHT, 3.5, 9.75)),
    ],
    '…': [
        ("dot", [(0.5, 0)]),
        ("dot", [(3.5, 0)]),
        ("dot", [(6.5, 0)]),
    ],
    '•': [
        ("closed", OCT(2.4, 4.6, 3.5, 5.7, 0.6)),
        ("closed", [(2.9, 4.0), (2.9, 5.2), (4.1, 5.2), (4.1, 4.0)]),
        ("dot", [(3.5, 4.6)]),
    ],
    '₹': [
        ("open", [(0, 11), (7, 11)]),
        ("open", [(0, 8.2), (7, 8.2)]),
        ("open", [(4.2, 11), (5.6, 9.6), (5.6, 7.4), (4.2, 6), (0.6, 6)]),
        ("open", [(0.6, 6), (6.4, 0)]),
    ],
    # ---- Weft 0.2: Latin Extended-A letters that are not accented forms ----
    'Đ': [
        ("closed", [(0, 0), (0, 11), (4, 11), (7, 8), (7, 3), (4, 0)]),
        ("open", [(-1.2, 5.5), (2.8, 5.5)]),
    ],
    'đ': [
        ("open", [(6.5, 11.5), (6.5, 0)]),
        ("open", [(6.5, 8), (2.5, 8), (0.5, 6), (0.5, 2), (2.5, 0), (6.5, 0)]),
        ("open", [(5.0, 10.0), (8.0, 10.0)]),
    ],
    'Ħ': [
        ("open", [(0, 0), (0, 11)]),
        ("open", [(7, 0), (7, 11)]),
        ("open", [(0, 5.8), (7, 5.8)]),
        ("open", [(-1.0, 8.9), (8.0, 8.9)]),
    ],
    'ħ': [
        ("open", [(0.5, 11.5), (0.5, 0)]),
        ("open", [(0.5, 8), (4.5, 8), (6.5, 6), (6.5, 0)]),
        ("open", [(-1.0, 10.3), (2.2, 10.3)]),
    ],
    'Ŧ': [
        ("open", [(0, 11), (7, 11)]),
        ("open", [(3.5, 11), (3.5, 0)]),
        ("open", [(1.5, 5.5), (5.5, 5.5)]),
    ],
    'ŧ': [
        ("open", [(2.5, 10.6), (2.5, 2), (4.5, 0), (6.2, 0)]),
        ("open", [(0.5, 8), (5.8, 8)]),
        ("open", [(0.8, 5.0), (4.2, 5.0)]),
    ],
    'Ł': [
        ("open", [(0, 11), (0, 0), (7, 0)]),
        ("open", [(-0.8, 4.3), (2.6, 6.7)]),
    ],
    'ł': [
        ("open", [(1, 11.5), (3, 11.5), (3, 1.6), (4.6, 0), (6.4, 0)]),
        ("open", [(1.2, 4.8), (4.8, 7.4)]),
    ],
    'Ŀ': [
        ("open", [(0, 11), (0, 0), (7, 0)]),
        ("dot", [(3.6, 5.5)]),
    ],
    'ŀ': [
        ("open", [(1, 11.5), (3, 11.5), (3, 1.6), (4.6, 0), (6.4, 0)]),
        ("dot", [(6.0, 6.0)]),
    ],
    'ĸ': [
        ("open", [(0.5, 8), (0.5, 0)]),
        ("open", [(6.2, 8), (0.5, 3)]),
        ("open", [(2.7, 4.93), (6.5, 0)]),
    ],
    'Ĳ': [
        ("open", [(0.3, 11), (0.3, 0)]),
        ("open", [(3.4, 11), (6.6, 11), (6.6, 2.3), (4.3, 0), (3.6, 0)]),
    ],
    'ĳ': [
        ("open", [(1, 8), (1, 0)]),
        ("dot", [(1, 10.6)]),
        ("open", [(5.5, 8), (5.5, -1.5), (3.5, -3.5), (2.2, -3.5)]),
        ("dot", [(5.5, 10.6)]),
    ],
    'ŉ': [
        ("open", [(-0.2, 11), (-0.2, 10.5), (-0.9, 9.0)]),
        ("open", [(2.2, 0), (2.2, 8), (6.2, 8), (8.2, 6), (8.2, 0)]),
    ],
    'Ŋ': [
        ("open", [(0, 0), (0, 11), (4.5, 11), (7, 8.5), (7, -1.5), (5, -3.5), (3.4, -3.5)]),
    ],
    'ŋ': [
        ("open", [(0.5, 0), (0.5, 8), (4.5, 8), (6.5, 6), (6.5, -1.5), (4.5, -3.5), (2.8, -3.5)]),
    ],
    'Œ': [
        ("open", [(3.6, 11), (2.5, 11), (0, 8.5), (0, 2.5), (2.5, 0), (3.6, 0)]),
        ("open", [(7, 11), (3.6, 11), (3.6, 0), (7, 0)]),
        ("open", [(3.6, 5.8), (6.4, 5.8)]),
    ],
    'œ': [
        ("closed", OCT(0.3, 3.5, 0, 8, 1.2)),
        ("open", [(3.5, 4.4), (6.7, 4.4), (6.7, 6.8), (5.5, 8), (4.7, 8), (3.5, 6.8)]),
        ("open", [(3.5, 1.2), (4.7, 0), (6.6, 0)]),
    ],
    'ſ': [
        ("open", [(6.2, 11.5), (4, 11.5), (2.5, 10), (2.5, 0)]),
    ],
    'ȷ': [
        ("open", [(1.5, 8), (4.5, 8), (4.5, -1.5), (2.5, -3.5), (0.5, -3.5)]),
    ],
    'ẞ': [
        ("open", [(0, 0), (0, 8.5), (2.5, 11), (6.5, 11), (3.4, 6.4), (5, 6.4), (7, 4.4), (7, 2), (5, 0), (2.6, 0)]),
    ],
    # ---- Weft 0.2: punctuation and symbols ----
    '‹': [
        ("open", [(4.8, 7.2), (2.2, 4.6), (4.8, 2.0)]),
    ],
    '›': [
        ("open", [(2.2, 7.2), (4.8, 4.6), (2.2, 2.0)]),
    ],
    '‚': [
        ("open", [(3.6, 0.5), (3.6, 0), (2.4, -2)]),
    ],
    '−': [
        ("open", [(0.8, 4.6), (6.2, 4.6)]),
    ],
    # ---- Weft 0.2: arrows (the shaft stops short of the tip, inside the head) ----
    '←': [
        ("open", [(3, 7.6), (0, 4.6), (3, 1.6)]),
        ("open", [(0.8, 4.6), (7, 4.6)]),
    ],
    '→': [
        ("open", [(4, 7.6), (7, 4.6), (4, 1.6)]),
        ("open", [(0, 4.6), (6.2, 4.6)]),
    ],
    '↑': [
        ("open", [(0.5, 8), (3.5, 11), (6.5, 8)]),
        ("open", [(3.5, 0), (3.5, 10.2)]),
    ],
    '↓': [
        ("open", [(0.5, 3), (3.5, 0), (6.5, 3)]),
        ("open", [(3.5, 11), (3.5, 0.8)]),
    ],
}

# ---- Weft 0.2: box drawing. The lines end on the cell edges ("butt"
# strokes, no caps): x -2.5 and 9.5 (the 12-unit advance), y -4.5 and
# 14.5 (the typo descender and ascender, one line of 19 units). The
# horizontal line is at y 5, the middle of the line; the vertical line
# is at x 3.5, the middle of the cell.
_BH = ("butt", [(-2.5, 5), (9.5, 5)])
_BV = ("butt", [(3.5, -4.5), (3.5, 14.5)])
STROKES_EXT.update({
    '─': [_BH],
    '│': [_BV],
    '┌': [("butt", [(9.5, 5), (3.5, 5), (3.5, -4.5)])],
    '┐': [("butt", [(-2.5, 5), (3.5, 5), (3.5, -4.5)])],
    '└': [("butt", [(3.5, 14.5), (3.5, 5), (9.5, 5)])],
    '┘': [("butt", [(3.5, 14.5), (3.5, 5), (-2.5, 5)])],
    '├': [_BV, ("butt", [(3.5, 5), (9.5, 5)])],
    '┤': [_BV, ("butt", [(3.5, 5), (-2.5, 5)])],
    '┬': [_BH, ("butt", [(3.5, 5), (3.5, -4.5)])],
    '┴': [_BH, ("butt", [(3.5, 5), (3.5, 14.5)])],
    '┼': [_BH, _BV],
})

# Unencoded alternates, reached through OpenType features.
# ss01: the dotted zero (the default zero is slashed).
ALTERNATES = {
    "zero.ss01": [
        ("closed", OCT(0.6, 6.4, 0, 11, 2.4)),
        ("dot", [(3.5, 5.5)]),
    ],
}
FEATURES = """languagesystem DFLT dflt;
languagesystem latn dflt;

@TOP_MARKS = [gravecomb acutecomb uni0302 tildecomb uni0304 uni0306 uni0307 uni0308 uni030A uni030B uni030C];

# i and j lose their dot under a combining mark above.
feature ccmp {
    sub i' @TOP_MARKS by dotlessi;
    sub j' @TOP_MARKS by uni0237;
} ccmp;

feature ss01 {
    featureNames {
        name "Dotted zero";
    };
    sub zero by zero.ss01;
} ss01;
"""

# Accent components. Marks with a lowercase and a capital form end in
# ".lc" / ".case", the others in ".mark". Each one is drawn with its
# lowest centre line at y = 0. Marks that hang below the base ("base" kind: cedilla, ogonek)
# are drawn in place; "caronvert" (the apostrophe-like caron of d, l, t
# and L) is drawn in place at the top right and moved per glyph.
ACCENTS = {
    "grave.lc": [("open", [(2.8, 1.4), (4.2, 0)])],
    "acute.lc": [("open", [(2.8, 0), (4.2, 1.4)])],
    "circumflex.lc": [("open", [(1.9, 0), (3.5, 1.4), (5.1, 0)])],
    "tilde.lc": [("open", [(1.2, 0), (2.4, 1.2), (3.0, 1.2), (4.2, 0), (4.6, 0), (5.8, 1.2)])],
    "dieresis.lc": [("dot", [(1.9, 0.3)]), ("dot", [(5.1, 0.3)])],
    "ring.lc": [("closed", OCT(2.2, 4.8, 0, 2.2, 0.7))],
    "macron.lc": [("open", [(1.6, 0.6), (5.4, 0.6)])],
    "cedilla.lc": [("open", [(3.3, 0.5), (3.3, -0.8), (4.7, -1.7), (4.7, -2.4), (4.0, -3.1), (2.3, -3.1)])],
    "caron.lc": [("open", [(1.9, 1.4), (3.5, 0), (5.1, 1.4)])],
    "breve.lc": [("open", [(1.9, 1.4), (2.9, 0), (4.1, 0), (5.1, 1.4)])],
    "dotaccent.lc": [("dot", [(3.5, 0.3)])],
    "hungarumlaut.lc": [("open", [(1.6, 0), (2.4, 1.6)]), ("open", [(4.4, 0), (5.2, 1.6)])],
    "grave.case": [("open", [(2.6, 1.0), (4.4, 0)])],
    "acute.case": [("open", [(2.6, 0), (4.4, 1.0)])],
    "circumflex.case": [("open", [(1.8, 0), (3.5, 1.0), (5.2, 0)])],
    "tilde.case": [("open", [(1.2, 0), (2.2, 1.0), (3.0, 1.0), (4.0, 0), (4.8, 0), (5.8, 1.0)])],
    "dieresis.case": [("dot", [(1.9, 0.3)]), ("dot", [(5.1, 0.3)])],
    "ring.case": [("closed", OCT(2.2, 4.8, 0, 2.0, 0.7))],
    "macron.case": [("open", [(1.4, 0), (5.6, 0)])],
    "caron.case": [("open", [(1.8, 1.0), (3.5, 0), (5.2, 1.0)])],
    "breve.case": [("open", [(1.9, 1.0), (2.8, 0), (4.2, 0), (5.1, 1.0)])],
    "dotaccent.case": [("dot", [(3.5, 0.3)])],
    "hungarumlaut.case": [("open", [(1.6, 0), (2.4, 1.2)]), ("open", [(4.4, 0), (5.2, 1.2)])],
    # Marks without a .lc / .case pair.
    "ogonek.mark": [("open", [(3.5, 0.3), (2.6, -1.0), (2.6, -2.1), (3.3, -2.8), (4.5, -2.8)])],
    "commabelow.mark": [("open", [(3.6, 0), (3.6, -0.3), (2.8, -1.5)])],
    "commaturnedabove.mark": [("open", [(3.4, 0), (3.4, 0.4), (4.4, 1.9)])],
    "caronvert.mark": [("open", [(7, 11.5), (6.8, 10.0)])],
}

# The stroke widths of the wght masters (100, 400, 900). Offsets and
# scales below are given at these widths and are linear in between.
W_MASTERS = (0.6, 1.35, 2.6)


def pwl(w: float, values) -> float:
    """Return a value at stroke width w, piecewise linear between masters.

    `values` is a number (the same at every width) or one value per
    master width. Outside the master range the end segments extend.
    """
    if isinstance(values, (int, float)):
        return float(values)
    (w0, w1, w2), (v0, v1, v2) = W_MASTERS, values
    if w <= w1:
        return v0 + (v1 - v0) * (w - w0) / (w1 - w0)
    return v1 + (v2 - v1) * (w - w1) / (w2 - w1)


# Accents above the base grow at heavy weights, so their counters and
# gaps stay open: scale per master width, about (3.5, 0).
ACCENT_SCALE = (1.0, 1.0, 1.25)
# Gap (design units) between the base ink and the mark ink, per master
# width. Weft 0.1 had 0.6 (lc) and 0.5 (case) at every weight; Black was
# too tight.
ACCENT_GAP = {
    "lc": (0.6, 0.65, 0.95),
    "case": (0.5, 0.55, 0.95),
    "asc": (0.5, 0.55, 0.95),
    "below": (0.4, 0.45, 0.55),
}
# Top centre line of the base: x-height, cap height, ascender.
ACCENT_BASE_TOP = {"lc": 8.0, "case": 11.0, "asc": 11.5}


def is_scaled(accent: str) -> bool:
    """True for the accents that scale with weight (marks above)."""
    return accent.endswith((".lc", ".case")) and not accent.startswith("cedilla")


def accent_scale(accent: str, w: float) -> float:
    return pwl(w, ACCENT_SCALE) if is_scaled(accent) else 1.0


def _ink_line(strokes, pick) -> tuple[float, float]:
    """Return (a, b) with pick(ink y) = a + b * w (exact for straight strokes)."""
    from loom.outline import stroke_polygons  # local import: data module stays light

    def ink(w: float) -> float:
        return pick(y for kind, pts in strokes for poly in stroke_polygons(kind, pts, w, 2.4)
                    for _, y in poly)
    l1, l2 = ink(1.0), ink(2.0)
    return (2 * l1 - l2, l2 - l1)


ACCENT_LOW = {name: _ink_line(st, min) for name, st in ACCENTS.items()}
ACCENT_HIGH = {name: _ink_line(st, max) for name, st in ACCENTS.items()}


def accent_low(accent: str, w: float) -> float:
    """Return the lowest ink y of an accent as drawn at width w (scaled).

    The accent is drawn at width w / s and scaled by s about y = 0, so
    its stroke width is w: low = s * (a + b * w / s) = s * a + b * w.
    """
    a, b = ACCENT_LOW[accent]
    return accent_scale(accent, w) * a + b * w


def accent_offset(kind: str, width: float, accent: str | None = None) -> float:
    """Return the y offset (design units) of a mark component.

    Above ("lc", "case", "asc"): the base ink ends at top + w/2, the mark
    ink starts gap(w) higher. Below ("below"): the base ink ends at -w/2,
    the top of the mark ink is gap(w) lower. "base" and "abs" marks are
    drawn in place (offset 0).
    """
    if kind in ("base", "abs", "comp"):
        return 0.0
    gap = pwl(width, ACCENT_GAP[kind])
    if kind == "below":
        a, b = ACCENT_HIGH[accent]
        return -width / 2 - gap - (a + b * width)
    return ACCENT_BASE_TOP[kind] + width / 2 + gap - accent_low(accent, width)


# Accented letters: char -> (base char, accent, kind, dx, base dx). The
# accent is a name in ACCENTS, or a word that becomes "<word>.lc" /
# "<word>.case". kind None picks "case" for capitals and "lc" otherwise.
# dx moves the mark and base dx the base (a number, or one value per
# master width).
_ACCENTED = {
    'À': ('A', 'grave'), 'Á': ('A', 'acute'), 'Â': ('A', 'circumflex'), 'Ã': ('A', 'tilde'),
    'Ä': ('A', 'dieresis'), 'Å': ('A', 'ring'), 'Ç': ('C', 'cedilla'),
    'È': ('E', 'grave'), 'É': ('E', 'acute'), 'Ê': ('E', 'circumflex'), 'Ë': ('E', 'dieresis'),
    'Ì': ('I', 'grave'), 'Í': ('I', 'acute'), 'Î': ('I', 'circumflex'), 'Ï': ('I', 'dieresis'),
    'Ñ': ('N', 'tilde'),
    'Ò': ('O', 'grave'), 'Ó': ('O', 'acute'), 'Ô': ('O', 'circumflex'), 'Õ': ('O', 'tilde'),
    'Ö': ('O', 'dieresis'),
    'Ù': ('U', 'grave'), 'Ú': ('U', 'acute'), 'Û': ('U', 'circumflex'), 'Ü': ('U', 'dieresis'),
    'Ý': ('Y', 'acute'),
    'à': ('a', 'grave'), 'á': ('a', 'acute'), 'â': ('a', 'circumflex'), 'ã': ('a', 'tilde'),
    'ä': ('a', 'dieresis'), 'å': ('a', 'ring'), 'ç': ('c', 'cedilla'),
    'è': ('e', 'grave'), 'é': ('e', 'acute'), 'ê': ('e', 'circumflex'), 'ë': ('e', 'dieresis'),
    'ì': ('ı', 'grave'), 'í': ('ı', 'acute'), 'î': ('ı', 'circumflex'), 'ï': ('ı', 'dieresis'),
    'ñ': ('n', 'tilde'),
    'ò': ('o', 'grave'), 'ó': ('o', 'acute'), 'ô': ('o', 'circumflex'), 'õ': ('o', 'tilde'),
    'ö': ('o', 'dieresis'),
    'ù': ('u', 'grave'), 'ú': ('u', 'acute'), 'û': ('u', 'circumflex'), 'ü': ('u', 'dieresis'),
    'ý': ('y', 'acute'), 'ÿ': ('y', 'dieresis'),
    # ---- Weft 0.2: Latin Extended-A ----
    'Ā': ('A', 'macron'), 'ā': ('a', 'macron'),
    'Ă': ('A', 'breve'), 'ă': ('a', 'breve'),
    'Ą': ('A', 'ogonek', 'base', 3.1), 'ą': ('a', 'ogonek', 'base', 2.8),
    'Ć': ('C', 'acute'), 'ć': ('c', 'acute'),
    'Ĉ': ('C', 'circumflex'), 'ĉ': ('c', 'circumflex'),
    'Ċ': ('C', 'dotaccent'), 'ċ': ('c', 'dotaccent'),
    'Č': ('C', 'caron'), 'č': ('c', 'caron'),
    'Ď': ('D', 'caron'), 'ď': ('d', 'caronvert', 'abs', (0.95, 1.6, 1.05), (0.0, -0.2, -2.0)),
    'Ē': ('E', 'macron'), 'ē': ('e', 'macron'),
    'Ĕ': ('E', 'breve'), 'ĕ': ('e', 'breve'),
    'Ė': ('E', 'dotaccent'), 'ė': ('e', 'dotaccent'),
    'Ę': ('E', 'ogonek', 'base', 2.0), 'ę': ('e', 'ogonek', 'base', 1.4),
    'Ě': ('E', 'caron'), 'ě': ('e', 'caron'),
    'Ĝ': ('G', 'circumflex'), 'ĝ': ('g', 'circumflex'),
    'Ğ': ('G', 'breve'), 'ğ': ('g', 'breve'),
    'Ġ': ('G', 'dotaccent'), 'ġ': ('g', 'dotaccent'),
    'Ģ': ('G', 'commabelow', 'below'), 'ģ': ('g', 'commaturnedabove', 'lc'),
    'Ĥ': ('H', 'circumflex'), 'ĥ': ('h', 'circumflex.case', 'asc', -2.0),
    'Ĩ': ('I', 'tilde'), 'ĩ': ('ı', 'tilde'),
    'Ī': ('I', 'macron'), 'ī': ('ı', 'macron'),
    'Ĭ': ('I', 'breve'), 'ĭ': ('ı', 'breve'),
    'Į': ('I', 'ogonek', 'base', 1.1), 'į': ('i', 'ogonek', 'base', 1.0),
    'İ': ('I', 'dotaccent'),
    'Ĵ': ('J', 'circumflex', None, 1.0), 'ĵ': ('ȷ', 'circumflex', None, 1.0),
    'Ķ': ('K', 'commabelow', 'below'), 'ķ': ('k', 'commabelow', 'below'),
    'Ĺ': ('L', 'acute', None, -2.0), 'ĺ': ('l', 'acute.case', 'asc', -0.5),
    'Ļ': ('L', 'commabelow', 'below'), 'ļ': ('l', 'commabelow', 'below', 2.0),
    'Ľ': ('L', 'caronvert', 'abs', (-5.55, -4.7, -3.1)), 'ľ': ('l', 'caronvert', 'abs', (-2.55, -1.7, -0.1)),
    'Ń': ('N', 'acute'), 'ń': ('n', 'acute'),
    'Ņ': ('N', 'commabelow', 'below'), 'ņ': ('n', 'commabelow', 'below'),
    'Ň': ('N', 'caron'), 'ň': ('n', 'caron'),
    'Ō': ('O', 'macron'), 'ō': ('o', 'macron'),
    'Ŏ': ('O', 'breve'), 'ŏ': ('o', 'breve'),
    'Ő': ('O', 'hungarumlaut'), 'ő': ('o', 'hungarumlaut'),
    'Ŕ': ('R', 'acute'), 'ŕ': ('r', 'acute'),
    'Ŗ': ('R', 'commabelow', 'below'), 'ŗ': ('r', 'commabelow', 'below', -3.0),
    'Ř': ('R', 'caron'), 'ř': ('r', 'caron'),
    'Ś': ('S', 'acute'), 'ś': ('s', 'acute'),
    'Ŝ': ('S', 'circumflex'), 'ŝ': ('s', 'circumflex'),
    'Ş': ('S', 'cedilla'), 'ş': ('s', 'cedilla'),
    'Š': ('S', 'caron'), 'š': ('s', 'caron'),
    'Ţ': ('T', 'cedilla'), 'ţ': ('t', 'cedilla', None, 0.6),
    'Ť': ('T', 'caron'), 'ť': ('t', 'caronvert', 'abs', (-3.05, -2.2, -0.6)),
    'Ũ': ('U', 'tilde'), 'ũ': ('u', 'tilde'),
    'Ū': ('U', 'macron'), 'ū': ('u', 'macron'),
    'Ŭ': ('U', 'breve'), 'ŭ': ('u', 'breve'),
    'Ů': ('U', 'ring'), 'ů': ('u', 'ring'),
    'Ű': ('U', 'hungarumlaut'), 'ű': ('u', 'hungarumlaut'),
    'Ų': ('U', 'ogonek', 'base', 1.0), 'ų': ('u', 'ogonek', 'base', 2.6),
    'Ŵ': ('W', 'circumflex'), 'ŵ': ('w', 'circumflex'),
    'Ŷ': ('Y', 'circumflex'), 'ŷ': ('y', 'circumflex'),
    'Ÿ': ('Y', 'dieresis'),
    'Ź': ('Z', 'acute'), 'ź': ('z', 'acute'),
    'Ż': ('Z', 'dotaccent'), 'ż': ('z', 'dotaccent'),
    'Ž': ('Z', 'caron'), 'ž': ('z', 'caron'),
    'Ǿ': ('Ø', 'acute'), 'ǿ': ('ø', 'acute'),
    # Auxiliary letters (shaperglot: Lithuanian, French, Norwegian).
    'Ǎ': ('A', 'caron'), 'ǎ': ('a', 'caron'), 'Ǔ': ('U', 'caron'), 'ǔ': ('u', 'caron'),
    'Ẽ': ('E', 'tilde'), 'ẽ': ('e', 'tilde'),
    # ---- Weft 0.2: Romanian comma below ----
    'Ș': ('S', 'commabelow', 'below'), 'ș': ('s', 'commabelow', 'below'),
    'Ț': ('T', 'commabelow', 'below'), 'ț': ('t', 'commabelow', 'below', 0.4),
}

# The offsets of the vertical caron (ď ľ ť Ľ) give a gap of 0.6, 0.65 and
# 0.95 units to the stem at the three master widths (0.6 for ď at Black,
# where d also moves left, so the caron stays inside the cell).
# The caron of t sits above the cross bar: it moves up at heavy weights.
ABS_DY = {'ť': (0.0, 0.4, 1.7)}

# Guillemets and double quotes: two copies of the single form. They move
# apart at heavy weights so the space between them stays open (in Weft
# 0.1 the guillemets were too tight at Black and the double quotes
# merged). At Regular they are where Weft 0.1 drew them.
GUILLEMET_DX = (2.0, 2.2, 2.55)
QUOTE_DX = (1.2, 1.2, 1.75)
_COMPOUND = {
    '«': ('‹', GUILLEMET_DX),
    '»': ('›', GUILLEMET_DX),
    '"': ("'", QUOTE_DX),
    '“': ('‘', QUOTE_DX),
    '”': ('’', QUOTE_DX),
    '„': ('‚', QUOTE_DX),
}

# Spacing accents: char -> accent. They sit at the lowercase accent
# height (the cedilla and the ogonek hang from the baseline).
_SPACING = {
    '`': "grave.lc", '´': "acute.lc", '¨': "dieresis.lc", '¯': "macron.lc", '¸': "cedilla.lc",
    'ˆ': "circumflex.lc", 'ˇ': "caron.lc", '˘': "breve.lc", '˙': "dotaccent.lc",
    '˚': "ring.lc", '˛': "ogonek.mark", '˜': "tilde.lc", '˝': "hungarumlaut.lc",
}


def _resolve(base: str, accent: str, kind: str | None) -> tuple[str, str]:
    if kind is None:
        kind = "base" if accent == "cedilla" else ("case" if base.isupper() else "lc")
    if accent in ACCENTS:
        return accent, kind
    if f"{accent}.mark" in ACCENTS:
        return f"{accent}.mark", kind
    if kind == "base":
        return f"{accent}.lc", kind
    return f"{accent}.{'case' if kind in ('case', 'asc') else 'lc'}", kind


def _composites():
    comps = {}
    for ch, spec in _ACCENTED.items():
        base, word = spec[0], spec[1]
        kind = spec[2] if len(spec) > 2 else None
        dx = spec[3] if len(spec) > 3 else 0.0
        accent, kind = _resolve(base, word, kind)
        comps[ch] = (base, accent, kind, dx)
        if len(spec) > 4:
            BASE_DX[ch] = spec[4]
    for ch, accent in _SPACING.items():
        kind = "base" if accent in ("cedilla.lc", "ogonek.mark") else "lc"
        comps[ch] = (None, accent, kind, 0.0)
    return comps


BASE_DX: dict = {}
# char -> (base char or None, accent name, offset kind, dx spec)
COMPOSITES = _composites()
# char -> (single form, dx spec) for the guillemets and double quotes.
COMPOUNDS = dict(_COMPOUND)


# Combining marks (Weft 0.2): char -> (accent, anchor name). They have
# no advance and sit over the previous cell (dx -12 units), at the
# lowercase accent height. The mark feature moves them to the anchor of
# the base (see base_anchors), so they also work on capitals.
COMBINING = {
    '\u0300': ("grave.lc", "top"), '\u0301': ("acute.lc", "top"),
    '\u0302': ("circumflex.lc", "top"), '\u0303': ("tilde.lc", "top"),
    '\u0304': ("macron.lc", "top"), '\u0306': ("breve.lc", "top"),
    '\u0307': ("dotaccent.lc", "top"), '\u0308': ("dieresis.lc", "top"),
    '\u030A': ("ring.lc", "top"), '\u030B': ("hungarumlaut.lc", "top"),
    '\u030C': ("caron.lc", "top"), '\u0326': ("commabelow.mark", "bottom"),
    '\u0327': ("cedilla.lc", "cedilla"), '\u0328': ("ogonek.mark", "ogonek"),
}
CELL = 12.0  # the advance in design units

# Letters with an ascender: marks above go over the ascender.
_ASCENDERS = set("bdhklt")
# Letters that carry the mark anchors.
ANCHOR_BASES = [chr(c) for c in range(0x41, 0x5B)] + [chr(c) for c in range(0x61, 0x7B)] + ['ı', 'ȷ']


def _top_kind(ch: str) -> str:
    if ch.isupper():
        return "case"
    return "asc" if ch in _ASCENDERS else "lc"


def mark_anchor_y(anchor: str, w: float, kind: str = "lc") -> float:
    """Return the y (design units) of a mark anchor at stroke width w."""
    if anchor == "top":
        return ACCENT_BASE_TOP[kind] + w / 2 + pwl(w, ACCENT_GAP[kind])
    if anchor == "bottom":
        return -w / 2 - pwl(w, ACCENT_GAP["below"])
    return 0.0  # cedilla, ogonek: they hang from the baseline


def base_anchors(ch: str, w: float) -> dict[str, tuple[float, float]]:
    """Return {anchor: (x, y)} in design units (box x) for a base letter."""
    out = {"top": (3.5, mark_anchor_y("top", w, _top_kind(ch))),
           "bottom": (3.5, mark_anchor_y("bottom", w))}
    # Cedilla and ogonek: where the precomposed letters put them.
    for mark, name in (("cedilla.lc", "cedilla"), ("ogonek.mark", "ogonek")):
        for comp, (base, accent, kind, dx) in COMPOSITES.items():
            if base == ch and accent == mark:
                out[name] = (3.5 + pwl(w, dx), 0.0)
                break
        else:
            if name == "cedilla":
                out[name] = (3.5, 0.0)
    return out


def mark_anchor(ch: str, w: float) -> tuple[str, tuple[float, float]]:
    """Return (anchor name, (x, y)) of a combining mark, in its own cell."""
    accent, anchor = COMBINING[ch]
    return anchor, (3.5 - CELL, mark_anchor_y(anchor, w))


def parts(ch: str, w: float) -> list[tuple[str, float, float]]:
    """Return the components of a composite at stroke width w.

    Each part is (char or accent name, dx, dy) in design units. A char
    names a drawn glyph (or ı, ȷ); an accent name is a key of ACCENTS.
    """
    if ch in COMBINING:
        accent, anchor = COMBINING[ch]
        kind = {"top": "lc", "bottom": "below"}.get(anchor, "base")
        return [(accent, -CELL, accent_offset(kind, w, accent))]
    if ch in COMPOUNDS:
        single, dx = COMPOUNDS[ch]
        d = pwl(w, dx)
        return [(single, -d, 0.0), (single, d, 0.0)]
    base, accent, kind, dx = COMPOSITES[ch]
    out = []
    if base is not None:
        out.append((base, pwl(w, BASE_DX.get(ch, 0.0)), 0.0))
    dy = accent_offset(kind, w, accent)
    if kind == "abs":
        dy += pwl(w, ABS_DY.get(ch, 0.0))
    out.append((accent, pwl(w, dx), dy))
    return out


# Production glyph names (AGL) for the new characters.
GLYPH_NAMES_EXT = {
    "&": "ampersand", "@": "at", "$": "dollar", "^": "asciicircum", "`": "grave",
    "{": "braceleft", "}": "braceright", "~": "asciitilde",
    "¡": "exclamdown", "¢": "cent", "£": "sterling", "¤": "currency", "¥": "yen",
    "¦": "brokenbar", "§": "section", "¨": "dieresis", "©": "copyright",
    "ª": "ordfeminine", "«": "guillemotleft", "¬": "logicalnot", "®": "registered",
    "¯": "macron", "°": "degree", "±": "plusminus", "²": "twosuperior",
    "³": "threesuperior", "´": "acute", "µ": "mu", "¶": "paragraph",
    "·": "periodcentered", "¸": "cedilla", "¹": "onesuperior", "º": "ordmasculine",
    "»": "guillemotright", "¼": "onequarter", "½": "onehalf", "¾": "threequarters",
    "¿": "questiondown", "×": "multiply", "÷": "divide",
    "Æ": "AE", "Ð": "Eth", "Ø": "Oslash", "Þ": "Thorn", "ß": "germandbls",
    "æ": "ae", "ð": "eth", "ø": "oslash", "þ": "thorn", "ı": "dotlessi",
    "€": "Euro", "’": "quoteright", "‘": "quoteleft", "”": "quotedblright",
    "“": "quotedblleft", "…": "ellipsis", "•": "bullet", "₹": "uni20B9",
    # Weft 0.2
    "Đ": "Dcroat", "đ": "dcroat", "Ħ": "Hbar", "ħ": "hbar", "Ŧ": "Tbar", "ŧ": "tbar",
    "Ł": "Lslash", "ł": "lslash", "Ŀ": "Ldot", "ŀ": "ldot", "ĸ": "kgreenlandic",
    "Ĳ": "IJ", "ĳ": "ij", "ŉ": "napostrophe", "Ŋ": "Eng", "ŋ": "eng",
    "Œ": "OE", "œ": "oe", "ſ": "longs", "ȷ": "uni0237",
    "‹": "guilsinglleft", "›": "guilsinglright", "‚": "quotesinglbase",
    "„": "quotedblbase", "−": "minus",
    "←": "arrowleft", "→": "arrowright", "↑": "arrowup", "↓": "arrowdown",
    "ˆ": "circumflex", "ˇ": "caron", "˘": "breve", "˙": "dotaccent", "˚": "ring",
    "˛": "ogonek", "˜": "tilde", "˝": "hungarumlaut",
    "İ": "Idotaccent", "Ș": "uni0218", "ș": "uni0219", "Ț": "uni021A", "ț": "uni021B",
    "Ģ": "Gcommaaccent", "ģ": "gcommaaccent", "Ķ": "Kcommaaccent", "ķ": "kcommaaccent",
    "Ļ": "Lcommaaccent", "ļ": "lcommaaccent", "Ņ": "Ncommaaccent", "ņ": "ncommaaccent",
    "Ŗ": "Rcommaaccent", "ŗ": "rcommaaccent", "Ő": "Ohungarumlaut", "ő": "ohungarumlaut",
    "Ű": "Uhungarumlaut", "ű": "uhungarumlaut",
    "ẞ": "uni1E9E", "Ǿ": "Oslashacute", "ǿ": "oslashacute",
    "Ǎ": "uni01CD", "ǎ": "uni01CE", "Ǔ": "uni01D3", "ǔ": "uni01D4", "Ẽ": "uni1EBC", "ẽ": "uni1EBD",
    "\u0300": "gravecomb", "\u0301": "acutecomb", "\u0303": "tildecomb",
}
for _ch in COMBINING:
    GLYPH_NAMES_EXT.setdefault(_ch, f"uni{ord(_ch):04X}")
for _cp in range(0x2500, 0x2580):
    if chr(_cp) in STROKES_EXT:
        GLYPH_NAMES_EXT[chr(_cp)] = f"uni{_cp:04X}"
for _ch, _spec in _ACCENTED.items():
    if _ch not in GLYPH_NAMES_EXT:
        _base = {"ı": "i", "ȷ": "j"}.get(_spec[0], _spec[0])
        _word = _spec[1].split(".")[0]
        _word = {"caronvert": "caron", "commabelow": "commaaccent"}.get(_word, _word)
        GLYPH_NAMES_EXT[_ch] = _base + _word
