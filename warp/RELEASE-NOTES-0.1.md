# machine-made Warp 0.1

Warp is a Modern serif for science, made by code. A level pen draws
every letter: each glyph is a few centre-lines with a pressure per
node, swept by one nib. Vertical stress, hairlines, thin bracketed
serifs and teardrop terminals all come out of that pen. Warp is set for
papers: lining tabular figures by default, old-style figures and small
capitals on request, full basic Greek, and the common maths symbols on
the maths axis.

## What is in 0.1

**machine-made Warp** (text, optical size 10, for 9 to 12 pt):
Regular, Italic, Bold, Bold Italic.

**machine-made Warp Display** (optical size 60, for titles): Regular,
Italic.

Static fonts in `ttf/` and `otf/`, WOFF2 in `webfonts/`. The variable
font (weight and optical size) is planned for 0.3.

**Characters**: printable ASCII; the Latin-1 letters and symbols; Œ œ Ÿ;
basic Greek (24 capitals, 24 lowercase, final sigma); + − × ÷ ± = ≠ < >
≤ ≥ ∑ ∏ ∫ √ ∞ ∂ ∇ ′ ″ · ∘ → ← ↔ ∈ ∉ ⊂ ⊆ ∪ ∩ ∀ ∃ ∅ ≈ ≡ ∝; € ₹ © ®; combining
marks. 306 characters, 429 glyphs.

**Features**: ff fi fl ffi ffl ligatures (`liga`); old-style figures
(`onum`); lining, proportional and tabular figures (`lnum`, `pnum`,
`tnum`); small capitals (`smcp`, `c2sc`); class kerning (`kern`); marks
(`mark`, `mkmk`).

**Italic**: a true cursive lowercase. The capitals A C G M N O Q V W
have their own italic forms; the others are the roman capitals, slanted,
with unbracketed serifs.

## Proofs

`proofs/warp/`: the sketch engine and the font overlaid for every style,
a paragraph from a paper at 9 to 12 pt, the Greek set, equations set by
the sketch's maths setter with the font's glyphs, kerning, accents,
small capitals and figures, the six styles, the full character set, and
the reports `fidelity.json`, `readability.json`, `sketch-compare.json`.

## Checks

- Fontspector 1.9.0, universal profile: no FAIL, no ERROR.
- Every glyph matches its pen sweep within 5 % of the ink at 16 to 128
  pixels per em.
- OCR (Tesseract) at 10, 12 and 14 px: character error rate 2.3 %
  (Regular) and 1.9 % (Italic), against 0.1 % and 0 % for DejaVu Serif.
- The build is byte-reproducible.

## Known limits

- No OpenType MATH table yet (0.2): stretchy delimiters, radicals and
  big operators come in one size. For TeX, use Warp for text next to a
  maths font.
- At 10 px on screen, OCR reads g, f, ﬁ and ﬂ less well than in DejaVu
  Serif. No hinting.
- Latin-1 and basic Greek only: no Latin Extended-A beyond Œ œ Ÿ, no
  Greek accents, no Cyrillic.
- Italic capitals other than A C G M N O Q V W are slanted roman.

## Licence

Fonts: SIL Open Font License 1.1, Reserved Font Name "machine-made".
Generator code: Apache-2.0.
