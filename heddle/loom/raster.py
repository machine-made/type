"""A small nonzero rasteriser, to check overlap removal.

pathops (Skia) can fail on curves that nearly coincide, for example
where the two rings of S share the spine. This module fills the raw
contours with the nonzero rule (no Boolean operations) and fills a
union result, so that the build can compare the two.

Apache-2.0.
"""

from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw

from loom.geom import signed_area

PX = 4.0                         # font units per pixel
BOX = (-400, -450, 1900, 1350)   # x0, y0, x1, y1 in font units


def _size():
    return int((BOX[2] - BOX[0]) / PX), int((BOX[3] - BOX[1]) / PX)


def _tr(p):
    return ((p[0] - BOX[0]) / PX, (BOX[3] - p[1]) / PX)


def _flatten(contour, steps: int = 12) -> list:
    """Points of a contour [(x, y, on), ...] as a polygon."""
    n = len(contour)
    out = [contour[0][:2]]
    i = 1
    while i <= n:
        p = contour[i % n]
        if p[2]:
            out.append(p[:2])
            i += 1
        else:
            p0 = out[-1]
            c1, c2, p3 = contour[i % n], contour[(i + 1) % n], contour[(i + 2) % n]
            for k in range(1, steps + 1):
                t = k / steps
                m = 1 - t
                out.append((m ** 3 * p0[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t ** 3 * p3[0],
                            m ** 3 * p0[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t ** 3 * p3[1]))
            i += 3
    return out


def nonzero_mask(contours) -> Image.Image:
    """Fill raw loom contours with the nonzero rule. Returns a mode "1" mask.

    Loom contours come in groups: a counter-clockwise contour, then the
    clockwise counter of the same ring, if any. Nonzero fill of such a
    list is the union of (outer minus counter) over the groups.
    """
    size = _size()
    out = Image.new("1", size, 0)
    ones = Image.new("1", size, 1)
    group = None
    for c in list(contours) + [None]:
        if c is not None and signed_area(c) < 0 and group is not None:
            layer = Image.new("1", size, 0)
            ImageDraw.Draw(layer).polygon([_tr(p) for p in _flatten(c)], fill=1)
            group = ImageChops.logical_and(group, ImageChops.logical_xor(layer, ones))
            continue
        if group is not None:
            out = ImageChops.logical_or(out, group)
            group = None
        if c is None:
            break
        if signed_area(c) < 0:
            raise ValueError("A clockwise contour without a ring before it.")
        group = Image.new("1", size, 0)
        poly = [_tr(p) for p in _flatten(c)]
        if len(poly) >= 3:
            ImageDraw.Draw(group).polygon(poly, fill=1)
    return out


def path_mask(path) -> Image.Image:
    """Fill an overlap-free pathops path (even-odd: each contour flips)."""
    from fontTools.pens.recordingPen import RecordingPen

    rec = RecordingPen()
    path.draw(rec)
    mask = Image.new("1", _size(), 0)
    contour = []
    for op, args in rec.value:
        if op == "moveTo":
            contour = [(*args[0], True)]
        elif op == "lineTo":
            contour.append((*args[0], True))
        elif op == "curveTo":
            contour += [(*args[0], False), (*args[1], False), (*args[2], True)]
        elif op in ("closePath", "endPath"):
            if contour and contour[-1][:2] == contour[0][:2] and len(contour) > 1:
                contour = contour[:-1] if contour[-1][2] else contour
            poly = [_tr(p) for p in _flatten(contour)] if len(contour) >= 2 else []
            if len(poly) >= 3:
                layer = Image.new("1", mask.size, 0)
                ImageDraw.Draw(layer).polygon(poly, fill=1)
                mask = ImageChops.logical_xor(mask, layer)
            contour = []
    return mask


def count(mask: Image.Image) -> int:
    return mask.convert("L").histogram()[255]


def mismatch(a: Image.Image, b: Image.Image) -> int:
    """Pixels that differ, after ignoring a one-pixel edge."""
    from PIL import ImageFilter

    x = ImageChops.logical_xor(a, b).convert("L").filter(ImageFilter.MinFilter(3))
    return x.histogram()[255]
