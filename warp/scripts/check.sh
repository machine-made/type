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
# Inspect each variable font separately, then match the accepted findings.
python - "$FS" "$REPORTS" "$WARP" <<'CHECK_VARIABLE'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[3]) / "tools"))
import vf_ladder

proof = json.loads((vf_ladder.PROOFS / "ladder.json").read_text())
accepted = json.loads((vf_ladder.PROOFS / "accepted_findings.json").read_text())
for slope, suffix in (("Roman", ""), ("Italic", "-Italic")):
    path = vf_ladder.ROOT / "fonts/warp/vf" / f"MachineMadeWarp{suffix}[wght].ttf"
    counts, interpolation = vf_ladder.inspect_font(sys.argv[1], path, Path(sys.argv[2]), slope)
    raw = json.loads((Path(sys.argv[2]) / f"fontspector-{slope}.json").read_text())
    baseline = [vf_ladder.finding_identity(r) for r in proof["previous_fontspector_findings"][slope]]
    findings = [r for r in vf_ladder.fontspector_findings(raw)
                if vf_ladder.finding_identity(r) not in baseline]
    verdict, _, _ = vf_ladder.accepted_findings_verdict(findings, accepted[slope])
    if interpolation or any(counts[k] for k in ("FAIL", "FATAL", "ERROR")) or verdict == "not verified":
        raise SystemExit(f"{slope}: variable font inspection failed")
    print(f"{slope}: {verdict}; {counts}")
CHECK_VARIABLE
exit "$status"
