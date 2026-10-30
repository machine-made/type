"""Heddle glyph table: every glyph as a list of primitives.

Source: reference/heddle-sketch-0.1.js (the glyph table `G`). The
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
under the SIL Open Font License 1.1 (see heddle/OFL.txt), Reserved Font
Name "machine-made". The rest of loom/ is Apache-2.0 (see LICENSE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from loom.geom import INF, open_strokes

UPM = 1000
XH, CAP, ASC, DESC, OS = 520, 700, 730, -210, 10

WGHT = (100, 400, 700, 900)
WDTH = (70, 85, 100, 140)
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


# Width factor of the tabular figures at the master widths: the sketch
# value wdth/100, clamped to 0.8..1.25.
_TAB = ((0.70, 0.80), (0.85, 0.85), (1.00, 1.00), (1.40, 1.25))


def tab_factor(wf: float) -> float:
    """Width factor of the tabular figures: 0.8 at wdth 70, 0.85 at 85,
    1 at 100, 1.25 at 140.

    The sketch value at every master width, linear between them, so the
    variable font gives the same value at every width (the sketch clamps
    wdth/100 to 0.8..1.25).
    """
    for (a, fa), (b, fb) in zip(_TAB, _TAB[1:]):
        if wf <= b or b == _TAB[-1][0]:
            return fa + (wf - a) * (fb - fa) / (b - a)
    return _TAB[-1][1]


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
        if self.sketch:
            # The sketch rule: counters scale with the width, with a floor.
            return max(self.base * p.wf, self.floor * p.S)
        # Glyphs new in 0.1: W = A * wf + B * S. This is linear in both
        # axes, so the variable font gives it exactly at every location
        # (a max() floor would bend between masters). A and B keep the
        # sketch rule at Regular width 100 and at Black width 70.
        a, b = self.linear_width()
        return a * p.wf + b * p.S

    def linear_width(self) -> tuple[float, float]:
        s_reg, s_black, wf_min = Params(400, 100).S, Params(900, 70).S, 0.7
        target = max(self.base * wf_min, self.floor * s_black)
        b = max(0.0, (target - self.base * wf_min) / (s_black - wf_min * s_reg))
        return self.base - b * s_reg, b


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

def hook_span(g, wr):
    """Return (width, terminal stroke) of a hook ring on a stem.

    A hook is half a ring whose one side runs into a stem as wide as
    the ring's stroke (f, t, j). Its visible counter lies between the
    stem and the terminal. 0.2 rule: that counter is at least two
    minimum counter radii wide. The ring gets wider (up to 1.8 stems
    plus the counter), then its terminal gets thinner. At light and
    regular weights nothing changes.
    """
    wr = max(wr, 1.8 * g.S + 2 * g.cmin)
    return wr, min(g.S, wr - g.S - 2 * g.cmin)


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
    # The minimum counter rule for the whole bowl: the bars get the same
    # strokes as the ring, so that the bars do not close the counter.
    s, h = open_strokes((x1 - x0) / 2, (y1 - y0) / 2, s, h, g.cmin)
    g.ring(x0, y0, x1, y1, ts=s, th=h, cmin=0.0)
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


def _j_body(g, W):
    x = W - g.S
    y0 = DESC - OS
    cy = DESC + 80
    # At heavy weights the hook reaches left of the glyph box, so that
    # its counter stays open (0.2; the sketch closed it).
    wr, ts = hook_span(g, W)
    g.ring(W - wr, y0, W, DESC + 170, [("l", cy, INF), ("r", cy, INF)], ts=ts)
    g.rect(x, cy - 1, W, XH)


@sketch("j", 0x6A, kind="stem", stem_width=lambda p: p.S + 120)
def _j(g, W):
    _j_body(g, W)
    x = W - g.S
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
    wr, ts = hook_span(g, 2 * r + 40)
    g.ring(x, ASC + OS - 2 * r, x + wr, ASC + OS, [("l", -INF, c), ("r", -INF, c)], ts=ts)
    g.rect(0, XH - g.H, W, XH)


@sketch("t", 0x74, 330)
def _t(g, W):
    x = W * 0.18
    r = min(130, (W - x) / 2)
    g.rect(x, r - OS - 1, x + g.S, XH + 150)
    c = r - OS
    wr, ts = hook_span(g, 2 * r + 30)
    g.ring(x, -OS, x + wr, 2 * r - OS, [("l", c, INF), ("r", c, INF)], ts=ts)
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
    # The inner c is as light as the frame, so that its counter stays
    # open at Black.
    s, h = g.S * 0.66, g.H * 0.66
    g.ring(W * 0.27, CAP * 0.22, W * 0.73, CAP * 0.78, [("r", CAP * 0.40, CAP * 0.60)], ts=s, th=h)


@glyph("registered", 0xAE, 760, floor=5.0)
def _registered(g, W):
    _circle_frame(g, W)
    # The inner R: as light as the frame; its bowl follows the minimum
    # counter rule (bowl_d), so that it stays open at Black.
    s, h = g.S * 0.62, g.H * 0.62
    x0, x1 = W * 0.33, W * 0.69
    y0, y1 = CAP * 0.21, CAP * 0.79
    ym = CAP * 0.45
    g.rect(x0, y0, x0 + s, y1)
    bowl_d(g, x0, ym, x1, y1, s, h)
    t = g.dt((x1 - x0) * 0.5, ym - y0) * 0.62
    g.par((x0 + x1) / 2, ym + h * 0.5, x1 - t / 2, y0, t)


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


@glyph("Eth", (0xD0, 0x110), 720)
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
    # The ascender leans back from the right side of the bowl. Its foot
    # starts inside the bowl's outer edge at that height, so that no
    # corner pokes out (0.2).
    yb = top * 0.62
    t = g.dt(W * 0.30, ASC - yb) * 0.85
    ry = (top + 2 * OS) / 2
    v = abs((yb - (top / 2)) / ry)
    xr = W / 2 + (W / 2) * (1 - v ** 2.6) ** (1 / 2.6)
    g.par(xr - t / 2 - 2, yb, W * 0.60, ASC, t)
    yc = ASC * 0.84
    g.rect(W * 0.38, yc - g.H * 0.38, W * 0.96, yc + g.H * 0.38)


# ------------------------------------------- Latin Extended-A (drawn, 0.2)

@glyph("dotlessj", 0x237, kind="stem", stem_width=lambda p: p.S + 120)
def _dotlessj(g, W):
    _j_body(g, W)


def _bar_y_asc():
    """Height of the bar of đ ħ: between the x-height and the ascender."""
    return (XH + OS + ASC) / 2 + 15


@glyph("dcroat", 0x111, 600)
def _dcroat(g, W):
    e = 0.10 * W
    wd = W - e
    g.flipX(wd, lambda: _bee(g, wd))
    hb = 0.72 * g.H
    yc = _bar_y_asc()
    g.rect(wd - g.S - 0.24 * wd, yc - hb / 2, W, yc + hb / 2)


@glyph("hbar", 0x127, 600)
def _hbar(g, W):
    e = 0.10 * W
    g.shift(e, 0, lambda: _h(g, W - e))
    hb = 0.72 * g.H
    yc = _bar_y_asc()
    g.rect(0, yc - hb / 2, e + g.S + 0.24 * (W - e), yc + hb / 2)


@glyph("Hbar", 0x126, 720)
def _Hbar(g, W):
    e = 0.06 * W
    g.shift(e, 0, lambda: _H(g, W - 2 * e))
    hb = 0.72 * g.H
    yc = CAP * 0.47 + g.H + (CAP - CAP * 0.47 - g.H) * 0.5
    g.rect(0, yc - hb / 2, W, yc + hb / 2)


@glyph("Tbar", 0x166, 580)
def _Tbar(g, W):
    _T(g, W)
    hb = 0.72 * g.H
    yc = CAP * 0.45
    a = 0.27 * W + 0.5 * g.S
    g.rect(W / 2 - a, yc - hb / 2, W / 2 + a, yc + hb / 2)


@glyph("tbar", 0x167, 330)
def _tbar(g, W):
    _t(g, W)
    hb = 0.72 * g.H
    yc = XH * 0.50
    x = W * 0.18
    g.rect(x - 0.6 * x, yc - hb / 2, x + g.S + 0.6 * x + 0.1 * W, yc + hb / 2)


def _slash_bar(g, cx, cy, length):
    """The bar of Ł ł: a rectangle turned 60 degrees from vertical."""
    import math
    bar_poly(g, cx, cy, length, 0.78 * g.H, math.radians(62))


def _lslash_e(S):
    """How far the bar of ł reaches out of the stem on each side."""
    return 40 + 0.45 * S


@glyph("Lslash", 0x141, 560)
def _Lslash(g, W):
    e = 0.12 * W
    g.shift(e, 0, lambda: _L(g, W - e))
    _slash_bar(g, e + g.S / 2, CAP * 0.42, g.S + 2.4 * e)


@glyph("lslash", 0x142, kind="stem", stem_width=lambda p: p.S + 2 * _lslash_e(p.S))
def _lslash(g, W):
    e = _lslash_e(g.S)
    g.rect(e, 0, e + g.S, ASC)
    _slash_bar(g, e + g.S / 2, ASC * 0.50, g.S + 2.2 * e)


@glyph("kgreenlandic", 0x138, 500)
def _kgreenlandic(g, W):
    g.rect(0, 0, g.S, XH)
    t = g.dt(W * 0.7, XH)
    g.par(g.S * 0.6, XH * 0.30, W - t / 2, XH, t)
    g.par(W * 0.34, XH * 0.52, W - t / 2, 0, t)


def _hook_below(g, x1, y_top, y_bot, wr0):
    """A j hook: the lower half of a ring ending at x1 (its right side under
    a stem that ends at x1). Returns the ring's centre level."""
    wr, ts = hook_span(g, wr0)
    cy = (y_top + y_bot) / 2
    g.ring(x1 - wr, y_bot, x1, y_top, [("l", cy, INF), ("r", cy, INF)], ts=ts)
    return cy


