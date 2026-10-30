# Weft status

Notes for the integration session. The root `STATUS.md` has one line
about Weft; the details are here.

| Field | Value |
| --- | --- |
| Family | machine-made Weft |
| Version | 0.2 (font version 0.200) |
| Branch | `weft/v0.2` |
| Stage | Weft 0.2 built: look-alikes, Latin Extended-A, combining marks, box drawing, arrows, hinted statics |
| Gate now | Founder reviews the proofs by eye; then PR, merge, release `weft-v0.2.0` |
| Next | Width axis, Thread style, small caps |
| Last local run | 2026-10-28: tests, build, byte-identical rebuild, interpolation, Fontspector, OCR gate, site build all green |
| Last green CI | `weft.yml` runs on pull requests and on main only; no run on the branch yet |

## Proven (local run, 2026-10-28)

- 1749 pytest tests pass.
- Two builds give the same bytes (hinted static TTFs included).
- `fonttools varLib.interpolatable`: no problems on the designspace, on
  the 12 master UFOs and on the compiled variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the variable
  font, the 9 static TTF and the 9 static OTF.
- OCR gate (Tesseract 5.3.4, eng): passes. See `proofs/weft/readability.json`.

  | | FRAG 0 | FRAG 8 | FRAG 15 | DejaVu Sans Mono |
  | --- | --- | --- | --- | --- |
  | Look-alike CER, Weft 0.1 | 0.121 | 0.128 | 0.122 | 0.0875 |
  | Look-alike CER, Weft 0.2 | 0.071 | 0.079 | 0.078 | 0.0875 |
  | Paragraph CER, Weft 0.2 | 0.0034 | 0.0011 | 0.0023 | 0.0046 |

  The look-alike set now has q (g9q), so the numbers differ from the
  0.1 report (0.124 against 0.075). Both rows above use the 0.2 test.
  The look-alike margin is 0: Weft must not read worse than DejaVu.
- shaperglot 1.2.2 (not in CI): every mandatory orthography check
  passes for Polish, Czech, Slovak, Hungarian, Romanian, Turkish,
  Croatian, Slovenian, Latvian, Lithuanian, Estonian, Maltese,
  Esperanto, Bosnian, Albanian, Catalan, Icelandic, German, French,
  Danish and Norwegian. Only the small-caps checks are skipped (no
  `smcp`).
- Sketch comparison (sketch 0.1 renderer against the Regular TTF,
  `proofs/weft/weft-sketch-compare.png`): coverage IoU 0.940. The
  differences are the deliberate changes below.

## Deliberate deviations from sketch 0.1

| Glyph | Change | Reason |
| --- | --- | --- |
| l | Stem at x 3 (was 3.5), tail (3, 1.6) to (4.6, 0) to (6.4, 0) | OCR read l as 1. A tail to the box edge read as L. |
| I | Serifs 0.5 to 6.5 (were 1.5 to 5.5) | OCR read I as 1. |
| 1 | Flag from (0.5, 8.2), base 0.8 to 6.2 | Longer flag, more distinct from l and I. |
| 0 | Slash (5, 8) to (2, 3) (was (5, 7.8) to (2, 3.2)) | A narrower zero read no better and closed up at Bold. |
| q | Foot spur (6.5, -2.5) to (7.5, -3.5) | OCR read q as g (6 of 720 characters). |
| " | Two ' components that move apart with weight | They merged at Black. |
| « » | Two ‹ › components that move apart with weight | Too tight at Black. |

Accents above the base are scaled by 1.25 at Black (1.0 up to Regular)
and the gap to the base grows with weight. This is new in 0.2; the
sketch has no heavy accents.

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `opentype/monospace` (bad-numberOfHMetrics) | all | 17 hmtx entries (the zero-width combining marks come first). The spec recommends 3. Harmless. |
| `contour_count` | VF, some statics | The VF keeps one contour per stroke piece (on purpose). Statics: at heavy weights "½", "#" and "ß" merge or close. |
| `typoascender_exceeds_Agrave` | VF, 7 statics | Capital accents reach above the typo ascender (906). Line spacing stays at 19 units on purpose; win metrics cover all ink, so nothing clips. |
| `mandatory_avar_table` | VF | Both axes are linear on purpose. |
| `alt_caron` (decomposed-outline) | static TTF | The statics are decomposed, so the check cannot see the components. ď ľ ť Ľ use `caronvert.mark`, a vertical stroke, not an apostrophe. |

## Metrics that changed

- win ascent / descent: 1250 / 403 (0.1: 1167 / 339). Bigger accents at
  Black with FRAG 100 drift, and the comma below at Black.
- Advance (750), typo and hhea metrics (906 / -281 / 0), x-height
  (500), cap height (688), underline (-150 / 84) and the axes do not
  change.

## Open

- ½ ¼ ¾: the fraction slash touches the small figures from Regular up
  (one contour in the statics). Needs narrower small figures.
- "#" merges at Black (as in 0.1).
- Small caps (`smcp`): not drawn. shaperglot skips its small-caps
  checks.
- Combining marks use the lowercase accent shapes, also on capitals
  (precomposed capitals use the flatter `.case` accents).
- FRAG 51 to 100 is for titles: pieces drop out and words are not
  readable (OCR CER 0.47 at FRAG 100). This is by design.
- The drift lock (`loom/drift_lock.json`) must be made again
  (`python tools/relock.py`) after any change to the strokes, the
  accent scale or `loom/pieces.py`. A test checks a sample of glyphs.
- The machine-made.github.io site still has the Weft 0.1 subset. Its
  tracking does not need a change (advance unchanged). Running its
  `fonts.py` on 0.2 gives a 24.6 KB `mm-weft.woff2` (was 23.7 KB) with
  the new l, I, 1, 0, q and heavier-weight accent spacing.
- Name: see `BRIEF.md` (near match "Wefts", web search only).
