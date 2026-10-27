"""Glyphs new in the font (not in sketch 0.2), drawn with the same pen.

The rest of printable ASCII, typographic punctuation, Latin-1 letters
and symbols, the marks for accents, the rest of basic Greek, the maths
operators, ffi and ffl, and the dotted circle. Every glyph is centre-
lines plus pressure, swept by the same nib as the sketch glyphs, with
the sketch's helpers (serifs, beaks, teardrops, rule pen).

Keys are the characters, or production names for unencoded glyphs
(marks for capitals end in ".case").

This file defines outlines of machine-made Warp: SIL Open Font License
1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

import math

from loom.engine import PI, TAU, GlyphDef
from loom.sketch import (AX, FIG, G, GI, OPW, Rw, bowl_right, dbowl, dotD, entry, exit_t, iarch, ibowl,
                         it_f, paren, rom, ita, round_c, rule, vbeak)

# Glyphs that are capitals but not A-Z: lighter stems and narrower frames, as the sketch's capitals.
CAP = {"cap": True}


def rom_cap(ch, **o):
    def deco(fn):
        G[ch] = GlyphDef(fn=fn, cap=True, **o)
        return fn
    return deco


def ita_cap(ch, **o):
    def deco(fn):
        GI[ch] = GlyphDef(fn=fn, cap=True, **o)
        return fn
    return deco


def fn_of(ch, ital=False):
    return ((GI.get(ch) if ital else None) or G[ch]).fn


# =====================================================================
# Marks. Drawn centred on x = 0. Lowercase marks sit above the x-height,
# capital marks (".case") above the cap height, flatter.
# =====================================================================

def _top(g, case):
    return (g.C + 52, 0.78) if case else (g.X + 62, 1.0)


def acute(g, case=False):
    y0, k = _top(g, case)
    g.P(-48, y0, 0.12).l(58, y0 + 150 * k, 1).draw()


def grave(g, case=False):
    y0, k = _top(g, case)
    g.P(48, y0, 0.12).l(-58, y0 + 150 * k, 1).draw()


def circumflex(g, case=False):
    y0, k = _top(g, case)
    w = 125
    g.P(-w, y0, 0).l(-6, y0 + 140 * k, 0.45).draw()
    g.P(6, y0 + 140 * k, 0.55).l(w, y0, 0.1).draw()


def caron(g, case=False):
    y0, k = _top(g, case)
    w = 125
    g.P(-w, y0 + 140 * k, 0.1).l(-6, y0, 0.55).draw()
    g.P(6, y0, 0.45).l(w, y0 + 140 * k, 0).draw()


def dieresis(g, case=False):
    y0, k = _top(g, case)
    d = dotD(g) * 0.92
    for x in (-98, 98):
        g.dot(x, y0 + d / 2 + 6, d)


def dotaccent(g, case=False):
    y0, k = _top(g, case)
    d = dotD(g) * 0.95
    g.dot(0, y0 + d / 2 + 6, d)


def tilde(g, case=False):
    y0, k = _top(g, case)
    h = 70 * k
    (g.P(-138, y0 + 8, 0.1).c(-128, y0 + h * 0.95, -82, y0 + h * 1.25, -30, y0 + h * 0.8, 0.75)
     .c(25, y0 + h * 0.35, 80, y0 + h * 0.1, 105, y0 + 15, 0.45).c(118, y0 + 22, 132, y0 + 55, 138, y0 + h * 1.1, 0.1).draw())


def ring(g, case=False):
    y0, k = _top(g, case)
    r = 64 * (0.9 if case else 1)
    g.ring(0, y0 + r + 4, r, r, 0.55)


def macron(g, case=False):
    y0, k = _top(g, case)
    g.P(-125, y0 + 40 * k, 0).l(125, y0 + 40 * k, 0).draw({"b": g.B * 1.5, "a": g.B * 1.5, "ne": 5})


def cedilla(g, case=False):
    (g.P(6, 4, 0.15).l(6, -58, 0.15).c(78, -60, 112, -92, 112, -132, 1)
     .c(112, -184, 46, -214, -62, -206, 0).draw())


MARKS = {
    "gravecomb": grave, "acutecomb": acute, "circumflexcomb": circumflex, "tildecomb": tilde,
    "macroncomb": macron, "dieresiscomb": dieresis, "ringcomb": ring, "caroncomb": caron,
    "dotaccentcomb": dotaccent, "cedillacomb": cedilla,
}
MARK_UNICODE = {
    "gravecomb": 0x0300, "acutecomb": 0x0301, "circumflexcomb": 0x0302, "tildecomb": 0x0303,
    "macroncomb": 0x0304, "dieresiscomb": 0x0308, "ringcomb": 0x030A, "caroncomb": 0x030C,
    "dotaccentcomb": 0x0307, "cedillacomb": 0x0327,
}
BELOW = {"cedillacomb"}

for _name, _f in MARKS.items():
    G[_name] = GlyphDef(fn=(lambda f: (lambda g: f(g)))(_f), l=0, r=0)
    if _name in ("gravecomb", "acutecomb", "circumflexcomb", "tildecomb", "dieresiscomb", "ringcomb"):
        G[_name + ".case"] = GlyphDef(fn=(lambda f: (lambda g: f(g, True)))(_f), l=0, r=0)

# Spacing marks (` ´ ¨ ¯ ¸ ^ ˜ ˆ ˚ ˇ ˙): the same drawings with side bearings.
for _ch, _f in (("`", grave), ("´", acute), ("¨", dieresis), ("¯", macron), ("¸", cedilla),
                ("ˆ", circumflex), ("˜", tilde), ("˚", ring), ("ˇ", caron), ("˙", dotaccent)):
    G[_ch] = GlyphDef(fn=(lambda f: (lambda g: f(g)))(_f), l=0.6, r=0.6)


# =====================================================================
# ASCII
# =====================================================================

@rom('"', l=0.9, r=0.9)
def _quotedbl(g):
    C = g.C
    for x in (0, 150):
        g.P(x, C - g.B / 2, 1).l(x, C * 0.66, 0.15).draw()


@rom("#", l=0.6, r=0.6)
def _numbersign(g):
    C = g.C
    g.P(205, C - 10, 0.7).l(125, 0, 0.7).draw()
    g.P(395, C - 10, 0.7).l(315, 0, 0.7).draw()
    g.bar(40, 480, C * 0.64)
    g.bar(20, 460, C * 0.34)


def s_curve(g, W, H, y0=0.0, beaks=True):
    """The S spine at any height (the sketch's S, scaled to H)."""
    B, o, h = g.B, g.o, g.h
    yt, yb = y0 + H + o - B / 2, y0 - o + B / 2
    Y = lambda f: y0 + H * f  # noqa: E731
    (g.P(W - 16, Y(0.78), 0.15).c(W - 30, Y(0.95), W * 0.68, yt, W * 0.5, yt, 0.5).c(W * 0.22, yt, h + 2, Y(0.92), h + 2, Y(0.75), 1)
     .c(h + 2, Y(0.5), W - h - 2, Y(0.52), W - h - 2, Y(0.26), 1).c(W - h - 2, Y(0.08), W * 0.76, yb, W * 0.5, yb, 0.5)
     .c(W * 0.24, yb, 26, Y(0.06), 12, Y(0.2), 0.15).draw())
    if beaks:
        vbeak(g, W - 16, Y(0.68), Y(0.92)); vbeak(g, 12, Y(0.08), Y(0.33))


@rom("$", **FIG)
def _dollar(g):
    C = g.C
    s_curve(g, 400, C * 0.92, C * 0.02)
    g.P(200, C + 70, 0).l(200, -90, 0).draw()


@rom("%", l=0.6, r=0.6)
def _percent(g):
    C = g.C
    g.ring(130, C * 0.76, 105 - g.h * 0.6, C * 0.21, 0.8)
    g.ring(500, C * 0.22, 105 - g.h * 0.6, C * 0.21, 0.8)
    g.P(530, C + 10, 0.4).l(100, -10, 0.4).draw()


@rom("*", l=0.6, r=0.6)
def _asterisk(g):
    C = g.C
    cx, cy, R = 170, C - 150, 140
    for k in range(5):
        a = PI / 2 + k * TAU / 5
        g.P(cx, cy, 0.15).l(cx + math.cos(a) * R, cy + math.sin(a) * R, 0.9).draw()
        g.dot(cx + math.cos(a) * (R - 6), cy + math.sin(a) * (R - 6), g.A * 0.62)


@rom("@", l=0.7, r=0.7)
def _at(g):
    X, B, o = g.X, g.B, g.o
    cx, cy, R = 400, X * 0.62, 380
    g.ring(372, X * 0.52, 118 - g.h * 0.3, X * 0.34)
    (g.P(500, X * 0.92, 1).l(500, X * 0.2, 1).c(500, X * 0.02, 540, -12, 600, -12, 0.45)
     .c(710, -12, cx + R, cy - 160, cx + R, cy, 1).arc(cx, cy, R, R, 0, 0.5 * PI, 0.6, 2.0)
     .arc(cx, cy, R, R, 0.5 * PI, PI, 1, 2.0).arc(cx, cy, R, R, PI, 1.5 * PI, 0.6, 2.0)
     .arc(cx, cy, R, R, 1.5 * PI, 1.78 * PI, 0.1, 2.0).draw())


@rom("\\", l=0.5, r=0.5)
def _backslash(g):
    C = g.C
    g.P(0, C + 60, 0.55).l(330, -120, 0.55).draw()


@rom("^", l=0.8, r=0.8, upright=True)
def _asciicircum(g):
    r = Rw(g)
    g.P(0, 330, 0).l(240, 670, 0).l(480, 330, 0).draw({"a": r, "b": r, "ne": 2.6, "role": "rule"})


@rom("_", l=0.1, r=0.1)
def _underscore(g):
    g.P(0, -130, 0).l(500, -130, 0).draw({"b": g.B * 1.5, "a": g.B * 1.5, "ne": 5})


@rom("|", l=1.0, r=1.0)
def _bar(g):
    g.P(0, 770, 0.3).l(0, -250, 0.3).draw()


@rom("¦", l=1.0, r=1.0)
def _brokenbar(g):
    g.P(0, 770, 0.3).l(0, 330, 0.3).draw()
    g.P(0, 190, 0.3).l(0, -250, 0.3).draw()


def brace(g, x0, w, top, bot, dir):
    m = (top + bot) / 2
    xr, xs = x0 + w * dir, x0 + w * 0.45 * dir
    (g.P(xr, top - g.B / 2, 0).c(xs + w * 0.2 * dir, top - 8, xs, top - 50, xs, top - 140, 0.55)
     .l(xs, m + 110, 0.55).c(xs, m + 40, x0 + w * 0.2 * dir, m + 6, x0, m, 0.1).draw())
    (g.P(x0, m, 0.1).c(x0 + w * 0.2 * dir, m - 6, xs, m - 40, xs, m - 110, 0.55)
     .l(xs, bot + 140, 0.55).c(xs, bot + 50, xs + w * 0.2 * dir, bot + 8, xr, bot + g.B / 2, 0).draw())


@rom("{", l=0.9, r=0.6)
def _braceleft(g):
    brace(g, 0, 170, 770, -250, 1)


@rom("}", l=0.6, r=0.9)
def _braceright(g):
    brace(g, 170, 170, 770, -250, -1)


@rom("~", l=0.8, r=0.8, upright=True)
def _asciitilde(g):
    r = Rw(g)
    (g.P(0, AX - 40, 0).c(40, AX + 60, 120, AX + 75, 250, AX, 0).c(380, AX - 75, 460, AX - 60, 500, AX + 40, 0)
     .draw({"a": r, "b": r, "ne": 8, "role": "rule"}))


# =====================================================================
# Punctuation
# =====================================================================

def drop_comma(g, x, y, flip=False):
    """A comma: a drop at (x, y) with a tail. flip turns it by 180 degrees."""
    d = dotD(g)
    s = -1 if flip else 1
    g.ball(x, y, d)
    (g.P(x + s * d * 0.22, y - s * d * 0.18, 0.85)
     .c(x + s * d * 0.3, y - s * d * 0.8, x, y - s * d * 1.4, x - s * d * 0.45, y - s * d * 1.75, 0).draw())


@rom("‘", l=0.9, r=0.9)
def _quoteleft(g):
    d = dotD(g)
    drop_comma(g, 0, g.C - d * 1.75, True)


@rom("“", l=0.9, r=0.9)
def _quotedblleft(g):
    d = dotD(g)
    drop_comma(g, 0, g.C - d * 1.75, True); drop_comma(g, d * 1.45, g.C - d * 1.75, True)


@rom("”", l=0.9, r=0.9)
def _quotedblright(g):
    d = dotD(g)
    drop_comma(g, 0, g.C - d / 2); drop_comma(g, d * 1.45, g.C - d / 2)


@rom("‚", l=0.9, r=0.9)
def _quotesinglbase(g):
    d = dotD(g)
    drop_comma(g, 0, d / 2)


@rom("„", l=0.9, r=0.9)
def _quotedblbase(g):
    d = dotD(g)
    drop_comma(g, 0, d / 2); drop_comma(g, d * 1.45, d / 2)


def chevron(g, x, dir):
    X = g.X
    w = 150
    x0, x1 = (x + w, x) if dir < 0 else (x, x + w)
    g.P(x0, X * 0.86, 0).l(x1, X * 0.45, 0.1).draw()
    g.P(x1, X * 0.45, 0.25).l(x0, X * 0.04, 1).draw()


@rom("‹", l=0.6, r=0.6)
def _guilsinglleft(g):
    chevron(g, 0, -1)


@rom("›", l=0.6, r=0.6)
def _guilsinglright(g):
    chevron(g, 0, 1)


@rom("«", l=0.6, r=0.6)
def _guillemetleft(g):
    chevron(g, 0, -1); chevron(g, 175, -1)


@rom("»", l=0.6, r=0.6)
def _guillemetright(g):
    chevron(g, 0, 1); chevron(g, 175, 1)


@rom("…", l=0.9, r=0.9)
def _ellipsis(g):
    d = dotD(g)
    for k in range(3):
        g.dot(k * d * 2.6, d / 2, d)


@rom("•", l=1.0, r=1.0)
def _bullet(g):
    g.dot(0, g.X * 0.52, g.A * 2.1)


@rom("¡", l=0.9, r=0.9)
def _exclamdown(g):
    X = g.X
    g.use_map(fn_of("!"), lambda x, y: (x, X - y))


@rom("¿", l=0.8, r=0.8)
def _questiondown(g):
    X = g.X
    g.use_map(fn_of("?"), lambda x, y: (325 - x, X - y))


@rom("°", l=0.7, r=0.7)
def _degree(g):
    C = g.C
    g.ring(0, C - 92, 88 - g.h * 0.25, 92 - g.B / 2, 0.5)


@rom("§", l=0.7, r=0.7)
def _section(g):
    C, D = g.C, g.D
    s_curve(g, 330, C * 0.62, C * 0.4, beaks=False)
    s_curve(g, 330, C * 0.62, -C * 0.07, beaks=False)
    g.ball(330 - 16, C * 0.4 + C * 0.62 * 0.78, g.bd * 0.85)
    g.ball(12, -C * 0.07 + C * 0.62 * 0.2, g.bd * 0.85)


@rom("¶", l=0.7, r=0.7)
def _paragraph(g):
    C, D, B = g.C, g.D, g.B
    g.P(250, C - B / 2, 0.6).l(250, D * 0.5, 0.6).draw()
    g.P(380, C - B / 2, 0.6).l(380, D * 0.5, 0.6).draw()
    g.bar(150, 380 + g.h * 0.6, C - B / 2)
    cx, cy, rx, ry = 170, C * 0.7, 125, C * 0.3 - B / 2
    pts = [g.pt(cx, cy, rx, ry, PI / 2 + k / 32 * PI, 2.1) for k in range(33)]
    g.fill(pts + [(250, cy - ry), (250, cy + ry)])


@rom("¬", **OPW)
def _logicalnot(g):
    rule(g, 0, AX + 60, 560, AX + 60)
    rule(g, 560 - Rw(g) / 2, AX + 60, 560 - Rw(g) / 2, AX - 140)


@rom("₹", **FIG)
def _rupee(g):
    C, B = g.C, g.B
    g.bar(40, 460, C - B / 2); g.bar(40, 460, C * 0.75)
    (g.P(130, C - B / 2, 0).c(300, C - B / 2, 372, C * 0.84, 372, C * 0.68, 1)
     .c(372, C * 0.53, 300, C * 0.46, 170, C * 0.46, 0).l(60, C * 0.46, 0).draw())
    g.P(120, C * 0.46, 0.15).l(400, B / 2, 1).draw(); g.serif(400, 0, 1, "b", g.A * 0.95, g.sl * 0.8)


@rom("¢", **FIG)
def _cent(g):
    X = g.X
    cx, rx, cy, ry, t0 = 260, 175 - g.h * 0.2, X * 0.55, X * 0.55 + g.o - g.B / 2, 0.2 * PI
    s = g.pt(cx, cy, rx, ry, t0)
    (g.E(cx, cy, rx, ry, t0, 0.3).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.55).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.7).arc(cx, cy, rx, ry, 1.5 * PI, 1.84 * PI, 0).draw())
    g.ball(s[0] - g.bd * 0.2, s[1] - g.bd * 0.12)
    g.P(270, X * 1.1 + 40, 0).l(250, -100, 0).draw()


