"""Small raster helpers shared by the tools (fidelity, proofs).

PolyPen flattens a font glyph into polygons; fill_glyph fills them with
the nonzero rule for an overlap-free outline (nesting depth: even = ink,
odd = counter); fill_sweep fills pen-sweep polygons (their union).

Apache-2.0.
"""

from __future__ import annotations

from fontTools.pens.basePen import BasePen
from PIL import ImageDraw


class PolyPen(BasePen):
    """Flatten a glyph into closed polygons (font units)."""

    def __init__(self, glyphset=None, dx=0.0, dy=0.0, scale=1.0):
        super().__init__(glyphset)
        self.polys, self.cur = [], []
        self.dx, self.dy, self.k = dx, dy, scale

    def _t(self, p):
        return (self.dx + p[0] * self.k, self.dy + p[1] * self.k)

    def _moveTo(self, p):
        self.cur = [self._t(p)]

    def _lineTo(self, p):
        self.cur.append(self._t(p))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._raw
        self._cubic(p0, p1, p2, p3)

    def _cubic(self, p0, p1, p2, p3):
        for k in range(1, 13):
            t = k / 12
            m = 1 - t
            self.cur.append(self._t((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                                     m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1])))

    def _qCurveToOne(self, p1, p2):
        p0 = self._raw
        for k in range(1, 9):
            t = k / 8
            m = 1 - t
            self.cur.append(self._t((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                                     m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1])))

    @property
    def _raw(self):
        x, y = self._getCurrentPoint()
        return (x, y)

    def _closePath(self):
        if len(self.cur) >= 3:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


def inside(pt, poly) -> bool:
    """Even-odd point in polygon."""
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def fill_glyph(draw: ImageDraw.ImageDraw, polys, tr, ink=255, paper=0) -> None:
    """Fill an overlap-free outline: even nesting depth is ink, odd is counter."""
    depth = [sum(inside(q[0], o) for j, o in enumerate(polys) if j != i) for i, q in enumerate(polys)]
    for d, poly in sorted(zip(depth, polys), key=lambda t: t[0]):
        pts = [tr(p) for p in poly]
        if d % 2 == 0:
            draw.polygon(pts, fill=ink)
        else:
            draw.polygon(pts, fill=paper, outline=ink)


def fill_sweep(draw: ImageDraw.ImageDraw, polys, tr, ink=255) -> None:
    for poly in polys:
        if len(poly) >= 3:
            draw.polygon([tr(p) for p in poly], fill=ink)
