# SPDX-License-Identifier: Apache-2.0
"""Boundary checks shared with the weight-ladder tool. Apache-2.0."""

from __future__ import annotations

import math
import sys
from copy import deepcopy
from itertools import pairwise
from pathlib import Path

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib.removeOverlaps import removeOverlaps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fidelity
from loom import outline as O
from loom.compatible import TOPOLOGY


class BoundaryPen(BasePen):
    """Flatten curves by a 0.01-unit control-polygon error bound."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours = []
        self.points = []

    def _moveTo(self, p):
        self.points = [p]

    def _lineTo(self, p):
        self.points.append(p)

    def _curveToOne(self, p1, p2, p3):
        self._flatten(np.array([self._getCurrentPoint(), p1, p2, p3], dtype=float))

    def _qCurveToOne(self, p1, p2):
        a, b, c = (np.array(p, dtype=float) for p in (self._getCurrentPoint(), p1, p2))
        self._flatten(np.array([a, a + (b - a) * (2 / 3), c + (b - c) * (2 / 3), c]))

    def _flatten(self, c):
        chord = c[3] - c[0]
        length = math.hypot(*chord)
        error = (
            max(math.hypot(*(p - c[0])) for p in c[1:3])
            if length == 0
            else max(
                abs(float((p[0] - c[0][0]) * chord[1] - (p[1] - c[0][1]) * chord[0]))
                / length
                for p in c[1:3]
            )
        )
        # Also split a curve whose controls extend past its chord.
        along = [float(O._dot2(p - c[0], chord)) for p in c[1:3]]
        if error <= 0.01 and all(0 <= v <= length * length for v in along):
            self.points.append(tuple(c[3]))
        else:
            left, right = O._split_at(c, 0.5)
            self._flatten(left)
            self._flatten(right)

    def _closePath(self):
        if self.points:
            self.contours.append(np.array(self.points + [self.points[0]], dtype=float))
        self.points = []

    _endPath = _closePath


def boundary(font, name):
    gs = font.getGlyphSet()
    pen = BoundaryPen(gs)
    gs[name].draw(pen)
    return pen.contours


def directed_distance(source, target):
    """Sample both directions at 0.1-unit intervals, including line ends."""
    if not source:
        return 0.0 if not target else math.inf
    if not target:
        return math.inf
    starts = np.concatenate([c[:-1] for c in target])
    ends = np.concatenate([c[1:] for c in target])
    vectors = ends - starts
    squares = O._dot2(vectors, vectors)
    squares[squares == 0] = 1
    maximum = 0.0
    for contour in source:
        for a, b in pairwise(contour):
            n = max(1, math.ceil(math.hypot(*(b - a)) * 10))
            for i in range(n + 1):
                p = a + (b - a) * (i / n)
                t = np.clip(O._dot2(p - starts, vectors) / squares, 0, 1)
                delta = starts + t[:, None] * vectors - p
                distance = math.sqrt(float(np.min(O._dot2(delta, delta))))
                maximum = max(maximum, distance)
    return maximum


def difference(instance, static, names=None):
    if instance.getGlyphOrder() != static.getGlyphOrder():
        raise ValueError("The instance and static glyph orders differ")
    maximum, worst = 0.0, None
    for name in static.getGlyphOrder() if names is None else names:
        a, b = boundary(instance, name), boundary(static, name)
        if len(a) == len(b) and all(np.array_equal(x, y) for x, y in zip(a, b)):
            continue
        d = max(directed_distance(a, b), directed_distance(b, a))
        if d > maximum:
            maximum, worst = d, name
    # A 0.1-unit sampling step can miss at most 0.05 units. Each flattened
    # boundary can differ by at most 0.01 units. Gate the upper bound.
    return {
        "max_units": maximum + 0.07,
        "sampled_max_units": maximum,
        "glyph": worst,
        "sampling_step_units": 0.1,
        "curve_flatness_units": 0.01,
    }


def endpoint_difference(instance, static):
    """Bound the distance between matching master polylines.

    The distance between corresponding points on two line segments is
    at most the larger endpoint displacement. Thus the largest vertex
    displacement bounds both directed boundary distances, without a
    sampling gap. Keep 0.02 units for the two curve-flattening bounds.
    """
    if instance.getGlyphOrder() != static.getGlyphOrder():
        raise ValueError("The instance and static glyph orders differ")
    maximum, worst = 0.0, None
    for name in static.getGlyphOrder():
        a, b = boundary(instance, name), boundary(static, name)
        if len(a) != len(b) or any(x.shape != y.shape for x, y in zip(a, b)):
            raise ValueError(f"Endpoint structure differs: {name}")
        for x, y in zip(a, b):
            for delta in x - y:
                distance = math.hypot(*delta)
                if distance > maximum:
                    maximum, worst = distance, name
    return {
        "max_units": maximum + 0.02,
        "vertex_bound_units": maximum,
        "glyph": worst,
        "curve_flatness_units": 0.01,
        "method": "Corresponding vertices bound the full flattened boundaries",
    }


def fidelity_report(fonts, styles):
    result = {}
    for style, font in zip(styles, fonts):
        # The raster helper expects disjoint outlines. Resolve nonzero
        # fill on a copy read from the compiled font; keep overlaps in
        # the masters and VF. The reference remains the independent sweep.
        raster_font = deepcopy(font)
        removeOverlaps(raster_font, TOPOLOGY.intersection(font.getGlyphOrder()))
        glyphs = fidelity.compare(style, raster_font)
        maximum, name, ppem = max(
            (v, n, s) for n, row in glyphs.items() for s, v in row.items()
        )
        result[style] = {
            "max": maximum,
            "glyph": name,
            "ppem": int(ppem),
            "pass": all(
                v <= fidelity.TOLERANCE[int(s)]
                for row in glyphs.values()
                for s, v in row.items()
            ),
            "glyphs": glyphs,
        }
        print(
            f"fidelity {style}: {maximum * 100:.3f}% ({name}, {ppem} ppem)", flush=True
        )
    return result


def main(argv=None):
    """Use the full weight ladder; keep the measurement helpers for tests."""
    from vf_ladder import main as ladder_main

    return ladder_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