@rom("£", **FIG)
def _sterling(g):
    C, B, h, bd = g.C, g.B, g.h, g.bd
    (g.P(405, C * 0.74, 0.25).c(400, C * 0.95, 340, C + g.o - B / 2, 280, C + g.o - B / 2, 0.5)
     .c(195, C + g.o - B / 2, 160, C * 0.9, 160, C * 0.72, 1).l(160, C * 0.3, 1)
     .c(160, C * 0.14, 120, 40, 50, B / 2, 0.5).draw())
    g.ball(405, C * 0.74)
    g.bar(70, 340, C * 0.45)
    g.bar(50, 455, B / 2); vbeak(g, 455 - g.S * 0.7, 0, 120)


@rom("¥", **FIG)
def _yen(g):
    C, A, B = g.C, g.A, g.B
    xl, xm, xr, yj = 20, 260, 500, C * 0.46
    g.P(xl + 30, C - B / 2, 1).l(xm, yj, 1).draw(); g.P(xr - 30, C - B / 2, 0).l(xm + A * 0.2, yj, 0).draw(); g.stem(xm, 0, yj + B)
    g.serif(xl + 30, C, -1, "b", A, g.sl * 0.6); g.serif(xr - 30, C, -1, "b", B * 1.6, g.sl * 0.6); g.serif(xm, 0, 1, "b")
    g.bar(90, 430, C * 0.4); g.bar(90, 430, C * 0.24)


