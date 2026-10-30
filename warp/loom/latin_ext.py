"""Glyphs new in Warp 0.2, drawn with the same pen.

* Marks for Latin Extended-A and Romanian: breve, ogonek, double acute,
  comma below, turned comma above (ģ), the vertical caron of ď ť ľ Ľ,
  and the capital forms of caron, macron, dot above, breve and double
  acute.
* Greek tonos and dialytika (tonos, dialytika tonos).
* The Latin Extended-A letters that are not a base plus a mark:
  đ ħ Ħ Ł ł Ŧ ŧ Ŋ ŋ ĸ ſ (roman and italic). Đ is the glyph of Ð; Ĳ ĳ ŉ
  Ŀ ŀ are composites (loom/charset.py).
* Symbols: ‰ † ‡ ℓ ℎ ℏ.
* Heavier horizontal bars for helper use (`hbar`).

Every glyph is centre-lines plus pressure, swept by the nib, as in
loom/sketch.py and loom/extended.py.

This file defines outlines of machine-made Warp: SIL Open Font License
1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

from loom.engine import PI, GlyphDef
from loom.extended import BELOW, MARK_UNICODE, MARKS, _top, acute, caron, dieresis, fn_of, rom_cap
from loom.sketch import G, GI, dotD, entry, exit_t, iarch, it_f, rom, ita, vbeak

# ---------------------------------------------------------------- helpers


def hbar(g, x0, x1, y, k=1.5):
    """A horizontal bar, ink x0..x1, centred on y, k hairlines thick.

    The level pen makes every horizontal a hairline. Letters that are
    only horizontals (Ξ, Σ) or a bar that must show at text size (đ ħ ŧ)
    use a nib k times as thick.
    """
    b = g.B * k
    a, c = min(x0, x1), max(x0, x1)
    return g.P(a + b / 2, y, 0).l(c - b / 2, y, 0).draw({"b": b, "role": "bar"})


def comma_shape(g, x, y, d, flip=False, tail=1.75):
    """A drop at (x, y) of diameter d with a tail; flip turns it by 180 degrees."""
    s = -1 if flip else 1
    g.ball(x, y, d)
    (g.P(x + s * d * 0.22, y - s * d * 0.18, 0.85)
     .c(x + s * d * 0.3, y - s * d * 0.8 * tail / 1.75, x, y - s * d * 1.4 * tail / 1.75,
        x - s * d * 0.45, y - s * d * tail, 0).draw())


# ------------------------------------------------------------------ marks

def breve(g, case=False):
    """A cup. The nib is turned upright, so the bottom is the heavy part."""
    y0, k = _top(g, case)
    w, hgt = 112, 118 * k
    yb = y0 + 22
    (g.P(-w, yb + hgt, 0).c(-w + 6, yb + hgt * 0.32, -w * 0.55, yb, 0, yb, 0.5)
     .c(w * 0.55, yb, w - 6, yb + hgt * 0.32, w, yb + hgt, 0).draw({"turn": PI / 2}))


def doubleacute(g, case=False):
    y0, k = _top(g, case)
    for dx in (-58, 74):
        g.P(dx - 42, y0, 0.12).l(dx + 46, y0 + 150 * k, 1).draw()


def ogonek(g, case=False):
    """Hangs from the base's right foot: the anchor is at (0, 0)."""
    (g.P(18, 36, 0.5).c(-40, -6, -64, -86, -22, -130, 1)
     .c(4, -152, 42, -154, 76, -136, 0).draw())


def commaaccent(g, case=False):
    """Comma below (ș ț, and the Latvian ķ ļ ņ ŗ Ģ)."""
    d = dotD(g) * 0.72
    comma_shape(g, 6, -52 - d / 2, d)


def commaturnedabove(g, case=False):
    """Turned comma above (ģ)."""
    y0, k = _top(g, case)
    d = dotD(g) * 0.72
    comma_shape(g, -6, y0 + 8 + d / 2, d, flip=True)


def caron_alt(g, case=False):
    """The vertical caron of ď ť ľ Ľ: a comma right of the stem, top at the ascender."""
    d = dotD(g) * 0.8
    comma_shape(g, 0, g.AS - d / 2, d, tail=1.55)


