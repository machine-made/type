# machine-made type site 0.1.0

The specimen and download site for machine-made Weft 0.1 and
machine-made Sans 0.1. Live at <https://machine-made.github.io/type/>.

This release attaches the built site as a zip file. The live site is
deployed from `main` by the `site` workflow; this zip is a copy of the
same build for the tag.

## What is on the site

- Home: the two families, with links to the releases.
- Weft: a playground with the `wght` and `FRAG` axes, FRAG rows from
  clean to broken, the glyph map, look-alike pairs and the OCR
  readability table from `proofs/weft/readability.json`.
- Sans: specimen, weight waterfall (upright and italic), the default
  straight forms and the sharp forms (ss02) as a switch, and the swirl
  set.
- Download: install steps and `@font-face` CSS for both families.

The site serves the committed WOFF2 files of the 0.1 fonts. It has no
analytics, no cookies and no third-party scripts.

## Licence

Site code: Apache-2.0. Fonts: SIL Open Font License 1.1, Reserved Font
Name "machine-made". See `LICENSING.md` in the repository.
