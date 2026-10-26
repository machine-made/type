"""Turn Weft centre-line strokes into closed outlines.

The rules match the sketch 0.1 canvas renderer:

* Open strokes get square caps: each end extends by half the stroke
  width along its end segment, then the end is cut flat.
* Joins are miter joins. If the miter ratio 1 / sin(theta / 2) is more
  than the miter limit (2.4), the join is a bevel.
* A dot is a square with side = stroke width, centred on its point.

The stroke is the union of one rectangle per segment and one join wedge
per corner. skia-pathops removes the overlaps.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import pathops

Point = tuple[float, float]
Polygon = list[Point]

EPS = 1e-9


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _mul(a: Point, k: float) -> Point:
    return (a[0] * k, a[1] * k)


def _norm(a: Point) -> Point:
    length = math.hypot(a[0], a[1])
    if length < EPS:
        raise ValueError("Segment has zero length. Remove the repeated point.")
    return (a[0] / length, a[1] / length)


def _perp(a: Point) -> Point:
    """Return the left normal of a direction."""
    return (-a[1], a[0])


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _dedupe(points: Sequence[Point], closed: bool) -> list[Point]:
    out: list[Point] = []
    for p in points:
        if not out or math.dist(p, out[-1]) > EPS:
            out.append((float(p[0]), float(p[1])))
    if closed and len(out) > 1 and math.dist(out[0], out[-1]) <= EPS:
        out.pop()
    return out


def signed_area(poly: Sequence[Point]) -> float:
    """Return the signed area. Counter-clockwise is positive."""
    area = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2


def _ccw(poly: Polygon) -> Polygon:
    return poly if signed_area(poly) >= 0 else poly[::-1]


def _segment_rect(a: Point, b: Point, half: float) -> Polygon:
    n = _mul(_perp(_norm(_sub(b, a))), half)
    return [_add(a, n), _add(b, n), _sub(b, n), _sub(a, n)]


def _join(prev: Point, vertex: Point, nxt: Point, half: float,
          miter_limit: float) -> Polygon | None:
    """Return the join wedge on the outer side of a corner, or None."""
    d1 = _norm(_sub(vertex, prev))
    d2 = _norm(_sub(nxt, vertex))
    turn = _cross(d1, d2)
    if abs(turn) < 1e-12:
        # The segments are collinear (straight on) or turn back (180 deg).
        return None
    # The outer side is right of the path for a left turn, and left of
    # the path for a right turn.
    side = -1.0 if turn > 0 else 1.0
    n1 = _mul(_perp(d1), side * half)
    n2 = _mul(_perp(d2), side * half)
    p1 = _add(vertex, n1)
    p2 = _add(vertex, n2)
    cos_t = max(-1.0, min(1.0, -(d1[0] * d2[0] + d1[1] * d2[1])))
    theta = math.acos(cos_t)  # interior angle between the two segments
    sin_half = math.sin(theta / 2)
    if sin_half > EPS and 1.0 / sin_half <= miter_limit:
        bis = _norm(_add(n1, n2))
        tip = _add(vertex, _mul(bis, half / sin_half))
        return [vertex, p1, tip, p2]
    return [vertex, p1, p2]


def stroke_polygons(kind: str, points: Sequence[Point], width: float,
                    miter_limit: float) -> list[Polygon]:
    """Return the raw polygons (they overlap) for one stroke."""
    half = width / 2
    if kind == "dot":
        (x, y), = points
        return [[(x - half, y - half), (x + half, y - half),
                 (x + half, y + half), (x - half, y + half)]]
    closed = kind == "closed"
    if kind not in ("open", "closed"):
        raise ValueError(f"Stroke kind {kind!r} is not known.")
    pts = _dedupe(points, closed)
    if len(pts) < 2 or (closed and len(pts) < 3):
        raise ValueError("Stroke has too few points.")
    if not closed:
        d0 = _norm(_sub(pts[1], pts[0]))
        d1 = _norm(_sub(pts[-1], pts[-2]))
        pts[0] = _sub(pts[0], _mul(d0, half))
        pts[-1] = _add(pts[-1], _mul(d1, half))
    polys: list[Polygon] = []
    n = len(pts)
    seg_count = n if closed else n - 1
    for i in range(seg_count):
        polys.append(_segment_rect(pts[i], pts[(i + 1) % n], half))
    corners = range(n) if closed else range(1, n - 1)
    for i in corners:
        wedge = _join(pts[i - 1], pts[i], pts[(i + 1) % n], half, miter_limit)
        if wedge is not None:
            polys.append(wedge)
    return [_ccw(p) for p in polys]


def glyph_outline(strokes: Iterable[tuple[str, Sequence[Point]]],
                  width: float, miter_limit: float, *, scale: float = 1.0,
                  dx: float = 0.0, dy: float = 0.0) -> pathops.Path:
    """Return one overlap-free path for all strokes of a glyph.

    Coordinates map as: font = ((design + dx) * scale, (design + dy) * scale).
    Contours are counter-clockwise for outer shapes (PostScript order).
    """
    path = pathops.Path()
    path.fillType = pathops.FillType.WINDING
    pen = path.getPen()
    for kind, pts in strokes:
        for poly in stroke_polygons(kind, pts, width, miter_limit):
            mapped = [((x + dx) * scale, (y + dy) * scale) for x, y in poly]
            pen.moveTo(mapped[0])
            for p in mapped[1:]:
                pen.lineTo(p)
            pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    return path


def path_contours(path: pathops.Path) -> list[Polygon]:
    """Return the contours of a line-only path as lists of points."""
    contours: list[Polygon] = []
    for verbs_points in path.contours:
        pts: Polygon = []
        for verb, seg in verbs_points.segments:
            if verb in ("moveTo", "lineTo"):
                pts.append(tuple(seg[0]))
            elif verb == "closePath":
                pass
            else:
                raise ValueError(f"Path has a curve segment ({verb}). Weft uses lines only.")
        contours.append(pts)
    return contours


def clean_contour(points: Polygon, *, grid: float = 1.0) -> Polygon:
    """Round points to the grid and remove repeated and collinear points."""
    pts: Polygon = []
    for x, y in points:
        q = (round(x / grid) * grid, round(y / grid) * grid)
        q = tuple(int(v) if float(v).is_integer() else v for v in q)
        if not pts or q != pts[-1]:
            pts.append(q)
    while len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    i = 0
    # Remove one point at a time, so that each test uses current neighbours.
    while len(pts) >= 3 and i < len(pts):
        n = len(pts)
        prev, cur, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        a, b = _sub(cur, prev), _sub(nxt, cur)
        if cur == prev or (_cross(a, b) == 0 and a[0] * b[0] + a[1] * b[1] >= 0):
            del pts[i]
            i = max(i - 1, 0)
            continue
        i += 1
    return pts
