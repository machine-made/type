#!/usr/bin/env bash
# Build Warp 0.1: six static styles as UFO, then TTF, OTF and WOFF2.
# Usage: warp/scripts/build.sh (from any directory)
set -euo pipefail
WARP="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WARP/.." && pwd)"
OUT="$ROOT/fonts/warp"
# Fixed timestamps (head.created, head.modified) make the build reproducible.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1793059200}"  # 2026-10-27 00:00 UTC
JOBS="${WARP_JOBS:-$(nproc 2>/dev/null || echo 1)}"
cd "$WARP"

python -m loom.build --out build --jobs "$JOBS"

rm -rf "$OUT"
mkdir -p "$OUT/ttf" "$OUT/otf" "$OUT/webfonts"

# The loom writes overlap-free outlines already: keep them as they are.
fontmake -u build/ufo/*.ufo -o ttf --keep-overlaps --output-dir "$OUT/ttf"
fontmake -u build/ufo/*.ufo -o otf --keep-overlaps --output-dir "$OUT/otf"
python tools/finish.py --static "$OUT"/ttf/*.ttf "$OUT"/otf/*.otf
python tools/finish.py --woff2-dir "$OUT/webfonts" --woff2 "$OUT"/ttf/*.ttf
