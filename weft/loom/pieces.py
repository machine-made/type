"""Fixed-topology stroke pieces for the Weft variable font.

Phase 1 made one outline per glyph with overlap removal. Overlap removal
gives a different point count at each weight, so those outlines do not
interpolate. This module makes outlines that interpolate:

* Each stroke is a fixed set of convex pieces: one quad per segment and
  one join wedge per corner (miter or bevel). The miter or bevel choice
  depends only on the corner angle, so it is the same at every weight.
* All contours run counter-clockwise (PostScript order). The pieces
  overlap. A non-zero fill gives their union. The variable font keeps
  the overlaps (OVERLAP_SIMPLE flag). Static fonts remove them.
* Every glyph has the same contours and the same points in every master.

FRAG (fragmentation) is a fixed design. A seeded generator picks it once
at build time, so the build is reproducible:

* FRAG 0: clean. Cuts exist but have zero width, so pieces abut.
* FRAG 1-15: ink-trap notches at square and acute corners and at
  T-junctions. Each notch is three points on the inner edges of the two
  pieces that meet. At FRAG 0 the three points sit on the edge (closed).
  At FRAG 15 they open to a notch of size 0.36 w.
* FRAG 16-50: cuts across strokes open to 0.42 w (narrower than the
  stroke). About 60 % of the cuts open in this stage.
* FRAG 51-100: all cuts open (0.6 w), notches close, pieces drift on a
  0.25-unit grid, get thinner (to 55 %), and about 36 % shrink to zero.

Cut positions are a fixed fraction of a free slot on one segment. The
slot ends depend linearly on the stroke width, so a cut stays on the same
segment in every master and never enters a corner, a notch or a cap.

All values are in design units (1 unit = 62.5 font units). x is in the
7-unit design box.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

Point = tuple[float, float]

SEED = "machine-made Weft 0.1"

# Stroke widths of the wght masters (100, 400, 900) and the FRAG masters.
W_MASTERS = (0.6, 1.35, 2.6)
F_MASTERS = (0, 15, 50, 100)

MITER_LIMIT = 2.4
NOTCH_SIZE = 0.36       # notch size at FRAG 15, times w
NOTCH_DEPTH = 0.8       # depth of the notch tip, times the notch size
NOTCH_MIN_ANGLE = 0.35  # radians (20 degrees)
NOTCH_MAX_ANGLE = 1.95  # radians (112 degrees)
NOTCH_MAX_DIST = 2.2    # inner corner distance limit, times w
OVERLAP = 0.12          # piece overlap at a closed cut, times w
GAP_50 = 0.42           # cut width at FRAG 50, times w
GAP_100 = 0.6           # cut width at FRAG 100, times w
P_EARLY = 0.6           # part of the cuts that open in stage 16-50
DRIFT_PERP = 1.15       # sideways drift limit at FRAG 100, times w
DRIFT_ALONG = 0.5       # drift limit along the piece at FRAG 100, units
DRIFT_GRID = 0.25
SHRINK = 0.45           # width loss limit at FRAG 100
P_DROP = 0.36           # part of the pieces that shrink to zero
DROP_END = 0.06          # size left of a dropped piece at FRAG 100
CUT_STEP = 1.5          # mean distance between cuts, units
MIN_PIECE = 0.35        # shortest piece between two cuts, units
MARGIN = 0.05


def clamp(v: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, v))


def t_notch(frag: float) -> float:
    """Notch size factor: 0 at FRAG 0, 1 from 15 to 50, 0 at 100."""
    return clamp(frag / 15) * (1 - clamp((frag - 50) / 50))


def t_cut(frag: float) -> float:
    return clamp((frag - 15) / 35)


def t_drift(frag: float) -> float:
    return clamp((frag - 50) / 50)


def gap_width(w: float, frag: float, early: bool) -> float:
    """Return the cut width. It is negative (an overlap) while closed.

    Pieces must overlap, not abut: a renderer that grid-fits each contour
    can open a hairline between two pieces that only touch.
    """
    if early:
        return w * (-OVERLAP + (OVERLAP + GAP_50) * t_cut(frag)
                    + (GAP_100 - GAP_50) * t_drift(frag))
    return w * (-OVERLAP + (OVERLAP + GAP_100) * t_drift(frag))


# ---------------------------------------------------------------- vectors

def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def mul(a: Point, k: float) -> Point:
    return (a[0] * k, a[1] * k)


def dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def norm(a: Point) -> Point:
    length = math.hypot(a[0], a[1])
    if length < 1e-12:
        raise ValueError("Vector has zero length. Remove the repeated point.")
    return (a[0] / length, a[1] / length)


def perp(a: Point) -> Point:
    return (-a[1], a[0])


def _solve(a: Point, b: Point, c: Point) -> tuple[float, float]:
    """Solve s * a + t * b = c for (s, t)."""
    det = cross(a, b)
    if abs(det) < 1e-12:
        raise ValueError("Lines are parallel.")
    return cross(c, b) / det, cross(a, c) / det


def _dedupe(points, closed: bool) -> list[Point]:
    out: list[Point] = []
    for p in points:
        p = (float(p[0]), float(p[1]))
        if not out or math.dist(p, out[-1]) > 1e-9:
            out.append(p)
    if closed and len(out) > 1 and math.dist(out[0], out[-1]) <= 1e-9:
        out.pop()
    return out


# --------------------------------------------------------------- geometry

@dataclass
class Seg:
    a: Point
    b: Point
    d: Point      # unit direction
    n: Point      # unit left normal
    length: float


@dataclass
class Notch:
    """An ink trap where two piece edges meet.

    The inner corner is I(h) = base + h * v. Edge "a" runs from I in
    direction ea, edge "b" in direction eb. Each edge is (stroke, segment,
    side), side +1 = left of the segment, -1 = right.
    """
    base: Point
    v: Point
    ea: Point
    eb: Point
    edge_a: tuple[int, int, int]
    edge_b: tuple[int, int, int]
    xa: float = 0.0  # second point on edge a: I + q * xa * ea
    xb: float = 0.0

    def __post_init__(self) -> None:
        bis = norm(add(self.ea, self.eb))
        p3 = mul(bis, -NOTCH_DEPTH)
        # Edge a: where the line p3 -> pb crosses the line of edge a.
        s, _ = _solve(self.ea, sub(p3, self.eb), p3)
        self.xa = s
        s, _ = _solve(self.eb, sub(p3, self.ea), p3)
        self.xb = s
        self.bis = bis

    def inner(self, h: float) -> Point:
        return add(self.base, mul(self.v, h))

    def points(self, w: float, frag: float) -> dict[str, Point]:
        h = w / 2
        q = NOTCH_SIZE * w * t_notch(frag)
        i = self.inner(h)
        return {
            "I": i,
            "pa": add(i, mul(self.ea, q)),
            "xa": add(i, mul(self.ea, q * self.xa)),
            "pb": add(i, mul(self.eb, q)),
            "xb": add(i, mul(self.eb, q * self.xb)),
            "p3": sub(i, mul(self.bis, NOTCH_DEPTH * q)),
        }


@dataclass
class Cut:
    seg: int
    slot: int
    frac: float
    early: bool


@dataclass
class Anchor:
    """A point on a segment that cuts must keep clear of."""
    pos: float                  # along the segment, from its start
    soft: object                # function (w) -> clearance, both sides
    kind: str = "vertex"


@dataclass
class StrokePlan:
    kind: str
    pts: list[Point]
    closed: bool
    segs: list[Seg] = field(default_factory=list)
    cuts: list[Cut] = field(default_factory=list)
    # Per segment: list of anchors (sorted by pos).
    anchors: list[list[Anchor]] = field(default_factory=list)
    # Piece random values for drift: list of (r_drop, r_perp, r_along, r_k).
    drift: list[tuple[float, float, float, float]] = field(default_factory=list)


@dataclass
class GlyphPlan:
    name: str
    strokes: list[StrokePlan]
    notches: list[Notch]
    attempt: int = 0          # drift seed attempt (see reroll_drift)
    drift_scale: float = 1.0  # drift and shrink scale for this glyph


def _make_stroke(kind: str, pts) -> StrokePlan:
    closed = kind == "closed"
    if kind == "dot":
        return StrokePlan(kind, [tuple(map(float, pts[0]))], False)
    p = _dedupe(pts, closed)
    sp = StrokePlan(kind, p, closed)
    n = len(p)
    count = n if closed else n - 1
    for k in range(count):
        a, b = p[k], p[(k + 1) % n]
        d = norm(sub(b, a))
        sp.segs.append(Seg(a, b, d, perp(d), math.dist(a, b)))
    return sp


def _seg_span(sp: StrokePlan, k: int, h: float) -> tuple[float, float]:
    """Return the along range of segment k, with square caps."""
    lo, hi = 0.0, sp.segs[k].length
    if not sp.closed:
        if k == 0:
            lo -= h
        if k == len(sp.segs) - 1:
            hi += h
    return lo, hi


def _along(sp: StrokePlan, k: int, p: Point) -> float:
    s = sp.segs[k]
    return dot(sub(p, s.a), s.d)


def _side(sp: StrokePlan, k: int, v: Point) -> int:
    c = cross(sp.segs[k].d, v)
    return 1 if c > 0 else -1


# ------------------------------------------------------------ notch finding

def _corner_notch(base: Point, ea: Point, eb: Point, ka, kb, plans) -> Notch | None:
    """Return a corner notch, or None if the angle is not in range."""
    phi = math.acos(clamp(dot(ea, eb), -1, 1))
    if phi > NOTCH_MAX_ANGLE or phi < NOTCH_MIN_ANGLE:
        return None
    dist = 0.5 / math.sin(phi / 2)  # times w
    if dist > NOTCH_MAX_DIST:
        return None
    bis = norm(add(ea, eb))
    v = mul(bis, 1 / math.sin(phi / 2))  # I = base + h * v
    sa = _side(plans[ka[0]], ka[1], v)
    sb = _side(plans[kb[0]], kb[1], v)
    return Notch(base, v, ea, eb, (ka[0], ka[1], sa), (kb[0], kb[1], sb))


def _find_notches(plans: list[StrokePlan]) -> list[Notch]:
    out: list[Notch] = []
    # Corners inside one stroke.
    for si, sp in enumerate(plans):
        if sp.kind == "dot":
            continue
        n = len(sp.pts)
        verts = range(n) if sp.closed else range(1, n - 1)
        for i in verts:
            kp = (i - 1) % len(sp.segs)
            kn = i % len(sp.segs)
            ea = mul(sp.segs[kp].d, -1)
            eb = sp.segs[kn].d
            nt = _corner_notch(sp.pts[i], ea, eb, (si, kp), (si, kn), plans)
            if nt:
                out.append(nt)
    # Stroke ends on other strokes: corners (end on end) and T-junctions.
    for ai, A in enumerate(plans):
        if A.kind != "open":
            continue
        nA = len(A.pts)
        for end in (0, nA - 1):
            E = A.pts[end]
            ka = 0 if end == 0 else len(A.segs) - 1
            dIn = A.segs[ka].d if end == 0 else mul(A.segs[ka].d, -1)
            for bi, B in enumerate(plans):
                if bi == ai or B.kind == "dot":
                    continue
                for j, sB in enumerate(B.segs):
                    ab = sub(sB.b, sB.a)
                    t = clamp(dot(sub(E, sB.a), ab) / dot(ab, ab))
                    foot = add(sB.a, mul(ab, t))
                    if math.dist(E, foot) > 0.06:
                        continue
                    last = len(B.segs) - 1
                    at_s = not B.closed and j == 0 and t < 0.02
                    at_e = not B.closed and j == last and t > 0.98
                    if at_s or at_e:
                        if ai < bi:
                            eb = sB.d if at_s else mul(sB.d, -1)
                            nt = _corner_notch(E, dIn, eb, (ai, ka), (bi, j), plans)
                            if nt:
                                out.append(nt)
                    elif 0.05 < t < 0.95:
                        if abs(dot(dIn, sB.d)) <= 0.985:
                            out.extend(_tee_notches(E, dIn, (ai, ka), sB, (bi, j), plans))
                    break
    return out


def _tee_notches(E, dIn, ka, sB: Seg, kb, plans) -> list[Notch]:
    """Return the two notches where the end of stroke A meets stroke B."""
    out = []
    nA = perp(dIn)
    nB = sB.n if dot(dIn, sB.n) > 0 else mul(sB.n, -1)  # B normal toward A
    for s in (1, -1):
        # A side line: E + s*nA*h + lam*dIn. B near line: E + nB*h + mu*d.
        # With h = 1: lam*dIn - mu*d = nB - s*nA.
        lam, mu = _solve(dIn, mul(sB.d, -1), sub(nB, mul(nA, s)))
        v = add(add(mul(nA, s), mul(dIn, lam)), (0.0, 0.0))
        eb = sB.d if mu >= 0 else mul(sB.d, -1)
        sa = _side(plans[ka[0]], ka[1], v)
        sb = _side(plans[kb[0]], kb[1], v)
        out.append(Notch(E, v, dIn, eb, (ka[0], ka[1], sa), (kb[0], kb[1], sb)))
    return out


def _notch_groups(nt: Notch, w: float, frag: float):
    """Return [(edge, [(along_pt, point) x3 in edge order])] for one notch."""
    pts = nt.points(w, frag)
    return [
        (nt.edge_a, [pts["pa"], pts["p3"], pts["xa"]], pts["I"]),
        (nt.edge_b, [pts["pb"], pts["p3"], pts["xb"]], pts["I"]),
    ]


def _notch_reach(plans, nt: Notch, w: float, frag: float):
    """Return [(edge, lo, hi)] along ranges that the notch uses."""
    out = []
    for edge, pts, i in _notch_groups(nt, w, frag):
        si, k, _ = edge
        al = [_along(plans[si], k, p) for p in (pts[0], pts[2], i)]
        out.append((edge, min(al), max(al)))
    return out


def _check_notches(plans: list[StrokePlan], notches: list[Notch]) -> list[Notch]:
    """Remove notches that do not fit inside their edges at every master."""
    keep = []
    for nt in notches:
        ok = True
        for w in W_MASTERS:
            for edge, lo, hi in _notch_reach(plans, nt, w, 15):
                si, k, _ = edge
                s0, s1 = _seg_span(plans[si], k, w / 2)
                if lo < s0 + MARGIN or hi > s1 - MARGIN:
                    ok = False
        if ok:
            keep.append(nt)
    # Two notches on one edge must not overlap.
    changed = True
    while changed:
        changed = False
        for w in W_MASTERS:
            ranges = {}
            for idx, nt in enumerate(keep):
                for edge, lo, hi in _notch_reach(plans, nt, w, 15):
                    ranges.setdefault(edge, []).append((lo, hi, idx))
            bad = set()
            for edge, rs in ranges.items():
                rs.sort()
                for (lo1, hi1, i1), (lo2, hi2, i2) in zip(rs, rs[1:]):
                    if lo2 < hi1 + MARGIN:
                        bad.add(max(i1, i2))
            if bad:
                keep = [nt for i, nt in enumerate(keep) if i not in bad]
                changed = True
                break
    return keep


# ------------------------------------------------------------- cut planning

def _anchors(plans: list[StrokePlan], si: int, notches: list[Notch]) -> list[list[Anchor]]:
    sp = plans[si]
    out = []
    nseg = len(sp.segs)
    for k, s in enumerate(sp.segs):
        anchors: list[Anchor] = []
        # Segment ends: a free end (cap) or a vertex.
        for pos, is_end in ((0.0, not sp.closed and k == 0),
                            (s.length, not sp.closed and k == nseg - 1)):
            if is_end:
                anchors.append(Anchor(pos, lambda w: 0.9, "end"))
                continue
            # Vertex: the sketch keeps cuts 0.55 units clear. The rect of
            # the next segment also covers h * cot(theta / 2) of this
            # segment (theta = interior angle).
            if pos == 0.0:
                cos_t = dot(mul(sp.segs[(k - 1) % nseg].d, -1), s.d)
            else:
                cos_t = dot(mul(s.d, -1), sp.segs[(k + 1) % nseg].d)
            theta = math.acos(clamp(cos_t, -1, 1))
            cot = min(4.0, 1 / math.tan(max(theta, 1e-3) / 2))
            anchors.append(Anchor(pos, (lambda c: (lambda w: 0.55 + 0.5 * w * c))(cot), "vertex"))
        # Other strokes that touch or cross this segment.
        for bi, B in enumerate(plans):
            if bi == si:
                continue
            if B.kind == "dot":
                continue
            ends = [] if B.kind == "closed" else [B.pts[0], B.pts[-1]]
            for E in ends:
                ab = sub(s.b, s.a)
                t = dot(sub(E, s.a), ab) / dot(ab, ab)
                if 0 < t < 1 and math.dist(E, add(s.a, mul(ab, t))) <= 0.06:
                    anchors.append(Anchor(t * s.length, lambda w: 0.55 + 0.6 * w, "tee"))
            for sB in B.segs:
                try:
                    tt, uu = _solve(sub(s.b, s.a), mul(sub(sB.b, sB.a), -1), sub(sB.a, s.a))
                except ValueError:
                    continue
                if 0.001 < tt < 0.999 and 0.001 < uu < 0.999:
                    sin_a = abs(cross(s.d, sB.d))
                    anchors.append(Anchor(tt * s.length,
                                          (lambda sa: (lambda w: 0.4 + 0.5 * w / max(sa, 0.25)))(sin_a),
                                          "cross"))
        anchors.sort(key=lambda a: a.pos)
        out.append(anchors)
    return out


def _reach_table(plans, notches, si, w, frag):
    """Return {segment: [(lo, hi)]} notch ranges on stroke si."""
    table: dict[int, list[tuple[float, float]]] = {}
    for nt in notches:
        for edge, lo, hi in _notch_reach(plans, nt, w, frag):
            if edge[0] == si:
                table.setdefault(edge[1], []).append((lo, hi))
    return table


def _slots(sp: StrokePlan, k: int, w: float, gap: float,
           reach: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return the free (lo, hi) slots between anchors on segment k."""
    anchors = sp.anchors[k]
    slots = []
    for a0, a1 in zip(anchors, anchors[1:]):
        lo = a0.pos + a0.soft(w)
        hi = a1.pos - a1.soft(w)
        # Keep clear of every notch range near the anchors.
        for r0, r1 in reach:
            if r1 <= (a0.pos + a1.pos) / 2:
                lo = max(lo, r1 + MARGIN)
            else:
                hi = min(hi, r0 - MARGIN)
        slots.append((lo + gap / 2 + MARGIN, hi - gap / 2 - MARGIN))
    return slots


