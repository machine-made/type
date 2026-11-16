# SPDX-License-Identifier: Apache-2.0
"""Weight parameters and the static build boundary. Apache-2.0."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import ufoLib2
from loom import build as B
from loom import engine as E

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import compat


def test_ladder_weight_endpoints():
    assert B.weight_params(400) == {key: E.DEFAULTS[key] for key in B.BOLD}
    assert B.weight_params(700) == B.BOLD
    for weight in (400, 700):
        expected = B.STYLES[B.WEIGHTS[weight]].p()
        assert E.params(opsz=B.TEXT_OPSZ, **B.weight_params(weight)) == expected


def test_ladder_weight_growth_and_floors():
    previous = 0
    for weight in range(300, 701):
        p = E.params(opsz=B.TEXT_OPSZ, **B.weight_params(weight))
        assert p.A > previous
        assert p.B >= 5
        assert p.S >= p.B
        previous = p.A
    for invalid in (299, 701, float("nan")):
        with pytest.raises(ValueError):
            B.weight_params(invalid)


def test_ladder_static_selection_and_names():
    assert B.DEFAULT_STYLES == (
        "Regular",
        "Italic",
        "Bold",
        "BoldItalic",
        "Display",
        "DisplayItalic",
    )
    assert len(B.LADDER_STYLES) == 10
    assert len(B.MASTER_STYLES) == 14
    assert B.MASTER_WEIGHTS == (300, 350, 400, 450, 500, 600, 700)
    for italic in (False, True):
        for weight in B.MASTER_WEIGHTS:
            style = B.STYLES[B.weight_style(weight, italic)]
            assert style.weight == weight
            assert style.italic == italic
            assert style.family == B.FAMILY
            assert len(f"{style.family} {style.style}") <= 32
            font = ufoLib2.Font()
            B.set_info(font, style)
            if weight not in (400, 700):
                assert font.info.openTypeNamePreferredFamilyName == B.FAMILY
                assert font.info.openTypeNamePreferredSubfamilyName == style.style


def test_ladder_default_byte_guard_rejects_compatible_path(tmp_path, monkeypatch):
    from test_compat import test_compat_default_build_bytes

    build_font = B.build_font

    def forced_compatible(*args, **kwargs):
        kwargs["compatible"] = True
        return build_font(*args, **kwargs)

    monkeypatch.setattr(B, "build_font", forced_compatible)
    with pytest.raises(
        AssertionError, match="Fresh Regular bytes differ from the committed font"
    ):
        test_compat_default_build_bytes(tmp_path, monkeypatch)


def test_ladder_all_glyphs_compatible():
    reports = compat.compare_ladder()
    for style, report in reports.items():
        bad = [row for row in report["rows"] if not row["point_compatible"]]
        assert not bad, (style, bad)
        assert report["glyphs"] == 890
    assert set(reports) == set(B.MASTER_STYLES)


def test_ladder_alignment_keeps_points():
    import numpy as np
    from loom.compatible import aligned_start

    points = np.array([(0, 0), (10, 0), (20, 10), (0, 10)])
    moved = np.roll(points, 2, axis=0)
    shift = aligned_start(points, moved)
    assert shift == 2
    assert np.array_equal(points, np.roll(moved, -shift, axis=0))


def test_ladder_contour_identity_survives_vertical_crossing():
    import numpy as np
    from loom.compatible import canonical, lines, match_contours

    def rectangle(width, height, y):
        return lines(
            np.array(
                [(0, y), (width, y), (width, y + height), (0, y + height)], dtype=float
            )
        )

    reference = canonical([rectangle(100, 100, 0), rectangle(30, 10, 46)])
    target = canonical([rectangle(100, 100, 0), rectangle(30, 10, 44)])
    assert abs(reference[0][0]) > abs(reference[1][0])
    assert abs(target[0][0]) < abs(target[1][0])
    matched = match_contours(reference, target)
    assert abs(matched[0][0]) > abs(matched[1][0])


def test_ladder_assignment_is_global():
    from itertools import permutations

    from loom.compatible import minimum_assignment

    # A greedy nearest pair would give the right dot the middle slot.
    costs = [[(x - y) * (x - y) for y in (120, 350, 580)] for x in (85, 250, 415)]
    assignment = minimum_assignment(costs)
    assert assignment == [0, 1, 2]
    assert sum(costs[i][j] for i, j in enumerate(assignment)) == min(
        sum(costs[i][j] for i, j in enumerate(p)) for p in permutations(range(3))
    )


def test_ladder_italic_policy_keeps_hulls():
    from loom.compatible import ITALIC_TOPOLOGY, TOPOLOGY, stroke_groups

    for weight in B.WEIGHTS:
        for name in ITALIC_TOPOLOGY - TOPOLOGY:
            d = B.drawn(B.weight_style(weight, True), name)
            assert [
                p for group in stroke_groups(d, name) for p in group
            ] == d.sweep.polys


def test_ladder_rejects_stale_fontspector_report(tmp_path, monkeypatch):
    import vf_ladder

    report = tmp_path / "fontspector-Roman.json"
    report.write_text('{"summary": {}, "results": {}}')
    monkeypatch.setattr(
        vf_ladder.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout="", stderr="failed"),
    )
    with pytest.raises(RuntimeError, match=r"did not write its report \(exit 1\)"):
        vf_ladder.inspect_font("fontspector", tmp_path / "test.ttf", tmp_path, "Roman")
    assert not report.exists()


def test_ladder_source_failure_preserves_diagnostics(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    import vf_ladder

    rows = [{"glyph": "gamma", "style": "Light", "weight": 300, "contours": 2}]
    error_path = tmp_path / "Roman-compile-error.json"
    error_path.write_text('{"reason": "stale"}')

    class FailedCompiler:
        exitcode = 1

        def __init__(self, **kwargs):
            pass

        def start(self):
            assert not error_path.exists()
            error_path.write_text(
                json.dumps({"reason": "gamma: topology differs", "diagnostics": rows})
            )

        def join(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        vf_ladder.multiprocessing,
        "get_context",
        lambda method: SimpleNamespace(Process=FailedCompiler),
    )
    with pytest.raises(vf_ladder.CompatibilityError, match="gamma") as caught:
        vf_ladder.compiled_sources(False, tmp_path)
    assert caught.value.diagnostics == rows


def test_ladder_endpoint_regression():
    from vf_ladder import endpoint_regression

    values = {"400": {"max_units": 0.02}, "700": {"max_units": 0.5200000000000029}}
    assert endpoint_regression(values)
    values["700"]["max_units"] = 0.9
    assert not endpoint_regression(values)


def test_ladder_encoded_master_location():
    from vf_ladder import finding_identity, master_weight

    assert master_weight(450.006103515625, B.MASTER_WEIGHTS) == 450
    assert master_weight(600.006103515625, B.MASTER_WEIGHTS) == 600
    assert master_weight(599.98779296875, B.MASTER_WEIGHTS) == 600
    assert master_weight(499.993896484375, B.WEIGHTS) == 500
    with pytest.raises(ValueError, match="No source master"):
        master_weight(600.1, B.WEIGHTS)
    a = {"glyph": "test", "location": {"wght": 600.006103515625}}
    b = {"glyph": "test", "location": {"wght": 599.98779296875}}
    assert finding_identity(a) == finding_identity(b)
    b["location"]["wght"] = 425
    assert finding_identity(b)["location"]["wght"] == 425
    assert finding_identity(a) != finding_identity(b)


def test_ladder_failed_run_invalidates_proof(tmp_path, monkeypatch):
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1793059200")
    for filename in ("ladder.json", "interpolation.json"):
        (tmp_path / filename).write_text('{"verdict": "verified"}')

    def fail(*args):
        raise ValueError("test failure")

    monkeypatch.setattr(vf_ladder, "run_slope", fail)
    with pytest.raises(ValueError, match="test failure"):
        vf_ladder.main(["--out", str(tmp_path / "build"), "--fontspector", "unused"])
    for filename in ("ladder.json", "interpolation.json"):
        assert (
            json.loads((tmp_path / filename).read_text())["verdict"] == "not verified"
        )


def test_ladder_keeps_findings_when_second_slope_fails(tmp_path, monkeypatch):
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    finding = {
        "slope": "Roman",
        "kind": "underweight",
        "glyph": "a",
        "actual": {"value_master1": 100},
        "expected": {"value_master2": 150},
    }

    def run(italic, *args):
        if italic:
            raise ValueError("Italic failed")
        return {"passed": True}, [finding], tmp_path / "Roman.ttf"

    monkeypatch.setattr(vf_ladder, "run_slope", run)
    with pytest.raises(ValueError, match="Italic failed"):
        vf_ladder.main(["--out", str(tmp_path / "build"), "--fontspector", "unused"])
    report = json.loads((tmp_path / "interpolation.json").read_text())
    assert report["kinds"]["underweight"] == [finding]
    assert report["glyph_counts"] == {"underweight": 1}
    assert "1.500000" in report["causes"]["underweight"]
    assert not report["complete"]
    assert report["verdict"] == "not verified"


def test_ladder_rejects_compiled_mismatch():
    from copy import deepcopy

    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable
    from vf_ladder import check_master_structure

    font = TTFont()
    font.setGlyphOrder(["test"])
    font["glyf"] = newTable("glyf")
    font["glyf"].glyphs = {}
    font["glyf"].glyphOrder = ["test"]
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((20, 0))
    pen.lineTo((20, 20))
    pen.closePath()
    font["glyf"]["test"] = pen.glyph()
    font["hmtx"] = newTable("hmtx")
    font["hmtx"].metrics = {"test": (30, 0)}
    other = deepcopy(font)
    check_master_structure([font, other])
    other["glyf"]["test"].flags[1] = 0
    with pytest.raises(ValueError, match="compiled master structure differs") as caught:
        check_master_structure([font, other])
    rows = caught.value.diagnostics
    assert [r["glyph"] for r in rows] == ["test", "test"]
    assert rows[0]["flags"] != rows[1]["flags"]


def local_test_fonts():
    """Small masters with a non-linear component offset and advance."""
    from ufo2ft import compileTTF
    from ufoLib2.objects import Component

    fonts = {}
    for weight, offset in zip(B.MASTER_WEIGHTS, (0, 135, 269, 276, 282, 294, 306)):
        ufo = ufoLib2.Font()
        B.set_info(ufo, B.STYLES[B.weight_style(weight)])
        ufo.newGlyph(".notdef")
        for name, size in (("base", weight // 5), ("mark", 30)):
            glyph = ufo.newGlyph(name)
            pen = glyph.getPen()
            pen.moveTo((0, 0))
            pen.lineTo((size, 0))
            pen.lineTo((size, size))
            pen.lineTo((0, size))
            pen.closePath()
            glyph.width = size + 20
        glyph = ufo.newGlyph("accented")
        glyph.components.extend(
            [Component("base"), Component("mark", (1, 0, 0, 1, offset, 200))]
        )
        glyph.width = 400 + offset
        fonts[weight] = compileTTF(ufo, removeOverlaps=False)
    return fonts


def test_ladder_local_tuples_reproduce_composites(tmp_path):
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.varLib.models import supportScalar
    from vf_ladder import build_vf
    from vf_spike import endpoint_difference

    statics = local_test_fonts()
    font, _ = build_vf(statics, list(B.MASTER_WEIGHTS), False, tmp_path)
    for weight in B.MASTER_WEIGHTS:
        instance = instantiateVariableFont(font, {"wght": weight})
        assert endpoint_difference(instance, statics[weight])["max_units"] <= 1.0
        for name in instance.getGlyphOrder():
            assert instance["hmtx"][name][0] == statics[weight]["hmtx"][name][0]
    variations = font["gvar"].variations["accented"]
    assert len(variations) == 6
    for variation in variations:
        assert None not in variation.coordinates
        peak = variation.axes["wght"][1]
        assert sum(supportScalar({"wght": peak}, v.axes) for v in variations) == 1


def test_ladder_axis_rounding_does_not_thin_midpoint_bar(tmp_path):
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from vf_ladder import build_vf

    statics = local_test_fonts()
    for weight, source in statics.items():
        growth = (weight - 400) // 50
        pen = TTGlyphPen(None)
        pen.moveTo((0, -142 - growth))
        pen.lineTo((100, -142 - growth))
        pen.lineTo((100, -118 + growth))
        pen.lineTo((0, -118 + growth))
        pen.closePath()
        source["glyf"]["mark"] = pen.glyph()
    font, _ = build_vf(statics, list(B.MASTER_WEIGHTS), False, tmp_path)
    instance = instantiateVariableFont(font, {"wght": 425})
    path = tmp_path / "midpoint.ttf"
    instance.save(path)
    with TTFont(path) as saved:
        glyph = saved["glyf"]["mark"]
        # An axis peak rounded up makes both edges round inward and
        # gives only 24 units instead of the midpoint's 25 or 26.
        assert glyph.yMax - glyph.yMin in (25, 26)


def test_ladder_cpu_features():
    code = """
