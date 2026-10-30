# Warp status

| Field | Value |
| --- | --- |
| Family | machine-made Warp, machine-made Warp Display |
| Version | 0.2 (font version 0.200) |
| Pull request | branch `warp/v0.2` (PR open for review) |
| Stage | Warp 0.2 built: 6 static styles (TTF hinted, OTF, WOFF2) with an OpenType MATH table |
| Gate now | Jac reviews the PR; the founder reviews the proofs by eye |
| Next | Release 0.2 (tag `warp-v0.2.0`). Then 0.3 (variable font, branch `warp/v0.3`) |
| Last local run | 2026-10-28: build twice (byte-identical), fidelity (max 4.0 %), OCR gate, Fontspector 1.9.0 (0 FAIL, 0 ERROR), LuaLaTeX maths proof, site build, pytest (88 passed) |
| Last green CI | see the PR |

## Proven (local run, 2026-10-28)

- TESTS pytest tests pass, among them: the sketch engine in node against
  the port; coverage of Latin Extended-A, Ș ș Ț ț and twelve Central
  European languages; the MATH table (presence in all 12 files,
  constants, every variant and part exists, variant heights grow,
  parts overlap by at least MinConnectorOverlap, the stems of the parts
  line up); HarfBuzz reads the MATH table (uharfbuzz 0.53.3); sups,
  subs, frac; the TTF are hinted.
- The build is byte-reproducible: two builds (one and two processes)
  give the same files, the hinted TTF too.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the 6 TTF and
  the 6 OTF (accepted WARNs below).
- Outline fidelity (`proofs/warp/fidelity.json`): every drawn glyph of
  every style against an independent fill of its pen sweep; FIDMAX.
  Limit 5 %.
- OCR readability gate (`proofs/warp/readability.json`): see below.
- LuaLaTeX and unicode-math set a page of formulas with the MATH table
  (`proofs/warp/warp-math.png`, `tools/math_proof.py`): fractions,
  radicals from the text size to assemblies, ∑ ∏ ∫ with limits,
  delimiters from \big to assemblies taller than the fourth variant,
  accents, cases. No missing character.

## Readability (OCR)

| Style | Warp 0.2 CER | Warp 0.1 CER | DejaVu Serif | Limit | Result |
| --- | --- | --- | --- | --- | --- |
| Regular | 0.0018 | 0.0234 | 0.0012 | 0.0312 | pass |
| Italic | 0.0126 | 0.0192 | 0.0000 | 0.0300 | pass |

What helped: the closed g, the firmer f hook, the ﬁ ﬂ bars that stop
short (no more "h" and "H"), the 310-unit word space (300 and 330 were
tried; 310 read best), and hinting. The italic at 10 px still loses a
few letters (v, c and e run together); it is fine from 12 px.

## MATH table

| Item | Value |
| --- | --- |
| Axis height | 250 |
| Rule thickness (fraction, radical, over- and underbar) | the rule pen Rw: 38 (Regular), 61 (Bold), 33 (Display); the thickness of − |
| Script / scriptscript | 70 % / 50 % |
| Shifts and gaps | from the x-height and the rule, as the OpenType MATH specification suggests (`loom/mathtable.py`) |
| Size variants | 4 per glyph: delimiters 1250 to 2450 units, ∑ ∏ 1400 to 2600, ∫ 1900 to 3400 |
| Assemblies | ( ) [ ] { } \| ‖ √ ∫; MinConnectorOverlap 40 |
| No assembly | ⟨ ⟩ ∑ ∏ (diagonal strokes cannot be extended) |
| Italic correction | mathematical italic letters, ℎ ℏ, ∫ variants |
| Top accent attachment | every letter (its top anchor) |

The size variants and the parts are upright in every style, the
italics too (stacked parts must line up). The text ( ) [ ] in the
italics stay slanted.

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `name/family_and_style_max_length` | Display TTF and OTF | Family and style together are over 32 characters. The name is long but unique. |
| `unreachable_glyphs` | all | The MATH variants and assembly parts are reached through the MATH table, not through cmap or GSUB. In the OTF also the capital marks and the denominators used only inside composites. |
| `contour_count` | all | Designs that differ from the usual count: ΅ ΐ ΰ (the tonos stands free between the dots), the double acute of the capitals, ţ in small capitals, Ű ű. |

## Deviations from the sketch

| What | Sketch 0.2 | Font 0.2 | Why |
| --- | --- | --- | --- |
| Outlines | canvas fill of hull polygons | union with skia-pathops, cubic fit (0.9 unit), extrema points | Clean outlines with few points. Checked by `tools/fidelity.py`. |
| Bar of A (roman and italic), Æ, ∀ | starts at x 95 (A) or 105 (italic A) | starts at 72 or 84 | The counter was open. |
| × < > | own advances | the advance of + | Operators line up in tables. |
| Lowercase head serifs | wedge serif in the engine, never drawn | flat serifs | The port follows the approved page. |
| Bold | not in the sketch | stem 134, contrast 11.3, serifs x 0.82, skeleton x 1.06 | A true bold. |
| g (0.2) | open lower loop | the loop closes on the link | OCR read the open loop as a comma at 10 px. |
| f, ﬀ (0.2) | small drop | larger drop, lower | OCR read f as t. |
| ﬁ ﬂ (0.2) | bar to the i and the l; ﬂ one arch into the l | bars stop short; the f of ﬂ ends in its own drop; the drop of ﬁ is the dot of the i | OCR read ﬁ as h and ﬂ as H. Italic ﬁ ﬂ: bars stop short. |
| Σ (0.2) | hairline bars | bars 1.9 hairlines thick (Ξ: 1.9 and 2.4) | All horizontals: the level pen made them light. |
| Word space (0.2) | 270 | 310 at opsz 10, 270 at opsz 60 (linear in the optical-size factor) | Words ran together at text size. |
| √ (0.2) | right side bearing 0.2 | 0 | The maths rule starts at the advance and must meet the bar. |
| Italic capitals (0.2) | slanted roman for all but A C G M N O Q V W | own cursive forms for B D E F H I J K L P R S T U X Y Z and & | 0.1 open issue. Æ Œ Ø Þ and the Greek capitals stay slanted romans (Þ has the new form). |
| Optical sizes | continuous `opsz` | two statics (opsz 10, 60) | `opsz` axis in 0.3. |

New glyphs in 0.2 (not in the sketch), drawn with the same pen: the
Latin Extended-A letters and marks, Greek tonos and dialytika, ‰ † ‡ ℓ
ℎ ℏ ‖ ⟨ ⟩, superior and inferior figures, the maths variants and parts,
the mathematical italic letters (the italic forms, drawn in the upright
styles; references in the italics).

## Open issues

- Name: register search for WARP before a wide release (see `BRIEF.md`).
- Italic at 10 px: v, c, e run together for OCR (CER 3.4 % at 10 px).
- Æ Œ Ø and the Greek capitals in the italic: still slanted romans.
- MATH: no math kerning (cut-ins), no `ssty` script forms, no
  horizontal stretchy glyphs (over- and underbraces, wide accents), no
  ∬ ∮ and no \mathcal, \mathbb alphabets.
- No hinting in the OTF (CFF) files; the TTF are hinted.
- Polytonic Greek.

## Planned for 0.3

- The variable font, axes `wght` and `opsz`, from the same pen model,
  with a fixed outline topology per glyph (an analytic sweep: each
  segment offset by the nib's support point, nib arcs at joins, cubic
  curves at fixed counts), masters at the axis corners and a drift
  report.
