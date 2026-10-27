"""From pen sweeps to clean outlines.

1. union: the sweep polygons (convex hulls of consecutive nib positions,
   discs, teardrops, bracket fillets) are joined with skia-pathops
   (nonzero fill). The result is a set of polygons with many short edges.
2. fit: each polygon is cut at its corners and each run between corners
   is fitted with as few cubic Bézier curves as the tolerance allows
   (Schneider's algorithm, with Newton reparameterisation). Straight
   runs become lines. Curves are split at their x and y extrema, so
   that every extremum is an on-curve point.
3. clean: no segment shorter than MIN_SEG, contours wind counter-
   clockwise outside and clockwise inside (PostScript order; ufo2ft
   reverses them for TrueType), tiny slivers are dropped.

loom/raster.py checks the result against an independent rasterised fill
of the sweep (tools/fidelity.py writes the numbers).

Apache-2.0.
"""

from __future__ import annotations

import math

import numpy as np
import pathops

TOL = 0.9            # largest distance of the fit from the union, in font units
CORNER_DEG = 32.0    # a vertex that turns more than this is a corner
CORNER_MERGE = 7.0   # corners closer than this (arc length) are one corner
MIN_SEG = 4.0        # no segment shorter than this
MIN_AREA = 40.0      # contours with less area are dropped (union slivers)
LINE_TOL = 0.35      # a run within this of its chord is a line


# ------------------------------------------------------------------ union

def union(polys) -> pathops.Path:
    path = pathops.Path()
    path.fillType = pathops.FillType.WINDING
    pen = path.getPen()
    for poly in polys:
        if len(poly) < 3:
            continue
        pen.moveTo(poly[0])
        for q in poly[1:]:
            pen.lineTo(q)
        pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    return path


def path_polygons(path: pathops.Path) -> list[np.ndarray]:
    """The contours of a line-only pathops path, as arrays (no repeated end)."""
    out = []
    for contour in path.contours:
        pts = []
        for verb, args in contour.segments:
            if verb == "moveTo":
                pts = [args[0]]
            elif verb == "lineTo":
                pts.append(args[0])
            elif verb in ("qCurveTo", "curveTo"):
                pts.append(args[-1])
        if len(pts) > 2 and pts[0] == pts[-1]:
            pts = pts[:-1]
        if len(pts) >= 3:
            out.append(np.array(pts, dtype=float))
    return out


