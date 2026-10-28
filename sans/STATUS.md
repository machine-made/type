# machine-made Sans: STATUS

| Field | Value |
| --- | --- |
| Family | machine-made Sans |
| Version | 0.200 (release 0.2) |
| Branch | `sans/v0.2` |
| Stage | 0.2 built and checked. Italic Cyrillic, OTF hinting, Latin Extended-A, kerning fixes, short italic instance names. |
| Gate now | Review of the branch and the proofs in `proofs/sans/`; then the PR. |
| Next | 0.3: see "Open" below. |
| Upstream | tokotype/PlusJakartaSans at `18d1cd2f7ea10481919d2f05c1f7064b7307fc26` |
| Last green CI | 0.1 on main. 0.2: see the branch run. Local run of the same steps on 2026-10-28: green. |

## Proven (local run, 2026-10-28)

- Build: `sans/scripts/build.sh` makes 2 variable fonts (wght 200 to
  800), 14 TTF, 14 OTF and 2 WOFF2. Two builds give the same bytes
  (with ttfautohint and otfautohint in the build).
- Fontspector 1.9.0, universal profile, `--skip-network`: **0 FAIL,
  0 ERROR, 0 FATAL** in all four runs. No overrides in
  `fontspector.toml` (0.1 had one).

  | Files | PASS | WARN | FAIL | ERROR | SKIP | INFO |
  | --- | --- | --- | --- | --- | --- | --- |
  | variable (2) | 182 | 9 | 0 | 0 | 41 | 5 |
  | ttf (14) | 1002 | 46 | 0 | 0 | 499 | 34 |
  | otf (14) | 890 | 46 | 0 | 0 | 625 | 20 |
  | webfonts (2) | 10 | 0 | 0 | 0 | 3 | 0 |

- fontTools `varLib.interpolatable` on the master UFOs of both sources:
  no problems.
- pytest: 249 tests pass (`sans/tests`). New in 0.2
  (`tests/test_v02.py`): version, Latin Extended-A and the Central
  European alphabets in every file, italic Cyrillic equal to the
  upright set, each italic Cyrillic outline equal to the slanted
  upright outline in the sources, long s, instance names of 32
  characters or fewer, STAT names, OTF and TTF hints, no overlapping
  pair (11,610 pairs, 14 static fonts and 8 variable instances between
  the masters), Cyrillic look-alikes kern like Latin.
- OCR readability gate (`scripts/readability.py`, Tesseract 5.3.4,
  `proofs/sans/readability.json`): no regression.

  | Style | CER 0.1 | CER 0.2 | DejaVu Sans | Gate |
  | --- | --- | --- | --- | --- |
  | Regular | 0.0350 | 0.0350 | 0.0073 | pass |
  | Italic | 0.0439 | 0.0439 | 0.0106 | pass |

  Sans reads worse than DejaVu Sans in Tesseract: it misses many of the
  narrow word spaces (170 units) and reads Il1 and O0 as other
  characters. The gate is "no worse than 0.1"; it does not prove
  parity.
- Kerning audit (`scripts/kernaudit.py`,
  `proofs/sans/kerning-audit.json`): overlapping pairs in the 14 static
  fonts, same 11,610-pair list: 0.1 has 326, 0.2 has 0.
- Site check (site/build.py, then Chromium at 360 and 1366 px): no
  external requests, no horizontal scroll, both Sans fonts load.

## Done in 0.2

1. **Hinting.**
   - Static TTF: ttfautohint, as in 0.1 (gftools default).
   - Static OTF: otfautohint from afdko 5.0.1 (`autohintOTF: true` in
     `sources/config.yaml`). afdko has no Python 3.14 wheel and its
     source build needs gitlab.gnome.org, so otfautohint runs in its
     own Python 3.13 environment (`requirements-otf.txt`); CI does the
     same. The upright source had no stem values, so otfautohint would
     have run without stems; `fork.py` copies the stems of the italic
     source (a horizontal slant keeps horizontal widths, so the values
     are the same). otfautohint writes fewer CFF subroutines, so
     `finish.py` subroutinizes the OTF again with cffsubr 0.4.0. Proof:
     `sans-hinting-otf.png`.
   - Variable fonts: not hinted (decision, see "Decisions").
2. **Style names in Word.** The italic variable font now names its
   instances "XLight Italic", "SemiBd Italic" and "XBold Italic"
   (`finish.py`), so "machine-made Sans" plus the style name fits in 32
   characters. STAT still names every axis value in full (ExtraLight,
   SemiBold, ExtraBold, Italic). The static fonts and the upright
   variable font keep the full names; they were within the limit.