@glyph("Eng", 0x14A, 650)
def _Eng(g, W):
    g.rect(0, 0, g.S, CAP)
    t = g.dt(W, CAP)
    g.poly([(0, CAP), (t, CAP), (W, 0), (W - t, 0)])
    cy = _hook_below(g, W, -10 + 170, DESC - OS, 0.62 * W)
    g.rect(W - g.S, cy - 1, W, CAP)


@glyph("eng", 0x14B, 540)
def _eng(g, W):
    g.rect(0, 0, g.S, XH)
    arch(g, 0, W, XH, XH * 0.4)
    cy = _hook_below(g, W, DESC + 170, DESC - OS, 0.55 * W)
    g.rect(W - g.S, cy - 1, W, XH * 0.5)


@glyph("longs", 0x17F, 280)
def _longs(g, W):
    r = min(150, W / 2 + 10)
    g.rect(0, 0, g.S, ASC - r + 1)
    c = ASC + OS - r
    wr, ts = hook_span(g, 2 * r + 40)
    g.ring(0, ASC + OS - 2 * r, wr, ASC + OS, [("l", -INF, c), ("r", -INF, c)], ts=ts)


# ---------------------------------------------------- symbols (0.2)

@glyph("cent", 0xA2, FW, kind="tab")
def _cent(g, W):
    y1 = XH + 90
    g.ring(W * 0.08, -OS, W * 0.92, y1, [("r", y1 * 0.30, y1 * 0.70)])
    b = g.S * 0.7
    xc = W * 0.5
    g.rect(xc - b / 2, -100, xc + b / 2, y1 + 100)


