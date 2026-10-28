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
    "A": _names("AÀÁÂÃÄÅΑΔΛ"),
    "T": _names("TΤΓ"),
    "V": _names("VW"),
    "Y": _names("YÝŸΥ"),
    "L": _names("L"),
    "P": _names("PΡÞ"),
    "F": _names("F"),
    "R": _names("R"),
    "K": _names("KΚXΧ"),
    "r": _names("r"),
    "f": _names("f"),
    "k": _names("kκ"),
    "o": _names("oòóôõöøbpþοσ"),
    "v": _names("vwyýÿνγ"),
    "quote": _names("'’\"”"),
    "seven": ["seven.lf", "seven.osf"],
}

# Second glyph (its left side).
KERN2 = {
    "a": _names("aàáâãäåæα"),
    "o": _names("ceoqdgçèéêëòóôõöøœðοσεθδφςω"),
    "s": _names("s"),
    "u": _names("ruùúûüıυικμ"),
    "n": _names("nmpñηπρ"),
    "v": _names("vwyýÿνγχ"),
    "A": _names("AÀÁÂÃÄÅÆΑΔΛ"),
    "O": _names("CGOQÇÒÓÔÕÖØŒΘΟΩ"),
    "J": _names("J"),
    "T": _names("TΤ"),
    "V": _names("VW"),
    "Y": _names("YÝŸΥ"),
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
}


def groups() -> dict[str, list[str]]:
    g = {f"public.kern1.{k}": v for k, v in KERN1.items()}
    g.update({f"public.kern2.{k}": v for k, v in KERN2.items()})
    return g


def kerning(st) -> dict[tuple[str, str], int]:
    f = 0.7 if st.italic else 1.0
    return {(f"public.kern1.{a}", f"public.kern2.{b}"): int(round(v * f)) for (a, b), v in PAIRS.items()}