def _cut_positions(sp: StrokePlan, plans, notches, si, w, cuts_in_slot):
    """Return the cut centres of one slot at stroke width w, or None.

    The slot uses the full notch size and the largest gap, so the cut
    centres do not change with FRAG and are linear in w.
    """
    k, slot = cuts_in_slot[0].seg, cuts_in_slot[0].slot
    reach = _reach_table(plans, notches, si, w, 15).get(k, [])
    gmax = GAP_100 * w
    lo, hi = _slots(sp, k, w, gmax, reach)[slot]
    if hi < lo:
        return None
    us = [lo + c.frac * (hi - lo) for c in cuts_in_slot]
    if all(u1 - u0 >= gmax + MIN_PIECE for u0, u1 in zip(us, us[1:])):
        return us
    return None


def _plan_cuts(plans, si, notches, rnd: random.Random) -> list[Cut]:
    sp = plans[si]
    cuts: list[Cut] = []
    for k in range(len(sp.segs)):
        reach = _reach_table(plans, notches, si, 1.35, 15).get(k, [])
        ref = _slots(sp, k, 1.35, GAP_100 * 1.35, reach)
        for slot, (lo, hi) in enumerate(ref):
            length = hi - lo
            n0 = max(0, round(length / CUT_STEP + rnd.random() - 0.5)) if length > 0 else 0
            jit = [rnd.random() for _ in range(max(n0, 1))]
            early = [rnd.random() < P_EARLY for _ in range(max(n0, 1))]
            for n in range(n0, 0, -1):
                group = [Cut(k, slot, (i + 0.5 + 0.5 * (jit[i] - 0.5)) / n, early[i])
                         for i in range(n)]
                if all(_cut_positions(sp, plans, notches, si, w, group) is not None
                       for w in W_MASTERS):
                    cuts.extend(group)
                    break
    return cuts