@glyph("sterling", 0xA3, FW, kind="tab")
def _sterling(g, W):
    S, H = g.S, g.H
    x = W * 0.20
    r = min(0.30 * W + 0.3 * S, (W - x) / 2)
    top = CAP + OS
    c = top - r
    # The stem rises into an arch that ends in a terminal on the right.
    g.rect(x, H - 1, x + S, c + 1)
    wr = max(2 * r, 1.8 * S + 2 * g.cmin)
    g.ring(x, top - 2 * r, x + wr, top, [("l", -INF, c), ("r", -INF, c + 0.15 * r)],
           ts=min(S, wr - S - 2 * g.cmin))
    yb = CAP * 0.42
    g.rect(0, yb - 0.8 * H, x + S + 0.32 * W, yb)
    g.rect(0, 0, W, H)


@glyph("yen", 0xA5, FW, kind="tab")
def _yen(g, W):
    yj = CAP * 0.42
    g.vee(0, W, CAP, yj, g.dt(W / 2, CAP - yj))
    g.rect(W / 2 - g.S / 2, 0, W / 2 + g.S / 2, yj + g.H * 0.2)
    bh = 0.62 * g.H
    gap = 26 + 0.18 * g.H
    a = 0.36 * W
    y1 = yj - 6
    for y in (y1, y1 - bh - gap):
        g.rect(W / 2 - a, y - bh, W / 2 + a, y)


