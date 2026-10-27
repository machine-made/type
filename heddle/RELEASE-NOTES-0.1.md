# machine-made Heddle 0.1

Heddle is a Swiss display grotesk made by code, for posters,
headlines, wordmarks and big figures. Every letter is built from four
parts: a rectangle, a superellipse ring, a parallelogram and a V. Every
opening is a level cut through one ring, which gives the horizontal
Swiss terminals. Width changes the counters, not the stems, so a
Compressed Bold and an Extended Bold have the same weight on the page.

## What is in 0.1

**Variable font** `fonts/heddle/variable/MachineMadeHeddle[wdth,wght].ttf`
(and `.woff2` in `fonts/heddle/webfonts/`):

| Axis | Tag | Range | Default | Named values |
| --- | --- | --- | --- | --- |
| Weight | `wght` | 100 to 900 | 400 | Thin 100, ExtraLight 200, Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900 |
| Width | `wdth` | 70 to 140 | 100 | Compressed 70, Condensed 85, Normal 100, Wide 120, Extended 140 |

**Static fonts** (`fonts/heddle/ttf/`): the nine weights at width 100,
Compressed Bold and Extended Bold. WOFF2 for Regular and Bold in
`fonts/heddle/webfonts/`.

**Characters**: printable ASCII, the Latin-1 letters (accented letters
for most Western European languages), ß Æ æ Ø ø Œ œ Ð ð Þ þ, curly
quotes, « » ‹ ›, … • · ¡ ¿ € ₹ © ® ° —. 182 characters. Figures are
tabular.

**Kerning**: a small class kerning for headlines (AV, To, LT, P., and
others).

## Proofs

`proofs/heddle/`: the sketch engine and the font side by side (pangram
and the 70 sketch characters at the corners of the designspace), weight
waterfall, width ladder, a grid over both axes, kerning, accents and
symbols, and the drift report (`drift.json`).

## Checks

- Fontspector 1.9.0, universal profile: no FAIL on any file.
- fontTools `varLib.interpolatable`: no problems.
- The build is byte-reproducible.

## Known limits

- Latin only: no Latin Extended-A beyond Œ œ Ÿ ı, no Greek or Cyrillic.
  No ¢ £ ¥ § ¶ ± × ÷ or fractions yet.
- A display face: tight spacing, no hinting. Not for body text.
- Between masters, at Black and widths near 85, narrow letters are up to
  35 units wider than the sketch formula.
- Accents at Black are heavy; capital accents go above the line-spacing
  ascender. Nothing clips.

## Licence

Fonts: SIL Open Font License 1.1, Reserved Font Name "machine-made".
Generator code: Apache-2.0.
