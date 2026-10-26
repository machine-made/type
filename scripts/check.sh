#!/usr/bin/env bash
# Check the compiled fonts with Fontspector (universal profile).
# Usage: scripts/check.sh [path-to-fontspector]
# Each format runs alone: TTF and OTF of one style are not one family.
# The process fails on FAIL or worse. WARN does not fail it.
set -euo pipefail
cd "$(dirname "$0")/.."

FS="${1:-fontspector}"
mkdir -p reports
status=0
for f in fonts/Weft-Regular.ttf fonts/Weft-Regular.otf; do
  name="$(basename "$f")"
  "$FS" --profile universal \
    --skip-network --error-code-on fail \
    --ghmarkdown "reports/fontspector-${name}.md" \
    --json "reports/fontspector-${name}.json" \
    "$f" || status=1
done
exit "$status"
