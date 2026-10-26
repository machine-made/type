#!/usr/bin/env bash
# Build Weft 0.1: UFO masters and statics, then the variable TTF, static
# TTF and OTF, and WOFF2.
# Usage: weft/scripts/build.sh (from any directory)
set -euo pipefail
WEFT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WEFT/.." && pwd)"
OUT="$ROOT/fonts/weft"
# Fixed timestamps (head.created, head.modified) make the build reproducible.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1792972800}"  # 2026-10-26 00:00 UTC
cd "$WEFT"

python -m loom.build --out build

rm -rf "$OUT"
mkdir -p "$OUT/variable" "$OUT/ttf" "$OUT/otf" "$OUT/webfonts"

# Variable font. The pieces overlap on purpose: keep the overlaps.
fontmake -m build/Weft.designspace -o variable --keep-overlaps \
  --output-path "$OUT/variable/MachineMadeWeft[FRAG,wght].ttf"
python tools/finish.py --variable "$OUT/variable/MachineMadeWeft[FRAG,wght].ttf"

# Static fonts at FRAG 0. The generator removed the overlaps already.
fontmake -u build/static/*.ufo -o ttf --keep-overlaps --output-dir "$OUT/ttf"
fontmake -u build/static/*.ufo -o otf --keep-overlaps --output-dir "$OUT/otf"
python tools/finish.py --static "$OUT"/ttf/*.ttf "$OUT"/otf/*.otf

python tools/finish.py --woff2-dir "$OUT/webfonts" --woff2 \
  "$OUT/variable/MachineMadeWeft[FRAG,wght].ttf" \
  "$OUT/ttf/MachineMadeWeft-Regular.ttf" \
  "$OUT/ttf/MachineMadeWeft-Bold.ttf"
