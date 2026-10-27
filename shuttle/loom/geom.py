"""Shuttle geometry: the four primitives, as outline contours.

Primitives (from the sketch engine, reference/shuttle-sketch-0.1.js):

* rect           an axis-aligned rectangle
* ring           a superellipse ring (exponent N = 2.6): an outer and an
                 inner contour. Cuts open the ring (see below).
* parallelogram  horizontal top and bottom edges, a set horizontal width
* vee            a V with horizontal ends

A contour is a closed list of points (x, y, on) in font units, y up.
`on` is True for on-curve points. Two off-curve points between two
on-curve points make a cubic segment. The first point is on-curve.

Rules that keep the masters point-compatible:

* Every primitive is its own contour (or contours). Overlaps stay; the
  variable font keeps them, the statics remove them.
* All filled contours run counter-clockwise. Ring counters run clockwise.
  So nonzero fill gives the union.
* A superellipse arc is one cubic per quarter (between the axis points),
  fitted to the curve. A cut arc breaks at the axis points it contains.
* A cut is (side, lo, hi). Sides "l" and "r" are horizontal cuts: they
  remove the left or right half of the ring between the levels y = lo and
  y = hi. Sides "t" and "b" are vertical cuts: they remove the top or
  bottom half between x = lo and x = hi. One cut works on one ring only.
* The vee always has 7 points. When the counter closes, the 3 inner
  points meet at the top centre.

Apache-2.0.
"""

from __future__ import annotations

import math
from functools import lru_cache

N = 2.6
P = 2.0 / N
INF = 1.0e9
TAU = 2.0 * math.pi
HALF_PI = 0.5 * math.pi
# Axis points closer than this to a cut are not used as break points.
AXIS_MARGIN = 0.02
# Cut levels stay inside this share of the inner radius, so that a cut
# always crosses the inner contour too (a horizontal terminal).
CUT_KEEP = 0.97
# Smallest inner radius of a ring. A ring whose counter closes keeps a
# tiny counter, so that the point structure does not change.
MIN_INNER = 0.5
# Rings whose counter closed (for diagnostics; see tools/drift.py).
CLOSED: list = []


def _sp(v: float) -> float:
    """Signed power: sign(v) * |v| ** P."""
    return math.copysign(abs(v) ** P, v)


def se_point(cx: float, cy: float, rx: float, ry: float, t: float) -> tuple[float, float]:
    return (cx + rx * _sp(math.cos(t)), cy + ry * _sp(math.sin(t)))


def se_tangent(rx: float, ry: float, t: float) -> tuple[float, float]:
    """Unit tangent of the superellipse at angle t (direction of growing t)."""
    c, s = math.cos(t), math.sin(t)
    dx = -rx * s * abs(s) ** (1.0 - P)
    dy = ry * c * abs(c) ** (1.0 - P)
    length = math.hypot(dx, dy)
    if length == 0.0:
        return (0.0, 0.0)
    return (dx / length, dy / length)


def _bez(p0, p1, p2, p3, t):
    m = 1.0 - t
    a, b, c, d = m * m * m, 3 * m * m * t, 3 * m * t * t, t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


