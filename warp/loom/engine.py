"""The Warp pen model: a Python port of the sketch 0.2 engine.

Source: reference/warp-sketch-0.2.js (parameters, nib, hull, centre-line
paths, glyph builder, sweep, teardrops, compose). Font units, y up,
1000 units per em.

Every glyph is a set of centre-lines ("strokes"). Each stroke is swept
by a nib: a superellipse `a` long and `b` thick, turned by the pen angle.
Pressure (0..1) on each node sets the nib length between b (hairline)
and A (stem). With the nib level, verticals come out thick and
horizontals thin: vertical stress comes out of the pen. The ink is the
union of the convex hulls of consecutive nib positions, plus discs,
teardrops and bracket fillets. This module returns those polygons; the
outline step (loom/outline.py) unions them and fits curves.

The port follows the engine line by line, so that the advances and the
ink are the same as in the sketch (tests/test_warp.py runs the engine in
node and compares). Additions for the font are marked "font:".

Apache-2.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

PI = math.pi
TAU = 2 * PI


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    """Smootherstep: unhurried swells, no abrupt pressure changes."""
    return t * t * t * (t * (6 * t - 15) + 10)


def _sign(v):
    return (v > 0) - (v < 0)


# ------------------------------------------------------------ parameters

DEFAULTS = dict(contrast=9, stress=0, xh=412, serif=1, bracket=0.2, ball=1,
                opsz=12, ital=False, stem=84,
                # font: multipliers for the bold styles (1 = the sketch).
                serifw=1.0, width=1.0)


@dataclass(frozen=True)
class Params:
    o: dict
    k: float
    A: float
    B: float
    S: float
    ratio: float
    ang: float
    xh: float
    cap: float
    asc: float
    desc: float
    os: float
    axis: float
    sl: float
    bk: float
    bd: float
    sb: float
    wd: float
    ital: bool
    slant: float

    def but(self, **kw) -> "Params":
        return replace(self, **kw)


def params(**kw) -> Params:
    o = dict(DEFAULTS)
    o.update(kw)
    k = clamp(math.log(o["opsz"] / 6) / math.log(72 / 6), 0, 1)       # 0 at 6 pt, 1 at 72 pt
    A = o["stem"] * (1.06 - 0.12 * k)                                    # stems a little lighter at display sizes
    ratio = 1 + (o["contrast"] - 1) * (0.34 + 0.66 * min(1, k / 0.72))   # full contrast from opsz 36 up
    B = max(A / ratio, 5)
    S = max(B * 1.05, A * (0.27 - 0.16 * k)) * o["serifw"]              # serif thickness, never thinner than hairline
    return Params(
        o=o, k=k, A=A, B=B, S=S, ratio=ratio,
        ang=o["stress"] * PI / 180,
        xh=o["xh"] + (1 - k) * 22, cap=670, asc=760, desc=-250, os=11, axis=250,
        sl=A * 0.74 * o["serif"],
        bk=o["bracket"],
        bd=A * (0.8 + 0.14 * (1 - k)) * o["ball"] if o["ball"] > 0 else 0,
        sb=30 + (1 - k) * 18,
        wd=(1 + (1 - k) * 0.04) * o["width"],
        ital=bool(o["ital"]), slant=0.25 if o["ital"] else 0,
    )


# ------------------------------------------------------------------- nib

NK = 28


def nib(a, b, ang, ne):
    """Superellipse nib, counter-clockwise polygon."""
    v = []
    c, s = math.cos(ang), math.sin(ang)
    for i in range(NK):
        t = i / NK * TAU
        ct, st = math.cos(t), math.sin(t)
        x = a / 2 * _sign(ct) * abs(ct) ** (2 / ne)
        y = b / 2 * _sign(st) * abs(st) ** (2 / ne)
        v.append((x * c - y * s, x * s + y * c))
    return v


def hull(P):
    """Monotone chain, counter-clockwise."""
    P = sorted(P, key=lambda q: (q[0], q[1]))

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    lo.pop()
    up.pop()
    return lo + up


def area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        s += a[0] * b[1] - b[0] * a[1]
    return s / 2


def ccw(poly):
    return list(reversed(poly)) if area(poly) < 0 else list(poly)


# ------------------------------------------------------ centre-line paths

def se_pt(cx, cy, rx, ry, t, e):
    c, s = math.cos(t), math.sin(t)
    return (cx + rx * _sign(c) * abs(c) ** (2 / e), cy + ry * _sign(s) * abs(s) ** (2 / e))


class Path:
    def __init__(self, g, x, y, pr=None):
        self.g = g
        self.pts = [[x, y, 1 if pr is None else pr]]
        self.nodes = [(x, y)]

    @property
    def last(self):
        return self.pts[-1]

    def l(self, x, y, pr=None):  # noqa: E741
        x0, y0, p0 = self.last
        pr = p0 if pr is None else pr
        n = 1 if p0 == pr else max(2, math.ceil(math.hypot(x - x0, y - y0) / 10))
        for i in range(1, n + 1):
            t = i / n
            u = smooth(t)
            self.pts.append([lerp(x0, x, t), lerp(y0, y, t), lerp(p0, pr, u)])
        self.nodes.append((x, y))
        return self

    def c(self, x1, y1, x2, y2, x, y, pr=None):
        x0, y0, p0 = self.last
        pr = p0 if pr is None else pr
        ln = math.hypot(x1 - x0, y1 - y0) + math.hypot(x2 - x1, y2 - y1) + math.hypot(x - x2, y - y2)
        n = max(6, math.ceil(ln / 7))
        for i in range(1, n + 1):
            t = i / n
            m = 1 - t
            self.pts.append([
                m * m * m * x0 + 3 * m * m * t * x1 + 3 * m * t * t * x2 + t * t * t * x,
                m * m * m * y0 + 3 * m * m * t * y1 + 3 * m * t * t * y2 + t * t * t * y,
                lerp(p0, pr, smooth(t)),
            ])
        self.nodes.append((x, y))
        return self

    def arc(self, cx, cy, rx, ry, t0, t1, pr=None, e=None):
        """Continue along a superellipse from angle t0 to t1."""
        e = e or self.g.ex
        p0 = self.last[2]
        pr = p0 if pr is None else pr
        n = max(6, math.ceil(abs(t1 - t0) * max(rx, ry) / 7))
        for i in range(1, n + 1):
            t = i / n
            q = se_pt(cx, cy, rx, ry, lerp(t0, t1, t), e)
            self.pts.append([q[0], q[1], lerp(p0, pr, smooth(t))])
        self.nodes.append(se_pt(cx, cy, rx, ry, t1, e))
        return self

    def draw(self, opts=None):
        self.g.strokes.append({"pts": self.pts, "nodes": self.nodes, "o": dict(opts or {})})
        return self


# ---------------------------------------------------------- glyph builder

class Builder:
    """The `g` object of the engine: metrics plus drawing helpers."""

    def __init__(self, p: Params):
        self.p = p
        self.A, self.B, self.S, self.sl, self.bk, self.bd = p.A, p.B, p.S, p.sl, p.bk, p.bd
        self.X, self.C, self.AS, self.D, self.o = p.xh, p.cap, p.asc, p.desc, p.os
        self.ex = 2.1
        self.strokes: list = []
        self.balls: list = []
        self.drops: list = []
        self.fills: list = []
        # The sketch reads `p.lc`, which its params() never sets: the
        # lowercase wedge head serif is never drawn. The port keeps that.
        self.lc = False
        self.h = self.A / 2
        self.yt = self.X + self.o - self.B / 2
        self.yb = -self.o + self.B / 2

    def P(self, x, y, pr=None):
        return Path(self, x, y, pr)

    def E(self, cx, cy, rx, ry, t0, pr=None, e=None):
        q = se_pt(cx, cy, rx, ry, t0, e or self.ex)
        return Path(self, q[0], q[1], pr)

    def pt(self, cx, cy, rx, ry, t, e=None):
        return se_pt(cx, cy, rx, ry, t, e or self.ex)

    def ring(self, cx, cy, rx, ry, pr=None, e=None):
        pr = 1 if pr is None else pr
        return self.E(cx, cy, rx, ry, 0, pr, e).arc(cx, cy, rx, ry, 0, TAU, pr, e).draw({"closed": True})

    def stem(self, x, y0, y1, pr=None, o=None):
        pr = 1 if pr is None else pr
        return self.P(x, y0 + self.B / 2, pr).l(x, y1 - self.B / 2, pr).draw(o)

    def hair(self, x0, y0, x1, y1, o=None):
        return self.P(x0, y0, 0).l(x1, y1, 0).draw(o)

    def bar(self, x0, x1, y):
        """Horizontal hairline, ink x0..x1, centred on y."""
        a, b = min(x0, x1), max(x0, x1)
        return self.P(a + self.B / 2, y, 0).l(b - self.B / 2, y, 0).draw({"role": "bar"})

    def dot(self, x, y, d=None):
        d = self.bd if d is None else d
        if d > 0:
            self.balls.append((x, y, d / 2))

    def ball(self, x, y, d=None):
        """A terminal: a teardrop that grows out of the nearest stroke end."""
        d = self.bd if d is None else d
        if d > 0:
            self.drops.append((x, y, d / 2))

    def fill(self, pts, role=None):
        self.fills.append({"pts": pts, "role": role or "fill"})

    def serif(self, x, y, dir, side, w=None, ln=None):
        """Serif on a stem of width w centred at x; y = outer edge.

        dir=+1 foot (serif rises from y), -1 head (hangs from y).
        """
        w = self.A if w is None else w
        ln = self.sl if ln is None else ln
        if ln <= 1:
            return
        S, hw = self.S, w / 2
        cy = y + dir * S / 2
        L = x if side == "r" else x - hw - ln
        R = x if side == "l" else x + hw + ln
        if dir < 0 and side == "l" and self.lc:
            dw = ln * 0.3
            self.P(L + S * 0.3, cy - dw, 0).l(x, cy, 0).draw({"a": S * 0.9, "b": S, "ne": 5, "role": "serif"})
            self.fill([(L + S * 0.2, cy - dw - S * 0.3), (x, y - S * 1.1), (x, y), (L + S * 0.2, cy - dw + S * 0.45)], "bracket")
        else:
            self.P(L + S / 2, cy, 0).l(R - S / 2, cy, 0).draw({"a": S, "b": S, "ne": 7, "role": "serif"})
        bh = self.bk * ln * 1.0
        bl = self.bk * ln * 0.85
        if bh > 2:
            def br(xe, sx):
                pts = [(xe - sx * 2, y + dir * S * 0.5), (xe - sx * 2, y + dir * (S + bh))]
                c = (xe, y + dir * S)
                e = (xe + sx * bl, y + dir * S)
                s0 = (xe, y + dir * (S + bh))
                for i in range(11):
                    t = i / 10
                    m = 1 - t
                    pts.append((m * m * s0[0] + 2 * m * t * c[0] + t * t * e[0],
                                m * m * s0[1] + 2 * m * t * c[1] + t * t * e[1]))
                pts.append((xe + sx * bl, y + dir * S * 0.5))
                self.fill(pts, "bracket")
            if side != "r":
                br(x - hw, -1)
            if side != "l":
                br(x + hw, 1)

    def beak(self, x, y, dir, ln=None):
        ln = self.A * 1.25 if ln is None else ln
        S = self.S * 0.95
        self.P(x - S / 2, y, 0.15).l(x - S / 2, y + dir * ln, 0).draw({"a": S * 1.05, "b": S, "ne": 4, "role": "serif"})

    # font: draw another glyph function into this glyph, moved by (dx, dy).
    def use(self, fn, dx=0.0, dy=0.0):
        return self.use_map(fn, lambda x, y: (x + dx, y + dy))

    # font: draw a glyph function with its centre-lines mapped by f(x, y).
    # The pen is not mapped: a rotated copy keeps the level nib.
    def use_map(self, fn, f):
        n = (len(self.strokes), len(self.balls), len(self.drops), len(self.fills))
        ret = fn(self)
        for s in self.strokes[n[0]:]:
            s["pts"] = [[*f(x, y), pr] for x, y, pr in s["pts"]]
            s["nodes"] = [f(x, y) for x, y in s["nodes"]]
        self.balls[n[1]:] = [(*f(x, y), r) for x, y, r in self.balls[n[1]:]]
        self.drops[n[2]:] = [(*f(x, y), r) for x, y, r in self.drops[n[2]:]]
        for fl in self.fills[n[3]:]:
            fl["pts"] = [f(x, y) for x, y in fl["pts"]]
        return ret


# ---------------------------------------------------------------- glyphs

@dataclass
class GlyphDef:
    fn: object
    cap: bool = False
    lc: bool = False
    l: float | None = None  # noqa: E741
    r: float | None = None
    adv: float | None = None
    empty: bool = False
    upright: bool = False
    bigop: bool = False
    slant: float | None = None
    yc: float | None = None
    greek: bool = False
    extra: dict = field(default_factory=dict)


def flags(ch: str) -> dict:
    """The engine's flags: `cap` for /^[A-ZΓΔΣΩ]$/, `lc` for /^[a-zﬁﬂﬀ]$/.

    font: the new Greek capitals count as capitals too (Θ Λ Ξ Π Φ Ψ), so
    that they get the same lighter stem and narrower frame.
    """
    cap = len(ch) == 1 and (("A" <= ch <= "Z") or ch in "ΓΔΣΩΘΛΞΠΦΨ")
    lc = len(ch) == 1 and (("a" <= ch <= "z") or ch in "ﬁﬂﬀ")
    return {"cap": cap, "lc": lc}


# ------------------------------------------------------------------ sweep

def nib_for(p: Params, o: dict, pr: float):
    b = o["b"] if o.get("b") is not None else p.B
    a = o["a"] if o.get("a") is not None else (b + (p.A - b) * clamp(pr, 0, 1))
    ang = 0 if o.get("role") == "rule" else p.ang + (o.get("turn") or 0)
    return nib(a, b, ang, o.get("ne") or 3.2)


def circle(x, y, r):
    v = []
    for i in range(40):
        t = i / 40 * TAU
        v.append((x + r * math.cos(t), y + r * math.sin(t)))
    return v


def teardrop(g: Builder, x, y, r):
    """Find the stroke end this terminal belongs to; grow a drop out of it."""
    best = None
    bd = r * 3.2
    for s in g.strokes:
        P = s["pts"]
        for end in (0, len(P) - 1):
            q = P[end]
            d = math.hypot(q[0] - x, q[1] - y)
            if d < bd:
                bd = d
                best = (P, end)
    if best is None:
        return circle(x, y, r), True
    P, end = best
    dir = 1 if end == 0 else -1
    acc = 0.0
    i = end
    tip = P[end]
    while 0 <= i + dir < len(P) and acc < r * 2.1:
        a, b = P[i], P[i + dir]
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        i += dir
        tip = P[i]
    ux, uy = x - tip[0], y - tip[1]
    ul = math.hypot(ux, uy) or 1
    cx, cy = x + ux / ul * r * 0.12, y + uy / ul * r * 0.12
    pts = circle(cx, cy, r) + [(tip[0], tip[1]),
                               (tip[0] + (cx - tip[0]) * 0.35, tip[1] + (cy - tip[1]) * 0.35)]
    return hull(pts), False


@dataclass
class Swept:
    polys: list
    strokes: list
    adv: float
    dx: float
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    ret: object = None
    yc: float = 0.0
    sl: float = 0.0
    p: object = None


def compose(d: GlyphDef, p: Params, mods: dict | None = None) -> Swept:
    """Sweep a glyph. Returns its polygons (not yet moved by dx) and metrics."""
    mods = mods or {}
    wdx = mods.get("wdx") or 1
    if d.cap and not mods.get("sc"):
        p = p.but(A=p.A * 0.92)
        wdx *= 0.955
    if mods.get("p"):
        p = p.but(**mods["p"])
    g = Builder(p)
    ret = d.fn(g)
    dy = mods.get("dy") or 0
    wd = p.wd * wdx
    sl = d.slant if d.slant is not None else (0 if d.upright else p.slant)
    yc = d.yc if d.yc is not None else p.xh * 0.45

    def T(x, y):
        return (x * wd + (y + dy - yc) * sl, y + dy)

    polys = []
    strokes = []
    bb = [1e9, -1e9, 1e9, -1e9]

    def grow(ux, uy):
        if ux < bb[0]:
            bb[0] = ux
        if ux > bb[1]:
            bb[1] = ux
        if uy < bb[2]:
            bb[2] = uy
        if uy > bb[3]:
            bb[3] = uy

    for s in g.strokes:
        prev = None
        out = []
        n = len(s["pts"])
        for x, y, pr in s["pts"]:
            nb = nib_for(p, s["o"], pr)
            q = T(x, y)
            for v in nb:
                grow(x * wd + v[0], y + dy + v[1])
            cur = [(q[0] + v[0], q[1] + v[1]) for v in nb]
            if prev is not None:
                polys.append(hull(prev + cur))
            elif n == 1:
                polys.append(cur)
            prev = cur
            out.append((q[0], q[1], pr))
        strokes.append({"pts": out, "nodes": [T(*nd) for nd in s["nodes"]], "role": s["o"].get("role") or "stroke"})
    for x, y, r in g.balls:
        q = T(x, y)
        polys.append(circle(q[0], q[1], r))
        grow(x * wd - r, y + dy - r)
        grow(x * wd + r, y + dy + r)
    for x, y, r in g.drops:
        pts, rnd = teardrop(g, x, y, r)
        g.fills.append({"pts": pts, "role": "ball" if rnd else "drop"})
    for f in g.fills:
        pts = []
        for x, y in f["pts"]:
            grow(x * wd, y + dy)
            pts.append(T(x, y))
        polys.append(ccw(pts))
    x0, x1, y0, y1 = bb
    if x0 > x1:
        x0 = x1 = y0 = y1 = 0
    if d.adv is not None and not mods.get("prop"):
        adv = d.adv * wd
        dx = 0 if d.empty else (adv - (x1 - x0)) / 2 - x0
    else:
        extra = mods.get("extra") or 0
        L = p.sb * (1 if d.l is None else d.l) + extra
        R = p.sb * (1 if d.r is None else d.r) + extra
        adv = x1 - x0 + L + R
        dx = L - x0
    return Swept(polys=polys, strokes=strokes, adv=adv, dx=dx, xmin=x0, xmax=x1, ymin=y0, ymax=y1, ret=ret,
                 yc=yc, sl=sl, p=p)


# Old-style figures: x-height (x), descending (d) or ascending (a).
OSF = {"0": "x", "1": "x", "2": "x", "3": "d", "4": "d", "5": "d", "7": "d", "9": "d", "6": "a", "8": "a"}


def osf_mods(p: Params, base: str) -> dict:
    k, X = OSF[base], p.xh
    return {"p": {"cap": X * 1.02 if k == "x" else X * 1.42}, "dy": -X * 0.42 if k == "d" else 0,
            "prop": True, "wdx": 0.97}


def sc_mods(p: Params) -> dict:
    """Small cap: the capital drawn at 1.1 x-height, narrower, heavier hairlines."""
    return {"sc": True, "p": {"cap": p.xh * 1.1, "A": p.A * 0.94, "B": p.B * 1.3, "S": p.S * 1.2, "sl": p.sl * 0.8},
            "wdx": 0.83, "extra": p.sb * 0.15}


def is_greek_lower(ch: str) -> bool:
    return len(ch) == 1 and "α" <= ch <= "ω"
