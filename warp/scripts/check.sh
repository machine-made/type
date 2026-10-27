#!/usr/bin/env bash
# Check the compiled fonts with Fontspector (universal profile).
# Usage: warp/scripts/check.sh [path-to-fontspector]
# Runs once per family (text: 4 styles, display: 2 styles) and format.
# The process fails on FAIL or worse. WARN does not fail it.
set -euo pipefail
WARP="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WARP/.." && pwd)"
FONTS="$ROOT/fonts/warp"

FS="${1:-fontspector}"
REPORTS="$WARP/build/reports"
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
run text-ttf "$FONTS"/ttf/MachineMadeWarp-*.ttf
run display-ttf "$FONTS"/ttf/MachineMadeWarpDisplay-*.ttf
run text-otf "$FONTS"/otf/MachineMadeWarp-*.otf
run display-otf "$FONTS"/otf/MachineMadeWarpDisplay-*.otf
exit "$status"