@glyph("section", 0xA7, 500, floor=3.0)
def _section(g, W):
    # An s whose spine is a ring: the top of an s (terminal upper right),
    # a middle ring, the bottom of an s (terminal lower left). The hooks
    # share their inner strokes with the middle ring, as S shares its
    # spine.
    top, bot = CAP + OS, -OS - 90
    T = top - bot
    m0, m1 = bot + 0.27 * T, top - 0.27 * T
    s, h = 0.9 * g.S, 0.9 * g.H
    g.ring(W * 0.04, m0, W * 0.96, m1, ts=s, th=h)
    u0 = m1 - h
    cu = (u0 + top) / 2
    g.ring(W * 0.06, u0, W * 0.98, top, [("r", -INF, cu + (top - cu) * 0.20)], ts=s, th=h)
    l1 = m0 + h
    cl = (bot + l1) / 2
    g.ring(W * 0.02, bot, W * 0.94, l1, [("l", cl - (cl - bot) * 0.20, INF)], ts=s, th=h)


@glyph("paragraph", 0xB6, 600, floor=3.6)
def _paragraph(g, W):
    S, H = g.S, g.H
    x2 = W - S
    # Linear in W and S, so that the variable font does not drift.
    x1 = 0.48 * W - 0.9 * S
    yb = CAP * 0.40
    g.rect(x1, -110, x1 + S, CAP)
    g.rect(x2, -110, W, CAP)
    g.rect(x1, CAP - H, W, CAP)
    # The bowl: half a filled superellipse with a rectangle to the stem.
    cx = (x1 + S) * 0.5
    g.ring(0, yb, 2 * cx, CAP, [("r", -INF, INF)], ts=cx, th=(CAP - yb) / 2, cmin=0.0)
    g.rect(cx - 1, yb, x1 + S, CAP)


MATH_A = 0.38  # half length of the math bars, in figure widths


@glyph("minus", 0x2212, FW, kind="tab")
def _minus(g, W):
    a = W * MATH_A
    g.rect(W / 2 - a, MATH_Y - g.H / 2, W / 2 + a, MATH_Y + g.H / 2)


@glyph("plusminus", 0xB1, FW, kind="tab")
def _plusminus(g, W):
    a = W * MATH_A
    yc = MATH_Y + 0.5 * g.H + 30
    arm = a * 0.92
    g.rect(W / 2 - a, yc - g.H / 2, W / 2 + a, yc + g.H / 2)
    g.rect(W / 2 - g.S / 2, yc - arm, W / 2 + g.S / 2, yc + arm)
    yb = yc - arm - 40 - 0.3 * g.H
    g.rect(W / 2 - a, yb - g.H, W / 2 + a, yb)


@glyph("multiply", 0xD7, FW, kind="tab")
def _multiply(g, W):
    import math
    L = 2 * W * MATH_A * 0.92
    for ang in (math.pi / 4, -math.pi / 4):
        bar_poly(g, W / 2, MATH_Y, L, 0.95 * g.S, ang)


@glyph("divide", 0xF7, FW, kind="tab")
def _divide(g, W):
    a = W * MATH_A
    g.rect(W / 2 - a, MATH_Y - g.H / 2, W / 2 + a, MATH_Y + g.H / 2)
    d = dot_size(g)
    gap = 36 + 0.25 * g.H
    for y in (MATH_Y + g.H / 2 + gap, MATH_Y - g.H / 2 - gap - d):
        g.rect(W / 2 - d / 2, y, W / 2 + d / 2, y + d)


