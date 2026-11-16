# SPDX-License-Identifier: Apache-2.0
"""Fixed outline structure for the text weight ladder. Apache-2.0.

Contours are ordered by winding and position. Each starts at its
lowest segment end. Arc fractions, rather than nearby point indices, give
the correspondence. A change in contour count or winding is left visible.
For the few shapes whose union changes topology, keep stroke groups
separate in all masters. Their overlaps remain ink under nonzero fill.
The ladder keeps the frozen Roman endpoints and uses their arc samples
at the other weights. Italic weights use the same rule on their own forms.
"""

from __future__ import annotations

import bisect
import math
from functools import cache
from itertools import pairwise

import numpy as np
import pathops

from loom import outline as O

TOPOLOGY = frozenset(
    (
        "germandbls",
        "f_f",
        "fi",
        "fl",
        "f_f_i",
        "f_f_l",
        "gamma",
        "kappa",
        "dieresistonos",
        "dieresistonoscomb",
        "u1D43F",
        "u1D6FE",
        "u1D705",
    )
)
ITALIC_TOPOLOGY = TOPOLOGY | frozenset(
    ("L", "Lslash", "hungarumlautcomb.case", "l.sc", "hbar.sc", "lslash.sc")
)

# A batch union loses ink at an interior weight; preserve the source stroke.
UNION_REPAIRS = frozenset(("iota",))


class CompatibilityError(ValueError):
    """A structure mismatch with the measured glyph and weight details."""

    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def stroke_groups(d, name):
    """Keep each stroke and each terminal from the original sweep.

    Compose emits one hull per pair of stroke samples, then dots and
    fills. Split gamma at the bottom node of its loop: the two runs
    overlap at the shared nib, but neither run closes its own counter.
    No hull is moved, dropped, or copied.
    """
    sw = d.sweep
    groups, offset = [], 0
    for i, stroke in enumerate(sw.strokes):
        count = max(1, len(stroke["pts"]) - 1)
        hulls = sw.polys[offset : offset + count]
        offset += count
        if name in ("gamma", "u1D6FE") and i == 0:
            node = stroke["nodes"][3]
            cut = next(j for j, p in enumerate(stroke["pts"]) if p[:2] == node)
            groups.extend((hulls[:cut], hulls[cut:]))
        else:
            groups.append(hulls)
    groups.extend([poly] for poly in sw.polys[offset:])
    return groups


def stroke_contours(d, name):
    result = []
    for group in stroke_groups(d, name):
        for points in O.path_polygons(O.union(group)):
            # Keep the small brackets too. Use their polygon edges so no
            # fit can remove a narrow piece at a stroke junction.
            points = points + (d.dx, 0)
            result.append(
                [
                    ("line", p, points[(i + 1) % len(points)])
                    for i, p in enumerate(points)
                ]
            )
    return result


def incremental_stroke_contours(d, name):
    """Union each stroke's hulls one at a time, keeping their fixed order.

    A batch union can cancel ink at coincident edges. The incremental
    union keeps every source hull and leaves the frozen endpoints alone.
    """
    contours = []
    for group in stroke_groups(d, name):
        path = pathops.Path()
        path.fillType = pathops.FillType.WINDING
        for hull in group:
            path = pathops.op(path, O.union([hull]), pathops.PathOp.UNION)
        for points in O.path_polygons(path):
            if abs(O.signed_area(points)) >= O.MIN_AREA:
                contours.append(lines(points + (d.dx, 0)))
    return contours


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


def canonical(contours, keep_order=False):
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
    if not keep_order:
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


def lines(points):
    """Close one polygon without changing its vertices."""
    return [("line", p, points[(i + 1) % len(points)]) for i, p in enumerate(points)]


def sample_like(reference, contour):
    """Use the frozen Regular arc fractions on another weight."""
    points = np.array([s[1] for s in reference])
    source = Arc(points, list(range(len(points))))
    target = Arc(contour[2], contour[3])
    return lines([target.at(t) for t in source.fractions[:-1]])