@rom("€", **FIG)
def _euro(g):
    C, h = g.C, g.h
    cx = 300
    s, e = round_c(g, cx, 230 - h * 0.4, 0.2 * PI, 1.8 * PI)
    vbeak(g, s[0] - 2, s[1] - 100, s[1] + 26); vbeak(g, e[0] - 2, e[1] - 20, e[1] + 90)
    g.bar(10, 360, C * 0.6); g.bar(10, 340, C * 0.42)


@rom("©", l=0.7, r=0.7)
def _copyright(g):
    C = g.C
    cx, cy, R = 370, C / 2, 360
    g.ring(cx, cy, R - 30, R - 15, 0.35)
    cy2, rx, ry, t0 = cy, 150 - g.h * 0.5, 190, 0.22 * PI
    (g.E(cx + 10, cy2, rx, ry, t0, 0.2).arc(cx + 10, cy2, rx, ry, t0, 0.5 * PI, 0.45).arc(cx + 10, cy2, rx, ry, 0.5 * PI, PI, 0.8)
     .arc(cx + 10, cy2, rx, ry, PI, 1.5 * PI, 0.45).arc(cx + 10, cy2, rx, ry, 1.5 * PI, 1.78 * PI, 0.1).draw())


@rom("®", l=0.7, r=0.7)
def _registered(g):
    C, B = g.C, g.B
    cx, cy, R = 370, C / 2, 360
    g.ring(cx, cy, R - 30, R - 15, 0.35)
    x0, y0, y1 = cx - 110, cy - 190, cy + 190
    g.P(x0, y0 + B / 2, 0.8).l(x0, y1 - B / 2, 0.8).draw()
    ym = cy + 10
    (g.P(x0, y1 - B / 2, 0).l(x0 + 110, y1 - B / 2, 0).c(x0 + 190, y1 - B / 2, x0 + 215, y1 - 40, x0 + 215, (y1 + ym) / 2, 0.8)
     .c(x0 + 215, ym + 40, x0 + 190, ym + B / 2, x0 + 110, ym + B / 2, 0).l(x0, ym + B / 2, 0).draw())
    g.P(x0 + 100, ym, 0.1).l(x0 + 225, y0 + B / 2, 0.8).draw()


