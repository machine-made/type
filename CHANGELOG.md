# Changelog

Each family keeps its own changelog:

- machine-made Weft: [`weft/CHANGELOG.md`](weft/CHANGELOG.md)
- machine-made Sans: [`sans/CHANGELOG.md`](sans/CHANGELOG.md)
- machine-made Heddle: [`heddle/CHANGELOG.md`](heddle/CHANGELOG.md)
- machine-made Warp: [`warp/CHANGELOG.md`](warp/CHANGELOG.md)

Release tags: `weft-vX.Y.Z`, `sans-vX.Y.Z`, `heddle-vX.Y.Z`, `warp-vX.Y.Z`, `site-vX.Y.Z`.

## 2026-10-28: Sans 0.2

- machine-made Sans 0.2.0 (font version 0.200): italic Cyrillic, OTF
  hinting, Latin Extended-A, kerning fixes. See `sans/CHANGELOG.md`.

## 2026-10-28: Heddle 0.2

- machine-made Heddle 0.2.0 (font version 0.200): Latin Extended-A,
  Ș ș Ț ț, new symbols and fractions, lighter marks, open counters at
  Black, masters at wdth 85, hinted statics. See `heddle/CHANGELOG.md`.
- Site: the Heddle page and the download page link
  `heddle-v0.2.0`.

## 2026-10-28: Weft 0.2

- machine-made Weft 0.2.0 (font version 0.200): look-alikes, Latin
  Extended-A, combining marks, box drawing, arrows, hinted static TTF.
  See `weft/CHANGELOG.md`. Site: the Weft download links point to
  `weft-v0.2.0`.

## 2026-10-27: Warp 0.1

- machine-made Warp 0.1.0 (font version 0.100): machine-made Warp
  Regular, Italic, Bold, Bold Italic and machine-made Warp Display
  Regular, Italic. See `warp/CHANGELOG.md`.
- Add `.github/workflows/warp.yml` (tests, build, byte check, fidelity
  report, OCR gate, Fontspector, proofs) and a `warp` job in
  `release.yml` for `warp-v*` tags. `package_release.sh` packs Warp.
- Site: add the Warp page (style switch, a paragraph from a paper,
  Greek, figures and small caps, equations, glyph map), Warp on the
  home and download pages, and Warp in the nav.

## 2026-10-27: Heddle 0.1

- machine-made Heddle 0.1.0 (font version 0.100). See
  `heddle/CHANGELOG.md`.
  Sketched as "Shuttle"; renamed before the release (name clash).
- Add `.github/workflows/heddle.yml` (tests, build, byte check,
  interpolation, drift report, Fontspector, proofs) and a `heddle` job
  in `release.yml` for `heddle-v*` tags. `package_release.sh` packs
  Heddle.
- Site: add the Heddle page (playground with weight and width, width
  rows, weight rows, glyph map), Heddle on the home and download
  pages, and Heddle in the nav.

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
