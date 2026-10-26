# machine-made Sans: STATUS

| Field | Value |
| --- | --- |
| Family | machine-made Sans |
| Version | 0.100 (release 0.1) |
| Branch | `sans/v0.1` |
| Stage | 0.1 built and checked. Forked from Plus Jakarta Sans 2.071; Lurus and Lancip forms are the defaults; line metrics match Weft. |
| Gate now | Jac reviews the branch and opens the PR. The founder looks at the proofs in `proofs/sans/`. |
| Next | 0.2: redraw the shapes in the style of Weft (see "For 0.2" below). |
| Upstream | tokotype/PlusJakartaSans at `18d1cd2f7ea10481919d2f05c1f7064b7307fc26` |
| Last green CI | none yet (workflow `.github/workflows/sans.yml` is new on this branch). Local run of the same steps on 2026-10-26: green. |

## Proven (local run, 2026-10-26)

- Build: `sans/scripts/build.sh` makes 2 variable fonts (wght 200 to
  800), 14 TTF, 14 OTF and 2 WOFF2. Two builds give the same bytes.
- Fontspector 1.9.0, universal profile, `--skip-network`: **0 FAIL,
  0 ERROR, 0 FATAL** in all four runs.

  | Files | PASS | WARN | FAIL | ERROR | SKIP | INFO |
  | --- | --- | --- | --- | --- | --- | --- |
  | variable (2) | 181 | 12 | 0 | 0 | 41 | 5 |
  | ttf (14) | 1017 | 32 | 0 | 0 | 499 | 33 |
  | otf (14) | 895 | 42 | 0 | 0 | 625 | 19 |
  | webfonts (2) | 10 | 0 | 0 | 0 | 3 | 0 |

- fontTools `varLib.interpolatable` on the master UFOs of both sources:
  no problems.
- pytest: 116 tests pass (`sans/tests`). They check that the committed
  sources are the output of `fork.py` on the pinned upstream, that each
  new default letter draws the same outline as the upstream Lurus or
  Lancip glyph, that ss01 draws the upstream default, the names, the
  line metrics, style linking and the stylistic-set names.
- For comparison, the upstream 2.071 fonts in the same Fontspector
  version: variable 36 FAIL (missing fvar PostScript names, Mac name
  records, instance name length), OTF 14 ERROR. The upstream static TTF
  of U+2195 is correct; a build of the upstream source with current
  glyphsLib makes it empty (repaired here).

## Line metrics

machine-made Weft 0.1: 1000 UPM, ascender 719, descender −219, typo and hhea
906/−281/0. (Weft phase 1 had 875. The release branch changed Sans
to 906 in `scripts/fork.py` to match Weft 0.1.)

| Metric | Plus Jakarta Sans 2.071 | machine-made Sans 0.1 |
| --- | --- | --- |
| UPM | 1000 | 1000 |
| typoAscender / typoDescender / typoLineGap | 772 / −228 / 0 (upright source) or 1038 / −222 / 0 (italic source); fonts: 1038 / −222 / 0 | **906 / −281 / 0** |
| hheaAscender / hheaDescender / hheaLineGap | 1038 / −222 / 0 | **906 / −281 / 0** |
| winAscent / winDescent | 1296 / 356 | 1296 / 356 (no change) |
| USE_TYPO_METRICS | on | on |
| Default line height (typo) | 1.260 em | **1.187 em**, the same as Weft |

The win values stay at the upstream values. They must be at least the
font bounding box (yMax 1294, yMin −263 in ExtraBold), or Windows clips
the glyphs. The line height on Windows GDI is thus larger than on other
platforms; it was so in upstream too.

The tighter line box (1.187 em) is a decision for the shared line with
Weft. Accents on capitals go above the typo ascender: Á is at 999 to
1019 and Ấ at 1049 to 1069, against an ascender of 906. With line
height "normal", stacked lines of accented capitals can touch the line
above. Set a CSS line-height of 1.3 or more for text with many accented
capitals. The `typoascender_exceeds_Agrave` WARN reports this.

## Measured x-heights (for 0.2)

Measured from the outlines (flat tops of x, z, v and of H, E, I) and
from OS/2:

| Font | x-height | Overshoot (o) | Cap height | x/cap |
| --- | --- | --- | --- | --- |
| machine-made Sans ExtraLight | 526 | 538 | 745 | 0.706 |
| machine-made Sans Regular | 536 | 548 | 745 | 0.719 |
| machine-made Sans Bold | 544 | 556 | 745 | 0.730 |
| machine-made Sans ExtraBold | 546 | 558 | 745 | 0.733 |
| machine-made Weft Regular (OS/2) | 500 | n/a | 688 | 0.727 |
| machine-made Weft Regular (outline, with stroke) | x top 559, o top 542 | | H top 730 | |