@rom("ª", l=0.7, r=0.7)
def _ordfeminine(g):
    y0, k = g.C * 0.45, 0.55
    g.use_map(fn_of("a"), lambda x, y: (x * k, y0 + y * k))
    g.bar(-10, 360 * k + 40, y0 - 70)


@rom("º", l=0.7, r=0.7)
def _ordmasculine(g):
    y0, k = g.C * 0.45, 0.55
    g.use_map(fn_of("o"), lambda x, y: (x * k, y0 + y * k))
    g.bar(-10, 440 * k + 10, y0 - 70)


# =====================================================================
# Latin-1 letters
# =====================================================================

@rom("ı")
def _dotlessi(g):
    X = g.X
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b")


@ita("ı", l=0.7, r=0.5)
def _idotlessi(g):
    exit_t(entry(g, 0, g.X), g, 0).draw()


@rom("ȷ", l=0.5)
def _dotlessj(g):
    X, D, B, bd, o = g.X, g.D, g.B, g.bd, g.o
    yb = D - o + B / 2
    (g.P(0, X - B / 2, 1).l(0, D + 150, 1).c(0, D + 50, -40, yb, -105, yb, 0.5)
     .c(-150, yb, -182, D + 22, -190, D + bd * 0.55 + 8, 0.25).draw())
    g.ball(-190, D + bd * 0.55 + 8); g.serif(0, X, -1, "l")


@rom("ß", r=0.7)
def _germandbls(g):
    X, AS, B, o, yb = g.X, g.AS, g.B, g.o, g.yb
    yt2 = AS + o - B / 2
    (g.P(0, B / 2, 1).l(0, AS - 190, 1).c(0, AS - 50, 75, yt2, 180, yt2, 0.5).c(285, yt2, 340, AS - 65, 340, AS - 170, 1)
     .c(340, X + 95, 280, X + 48, 175, X + 40, 0).draw())
    (g.P(175, X + 40, 0).c(335, X + 20, 412, X * 0.74, 412, X * 0.38, 1).c(412, X * 0.08, 320, yb, 220, yb, 0.5)
     .c(170, yb, 132, X * 0.04, 122, X * 0.13, 0.1).draw())
    g.serif(0, 0, 1, "b")


@ita("ß", l=0.7, r=0.7)
def _igermandbls(g):
    X, AS, B, o, yb, D = g.X, g.AS, g.B, g.o, g.yb, g.D
    yt2 = AS + o - B / 2
    (g.P(0, D + 40, 0.6).l(0, AS - 190, 1).c(0, AS - 50, 75, yt2, 180, yt2, 0.5).c(285, yt2, 340, AS - 65, 340, AS - 170, 1)
     .c(340, X + 95, 280, X + 48, 175, X + 40, 0).draw())
    (g.P(175, X + 40, 0).c(335, X + 20, 412, X * 0.74, 412, X * 0.38, 1).c(412, X * 0.08, 320, yb, 220, yb, 0.5)
     .c(170, yb, 132, X * 0.04, 122, X * 0.13, 0.1).draw())


