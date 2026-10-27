# Warp brief

machine-made Warp is a Modern serif for science: papers, theses,
journals and maths. A level pen draws every letter. Its stress is
vertical, its hairlines are horizontal, its serifs are thin and lightly
bracketed, and its terminals are teardrops. This file sets the metrics,
the styles, the glyph set, the build and the name check. Source of all
shapes: the approved sketch 0.2 (`reference/warp-sketch-0.2.js`, glyph
tables `G` and `GI`; specimen page `reference/warp-sketch-0.2.html`).

## Name check: "Warp"

Result (2026-10-27, web search; first done for the sketch): **several
typefaces named "Warp" exist, all display or novelty faces. None is a
text serif.** The family ships only as "machine-made Warp" and
"machine-made Warp Display". The name table never has a bare "Warp".

| Finding | Link | Risk |
| --- | --- | --- |
| Warp by Intellecta Design (Brazil), MyFonts, 2007, 3 styles, display. An exact name. | [myfonts.com/fonts/intellecta/warp](https://www.myfonts.com/fonts/intellecta/warp/), [myfonts.com/collections/warp-font-intellecta-design](https://www.myfonts.com/collections/warp-font-intellecta-design) | Medium for a bare "Warp". Low for "machine-made Warp": a different genre. |
| Tilt Warp by Andy Clymer, Google Fonts (OFL), a variable display face of the Tilt family. | [fonts.google.com/specimen/Tilt+Warp/about](https://fonts.google.com/specimen/Tilt+Warp/about), [github.com/googlefonts/Tilt-Fonts](https://github.com/googlefonts/Tilt-Fonts) | Low. Display; the name is "Tilt Warp". |
| Warp Three NF (Nick's Fonts), Warp Anark and Warp Letunical (Ingrimayne Type), West Warp (EVCCO), Funky Warp, Warp Thruster (free). All display or novelty. | [myfonts.com/fonts/nicksfonts/warp-three-nf](https://www.myfonts.com/fonts/nicksfonts/warp-three-nf), [myfonts.com/fonts/ingrimayne/warp-anark](https://myfonts.com/fonts/ingrimayne/warp-anark), [myfonts.com/fonts/evcco/west-warp](https://www.myfonts.com/fonts/evcco/west-warp/) | Low. |
| No "Warp" family on Adobe Fonts and no Fonts In Use typeface page turned up. | | None found. |
| Trademarks: USPTO WARP, reg. 6556914, class 42 (Warp, a terminal app for developers). Other WARP marks are in software classes. None found for fonts. | [trademark.justia.com/903/42/warp-90342560.html](https://trademark.justia.com/903/42/warp-90342560.html) | Low for a typeface. |

Limits of this check:

* A web search, not a trademark clearance. Before a wide release, do a
  register search (USPTO, EUIPO eSearch, Swissreg, WIPO Global Brand
  Database) for WARP in classes 9, 16 and 42.
* Some store search pages were not reachable from the build machine;
  site-restricted web searches stood in for them.
* Fontspector's network checks (`fontdata_namecheck`) do not run
  (`--skip-network`).

## Styles

Six static fonts. Pen sweeps are unions of nib hulls; their point
structure changes with the stem, the contrast and the optical size, so
masters are not point-compatible. 0.1 ships statics. The variable font
(wght and opsz) is planned for 0.3.

| Family | Style | File | opsz | Weight class |
| --- | --- | --- | --- | --- |
| machine-made Warp | Regular, Italic, Bold, Bold Italic | `MachineMadeWarp-*.ttf` | 10 | 400, 700 |
| machine-made Warp Display | Regular, Italic | `MachineMadeWarpDisplay-*.ttf` | 60 | 400 |

Every family name plus style name fits in 32 characters. The full name
of Display Regular is "machine-made Warp Display" ("Regular" elided;
with it the name is 33 characters).

### Text optical size: opsz 10

opsz is the engine's optical-size parameter in points. It sets the
contrast, the hairline floor, the x-height, the side bearings and the
skeleton width. 0.1 sets the text styles at opsz 10:

* it is the sturdiest value in the 10–12 range: hairlines 16.6 units
  (Regular), the x-height 430, side bearings 44;
* the sketch sets its text below 20 px at opsz 10, and its paragraph at
  opsz 9;
* the OCR test reads opsz 9, 10, 11 and 12 equally well within its noise
  (mean CER over 9 to 16 px: 0.022, 0.026, 0.037, 0.018 for Regular);
  the differences come from pixel rounding, not from the optical size.

Display uses opsz 60, the sketch's display setting.

### Parameters

The sketch 0.2 defaults: contrast 9, pen angle 0 (level nib, vertical
stress), bracket 0.2, ball 1, serif 1, stem 84, x-height 412 at display,
superellipse exponent 2.1, smootherstep pressure, teardrop terminals.

| Style | Stem A | Hairline B | Serif S | Serif length | Teardrop | Side bearing | Skeleton |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Regular, Italic (opsz 10) | 87.0 | 16.6 | 20.6 | 64.4 | 79.2 | 44.3 | x 1.032 |
| Bold, Bold Italic (opsz 10) | 138.7 (+59 %) | 21.5 (+30 %) | 27.0 (+31 %) | 66.7 | 126.4 | 44.3 | x 1.094 |
| Display, Display Italic (opsz 60) | 79.7 | 8.9 | 9.7 | 59.0 | 64.6 | 31.3 | x 1.003 |

Bold: engine `stem` 134 (Regular 84), `contrast` 11.3, serif thickness
x 0.82 (`serifw`, new), serif length 0.65 (the same length as the
Regular's), skeleton x 1.06 (`width`, new) so that the counters stay
open. Capitals are 8 % lighter and 4.5 % narrower than the lowercase,
as in the sketch.

## Metrics

1000 units per em. Values in font units.

| Metric | Text (opsz 10) | Display (opsz 60) |
| --- | --- | --- |
| x-height | 430 | 414 |
| Cap height | 670 | 670 |
| Ascender | 760 | 760 |
| Descender | -250 | -250 |
| Overshoot | 11 | 11 |
| Maths axis | 250 | 250 |
| Typo / hhea ascender, descender, line gap | 900, -300, 0 (line height 1200) | same |
| win ascent / descent | from the bounds of all six styles (941 / 441) | same |
| Underline position / thickness | -150 / 25 | same |
| Italic angle | -14.04° (slant 0.25) | same |

## Outlines

1. **Sweep** (`loom/engine.py`, a line-by-line port of the sketch
   engine): each stroke is a centre-line with a pressure per node. The
   nib is a superellipse (exponent 3.2), `a` long and `b` thick, level.
   The ink is the convex hull of each pair of consecutive nib
   positions, plus discs, teardrops and bracket fillets.
2. **Union** (`loom/outline.py`): skia-pathops joins the polygons
   (nonzero fill). Slivers under 40 square units are dropped.
3. **Fit**: each contour is cut at its corners. Each run is fitted with
   as few cubic curves as a 0.9-unit tolerance allows (Schneider's
   method). Straight runs become lines. Curves are split at their x and
   y extrema. No segment is shorter than 4 units. Outer contours wind
   counter-clockwise (PostScript order).
4. **Check** (`tools/fidelity.py`): every font glyph, read back from the
   compiled TTF, is compared with an independent fill of its sweep at
   16, 32, 64 and 128 pixels per em. Limit: 5 % of the ink. See
   `proofs/warp/fidelity.json`.

Median 76 points per glyph (Regular), at most 198.

## Glyph set (0.1)

429 glyphs, 308 code points (306 visible characters, space, no-break
space). 314 drawn glyphs, 114 composites.

| Set | Characters |
| --- | --- |
| ASCII | all printable ASCII |
| Latin-1 | the letters with accents (composites of base and mark), `ß Æ æ Ø ø Ð ð Þ þ`, and `Œ œ Ÿ ı ȷ` |
| Punctuation and symbols | `‘ ’ “ ” ‚ „ ‹ › « » … • · € ₹ © ® ° — – ¡ ¿ § ¶ ¢ £ ¥ ¦ ¬ ª º ¹ ² ³ ¼ ½ ¾ µ`, the spacing accents, the no-break space |
| Greek | 24 capitals, 24 lowercase and final sigma. Drawn: `Γ Δ Θ Λ Ξ Π Σ Φ Ψ Ω` and all lowercase. References to Latin: `Α Β Ε Ζ Η Ι Κ Μ Ν Ο Ρ Τ Υ Χ`; `ο` refers to `o`, `µ` to `μ` |
| Maths | `+ − × ÷ ± = ≠ < > ≤ ≥ ∑ ∏ ∫ √ ∞ ∂ ∇ ′ ″ · ∘ → ← ↔ ∈ ∉ ⊂ ⊆ ∪ ∩ ∀ ∃ ∅ ≈ ≡ ∝` |
| Marks | combining grave, acute, circumflex, tilde, macron, dot, dieresis, ring, caron, cedilla (U+0300–0327), capital forms (`.case`), dotted circle |
| Ligatures | `ﬀ ﬁ ﬂ ﬃ ﬄ` |
| Figures | lining tabular (default), lining proportional (`.lf`), old-style proportional (`.osf`), old-style tabular (`.tosf`), superiors and two denominators for ¹ ² ³ ¼ ½ ¾ |
| Small capitals | a–z, the accented lowercase, `æ œ ø ð þ` and the Greek lowercase (`.sc`) |

The OpenType MATH table is planned for 0.2.

## OpenType features

| Feature | What |
| --- | --- |
| `ccmp` | i and j lose the dot before a combining mark above |
| `liga` | ff, fi, fl, ffi, ffl |
| `onum`, `lnum`, `pnum`, `tnum` | figures; default lining tabular; `onum` gives the sketch's old-style figures, proportional |
| `smcp`, `c2sc` | small capitals (ß becomes two small-cap S) |
| `kern` | class kerning (see below) |
| `mark`, `mkmk` | marks on base letters and on marks, from anchors |

Kerning starts from the sketch's table (To Te Ta Tr Ty TA T. Av Aw AV
AT AY A' Va Ve Vo Ya Yo LT LV LY L' P. P, F. r. f' quotes and others)
and turns it into classes: accented letters and Greek look-alikes join
the Latin classes (ΤΑ, ΓΑ, Το, ΥΑ, Àv). The proportional figures have
a few pairs (7. 74). The default tabular figures are not kerned. Italic
uses 70 % of the values, as in the sketch.

## Rules

* All outlines come from `loom/sketch.py` and `loom/extended.py`
  through the pen. Do not trace, import or copy outlines from any other
  font. No outline or metric was taken from Computer Modern, Latin
  Modern, STIX or Century.
* Fonts: SIL OFL 1.1, Reserved Font Name "machine-made"
  (`warp/OFL.txt`). Generator code: Apache-2.0 (`LICENSE`).
