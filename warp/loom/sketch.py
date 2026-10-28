"""The glyph tables of the approved sketch 0.2, ported to Python.

Source: reference/warp-sketch-0.2.js, the `def(...)` and `idef(...)`
calls. Each function draws the centre-lines of one glyph with the
builder `g` (loom/engine.py). Coordinates and pressures are the
sketch's, unchanged. G holds the roman glyphs, GI the italic overrides.

This file defines the outlines of machine-made Warp: SIL Open Font
License 1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

import math

from loom.engine import PI, TAU, GlyphDef, flags

G: dict[str, GlyphDef] = {}
GI: dict[str, GlyphDef] = {}


def rom(ch, **o):
    def deco(fn):
        G[ch] = GlyphDef(fn=fn, **{**flags(ch), **o})
        return fn
    return deco


def ita(ch, **o):
    def deco(fn):
        GI[ch] = GlyphDef(fn=fn, **{**flags(ch), **o})
        return fn
    return deco


# =====================================================================
# ROMAN LOWERCASE. Coordinates are centre-lines. g.h = half stem.
# g.yt / g.yb = centre-line of round tops / bottoms.
# =====================================================================

def arch(g, x0, x1, top):
    """Hairline branch out of the stem, over the shoulder, down the right stem."""
    B, h = g.B, g.h
    yt = top + g.o - B / 2
    xm = (x0 + x1) / 2 + 12
    (g.P(x0 + h * 0.3, top * 0.6, 0).c(x0 + h * 0.3 + 30, top * 0.88, xm - (xm - x0) * 0.55, yt, xm, yt, 0.55)
     .c(xm + (x1 - xm) * 0.6, yt, x1, top * 0.9, x1, top * 0.6, 1).l(x1, B / 2, 1).draw())
    g.serif(x1, 0, 1, "b")


def bowl_right(g, x0):
    """b, p: bowl hanging off a left stem."""
    X, o, B = g.X, g.o, g.B
    rx = 205
    cx, cy, ry, t0 = x0 + rx, X / 2, X / 2 + o - B / 2, 0.84 * PI
    (g.E(cx, cy, rx, ry, t0, 0).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.6).arc(cx, cy, rx, ry, 0.5 * PI, 0, 1)
     .arc(cx, cy, rx, ry, 0, -0.5 * PI, 0.6).arc(cx, cy, rx, ry, -0.5 * PI, -t0, 0).draw())


def bowl_left(g, x1):
    """d, q."""
    X, o, B = g.X, g.o, g.B
    rx = 205
    cx, cy, ry, t0 = x1 - rx, X / 2, X / 2 + o - B / 2, 0.16 * PI
    (g.E(cx, cy, rx, ry, t0, 0).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.6).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.6).arc(cx, cy, rx, ry, 1.5 * PI, 2 * PI - t0, 0).draw())


def dotD(g):
    return g.A * 1.16


@rom("n")
def _n(g):
    X = g.X
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b"); arch(g, 0, 330, X)


@rom("m")
def _m(g):
    X = g.X
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b"); arch(g, 0, 290, X); arch(g, 290, 580, X)


@rom("h")
def _h(g):
    X, AS = g.X, g.AS
    g.stem(0, 0, AS); g.serif(0, AS, -1, "l"); g.serif(0, 0, 1, "b"); arch(g, 0, 330, X)


@rom("u")
def _u(g):
    B, X, yb, h = g.B, g.X, g.yb, g.h
    x0, x1 = 0, 330
    xm = (x0 + x1) / 2 - 12
    (g.P(x0, X - B / 2, 1).l(x0, X * 0.36, 1).c(x0, X * 0.08, xm - (xm - x0) * 0.6, yb, xm, yb, 0.55)
     .c(xm + (x1 - xm) * 0.55, yb, x1 - h * 0.3 - 30, X * 0.12, x1 - h * 0.3, X * 0.4, 0).draw())
    g.serif(x0, X, -1, "l"); g.stem(x1, 0, X); g.serif(x1, X, -1, "l"); g.serif(x1, 0, 1, "r")


@rom("o", l=0.82, r=0.82)
def _o(g):
    X, o, B, h = g.X, g.o, g.B, g.h
    g.ring(220, X / 2, 220 - h, X / 2 + o - B / 2)


@rom("c", l=0.82, r=0.7)
def _c(g):
    X, o, B, h, bd = g.X, g.o, g.B, g.h, g.bd
    cx, rx, cy, ry, t0 = 220, 220 - h, X / 2, X / 2 + o - B / 2, 0.2 * PI
    s = g.pt(cx, cy, rx, ry, t0)
    (g.E(cx, cy, rx, ry, t0, 0.3).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.55).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.7).arc(cx, cy, rx, ry, 1.5 * PI, 1.84 * PI, 0).draw())
    g.ball(s[0] - bd * 0.2, s[1] - bd * 0.12)


@rom("e", l=0.82, r=0.75)
def _e(g):
    X, o, B, h = g.X, g.o, g.B, g.h
    cx, rx, cy, ry, yc = 222, 222 - h, X / 2, X / 2 + o - B / 2, X * 0.56
    t0 = math.asin(((yc - cy) / ry) ** (g.ex / 2))
    g.bar(cx - rx - h * 0.5, cx + rx + h * 0.5, yc)
    (g.E(cx, cy, rx, ry, t0, 0.9).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.7).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.7).arc(cx, cy, rx, ry, 1.5 * PI, 1.86 * PI, 0).draw())


@rom("a", r=0.6)
def _a(g):
    X, B, h, yt, yb, bd = g.X, g.B, g.h, g.yt, g.yb, g.bd
    xr, xq = 320, h + 4
    xb, yB = h + max(bd, g.A) * 0.42, X * 0.7
    (g.P(xb, yB, 0.25).c(xb + 6, X * 0.94, xr - 205, yt, xr - 115, yt, 0.55).c(xr - 28, yt, xr, X * 0.86, xr, X * 0.62, 1)
     .l(xr, X * 0.13, 1).c(xr, X * 0.03, xr + 22, yb, xr + 56, yb, 0.25).c(xr + 78, yb, xr + 92, 16, xr + 96, 40, 0).draw())
    (g.P(xr - h * 0.3, X * 0.57, 0).c(xr - 110, X * 0.53, xq, X * 0.45, xq, X * 0.23, 1)
     .c(xq, X * 0.05, xq + 48, yb, xq + 108, yb, 0.6).c(xq + 185, yb, xr - 40, X * 0.06, xr - h * 0.3, X * 0.22, 0).draw())
    g.ball(xb, yB)


@rom("b", r=0.82)
def _b(g):
    AS = g.AS
    g.stem(0, 0, AS); g.serif(0, AS, -1, "l"); bowl_right(g, 0)


@rom("p", r=0.82)
def _p(g):
    X, D = g.X, g.D
    g.stem(0, D, X); g.serif(0, X, -1, "l"); g.serif(0, D, 1, "b"); bowl_right(g, 0)


@rom("d", l=0.82)
def _d(g):
    AS = g.AS
    x1 = 410
    g.stem(x1, 0, AS); g.serif(x1, AS, -1, "l"); g.serif(x1, 0, 1, "r"); bowl_left(g, x1)


@rom("q", l=0.82)
def _q(g):
    X, D = g.X, g.D
    x1 = 410
    g.stem(x1, D, X); g.serif(x1, D, 1, "b"); bowl_left(g, x1)


@rom("i")
def _i(g):
    X, AS = g.X, g.AS
    g.stem(0, 0, X); g.serif(0, X, -1, "l"); g.serif(0, 0, 1, "b"); g.dot(-g.A * 0.04, X + (AS - X) * 0.66, dotD(g))


@rom("j", l=0.5)
def _j(g):
    X, AS, D, B, bd, o = g.X, g.AS, g.D, g.B, g.bd, g.o
    x0, yb = 0, D - o + B / 2
    (g.P(x0, X - B / 2, 1).l(x0, D + 150, 1).c(x0, D + 50, x0 - 40, yb, x0 - 105, yb, 0.5)
     .c(x0 - 150, yb, x0 - 182, D + 22, x0 - 190, D + bd * 0.55 + 8, 0.25).draw())
    g.ball(x0 - 190, D + bd * 0.55 + 8); g.serif(x0, X, -1, "l"); g.dot(-g.A * 0.04, X + (AS - X) * 0.66, dotD(g))


@rom("k", r=0.6)
def _k(g):
    X, AS, A, B, h = g.X, g.AS, g.A, g.B, g.h
    x0 = 0
    ax = x0 + 262
    g.stem(x0, 0, AS); g.serif(x0, AS, -1, "l"); g.serif(x0, 0, 1, "b")
    g.P(x0 + h - 4, X * 0.26, 0).l(ax, X - B / 2, 0).draw(); g.serif(ax, X, -1, "b", B * 1.6, g.sl * 0.8)
    g.P(x0 + 128, X * 0.55, 0.85).l(x0 + 292, B / 2, 1).draw(); g.serif(x0 + 292, 0, 1, "b", A * 0.95)


@rom("l")
def _l(g):
    AS = g.AS
    g.stem(0, 0, AS); g.serif(0, AS, -1, "l"); g.serif(0, 0, 1, "b")


@rom("r", r=0.5)
def _r(g):
    X, B, h, yt, bd, A = g.X, g.B, g.h, g.yt, g.bd, g.A
    x0 = 0
    xe, ye = x0 + 228, X - max(bd, A * 0.6) * 0.45 - 8
    g.stem(x0, 0, X); g.serif(x0, X, -1, "l"); g.serif(x0, 0, 1, "b", A, g.sl * 1.15)
    (g.P(x0 + h * 0.3, X * 0.6, 0).c(x0 + h * 0.3 + 28, X * 0.88, x0 + 98, yt, x0 + 158, yt, 0.5)
     .c(x0 + 200, yt, xe, X * 0.96, xe, ye, 0.25).draw())
    g.ball(xe - bd * 0.05, ye)


@rom("s", l=0.8, r=0.8)
def _s(g):
    X, B, yt, yb, h, S = g.X, g.B, g.yt, g.yb, g.h, g.S
    W = 330
    (g.P(W - 14, X * 0.79, 0.12).c(W - 28, X * 0.95, W * 0.68, yt, W * 0.5, yt, 0.5).c(W * 0.24, yt, h + 2, X * 0.92, h + 2, X * 0.74, 1)
     .c(h + 2, X * 0.5, W - h - 2, X * 0.52, W - h - 2, X * 0.27, 1).c(W - h - 2, X * 0.08, W * 0.76, yb, W * 0.5, yb, 0.5)
     .c(W * 0.27, yb, 30, X * 0.06, 12, X * 0.21, 0.12).draw())
    g.P(W - 14, X * 0.66, 0).l(W - 14, X * 0.9, 0).draw({"a": S * 1.4, "b": S, "role": "serif"})
    g.P(12, X * 0.1, 0).l(12, X * 0.34, 0).draw({"a": S * 1.4, "b": S, "role": "serif"})


@rom("t", l=0.7, r=0.6)
def _t(g):
    X, B, yb, h = g.X, g.B, g.yb, g.h
    x0 = 0
    (g.P(x0, X + 118, 0.45).l(x0, X * 0.8, 1).l(x0, X * 0.25, 1).c(x0, X * 0.04, x0 + 40, yb, x0 + 100, yb, 0.45)
     .c(x0 + 150, yb, x0 + 186, X * 0.06, x0 + 196, X * 0.2, 0).draw())
    g.bar(x0 - h - 82, x0 + h + 108, X - B / 2)


@rom("v", l=0.5, r=0.5)
def _v(g):
    X, A, B, o = g.X, g.A, g.B, g.o
    xl, xm, xr = 0, 225, 445
    g.P(xl, X - B / 2, 1).l(xm - A * 0.2, B / 2 - o, 0.9).draw(); g.P(xm + A * 0.1, B / 2 - o, 0).l(xr, X - B / 2, 0).draw()
    g.serif(xl, X, -1, "b", A); g.serif(xr, X, -1, "b", B * 1.6, g.sl * 0.85)


@rom("w", l=0.5, r=0.5)
def _w(g):
    X, A, B, o = g.X, g.A, g.B, g.o
    a, b, c, d, e = 0, 172, 318, 490, 640
    g.P(a, X - B / 2, 1).l(b - A * 0.2, B / 2 - o, 0.9).draw(); g.P(b + A * 0.1, B / 2 - o, 0).l(c, X - B / 2, 0).draw()
    g.P(c, X - B / 2, 1).l(d - A * 0.2, B / 2 - o, 0.9).draw(); g.P(d + A * 0.1, B / 2 - o, 0).l(e, X - B / 2, 0).draw()
    g.serif(a, X, -1, "b", A); g.serif(c, X, -1, "b", A * 1.1, g.sl * 0.7); g.serif(e, X, -1, "b", B * 1.6, g.sl * 0.85)


@rom("x", l=0.6, r=0.6)
def _x(g):
    X, A, B = g.X, g.A, g.B
    xl, xr = 0, 410
    g.P(xl + 8, X - B / 2, 1).l(xr - 8, B / 2, 1).draw(); g.P(xl + 12, B / 2, 0).l(xr - 12, X - B / 2, 0).draw()
    g.serif(xl + 8, X, -1, "b", A); g.serif(xr - 8, 0, 1, "b", A)
    g.serif(xl + 12, 0, 1, "b", B * 1.6, g.sl * 0.85); g.serif(xr - 12, X, -1, "b", B * 1.6, g.sl * 0.85)


@rom("y", l=0.5, r=0.5)
def _y(g):
    X, A, B, D, bd, o = g.X, g.A, g.B, g.D, g.bd, g.o
    xl, xm, xr = 0, 225, 445
    g.P(xl, X - B / 2, 1).l(xm - A * 0.15, B / 2 - o, 0.85).draw()
    k = (xr - xm) / X
    xb = xm - k * (-D * 0.55)
    (g.P(xr, X - B / 2, 0).l(xb, D * 0.55, 0.1)
     .c(xb - k * 60, D * 0.55 - 60, xm - 150, D + bd * 0.55 + 6, xm - 205, D + bd * 0.55 + 6, 0.35).draw())
    g.ball(xm - 205, D + bd * 0.55 + 6)
    g.serif(xl, X, -1, "b", A); g.serif(xr, X, -1, "b", B * 1.6, g.sl * 0.85)


@rom("z", l=0.7, r=0.7)
def _z(g):
    X, A, B, S = g.X, g.A, g.B, g.S
    x0, x1 = 0, 370
    g.bar(x0, x1, X - B / 2); g.bar(x0, x1, B / 2)
    g.P(x1 - A * 0.5, X - B, 1).l(x0 + A * 0.5, B, 1).draw()
    g.P(x0 + S * 0.7, X, 0).l(x0 + S * 0.7, X - 115, 0).draw({"a": S * 1.4, "b": S, "role": "serif"})
    g.P(x1 - S * 0.7, 0, 0).l(x1 - S * 0.7, 125, 0).draw({"a": S * 1.4, "b": S, "role": "serif"})


@rom("f", r=-0.7)
def _f(g):
    X, AS, B, h, bd, A, o = g.X, g.AS, g.B, g.h, g.bd, g.A, g.o
    x0 = 0
    yt2, xe, ye = AS + o - B / 2, x0 + 232, AS - max(bd, A * 0.6) * 0.5 - 12
    (g.P(x0, B / 2, 1).l(x0, AS - 175, 1).c(x0, AS - 45, x0 + 62, yt2, x0 + 150, yt2, 0.5)
     .c(x0 + 205, yt2, xe, AS - 25, xe, ye, 0.25).draw())
    g.ball(xe, ye); g.bar(x0 - h - 78, x0 + h + 118, X - B / 2); g.serif(x0, 0, 1, "b", A, g.sl * 1.2)


# =====================================================================
# ROMAN CAPITALS. Thick stems, hairline arms, beaks on arm ends.
# =====================================================================

def vbeak(g, x, y0, y1):
    g.P(x, y0, 0).l(x, y1, 0).draw({"a": g.S * 1.4, "b": g.S, "role": "serif"})


def dbowl(g, x0, y0, y1, xr, xf):
    """Flat hairline top and bottom, round thick right side."""
    B = g.B
    r, ym, a, b = (y1 - y0) / 2, (y0 + y1) / 2, y1 - B / 2, y0 + B / 2
    (g.P(x0, a, 0).l(xf, a, 0).c(xf + (xr - xf) * 0.62, a, xr, ym + r * 0.55, xr, ym, 1)
     .c(xr, ym - r * 0.55, xf + (xr - xf) * 0.62, b, xf, b, 0).l(x0, b, 0).draw())


@rom("H")
def _H(g):
    C, B = g.C, g.B
    x1 = 470
    g.stem(0, 0, C); g.stem(x1, 0, C); g.bar(0, x1, C * 0.5)
    for x in (0, x1):
        g.serif(x, C, -1, "b"); g.serif(x, 0, 1, "b")


@rom("I")
def _I(g):
    C = g.C
    g.stem(0, 0, C); g.serif(0, C, -1, "b"); g.serif(0, 0, 1, "b")


@rom("E", r=0.6)
def _E(g):
    C, B, h = g.C, g.B, g.h
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "l")
    g.bar(-h, 385, C - B / 2); vbeak(g, 385 - g.S * 0.7, C, C - 118)
    g.bar(-h, 330, C * 0.51); vbeak(g, 330 - g.S * 0.7, C * 0.51 - 60, C * 0.51 + 60)
    g.bar(-h, 405, B / 2); vbeak(g, 405 - g.S * 0.7, 0, 128)


@rom("F", r=0.5)
def _F(g):
    C, B, h = g.C, g.B, g.h
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "b")
    g.bar(-h, 385, C - B / 2); vbeak(g, 385 - g.S * 0.7, C, C - 118)
    g.bar(-h, 325, C * 0.5); vbeak(g, 325 - g.S * 0.7, C * 0.5 - 60, C * 0.5 + 60)


@rom("L", r=0.6)
def _L(g):
    C, B, h = g.C, g.B, g.h
    g.stem(0, 0, C); g.serif(0, C, -1, "b"); g.serif(0, 0, 1, "l")
    g.bar(-h, 395, B / 2); vbeak(g, 395 - g.S * 0.7, 0, 135)


@rom("T", l=0.5, r=0.5)
def _T(g):
    C, B = g.C, g.B
    W = 540
    g.bar(0, W, C - B / 2); vbeak(g, g.S * 0.7, C, C - 130); vbeak(g, W - g.S * 0.7, C, C - 130)
    g.stem(W / 2, 0, C); g.serif(W / 2, 0, 1, "b")


@rom("D", r=0.85)
def _D(g):
    C = g.C
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "l"); dbowl(g, 0, 0, C, 500, 200)


@rom("B", r=0.8)
def _B(g):
    C = g.C
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "l")
    dbowl(g, 0, C * 0.52 - g.B, C, 385, 170); dbowl(g, 0, 0, C * 0.52, 440, 190)


@rom("P", r=0.7)
def _P(g):
    C = g.C
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "b"); dbowl(g, 0, C * 0.44, C, 420, 190)


def round_c(g, cx, rx, t0, t1):
    C, o, B = g.C, g.o, g.B
    cy, ry = C / 2, C / 2 + o - B / 2
    (g.E(cx, cy, rx, ry, t0, 0.2).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.6).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.6).arc(cx, cy, rx, ry, 1.5 * PI, t1, 0.15).draw())
    return g.pt(cx, cy, rx, ry, t0), g.pt(cx, cy, rx, ry, t1)


@rom("C", l=0.82, r=0.6)
def _C(g):
    C, h = g.C, g.h
    cx = 300
    s, e = round_c(g, cx, cx - h, 0.2 * PI, 1.8 * PI)
    vbeak(g, s[0] - 2, s[1] - 110, s[1] + 30); vbeak(g, e[0] - 2, e[1] - 20, e[1] + 100)


@rom("O", l=0.82, r=0.82)
def _O(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    g.ring(330, C / 2, 330 - h, C / 2 + o - B / 2)


@rom("S", l=0.8, r=0.8)
def _S(g):
    C, B, o, h, S = g.C, g.B, g.o, g.h, g.S
    W = 420
    yt, yb = C + o - B / 2, -o + B / 2
    (g.P(W - 16, C * 0.78, 0.15).c(W - 30, C * 0.95, W * 0.68, yt, W * 0.5, yt, 0.5).c(W * 0.22, yt, h + 2, C * 0.92, h + 2, C * 0.75, 1)
     .c(h + 2, C * 0.5, W - h - 2, C * 0.52, W - h - 2, C * 0.26, 1).c(W - h - 2, C * 0.08, W * 0.76, yb, W * 0.5, yb, 0.5)
     .c(W * 0.24, yb, 26, C * 0.06, 12, C * 0.2, 0.15).draw())
    vbeak(g, W - 16, C * 0.68, C * 0.92); vbeak(g, 12, C * 0.08, C * 0.33)


@rom("U")
def _U(g):
    C, B, o, h, A = g.C, g.B, g.o, g.h, g.A
    x0, x1 = 0, 480
    yb, xm = -o + B / 2, (x0 + x1) / 2
    (g.P(x0, C - B / 2, 1).l(x0, C * 0.32, 1).c(x0, C * 0.08, xm - 150, yb, xm, yb, 0.5)
     .c(xm + 150, yb, x1, C * 0.08, x1, C * 0.32, 0).l(x1, C - B / 2, 0).draw())
    g.serif(x0, C, -1, "b"); g.serif(x1, C, -1, "b", B * 1.6, g.sl * 0.9)


@rom("V", l=0.45, r=0.45)
def _V(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    xl, xm, xr = 0, 275, 550
    g.P(xl, C - B / 2, 1).l(xm - A * 0.22, B / 2 - o, 0.9).draw(); g.P(xm + A * 0.1, B / 2 - o, 0).l(xr, C - B / 2, 0).draw()
    g.serif(xl, C, -1, "b"); g.serif(xr, C, -1, "b", B * 1.6)


@rom("W", l=0.45, r=0.45)
def _W(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    a, b, c, d, e = 0, 200, 395, 600, 800
    g.P(a, C - B / 2, 1).l(b - A * 0.2, B / 2 - o, 0.9).draw(); g.P(b + A * 0.1, B / 2 - o, 0).l(c, C - B / 2, 0).draw()
    g.P(c, C - B / 2, 1).l(d - A * 0.2, B / 2 - o, 0.9).draw(); g.P(d + A * 0.1, B / 2 - o, 0).l(e, C - B / 2, 0).draw()
    g.serif(a, C, -1, "b"); g.serif(c, C, -1, "b", A * 1.1, g.sl * 0.7); g.serif(e, C, -1, "b", B * 1.6)


@rom("X", l=0.55, r=0.55)
def _X(g):
    C, A, B = g.C, g.A, g.B
    xl, xr = 0, 500
    g.P(xl + 8, C - B / 2, 1).l(xr - 8, B / 2, 1).draw(); g.P(xl + 14, B / 2, 0).l(xr - 14, C - B / 2, 0).draw()
    g.serif(xl + 8, C, -1, "b"); g.serif(xr - 8, 0, 1, "b"); g.serif(xl + 14, 0, 1, "b", B * 1.6); g.serif(xr - 14, C, -1, "b", B * 1.6)


@rom("Y", l=0.45, r=0.45)
def _Y(g):
    C, A, B = g.C, g.A, g.B
    xl, xm, xr, yj = 0, 260, 520, C * 0.44
    g.P(xl, C - B / 2, 1).l(xm, yj, 1).draw(); g.P(xr, C - B / 2, 0).l(xm + A * 0.2, yj, 0).draw(); g.stem(xm, 0, yj + B)
    g.serif(xl, C, -1, "b"); g.serif(xr, C, -1, "b", B * 1.6); g.serif(xm, 0, 1, "b")


@rom("Z", l=0.7, r=0.7)
def _Z(g):
    C, A, B, S = g.C, g.A, g.B, g.S
    x0, x1 = 0, 470
    g.bar(x0, x1, C - B / 2); g.bar(x0, x1, B / 2); g.P(x1 - A * 0.5, C - B, 1).l(x0 + A * 0.5, B, 1).draw()
    vbeak(g, x0 + S * 0.7, C, C - 140); vbeak(g, x1 - S * 0.7, 0, 150)


@rom("K", r=0.5)
def _K(g):
    C, A, B, h = g.C, g.A, g.B, g.h
    x0 = 0
    g.stem(x0, 0, C); g.serif(x0, C, -1, "b"); g.serif(x0, 0, 1, "b")
    g.P(x0 + h - 4, C * 0.3, 0).l(x0 + 410, C - B / 2, 0).draw(); g.serif(x0 + 410, C, -1, "b", B * 1.6, g.sl * 0.9)
    g.P(x0 + 180, C * 0.53, 0.85).l(x0 + 452, B / 2, 1).draw(); g.serif(x0 + 452, 0, 1, "b", A * 0.95)


@rom("M")
def _M(g):
    C, A, B = g.C, g.A, g.B
    x0, xm, x1 = 0, 330, 660
    g.stem(x0, 0, C, 0); g.P(x0 + A * 0.05, C - B / 2, 1).l(xm - A * 0.2, B / 2 - g.o, 0.9).draw()
    g.P(xm + A * 0.1, B / 2 - g.o, 0).l(x1 - A * 0.3, C - B / 2, 0).draw(); g.stem(x1, 0, C)
    g.serif(x0, C, -1, "l", B * 1.6); g.serif(x0, 0, 1, "b", B * 1.6); g.serif(x1, C, -1, "r"); g.serif(x1, 0, 1, "b")


@rom("N")
def _N(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    x0, x1 = 0, 500
    g.stem(x0, 0, C, 0); g.P(x0 + A * 0.1, C - B / 2, 1).l(x1 - A * 0.15, B / 2 - o * 2, 1).draw()
    g.P(x1, C - B / 2, 0).l(x1, -o * 2, 0).draw()
    g.serif(x0, C, -1, "l", B * 1.6); g.serif(x0, 0, 1, "b", B * 1.6); g.serif(x1, C, -1, "b", B * 1.6)


@rom("A", l=0.45, r=0.45)
def _A(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    xl, xm, xr = 0, 280, 560
    g.P(xl, B / 2, 0).l(xm - A * 0.15, C + o - B / 2, 0).draw(); g.P(xm - A * 0.25, C + o - B / 2, 0.9).l(xr, B / 2, 1).draw()
    # font: the sketch's bar starts at xl + 95 and stops a few units short
    # of the hairline (the counter is open). It starts at xl + 72 here.
    g.bar(xl + 72, xr - 85, C * 0.3); g.serif(xl, 0, 1, "b", B * 1.6); g.serif(xr, 0, 1, "b")


# ---------- 0.2: refined forms ----------

@rom("g", r=0.7)
def _g(g):
    X, B, D, o, bd, h = g.X, g.B, g.D, g.o, g.bd, g.h
    cx, rx, cy, ry, yb2 = 198, 138, X * 0.655, X * 0.345 - B / 2 + o * 0.5, D - o + B / 2
    g.ring(cx, cy, rx, ry)
    e = g.pt(cx, cy, rx, ry, 0.3 * PI)
    g.P(e[0], e[1], 0).c(e[0] + 26, X + 2, cx + rx + 18, X + 16, cx + rx + 66, X + 12, 0.12).draw()
    g.ball(cx + rx + 70, X + 2, bd * 0.62)
    s = g.pt(cx, cy, rx, ry, 1.22 * PI)
    (g.P(s[0], s[1], 0.3).c(s[0] - 34, s[1] - 50, 46, 46, 140, 34, 0).l(300, 32, 0)
     .c(398, 32, 436, -12, 436, -80, 1).c(436, -178, 342, yb2, 228, yb2, 0.5)
     .c(108, yb2, 22, -188, 22, -130, 1).c(22, -82, 62, -54, 118, -46, 0).draw())


@rom("G", l=0.82, r=0.6)
def _G(g):
    C, A, B, h = g.C, g.A, g.B, g.h
    cx = 300
    rx = cx - h
    s, _ = round_c(g, cx, rx, 0.2 * PI, 1.88 * PI)
    vbeak(g, s[0] - 2, s[1] - 100, s[1] + 24)
    xr, yS = cx + rx * 0.99, C * 0.44
    g.P(xr, yS - B / 2, 1).l(xr, C * 0.12, 1).l(xr, -4, 0.35).draw()
    g.serif(xr, yS, -1, "b", A, g.sl * 0.7)


@rom("R", r=0.5)
def _R(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    yb = -o + B / 2
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "b"); dbowl(g, 0, C * 0.47, C, 405, 180)
    (g.P(170, C * 0.47 + B / 2, 0.1).c(298, C * 0.45, 352, C * 0.36, 360, C * 0.2, 1).l(363, C * 0.1, 1)
     .c(365, C * 0.02, 392, yb, 428, yb, 0.35).c(458, yb, 476, 16, 482, 44, 0).draw())


@rom("Q", l=0.82, r=0.45)
def _Q(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    cx = 325
    g.ring(cx, C / 2, cx - h, C / 2 + o - B / 2)
    (g.P(cx - 40, -o + B / 2 + 8, 0.25).c(cx + 10, -62, cx + 110, -122, cx + 235, -120, 0.8)
     .c(cx + 305, -119, cx + 350, -102, cx + 390, -82, 0).draw())


@rom("J", l=0.6)
def _J(g):
    C, B, bd, D = g.C, g.B, g.bd, g.D
    x0, yb = 230, D * 0.62
    (g.P(x0, C - B / 2, 1).l(x0, C * 0.04, 1).c(x0, yb * 0.55, x0 - 40, yb, x0 - 108, yb, 0.5)
     .c(x0 - 162, yb, x0 - 196, yb * 0.76, x0 - 204, yb * 0.5, 0.25).draw())
    g.ball(x0 - 204, yb * 0.5); g.serif(x0, C, -1, "b")


@rom("&", l=0.7, r=0.55)
def _amp(g):
    C, B, o, h = g.C, g.B, g.o, g.h
    yt, yb = C + o - B / 2, -o + B / 2
    (g.P(615, yb, 0).c(540, yb, 470, 30, 410, C * 0.18, 0.9).c(330, C * 0.36, 215, C * 0.5, 215, C * 0.73, 1)
     .c(215, C * 0.9, 255, yt, 305, yt, 0.5).c(360, yt, 392, C * 0.92, 392, C * 0.82, 1).c(392, C * 0.67, 300, C * 0.6, 215, C * 0.52, 0.3)
     .c(110, C * 0.44, h + 4, C * 0.34, h + 4, C * 0.22, 1).c(h + 4, C * 0.06, 120, yb, 232, yb, 0.5)
     .c(362, yb, 458, C * 0.18, 508, C * 0.41, 0.2).draw())
    g.bar(470, 620, C * 0.42)


# ---------- ligatures ----------

def f_top(g, x0, xe):
    AS, B, o, bd, A = g.AS, g.B, g.o, g.bd, g.A
    yt2 = AS + o - B / 2
    ye = AS - max(bd, A * 0.6) * 0.5 - 14
    return (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 66, yt2, x0 + (xe - x0) * 0.62, yt2, 0.5)
            .c(x0 + (xe - x0) * 0.88, yt2, xe, AS - 28, xe, ye, 0.25))


@rom("ﬁ")
def _fi(g):
    X, AS, B, h, bd, A = g.X, g.AS, g.B, g.h, g.bd, g.A
    x0, xi = 0, 292
    ye = AS - max(bd, A * 0.6) * 0.5 - 14
    f_top(g, x0, xi).draw(); g.ball(xi, ye); g.stem(xi, 0, X); g.bar(x0 - h - 78, xi, X - B / 2)
    g.serif(x0, 0, 1, "b", A, g.sl * 1.2); g.serif(xi, 0, 1, "b")


@rom("ﬂ")
def _fl(g):
    X, AS, B, o, h, A = g.X, g.AS, g.B, g.o, g.h, g.A
    x0, xl = 0, 292
    yt2 = AS + o - B / 2
    (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 66, yt2, x0 + 160, yt2, 0.5)
     .c(x0 + 240, yt2, xl, AS - 20, xl, AS - 110, 1).l(xl, B / 2, 1).draw())
    g.bar(x0 - h - 78, xl, X - B / 2); g.serif(x0, 0, 1, "b", A, g.sl * 1.2); g.serif(xl, 0, 1, "b")


@rom("ﬀ", r=-0.7)
def _ff(g):
    X, AS, B, o, h, bd, A = g.X, g.AS, g.B, g.o, g.h, g.bd, g.A
    x0, x2 = 0, 262
    yt2 = AS + o - B / 2
    ye = AS - max(bd, A * 0.6) * 0.5 - 14
    (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 60, yt2, x0 + 140, yt2, 0.5)
     .c(x0 + 200, yt2, x2 - h - 6, AS - 30, x2 - h * 0.4, AS - 82, 0.05).draw())
    f_top(g, x2, x2 + 232).draw(); g.ball(x2 + 232, ye); g.bar(x0 - h - 78, x2 + h + 118, X - B / 2)
    g.serif(x0, 0, 1, "b", A, g.sl * 1.2); g.serif(x2, 0, 1, "b", A, g.sl * 1.2)


# ---------- figures: lining, tabular ----------

FIG = {"adv": 520}


@rom("0", **FIG)
def _0(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    g.ring(250, C / 2, 200 - h, C / 2 + o - B / 2, 1, 2.05)


@rom("1", **FIG)
def _1(g):
    C, B, A = g.C, g.B, g.A
    x = 260
    g.stem(x, 0, C); g.P(x - g.h + 6, C - B * 0.7, 0.35).l(x - 125, C * 0.8, 0).draw(); g.serif(x, 0, 1, "b", A, g.sl * 1.35)


@rom("2", **FIG)
def _2(g):
    C, B, o, bd, S = g.C, g.B, g.o, g.bd, g.S
    yt = C + o - B / 2
    (g.P(95, C * 0.71, 0.25).c(98, C * 0.93, 170, yt, 255, yt, 0.5).c(360, yt, 420, C * 0.86, 420, C * 0.68, 1)
     .c(420, C * 0.46, 235, C * 0.3, 72, B, 0.85).draw())
    g.ball(95, C * 0.71); g.bar(52, 448, B / 2); vbeak(g, 448 - S * 0.7, 0, 125)


@rom("3", **FIG)
def _3(g):
    C, B, o, bd = g.C, g.B, g.o, g.bd
    yt, yb = C + o - B / 2, -o + B / 2
    (g.P(92, C * 0.75, 0.25).c(98, C * 0.95, 170, yt, 248, yt, 0.5).c(350, yt, 402, C * 0.88, 402, C * 0.76, 1)
     .c(402, C * 0.62, 322, C * 0.545, 205, C * 0.545, 0).draw())
    (g.P(205, C * 0.545, 0).c(352, C * 0.545, 432, C * 0.45, 432, C * 0.28, 1).c(432, C * 0.08, 342, yb, 240, yb, 0.5)
     .c(150, yb, 82, C * 0.06, 78, C * 0.21, 0.25).draw())
    g.ball(92, C * 0.75); g.ball(80, C * 0.2)


@rom("4", **FIG)
def _4(g):
    C, B, A = g.C, g.B, g.A
    x = 345
    g.P(x - A * 0.2, C - B / 2, 0).l(38, C * 0.28, 0).draw(); g.stem(x, 0, C)
    g.bar(30, 462, C * 0.27); g.serif(x, 0, 1, "b", A, g.sl * 1.1)


@rom("5", **FIG)
def _5(g):
    C, B, o = g.C, g.B, g.o
    yb = -o + B / 2
    g.bar(118, 415, C - B / 2); g.P(124, C - B / 2, 0.45).l(124, C * 0.53, 0.45).draw()
    (g.P(124, C * 0.54, 0).c(170, C * 0.62, 215, C * 0.635, 260, C * 0.635, 0.4).c(380, C * 0.635, 438, C * 0.5, 438, C * 0.32, 1)
     .c(438, C * 0.1, 345, yb, 245, yb, 0.5).c(150, yb, 82, C * 0.06, 78, C * 0.21, 0.25).draw())
    g.ball(80, C * 0.2)


def six(g, M):
    C, B, o = g.C, g.B, g.o
    yt, ry = C + o - B / 2, C * 0.32 + o - B / 2 - 6

    def T(x, y):
        return (500 - x, C - y) if M else (x, y)

    q0 = T(405, C * 0.82)
    p = g.P(q0[0], q0[1], 0.25)

    def c(a, b, c2, d, e, f, pr):
        q1, q2, q3 = T(a, b), T(c2, d), T(e, f)
        p.c(q1[0], q1[1], q2[0], q2[1], q3[0], q3[1], pr)

    c(398, C * 0.96, 330, yt, 262, yt, 0.5)
    c(140, yt, 75, C * 0.75, 75, C * 0.36, 1)
    p.draw()
    q = T(250, C * 0.32 - 6)
    g.ring(q[0], q[1], 175, ry)
    b = T(405, C * 0.82)
    g.ball(b[0], b[1])


@rom("6", **FIG)
def _6(g):
    six(g, False)


@rom("9", **FIG)
def _9(g):
    six(g, True)


@rom("7", **FIG)
def _7(g):
    C, B, A = g.C, g.B, g.A
    g.bar(48, 452, C - B / 2); vbeak(g, 48 + g.S * 0.7, C, C - 130)
    g.P(452 - A * 0.5, C - B, 0.9).c(390, C * 0.6, 240, C * 0.38, 222, B / 2, 1).draw()


@rom("8", **FIG)
def _8(g):
    C, o, B = g.C, g.o, g.B
    yj = C * 0.535
    g.ring(250, (yj + C + o - B / 2) / 2, 148, (C + o - B / 2 - yj) / 2)
    g.ring(250, (yj - o + B / 2) / 2, 176, (yj + o - B / 2) / 2)


# ---------- punctuation and delimiters ----------

def paren(g, x0, w, top, bot, dir):
    m, H = (top + bot) / 2, top - bot
    xr, B = x0 + w * dir, g.B
    (g.P(xr, top - B / 2, 0).c(xr - dir * w * 0.82, top - H * 0.2, x0, m + H * 0.26, x0, m, 1)
     .c(x0, m - H * 0.26, xr - dir * w * 0.82, bot + H * 0.2, xr, bot + B / 2, 0).draw())


def brack(g, x, top, bot, dir):
    B = g.B
    g.stem(x, bot, top, 1); g.bar(x - dir * g.h, x + dir * 130, top - B / 2); g.bar(x - dir * g.h, x + dir * 130, bot + B / 2)


@rom(" ", adv=270, empty=True)
def _space(g):
    pass


@rom(".", l=0.9, r=0.9)
def _period(g):
    g.dot(0, dotD(g) / 2, dotD(g))


def comma_at(g, y):
    d = dotD(g)
    g.ball(0, y + d / 2, d)
    g.P(d * 0.22, y + d * 0.32, 0.85).c(d * 0.3, y - d * 0.3, 0, y - d * 0.9, -d * 0.45, y - d * 1.25, 0).draw()


@rom(",", l=0.9, r=0.9)
def _comma(g):
    d = dotD(g)
    g.ball(0, d / 2, d); g.P(d * 0.22, d * 0.32, 0.85).c(d * 0.3, -d * 0.3, 0, -d * 0.9, -d * 0.45, -d * 1.25, 0).draw()


@rom(":", l=0.9, r=0.9)
def _colon(g):
    d = dotD(g)
    g.dot(0, d / 2, d); g.dot(0, g.X - d / 2, d)


@rom(";", l=0.9, r=0.9)
def _semicolon(g):
    d = dotD(g)
    g.dot(0, g.X - d / 2, d); g.ball(0, d / 2, d)
    g.P(d * 0.22, d * 0.32, 0.85).c(d * 0.3, -d * 0.3, 0, -d * 0.9, -d * 0.45, -d * 1.25, 0).draw()


@rom("!", l=0.9, r=0.9)
def _exclam(g):
    d, C, B = dotD(g), g.C, g.B
    g.P(0, C - B / 2, 1).l(0, C * 0.6, 0.85).l(0, d + 70, 0.15).draw(); g.dot(0, d / 2, d)


@rom("?", l=0.8, r=0.8)
def _question(g):
    d, C, B, o = dotD(g), g.C, g.B, g.o
    yt = C + o - B / 2
    (g.P(48, C * 0.72, 0.25).c(52, C * 0.94, 120, yt, 190, yt, 0.5).c(280, yt, 325, C * 0.86, 325, C * 0.73, 1)
     .c(325, C * 0.55, 190, C * 0.5, 190, C * 0.33, 0.6).l(190, d + 80, 0.2).draw())
    g.ball(48, C * 0.72); g.dot(190, d / 2, d)


@rom("'", l=0.9, r=0.9)
def _quotesingle(g):
    C = g.C
    g.P(0, C - g.B / 2, 1).l(0, C * 0.66, 0.15).draw()


@rom("’", l=0.9, r=0.9)
def _quoteright(g):
    d, C = dotD(g), g.C
    g.ball(0, C - d / 2, d)
    g.P(d * 0.22, C - d * 0.68, 0.85).c(d * 0.3, C - d * 1.3, 0, C - d * 1.9, -d * 0.45, C - d * 2.25, 0).draw()


@rom("-", l=0.8, r=0.8)
def _hyphen(g):
    X = g.X
    g.P(0, X * 0.56, 0).l(170, X * 0.56, 0).draw({"b": g.A * 0.5, "a": g.A * 0.5, "ne": 5})


@rom("–", l=0.4, r=0.4)
def _endash(g):
    X = g.X
    g.P(0, X * 0.56, 0).l(500, X * 0.56, 0).draw({"b": g.B * 1.5, "a": g.B * 1.5, "ne": 5})


@rom("—", l=0.2, r=0.2)
def _emdash(g):
    X = g.X
    g.P(0, X * 0.56, 0).l(940, X * 0.56, 0).draw({"b": g.B * 1.5, "a": g.B * 1.5, "ne": 5})


@rom("/", l=0.5, r=0.5)
def _slash(g):
    C = g.C
    g.P(330, C + 60, 0.55).l(0, -120, 0.55).draw()


@rom("(", l=0.9, r=0.6)
def _parenleft(g):
    paren(g, 0, 150, 770, -250, 1)


@rom(")", l=0.6, r=0.9)
def _parenright(g):
    paren(g, 150, 150, 770, -250, -1)


@rom("[", l=0.9, r=0.6)
def _bracketleft(g):
    brack(g, 0, 770, -250, 1)


@rom("]", l=0.6, r=0.9)
def _bracketright(g):
    brack(g, 130, 770, -250, -1)


# =====================================================================
# GREEK. One continuous pen line where the hand would make one.
# =====================================================================

@rom("α", l=0.8, r=0.5)
def _alpha(g):
    X, yt, yb, h = g.X, g.yt, g.yb, g.h
    (g.P(448, X + 8, 0.1).c(425, X * 0.58, 335, yb, 215, yb, 0.6).c(92, yb, h + 2, X * 0.24, h + 2, X * 0.5, 1)
     .c(h + 2, X * 0.78, 100, yt, 212, yt, 0.6).c(318, yt, 392, X * 0.42, 478, 4, 0.05).draw())


@rom("β", r=0.8)
def _beta(g):
    X, AS, D, B, o, h = g.X, g.AS, g.D, g.B, g.o, g.h
    x0 = 0
    yt2, yb = AS + o - B / 2, -o + B / 2
    (g.P(x0, D, 0.7).l(x0, D + 50, 1).l(x0, AS * 0.66, 1).c(x0, AS - 12, 95, yt2, 190, yt2, 0.5).c(290, yt2, 345, AS * 0.9, 345, AS * 0.79, 1)
     .c(345, X * 1.18, 268, X + 16, 165, X + 16, 0).c(335, X + 16, 412, X * 0.78, 412, X * 0.42, 1)
     .c(412, X * 0.1, 322, yb, 215, yb, 0.5).c(118, yb, x0 + 30, X * 0.08, x0 + h * 0.3, X * 0.22, 0).draw())


@rom("γ", l=0.6, r=0.5)
def _gamma(g):
    X, D, B = g.X, g.D, g.B
    (g.P(0, X * 0.72, 0.15).c(10, X + 4, 92, X + 6, 128, X * 0.76, 0.9).l(232, -30, 1).c(262, -95, 262, D + 70, 226, D + 70, 0.45)
     .c(190, D + 70, 190, -95, 226, -30, 0.15).draw())
    g.P(450, X - B / 2, 0).l(232, -30, 0).draw()


@rom("δ", l=0.82, r=0.8)
def _delta(g):
    X, AS, B, o, h, bd = g.X, g.AS, g.B, g.o, g.h, g.bd
    cx, cy, rx, ry, yt2 = 225, X * 0.46, 225 - h, X * 0.46 + o - B / 2, AS + o - B / 2
    g.ring(cx, cy, rx, ry)
    e = g.pt(cx, cy, rx, ry, 0.36 * PI)
    (g.P(372, AS - bd * 0.45 - 10, 0.2).c(366, AS + 2, 300, yt2, 232, yt2, 0.45).c(150, yt2, 108, AS * 0.94, 108, AS * 0.86, 0.8)
     .c(108, AS * 0.72, e[0] - 40, X * 1.04, e[0], e[1], 1).draw())
    g.ball(372, AS - bd * 0.45 - 10, bd * 0.9)


@rom("ε", l=0.82, r=0.7)
def _epsilon(g):
    X, yt, yb, h, bd = g.X, g.yt, g.yb, g.h, g.bd
    (g.P(352, X * 0.79, 0.2).c(345, X * 0.97, 282, yt, 218, yt, 0.4).c(122, yt, h + 28, X * 0.9, h + 28, X * 0.76, 1)
     .c(h + 28, X * 0.6, 128, X * 0.53, 232, X * 0.53, 0).draw())
    (g.P(232, X * 0.53, 0).c(108, X * 0.53, h, X * 0.42, h, X * 0.25, 1).c(h, X * 0.06, 108, yb, 218, yb, 0.5)
     .c(318, yb, 366, X * 0.06, 385, X * 0.17, 0).draw())
    g.ball(352, X * 0.79, bd * 0.85)


@rom("θ", l=0.82, r=0.82)
def _theta(g):
    AS, o, B, h = g.AS, g.o, g.B, g.h
    cy = AS / 2 - o
    g.ring(215, cy, 215 - h, AS / 2 + o - B / 2, 1, 2.0); g.bar(h * 0.6, 430 - h * 0.6, cy)


@rom("λ", l=0.6, r=0.55)
def _lambda(g):
    X, AS, B = g.X, g.AS, g.B
    yb = -g.o + B / 2
    (g.P(12, AS - 38, 0.1).c(38, AS + 4, 95, AS, 122, AS - 72, 0.9).l(390, 62, 1)
     .c(400, 22, 422, yb, 452, yb, 0.3).draw())
    g.P(290, X * 0.62, 0).l(12, B / 2, 0.25).draw()


@rom("μ", r=0.55)
def _mu(g):
    X, D, B, yb, h = g.X, g.D, g.B, g.yb, g.h
    x0, x1 = 0, 330
    g.P(x0, X - B / 2, 0.5).l(x0, X - 60, 1).l(x0, D + 40, 1).l(x0, D + B / 2, 0.7).draw()
    (g.P(x0 + h * 0.3, X * 0.34, 0).c(x0 + 28, X * 0.06, 100, yb, 165, yb, 0.55)
     .c(250, yb, x1 - 30, X * 0.12, x1 - h * 0.3, X * 0.38, 0).draw())
    (g.P(x1, X - B / 2, 0.5).l(x1, X - 60, 1).l(x1, 70, 1).c(x1, 22, x1 + 22, yb, x1 + 60, yb, 0.3)
     .c(x1 + 80, yb, x1 + 93, 18, x1 + 96, 42, 0).draw())


@rom("π", l=0.5, r=0.5)
def _pi(g):
    X, A, B, o = g.X, g.A, g.B, g.o
    yb, bb = -o + B / 2, A * 0.36
    yb2 = X - bb / 2
    g.P(-12, X * 0.76, 0.4).c(0, X * 0.92, 40, yb2, 110, yb2, 0.6).l(540, yb2, 0.3).draw({"b": bb})
    g.P(165, X - bb, 0.8).c(165, X * 0.45, 138, X * 0.18, 72, 26, 0.35).draw()
    g.P(398, X - bb, 1).l(398, 78, 1).c(398, 25, 418, yb, 452, yb, 0.3).c(478, yb, 492, 20, 495, 46, 0).draw()


@rom("ρ", l=0.8, r=0.82)
def _rho(g):
    X, D, o, B, h = g.X, g.D, g.o, g.B, g.h
    cx, rx, cy, ry = 225, 225 - h, X / 2, X / 2 + o - B / 2
    g.ring(cx, cy, rx, ry); g.P(h, X * 0.48, 1).l(h, D + 40, 1).l(h, D + B / 2, 0.7).draw()


@rom("σ", l=0.82, r=0.5)
def _sigma(g):
    X, o, B, h = g.X, g.o, g.B, g.h
    cx, cy, rx, ry, bb = 212, X * 0.47, 212 - h, X * 0.47 + o - B / 2, B * 2.1
    g.ring(cx, cy, rx, ry)
    g.P(cx, cy + ry + B / 2 - bb / 2, 0).l(470, cy + ry + B / 2 - bb / 2, 0).draw({"b": bb, "a": bb, "ne": 3})


@rom("φ", l=0.82, r=0.82)
def _phi(g):
    X, AS, D, o, B = g.X, g.AS, g.D, g.o, g.B
    cx = 245
    g.ring(cx, X / 2, 245 - g.h, X / 2 + o - B / 2, 1, 2.1)
    g.P(cx, D, 0.7).l(cx, D + 45, 1).l(cx, AS - 80, 1).l(cx, AS - 30, 0.7).draw()


@rom("ψ", l=0.6, r=0.6)
def _psi(g):
    X, AS, D, B = g.X, g.AS, g.D, g.B
    cx = 250
    g.P(cx, D, 0.7).l(cx, D + 45, 1).l(cx, AS - 80, 1).l(cx, AS - 30, 0.7).draw()
    (g.P(18, X, 0.3).l(18, X - 50, 1).l(18, X * 0.55, 1).c(18, X * 0.12, 110, 40, cx, 40, 0.4)
     .c(390, 40, 482, X * 0.12, 482, X * 0.55, 1).l(482, X - 50, 1).l(482, X, 0.3).draw())


@rom("ω", l=0.75, r=0.75)
def _omega(g):
    X, yb, h = g.X, g.yb, g.h
    W = 600
    (g.P(118, X + 4, 0.15).c(48, X * 0.82, h, X * 0.6, h, X * 0.36, 1).c(h, X * 0.08, 92, yb, 165, yb, 0.5)
     .c(238, yb, 282, X * 0.15, 300, X * 0.52, 0.15)
     .c(318, X * 0.15, 362, yb, 435, yb, 0.5).c(508, yb, W - h, X * 0.08, W - h, X * 0.36, 1)
     .c(W - h, X * 0.6, W - 48, X * 0.82, W - 118, X + 4, 0.15).draw())


@rom("Γ", r=0.5)
def _Gamma(g):
    C, B, h = g.C, g.B, g.h
    g.stem(0, 0, C); g.serif(0, C, -1, "l"); g.serif(0, 0, 1, "b"); g.bar(-h, 395, C - B / 2); vbeak(g, 395 - g.S * 0.7, C, C - 128)


@rom("Δ", l=0.45, r=0.45)
def _Delta(g):
    C, A, B, o = g.C, g.A, g.B, g.o
    xl, xm, xr = 0, 290, 580
    g.P(xl + 20, B, 0).l(xm - A * 0.15, C + o - B / 2, 0).draw(); g.P(xm - A * 0.25, C + o - B / 2, 0.9).l(xr - A * 0.35, B, 1).draw()
    g.bar(xl, xr, B / 2)


@rom("Σ", l=0.6, r=0.6)
def _Sigma(g):
    C, A, B, S = g.C, g.A, g.B, g.S
    W = 480
    g.bar(0, W, C - B / 2); vbeak(g, W - S * 0.7, C, C - 130); g.P(30, C - B, 1).l(255, C * 0.5, 1).draw()
    g.P(255, C * 0.5, 0).l(25, B, 0).draw()
    g.bar(0, W + 20, B / 2); vbeak(g, W + 20 - S * 0.7, 0, 140)


@rom("Ω", l=0.6, r=0.6)
def _Omega(g):
    C, B, A, o = g.C, g.B, g.A, g.o
    cx, cy, rx, ry, t0, t1 = 330, C * 0.56, 330 - g.h - 30, C * 0.44 + o - B / 2, 1.37 * PI, -0.37 * PI
    s, e = g.pt(cx, cy, rx, ry, t0), g.pt(cx, cy, rx, ry, t1)
    (g.P(s[0] + 40, B, 0.5).c(s[0] + 15, s[1] * 0.5, s[0], s[1], s[0], s[1], 0.7).arc(cx, cy, rx, ry, t0, PI, 1)
     .arc(cx, cy, rx, ry, PI, 0.5 * PI, 0.6).arc(cx, cy, rx, ry, 0.5 * PI, 0, 1).arc(cx, cy, rx, ry, 0, t1, 0.7)
     .c(e[0], e[1], e[0] - 15, e[1] * 0.5, e[0] - 40, B, 0.5).draw())
    g.bar(s[0] - 130, s[0] + 60, B / 2); g.bar(e[0] - 60, e[0] + 130, B / 2)


# =====================================================================
# MATHS. Operators use the rule pen: a square nib, R thick.
# The math axis is at 250; big operators are centred on it.
# =====================================================================

AX = 250


def Rw(g):
    return max(g.B * 1.35, g.A * 0.44)


def rule(g, x0, y0, x1, y1, ne=None):
    r = Rw(g)
    g.P(x0, y0, 0).l(x1, y1, 0).draw({"a": r, "b": r, "ne": ne or 8, "role": "rule"})


OPW = {"l": 1.4, "r": 1.4, "upright": True}


@rom("+", **OPW)
def _plus(g):
    rule(g, 0, AX, 560, AX); rule(g, 280, AX - 280, 280, AX + 280)


@rom("−", **OPW)
def _minus(g):
    rule(g, 0, AX, 560, AX)


@rom("=", **OPW)
def _equal(g):
    rule(g, 0, AX + 108, 560, AX + 108); rule(g, 0, AX - 108, 560, AX - 108)


@rom("×", **OPW)
def _multiply(g):
    d = 200
    rule(g, 280 - d, AX - d, 280 + d, AX + d, 3); rule(g, 280 - d, AX + d, 280 + d, AX - d, 3)


@rom("<", **OPW)
def _less(g):
    r = Rw(g)
    g.P(500, AX + 250, 0).l(0, AX, 0).l(500, AX - 250, 0).draw({"a": r, "b": r, "ne": 2.6, "role": "rule"})


@rom(">", **OPW)
def _greater(g):
    r = Rw(g)
    g.P(0, AX + 250, 0).l(500, AX, 0).l(0, AX - 250, 0).draw({"a": r, "b": r, "ne": 2.6, "role": "rule"})


@rom("·", l=1.2, r=1.2, upright=True)
def _periodcentered(g):
    g.dot(0, AX, g.A * 0.95)


@rom("∑", l=0.6, r=0.6, bigop=True, upright=True)
def _summation(g):
    A, B, S = g.A, g.B, g.S
    top, bot, W = AX + 520, AX - 520, 820
    g.bar(0, W, top - B / 2); vbeak(g, W - S * 0.7, top, top - 160); g.P(40, top - B, 1).l(430, AX, 1).draw()
    g.P(430, AX, 0).l(30, bot + B, 0).draw()
    g.bar(0, W + 30, bot + B / 2); vbeak(g, W + 30 - S * 0.7, bot, bot + 170)


@rom("∫", l=0.6, r=0.6, bigop=True, slant=0.2, yc=AX)
def _integral(g):
    bd, A = g.bd, g.A
    d = max(bd, A * 0.9) * 0.92
    (g.P(352, AX + 600, 0.25).c(352, AX + 655, 315, AX + 680, 280, AX + 680, 0.35).c(232, AX + 680, 212, AX + 630, 205, AX + 520, 1)
     .l(150, AX - 520, 1).c(143, AX - 630, 123, AX - 680, 75, AX - 680, 0.35).c(40, AX - 680, 3, AX - 655, 3, AX - 600, 0.25).draw())
    g.ball(352, AX + 600, d); g.ball(3, AX - 600, d)


@rom("∞", l=0.8, r=0.8)
def _infinity(g):
    a, b = 360, 150
    cx, cy = a, AX
    p = g.P(cx, cy, 1)
    for i in range(1, 201):
        t = i / 200 * TAU
        p.l(cx + a * 0.9 * math.sin(t) / (1 + 0.18 * math.cos(2 * t)),
            cy + b * math.sin(2 * t) / (1 + 0.18 * math.cos(2 * t)) * 1.05, 1)
    p.draw()


@rom("∂", l=0.8, r=0.8)
def _partialdiff(g):
    yb, bd, X, B, o = g.yb, g.bd, g.X, g.B, g.o
    yt = 700 + o - B / 2
    (g.P(112, 600, 0.2).c(112, 672, 180, yt, 252, yt, 0.5).c(352, yt, 392, 600, 392, 420, 1).l(392, 260, 1)
     .c(392, 80, 305, yb, 212, yb, 0.6).c(112, yb, 62, 90, 62, 195, 1).c(62, 312, 145, 382, 236, 382, 0.5)
     .c(305, 382, 362, 345, 392, 288, 0.1).draw())
    g.ball(112, 600, bd * 0.9)


@rom("∇", l=0.5, r=0.5, upright=True)
def _nabla(g):
    C, A, B = g.C, g.A, g.B
    W = 600
    g.bar(0, W, C - B / 2); g.P(30, C - B, 1).l(W / 2 - A * 0.1, -g.o + B / 2, 0.9).draw()
    g.P(W / 2 + A * 0.2, -g.o + B / 2, 0).l(W - 25, C - B, 0).draw()


def radical(g, top, bot, bar):
    A, B = g.A, g.B
    r = Rw(g)
    mid, H = bot + (top - bot) * 0.42, top - bot
    xb = 165 + H * 0.05
    xt = xb + H * 0.26
    g.P(0, mid - 12, 0).l(62, mid + 30, 0.2).draw({"a": r * 0.9, "b": r * 0.9, "ne": 3})
    g.P(62, mid + 30, 0.9).l(xb, bot + B / 2, 1).draw()
    g.P(xb, bot + B / 2, 0).l(xt, top - r / 2, 0).draw()
    rule(g, xt, top - r / 2, xt + bar, top - r / 2)
    return xt


@rom("√", l=0.5, r=0.2, upright=True)
def _radical(g):
    return radical(g, 770, -240, 40)


@rom("′", l=0.4, r=0.4)
def _minute(g):
    g.P(150, 720, 1).l(40, 440, 0.1).draw()


# =====================================================================
# ITALIC. A true cursive: entry hooks, exit tails, single-storey a and
# g, a descending f, round-bottomed v and w. Drawn upright; the engine
# slants the centre-lines but not the pen.
# =====================================================================

def entry(g, x, top):
    B = g.B
    return g.P(x - 72, top - 88, 0).c(x - 50, top - 36, x - 26, top - B / 2, x - 6, top - B / 2, 0.4).c(x, top - B / 2, x, top - 34, x, top - 64, 1)


def exit_t(p, g, x):
    yb = g.yb
    return p.l(x, 112, 1).c(x, 34, x + 22, yb, x + 62, yb, 0.4).c(x + 96, yb, x + 118, 30, x + 130, 76, 0)


def iarch(g, x0, x1, top):
    B, h = g.B, g.h
    yt = top + g.o - B / 2
    xm = (x0 + x1) / 2 + 20
    return (g.P(x0 + h * 0.3, top * 0.46, 0).c(x0 + 30, top * 0.84, xm - (xm - x0) * 0.6, yt, xm, yt, 0.5)
            .c(xm + (x1 - xm) * 0.65, yt, x1, top * 0.86, x1, top * 0.6, 1))


def ibowl(g, xr):
    """The a, d, g, q bowl: open at the right, joins the stem."""
    X, yt, yb, h = g.X, g.yt, g.yb, g.h
    (g.P(xr - h * 0.2, X * 0.8, 0.1).c(xr - 30, X + 4, xr - 80, yt, xr - 122, yt, 0.4).c(xr - 232, yt, h, X * 0.64, h, X * 0.36, 1)
     .c(h, X * 0.1, 62, yb, 128, yb, 0.5).c(200, yb, xr - 30, X * 0.25, xr - h * 0.25, X * 0.47, 0).draw())


@ita("i", l=0.7, r=0.5)
def _ii(g):
    X, AS = g.X, g.AS
    exit_t(entry(g, 0, X), g, 0).draw(); g.dot(18, X + (AS - X) * 0.66, dotD(g))


@ita("l", l=0.7, r=0.5)
def _il(g):
    exit_t(entry(g, 0, g.AS), g, 0).draw()


@ita("j", l=0.5, r=0.6)
def _ij(g):
    X, AS, D, B, bd, o = g.X, g.AS, g.D, g.B, g.bd, g.o
    yb = D - o + B / 2
    (entry(g, 0, X).l(0, D + 150, 1).c(0, D + 50, -40, yb, -105, yb, 0.5)
     .c(-150, yb, -182, D + 22, -190, D + bd * 0.5 + 8, 0.25).draw())
    g.ball(-190, D + bd * 0.5 + 8); g.dot(18, X + (AS - X) * 0.66, dotD(g))


@ita("n", l=0.7, r=0.5)
def _in(g):
    X, B = g.X, g.B
    entry(g, 0, X).l(0, B / 2, 1).draw(); exit_t(iarch(g, 0, 300, X), g, 300).draw()


@ita("m", l=0.7, r=0.5)
def _im(g):
    X, B = g.X, g.B
    entry(g, 0, X).l(0, B / 2, 1).draw(); iarch(g, 0, 270, X).l(270, B / 2, 1).draw(); exit_t(iarch(g, 270, 540, X), g, 540).draw()


@ita("h", l=0.7, r=0.5)
def _ih(g):
    X, AS, B = g.X, g.AS, g.B
    entry(g, 0, AS).l(0, B / 2, 1).draw(); exit_t(iarch(g, 0, 300, X), g, 300).draw()


@ita("u", l=0.7, r=0.5)
def _iu(g):
    X, B, yb, h = g.X, g.B, g.yb, g.h
    x1 = 300
    (entry(g, 0, X).l(0, X * 0.34, 1).c(0, X * 0.08, 60, yb, 128, yb, 0.5)
     .c(200, yb, x1 - 28, X * 0.22, x1 - h * 0.25, X * 0.48, 0).draw())
    exit_t(g.P(x1, X, 0.5).l(x1, X - 44, 1), g, x1).draw()


@ita("a", l=0.8, r=0.5)
def _ia(g):
    X = g.X
    x1 = 300
    ibowl(g, x1); exit_t(g.P(x1, X, 0.5).l(x1, X - 44, 1), g, x1).draw()


@ita("d", l=0.8, r=0.5)
def _id(g):
    AS = g.AS
    x1 = 300
    ibowl(g, x1); exit_t(g.P(x1, AS, 0.5).l(x1, AS - 44, 1), g, x1).draw()


@ita("q", l=0.8, r=0.6)
def _iq(g):
    X, D = g.X, g.D
    x1 = 300
    ibowl(g, x1); g.P(x1, X, 0.5).l(x1, X - 44, 1).l(x1, D + g.B / 2, 1).draw(); g.serif(x1, D, 1, "b")


@ita("g", l=0.8, r=0.6)
def _ig(g):
    X, D, B, bd, o = g.X, g.D, g.B, g.bd, g.o
    x1, yb = 300, D - o + B / 2
    ibowl(g, x1)
    (g.P(x1, X, 0.5).l(x1, X - 44, 1).l(x1, D + 160, 1).c(x1, D + 55, x1 - 48, yb, x1 - 130, yb, 0.5)
     .c(x1 - 205, yb, x1 - 245, D + 40, x1 - 250, D + bd * 0.5 + 10, 0.25).draw())
    g.ball(x1 - 250, D + bd * 0.5 + 10)


@ita("e", l=0.8, r=0.5)
def _ie(g):
    X, yt, yb, h = g.X, g.yt, g.yb, g.h
    (g.P(h * 0.5, X * 0.36, 0).c(110, X * 0.4, 268, X * 0.52, 268, X * 0.77, 0.35).c(268, X * 0.95, 218, yt, 160, yt, 0.4)
     .c(62, yt, h, X * 0.62, h, X * 0.36, 1).c(h, X * 0.1, 80, yb, 150, yb, 0.5).c(212, yb, 252, 30, 278, 82, 0).draw())


@ita("c", l=0.8, r=0.5)
def _ic(g):
    X, yt, yb, h, bd = g.X, g.yt, g.yb, g.h, g.bd
    (g.P(258, X * 0.74, 0.2).c(255, X * 0.95, 212, yt, 165, yt, 0.4).c(62, yt, h, X * 0.62, h, X * 0.36, 1)
     .c(h, X * 0.1, 80, yb, 150, yb, 0.5).c(212, yb, 252, 30, 278, 82, 0).draw())
    g.ball(258, X * 0.74, bd * 0.8)


@ita("o", l=0.8, r=0.8)
def _io(g):
    X, yt, yb, h = g.X, g.yt, g.yb, g.h
    cx, rx = 200, 200 - h
    g.ring(cx, X / 2, rx, X / 2 + g.o - g.B / 2)


def it_f(g, x, xd):
    X, AS, D, B, bd, o, A = g.X, g.AS, g.D, g.B, g.bd, g.o, g.A
    yt2, yb, ye = AS + o - B / 2, D - o + B / 2, AS - max(bd, A * 0.6) * 0.5 - 12
    (g.P(xd, ye, 0.25).c(xd, AS - 4, x + (xd - x) * 0.7, yt2, x + 70, yt2, 0.4).c(x + 20, yt2, x, AS - 60, x, AS - 160, 1)
     .l(x, D + 150, 1).c(x, D + 55, x - 35, yb, x - 90, yb, 0.4).c(x - 140, yb, x - 170, D + 40, x - 172, D + bd * 0.45 + 12, 0.25).draw())
    g.ball(xd, ye); g.ball(x - 172, D + bd * 0.45 + 12, bd * 0.85)


@ita("f", l=0.3, r=0.2)
def _if(g):
    X, B = g.X, g.B
    x = 190
    it_f(g, x, x + 150); g.bar(x - 130, x + 125, X - B / 2)


@ita("ﬁ", l=0.3, r=0.5)
def _ifi(g):
    X, B = g.X, g.B
    x = 190
    xi = x + 250
    it_f(g, x, xi + 12); exit_t(entry(g, xi, X), g, xi).draw(); g.bar(x - 130, xi - 40, X - B / 2)


@ita("ﬂ", l=0.3, r=0.5)
def _ifl(g):
    X, AS, B = g.X, g.AS, g.B
    x = 190
    xl = x + 262
    it_f(g, x, x + 150); exit_t(entry(g, xl, AS), g, xl).draw(); g.bar(x - 130, xl - 30, X - B / 2)


@ita("ﬀ", l=0.3, r=0.2)
def _iff(g):
    X, B = g.X, g.B
    x = 190
    x2 = x + 215
    it_f(g, x, x + 128); it_f(g, x2, x2 + 150); g.bar(x - 130, x2 + 125, X - B / 2)


# italic capitals: their own forms (curled feet, entry hooks, drops)

def ifoot(g, x):
    B, o = g.B, g.o
    yb = -o + B / 2
    return g.P(x - 62, 52, 0).c(x - 50, 10, x - 22, yb, x + 4, 20, 0.05)


def iexit(p, g, x):
    B, o = g.B, g.o
    yb = -o + B / 2
    return p.l(x, 78, 1).c(x, 24, x + 20, yb, x + 56, yb, 0.35).c(x + 84, yb, x + 100, 18, x + 104, 44, 0)


@ita("A", l=0.45, r=0.4)
def _iA(g):
    C, B, o, A = g.C, g.B, g.o, g.A
    ifoot(g, 0).l(300, C + o - B / 2, 0).draw()
    # font: the sketch's bar starts at x 105, a few units short of the
    # hairline at Display sizes (open counter). It starts at 84 here.
    iexit(g.P(300 - A * 0.2, C + o - B / 2, 0.85).l(408, 120, 1), g, 412).draw(); g.bar(84, 400, C * 0.31)


@ita("V", l=0.45, r=0.45)
def _iV(g):
    C, B, A, bd = g.C, g.B, g.A, g.bd
    g.P(-58, C - 82, 0).c(-44, C - 20, -4, C - B / 2, 26, C - B / 2, 0.4).c(52, C - B / 2, 60, C - 40, 62, C - 82, 1).l(255, 24, 1).draw()
    g.P(255 + A * 0.1, 24, 0).l(452, C - 130, 0.05).c(462, C - 70, 474, C - 34, 500, C - 24, 0.3).draw(); g.ball(506, C - 28, bd * 0.8)


@ita("W", l=0.45, r=0.45)
def _iW(g):
    C, B, A, bd = g.C, g.B, g.A, g.bd
    g.P(-58, C - 82, 0).c(-44, C - 20, -4, C - B / 2, 26, C - B / 2, 0.4).c(52, C - B / 2, 60, C - 40, 62, C - 82, 1).l(220, 24, 1).draw()
    g.P(220 + A * 0.1, 24, 0).l(390, C - B / 2, 0).draw(); g.P(390, C - B / 2, 0.8).l(560, 24, 1).draw()
    g.P(560 + A * 0.1, 24, 0).l(732, C - 130, 0.05).c(742, C - 70, 754, C - 34, 780, C - 24, 0.3).draw(); g.ball(786, C - 28, bd * 0.8)


@ita("M", l=0.5, r=0.4)
def _iM(g):
    C, B, A = g.C, g.B, g.A
    ifoot(g, 10).l(70, C - B / 2, 0).draw(); g.P(70, C - B / 2, 1).l(320, 12, 0.95).draw(); g.P(320 + A * 0.1, 12, 0).l(600, C - B / 2, 0).draw()
    iexit(g.P(600, C - B / 2, 1), g, 600).draw(); g.serif(600, C, -1, "r", A, g.sl * 0.6)


@ita("N", l=0.45, r=0.45)
def _iN(g):
    C, B, A, bd = g.C, g.B, g.A, g.bd
    ifoot(g, 10).l(40, C - B / 2, 0).draw(); g.P(40, C - B / 2, 1).l(470, 12, 1).draw()
    g.P(470, 12, 0).l(476, C - 110, 0).c(478, C - 50, 500, C - B / 2, 532, C - B / 2, 0.25).draw(); g.ball(540, C - 34, bd * 0.75)


@ita("O", l=0.8, r=0.8)
def _iO(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    g.ring(290, C / 2, 290 - h, C / 2 + o - B / 2, 1, 2.0)


def round_ci(g, cx, t1, end_pr):
    C, o, B, h, bd = g.C, g.o, g.B, g.h, g.bd
    rx, cy, ry, t0 = cx - h, C / 2, C / 2 + o - B / 2, 0.2 * PI
    s = g.pt(cx, cy, rx, ry, t0, 2.0)
    (g.E(cx, cy, rx, ry, t0, 0.25, 2.0).arc(cx, cy, rx, ry, t0, 0.5 * PI, 0.6, 2.0).arc(cx, cy, rx, ry, 0.5 * PI, PI, 1, 2.0)
     .arc(cx, cy, rx, ry, PI, 1.5 * PI, 0.6, 2.0).arc(cx, cy, rx, ry, 1.5 * PI, t1, end_pr, 2.0).draw())
    g.ball(s[0], s[1])
    return cx, rx


@ita("C", l=0.8, r=0.55)
def _iC(g):
    round_ci(g, 280, 1.84 * PI, 0)


@ita("G", l=0.8, r=0.5)
def _iG(g):
    C, B = g.C, g.B
    cx, rx = round_ci(g, 285, 1.9 * PI, 0.15)
    xr = cx + rx * 0.99
    iexit(g.P(xr, C * 0.42, 0.5).l(xr, C * 0.38, 1), g, xr).draw()


@ita("Q", l=0.8, r=0.45)
def _iQ(g):
    C, o, B, h = g.C, g.o, g.B, g.h
    g.ring(290, C / 2, 290 - h, C / 2 + o - B / 2, 1, 2.0)
    g.P(200, -4, 0.2).c(250, -70, 360, -112, 470, -100, 0.75).c(530, -94, 566, -74, 596, -52, 0).draw()


@ita("r", l=0.7, r=0.4)
def _ir(g):
    X, B, yt, bd, h = g.X, g.B, g.yt, g.bd, g.h
    ye = X - bd * 0.45 - 6
    entry(g, 0, X).l(0, B / 2, 1).draw()
    g.P(h * 0.3, X * 0.48, 0).c(32, X * 0.84, 110, yt, 170, yt, 0.4).c(212, yt, 236, X * 0.95, 236, ye, 0.2).draw(); g.ball(232, ye, bd * 0.9)


@ita("t", l=0.7, r=0.4)
def _it(g):
    X, B = g.X, g.B
    exit_t(g.P(0, X + 112, 0.45).l(0, X * 0.8, 1), g, 0).draw(); g.bar(-g.h - 62, g.h + 110, X - B / 2)


@ita("v", l=0.7, r=0.5)
def _iv(g):
    X, yb, bd = g.X, g.yb, g.bd
    x1 = 310
    (entry(g, 0, X).l(0, X * 0.4, 1).c(0, X * 0.1, 60, yb, 140, yb, 0.5).c(232, yb, x1, X * 0.32, x1, X * 0.62, 0.35)
     .c(x1, X * 0.8, x1 - 14, X * 0.86, x1 - 38, X * 0.9, 0.2).draw())
    g.ball(x1 - 36, X * 0.86, bd * 0.8)


@ita("w", l=0.7, r=0.5)
def _iw(g):
    X, yb, bd, B = g.X, g.yb, g.bd, g.B
    m, x1 = 250, 520
    (entry(g, 0, X).l(0, X * 0.4, 1).c(0, X * 0.1, 52, yb, 118, yb, 0.5).c(190, yb, m - 16, X * 0.22, m - g.h * 0.25, X * 0.5, 0).draw())
    (g.P(m, X, 0.5).l(m, X - 44, 1).l(m, X * 0.4, 1).c(m, X * 0.1, m + 52, yb, m + 120, yb, 0.5)
     .c(m + 212, yb, x1, X * 0.32, x1, X * 0.62, 0.35).c(x1, X * 0.8, x1 - 14, X * 0.86, x1 - 38, X * 0.9, 0.2).draw())
    g.ball(x1 - 36, X * 0.86, bd * 0.8)


@ita("y", l=0.7, r=0.6)
def _iy(g):
    X, D, B, yb, bd, o, h = g.X, g.D, g.B, g.yb, g.bd, g.o, g.h
    x1, yd = 300, D - o + B / 2
    (entry(g, 0, X).l(0, X * 0.34, 1).c(0, X * 0.08, 60, yb, 128, yb, 0.5)
     .c(200, yb, x1 - 28, X * 0.22, x1 - h * 0.25, X * 0.48, 0).draw())
    (g.P(x1, X, 0.5).l(x1, X - 44, 1).l(x1, D + 160, 1).c(x1, D + 55, x1 - 48, yd, x1 - 130, yd, 0.5)
     .c(x1 - 205, yd, x1 - 245, D + 40, x1 - 250, D + bd * 0.5 + 10, 0.25).draw())
    g.ball(x1 - 250, D + bd * 0.5 + 10)


@ita("p", l=0.7, r=0.8)
def _ip(g):
    X, D = g.X, g.D
    entry(g, 0, X).l(0, D + g.B / 2, 1).draw(); g.serif(0, D, 1, "b")
    (iarch(g, 0, 330, X).l(330, X * 0.4, 1).c(330, X * 0.1, 270, g.yb, 190, g.yb, 0.5)
     .c(120, g.yb, 40, X * 0.08, g.h * 0.3, X * 0.25, 0).draw())


@ita("b", l=0.7, r=0.8)
def _ib(g):
    X, AS = g.X, g.AS
    (entry(g, 0, AS).l(0, X * 0.3, 1).c(0, X * 0.08, 80, g.yb, 165, g.yb, 0.5).c(270, g.yb, 330, X * 0.2, 330, X * 0.5, 1)
     .c(330, X * 0.82, 280, g.yt, 215, g.yt, 0.5).c(140, g.yt, 60, X * 0.78, g.h * 0.3, X * 0.5, 0).draw())


@ita("k", l=0.7, r=0.5)
def _ik(g):
    X, AS, B, h = g.X, g.AS, g.B, g.h
    entry(g, 0, AS).l(0, B / 2, 1).draw()
    g.P(h * 0.3, X * 0.32, 0).c(80, X * 0.6, 170, X + 6, 235, X * 0.86, 0.4).c(270, X * 0.74, 200, X * 0.56, 90, X * 0.5, 0.6).draw()
    exit_t(g.P(120, X * 0.52, 0.5).c(190, X * 0.45, 220, X * 0.3, 220, X * 0.2, 1), g, 220).draw()


@ita("s", l=0.8, r=0.8)
def _is(g):
    X, B, yt, yb, h, bd = g.X, g.B, g.yt, g.yb, g.h, g.bd
    W = 290
    (g.P(W - 20, X * 0.78, 0.2).c(W - 28, X * 0.95, W * 0.68, yt, W * 0.5, yt, 0.5).c(W * 0.24, yt, h + 2, X * 0.92, h + 2, X * 0.74, 1)
     .c(h + 2, X * 0.5, W - h - 2, X * 0.52, W - h - 2, X * 0.27, 1).c(W - h - 2, X * 0.08, W * 0.76, yb, W * 0.5, yb, 0.5)
     .c(W * 0.27, yb, 22, X * 0.06, 8, X * 0.2, 0.2).draw())
    g.ball(W - 22, X * 0.78, bd * 0.75); g.ball(10, X * 0.22, bd * 0.75)


@ita("x", l=0.6, r=0.6)
def _ix(g):
    X, B, yb, yt = g.X, g.B, g.yb, g.yt
    g.P(-40, X * 0.78, 0.2).c(-20, X + 4, 60, yt, 100, X * 0.7, 0.9).l(200, X * 0.3, 1).c(240, yb + 10, 300, yb, 330, X * 0.22, 0).draw()
    g.P(-10, X * 0.2, 0).c(20, yb, 90, yb, 120, X * 0.3, 0.3).l(240, X * 0.72, 0).c(260, yt, 320, X + 4, 330, X * 0.82, 0).draw()


@ita("z", l=0.7, r=0.7)
def _iz(g):
    X, A, B = g.X, g.A, g.B
    g.P(30, X * 0.82, 0.1).c(70, X + 4, 150, X - B * 2, 330, X - B / 2, 0).draw(); g.P(330 - A * 0.4, X - B, 0.9).l(30, B, 0.9).draw()
    g.P(30, B / 2, 0).c(150, B * 3, 250, -B, 340, B * 2, 0.1).draw()


# The kerning table of the sketch, in font units (roman; italic uses 70 %).
def sketch_kern() -> dict[str, float]:
    K: dict[str, float] = {}

    def add(L, R, v):
        for a in L:
            for b in R:
                K[a + b] = v

    add("T", "aceosru", -62); add("T", "yvw", -45); add("T", "AΔ", -55); add("T", ".,", -70); add("T", "J", -40)
    add("A", "TVWY", -58); add("A", "vwy", -34); add("A", "'’", -60); add("AΔ", "CGOQ", -18)
    add("VW", "aeo", -46); add("VW", ".,", -70); add("VW", "A", -55); add("Y", "aeo", -64); add("Y", ".,", -80); add("Y", "A", -60)
    add("L", "TVWY", -70); add("L", "'’", -80); add("L", "y", -30); add("P", ".,", -80); add("P", "A", -40); add("F", ".,", -60); add("F", "a", -20)
    add("r", ".,", -50); add("vwy", ".,", -40); add("f", "'’)?!]", 30); add("'’", "s", -25); add("'’", "A", -55)
    add("k", "eo", -12); add("o", "vwxy", -10); add("vwy", "o", -10); add("c", "k", 0); add("R", "TVWY", -24)
    return K


ROMAN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?'’-–—/()[]&"
EXTRA = "ﬁﬂﬀ"
GREEKSET = "αβγδεθλμπρσφψωΓΔΣΩ"
MATHSET = "+−×=<>()[]∑∫√∞∂′∇·"
SKETCH_CHARS = ROMAN + EXTRA + GREEKSET + MATHSET
