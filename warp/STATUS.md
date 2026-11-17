# Warp status

| Field | Value |
| --- | --- |
| Family | machine-made Warp, machine-made Warp Display |
| Version | 0.2 (font version 0.200) |
| Pull request | Weight ladder, branch warp-wght-ladder |
| Stage | Warp 0.2 built: 6 static styles (TTF hinted, OTF, WOFF2) with an OpenType MATH table |
| Gate now | Both variable fonts fit 9,437,184 bytes. Numerical gates pass. Fontspector reports 0 FAIL and 0 ERROR for both. |
| Next | Investigate the new side-bearing findings (3 in Roman, 5 in Italic). The optical-size axis remains open. |
| Last local run | 2026-11-17, after the correction-order fix: Roman is 7,448,792 bytes; Italic is 6,679,608 bytes. Both report 0 FAIL and 0 ERROR. The verdict remains not verified because of the new side-bearing findings. |

## Variable font size (2026-11-17)

Both files retain seven masters and 890 glyphs. The saved masters keep their bytes.
The build shares only identical outlines, metrics and complete variation stores.
Each alias keeps its own metric deltas. Roman shares 15 outlines; Italic shares 3.

| File | Before, bytes | Rebuilt, bytes | Limit, bytes |
| --- | --- | --- | --- |
| Roman | 11,350,336 | 7,448,792 | 9,437,184 |
| Italic | 12,509,356 | 6,679,608 | 9,437,184 |

| Source weight | IUP tolerance, units |
| --- | --- |
| 300 | 0.98 |
| 350 | 1.0 |
| 450 | 1.0 |
| 500 | 0.98 |
| 600 | 0.95 |
| 700 | 0.5 |

The named-instance maximum is 0.997061 units in both slopes. The limit remains 1.0 unit.
Regular remains at 0.020 units; Bold remains at 0.520 units.
The raster maximum is 4.994 percent in both slopes, against the unchanged 5 percent limit.

Measurement mode reuses the saved, corrected masters without rewriting them.
It records their hashes and leaves the previous interpolation report intact.
Checks of fresh builds compare compiled outlines and metrics separately from metadata.
Moving contours keep their deltas when IUP would omit the entire contour.
The focused weight ladder suite passed 36 tests, including fresh builds of both fonts.
The full Warp suite passed 139 tests. The byte guard for the released styles passed.
The committed inspection reports 0 FAIL, 0 ERROR and 0 start-point findings for both files.
The verdict is **not verified** because Roman has three new side-bearing findings and Italic has five.
Both slopes add advance-width findings for ellipsis at 350, 449.98779296875 and 450.006103515625.
Italic also adds right-side-bearing findings for zcaron at 449.98779296875 and 450.006103515625.
These glyphs retain exact phantom-point deltas at every tuple; their phantom metrics were not lost.
The warning cause remains unresolved; the metric encoding is unchanged.
Replaying the correction-order fix changes three LightItalic outlines: etatonos, u1D6EF and u1D702.
Their revised build needs another Fontspector run.
The next section records the earlier numerical measurements and the latest inspection counts.

## Text weight ladder (2026-11-16)

Verdict: **not verified**. The latest inspection has 0 FAIL, 0 FATAL, 0 ERROR and 0 start-point findings in both files.
New side-bearing warnings block verification. The tables below retain the earlier numerical measurements, before size optimisation.

Each variable font has masters at 300, 350, 400, 450, 500, 600 and 700,
with axis range 300 to 700 and default 400. The five named weights remain
Light, Regular, Medium, Demi and Bold. All 14 sources have 890 of 890
glyphs with matching contours and points within their slope. This covers
the ten named styles and both new source weights. No glyph is excluded.
The default build still emits only the six released styles.

Policy a keeps overlapping stroke contours. Gamma uses its existing
bottom node to split its loop into two stroke runs.
The table applies at all seven weights; a source name
in parentheses identifies the corrected part of a composite.
`proofs/warp/compat.json` records the glyph, style, weight and counts.