@lru_cache(maxsize=None)
def _unit_handles(rx: float, ry: float, t0: float, t1: float) -> tuple[float, float]:
    """Return the handle lengths (a, b) of the cubic that fits the arc.

    Least squares on 12 points of the arc, with 3 rounds of Newton
    reparametrisation. The result depends smoothly on the inputs.
    """
    p0 = se_point(0, 0, rx, ry, t0)
    p3 = se_point(0, 0, rx, ry, t1)
    u0 = se_tangent(rx, ry, t0)
    u3 = se_tangent(rx, ry, t1)
    chord = math.dist(p0, p3)
    if chord < 1e-9 or rx < 1e-6 or ry < 1e-6:
        return (chord / 3.0, chord / 3.0)
    m = 12
    qs = [se_point(0, 0, rx, ry, t0 + (t1 - t0) * i / (m + 1)) for i in range(1, m + 1)]
    pts = [p0] + qs + [p3]
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    ts = [v / acc[-1] for v in acc[1:-1]]
    ha = hb = chord / 3.0
    for _ in range(3):
        a11 = a12 = a22 = r1 = r2 = 0.0
        for t, q in zip(ts, qs):
            mt = 1.0 - t
            b0, b1, b2, b3 = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
            bx = p0[0] * (b0 + b1) + p3[0] * (b2 + b3)
            by = p0[1] * (b0 + b1) + p3[1] * (b2 + b3)
            ux, uy = u0[0] * b1, u0[1] * b1
            vx, vy = -u3[0] * b2, -u3[1] * b2
            rx_, ry_ = q[0] - bx, q[1] - by
            a11 += ux * ux + uy * uy
            a12 += ux * vx + uy * vy
            a22 += vx * vx + vy * vy
            r1 += ux * rx_ + uy * ry_
            r2 += vx * rx_ + vy * ry_
        det = a11 * a22 - a12 * a12
        if abs(det) < 1e-12:
            break
        ha = (r1 * a22 - r2 * a12) / det
        hb = (a11 * r2 - a12 * r1) / det
        if not (0.0 < ha < chord and 0.0 < hb < chord):
            ha = hb = chord / 3.0
            break
        p1 = (p0[0] + ha * u0[0], p0[1] + ha * u0[1])
        p2 = (p3[0] - hb * u3[0], p3[1] - hb * u3[1])
        new = []
        for t, q in zip(ts, qs):
            for _ in range(2):
                mt = 1.0 - t
                bx, by = _bez(p0, p1, p2, p3, t)
                d1x = 3 * mt * mt * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0])
                d1y = 3 * mt * mt * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1])
                d2x = 6 * mt * (p2[0] - 2 * p1[0] + p0[0]) + 6 * t * (p3[0] - 2 * p2[0] + p1[0])
                d2y = 6 * mt * (p2[1] - 2 * p1[1] + p0[1]) + 6 * t * (p3[1] - 2 * p2[1] + p1[1])
                ex, ey = bx - q[0], by - q[1]
                num = ex * d1x + ey * d1y
                den = d1x * d1x + d1y * d1y + ex * d2x + ey * d2y
                if den > 1e-12:
                    t = min(1.0, max(0.0, t - num / den))
            new.append(t)
        ts = new
    return (ha, hb)


def se_arc(cx: float, cy: float, rx: float, ry: float, t0: float, t1: float,
           margin: float = AXIS_MARGIN) -> list:
    """Return the points of the arc from t0 to t1 (t1 > t0), without the start.

    The arc breaks at every axis point (k * pi/2) inside it. Each part
    is one cubic. Output: [(x, y, on), ...], starting after t0.
    """
    breaks = [t0]
    k = math.ceil((t0 + margin) / HALF_PI)
    while k * HALF_PI < t1 - margin:
        breaks.append(k * HALF_PI)
        k += 1
    breaks.append(t1)
    out = []
    for a, b in zip(breaks, breaks[1:]):
        ha, hb = _unit_handles(_key(rx), _key(ry), _key(a), _key(b))
        p0 = se_point(cx, cy, rx, ry, a)
        p3 = se_point(cx, cy, rx, ry, b)
        u0 = se_tangent(rx, ry, a)
        u3 = se_tangent(rx, ry, b)
        out.append((p0[0] + ha * u0[0], p0[1] + ha * u0[1], False))
        out.append((p3[0] - hb * u3[0], p3[1] - hb * u3[1], False))
        out.append((p3[0], p3[1], True))
    return out


def _key(v: float) -> float:
    """Round a float for the fit cache (does not change the output)."""
    return round(v, 9)


# ------------------------------------------------------------------ cuts

def _angle_h(cy: float, ry: float, y: float, side: str) -> float:
    v = max(-1.0, min(1.0, (y - cy) / ry)) if ry > 0 else (1.0 if y > cy else -1.0)
    a = math.asin(math.copysign(abs(v) ** (N / 2.0), v))
    return a if side == "r" else math.pi - a


def _angle_v(cx: float, rx: float, x: float, side: str) -> float:
    u = max(-1.0, min(1.0, (x - cx) / rx)) if rx > 0 else (1.0 if x > cx else -1.0)
    a = math.acos(math.copysign(abs(u) ** (N / 2.0), u))
    return a if side == "t" else TAU - a