def plan_glyph(name: str, strokes) -> GlyphPlan:
    """Plan the pieces, notches and cuts of one glyph (seeded, fixed)."""
    plans = [_make_stroke(kind, pts) for kind, pts in strokes]
    notches = _check_notches(plans, _find_notches(plans))
    for si, sp in enumerate(plans):
        rnd = random.Random(f"{SEED}|{name}|{si}")
        if sp.kind != "dot":
            sp.anchors = _anchors(plans, si, notches)
            sp.cuts = _plan_cuts(plans, si, notches, rnd)
    gp = GlyphPlan(name, plans, notches)
    reroll_drift(gp, 0)
    return gp


def piece_count(sp: StrokePlan) -> int:
    if sp.kind == "dot" or (sp.closed and not sp.cuts):
        return 1
    return len(sp.cuts) if sp.closed else len(sp.cuts) + 1


def reroll_drift(gp: GlyphPlan, attempt: int) -> None:
    """Set the drift values of every piece from the seed and the attempt.

    The build calls this again with a higher attempt if the drift makes
    pieces change places between masters (fontTools interpolatable then
    reports a contour order problem). After 8 attempts the drift scale
    goes down by 15 % for each attempt.
    """
    gp.attempt = attempt
    gp.drift_scale = 0.85 ** max(0, attempt - 8)
    for si, sp in enumerate(gp.strokes):
        tag = "" if attempt == 0 else f"|drift{attempt}"
        rnd = random.Random(f"{SEED}|{gp.name}|{si}|pieces{tag}")
        sp.drift = [(rnd.random(), rnd.random(), rnd.random(), rnd.random())
                    for _ in range(piece_count(sp))]