@rom("æ", l=0.82, r=0.75)
def _ae(g):
    X, B, h, yt, yb, bd = g.X, g.B, g.h, g.yt, g.yb, g.bd
    xr, xq = 300, h + 4
    xb, yB = h + max(bd, g.A) * 0.42, X * 0.7
    (g.P(xb, yB, 0.25).c(xb + 6, X * 0.94, xr - 205, yt, xr - 115, yt, 0.55).c(xr - 28, yt, xr, X * 0.86, xr, X * 0.62, 1)
     .l(xr, X * 0.3, 1).draw())
    (g.P(xr - h * 0.3, X * 0.57, 0).c(xr - 110, X * 0.53, xq, X * 0.45, xq, X * 0.23, 1)
     .c(xq, X * 0.05, xq + 48, yb, xq + 108, yb, 0.6).c(xq + 185, yb, xr - 40, X * 0.06, xr - h * 0.3, X * 0.22, 0).draw())
    g.ball(xb, yB)
    g.use(fn_of("e"), xr - h)


@ita("æ", l=0.8, r=0.5)
def _iae(g):
    X, h = g.X, g.h
    x1 = 300
    ibowl(g, x1); g.P(x1, X, 0.5).l(x1, X - 44, 1).l(x1, X * 0.3, 1).draw()
    g.use(fn_of("e", True), x1 - h * 0.6)


@rom("œ", l=0.82, r=0.75)
def _oe(g):
    X, o, B, h = g.X, g.o, g.B, g.h
    g.ring(220, X / 2, 220 - h, X / 2 + o - B / 2)
    g.use(fn_of("e"), 440 - 2 * h)


@ita("œ", l=0.8, r=0.5)
def _ioe(g):
    X, h = g.X, g.h
    g.ring(200, X / 2, 200 - h, X / 2 + g.o - g.B / 2)
    g.use(fn_of("e", True), 400 - 2 * h)


@rom("ø", l=0.82, r=0.82)
def _oslash(g):
    g.use(fn_of("o"))
    g.P(450, g.X + 45, 0.15).l(-10, -45, 0.15).draw()


@ita("ø", l=0.8, r=0.8)
def _ioslash(g):
    g.use(fn_of("o", True))
    g.P(420, g.X + 45, 0.15).l(-20, -45, 0.15).draw()


@rom_cap("Ø", l=0.82, r=0.82)
def _Oslash(g):
    g.use(fn_of("O"))
    g.P(650, g.C + 45, 0.15).l(10, -45, 0.15).draw()


@rom_cap("Æ", l=0.45, r=0.6)
def _AE(g):
    C, A, B, h = g.C, g.A, g.B, g.h
    xs = 330
    g.P(0, B / 2, 0).l(xs - A * 0.2, C - B / 2, 0).draw()
    g.stem(xs, 0, C); g.serif(xs, 0, 1, "b")
    g.bar(xs - A * 0.6, xs + 385, C - B / 2); vbeak(g, xs + 385 - g.S * 0.7, C, C - 118)
    g.bar(xs - h, xs + 330, C * 0.51); vbeak(g, xs + 330 - g.S * 0.7, C * 0.51 - 60, C * 0.51 + 60)
    g.bar(xs - h, xs + 405, B / 2); vbeak(g, xs + 405 - g.S * 0.7, 0, 128)
    g.bar(72, xs, C * 0.3); g.serif(0, 0, 1, "b", B * 1.6)


@rom_cap("Œ", l=0.82, r=0.6)
def _OE(g):
    C, B, h = g.C, g.B, g.h
    cx, xs = 320, 470
    cy, rx, ry = C / 2, cx - h, C / 2 - B / 2
    (g.P(xs, C - B / 2, 0).l(cx, C - B / 2, 0).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0).l(xs, B / 2, 0).draw())
    g.stem(xs, 0, C)
    g.bar(xs, xs + 385, C - B / 2); vbeak(g, xs + 385 - g.S * 0.7, C, C - 118)
    g.bar(xs - h, xs + 330, C * 0.51); vbeak(g, xs + 330 - g.S * 0.7, C * 0.51 - 60, C * 0.51 + 60)
    g.bar(xs, xs + 405, B / 2); vbeak(g, xs + 405 - g.S * 0.7, 0, 128)


@rom_cap("Ð", r=0.85)
def _Eth(g):
    g.use(fn_of("D"))
    g.bar(-g.h - 70, g.h + 120, g.C * 0.49)


@rom_cap("Þ", r=0.7)
def _Thorn(g):
    C = g.C
    g.stem(0, 0, C); g.serif(0, C, -1, "b"); g.serif(0, 0, 1, "b"); dbowl(g, 0, C * 0.2, C * 0.8, 420, 190)


@rom("ð", l=0.82, r=0.8)
def _eth(g):
    X, AS, B, o, h = g.X, g.AS, g.B, g.o, g.h
    cx, cy, rx, ry = 222, X * 0.48, 222 - h, X * 0.48 + o - B / 2
    g.ring(cx, cy, rx, ry)
    e = g.pt(cx, cy, rx, ry, 0.15 * PI)
    g.P(e[0], e[1], 1).c(e[0] + 8, X * 1.05, 330, AS - 120, 150, AS - 8, 0).draw()
    g.P(150, AS - 260, 0).l(390, AS - 140, 0).draw()


@rom("þ", r=0.82)
def _thorn(g):
    AS, D = g.AS, g.D
    g.stem(0, D, AS); g.serif(0, AS, -1, "l"); g.serif(0, D, 1, "b"); bowl_right(g, 0)


@ita("þ", l=0.7, r=0.8)
def _ithorn(g):
    X, D, AS = g.X, g.D, g.AS
    entry(g, 0, AS).l(0, D + g.B / 2, 1).draw(); g.serif(0, D, 1, "b")
    (iarch(g, 0, 330, X).l(330, X * 0.4, 1).c(330, X * 0.1, 270, g.yb, 190, g.yb, 0.5)
     .c(120, g.yb, 40, X * 0.08, g.h * 0.3, X * 0.25, 0).draw())


