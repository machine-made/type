# Warp status

| Field | Value |
| --- | --- |
| Family | machine-made Warp, machine-made Warp Display |
| Version | 0.1 (font version 0.100) |
| Pull request | branch `warp/v0.1` (PR to open) |
| Stage | Warp 0.1 built: 6 static styles (TTF, OTF, WOFF2) |
| Gate now | Jac reviews the PR; the founder reviews the proofs by eye |
| Next | Release 0.1 (tag `warp-v0.1.0`). Then 0.2 (MATH table) and 0.3 (variable font) |
| Last local run | 2026-10-27: tests, build, byte check, fidelity, OCR gate, Fontspector, site build all green |
| Last green CI | none yet (first run is on the PR) |

## Proven (local run, 2026-10-27)

- 44 pytest tests pass. One runs the sketch engine in node and compares
  the advances and the ink bounds of the 120 sketch characters, the
  old-style figures and the small capitals with the port (Regular,
  Italic, Display, Display Italic; within 0.02 unit).
- The build is byte-reproducible: two builds give the same files (also
  one with one process and one with two).
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the 6 TTF and
  the 6 OTF (accepted WARNs below).
- Outline fidelity (`proofs/warp/fidelity.json`): every drawn glyph of
  every style, read back from the compiled TTF, against an independent
  fill of its pen sweep. Largest difference 4.7 % of the ink (Display
  ξ small cap, 128 ppem; hairlines of 9 units and integer points), mean
  0.7 to 1.7 %. Limit 5 %.
- Sketch comparison (`proofs/warp/sketch-compare.json`): mean IoU with
  the sketch engine 0.95 (Regular), 0.95 (Italic), 0.95 (Display),
  0.94 (Display Italic). × < > score low because they moved (see
  "Deviations"). Bold and Bold Italic score 0.81: the bold skeleton is
  6 % wider on purpose.
- OCR readability gate (`proofs/warp/readability.json`, Tesseract 5.3.4,
  10, 12 and 14 px): see below. Passes.

## Readability (OCR)

| Style | Warp CER | DejaVu Serif CER | Limit | Result |
| --- | --- | --- | --- | --- |
| Regular | 0.0234 (10 px 0.034, 12 px 0.020, 14 px 0.016) | 0.0012 | 0.0312 | pass |
| Italic | 0.0192 (10 px 0.049, 12 px 0.004, 14 px 0.005) | 0.0000 | 0.0300 | pass |

Warp reads a little worse than DejaVu Serif, a screen face. The gap is
about 2 points at 10 px and closes at 12–14 px in the italic. The
errors come from approved forms: Tesseract reads the open lower loop of
g as a comma ("ng, t"), f as t, ﬁ and ﬂ as h and H, and joins words at
the narrow word space. The optical size does not change this (opsz 9
to 12 all give about 2 %). The margin (3 points) stops a regression; it
does not prove parity.

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `name/family_and_style_max_length` | Display TTF and OTF | PostScript names over 27 characters (`MachineMadeWarpDisplay-Regular`, `-Italic`). Only old PostScript printers care. |
| `unreachable_glyphs` | OTF | The capital marks (`*comb.case`) and `two.dnom`, `four.dnom` are used only inside composites; CFF flattens composites. The TTF keep them as components. |

## Deviations from the sketch

| What | Sketch 0.2 | Font 0.1 | Why |
| --- | --- | --- | --- |
| Outlines | canvas fill of hull polygons | union with skia-pathops, cubic fit (0.9 unit), extrema points | Clean outlines with few points. Checked by `tools/fidelity.py`. |
| Bar of A (roman and italic), Æ, ∀ | starts at x 95 (A) or 105 (italic A) | starts at 72 or 84 | The bar stopped a few units short of the hairline: the counter was open (Fontspector `contour_count`). |
| × < > | own advances | the advance of + (with ÷ ± ≠ ≤ ≥ ∈ ∉ ⊂ ⊆ ≈ ≡ ∝ ¬) | Operators line up in tables (Fontspector `math_signs_width`). The ink is the sketch's. |
| Lowercase head serifs | the engine has a wedge serif, but it reads `p.lc`, which `params()` never sets | flat serifs, as the sketch draws them | The port follows what the approved page shows. |
| Bold | not in the sketch (the sketch has the `stem` parameter) | stem 134, contrast 11.3, serif x 0.82 thick and 0.65 long, skeleton x 1.06 | A true bold, not a smear (see `proofs/warp/warp-styles.png`, `warp-paragraph.png`). |
| Italic capitals other than A C G M N O Q V W | slanted roman | slanted roman with unbracketed serifs | Didone italics are unbracketed; slanted brackets look lopsided. No roman serif sits where the italic draws a hook or a drop (those letters have their own forms). |
| Optical sizes | continuous `opsz` | two statics: opsz 10 (text) and 60 (Display) | Statics in 0.1; `opsz` axis in 0.3. Maths scripts in the setter use smaller optical sizes; the font has one. |
| Stretchy delimiters, radicals, big operators at size | drawn by the pen at any height | one size each | The MATH table (variants, assemblies) is 0.2. |
| Nib cache | the engine caches nibs by keys rounded to 0.01 | no cache | Same shapes within 0.01 unit. |

New glyphs (not in the sketch), drawn with the same pen: the rest of
ASCII, the Latin-1 letters and symbols, the marks, ffi and ffl, the
rest of Greek, 23 maths symbols, ₹, the dotted circle.

## Open issues for 0.2

- OpenType MATH table: constants (axis 250, rule thickness, script
  sizes and shifts), italic correction, top accent attachment, size
  variants and assemblies for ( ) [ ] { } √ ∫ ∑ ∏, drawn by the pen at
  each height.
- OCR: the open loop of g, f, ﬁ and ﬂ at 10 px; the word space (270
  units) is narrow for text. Try a wider space at text size and a
  firmer f hook, then re-run the gate.
- Ξ is all horizontal strokes, so the level pen makes it light (Σ too, a
  little). Consider a heavier middle bar.
- Italic capitals other than A C G M N O Q V W: own cursive forms; the
  italic & is the roman one, slanted.
- More kerning: lowercase pairs, Greek lowercase, italic-specific pairs.
- Latin Extended-A, Greek tonos and dialytika, more symbols (‰ ‡ † ℓ ℏ).
- Superior and inferior figures as a feature (`sups`, `subs`, `frac`).
- Name: register search for WARP before a wide release (see `BRIEF.md`).
- No hinting.

## Planned for 0.3

- The variable font, axes `wght` and `opsz`, from the same pen model.
  Pen sweeps are not point-compatible across masters, so 0.3 needs a
  fixed outline topology per glyph (for example an analytic sweep:
  offset each segment by the nib's support point, join with nib arcs,
  with a fixed point count), then masters at the axis corners and a
  drift report as for Heddle.
