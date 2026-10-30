"""Tests for the Warp generator and fonts: metrics, glyph set, the
port of the sketch engine (node), outlines, kerning, features, names,
the MATH table, hinting, the fidelity and readability reports,
determinism."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pathops
import pytest
from fontTools.ttLib import TTFont

from loom import build as Bd
from loom import charset as CS
from loom import engine as E
from loom import kerning as K
from loom import mathglyphs as MG
from loom import outline as O
from loom import revisions as RV

HERE = Path(__file__).resolve().parent
WARP = HERE.parent
ROOT = WARP.parent
FONTS = ROOT / "fonts" / "warp"
PROOFS = ROOT / "proofs" / "warp"
STYLES = list(Bd.STYLES)
DRAWN = [g.name for g in CS.GLYPHS if not g.comps and g.variant != "notdef"]


def ttf(key: str) -> TTFont:
    return TTFont(FONTS / "ttf" / f"{Bd.ps_name(Bd.STYLES[key])}.ttf")


# ---------------------------------------------------------------- metrics

def test_sketch_defaults():
    assert E.DEFAULTS["contrast"] == 9
    assert E.DEFAULTS["stress"] == 0
    assert E.DEFAULTS["bracket"] == 0.2
    assert E.DEFAULTS["xh"] == 412
    assert E.DEFAULTS["stem"] == 84
    p = E.params(opsz=72)
    assert (p.xh, p.cap, p.asc, p.desc, p.axis, p.os) == (412, 670, 760, -250, 250, 11)


def test_optical_sizes():
    assert Bd.TEXT_OPSZ == 10 and Bd.DISPLAY_OPSZ == 60
    text, display = Bd.STYLES["Regular"].p(), Bd.STYLES["Display"].p()
    assert text.xh > display.xh > 412
    assert text.B > display.B  # sturdier hairlines at text size
    assert text.sb > display.sb


def test_bold_is_a_true_bold():
    r, b = Bd.STYLES["Regular"].p(), Bd.STYLES["Bold"].p()
    assert 1.55 <= b.A / r.A <= 1.65
    assert 1.2 <= b.B / r.B <= 1.4
    assert b.S / r.S < b.A / r.A


def test_vertical_metrics_in_fonts():
    for key in STYLES:
        f = ttf(key)
        os2, hhea = f["OS/2"], f["hhea"]
        assert f["head"].unitsPerEm == 1000
        assert os2.sCapHeight == 670
        assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == (900, -300, 0)
        assert (hhea.ascent, hhea.descent) == (900, -300)
        assert os2.fsSelection & (1 << 7)
        assert os2.usWinAscent >= 900 and os2.usWinDescent >= 300


# --------------------------------------------------------------- glyph set

def required() -> set[int]:
    cps = set(range(0x20, 0x7F))
    cps |= {ord(c) for c in CS.LATIN1_LETTERS}
    cps |= {ord(c) for c in "ßÆæØøŒœ‘’“”‚„‹›«»…•·€©®°—– "}
    cps |= {ord(c) for c in CS.GREEK}
    cps |= {ord(c) for c in "+−×÷±=≠<>≤≥∑∏∫√∞∂∇′″·∘→←↔∈∉⊂⊆∪∩∀∃∅≈≡∝"}
    # 0.2
    cps |= set(range(0x100, 0x180)) | {0x218, 0x219, 0x21A, 0x21B}
    cps |= {ord(c) for c in "ΆΈΉΊΌΎΏΐΪΫάέήίΰϊϋόύώ΄΅"}
    cps |= {ord(c) for c in "‰‡†ℓℏℎ‖⟨⟩"}
    cps |= {0x2070, 0xB9, 0xB2, 0xB3} | set(range(0x2074, 0x207A)) | set(range(0x2080, 0x208A))
    cps |= {0x306, 0x30B, 0x326, 0x328, 0x312}
    return cps


# Central European languages: the letters each needs (beyond ASCII).
LANGUAGES = {
    "Polish": "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "Czech": "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
    "Slovak": "áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ",
    "Hungarian": "áéíóöőúüűÁÉÍÓÖŐÚÜŰ",
    "Romanian": "ăâîșțĂÂÎȘȚ",
    "Turkish": "çğıİöşüÇĞÖŞÜ",
    "Croatian": "čćđšžČĆĐŠŽ",
    "Slovenian": "čšžČŠŽ",
    "Latvian": "āčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ",
    "Lithuanian": "ąčęėįšųūžĄČĘĖĮŠŲŪŽ",
    "Estonian": "äöõüšžÄÖÕÜŠŽ",
    "Greek (monotonic)": "άέήίόύώϊϋΐΰΆΈΉΊΌΎΏΪΫ",
}


@pytest.mark.parametrize("lang", sorted(LANGUAGES))
def test_language_coverage(lang):
    cmap = ttf("Regular").getBestCmap()
    missing = [c for c in LANGUAGES[lang] if ord(c) not in cmap]
    assert not missing, (lang, missing)


def test_comma_below_and_caron_forms():
    """Romanian and Latvian use a comma below; ď ť ľ Ľ a vertical caron; ģ a turned comma."""
    for ch in "ȘșȚțĢĶķĻļŅņŖŗ":
        assert CS.BY_NAME[CS.glyph_name(ch)].comps[1] == "commaaccentcomb", ch
    for ch in "ďťľĽ":
        assert CS.BY_NAME[CS.glyph_name(ch)].comps[1] == "caroncomb.alt", ch
    assert CS.BY_NAME["gcommaaccent"].comps[1] == "commaturnedabovecomb"
    assert CS.BY_NAME[CS.glyph_name("Ş")].comps[1] == "cedillacomb"  # Turkish keeps the cedilla


def test_greek_set():
    low = [c for c in CS.GREEK if c.islower()]
    cap = [c for c in CS.GREEK if c.isupper()]
    assert len(cap) == 24 and len(low) == 25 and "ς" in low


@pytest.mark.parametrize("key", STYLES)
def test_coverage(key):
    cmap = ttf(key).getBestCmap()
    missing = sorted(required() - set(cmap))
    assert not missing, [hex(c) for c in missing]


def test_greek_capitals_drawn_or_referenced():
    drawn = set("ΓΔΘΛΞΠΣΦΨΩ")
    for ch in CS.GREEK:
        if not ch.isupper():
            continue
        g = CS.BY_NAME[CS.glyph_name(ch)]
        if ch in drawn:
            assert g.key == ch and not g.comps, ch
        else:
            assert g.comps == [CS.glyph_name(CS.GREEK_LOOKALIKE[ch])], ch


def test_accented_letters_are_composites():
    for ch in CS.LATIN1_LETTERS:
        g = CS.BY_NAME[CS.glyph_name(ch)]
        if ch in "ÆÐ×ØÞßæð÷øþ" or not g.comps:
            continue
        assert g.comp_kind == "accent" and len(g.comps) == 2


def test_space_and_nbsp():
    f = ttf("Regular")
    cmap = f.getBestCmap()
    assert f["hmtx"][cmap[0x20]][0] == f["hmtx"][cmap[0xA0]][0] > 0


# ---------------------------------------------------- port of the engine

SN = None


def sketch_node():
    global SN
    if SN is None:
        import sys
        sys.path.insert(0, str(WARP / "tools"))
        import sketch_node
        if sketch_node.node() is None:
            pytest.skip("node is not installed")
        SN = sketch_node
    return SN


PORT_STYLES = ["Regular", "Italic", "Display", "DisplayItalic"]
# Changed from the sketch on purpose in 0.2 (loom/revisions.py, STATUS.md): the port
# still draws the sketch's form, the font does not.
CHANGED = set(RV.REVISED) | {" "}


@pytest.mark.parametrize("key", PORT_STYLES)
def test_advances_and_bounds_match_the_sketch_engine(key):
    """The port gives the sketch's advances and ink bounds (to 0.01 unit;
    the engine caches nibs by keys rounded to 0.01). The maths operators
    that share one advance (CS.EQUAL_WIDTH_MATHS) are compared on ink only."""
    sn = sketch_node()
    st = Bd.STYLES[key]
    prm = {k: v for k, v in dict(st.params).items() if k in ("opsz", "ital")}
    chars = CS.SKETCH_CHARS + " "
    names = list(chars) + [f"{d}.os" for d in "0123456789"] + [f"sc:{c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    ref = sn.glyphs(prm, names, polys=False)
    p = st.p()
    for nm, r in ref.items():
        base, mods = nm, {}
        if nm.endswith(".os"):
            base, mods = nm[0], E.osf_mods(p, nm[0])
        elif nm.startswith("sc:"):
            base, mods = nm[3:], E.sc_mods(p)
        d = RV.sketch_def(base, p.ital)
        sw = E.compose(d, p, mods)
        adv, dx = sw.adv, sw.dx
        if E.is_greek_lower(base):
            adv += p.sb * 0.5
            dx += p.sb * 0.25
        for a, b in ((sw.xmin, r["xmin"]), (sw.xmax, r["xmax"]), (sw.ymin, r["ymin"]), (sw.ymax, r["ymax"])):
            assert a == pytest.approx(b, abs=0.01), nm
        assert adv == pytest.approx(r["adv"], abs=0.02), nm
        # and the font: the advance in the compiled TTF, rounded
        changed = CHANGED | (set(RV.ITALIC_CAPS_02) if p.ital else set())
        if len(nm) == 1 and nm not in CS.EQUAL_WIDTH_MATHS and nm not in changed:
            name = CS.glyph_name(nm)
            if name in CS.BY_NAME and not CS.BY_NAME[name].comps:
                assert Bd.drawn(key, name).adv == pytest.approx(r["adv"], abs=0.02), nm


def test_word_space():
    assert Bd.drawn("Regular", "space").adv == pytest.approx(RV.SPACE_TEXT)
    assert Bd.drawn("Display", "space").adv == pytest.approx(RV.SPACE_DISPLAY)
    f = ttf("Regular")
    assert f["hmtx"]["space"][0] == RV.SPACE_TEXT


def test_revised_forms_differ_from_the_sketch():
    for key in ("g", "f", "ﬁ", "ﬂ", "Σ"):
        p = Bd.STYLES["Regular"].p()
        a = E.compose(RV.sketch_def(key, False), p)
        b = E.compose(Bd.table_def(key, False), p)
        assert a.polys != b.polys, key


def test_xi_sigma_bars_are_heavier():
    """The horizontals of Ξ and Σ are thicker than a hairline (the 0.1 bars were B thick)."""
    p = Bd.STYLES["Regular"].p()
    for ch in "ΞΣ":
        sw = E.compose(Bd.table_def(ch, False), p)
        bars = [s for s in Bd.drawn("Regular", CS.glyph_name(ch)).sweep.strokes if s["role"] == "bar"]
        assert bars, ch
    g = E.Builder(p)
    RV._Xi(g)
    assert max(s["o"].get("b", 0) for s in g.strokes) >= p.B * 2.3


def test_italic_capitals_have_own_forms():
    from loom.sketch import GI
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ&":
        assert ch in GI, ch


def test_font_advances_are_the_loom_advances():
    for key in STYLES:
        f = ttf(key)
        for name in DRAWN[:: 7]:
            assert f["hmtx"][name][0] == Bd.rnd(Bd.drawn(key, name).adv), (key, name)


def test_equal_width_maths():
    for key in STYLES:
        f = ttf(key)
        cmap = f.getBestCmap()
        widths = {f["hmtx"][cmap[ord(c)]][0] for c in CS.EQUAL_WIDTH_MATHS}
        assert len(widths) == 1, key


# --------------------------------------------------------------- outlines

def contour_area(segs) -> float:
    pts = []
    for s in segs:
        if s[0] == "line":
            pts.append(s[1])
        else:
            pts += list(O._bez(s[1], np.linspace(0, 1, 9))[:-1])
    a = np.array(pts)
    return O.signed_area(a)


@pytest.mark.parametrize("key", ["Regular", "BoldItalic", "Display"])
def test_outlines_are_clean(key):
    for name in DRAWN:
        cs = Bd.drawn(key, name).contours
        for segs in cs:
            for s in segs:
                assert O._seg_len(s) >= O.MIN_SEG - 0.5, (name, "short segment")
        # outer contours counter-clockwise (PostScript order); the union is
        # already overlap-free: removing overlaps again changes nothing
        path = pathops.Path()
        O.draw(cs, path.getPen(), rnd=False)
        before = path.area
        path.simplify(fix_winding=True)
        assert path.area == pytest.approx(before, rel=0.002), (name, "self-intersection")
        if cs:
            biggest = max(cs, key=lambda c: abs(contour_area(c)))
            assert contour_area(biggest) > 0, (name, "direction")


def test_points_per_glyph_are_few():
    counts = []
    for name in DRAWN:
        n = sum(1 if s[0] == "line" else 3 for c in Bd.drawn("Regular", name).contours for s in c)
        counts.append(n)
    assert np.median(counts) < 90
    assert max(counts) < 600


def test_fidelity_report():
    rep = json.loads((PROOFS / "fidelity.json").read_text())
    assert rep["pass"] is True
    assert set(rep["styles"]) == set(STYLES)
    for st in rep["styles"].values():
        for s, row in st["summary"].items():
            assert row["max"] <= rep["tolerance"][s]


# ---------------------------------------------------------------- kerning

def test_kerning_groups_are_disjoint_and_exist():
    names = set(CS.ORDER)
    for side in (K.KERN1, K.KERN2):
        seen = set()
        for members in side.values():
            for m in members:
                assert m in names, m
                assert m not in seen, f"{m} is in two groups"
                seen.add(m)
    for a, b in K.PAIRS:
        assert a in K.KERN1 and b in K.KERN2


def test_kerning_starts_from_the_sketch_table():
    from loom.sketch import sketch_kern
    sk = sketch_kern()
    for pair, v in (("To", -62), ("AV", -58), ("Y.", -80), ("L'", -80), ("P.", -80)):
        assert sk[pair] == v
        a = next(k for k, m in K.KERN1.items() if CS.glyph_name(pair[0]) in m)
        b = next(k for k, m in K.KERN2.items() if CS.glyph_name(pair[1]) in m)
        assert K.PAIRS[(a, b)] == v


def profile(key, name, side):
    """x of the outer ink edge in bands of 20 units (min for left, max for right)."""
    d = Bd.drawn(key, name)
    out = {}
    for poly in d.sweep.polys:
        for x, y in poly:
            b = int(y // 20)
            x += d.dx
            if side == "r":
                out[b] = max(out.get(b, -1e9), x)
            else:
                out[b] = min(out.get(b, 1e9), x)
    return out, d.adv


@pytest.mark.parametrize("key", ["Regular", "Italic", "Bold", "Display"])
def test_no_kerned_pair_touches(key):
    kern = K.kerning(Bd.STYLES[key])
    for (g1, g2), v in kern.items():
        for a in K.KERN1[g1.split(".")[-1]]:
            ra, adv = profile(key, a, "r") if not CS.BY_NAME[a].comps else (None, None)
            if ra is None:
                continue
            for b in K.KERN2[g2.split(".")[-1]]:
                if CS.BY_NAME[b].comps:
                    continue
                lb, _ = profile(key, b, "l")
                gaps = [adv + v + lb[k] - ra[k] for k in ra if k in lb]
                if gaps:
                    assert min(gaps) > 0, (key, a, b, min(gaps))


# --------------------------------------------------------------- features

def gsub_features(f: TTFont) -> set[str]:
    return {r.FeatureTag for r in f["GSUB"].table.FeatureList.FeatureRecord}


def single_map(f: TTFont, tag: str) -> dict:
    out = {}
    gsub = f["GSUB"].table
    for r in gsub.FeatureList.FeatureRecord:
        if r.FeatureTag != tag:
            continue
        for li in r.Feature.LookupListIndex:
            for st in gsub.LookupList.Lookup[li].SubTable:
                st = getattr(st, "ExtSubTable", st)
                if hasattr(st, "mapping"):
                    # smcp is one multiple substitution lookup (ß -> s.sc s.sc)
                    out.update({k: v[0] if isinstance(v, list) and len(v) == 1 else v
                                for k, v in st.mapping.items()})
    return out


@pytest.mark.parametrize("key", STYLES)
def test_features(key):
    f = ttf(key)
    feats = gsub_features(f)
    assert {"ccmp", "liga", "smcp", "c2sc", "onum", "lnum", "pnum", "tnum",
            "sups", "subs", "sinf", "numr", "dnom", "frac"} <= feats
    assert single_map(f, "sups")["four"] == "uni2074"
    assert single_map(f, "subs")["two"] == "uni2082"
    assert single_map(f, "dnom")["seven"] == "seven.dnom"
    assert {"kern", "mark", "mkmk"} <= {r.FeatureTag for r in f["GPOS"].table.FeatureList.FeatureRecord}
    assert single_map(f, "smcp")["a"] == "a.sc"
    assert single_map(f, "c2sc")["A"] == "a.sc"
    assert single_map(f, "smcp")["alpha"] == "alpha.sc"
    assert single_map(f, "onum")["zero"] == "zero.osf"
    assert single_map(f, "tnum")["zero.osf"] == "zero.tosf"
    assert single_map(f, "pnum")["zero"] == "zero.lf"
    lig = {}
    gsub = f["GSUB"].table
    for r in gsub.FeatureList.FeatureRecord:
        if r.FeatureTag == "liga":
            for li in r.Feature.LookupListIndex:
                for st in gsub.LookupList.Lookup[li].SubTable:
                    lig.update(getattr(st, "ligatures", {}))
    got = {tuple([first] + l.Component): l.LigGlyph for first, ls in lig.items() for l in ls}
    for seq, name in ((("f", "i"), "fi"), (("f", "l"), "fl"), (("f", "f"), "f_f"),
                      (("f", "f", "i"), "f_f_i"), (("f", "f", "l"), "f_f_l")):
        assert got.get(seq) == name


def test_default_figures_are_lining_tabular():
    f = ttf("Regular")
    widths = {f["hmtx"][n][0] for n in CS.FIG_NAMES}
    assert len(widths) == 1
    assert len({f["hmtx"][n + ".tosf"][0] for n in CS.FIG_NAMES}) == 1
    assert len({f["hmtx"][n + ".osf"][0] for n in CS.FIG_NAMES}) > 1


def shape(key, text, features):
    hb = pytest.importorskip("uharfbuzz")
    blob = hb.Blob.from_file_path(str(FONTS / "ttf" / f"{Bd.ps_name(Bd.STYLES[key])}.ttf"))
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    names = [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    return names, buf.glyph_positions


def test_frac_feature():
    names, _ = shape("Regular", "1/2 3", {"frac": True})
    assert names[:3] == ["one.numr", "fraction", "two.dnom"]
    names, _ = shape("Regular", "17/32", {"frac": True})
    assert names == ["one.numr", "seven.numr", "fraction", "three.dnom", "two.dnom"]


def test_superiors_and_inferiors_sit_right():
    f = ttf("Regular")
    gs = f.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    def bounds(n):
        pen = BoundsPen(gs); gs[n].draw(pen); return pen.bounds
    sup, inf, dnom = bounds("uni2074"), bounds("uni2084"), bounds("four.dnom")
    assert sup[3] == pytest.approx(670, abs=15)       # superiors reach the cap height
    assert abs(dnom[1]) < 15                           # denominators sit on the baseline
    assert inf[1] == pytest.approx(dnom[1] + Bd.INFERIOR_DY, abs=1)


# ------------------------------------------------------------------- MATH

def math_tab(key):
    return ttf(key)["MATH"].table


@pytest.mark.parametrize("key", STYLES)
def test_math_table_present(key):
    for fmt in ("ttf", "otf"):
        f = TTFont(FONTS / fmt / f"{Bd.ps_name(Bd.STYLES[key])}.{fmt}")
        assert "MATH" in f, (key, fmt)


@pytest.mark.parametrize("key", STYLES)
def test_math_constants_are_sane(key):
    from loom.sketch import Rw
    c = math_tab(key).MathConstants
    p = Bd.STYLES[key].p()
    v = lambda name: getattr(c, name).Value if hasattr(getattr(c, name), "Value") else getattr(c, name)  # noqa: E731
    assert v("AxisHeight") == 250
    r = Bd.rnd(Rw(p))
    for name in ("FractionRuleThickness", "RadicalRuleThickness", "OverbarRuleThickness", "UnderbarRuleThickness"):
        assert v(name) == r, name
    # the rule matches the pen: the thickness of the minus sign
    f = ttf(key)
    gs = f.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    pen = BoundsPen(gs); gs["minus"].draw(pen)
    assert pen.bounds[3] - pen.bounds[1] == pytest.approx(r, abs=3)
    assert 60 <= v("ScriptPercentScaleDown") <= 80
    assert 40 <= v("ScriptScriptPercentScaleDown") < v("ScriptPercentScaleDown")
    assert v("AccentBaseHeight") == Bd.rnd(p.xh)
    assert v("FlattenedAccentBaseHeight") == 670
    assert 0 < v("SubscriptShiftDown") < v("SubscriptTopMax") < p.xh
    assert 0 < v("SuperscriptBottomMin") < v("SuperscriptShiftUp") < p.xh
    assert v("FractionNumeratorDisplayStyleShiftUp") > v("FractionNumeratorShiftUp") > 250
    assert v("FractionDenominatorDisplayStyleShiftDown") > v("FractionDenominatorShiftDown") > 0
    assert v("RadicalVerticalGap") >= r
    assert v("DisplayOperatorMinHeight") > 1040                 # above the text ∑ (1040 units)
    assert math_tab(key).MathVariants.MinConnectorOverlap > Bd.STYLES[key].p().B


@pytest.mark.parametrize("key", ["Regular", "Bold", "Display", "Italic"])
def test_math_variants_and_assemblies(key):
    """Every variant and part exists; at least four sizes, growing; parts connect."""
    f = ttf(key)
    order = set(f.getGlyphOrder())
    mv = math_tab(key).MathVariants
    cov = mv.VertGlyphCoverage.glyphs
    by = dict(zip(cov, mv.VertGlyphConstruction))
    need = {"parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright", "bar",
            "uni2016", "radical", "integral", "summation", "product", "uni27E8", "uni27E9"}
    assert need <= set(by)
    for base, con in by.items():
        heights = [r.AdvanceMeasurement for r in con.MathGlyphVariantRecord]
        names = [r.VariantGlyph for r in con.MathGlyphVariantRecord]
        assert names[0] == base and len(names) >= 5, base
        assert all(n in order for n in names)
        assert heights == sorted(heights) and len(set(heights)) == len(heights), (base, heights)
        asm = con.GlyphAssembly
        if base in MG.ASSEMBLY:
            assert asm is not None, base
            parts = asm.PartRecords
            assert any(p.PartFlags & 1 for p in parts), base
            for p in parts:
                assert p.glyph in order
                assert p.FullAdvance > 0
            for a, b in zip(parts, parts[1:]):
                # the overlap the shaper may use must cover the minimum overlap
                assert min(a.EndConnectorLength, b.StartConnectorLength) >= mv.MinConnectorOverlap, (base, a.glyph, b.glyph)
        else:
            assert asm is None, base


def test_math_parts_line_up():
    """The stems of the parts of an assembly are at the same x (the shaper stacks them at one origin)."""
    f = ttf("Regular")
    gs = f.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    for base, parts in MG.ASSEMBLY.items():
        advs = {f["hmtx"][n][0] for n, _, _ in parts}
        assert len(advs) == 1, base
        ext = next(n for n, e, _ in parts if e)
        pen = BoundsPen(gs); gs[ext].draw(pen)
        e0, e1 = pen.bounds[0], pen.bounds[2]
        for n, _, role in parts:
            if role in ("top", "bot"):
                d = Bd.drawn("Regular", n)
                # the connector end: ink in the straight part, at the stem
                xs = [x + d.dx for poly in d.sweep.polys for x, y in poly
                      if (y < d.sweep.ymin + 60 if role == "top" else y > d.sweep.ymax - 60)]
                assert min(xs) == pytest.approx(e0, abs=3) and max(xs) == pytest.approx(e1, abs=3), (base, n)


def test_math_with_harfbuzz():
    hb = pytest.importorskip("uharfbuzz")
    blob = hb.Blob.from_file_path(str(FONTS / "ttf" / "MachineMadeWarp-Regular.ttf"))
    face = hb.Face(blob)
    font = hb.Font(face)
    assert face.has_math_data
    assert font.get_math_constant(hb.OTMathConstant.AXIS_HEIGHT) == 250
    gid = font.get_nominal_glyph(ord("("))
    variants = font.get_math_glyph_variants(gid, "TTB")
    assert len(variants) >= 5
    parts, ic = font.get_math_glyph_assembly(gid, "TTB")
    assert len(parts) == 3
    assert font.get_math_min_connector_overlap("TTB") > 0
    x = font.get_nominal_glyph(0x1D465)   # mathematical italic x
    assert x and font.get_math_glyph_top_accent_attachment(x) > 0
    f = font.get_nominal_glyph(0x1D453)   # mathematical italic f leans out: italic correction
    assert font.get_math_glyph_italics_correction(f) > 0


def test_math_italic_letters():
    """Upright styles draw the italic forms; italic styles refer to their letters."""
    reg, ita = ttf("Regular"), ttf("Italic")
    cr, ci = reg.getBestCmap(), ita.getBestCmap()
    for u, ch in CS.MATH_ITALIC:
        assert u in cr and u in ci
    assert ci[0x1D44E] and ita["glyf"][ci[0x1D44E]].isComposite()
    assert not reg["glyf"][cr[0x1D44E]].isComposite()
    assert reg["hmtx"][cr[0x1D44E]][0] == ita["hmtx"]["a"][0]
    assert 0x210E in cr and 0x210F in cr


# ---------------------------------------------------------------- hinting

@pytest.mark.parametrize("key", STYLES)
def test_ttf_are_hinted(key):
    f = ttf(key)
    assert {"fpgm", "prep", "cvt ", "gasp"} <= set(f.keys())
    assert "ttfautohint" not in (f["name"].getDebugName(5) or "")   # --no-info


# ------------------------------------------------------------------ names

def test_names_fit():
    for key in STYLES:
        f = ttf(key)
        fam = f["name"].getDebugName(16) or f["name"].getDebugName(1)
        sty = f["name"].getDebugName(17) or f["name"].getDebugName(2)
        assert fam.startswith("machine-made Warp")
        assert len(fam if sty == "Regular" else f"{fam} {sty}") <= 32
        for rec in f["name"].names:
            if rec.nameID in (1, 2, 4, 16, 17):
                assert len(rec.toUnicode()) <= 32, (key, rec.nameID, rec.toUnicode())
        assert f["name"].getDebugName(6) == Bd.ps_name(Bd.STYLES[key])


def test_no_bare_warp_family():
    for key in STYLES:
        f = ttf(key)
        for rec in f["name"].names:
            if rec.nameID in (1, 16, 4):
                assert rec.toUnicode().startswith("machine-made Warp")


def test_italic_angle():
    for key in STYLES:
        f = ttf(key)
        if Bd.STYLES[key].italic:
            assert f["post"].italicAngle == pytest.approx(-math.degrees(math.atan(0.25)), abs=0.01)
        else:
            assert f["post"].italicAngle == 0


# ---------------------------------------------------------------- reports

def test_readability_report():
    rep = json.loads((PROOFS / "readability.json").read_text())
    assert rep["gate"]["pass"] is True
    assert rep["sizes_px"] == [10, 12, 14]
    assert {c["style"] for c in rep["gate"]["checks"]} == {"Regular", "Italic"}


def test_sketch_compare_report():
    rep = json.loads((PROOFS / "sketch-compare.json").read_text())
    # The italic capitals of 0.2 are drawn in their own cursive forms
    # (STATUS.md, "Deviations from the sketch"), so the sketch does not
    # match them by design. The gate leaves them out for the italics.
    own = set(RV.ITALIC_CAPS_02)
    for key in ("Regular", "Italic", "Display", "DisplayItalic"):
        iou = rep["styles"][key]["iou"]
        if key in ("Italic", "DisplayItalic"):
            iou = {ch: v for ch, v in iou.items() if ch not in own}
        assert sum(iou.values()) / len(iou) >= 0.9, key


# ------------------------------------------------------------ determinism

def test_build_is_deterministic():
    Bd.drawn.cache_clear()
    a = Bd.build_font("Display")
    Bd.drawn.cache_clear()
    b = Bd.build_font("Display")
    for name in CS.ORDER[::5]:
        ga, gb = a[name], b[name]
        assert ga.width == gb.width
        assert [[(p.x, p.y, p.segmentType) for p in c] for c in ga.contours] == \
               [[(p.x, p.y, p.segmentType) for p in c] for c in gb.contours]
    assert a.kerning == b.kerning and a.features.text == b.features.text