# Numerators and denominators: the figures, drawn at FRAC_K of their size
# with a stroke of 0.62 S + 8, so that they keep their colour.
FRAC_K = 0.58
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
NUMR_W = 330


def _small_figure(name, raise_y):
    def draw(g, W):
        from loom.geom import Canvas
        k = FRAC_K
        s_v = (0.62 * g.S + 8) / k
        sub = Canvas(s_v, 0.84 * s_v)
        GLYPHS[name].draw(sub, W / k)
        for c in sub.contours:
            g.add([(x * k, y * k + raise_y, on) for x, y, on in c])
    return draw


def _fraction_draw(g, W):
    # The fraction slash reaches out of its box on both sides, so that
    # numerator and denominator tuck under it.
    ov = 0.55 * W
    t = g.dt(W + 2 * ov, CAP) * 0.62
    g.par(W + ov - t / 2, CAP, -ov + t / 2, 0, t)


glyph("fraction", 0x2044, 120, kind="tab")(_fraction_draw)

for _i, _fig in enumerate(FIGURES):
    glyph(f"{_fig}.numr", None, NUMR_W, kind="tab")(_small_figure(_fig, CAP * (1 - FRAC_K)))
    glyph(f"{_fig}.dnom", None, NUMR_W, kind="tab")(_small_figure(_fig, 0.0))


# ------------------------------------------------------------- notdef

@glyph(".notdef", None, 420)
def _notdef(g, W):
    s = 0.5 * g.S + 10
    g.rect(0, 0, W, CAP)
    # The counter runs the other way.
    from loom.geom import polygon, reverse
    g.add(reverse(polygon([(s, s), (W - s, s), (W - s, CAP - s), (s, CAP - s)])))


@sketch("space", (0x20, 0xA0), 260)
def _space(g, W):
    pass


# --------------------------------------------------------------- marks
#
# 0.2: marks are lighter and smaller than in 0.1, so that they do not
# crowd the letters at Black. Their stroke grows more slowly than the
# stem (mark_stem). Capital marks stay below the typo ascender (950).
# Narrow bases (dotless i, I, l, dotless j) get ".narrow" marks that
# are no wider than the base plus 1.45 sidebearings, so that ï Ï Ĩ ĺ do
# not widen their base.

def mark_stem(S: float) -> float:
    """Stroke of the marks: 0.62 S + 12 (S at Thin, 0.69 S at Black)."""
    return 0.62 * S + 12


def accent_gap(S: float, case: str) -> float:
    """Gap between the x-height (or cap height) and the mark."""
    return (40 + 0.22 * S) if case == "lc" else (30 + 0.16 * S)


def accent_size(S: float, case: str) -> float:
    """Height of the acute, grave, circumflex and caron."""
    h = 140 + 0.20 * S
    return h if case == "lc" else h * 0.72


def narrow_width(S: float) -> float:
    """Largest ink width of a .narrow mark: the stem plus 1.45 sidebearings."""
    return S + 1.45 * (22 + 0.22 * S)


def _accent_box(p, kind) -> float:
    """Width of the spacing grave (U+0060): the mark plus a small margin."""
    h = accent_size(p.S, "lc")
    sm = mark_stem(p.S)
    dx = 0.6 * h
    t = 0.9 * sm * (dx * dx + h * h) ** 0.5 / h
    return dx + t


def _slant_dims(sm, h, wmax=None, k=0.6):
    """(dx, t) of an acute: run dx over height h, horizontal width t.

    The ink is dx + t wide. With wmax, dx shrinks until the ink fits.
    """
    import math
    dx = k * h
    t = 0.9 * sm * math.hypot(dx, h) / h
    if wmax is not None and dx + t > wmax:
        for _ in range(6):
            dx = max(0.12 * h, wmax - t)
            t = 0.9 * sm * math.hypot(dx, h) / h
    return dx, t


