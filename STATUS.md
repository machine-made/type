# STATUS

| Field | Value |
| --- | --- |
| Repo | machine-made/type |
| House | machine-made |
| Line | identity |
| Visibility | public after the 0.1 release (founder approved) |
| Stage | released 0.1: machine-made Weft 0.1.0, machine-made Sans 0.1.0, specimen site 0.1.0. machine-made Shuttle 0.1 built on `shuttle/v0.1` |
| Gate now | Shuttle: Jac reviews and merges `shuttle/v0.1`; the founder reviews the proofs and decides on the name (an exact match exists, see `shuttle/BRIEF.md`); then the tags `shuttle-v0.1.0` and a new `site-v*` |
| Next task | Shuttle 0.2 (see `shuttle/STATUS.md`). Weft: polish (look-alikes l/1, I/1, O/0; heavy accented capitals), width axis, Thread style. Sans 0.2: redraw in the style of Weft and match Weft's x-height (see `sans/STATUS.md`). npm packages for both families. |
| Blocked by | none |
| Last green CI | none yet (first runs are on the release PR). Local end-to-end run of all steps on 2026-10-26: green |
| Owner model | to assign |

Family notes: `weft/STATUS.md`, `sans/STATUS.md`,
`shuttle/STATUS.md`. Changes: `CHANGELOG.md`.

## Proven (local run, 2026-10-27)

### Shuttle 0.1

- 334 pytest tests pass (one runs the sketch engine in node and
  compares the advances at all 12 masters).
- The build is byte-reproducible: a fresh build equals the committed
  `fonts/shuttle/`.
- `fonttools varLib.interpolatable`: no problems on the designspace,
  the 12 master UFOs and the variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the
  variable font and 11 static TTF (accepted WARNs in
  `shuttle/STATUS.md`).
- The site builds with the Shuttle page; no console errors, no failed
  requests, no horizontal scroll at 360 px.

## Proven (local run, 2026-10-26)

### Weft 0.1

- 948 pytest tests pass.
- The build is byte-reproducible: a fresh build equals the committed
  `fonts/weft/`.
- `fonttools varLib.interpolatable`: no problems on the designspace,
  the 12 master UFOs and the variable font.
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the
  variable font, 9 static TTF and 9 static OTF (accepted WARNs in
  `weft/STATUS.md`).
- OCR gate (Tesseract 5.3.4): FRAG 0 CER 0.23 %, FRAG 15 0.11 %,
  DejaVu Sans Mono 0.46 %. Gate passes.

### Sans 0.1

- Default forms: straight (Lurus) a j p q r y. Sharp (Lancip) forms in
  ss02 (founder decision on the release branch).
- Typo and hhea line metrics 906/−281/0, the same as Weft 0.1 (changed
  from the phase 1 value 875 on the release branch).
- The build is byte-reproducible (fixed `SOURCE_DATE_EPOCH`).
- 117 pytest tests pass, 1 skips (no italic Cyrillic, as upstream).
- Fontspector 1.9.0, universal profile: 0 FAIL, 0 ERROR on the 2
  variable fonts, 14 TTF, 14 OTF and 2 WOFF2.
- `varLib.interpolatable` on the master UFOs: no problems.

### Site 0.1

- `site/build.py` uses only the committed WOFF2 files and stops when one
  is missing. No stand-in fonts remain.
- The Weft page: the FRAG slider changes the real variable font (0 to
  100) and the readability table shows 4 FRAG rows from
  `proofs/weft/readability.json`. The Sans page shows ss02 as a switch.
  No console errors, no failed requests, no horizontal scroll at 360 px.

### Release workflow

- `.github/workflows/release.yml` makes the GitHub releases from the
  tags. Every action is pinned to a full commit SHA. The workflow has
  not run on GitHub yet.

## Open risks

- **CI has not run on GitHub.** `weft.yml`, `sans.yml`, `site.yml` and
  `release.yml` ran only as local copies of their steps. The first run
  is on the PR (checks) and on the tags (release).
- **Reproducibility across machines.** The release workflow fails when
  a rebuild differs from the committed fonts. Both builds are
  byte-identical on the build machine with the pinned packages. Ubuntu
  runners can differ (for example ttfautohint for the Sans static TTF).
  If the Sans byte check fails on the runner, the workflow says so; the
  fallback is the structural check `sans/scripts/compare_builds.py`.
- **Weft look-alikes.** OCR confuses l and I with 1, and O with 0, more
  than in DejaVu Sans Mono (CER 0.12 against 0.075). The gate stops a
  regression; it does not prove parity.
- **Line height with accented capitals.** Both families use an ascender
  of 906. Accented capitals go above it (Sans Á at about 1000). Win
  metrics cover all ink, so nothing clips, but tight line spacing can
  make lines touch.
- **Sans italic Cyrillic.** Upstream has Cyrillic in the upright only.
- **Sans style names in Word.** Three italic VF instance names are
  longer than 32 characters.
- **OFL FAQ 5.10** (adding a Reserved Font Name to a derivative) was
  read from SIL's copy in `silnrsi/font-andika`; openfontlicense.org
  was blocked on the build machine. Confirm on the web page.
- **Name.** "Wefts" (Overlap Type, 2026) is a near match. Web search
  only, not a register search. See `weft/BRIEF.md`.
- **Shuttle name.** "Shuttle" by Volcano Type (MyFonts, 2006) is an
  exact match; "Shuttleblock" (Fort Foundry, 2024) is close. See
  `shuttle/BRIEF.md`.
- **Shuttle CI has not run on GitHub.** `shuttle.yml` and the
  `shuttle` release job ran only as local copies of their steps
  (Python 3.13 locally, 3.14 in CI).
- **Fontspector network checks** (`fontdata_namecheck` and others) do
  not run (`--skip-network`).