| Glyph | Roman policy (all seven weights) | Italic policy (all seven weights) |
| --- | --- | --- |
| L | — | a (L) |
| Lacute | — | a (L) |
| Lcaron | — | a (L) |
| Lcommaaccent | — | a (L) |
| Ldot | — | a (L) |
| Lslash | — | a (Lslash) |
| Ohungarumlaut | — | a (hungarumlautcomb.case) |
| Uhungarumlaut | — | a (hungarumlautcomb.case) |
| dieresistonos | a (dieresistonos) | a (dieresistonos) |
| dieresistonoscomb | a (dieresistonoscomb) | a (dieresistonoscomb) |
| f_f | a (f_f) | a (f_f) |
| f_f_i | a (f_f_i) | a (f_f_i) |
| f_f_l | a (f_f_l) | a (f_f_l) |
| fi | a (fi) | a (fi) |
| fl | a (fl) | a (fl) |
| gamma | a (gamma) | a (gamma) |
| germandbls | a (germandbls) | a (germandbls) |
| hbar.sc | — | a (hbar.sc) |
| hungarumlautcomb.case | — | a (hungarumlautcomb.case) |
| iotadieresistonos | a (dieresistonoscomb) | a (dieresistonoscomb) |
| kappa | a (kappa) | a (kappa) |
| l.sc | — | a (l.sc) |
| lacute.sc | — | a (l.sc) |
| lcaron.sc | — | a (l.sc) |
| lcommaaccent.sc | — | a (l.sc) |
| ldot.sc | — | a (l.sc) |
| lslash.sc | — | a (lslash.sc) |
| ohungarumlaut.sc | — | a (hungarumlautcomb.case) |
| u1D43F | a (u1D43F) | a (L) |
| u1D6FE | a (u1D6FE) | a (gamma) |
| u1D705 | a (u1D705) | a (kappa) |
| uhungarumlaut.sc | — | a (hungarumlautcomb.case) |
| upsilondieresistonos | a (dieresistonoscomb) | a (dieresistonoscomb) |

A batch union drops ink in Roman iota at weight 450. The compatible
sources at 300, 350, 450, 500 and 600 union each stroke hull in fixed
order; its composites inherit that repair. Every hull is kept. The
Regular and Bold source coordinates stay frozen.

The earlier three-source trial needed extra sources at 500 and 600:
its Roman maximum differences were 37.346 and 40.824 units; its Italic
maxima were 141.710 and 70.400 units. Those sources remain. The new
350 and 450 sources use the same engine-parameter rule as the named
weights. BRIEF gives the rule and the stem widths.

Every named-instance check reads the saved variable font and compares
all 890 glyphs with the compiled compatible static at the same weight.
The bound includes 0.02 units for curve flattening. The Regular and
Bold bounds still equal the earlier endpoint result.

| Weight | Roman, units | Italic, units |
| --- | --- | --- |
| 300 | 0.520 | 0.520 |
| 400 | 0.020 | 0.020 |
| 500 | 0.520 | 0.520 |
| 600 | 0.547 | 0.547 |
| 700 | 0.520 | 0.520 |

The raster gate derives the middle of every adjacent master gap with
`(left + right) / 2`. It compares every drawn glyph with an independent
fill of the pen sweep at 16, 32, 64 and 128 pixels per em. All maxima
below occur at 128 pixels per em. The limit stays at 5 percent.

| Masters | Gap | Midpoint | Roman, percent | Italic, percent |
| --- | --- | --- | --- | --- |
| 300 to 350 | 50 | 325 | 4.990 | 4.990 |
| 350 to 400 | 50 | 375 | 4.088 | 4.087 |
| 400 to 450 | 50 | 425 | 4.383 | 4.108 |
| 450 to 500 | 50 | 475 | 3.286 | 2.943 |
| 500 to 600 | 100 | 550 | 3.439 | 3.439 |
| 600 to 700 | 100 | 650 | 3.434 | 3.434 |

The earlier checks at 350 and 450 remain in the report as well. At a
source weight, the residual includes arc sampling and integer rounding
relative to the independent sweep.

| Source weight | Roman, percent | Italic, percent |
| --- | --- | --- |
| 350 | 3.098 | 2.942 |
| 450 | 2.703 | 2.703 |

The first Roman measurement gave 5.737 percent for underscore at 425.
The stored 450 support had rounded up on the axis grid. This put both
edges of the bar just inside a half-unit boundary; integer rounding
then made the bar too thin. Supports now round down on the stored
1/16384 grid before interpolation. Source weights, test weights and
limits stay the same. The second round passes every raster check in
both files; the maximum is 4.990 percent at 325 for radical.ext.