def match_contours(reference, contours):
    """Keep contour identity when two vertical centres cross with weight.

    Match winding, size and centre. A rounded vertical sort alone can
    exchange a large ring with the small bar inside it.
    """

    def box(c):
        p = c[2]
        x0, y0 = min(float(q[0]) for q in p), min(float(q[1]) for q in p)
        x1, y1 = max(float(q[0]) for q in p), max(float(q[1]) for q in p)
        return (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0

    a, b = [box(c) for c in reference], [box(c) for c in contours]
    costs = []
    for i, ca in enumerate(reference):
        row = []
        for j, cb in enumerate(contours):
            if (ca[0] > 0) == (cb[0] > 0):
                cost = sum((x - y) * (x - y) for x, y in zip(a[i], b[j]))
            else:
                cost = math.inf
            row.append(cost)
        costs.append(row)
    if len(reference) != len(contours):
        raise ValueError("Cannot match contour winding and count")
    return [contours[j] for j in minimum_assignment(costs)]


def minimum_assignment(costs):
    """Find the least total cost, without a greedy exchange of nearby dots.

    The augmenting paths use scalar arithmetic in a fixed order. Equal
    costs choose the first column, so the result is repeatable.
    """
    n = len(costs)
    u, v = [0.0] * (n + 1), [0.0] * (n + 1)
    p, way = [0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minimum, used = [math.inf] * (n + 1), [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], math.inf, 0
            for j in range(1, n + 1):
                if not used[j]:
                    cost = costs[i0 - 1][j - 1] - u[i0] - v[j]
                    if cost < minimum[j]:
                        minimum[j], way[j] = cost, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            if not math.isfinite(delta):
                raise ValueError("Cannot match contour winding and count")
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0], j0 = p[j1], j1
    result = [0] * n
    for j in range(1, n + 1):
        result[p[j] - 1] = j - 1
    return result


def aligned_start(reference, points):
    """Find a cyclic start by squared vertex distance, with fixed-order sums.

    First sample 64 vertices for every possible start. Then compare all
    vertices near the best sampled starts. Only the order changes.
    """
    n = len(points)
    if n != len(reference):
        raise ValueError("Cannot align contours with different point counts")
    if n < 2:
        return 0
    a, b = np.asarray(reference, dtype=float), np.asarray(points, dtype=float)
    indices = np.array(sorted({i * n // 64 for i in range(64)}))
    costs = []
    for shift in range(n):
        delta = a[indices] - b[(indices + shift) % n]
        costs.append(O._sum(delta * delta))
    candidates = {0}
    for shift in sorted(range(n), key=lambda i: (costs[i], i))[:4]:
        candidates.update((shift + d) % n for d in range(-4, 5))

    def cost(shift):
        delta = a - np.roll(b, -shift, axis=0)
        return O._sum(delta * delta), shift

    return min(candidates, key=cost)


@cache
def ladder(name, italic=False):
    """Keep the old Roman endpoints; sample new weights on their structure."""
    from loom import build as B

    styles = [B.weight_style(w, italic) for w in B.MASTER_WEIGHTS]
    regular_index = B.MASTER_WEIGHTS.index(400)
    bold_index = B.MASTER_WEIGHTS.index(700)
    originals = []
    separate = name in (ITALIC_TOPOLOGY if italic else TOPOLOGY)
    for style in styles:
        d = B.drawn(style, name)
        if (
            name in UNION_REPAIRS
            and not italic
            and B.STYLES[style].weight not in (400, 700)
        ):
            originals.append(incremental_stroke_contours(d, name))
        else:
            originals.append(stroke_contours(d, name) if separate else d.contours)
    ordered = [canonical(cs, keep_order=separate) for cs in originals]
    signatures = [[c[0] > 0 for c in cs] for cs in ordered]
    if any(s != signatures[regular_index] for s in signatures):
        raise CompatibilityError(
            f"{name}: contour topology differs at {dict(zip(styles, signatures))}",
            [
                {
                    "glyph": name,
                    "style": style,
                    "weight": B.STYLES[style].weight,
                    "contours": len(cs),
                    "winding": [1 if c[0] > 0 else -1 for c in cs],
                    "points": [len(c[2]) for c in cs],
                }
                for style, cs in zip(styles, ordered)
            ],
        )
    if separate:
        # Each retained stroke already has an identity in the sweep.
        order = sorted(
            range(len(ordered[regular_index])),
            key=lambda i: contour_key(ordered[regular_index][i][2]),
        )
        ordered = [[cs[i] for i in order] for cs in ordered]
    else:
        for i in range(len(styles)):
            if i == regular_index or (not italic and i == bold_index):
                continue
            ordered[i] = match_contours(ordered[regular_index], ordered[i])
    if not italic:
        regular, bold = pair(name)
    else:
        regular, bold = [], []
        for a, b in zip(ordered[regular_index], ordered[bold_index]):
            ra, rb = fit_pair(a, b, "sample")
            regular.append(ra)
            bold.append(rb)
    result = []
    for i, contours in enumerate(ordered):
        if i == regular_index:
            result.append(regular)
        elif i == bold_index:
            result.append(bold)
        else:
            result.append([sample_like(ref, c) for ref, c in zip(regular, contours)])
    return result


@cache
def pair(name, method="sample"):
    from loom.build import drawn

    originals = [drawn(style, name).contours for style in ("Regular", "Bold")]
    if name in TOPOLOGY:
        originals = [
            stroke_contours(drawn(style, name), name) for style in ("Regular", "Bold")
        ]
    a, b = [canonical(cs) for cs in originals]
    if len(a) != len(b) or any((ca[0] > 0) != (cb[0] > 0) for ca, cb in zip(a, b)):
        return originals
    result = [[], []]
    for ca, cb in zip(a, b):
        for out, contour in zip(result, fit_pair(ca, cb, method)):
            out.append(contour)
    return result
