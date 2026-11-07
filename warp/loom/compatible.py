# SPDX-License-Identifier: Apache-2.0
"""Two fixed-structure experiments for the Regular/Bold pair. Apache-2.0.

Contours are ordered by winding and position. Each starts at its
lowest segment end. Arc fractions, rather than nearby point indices, give
the correspondence. A change in contour count or winding is left visible.
No contour is added or removed to make the masters agree.
"""

from __future__ import annotations

import bisect
import math
from functools import cache
from itertools import pairwise

import numpy as np

from loom import outline as O


def polygon(contour):
    """Read curves with dense parameter samples and keep all line ends."""
    points, ends = [], []
    for s in contour:
        ends.append(len(points))
        if s[0] == "line":
            points.append(s[1])
        else:
            c = s[1]
            length = sum(math.hypot(*(c[i + 1] - c[i])) for i in range(3))
            n = max(4, math.ceil(length * 2))
            points.extend(O._bez(c, [i / n for i in range(n)]))
    return np.array(points), ends


def contour_key(points):
    """Order contours from bottom to top, then left to right, per winding."""
    area = O.signed_area(points)
    x = (min(float(p[0]) for p in points) + max(float(p[0]) for p in points)) / 2
    y = (min(float(p[1]) for p in points) + max(float(p[1]) for p in points)) / 2
    return area < 0, math.floor(y + 0.5), math.floor(x + 0.5), -abs(area)


def canonical(contours):
    result = []
    for contour in contours:
        starts = [s[1] if s[0] == "line" else s[1][0] for s in contour]
        first = min(
            range(len(starts)), key=lambda i: (float(starts[i][1]), float(starts[i][0]))
        )
        contour = contour[first:] + contour[:first]
        p, ends = polygon(contour)
        area = O.signed_area(p)
        result.append((area, contour, p, ends))
    result.sort(key=lambda c: contour_key(c[2]))
    return result


class Arc:
    def __init__(self, points, ends):
        self.points = np.vstack([points, points[:1]])
        lengths = [0.0]
        for a, b in zip(self.points, self.points[1:]):
            lengths.append(lengths[-1] + math.hypot(*(b - a)))
        self.length = lengths[-1]
        self.fractions = [v / self.length for v in lengths]
        self.ends = [self.fractions[i] for i in ends] + [1.0]

    def at(self, t):
        i = min(bisect.bisect_right(self.fractions, t) - 1, len(self.points) - 2)
        lo, hi = self.fractions[i : i + 2]
        u = (t - lo) / (hi - lo) if hi > lo else 0.0
        return self.points[i] + u * (self.points[i + 1] - self.points[i])


def fit_pair(a, b, method):
    aa, bb = Arc(a[2], a[3]), Arc(b[2], b[3])
    if method == "refit":
        # Keep the Regular segment boundaries. Fit one cubic on each run
        # in each master, with no error-dependent split.
        breaks = aa.ends
        result = []
        for arc in (aa, bb):
            contour = []
            for lo, hi in pairwise(breaks):
                points = np.array([arc.at(lo + (hi - lo) * i / 16) for i in range(17)])
                ctrl = O._generate(
                    points,
                    O._chord_params(points),
                    O._unit(points[1] - points[0]),
                    O._unit(points[-2] - points[-1]),
                )
                contour.append(("curve", ctrl))
            result.append(contour)
        return result
    if method != "sample":
        raise ValueError(f"Unknown outline method: {method}")
    # Include both sets of segment ends so that corners stay sharp. Use
    # the same arc fractions at intervals of at most two units in either
    # master. This is a feasibility test, not a point-count optimisation.
    n = max(4, math.ceil(max(aa.length, bb.length) / 2))
    breaks = sorted(set(aa.ends + bb.ends + [i / n for i in range(n)]))[:-1]
    points = [[arc.at(t) for t in breaks] for arc in (aa, bb)]

    # Drop only points which round to the previous point in BOTH masters.
    # A one-master cleanup would break the common structure.
    def rounded(p):
        return tuple(math.floor(float(v) + 0.5) for v in p)

    keep = []
    for i in range(len(breaks)):
        if not keep or any(rounded(p[i]) != rounded(p[keep[-1]]) for p in points):
            keep.append(i)
    if len(keep) > 1 and all(
        rounded(p[keep[-1]]) == rounded(p[keep[0]]) for p in points
    ):
        keep.pop()
    return [
        [("line", p[i], p[keep[(k + 1) % len(keep)]]) for k, i in enumerate(keep)]
        for p in points
    ]


@cache
def pair(name, method="sample"):
    from loom.build import drawn

    originals = [drawn(style, name).contours for style in ("Regular", "Bold")]
    a, b = [canonical(cs) for cs in originals]
    if len(a) != len(b) or any((ca[0] > 0) != (cb[0] > 0) for ca, cb in zip(a, b)):
        return originals
    result = [[], []]
    for ca, cb in zip(a, b):
        for out, contour in zip(result, fit_pair(ca, cb, method)):
            out.append(contour)
    return result