# ---------------------------------------------------------------- outlines

def _pt(sp: StrokePlan, k: int, s: float) -> Point:
    seg = sp.segs[k]
    return add(seg.a, mul(seg.d, s))


def _wedge(prev: Point, v: Point, nxt: Point, half: float) -> list[Point] | None:
    d1 = norm(sub(v, prev))
    d2 = norm(sub(nxt, v))
    turn = cross(d1, d2)
    if abs(turn) < 1e-12:
        return None
    side = -1.0 if turn > 0 else 1.0
    n1 = mul(perp(d1), side * half)
    n2 = mul(perp(d2), side * half)
    p1, p2 = add(v, n1), add(v, n2)
    theta = math.acos(clamp(-dot(d1, d2), -1, 1))
    sin_half = math.sin(theta / 2)
    if sin_half > 1e-9 and 1 / sin_half <= MITER_LIMIT:
        bis = norm(add(perp(d1), perp(d2))) if half == 0 else norm(add(n1, n2))
        tip = add(v, mul(bis, half / sin_half))
        poly = [v, p1, tip, p2]
    else:
        poly = [v, p1, p2]
    return poly if turn > 0 else poly[::-1]


def _wedge_kind(prev: Point, v: Point, nxt: Point) -> int:
    """Return the wedge point count (0, 3 or 4). It depends only on the angle."""
    d1 = norm(sub(v, prev))
    d2 = norm(sub(nxt, v))
    if abs(cross(d1, d2)) < 1e-12:
        return 0
    theta = math.acos(clamp(-dot(d1, d2), -1, 1))
    sin_half = math.sin(theta / 2)
    return 4 if sin_half > 1e-9 and 1 / sin_half <= MITER_LIMIT else 3


