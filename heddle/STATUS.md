# Heddle status

| Field | Value |
| --- | --- |
| Family | machine-made Heddle |
| Version | 0.1 (font version 0.100) |
| Pull request | machine-made/type#4 |
| Stage | Heddle 0.1 built: variable font (wght, wdth), 11 statics, WOFF2 |
| Gate now | Jac reviews PR #4; founder reviews the proofs by eye |
| Next | Release 0.1 (tag `heddle-v0.1.0`). Then 0.2 (see below) |
| Last local run | 2026-10-27: tests, build, byte check, interpolation, Fontspector, site build all green |
| Last green CI | none yet (first run is on the PR) |

## Proven (local run, 2026-10-27)

- 334 pytest tests pass.
- The build is byte-reproducible: two builds give the same files.
- `fonttools varLib.interpolatable`: no problems on the designspace,
  on the 12 master UFOs and on the variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the
  variable font and the 11 static TTF.
- The 70 sketch characters match the sketch engine at the five corner
  and default locations (`proofs/heddle/heddle-sketch-vs-font-*.png`,
  soft IoU 0.96 to 0.97 at Regular and heavier; see "Sketch comparison").
- Advances match the sketch engine exactly at all 12 masters (test runs
  the engine in node).
- Every static glyph equals the nonzero fill of its primitives (the
  build checks each union and stops if one differs).

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `contour_count` | VF | The variable font keeps one contour per primitive (on purpose). The statics pass. |
| `mandatory_avar_table` | VF | Both axes are linear on purpose. |
| `name/family_and_style_max_length` | 3 statics | PostScript names longer than 27 characters (`MachineMadeHeddle-CompressedBold`, `-ExtendedBold`, `-ExtraLight`). Only old PostScript printers care. |

## Interpolation drift

The variable font interpolates 12 masters. The engine's rules are not
all linear, so between masters the font can differ a little from what
the engine would draw. `tools/drift.py` measures it for every glyph at
21 locations between the masters (`proofs/heddle/drift.json`):

- Median shape drift: 0. Most glyphs are the same.
- Largest: J at wght 900, wdth 85: 11 % of the ink area moves. Next: the
  hyphen (9 % at wght 550), õ, z, the en dash, s, ä (5 to 7 %), all at
  wdth 85, most at wght 800 to 900.
- Cause: the width floor `W >= 2.3 S` of the sketch. At Black it bends
  between wdth 70 and 100. The font is up to 35 units wider there than
  the engine. A wdth 85 master would cut this but add 4 masters.
- The space: up to 26 units wider between masters (same floor).
- Glyphs new in 0.1 use linear widths and do not drift in width.

## Sketch comparison

`tools/sketch_compare.py` renders the sketch engine and the font in
Chromium and writes `proofs/heddle/sketch-compare.json`. Soft IoU (1.0
= same pixels): 0.96 to 0.97 at wght 400 and 900, 0.75 to 0.81 at
wght 100. Thin strokes are under 2 px at the proof size, so canvas and
font anti-aliasing differ a lot in relative terms; the overlay shows no
shape difference. Between masters, the pangram score drops (0.52 at
650, 120) because the spaces drift and the lines move apart.

## Deviations from the sketch

| What | Sketch | 0.1 | Why |
| --- | --- | --- | --- |
| Cuts | rectangles erased with `destination-out` | side cuts on one ring | No erasing of other primitives (the sketch bug that made stems vanish); fixed point count. |
| Curves | 96-point polygon | one cubic per quarter | Compatible masters, clean outlines (within about 2 units of the curve). |
| Hairline stroke | 1 px stroke to close seams | none | Overlaps fill correctly in the font. |
| Tabular figure width | wdth / 100 clamped to 0.8 to 1.25 | 0.8 at 70, 1 at 100, 1.25 at 140, linear between | The variable font interpolates between masters; this is what it gives. |
| K arm | starts at x = S/2 | starts at x = max(S/2, t/2) | At heavy weights the sketch arm poked out left of the stem. |
| Closed counters | no inner contour when too small | inner contour shrinks to a point | Same look, same point structure in every master. |
| Cut levels near a counter's top or bottom | cut can end in the solid band | level kept within 97 % of the inner radius | A cut always ends in a clean terminal (e at Black). |
| `&` | dropped | redrawn | The brief asked for a proper `&`. |
| Width between masters | `max(base wf, 2.3 S)` | interpolated from 12 masters | See "Interpolation drift". |

## Open issues for 0.2

- Name: register search for HEDDLE before a public release (see
  `BRIEF.md`).
- Width drift at Black near wdth 85: add masters at wdth 85, or make the
  floor smooth.
- Accents at Black are wide and heavy; on narrow bases (ï, Ï) they
  widen the glyph. Capital accents go above the typo ascender (950);
  win metrics cover them.
- `ß`, `ð`, `@`, `©`, `®` and `%` are first drawings. At Black the small
  rings of `%`, `©`, `®` and the hooks of a, f, j, s, t close (as in the
  sketch).
- No Latin Extended-A beyond Œ œ Ÿ ı; no `¢ £ ¥ § ¶ ± × ÷` and
  fractions.
- Kerning is a small class table (A V W Y T L P F against round letters
  and punctuation). No kerning for lowercase pairs or figures.
- pathops fails on some unions (S spine) and on re-simplifying 15
  rounded static glyphs. The build detects both and falls back (jitter,
  or the rounded union). A better boolean step would remove the
  fallbacks.
- No hinting.
