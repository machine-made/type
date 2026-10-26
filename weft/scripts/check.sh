#!/usr/bin/env bash
# Check the compiled fonts with Fontspector (universal profile).
# Usage: weft/scripts/check.sh [path-to-fontspector]
# Each format runs alone: TTF and OTF of one style are not one family.
# The process fails on FAIL or worse. WARN does not fail it.
set -euo pipefail
WEFT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$WEFT/.." && pwd)"

FS="${1:-fontspector}"
REPORTS="$WEFT/build/reports"
mkdir -p "$REPORTS"
status=0
for f in "$ROOT/fonts/weft/Weft-Regular.ttf" "$ROOT/fonts/weft/Weft-Regular.otf"; do
  name="$(basename "$f")"
  "$FS" --profile universal \
    --skip-network --error-code-on fail \
    --ghmarkdown "$REPORTS/fontspector-${name}.md" \
    --json "$REPORTS/fontspector-${name}.json" \
    "$f" || status=1
done
exit "$status"