def _join_points(s0: Seg, s1: Seg, half: float) -> tuple[list[Point], list[Point]]:
    """Return the join points to put in the end edge of segment s0.

    The end edge of s0 runs from b - n to b + n (b = vertex). The result
    is (points after b - n, points after b + n). For a right turn the
    outer side is +n, so the wedge goes after b - n ... b + n as
    [v, p2, tip]: the contour runs b - n, v, p2, tip, b + n. For a left
    turn the outer side is -n: b - n, tip, p2, v, b + n.
    """
    v = s0.b
    turn = cross(s0.d, s1.d)
    kind = _wedge_kind(s0.a, v, s1.b)
    if kind == 0:
        return [], []
    side = 1.0 if turn < 0 else -1.0  # outer side, in units of n
    p2 = add(v, mul(s1.n, side * half))
    theta = math.acos(clamp(-dot(s0.d, s1.d), -1, 1))
    sin_half = math.sin(theta / 2)
    # The inner point of the wedge moves from the vertex toward the inner
    # corner, so the wedge overlaps both segments (no shared edge).
    vin = add(v, mul(norm(sub(s1.d, s0.d)), 0.5 * half))
    mid = [p2]
    if kind == 4:
        bis = norm(add(mul(s0.n, side), mul(s1.n, side)))
        mid = [p2, add(v, mul(bis, half / sin_half))]
    if side > 0:
        return [vin] + mid, []
    return mid[::-1] + [vin], []


