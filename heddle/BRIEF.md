# Heddle brief

machine-made Heddle is a Swiss display grotesk for posters, headlines,
wordmarks and big figures. This file sets the metrics, the glyph set,
the axes, the build plan and the name check. Source of all shapes: the
approved sketch 0.1 (`reference/heddle-sketch-0.1.js`, glyph table `G`;
specimen page `reference/heddle-sketch-0.1.html`; screenshot
`reference/sketch-0.1-reference.png`).

## Name: renamed from "Shuttle"

The family was sketched and first built as "Shuttle". The name check
found a commercial typeface named exactly "Shuttle" (Heinrich Lischka,
Volcano Type, on MyFonts since 2006, a 3D display face) and a close
match, "Shuttleblock" (Fort Foundry, 2024, on Adobe Fonts, a geometric
sans in four widths). On 2026-10-27 the founder renamed the family to
Heddle: the heddle is the part of a loom that lifts the warp threads,
next to Weft and the loom.

The files in `reference/` are the approved sketch, kept as they were
approved. Their file names are new; their content still says
"Shuttle".

## Name check: "Heddle"

Result (2026-10-27): **no typeface named "Heddle" found.** The near
names in font stores are different words. Software and companies named
Heddle exist, none in the font market.

| Finding | Link | Risk |
| --- | --- | --- |
| MyFonts, Adobe Fonts, Fonts In Use, dafont and Fontspring (site searches for "heddle"): no family named Heddle. The nearest names are Hedley New (Moretype), Headley, Hedge and Hedhead. | [myfonts.com/collections/hedley-new-font-moretype](https://www.myfonts.com/collections/hedley-new-font-moretype/), [fonts.adobe.com/fonts/hedley-new](https://fonts.adobe.com/fonts/hedley-new), [fontsinuse.com/typefaces/232037/hedge](https://fontsinuse.com/typefaces/232037/hedge), [dafont.com/hedhead.font](https://www.dafont.com/hedhead.font) | Low. Different names. Hedley is the closest in sound. |
| Google Fonts: no family named Heddle found by web search. The search page itself was not reachable from the build machine. | [fonts.google.com](https://fonts.google.com/) | Low. |
| General web search for "Heddle" typeface or font: weaving (rigid heddle looms), people named Heddle, Heddle Shipyards (Canada). No typeface. | | None for typefaces. |
| Software named heddle: an AI-native version control CLI (MacPorts port `heddle`), and `heddle-mcp` on PyPI. | [ports.macports.org/port/heddle](https://ports.macports.org/port/heddle/), [socket.dev/pypi/package/heddle-mcp](https://socket.dev/pypi/package/heddle-mcp) | Low for a typeface. Not in the font market. |
| Trademarks (web): Steel Heddle Manufacturing Company holds marks for loom parts (textile machinery). No "HEDDLE" mark for fonts or typefaces found. | [trademark.justia.com/owners/steel-heddle-manufacturing-company-239051](https://trademark.justia.com/owners/steel-heddle-manufacturing-company-239051), [gleanmark.com/search?q=HEDDLE](https://gleanmark.com/search?q=HEDDLE) | Low. Weaving equipment, not type. The pages did not load in full; not a register search. |

Limits of this check:

* A web search, not a trademark clearance. Before a public release, do
  a register search (USPTO, EUIPO eSearch, Swissreg, WIPO Global Brand
  Database) for HEDDLE in classes 9, 16 and 42.
* Some pages were not reachable from the build machine (the Fonts In
  Use and MyFonts search pages, the Google Fonts search, the Justia
  owner page); site-restricted web searches stood in for them.
* The shipped family name is "machine-made Heddle", not "Heddle"
  alone, and the OFL Reserved Font Name is "machine-made".
* Fontspector's network checks (`fontdata_namecheck`) do not run
  (`--skip-network`).

## Metrics

1000 units per em. All values in font units.

| Metric | Value |
| --- | --- |
| Baseline | 0 |
| x-height | 520 |
| Cap height | 700 |
| Ascender | 730 |
| Descender | -210 |
| Overshoot (rounds) | 10 |
| Typo / hhea ascender | 950 |
| Typo / hhea descender | -250 |
| Line gap | 0 (line height 1200) |
| win ascent / descent | from the bounds of all masters (1051 / 295) |
| Underline position / thickness | -120 / 71 |

Stroke rules (from the sketch engine):

* Stem `S = 28 + (wght - 100) / 800 * 150`: 28 at wght 100, 84.25 at 400,
  178 at 900.
* Horizontal thickness `H = 0.84 S`.
* Diagonals: horizontal width `dt(dx, dy) = 0.9 S * hypot(dx, dy) / |dy|`.
* Sidebearing on each side `22 + 0.22 S`. Spacing is tight.

Width rules:

* Sketch glyphs: `W = base * wdth / 100`, at least `2.3 S`. Counters
  scale, stems do not.
* Stem-width glyphs follow the stem: `i j l I . , : ! '` from the sketch,
  and the new `; | " ‘ ’ ‚ “ ” „ … · • ° ‹ › « » ¡ ı` and the spacing
  grave.
* Tabular figures (the default figures): base 560, width factor 0.8 at
  wdth 70, 1 at 100, 1.25 at 140, linear in between.
* Glyphs new in 0.1: `W = A * wdth / 100 + B * S`, with A and B chosen
  so that the sketch rule holds at Regular width 100 and at Black
  width 70. This is linear on both axes, so the variable font gives it
  exactly everywhere.

## Primitives and cuts

Four primitives only: rect, superellipse ring (exponent 2.6, outer and
inner contour), parallelogram, V. Two new glyph helpers are the same
primitives: a chevron is a V turned on its side (one contour), and the
asterisk uses three parallelograms with square ends.

A cut opens one ring. The sketch wrote cuts as rectangles and erased
them on the canvas. The loom writes each cut as a side and two levels:

| Cut | Removes |
| --- | --- |
| `("r", lo, hi)` | the right half of the ring between y = lo and y = hi |
| `("l", lo, hi)` | the left half between y = lo and y = hi |
| `("t", lo, hi)` | the top half between x = lo and x = hi |
| `("b", lo, hi)` | the bottom half between x = lo and x = hi |

`INF` means "past the ring". Side cuts give the horizontal Swiss
terminals. A cut never touches another primitive. Where a sketch
rectangle ended inside a stroke that another primitive covers (a, 3, 5),
the side cut removes that hidden part too; the visible shape is the
same.

A cut ring is one or more closed pieces: an outer superellipse arc and
an inner arc between the cut levels. Each arc is one cubic per quarter,
fitted to the curve (within about 2 units), and breaks at the axis
points it contains. A cut level stays inside 97 % of the inner radius,
so a cut always ends in a horizontal (or vertical) terminal. When a
counter closes (heavy weights, small hooks), the inner contour shrinks
to a point at the centre, as the sketch drew no counter there.

## Glyph set (0.1)

197 glyphs, 184 code points (182 visible characters, space, no-break
space):

| Set | Characters |
| --- | --- |
| Sketch set (70 and the space) | `a-z A-Z 0-9 . , : ! ' - – /` |
| Rest of ASCII | ``" # $ % & ( ) * + ; < = > ? @ [ \ ] ^ _ ` { | } ~`` |
| Latin-1 letters | `À-ÿ` letters with acute, grave, circumflex, dieresis, tilde, ring, cedilla (components), `ß Æ æ Ø ø Ð ð Þ þ`, and `Œ œ Ÿ ı` |
| Punctuation and symbols | `‘ ’ “ ” ‚ „ ‹ › « » … • · ¡ ¿ € ₹ © ® ° —`, no-break space |
| Marks (unencoded) | acute, grave, circumflex, dieresis, tilde, ring (lowercase and capital forms), cedilla |
| `.notdef` | an open box |

The sketch dropped `&` because it drew badly. 0.1 draws a new `&`: a
lower bowl open at the upper right, a small closed loop, and a leg to
the right foot.

## Axes

| Axis | Tag | Range | Default | Named values (STAT) |
| --- | --- | --- | --- | --- |
| Weight | `wght` | 100 to 900 | 400 | Thin 100, ExtraLight 200, Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900 |
| Width | `wdth` | 70 to 140 | 100 | Compressed 70, Condensed 85, Normal 100, Wide 120, Extended 140 |

usWidthClass follows the nearest OpenType width (75, 87.5, 100, 125,
150 %): 3, 4, 5, 7, 8. Named instances in `fvar`: the 9 weights at
Normal and the 4 other widths at Regular. A width and a weight together
("Compressed Bold") make a name longer than 32 characters with
"machine-made Heddle" (a Fontspector FAIL). STAT names every width and
weight.

## Build plan

| Step | Scope | Gate |
| --- | --- | --- |
| 1 | Port the engine to `loom/` (Python). Analytic cut rings, fixed topology. | Same advances as the sketch engine at every master (test with node). |
| 2 | 12 masters: wght 100, 400, 700, 900 x wdth 70, 100, 140. Variable TTF with overlaps (overlap flags set). | `varLib.interpolatable` clean; drift report. |
| 3 | Statics from the masters (same interpolation), overlaps removed with skia-pathops, every union checked against a nonzero fill. | Fontspector universal: no FAIL. |
| 4 | Rest of ASCII, Latin-1 letters, marks, symbols, kerning. | Glyph and kerning tests. |
| 5 | Proofs, CI, release job, site page. | **Founder reviews the proofs by eye.** |

Masters: wght 400 and 700 sit between the corners because the width
floor (`W >= 2.3 S`) bends inside the cells. With 700, Bold is exact.
See `STATUS.md` for the remaining drift.

## Rules

* All outlines come from `loom/glyphs.py`. Do not trace, import or copy
  outlines from any other font.
* Fonts: SIL OFL 1.1, Reserved Font Name "machine-made"
  (`heddle/OFL.txt`). Generator code: Apache-2.0 (`LICENSE`).
