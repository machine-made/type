# machine-made Weft 0.2

Weft is a grid-built monospace by machine-made, with a weight axis
(`wght` 100 to 900) and a fragmentation axis (`FRAG` 0 to 100).

## What is new

- **Code look-alikes.** l, I, 1, 0 and q are drawn so they do not read as
  each other. In the OCR test Weft now reads look-alike strings better
  than DejaVu Sans Mono (character error rate 0.071 against 0.0875 at
  FRAG 0; Weft 0.1: 0.121). A dotted zero is in `ss01`.
- **Central European languages.** All of Latin Extended-A, Romanian Ș ș
  Ț ț, ẞ, and 14 combining marks with mark positioning. Polish, Czech,
  Slovak, Hungarian, Romanian, Turkish, Croatian, Slovenian, Latvian,
  Lithuanian, Estonian, Maltese and Esperanto are covered.
- **Heavy weights.** Accents on capitals and lowercase have more room at
  Black, and « » " “ ” „ no longer close up.
- **For code.** Box drawing (─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼) that joins across
  cells and lines, arrows (← → ↑ ↓), the minus sign, ‹ › ‚ „.
- **Hinting.** The static TTFs are hinted with ttfautohint.

Every glyph keeps the 750-unit advance (combining marks have none).
The line metrics (typo and hhea 906 / -281 / 0) do not change.

## Files

- `MachineMadeWeft[FRAG,wght].ttf`: the variable font.
- `ttf/`, `otf/`: nine static weights at FRAG 0 (Thin to Black).
- `webfonts/`: WOFF2 of the variable font, Regular and Bold.
- `readability.json`: the OCR report.

## Licence

SIL Open Font License 1.1, with Reserved Font Name "machine-made".
