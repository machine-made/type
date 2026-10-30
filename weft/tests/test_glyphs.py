"""Tests for the Weft generator: glyph data, pieces, masters, statics."""

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


def test_character_set_covers_weft_02_scope():
    chars = set(B.charset())
    latin_ext_a = {chr(c) for c in range(0x100, 0x180)}
    assert latin_ext_a <= chars, sorted(latin_ext_a - chars)
    assert set("ȘșȚț") <= chars
    assert set("£¥§¶±×÷¢½¼¾") <= chars
    assert set("─│┌┐└┘├┤┬┴┼") <= chars
    assert set("←→↑↓") <= chars
    assert set("‹›‚„−ˆˇ˘˙˚˛˜˝") <= chars
    combining = {chr(c) for c in (0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307,
                                  0x308, 0x30A, 0x30B, 0x30C, 0x326, 0x327, 0x328)}
    assert combining <= chars


# Characters each language needs beyond ASCII (Central European and
# Baltic languages, Turkish and Romanian; the 0.2 target).
LANGUAGES = {
    "Polish": "ĄąĆćĘęŁłŃńÓóŚśŹźŻż",
    "Czech": "ÁáČčĎďÉéĚěÍíŇňÓóŘřŠšŤťÚúŮůÝýŽž",
    "Slovak": "ÁáÄäČčĎďÉéÍíĹĺĽľŇňÓóÔôŔŕŠšŤťÚúÝýŽž",
    "Hungarian": "ÁáÉéÍíÓóÖöŐőÚúÜüŰű",
    "Romanian": "ĂăÂâÎîȘșȚț",
    "Turkish": "ÇçĞğİıÖöŞşÜü",
    "Croatian": "ČčĆćĐđŠšŽž",
    "Slovenian": "ČčŠšŽž",
    "Latvian": "ĀāČčĒēĢģĪīĶķĻļŅņŠšŪūŽž",
    "Lithuanian": "ĄąČčĘęĖėĮįŠšŲųŪūŽž",
    "Estonian": "ÄäÕõÖöÜüŠšŽž",
    "Maltese": "ĊċĠġĦħŻż",
    "Esperanto": "ĈĉĜĝĤĥĴĵŜŝŬŭ",
}


@pytest.mark.parametrize("language", sorted(LANGUAGES))
def test_language_coverage(language):
    missing = set(LANGUAGES[language]) - set(B.charset())
    assert not missing, f"{language} needs {sorted(missing)}."


def test_every_char_has_one_glyph_name():
    names = [B.glyph_name(c) for c in B.CHARS]
    assert len(names) == len(set(names))


def test_composites_use_existing_glyphs():
    for ch, (base, accent, kind, dx) in ext.COMPOSITES.items():
        assert accent in ext.ACCENTS
        assert base is None or base in B.DRAWN
        assert kind in ("lc", "case", "asc", "base", "below", "abs")
    for ch, (single, dx) in ext.COMPOUNDS.items():
        assert single in B.DRAWN


def test_master_widths_match():
    assert ext.W_MASTERS == pieces.W_MASTERS


COMPOSITE_CHARS = list(ext.COMPOSITES) + list(ext.COMPOUNDS)


@pytest.mark.parametrize("ch", COMPOSITE_CHARS)
def test_component_offsets_are_piecewise_linear(ch):
    # The variable font interpolates component offsets linearly between
    # masters. The statics compute them at their own width. Both agree
    # only if the offsets are linear between the master widths.
    ws = pieces.W_MASTERS
    for w0, w1 in zip(ws, ws[1:]):
        a, b, m = ext.parts(ch, w0), ext.parts(ch, w1), ext.parts(ch, (w0 + w1) / 2)
        for pa, pb, pm in zip(a, b, m):
            assert pm[1] == pytest.approx((pa[1] + pb[1]) / 2)
            assert pm[2] == pytest.approx((pa[2] + pb[2]) / 2)


def test_accent_scale_keeps_stroke_width():
    # A scaled accent is drawn at w / s and scaled by s: a dot stays w wide.
    for w in pieces.W_MASTERS:
        (c,) = B.contours("dotaccent.case", w, 0)
        xs = [p[0] for p in c]
        assert max(xs) - min(xs) == pytest.approx(w)
    assert ext.accent_scale("acute.case", pieces.W_MASTERS[2]) > 1.0


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
    for name in ("a", "bullet", "zero", "T", "l", "I", "one", "ring.case", "uni253C", "OE", "zero.ss01"):
        gp = B.plan(name)
        assert gp.attempt == lock["attempts"].get(name, 0)
        assert not interp.problems(gp, B.to_font, contours=B.plan_contours), \
            f"Run tools/relock.py: {name!r} fails."


