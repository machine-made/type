# machine-made Sans changelog

## 0.200 (0.2), 2026-10-28

- Add the Cyrillic to the italic: the 98 code points of the upright,
  made from the upright Cyrillic slanted by 8 degrees about half the
  x-height, as upstream made its Latin italic (`scripts/extend.py`).
  The Bulgarian forms (locl BGR, ss04) work in the italic too.
- Add ſ (U+017F) and ŉ (U+0149). Latin Extended-A is complete.
- Hint the static OTF with otfautohint (afdko 5.0.1). Give the upright
  source the stem values of the italic. Subroutinize the hinted CFF
  again with cffsubr. The variable fonts stay unhinted.
- Shorten three instance names of the italic variable font (XLight
  Italic, SemiBd Italic, XBold Italic), so that family and style fit in
  32 characters. STAT keeps the full names. Remove the Fontspector
  override for this.
- Kerning: 47 upright and 31 italic exceptions so that no pair in the
  audit list touches (accented i after T V W Y F f P, Ľ before T V W Y,
  Cyrillic ї). Cyrillic look-alikes kern with their Latin groups.
- Add `scripts/kernaudit.py` (pair audit), `scripts/readability.py`
  (OCR gate), new tests and proofs (italic Cyrillic, coverage, kerning,
  OTF hinting).
- Version 0.200.

## 0.100 (0.1), 2026-10-26

First version. A modified version of Plus Jakarta Sans 2.071 by Gumpita
Rahayu, Tokotype (commit 18d1cd2f7ea10481919d2f05c1f7064b7307fc26).

- Add the upstream Glyphs sources, unchanged, as the first commit.
- Rename the family to "machine-made Sans". Set the file and PostScript
  prefix `MachineMadeSans`, version 0.100 and vendor `NONE`.
- Keep the upstream copyright line. Add "Copyright 2026 The
  machine-made Sans Project Authors". Add the Reserved Font Name
  "machine-made" (OFL FAQ 5.10).
- Make the Lurus (straight) alternates the default forms: a, j, r, y,
  p, q and their accented forms, 48 glyphs per style.
- Keep the old default forms of these glyphs in ss01 "Round forms
  (original defaults)". Put all Lancip (sharp) forms in ss02 "Lancip:
  sharp forms" (175 glyphs per style). Keep Lingkar in ss03 and make it
  work from all forms. Give each set a name in the font.
- Keep the upstream f ligatures in default text. Put liga after the
  sets, so ss02 gives the sharp f, i and l with no ligature.
- Change the widths, offsets and anchors of composite glyphs that use a
  changed letter (Cyrillic а р у ў ј, digraphs).
- Release branch: before the release, the founder changed the defaults
  from "Lurus and Lancip" to "Lurus only, Lancip in ss02". The change
  is in `scripts/fork.py`.
- Set the typo and hhea line metrics to 906/−281/0, the same as Weft 0.1.
  Keep win metrics 1296/356.
- Repair upstream source errors: bad escapes in the ss04 feature, the
  unused @noexport class, scale (0,0) in upDownArrow, the upright Bold
  instance not marked bold, a second unused Regular instance.
- Add PostScript names without a hyphen, the WWS bit, STAT in the
  static fonts, and remove the TrueType `prep` table from the OTF fonts.
- Build two variable fonts (wght 200 to 800), 14 TTF, 14 OTF and WOFF2
  of the variable fonts. The build is repeatable.
- Add the fork script, build, checks (Fontspector universal profile,
  varLib.interpolatable), tests, proof sheets and the CI workflow.
