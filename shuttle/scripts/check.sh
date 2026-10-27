#!/usr/bin/env bash
# Check the compiled fonts with Fontspector (universal profile).
# Usage: shuttle/scripts/check.sh [path-to-fontspector]
# Runs once for the variable font and once for the static TTF family.
# The process fails on FAIL or worse. WARN does not fail it.
set -euo pipefail
SHUTTLE="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$SHUTTLE/.." && pwd)"
FONTS="$ROOT/fonts/shuttle"

FS="${1:-fontspector}"
REPORTS="$SHUTTLE/build/reports"
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
exit "$status"
