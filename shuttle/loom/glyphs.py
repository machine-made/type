"""Shuttle glyph table: every glyph as a list of primitives.

Source: reference/shuttle-sketch-0.1.js (the glyph table `G`). The
sketch glyphs are ported one to one. The rest of the set (ASCII
punctuation, symbols, Latin-1 letters, marks) is drawn here from the
same four primitives: rect, ring, parallelogram, vee.

Units: font units, 1000 per em, y up. A draw function gets the canvas
`g` (loom/geom.py) and the glyph width W, with the origin at the left
side of the glyph box. The build adds the sidebearings.

Cuts: a ring cut is (side, lo, hi). "l" and "r" remove the left or
right half of the ring between y = lo and y = hi. "t" and "b" remove the
top or bottom half between x = lo and x = hi. INF means "past the ring".
The sketch wrote cuts as rectangles; each one is rewritten here as the
side cut that gives the same visible shape (see BRIEF.md).

Do not trace, import or copy outlines from other fonts. All shapes come
from this table.

Licence: this table defines the font outlines, so it is Font Software
under the SIL Open Font License 1.1 (see shuttle/OFL.txt), Reserved Font
Name "machine-made". The rest of loom/ is Apache-2.0 (see LICENSE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from loom.geom import INF

UPM = 1000
XH, CAP, ASC, DESC, OS = 520, 700, 730, -210, 10

WGHT = (100, 400, 700, 900)
WDTH = (70, 100, 140)
FW = 560  # tabular figure width at wdth 100


@dataclass(frozen=True)
class Params:
    wght: float
    wdth: float

    @property
    def t(self) -> float:
        return (self.wght - 100) / 800

    @property
    def S(self) -> float:
        """Stem width: 28 at wght 100, 178 at wght 900."""
        return 28 + self.t * 150

    @property
    def H(self) -> float:
        """Horizontal thickness: 84 % of the stem."""
        return self.S * 0.84

    @property
    def wf(self) -> float:
        return self.wdth / 100

    @property
    def sb(self) -> float:
        """Sidebearing on each side."""
        return 22 + 0.22 * self.S


def tab_factor(wf: float) -> float:
    """Width factor of the tabular figures: 0.8 at wdth 70, 1 at 100, 1.25 at 140.

    Linear between the master widths, so the variable font gives the
    same value at every width (the sketch clamps wdth/100 to 0.8..1.25).
    """
    if wf <= 1.0:
        return 1.0 - (1.0 - wf) * (0.2 / 0.3)
    return 1.0 + (wf - 1.0) * (0.25 / 0.4)


@dataclass
class Glyph:
    name: str
    unicodes: tuple
    draw: Callable
    base: float = 0.0          # width at wdth 100
    kind: str = "prop"         # "prop", "tab" or "stem" (width from the stem)
    stem_width: Callable | None = None   # for kind "stem": W from Params
    floor: float = 2.3         # smallest width, in stems
    sketch: bool = False       # part of the approved sketch set

    def width(self, p: Params) -> float:
        if self.kind == "stem":
            return self.stem_width(p)
        if self.kind == "tab":
            return self.base * tab_factor(p.wf)
        return max(self.base * p.wf, self.floor * p.S)


GLYPHS: dict[str, Glyph] = {}


def glyph(name, uni, base=0.0, kind="prop", stem_width=None, floor=2.3, sketch=False):
    def deco(fn):
        unis = tuple(uni) if isinstance(uni, (tuple, list)) else ((uni,) if uni is not None else ())
        GLYPHS[name] = Glyph(name, unis, fn, base, kind, stem_width, floor, sketch)
        return fn
    return deco


def sketch(name, uni, base=0.0, **kw):
    return glyph(name, uni, base, sketch=True, **kw)


def dot_size(p_or_g) -> float:
    return p_or_g.S * 1.06


def i_gap(S: float) -> float:
    return max(60.0, S * 0.55)


# --------------------------------------------------- shared constructions

def arch(g, x0, x1, top, stem_to):
    """n shoulder: the upper half of a ring, then the right stem."""
    ry = min((x1 - x0) * 0.52, top * 0.62)
    y0 = top + OS - 2 * ry
    cy = (y0 + top + OS) / 2
    g.ring(x0, y0, x1, top + OS, [("l", -INF, cy), ("r", -INF, cy)])
    g.rect(x1 - g.S, stem_to, x1, cy + 1)


def bowl_d(g, x0, y0, x1, y1, s=None, h=None):
    """Square on the left, round on the right."""
    s = g.S if s is None else s
    h = g.H if h is None else h
    g.ring(x0, y0, x1, y1, ts=s, th=h)
    g.rect(x0, y0, x0 + (x1 - x0) / 2, y0 + h)
    g.rect(x0, y1 - h, x0 + (x1 - x0) / 2, y1)
    g.rect(x0, y0, x0 + s, y1)


def two_ring_s(g, W, top):
    """S and s: two stacked rings that share the spine."""
    mid = top * 0.48
    yl1 = mid + g.H
    cu = (mid + top + OS) / 2
    cl = (-OS + yl1) / 2
    g.ring(W * 0.04, mid, W * 0.97, top + OS, [("r", -INF, cu + (top - cu) * 0.26)])
    g.ring(0, -OS, W, yl1, [("l", cl * 0.72, INF)])


def six(g, W):
    g.ring(0, -OS, W, CAP * 0.64)
    g.ring(0, -OS, W * 1.02, CAP + OS, [("r", -INF, CAP * 0.74)])


def chevron(g, x0, wc, ym, v, t, left=True):
    """A < (left=True) or > with its tip at x0 (or x0 + wc).

    wc is the full width; each arm moves wc - t across. Callers keep
    wc - t > 0 (see chevron_size), or the arms would cross.
    """
    # One contour: the union of the two arms (a V turned on its side,
    # with horizontal ends).
    pts = [(0, 0), (wc - t, v), (wc, v), (t, 0), (wc, -v), (wc - t, -v)]
    if left:
        g.poly([(x0 + x, ym + y) for x, y in pts])
    else:
        g.poly([(x0 + wc - x, ym + y) for x, y in pts])


def chevron_size(g, d, v, k=1.0):
    """Return (wc, t): full width and arm width for an arm that moves d across."""
    t = g.dt(d, v) * k
    return d + t, t


def bar_poly(g, cx, cy, length, width, angle):
    """A rectangle turned by `angle` (radians from vertical), centred on (cx, cy)."""
    import math
    ux, uy = math.sin(angle), math.cos(angle)
    px, py = uy, -ux
    hl, hw = length / 2, width / 2
    g.poly([(cx - ux * hl - px * hw, cy - uy * hl - py * hw),
            (cx - ux * hl + px * hw, cy - uy * hl + py * hw),
            (cx + ux * hl + px * hw, cy + uy * hl + py * hw),
            (cx + ux * hl - px * hw, cy + uy * hl - py * hw)])


def comma_shape(g, x, y):
    """The sketch comma with its square at (x, y)."""
    d = dot_size(g)
    g.rect(x, y, x + d, y + d)
    g.poly([(x + d * 0.25, y), (x + d, y), (x + d * 0.55, y - d * 1.1), (x + d * 0.1, y - d * 1.1)])


def quote_right(g, x):
    d = dot_size(g)
    comma_shape(g, x, CAP - d)


def quote_left(g, x):
    d = dot_size(g)
    # The right quote turned by 180 degrees: square at the bottom.
    g.shift(x, 0, lambda: g.rot(d, CAP - d * 1.05, lambda: comma_shape(g, 0, CAP - d)))


# --------------------------------------------------------------- lowercase

@sketch("o", 0x6F, 560)
def _o(g, W):
    g.ring(0, -OS, W, XH + OS)


@sketch("c", 0x63, 520)
def _c(g, W):
    g.ring(0, -OS, W, XH + OS, [("r", XH * 0.30, XH * 0.71)])


@sketch("e", 0x65, 540)
def _e(g, W):
    yb = XH * 0.44
    g.ring(0, -OS, W, XH + OS, [("r", XH * 0.25, yb)])
    g.rect(g.S * 0.5, yb, W, yb + g.H)


@sketch("n", 0x6E, 540)
def _n(g, W):
    g.rect(0, 0, g.S, XH)
    arch(g, 0, W, XH, 0)


@sketch("h", 0x68, 540)
def _h(g, W):
    g.rect(0, 0, g.S, ASC)
    arch(g, 0, W, XH, 0)


@sketch("m", 0x6D, 820)
def _m(g, W):
    m = (W + g.S) / 2
    g.rect(0, 0, g.S, XH)
    arch(g, 0, m, XH, 0)
    arch(g, m - g.S, W, XH, 0)


@sketch("u", 0x75, 540)
def _u(g, W):
    g.rot(W, XH / 2, lambda: _n(g, W))


def _bee(g, W):
    g.rect(0, 0, g.S, ASC)
    g.ring(0, -OS, W, XH + OS)


@sketch("b", 0x62, 560)
def _b(g, W):
    _bee(g, W)


@sketch("d", 0x64, 560)
def _d(g, W):
    g.flipX(W, lambda: _bee(g, W))


@sketch("p", 0x70, 560)
def _p(g, W):
    g.rot(W, XH / 2, lambda: g.flipX(W, lambda: _bee(g, W)))


@sketch("q", 0x71, 560)
def _q(g, W):
    g.rot(W, XH / 2, lambda: _bee(g, W))


@sketch("g", 0x67, 560)
def _g(g, W):
    g.ring(0, -OS + 20, W, XH + OS)
    rh = 170
    y0 = DESC - OS
    cy = y0 + rh
    g.ring(0, y0, W, y0 + 2 * rh, [("l", cy, INF), ("r", cy, INF)])
    g.rect(W - g.S, cy - 1, W, XH)


@sketch("a", 0x61, 520)
def _a(g, W):
    r = XH * 0.36
    y1 = XH + OS
    y0 = y1 - 2 * r
    cy = y0 + r
    # Sketch: two cut rectangles; the right one ends at the stem, which
    # covers the rest of that quarter.
    g.ring(0, y0, W, y1, [("l", -INF, cy + r * 0.28), ("r", -INF, cy)])
    g.rect(W - g.S, 0, W, cy + 1)
    b1 = XH * 0.55
    g.ring(0, -OS, W - g.S * 0.4, b1)
    g.rect(W - g.S, 0, W, b1)


@sketch("s", 0x73, 500)
def _s(g, W):
    two_ring_s(g, W, XH)


def _i_stem(g, W):
    g.rect(0, 0, g.S, XH)


@sketch("i", 0x69, kind="stem", stem_width=lambda p: p.S)
def _i(g, W):
    _i_stem(g, W)
    gap = i_gap(g.S)
    g.rect(0, XH + gap, g.S, XH + gap + g.S * 1.04)


@glyph("dotlessi", 0x131, kind="stem", stem_width=lambda p: p.S)
def _dotlessi(g, W):
    _i_stem(g, W)


@sketch("j", 0x6A, kind="stem", stem_width=lambda p: p.S + 120)
def _j(g, W):
    x = W - g.S
    y0 = DESC - OS
    cy = DESC + 80
    g.ring(0, y0, W, DESC + 170, [("l", cy, INF), ("r", cy, INF)])
    g.rect(x, cy - 1, W, XH)
    gap = i_gap(g.S)
    g.rect(x, XH + gap, W, XH + gap + g.S * 1.04)


@sketch("l", 0x6C, kind="stem", stem_width=lambda p: p.S)
def _l(g, W):
    g.rect(0, 0, g.S, ASC)


@sketch("f", 0x66, 330)
def _f(g, W):
    x = W * 0.18
    r = min(150, (W - x) / 2 + 10)
    g.rect(x, 0, x + g.S, ASC - r + 1)
    c = ASC + OS - r
    g.ring(x, ASC + OS - 2 * r, x + 2 * r + 40, ASC + OS, [("l", -INF, c), ("r", -INF, c)])
    g.rect(0, XH - g.H, W, XH)


@sketch("t", 0x74, 330)
def _t(g, W):
    x = W * 0.18
    r = min(130, (W - x) / 2)
    g.rect(x, r - OS - 1, x + g.S, XH + 150)
    c = r - OS
    g.ring(x, -OS, x + 2 * r + 30, 2 * r - OS, [("l", c, INF), ("r", c, INF)])
    g.rect(0, XH - g.H, W, XH)


@sketch("r", 0x72, 330)
def _r(g, W):
    ry = XH * 0.42
    c = XH + OS - ry
    # Sketch: the lower half goes, and everything right of x = W.
    g.ring(0, XH + OS - 2 * ry, W * 1.9, XH + OS, [("l", -INF, c), ("r", -INF, c), ("t", W, INF)])
    g.rect(0, 0, g.S, XH)


@sketch("k", 0x6B, 520)
def _k(g, W):
    g.rect(0, 0, g.S, ASC)
    t = g.dt(W * 0.7, XH)
    g.par(g.S * 0.6, XH * 0.30, W - t / 2, XH, t)
    g.par(W * 0.34, XH * 0.52, W - t / 2, 0, t)


@sketch("v", 0x76, 520)
def _v(g, W):
    g.vee(0, W, XH, 0, g.dt(W / 2, XH))


@sketch("w", 0x77, 780)
def _w(g, W):
    t = g.dt(W / 4, XH)
    g.vee(0, W * 0.56, XH, 0, t)
    g.vee(W * 0.44, W, XH, 0, t)


@sketch("x", 0x78, 520)
def _x(g, W):
    t = g.dt(W, XH)
    g.par(t / 2, XH, W - t / 2, 0, t)
    g.par(W - t / 2, XH, t / 2, 0, t)


@sketch("y", 0x79, 520)
def _y(g, W):
    t = g.dt(W / 2, XH)
    g.vee(0, W, XH, 0, t)
    k = (W / 2) / XH * (-DESC) * 0.85
    g.par(W / 2, 0, W / 2 - k, DESC + g.H * 0.2, t)
    g.rect(W / 2 - k - t / 2 - 60, DESC, W / 2 - k + t / 2, DESC + g.H)


@sketch("z", 0x7A, 480)
def _z(g, W):
    t = g.dt(W, XH)
    g.rect(0, XH - g.H, W, XH)
    g.rect(0, 0, W, g.H)
    g.par(W - t / 2, XH - g.H, t / 2, g.H, t)


# --------------------------------------------------------------- uppercase

@sketch("A", 0x41, 660)
def _A(g, W):
    t = g.dt(W / 2, CAP)
    g.rot(W, CAP / 2, lambda: g.vee(0, W, CAP, 0, t))
    g.rect(W * 0.18, CAP * 0.22, W * 0.82, CAP * 0.22 + g.H)


@sketch("B", 0x42, 620)
def _B(g, W):
    bowl_d(g, 0, CAP * 0.48, W * 0.9, CAP)
    bowl_d(g, 0, 0, W, CAP * 0.48 + g.H)


@sketch("C", 0x43, 680)
def _C(g, W):
    g.ring(0, -OS, W, CAP + OS, [("r", CAP * 0.31, CAP * 0.69)])


@sketch("D", 0x44, 660)
def _D(g, W):
    bowl_d(g, 0, 0, W, CAP)


def _E(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(0, CAP - g.H, W, CAP)
    g.rect(0, 0, W, g.H)
    g.rect(0, CAP * 0.47, W * 0.9, CAP * 0.47 + g.H)


sketch("E", 0x45, 560)(_E)


@sketch("F", 0x46, 530)
def _F(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(0, CAP - g.H, W, CAP)
    g.rect(0, CAP * 0.45, W * 0.9, CAP * 0.45 + g.H)


@sketch("G", 0x47, 700)
def _G(g, W):
    g.ring(0, -OS, W, CAP + OS, [("r", CAP * 0.47, CAP * 0.69)])
    g.rect(W * 0.5, CAP * 0.47 - g.H, W, CAP * 0.47)
    g.rect(W - g.S, 0, W, CAP * 0.47)


@sketch("H", 0x48, 640)
def _H(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(W - g.S, 0, W, CAP)
    g.rect(0, CAP * 0.47, W, CAP * 0.47 + g.H)


@sketch("I", 0x49, kind="stem", stem_width=lambda p: p.S)
def _I(g, W):
    g.rect(0, 0, g.S, CAP)


@sketch("J", 0x4A, 520)
def _J(g, W):
    r = W * 0.5
    cy = r - OS
    g.ring(0, -OS, W, 2 * r - OS, [("l", cy, INF), ("r", cy, INF)])
    g.rect(W - g.S, cy - 1, W, CAP)


@sketch("K", 0x4B, 640)
def _K(g, W):
    g.rect(0, 0, g.S, CAP)
    t = g.dt(W, CAP * 0.6)
    # Sketch: the arm starts at x = S/2. When the arm is wider than the
    # stem it poked out left of the stem; it now starts at t/2 at least.
    g.par(max(g.S * 0.5, t / 2), CAP * 0.28, W - t / 2, CAP, t)
    g.par(W * 0.32, CAP * 0.5, W - t / 2, 0, t)


@sketch("L", 0x4C, 520)
def _L(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(0, 0, W, g.H)


@sketch("M", 0x4D, 800)
def _M(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(W - g.S, 0, W, CAP)
    g.vee(0, W, CAP, 0, g.dt(W / 2, CAP) * 0.92)


@sketch("N", 0x4E, 650)
def _N(g, W):
    g.rect(0, 0, g.S, CAP)
    g.rect(W - g.S, 0, W, CAP)
    t = g.dt(W, CAP)
    g.poly([(0, CAP), (t, CAP), (W, 0), (W - t, 0)])


def _O(g, W):
    g.ring(0, -OS, W, CAP + OS)


sketch("O", 0x4F, 740)(_O)


@sketch("P", 0x50, 600)
def _P(g, W):
    g.rect(0, 0, g.S, CAP)
    bowl_d(g, 0, CAP * 0.40, W, CAP)


@sketch("Q", 0x51, 740)
def _Q(g, W):
    g.ring(0, -OS, W, CAP + OS)
    t = g.dt(W * 0.3, CAP * 0.35)
    g.par(W * 0.62, CAP * 0.24, W * 0.96, -OS - 30, t)


@sketch("R", 0x52, 630)
def _R(g, W):
    g.rect(0, 0, g.S, CAP)
    bowl_d(g, 0, CAP * 0.42, W * 0.97, CAP)
    t = g.dt(W * 0.5, CAP * 0.42)
    g.par(W * 0.5, CAP * 0.42 + g.H * 0.5, W - t / 2, 0, t)


@sketch("S", 0x53, 620)
def _S(g, W):
    two_ring_s(g, W, CAP)


@sketch("T", 0x54, 580)
def _T(g, W):
    g.rect(0, CAP - g.H, W, CAP)
    g.rect(W / 2 - g.S / 2, 0, W / 2 + g.S / 2, CAP)


@sketch("U", 0x55, 640)
def _U(g, W):
    r = W * 0.48
    cy = r - OS
    g.ring(0, -OS, W, 2 * r - OS, [("l", cy, INF), ("r", cy, INF)])
    g.rect(0, cy - 1, g.S, CAP)
    g.rect(W - g.S, cy - 1, W, CAP)


@sketch("V", 0x56, 640)
def _V(g, W):
    g.vee(0, W, CAP, 0, g.dt(W / 2, CAP))


@sketch("W", 0x57, 920)
def _W(g, W):
    t = g.dt(W / 4, CAP)
    g.vee(0, W * 0.56, CAP, 0, t)
    g.vee(W * 0.44, W, CAP, 0, t)


@sketch("X", 0x58, 640)
def _X(g, W):
    t = g.dt(W, CAP)
    g.par(t / 2, CAP, W - t / 2, 0, t)
    g.par(W - t / 2, CAP, t / 2, 0, t)


@sketch("Y", 0x59, 620)
def _Y(g, W):
    g.vee(0, W, CAP, CAP * 0.40, g.dt(W / 2, CAP * 0.6))
    g.rect(W / 2 - g.S / 2, 0, W / 2 + g.S / 2, CAP * 0.44)


@sketch("Z", 0x5A, 590)
def _Z(g, W):
    t = g.dt(W, CAP)
    g.rect(0, CAP - g.H, W, CAP)
    g.rect(0, 0, W, g.H)
    g.par(W - t / 2, CAP - g.H, t / 2, g.H, t)


# ------------------------------------------------------- figures (tabular)

@sketch("zero", 0x30, FW, kind="tab")
def _zero(g, W):
    g.ring(W * 0.04, -OS, W * 0.96, CAP + OS)


@sketch("one", 0x31, FW, kind="tab")
def _one(g, W):
    x = W * 0.55
    g.rect(x, 0, x + g.S, CAP)
    g.poly([(x + g.S * 0.3, CAP), (x - W * 0.34, CAP * 0.74),
            (x - W * 0.34, CAP * 0.74 - g.H), (x + g.S * 0.3, CAP - g.H * 1.5)])


@sketch("two", 0x32, FW, kind="tab")
def _two(g, W):
    r = CAP * 0.27
    y0 = CAP + OS - 2 * r
    cy = y0 + r
    g.ring(0, y0, W, CAP + OS, [("l", -INF, cy + r * 0.25), ("r", -INF, cy)])
    t = g.dt(W * 0.8, cy)
    g.poly([(W - t, cy), (W, cy), (t * 0.9, g.H), (0, g.H)])
    g.rect(0, 0, W, g.H)
    g.rect(W - g.S, cy - 30, W, cy + 1)


@sketch("three", 0x33, FW, kind="tab")
def _three(g, W):
    m = CAP * 0.53
    cu = (m - g.H + CAP + OS) / 2
    cl = (-OS + m) / 2
    # Sketch cuts end at x = 0.45 W; the bar covers the rest.
    g.ring(W * 0.06, m - g.H, W * 0.94, CAP + OS, [("l", -INF, cu + (CAP - cu) * 0.12)])
    g.ring(0, -OS, W, m, [("l", cl * 0.65, INF)])
    g.rect(W * 0.32, m - g.H, W * 0.6, m)


@sketch("four", 0x34, FW, kind="tab")
def _four(g, W):
    x = W * 0.64
    g.rect(x, 0, x + g.S, CAP)
    t = g.dt(x, CAP * 0.7)
    g.poly([(x - t * 0.2, CAP), (x + g.S * 0.4, CAP), (t * 0.7, CAP * 0.3), (0, CAP * 0.3)])
    g.rect(0, CAP * 0.24, W, CAP * 0.24 + g.H)


@sketch("five", 0x35, FW, kind="tab")
def _five(g, W):
    top = CAP * 0.62
    cy = top / 2
    g.ring(0, -OS, W, top + OS, [("l", cy * 0.58, INF), ("t", -INF, W * 0.46)])
    g.rect(W * 0.06, top + OS - g.H, W * 0.5, top + OS)
    g.rect(W * 0.06, top - 30, W * 0.06 + g.S, CAP)
    g.rect(W * 0.06, CAP - g.H, W * 0.94, CAP)


@sketch("six", 0x36, FW, kind="tab")
def _six(g, W):
    six(g, W)


@sketch("seven", 0x37, FW, kind="tab")
def _seven(g, W):
    g.rect(0, CAP - g.H, W, CAP)
    t = g.dt(W * 0.6, CAP)
    g.par(W - t / 2, CAP - g.H, W * 0.36, 0, t)


@sketch("eight", 0x38, FW, kind="tab")
def _eight(g, W):
    g.ring(W * 0.07, CAP * 0.52 - g.H, W * 0.93, CAP + OS)
    g.ring(0, -OS, W, CAP * 0.52)


@sketch("nine", 0x39, FW, kind="tab")
def _nine(g, W):
    g.rot(W, CAP / 2, lambda: six(g, W))


# ------------------------------------------------------------ punctuation

def _dot_w(p):
    return p.S * 1.06


@sketch("period", 0x2E, kind="stem", stem_width=_dot_w)
def _period(g, W):
    d = dot_size(g)
    g.rect(0, 0, d, d)


@sketch("comma", 0x2C, kind="stem", stem_width=_dot_w)
def _comma(g, W):
    comma_shape(g, 0, 0)


@sketch("colon", 0x3A, kind="stem", stem_width=_dot_w)
def _colon(g, W):
    d = dot_size(g)
    g.rect(0, 0, d, d)
    g.rect(0, XH - d, d, XH)


@glyph("semicolon", 0x3B, kind="stem", stem_width=_dot_w)
def _semicolon(g, W):
    d = dot_size(g)
    comma_shape(g, 0, 0)
    g.rect(0, XH - d, d, XH)


def _exclam_draw(g, W):
    d = dot_size(g)
    g.rect(0, 0, d, d)
    g.rect(d * 0.04, d + max(60, g.S * 0.5), d * 0.96, CAP)


sketch("exclam", 0x21, kind="stem", stem_width=_dot_w)(_exclam_draw)


@glyph("exclamdown", 0xA1, kind="stem", stem_width=_dot_w)
def _exclamdown(g, W):
    g.rot(W, XH / 2, lambda: _exclam_draw(g, W))


@sketch("quotesingle", 0x27, kind="stem", stem_width=lambda p: p.S)
def _quotesingle(g, W):
    g.rect(0, CAP * 0.66, g.S, CAP)


def _quotedbl_w(p):
    return 2 * p.S + 30 + 0.45 * p.S


@glyph("quotedbl", 0x22, kind="stem", stem_width=_quotedbl_w)
def _quotedbl(g, W):
    g.rect(0, CAP * 0.66, g.S, CAP)
    g.rect(W - g.S, CAP * 0.66, W, CAP)


@sketch("hyphen", 0x2D, 300)
def _hyphen(g, W):
    g.rect(0, XH * 0.42, W, XH * 0.42 + g.H * 1.05)


@sketch("endash", 0x2013, 500)
def _endash(g, W):
    g.rect(0, XH * 0.42, W, XH * 0.42 + g.H)


@glyph("emdash", 0x2014, 900)
def _emdash(g, W):
    g.rect(0, XH * 0.42, W, XH * 0.42 + g.H)


def _slash_draw(g, W):
    t = g.dt(W, CAP + 120)
    g.par(W - t / 2, CAP + 20, t / 2, -100, t)


sketch("slash", 0x2F, 360)(_slash_draw)


@glyph("backslash", 0x5C, 360)
def _backslash(g, W):
    g.flipX(W, lambda: _slash_draw(g, W))


@glyph("bar", 0x7C, kind="stem", stem_width=lambda p: p.S)
def _bar(g, W):
    g.rect(0, -180, g.S, CAP + 100)


@glyph("underscore", 0x5F, 500)
def _underscore(g, W):
    g.rect(0, -150, W, -150 + g.H)


def _quote_w(p):
    return _dot_w(p)


def _dblquote_w(p):
    d = _dot_w(p)
    return 2 * d + 0.45 * d + 30


@glyph("quoteright", 0x2019, kind="stem", stem_width=_quote_w)
def _quoteright(g, W):
    quote_right(g, 0)


@glyph("quoteleft", 0x2018, kind="stem", stem_width=_quote_w)
def _quoteleft(g, W):
    quote_left(g, 0)


@glyph("quotesinglbase", 0x201A, kind="stem", stem_width=_quote_w)
def _quotesinglbase(g, W):
    comma_shape(g, 0, 0)


@glyph("quotedblright", 0x201D, kind="stem", stem_width=_dblquote_w)
def _quotedblright(g, W):
    quote_right(g, 0)
    quote_right(g, W - dot_size(g))


@glyph("quotedblleft", 0x201C, kind="stem", stem_width=_dblquote_w)
def _quotedblleft(g, W):
    quote_left(g, 0)
    quote_left(g, W - dot_size(g))


@glyph("quotedblbase", 0x201E, kind="stem", stem_width=_dblquote_w)
def _quotedblbase(g, W):
    comma_shape(g, 0, 0)
    comma_shape(g, W - dot_size(g), 0)


def _ellipsis_w(p):
    d = _dot_w(p)
    return 3 * d + 2 * (0.8 * d + 20)


@glyph("ellipsis", 0x2026, kind="stem", stem_width=_ellipsis_w)
def _ellipsis(g, W):
    d = dot_size(g)
    step = d + 0.8 * d + 20
    for k in range(3):
        g.rect(k * step, 0, k * step + d, d)


@glyph("periodcentered", 0xB7, kind="stem", stem_width=_dot_w)
def _periodcentered(g, W):
    d = dot_size(g)
    ym = XH * 0.5
    g.rect(0, ym - d / 2, d, ym + d / 2)


def _bullet_w(p):
    return 120 + 1.2 * p.S


@glyph("bullet", 0x2022, kind="stem", stem_width=_bullet_w)
def _bullet(g, W):
    ym = XH * 0.5
    g.disc(0, ym - W / 2, W, ym + W / 2)


def _question_draw(g, W):
    d = dot_size(g)
    cx = W / 2
    y0 = CAP * 0.36
    y1 = CAP + OS
    cy = (y0 + y1) / 2
    r = (y1 - y0) / 2
    # The bowl ends at the left edge of the stem. That end is always left
    # of the bottom point, so the bottom point stays (small margin).
    g.ring(0, y0, W, y1, [("l", cy, cy + r * 0.25), ("b", -INF, cx - g.S / 2)], margin=1e-4)
    gap = max(60, g.S * 0.5)
    g.rect(cx - g.S / 2, d + gap, cx + g.S / 2, y0 + g.H * 0.5)
    g.rect(cx - d / 2, 0, cx + d / 2, d)


glyph("question", 0x3F, 500)(_question_draw)


@glyph("questiondown", 0xBF, 500)
def _questiondown(g, W):
    g.rot(W, XH / 2, lambda: _question_draw(g, W))


def _paren_draw(g, W):
    """A tall superellipse arc, cut level at both ends."""
    yb, yt = -140, CAP + 100
    f = 0.70  # the ends sit at 70 % of the ring's half height
    ry = (yt - yb) / 2 / f
    cy = (yt + yb) / 2
    iry = ry - g.H
    si = min(0.999, ((yt - cy) / iry)) ** (2.6 / 2)
    ci = (1 - si * si) ** 0.5
    k = ci ** (2 / 2.6)
    # Choose rx so that the inner end of the arc lands at x = W.
    rx = (W - g.S * k) / (1 - k)
    g.ring(0, cy - ry, 2 * rx, cy + ry, [("r", -INF, INF), ("l", yt, INF), ("l", -INF, yb)])


glyph("parenleft", 0x28, 280)(_paren_draw)


@glyph("parenright", 0x29, 280)
def _parenright(g, W):
    g.flipX(W, lambda: _paren_draw(g, W))


def _bracket_draw(g, W):
    yb, yt = -140, CAP + 100
    g.rect(0, yb, g.S, yt)
    g.rect(0, yt - g.H, W, yt)
    g.rect(0, yb, W, yb + g.H)


glyph("bracketleft", 0x5B, 260)(_bracket_draw)


@glyph("bracketright", 0x5D, 260)
def _bracketright(g, W):
    g.flipX(W, lambda: _bracket_draw(g, W))


def _brace_draw(g, W):
    yb, yt = -140, CAP + 100
    ym = (yt + yb) / 2
    xs = (W - g.S) * 0.45
    g.rect(xs, yb, xs + g.S, yt)
    g.rect(xs, yt - g.H, W, yt)
    g.rect(xs, yb, W, yb + g.H)
    g.rect(0, ym - g.H / 2, xs + g.S, ym + g.H / 2)


glyph("braceleft", 0x7B, 320, floor=3.0)(_brace_draw)


@glyph("braceright", 0x7D, 320, floor=3.0)
def _braceright(g, W):
    g.flipX(W, lambda: _brace_draw(g, W))


@glyph("asterisk", 0x2A, 460)
def _asterisk(g, W):
    import math
    h = 300 + 0.5 * g.S
    cx, yc = W / 2, CAP - h / 2
    # Three bars at 60 degrees: parallelograms with square ends.
    for a in (0.0, math.pi / 3, -math.pi / 3):
        bar_poly(g, cx, yc, h, g.S * 0.85, a)


MATH_Y = CAP * 0.48


@glyph("plus", 0x2B, FW, kind="tab")
def _plus(g, W):
    a = W * 0.38
    g.rect(W / 2 - a, MATH_Y - g.H / 2, W / 2 + a, MATH_Y + g.H / 2)
    g.rect(W / 2 - g.S / 2, MATH_Y - a, W / 2 + g.S / 2, MATH_Y + a)


@glyph("equal", 0x3D, FW, kind="tab")
def _equal(g, W):
    a = W * 0.38
    gap = 0.5 * g.H + 50
    g.rect(W / 2 - a, MATH_Y + gap / 2, W / 2 + a, MATH_Y + gap / 2 + g.H)
    g.rect(W / 2 - a, MATH_Y - gap / 2 - g.H, W / 2 + a, MATH_Y - gap / 2)


def _less_draw(g, W, left=True):
    v = 150 + 0.08 * g.S
    wc, t = chevron_size(g, W * 0.40, v)
    chevron(g, W / 2 - wc / 2, wc, MATH_Y, v, t, left=left)


@glyph("less", 0x3C, FW, kind="tab")
def _less(g, W):
    _less_draw(g, W, True)


@glyph("greater", 0x3E, FW, kind="tab")
def _greater(g, W):
    _less_draw(g, W, False)


def _tilde_shape(g, cx, ym, w, h, s, hh):
    """Two half rings: a hump on the left, a dip on the right."""
    m = cx
    g.ring(cx - w / 2, ym - h, m + s / 2, ym + h, [("l", -INF, ym), ("r", -INF, ym)], ts=s, th=hh)
    g.ring(m - s / 2, ym - h, cx + w / 2, ym + h, [("l", ym, INF), ("r", ym, INF)], ts=s, th=hh)


@glyph("asciitilde", 0x7E, FW, kind="tab")
def _asciitilde(g, W):
    w = W * 0.8
    ts = min(0.8 * g.S, (w - 40) / 3.4)
    tt = 0.62 * g.H * ts / (0.8 * g.S)
    th = tt + 40 + 0.1 * g.S
    _tilde_shape(g, W / 2, MATH_Y, w, th, ts, tt)


def _caret(g, cx, w, yb, yt, t):
    """A small turned V: point up at yt, open end at yb."""
    yc = (yb + yt) / 2
    g.rot(2 * cx, yc, lambda: g.vee(cx - w / 2, cx + w / 2, yt, yb, t))


@glyph("asciicircum", 0x5E, FW, kind="tab")
def _asciicircum(g, W):
    w = W * 0.7
    h = CAP * 0.42
    _caret(g, W / 2, w, CAP - h, CAP, g.dt(w / 2, h))


@glyph("numbersign", 0x23, 620, floor=3.6)
def _numbersign(g, W):
    t = g.dt(0.12 * W, CAP)
    g.par(0.26 * W, 0, 0.38 * W, CAP, t)
    g.par(0.62 * W, 0, 0.74 * W, CAP, t)
    for yc in (CAP * 0.33, CAP * 0.67):
        g.rect(0, yc - g.H / 2, W, yc + g.H / 2)


@glyph("dollar", 0x24, FW, kind="tab")
def _dollar(g, W):
    two_ring_s(g, W, CAP)
    b = g.S * 0.7
    g.rect(W / 2 - b / 2, -90, W / 2 + b / 2, CAP + 90)


@glyph("percent", 0x25, 780, floor=4.6)
def _percent(g, W):
    rw = W * 0.38
    rh = CAP * 0.44 + OS
    s, h = min(g.S, 0.36 * rw), min(g.H, 0.36 * rh)
    g.ring(0, CAP - rh + OS, rw, CAP + OS, ts=s, th=h)
    g.ring(W - rw, -OS, W, rh - OS, ts=s, th=h)
    t = g.dt(W * 0.7, CAP + 2 * OS)
    g.par(W * 0.85 - t / 2, CAP + OS, W * 0.15 + t / 2, -OS, t)


@glyph("ampersand", 0x26, 700, floor=3.4)
def _ampersand(g, W):
    S, H = g.S, g.H
    # Lower bowl, open at the upper right: its right end is the tail.
    ly1 = CAP * 0.60
    lx1 = W * 0.86
    g.ring(0, -OS, lx1, ly1, [("r", CAP * 0.36, INF)])
    # Upper loop: a small closed ring on the bowl, lighter when tight.
    ux0, ux1 = W * 0.10, W * 0.66
    uy0, uy1 = ly1 - H, CAP + OS
    us = min(S, 0.30 * (ux1 - ux0))
    uh = min(H, 0.30 * (uy1 - uy0))
    g.ring(ux0, uy0, ux1, uy1, ts=us, th=uh)
    # The leg: from the left of the loop down to the right foot.
    ya = uy0 + uh
    t = g.dt(W * 0.62, ya)
    g.par(ux0 + us + t * 0.1, ya, W - t / 2, 0, t)


def _at_draw(g, W):
    s, h = g.S * 0.8, g.H * 0.8
    y0, y1 = -150, CAP + 20
    g.ring(0, y0, W, y1, [("r", y0 - 1, CAP * 0.10)], ts=s, th=h)
    # The a inside: a ring and a stem that runs down into a foot.
    ix0, ix1 = W * 0.27, W * 0.70
    iy0, iy1 = CAP * 0.10, CAP * 0.62
    g.ring(ix0, iy0, ix1, iy1, ts=s, th=h)
    g.rect(ix1 - s, iy0, ix1, iy1)
    g.rect(ix1 - s, iy0, W, iy0 + h)


glyph("at", 0x40, 900, floor=6.0)(_at_draw)


@glyph("grave", 0x60, kind="stem", stem_width=lambda p: _accent_box(p, "grave"))
def _grave_sp(g, W):
    _accent(g, "grave", "lc", W / 2)


# ------------------------------------------------------------- symbols

@glyph("Euro", 0x20AC, FW, kind="tab")
def _euro(g, W):
    g.ring(W * 0.14, -OS, W, CAP + OS, [("r", CAP * 0.30, CAP * 0.70)])
    bh = 0.8 * g.H
    gap = 40 + 0.25 * g.H
    g.rect(0, CAP / 2 + gap / 2, W * 0.68, CAP / 2 + gap / 2 + bh)
    g.rect(0, CAP / 2 - gap / 2 - bh, W * 0.64, CAP / 2 - gap / 2)


@glyph("rupeeIndian", 0x20B9, FW, kind="tab")
def _rupee(g, W):
    S, H = g.S, g.H
    g.rect(0, CAP - H, W, CAP)
    y2 = CAP * 0.70
    g.rect(0, y2 - H, W, y2)
    yb = CAP * 0.36
    xb = W * 0.80
    g.ring(-xb * 0.0, yb, xb, CAP, [("l", -INF, INF)])
    g.rect(0, yb, xb / 2 + 1, yb + H)
    t = g.dt(W * 0.6, yb)
    g.par(W * 0.16 + t / 2, yb + H * 0.5, W - t / 2, 0, t)


def _circle_frame(g, W):
    s, h = g.S * 0.62, g.H * 0.62
    g.ring(0, -OS, W, CAP + OS, ts=s, th=h)


@glyph("copyright", 0xA9, 760, floor=5.0)
def _copyright(g, W):
    _circle_frame(g, W)
    s, h = g.S * 0.8, g.H * 0.8
    g.ring(W * 0.28, CAP * 0.24, W * 0.72, CAP * 0.76, [("r", CAP * 0.40, CAP * 0.60)], ts=s, th=h)


@glyph("registered", 0xAE, 760, floor=5.0)
def _registered(g, W):
    _circle_frame(g, W)
    s, h = g.S * 0.8, g.H * 0.8
    x0, x1 = W * 0.33, W * 0.68
    y0, y1 = CAP * 0.22, CAP * 0.78
    g.rect(x0, y0, x0 + s, y1)
    bowl_d(g, x0, CAP * 0.47, x1, y1, s, h)
    t = g.dt((x1 - x0) * 0.5, CAP * 0.25) * 0.8
    g.par((x0 + x1) / 2, CAP * 0.47 + h * 0.5, x1 - t / 2, y0, t)


def _degree_w(p):
    return 150 + 1.1 * p.S


@glyph("degree", 0xB0, kind="stem", stem_width=_degree_w)
def _degree(g, W):
    g.ring(0, CAP - W, W, CAP, ts=g.S * 0.8, th=g.H * 0.8)


def _guil_dims(S):
    v = 105 + 0.2 * S
    d = 0.85 * v
    t = 0.9 * S * (d * d + v * v) ** 0.5 / v
    return v, d, t, d + t, 0.25 * (d + t) + 20


def _guil_w(p, n):
    v, d, t, wc, gap = _guil_dims(p.S)
    return n * wc + (n - 1) * gap


def _guil(g, W, n, left):
    v, d, t, wc, gap = _guil_dims(g.S)
    for k in range(n):
        chevron(g, k * (wc + gap), wc, XH * 0.5, v, t, left=left)


@glyph("guilsinglleft", 0x2039, kind="stem", stem_width=lambda p: _guil_w(p, 1))
def _guilsinglleft(g, W):
    _guil(g, W, 1, True)


@glyph("guilsinglright", 0x203A, kind="stem", stem_width=lambda p: _guil_w(p, 1))
def _guilsinglright(g, W):
    _guil(g, W, 1, False)


@glyph("guillemotleft", 0xAB, kind="stem", stem_width=lambda p: _guil_w(p, 2))
def _guillemotleft(g, W):
    _guil(g, W, 2, True)


@glyph("guillemotright", 0xBB, kind="stem", stem_width=lambda p: _guil_w(p, 2))
def _guillemotright(g, W):
    _guil(g, W, 2, False)


# ------------------------------------------------ Latin-1 letters

@glyph("germandbls", 0xDF, 580, floor=3.6)
def _germandbls(g, W):
    S, H = g.S, g.H
    ym = XH * 0.86
    ux1 = W * 0.80
    uy0 = ym - H
    cu = (uy0 + ASC + OS) / 2
    # Stem from the baseline into the round top-left of the upper bowl.
    g.rect(0, 0, S, cu + 1)
    g.ring(0, uy0, ux1, ASC + OS, [("l", -INF, cu)])
    g.rect(S * 0.5, uy0, W / 2 + 1, ym)
    # Lower bowl: the right half and the bottom, open towards the stem.
    xt = min(1.4 * S + 30, 0.44 * W)
    g.ring(0, -OS, W, ym, [("l", (ym - OS) / 2, INF), ("b", -INF, xt)])


@glyph("AE", 0xC6, 900)
def _AE(g, W):
    xs = W * 0.40
    t = g.dt(xs, CAP)
    g.par(t / 2, 0, xs + t / 2, CAP, t)
    yb = CAP * 0.22
    g.rect(t / 2 + xs * 0.22, yb, xs + g.S, yb + g.H)
    g.rect(xs, 0, xs + g.S, CAP)
    g.rect(xs, CAP - g.H, W, CAP)
    g.rect(xs, 0, W, g.H)
    g.rect(xs, CAP * 0.47, W * 0.94, CAP * 0.47 + g.H)


@glyph("ae", 0xE6, 860)
def _ae(g, W):
    wa = (W + g.S) / 2
    _a(g, wa)
    g.shift(wa - g.S, 0, lambda: _e(g, W - wa + g.S))


@glyph("OE", 0x152, 980)
def _OE(g, W):
    xc = W * 0.48
    g.ring(0, 0, 2 * xc, CAP, [("r", -INF, INF)])
    g.rect(xc - 1, 0, xc + g.S, CAP)
    g.rect(xc - 1, CAP - g.H, W, CAP)
    g.rect(xc - 1, 0, W, g.H)
    g.rect(xc, CAP * 0.47, W * 0.94, CAP * 0.47 + g.H)


@glyph("oe", 0x153, 900)
def _oe(g, W):
    wo = (W + g.S) / 2
    g.ring(0, -OS, wo, XH + OS)
    g.shift(wo - g.S, 0, lambda: _e(g, W - wo + g.S))


@glyph("Oslash", 0xD8, 740)
def _Oslash(g, W):
    _O(g, W)
    t = g.dt(W * 0.84, CAP + 2 * OS + 60)
    g.par(W * 0.08 + t / 2, -OS - 30, W * 0.92 - t / 2, CAP + OS + 30, t)


@glyph("oslash", 0xF8, 560)
def _oslash(g, W):
    _o(g, W)
    t = g.dt(W * 0.84, XH + 2 * OS + 60)
    g.par(W * 0.08 + t / 2, -OS - 30, W * 0.92 - t / 2, XH + OS + 30, t)


@glyph("Eth", 0xD0, 720)
def _Eth(g, W):
    e = W * 0.10
    g.shift(e, 0, lambda: bowl_d(g, 0, 0, W - e, CAP))
    yc = CAP * 0.47
    g.rect(0, yc - g.H / 2, e + g.S + (W - e) * 0.28, yc + g.H / 2)


@glyph("Thorn", 0xDE, 600)
def _Thorn(g, W):
    g.rect(0, 0, g.S, CAP)
    bowl_d(g, 0, CAP * 0.18, W, CAP * 0.82)


@glyph("thorn", 0xFE, 560)
def _thorn(g, W):
    g.rect(0, DESC, g.S, ASC)
    g.ring(0, -OS, W, XH + OS)


@glyph("eth", 0xF0, 560)
def _eth(g, W):
    top = XH * 1.04
    g.ring(0, -OS, W, top + OS)
    # The ascender leans back from the right side of the bowl.
    t = g.dt(W * 0.30, ASC - top * 0.62) * 0.85
    g.par(W - t / 2, top * 0.62, W * 0.62, ASC, t)
    yc = ASC * 0.86
    g.rect(W * 0.40, yc - g.H * 0.36, W * 0.98, yc + g.H * 0.36)


# ------------------------------------------------------------- notdef

@glyph(".notdef", None, 420)
def _notdef(g, W):
    s = 0.5 * g.S + 10
    g.rect(0, 0, W, CAP)
    # The counter runs the other way.
    from loom.geom import polygon, reverse
    g.add(reverse(polygon([(s, s), (W - s, s), (W - s, CAP - s), (s, CAP - s)])))


@glyph("space", (0x20, 0xA0), 260)
def _space(g, W):
    pass


# --------------------------------------------------------------- marks

def accent_gap(S: float, case: str) -> float:
    return (44 + 0.30 * S) if case == "lc" else (36 + 0.24 * S)


def accent_size(S: float, case: str) -> float:
    """Height of the acute, grave and circumflex."""
    h = 150 + 0.35 * S
    return h if case == "lc" else h * 0.78


def _accent_box(p, kind) -> float:
    """Width of the spacing accent glyphs: the mark plus a small margin."""
    h = accent_size(p.S, "lc")
    t = 0.9 * p.S * (1 + (0.55) ** 2) ** 0.5
    return 0.55 * h + t


def _accent(g, kind, case, cx):
    """Draw a mark with its ink centred on x = cx.

    lc marks sit above the x-height, case marks above the cap height.
    The cedilla hangs below the baseline.
    """
    S, H = g.S, g.H
    base_y = (XH if case == "lc" else CAP) + accent_gap(S, case)
    h = accent_size(S, case)
    s = S * 0.9
    hh = H * 0.9
    if kind in ("acute", "grave"):
        dx = 0.55 * h
        t = g.dt(dx, h) * 0.9
        if kind == "acute":
            g.par(cx - dx / 2, base_y, cx + dx / 2, base_y + h, t)
        else:
            g.par(cx + dx / 2, base_y, cx - dx / 2, base_y + h, t)
    elif kind == "circumflex":
        w = 1.6 * h + 0.3 * S
        t = g.dt(w / 2, h) * 0.78
        _caret(g, cx, w, base_y, base_y + h, t)
    elif kind == "dieresis":
        d = S * 0.95
        gap = 0.6 * d + 40
        g.rect(cx - gap / 2 - d, base_y, cx - gap / 2, base_y + d)
        g.rect(cx + gap / 2, base_y, cx + gap / 2 + d, base_y + d)
    elif kind == "tilde":
        ts, tt = S * 0.62, H * 0.55
        th = (tt + 30 + 0.06 * S) if case == "lc" else (tt + 24 + 0.05 * S)
        w = 3.8 * ts + 70
        _tilde_shape(g, cx, base_y + th, w, th, ts, tt)
    elif kind == "ring":
        d = (150 + 0.9 * S) if case == "lc" else (130 + 0.8 * S)
        g.ring(cx - d / 2, base_y, cx + d / 2, base_y + d, ts=S * 0.75, th=H * 0.75)
    elif kind == "cedilla":
        s2 = S * 0.8
        g.rect(cx - s2 / 2, -60, cx + s2 / 2, 12)
        r = 70 + 0.45 * S
        y1 = -40
        y0 = y1 - 2 * r * 0.85
        g.ring(cx - r, y0, cx + r, y1, [("l", -INF, INF)], ts=s2, th=H * 0.8)
    else:
        raise KeyError(kind)


ACCENT_KINDS = ("acute", "grave", "circumflex", "dieresis", "tilde", "ring", "cedilla")


def accent_names() -> list[str]:
    out = []
    for kind in ACCENT_KINDS:
        if kind == "cedilla":
            out.append("cedillacomb")
        else:
            out += [f"{kind}comb", f"{kind}comb.case"]
    return out


def draw_accent(g, name: str) -> None:
    kind = name.replace("comb", "").replace(".case", "")
    case = "case" if name.endswith(".case") else "lc"
    _accent(g, kind, case, 0.0)


# Composites: name -> (unicode, base glyph, accent glyph).
_MARK = {"grave": 0x300, "acute": 0x301, "circumflex": 0x302, "tilde": 0x303,
         "dieresis": 0x308, "ring": 0x30A, "cedilla": 0x327}


def _composites() -> dict[str, tuple[int, str, str]]:
    import unicodedata
    out = {}
    for cp in list(range(0xC0, 0x100)) + [0x178]:
        ch = chr(cp)
        decomp = unicodedata.decomposition(ch).split()
        if len(decomp) != 2 or decomp[0].startswith("<"):
            continue
        base, mark = chr(int(decomp[0], 16)), int(decomp[1], 16)
        kind = next((k for k, v in _MARK.items() if v == mark), None)
        if kind is None:
            continue
        base_name = {"i": "dotlessi"}.get(base, base)
        case = base.isupper()
        acc = "cedillacomb" if kind == "cedilla" else (f"{kind}comb.case" if case else f"{kind}comb")
        name = unicodedata.name(ch)
        out[_agl_name(cp)] = (cp, base_name, acc)
    return out


def _agl_name(cp: int) -> str:
    from fontTools.agl import UV2AGL
    return UV2AGL.get(cp, f"uni{cp:04X}")


COMPOSITES = _composites()


def glyph_order() -> list[str]:
    """.notdef, space, the drawn glyphs by code point, composites, marks."""
    drawn = [n for n in GLYPHS if n not in (".notdef", "space")]
    drawn.sort(key=lambda n: GLYPHS[n].unicodes[0] if GLYPHS[n].unicodes else 0x10FFFF)
    comps = sorted(COMPOSITES, key=lambda n: COMPOSITES[n][0])
    return [".notdef", "space"] + drawn + comps + accent_names()


def cmap() -> dict[int, str]:
    out = {}
    for n, gl in GLYPHS.items():
        for u in gl.unicodes:
            out[u] = n
    for n, (u, _, _) in COMPOSITES.items():
        out[u] = n
    return out


SKETCH_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:!'-–/"
