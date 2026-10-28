# Heddle changelog

## 0.200 (Heddle 0.2)

### Added

- Latin Extended-A (U+0100 to U+017F) and Ș ș Ț ț. Accented letters
  are components; Đ đ Ħ ħ Ŧ ŧ Ł ł ĸ Ŋ ŋ ſ and the dotless j are drawn.
  New marks: macron, breve, dot above, caron, double acute, ogonek,
  comma below, turned comma above, vertical caron.
- `¢ £ ¥ § ¶ ± × ÷ −`, the fraction slash, `½ ¼ ¾`, numerators and
  denominators, and the spacing marks `¨ ¯ ´ ¸ ˆ ˇ ˘ ˙ ˚ ˛ ˜ ˝`.
  398 glyphs, 338 code points.
- Features `frac`, `numr` and `dnom`.
- Kerning for lowercase pairs and for figures against punctuation.
- Masters at wdth 85: 16 masters.
- Hinting: the static TTF are hinted with ttfautohint 1.8.4
  (ttfautohint-py 0.6.1, pinned).
- `tools/readability.py`: an OCR check against 0.1 and DejaVu Sans.
- Proofs: `heddle-latin-ext.png`, `heddle-symbols.png` and before/after
  sheets for the marks, the counters and the drift.

### Changed

- Marks are lighter and smaller. Narrow bases (ı I l ȷ) get narrow
  marks, so ï Ï Ĩ ĺ keep the advance of their base. Capital marks stay
  below the typo ascender; win ascent is now 950 (was 1051).
- Minimum counter rule: rings keep an open counter at Black (inner
  radius at least 0.25 S, at most 38 units). The hooks of f, t, j (and
  ſ ŋ Ŋ £) get wider at heavy weights so their counters stay open.
- ß, ð, @, ©, ®, % redrawn with the counter rule (© ® with lighter
  inner letters; ð's ascender starts inside the bowl).
- Tabular figures at wdth 85 are 0.85 of their width (the sketch
  value); 0.1 gave 0.9.
- Overlap removal for the statics: union, snap to integers, split
  self-touching contours, wind by nesting depth, check. The fallbacks
  of 0.1 (jitter, unsimplified rounded paths) are gone.
- The kerning test checks every member of every class.

## 0.100 (Heddle 0.1)

Sketched and first built as "Shuttle"; renamed to Heddle before the
release because of a name clash (see `BRIEF.md`).

### Added

- The loom (`loom/`): a Python port of the approved sketch engine
  (`reference/heddle-sketch-0.1.js`). Four primitives: rect,
  superellipse ring (exponent 2.6), parallelogram, V.
- Cut rings built from arcs: each piece is an outer and an inner
  superellipse arc between the cut levels, one cubic per quarter. Cuts
  are side cuts (`l r t b`) on one ring.
- 12 masters: wght 100, 400, 700, 900 x wdth 70, 100, 140. Every glyph
  has the same contours and points in all masters. The variable font
  keeps the overlaps and sets the `OVERLAP_SIMPLE` and
  `OVERLAP_COMPOUND` flags.
- Variable font `MachineMadeHeddle[wdth,wght].ttf`: `wght` 100 to 900
  (default 400), `wdth` 70 to 140 (default 100). STAT names 9 weights
  and 5 widths (Compressed, Condensed, Normal, Wide, Extended). 13
  named instances.
- 11 static TTF: 9 weights at width 100, Compressed Bold, Extended Bold.
  Made from the masters by the same interpolation, overlaps removed and
  checked against a nonzero fill.
- WOFF2 for the variable font, Regular and Bold.
- Character set: the 70 sketch characters, the rest of printable ASCII,
  the Latin-1 letters (accents as components), `ß Æ æ Ø ø Ð ð Þ þ Œ œ Ÿ
  ı`, curly quotes, guillemets, `… • · ¡ ¿ € ₹ © ® ° —` and the no-break
  space. 184 code points, 197 glyphs.
- A new `&` (the sketch had dropped it).
- Class kerning for display use (A V W Y T L P F against round letters,
  round capitals and punctuation).
- `tools/finish.py`, `tools/proof.py`, `tools/sketch_compare.py`,
  `tools/drift.py`, `scripts/build.sh`, `scripts/check.sh`.
- Tests (`tests/test_heddle.py`): metrics, glyph set, compatibility,
  contour direction, the port against the sketch engine, kerning
  sanity, drift, statics, names, determinism.
- `heddle/OFL.txt`.
