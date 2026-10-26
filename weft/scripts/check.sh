#!/usr/bin/env bash
# Check the compiled fonts with Fontspector (universal profile).
# Usage: weft/scripts/check.sh [path-to-fontspector]
# Runs once for the variable font, once for the static TTF family and
# once for the static OTF family. TTF and OTF of one style are not one
# family, so they run apart.
# The process fails on FAIL or worse. WARN does not fail it.
set -euo pipefail
WEFT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WEFT/.." && pwd)"
FONTS="$ROOT/fonts/weft"

FS="${1:-fontspector}"
REPORTS="$WEFT/build/reports"
mkdir -p "$REPORTS"
status=0
run() {
  local label="$1"; shift
  "$FS" --profile universal \
    --skip-network --error-code-on fail \
    --ghmarkdown "$REPORTS/fontspector-${label}.md" \
    --json "$REPORTS/fontspector-${label}.json" \
    "$@" || status=1
}
run variable "$FONTS"/variable/*.ttf
run ttf "$FONTS"/ttf/*.ttf
run otf "$FONTS"/otf/*.otf
exit "$status"
