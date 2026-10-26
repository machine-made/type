# Changelog

Each family keeps its own changelog:

- machine-made Weft: [`weft/CHANGELOG.md`](weft/CHANGELOG.md)
- machine-made Sans: [`sans/CHANGELOG.md`](sans/CHANGELOG.md)

Release tags: `weft-vX.Y.Z`, `sans-vX.Y.Z`, `site-vX.Y.Z`.

## 2026-10-26: release 0.1

- machine-made Weft 0.1.0 (font version 0.100). See `weft/CHANGELOG.md`.
- machine-made Sans 0.1.0 (font version 0.100). See `sans/CHANGELOG.md`.
- Specimen site 0.1.0 (`site/`):
  - Add the site generator `site/build.py`, the pages (home, Weft,
    Sans, download, 404) and the Pages deploy workflow `site.yml`.
  - The site uses only the committed WOFF2 files and
    `proofs/weft/readability.json`. The build stops when a file is
    missing. Remove the stand-in fonts.
  - The Weft page has a playground with the wght and FRAG axes, FRAG
    rows, the glyph map and the OCR readability table. The Sans page
    has a waterfall and the stylistic sets, with ss02 as a switch.
- Repository:
  - Merge the Weft, Sans and site branches. Track `fonts/` and
    `proofs/` without `git add -f`.
  - Remove the root `OFL.txt`. Each family has its own `OFL.txt`. Add
    `LICENSING.md`.
  - Add `.github/workflows/release.yml`: releases with attestations
    from the tags.
