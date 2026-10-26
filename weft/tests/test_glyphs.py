"""Tests for the Weft phase 1 generator."""

from __future__ import annotations

import math

import pathops
import pytest

from loom import glyphs as data
from loom.build import ADVANCE, SCALE, UPM, build_font, glyph_contours
from loom.outline import path_contours, signed_area, stroke_polygons


@pytest.fixture(scope="module")
def font():
    return build_font(400)


def contours_of(glyph):
    return [[(p.x, p.y) for p in c.points] for c in glyph.contours]


def union_area(contours) -> float:
    path = pathops.Path()
    pen = path.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for p in c[1:]:
            pen.lineTo(p)
        pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    return sum(signed_area(c) for c in path_contours(path))


def test_scale_maps_units_to_upm():
    assert UPM == 1000
    assert SCALE == 62.5
    assert ADVANCE == 750


def test_stroke_width_formula():
    assert data.stroke_width(100) == pytest.approx(0.6)
    assert data.stroke_width(400) == pytest.approx(1.35)
    assert data.stroke_width(900) == pytest.approx(2.6)


def test_phase1_glyph_set(font):
    expected = {".notdef", "space"} | {data.glyph_name(c) for c in data.PHASE1_CHARS}
    assert set(font.keys()) == expected
    assert len(font) == 64


def test_unicode_values(font):
    for ch in data.PHASE1_CHARS:
        assert font[data.glyph_name(ch)].unicodes == [ord(ch)]
    assert font["space"].unicodes == [0x20, 0xA0]
    assert font[".notdef"].unicodes == []


def test_advance_width_is_constant(font):
    assert {g.width for g in font} == {ADVANCE}


def test_vertical_metrics(font):
    info = font.info
    assert info.unitsPerEm == 1000
    assert info.xHeight == 500
    assert info.capHeight == 688
    assert info.ascender == 719
    assert info.descender == -219
    assert info.openTypeOS2TypoAscender == info.openTypeHheaAscender
    assert info.openTypeOS2TypoDescender == info.openTypeHheaDescender
    assert info.postscriptIsFixedPitch is True


@pytest.mark.parametrize("ch", list(data.STROKES))
def test_every_sketch_glyph_builds(ch):
    contours = glyph_contours(data.STROKES[ch])
    assert contours, f"Glyph {ch!r} has no contours."


@pytest.mark.parametrize("name", [".notdef"] + [data.glyph_name(c) for c in data.PHASE1_CHARS])
def test_contours_closed_and_not_empty(font, name):
    glyph = font[name]
    assert len(glyph.contours) > 0
    for contour in glyph.contours:
        assert len(contour.points) >= 3
        # UFO "line" points with no "move" point make a closed contour.
        assert all(p.type == "line" for p in contour.points)
        assert abs(signed_area([(p.x, p.y) for p in contour.points])) > 0


@pytest.mark.parametrize("name", [".notdef"] + [data.glyph_name(c) for c in data.PHASE1_CHARS])
def test_no_overlaps_remain(font, name):
    contours = contours_of(font[name])
    # Outer contours are counter-clockwise and counters are clockwise, so
    # with no overlap the signed sum equals the area of the union.
    signed = sum(signed_area(c) for c in contours)
    assert signed > 0
    assert union_area(contours) == pytest.approx(signed, abs=1.0)
    # A second simplify must not change the contour count.
    path = pathops.Path()
    pen = path.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for p in c[1:]:
            pen.lineTo(p)
        pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    assert len(list(path.contours)) == len(contours)


def test_space_is_empty(font):
    assert len(font["space"].contours) == 0


def test_stem_width_matches_stroke(font):
    # 'l' stem: centre x = 3.5 in the box, width 1.35 units.
    glyph = font["l"]
    xs = sorted({p.x for c in glyph.contours for p in c.points})
    centre = (3.5 + data.METRICS["box_offset"]) * SCALE
    half = data.stroke_width(400) / 2 * SCALE
    assert min(xs, key=lambda x: abs(x - (centre - half))) == pytest.approx(centre - half, abs=1)
    assert min(xs, key=lambda x: abs(x - (centre + half))) == pytest.approx(centre + half, abs=1)


def test_square_caps_extend_by_half_width():
    polys = stroke_polygons("open", [(0, 0), (0, 10)], 2.0, data.MITER_LIMIT)
    ys = [p[1] for poly in polys for p in poly]
    assert min(ys) == pytest.approx(-1.0)
    assert max(ys) == pytest.approx(11.0)


def test_miter_join_within_limit():
    # A 90 degree corner: ratio 1/sin(45) = 1.414, under 2.4, so miter.
    polys = stroke_polygons("open", [(0, 0), (10, 0), (10, 10)], 2.0, data.MITER_LIMIT)
    pts = {(round(x, 6), round(y, 6)) for poly in polys for x, y in poly}
    assert (11.0, -1.0) in pts


def test_bevel_join_beyond_limit():
    # A 30 degree corner: ratio 1/sin(15) = 3.86, over 2.4, so bevel.
    a = math.radians(30)
    pts_in = [(0, 0), (10, 0), (10 - 10 * math.cos(a), 10 * math.sin(a))]
    polys = stroke_polygons("open", pts_in, 2.0, data.MITER_LIMIT)
    far = max(x for poly in polys for x, _ in poly)
    # The bevel stays within half the width of the vertex plus the
    # segment end; a miter tip would reach 10 + 1/sin(15) = 13.86.
    assert far < 11.5


def test_dot_is_square_of_stroke_width():
    polys = stroke_polygons("dot", [(3.5, 10.6)], 1.35, data.MITER_LIMIT)
    assert len(polys) == 1
    xs = [p[0] for p in polys[0]]
    ys = [p[1] for p in polys[0]]
    assert max(xs) - min(xs) == pytest.approx(1.35)
    assert max(ys) - min(ys) == pytest.approx(1.35)
