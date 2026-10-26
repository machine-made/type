# Weft changelog

Notes for the integration session. The root `CHANGELOG.md` is not
changed by the Weft sessions.

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
