#!/usr/bin/env bash
# Build Weft: UFO master, then static TTF and OTF.
# Usage: weft/scripts/build.sh (from any directory)
set -euo pipefail
WEFT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WEFT/.." && pwd)"
cd "$WEFT"

python -m loom.build --out build/master/Weft-Regular.ufo
rm -rf "$ROOT/fonts/weft"
fontmake -u build/master/Weft-Regular.ufo -o ttf otf --output-dir "$ROOT/fonts/weft"
python tools/finish.py "$ROOT/fonts/weft/Weft-Regular.ttf" "$ROOT/fonts/weft/Weft-Regular.otf"