def tonos(g, case=False):
    """Greek tonos: steeper than the acute. The capital form stands left of the letter."""
    if case:
        y0, k = g.C - 128, 0.9
    else:
        y0, k = g.X + 62, 1.0
    g.P(-28, y0, 0.12).l(36, y0 + 168 * k, 1).draw()


def dieresistonos(g, case=False):
    y0, k = _top(g, case)
    d = dotD(g) * 0.92
    for x in (-118, 118):
        g.dot(x, y0 + d / 2 + 6, d)
    g.P(-24, y0 + 6, 0.12).l(34, y0 + 190, 1).draw()


NEW_MARKS = {
    "brevecomb": (breve, 0x0306, True),
    "hungarumlautcomb": (doubleacute, 0x030B, True),
    "ogonekcomb": (ogonek, 0x0328, False),
    "commaaccentcomb": (commaaccent, 0x0326, False),
    "commaturnedabovecomb": (commaturnedabove, 0x0312, False),
}
MARKS.update({k: v[0] for k, v in NEW_MARKS.items()})
MARK_UNICODE.update({k: v[1] for k, v in NEW_MARKS.items()})
BELOW.update({"commaaccentcomb"})
# Marks that attach at their own anchor ("ogonek"), not top or bottom.
OGONEK = {"ogonekcomb"}

for _name, (_f, _u, _case) in NEW_MARKS.items():
    G[_name] = GlyphDef(fn=(lambda f: (lambda g: f(g)))(_f), l=0, r=0)
    if _case:
        G[_name + ".case"] = GlyphDef(fn=(lambda f: (lambda g: f(g, True)))(_f), l=0, r=0)
# capital forms of 0.1 marks that 0.1 did not need
for _name in ("macroncomb", "caroncomb", "dotaccentcomb"):
    G[_name + ".case"] = GlyphDef(fn=(lambda f: (lambda g: f(g, True)))(MARKS[_name]), l=0, r=0)
G["caroncomb.alt"] = GlyphDef(fn=caron_alt, l=0, r=0)
G["tonoscomb"] = GlyphDef(fn=tonos, l=0, r=0)
G["tonoscomb.case"] = GlyphDef(fn=lambda g: tonos(g, True), l=0, r=0)
G["dieresistonoscomb"] = GlyphDef(fn=dieresistonos, l=0, r=0)

# Spacing forms.
for _ch, _f in (("˘", breve), ("˝", doubleacute), ("΄", tonos), ("΅", dieresistonos)):
    G[_ch] = GlyphDef(fn=(lambda f: (lambda g: f(g)))(_f), l=0.6, r=0.6)


@rom("˛", l=0.6, r=0.6)
def _ogonek_spacing(g):
    ogonek(g)


# Marks with a capital form (".case").
CASE_MARKS_NEW = ("brevecomb", "hungarumlautcomb", "macroncomb", "caroncomb", "dotaccentcomb")

# ------------------------------------------------- Latin Extended-A letters


@rom("đ", l=0.82)
def _dcroat(g):
    g.use(fn_of("d"))
    hbar(g, 410 - g.h - 112, 410 + g.h + 44, g.AS - 148, 1.4)


@ita("đ", l=0.8, r=0.5)
def _idcroat(g):
    g.use(fn_of("d", True))
    hbar(g, 300 - g.h - 112, 300 + g.h + 40, g.AS - 148, 1.4)


@rom("ħ")
def _hbar(g):
    g.use(fn_of("h"))
    hbar(g, -g.h - 72, g.h + 128, g.X + (g.AS - g.X) * 0.48, 1.4)


@ita("ħ", l=0.7, r=0.5)
def _ihbar(g):
    g.use(fn_of("h", True))
    hbar(g, -g.h - 72, g.h + 128, g.X + (g.AS - g.X) * 0.48, 1.4)


def _x0(g):
    """The stem of the italic capitals with their own form stands at x 120 (loom/italic_caps.py)."""
    return 120 if g.p.ital else 0


@rom_cap("Ħ")
def _Hbar(g):
    g.use(fn_of("H", g.p.ital))
    x0, x1 = (120, 540) if g.p.ital else (0, 470)
    hbar(g, x0 - g.h - 46, x1 + g.h + 46, g.C * 0.77, 1.2)


