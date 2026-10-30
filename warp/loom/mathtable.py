"""The OpenType MATH table of machine-made Warp (0.2).

`math_data(style_key, bounds)` returns the arguments of
fontTools.otlLib.builder.buildMathTable for one style. `bounds` maps a
glyph name to its (yMin, yMax) in the compiled font, so that the
variant heights and part advances are the ones the font has.

Constants come from the metrics of the face and from the pen:

* the rule thickness is the rule pen of the maths operators (the
  thickness of −, of the fraction bar and of the top of √): Rw in
  loom/sketch.py;
* the maths axis is 250 (BRIEF.md), the accent base height is the
  x-height, the flattened accent base height the cap height;
* shifts and gaps follow the suggestions of the OpenType MATH
  specification (multiples of the rule thickness and of the x-height).

Italic corrections: the mathematical italic letters, ℎ, ℏ and the large
integrals (how far the top of the ink leans out past the advance).
Top accent attachment: the top anchor of every letter.

Apache-2.0.
"""

from __future__ import annotations

from loom import build as Bd
from loom import charset as CS
from loom import mathglyphs as MG
from loom.sketch import AX, Rw

MIN_CONNECTOR_OVERLAP = 40   # more than the thickest hairline (Bold, 21.5 units), see loom/mathglyphs.py


def rule_thickness(p) -> int:
    return Bd.rnd(Rw(p))


def constants(p) -> dict:
    r = rule_thickness(p)
    x = p.xh
    R = Bd.rnd
    return {
        "ScriptPercentScaleDown": 70,
        "ScriptScriptPercentScaleDown": 50,
        "DelimitedSubFormulaMinHeight": 1500,
        "DisplayOperatorMinHeight": 1380,          # the first variant of ∑ ∏ (1400) and of ∫
        "MathLeading": 150,
        "AxisHeight": AX,
        "AccentBaseHeight": R(x),
        "FlattenedAccentBaseHeight": R(p.cap),
        "SubscriptShiftDown": R(0.36 * x),
        "SubscriptTopMax": R(0.8 * x),
        "SubscriptBaselineDropMin": R(0.47 * x),
        "SuperscriptShiftUp": R(0.84 * x),
        "SuperscriptShiftUpCramped": R(0.67 * x),
        "SuperscriptBottomMin": R(0.25 * x),
        "SuperscriptBaselineDropMax": R(0.58 * x),
        "SubSuperscriptGapMin": 4 * r,
        "SuperscriptBottomMaxWithSubscript": R(0.8 * x),
        "SpaceAfterScript": 42,
        "UpperLimitGapMin": R(0.26 * x),
        "UpperLimitBaselineRiseMin": R(0.47 * x),
        "LowerLimitGapMin": R(0.39 * x),
        "LowerLimitBaselineDropMin": R(1.4 * x),
        "StackTopShiftUp": R(1.03 * x),
        "StackTopDisplayStyleShiftUp": R(1.57 * x),
        "StackBottomShiftDown": R(0.8 * x),
        "StackBottomDisplayStyleShiftDown": R(1.6 * x),
        "StackGapMin": 3 * r,
        "StackDisplayStyleGapMin": 7 * r,
        "StretchStackTopShiftUp": R(0.26 * x),
        "StretchStackBottomShiftDown": R(1.39 * x),
        "StretchStackGapAboveMin": R(0.47 * x),
        "StretchStackGapBelowMin": R(0.39 * x),
        "FractionNumeratorShiftUp": R(0.9 * x),
        "FractionNumeratorDisplayStyleShiftUp": R(1.57 * x),
        "FractionDenominatorShiftDown": R(0.8 * x),
        "FractionDenominatorDisplayStyleShiftDown": R(1.6 * x),
        "FractionNumeratorGapMin": r,
        "FractionNumDisplayStyleGapMin": 3 * r,
        "FractionRuleThickness": r,
        "FractionDenominatorGapMin": r,
        "FractionDenomDisplayStyleGapMin": 3 * r,
        "SkewedFractionHorizontalGap": 350,
        "SkewedFractionVerticalGap": R(0.22 * x),
        "OverbarVerticalGap": 3 * r,
        "OverbarRuleThickness": r,
        "OverbarExtraAscender": r,
        "UnderbarVerticalGap": 3 * r,
        "UnderbarRuleThickness": r,
        "UnderbarExtraDescender": r,
        "RadicalVerticalGap": R(r * 1.25),
        "RadicalDisplayStyleVerticalGap": R(r + 0.25 * x),
        "RadicalRuleThickness": r,
        "RadicalExtraAscender": r,
        "RadicalKernBeforeDegree": 278,
        "RadicalKernAfterDegree": -556,
        "RadicalDegreeBottomRaisePercent": 60,
    }


