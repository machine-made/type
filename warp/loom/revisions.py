"""Warp 0.2 changes to glyphs of the sketch and of 0.1.

The approved sketch port (loom/sketch.py) stays as it is, so that the
test against the sketch engine keeps checking the port. The forms that
0.2 changes are replaced here; SKETCH keeps the originals.

* g: the lower loop closes on the link (OCR read the open loop as a
  comma at 10 px).
* f, ﬀ, ﬃ, ﬄ, ſ: a firmer hook: the drop is larger and hangs lower
  (OCR read f as t).
* ﬁ, ﬂ: the bar stops short of the i and the l, and the f of ﬂ ends
  in its own drop instead of running into the l (OCR read them as h and
  H). Italic ﬁ ﬂ the same.
* √: no right side bearing (the rule of the maths engine starts at the
  advance and must meet the bar of the sign).
* Σ, Ξ: heavier horizontals (they are all horizontals, which the level
  pen draws as hairlines).
* The word space is wider at text sizes (see `word_space`).

This file defines outlines of machine-made Warp: SIL Open Font License
1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

from loom.engine import PI, GlyphDef
from loom.latin_ext import hbar
from loom.sketch import G, GI, entry, exit_t, vbeak

REVISED = ("g", "f", "ﬁ", "ﬂ", "ﬀ", "Σ", "√")
REVISED_ITALIC = ("ﬁ", "ﬂ")
SKETCH = {k: G[k] for k in REVISED}
SKETCH_ITALIC = {k: GI[k] for k in REVISED_ITALIC}
# italic capitals that 0.2 draws with their own forms (loom/italic_caps.py)
ITALIC_CAPS_02 = "BDEFHIJKLPRSTUXYZ&"
SKETCH_GI = dict(GI)   # the italic table before 0.2 (loom/italic_caps.py adds the capitals)


def sketch_def(key: str, ital: bool) -> GlyphDef:
    """The glyph as the approved sketch draws it."""
    if ital and key in SKETCH_ITALIC:
        return SKETCH_ITALIC[key]
    if ital and key in SKETCH_GI:
        return SKETCH_GI[key]
    return SKETCH.get(key) or G[key]


def _def(old: GlyphDef, fn) -> GlyphDef:
    return GlyphDef(fn=fn, cap=old.cap, lc=old.lc, l=old.l, r=old.r, adv=old.adv, empty=old.empty,
                    upright=old.upright, bigop=old.bigop, slant=old.slant, yc=old.yc, greek=old.greek)


# ------------------------------------------------------------------- g

def _g(g):
    X, B, D, o, bd = g.X, g.B, g.D, g.o, g.bd
    cx, rx, cy, ry, yb2 = 198, 138, X * 0.655, X * 0.345 - B / 2 + o * 0.5, D - o + B / 2
    g.ring(cx, cy, rx, ry)
    e = g.pt(cx, cy, rx, ry, 0.3 * PI)
    g.P(e[0], e[1], 0).c(e[0] + 26, X + 2, cx + rx + 18, X + 16, cx + rx + 66, X + 12, 0.12).draw()
    g.ball(cx + rx + 70, X + 2, bd * 0.62)
    s = g.pt(cx, cy, rx, ry, 1.22 * PI)
    # 0.2: the loop ends on the link (the sketch stops at (118, -46)).
    (g.P(s[0], s[1], 0.3).c(s[0] - 34, s[1] - 50, 46, 46, 140, 34, 0).l(300, 32, 0)
     .c(398, 32, 436, -12, 436, -80, 1).c(436, -178, 342, yb2, 228, yb2, 0.5)
     .c(108, yb2, 22, -188, 22, -130, 1).c(22, -62, 70, -18, 128, 14, 0.25).c(150, 26, 172, 32, 196, 33, 0).draw())


# --------------------------------------------------------------- f hook

def f_hook(g, x0, xe):
    """The stem of f with its arch and a firm drop (0.2)."""
    AS, B, o, bd, A = g.AS, g.B, g.o, g.bd, g.A
    yt2 = AS + o - B / 2
    d = max(bd, A * 0.9) * 1.06
    ye = AS - d * 0.62 - 10
    (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 62, yt2, x0 + (xe - x0) * 0.64, yt2, 0.55)
     .c(x0 + (xe - x0) * 0.9, yt2, xe, AS - 22, xe, ye, 0.3).draw())
    g.ball(xe, ye, d)
    return ye


def _f(g):
    X, B, h, A = g.X, g.B, g.h, g.A
    f_hook(g, 0, 236)
    g.bar(-h - 78, h + 118, X - B / 2); g.serif(0, 0, 1, "b", A, g.sl * 1.2)


def _fi(g):
    X, B, h, A = g.X, g.B, g.h, g.A
    xi = 252
    # the drop of the f is the dot of the i
    f_hook(g, 0, xi)
    g.stem(xi, 0, X); g.serif(xi, 0, 1, "b")
    # the bar stops short of the i: a gap, not a shoulder
    g.bar(-h - 78, h + 100, X - B / 2)
    g.serif(0, 0, 1, "b", A, g.sl * 1.2)


FL_FORM = 2


def _fl(g):
    X, AS, B, o, h, A = g.X, g.AS, g.B, g.o, g.h, g.A
    if FL_FORM == 1:
        # the sketch's arch into the l; the bar stops short of the l
        xl = 292
        yt2 = AS + o - B / 2
        (g.P(0, B / 2, 1).l(0, AS - 178, 1).c(0, AS - 45, 66, yt2, 160, yt2, 0.5)
         .c(240, yt2, xl, AS - 20, xl, AS - 110, 1).l(xl, B / 2, 1).draw())
        g.serif(xl, 0, 1, "b")
    else:
        # the f ends in its own drop; the l stands apart (no head serif)
        xl = 346
        f_hook(g, 0, 236)
        g.stem(xl, 0, AS); g.serif(xl, 0, 1, "b")
    g.bar(-h - 78, h + 100, X - B / 2)
    g.serif(0, 0, 1, "b", A, g.sl * 1.2)


def _ff(g):
    X, AS, B, o, h, A = g.X, g.AS, g.B, g.o, g.h, g.A
    x0, x2 = 0, 262
    yt2 = AS + o - B / 2
    (g.P(x0, B / 2, 1).l(x0, AS - 178, 1).c(x0, AS - 45, x0 + 60, yt2, x0 + 140, yt2, 0.5)
     .c(x0 + 200, yt2, x2 - h - 6, AS - 30, x2 - h * 0.4, AS - 82, 0.05).draw())
    f_hook(g, x2, x2 + 236)
    g.bar(x0 - h - 78, x2 + h + 118, X - B / 2)
    g.serif(x0, 0, 1, "b", A, g.sl * 1.2); g.serif(x2, 0, 1, "b", A, g.sl * 1.2)


# ---------------------------------------------------------- italic fi fl

def _ifi(g):
    from loom.sketch import it_f
    X, B = g.X, g.B
    x = 190
    xi = x + 262
    it_f(g, x, x + 150); exit_t(entry(g, xi, X), g, xi).draw(); g.bar(x - 130, x + 112, X - B / 2)


def _ifl(g):
    from loom.sketch import it_f
    X, AS, B = g.X, g.AS, g.B
    x = 190
    xl = x + 272
    it_f(g, x, x + 150); exit_t(entry(g, xl, AS), g, xl).draw(); g.bar(x - 130, x + 112, X - B / 2)


# ------------------------------------------------------------- Sigma, Xi

def _Sigma(g):
    C, B, S = g.C, g.B, g.S
    W, k = 480, 1.9
    t = B * k
    hbar(g, 0, W, C - t / 2, k); vbeak(g, W - S * 0.7, C, C - 130)
    g.P(30, C - t, 1).l(255, C * 0.5, 1).draw()
    g.P(255, C * 0.5, 0).l(25, t, 0).draw()
    hbar(g, 0, W + 20, t / 2, k); vbeak(g, W + 20 - S * 0.7, 0, 140)


def _Xi(g):
    C, B, S = g.C, g.B, g.S
    W = 470
    to, tm = B * 1.9, B * 2.4
    hbar(g, 0, W, C - to / 2, 1.9); vbeak(g, S * 0.7, C, C - 120); vbeak(g, W - S * 0.7, C, C - 120)
    hbar(g, 70, W - 70, C * 0.5, 2.4)
    vbeak(g, 70 + S * 0.7, C * 0.5 - 55, C * 0.5 + 55); vbeak(g, W - 70 - S * 0.7, C * 0.5 - 55, C * 0.5 + 55)
    hbar(g, 0, W, to / 2, 1.9); vbeak(g, S * 0.7, 0, 120); vbeak(g, W - S * 0.7, 0, 120)
    return tm


G["g"] = _def(G["g"], _g)
G["f"] = _def(G["f"], _f)
G["ﬁ"] = _def(G["ﬁ"], _fi)
G["ﬂ"] = _def(G["ﬂ"], _fl)
G["ﬀ"] = _def(G["ﬀ"], _ff)
G["Σ"] = _def(G["Σ"], _Sigma)
G["Ξ"] = _def(G["Ξ"], _Xi)
# √: no right side bearing, so that the maths engine's rule joins its bar
G["√"] = GlyphDef(**{**G["√"].__dict__, "r": 0.0})
GI["ﬁ"] = _def(GI["ﬁ"], _ifi)
GI["ﬂ"] = _def(GI["ﬂ"], _ifl)


# ------------------------------------------------------------ word space

SPACE_TEXT = 310     # at opsz 10 (the text styles); the sketch has 270
SPACE_DISPLAY = 270  # at opsz 60 (Display), as in the sketch


def word_space(p) -> float:
    """The space advance. Linear in the engine's optical-size factor k,
    so that it interpolates exactly along the opsz axis."""
    from loom.engine import params
    k10, k60 = params(opsz=10).k, params(opsz=60).k
    t = (p.k - k10) / (k60 - k10)
    t = min(1.0, max(0.0, t))
    return SPACE_TEXT + (SPACE_DISPLAY - SPACE_TEXT) * t