def _wedge_safe(prev, v, nxt, half):
    """Like _wedge, but correct when half is 0 (all points on v)."""
    kind = _wedge_kind(prev, v, nxt)
    if kind == 0:
        return None
    if half > 0:
        return _wedge(prev, v, nxt, half)
    return [v] * kind


def _pieces(sp: StrokePlan, w: float, frag: float, cutpos):
    """Return pieces as lists of (segment, s0, s1). cutpos: [(seg, u, gap)]."""
    h = w / 2
    nseg = len(sp.segs)
    if not sp.closed:
        bounds = [(0, -h)]
        for k, u, g in cutpos:
            bounds.append((k, u - g / 2))
            bounds.append((k, u + g / 2))
        bounds.append((nseg - 1, sp.segs[-1].length + h))
        pieces = []
        for (k0, s0), (k1, s1) in zip(bounds[0::2], bounds[1::2]):
            pieces.append(_ranges(sp, k0, s0, k1, s1, False))
        return pieces
    if not cutpos:
        return [[(k, 0.0, sp.segs[k].length) for k in range(nseg)] + [("ring",)]]
    pieces = []
    m = len(cutpos)
    for i in range(m):
        k0, u0, g0 = cutpos[i]
        k1, u1, g1 = cutpos[(i + 1) % m]
        pieces.append(_ranges(sp, k0, u0 + g0 / 2, k1, u1 - g1 / 2, True,
                              full=(m == 1)))
    return pieces


