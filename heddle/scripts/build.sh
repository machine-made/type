#!/usr/bin/env bash
# Build Heddle 0.1: UFO masters and statics, then the variable TTF, the
# static TTF and WOFF2.
# Usage: heddle/scripts/build.sh (from any directory)
set -euo pipefail
HEDDLE="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$HEDDLE/.." && pwd)"
OUT="$ROOT/fonts/heddle"
VF="MachineMadeHeddle[wdth,wght].ttf"
# Fixed timestamps (head.created, head.modified) make the build reproducible.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1793059200}"  # 2026-10-27 00:00 UTC
cd "$HEDDLE"

python -m loom.build --out build

rm -rf "$OUT"
mkdir -p "$OUT/variable" "$OUT/ttf" "$OUT/webfonts"

# Variable font. The primitives overlap on purpose: keep the overlaps.
fontmake -m build/Heddle.designspace -o variable --keep-overlaps \
  --output-path "$OUT/variable/$VF"
python tools/finish.py --variable "$OUT/variable/$VF"

# Static fonts. The generator removed the overlaps already.
fontmake -u build/static/*.ufo -o ttf --keep-overlaps --output-dir "$OUT/ttf"
python tools/finish.py --static "$OUT"/ttf/*.ttf

python tools/finish.py --woff2-dir "$OUT/webfonts" --woff2 \
  "$OUT/variable/$VF" \
  "$OUT/ttf/MachineMadeHeddle-Regular.ttf" \
  "$OUT/ttf/MachineMadeHeddle-Bold.ttf"
