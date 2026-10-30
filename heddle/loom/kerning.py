"""Heddle kerning: a small class kerning for display use.

Classes cover the pairs that open up most in headlines: A V W Y T L P F
against round lowercase and capitals, and punctuation. 0.2 adds
lowercase pairs (v w y k x r f t against round letters) and figures
against punctuation (7 and the round figures before . and ,). The
default figures are tabular, so figures do not kern with each other
(Fontspector tabular_kerning). Values are in
font units at wdth 100 and scale with the width axis. Tests check that
no kerned pair makes two glyphs touch, in any master.

Licence: Font Software under the SIL Open Font License 1.1 (see
heddle/OFL.txt), as this table sets the spacing of the fonts.
"""

from __future__ import annotations

from loom import glyphs as G


def _with_accents(*bases: str) -> list[str]:
    out = list(bases)
    for name, c in sorted(G.COMPOSITES.items()):
        if c.base in bases and not c.row:
            out.append(name)
    return out


# Left side of a pair: the glyph's right side.
KERN1 = {
    "A": _with_accents("A"),
    "V": ["V"],
    "W": ["W"],
    "Y": _with_accents("Y"),
    "T": ["T"],
    "L": ["L"],
    "P": ["P", "Thorn"],
    "F": ["F"],
    "O": _with_accents("O", "D", "Q") + ["Oslash", "Eth"],
    "v": _with_accents("v", "w", "y"),
    "r": _with_accents("r"),
    # 0.2: lowercase and figures.
    "or": _with_accents("o", "b", "p") + ["oslash", "thorn"],
    "f": ["f"],
    "k": ["k", "x", "kgreenlandic"] + _with_accents("k")[1:],
    "t": _with_accents("t")[1:] + ["t", "tbar"],
    "seven": ["seven"],
    "figround": ["zero", "six", "eight", "nine", "three"],
}

# Right side of a pair: the glyph's left side.
KERN2 = {
    "o": _with_accents("o", "c", "d", "e", "g", "q") + ["oslash", "oe", "eth"],
    "a": _with_accents("a") + ["ae"],
    "O": _with_accents("O", "C", "G", "Q") + ["Oslash", "OE"],
    "A": _with_accents("A") + ["AE"],
    "V": ["V"],
    "W": ["W"],
    "Y": _with_accents("Y"),
    "T": ["T"],
    "period": ["period", "comma", "ellipsis", "quotesinglbase", "quotedblbase"],
    "hyphen": ["hyphen", "endash", "emdash"],
    # 0.2: lowercase and figures.
    "v": _with_accents("v", "w", "y"),
    "x": ["x"],
}

# (left class, right class): value at wdth 100.
PAIRS = {
    ("A", "V"): -60, ("A", "W"): -40, ("A", "Y"): -60, ("A", "T"): -55, ("A", "O"): -20,
    ("V", "A"): -60, ("W", "A"): -40, ("Y", "A"): -60, ("T", "A"): -55,
    ("P", "A"): -45, ("F", "A"): -40,
    ("L", "T"): -70, ("L", "V"): -65, ("L", "W"): -45, ("L", "Y"): -70, ("L", "O"): -20,
    ("T", "o"): -75, ("T", "a"): -70, ("V", "o"): -50, ("V", "a"): -50,
    ("W", "o"): -35, ("W", "a"): -35, ("Y", "o"): -70, ("Y", "a"): -65,
    ("P", "o"): -20, ("P", "a"): -20, ("F", "o"): -20, ("F", "a"): -20,
    ("T", "period"): -80, ("V", "period"): -70, ("W", "period"): -50, ("Y", "period"): -80,
    ("P", "period"): -90, ("F", "period"): -80,
    ("O", "A"): -20, ("O", "V"): -25, ("O", "W"): -15, ("O", "Y"): -30, ("O", "T"): -20,
    ("O", "period"): -25,
    ("v", "period"): -45, ("r", "period"): -40,
    ("T", "hyphen"): -40, ("V", "hyphen"): -30, ("W", "hyphen"): -20, ("Y", "hyphen"): -40,
    # 0.2: lowercase pairs.
    ("v", "o"): -20, ("v", "a"): -15, ("or", "v"): -20, ("or", "x"): -15,
    ("r", "o"): -15, ("r", "a"): -12, ("f", "o"): -15, ("f", "a"): -10, ("f", "period"): -35,
    ("k", "o"): -20, ("t", "o"): -10, ("v", "v"): -10,
    # 0.2: figures.
    ("seven", "period"): -70, ("seven", "hyphen"): -20, ("figround", "period"): -15,
}


def groups() -> dict[str, list[str]]:
    out = {f"public.kern1.{k}": v for k, v in KERN1.items()}
    out.update({f"public.kern2.{k}": v for k, v in KERN2.items()})
    return out


def kerning(p: G.Params) -> dict[tuple[str, str], int]:
    """Return the kerning of one master (class pairs, rounded)."""
    return {(f"public.kern1.{a}", f"public.kern2.{b}"): round(v * p.wf)
            for (a, b), v in PAIRS.items()}
