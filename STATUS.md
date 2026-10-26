# STATUS

| Field | Value |
| --- | --- |
| Repo | machine-made/type |
| House | machine-made |
| Line | identity |
| Visibility | private |
| Stage | Weft phase 1 built (one master: Regular, wght 400, FRAG 0, Solid; a-z, A-Z, 0-9) |
| Gate now | Founder reviews the phase 1 proof by eye (`proofs/weft-phase1-proof.png`, `proofs/weft-phase1-vs-sketch.png`) and confirms the licence split |
| Next task | Weft phase 2: wght axis (masters at 100 and 900 with compatible outlines), variable TTF, interpolation checks |
| Blocked by | founder proof review |
| Last green CI | none yet (workflow added on branch `weft/phase-1`; first run is on the PR). Local run of the same steps on 2026-10-26: green |
| Owner model | to assign |

## Proven

- Generator turns the sketch 0.1 stroke table into closed outlines:
  square caps, miter joins at limit 2.4, bevel beyond, overlaps removed
  with skia-pathops.
- UFO master at 1000 UPM (1 design unit = 62.5 units), 64 glyphs, advance
  750 for every glyph, correct unicode values.
- 226 pytest tests pass: every sketch glyph builds (88), phase 1 contours
  closed and not empty, constant advance, no overlaps remain, cap, join,
  dot and stem rules.
- fontmake builds static TTF and OTF.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR, 2 WARN per font.
- Compiled font matches the sketch renderer: at 320 px, no difference
  survives a 5 x 5 px erosion of the ink XOR (only edge anti-aliasing
  differs). Coverage IoU 0.969 at 320 px, 0.913 at 64 px.

## Open risks

- Name: "Wefts" (Overlap Type, 2026) is a near match with a weaving
  concept. No exact "Weft" typeface or font trademark found. Web search
  only, not a register search. See `BRIEF.md`.
- Phase 2 needs compatible outlines across weights. The current path
  (union of segment shapes, then overlap removal) gives different point
  counts per weight, so it cannot feed interpolation as is. Plan: build
  outlines per master with a fixed contour topology, or ship overlapping
  contours in the masters and remove overlaps only at export.
- FRAG cuts and drift use a seeded random generator in the sketch. A
  variable font needs fixed, interpolating masters; the random stages
  need a new design (phase 4).
- Joins sharper than 49.2 degrees bevel (miter limit 2.4). In phase 1
  this hits 7 joins: 'w' (27.1), 'M' (31.1, two), 'N' (32.5, two), 'W'
  (21.0) and '4' (35.2). The sketch canvas does the same, and the proof
  overlay matches, but the founder should judge these blunt tips by eye.
- Fontspector `fontdata_namecheck` cannot run on the build machine (no
  network to fontdata.com). It may run in GitHub Actions.
- Licence split (OFL fonts, Apache-2.0 code) waits for founder approval.