@rom_cap("Ł", r=0.6)
def _Lslash(g):
    g.use(fn_of("L", g.p.ital))
    x = _x0(g)
    g.P(x - 112, g.C * 0.33, 0).l(x + 150, g.C * 0.56, 0).draw({"b": g.B * 1.5})


@rom("ł")
def _lslash(g):
    g.use(fn_of("l"))
    y = (g.X + g.AS) / 2 - 40
    g.P(-112, y - 70, 0).l(112, y + 70, 0).draw({"b": g.B * 1.5})


@ita("ł", l=0.7, r=0.5)
def _ilslash(g):
    g.use(fn_of("l", True))
    y = (g.X + g.AS) / 2 - 40
    g.P(-110, y - 70, 0).l(110, y + 70, 0).draw({"b": g.B * 1.5})


@rom_cap("Ŧ", l=0.5, r=0.5)
def _Tbar(g):
    g.use(fn_of("T", g.p.ital))
    xs = 270
    hbar(g, xs - 122, xs + 122, g.C * 0.47, 1.3)


@rom("ŧ", l=0.7, r=0.6)
def _tbar(g):
    g.use(fn_of("t"))
    hbar(g, -g.h - 64, g.h + 84, g.X * 0.47, 1.3)


@ita("ŧ", l=0.7, r=0.4)
def _itbar(g):
    g.use(fn_of("t", True))
    hbar(g, -g.h - 60, g.h + 80, g.X * 0.47, 1.3)


def descender_hook(p, g, x, depth=1.0):
    """Continue a stem at x down into the j hook, with its drop."""
    D, B, o, bd = g.D * depth, g.B, g.o, g.bd
    yb = D - o + B / 2
    (p.l(x, D + 150, 1).c(x, D + 50, x - 40, yb, x - 105, yb, 0.5)
     .c(x - 150, yb, x - 182, D + 22, x - 190, D + bd * 0.55 + 8, 0.25).draw())
    g.ball(x - 190, D + bd * 0.55 + 8)


@rom_cap("Ŋ")
def _Eng(g):
    C, B, o, h = g.C, g.B, g.o, g.h
    x1 = 470
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "b")
    yt = C + o - B / 2
    xm = x1 / 2 + 14
    p = (g.P(h * 0.3, C * 0.62, 0).c(h * 0.3 + 40, C * 0.9, xm - xm * 0.55, yt, xm, yt, 0.55)
         .c(xm + (x1 - xm) * 0.6, yt, x1, C * 0.9, x1, C * 0.62, 1))
    descender_hook(p, g, x1, 0.82)


@rom("ŋ")
def _eng(g):
    X, B, o, h = g.X, g.B, g.o, g.h
    x1 = 330
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b")
    yt = X + o - B / 2
    xm = x1 / 2 + 12
    p = (g.P(h * 0.3, X * 0.6, 0).c(h * 0.3 + 30, X * 0.88, xm - xm * 0.55, yt, xm, yt, 0.55)
         .c(xm + (x1 - xm) * 0.6, yt, x1, X * 0.9, x1, X * 0.6, 1))
    descender_hook(p, g, x1)


@ita("ŋ", l=0.7, r=0.5)
def _ieng(g):
    X, B = g.X, g.B
    entry(g, 0, X).l(0, B / 2, 1).draw()
    descender_hook(iarch(g, 0, 300, X), g, 300)


@rom("ĸ", r=0.6)
def _kra(g):
    X, A, B, h = g.X, g.A, g.B, g.h
    ax = 262
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b")
    g.P(h - 4, X * 0.26, 0).l(ax, X - B / 2, 0).draw(); g.serif(ax, X, -1, "b", B * 1.6, g.sl * 0.8)
    g.P(128, X * 0.55, 0.85).l(292, B / 2, 1).draw(); g.serif(292, 0, 1, "b", A * 0.95)


