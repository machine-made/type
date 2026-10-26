"""Tests for the compiled fonts in fonts/sans."""

from __future__ import annotations

import glob

import pytest
import uharfbuzz as hb
from conftest import FONTS
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

VF = FONTS / "variable" / "MachineMadeSans[wght].ttf"
VF_IT = FONTS / "variable" / "MachineMadeSans-Italic[wght].ttf"
ALL = sorted(glob.glob(str(FONTS / "*" / "*.*")))
STATICS = [p for p in ALL if "/ttf/" in p or "/otf/" in p]
WEIGHTS = ["ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]

# Letters with a Lancip or Lurus default form (base letters only).
CHANGED = "afghijklmnpqrtuyGIKU"


def test_file_set():
    names = {p.split("/fonts/sans/")[1] for p in ALL}
    expected = {"variable/MachineMadeSans[wght].ttf", "variable/MachineMadeSans-Italic[wght].ttf"}
    expected |= {"webfonts/MachineMadeSans[wght].woff2", "webfonts/MachineMadeSans-Italic[wght].woff2"}
    for w in WEIGHTS:
        for ext in ("ttf", "otf"):
            expected.add(f"{ext}/MachineMadeSans-{w}.{ext}")
            it = "Italic" if w == "Regular" else f"{w}Italic"
            expected.add(f"{ext}/MachineMadeSans-{it}.{ext}")
    assert names == expected


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.split("/fonts/sans/")[1])
def test_names(path):
    font = TTFont(path)
    for rec in font["name"].names:
        text = rec.toUnicode()
        if rec.nameID in (0, 10):
            continue  # Copyright and description keep the upstream credit.
        assert "Jakarta" not in text, (rec.nameID, text)
        assert "machine-madeSans" not in text, (rec.nameID, text)
    assert font["name"].getDebugName(1).startswith("machine-made Sans")
    assert "Plus Jakarta Sans Project Authors" in font["name"].getDebugName(0)
    assert "machine-made Sans Project Authors" in font["name"].getDebugName(0)
    assert "Gumpita Rahayu" in font["name"].getDebugName(10)


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.split("/fonts/sans/")[1])
def test_line_metrics(path):
    font = TTFont(path)
    os2, hhea = font["OS/2"], font["hhea"]
    assert font["head"].unitsPerEm == 1000
    assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == (875, -281, 0)
    assert (hhea.ascent, hhea.descent, hhea.lineGap) == (875, -281, 0)
    assert os2.fsSelection & (1 << 7), "USE_TYPO_METRICS must be set."
    assert os2.usWinAscent >= font["head"].yMax
    assert os2.usWinDescent >= -font["head"].yMin


@pytest.mark.parametrize("path", STATICS, ids=lambda p: p.split("/fonts/sans/")[1])
def test_style_linking(path):
    font = TTFont(path)
    style = font["name"].getDebugName(2)
    bold = style in ("Bold", "Bold Italic")
    italic = "Italic" in style
    sel = font["OS/2"].fsSelection
    assert bool(sel & 1) == italic
    assert bool(sel & (1 << 5)) == bold
    assert "STAT" in font


def outline(font: TTFont, glyph: str):
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[glyph].draw(pen)
    return pen.value


def shape(path, text: str, features: dict) -> list[str]:
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


@pytest.mark.parametrize("italic", [False, True], ids=["upright", "italic"])
def test_defaults_are_upstream_alternates(upstream, italic):
    """Each changed default draws the upstream Lurus form, else the Lancip form.

    And ss01 draws the upstream default form. Outlines are compared at the
    default location (wght 400).
    """
    name = "PlusJakartaSans-Italic[wght].ttf" if italic else "PlusJakartaSans[wght].ttf"
    up_path = upstream / "fonts" / "variable" / name
    mine_path = VF_IT if italic else VF
    up, mine = TTFont(up_path), TTFont(mine_path)
    for ch in CHANGED:
        g_up_lurus = shape(up_path, ch, {"ss02": True})[0]
        g_up_lancip = shape(up_path, ch, {"ss01": True})[0]
        g_up_default = shape(up_path, ch, {})[0]
        expected = g_up_lurus if g_up_lurus != g_up_default else g_up_lancip
        g_mine = shape(mine_path, ch, {})[0]
        assert outline(mine, g_mine) == outline(up, expected), ch
        g_mine_round = shape(mine_path, ch, {"ss01": True})[0]
        assert outline(mine, g_mine_round) == outline(up, g_up_default), ch


@pytest.mark.parametrize("path", [VF, VF_IT], ids=["upright", "italic"])
def test_set_names_in_font(path):
    font = TTFont(path)
    labels = {}
    for rec in font["GSUB"].table.FeatureList.FeatureRecord:
        tag = rec.FeatureTag
        params = rec.Feature.FeatureParams
        if tag.startswith("ss") and params is not None:
            labels[tag] = font["name"].getDebugName(params.UINameID)
    assert labels["ss01"] == "Round forms (original defaults)"
    assert labels["ss02"] == "Lancip: sharp a j r y"
    assert labels["ss03"] == "Lingkar: swirl"


@pytest.mark.parametrize("path", [VF, VF_IT], ids=["upright", "italic"])
def test_ligatures_use_round_f(path):
    """The f ligatures have round forms, so only the round set (ss01) makes them.

    The default sharp f has no hook over the next letter and needs no ligature.
    """
    assert shape(path, "fi", {}) == ["f", "i"]
    assert shape(path, "fi", {"ss01": True}) == ["fi"]
    assert shape(path, "fl", {"ss01": True}) == ["fl"]
    assert shape(path, "ffi", {"ss01": True}) == ["f_f_i"]
    assert shape(path, "fi", {"ss01": True, "liga": False}) == ["f.ss01", "i.ss01"]


def test_up_down_arrow_has_outline():
    for path in [VF] + [p for p in STATICS if "Italic" not in p]:
        font = TTFont(path)
        glyph = font.getBestCmap()[0x2195]
        assert outline(font, glyph), path
