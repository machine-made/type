#!/usr/bin/env bash
# Check machine-made Sans with Fontspector (universal profile) and with
# fontTools varLib.interpolatable.
# Usage: sans/scripts/check.sh [path-to-fontspector]
# Each format runs as its own family. The process fails on FAIL or worse.
# WARN does not fail it. Reports go to reports/sans/.
set -euo pipefail
cd "$(dirname "$0")/../.."

FS="${1:-fontspector}"
OUT=reports/sans
rm -rf "$OUT"
mkdir -p "$OUT"
status=0

run() {
  local label="$1"; shift
  "$FS" --profile universal --skip-network --error-code-on fail \
    --configuration sans/fontspector.toml \
    --ghmarkdown "$OUT/fontspector-${label}.md" \
    --json "$OUT/fontspector-${label}.json" \
    "$@" > "$OUT/fontspector-${label}.txt" 2>&1 || status=1
  tail -n 2 "$OUT/fontspector-${label}.txt"
}

run variable fonts/sans/variable/*.ttf
run ttf fonts/sans/ttf/*.ttf
run otf fonts/sans/otf/*.otf
run webfonts fonts/sans/webfonts/*.woff2

python sans/scripts/fs_summary.py "$OUT"/fontspector-*.json --md "$OUT/summary.md" || status=1

# Interpolation compatibility of the masters, per source. glyphsLib adds
# a discrete "ital" axis to the italic designspace, which
# varLib.interpolatable cannot read, so the check runs on the master UFOs.
UFO_DIR="build/sans/interpolatable"
rm -rf "$UFO_DIR"
for src in sans/sources/MachineMadeSans.glyphs sans/sources/MachineMadeSans-Italic.glyphs; do
  name="$(basename "$src" .glyphs)"
  mkdir -p "$UFO_DIR/$name"
  glyphs2ufo --minimal -m "$UFO_DIR/$name" "$src" > /dev/null
  if ! fonttools varLib.interpolatable "$UFO_DIR/$name"/*.ufo > "$OUT/interpolatable-${name}.txt" 2>&1; then
    echo "error: varLib.interpolatable reports problems in $src" >&2
    status=1
  fi
  if [ -s "$OUT/interpolatable-${name}.txt" ]; then
    echo "error: varLib.interpolatable output for $src is not empty:" >&2
    head -n 40 "$OUT/interpolatable-${name}.txt" >&2
    status=1
  else
    echo "varLib.interpolatable: $name: no problems."
  fi
done

exit "$status"
