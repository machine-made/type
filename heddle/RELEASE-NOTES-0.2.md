# machine-made Heddle 0.2

Heddle is a Swiss display grotesk built from four parts (rect, ring,
slant, vee) with a weight axis (100 to 900) and a width axis (70 to
140). Version 0.2 adds Central European languages and fixes the
heavy weights.

## New

- Latin Extended-A and Ș ș Ț ț: Polish, Czech, Slovak, Hungarian,
  Romanian, Turkish, Croatian, Slovenian, Latvian, Lithuanian,
  Estonian, Maltese and more.
- `¢ £ ¥ § ¶ ± × ÷ −`, `½ ¼ ¾`, and the `frac` feature for any
  fraction (type 3/16 and turn on `frac`).
- Kerning for lowercase pairs and for figures before a period.
- Hinted static fonts (ttfautohint).

## Better

- Marks are lighter and smaller. ï and Ï no longer get wider at Black.
- Small rings and the hooks of a, f, j, s and t stay open at Black.
- ß, ð, @, ©, ® and % are redrawn.
- The variable font follows the generator more closely near width 85
  (four more masters).

## Files

- `MachineMadeHeddle[wdth,wght].ttf`: the variable font.
- 11 static TTF: Thin to Black at Normal width, Compressed Bold,
  Extended Bold.
- WOFF2: the variable font, Regular and Bold.

Free under the SIL Open Font License 1.1, Reserved Font Name
"machine-made".