def _ranges(sp, k0, s0, k1, s1, closed, full=False):
    nseg = len(sp.segs)
    if k0 == k1 and not full and (s1 > s0 or not closed):
        return [(k0, s0, s1)]
    out = [(k0, s0, sp.segs[k0].length)]
    k = (k0 + 1) % nseg
    while k != k1:
        out.append((k, 0.0, sp.segs[k].length))
        k = (k + 1) % nseg
    out.append((k1, 0.0, s1))
    return out


def _stroke_cutpos(gp: GlyphPlan, si: int, w: float, frag: float):
    """Return [(segment, centre, gap)] for the cuts of one stroke."""
    sp = gp.strokes[si]
    groups: dict[tuple[int, int], list[Cut]] = {}
    for c in sp.cuts:
        groups.setdefault((c.seg, c.slot), []).append(c)
    out = []
    for key in sorted(groups):
        us = _cut_positions(sp, gp.strokes, gp.notches, si, w, groups[key])
        if us is None:
            raise ValueError(f"Cut plan does not fit in {gp.name!r} at w={w}.")
        for u, c in zip(us, groups[key]):
            out.append((key[0], u, gap_width(w, frag, c.early)))
    return out


def glyph_contours(gp: GlyphPlan, w: float, frag: float) -> list[list[Point]]:
    """Return all piece contours of a glyph at one (w, FRAG) location.

    The result has the same structure (contour count, point counts and
    point order) for every w and FRAG.
    """
    h = w / 2
    td = t_drift(frag) * gp.drift_scale
    tdrop = t_drift(frag)
    # Notch inserts per edge: edge -> [(along, [p, p3, p'])].
    inserts: dict[tuple[int, int, int], list] = {}
    for nt in gp.notches:
        for edge, pts, i in _notch_groups(nt, w, frag):
            sp = gp.strokes[edge[0]]
            inserts.setdefault(edge, []).append((_along(sp, edge[1], i), pts, i, h))
    contours: list[list[Point]] = []
    for si, sp in enumerate(gp.strokes):
        if sp.kind == "dot":
            pieces_pts = [[_dot(sp.pts[0], h * _k(sp.drift[0], td))]]
            centres = [sp.pts[0]]
            dirs = [(1.0, 0.0)]
        else:
            cutpos = _stroke_cutpos(gp, si, w, frag)
            pieces_pts, centres, dirs = [], [], []
            for pi, rngs in enumerate(_pieces(sp, w, frag, cutpos)):
                k = _k(sp.drift[pi], td)
                cs, c, d = _piece_contours(sp, si, rngs, h, k, inserts, td)
                pieces_pts.append(cs)
                centres.append(c)
                dirs.append(d)
        for pi, cs in enumerate(pieces_pts):
            r_drop, r_perp, r_along, _ = sp.drift[pi]
            dx, dy = _drift(dirs[pi], w, r_perp, r_along)
            dx, dy = dx * td, dy * td
            drop = r_drop < P_DROP
            c = centres[pi]
            for poly in cs:
                out = []
                for p in poly:
                    if drop:
                        p = add(c, mul(sub(p, c), 1 - (1 - DROP_END) * tdrop))
                    out.append((p[0] + dx, p[1] + dy))
                contours.append(out)
    return contours


