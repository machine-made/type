# Heddle changelog

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