def _accent(g, kind, case, cx, narrow=False):
    """Draw a mark with its ink centred on x = cx.

    lc marks sit above the x-height, case marks above the cap height.
    Marks below the baseline (cedilla, ogonek, comma) and the vertical
    caron (caroncomb.alt) have their own rules.
    """
    import math
    S, H = g.S, g.H
    sm = mark_stem(S)
    hm = 0.84 * sm
    base_y = (XH if case == "lc" else CAP) + accent_gap(S, case)
    h = accent_size(S, case)
    wmax = narrow_width(S) if narrow else None

    def fit(w):
        return min(w, wmax) if wmax is not None else w

    if kind in ("acute", "grave"):
        dx, t = _slant_dims(sm, h, wmax)
        if kind == "acute":
            g.par(cx - dx / 2, base_y, cx + dx / 2, base_y + h, t)
        else:
            g.par(cx + dx / 2, base_y, cx - dx / 2, base_y + h, t)
    elif kind == "hungarumlaut":
        dx, t = _slant_dims(sm * 0.9, h, None, 0.5)
        sep = t + 0.45 * t + 24
        for o in (-sep / 2, sep / 2):
            g.par(cx + o - dx / 2, base_y, cx + o + dx / 2, base_y + h, t)
    elif kind in ("circumflex", "caron"):
        w = fit(1.5 * h + 0.3 * sm)
        t = 0.9 * sm * math.hypot(w / 2, h) / h * 0.8
        if kind == "circumflex":
            _caret(g, cx, w, base_y, base_y + h, t)
        else:
            g.vee(cx - w / 2, cx + w / 2, base_y + h, base_y, t)
    elif kind == "dieresis":
        d = 0.95 * sm
        gap = 0.45 * d + 30
        if wmax is not None and 2 * d + gap > wmax:
            gap = 0.3 * wmax
            d = min(d, (wmax - gap) / 2)
        g.rect(cx - gap / 2 - d, base_y, cx - gap / 2, base_y + d)
        g.rect(cx + gap / 2, base_y, cx + gap / 2 + d, base_y + d)
    elif kind == "dotaccent":
        d = 0.95 * sm
        g.rect(cx - d / 2, base_y, cx + d / 2, base_y + d)
    elif kind == "tilde":
        ts, tt = 0.78 * sm, 0.62 * sm
        amp = (tt + 18 + 0.04 * sm) if case == "lc" else (tt + 14 + 0.03 * sm)
        w = fit(5.0 * amp + 0.4 * ts)
        _tilde_shape(g, cx, base_y + amp, w, amp, ts, tt)
    elif kind == "macron":
        w = fit(0.9 * h + 0.6 * sm)
        g.rect(cx - w / 2, base_y, cx + w / 2, base_y + 0.8 * hm)
    elif kind == "breve":
        w = fit(1.25 * h + 0.3 * sm)
        hb = 0.62 * h
        cy = base_y + hb
        g.ring(cx - w / 2, base_y, cx + w / 2, base_y + 2 * hb,
               [("l", cy, INF), ("r", cy, INF)], ts=0.8 * sm, th=0.7 * sm)
    elif kind == "ring":
        if case == "lc":
            w, hr = 150 + 0.6 * sm, 150 + 0.6 * sm
        else:
            w, hr = 140 + 0.55 * sm, 110 + 0.45 * sm
        g.ring(cx - w / 2, base_y, cx + w / 2, base_y + hr, ts=0.75 * sm, th=0.62 * sm)
    elif kind == "cedilla":
        s2 = 0.85 * sm
        g.rect(cx - s2 / 2, -60, cx + s2 / 2, 12)
        r = 62 + 0.45 * sm
        y1 = -40
        y0 = y1 - 2 * r * 0.85
        g.ring(cx - r, y0, cx + r, y1, [("l", -INF, INF)], ts=s2, th=0.8 * hm)
    elif kind == "ogonek":
        # The attachment point is the origin: the tail hangs from the
        # base's lower right and curls back to the right.
        wo = 120 + 0.6 * sm
        ho = 2 * (100 + 0.32 * sm)
        y1 = 0.9 * hm
        cy = y1 - ho / 2
        x1 = 0.0
        g.ring(x1 - wo, y1 - ho, x1, y1, [("r", cy - 0.45 * ho / 2, INF)],
               ts=0.85 * sm, th=0.72 * sm)
    elif kind == "commaaccent":
        d = 0.9 * sm
        top = -(36 + 0.16 * S)
        comma_shape_d(g, cx - d * 0.55, top - d, d)
    elif kind == "commaturnedabove":
        d = 0.9 * sm
        y = base_y
        # A comma turned by 180 degrees: the square on top.
        g.rot(2 * cx, y + d * 1.0, lambda: comma_shape_d(g, cx - d * 0.55, y + d * 0.95, d))
    elif kind == "caronalt":
        # The vertical caron of ď ľ ť Ľ: a comma with its top at y = 0,
        # its ink starting at x = 0.
        d = 0.85 * sm
        comma_shape_d(g, 0, -d, d, tail=0.9)
    else:
        raise KeyError(kind)


