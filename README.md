# type

machine-made Weft and machine-made Sans: typefaces made by code.

> **Status: Weft phase 1 built, private.** One master (Regular, wght 400,
> FRAG 0): a-z, A-Z, 0-9. Waits for the founder's proof review before phase 2.
> This repo is managed by Jac, the CEO agent of machine-made
> (`machine-made/jac`). See `STATUS.md` and `BRIEF.md`.

## Mission

Two typefaces built by agents. **Weft**: a grid-built variable font with a `FRAG` axis from 0 (clean monospace) to 100 (fragmented), readable at every level used for text. **Sans**: a reading sans, modified from an open-licence base and given Weft's details. Both under the SIL Open Font License.

## Weft: how to build

Needs Python 3.14+ and, for the checks, the Fontspector binary.

```sh
python -m pip install -e ".[test]"
python -m pytest -q          # generator tests
scripts/build.sh             # UFO master, then fonts/Weft-Regular.ttf and .otf
scripts/check.sh fontspector # Fontspector, universal profile
python tools/proof.py        # proofs/weft-phase1-proof.png from the TTF
```

| Path | Content |
| --- | --- |
| `loom/glyphs.py` | Stroke table (plain data), metrics, stroke-width formula. |
| `loom/outline.py` | Centre line to outline: square caps, miter joins (limit 2.4), bevel, overlap removal (skia-pathops). |
| `loom/build.py` | Writes the UFO master (ufoLib2) at 1000 UPM. |
| `tools/finish.py` | Adds a STAT table to the static fonts. |
| `tools/proof.py` | Proof sheet from the compiled font; comparison with the sketch. |
| `tools/sketch_render.js` | Renders the same proof lines with the sketch 0.1 code (reference only, needs `@napi-rs/canvas`). |
| `reference/weft-sketch-0.1.html` | Approved sketch 0.1. Source of every shape. |
| `proofs/` | Proof PNGs. |

All shapes come from the sketch stroke table. No outline comes from any
other font.

## Standards

Follows the machine-made standards (`machine-made/jac`, `org/STANDARDS.md`):
C++23 and CUDA 13.3+, Rust 2024 with no unsafe code, Python 3.14+, tests and
parity before merge, actions pinned to commit SHAs, ASD-STE100 for changelogs,
comments and errors. Built by agents; no human writes code here.

## Licence

Split licence (decision for the founder to confirm):

* **Fonts** (the font files and the glyph data that defines them): SIL
  Open Font License 1.1, Reserved Font Name "machine-made". See `OFL.txt`.
* **Code** (the generator, tools, tests and CI): Apache-2.0. See `LICENSE`.
