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
from loom.sketch import G, GI

VERSION = (0, 100)  # 0.100: Warp 0.1
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
# (contrast 11.3 instead of 9), serifs +30 % thick (serifw 0.82) and
# 20 % shorter, skeleton 6 % wider so that the counters stay open.
BOLD = dict(stem=134, contrast=11.3, serifw=0.82, serif=0.8, width=1.06)


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


def table_def(key: str, ital: bool):
    return (GI.get(key) if ital else None) or G[key]


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
    d = table_def(gl.key, p.ital)
    mods = variant_mods(gl, p)
    sw = E.compose(d, p, mods)
    adv, dx = sw.adv, sw.dx
    if gl.variant is None and E.is_greek_lower(gl.key):
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
    return Drawn(contours, adv, c + dx, sw.yc, sw.sl, top, sw.ymax, sw)


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
    st = STYLES[style_key]
    p = st.p()
    if gl.comp_kind == "ref":
        b = drawn(style_key, gl.comps[0])
        return [(gl.comps[0], 0, 0)], b.adv
    if gl.comp_kind == "greek-ref":
        b = drawn(style_key, gl.comps[0])
        return [(gl.comps[0], p.sb * 0.25, 0)], b.adv + p.sb * 0.5
    if gl.comp_kind == "frac":
        parts, x = [], 0.0
        for k, nm in enumerate(gl.comps):
            dd = drawn(style_key, nm)
            parts.append((nm, x, 0))
            x += dd.adv
        return parts, x
    base, mark = gl.comps
    b = drawn(style_key, base)
    m = drawn(style_key, mark)
    dy = 0.0
    if gl.comp_kind == "sc-accent" and mark != "cedillacomb":
        dy = b.top - p.cap
    dx = b.center + dy * b.sl
    adv = b.adv
    # a mark wider than a narrow base (ı, I) widens the glyph a little
    return [(base, 0, 0), (mark, dx, dy)], adv


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
        if name.split(".")[0] in BELOW:
            return [("_bottom", (0 - d.yc) * d.sl, 0)]
        top = d.ymax
        return [("_top", (base_y - d.yc) * d.sl, base_y), ("top", (top - d.yc) * d.sl, top)]
    if gl.category == "ligature":
        n = gl.name.count("_") + 1 if "_" in gl.name else 2
        return [(f"caret_{k}", d.adv * k / n, 0) for k in range(1, n)]
    if not gl.unicodes or gl.variant:
        return []
    ch = chr(gl.unicodes[0])
    if not ch.isalpha() or gl.category == "ligature":
        return []
    out = [("top", d.center + (d.top - d.yc) * d.sl, d.top)]
    out.append(("bottom", d.center + (0 - d.yc) * d.sl, 0))
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
        if gl.comps:
            comps, adv = component_offsets(style_key, gl)
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
