# Weft status

Notes for the integration session. The root `STATUS.md` is not changed
by the Weft sessions.

| Field | Value |
| --- | --- |
| Family | machine-made Weft |
| Version | 0.1 (font version 0.100) |
| Branch | `weft/phase-2` |
| Stage | Weft 0.1 built: variable font (wght, FRAG), 9 statics, WOFF2 |
| Gate now | Jac reviews the branch; founder reviews the proofs by eye |
| Next | Release 0.1 (Jac). Then: polish, width axis, Thread style |
| Last local run | 2026-10-26: tests, build, interpolation, Fontspector, OCR gate all green |
| Last green CI | none yet (first run is on the PR) |

## Proven (local run, 2026-10-26)

- 948 pytest tests pass.
- `fonttools varLib.interpolatable`: no problems on the designspace, on
  the 12 master UFOs and on the compiled variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the variable
  font, the 9 static TTF and the 9 static OTF.
- OCR gate (Tesseract 5.3.4, eng): passes. See `proofs/weft/readability.json`.
- The build is byte-reproducible.

## Fontspector WARNs (accepted)

| Check | Files | Reason |
| --- | --- | --- |
| `opentype/monospace` (bad-numberOfHMetrics) | all | fontTools writes 1 hmtx entry for a font where all advances are equal. The spec recommends 3. Harmless. |
| `contour_count` | VF, some statics | The VF keeps one contour per stroke piece (on purpose). Statics: at heavy weights, "«", "»", "½", '"', "“", "”", "…", "#" merge into one contour. |
| `typoascender_exceeds_Agrave` | VF, 6 statics | Capital accents reach above the typo ascender (906) from Medium up. Line spacing stays at 19 units on purpose; win metrics cover all ink, so nothing clips. |
| `mandatory_avar_table` | VF | Both axes are linear on purpose. |

## Open risks

- Look-alike OCR: Tesseract confuses Weft's l and I with 1, and O with 0,
  more than DejaVu Sans Mono (CER about 0.12 against 0.075). The gate
  margin for this test (0.06) was set after the first run. It stops a
  regression; it does not prove parity. A slashed or dotted zero and a
  different l are design questions for later.
- At wght 900, some accented capitals and the bold `«` `»` are tight.
- FRAG 51 to 100 is for titles: pieces drop out and words are not
  readable (OCR CER 0.41 at FRAG 100). This is by design.
- The drift lock (`loom/drift_lock.json`) must be made again
  (`python tools/relock.py`) after any change to the strokes or to
  `loom/pieces.py`. A test checks a sample of glyphs.
- Name: see `BRIEF.md` (near match "Wefts", web search only).