# ---------- ligatures ffi, ffl ----------

def ff_first(g, x0, x2):
    AS, B, o, h = g.AS, g.B, g.o, g.h
    yt2 = AS + o - B / 2
    (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 60, yt2, x0 + 140, yt2, 0.5)
     .c(x0 + 200, yt2, x2 - h - 6, AS - 30, x2 - h * 0.4, AS - 82, 0.05).draw())
    g.serif(x0, 0, 1, "b", g.A, g.sl * 1.2)


@rom("ﬃ")
def _ffi(g):
    x2 = 262
    ff_first(g, 0, x2)
    g.bar(-g.h - 78, x2, g.X - g.B / 2)
    g.use(fn_of("ﬁ"), x2)


@rom("ﬄ")
def _ffl(g):
    x2 = 262
    ff_first(g, 0, x2)
    g.bar(-g.h - 78, x2, g.X - g.B / 2)
    g.use(fn_of("ﬂ"), x2)


@ita("ﬃ", l=0.3, r=0.5)
def _iffi(g):
    x = 190
    it_f(g, x, x + 128)
    g.bar(x - 130, x + 215, g.X - g.B / 2)
    g.use(fn_of("ﬁ", True), 215)


@ita("ﬄ", l=0.3, r=0.5)
def _iffl(g):
    x = 190
    it_f(g, x, x + 128)
    g.bar(x - 130, x + 215, g.X - g.B / 2)
    g.use(fn_of("ﬂ", True), 215)


# =====================================================================
# Greek: the rest of the basic lowercase and the capitals that are not
# Latin look-alikes. Same rules as the sketch's Greek.
# =====================================================================

def gstem_top(g, x):
    """A Greek stem start: light at the top, full by 60 units down."""
    return g.P(x, g.X - g.B / 2, 0.5).l(x, g.X - 60, 1)


def tail_hook(p, g, x, y0):
    """The descending hook of ζ, ξ, ς."""
    return p.c(x + 110, y0 - 5, x + 140, y0 - 55, x + 125, y0 - 115, 0.9).c(x + 115, y0 - 165, x + 65, y0 - 190, x + 15, y0 - 195, 0.1)


@rom("ζ", l=0.8, r=0.6)
def _zeta(g):
    X, AS = g.X, g.AS
    g.P(70, AS - 40, 0.05).c(160, AS - 22, 260, AS - 18, 340, AS - 36, 0.3).draw()
    p = (g.P(330, AS - 40, 0.3).c(170, X * 1.05, 25, X * 0.62, 25, X * 0.3, 1).c(25, 55, 95, 28, 205, 22, 0.35))
    tail_hook(p, g, 205, 22).draw()


@rom("η", l=0.7, r=0.6)
def _eta(g):
    X, D, B, h = g.X, g.D, g.B, g.h
    x1 = 330
    gstem_top(g, 0).l(0, B / 2, 1).draw()
    yt = X + g.o - B / 2
    xm = x1 / 2 + 12
    (g.P(h * 0.3, X * 0.6, 0).c(h * 0.3 + 30, X * 0.88, xm - xm * 0.55, yt, xm, yt, 0.55)
     .c(xm + (x1 - xm) * 0.6, yt, x1, X * 0.9, x1, X * 0.6, 1).l(x1, D + 40, 1).l(x1, D + B / 2, 0.7).draw())


@rom("ι", l=0.7, r=0.5)
def _iota(g):
    yb = g.yb
    gstem_top(g, 0).l(0, 70, 1).c(0, 22, 22, yb, 60, yb, 0.3).c(80, yb, 93, 18, 96, 42, 0).draw()


@rom("κ", l=0.7, r=0.55)
def _kappa(g):
    X, B, h, bd = g.X, g.B, g.h, g.bd
    gstem_top(g, 0).l(0, B / 2, 1).draw()
    g.P(h - 2, X * 0.36, 0).c(110, X * 0.5, 210, X * 0.9, 300, X - 30, 0).draw()
    g.ball(306, X - 36, bd * 0.75)
    (g.P(110, X * 0.55, 0.9).l(262, 70, 1).c(272, 30, 290, g.yb, 320, g.yb, 0.3)
     .c(340, g.yb, 352, 18, 355, 42, 0).draw())


@rom("ν", l=0.6, r=0.5)
def _nu(g):
    X, A, B, o = g.X, g.A, g.B, g.o
    g.P(-40, X - 45, 0.2).c(-20, X + 2, 20, X + 4, 30, X - 40, 1).l(205, B / 2 - o, 0.9).draw()
    g.P(205 + A * 0.1, B / 2 - o, 0).c(300, X * 0.3, 385, X * 0.58, 392, X - 10, 0.25).draw()


@rom("ξ", l=0.8, r=0.6)
def _xi(g):
    X, AS = g.X, g.AS
    g.P(70, AS - 40, 0.05).c(160, AS - 22, 260, AS - 18, 340, AS - 36, 0.3).draw()
    (g.P(320, AS - 40, 0.2).c(190, AS - 48, 95, AS - 100, 95, AS - 175, 1)
     .c(95, X + 62, 170, X + 32, 270, X + 30, 0).draw())
    p = (g.P(270, X + 30, 0).c(130, X + 30, 25, X * 0.66, 25, X * 0.32, 1).c(25, 55, 95, 28, 205, 22, 0.35))
    tail_hook(p, g, 205, 22).draw()


@rom("τ", l=0.5, r=0.5)
def _tau(g):
    X, A, B, o = g.X, g.A, g.B, g.o
    yb, bb = -o + B / 2, A * 0.36
    yb2 = X - bb / 2
    g.P(-12, X * 0.76, 0.4).c(0, X * 0.92, 40, yb2, 110, yb2, 0.6).l(400, yb2, 0.3).draw({"b": bb})
    g.P(205, X - bb, 1).l(205, 78, 1).c(205, 25, 225, yb, 259, yb, 0.3).c(285, yb, 299, 20, 302, 46, 0).draw()