def signed_area(a: np.ndarray) -> float:
    x, y = a[:, 0], a[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


# -------------------------------------------------------------- cleanup

def dedupe(a: np.ndarray, eps: float = 0.05) -> np.ndarray:
    keep = [0]
    for i in range(1, len(a)):
        if np.hypot(*(a[i] - a[keep[-1]])) > eps:
            keep.append(i)
    a = a[keep]
    if len(a) > 2 and np.hypot(*(a[0] - a[-1])) <= eps:
        a = a[:-1]
    return a


def drop_collinear(a: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    changed = True
    while changed and len(a) > 3:
        changed = False
        n = len(a)
        keep = []
        for i in range(n):
            p0, p1, p2 = a[i - 1], a[i], a[(i + 1) % n]
            d1, d2 = p1 - p0, p2 - p1
            cross = d1[0] * d2[1] - d1[1] * d2[0]
            dot = d1[0] * d2[0] + d1[1] * d2[1]
            if abs(cross) <= eps * np.hypot(*d1) * np.hypot(*d2) and dot > 0:
                changed = True
                continue
            keep.append(i)
        a = a[keep]
    return a


def turning(a: np.ndarray) -> np.ndarray:
    """Signed turning angle at each vertex, in degrees."""
    d_in = a - np.roll(a, 1, axis=0)
    d_out = np.roll(a, -1, axis=0) - a
    ang = np.arctan2(d_in[:, 0] * d_out[:, 1] - d_in[:, 1] * d_out[:, 0],
                     (d_in * d_out).sum(axis=1))
    return np.degrees(ang)


def corners(a: np.ndarray) -> list[int]:
    """Indices of corner vertices.

    A vertex is a corner when it turns more than CORNER_DEG, or when the
    vertices within CORNER_MERGE / 2 around it turn more than 2 x
    CORNER_DEG together (a small rounded nib end). Corners closer than
    CORNER_MERGE merge into the one that turns most.
    """
    n = len(a)
    th = turning(a)
    seg = np.hypot(*(np.roll(a, -1, axis=0) - a).T)
    cand = []
    half = CORNER_MERGE / 2
    for i in range(n):
        if abs(th[i]) > CORNER_DEG:
            cand.append(i)
            continue
        # turning in a short window
        tot = th[i]
        s = 0.0
        j = i
        while True:
            s += seg[j % n]
            j += 1
            if s > half or j - i >= n:
                break
            tot += th[j % n]
        s = 0.0
        j = i
        while True:
            j -= 1
            s += seg[j % n]
            if s > half or i - j >= n:
                break
            tot += th[j % n]
        if abs(tot) > 2 * CORNER_DEG and abs(th[i]) > 8:
            cand.append(i)
    if not cand:
        return []
    # merge close candidates: keep the strongest of each cluster
    pos = np.concatenate([[0], np.cumsum(seg)])[:n]
    total = float(seg.sum())
    cand.sort()
    clusters = [[cand[0]]]
    for c in cand[1:]:
        if pos[c] - pos[clusters[-1][-1]] < CORNER_MERGE:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    if len(clusters) > 1 and (pos[clusters[0][0]] + total - pos[clusters[-1][-1]]) < CORNER_MERGE:
        clusters[0] = clusters.pop() + clusters[0]
    return sorted(max(cl, key=lambda k: abs(th[k])) for cl in clusters)


# -------------------------------------------------------------- fitting

def _bez(ctrl, t):
    t = np.asarray(t)[:, None]
    m = 1 - t
    return m ** 3 * ctrl[0] + 3 * m * m * t * ctrl[1] + 3 * m * t * t * ctrl[2] + t ** 3 * ctrl[3]


def _bez_d1(ctrl, t):
    t = np.asarray(t)[:, None]
    m = 1 - t
    return 3 * (m * m * (ctrl[1] - ctrl[0]) + 2 * m * t * (ctrl[2] - ctrl[1]) + t * t * (ctrl[3] - ctrl[2]))


def _bez_d2(ctrl, t):
    t = np.asarray(t)[:, None]
    m = 1 - t
    return 6 * (m * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + t * (ctrl[3] - 2 * ctrl[2] + ctrl[1]))


def _chord_params(pts):
    d = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    return d / d[-1] if d[-1] > 0 else d


def _unit(v):
    n = np.hypot(*v)
    return v / n if n > 0 else v


def _generate(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    A1 = t1[None, :] * (3 * (1 - u) ** 2 * u)[:, None]
    A2 = t2[None, :] * (3 * (1 - u) * u ** 2)[:, None]
    C00 = (A1 * A1).sum()
    C01 = (A1 * A2).sum()
    C11 = (A2 * A2).sum()
    base = _bez(np.array([p0, p0, p3, p3]), u)
    tmp = pts - base
    X0 = (A1 * tmp).sum()
    X1 = (A2 * tmp).sum()
    det = C00 * C11 - C01 * C01
    seg = np.hypot(*(p3 - p0))
    if abs(det) > 1e-12:
        a1 = (X0 * C11 - X1 * C01) / det
        a2 = (C00 * X1 - C01 * X0) / det
    else:
        a1 = a2 = seg / 3
    eps = 1e-6 * seg
    if a1 < eps or a2 < eps or a1 > seg * 2 or a2 > seg * 2:
        a1 = a2 = seg / 3
    return np.array([p0, p0 + t1 * a1, p3 + t2 * a2, p3])


def _max_error(pts, ctrl, u):
    d = np.hypot(*(_bez(ctrl, u) - pts).T)
    i = int(np.argmax(d))
    return float(d[i]), i


def _reparam(pts, ctrl, u):
    q = _bez(ctrl, u)
    d1 = _bez_d1(ctrl, u)
    d2 = _bez_d2(ctrl, u)
    num = ((q - pts) * d1).sum(axis=1)
    den = (d1 * d1).sum(axis=1) + ((q - pts) * d2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        nu = np.where(np.abs(den) > 1e-12, u - num / den, u)
    nu = np.clip(nu, 0, 1)
    nu[0], nu[-1] = 0.0, 1.0
    if np.any(np.diff(nu) < 0):
        return u
    return nu


def _true_error(pts, ctrl, samples=24):
    """Largest distance from the polyline vertices to the curve, and from
    the curve back to the polyline (so that a curve cannot bulge between
    vertices)."""
    tt = np.linspace(0, 1, samples * 4 + 1)
    cp = _bez(ctrl, tt)
    # vertex -> curve
    d1 = np.min(np.hypot(pts[:, None, 0] - cp[None, :, 0], pts[:, None, 1] - cp[None, :, 1]), axis=1).max()
    # curve -> polyline segments
    a, b = pts[:-1], pts[1:]
    ab = b - a
    L2 = (ab * ab).sum(axis=1)
    L2[L2 == 0] = 1
    best = np.full(len(cp), np.inf)
    for k in range(len(a)):
        t = np.clip(((cp - a[k]) @ ab[k]) / L2[k], 0, 1)
        proj = a[k] + t[:, None] * ab[k]
        best = np.minimum(best, np.hypot(*(cp - proj).T))
    return max(float(d1), float(best.max()))


def fit_cubics(pts, t1, t2, tol=TOL, depth=0):
    """Fit a polyline (m x 2) with cubic segments. Returns a list of 4x2 arrays."""
    n = len(pts)
    if n == 2:
        # two points: a straight segment (the tangents of a corner run do not apply)
        return [np.array([pts[0], pts[0] + (pts[1] - pts[0]) / 3, pts[1] - (pts[1] - pts[0]) / 3, pts[1]])]
    u = _chord_params(pts)
    ctrl = _generate(pts, u, t1, t2)
    err, split = _max_error(pts, ctrl, u)
    if err < tol and _true_error(pts, ctrl) < tol * 1.5:
        return [ctrl]
    if err < tol * 4:
        for _ in range(12):
            u = _reparam(pts, ctrl, u)
            ctrl = _generate(pts, u, t1, t2)
            err, split = _max_error(pts, ctrl, u)
            if err < tol:
                break
        if err < tol and _true_error(pts, ctrl) < tol * 1.5:
            return [ctrl]
    if depth > 40:
        return [ctrl]
    split = min(max(split, 1), n - 2)
    tc = _unit(pts[split - 1] - pts[split + 1])
    if not np.any(tc):
        tc = _unit(pts[split - 1] - pts[split])
    return (fit_cubics(pts[: split + 1], t1, tc, tol, depth + 1)
            + fit_cubics(pts[split:], -tc, t2, tol, depth + 1))


def _is_line(pts, tol=LINE_TOL) -> bool:
    a, b = pts[0], pts[-1]
    ab = b - a
    L = np.hypot(*ab)
    if L == 0:
        return False
    d = np.abs((pts[:, 0] - a[0]) * ab[1] - (pts[:, 1] - a[1]) * ab[0]) / L
    return float(d.max()) <= tol


def _tangent_out(run):
    """Direction leaving the start of a run (first 3 units of arc)."""
    acc = 0.0
    for k in range(1, len(run)):
        acc += np.hypot(*(run[k] - run[k - 1]))
        if acc >= 3.0:
            return _unit(run[k] - run[0])
    return _unit(run[-1] - run[0])


def _split_extrema(ctrl, min_len=12.0):
    """Split a cubic at its interior x and y extrema."""
    p0, p1, p2, p3 = ctrl
    ts = []
    for k in (0, 1):
        a = -p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]
        b = 2 * (p0[k] - 2 * p1[k] + p2[k])
        c = p1[k] - p0[k]
        if abs(a) < 1e-9:
            if abs(b) > 1e-9:
                ts.append(-c / b)
        else:
            disc = b * b - 4 * a * c
            if disc >= 0:
                r = math.sqrt(disc)
                ts += [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    ts = sorted(t for t in ts if 0.02 < t < 0.98)
    if not ts:
        return [ctrl]
    pieces, rest, t_prev = [], ctrl, 0.0
    for t in ts:
        tl = (t - t_prev) / (1 - t_prev)
        left, right = _split_at(rest, tl)
        if _arc_len(left) < min_len or _arc_len(right) < min_len:
            continue
        pieces.append(left)
        rest, t_prev = right, t
    pieces.append(rest)
    return pieces


def _split_at(c, t):
    p01 = c[0] + (c[1] - c[0]) * t
    p12 = c[1] + (c[2] - c[1]) * t
    p23 = c[2] + (c[3] - c[2]) * t
    a = p01 + (p12 - p01) * t
    b = p12 + (p23 - p12) * t
    m = a + (b - a) * t
    return np.array([c[0], p01, a, m]), np.array([m, b, p23, c[3]])


def _arc_len(c):
    q = _bez(c, np.linspace(0, 1, 9))
    return float(np.hypot(*np.diff(q, axis=0).T).sum())


def fit_contour(a: np.ndarray, tol=TOL) -> list:
    """Fit one closed polygon. Returns segments: ("line", p0, p1) or ("curve", 4x2)."""
    a = drop_collinear(dedupe(a))
    n = len(a)
    if n < 3:
        return []
    cs = corners(a)
    if not cs:
        # smooth closed contour: start at the lowest point
        i0 = int(np.lexsort((a[:, 0], a[:, 1]))[0])
        a = np.roll(a, -i0, axis=0)
        cs_runs = [np.vstack([a, a[:1]])]
        smooth_close = True
    else:
        cs_runs = []
        for k, c in enumerate(cs):
            nxt = cs[(k + 1) % len(cs)]
            idx = list(range(c, nxt + 1)) if nxt > c else list(range(c, n)) + list(range(0, nxt + 1))
            cs_runs.append(a[idx])
        smooth_close = False
    segs = []
    for run in cs_runs:
        if len(run) < 2:
            continue
        if _is_line(run):
            segs.append(("line", run[0], run[-1]))
            continue
        if smooth_close:
            t1 = _unit(run[1] - run[-2])
            t2 = -t1
        else:
            t1 = _tangent_out(run)
            t2 = _tangent_out(run[::-1])
        for c in fit_cubics(run, t1, t2, tol):
            for piece in _split_extrema(c):
                if _is_line(_bez(piece, np.linspace(0, 1, 9))):
                    segs.append(("line", piece[0], piece[3]))
                else:
                    segs.append(("curve", piece))
    return merge_short(segs)


def _seg_len(s):
    return float(np.hypot(*(s[2] - s[1]))) if s[0] == "line" else _arc_len(s[1])


def merge_short(segs: list) -> list:
    """Remove segments shorter than MIN_SEG by moving their end point."""
    changed = True
    while changed and len(segs) > 2:
        changed = False
        for i, s in enumerate(segs):
            if _seg_len(s) >= MIN_SEG:
                continue
            j = (i + 1) % len(segs)
            start = s[1] if s[0] == "line" else s[1][0]
            nxt = segs[j]
            if nxt[0] == "line":
                segs[j] = ("line", start, nxt[2])
            else:
                c = nxt[1].copy()
                c[1] = c[1] + (start - c[0])
                c[0] = start
                segs[j] = ("curve", c)
            del segs[i]
            changed = True
            break
    return segs


def outline(polys, tol=TOL) -> list[list]:
    """Union the sweep polygons and fit them. Returns contours of segments."""
    path = union(polys)
    out = []
    for a in path_polygons(path):
        if abs(signed_area(a)) < MIN_AREA:
            continue
        segs = fit_contour(a, tol)
        if len(segs) >= 2:
            out.append(segs)
    return out


def draw(contours, pen, dx=0.0, rnd=True) -> None:
    """Draw fitted contours into a segment pen, moved by dx, rounded."""
    def R(p):
        x, y = float(p[0]) + dx, float(p[1])
        return (int(math.floor(x + 0.5)), int(math.floor(y + 0.5))) if rnd else (x, y)

    for segs in contours:
        first = segs[0][1] if segs[0][0] == "line" else segs[0][1][0]
        pen.moveTo(R(first))
        for s in segs:
            if s[0] == "line":
                pen.lineTo(R(s[2]))
            else:
                c = s[1]
                pen.curveTo(R(c[1]), R(c[2]), R(c[3]))
        pen.closePath()