3. **Italic Cyrillic.** The italic has the 98 Cyrillic code points of
   the upright (821 code points in each style now). Method: the
   upstream Latin italic is the upright slanted by 8 degrees about half
   the x-height of each master, with the same advance widths (straight
   letters such as H, E, n match to under 1 unit; round letters have an
   extra optical correction of up to about 30 units in the node
   positions). `scripts/extend.py` makes the italic Cyrillic the same
   way: outlines and anchors slanted, components kept (so а е о р с у х
   і ј ѕ use the italic Latin glyphs), component offsets slanted, and
   mirrored components (Я, Э, Є, є) made outlines first. Bulgarian
   forms (locl BGR and ss04) are in the italic too. Proof:
   `sans-italic-cyrillic.png` (the Latin check strip gives a mean pixel
   difference of 8.8 %, against about 4 % noise for a pure slant).
4. **Language coverage.** Latin Extended-A (U+0100 to U+017F) and Șș Țț
   are complete. New: ſ (U+017F, the upstream f without its crossbar)
   and ŉ (U+0149, quoteright and n as components). Proof:
   `sans-coverage.png`.
5. **Kerning.** Audit with `scripts/kernaudit.py` over 11,610 pairs
   (lowercase, uppercase, figures, punctuation, accented pairs, the
   vertical caron letters ď ľ ť Ľ, Cyrillic). Fixes in `fork.py`:
   - 47 upright and 31 italic kerning exceptions (`KERN_FIXES`), each
     the smallest change that leaves 20 units between the inks in every
     master: accented i (ì î ĩ ĭ ȉ ȋ) after T V W Y F f P j ď ľ ť; Ľ
     before T V W X Y; Cyrillic ї after letters with a high left
     side; Y ř in the italic.
   - Cyrillic look-alikes take the kerning groups of their Latin base
     (А = A, Т = T, о = o and so on), so Cyrillic text now kerns.
   - Tó Vá Yō Wé Ťá did not touch and do not change.
   - The mean-gap measure finds no pair that is clearly too loose or
     tight beyond these; no other values changed.
   Proof: `sans-kerning.png`.