# ------------------------------------------------------------------ masters

def test_master_glyph_set(default_master):
    assert list(default_master.keys()) == B.glyph_order() or set(default_master.keys()) == set(B.glyph_order())
    for ch in B.CHARS:
        assert default_master[B.glyph_name(ch)].unicodes == [ord(ch)]
    assert default_master["space"].unicodes == [0x20, 0xA0]


def test_master_advance_is_constant(default_master):
    # Every glyph is 750 wide, except the combining marks (0).
    for g in default_master:
        assert g.width == (0 if g.name in B.mark_names() else B.ADVANCE), g.name
    assert len(B.mark_names()) == len(ext.COMBINING)


def test_composites_have_components(default_master):
    g = default_master["Aacute"]
    assert [c.baseGlyph for c in g.components] == ["A", "acute.case"]
    assert not g.contours
    assert default_master["idieresis"].components[0].baseGlyph == "dotlessi"
    assert [c.baseGlyph for c in default_master["guillemotleft"].components] == ["guilsinglleft"] * 2
    assert [c.baseGlyph for c in default_master["quotedbl"].components] == ["quotesingle"] * 2
    assert [c.baseGlyph for c in default_master["uni0219"].components] == ["s", "commabelow.mark"]


@pytest.mark.parametrize("accent", [a for a in ext.ACCENTS if ext.is_scaled(a)])
def test_accents_clear_the_base(accent):
    # The accent ink must start gap(w) above the base ink at every weight.
    # A slanted accent has square caps that reach a little below w / 2.
    kind = accent.split(".")[1]
    top = ext.ACCENT_BASE_TOP[kind]
    for w in pieces.W_MASTERS:
        cs = B.contours(accent, w, 0)
        low = min(y for c in cs for _, y in c) + ext.accent_offset(kind, w, accent)
        assert low - (top + w / 2) == pytest.approx(ext.pwl(w, ext.ACCENT_GAP[kind]), abs=0.02)


def _part_unions(ch, w):
    out = []
    for part, dx, dy in ext.parts(ch, w):
        out.append(union([[(x + dx, y + dy) for x, y in c] for c in B.contours(B.part_name(part), w, 0)]))
    return out


DETACHED = [ch for ch, (base, accent, kind, dx) in ext.COMPOSITES.items()
            if base is not None and kind in ("lc", "case", "asc", "below", "abs")] + list(ext.COMPOUNDS)


@pytest.mark.parametrize("ch", DETACHED)
def test_marks_do_not_touch(ch):
    # Marks above and below, the vertical caron, and the two halves of a
    # guillemet or a double quote stay apart at every master weight.
    for w in pieces.W_MASTERS:
        a, b = _part_unions(ch, w)
        both = pathops.op(a, b, pathops.PathOp.INTERSECTION)
        assert abs(area(both)) < 1e-6, f"{ch!r} touches at w={w}."
        # And at least 0.3 units apart (about 19 font units).
        grown = union([[(x + dx, y + dy) for x, y in c] for c in path_contours(b)
                       for dx, dy in ((0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3))])
        near = pathops.op(a, grown, pathops.PathOp.INTERSECTION)
        assert abs(area(near)) < 1e-6, f"{ch!r} parts are closer than 0.3 units at w={w}."


ATTACHED = [ch for ch, (base, accent, kind, dx) in ext.COMPOSITES.items()
            if base is not None and kind == "base"]


@pytest.mark.parametrize("ch", ATTACHED)
def test_cedilla_and_ogonek_attach(ch):
    for w in pieces.W_MASTERS:
        a, b = _part_unions(ch, w)
        assert area(pathops.op(a, b, pathops.PathOp.INTERSECTION)) > 0, f"{ch!r} mark floats at w={w}."