def comma_shape_d(g, x, y, d, tail=1.1):
    """A comma of size d with its square at (x, y)."""
    g.rect(x, y, x + d, y + d)
    g.poly([(x + d * 0.25, y), (x + d, y), (x + d * 0.55, y - d * tail), (x + d * 0.1, y - d * tail)])


TOP_KINDS = ("grave", "acute", "circumflex", "tilde", "macron", "breve", "dotaccent",
             "dieresis", "ring", "hungarumlaut", "caron")
NARROW_KINDS = ("grave", "acute", "circumflex", "tilde", "macron", "breve", "dieresis")
BOTTOM_KINDS = ("cedilla", "ogonek", "commaaccent")


def accent_names() -> list[str]:
    out = []
    for kind in TOP_KINDS:
        out += [f"{kind}comb", f"{kind}comb.case"]
        if kind in NARROW_KINDS:
            out += [f"{kind}comb.narrow", f"{kind}comb.case.narrow"]
    out += [f"{k}comb" for k in BOTTOM_KINDS]
    out += ["commaturnedabovecomb", "caroncomb.alt"]
    return out


def mark_kind(name: str) -> tuple[str, str, bool]:
    """Return (kind, case, narrow) of a mark glyph name."""
    if name == "caroncomb.alt":
        return "caronalt", "lc", False
    parts = name.split(".")
    kind = parts[0][: -len("comb")]
    return kind, ("case" if "case" in parts else "lc"), ("narrow" in parts)


def draw_accent(g, name: str) -> None:
    kind, case, narrow = mark_kind(name)
    _accent(g, kind, case, 0.0, narrow)


# ------------------------------------------------------------ composites
#
# A composite is a base glyph plus marks, or a row of glyphs (Ĳ, ŉ, ½).
# loom/build.py places the parts (see build.composite).

@dataclass(frozen=True)
class Comp:
    cp: int
    base: str
    # (mark glyph, place). Places: "top" (centred on the base's ink, or
    # on its top anchor), "top-asc" (a capital mark lifted to the
    # ascender: ĥ ĺ), "bottom" (centred below), "ogonek" (at the base's
    # lower right), "right" (the vertical caron, right of the stem),
    # "dot" (the middle dot of Ŀ ŀ).
    marks: tuple = ()
    # A row of glyphs (the base is the first one), set by advance.
    row: tuple = ()


_TOP = {0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde", 0x304: "macron",
        0x306: "breve", 0x307: "dotaccent", 0x308: "dieresis", 0x30A: "ring",
        0x30B: "hungarumlaut", 0x30C: "caron"}
_BOTTOM = {0x327: "cedilla", 0x328: "ogonek", 0x326: "commaaccent"}
# Bases with an ascender: a top mark is a capital mark, lifted.
ASCENDER_BASES = {"h", "l", "k", "b", "d"}
# Narrow bases: top marks are .narrow marks.
NARROW_BASES = {"dotlessi", "I", "l", "dotlessj"}
# Letters whose cedilla is a comma below (Latvian, Romanian).
_COMMA_BELOW = {0x122, 0x136, 0x137, 0x13B, 0x13C, 0x145, 0x146, 0x156, 0x157}
# Vertical caron (ď ľ ť Ľ).
_CARON_ALT = {0x10F, 0x13D, 0x13E, 0x165}