def _k(drift, td: float) -> float:
    return 1 - SHRINK * drift[3] * td


def _drift(direction: Point, w: float, r_perp: float, r_along: float) -> Point:
    pp = perp(direction)
    m = round(((r_perp * 2 - 1) * DRIFT_PERP * w) / DRIFT_GRID) * DRIFT_GRID
    al = (r_along * 2 - 1) * DRIFT_ALONG
    dx = pp[0] * m + direction[0] * al
    dy = pp[1] * m + direction[1] * al
    return (round(dx / DRIFT_GRID) * DRIFT_GRID, round(dy / DRIFT_GRID) * DRIFT_GRID)


def _dot(p: Point, half: float) -> list[Point]:
    x, y = p
    return [(x - half, y - half), (x + half, y - half), (x + half, y + half), (x - half, y + half)]


def _piece_contours(sp, si, rngs, h, k, inserts, td):
    ring = bool(rngs) and rngs[-1] == ("ring",)
    if ring:
        rngs = rngs[:-1]
    hk = h * k
    # The join wedge at the end of a segment goes into the contour of that
    # segment (between the two end corners), so a piece has one contour
    # per segment. The wedge point count depends only on the angle.
    joins = {}
    pairs = list(zip(rngs, rngs[1:]))
    if ring:
        pairs.append((rngs[-1], rngs[0]))
    for (k0, _, _), (k1, _, _) in pairs:
        joins[k0] = k1
    cs = []
    for (seg, s0, s1) in rngs:
        a, b = _pt(sp, seg, s0), _pt(sp, seg, s1)
        n = mul(sp.segs[seg].n, hk)
        right = _edge_inserts(sp, si, seg, -1, s0, s1, inserts, hk, td, ascending=True)
        left = _edge_inserts(sp, si, seg, 1, s0, s1, inserts, hk, td, ascending=False)
        lo_end, hi_end = [], []
        if seg in joins:
            lo_end, hi_end = _join_points(sp.segs[seg], sp.segs[joins[seg]], hk)
        cs.append([sub(a, n)] + right + [sub(b, n)] + lo_end + [add(b, n)] + hi_end
                  + left + [add(a, n)])
    first = _pt(sp, rngs[0][0], rngs[0][1])
    last = _pt(sp, rngs[-1][0], rngs[-1][2])
    centre = mul(add(first, last), 0.5)
    if ring:
        xs = [p[0] for p in sp.pts]
        ys = [p[1] for p in sp.pts]
        centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        direction = (1.0, 0.0)
    else:
        dl = sub(last, first)
        direction = norm(dl) if math.hypot(*dl) > 1e-6 else (1.0, 0.0)
    return cs, centre, direction


def _edge_inserts(sp, si, seg, side, s0, s1, inserts, hk, td, ascending):
    """Return the notch points on one piece edge, in traversal order.

    The notch points are made for the full half width h. A piece that
    shrinks (drift stage) has its edge at h * k, so the points move in
    by the same amount along the normal.
    """
    groups = [g for g in inserts.get((si, seg, side), []) if s0 < g[0] < s1]
    groups.sort(key=lambda g: g[0], reverse=not ascending)
    out: list[Point] = []
    for along_i, pts, i, h in groups:
        shift = mul(sp.segs[seg].n, side * (hk - h))
        e1, p3, e2 = (add(p, shift) for p in pts)
        a1, a2 = _along(sp, seg, e1), _along(sp, seg, e2)
        if (a1 < a2) == ascending:
            out.extend([e1, p3, e2])
        else:
            out.extend([e2, p3, e1])
    return out


def structure(contours: list[list[Point]]) -> tuple[int, ...]:
    """Return the point count of each contour (the interpolation shape)."""
    return tuple(len(c) for c in contours)