def _glyph_ic(style_key: str, name: str, ref: str | None = None) -> int:
    """Italic correction: how far the ink of the top half leans out past the advance."""
    d = Bd.drawn(style_key, ref or name)
    lo = d.ymax * 0.5 if d.ymax > 0 else 0
    xs = [x + d.dx for poly in d.sweep.polys for x, y in poly if y >= lo]
    if not xs:
        return 0
    return max(0, Bd.rnd(max(xs) - d.adv + 12))


def italic_corrections(style_key: str) -> dict[str, int]:
    st = Bd.STYLES[style_key]
    out = {}
    for gl in CS.GLYPHS:
        if gl.variant == "mathit":
            if st.italic:
                base = CS.glyph_name(Bd.mathit_key(gl.key)) if gl.key != "∂" else "partialdiff"
                if CS.BY_NAME[base].comps:
                    base = CS.BY_NAME[base].comps[0]
                v = _glyph_ic(style_key, base)
            else:
                v = _glyph_ic(style_key, gl.name)
            if v:
                out[gl.name] = v
    for name in ("uni210E", "uni210F"):
        v = _glyph_ic(style_key, name)
        if v:
            out[name] = v
    # integrals: the top drop leans right of the bottom one
    for name in ["integral"] + MG.VARIANTS["integral"]:
        d = Bd.drawn(style_key, name)
        top = [x for poly in d.sweep.polys for x, y in poly if y > AX + (d.ymax - AX) * 0.5]
        bot = [x for poly in d.sweep.polys for x, y in poly if y < AX - (AX - d.sweep.ymin) * 0.5]
        if top and bot:
            out[name] = max(0, Bd.rnd((max(top) - max(bot)) * 0.5))
    return out


def top_accents(style_key: str) -> dict[str, int]:
    st = Bd.STYLES[style_key]
    out = {}
    for gl in CS.GLYPHS:
        if gl.comps:
            continue
        if gl.variant == "mathit" and st.italic:
            continue
        for nm, x, y in Bd.anchors(style_key, gl.name):
            if nm == "top":
                out[gl.name] = Bd.rnd(x)
    if st.italic:
        for gl in CS.GLYPHS:
            if gl.variant == "mathit":
                base = CS.glyph_name(Bd.mathit_key(gl.key)) if gl.key != "∂" else "partialdiff"
                if base in out:
                    out[gl.name] = out[base]
    return out


def math_data(style_key: str, bounds: dict[str, tuple[float, float]]) -> dict:
    p = Bd.STYLES[style_key].p()
    variants, assembly = {}, {}
    for base, names in MG.VARIANTS.items():
        seq = [base] + names
        variants[base] = [(n, Bd.rnd(bounds[n][1] - bounds[n][0])) for n in seq]
    for base, parts in MG.ASSEMBLY.items():
        out = []
        for name, extender, role in parts:
            h = bounds[name][1] - bounds[name][0]
            s, e = MG.connectors(role, p.B, h)
            out.append((name, 1 if extender else 0, Bd.rnd(s), Bd.rnd(e), Bd.rnd(h)))
        assembly[base] = (out, 0)
    extended = set(MG.MATH_GLYPHS) | set(MG.VARIANTS)
    return {
        "constants": constants(p),
        "italicsCorrections": italic_corrections(style_key),
        "topAccentAttachments": top_accents(style_key),
        "extendedShapes": extended,
        "minConnectorOverlap": MIN_CONNECTOR_OVERLAP,
        "vertGlyphVariants": variants,
        "vertGlyphAssembly": assembly,
    }