def _composites() -> dict[str, Comp]:
    import unicodedata
    out = {}
    cps = list(range(0xC0, 0x100)) + list(range(0x100, 0x180)) + [0x218, 0x219, 0x21A, 0x21B]
    for cp in cps:
        ch = chr(cp)
        decomp = unicodedata.decomposition(ch).split()
        if len(decomp) != 2 or decomp[0].startswith("<"):
            continue
        base, mark = chr(int(decomp[0], 16)), int(decomp[1], 16)
        if base not in "".join(chr(u) for u in cmap_drawn()):
            continue
        case = base.isupper()
        base_name = _agl_name(ord(base))
        if cp == 0x123:  # ģ: a turned comma above
            out[_agl_name(cp)] = Comp(cp, "g", (("commaturnedabovecomb", "top"),))
            continue
        if mark in _TOP:
            kind = _TOP[mark]
            if cp in _CARON_ALT:
                out[_agl_name(cp)] = Comp(cp, base_name, (("caroncomb.alt", "right"),))
                continue
            if base == "i":
                base_name = "dotlessi"
            elif base == "j":
                base_name = "dotlessj"
            place = "top"
            mark_name = f"{kind}comb"
            if case or base_name in ASCENDER_BASES:
                mark_name += ".case"
                place = "top" if case else "top-asc"
            if base_name in NARROW_BASES and kind in NARROW_KINDS:
                mark_name += ".narrow"
            out[_agl_name(cp)] = Comp(cp, base_name, ((mark_name, place),))
        elif mark in _BOTTOM:
            kind = _BOTTOM[mark]
            if cp in _COMMA_BELOW:
                kind = "commaaccent"
            place = "ogonek" if kind == "ogonek" else "bottom"
            out[_agl_name(cp)] = Comp(cp, base_name, ((f"{kind}comb", place),))
    # Compatibility letters: rows of glyphs, and the middle dot.
    out["IJ"] = Comp(0x132, "I", row=("I", "J"))
    out["ij"] = Comp(0x133, "i", row=("i", "j"))
    out["napostrophe"] = Comp(0x149, "quoteright", row=("quoteright", "n"))
    out["Ldot"] = Comp(0x13F, "L", (("periodcentered", "dot"),))
    out["ldot"] = Comp(0x140, "l", (("periodcentered", "dot"),))
    # Fractions.
    out["onehalf"] = Comp(0xBD, "one.numr", row=("one.numr", "fraction", "two.dnom"))
    out["onequarter"] = Comp(0xBC, "one.numr", row=("one.numr", "fraction", "four.dnom"))
    out["threequarters"] = Comp(0xBE, "three.numr", row=("three.numr", "fraction", "four.dnom"))
    # Spacing marks: one mark, centred in its own advance.
    for cp, mark in SPACING_MARKS.items():
        out[_agl_name(cp)] = Comp(cp, mark, row=(mark,))
    return out


# Spacing forms of the marks (the spacing grave U+0060 is drawn).
SPACING_MARKS = {
    0xA8: "dieresiscomb", 0xAF: "macroncomb", 0xB4: "acutecomb", 0xB8: "cedillacomb",
    0x2C6: "circumflexcomb", 0x2C7: "caroncomb", 0x2D8: "brevecomb", 0x2D9: "dotaccentcomb",
    0x2DA: "ringcomb", 0x2DB: "ogonekcomb", 0x2DC: "tildecomb", 0x2DD: "hungarumlautcomb",
}


def cmap_drawn() -> list[int]:
    return [u for gl in GLYPHS.values() for u in gl.unicodes]


def _agl_name(cp: int) -> str:
    from fontTools.agl import UV2AGL
    return UV2AGL.get(cp, f"uni{cp:04X}")


COMPOSITES = _composites()


def glyph_order() -> list[str]:
    """.notdef, space, the drawn glyphs by code point, composites, marks."""
    drawn = [n for n in GLYPHS if n not in (".notdef", "space")]
    drawn.sort(key=lambda n: (GLYPHS[n].unicodes[0] if GLYPHS[n].unicodes else 0x10FFFF, n))
    comps = sorted(COMPOSITES, key=lambda n: COMPOSITES[n].cp)
    return [".notdef", "space"] + drawn + comps + accent_names()


def cmap() -> dict[int, str]:
    out = {}
    for n, gl in GLYPHS.items():
        for u in gl.unicodes:
            out[u] = n
    for n, c in COMPOSITES.items():
        out[c.cp] = n
    return out


SKETCH_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:!'-–/"