6. **OFL FAQ.** Confirmed on the web on 2026-10-28: the page
   <https://openfontlicense.org/ofl-reserved-font-names/> has the
   question "Can I add other Reserved Font Names when making a
   derivative font?" with the answer "Yes. List your additional
   Reserved Font Names after your additional copyright statement" and
   "Be sure you do not remove any existing RFNs but only add your
   own." This is the text of FAQ entry 5.10. The FAQ page itself
   (<https://openfontlicense.org/ofl-faq/>) could not be fetched from
   the build machine. The decision in `README.md` stands.
7. **x-height.** Outlines are not scaled (decision). To set Sans and
   Weft with the same nominal x-height in CSS, use `size-adjust` on the
   Sans `@font-face`:

   | Match | Weft | Sans | `size-adjust` |
   | --- | --- | --- | --- |
   | Nominal x-height (OS/2) | 500 | 536 | **93.3%** |
   | Cap height | 688 | 745 | 92.3% |
   | Visible top of o (with Weft's stroke) | 542 | 548 | 98.9% |

   The visible tops are near (98.9 %), so the machine-made site keeps
   100 % (no `size-adjust`). Use 93.3 % only where Sans must match
   Weft's nominal grid.
8. **Site.** machine-made.github.io uses the upright variable font,
   cut to Latin-1 (`fonts.py`). Compared with 0.1 at wght 200 to 800:
   no advance width, side bearing, word space (170), cmap name or
   line metric changes. GPOS changes in 9 Latin-1 pairs only (Fì Fî
   Tì Vì Wì Yì fì ¥ì Ýì, positive kerning so the accent does not
   touch). The site's `word-spacing: 0.05em` and tracking need no
   change. Regenerate `mm-sans.woff2` with `fonts.py` when the site
   takes 0.2.

## Line metrics

machine-made Weft 0.1: 1000 UPM, ascender 719, descender −219, typo and
hhea 906/−281/0. Sans uses the same typo and hhea values.

| Metric | Plus Jakarta Sans 2.071 | machine-made Sans 0.2 |
| --- | --- | --- |
| UPM | 1000 | 1000 |
| typoAscender / typoDescender / typoLineGap | fonts: 1038 / −222 / 0 | **906 / −281 / 0** |
| hheaAscender / hheaDescender / hheaLineGap | 1038 / −222 / 0 | **906 / −281 / 0** |
| winAscent / winDescent | 1296 / 356 | 1296 / 356 (no change) |
| USE_TYPO_METRICS | on | on |
| Default line height (typo) | 1.260 em | **1.187 em**, the same as Weft |

The win values must be at least the font bounding box (yMax 1294,
yMin −263 in ExtraBold). Accents on capitals go above the typo
ascender (Á 999 to 1019, Ấ 1049 to 1069). Set a CSS line-height of 1.3
or more for text with many accented capitals.

## Accepted WARNs (with reasons)

| Check | Files | Reason |
| --- | --- | --- |
| `typoascender_exceeds_Agrave` | all 30 TTF, OTF, VF | Intended. The typo ascender is 906 for the shared line with Weft. Win metrics are not changed, so no clipping. |
| `unreachable_glyphs` | all 30 | Upstream glyphs that no cmap or feature reaches: `dotlessi.wide`, `registered.alt`, `igravecyr.loclBGR` (now in both styles). Kept to stay close to upstream. |
| `contour_count` | VF (2), TTF (14), OTF (14) | Upstream design: `infinity` (4 contours), U+2B10 (2), the unencoded sharp alternates `uni1E21.ss02` and `uni1ECB.ss02`; in OTF, ỡ ợ after overlap removal. No Cyrillic or new glyph is listed. |
| `name/family_and_style_max_length` (nameid6-too-long) | 4 TTF + 4 OTF | PostScript names such as `MachineMadeSans-ExtraLightItalic` are longer than 27 characters. The prefix `MachineMadeSans` is fixed. |
| `mandatory_avar_table` | VF (2) | Linear wght axis, as upstream. |
| `suspicious_sidebearings` | upright VF | U+2B10 right side bearing; upstream design. |

## Decisions

- Founder decision (2026-10-26): only the straight (Lurus) forms are
  defaults; all sharp (Lancip) forms are in ss02.
- The f ligatures work in default text; liga comes after the sets.
- Composites that use a changed letter follow the new defaults.
- Reserved Font Name "machine-made" (OFL FAQ 5.10, confirmed above).
- 0.2: **variable fonts stay unhinted.** ttfautohint does not read
  `gvar`; the experimental "ttfautohint-vf" fork is not maintained, has
  no pinned release on PyPI, and Google Fonts reports that it "didn't
  work well". gftools gives the variable fonts a `gasp` table and a
  `prep` table for smooth rendering without hints, as for Google Fonts
  variable fonts. Revisit when a maintained variable autohinter
  exists.
- 0.2: **italic Cyrillic is a sloped roman.** The upstream Latin italic
  is a sloped roman (n, a, u keep their upright forms), so the
  Cyrillic follows it: и п т г д keep their upright forms. Cursive
  forms (и as u, п as n, т as m, д as g) would have no Latin model in
  this italic. They exist as the Bulgarian forms, which the italic now
  has too (locl BGR and ss04).
- 0.2: **no outline scaling for x-height** (see item 7).
- 0.2: short italic instance names XLight, SemiBd, XBold (Adobe-style
  abbreviations) only where the 32-character limit needs them.

## Deliberate deviations in the proofs

- `sans-italic-cyrillic.png`, check strip: round letters (o, e, s)
  differ from a pure slant by 11 to 17 % of their pixels. That is the
  upstream optical correction of the Latin italic; the italic Cyrillic
  has no such correction (it is a pure slant). Visible only at large
  sizes as slightly thinner diagonal parts of bowls (С-like and
  О-like Cyrillic letters use the corrected Latin glyphs, so most
  rounds are corrected).
- `sans-kerning.png`: the "before" italic Cyrillic row shows missing
  glyphs: 0.1 had no italic Cyrillic.

## Open (for 0.3)

- Redraw the shapes in the style of Weft (the earlier plan for 0.2 is
  moved to 0.3).
- Optical correction of round italic Cyrillic letters (б в з э ю я ф),
  as upstream did for the Latin.
- Word space: Tesseract misses many spaces at 10 px. A wider space
  would change the site's tuned `word-spacing`.
- Look-alikes Il1 and O0 for code and serial numbers.
- Line height with accented capitals (see "Line metrics").
- Variable font hinting (see "Decisions").
- The italic Cyrillic has had less use than the Latin; it is new in a
  release.