def test_new_glyphs_stay_in_the_cell():
    # Weft 0.2 glyphs keep their ink inside the 12-unit cell at FRAG 0
    # (a small tolerance for the d with caron at Black).
    new = [c for c in B.CHARS if ord(c) >= 0x100 and c not in "…•€₹’‘“”—–" and c not in ext.COMBINING]
    for w in pieces.W_MASTERS:
        for ch in new:
            name = B.glyph_name(ch)
            ch_comp = B.composite_char(name)
            if ch_comp:
                pts = [(x + dx, y) for part, dx, dy in ext.parts(ch_comp, w)
                       for c in B.contours(B.part_name(part), w, 0) for x, y in c]
            else:
                pts = [p for c in B.contours(name, w, 0) for p in c]
            xs = [x + B.BOX for x, _ in pts]
            assert min(xs) >= -0.35 and max(xs) <= 12.05, \
                f"{ch!r} leaves the cell at w={w}: {min(xs):.2f} {max(xs):.2f}."


BOX_CHARS = "─│┌┐└┘├┤┬┴┼"


@pytest.mark.parametrize("ch", list(BOX_CHARS))
def test_box_drawing_ends_on_the_cell_edges(ch):
    # Lines end exactly on the cell edges, so neighbours join.
    name = B.glyph_name(ch)
    for w in pieces.W_MASTERS:
        pts = [p for c in B.contours(name, w, 0) for p in c]
        xs = [B.to_font(p)[0] for p in pts]
        ys = [B.to_font(p)[1] for p in pts]
        horizontal = ch in "─┌┐└┘├┤┬┴┼"
        vertical = ch in "│┌┐└┘├┤┬┴┼"
        left = ch in "─┐┘┤┬┴┼"
        right = ch in "─┌└├┬┴┼"
        up = ch in "│└┘├┤┴┼"
        down = ch in "│┌┐├┤┬┼"
        assert (min(xs) == 0) == left and (max(xs) == B.ADVANCE) == right
        assert (min(ys) == B.u(B.TYPO_DESCENDER)) == down and (max(ys) == B.u(B.TYPO_ASCENDER)) == up
        assert horizontal or vertical


def test_combining_marks(default_master):
    # Combining marks: no advance, over the previous cell, with an anchor
    # that matches the anchor of the base letters (mark feature).
    for ch, (accent, anchor) in ext.COMBINING.items():
        g = default_master[B.glyph_name(ch)]
        assert g.unicodes == [ord(ch)]
        assert g.width == 0
        b = g.getBounds(default_master)
        assert b.xMax <= 0 < b.xMax + B.ADVANCE
        assert [a.name for a in g.anchors] == [f"_{anchor}"]
    for ch in "AaHhgx":
        names = {a.name for a in default_master[B.glyph_name(ch)].anchors}
        assert {"top", "bottom", "cedilla"} <= names
    assert {a.name for a in default_master["A"].anchors} >= {"ogonek"}
    assert "sub i' @TOP_MARKS by dotlessi;" in default_master.features.text
    assert default_master.lib["public.openTypeCategories"]["acutecomb"] == "mark"


def test_dotted_zero_is_ss01(default_master):
    assert "zero.ss01" in default_master
    assert "sub zero by zero.ss01;" in default_master.features.text
    assert "feature ss01" in default_master.features.text


LOOKALIKES = [("O", "zero", 0.3), ("zero", "o", 0.3), ("O", "o", 0.3), ("l", "one", 0.3),
              ("I", "one", 0.3), ("I", "l", 0.3), ("l", "bar", 0.3), ("B", "eight", 0.15),
              ("S", "five", 0.15), ("Z", "two", 0.15), ("g", "nine", 0.15), ("g", "q", 0.15)]


@pytest.mark.parametrize("a,b,limit", LOOKALIKES)
def test_lookalikes_differ(a, b, limit):
    # The ink that differs (XOR) is a large part of the glyph at every weight.
    for w in pieces.W_MASTERS:
        pa, pb = union(B.contours(a, w, 0)), union(B.contours(b, w, 0))
        diff = area(pathops.op(pa, pb, pathops.PathOp.XOR))
        assert diff / max(area(pa), area(pb)) >= limit, f"{a} and {b} are too alike at w={w}."


# ------------------------------------------------------------------ statics

def test_static_glyph_set(regular):
    expected = set(B.glyph_order()) - set(ext.ACCENTS)
    assert set(regular.keys()) == expected


def test_static_advance_is_constant(regular):
    for g in regular:
        assert g.width == (0 if g.name in B.mark_names() else B.ADVANCE), g.name


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
    glyph = regular["I"]
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
