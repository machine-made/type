"""Tests for the changes of machine-made Sans 0.2."""

from __future__ import annotations

import glob
import math

import pytest
from conftest import FONTS
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

VF = FONTS / "variable" / "MachineMadeSans[wght].ttf"
VF_IT = FONTS / "variable" / "MachineMadeSans-Italic[wght].ttf"
ALL = sorted(glob.glob(str(FONTS / "*" / "*.*")))
TTF = sorted(glob.glob(str(FONTS / "ttf" / "*.ttf")))
OTF = sorted(glob.glob(str(FONTS / "otf" / "*.otf")))
BINARY = [p for p in ALL if not p.endswith(".woff2")]

LATIN_EXT_A = list(range(0x0100, 0x0180)) + [0x0218, 0x0219, 0x021A, 0x021B]


def ids(p):
    return p.split("/fonts/sans/")[1]


@pytest.mark.parametrize("path", ALL, ids=ids)
def test_version(path):
    font = TTFont(path)
    assert round(font["head"].fontRevision, 3) == 0.2
    assert font["name"].getDebugName(5).startswith("Version 0.200")


@pytest.mark.parametrize("path", ALL, ids=ids)
def test_latin_extended_a(path):
    cmap = TTFont(path).getBestCmap()
    missing = [f"U+{c:04X}" for c in LATIN_EXT_A if c not in cmap]
    assert not missing


@pytest.mark.parametrize("path", BINARY, ids=ids)
def test_central_european_languages(path):
    """Base exemplar characters of the Central European languages."""
    cmap = TTFont(path).getBestCmap()
    text = (
        "ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ"  # Polish
        "áčďéěíňóřšťúůýž ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"  # Czech
        "äĺľôŕ ÄĹĽÔŔ"  # Slovak
        "öőüű ÖŐÜŰ"  # Hungarian
        "ăâîșț ĂÂÎȘȚ"  # Romanian
        "çğıİöşü ÇĞÖŞÜ"  # Turkish
        "ćčđšž ĆČĐŠŽ"  # Croatian, Slovenian
        "āčēģīķļņšūž ĀČĒĢĪĶĻŅŠŪŽ"  # Latvian
        "ąčęėįšųūž ĄČĘĖĮŠŲŪŽ"  # Lithuanian
        "äöõüšž ÄÖÕÜŠŽ"  # Estonian
    )
    missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
    assert not missing


def test_italic_has_the_upright_cyrillic():
    up = {c for c in TTFont(VF).getBestCmap() if 0x0400 <= c <= 0x052F}
    it = {c for c in TTFont(VF_IT).getBestCmap() if 0x0400 <= c <= 0x052F}
    assert len(up) == 98
    assert up == it


def test_italic_cyrillic_is_the_slanted_upright():
    """In the sources, each italic Cyrillic outline is the upright outline
    slanted by 8 degrees about half the x-height of its master (to the
    rounding of the coordinates). Glyphs made of components are checked
    by the other tests (the components are the italic Latin glyphs)."""
    import glyphsfmt
    from conftest import SANS

    up = glyphsfmt.loads((SANS / "sources" / "MachineMadeSans.glyphs").read_text(encoding="utf-8"))
    it = glyphsfmt.loads((SANS / "sources" / "MachineMadeSans-Italic.glyphs").read_text(encoding="utf-8"))
    it_glyphs = {g["glyphname"]: g for g in it["glyphs"]}
    xh_index = next(i for i, m in enumerate(it["metrics"]) if m.get("type") == "x-height")
    it_master = {tuple(m["axesValues"]): (m["id"], m["metricValues"][xh_index]["pos"]) for m in it["fontMaster"]}
    up_master = {m["id"]: tuple(m["axesValues"]) for m in up["fontMaster"]}
    t = math.tan(math.radians(8))
    checked = 0
    for g in up["glyphs"]:
        u = g.get("unicode")
        if not (isinstance(u, int) and 0x0400 <= u <= 0x052F):
            continue
        for layer in g["layers"]:
            if layer["layerId"] not in up_master or any("ref" in s for s in layer.get("shapes", [])):
                continue
            mid, xh = it_master[up_master[layer["layerId"]]]
            other = next(l for l in it_glyphs[g["glyphname"]]["layers"] if l["layerId"] == mid)
            assert other["width"] == layer["width"], g["glyphname"]
            for a, b in zip(layer["shapes"], other["shapes"], strict=True):
                for (ax, ay, *_), (bx, by, *_) in zip(a["nodes"], b["nodes"], strict=True):
                    assert by == ay
                    assert abs(bx - (ax + t * (ay - xh / 2))) <= 0.5, (g["glyphname"], ax, ay, bx)
            checked += 1
    assert checked >= 3 * 50