Fontspector 1.9.0 is the cached release named by the workflow. Its
archive SHA-256 matches the workflow, and its executable matches the
archive. The full universal profile uses network checks off and one
worker, with two Rayon threads. Three Roman runs were killed with
exit -9 before a report was written. Timed attempts reached about
9.2 GiB resident memory. The shared agent group has a 13 GiB limit.
The complete run used a machine with more memory and the same
profile, one worker and two Rayon threads.

| Final profile | Complete | SKIP | INFO | PASS | WARN | FAIL | ERROR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Roman | yes | 23 | 1 | 96 | 5 | 0 | 0 |
| Italic | yes | 22 | 1 | 97 | 7 | 0 | 0 |

These counts come from the latest committed `proofs/warp/ladder.json`.

The pinned inspector's [contour comparison](https://github.com/simoncozens/interpolatable/blob/ad22fffde7407ed3136a8ee3723a99b9786ead01/interpolatable-lib/src/isomorphism.rs)
builds all cyclic contour vectors. Their memory
use grows with the square of the point count; the largest contour has
6,842 points. Font build, correction and measurement now run in separate
processes that exit before inspection. The inspection allocator also
returns large freed buffers between glyphs. The large-contour allocation remains.

There were 770 findings in the two-master spike report; 0 in the seven-master ladder.
The previous five-master report had 1 finding. The previous
finding was Italic uni2080, a zero.dnom component translated by (0, -150).
The old correction loop skipped composite glyphs.
The correction loop resolves reported composites in every master before rotating any glyph.
It keeps contour order and rotates each requested contour once.
The previous finding was replayed only after an exact cyclic comparison
of the old and new compiled contours; no rebase shift was needed. The
full-profile result shows zero interpolation findings.

| Variable font | Five-master bytes | Seven-master bytes |
| --- | --- | --- |
| Roman | 7,419,520 | 11,350,336 |
| Italic | 6,386,772 | 12,509,356 |

All 130 tests passed serially. With AVX-512 off, 43 selected compatibility,
ladder, deterministic and CPU tests passed, with 87 deselected. The
unchanged hard-glyph test passes, as do the frozen coordinate hashes of
the 875 Regular and Bold glyphs. The byte guard also detects the expected
mismatch when the compatible flag is forced on.

A fresh default build emitted exactly six styles. All 18 TTF, OTF and
WOFF2 files match HEAD byte for byte. OTF uses CFF optimization level 2.
No tracked font file was written.

The local proof sheet shows five named weights in both slopes at 20, 40 and 80 pixels.
The proof sheet was reviewed by hand on one machine.
The helper renders the image; it performs no automatic clipping check.
The complete numerical report is `proofs/warp/ladder.json`.

## Regular and Bold variable-font test (2026-11-07)

Verdict: **verified at the two endpoints** of the Regular/Bold test. The
checks below compare each endpoint with the master that built it; they do not
show that the interpolation between the masters is correct. The earlier
`vf_spike.py` run printed "inconclusive" until Fontspector was run.
The tool now calls `vf_ladder.py` for the full text weight range.
This is not a production variable-font release.

All 890 glyphs now have matching contour and point structure. No glyph is
excluded. No font file in `fonts/warp` was changed.

| Path | Glyphs | Contours compatible | Points compatible |
| --- | --- | --- | --- |
| Default | 890 | 851 | 28 |
| Shared arc sampling before the topology fix | 890 | 875 | 875 |
| Shared arc sampling with separate stroke contours | 890 | 890 | 890 |

Policy **a** applies to all 15 glyphs below: retain overlapping stroke
contours. Each stroke, dot, terminal and bracket keeps its source hulls.
Gamma's loop is cut at its existing bottom node into two stroke runs.
Each hull is used once; none is moved or dropped. Both runs keep the
shared nib. The two accented Greek letters keep their existing components
and use the corrected mark.

The compatible build keeps `removeOverlaps` off. Its simple glyphs have
the overlap flag set. The other 875 compatible glyphs keep every point:
frozen coordinate hashes for both masters match, and their 875 report
rows have zero changes. Contour order also keeps the same source-stroke
order in the two masters.

