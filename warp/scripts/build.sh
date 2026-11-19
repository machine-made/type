#!/usr/bin/env bash
# Build Warp 0.3: six static styles and the Roman and Italic weight ladders.
# Usage: warp/scripts/build.sh (from any directory)
set -euo pipefail
WARP="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WARP/.." && pwd)"
OUT="$ROOT/fonts/warp"
# Fixed timestamps (head.created, head.modified) make the build reproducible.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1793059200}"  # 2026-10-27 00:00 UTC
JOBS="${WARP_JOBS:-$(nproc 2>/dev/null || echo 1)}"
cd "$WARP"

static_start=$SECONDS
python -m loom.build --out build --jobs "$JOBS"

rm -rf "$OUT"
mkdir -p "$OUT/ttf" "$OUT/otf" "$OUT/webfonts"

# The loom writes overlap-free outlines already: keep them as they are.
fontmake -u build/ufo/*.ufo -o ttf --keep-overlaps --output-dir "$OUT/ttf"
fontmake -u build/ufo/*.ufo -o otf --keep-overlaps --output-dir "$OUT/otf"
# Hint the TTF with ttfautohint (pinned in pyproject.toml as ttfautohint-py).
# --no-info keeps the version string; finish.py then resets head.modified
# from SOURCE_DATE_EPOCH, so the hinted files are the same on every build.
for f in "$OUT"/ttf/*.ttf; do
  python -m ttfautohint --no-info "$f" "$f.hinted"
  mv "$f.hinted" "$f"
done
python tools/finish.py --static "$OUT"/ttf/*.ttf "$OUT"/otf/*.otf
python tools/finish.py --woff2-dir "$OUT/webfonts" --woff2 "$OUT"/ttf/*.ttf

echo "Static build: $((SECONDS - static_start)) seconds"
ladder_start=$SECONDS
python tools/vf_ladder.py --skip-fontspector --out "$ROOT/build/warp-vf"
mkdir -p "$OUT/vf"
cp "$ROOT/build/warp-vf/"*'[wght].ttf' "$OUT/vf/"
python tools/finish.py --woff2-dir "$OUT/vf" --woff2 "$OUT/vf/"*.ttf
python - "$ROOT" <<'PIN_WEB'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
path = root / "build/warp-vf/release.json"
report = json.loads(path.read_text())
for style in report["styles"].values():
    for measurement in style["fidelity"].values():
        measurement.pop("glyphs", None)
report["web_fonts"] = {
    font.name: {"sha256": hashlib.sha256(font.read_bytes()).hexdigest(),
                "size_bytes": font.stat().st_size}
    for font in sorted((root / "fonts/warp/vf").glob("*.woff2"))
}
path.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
PIN_WEB
echo "Ladder build and WOFF2: $((SECONDS - ladder_start)) seconds"
