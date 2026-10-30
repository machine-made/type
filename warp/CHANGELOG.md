# Warp changelog

## 0.200 (Warp 0.2)

### Added

- OpenType MATH table in all six fonts (`loom/mathtable.py`,
  `loom/mathglyphs.py`): constants (axis 250, rule thickness = the rule
  pen, script sizes 70 % and 50 %, shifts and gaps from the x-height
  and the rule), italic corrections, top accent attachment, four size
  variants for ( ) [ ] { } | ‖ ⟨ ⟩ √ ∫ ∑ ∏ and assemblies for
  ( ) [ ] { } | ‖ √ ∫. Every variant and part is drawn by the pen at
  its height.
- Mathematical italic letters (U+1D434 to U+1D467, Greek U+1D6E2 to
  U+1D715, ℎ): the italic forms, drawn in the upright styles.
- `tools/math_proof.py`: a page of formulas set by LuaLaTeX and
  unicode-math (`proofs/warp/warp-math.png`).
- Latin Extended-A (U+0100 to U+017F) and Ș ș Ț ț: new marks (breve,
  ogonek, double acute, comma below, turned comma above, the vertical
  caron of ď ť ľ Ľ, capital forms), new letters đ ħ Ħ Ł ł Ŧ ŧ Ŋ ŋ ĸ ſ,
  composites for the rest. Latvian and Romanian letters use the comma
  below.
- Greek tonos and dialytika (Ά to ώ, ΐ ΰ, ΄ ΅, ano teleia, question mark).
- ‰ † ‡ ℓ ℎ ℏ ‖ ⟨ ⟩ ˘ ˛ ˝.
- Superior and inferior figures (U+2070 to U+2089), numerators,
  denominators; features `sups`, `subs`, `sinf`, `numr`, `dnom`, `frac`.
- Italic capitals with their own cursive forms: B D E F H I J K L P R S
  T U X Y Z and the italic & (an Et).
- Kerning: lowercase pairs (ro xo ox ev ex vs ka), Greek lowercase (τ γ
  ν χ), italic-only pairs, the Extended-A letters in the classes.
- Hinting: the TTF are hinted with ttfautohint 1.8.4 (ttfautohint-py
  0.6.1), byte-reproducible.
- Small capitals for đ ħ ł ŧ ŋ ŀ and ϊ ϋ; smcp maps every lowercase
  letter.

### Changed

- g: the lower loop closes on the link (OCR read it as a comma).
- f, ﬀ: a firmer hook with a larger drop. ﬁ ﬂ: the bar stops short of
  the i and the l; the f of ﬂ ends in its own drop.
- Ξ and Σ: heavier horizontals.
- Word space 310 units at text size (270 in 0.1); Display keeps 270.
- √ has no right side bearing, so that the rule of a maths engine meets
  its bar.
- Readability gate (Tesseract, 10 to 14 px): Regular CER 0.0234 to 0.0018, Italic 0.0192 to 0.0126.

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
