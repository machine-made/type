"""Italic capitals with their own cursive forms (Warp 0.2).

The sketch gave cursive forms to A C G M N O Q V W only; 0.1 slanted
the roman for the rest. 0.2 draws B D E F H I J K L P R S T U X Y Z and
the italic & with the same vocabulary as the sketch's italic: an entry
hook at the top of the main stem, a foot that curls to the left, exit
tails to the right, drops instead of beaks. Like all italics they are
drawn upright; the engine slants the centre-lines, not the pen.

Still slanted romans (unbracketed serifs): Æ Œ Ø Þ and the Greek
capitals (see STATUS.md).

This file defines outlines of machine-made Warp: SIL Open Font License
1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

from loom.extended import ita_cap
from loom.sketch import dbowl, iexit

# ------------------------------------------------------------- helpers


def cap_entry(g, x, top=None):
    """An entry hook from the left into a stem at x; returns the path at (x, top - 82)."""
    C, B = g.C, g.B
    t = C if top is None else top
    return (g.P(x - 118, t - 84, 0).c(x - 104, t - 22, x - 64, t - B / 2, x - 34, t - B / 2, 0.4)
            .c(x - 8, t - B / 2, x, t - 40, x, t - 84, 1))


def foot_left(p, g, x):
    """Continue a stem at x down into a foot that curls to the left, ending in a small drop."""
    B, o, bd = g.B, g.o, g.bd
    yb = -o + B / 2
    p.l(x, 84, 1).c(x, 26, x - 22, yb, x - 60, yb, 0.35).c(x - 92, yb, x - 112, 16, x - 116, 46, 0).draw()
    g.ball(x - 114, 50, bd * 0.55)


def tail_right(p, g, x):
    return iexit(p, g, x)


def drop_end(g, x, y, k=0.7):
    g.ball(x, y, g.bd * k)


def istem(g, x, top=None):
    foot_left(cap_entry(g, x, top).l(x, g.C * 0.5, 1), g, x)


# ------------------------------------------------------------- letters


@ita_cap("I", l=0.9, r=0.5)
def _iI(g):
    istem(g, 120)


@ita_cap("J", l=0.7, r=0.4)
def _iJ(g):
    C, B, D, bd, o = g.C, g.B, g.D, g.bd, g.o
    x = 240
    yb = D * 0.62 - o + B / 2
    (cap_entry(g, x).l(x, C * 0.06, 1).c(x, yb * 0.45, x - 40, yb, x - 108, yb, 0.5)
     .c(x - 162, yb, x - 196, yb * 0.76, x - 204, yb * 0.5, 0.25).draw())
    g.ball(x - 204, yb * 0.5)


@ita_cap("L", l=0.8, r=0.4)
def _iL(g):
    C, B, o, bd = g.C, g.B, g.o, g.bd
    x = 120
    yb = -o + B / 2
    cap_entry(g, x).l(x, 96, 1).c(x, 40, x - 20, 14, x - 58, 14, 0.3).draw()
    # the base: a hairline that dips under the stem and turns up at the end
    (g.P(x - 58, 14, 0.2).c(x - 96, 14, x - 104, 52, x - 76, 60, 0.1).draw())
    (g.P(x - 40, 22, 0).c(x + 20, yb, 200, yb, 300, yb, 0).c(350, yb, 384, 30, 396, 92, 0.15).draw())
    drop_end(g, 398, 96, 0.62)


@ita_cap("E", l=0.8, r=0.4)
def _iE(g):
    C, B, h = g.C, g.B, g.h
    x = 120
    istem(g, x)
    g.bar(x - h, x + 300, C - B / 2); drop_end(g, x + 300, C - 34, 0.6)
    g.bar(x - h, x + 240, C * 0.51)
    g.P(x - h, B / 2, 0).l(x + 250, B / 2, 0).c(x + 290, B / 2, x + 312, 30, x + 318, 82, 0.1).draw()
    drop_end(g, x + 318, 88, 0.6)


@ita_cap("F", l=0.8, r=0.3)
def _iF(g):
    C, B, h = g.C, g.B, g.h
    x = 120
    istem(g, x)
    g.bar(x - h, x + 300, C - B / 2); drop_end(g, x + 300, C - 34, 0.6)
    g.bar(x - h, x + 236, C * 0.5)


@ita_cap("T", l=0.6, r=0.4)
def _iT(g):
    C, B = g.C, g.B
    W = 520
    # the top: a hairline that starts in a drop and runs into a straight bar
    (g.P(28, C - 92, 0.15).c(36, C - 30, 80, C - B / 2, 150, C - B / 2, 0).l(W, C - B / 2, 0).draw())
    drop_end(g, 30, C - 96, 0.6)
    xs = W / 2 + 10
    foot_left(g.P(xs, C - B, 0.9).l(xs, C * 0.5, 1), g, xs)


@ita_cap("H", l=0.9, r=0.45)
def _iH(g):
    C, B = g.C, g.B
    x0, x1 = 120, 540
    istem(g, x0)
    tail_right(g.P(x1, C - B / 2, 0.55).l(x1, C - 60, 1), g, x1).draw()
    g.bar(x0, x1, C * 0.5)


@ita_cap("K", l=0.9, r=0.4)
def _iK(g):
    C, B, h, bd = g.C, g.B, g.h, g.bd
    x = 120
    istem(g, x)
    g.P(x + h - 4, C * 0.32, 0).c(x + 140, C * 0.52, x + 300, C * 0.84, x + 400, C - 44, 0).draw()
    drop_end(g, x + 404, C - 46, 0.7)
    tail_right(g.P(x + 150, C * 0.52, 0.8).l(x + 352, 110, 1), g, x + 360).draw()


@ita_cap("U", l=0.9, r=0.45)
def _iU(g):
    C, B, o, h = g.C, g.B, g.o, g.h
    x0, x1 = 120, 520
    yb = -o + B / 2
    xm = (x0 + x1) / 2
    (cap_entry(g, x0).l(x0, C * 0.32, 1).c(x0, C * 0.08, xm - 130, yb, xm, yb, 0.5)
     .c(xm + 130, yb, x1 - 24, C * 0.12, x1 - h * 0.25, C * 0.34, 0).draw())
    tail_right(g.P(x1, C - B / 2, 0.55).l(x1, C - 60, 1), g, x1).draw()


@ita_cap("Y", l=0.6, r=0.4)
def _iY(g):
    C, B, A, bd = g.C, g.B, g.A, g.bd
    xm, yj = 300, C * 0.44
    (g.P(-30, C - 84, 0).c(-16, C - 22, 24, C - B / 2, 54, C - B / 2, 0.4)
     .c(80, C - B / 2, 92, C - 40, 96, C - 84, 1).l(xm, yj, 1).draw())
    g.P(xm + A * 0.2, yj, 0).l(520, C - 96, 0).c(526, C - 50, 540, C - 30, 560, C - 26, 0.2).draw()
    drop_end(g, 566, C - 30, 0.7)
    foot_left(g.P(xm, yj + B, 0.9).l(xm, yj - 40, 1), g, xm)


@ita_cap("X", l=0.6, r=0.5)
def _iX(g):
    C, B, o, bd = g.C, g.B, g.o, g.bd
    yb, yt = -o + B / 2, C + o - B / 2
    (g.P(-40, C * 0.8, 0.2).c(-20, C + 4, 70, yt, 110, C * 0.74, 0.9).l(350, C * 0.24, 1)
     .c(380, yb + 12, 450, yb, 480, C * 0.2, 0).draw())
    drop_end(g, -38, C * 0.79, 0.6)
    (g.P(-10, C * 0.2, 0).c(20, yb, 100, yb, 130, C * 0.26, 0.3).l(380, C * 0.74, 0)
     .c(400, yt, 470, C + 4, 490, C * 0.8, 0).draw())
    drop_end(g, 492, C * 0.79, 0.6)


@ita_cap("Z", l=0.7, r=0.6)
def _iZ(g):
    C, A, B = g.C, g.A, g.B
    g.P(40, C * 0.84, 0.1).c(90, C + 4, 200, C - B * 2.5, 450, C - B / 2, 0).draw()
    drop_end(g, 40, C * 0.84, 0.6)
    g.P(450 - A * 0.4, C - B, 0.9).l(40, B, 0.9).draw()
    g.P(40, B / 2, 0).c(200, B * 3.5, 330, -B, 470, B * 2.5, 0.1).draw()
    drop_end(g, 472, B * 2.6 + 6, 0.6)


@ita_cap("S", l=0.8, r=0.8)
def _iS(g):
    C, B, o, h, bd = g.C, g.B, g.o, g.h, g.bd
    W = 400
    yt, yb = C + o - B / 2, -o + B / 2
    (g.P(W - 22, C * 0.78, 0.2).c(W - 30, C * 0.95, W * 0.68, yt, W * 0.5, yt, 0.5).c(W * 0.22, yt, h + 2, C * 0.92, h + 2, C * 0.75, 1)
     .c(h + 2, C * 0.5, W - h - 2, C * 0.52, W - h - 2, C * 0.26, 1).c(W - h - 2, C * 0.08, W * 0.76, yb, W * 0.5, yb, 0.5)
     .c(W * 0.24, yb, 22, C * 0.06, 8, C * 0.2, 0.2).draw())
    drop_end(g, W - 24, C * 0.78, 0.8); drop_end(g, 10, C * 0.22, 0.8)


def _bowl_stem(g, x):
    istem(g, x)


@ita_cap("B", l=0.9, r=0.7)
def _iB(g):
    C = g.C
    x = 120
    _bowl_stem(g, x)
    dbowl(g, x, C * 0.52 - g.B, C, x + 370, x + 160); dbowl(g, x, 0, C * 0.52, x + 420, x + 180)


@ita_cap("D", l=0.9, r=0.75)
def _iD(g):
    C = g.C
    x = 120
    _bowl_stem(g, x)
    dbowl(g, x, 0, C, x + 490, x + 190)


@ita_cap("P", l=0.9, r=0.6)
def _iP(g):
    C = g.C
    x = 120
    _bowl_stem(g, x)
    dbowl(g, x, C * 0.44, C, x + 410, x + 180)


@ita_cap("R", l=0.9, r=0.4)
def _iR(g):
    C, B, o = g.C, g.B, g.o
    x = 120
    _bowl_stem(g, x)
    dbowl(g, x, C * 0.47, C, x + 395, x + 175)
    tail_right(g.P(x + 165, C * 0.47 + B / 2, 0.1).c(x + 290, C * 0.45, x + 340, C * 0.36, x + 346, C * 0.2, 1), g, x + 350).draw()


@ita_cap("Þ", l=0.9, r=0.6)
def _iThorn(g):
    C = g.C
    x = 120
    _bowl_stem(g, x)
    dbowl(g, x, C * 0.2, C * 0.8, x + 410, x + 180)


@ita_cap("&", l=0.7, r=0.4)
def _iamp(g):
    """The italic &: an Et, as in old italics: an epsilon-like E run into a t."""
    C, B, o, h, bd = g.C, g.B, g.o, g.h, g.bd
    yt, yb = C + o - B / 2, -o + B / 2
    (g.P(330, C * 0.82, 0.2).c(322, C * 0.96, 270, yt, 210, yt, 0.4).c(120, yt, 70, C * 0.88, 70, C * 0.76, 1)
     .c(70, C * 0.6, 140, C * 0.53, 230, C * 0.53, 0).draw())
    drop_end(g, 330, C * 0.82, 0.75)
    (g.P(230, C * 0.53, 0).c(110, C * 0.53, h + 4, C * 0.43, h + 4, C * 0.25, 1).c(h + 4, C * 0.07, 100, yb, 210, yb, 0.5)
     .c(330, yb, 400, C * 0.2, 450, C * 0.5, 0.9).l(520, C * 0.92, 1).draw())
    g.bar(390, 600, C * 0.6)
