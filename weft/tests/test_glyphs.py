"""Tests for the Weft 0.1 generator: glyph data, pieces, masters, statics."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pathops
import pytest

from loom import build as B
from loom import extended as ext
from loom import glyphs as data
from loom import interp, pieces
from loom.outline import glyph_outline, path_contours, signed_area, stroke_polygons

DRAWN_NAMES = B.drawn_names()
SKETCH_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?-–—_/\\|()[]'\"+=*#<>%"
MASTERS = [(w, f) for w in pieces.W_MASTERS for f in pieces.F_MASTERS]


def union(contours) -> pathops.Path:
    path = pathops.Path()
    path.fillType = pathops.FillType.WINDING
    pen = path.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for p in c[1:]:
            pen.lineTo(p)
        pen.closePath()
    path.simplify(fix_winding=True, keep_starting_points=False, clockwise=False)
    return path


def area(path: pathops.Path) -> float:
    return sum(signed_area(c) for c in path_contours(path)) if list(path.contours) else 0.0


@pytest.fixture(scope="module")
def regular():
    return B.build_static(400, "Regular")


@pytest.fixture(scope="module")
def default_master():
    return B.build_master(400, 0)


# ------------------------------------------------------------ metrics, data

def test_scale_maps_units_to_upm():
    assert B.UPM == 1000
    assert B.SCALE == 62.5
    assert B.ADVANCE == 750


def test_stroke_width_formula():
    assert data.stroke_width(100) == pytest.approx(0.6)
    assert data.stroke_width(400) == pytest.approx(1.35)
    assert data.stroke_width(900) == pytest.approx(2.6)
    assert pieces.W_MASTERS == tuple(data.stroke_width(w) for w in B.WGHT_MASTERS)


def test_character_set_covers_scope():
    chars = set(B.charset())
    printable_ascii = {chr(c) for c in range(0x20, 0x7F)}
    assert printable_ascii <= chars
    assert set(SKETCH_CHARS) <= chars
    latin1 = {chr(c) for c in range(0xA0, 0x100)} - {"­"}
    assert latin1 <= chars
    assert set("€’‘“”…•₹") <= chars


def test_every_char_has_one_glyph_name():
    names = [B.glyph_name(c) for c in B.CHARS]
    assert len(names) == len(set(names))


def test_composites_use_existing_glyphs():
    for ch, (base, accent, kind) in ext.COMPOSITES.items():
        assert accent in ext.ACCENTS
        assert base is None or base in B.DRAWN
        assert kind in ("lc", "case", "base")


def test_accent_offset_is_linear_in_width():
    for kind in ("lc", "case"):
        a, b, c = (ext.accent_offset(kind, w, f"acute.{kind}") for w in pieces.W_MASTERS)
        k = (pieces.W_MASTERS[1] - pieces.W_MASTERS[0]) / (pieces.W_MASTERS[2] - pieces.W_MASTERS[0])
        assert b == pytest.approx(a + k * (c - a))


# ----------------------------------------------------------- piece outlines

@pytest.mark.parametrize("name", DRAWN_NAMES)
def test_same_structure_in_every_master(name):
    gp = B.plan(name)
    shapes = {pieces.structure(pieces.glyph_contours(gp, w, f)) for w, f in MASTERS}
    assert len(shapes) == 1, f"Glyph {name!r} has a different point structure between masters."


@pytest.mark.parametrize("name", DRAWN_NAMES)
def test_pieces_are_counter_clockwise_and_closed(name):
    gp = B.plan(name)
    for w in pieces.W_MASTERS:
        for c in pieces.glyph_contours(gp, w, 0):
            assert len(c) >= 3
            assert signed_area(c) > 0, f"Glyph {name!r} has a piece with no area or wrong direction."


@pytest.mark.parametrize("ch", list(data.STROKES))
def test_frag0_union_matches_phase1_outline(ch):
    # At FRAG 0 the union of the pieces is the phase 1 stroke outline.
    gp = pieces.plan_glyph(ch, data.STROKES[ch])
    for w in pieces.W_MASTERS:
        pieces_union = union(pieces.glyph_contours(gp, w, 0))
        ref = glyph_outline(data.STROKES[ch], w, data.MITER_LIMIT)
        xor = pathops.op(pieces_union, ref, pathops.PathOp.XOR)
        assert abs(area(xor)) < 0.02, f"Glyph {ch!r} at w={w}: pieces differ from the stroke outline."


@pytest.mark.parametrize("name", DRAWN_NAMES)
def test_frag15_notches_only_remove_ink(name):
    gp = B.plan(name)
    w = data.stroke_width(400)
    clean = union(pieces.glyph_contours(gp, w, 0))
    notched = union(pieces.glyph_contours(gp, w, 15))
    added = pathops.op(notched, clean, pathops.PathOp.DIFFERENCE)
    assert abs(area(added)) < 1e-3
    loss = area(clean) - area(notched)
    assert loss >= -1e-6
    # Notches are small: less than 6 % of the ink.
    assert loss <= 0.06 * area(clean) + 1e-6


def test_notches_exist_at_corners_and_tees():
    assert B.plan("T").notches, "T must have T-junction notches."
    assert B.plan("L").notches, "L must have a corner notch."
    assert not B.plan("o").notches, "o has only 135 degree corners: no notch."


@pytest.mark.parametrize("name", DRAWN_NAMES)
def test_cuts_are_narrower_than_the_stroke(name):
    gp = B.plan(name)
    for w in pieces.W_MASTERS:
        for f in (15, 30, 50, 100):
            for si, sp in enumerate(gp.strokes):
                if sp.kind == "dot":
                    continue
                for _, _, gap in pieces._stroke_cutpos(gp, si, w, f):
                    assert gap < w


def test_cuts_closed_at_frag15_and_open_at_frag50():
    gp = B.plan("T")
    w = data.stroke_width(400)
    assert any(sp.cuts for sp in gp.strokes)
    for si, sp in enumerate(gp.strokes):
        for _, _, gap in pieces._stroke_cutpos(gp, si, w, 15):
            assert gap < 0  # overlap: closed
    gaps50 = [g for si in range(len(gp.strokes)) for _, _, g in pieces._stroke_cutpos(gp, si, w, 50)]
    assert any(g > 0 for g in gaps50)


def test_frag_plan_is_reproducible():
    a = pieces.glyph_contours(pieces.plan_glyph("g", data.STROKES["g"]), 1.35, 70)
    b = pieces.glyph_contours(pieces.plan_glyph("g", data.STROKES["g"]), 1.35, 70)
    assert a == b


def test_drift_is_on_quarter_grid():
    for direction in ((1.0, 0.0), (0.6, 0.8)):
        dx, dy = pieces._drift(direction, 1.35, 0.9, 0.2)
        assert (dx / 0.25).is_integer() and (dy / 0.25).is_integer()


def test_drift_lock_is_current():
    lock = json.loads((Path(B.__file__).with_name("drift_lock.json")).read_text())
    assert lock["seed"] == pieces.SEED
    for name in ("a", "bullet", "zero", "T"):
        gp = B.plan(name)
        assert gp.attempt == lock["attempts"].get(name, 0)
        assert not interp.problems(gp, B.to_font), f"Run tools/relock.py: {name!r} fails."


# ------------------------------------------------------------------ masters

def test_master_glyph_set(default_master):
    assert list(default_master.keys()) == B.glyph_order() or set(default_master.keys()) == set(B.glyph_order())
    for ch in B.CHARS:
        assert default_master[B.glyph_name(ch)].unicodes == [ord(ch)]
    assert default_master["space"].unicodes == [0x20, 0xA0]


def test_master_advance_is_constant(default_master):
    assert {g.width for g in default_master} == {B.ADVANCE}


def test_composites_have_components(default_master):
    g = default_master["Aacute"]
    assert [c.baseGlyph for c in g.components] == ["A", "acute.case"]
    assert not g.contours
    assert default_master["idieresis"].components[0].baseGlyph == "dotlessi"


@pytest.mark.parametrize("accent", [a for a in ext.ACCENTS if not a.startswith("cedilla")])
def test_accents_clear_the_base(accent):
    # The accent ink must start above the base ink at every weight. A
    # slanted accent has square caps that reach a little below w / 2.
    kind = accent.split(".")[1]
    top = ext.ACCENT_BASE_TOP[kind]
    for w in pieces.W_MASTERS:
        cs = pieces.glyph_contours(B.plan(accent), w, 0)
        low = min(y for c in cs for _, y in c) + ext.accent_offset(kind, w, accent)
        assert low - (top + w / 2) == pytest.approx(ext.ACCENT_GAP[kind], abs=0.02)


# ------------------------------------------------------------------ statics

def test_static_glyph_set(regular):
    expected = set(B.glyph_order()) - set(ext.ACCENTS)
    assert set(regular.keys()) == expected


def test_static_advance_is_constant(regular):
    assert {g.width for g in regular} == {B.ADVANCE}


@pytest.mark.parametrize("name", [n for n in B.glyph_order() if n not in ext.ACCENTS and n != "space"])
def test_static_has_no_overlaps(regular, name):
    contours = [[(p.x, p.y) for p in c.points] for c in regular[name].contours]
    assert contours, f"Glyph {name!r} is empty."
    signed = sum(signed_area(c) for c in contours)
    assert signed > 0
    assert area(union(contours)) == pytest.approx(signed, abs=1.0)


def test_static_names_and_weight():
    for wght, style in B.STATICS:
        f = B.build_static(wght, style) if style in ("Thin", "Bold") else None
        if f is None:
            continue
        assert f.info.openTypeOS2WeightClass == wght
        assert f.info.postscriptFontName == f"MachineMadeWeft-{style}"
        assert f.info.familyName == "machine-made Weft"
        if style == "Bold":
            assert f.info.styleMapStyleName == "bold"
            assert f.info.styleMapFamilyName == "machine-made Weft"
        else:
            assert f.info.styleMapFamilyName == f"machine-made Weft {style}"


def test_vertical_metrics(regular):
    info = regular.info
    assert info.unitsPerEm == 1000
    assert info.xHeight == 500
    assert info.capHeight == 688
    assert info.openTypeOS2TypoAscender == info.openTypeHheaAscender
    assert info.openTypeOS2TypoDescender == info.openTypeHheaDescender
    assert info.postscriptIsFixedPitch is True
    assert info.openTypeOS2Panose[3] == 9


def test_stem_width_matches_stroke(regular):
    glyph = regular["l"]
    xs = sorted({p.x for c in glyph.contours for p in c.points})
    centre = (3.5 + data.METRICS["box_offset"]) * B.SCALE
    half = data.stroke_width(400) / 2 * B.SCALE
    assert min(xs, key=lambda x: abs(x - (centre - half))) == pytest.approx(centre - half, abs=1)
    assert min(xs, key=lambda x: abs(x - (centre + half))) == pytest.approx(centre + half, abs=1)


# ------------------------------------------------------ outline primitives

def test_square_caps_extend_by_half_width():
    polys = stroke_polygons("open", [(0, 0), (0, 10)], 2.0, data.MITER_LIMIT)
    ys = [p[1] for poly in polys for p in poly]
    assert min(ys) == pytest.approx(-1.0)
    assert max(ys) == pytest.approx(11.0)


def test_miter_join_within_limit():
    polys = stroke_polygons("open", [(0, 0), (10, 0), (10, 10)], 2.0, data.MITER_LIMIT)
    pts = {(round(x, 6), round(y, 6)) for poly in polys for x, y in poly}
    assert (11.0, -1.0) in pts


def test_bevel_join_beyond_limit():
    a = math.radians(30)
    pts_in = [(0, 0), (10, 0), (10 - 10 * math.cos(a), 10 * math.sin(a))]
    polys = stroke_polygons("open", pts_in, 2.0, data.MITER_LIMIT)
    far = max(x for poly in polys for x, _ in poly)
    assert far < 11.5


def test_dot_is_square_of_stroke_width():
    gp = pieces.plan_glyph("period", data.STROKES["."])
    (c,) = pieces.glyph_contours(gp, 1.35, 0)
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    assert max(xs) - min(xs) == pytest.approx(1.35)
    assert max(ys) - min(ys) == pytest.approx(1.35)