@rom("υ", l=0.7, r=0.75)
def _upsilon(g):
    X, yb = g.X, g.yb
    (gstem_top(g, 0).l(0, X * 0.4, 1).c(0, X * 0.08, 90, yb, 185, yb, 0.5).c(300, yb, 375, X * 0.25, 375, X * 0.58, 1)
     .c(375, X * 0.84, 352, X * 0.96, 318, X + 6, 0.1).draw())


@rom("χ", l=0.6, r=0.6)
def _chi(g):
    X, D = g.X, g.D
    g.P(-35, X - 50, 0.2).c(-15, X + 2, 25, X + 4, 45, X - 45, 1).l(365, D + 70, 1).c(375, D + 30, 395, D + 18, 425, D + 40, 0).draw()
    g.P(405, X - 12, 0).l(5, D + 15, 0).draw()


@rom("ς", l=0.82, r=0.55)
def _sigmafinal(g):
    X, yt, h, bd = g.X, g.yt, g.h, g.bd
    p = (g.P(335, X * 0.79, 0.2).c(328, X * 0.97, 268, yt, 205, yt, 0.4).c(85, yt, h, X * 0.75, h, X * 0.42, 1)
         .c(h, X * 0.1, 95, 26, 210, 20, 0.35))
    tail_hook(p, g, 210, 20).draw()
    g.ball(335, X * 0.79, bd * 0.85)


@rom_cap("Θ", l=0.82, r=0.82)
def _Theta(g):
    C = g.C
    g.use(fn_of("O"))
    g.bar(330 - 165, 330 + 165, C / 2)
    for x in (330 - 165, 330 + 165):
        vbeak(g, x + (g.S * 0.7 if x < 330 else -g.S * 0.7), C / 2 - 52, C / 2 + 52)


