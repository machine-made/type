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
from loom import latin_ext as LX  # noqa: F401  (0.2: marks, Latin Extended-A, symbols)
from loom import revisions as RV  # noqa: F401  (0.2: revised forms)
from loom import italic_caps as IC  # noqa: F401  (0.2: italic capitals)
from loom import mathglyphs as MG  # noqa: F401  (0.2: maths variants and parts)
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
    0x0122: "Gcommaaccent", 0x0123: "gcommaaccent", 0x0136: "Kcommaaccent", 0x0137: "kcommaaccent",
    0x013B: "Lcommaaccent", 0x013C: "lcommaaccent", 0x0145: "Ncommaaccent", 0x0146: "ncommaaccent",
    0x0156: "Rcommaaccent", 0x0157: "rcommaaccent", 0x0218: "Scommaaccent", 0x0219: "scommaaccent",
    0x021A: "Tcommaaccent", 0x021B: "tcommaaccent", 0x0162: "Tcedilla", 0x0163: "tcedilla",
}

# Greek capitals that are Latin look-alikes: a reference to the Latin glyph.
GREEK_LOOKALIKE = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
                   "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X"}

# Marks with a capital form (".case"): the ones the accented capitals use.
CASE_MARKS = ("gravecomb", "acutecomb", "circumflexcomb", "tildecomb", "dieresiscomb", "ringcomb") + LX.CASE_MARKS_NEW
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
# 0.2: Latin Extended-A (U+0100-017F) and the Romanian comma-below letters.
LATIN_EXT_A = "".join(chr(c) for c in range(0x100, 0x180) if chr(c) not in LATIN_EXTRA) + "ȘșȚț"
# Letters of Extended-A that are composites of other kinds than base + mark.
EXT_SPECIAL = {
    "Đ": ("ref", ["Eth"]),
    "Ĳ": ("pair", ["I", "J"]),
    "ĳ": ("pair", ["i", "j"]),
    "ŉ": ("pair", ["quoteright", "n"]),
    "Ŀ": ("ldot", ["L", "periodcentered"]),
    "ŀ": ("ldot", ["l", "periodcentered"]),
}
# Base + mark letters that take another mark than the decomposition says.
# Latvian and Romanian use a comma below where Unicode decomposes to a
# cedilla; ď ť ľ Ľ use the vertical caron; ģ a turned comma above.
MARK_OVERRIDE = {
    "Ģ": "commaaccentcomb", "Ķ": "commaaccentcomb", "ķ": "commaaccentcomb", "Ļ": "commaaccentcomb",
    "ļ": "commaaccentcomb", "Ņ": "commaaccentcomb", "ņ": "commaaccentcomb", "Ŗ": "commaaccentcomb",
    "ŗ": "commaaccentcomb", "ģ": "commaturnedabovecomb",
    "ď": "caroncomb.alt", "ť": "caroncomb.alt", "ľ": "caroncomb.alt", "Ľ": "caroncomb.alt",
}
# Lowercase letters with an ascender whose top mark sits above the ascender, over the stem.
ASCENDER_ACCENT = {"ĥ"}
# Greek with tonos and dialytika.
GREEK_ACCENTED = "ΆΈΉΊΌΎΏΐΪΫάέήίΰϊϋόύώ"
GREEK_PUNCT = {"\u0387": "periodcentered", "\u037e": "semicolon"}  # ano teleia, question mark: references
SYMBOLS_02 = "‰†‡ℓℎℏ˘˛˝΄΅"
# Superior and inferior figures (sups, subs, numr, dnom, frac).
SUPERIORS = {"0": 0x2070, "1": 0xB9, "2": 0xB2, "3": 0xB3, "4": 0x2074, "5": 0x2075, "6": 0x2076,
             "7": 0x2077, "8": 0x2078, "9": 0x2079}