import hashlib
import json
from loom import build as B
from loom.compatible import aligned_start
import compat
h = hashlib.sha256()
for style in B.MASTER_STYLES:
    for name in ('a', 'iota', 'Xi', 'L', 'hungarumlautcomb.case', 'l.sc', 'hbar.sc', 'theta.sc', 'ellipsis'):
        for contour in compat.contours(style, name, True):
            for segment in contour:
                for p in segment[1:]:
                    h.update(p.tobytes())
for w in range(300, 701):
    h.update(json.dumps(B.weight_params(w), sort_keys=True).encode())
points = [(0, 0), (20, 0), (30, 10), (0, 10)]
h.update(str(aligned_start(points, points[2:] + points[:2])).encode())
from tempfile import TemporaryDirectory
from pathlib import Path
from test_ladder import local_test_fonts
from vf_ladder import build_vf
with TemporaryDirectory() as directory:
    font, _ = build_vf(local_test_fonts(), list(B.MASTER_WEIGHTS), False, Path(directory))
    h.update(font['gvar'].compile(font))
print(h.hexdigest())
"""
    warp = Path(__file__).resolve().parents[1]
    hashes = []
    for disabled in (False, True):
        env = dict(os.environ)
        env.pop("NPY_DISABLE_CPU_FEATURES", None)
        if disabled:
            env["NPY_DISABLE_CPU_FEATURES"] = "X86_V4 AVX512_ICL AVX512_SKX AVX512F"
        env["PYTHONPATH"] = os.pathsep.join(
            (str(warp), str(warp / "tools"), str(warp / "tests"))
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        hashes.append(result.stdout.strip())
    assert hashes[0] == hashes[1]


def test_ladder_midpoints_come_from_master_list():
    from itertools import pairwise

    from vf_ladder import fidelity_weights, gap_midpoints

    expected = [(left + right) / 2 for left, right in pairwise(B.MASTER_WEIGHTS)]
    assert gap_midpoints(B.MASTER_WEIGHTS) == expected
    assert expected == [325, 375, 425, 475, 550, 650]
    assert fidelity_weights(B.MASTER_WEIGHTS) == sorted(
        set(expected) | {350, 450, 550, 650}
    )
    assert gap_midpoints([300, 360, 400, 700]) == [330, 380, 550]
    assert {330, 380, 550} <= set(fidelity_weights([300, 360, 400, 700]))


def test_ladder_resolve_composite_keeps_translated_contours(tmp_path):
    from fontTools.ttLib import TTFont
    from vf_ladder import resolve_composite, rotate_contour

    font = local_test_fonts()[600]
    glyph = font["glyf"]["accented"]
    coordinates, ends, flags = glyph.getCoordinates(font["glyf"])
    before = list(coordinates), list(ends), list(flags)
    metrics = font["hmtx"]["accented"]
    base_points = list(font["glyf"]["base"].coordinates)
    resolve_composite(font, "accented")
    glyph = font["glyf"]["accented"]
    assert not glyph.isComposite()
    assert (
        list(glyph.coordinates),
        glyph.endPtsOfContours,
        list(glyph.flags),
    ) == before
    rotate_contour(glyph, 1, 2)
    assert list(glyph.coordinates[4:]) == before[0][6:] + before[0][4:6]
    assert list(font["glyf"]["base"].coordinates) == base_points
    assert font["hmtx"]["accented"] == metrics
    path = tmp_path / "resolved.ttf"
    font.save(path)
    with TTFont(path) as saved:
        assert not saved["glyf"]["accented"].isComposite()
        assert list(saved["glyf"]["accented"].coordinates) == list(glyph.coordinates)


def test_ladder_stroke_union_keeps_iota_ink():
    from loom import outline as O
    from loom.compatible import incremental_stroke_contours, polygon

    d = B.drawn(B.weight_style(450), "iota")
    batch_area = sum(abs(O.signed_area(polygon(c)[0])) for c in d.contours)
    repaired = incremental_stroke_contours(d, "iota")
    assert len(d.contours) == 2
    assert len(repaired) == 1
    area = abs(O.signed_area(polygon(repaired[0])[0]))
    assert 41000 < area < 41100
    assert area > batch_area + 15000


def test_ladder_new_warning_blocks_verdict_and_keeps_baseline(tmp_path, monkeypatch):
    import json

    import vf_ladder

    old = {
        "check_id": "file_size",
        "code": "large-font",
        "severity": "WARN",
        "glyph": None,
        "location": {},
    }
    new = {
        "check_id": "suspicious_sidebearings",
        "code": "large-aw-variation",
        "severity": "WARN",
        "glyph": "a",
        "location": {"wght": 450},
    }
    baseline = {"Roman": [old], "Italic": [old]}
    sizes = {"Roman.ttf": 123}
    (tmp_path / "ladder.json").write_text(
        json.dumps(
            {
                "previous_fontspector_findings": baseline,
                "previous_file_sizes_bytes": sizes,
            }
        )
    )
    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    monkeypatch.setattr(vf_ladder, "proof_sheet", lambda *args: "proof.png")

    def run(italic, *args):
        return (
            {"passed": True, "fontspector_findings": [old if italic else new]},
            [],
            tmp_path / "test.ttf",
        )

    monkeypatch.setattr(vf_ladder, "run_slope", run)
    assert (
        vf_ladder.main(["--out", str(tmp_path / "build"), "--fontspector", "unused"])
        == 1
    )
    report = json.loads((tmp_path / "ladder.json").read_text())
    assert report["verdict"] == "not verified"
    assert report["styles"]["Roman"]["new_fontspector_findings"] == [new]
    assert not report["styles"]["Roman"]["passed"]
    assert report["previous_fontspector_findings"] == baseline
    assert report["previous_file_sizes_bytes"] == sizes


def test_ladder_fontspector_keeps_font_problem_glyphs():
    from vf_ladder import fontspector_findings

    def report(names):
        return {
            "results": {
                "font": {
                    "universal": [
                        {
                            "check_id": "unreachable_glyphs",
                            "subresults": [
                                {
                                    "severity": "WARN",
                                    "code": "unreachable-glyphs",
                                    "metadata": [
                                        {
                                            "FontProblem": {
                                                "context": {"unreachable_glyphs": names}
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

    baseline = fontspector_findings(report(["part"]))
    current = fontspector_findings(report(["part", "newpart"]))
    added = [row for row in current if row not in baseline]
    assert len(added) == 1
    assert added[0]["glyph"] == "newpart"


def test_ladder_worker_returns_results_and_errors():
    from vf_ladder import gap_midpoints, master_weight, worker_process

    assert worker_process(gap_midpoints, B.MASTER_WEIGHTS) == [
        325,
        375,
        425,
        475,
        550,
        650,
    ]
    with pytest.raises(RuntimeError, match="No source master"):
        worker_process(master_weight, 600.1, B.MASTER_WEIGHTS)


def test_ladder_failed_inspection_keeps_measurements(tmp_path, monkeypatch):
    import vf_ladder

    instances = {str(w): {"max_units": 0.02} for w in B.WEIGHTS}
    fidelities = {"325": {"passed": True}}

    def worker(target, *args):
        if target is vf_ladder.prepare_slope:
            return {}
        assert target is vf_ladder.measure_slope
        return instances, fidelities

    def inspect(*args):
        raise RuntimeError("no report (exit -9)")

    monkeypatch.setattr(vf_ladder, "worker_process", worker)
    monkeypatch.setattr(vf_ladder, "inspect_font", inspect)
    (tmp_path / "MachineMadeWarp[wght].ttf").touch()
    report, findings, _ = vf_ladder.run_slope(False, tmp_path, "unused")
    assert report["instances"] == instances
    assert report["fidelity"] == fidelities
    assert not report["fontspector_complete"]
    assert all(value is None for value in report["fontspector"].values())
    assert "exit -9" in report["fontspector_error"]
    assert not report["passed"]
    assert findings == []


def test_ladder_incomplete_inspection_does_not_claim_zero_findings(
    tmp_path, monkeypatch
):
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    monkeypatch.setattr(vf_ladder, "proof_sheet", lambda *args: "proof.png")
    monkeypatch.setattr(
        vf_ladder,
        "run_slope",
        lambda *args: (
            {"passed": False, "fontspector_complete": False},
            [],
            tmp_path / "font.ttf",
        ),
    )
    assert vf_ladder.main(["--out", str(tmp_path), "--fontspector", "unused"]) == 1
    report = json.loads((tmp_path / "interpolation.json").read_text())
    assert not report["complete"]
    assert report["remaining"] is None
    assert report["start_point_count"] is None