def _clamp_level(v: float, c: float, r_out: float, r_in: float) -> float:
    """Keep a cut level inside the inner radius, or push it past the outer."""
    d = v - c
    if abs(d) >= r_out:
        return c + math.copysign(INF, d)
    lim = CUT_KEEP * r_in
    if abs(d) > lim:
        return c + math.copysign(lim, d)
    return v


def cut_intervals(geo, cut) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the removed angle intervals (outer, inner) of one cut."""
    cx, cy, rx, ry, irx, iry = geo
    side, lo, hi = cut
    if lo > hi:
        lo, hi = hi, lo
    res = []
    if side in ("l", "r"):
        lo = _clamp_level(lo, cy, ry, iry)
        hi = _clamp_level(hi, cy, ry, iry)
        for r in (ry, iry):
            a, b = _angle_h(cy, r, lo, side), _angle_h(cy, r, hi, side)
            res.append((min(a, b), max(a, b)))
    elif side in ("t", "b"):
        lo = _clamp_level(lo, cx, rx, irx)
        hi = _clamp_level(hi, cx, rx, irx)
        for r in (rx, irx):
            a, b = _angle_v(cx, r, lo, side), _angle_v(cx, r, hi, side)
            res.append((min(a, b), max(a, b)))
    else:
        raise ValueError(f"Unknown cut side {side!r}.")
    return res[0], res[1]


def kept_pieces(geo, cuts) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return the kept (outer, inner) angle intervals of a cut ring."""
    eps = 1e-9
    items = []
    for c in cuts:
        (oa, ob), (ia, ib) = cut_intervals(geo, c)
        if ob - oa < eps and ib - ia < eps:
            continue
        k = math.floor(oa / TAU)
        items.append([oa - k * TAU, ob - k * TAU, ia - k * TAU, ib - k * TAU])
    if not items:
        return []
    items.sort()
    merged = [items[0]]
    for it in items[1:]:
        last = merged[-1]
        if it[0] <= last[1] + eps or it[2] <= last[3] + eps:
            last[1] = max(last[1], it[1])
            last[3] = max(last[3], it[3])
        else:
            merged.append(it)
    # Wrap around: the first group again, one turn later.
    while len(merged) > 1:
        first = [v + TAU for v in merged[0]]
        last = merged[-1]
        if first[0] <= last[1] + eps or first[2] <= last[3] + eps:
            last[1] = max(last[1], first[1])
            last[3] = max(last[3], first[3])
            merged.pop(0)
        else:
            break
    pieces = []
    for i, g in enumerate(merged):
        nxt = merged[(i + 1) % len(merged)]
        shift = TAU if i + 1 >= len(merged) else 0.0
        if len(merged) == 1:
            shift = TAU
        o = (g[1], nxt[0] + shift)
        n = (g[3], nxt[2] + shift)
        if o[1] - o[0] <= eps or n[1] - n[0] <= eps:
            raise ValueError("A ring cut leaves nothing.")
        pieces.append((o, n))
    return pieces


# ------------------------------------------------------------ contours

def signed_area(contour) -> float:
    """Signed area of the on- and off-curve polygon (counter-clockwise > 0)."""
    a = 0.0
    n = len(contour)
    for i in range(n):
        x0, y0 = contour[i][0], contour[i][1]
        x1, y1 = contour[(i + 1) % n][0], contour[(i + 1) % n][1]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def reverse(contour):
    pts = list(reversed(contour))
    # Start again at an on-curve point.
    i = next(k for k, p in enumerate(pts) if p[2])
    return pts[i:] + pts[:i]


def polygon(pts):
    c = [(x, y, True) for x, y in pts]
    return c if signed_area(c) >= 0 else reverse(c)