INFERIORS = {str(d): 0x2080 + d for d in range(10)}
# Mathematical italic letters (U+1D434...): the italic forms, for maths.
MATH_ITALIC = (
    [(0x1D434 + i, chr(0x41 + i)) for i in range(26)]
    + [(0x1D44E + i, chr(0x61 + i)) for i in range(26) if i != 7]   # U+1D455 is ℎ (U+210E)
    + [(0x1D6E2 + i, ch) for i, ch in enumerate("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡ")]
    + [(0x1D6F4 + i, ch) for i, ch in enumerate("ΣΤΥΦΧΨΩ")]
    + [(0x1D6FC + i, chr(0x3B1 + i)) for i in range(25)]
    + [(0x1D715, "∂")]
)
GREEK = "".join(chr(c) for c in range(0x391, 0x3AA) if c != 0x3A2) + "".join(chr(c) for c in range(0x3B1, 0x3CA))
RUPEE = "₹"
MATHS = "+−×÷±=≠<>≤≥∑∏∫√∞∂∇′″·∘→←↔∈∉⊂⊆∪∩∀∃∅≈≡∝‖⟨⟩"
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
    if name:
        return name
    return f"uni{u:04X}" if u <= 0xFFFF else f"u{u:05X}"


@dataclass
class Glyph:
    name: str
    unicodes: list = field(default_factory=list)
    key: str | None = None            # drawing key (sketch / extended tables)
    variant: str | None = None        # sc, lf, osf, tosf, sup, dnom
    comps: list | None = None         # composite: [base] or [base, mark]
    comp_kind: str | None = None      # "accent", "sc-accent", "ref", "greek-ref", "pair", "ldot", "tonos", "shift"
    category: str = "base"            # base, mark, ligature
    height: str = "x"                 # x, cap, sc: where a top mark sits


def _height_of(ch: str) -> str:
    if ch.isupper() or ch in "ÆŒØÐÞ":
        return "cap"
    return "x"


def _dec(ch: str) -> tuple[str, str] | None:
    """(base, mark) of a canonical decomposition into exactly two characters."""
    d = unicodedata.decomposition(ch)
    if not d or d.startswith("<"):
        return None
    parts = [chr(int(x, 16)) for x in d.split()]
    return (parts[0], parts[1]) if len(parts) == 2 else None


def _mark_name(m: str) -> str:
    return glyph_name(m)