`proofs/warp/compat.json` records each cause, original contour counts,
contour bounds and signed areas on both sides of each transition. The
weight scan interpolates the engine parameters from Regular to Bold at
opsz 10. It checks each integer weight and brackets each detected change
to 1/128 of a weight unit. These are changes in generated sweeps, not
measurements of intermediate variable-font instances.

Counts below are Regular/Bold. Weights are rounded here; the JSON has
the brackets. The last column is the maximum boundary difference between
the compatible and default compiled outlines, in font units, including
a 0.07-unit error bound. Internal overlap edges are removed from a copy
before this ink-boundary comparison.

| Glyph | Policy | Default contours | Fixed contours | Weight of change | Default difference R / B |
| --- | --- | --- | --- | --- | --- |
| germandbls | a | 1/2 | 5/5 | 530.80 | 2.485 / 2.070 |
| f_f | a | 2/3 | 10/10 | 480.04 | 2.070 / 2.069 |
| fi | a | 2/1 | 10/10 | 495.67 | 4.032 / 2.055 |
| fl | a | 2/1 | 10/10 | 537.82 | 3.467 / 2.055 |
| f_f_i | a | 3/3 | 15/15 | 480.04, 495.67 | 3.827 / 2.993 |
| f_f_l | a | 3/3 | 15/15 | 480.04, 537.82 | 3.291 / 2.069 |
| gamma | a | 2/1 | 3/3 | 419.89 | 3.070 / 1.663 |
| kappa | a | 1/2 | 4/4 | 611.44 | 3.311 / 2.009 |
| iotadieresistonos | a | 4/3 | 4/4 | 683.87 | 2.090 / 1.579 |
| upsilondieresistonos | a | 4/3 | 4/4 | 683.87 | 2.090 / 1.579 |
| dieresistonos | a | 3/2 | 3/3 | 683.87 | 1.761 / 1.622 |
| dieresistonoscomb | a | 3/2 | 3/3 | 683.87 | 2.090 / 1.579 |
| u1D43F | a | 1/2 | 4/4 | 685.83 | 2.049 / 2.424 |
| u1D6FE | a | 2/1 | 3/3 | 421.47 | 2.070 / 1.895 |
| u1D705 | a | 1/2 | 4/4 | 610.58 | 1.651 / 2.006 |

The two gamma counters fall below the existing 40 square unit area filter;
that event is not their geometric closure. The other events are joins:
the lower bowl and foot of ß, the feet and terminals of the ligatures,
the arms and stem of kappa, the foot curl of the italic L, and the right
dieresis dot with the tonos. The JSON has the cause for each glyph.

The endpoint reference is the compiled compatible static master for all
890 glyphs, including the 15 corrected glyphs. The maximum displacement
of corresponding vertices bounds both directions of the full polyline
distance. The gate adds 0.02 units for curve flattening. It does not
round away the small interpolation residuals. The largest raw displacement
is 0 at 400 and 0.5 units at 700 (oslash).

```text
compat.py: glyphs 890, contours-compatible 851, point-compatible 28
compat.py --fixed: glyphs 890, contours-compatible 890, point-compatible 890
pytest -k "compat or deterministic or cpu": 16 passed, 87 deselected
vf_spike.py: instance 400: max difference 0.020 units, instance 700: max difference 0.520 units
Fontspector: SKIP 23, INFO 1, PASS 95, WARN 775, FAIL 0, FATAL 0, ERROR 0
Default build: 18/18 files byte-identical
```

Fidelity passes the unchanged 5 % limit: Regular 3.048 % (N, 128 ppem),
Bold 2.327 % (radical.bot, 128 ppem). The gate checks all 555 drawn glyphs
in each compiled compatible static against an independent fill of the
original pen sweep. A copy of each compiled glyph has its overlaps
resolved for the raster helper, which requires disjoint contours. The
actual masters and variable font retain their overlaps. The 890-glyph
structure and endpoint checks also cover the composites.

Fontspector 1.9.0 uses the universal profile with network checks off. It was run by
hand on the local two-master test font with
`fontspector -p universal --skip-network`; no report is committed, so this is a
local result. Its
archive matches the checksum in the workflow; its executable matches
the archive. The two named instances have PostScript names. Adding these
names left the outline, variation and advance-width tables byte-identical.

