# Heddle status

| Field | Value |
| --- | --- |
| Family | machine-made Heddle |
| Version | 0.2 (font version 0.200) |
| Branch | `heddle/v0.2` |
| Stage | Heddle 0.2 built: variable font (wght, wdth), 11 hinted statics, WOFF2 |
| Gate now | Jac reviews the PR; founder reviews the proofs by eye |
| Next | Release 0.2 (tag `heddle-v0.2.0`). Then the open items below |
| Last local run | 2026-10-28: tests, build, byte check, interpolation, Fontspector, drift, OCR check, site build all green |
| Last green CI | 0.1: PR #4. 0.2: on the PR |

## Proven (local run, 2026-10-28)

- 533 pytest tests pass.
- The build is byte-reproducible, hinting included: two builds give the
  same files.
- `fonttools varLib.interpolatable`: no problems on the designspace, on
  the 16 master UFOs and on the variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the variable
  font (4 WARN) and the 11 static TTF (47 WARN). Accepted WARNs below.
- Advances match the sketch engine exactly at all 16 masters (test runs
  the engine in node).
- Every static glyph equals the nonzero fill of its primitives, and no
  static glyph keeps an overlap. No glyph needs a fallback (see
  "Boolean step").
- Drift (`proofs/heddle/drift.json`): largest shape drift 8.7 % (0.1:
  11.1 %), largest advance drift 30.6 units (0.1: 38.8).
- OCR check (`proofs/heddle/readability.json`, Tesseract 5.3.4, 24, 32
  and 48 px): CER Regular 0.17 % (0.1: 0 %), Bold 0.17 % (0.1: 0.34 %),
  Black 0 % (0.1: 0 %). DejaVu Sans: 0.17 %, 0 %, 0 %. Gate (at most
  1 point above 0.1) passes. Heddle is a display face; this check stops
  regressions only.
- Sketch comparison (`proofs/heddle/sketch-compare.json`): soft IoU
  0.96 to 0.97 at Regular and Black; between masters at wght 250, wdth
  85: 0.86 (0.1: 0.73).

## Done in 0.2

- Drift at Black near wdth 85: masters at wdth 85 (16 masters). J at
  wght 900, wdth 85 now has no drift (it is a master); the worst glyph
  is now the hyphen at wght 550, wdth 85 (8.7 %: the width floor bends
  between wght 400 and 700).
- Accents: lighter, smaller marks; ".narrow" marks on ı I l ȷ, so ï Ï
  Ĩ ĺ do not widen their base. Capital marks stay below 950; win ascent
  is 950 (0.1: 1051).
- Minimum counter rule: small rings and the hooks of a f j s t stay open
  at Black. ß ð @ © ® % redrawn with it (© ® with lighter inner letters;
  ð with its ascender starting inside the bowl; § new).
- Latin Extended-A (U+0100 to U+017F), Ș ș Ț ț, `¢ £ ¥ § ¶ ± × ÷ −`,
  `½ ¼ ¾`, fraction slash, spacing marks, and `frac`, `numr`, `dnom`.
  Tests check text in Polish, Czech, Slovak, Hungarian, Romanian,
  Turkish, Croatian, Slovenian, Latvian, Lithuanian, Estonian, Maltese
  and Esperanto.
- Kerning: lowercase pairs (v w y, r, f, k x, t, o b p against round
  letters, a, period) and figures against punctuation. The no-touch
  test now checks every member of every class, in every master.
- Boolean step without fallbacks (below).
- Hinting: ttfautohint on the statics.
- Name: register search for HEDDLE (see `BRIEF.md`). No mark for fonts
  or software found; not renamed.

## Boolean step