def build_glyphs() -> list[Glyph]:
    out: list[Glyph] = []
    seen: set[str] = set()
    from loom.extended import BELOW, MARK_UNICODE

    def add(gl: Glyph):
        if gl.name in seen:
            raise ValueError(f"duplicate glyph {gl.name}")
        seen.add(gl.name)
        out.append(gl)

    add(Glyph(".notdef", key=None, variant="notdef"))

    def drawn(ch, key=None):
        add(Glyph(glyph_name(ch), [ord(ch)], key=key or ch, height=_height_of(ch),
                  category="ligature" if ch in LIGATURES else "base"))

    def accent(ch, b, mark):
        """A base + mark composite. Marks below sit on the dotted i and j."""
        below = mark in BELOW or mark == "ogonekcomb"
        base = "ı" if b == "i" and not below else ("ȷ" if b == "j" and not below else b)
        cap = b.isupper()
        if mark == "caroncomb.alt":
            kind = "caronalt"
        elif ch in ASCENDER_ACCENT:
            kind, mark = "ascender", mark + ".case"
        elif mark == "ogonekcomb":
            kind = "ogonek"
        else:
            kind = "accent"
            if cap and not below and mark + ".case" in S.G:
                mark = mark + ".case"
        add(Glyph(glyph_name(ch), [ord(ch)], comps=[glyph_name(base), mark], comp_kind=kind,
                  height="cap" if cap else "x"))

    accented = []
    for ch in ASCII:
        drawn(ch)
    drawn("\u00a0", " ")
    for ch in PUNCT:
        drawn(ch)
    for ch in LATIN1_LETTERS + LATIN_EXTRA:
        if _dec(ch):
            accented.append(ch)
        else:
            drawn(ch)
    # accented letters: base + mark
    for ch in accented:
        b, m = _dec(ch)
        accent(ch, b, _mark_name(m))
    # 0.2: Latin Extended-A and Ș ș Ț ț
    ext_accented = []
    for ch in LATIN_EXT_A:
        if ch in EXT_SPECIAL:
            kind, comps = EXT_SPECIAL[ch]
            add(Glyph(glyph_name(ch), [ord(ch)], comps=list(comps), comp_kind=kind, height=_height_of(ch)))
        elif _dec(ch):
            b, m = _dec(ch)
            mark = MARK_OVERRIDE.get(ch, _mark_name(m))
            accent(ch, b, mark)
            ext_accented.append(ch)
        else:
            drawn(ch)
    for ch in LIGATURES:
        drawn(ch)
    for ch in GREEK:
        if ch in GREEK_LOOKALIKE:
            add(Glyph(glyph_name(ch), [ord(ch)], comps=[glyph_name(GREEK_LOOKALIKE[ch])], comp_kind="ref", height="cap"))
        elif ch == "ο":
            add(Glyph(glyph_name(ch), [ord(ch)], comps=["o"], comp_kind="greek-ref"))
        else:
            drawn(ch)
    # 0.2: Greek tonos and dialytika
    for ch in GREEK_ACCENTED:
        b, m = _dec(ch)
        if b in "ϊϋ":                       # ΐ ΰ: iota, upsilon + dialytika tonos
            base, mark, kind = ("iota" if b == "ϊ" else "upsilon"), "dieresistonoscomb", "accent"
        else:
            base = glyph_name(GREEK_LOOKALIKE.get(b, b)) if b.isupper() else glyph_name(b)
            if b == "ο":
                base = "omicron"
            if m == "\u0301":
                mark, kind = ("tonoscomb.case", "tonos") if b.isupper() else ("tonoscomb", "accent")
            else:
                mark, kind = ("dieresiscomb.case" if b.isupper() else "dieresiscomb"), "accent"
        add(Glyph(glyph_name(ch), [ord(ch)], comps=[base, mark], comp_kind=kind,
                  height="cap" if b.isupper() else "x"))
    for ch, ref in GREEK_PUNCT.items():
        add(Glyph(glyph_name(ch), [ord(ch)], comps=[ref], comp_kind="ref"))
    drawn("₹")
    for ch in MATHS:
        if glyph_name(ch) not in seen:
            drawn(ch)
    for ch in SYMBOLS_02:
        drawn(ch)
    # other: nbsp done above
    drawn("⁄", "⁄")
    # superior figures (sups, numerators), inferior figures (subs)
    for f, u in SUPERIORS.items():
        add(Glyph(glyph_name(chr(u)), [u], key=f, variant="sup"))
    add(Glyph("ordfeminine", [0xAA], key="a", variant="sup"))
    add(Glyph("ordmasculine", [0xBA], key="o", variant="sup"))
    add(Glyph("micro", [0xB5], comps=["mu"], comp_kind="ref"))
    drawn("◌")
    # marks: encoded combining marks and their capital forms
    for name, u in MARK_UNICODE.items():
        add(Glyph(name, [u], key=name, category="mark"))
        if name in CASE_MARKS:
            add(Glyph(name + ".case", key=name + ".case", category="mark"))
    for name in ("caroncomb.alt", "tonoscomb", "tonoscomb.case", "dieresistonoscomb"):
        add(Glyph(name, key=name, category="mark"))
    # figures
    for st in FIG_STYLES:
        for f, n in zip(FIGURES, FIG_NAMES):
            add(Glyph(f"{n}.{st}", key=f, variant=st))
    for f, n in zip(FIGURES, FIG_NAMES):
        add(Glyph(f"{n}.dnom", key=f, variant="dnom"))
    for f, n in zip(FIGURES, FIG_NAMES):
        add(Glyph(f"{n}.numr", comps=[glyph_name(chr(SUPERIORS[f]))], comp_kind="ref"))
    for f, n in zip(FIGURES, FIG_NAMES):
        u = INFERIORS[f]
        add(Glyph(glyph_name(chr(u)), [u], comps=[f"{n}.dnom"], comp_kind="inferior"))
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
    for ch in accented + ext_accented:
        if not ch.islower():
            continue
        b, m = _dec(ch)
        if f"{b}.sc" not in seen:
            continue
        mark = MARK_OVERRIDE.get(ch, _mark_name(m))
        if mark == "caroncomb.alt":
            mark = "caroncomb"
        if mark == "commaturnedabovecomb":
            mark = "commaaccentcomb"
        if mark == "ogonekcomb":
            add(Glyph(f"{glyph_name(ch)}.sc", comps=[f"{b}.sc", mark], comp_kind="ogonek", height="sc"))
            continue
        below = mark in BELOW
        add(Glyph(f"{glyph_name(ch)}.sc", comps=[f"{b}.sc", mark + ("" if below else ".case")],
                  comp_kind="sc-accent", height="sc"))
    # 0.2: small capitals of the Extended-A letters with a stroke, and of ϊ ϋ
    add(Glyph("dcroat.sc", comps=["eth.sc"], comp_kind="ref", height="sc"))
    for low, cap in (("hbar", "Ħ"), ("lslash", "Ł"), ("tbar", "Ŧ"), ("eng", "Ŋ")):
        add(Glyph(f"{low}.sc", key=cap, variant="sc", height="sc"))
    add(Glyph("ldot.sc", comps=["l.sc", "periodcentered"], comp_kind="ldot", height="sc"))
    add(Glyph("iotadieresis.sc", comps=["iota.sc", "dieresiscomb.case"], comp_kind="sc-accent", height="sc"))
    add(Glyph("upsilondieresis.sc", comps=["upsilon.sc", "dieresiscomb.case"], comp_kind="sc-accent", height="sc"))
    # 0.2: maths. Size variants and assembly parts, then the italic letters.
    for name in MG.MATH_GLYPHS:
        add(Glyph(name, key=name, category="base"))
    for u, ch in MATH_ITALIC:
        add(Glyph(glyph_name(chr(u)), [u], key=ch, variant="mathit", height="cap" if ch.isupper() else "x"))
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
    have = {a for a, _ in pairs}
    for a, b in SMCP_EXTRA.items():
        if a not in have:
            pairs.append((a, b))
    # mathematical italic small letters: the small cap of their letter (for completeness)
    for u, ch in MATH_ITALIC:
        if ch.islower() and ch != "∂":
            base = glyph_name("σ" if ch == "ς" else ch)
            if base + ".sc" in BY_NAME:
                pairs.append((glyph_name(chr(u)), base + ".sc"))
    return pairs


