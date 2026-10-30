"""Class kerning for machine-made Warp.

Starts from the sketch's kerning table (`sketch_kern` in loom/sketch.py:
To Te Ta Tr Ty TA T. Av Aw AV AT AY A' Va Ve Vo Ya Yo LT LV LY L' P. P,
F. r. f' quotes and others) and turns it into classes: accented letters
and Greek letters join the class of their Latin look-alike, so that
Tά, Ταυ, ΓΑ, ΥΑ and Àv kern like To, TA and Av. Figures: the
proportional styles (lf, osf) get a few pairs; the default tabular
figures are not kerned. Italic uses 70 % of the values, as in the
sketch.

This file defines the spacing of machine-made Warp: SIL Open Font
License 1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

from loom import charset as CS


def _names(chars: str, extra: tuple = ()) -> list[str]:
    out = []
    for ch in chars:
        n = CS.glyph_name(ch)
        if n in CS.BY_NAME:
            out.append(n)
    out += [n for n in extra if n in CS.BY_NAME]
    return out


# First glyph (its right side).
KERN1 = {
    "A": _names("AÀÁÂÃÄÅΑΔΛĀĂĄ"),
    "T": _names("TΤΓŢŤȚŦ"),
    "V": _names("VWŴ"),
    "Y": _names("YÝŸΥŶ"),
    "L": _names("LĹĻŁ"),
    "P": _names("PΡÞ"),
    "F": _names("F"),
    "R": _names("RŔŖŘ"),
    "K": _names("KΚXΧĶ"),
    "r": _names("rŕŗř"),
    "f": _names("f"),
    "k": _names("kκķĸ"),
    "o": _names("oòóôõöøbpþοσōŏő"),
    "v": _names("vwyýÿνγχŵŷ"),
    "x": _names("x"),
    "tau": _names("τ"),
    "e": _names("eèéêëēĕėęě"),
    "quote": _names("'’\"”"),
    "seven": ["seven.lf", "seven.osf"],
}

# Second glyph (its left side).
KERN2 = {
    "a": _names("aàáâãäåæαāăą"),
    "o": _names("ceoqdgçèéêëòóôõöøœðοσεθδφςωćĉċčďđēĕėęěĝğġģōŏő"),
    "s": _names("sśŝşšș"),
    "u": _names("ruùúûüıυικμŕŗřũūŭůűų"),
    "n": _names("nmpñηπρńņňŋ"),
    "v": _names("vwyýÿνγχŵŷ"),
    "x": _names("x"),
    "A": _names("AÀÁÂÃÄÅÆΑΔΛĀĂĄ"),
    "O": _names("CGOQÇÒÓÔÕÖØŒΘΟΩĆĈĊČĜĞĠĢŌŎŐ"),
    "J": _names("JĴ"),
    "T": _names("TΤŢŤȚŦ"),
    "V": _names("VWŴ"),
    "Y": _names("YÝŸΥŶ"),
    "quote": _names("'’\"”"),
    "period": _names(".,…‚„"),
    "close": _names(")]}?!"),
    "four": ["four.lf", "four.osf"],
}

# (first class, second class): value in font units (roman).
PAIRS = {
    ("T", "o"): -62, ("T", "a"): -62, ("T", "s"): -62, ("T", "u"): -62, ("T", "n"): -40,
    ("T", "v"): -45, ("T", "A"): -55, ("T", "period"): -70, ("T", "J"): -40,
    ("A", "T"): -58, ("A", "V"): -58, ("A", "Y"): -58, ("A", "v"): -34, ("A", "quote"): -60, ("A", "O"): -18,
    ("V", "a"): -46, ("V", "o"): -46, ("V", "period"): -70, ("V", "A"): -55, ("V", "u"): -24,
    ("Y", "a"): -64, ("Y", "o"): -64, ("Y", "period"): -80, ("Y", "A"): -60, ("Y", "u"): -36,
    ("L", "T"): -70, ("L", "V"): -70, ("L", "Y"): -70, ("L", "quote"): -80, ("L", "v"): -30,
    ("P", "period"): -80, ("P", "A"): -40,
    ("F", "period"): -60, ("F", "a"): -20, ("F", "A"): -30,
    ("R", "T"): -24, ("R", "V"): -24, ("R", "Y"): -24,
    ("K", "o"): -18, ("K", "O"): -20,
    ("r", "period"): -50,
    ("v", "period"): -40, ("v", "o"): -10, ("v", "a"): -8,
    ("f", "quote"): 30, ("f", "close"): 30,
    ("quote", "s"): -25, ("quote", "A"): -55,
    ("k", "o"): -12,
    ("o", "v"): -10,
    ("seven", "period"): -50, ("seven", "four"): -30,
    # 0.2: lowercase and Greek lowercase
    ("r", "o"): -6,
    ("x", "o"): -10, ("o", "x"): -8,
    ("e", "v"): -8, ("e", "x"): -6,
    ("v", "s"): -6,
    ("k", "a"): -6,
    ("tau", "o"): -20, ("tau", "a"): -16, ("tau", "u"): -8,
    ("T", "x"): -40,
}

# 0.2: pairs for the italic only (full values; the italic forms differ:
# the descending f, the round-bottomed v and w, the cursive capitals).
PAIRS_ITALIC = {
    ("f", "o"): -18, ("f", "a"): -16, ("f", "period"): -40,
    ("r", "period"): -40,
    ("v", "o"): 0, ("o", "v"): 0,
    ("T", "o"): -70, ("T", "a"): -70,
    ("quote", "o"): -20,
}


def groups() -> dict[str, list[str]]:
    g = {f"public.kern1.{k}": v for k, v in KERN1.items()}
    g.update({f"public.kern2.{k}": v for k, v in KERN2.items()})
    return g


def kerning(st) -> dict[tuple[str, str], int]:
    f = 0.7 if st.italic else 1.0
    out = {(f"public.kern1.{a}", f"public.kern2.{b}"): int(round(v * f)) for (a, b), v in PAIRS.items()}
    if st.italic:
        for (a, b), v in PAIRS_ITALIC.items():
            key = (f"public.kern1.{a}", f"public.kern2.{b}")
            if v == 0:
                out.pop(key, None)
            else:
                out[key] = v
    return out
