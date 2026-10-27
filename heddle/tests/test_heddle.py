"""Tests for the Heddle 0.1 generator: metrics, glyph set, masters,
the port of the sketch engine, kerning, drift, statics, names."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from loom import build as B
from loom import geom
from loom import glyphs as G
from loom import kerning as K
from loom import raster as R

HERE = Path(__file__).resolve().parent
HEDDLE = HERE.parent
ENGINE = HEDDLE / "reference" / "heddle-sketch-0.1.js"
MASTERS = [(w, d) for w in B.WGHT_MASTERS for d in B.WDTH_MASTERS]
DRAWN = B.drawn_names()
ENCODED = sorted(G.cmap())


# ---------------------------------------------------------------- metrics

def test_vertical_metrics():
    assert (G.UPM, G.XH, G.CAP, G.ASC, G.DESC, G.OS) == (1000, 520, 700, 730, -210, 10)
    assert geom.N == 2.6


@pytest.mark.parametrize("wght,S", [(100, 28), (400, 84.25), (500, 103), (900, 178)])
def test_stem_formula(wght, S):
    p = G.Params(wght, 100)
    assert p.S == pytest.approx(S)
    assert p.H == pytest.approx(0.84 * S)
    assert p.sb == pytest.approx(22 + 0.22 * S)


def test_diagonal_formula():
    g = geom.Canvas(100, 84)
    assert g.dt(30, 40) == pytest.approx(0.9 * 100 * 50 / 40)


def test_width_rule_for_sketch_glyphs():
    o = G.GLYPHS["o"]
    assert o.width(G.Params(400, 100)) == pytest.approx(560)
    assert o.width(G.Params(400, 70)) == pytest.approx(392)
    # The floor: 2.3 stems.
    r = G.GLYPHS["r"]
    assert r.width(G.Params(900, 70)) == pytest.approx(2.3 * 178)
    # Fixed glyphs follow the stem.
    assert G.GLYPHS["i"].width(G.Params(700, 140)) == pytest.approx(G.Params(700, 140).S)
    assert G.GLYPHS["j"].width(G.Params(700, 70)) == pytest.approx(G.Params(700, 70).S + 120)
    assert G.GLYPHS["period"].width(G.Params(100, 100)) == pytest.approx(28 * 1.06)


@pytest.mark.parametrize("wdth,factor", [(70, 0.8), (100, 1.0), (140, 1.25)])
def test_tabular_figures(wdth, factor):
    for n in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"):
        assert G.GLYPHS[n].width(G.Params(400, wdth)) == pytest.approx(560 * factor)


def test_new_glyph_widths_are_linear_in_both_axes():
    # W = A * wf + B * S: the variable font gives it exactly.
    for name, gl in G.GLYPHS.items():
        if gl.kind != "prop" or gl.sketch:
            continue
        f = lambda w, d: gl.width(G.Params(w, d))  # noqa: E731
        mid = f(500, 105)
        assert mid == pytest.approx((f(100, 70) + f(900, 70) + f(100, 140) + f(900, 140)) / 4), name


# --------------------------------------------------------------- glyph set

def test_printable_ascii_and_latin1_letters():
    cps = set(ENCODED)
    assert set(range(0x20, 0x7F)) <= cps
    assert 0xA0 in cps
    letters = {cp for cp in range(0xC0, 0x100) if chr(cp).isalpha()}
    assert letters <= cps
    for ch in "ßÆæØøŒœ‘’“”‚„…•·€©®°—ŸıÐðÞþ¡¿«»‹›₹":
        assert ord(ch) in cps, ch


def test_sketch_charset_is_from_the_sketch():
    for ch in G.SKETCH_CHARS:
        name = G.cmap()[ord(ch)]
        assert G.GLYPHS[name].sketch, ch
    # The sketch page says "70 characters": a-z, A-Z, 0-9, . , : ! ' - – /
    # (the space comes on top).
    assert len(G.SKETCH_CHARS) == 70


def test_glyph_order_and_names():
    order = G.glyph_order()
    assert order[:2] == [".notdef", "space"]
    assert len(order) == len(set(order))
    for name in order:
        assert name.isascii() and len(name) <= 63


def test_composites_use_existing_glyphs():
    marks = set(G.accent_names())
    for name, (cp, base, acc) in G.COMPOSITES.items():
        assert base in G.GLYPHS and acc in marks, name
        assert G.cmap()[cp] == name


def test_space_and_nbsp_share_a_glyph():
    assert G.cmap()[0x20] == G.cmap()[0xA0] == "space"


# ------------------------------------------------------------- masters

@pytest.mark.parametrize("name", DRAWN)
def test_same_structure_in_every_master(name):
    shapes = {B.structure(B.drawn(name, w, d)[0]) for w, d in MASTERS}
    assert len(shapes) == 1, f"{name} is not compatible between masters"


@pytest.mark.parametrize("name", DRAWN)
def test_contour_directions(name):
    # Filled contours run counter-clockwise; a clockwise contour is the
    # counter of the ring right before it.
    for w, d in MASTERS:
        contours, _ = B.drawn(name, w, d)
        prev_ccw = False
        for c in contours:
            a = geom.signed_area(c)
            if a < 0:
                assert prev_ccw, f"{name}: a counter without its ring"
                prev_ccw = False
            else:
                prev_ccw = True


def test_vee_has_seven_points_always():
    for x1, t in ((400, 60), (400, 199), (400, 200), (400, 260), (300, 400)):
        pts = geom.vee_points(0, x1, 520, 0, t)
        assert len(pts) == 7
        assert geom.signed_area([(x, y, True) for x, y in pts]) != 0


def test_side_cuts_make_horizontal_terminals():
    c = geom.ring_contours(0, -10, 560, 530, [("r", 156, 369)], 84, 70)
    assert len(c) == 1
    piece = c[0]
    ons = [p for p in piece if p[2]]
    # Outer end, then inner start: same y (a horizontal end). The second
    # end closes the contour (last point to first point).
    pairs = list(zip(ons, ons[1:] + ons[:1]))
    ends = [(a, b) for a, b in pairs if abs(a[1] - b[1]) < 1e-6 and abs(a[0] - b[0]) > 10]
    assert len(ends) >= 2


def test_cut_ring_point_count_is_fixed():
    counts = set()
    for S in (28, 84.25, 140.5, 178):
        c = geom.ring_contours(0, -10, 520, 530, [("r", 156, 369)], S, 0.84 * S)
        counts.add(tuple(len(x) for x in c))
    assert len(counts) == 1


def test_superellipse_fit_is_close():
    # One cubic per quarter stays within 3 units of the curve.
    cx, cy, rx, ry = 0, 0, 280, 270
    arc = geom.se_arc(cx, cy, rx, ry, 0, math.pi / 2)
    p0 = geom.se_point(cx, cy, rx, ry, 0)
    p1, p2, p3 = arc[0][:2], arc[1][:2], arc[2][:2]
    for i in range(1, 50):
        t = i / 50
        m = 1 - t
        bx = m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0]
        by = m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]
        # Distance from the curve: |x/rx|^N + |y/ry|^N = 1.
        rr = (abs(bx / rx) ** geom.N + abs(by / ry) ** geom.N) ** (1 / geom.N)
        assert abs(rr - 1) * 280 < 3


# ----------------------------------------------------- port of the sketch

def _node_widths():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    locs = [[w, d] for w, d in MASTERS]
    js = (
        f"const Sh=require({json.dumps(str(ENGINE))});"
        f"const chars={json.dumps(G.SKETCH_CHARS + ' ')};const out={{}};"
        f"for(const [w,d] of {json.dumps(locs)}){{const p=Sh.params({{wght:w,wdth:d}});"
        "for(const ch of chars){out[w+','+d+','+ch]=Sh.glyphBox(ch,p).adv;}}"
        "console.log(JSON.stringify(out));"
    )
    res = subprocess.run([node, "-e", js], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def test_advances_match_the_sketch_engine():
    ref = _node_widths()
    for key, adv in ref.items():
        w, d, ch = key.split(",", 2)
        name = G.cmap()[ord(ch)]
        _, mine = B.drawn(name, float(w), float(d))
        assert mine == pytest.approx(adv, abs=1e-6), key


# ----------------------------------------------------------------- kerning

def test_kerning_groups_are_disjoint_and_exist():
    names = set(G.glyph_order())
    for side in (K.KERN1, K.KERN2):
        seen = set()
        for members in side.values():
            for m in members:
                assert m in names, m
                assert m not in seen, f"{m} is in two groups"
                seen.add(m)
    for a, b in K.PAIRS:
        assert a in K.KERN1 and b in K.KERN2


def test_kerning_is_modest():
    for v in K.PAIRS.values():
        assert -100 <= v < 0


def _profile(contours, side):
    """x of the outer ink edge at y steps of 10 units (min for left, max for right)."""
    out = {}
    for c in contours:
        poly = R._flatten(c, 8)
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            lo, hi = sorted((y0, y1))
            for y in range(math.ceil(lo / 10) * 10, math.floor(hi / 10) * 10 + 1, 10):
                if y0 == y1:
                    xs = (x0, x1)
                else:
                    xs = (x0 + (y - y0) * (x1 - x0) / (y1 - y0),)
                for x in xs:
                    if y not in out:
                        out[y] = x
                    out[y] = min(out[y], x) if side == "left" else max(out[y], x)
    return out


def _outline(name, w, d):
    cs, adv = B.direct_outline(name, w, d)
    return cs, adv


@pytest.mark.parametrize("loc", MASTERS)
def test_kerned_pairs_do_not_touch(loc):
    w, d = loc
    kern = K.kerning(G.Params(w, d))
    reps = {k: v[0] for k, v in {**{f"1{k}": v for k, v in K.KERN1.items()},
                                  **{f"2{k}": v for k, v in K.KERN2.items()}}.items()}
    for (a, b), v in kern.items():
        left = reps["1" + a.split(".")[-1]]
        right = reps["2" + b.split(".")[-1]]
        lc, ladv = _outline(left, w, d)
        rc, _ = _outline(right, w, d)
        lp, rp = _profile(lc, "right"), _profile(rc, "left")
        gaps = [ladv + v + rp[y] - lp[y] for y in lp if y in rp]
        if gaps:
            assert min(gaps) >= 12, f"{left}{right} at {loc}: gap {min(gaps):.0f}"


# ------------------------------------------------------------------- drift

@pytest.mark.parametrize("loc", [(100, 70), (400, 100), (900, 140)])
def test_no_drift_at_masters(loc):
    for name in ("o", "a", "S", "e", "g", "ampersand", "at", "Agrave"):
        a, _ = B.direct_outline(name, *loc)
        b, _ = B.interpolated(name, *loc)
        assert R.mismatch(R.nonzero_mask(a), R.nonzero_mask(b)) == 0, name


@pytest.mark.parametrize("loc", [(250, 85), (550, 120), (800, 100)])
def test_drift_between_masters_is_small(loc):
    worst = 0.0
    for name in [n for n in G.glyph_order() if n in G.GLYPHS and n not in ("space",)]:
        a, aa = B.direct_outline(name, *loc)
        b, ba = B.interpolated(name, *loc)
        if not a:
            continue
        ma = R.nonzero_mask(a)
        worst = max(worst, R.mismatch(ma, R.nonzero_mask(b)) / max(1, R.count(ma)))
        assert abs(aa - ba) <= 40, name
    assert worst <= 0.12


# ----------------------------------------------------------------- statics

@pytest.fixture(scope="module")
def black():
    return B.build_static(900, 100)


def test_static_has_no_marks_and_no_components(black):
    assert not set(G.accent_names()) & set(black.keys())
    assert all(not g.components for g in black)


def test_static_union_matches_nonzero_fill(black):
    from fontTools.pens.recordingPen import RecordingPen
    for name in ("S", "s", "B", "ampersand", "Aring", "percent", "g", "at"):
        cs, _ = B.interpolated(name, 900, 100)
        rec = RecordingPen()
        black[name].draw(rec)
        contour, cont = [], []
        for op, args in rec.value:
            if op == "moveTo":
                contour = [(*args[0], True)]
            elif op == "lineTo":
                contour.append((*args[0], True))
            elif op == "curveTo":
                contour += [(*args[0], False), (*args[1], False), (*args[2], True)]
            elif op == "qCurveTo":
                raise AssertionError("unexpected quadratic")
            else:
                if contour[-1][:2] == contour[0][:2]:
                    contour = contour[:-1] if contour[-1][2] else contour
                cont.append(contour)
        # The static outline is overlap-free: even-odd and nonzero agree.
        import pathops
        path = B._to_path(cont)
        assert R.mismatch(R.nonzero_mask(cs), R.path_mask(path)) == 0, name


def test_robust_union_fixes_the_spine_of_S():
    # pathops alone drops the upper ring here (curves nearly coincide).
    cs, _ = B.direct_outline("S", 400, 120)
    p = B.robust_union(cs)
    assert R.mismatch(R.nonzero_mask(cs), R.path_mask(p)) == 0


# ------------------------------------------------------------------- names

def test_names_fit_32_characters():
    for w, _ in B.WEIGHTS:
        for d, _, _ in B.WIDTHS:
            if (w, d) in B.STATICS:
                fam = f"{B.FAMILY}" + ("" if d == 100 else f" {B.WIDTH_NAME[d]}")
                assert len(fam) <= 32
    doc = B.build_designspace({})
    assert len(doc.instances) == 13
    for inst in doc.instances:
        name = f"{B.FAMILY} {inst.styleName}"
        assert len(name) <= 32, name


def test_width_classes():
    assert [c for _, _, c in B.WIDTHS] == [3, 4, 5, 7, 8]


def test_no_personal_names_in_credits():
    font = B.build_master(400, 100)
    assert font.info.openTypeNameDesigner == "machine-made agents"
    assert font.info.openTypeOS2VendorID == "NONE"


# ------------------------------------------------------------- determinism

def test_masters_are_deterministic(tmp_path):
    a, b = tmp_path / "a.ufo", tmp_path / "b.ufo"
    B.build_master(700, 70).save(a)
    B.drawn.cache_clear()
    B.build_master(700, 70).save(b)
    for f in sorted(a.rglob("*")):
        if f.is_file():
            assert f.read_bytes() == (b / f.relative_to(a)).read_bytes(), f.name
