# Weft brief

Phase 0 of machine-made Weft. This file sets the metrics, the glyph list,
the axes and the build plan. Source of all shapes: the approved sketch 0.1
(`reference/weft-sketch-0.1.html`, glyph table `G`).

> Update for Weft 0.1 (phase 2): the build plan below is done up to
> phase 4. The width axis and the Thread style are not in 0.1. See
> `STATUS.md`, `CHANGELOG.md` and `RELEASE-NOTES-0.1.md`.
>
> Update for Weft 0.2: l, I, 1, 0 and q changed for code look-alikes,
> and the set grew to Latin Extended-A, combining marks, box drawing
> and arrows. See `STATUS.md` (deviations from the sketch) and
> `RELEASE-NOTES-0.2.md`.

## Name check: "Weft"

Result (2026-10-26): **no serious conflict found.** No published typeface
named exactly "Weft" was found, and no trademark "WEFT" for fonts was found.
One near match exists. The founder decides; this session did not rename.

| Finding | Link | Risk |
| --- | --- | --- |
| **Wefts** (plural), by Aasawari Kulkarni, Overlap Type. Slanted all-caps pixel display face, variable width axis, styles Regular / Weaving / Woven. Listed on Fonts In Use in April 2026. | [store.overlaptype.com/fonts/wefts](https://store.overlaptype.com/fonts/wefts), [fontsinuse.com/typefaces/248041/wefts](https://fontsinuse.com/typefaces/248041/wefts) | Medium. Different name form, genre and use, but the same weaving idea and a "breaks down along an axis" concept. Users can confuse the two in search. |
| Microsoft WEFT (Web Embedding Fonts Tool), the old EOT tool, end of life. | [Wikipedia: Embedded OpenType](https://en.wikipedia.org/wiki/Embedded_OpenType) | Low. A discontinued tool, not a typeface. It does make "Weft font" searches noisy. |
| MyFonts search for "weft": no families. | [myfonts.com/search?query=weft](https://www.myfonts.com/search?query=weft) | None. |
| Fonts In Use search for "weft": only "Wefts" (above). | [fontsinuse.com/search?terms=weft](https://fontsinuse.com/search?terms=weft) | None more. |
| Software and companies named Weft: a programming language (WeaveMindAI/weft), a Go template engine (cpcf/weft), a GPU verifier (lightsighter/Weft), Weft Technologies (Dubai, supply chain), weft.io, WEFT 90.1 FM radio, WEFT Magazine (weaving). | [github.com/WeaveMindAI/weft](https://github.com/WeaveMindAI/weft), [pkg.go.dev/github.com/cpcf/weft](https://pkg.go.dev/github.com/cpcf/weft), [g2.com/sellers/weft](https://www.g2.com/sellers/weft), [new.weft.org](https://new.weft.org/), [weftmagazine.com](https://www.weftmagazine.com/) | Low for a typeface. Not in the font market. |
| Trademark search (web): only uses of "weft" as a weaving term in class 7/9 goods (weft insertion systems for looms). No "WEFT" mark for fonts or typefaces found. | [USPTO TMOG 2014-08-05](https://www.uspto.gov/web/trademarks/tmog/20140805_OG.pdf) | Low. Not a search of the registers. |

Limits of this check:

* Google Fonts metadata and the fontdata.com name-check API were not
  reachable from the build machine. Fontspector's `fontdata_namecheck`
  check is skipped (network) for the same reason.
* This is a web search, not a trademark clearance. Before a public
  release, do a register search (USPTO TESS, EUIPO eSearch, Swissreg,
  WIPO Global Brand Database) for WEFT in classes 9, 16 and 42.
* The shipped family name is "machine-made Weft", not "Weft" alone. The
  OFL Reserved Font Name is "machine-made". This reduces the risk of
  confusion with "Wefts".

## Metrics

1000 units per em. **1 design unit = 62.5 font units.** The sketch's
16-unit em is 1000, the 12-unit advance is 750.

| Metric | Design units | Font units |
| --- | --- | --- |
| Em | 16 | 1000 |
| Advance (all glyphs) | 12 | 750 |
| Design box | 7 wide, at x 2.5 | 438 wide, at x 156 |
| Baseline | 0 | 0 |
| x-height | 8 | 500 |
| Cap height | 11 | 688 |
| Ascender | 11.5 | 719 |
| Descender | -3.5 | -219 |
| Typo / hhea ascender | 14.5 | 906 |
| Typo / hhea descender | -4.5 | -281 |
| Line gap | 0 | 0 |
| Line height (typo) | 19 | 1188 |
| win ascent / descent | from glyph bounds of all masters, one value for the family | 1167 / 339 |
| Underline position | -2.4 | -150 |

Stroke rules (from the sketch):

* Stroke width `w = 0.6 + (wght - 100) / 800 * 2.0` design units.
  wght 100 = 0.6 (38 u), wght 400 = 1.35 (84 u), wght 900 = 2.6 (163 u).
* Open strokes: square caps (each end extends by w/2).
* Joins: miter, limit 2.4. A sharper join is a bevel.
* Dots: squares of side w, centred on the point.
* Lines only. No curves.

The typo line height (19 units) is the sketch's 19-unit line step, and
leaves room above the cap height for most accents.

## Glyph list

Sketch 0.1 holds 88 characters. All 88 are in `loom/glyphs.py`.

| Set | Characters | Phase |
| --- | --- | --- |
| Lowercase | `a`-`z` | 1 |
| Uppercase | `A`-`Z` | 1 |
| Figures | `0`-`9` | 1 |
| Space | U+0020, U+00A0 (same glyph) | 1 |
| .notdef | open box | 1 |
| Punctuation | `. , : ; ! ? - – — _ / \ \| ( ) [ ] ' " + = * # < > %` | 3 |
| Rest of ASCII | `` @ $ & ^ ` { } ~ `` | 3 (new drawings) |
| Latin-1 | U+00A1-U+00FF | 3 (new drawings) |

Phase 1 builds 64 glyphs: .notdef, space, 26 + 26 + 10.

## Axes (plan)

| Axis | Tag | Range | Default | Notes |
| --- | --- | --- | --- | --- |
| Weight | `wght` | 100-900 | 400 | Stroke width formula above. |
| Fragmentation | `FRAG` | 0-100 | 0 | Custom axis. See stages below. |
| Width | `wdth` | 100-160 | 100 | Scales x of the centre lines by wdth/100 and the advance with it (12 units at 100, 19.2 at 160). Stroke width stays the same. |

Style: "Solid" is the default. "Thread" (horizontal slots through the
glyph) ships after the first release.

### FRAG stages (later phases; not built in phase 1)

| Range | Stage | What happens | Safe for |
| --- | --- | --- | --- |
| 0 | Clean | Plain strokes. | Body text |
| 1-15 | Notches | Ink-trap notches at square and acute corners (interior angle 20 to 112 degrees) and at T-junctions. Notch size grows to 0.36 w at 15. | Body text |
| 16-50 | Cuts | Gaps across strokes, narrower than the stroke. Gap width 0.14 w to 0.42 w; cuts keep clear of ends and vertices. | Headings |
| 51-100 | Drift | Pieces drift sideways (up to 1.15 w, on a 0.25 grid), shrink (to 55 %), and up to 36 % drop out. Notches fade out. | Titles and marks |

The sketch uses a seeded random generator for cuts and drift. A variable
font cannot be random per instance, so phase 4 must fix the seed per
glyph and make masters at FRAG 0, 15, 50 and 100 that interpolate. This
needs compatible outlines across masters (same contour and point count),
which the current overlap-removal path does not give. See open risks in
`STATUS.md`.

## Build plan

| Phase | Scope | Gate |
| --- | --- | --- |
| 0 | This brief. Name check. | Founder reads the brief. |
| 1 | One master: wght 400, FRAG 0, Solid. a-z, A-Z, 0-9, space, .notdef. Generator, tests, fontmake, Fontspector, proof, CI. | **Founder reviews the proof by eye.** |
| 2 | wght axis: masters at 100 and 900 with compatible outlines; variable TTF; `interpolatable` checks. | Interpolation clean, proof at 100/400/900. |
| 3 | Full sketch set (punctuation), rest of ASCII, Latin-1, kerning-free spacing check, fontbakery universal clean. | Glyph coverage. |
| 4 | FRAG axis: notches (1-15), cuts (16-50), drift (51-100). | Body text at FRAG 15 reads the same as FRAG 0. |
| 5 | wdth axis, Thread style, release. | Founder approval. |

## Rules

* All outlines come from the stroke table. Do not trace, import or copy
  outlines from any other font.
* Fonts: SIL OFL 1.1, Reserved Font Name "machine-made" (`weft/OFL.txt`).
  Generator code: Apache-2.0 (`LICENSE`).