Sans Regular has an x-height 36 units (7.2 %) taller than Weft's
nominal x-height (500) and a cap height 57 units (8.3 %) taller (745
against 688). The ratios x/cap are near (0.719 against 0.727). Weft
strokes extend 42 units above and below the nominal lines (square caps),
so the visible Weft tops (542 for o, 730 for H) are near the Sans tops
(548, 745). See `proofs/sans/sans-weft-shared-line.png`.

For 0.2: to match Weft's nominal metrics, scale Sans by 688/745 = 0.923
(caps) or 500/536 = 0.933 (x-height), or keep the Sans proportions and
set the Weft size per font in CSS (size-adjust). 0.1 does not scale or
redraw outlines.

## Remaining WARNs (with reasons)

| Check | Files | Reason |
| --- | --- | --- |
| `typoascender_exceeds_Agrave` | all 30 TTF, OTF, VF | Intended. The typo ascender is 906 for the shared line with Weft. Accented capitals are taller (999 to 1019). Win metrics are not changed, so no clipping. |
| `unreachable_glyphs` | all 30 | Upstream glyphs that no cmap or feature reaches: `dotlessi.wide`, `registered.alt` (both styles), `igravecyr.loclBGR` (upright). Not removed in 0.1; keep the fork close to upstream. |
| `contour_count` | VF (2), OTF (10) | Upstream design. `infinity` has 4 contours and U+2B10 has 2; in OTF, overlap removal gives 2 contours for ỡ, ợ (uni1EDF, uni1EE1) in some weights. Upstream has the same WARN. |
| `name/family_and_style_max_length` (nameid6-too-long) | 4 TTF + 4 OTF | PostScript names such as `MachineMadeSans-ExtraLightItalic` (32 characters) are longer than 27. The family prefix `MachineMadeSans` is fixed. Upstream has the same WARN. |
| `name/family_and_style_max_length` (instance-too-long) | italic VF | FAIL changed to WARN in `sans/fontspector.toml`. "machine-made Sans ExtraLight Italic" (35), "SemiBold Italic" (33), "ExtraBold Italic" (34) are longer than 32 characters. Reported risk: accent shaping in some Microsoft Word versions. The family name is fixed by the brief. Upstream has the same FAIL ("Plus Jakarta Sans ExtraBold Italic"). |
| `mandatory_avar_table` | VF (2) | Linear wght axis, as upstream. No avar needed. |
| `suspicious_sidebearings` | upright VF | U+2B10 right sidebearing changes much between weights. Upstream design; upstream has the same WARN. |

## Decisions

- Glyphs with a sharp and a straight alternate (a, j, r, y and their
  accented forms, 46 per style): straight (Lurus) is the default, sharp
  (Lancip) is in ss02.
- The f ligatures (fi, fl, ff, ffi, ffl) have the round shapes, so liga
  applies only after ss01. Default text has no f ligature.
- Composites that use a changed letter (Cyrillic look-alikes, Bulgarian
  forms, digraphs) follow the new defaults, so mixed Latin and Cyrillic
  text has one style.
- Reserved Font Name "machine-made" added (OFL FAQ 5.10). See
  `README.md`.

## Open risks

- **OFL FAQ source.** openfontlicense.org is blocked on the build
  machine. The RFN decision uses OFL FAQ 1.1-update7 (November 2023)
  from SIL's own copy in `silnrsi/font-andika`. Confirm entry 5.10 on
  the web page before release.
- **Line height with accented capitals** (see "Line metrics").
- **Italic Cyrillic.** Upstream added Cyrillic to the upright source
  only (commit 5854bde, 2023-08), after its last font build. So the
  upright fonts cover 819 code points (98 Cyrillic) and the italic
  fonts 721 (no Cyrillic). The upstream binary fonts in the upstream
  repository have no Cyrillic at all. The Cyrillic is new in a release
  and has had less use than the Latin.
- **Style names in Word.** The italic VF instance names are longer than
  32 characters (see WARNs).
- **Hinting.** Static TTF are autohinted by ttfautohint (gftools
  default). The variable fonts and OTF are not hinted. Upstream is the
  same.
- **CI not run yet.** `sans.yml` installs `libraqm0` for shaped proofs
  and fetches upstream at the pinned commit with git. It has not run on
  GitHub yet.
- **Weft proof.** The shared line proof uses
  `fonts/weft/ttf/MachineMadeWeft-Regular.ttf` (Weft 0.1).
