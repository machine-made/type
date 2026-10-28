"""Build the machine-made Warp 0.1 sources: one UFO per static style.

Usage:
    python -m loom.build [--out build] [--styles Regular,Italic,...]

Writes build/ufo/MachineMadeWarp-{Style}.ufo and
build/ufo/MachineMadeWarpDisplay-{Style}.ufo. fontmake compiles them
(scripts/build.sh).

Each glyph is swept by the pen model (loom/engine.py), its sweep is
unioned with skia-pathops and fitted with cubic curves
(loom/outline.py). Accented letters, the Greek capitals that look like
Latin ones, µ, ο and the fractions are composites.

Why statics and not a variable font: a pen sweep is a union of nib
hulls. Its point structure changes with the stem, the contrast and the
optical size, so masters are not point-compatible without a fixed
outline topology. The variable font (wght, opsz) is planned for 0.3.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import math
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import ufoLib2
from ufoLib2.objects import Anchor, Component

from loom import charset as CS
from loom import engine as E
from loom import features as F
from loom import kerning as K
from loom import outline as O
from loom import revisions as RV
from loom.latin_ext import OGONEK, mathit_def
from loom.sketch import G, GI

VERSION = (0, 200)  # 0.200: Warp 0.2
COPYRIGHT = "Copyright 2026 The machine-made Warp Project Authors (https://github.com/machine-made/type)"
LICENSE_DESCRIPTION = (
    "This Font Software is licensed under the SIL Open Font License, "
    "Version 1.1. This license is available with a FAQ at: "
    "https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
UPM = 1000
TYPO_ASCENDER = 900
TYPO_DESCENDER = -300
UNDERLINE_POSITION = -150
UNDERLINE_THICKNESS = 25

# Optical sizes of the statics (the engine's opsz parameter, in points).
# Text: opsz 10 sets best at 9 to 12 pt (tools/readability.py compares
# 9, 10, 11 and 12; see BRIEF.md). Display: opsz 60, for titles.
TEXT_OPSZ = 10
DISPLAY_OPSZ = 60

# Bold: stem +59.5 % (84 -> 134 units at opsz 72), hairline +30 %
# (contrast 11.3 instead of 9), serifs +30 % thick (serifw 0.82) and as
# long as the Regular's (serif 0.65 of the bold stem), skeleton 6 % wider
# so that the counters stay open.
BOLD = dict(stem=134, contrast=11.3, serifw=0.82, serif=0.65, width=1.06)


@dataclass(frozen=True)
class Style:
    key: str          # file style: Regular, Italic, Bold, BoldItalic, Display, DisplayItalic
    family: str
    style: str        # name table style
    ps_family: str
    ps_style: str
    weight: int
    italic: bool
    opsz: int
    params: tuple     # engine parameters

    def p(self) -> E.Params:
        return E.params(**dict(self.params))


def _style(key, family, style, ps_family, ps_style, weight, italic, opsz, **extra):
    prm = dict(opsz=opsz, ital=italic, **extra)
    return Style(key, family, style, ps_family, ps_style, weight, italic, opsz, tuple(sorted(prm.items())))


FAMILY = "machine-made Warp"
DISPLAY_FAMILY = "machine-made Warp Display"
PS_FAMILY = "MachineMadeWarp"
PS_DISPLAY = "MachineMadeWarpDisplay"

STYLES = {
    "Regular": _style("Regular", FAMILY, "Regular", PS_FAMILY, "Regular", 400, False, TEXT_OPSZ),
    "Italic": _style("Italic", FAMILY, "Italic", PS_FAMILY, "Italic", 400, True, TEXT_OPSZ),
    "Bold": _style("Bold", FAMILY, "Bold", PS_FAMILY, "Bold", 700, False, TEXT_OPSZ, **BOLD),
    "BoldItalic": _style("BoldItalic", FAMILY, "Bold Italic", PS_FAMILY, "BoldItalic", 700, True, TEXT_OPSZ, **BOLD),
    "Display": _style("Display", DISPLAY_FAMILY, "Regular", PS_DISPLAY, "Regular", 400, False, DISPLAY_OPSZ),
    "DisplayItalic": _style("DisplayItalic", DISPLAY_FAMILY, "Italic", PS_DISPLAY, "Italic", 400, True, DISPLAY_OPSZ),
}


def ps_name(st: Style) -> str:
    return f"{st.ps_family}-{st.ps_style}"


def rnd(v: float) -> int:
    return int(math.floor(v + 0.5))


# ------------------------------------------------------------- variants

def sup_mods(p: E.Params, top: float) -> dict:
    """Superior forms: the drawing at 60 % size, lighter, narrower, raised so its top is at `top`."""
    k = 0.6
    q = {"cap": p.cap * k, "xh": p.xh * k, "A": p.A * 0.72, "B": max(p.B * 0.85, 5), "S": p.S * 0.8,
         "sl": p.sl * 0.6, "bd": p.bd * 0.7, "os": p.os * k, "sb": p.sb * 0.6}
    return {"p": q, "wdx": 0.62, "prop": True, "dy": top}


def variant_mods(gl: CS.Glyph, p: E.Params) -> dict:
    v = gl.variant
    if v is None:
        return {}
    if v == "sc":
        return E.sc_mods(p)
    if v == "osf":
        return E.osf_mods(p, gl.key)
    if v == "tosf":
        m = E.osf_mods(p, gl.key)
        m["prop"] = False
        return m
    if v == "lf":
        return {"prop": True}
    if v == "sup":
        m = sup_mods(p, 0)
        h = m["p"]["xh"] if gl.key in ("a", "o") else m["p"]["cap"]
        m["dy"] = p.cap - h + (p.os if gl.key in ("a", "o") else 0)
        return m
    if v == "dnom":
        return sup_mods(p, 0)
    raise ValueError(v)


# ---------------------------------------------------------------- glyphs

@dataclass
class Drawn:
    contours: list      # fitted contours (segments), already moved by dx
    adv: float
    center: float       # unslanted ink centre of the middle band, in glyph coordinates
    yc: float
    sl: float
    top: float          # height where a top mark sits
    ymax: float
    sweep: object = None
    dx: float = 0.0


def table_def(key: str, ital: bool):
    return (GI.get(key) if ital else None) or G[key]


# Italic counterpart of each style (for the mathematical italic letters).
ITALIC_OF = {"Regular": "Italic", "Bold": "BoldItalic", "Display": "DisplayItalic",
             "Italic": "Italic", "BoldItalic": "BoldItalic", "DisplayItalic": "DisplayItalic"}


def mathit_key(key: str) -> str:
    """The drawing of a mathematical italic letter: Greek look-alikes use the Latin drawing."""
    if key == "ο":
        return "o"
    return CS.GREEK_LOOKALIKE.get(key, key)


# Glyphs that get the ogonek: the inset of its anchor from the right foot
# (design units), or None for the middle of the foot.
OGONEK_BASES = {"A": 100, "a": 34, "E": 125, "e": 60, "I": None, "i": None, "U": 135, "u": 58}


def ink_bounds(contours) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for c in contours:
        for s in c:
            pts = [s[1], s[2]] if s[0] == "line" else list(s[1])
            for q in pts:
                xs.append(float(q[0])); ys.append(float(q[1]))
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs), max(xs), min(ys), max(ys)


def band_xmax(d, lo: float, hi: float) -> float | None:
    """Rightmost ink of a drawn glyph between heights lo and hi (font coordinates)."""
    xs = [x + d.dx for poly in d.sweep.polys for x, y in poly if lo <= y <= hi]
    return max(xs) if xs else None


def band_xmin(d, lo: float, hi: float) -> float | None:
    xs = [x + d.dx for poly in d.sweep.polys for x, y in poly if lo <= y <= hi]
    return min(xs) if xs else None


def band_center(sw: E.Swept, lo: float, hi: float) -> float | None:
    xs = []
    for poly in sw.polys:
        for x, y in poly:
            if lo <= y <= hi:
                xs.append(x - (y - sw.yc) * sw.sl)
    if not xs:
        return None
    return (min(xs) + max(xs)) / 2


@lru_cache(maxsize=None)
def drawn(style_key: str, name: str) -> Drawn:
    st = STYLES[style_key]
    p = st.p()
    gl = CS.BY_NAME[name]
    if gl.variant == "notdef":
        return notdef(p)
    if gl.variant == "mathit":
        key = mathit_key(gl.key)
        d = mathit_def(key)
        mods = {}
        if d.cap and key not in GI:
            mods = {"p": {"bk": 0}}
        return _finish(style_key, gl, p, d, mods)
    d = table_def(gl.key, p.ital)
    mods = variant_mods(gl, p)
    return _finish(style_key, gl, p, d, mods)


def _finish(style_key: str, gl, p, d, mods) -> Drawn:
    if p.ital and d.cap and gl.key not in GI and gl.variant != "mathit":
        # Italic capitals without their own form are the roman ones,
        # slanted, with unbracketed serifs (as in Didone italics).
        mods = dict(mods)
        mods["p"] = {**mods.get("p", {}), "bk": 0}
    sw = E.compose(d, p, mods)
    adv, dx = sw.adv, sw.dx
    if isinstance(sw.ret, dict) and "dx" in sw.ret:
        # assembly parts: a placement shared by all parts of one assembly
        adv, dx = sw.ret["adv"], sw.ret["dx"]
    if gl.key == " ":
        adv = RV.word_space(p)
    if gl.variant in (None, "mathit") and E.is_greek_lower(gl.key):
        adv += p.sb * 0.5
        dx += p.sb * 0.25
    if gl.category == "mark":
        adv, dx = 0.0, 0.0
    if gl.variant is None and gl.key in CS.EQUAL_WIDTH_MATHS and gl.key != "+":
        adv = drawn(style_key, "plus").adv
        dx = (adv - (sw.xmax - sw.xmin)) / 2 - sw.xmin
    contours = O.outline(sw.polys)
    contours = [[(s[0], s[1] + (dx, 0), s[2] + (dx, 0)) if s[0] == "line" else (s[0], s[1] + (dx, 0)) for s in c]
                for c in contours]
    if gl.height == "cap":
        top = p.cap
    elif gl.height == "sc":
        top = p.xh * 1.1
    else:
        top = p.xh
    c = band_center(sw, top * 0.2, top * 0.8)
    if c is None:
        c = (sw.xmin + sw.xmax) / 2
    return Drawn(contours, adv, c + dx, sw.yc, sw.sl, top, sw.ymax, sw, dx)


def notdef(p: E.Params) -> Drawn:
    import numpy as np
    w, h, t = 480, p.cap, 50
    x0 = 60

    def box(a, b, c, d, ccw=True):
        pts = [(a, b), (c, b), (c, d), (a, d)]
        if not ccw:
            pts = pts[::-1]
        return [("line", np.array(pts[i], float), np.array(pts[(i + 1) % 4], float)) for i in range(4)]
    contours = [box(x0, 0, x0 + w, h), box(x0 + t, t, x0 + w - t, h - t, ccw=False)]
    return Drawn(contours, w + 2 * x0, x0 + w / 2, 0, 0, h, h)


def component_offsets(style_key: str, gl: CS.Glyph) -> tuple[list, float]:
    """[(component, dx, dy)] and the advance of a composite glyph."""
    from loom.extended import BELOW
    st = STYLES[style_key]
    p = st.p()
    kind = gl.comp_kind
    if kind == "ref":
        b = drawn_or_comp_adv(style_key, gl.comps[0])
        return [(gl.comps[0], 0, 0)], b
    if kind == "greek-ref":
        b = drawn(style_key, gl.comps[0])
        return [(gl.comps[0], p.sb * 0.25, 0)], b.adv + p.sb * 0.5
    if kind == "inferior":
        b = drawn(style_key, gl.comps[0])
        return [(gl.comps[0], 0, INFERIOR_DY)], b.adv
    if kind == "frac":
        parts, x = [], 0.0
        for k, nm in enumerate(gl.comps):
            dd = drawn(style_key, nm)
            parts.append((nm, x, 0))
            x += dd.adv
        return parts, x
    if kind == "pair":
        a, b = gl.comps
        da, db = drawn(style_key, a), drawn(style_key, b)
        if (a, b) == ("i", "j"):
            # the stems of ĳ stand a fixed distance apart; the hook of j runs under the i
            dist = (300 if st.italic else 250) * p.wd
            x = da.dx + dist - db.dx
            return [(a, 0, 0), (b, x, 0)], x + db.adv
        kern = -p.sb * 0.35
        return [(a, 0, 0), (b, da.adv + kern, 0)], da.adv + kern + db.adv
    if kind == "ldot":
        base, dot = gl.comps
        b, m = drawn(style_key, base), drawn(style_key, dot)
        cap = base == "L"
        yd = p.cap * 0.47 if cap else p.xh * 0.62
        stem_half = p.A * (0.92 if cap else 1.0) / 2
        x = (stem_half + (120 if cap else 95)) * p.wd + b.dx + (yd - b.yc) * b.sl
        dx = x - m.center
        dy = yd - 250
        adv = b.adv if cap else max(b.adv, x + (m.adv - m.center) * 0.9)
        return [(base, 0, 0), (dot, dx, dy)], adv
    base, mark = gl.comps
    b = drawn_any(style_key, base)
    m = drawn(style_key, mark)
    if kind == "ogonek":
        x = ogonek_x(style_key, base)
        return [(base, 0, 0), (mark, x - (0 - m.yc) * m.sl, 0)], b.adv
    if kind == "caronalt":
        # right of the ascender (d l), the cap stem (L) or the t
        top = {"t": p.xh + 178, "L": p.cap}.get(base, p.asc)
        dy = top - p.asc
        xr = band_xmax(b, top - 150, top + 40)
        mx0 = ink_bounds(m.contours)[0]
        gap = 26 if base != "L" else 40
        dx = xr + gap - (mx0 + dy * m.sl)
        adv = b.adv if base in ("L", "t") else max(b.adv, dx + ink_bounds(m.contours)[1] + dy * m.sl + p.sb * 0.5)
        if base == "t":
            adv = max(b.adv, dx + ink_bounds(m.contours)[1] + dy * m.sl + p.sb * 0.3)
        return [(base, 0, 0), (mark, dx, dy)], adv
    if kind == "ascender":
        # above the ascender, over the stem (ĥ)
        dy = p.asc - p.cap
        dx = b.dx + (p.asc - b.yc) * b.sl - (p.cap - m.yc) * m.sl
        return [(base, 0, 0), (mark, dx, dy)], b.adv
    if kind == "tonos":
        # Greek capitals: the tonos stands left of the letter, which moves right.
        bx0 = ink_bounds(b.contours)[0]
        mx0, mx1 = ink_bounds(m.contours)[:2]
        gap = 34
        shift = max(0.0, (mx1 - mx0) + gap + p.sb * 0.7 - bx0)
        dx = shift + bx0 - gap - mx1
        return [(base, shift, 0), (mark, dx, 0)], b.adv + shift
    dy = 0.0
    if kind == "sc-accent" and mark not in BELOW and mark != "cedillacomb":
        dy = b.top - p.cap
    dx = b.center + dy * b.sl
    adv = b.adv
    return [(base, 0, 0), (mark, dx, dy)], adv


INFERIOR_DY = -150   # inferior figures: the denominators, lowered


def flatten(style_key: str, comps: list) -> list:
    """Replace components that are themselves composites by their components (no nesting)."""
    out = []
    for name, dx, dy in comps:
        gl = CS.BY_NAME[name]
        if gl.comps:
            sub, _ = component_offsets(style_key, gl)
            out += [(n, dx + x, dy + y) for n, x, y in flatten(style_key, sub)]
        else:
            out.append((name, dx, dy))
    return out


def drawn_any(style_key: str, name: str) -> Drawn:
    """drawn() for a glyph, or for a reference composite (ο, Greek look-alikes): the referenced
    drawing, moved by its offset."""
    from dataclasses import replace
    gl = CS.BY_NAME[name]
    if not gl.comps:
        return drawn(style_key, name)
    if gl.comp_kind not in ("ref", "greek-ref"):
        raise ValueError(f"{name}: cannot be the base of an accented composite")
    (ref, ox, oy), adv = component_offsets(style_key, gl)[0][0], component_offsets(style_key, gl)[1]
    d = drawn_any(style_key, ref)
    contours = [[(s[0], s[1] + (ox, 0), s[2] + (ox, 0)) if s[0] == "line" else (s[0], s[1] + (ox, 0)) for s in c]
                for c in d.contours]
    return replace(d, contours=contours, adv=adv, center=d.center + ox, dx=d.dx + ox)


def drawn_or_comp_adv(style_key: str, name: str) -> float:
    gl = CS.BY_NAME[name]
    if gl.comps:
        return component_offsets(style_key, gl)[1]
    return drawn(style_key, name).adv


def ogonek_x(style_key: str, name: str) -> float:
    """x of the ogonek anchor: the right foot of the base, moved in."""
    d = drawn(style_key, name)
    key = CS.BY_NAME[name].key
    xr = band_xmax(d, -5, 60)
    xl = band_xmin(d, -5, 60)
    inset = OGONEK_BASES.get(key, 60)
    p = STYLES[style_key].p()
    if inset is None:
        return (xr + xl) / 2
    return xr - inset * p.wd


# -------------------------------------------------------------- anchors

def anchors(style_key: str, name: str) -> list[tuple[str, float, float]]:
    gl = CS.BY_NAME[name]
    if gl.comps or gl.variant == "notdef":
        return []
    d = drawn(style_key, name)
    if gl.category == "mark":
        from loom.extended import BELOW
        p = STYLES[style_key].p()
        base_y = p.cap if name.endswith(".case") else p.xh
        if name in ("caroncomb.alt", "tonoscomb.case"):
            return []   # placed by the composites only
        if name.split(".")[0] in BELOW:
            return [("_bottom", (0 - d.yc) * d.sl, 0)]
        if name in OGONEK:
            return [("_ogonek", (0 - d.yc) * d.sl, 0)]
        top = d.ymax
        return [("_top", (base_y - d.yc) * d.sl, base_y), ("top", (top - d.yc) * d.sl, top)]
    if gl.category == "ligature":
        n = gl.name.count("_") + 1 if "_" in gl.name else 2
        return [(f"caret_{k}", d.adv * k / n, 0) for k in range(1, n)]
    if not gl.unicodes or gl.variant not in (None, "mathit"):
        return []
    ch = chr(gl.unicodes[0])
    if not ch.isalpha() or gl.category == "ligature":
        return []
    out = [("top", d.center + (d.top - d.yc) * d.sl, d.top)]
    out.append(("bottom", d.center + (0 - d.yc) * d.sl, 0))
    if gl.key in OGONEK_BASES and gl.variant is None:
        out.append(("ogonek", ogonek_x(style_key, name), 0))
    return out


# ------------------------------------------------------------------ UFO

def set_info(font: ufoLib2.Font, st: Style) -> None:
    p = st.p()
    info = font.info
    info.familyName = st.family
    info.styleName = st.style
    info.styleMapFamilyName = st.family
    info.styleMapStyleName = {("Regular"): "regular", "Italic": "italic", "Bold": "bold",
                              "Bold Italic": "bold italic"}[st.style]
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = COPYRIGHT
    info.openTypeNameLicense = LICENSE_DESCRIPTION
    info.openTypeNameLicenseURL = LICENSE_URL
    info.openTypeNameManufacturer = "machine-made"
    info.openTypeNameManufacturerURL = "https://github.com/machine-made"
    info.openTypeNameDesigner = "machine-made agents"
    info.openTypeNameDescription = (
        "Warp is a Modern serif for science by machine-made: every letter is a few "
        "centre-lines swept by one level pen."
    )
    info.postscriptFontName = ps_name(st)
    info.postscriptIsFixedPitch = False
    info.postscriptUnderlinePosition = UNDERLINE_POSITION
    info.postscriptUnderlineThickness = UNDERLINE_THICKNESS
    info.openTypeOS2VendorID = "NONE"
    info.openTypeOS2WeightClass = st.weight
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2Type = []
    # Bit 7: USE_TYPO_METRICS. Bit 8: WWS (both families name only
    # weight and slope in the style; "Display" is in the family name).
    info.openTypeOS2Selection = [7, 8]
    info.openTypeOS2Panose = [2, 0, 5 if st.weight == 400 else 8, 3, 0, 0, 0, 0, 0, 0]
    info.unitsPerEm = UPM
    info.xHeight = rnd(p.xh)
    info.capHeight = rnd(p.cap)
    info.ascender = rnd(p.asc)
    info.descender = rnd(p.desc)
    info.italicAngle = -round(math.degrees(math.atan(p.slant)), 2) if st.italic else 0
    info.openTypeOS2TypoAscender = TYPO_ASCENDER
    info.openTypeOS2TypoDescender = TYPO_DESCENDER
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = TYPO_ASCENDER
    info.openTypeHheaDescender = TYPO_DESCENDER
    info.openTypeHheaLineGap = 0
    full = f"{st.family} {st.style}"
    if len(full) > 32:
        # "machine-made Warp Display Regular" is 33 characters: the full
        # name elides "Regular", as many families do.
        full = st.family
        info.openTypeNameRecords = [
            {"nameID": 4, "platformID": 3, "encodingID": 1, "languageID": 0x409, "string": full},
        ]
    assert len(full) <= 32
    font.lib["public.postscriptNames"] = {}
    font.lib["com.github.googlei18n.ufo2ft.featureWriters"] = [
        {"class": "KernFeatureWriter"},
        {"class": "MarkFeatureWriter"},
        {"class": "GdefFeatureWriter"},
    ]


def build_font(style_key: str) -> ufoLib2.Font:
    st = STYLES[style_key]
    font = ufoLib2.Font()
    set_info(font, st)
    font.lib["public.glyphOrder"] = list(CS.ORDER)
    cats = {}
    for gl in CS.GLYPHS:
        g = font.newGlyph(gl.name)
        g.unicodes = list(gl.unicodes)
        if gl.variant == "mathit" and st.italic:
            # in the italic styles the mathematical italic letter is the letter itself
            base = CS.glyph_name(gl.key)
            g.width = rnd(drawn_or_comp_adv(style_key, base))
            for n, dx, dy in flatten(style_key, [(base, 0, 0)]):
                g.components.append(Component(n, transformation=(1, 0, 0, 1, rnd(dx), rnd(dy))))
        elif gl.comps:
            comps, adv = component_offsets(style_key, gl)
            comps = flatten(style_key, comps)
            g.width = rnd(adv)
            for base, dx, dy in comps:
                g.components.append(Component(base, transformation=(1, 0, 0, 1, rnd(dx), rnd(dy))))
        else:
            d = drawn(style_key, gl.name)
            g.width = rnd(d.adv)
            O.draw(d.contours, g.getPen())
        for nm, x, y in anchors(style_key, gl.name):
            g.anchors.append(Anchor(rnd(x), rnd(y), nm))
        cats[gl.name] = gl.category
    font.lib["public.openTypeCategories"] = cats
    font.groups.update(K.groups())
    font.kerning.update(K.kerning(st))
    font.features.text = F.features(st)
    return font


def win_metrics(fonts) -> tuple[int, int]:
    y_min, y_max = 0.0, 0.0
    for f in fonts:
        for glyph in f:
            b = glyph.getBounds(f)
            if b is not None:
                y_min = min(y_min, b.yMin)
                y_max = max(y_max, b.yMax)
    return max(TYPO_ASCENDER, math.ceil(y_max)), max(-TYPO_DESCENDER, math.ceil(-y_min))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Warp 0.1 UFO sources.")
    ap.add_argument("--out", default="build")
    ap.add_argument("--styles", default=",".join(STYLES))
    ap.add_argument("--jobs", type=int, default=1, help="Build styles in parallel processes.")
    args = ap.parse_args(argv)
    out = Path(args.out) / "ufo"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    keys = [k for k in args.styles.split(",") if k]
    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(args.jobs) as ex:
            fonts = dict(zip(keys, ex.map(build_font, keys)))
    else:
        fonts = {k: build_font(k) for k in keys}
    metrics = win_metrics(fonts.values())
    for k, f in fonts.items():
        f.info.openTypeOS2WinAscent, f.info.openTypeOS2WinDescent = metrics
        path = out / f"{ps_name(STYLES[k])}.ufo"
        f.save(path, overwrite=True)
        print(f"Wrote {path} ({len(f)} glyphs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
