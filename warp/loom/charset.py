"""The glyph set of machine-made Warp 0.1: names, code points, sources.

Every glyph is one of:

* drawn: a key into the glyph tables (loom/sketch.py, loom/extended.py)
  plus an optional variant (small cap, figure style, superior);
* composite: a base glyph and a mark (accented letters), or a single
  reference (Greek capitals that look like Latin ones, µ, ο).

Apache-2.0.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from fontTools.agl import UV2AGL

from loom import extended as X  # noqa: F401  (registers the new glyphs)
from loom import sketch as S

GREEK_NAMES = {
    0x391: "Alpha", 0x392: "Beta", 0x393: "Gamma", 0x394: "Delta", 0x395: "Epsilon", 0x396: "Zeta",
    0x397: "Eta", 0x398: "Theta", 0x399: "Iota", 0x39A: "Kappa", 0x39B: "Lambda", 0x39C: "Mu",
    0x39D: "Nu", 0x39E: "Xi", 0x39F: "Omicron", 0x3A0: "Pi", 0x3A1: "Rho", 0x3A3: "Sigma",
    0x3A4: "Tau", 0x3A5: "Upsilon", 0x3A6: "Phi", 0x3A7: "Chi", 0x3A8: "Psi", 0x3A9: "Omega",
    0x3B1: "alpha", 0x3B2: "beta", 0x3B3: "gamma", 0x3B4: "delta", 0x3B5: "epsilon", 0x3B6: "zeta",
    0x3B7: "eta", 0x3B8: "theta", 0x3B9: "iota", 0x3BA: "kappa", 0x3BB: "lambda", 0x3BC: "mu",
    0x3BD: "nu", 0x3BE: "xi", 0x3BF: "omicron", 0x3C0: "pi", 0x3C1: "rho", 0x3C2: "sigmafinal",
    0x3C3: "sigma", 0x3C4: "tau", 0x3C5: "upsilon", 0x3C6: "phi", 0x3C7: "chi", 0x3C8: "psi",
    0x3C9: "omega",
}
SPECIAL_NAMES = {
    0x00A0: "uni00A0", 0x00B9: "onesuperior", 0x00B2: "twosuperior", 0x00B3: "threesuperior", 0x00B5: "micro", 0x0237: "dotlessj", 0x2218: "ringoperator", 0x2207: "nabla",
    0x2211: "summation", 0x220F: "product", 0x2206: "increment", 0x25CC: "dottedcircle",
    0xFB00: "f_f", 0xFB01: "fi", 0xFB02: "fl", 0xFB03: "f_f_i", 0xFB04: "f_f_l",
}

# Greek capitals that are Latin look-alikes: a reference to the Latin glyph.
GREEK_LOOKALIKE = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
                   "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X"}

# Marks with a capital form (".case"): the ones the accented capitals use.
CASE_MARKS = ("gravecomb", "acutecomb", "circumflexcomb", "tildecomb", "dieresiscomb", "ringcomb")
# Maths operators that share one advance (the advance of +), so that
# they line up in tables. The sketch gave < > × their own widths.
EQUAL_WIDTH_MATHS = "+<=>±×÷−∈∉∝≈≠≡≤≥⊂⊆¬"

FIGURES = "0123456789"
FIG_NAMES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
# Figure styles. Default: lining, tabular (the sketch's figures).
FIG_STYLES = {"lf": "lining, proportional", "osf": "old-style, proportional", "tosf": "old-style, tabular"}

ASCII = "".join(chr(c) for c in range(0x20, 0x7F))
PUNCT = "‘’“”‚„‹›«»…•·€©®°—–¡¿§¶¢£¥¦¬¨´¯¸ˆ˜˚ˇ˙"
LATIN1_LETTERS = "".join(chr(c) for c in range(0xC0, 0x100) if unicodedata.category(chr(c)).startswith("L"))
LATIN_EXTRA = "ŒœŸıȷ"
GREEK = "".join(chr(c) for c in range(0x391, 0x3AA) if c != 0x3A2) + "".join(chr(c) for c in range(0x3B1, 0x3CA))
RUPEE = "₹"
MATHS = "+−×÷±=≠<>≤≥∑∏∫√∞∂∇′″·∘→←↔∈∉⊂⊆∪∩∀∃∅≈≡∝"
OTHER = " ⁄¹²³¼½¾ªºµ◌"
LIGATURES = "ﬀﬁﬂﬃﬄ"


def glyph_name(ch: str) -> str:
    u = ord(ch)
    if u in GREEK_NAMES:
        return GREEK_NAMES[u]
    if u in SPECIAL_NAMES:
        return SPECIAL_NAMES[u]
    from loom.extended import MARK_UNICODE
    for n, mu in MARK_UNICODE.items():
        if mu == u:
            return n
    name = UV2AGL.get(u)
    return name if name else f"uni{u:04X}"


@dataclass
class Glyph:
    name: str
    unicodes: list = field(default_factory=list)
    key: str | None = None            # drawing key (sketch / extended tables)
    variant: str | None = None        # sc, lf, osf, tosf, sup, dnom
    comps: list | None = None         # composite: [base] or [base, mark]
    comp_kind: str | None = None      # "accent", "sc-accent", "ref", "greek-ref"
    category: str = "base"            # base, mark, ligature
    height: str = "x"                 # x, cap, sc: where a top mark sits


def _height_of(ch: str) -> str:
    if ch.isupper() or ch in "ÆŒØÐÞ":
        return "cap"
    return "x"


def build_glyphs() -> list[Glyph]:
    out: list[Glyph] = []
    seen: set[str] = set()

    def add(gl: Glyph):
        if gl.name in seen:
            raise ValueError(f"duplicate glyph {gl.name}")
        seen.add(gl.name)
        out.append(gl)

    add(Glyph(".notdef", key=None, variant="notdef"))

    def drawn(ch, key=None):
        add(Glyph(glyph_name(ch), [ord(ch)], key=key or ch, height=_height_of(ch),
                  category="ligature" if ch in LIGATURES else "base"))

    accented = []
    for ch in ASCII:
        drawn(ch)
    drawn(" ", " ")
    for ch in PUNCT:
        drawn(ch)
    for ch in LATIN1_LETTERS + LATIN_EXTRA:
        dec = unicodedata.decomposition(ch)
        if dec and not dec.startswith("<"):
            accented.append(ch)
        else:
            drawn(ch)
    # accented letters: base + mark
    for ch in accented:
        b, m = (chr(int(x, 16)) for x in unicodedata.decomposition(ch).split())
        base = "ı" if b == "i" else b
        mark = glyph_name(m)
        cap = b.isupper()
        add(Glyph(glyph_name(ch), [ord(ch)], comps=[glyph_name(base), mark + (".case" if cap and mark != "cedillacomb" else "")],
                  comp_kind="accent", height="cap" if cap else "x"))
    for ch in LIGATURES:
        drawn(ch)
    for ch in GREEK:
        if ch in GREEK_LOOKALIKE:
            add(Glyph(glyph_name(ch), [ord(ch)], comps=[glyph_name(GREEK_LOOKALIKE[ch])], comp_kind="ref", height="cap"))
        elif ch == "ο":
            add(Glyph(glyph_name(ch), [ord(ch)], comps=["o"], comp_kind="greek-ref"))
        else:
            drawn(ch)
    drawn("₹")
    for ch in MATHS:
        if glyph_name(ch) not in seen:
            drawn(ch)
    # other: nbsp done above
    drawn("⁄", "⁄")
    for ch, f in (("¹", "1"), ("²", "2"), ("³", "3")):
        add(Glyph(glyph_name(ch), [ord(ch)], key=f, variant="sup"))
    add(Glyph("ordfeminine", [0xAA], key="a", variant="sup"))
    add(Glyph("ordmasculine", [0xBA], key="o", variant="sup"))
    add(Glyph("micro", [0xB5], comps=["mu"], comp_kind="ref"))
    drawn("◌")
    # marks: encoded combining marks and their capital forms
    from loom.extended import BELOW, MARK_UNICODE
    for name, u in MARK_UNICODE.items():
        add(Glyph(name, [u], key=name, category="mark"))
        if name in CASE_MARKS:
            add(Glyph(name + ".case", key=name + ".case", category="mark"))
    # figures
    for st in FIG_STYLES:
        for f, n in zip(FIGURES, FIG_NAMES):
            add(Glyph(f"{n}.{st}", key=f, variant=st))
    for f in "24":
        add(Glyph(f"{FIG_NAMES[int(f)]}.dnom", key=f, variant="dnom"))
    for ch, parts in (("¼", ["onesuperior", "fraction", "four.dnom"]), ("½", ["onesuperior", "fraction", "two.dnom"]),
                      ("¾", ["threesuperior", "fraction", "four.dnom"])):
        add(Glyph(glyph_name(ch), [ord(ch)], comps=parts, comp_kind="frac"))
    # small capitals
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        add(Glyph(f"{ch.lower()}.sc", key=ch, variant="sc", height="sc"))
    for ch, key in (("æ", "Æ"), ("œ", "Œ"), ("ø", "Ø"), ("ð", "Ð"), ("þ", "Þ")):
        add(Glyph(f"{glyph_name(ch)}.sc", key=key, variant="sc", height="sc"))
    # Greek small capitals: drawn capitals at small-cap size; look-alikes refer to the Latin ones
    for ch in GREEK:
        if ch.isupper():
            low = ch.lower()
            if ch in GREEK_LOOKALIKE:
                add(Glyph(f"{glyph_name(low)}.sc", comps=[f"{GREEK_LOOKALIKE[ch].lower()}.sc"], comp_kind="ref", height="sc"))
            else:
                add(Glyph(f"{glyph_name(low)}.sc", key=ch, variant="sc", height="sc"))
    for ch in accented:
        if ch.islower():
            b, m = (chr(int(x, 16)) for x in unicodedata.decomposition(ch).split())
            mark = glyph_name(m)
            add(Glyph(f"{glyph_name(ch)}.sc", comps=[f"{b}.sc", mark + ("" if mark == "cedillacomb" else ".case")],
                      comp_kind="sc-accent", height="sc"))
    return out


GLYPHS = build_glyphs()
BY_NAME = {g.name: g for g in GLYPHS}
ORDER = [g.name for g in GLYPHS]


def cmap() -> dict[int, str]:
    return {u: g.name for g in GLYPHS for u in g.unicodes}


def smcp_pairs() -> list[tuple[str, str]]:
    """(lowercase glyph, small cap glyph) for smcp; c2sc maps the capitals."""
    pairs = []
    for g in GLYPHS:
        if g.name.endswith(".sc"):
            base = g.name[:-3]
            if base in BY_NAME:
                pairs.append((base, g.name))
    pairs.append(("dotlessi", "i.sc"))
    pairs.append(("sigmafinal", "sigma.sc"))
    return pairs


def c2sc_pairs() -> list[tuple[str, str]]:
    pairs = []
    for low, sc in smcp_pairs():
        if low == "dotlessi":
            continue
        ch = next((chr(u) for u in BY_NAME[low].unicodes), None)
        if ch is None:
            continue
        up = ch.upper()
        if len(up) == 1 and up != ch and glyph_name(up) in BY_NAME:
            pairs.append((glyph_name(up), sc))
    return pairs


SKETCH_CHARS = S.SKETCH_CHARS
