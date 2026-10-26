"""Weft glyph data for Weft 0.1 beyond sketch 0.1.

This file holds plain data only, in the same form as loom/glyphs.py:
centre-line strokes in design units, x in the 7-unit design box, y from
the baseline. The shapes follow the sketch rules: centre-line strokes,
octagonal bowls cut at 45 degrees, square shoulders, square caps.

Contents:

* New drawings: the rest of printable ASCII, the Latin-1 Supplement
  symbols and letters that are not accented forms, and the extras
  (Euro, curly quotes, ellipsis, bullet, rupee, dotless i).
* Accent components (".lc" for lowercase, ".case" for capitals).
* COMPOSITES: accented letters and spacing accents, built from a base
  glyph and an accent component. The accent offset depends on the stroke
  width (see accent_offset), so accents clear the base at every weight.

Do not trace, import or copy outlines from other fonts.

Licence: this table defines font outlines, so it is Font Software under
the SIL Open Font License 1.1 (see OFL.txt), Reserved Font Name
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
    '«': [
        ("open", [(2.6, 7.2), (0, 4.6), (2.6, 2.0)]),
        ("open", [(7, 7.2), (4.4, 4.6), (7, 2.0)]),
    ],
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
    '»': [
        ("open", [(0, 7.2), (2.6, 4.6), (0, 2.0)]),
        ("open", [(4.4, 7.2), (7, 4.6), (4.4, 2.0)]),
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
    '”': [
        ("open", _move(_QUOTERIGHT, -1.2)),
        ("open", _move(_QUOTERIGHT, 1.2)),
    ],
    '“': [
        ("open", _move(_rot180(_QUOTERIGHT, 3.5, 9.75), -1.2)),
        ("open", _move(_rot180(_QUOTERIGHT, 3.5, 9.75), 1.2)),
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
}

# Accent components. Each one is drawn with its lowest centre line at
# y = 0 (the cedilla hangs from the baseline instead). accent_offset()
# gives the vertical offset in the composite.
ACCENTS = {
    "grave.lc": [("open", [(2.8, 1.4), (4.2, 0)])],
    "acute.lc": [("open", [(2.8, 0), (4.2, 1.4)])],
    "circumflex.lc": [("open", [(1.9, 0), (3.5, 1.4), (5.1, 0)])],
    "tilde.lc": [("open", [(1.2, 0), (2.4, 1.2), (3.0, 1.2), (4.2, 0), (4.6, 0), (5.8, 1.2)])],
    "dieresis.lc": [("dot", [(1.9, 0.3)]), ("dot", [(5.1, 0.3)])],
    "ring.lc": [("closed", OCT(2.3, 4.7, 0, 2.0, 0.6))],
    "macron.lc": [("open", [(1.6, 0.6), (5.4, 0.6)])],
    "cedilla.lc": [("open", [(3.3, 0.5), (3.3, -0.8), (4.7, -1.7), (4.7, -2.4), (4.0, -3.1), (2.3, -3.1)])],
    "grave.case": [("open", [(2.6, 1.0), (4.4, 0)])],
    "acute.case": [("open", [(2.6, 0), (4.4, 1.0)])],
    "circumflex.case": [("open", [(1.8, 0), (3.5, 1.0), (5.2, 0)])],
    "tilde.case": [("open", [(1.2, 0), (2.2, 1.0), (3.0, 1.0), (4.0, 0), (4.8, 0), (5.8, 1.0)])],
    "dieresis.case": [("dot", [(1.9, 0.3)]), ("dot", [(5.1, 0.3)])],
    "ring.case": [("closed", OCT(2.4, 4.6, 0, 1.8, 0.6))],
}

# Gap (design units) between the top of the base ink and the bottom of
# the accent ink.
ACCENT_GAP = {"lc": 0.6, "case": 0.5}
# Top centre line of the base: x-height for lowercase, cap height for
# capitals.
ACCENT_BASE_TOP = {"lc": 8.0, "case": 11.0}


def accent_offset(kind: str, width: float, accent: str | None = None) -> float:
    """Return the y offset (design units) of an accent component.

    The base ink ends at top + w/2. The accent ink starts at offset +
    low(w), where low(w) is the lowest ink point of the accent (linear in
    w: square caps of a slanted stroke reach below the centre line). So
    the offset is top + w/2 + gap - low(w). It is linear in w, so it
    interpolates.
    """
    if kind == "base":
        return 0.0
    low = ACCENT_LOW.get(accent, (0.0, -0.5))
    return ACCENT_BASE_TOP[kind] + width / 2 + ACCENT_GAP[kind] - (low[0] + low[1] * width)


def _accent_low(strokes) -> tuple[float, float]:
    """Return (a, b) with lowest ink y = a + b * w (exact for straight strokes)."""
    from loom.outline import stroke_polygons  # local import: data module stays light

    def low(w: float) -> float:
        return min(y for kind, pts in strokes for poly in stroke_polygons(kind, pts, w, 2.4)
                   for _, y in poly)
    l1, l2 = low(1.0), low(2.0)
    return (2 * l1 - l2, l2 - l1)


ACCENT_LOW = {name: _accent_low(st) for name, st in ACCENTS.items()}


_ACCENT_WORDS = {
    "GRAVE": "grave", "ACUTE": "acute", "CIRCUMFLEX": "circumflex",
    "TILDE": "tilde", "DIAERESIS": "dieresis", "RING ABOVE": "ring",
    "CEDILLA": "cedilla",
}

# Accented letters: char -> (base char, accent word).
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
}


def _composites():
    comps = {}
    for ch, (base, accent) in _ACCENTED.items():
        if accent == "cedilla":
            comps[ch] = (base, f"{accent}.lc", "base")
        elif base.isupper():
            comps[ch] = (base, f"{accent}.case", "case")
        else:
            comps[ch] = (base, f"{accent}.lc", "lc")
    # Spacing accents: an empty base (None) and the lowercase accent.
    comps['`'] = (None, "grave.lc", "lc")
    comps['´'] = (None, "acute.lc", "lc")
    comps['¨'] = (None, "dieresis.lc", "lc")
    comps['¯'] = (None, "macron.lc", "lc")
    comps['¸'] = (None, "cedilla.lc", "base")
    return comps


# char -> (base char or None, accent component name, offset kind)
COMPOSITES = _composites()

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
}
for _ch, (_base, _acc) in _ACCENTED.items():
    GLYPH_NAMES_EXT[_ch] = ("i" if _base == "ı" else _base) + _acc