The 775 warnings are 770 interpolation findings, one unusual contour
count check, one file-size check, one missing avar check, one unreachable
glyph check and one advance-width variation check. The interpolation
findings include start points and uneven weight. They remain open before
a production variable font can ship. This test verifies two endpoints;
it does not prove the full weight range, italics or optical-size axis.
The variable TTF is about 3.24 MB. There is no size or speed claim.

The local proof sheets show the corrected glyphs at
weights 400, 550 and 700 at 20, 40 and 80 pixels. A second sheet uses
50 % opacity at 100 pixels. They were looked at by eye on one
machine (FreeType and Pillow); the script and the images are not committed, so
this is a local observation, not a reproducible check, and not a test of every
renderer.

All 18 default files match a fresh build: six styles in TTF, OTF and
WOFF2. The OTF check uses the release command's CFF optimization level 2.
The compatible flag stays off by default. In a separate process, setting
the default of `build_font` to true made the byte test fail at its hash
assertion: 1 failed, 12 deselected. The source was not changed. With the
default off, that test passes.

The final selected test run has 16 passes, including the unchanged
hard-glyph test. It checks both CPU feature paths, all 13 drawn topology
fixes, the endpoint bound, and the frozen coordinates of the other 875
glyphs. Their changed-point count is zero in both masters. The old
fallback assertion now checks that every hull is kept once, all stroke
contours have positive area, and source order matches. No zero-area
contour is added to make the masters agree.

## CPU build check (2026-11-07)

The outline fit uses products for powers, scalar math for distances and
angles, and a fixed order for sums. It does not use BLAS. The pen model
and the fit limits stay the same.

The build is reproducible across the two tested CPU paths. A fresh build
with the default features and a fresh build with AVX-512 off each matched
all 18 rebuilt font files, byte for byte. This was checked on one machine.

The outline fidelity gate passes: the maximum ink difference is 4.016 %
(limit 5 %). Fontspector 1.9.0 passes on all 12 TTF and OTF files, with
0 FAIL and 0 ERROR. The checks used the universal profile with network
checks off. JSON reports were written; Markdown export could not write
its template cache.

The proof sheets were rebuilt. Two local checks remain open: Tesseract
is not installed, so the OCR gate could not run. LuaLaTeX cannot load
`luaotfload-main`, so the MATH proof could not be rebuilt. The old OCR
report and MATH image stay in place; they are not evidence for this run.

Two tests use separate processes with the default CPU features and with
AVX-512 off. One checks curve points, the fit, and corner angles. The
other builds the small glyph set needed to check the Greek capital Xi:
Xi, .notdef, and o for hinting. It compares every byte of the hinted TTF,
OTF, and WOFF2 files. Both tests fail with the old arithmetic and pass
with the fixed code.

From the repo root, with the build tools on PATH, run:

```sh
RAYON_NUM_THREADS=2 WARP_JOBS=1 warp/scripts/build.sh
NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SKX AVX512F" \
  RAYON_NUM_THREADS=2 WARP_JOBS=1 warp/scripts/build.sh
RAYON_NUM_THREADS=2 python -m pytest warp/tests -k cpu_features
```

CI checks each build against the committed fonts. Any byte change fails
the check. GNU cmp has no recursive mode: for a local folder check,
compare the file lists, then run `cmp` on each pair of files.

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
  every style against an independent fill of its pen sweep.
  Limit 5 %.
- OCR readability gate (`proofs/warp/readability.json`): see below.
- LuaLaTeX and unicode-math set a page of formulas with the MATH table
  (`proofs/warp/warp-math.png`, `tools/math_proof.py`): fractions,
  radicals from the text size to assemblies, ∑ ∏ ∫ with limits,
  delimiters from \big to assemblies taller than the fourth variant,
  accents, cases. No missing character.

## Readability (OCR)

Results of 2026-10-28, from the 0.2 build before the CPU-independent rebuild of 2026-11-07.

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

## Variable-font follow-up (0.4 fallback)

- The variable font, axes `wght` and `opsz`, from the same pen model,
  with a fixed outline topology per glyph (an analytic sweep: each
  segment offset by the nib's support point, nib arcs at joins, cubic
  curves at fixed counts), masters at the axis corners and a drift
  report.