# 0.2: lowercase letters whose small cap is another glyph's (Greek drops the tonos in capitals).
SMCP_EXTRA = {
    "kgreenlandic": "k.sc", "longs": "s.sc", "uni2113": "l.sc", "uni210E": "h.sc", "uni210F": "hbar.sc",
    "ldot": "ldot.sc",
    "alphatonos": "alpha.sc", "epsilontonos": "epsilon.sc", "etatonos": "eta.sc", "iotatonos": "iota.sc",
    "omicrontonos": "omicron.sc", "upsilontonos": "upsilon.sc", "omegatonos": "omega.sc",
    "iotadieresis": "iotadieresis.sc", "upsilondieresis": "upsilondieresis.sc",
    "iotadieresistonos": "iotadieresis.sc", "upsilondieresistonos": "upsilondieresis.sc",
}


def c2sc_pairs() -> list[tuple[str, str]]:
    pairs = []
    seen = set()
    for low, sc in smcp_pairs():
        if low == "dotlessi":
            continue
        ch = next((chr(u) for u in BY_NAME[low].unicodes), None)
        if ch is None:
            continue
        up = ch.upper()
        if len(up) == 1 and up != ch and glyph_name(up) in BY_NAME and glyph_name(up) not in seen:
            seen.add(glyph_name(up))
            pairs.append((glyph_name(up), sc))
    # mathematical italic capitals: the small cap of their letter
    for u, ch in MATH_ITALIC:
        if ch.isupper():
            sc = glyph_name(ch.lower()) + ".sc"
            if sc in BY_NAME:
                pairs.append((glyph_name(chr(u)), sc))
    return pairs


SKETCH_CHARS = S.SKETCH_CHARS
