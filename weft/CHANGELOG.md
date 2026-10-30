# Weft changelog

Notes for the integration session. The root `CHANGELOG.md` is not
changed by the Weft sessions.

## 0.200 (Weft 0.2)

### Changed

- Look-alikes for code. l: the stem moves to x 3 and the tail is
  longer. I: serifs 6 units wide (were 4). 1: a longer flag and a wider
  base. 0: a longer slash. q: a spur at the foot. The OCR look-alike
  CER is now 0.071 / 0.079 / 0.078 at FRAG 0 / 8 / 15, against 0.0875
  for DejaVu Sans Mono (Weft 0.1: 0.121 / 0.128 / 0.122, same test).
- Accents above the base grow with weight (scale 1.25 at Black) and
  sit further from the base at heavy weights (gap 0.95 units at Black,
  was 0.5 / 0.6). Ring counters stay open at Black.
- « » are two ‹ › components, and " “ ” „ two single quotes. They
  move apart at heavy weights (Weft 0.1 was too tight at Black; the
  double quotes merged).
- Component offsets can depend on the stroke width (piecewise linear
  between the master widths, so the variable font and the statics
  agree).
- OS/2 Unicode ranges and code pages come from the character set
  (code pages: Latin 1, Latin 2, Turkish, Baltic).
- win ascent / descent 1250 / 403 (were 1167 / 339): the new accents at
  Black with FRAG 100 drift, and the comma below at Black. Typo and
  hhea metrics do not change.

### Added

- Latin Extended-A (U+0100 to U+017F, all 128), Ș ș Ț ț, ẞ, Ǿ ǿ, and
  Ǎ ǎ Ǔ ǔ Ẽ ẽ. New marks: caron, vertical caron (ď ľ ť Ľ), breve, dot
  above, double acute, ogonek, comma below, turned comma above, capital
  macron.
- 14 combining marks (U+0300 to U+0328) with no advance, a mark feature
  (anchors on A-Z, a-z, ı, ȷ) and GDEF classes. ccmp: i and j lose
  their dot under a mark above.
- ‹ › ‚ „ − and the spacing accents ˆ ˇ ˘ ˙ ˚ ˛ ˜ ˝.
- Box drawing ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼: lines end on the cell edges (new
  "butt" stroke kind without caps), so they join across cells and
  lines at the typo line height. Arrows ← → ↑ ↓.
- ss01: dotted zero.
- The static TTFs are hinted with ttfautohint (ttfautohint-py 0.6.1,
  pinned; `tools/finish.py --hint`). The build stays byte-identical.
- OCR gate: FRAG 8 is gated too, q is in the look-alike set, and the
  look-alike margin is 0 (was 0.06): Weft must not read worse than
  DejaVu Sans Mono.
- Tests: language coverage (Central European, Baltic, Turkish,
  Romanian, Maltese, Esperanto), marks do not touch their base,
  cedilla and ogonek attach, box drawing ends on the cell edges,
  look-alike pairs differ, offsets are piecewise linear, combining
  marks. 1749 tests.
- Proofs: accents, code (box drawing, arrows, symbols), designspace
  grid, sketch comparison, before/after for look-alikes and wght 900.

## 0.100 (Weft 0.1, phase 2)

### Added

- Variable font `MachineMadeWeft[FRAG,wght].ttf` with two axes: `wght`
  100 to 900 (default 400) and `FRAG` 0 to 100 (default 0).
- 12 masters: wght 100, 400, 900 x FRAG 0, 15, 50, 100.
- Stroke-piece outlines (`loom/pieces.py`). Every glyph has the same
  contours and points in all masters. The variable font keeps the
  overlaps and sets the `OVERLAP_SIMPLE` and `OVERLAP_COMPOUND` flags.
- FRAG as a fixed, seeded design: ink-trap notches (1 to 15), cuts
  across strokes (16 to 50), drift, shrink and drop (51 to 100).
- `loom/drift_lock.json` and `tools/relock.py`: the drift seed per
  glyph that makes `fontTools varLib.interpolatable` clean.
- Nine static instances at FRAG 0 (Thin 100 to Black 900), TTF and OTF,
  overlaps removed.
- WOFF2 for the variable font, Regular and Bold.
- STAT table: wght names (Regular elidable, linked to Bold) and FRAG
  names (Clean 0 elidable, Notched 15, Cut 50, Broken 100). Statics have
  one value per axis.
- Character set: printable ASCII, Latin-1 Supplement (except the soft
  hyphen), Euro sign, curly quotes, ellipsis, bullet, dotless i, Indian
  rupee sign. 201 encoded characters, 215 glyphs in the variable font.
- Accented letters as components with anchors. The accent position
  follows the stroke width, so accents clear the base at every weight.
- `tools/readability.py`: Tesseract OCR gate against DejaVu Sans Mono.
- `tools/proof.py`: character set, weight waterfall, FRAG waterfall,
  body text, look-alike proofs in `proofs/weft/`.
- `weft/OFL.txt`: a copy of the font licence.

### Changed

- Move all Weft files into `weft/`. Fonts go to `fonts/weft/`, proofs
  to `proofs/weft/`.
- Rename the files to the `MachineMadeWeft` prefix.
- Typo and hhea ascender: 14.5 units (906), was 14 (875).
- One underline thickness (84) and one pair of win metrics for the
  whole family.
- The build is reproducible (`SOURCE_DATE_EPOCH`).
- The phase 1 sketch comparison moves to `tools/sketch_compare.py`.

### Removed

- The phase 1 proof PNGs.

## 0.100 (Weft phase 1, unreleased)

- Add the Weft brief, the sketch 0.1 stroke table, the outline
  generator, the UFO build, static TTF and OTF, Fontspector checks, the
  proof sheet and the CI workflow.
