#!/usr/bin/env bash
# Build Weft phase 1: UFO master, then static TTF and OTF.
# Usage: scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."

python -m loom.build --out master/Weft-Regular.ufo
rm -rf fonts
fontmake -u master/Weft-Regular.ufo -o ttf otf --output-dir fonts
python tools/finish.py fonts/Weft-Regular.ttf fonts/Weft-Regular.otf