@pytest.mark.parametrize("path", [VF, VF_IT], ids=["upright", "italic"])
def test_long_s_is_f_without_bar(path):
    font = TTFont(path)
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen

    def bounds(g):
        pen = BoundsPen(gs)
        gs[g].draw(pen)
        return pen.bounds

    f, s = bounds(cmap[ord("f")]), bounds(cmap[0x017F])
    assert s[3] == f[3]  # same top (the hook)
    assert (s[2] - s[0]) < (f[2] - f[0])  # narrower: no crossbar


@pytest.mark.parametrize("path", [VF, VF_IT], ids=["upright", "italic"])
def test_instance_names_fit_32(path):
    font = TTFont(path)
    name = font["name"]
    family = name.getDebugName(16) or name.getDebugName(1)
    for inst in font["fvar"].instances:
        full = f"{family} {name.getDebugName(inst.subfamilyNameID)}"
        assert len(full) <= 32, full


def test_stat_names_every_weight():
    names = {"ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"}
    for path in (VF, VF_IT):
        font = TTFont(path)
        stat = font["STAT"].table
        got = {font["name"].getDebugName(v.ValueNameID) for v in stat.AxisValueArray.AxisValue if v.AxisIndex == 0}
        assert names <= got, path


@pytest.mark.parametrize("path", OTF, ids=ids)
def test_otf_is_hinted(path):
    import fontTools.subset.cff  # noqa: F401  (adds CFFFontSet.desubroutinize)

    font = TTFont(path)
    font["CFF "].cff.desubroutinize()
    top = font["CFF "].cff.topDictIndex[0]
    private = top.Private
    assert getattr(private, "StdVW", None), "No StdVW: otfautohint ran without stems."
    assert private.BlueValues
    for glyph in ("H", "n", "o"):
        cs = top.CharStrings[glyph]
        cs.decompile()
        ops = {x for x in cs.program if isinstance(x, str)}
        assert ops & {"hstem", "hstemhm", "vstem", "vstemhm"}, glyph


@pytest.mark.parametrize("path", TTF, ids=ids)
def test_ttf_is_hinted(path):
    font = TTFont(path)
    assert "fpgm" in font and "prep" in font
    assert "TTFA" not in font  # --no-info


def _audit_fonts():
    from kernaudit import Font

    fonts = [(p.split("/")[-1], Font(p)) for p in TTF]
    for path in (VF, VF_IT):
        for w in (250, 450, 650, 750):
            fonts.append((f"{path.name}@{w}", Font(str(path), {"wght": w})))
    return fonts


def test_no_pair_touches():
    """No pair in the kerning audit list overlaps, in any static font and at
    weights between the masters of the variable fonts."""
    from kernaudit import default_pairs, measure

    pairs = default_pairs()
    bad = []
    for label, font in _audit_fonts():
        for p in pairs:
            m = measure(font, p)
            if m and m["min_gap"] is not None and m["min_gap"] < 0:
                bad.append((label, p, m["min_gap"], m["kern"]))
    assert not bad, bad[:20]


def test_cyrillic_lookalikes_kern_like_latin():
    import uharfbuzz as hb

    for path in (VF, VF_IT):
        f = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

        def adv(text):
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(f, buf, {})
            return [p.x_advance for p in buf.glyph_positions]

        for lat, cyr in (("To", "То"), ("TA", "ТА"), ("Po", "Ро"), ("AT", "АТ")):
            assert adv(lat) == adv(cyr), (path.name, lat)
