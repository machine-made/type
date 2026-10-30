# machine-made Warp 0.2

Warp is a Modern serif for science, made by code. A level pen draws
every letter: each glyph is a few centre-lines with a pressure per
node, swept by one nib. 0.2 makes Warp a maths font: it has an
OpenType MATH table, so LuaLaTeX, XeLaTeX, Word and browsers with
MathML can set formulas with it. It also covers the Central European
languages.

## What is new in 0.2

**Maths.** An OpenType MATH table in all six fonts:

- constants from the face: the maths axis at 250, the rule thickness of
  the rule pen (the thickness of − and of the top of √), scripts at 70 %
  and 50 %;
- four size variants each for ( ) [ ] { } | ‖ ⟨ ⟩ √ ∫ ∑ ∏, and
  assemblies (pieces that stack to any height) for ( ) [ ] { } | ‖ √ ∫.
  The pen draws every variant and every piece at its height; nothing is
  scaled;
- the mathematical italic letters (Latin and Greek, and ℎ), with italic
  corrections and accent positions.

Set it with LuaLaTeX and unicode-math:

```latex
\usepackage{unicode-math}
\setmainfont{MachineMadeWarp-Regular.ttf}[ItalicFont=MachineMadeWarp-Italic.ttf,
  BoldFont=MachineMadeWarp-Bold.ttf, BoldItalicFont=MachineMadeWarp-BoldItalic.ttf]
\setmathfont{MachineMadeWarp-Regular.ttf}
```

**Languages.** Latin Extended-A (Ā to ſ) and Ș ș Ț ț: Polish, Czech,
Slovak, Hungarian, Romanian, Turkish, Croatian, Slovenian, Latvian,
Lithuanian, Estonian, Maltese and more. Romanian and Latvian use the
comma below; ď ť ľ Ľ use the vertical caron. Greek with tonos and
dialytika.

**Figures.** Superior and inferior figures, numerators and
denominators: `sups`, `subs`, `sinf`, `numr`, `dnom`, `frac`.

**Italic.** The capitals B D E F H I J K L P R S T U X Y Z and the &
have their own cursive forms now (entry hooks, curled feet, drops).

**Reading at small sizes.** The lower loop of g closes; f has a firmer
hook; the bar of ﬁ and ﬂ stops short of the i and the l; the word space
is wider at text sizes (310 units). Ξ and Σ have heavier bars.

**Symbols.** ‰ † ‡ ℓ ℎ ℏ ‖ ⟨ ⟩.

**Hinting.** The TTF files are hinted with ttfautohint.

**Kerning.** More lowercase, Greek and italic pairs.

## Files

**machine-made Warp** (text, optical size 10): Regular, Italic, Bold,
Bold Italic. **machine-made Warp Display** (optical size 60): Regular,
Italic. TTF (hinted) and OTF, WOFF2 for the web. 593 characters,
890 glyphs.

## Checks

- Fontspector 1.9.0, universal profile: no FAIL, no ERROR.
- Every glyph matches its pen sweep within 5 % of the ink at 16 to 128
  pixels per em.
- OCR (Tesseract) at 10, 12 and 14 px: character error rate 0.18 %
  (Regular) and 1.26 % (Italic); 0.1 had 2.3 % and 1.9 %.
- The MATH table is tested with fontTools and HarfBuzz, and a page of
  formulas is set with LuaLaTeX (`proofs/warp/warp-math.png`).

Licence: SIL Open Font License 1.1, Reserved Font Name "machine-made".
