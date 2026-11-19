# Warp changelog

## Unreleased

## 0.3.0

### Added

- Roman and Italic variable TTF and WOFF2 fonts, with weights from 300 to 700.
- Clean variable builds that replay inspected contour corrections and run the numerical gates.
- Release archives with variable fonts, pinned file checks and SHA-256 sums for every font.
- Tests for archive contents and missing or changed variable fonts.

### Changed

- Raised the release job timeout to 75 minutes and added variable font inspection.
- Set the package and font versions to 0.3.0 and 0.300.


- Added eight measured side-bearing findings and an exact comparison that rejects missing or unlisted findings.

- Fixed the measurement mode accepting a saved proof without source hashes: it now needs a hash for each of the seven masters. A correction now updates the saved hashes and correction list at once, so a failed measurement can be retried.
- Fixed a failed correction build leaving rewritten masters beside saved hashes of the old ones: the masters are now restored.
- Raised the build job timeout of the Warp workflow from 40 to 75 minutes.
- Fixed correction replay to resolve composites before rotating their bases, preserving the frozen source outlines.
- Fixed correction order so reported composites resolve before any base glyph rotates.
- Last inspected files: Roman 7,448,792 bytes; Italic 6,679,608 bytes. Both report 0 FAIL and 0 ERROR.
- The inspected ladder is verified with eight accepted side-bearing findings: three in Roman and five in Italic.
- Reduced variable font size by sharing identical outlines and variation data, with IUP tolerances for each weight.
- Added checks that rebuild both fonts and limit each file to 9,437,184 bytes.
- Added a mode that measures corrected masters and leaves Fontspector results unknown.
- Preserved contours with edge movements of one unit when IUP would omit them.

- Fixed compatibility errors losing their diagnostic payload when passed between processes.
- Fixed PANOSE weight digits for new text weights while keeping released styles unchanged.
- Changed interpolation reports to name the two-master source for the 770 findings.
- Removed the polygon-area filter; contour order and coordinates are unchanged at the five affected source weights.
- Removed an unnecessary font copy.
- Added type annotations for the weight ladder APIs, reports and tests.

- Added source masters at weights 350 and 450 to both variable fonts and raster checks at the middle of every master gap.
- Changed font build, correction and measurement to run in separate processes that exit before inspection.
- Changed the inspection allocator settings to return freed buffers between glyph checks.
- Fixed incomplete inspection reports so that unknown finding counts are not reported as zero.
- Fixed thin strokes at gap midpoints by storing variation supports on the axis grid before interpolation.
- Fixed lost ink in the new Roman iota sources by joining each stroke hull in order.
- Fixed contour start correction for composite glyphs by resolving their component outlines in every master.
- Fixed the warning comparison so that new unreachable glyphs cannot pass as an unchanged warning.
- Added text weight parameters from 300 to 700 and Light, Medium and Demi styles on the compatible path.
- Added a Roman and Italic weight-ladder tool with named-weight, raster and interpolation checks.
- Fixed summed variation errors at interior weights with local weight supports and exact component offsets.
- Fixed six further italic contour changes with separate stroke contours.
- Changed weight checks to run the source compiler in a child process and use one Fontspector worker.
- Added a Regular and Bold outline report and two methods behind `--compatible`.
- Fixed the 15 contour mismatches with separate stroke contours on the compatible path. All 890 glyphs now have matching point structure.
- Added a two-master variable-font test, measured topology changes, endpoint checks and a check that the other 875 outlines stay the same.
- Added checks for the default font bytes and for CPU-independent output from the compatible path.

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

- The build output no longer depends on the CPU path used by NumPy. `fonts/warp` and the fidelity, sketch and charset proofs in `proofs/warp` were rebuilt. The OCR report and the MATH image were not rebuilt and still come from the 28 October build. Most outlines change only in the last bits of their coordinates; the largest known change is in the Xi (Regular) outline, which moved by up to 2 font units because of the CPU-dependent curve fit.
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