def ring_contours(x0, y0, x1, y1, cuts=(), ts=0.0, th=0.0, margin=AXIS_MARGIN) -> list:
    """Return the contours of a superellipse ring with cuts."""
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    irx, iry = rx - ts, ry - th
    if irx < MIN_INNER or iry < MIN_INNER:
        # The counter is closed. Keep it as a tiny point at the centre, so
        # the point structure stays the same and no slit shows.
        CLOSED.append((x0, y0, x1, y1))
        irx = iry = MIN_INNER
    geo = (cx, cy, rx, ry, irx, iry)
    if not cuts:
        start = -HALF_PI
        p = se_point(cx, cy, rx, ry, start)
        outer = [(p[0], p[1], True)] + se_arc(cx, cy, rx, ry, start, start + TAU)[:-1]
        q = se_point(cx, cy, irx, iry, start)
        inner = [(q[0], q[1], True)] + se_arc(cx, cy, irx, iry, start, start + TAU)[:-1]
        return [outer, reverse(inner)]
    out = []
    for (oa, ob), (ia, ib) in kept_pieces(geo, cuts):
        p = se_point(cx, cy, rx, ry, oa)
        c = [(p[0], p[1], True)] + se_arc(cx, cy, rx, ry, oa, ob, margin)
        q = se_point(cx, cy, irx, iry, ia)
        inner = [(q[0], q[1], True)] + se_arc(cx, cy, irx, iry, ia, ib, margin)
        c += list(reversed(inner))
        out.append(c)
    return out


def vee_points(x0, x1, yT, yB, t):
    """Return the 7 points of a V (top at yT, point at yB)."""
    xm = (x0 + x1) / 2.0
    oL, oR = (x0, yT), (x1, yT)
    bL, bR = (xm - t / 2.0, yB), (xm + t / 2.0, yB)
    iL, iR = (x0 + t, yT), (x1 - t, yT)
    d1 = (bL[0] - oL[0], yB - yT)
    d2 = (bR[0] - oR[0], yB - yT)
    det = -d1[0] * d2[1] + d2[0] * d1[1]
    rx, ry = iR[0] - iL[0], iR[1] - iL[1]
    a = (rx * (-d2[1]) - (-d2[0]) * ry) / det if det else 0.0
    inter = (iL[0] + a * d1[0], iL[1] + a * d1[1])
    if a <= 0.0 or inter[1] >= yT:
        # The counter is closed: the inner points meet at the top centre.
        iL = iR = inter = (xm, yT)
    return [oL, iL, inter, iR, oR, bR, bL]


class Canvas:
    """Collects contours. Mirrors the drawing tools of the sketch engine."""

    def __init__(self, S: float, H: float):
        self.S = S
        self.H = H
        self.contours: list = []
        self._m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    # -- transforms
    def _apply(self, contour):
        a, b, c, d, e, f = self._m
        out = [(a * x + c * y + e, b * x + d * y + f, on) for x, y, on in contour]
        if a * d - b * c < 0:
            out = reverse(out)
        return out

    def _push(self, m, fn):
        old = self._m
        a, b, c, d, e, f = old
        A, B, C, D, E, F = m
        self._m = (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D,
                   a * E + c * F + e, b * E + d * F + f)
        try:
            fn()
        finally:
            self._m = old

    def flipX(self, W, fn):
        self._push((-1.0, 0.0, 0.0, 1.0, W, 0.0), fn)

    def rot(self, W, yc, fn):
        """Turn by 180 degrees around (W/2, yc)."""
        self._push((-1.0, 0.0, 0.0, -1.0, W, 2.0 * yc), fn)

    def shift(self, dx, dy, fn):
        self._push((1.0, 0.0, 0.0, 1.0, dx, dy), fn)

    def add(self, contour):
        self.contours.append(self._apply(contour))

    # -- primitives
    def rect(self, x0, y0, x1, y1):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        self.add(polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))

    def ring(self, x0, y0, x1, y1, cuts=(), ts=None, th=None, margin=AXIS_MARGIN):
        """A ring. `margin`: a smaller value keeps axis points close to a cut."""
        ts = self.S if ts is None else ts
        th = self.H if th is None else th
        for c in ring_contours(x0, y0, x1, y1, cuts, ts, th, margin):
            self.add(c)

    def disc(self, x0, y0, x1, y1):
        """A filled superellipse (no counter)."""
        self.add(ring_contours(x0, y0, x1, y1, (), 0.0, 0.0)[0])

    def poly(self, pts):
        self.add(polygon(pts))

    def dt(self, dx, dy):
        """Horizontal width that keeps a diagonal as heavy as a stem."""
        return self.S * 0.9 * math.hypot(dx, dy) / abs(dy)

    def par(self, xa, ya, xb, yb, t):
        h = t / 2.0
        self.poly([(xa - h, ya), (xa + h, ya), (xb + h, yb), (xb - h, yb)])

    def vee(self, x0, x1, yT, yB, t):
        self.poly(vee_points(x0, x1, yT, yB, t))
