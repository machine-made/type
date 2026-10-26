# machine-made Weft 0.1

Weft is a grid-built monospace made by code. Every shape comes from a
table of centre-line strokes on a 12-unit grid: octagonal bowls cut at
45 degrees, square shoulders, square caps. A second axis, FRAG, takes
the letters apart in fixed steps, from clean text to broken marks.

## What is in 0.1

**Variable font** `fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf`
(and `.woff2` in `fonts/weft/webfonts/`):

| Axis | Tag | Range | Default | Named values |
| --- | --- | --- | --- | --- |
| Weight | `wght` | 100 to 900 | 400 | Thin 100, ExtraLight 200, Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900 |
| Fragmentation | `FRAG` | 0 to 100 | 0 | Clean 0, Notched 15, Cut 50, Broken 100 |

FRAG stages:

| FRAG | Stage | Use |
| --- | --- | --- |
| 0 | Clean strokes | Body text |
| 1 to 15 | Ink-trap notches at corners and joins | Body text |
| 16 to 50 | Cuts across strokes, always narrower than the stroke | Headings |
| 51 to 100 | Pieces drift, shrink and drop out | Titles and marks |

FRAG is a fixed design, not randomness: the same value gives the same
letters every time.

**Static fonts** at FRAG 0, nine weights from Thin to Black, as TTF
(`fonts/weft/ttf/`) and OTF (`fonts/weft/otf/`). WOFF2 for Regular and
Bold in `fonts/weft/webfonts/`.

**Characters**: printable ASCII, the Latin-1 Supplement (accented
letters for most Western European languages, « » ¡ ¿ ° © ® § ¶ ½ and
others), € ‘ ’ “ ” … • and ₹. 201 characters. Every glyph has the same
advance (750 units).

## Proofs

`proofs/weft/`: character set, weight waterfall, FRAG waterfall, body
text at 16 to 24 px, look-alike pairs, and the OCR readability report
(`readability.json`).

## Checks

- Fontspector 1.9.0, universal profile: no FAIL on any file.
- fontTools `varLib.interpolatable`: no problems.
- OCR (Tesseract): body text at FRAG 0 and 15 reads as well as DejaVu
  Sans Mono (character error rate 0.2 % and 0.1 %, reference 0.5 %).

## Known limits

- Latin only: no Latin Extended-A (no Polish, Czech, Turkish letters and
  so on), no Greek or Cyrillic.
- No kerning (monospace), no OpenType features (`zero`, `tnum` are not
  needed or not in 0.1: the figures are already tabular, and zero
  already has a slash).
- No hinting. Small sizes on Windows can look soft.
- The look-alike pairs l/1, I/1 and O/0 are harder for OCR than in
  DejaVu Sans Mono. People read them well; machines less so.
- FRAG above 50 is not for text.
- Capital accents at heavy weights go above the line-spacing ascender.
  Nothing clips, but tight line spacing can make lines touch.
- No width axis and no Thread style yet.

## Licence

Fonts: SIL Open Font License 1.1, Reserved Font Name "machine-made".
Generator code: Apache-2.0.
