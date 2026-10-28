# Warp changelog

## 0.100 (Warp 0.1)

### Added

- The loom (`loom/`): a Python port of the approved sketch engine
  (`reference/warp-sketch-0.2.js`): parameters, superellipse nib,
  centre-line paths with pressure, serifs, beaks, teardrops, the rule
  pen for maths, and every glyph of the sketch (`loom/sketch.py`).
- New glyphs drawn with the same pen (`loom/extended.py`): the rest of
  printable ASCII, the Latin-1 letters and symbols, the marks for
  accents, ffi and ffl, the rest of basic Greek (ζ η ι κ ν ξ τ υ χ ς,
  Θ Λ Ξ Π Φ Ψ), 23 maths symbols, ₹ and the dotted circle.
- Outlines: the sweep polygons are joined with skia-pathops and fitted
  with cubic curves (`loom/outline.py`).
- Six static fonts: machine-made Warp Regular, Italic, Bold, Bold
  Italic (opsz 10) and machine-made Warp Display Regular, Italic
  (opsz 60). TTF, OTF and WOFF2.
- 429 glyphs, 308 code points: ASCII, Latin-1, Œ œ Ÿ ı ȷ, basic Greek,
  maths, marks, ligatures, four figure styles, small capitals.
- OpenType: ccmp, liga, onum, lnum, pnum, tnum, smcp, c2sc, kern, mark,
  mkmk. Class kerning from the sketch's table.
- `tools/fidelity.py` (outlines against the sweep),
  `tools/readability.py` (OCR gate against DejaVu Serif),
  `tools/proof.py` and `tools/sketch_node.py` (proofs; the sketch engine
  in node), `tools/finish.py` (STAT, WOFF2), `scripts/build.sh`,
  `scripts/check.sh`.
- Tests (`tests/test_warp.py`): metrics, glyph set, the port against the
  sketch engine, outlines, kerning, features, names, reports,
  determinism.
- `warp/OFL.txt`.

### Changed from the sketch

- The bar of A, Æ and ∀ reaches the hairline (the counter was open).
- The maths operators share one advance.
- See `STATUS.md`, "Deviations from the sketch".