@rom_cap("Λ", l=0.45, r=0.45)
def _Lambda(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    xl, xm, xr = 0, 280, 560
    g.P(xl, B / 2, 0).l(xm - A * 0.15, C + o - B / 2, 0).draw(); g.P(xm - A * 0.25, C + o - B / 2, 0.9).l(xr, B / 2, 1).draw()
    g.serif(xl, 0, 1, "b", B * 1.6); g.serif(xr, 0, 1, "b")


@rom_cap("Ξ", l=0.6, r=0.6)
def _Xi(g):
    C, B, S = g.C, g.B, g.S
    W = 470
    g.bar(0, W, C - B / 2); vbeak(g, S * 0.7, C, C - 120); vbeak(g, W - S * 0.7, C, C - 120)
    g.bar(70, W - 70, C * 0.5); vbeak(g, 70 + S * 0.7, C * 0.5 - 55, C * 0.5 + 55); vbeak(g, W - 70 - S * 0.7, C * 0.5 - 55, C * 0.5 + 55)
    g.bar(0, W, B / 2); vbeak(g, S * 0.7, 0, 120); vbeak(g, W - S * 0.7, 0, 120)


@rom_cap("Π")
def _Pi(g):
    C, B, h = g.C, g.B, g.h
    x1 = 480
    g.stem(0, 0, C); g.stem(x1, 0, C); g.bar(-h, x1 + h, C - B / 2)
    g.serif(0, C, -1, "l"); g.serif(x1, C, -1, "r"); g.serif(0, 0, 1, "b"); g.serif(x1, 0, 1, "b")


@rom_cap("Φ", l=0.82, r=0.82)
def _Phi(g):
    C, B, o = g.C, g.B, g.o
    cx = 330
    g.stem(cx, 0, C); g.serif(cx, C, -1, "b"); g.serif(cx, 0, 1, "b")
    g.ring(cx, C / 2, 300 - g.h, C * 0.3, 1)


@rom_cap("Ψ", l=0.6, r=0.6)
def _Psi(g):
    C, B, A, o = g.C, g.B, g.A, g.o
    cx, w = 320, 285
    g.stem(cx, 0, C); g.serif(cx, C, -1, "b"); g.serif(cx, 0, 1, "b")
    yb = C * 0.3
    (g.P(cx - w, C - B / 2, 1).l(cx - w, C * 0.66, 1).c(cx - w, C * 0.42, cx - w * 0.55, yb, cx, yb, 0.4)
     .c(cx + w * 0.55, yb, cx + w, C * 0.42, cx + w, C * 0.66, 0).l(cx + w, C - B / 2, 0).draw())
    g.serif(cx - w, C, -1, "b"); g.serif(cx + w, C, -1, "b", B * 1.6, g.sl * 0.8)


# =====================================================================
# Maths: the rule pen (square nib, R thick), centred on the axis (250).
# =====================================================================

@rom("÷", **OPW)
def _divide(g):
    rule(g, 0, AX, 560, AX)
    for y in (AX + 160, AX - 160):
        g.dot(280, y, g.A * 0.95)


@rom("±", **OPW)
def _plusminus(g):
    rule(g, 0, AX + 80, 560, AX + 80); rule(g, 280, AX - 170, 280, AX + 330); rule(g, 0, AX - 250, 560, AX - 250)


@rom("≠", **OPW)
def _notequal(g):
    rule(g, 0, AX + 108, 560, AX + 108); rule(g, 0, AX - 108, 560, AX - 108); rule(g, 170, AX - 270, 390, AX + 270, 3)


@rom("≤", **OPW)
def _lessequal(g):
    r = Rw(g)
    g.P(500, AX + 310, 0).l(0, AX + 95, 0).l(500, AX - 120, 0).draw({"a": r, "b": r, "ne": 2.6, "role": "rule"})
    rule(g, 0, AX - 260, 500, AX - 260)


@rom("≥", **OPW)
def _greaterequal(g):
    r = Rw(g)
    g.P(0, AX + 310, 0).l(500, AX + 95, 0).l(0, AX - 120, 0).draw({"a": r, "b": r, "ne": 2.6, "role": "rule"})
    rule(g, 0, AX - 260, 500, AX - 260)


@rom("≈", **OPW)
def _approxequal(g):
    r = Rw(g)
    for dy in (95, -95):
        y = AX + dy
        (g.P(0, y - 40, 0).c(40, y + 60, 140, y + 75, 280, y, 0).c(420, y - 75, 520, y - 60, 560, y + 40, 0)
         .draw({"a": r, "b": r, "ne": 8, "role": "rule"}))


@rom("≡", **OPW)
def _equivalence(g):
    for dy in (165, 0, -165):
        rule(g, 0, AX + dy, 560, AX + dy)


def member(g, bar=True, raise_=0):
    r = Rw(g)
    t, b = AX + 270 + raise_, AX - 270 + raise_
    m = (t + b) / 2
    (g.P(520, t, 0).l(300, t, 0).c(130, t, 40, m + 150, 40, m, 0).c(40, m - 150, 130, b, 300, b, 0).l(520, b, 0)
     .draw({"a": r, "b": r, "ne": 8, "role": "rule"}))
    if bar:
        rule(g, 40, m, 500, m)


@rom("∈", **OPW)
def _element(g):
    member(g)


@rom("∉", **OPW)
def _notelement(g):
    member(g); rule(g, 150, AX - 330, 420, AX + 330, 3)


@rom("⊂", **OPW)
def _subset(g):
    member(g, bar=False)


@rom("⊆", **OPW)
def _reflexsubset(g):
    member(g, bar=False, raise_=80); rule(g, 40, AX - 290, 520, AX - 290)


@rom("∪", **OPW)
def _union(g):
    r = Rw(g)
    (g.P(0, AX + 300, 0).l(0, AX).c(0, AX - 180, 110, AX - 280, 280, AX - 280).c(450, AX - 280, 560, AX - 180, 560, AX)
     .l(560, AX + 300).draw({"a": r, "b": r, "ne": 8, "role": "rule"}))


@rom("∩", **OPW)
def _intersection(g):
    r = Rw(g)
    (g.P(0, AX - 300, 0).l(0, AX).c(0, AX + 180, 110, AX + 280, 280, AX + 280).c(450, AX + 280, 560, AX + 180, 560, AX)
     .l(560, AX - 300).draw({"a": r, "b": r, "ne": 8, "role": "rule"}))


@rom("∘", **OPW)
def _ring(g):
    g.ring(0, AX, 95, 95, 0.3)


def arrow_head(g, x, dir):
    r = Rw(g)
    for s in (1, -1):
        (g.P(x, AX, 0).c(x - dir * 40, AX + s * 20, x - dir * 85, AX + s * 70, x - dir * 120, AX + s * 150, 0)
         .draw({"a": r, "b": r, "ne": 8, "role": "rule"}))


@rom("→", **OPW)
def _arrowright(g):
    rule(g, 0, AX, 780, AX); arrow_head(g, 800, 1)


@rom("←", **OPW)
def _arrowleft(g):
    rule(g, 20, AX, 800, AX); arrow_head(g, 0, -1)


@rom("↔", **OPW)
def _arrowboth(g):
    rule(g, 20, AX, 880, AX); arrow_head(g, 0, -1); arrow_head(g, 900, 1)


@rom("∀", l=0.45, r=0.45, upright=True)
def _universal(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    g.P(0, C - B / 2, 1).l(275 - A * 0.2, B / 2 - o, 0.9).draw(); g.P(275 + A * 0.1, B / 2 - o, 0).l(550, C - B / 2, 0).draw()
    g.bar(75, 475, C * 0.62)


@rom("∃", l=0.6, r=0.6, upright=True)
def _existential(g):
    C, B, h = g.C, g.B, g.h
    x = 420
    g.stem(x, 0, C)
    g.bar(0, x + h, C - B / 2); g.bar(60, x + h, C * 0.51); g.bar(0, x + h, B / 2)


@rom("∅", l=0.7, r=0.7, upright=True)
def _emptyset(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    g.ring(290, C / 2, 250 - h, C / 2 + o - B / 2, 1, 2.05)
    g.P(560, C + 50, 0.3).l(20, -50, 0.3).draw()


@rom("∝", **OPW)
def _proportional(g):
    r = Rw(g)
    a, b, cx = 330, 150, 290
    p = g.P(560, AX - 150, 0).c(470, AX - 150, 400, AX - 110, cx + 20, AX - 15, 0)
    pts = []
    for i in range(0, 101):
        t = PI + i / 100 * PI
        pts.append((cx + a * 0.9 * math.sin(t) / (1 + 0.18 * math.cos(2 * t)),
                    AX + b * math.sin(2 * t) / (1 + 0.18 * math.cos(2 * t)) * 1.05))
    for x, y in pts:
        p.l(x, y, 0)
    p.c(cx + 80, AX + 90, 470, AX + 150, 560, AX + 150, 0).draw({"a": r, "b": r, "ne": 8, "role": "rule"})


@rom("∏", l=0.6, r=0.6, bigop=True, upright=True)
def _product(g):
    B, h = g.B, g.h
    top, bot = AX + 520, AX - 520
    x0, x1 = 60, 640
    g.stem(x0, bot, top); g.stem(x1, bot, top)
    g.bar(x0 - h - 40, x1 + h + 40, top - B / 2)
    g.serif(x0, bot, 1, "b"); g.serif(x1, bot, 1, "b")


@rom("″", l=0.4, r=0.4)
def _second(g):
    for dx in (0, 150):
        g.P(150 + dx, 720, 1).l(40 + dx, 440, 0.1).draw()


@rom("◌", l=0.6, r=0.6, upright=True)
def _dottedcircle(g):
    cx, cy, R = 300, g.X / 2, 270
    for k in range(12):
        a = k * TAU / 12
        g.dot(cx + R * math.cos(a), cy + R * math.sin(a), 46)


@rom("⁄", l=-0.6, r=-0.6)
def _fraction(g):
    C = g.C
    g.P(330, C + 10, 0.35).l(-10, -20, 0.35).draw()
