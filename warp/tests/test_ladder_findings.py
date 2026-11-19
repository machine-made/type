# SPDX-License-Identifier: Apache-2.0
"""Accepted findings must equal the findings outside the frozen baseline."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from vf_ladder import Record

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "warp/tools"))

from vf_ladder import (
    accepted_findings_verdict,
    finding_identity,
    fontspector_findings,
)


def read_proofs() -> tuple[Record, Record]:
    return (
        json.loads((ROOT / "proofs/warp/ladder.json").read_text()),
        json.loads((ROOT / "proofs/warp/accepted_findings.json").read_text()),
    )


def outside_baseline(proof: Record, slope: str) -> list[Record]:
    baseline = [
        finding_identity(row) for row in proof["previous_fontspector_findings"][slope]
    ]
    return [
        row
        for row in proof["styles"][slope]["fontspector_findings"]
        if finding_identity(row) not in baseline
    ]


def test_accepted_committed_findings_agree() -> None:
    proof, accepted = read_proofs()
    assert set(accepted) == {"Roman", "Italic"}
    assert sum(map(len, accepted.values())) == 8
    for slope, count in (("Roman", 3), ("Italic", 5)):
        findings = outside_baseline(proof, slope)
        assert len(findings) == count
        assert findings == proof["styles"][slope]["new_fontspector_findings"]
        assert accepted_findings_verdict(findings, accepted[slope]) == (
            "verified with accepted findings",
            [],
            [],
        )
        assert all(row["z_score"] > 10 and row["cause"] for row in accepted[slope])


@pytest.mark.parametrize(
    "change", ["removed", "extra", "other_glyph", "location", "check", "code"]
)
def test_accepted_difference_is_not_verified(tmp_path: Path, change: str) -> None:
    proof, accepted = read_proofs()
    rows = proof["styles"]["Roman"]["fontspector_findings"]
    target = proof["styles"]["Roman"]["new_fontspector_findings"][0]
    if change == "removed":
        rows.remove(target)
    else:
        new = deepcopy(target)
        if change == "other_glyph":
            new["glyph"] = "unlisted_glyph"
        elif change == "location":
            new["location"]["wght"] += 0.000001
        elif change == "check":
            new["check_id"] = "another_check"
        elif change == "code":
            new["code"] = "another_code"
        # An extra duplicate also counts as a difference.
        rows.append(new)
    path = tmp_path / "ladder.json"
    path.write_text(json.dumps(proof))
    copied = json.loads(path.read_text())
    verdict, unaccepted, missing = accepted_findings_verdict(
        outside_baseline(copied, "Roman"), accepted["Roman"]
    )
    assert verdict == "not verified"
    assert bool(missing) == (change == "removed")
    assert bool(unaccepted) == (change != "removed")


def test_accepted_old_format_and_new_measurements_share_baseline() -> None:
    proof, accepted = read_proofs()
    for slope in accepted:
        old = deepcopy(proof)
        for rows in (
            old["previous_fontspector_findings"][slope],
            old["styles"][slope]["fontspector_findings"],
        ):
            for row in rows:
                row.pop("z_score", None)
                row.pop("measurement", None)
        expected = outside_baseline(old, slope)
        for row in old["styles"][slope]["fontspector_findings"]:
            row.update(z_score=12.0, measurement="advance widths")
        assert len(outside_baseline(old, slope)) == len(expected)
        assert accepted_findings_verdict(expected, accepted[slope])[0] == (
            "verified with accepted findings"
        )


def test_accepted_fontspector_extracts_measurements() -> None:
    _, accepted = read_proofs()
    for entries in accepted.values():
        for entry in entries:
            raw = {
                "results": {
                    "font": {
                        "section": [
                            {
                                "check_id": entry["check_id"],
                                "subresults": [
                                    {
                                        "code": entry["code"],
                                        "severity": "WARN",
                                        "metadata": [
                                            {
                                                "GlyphProblem": {
                                                    "glyph_name": entry["glyph"],
                                                    "userspace_location": entry[
                                                        "location"
                                                    ],
                                                    "actual": {
                                                        key: entry[key]
                                                        for key in (
                                                            "z_score",
                                                            "measurement",
                                                        )
                                                    },
                                                }
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                }
            }
            (row,) = fontspector_findings(raw)
            for key in (
                "check_id",
                "code",
                "glyph",
                "location",
                "z_score",
                "measurement",
            ):
                assert row[key] == entry[key]
            raw["results"]["font"]["section"][0]["check_id"] = "other"
            (row,) = fontspector_findings(raw)
            assert row["z_score"] is None
            assert row["measurement"] is None


def test_accepted_empty_list_and_stale_entry() -> None:
    _, accepted = read_proofs()
    assert accepted_findings_verdict([], []) == ("verified", [], [])
    assert accepted_findings_verdict([], accepted["Roman"])[0] == "not verified"


@pytest.mark.parametrize(
    "gate",
    ["pass", "numerical", "FAIL", "FATAL", "ERROR", "interpolation", "incomplete"],
)
def test_accepted_main_preserves_other_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gate: str
) -> None:
    import vf_ladder

    proof, accepted = read_proofs()
    (tmp_path / "ladder.json").write_text(json.dumps(proof))
    (tmp_path / "accepted_findings.json").write_text(json.dumps(accepted))
    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    monkeypatch.setattr(vf_ladder, "proof_sheet", lambda *_args: "proof.png")

    def run(
        italic: bool, *args: object, **kwargs: object
    ) -> tuple[Record, list[Record], Path]:
        result = deepcopy(proof["styles"]["Italic" if italic else "Roman"])
        # run_slope's passed field combines the existing numerical,
        # inspection, severity-count and interpolation gates.
        result["passed"] = gate == "pass"
        result["numerical_passed"] = gate != "numerical"
        result["fontspector_complete"] = gate != "incomplete"
        if gate in ("FAIL", "FATAL", "ERROR"):
            result["fontspector"][gate] = 1
        if gate == "incomplete":
            result["new_fontspector_findings"] = None
        return result, [], tmp_path / "font.ttf"

    monkeypatch.setattr(vf_ladder, "run_slope", run)
    assert vf_ladder.main(
        ["--out", str(tmp_path / "build"), "--fontspector", "unused"]
    ) == (gate != "pass")
    report = json.loads((tmp_path / "ladder.json").read_text())
    expected = "verified with accepted findings" if gate == "pass" else "not verified"
    assert report["verdict"] == expected
    for result in report["styles"].values():
        assert result["passed"] == (gate == "pass")
        if gate != "incomplete":
            assert result["verdict"] == expected