0.1 needed two fallbacks: a jitter for the S spine, and the rounded but
not re-simplified path for 15 static glyphs. The second came from a bug
in the check, not in pathops: re-simplifying after rounding returns
quadratic curves, and the check could not read them. 0.2 does: union
(pathops), snap to integers and drop degenerate segments, split
self-touching contours into loops (pathops returned Œ at wght 800 with
its counter joined to the outer contour by a slit, wound the wrong way
for nonzero), wind each loop by its nesting depth, then check the
result against the nonzero fill and check that no overlap is left. No
static glyph needs a fallback; the build stops if one ever fails.

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `contour_count` | VF | The variable font keeps one contour per primitive (on purpose). The statics pass. |
| `mandatory_avar_table` | VF | Both axes are linear on purpose. |
| `suspicious_sidebearings` | VF | The space (its width floor `2.3 S` bends between masters) and ſ (its hook ring widens at heavy weights, minimum counter rule). Both on purpose. |
| `alt_caron` | statics | Fontspector cannot check ď ľ ť Ľ in decomposed statics. They use a vertical caron (`caroncomb.alt`); see `proofs/heddle/heddle-latin-ext.png`. |
| `name/family_and_style_max_length` | 3 statics | PostScript names longer than 27 characters (`MachineMadeHeddle-CompressedBold`, `-ExtendedBold`, `-ExtraLight`). Only old PostScript printers care. |

## Interpolation drift

The variable font interpolates 16 masters. `tools/drift.py` measures
every glyph at 25 locations between the masters (the 21 of 0.1 and 4
new ones between wdth 70, 85 and 100):

- Median shape drift: 0.
- Largest: the hyphen at wght 550, wdth 85 (8.7 %, 30.6 units of
  advance). Next: J at wght 900, wdth 78 (6.8 %), ţ ț t at wght 550,
  wdth 85 (about 6 %).
- Cause: the width floor `W >= 2.3 S` of the sketch bends inside the
  cells, now also along the weight axis between 400 and 700.

## Deviations from the sketch

| What | Sketch | 0.2 | Why |
| --- | --- | --- | --- |
| Cuts | rectangles erased with `destination-out` | side cuts on one ring | No erasing of other primitives (the sketch bug that made stems vanish); fixed point count. |
| Curves | 96-point polygon | one cubic per quarter | Compatible masters, clean outlines (within about 2 units of the curve). |
| Hairline stroke | 1 px stroke to close seams | none | Overlaps fill correctly in the font. |
| Tabular figure width | wdth / 100 clamped to 0.8 to 1.25 | the sketch value at each master width, linear between | The variable font interpolates between masters. |
| K arm | starts at x = S/2 | starts at x = max(S/2, t/2) | At heavy weights the sketch arm poked out left of the stem. |
| Closed counters | no inner contour when too small | minimum counter rule: inner radius at least 0.25 S, at most 38 units; the ring gets thinner | 0.2: small rings and hooks stay open at Black (a f j s t, B's upper bowl, %, ©, ®). At Black the strokes there are up to 55 % lighter than the stem. |
| Hooks of f, t, j | ring as wide as the sketch drew it | wider at heavy weights; j reaches left of its box | 0.2: so the hook counter stays open; no change at Regular. |
| Cut levels near a counter's top or bottom | cut can end in the solid band | level kept within 97 % of the inner radius | A cut always ends in a clean terminal (e at Black). |
| `&` | dropped | redrawn | The brief asked for a proper `&`. |
| Width between masters | `max(base wf, 2.3 S)` | interpolated from 16 masters | See "Interpolation drift". |

## Open issues for 0.3

- Drift from the width floor along the weight axis (hyphen, t, ţ at
  wght 550, wdth 85). A master at wght 550 or a smooth floor would cut
  it.
- Marks are not encoded and there is no `mark`/`mkmk` feature: text
  with combining marks (e + U+0301) does not compose. Precomposed
  letters work.
- No proportional figures, so figures do not kern with each other
  (Fontspector `tabular_kerning`).
- The ogonek and the vertical caron are first drawings; check them in
  Polish and Czech headlines.
- § is new (an s with a ring as its spine); ¶ uses a half disc. Review
  both by eye.
- Hinting is ttfautohint defaults; no hand-tuned control file.