@ita("ĸ", l=0.7, r=0.5)
def _ikra(g):
    X, B, h = g.X, g.B, g.h
    entry(g, 0, X).l(0, B / 2, 1).draw()
    g.P(h * 0.3, X * 0.32, 0).c(80, X * 0.6, 170, X + 6, 235, X * 0.86, 0.4).c(270, X * 0.74, 200, X * 0.56, 90, X * 0.5, 0.6).draw()
    exit_t(g.P(120, X * 0.52, 0.5).c(190, X * 0.45, 220, X * 0.3, 220, X * 0.2, 1), g, 220).draw()


@rom("ſ", r=-0.7)
def _longs(g):
    AS, B, bd, A, o = g.AS, g.B, g.bd, g.A, g.o
    x0 = 0
    yt2, xe, ye = AS + o - B / 2, x0 + 232, AS - max(bd, A * 0.6) * 0.5 - 12
    (g.P(x0, B / 2, 1).l(x0, AS - 175, 1).c(x0, AS - 45, x0 + 62, yt2, x0 + 150, yt2, 0.5)
     .c(x0 + 205, yt2, xe, AS - 25, xe, ye, 0.25).draw())
    g.ball(xe, ye); g.serif(x0, 0, 1, "b", A, g.sl * 1.2)


@ita("ſ", l=0.3, r=0.2)
def _ilongs(g):
    it_f(g, 190, 340)


# ---------------------------------------------------------------- symbols

@rom("‰", l=0.6, r=0.6)
def _perthousand(g):
    C = g.C
    rx, ry = 105 - g.h * 0.6, C * 0.21
    g.ring(130, C * 0.76, rx, ry, 0.8)
    g.ring(500, C * 0.22, rx, ry, 0.8)
    g.ring(745, C * 0.22, rx, ry, 0.8)
    g.P(530, C + 10, 0.4).l(100, -10, 0.4).draw()


def dagger_bar(g, y, w):
    """A cross bar of the daggers: heavy in the middle, light at the tips."""
    (g.P(-w, y, 0).l(-w * 0.35, y, 0.6).l(w * 0.35, y, 0.6).l(w, y, 0).draw({"turn": PI / 2, "b": g.B * 1.2}))


@rom("†", l=0.8, r=0.8)
def _dagger(g):
    C, D = g.C, g.D
    g.P(0, C + 30, 0.55).l(0, C - 150, 1).l(0, D * 0.62, 0.15).draw()
    dagger_bar(g, C - 175, 175)


@rom("‡", l=0.8, r=0.8)
def _daggerdbl(g):
    C, D = g.C, g.D
    g.P(0, C + 30, 0.55).l(0, C - 150, 1).l(0, 140, 0.45).l(0, D * 0.62, 0.55).draw()
    dagger_bar(g, C - 175, 175)
    dagger_bar(g, 40, 175)


@rom("ℓ", l=0.7, r=0.6)
def _scriptl(g):
    """Script l: one pen line, a loop up to the ascender and an exit tail."""
    AS, B, o, yb = g.AS, g.B, g.o, g.yb
    yt = AS + o - B / 2
    (g.P(10, 150, 0.2).c(110, 260, 255, 470, 255, 610, 0.9).c(255, 700, 222, yt, 180, yt, 0.4)
     .c(120, yt, 92, 640, 92, 470, 1).l(92, 150, 1).c(92, 50, 130, yb, 182, yb, 0.4)
     .c(225, yb, 258, 34, 274, 86, 0).draw())


def mathit_def(key: str) -> GlyphDef:
    """The italic form of a letter, for a glyph that is italic in every style
    (ℎ ℏ and the mathematical italic letters)."""
    d = GI.get(key) or G[key]
    return GlyphDef(fn=d.fn, cap=d.cap, lc=d.lc, l=d.l, r=d.r, adv=d.adv, slant=0.25, greek=d.greek)


def _planck_bar(g):
    GI["h"].fn(g)
    # the bar of ℏ: a slanted hairline across the ascender
    g.P(-110, g.X + 80, 0).l(150, g.X + 205, 0).draw({"b": g.B * 1.5})


G["ℎ"] = mathit_def("h")
G["ℏ"] = GlyphDef(fn=_planck_bar, l=GI["h"].l, r=GI["h"].r, slant=0.25)


__all__ = ["hbar", "comma_shape", "mathit_def", "OGONEK", "CASE_MARKS_NEW", "acute", "caron", "dieresis", "vbeak"]
