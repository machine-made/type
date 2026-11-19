# SPDX-License-Identifier: Apache-2.0
"""Weight parameters and the static build boundary. Apache-2.0."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import ufoLib2
from fontTools.ttLib import TTFont
from loom import build as B
from loom import engine as E
from pytest import MonkeyPatch

if TYPE_CHECKING:
    from loom.compatible import Contour, Diagnostics
    from vf_ladder import Record

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import compat


def test_ladder_compatibility_error_pickle() -> None:
    import pickle

    from loom.compatible import CompatibilityError

    rows: Diagnostics = [
        {"glyph": "gamma", "style": "Light", "weight": 300, "contours": 2}
    ]
    error = CompatibilityError("gamma: topology differs", rows)
    restored = pickle.loads(pickle.dumps(error))
    assert str(restored) == str(error)
    assert restored.diagnostics == error.diagnostics


def test_ladder_panose_weights() -> None:
    # Check the five named weights and the two extra masters, in both slopes.
    for italic in (False, True):
        for weight, digit in (
            (300, 3),
            (350, 4),
            (400, 5),
            (450, 6),
            (500, 6),
            (600, 7),
            (700, 8),
        ):
            font = ufoLib2.Font()
            B.set_info(font, B.STYLES[B.weight_style(weight, italic)])
            assert font.info.openTypeOS2Panose[2] == digit, (weight, italic)


def test_ladder_interpolation_names_two_master_source() -> None:
    import json

    from vf_ladder import interpolation_report

    report = interpolation_report([], complete=True)
    committed = json.loads(
        (
            Path(__file__).resolve().parents[2] / "proofs/warp/interpolation.json"
        ).read_text()
    )
    for measured in (report, committed):
        assert "baseline" not in measured
        assert measured["two_master_findings"] == 770
        assert (
            measured["two_master_source"]
            == "warp/STATUS.md#regular-and-bold-variable-font-test-2026-11-07"
        )
        assert measured["remaining"] == 0


def test_ladder_weight_endpoints() -> None:
    assert B.weight_params(400) == {key: E.DEFAULTS[key] for key in B.BOLD}
    assert B.weight_params(700) == B.BOLD
    for weight in (400, 700):
        expected = B.STYLES[B.WEIGHTS[weight]].p()
        assert E.params(opsz=B.TEXT_OPSZ, **B.weight_params(weight)) == expected


def test_ladder_weight_growth_and_floors() -> None:
    previous = 0.0
    # Check every integer weight in the supported 300 to 700 range.
    for weight in range(300, 701):
        p = E.params(opsz=B.TEXT_OPSZ, **B.weight_params(weight))
        assert p.A > previous
        # The engine clamps hairlines to five font units.
        assert p.B >= 5
        # Serif thickness must stay at or above the clamped hairline width.
        assert p.S >= p.B
        previous = p.A
    for invalid in (299, 701, float("nan")):
        with pytest.raises(ValueError):
            B.weight_params(invalid)


def test_ladder_static_selection_and_names() -> None:
    assert B.DEFAULT_STYLES == (
        "Regular",
        "Italic",
        "Bold",
        "BoldItalic",
        "Display",
        "DisplayItalic",
    )
    # Five named weights and seven source weights each have two slopes.
    assert len(B.LADDER_STYLES) == 10
    assert len(B.MASTER_STYLES) == 14
    assert B.MASTER_WEIGHTS == (300, 350, 400, 450, 500, 600, 700)
    for italic in (False, True):
        for weight in B.MASTER_WEIGHTS:
            style = B.STYLES[B.weight_style(weight, italic)]
            assert style.weight == weight
            assert style.italic == italic
            assert style.family == B.FAMILY
            # OpenType legacy family and style names must fit 32 characters.
            assert len(f"{style.family} {style.style}") <= 32
            font = ufoLib2.Font()
            B.set_info(font, style)
            if weight not in (400, 700):
                assert font.info.openTypeNamePreferredFamilyName == B.FAMILY
                assert font.info.openTypeNamePreferredSubfamilyName == style.style


def test_ladder_default_byte_guard_rejects_compatible_path(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    from test_compat import test_compat_default_build_bytes

    build_font = B.build_font

    def forced_compatible(
        style_key: str, compatible: bool = False, method: str = "sample"
    ) -> ufoLib2.Font:
        return build_font(style_key, compatible=True, method=method)

    monkeypatch.setattr(B, "build_font", forced_compatible)
    with pytest.raises(
        AssertionError, match="Fresh Regular bytes differ from the committed font"
    ):
        test_compat_default_build_bytes(tmp_path, monkeypatch)


def test_ladder_all_glyphs_compatible() -> None:
    reports = compat.compare_ladder()
    for style, report in reports.items():
        bad = [row for row in report["rows"] if not row["point_compatible"]]
        assert not bad, (style, bad)
        # The full ladder charset has 890 glyphs, including composites.
        assert report["glyphs"] == 890
    assert set(reports) == set(B.MASTER_STYLES)


def test_ladder_alignment_keeps_points() -> None:
    import numpy as np
    from loom.compatible import aligned_start

    points = np.array([(0, 0), (10, 0), (20, 10), (0, 10)])
    moved = np.roll(points, 2, axis=0)
    shift = aligned_start(points, moved)
    assert shift == 2
    assert np.array_equal(points, np.roll(moved, -shift, axis=0))


def test_ladder_contour_identity_survives_vertical_crossing() -> None:
    import numpy as np
    from loom.compatible import canonical, lines, match_contours

    def rectangle(width: float, height: float, y: float) -> Contour:
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


def test_ladder_assignment_is_global() -> None:
    from itertools import permutations

    from loom.compatible import minimum_assignment

    # A greedy nearest pair would give the right dot the middle slot.
    costs: list[list[float]] = [
        [(x - y) * (x - y) for y in (120, 350, 580)] for x in (85, 250, 415)
    ]
    assignment = minimum_assignment(costs)
    assert assignment == [0, 1, 2]
    assert sum(costs[i][j] for i, j in enumerate(assignment)) == min(
        sum(costs[i][j] for i, j in enumerate(p)) for p in permutations(range(3))
    )


def test_ladder_italic_policy_keeps_hulls() -> None:
    from loom.compatible import ITALIC_TOPOLOGY, TOPOLOGY, stroke_groups

    for weight in B.WEIGHTS:
        for name in ITALIC_TOPOLOGY - TOPOLOGY:
            d = B.drawn(B.weight_style(weight, True), name)
            assert [
                p for group in stroke_groups(d, name) for p in group
            ] == d.sweep.polys


def test_ladder_rejects_stale_fontspector_report(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import vf_ladder

    report = tmp_path / "fontspector-Roman.json"
    report.write_text('{"summary": {}, "results": {}}')

    def failed_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="failed")

    monkeypatch.setattr(vf_ladder.subprocess, "run", failed_run)
    with pytest.raises(RuntimeError, match=r"did not write its report \(exit 1\)"):
        vf_ladder.inspect_font("fontspector", tmp_path / "test.ttf", tmp_path, "Roman")
    assert not report.exists()


def test_ladder_source_failure_preserves_diagnostics(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import json
    from types import SimpleNamespace

    import vf_ladder

    rows: Diagnostics = [
        {"glyph": "gamma", "style": "Light", "weight": 300, "contours": 2}
    ]
    error_path = tmp_path / "Roman-compile-error.json"
    error_path.write_text('{"reason": "stale"}')

    class FailedCompiler:
        exitcode = 1

        def __init__(self, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            assert not error_path.exists()
            error_path.write_text(
                json.dumps({"reason": "gamma: topology differs", "diagnostics": rows})
            )

        def join(self) -> None:
            pass

        def close(self) -> None:
            pass

    def failed_context(method: str) -> SimpleNamespace:
        return SimpleNamespace(Process=FailedCompiler)

    monkeypatch.setattr(vf_ladder.multiprocessing, "get_context", failed_context)
    with pytest.raises(vf_ladder.CompatibilityError, match="gamma") as caught:
        vf_ladder.compiled_sources(False, tmp_path)
    assert caught.value.diagnostics == rows


def test_ladder_endpoint_regression() -> None:
    from vf_ladder import endpoint_regression

    # These are the frozen two-master endpoint measurements, in font units.
    values = {"400": {"max_units": 0.02}, "700": {"max_units": 0.5200000000000029}}
    assert endpoint_regression(values)
    # A 0.9-unit change stays below the card limit but must fail endpoint parity.
    values["700"]["max_units"] = 0.9
    assert not endpoint_regression(values)


def test_ladder_encoded_master_location() -> None:
    from vf_ladder import finding_identity, master_weight

    # F2Dot14 axis rounding puts these locations within one step of a master.
    assert master_weight(450.006103515625, B.MASTER_WEIGHTS) == 450
    assert master_weight(600.006103515625, B.MASTER_WEIGHTS) == 600
    assert master_weight(599.98779296875, B.MASTER_WEIGHTS) == 600
    assert master_weight(499.993896484375, B.WEIGHTS) == 500
    # A 0.1-weight offset exceeds one F2Dot14 step across the 300-unit span.
    with pytest.raises(ValueError, match="No source master"):
        master_weight(600.1, B.WEIGHTS)
    a = {"glyph": "test", "location": {"wght": 600.006103515625}}
    b = {"glyph": "test", "location": {"wght": 599.98779296875}}
    assert finding_identity(a) == finding_identity(b)
    b["location"]["wght"] = 425
    assert finding_identity(b)["location"]["wght"] == 425
    assert finding_identity(a) != finding_identity(b)


def test_ladder_shared_outlines_preserve_interpolation(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    from copy import deepcopy

    import vf_ladder
    from fontTools.varLib.instancer import instantiateVariableFont

    statics = local_test_fonts()
    for weight, source in statics.items():
        for name in ("alias", "different.delta", "different.metrics"):
            source["glyf"][name] = deepcopy(source["glyf"]["base"])
            source["hmtx"][name] = source["hmtx"]["base"]
        source["glyf"]["different.delta"].coordinates[0] = (
            (weight - 400) // 50,
            0,
        )
        advance, lsb = source["hmtx"]["base"]
        source["hmtx"]["different.metrics"] = advance + 1, lsb
        source.setGlyphOrder(
            [
                n
                for n in source.getGlyphOrder()
                if n not in ("alias", "different.delta", "different.metrics")
            ]
            + ["alias", "different.delta", "different.metrics"]
        )
    with monkeypatch.context() as context:
        context.setattr(vf_ladder, "reuse_identical_outlines", lambda font: {})
        font, _ = vf_ladder.build_vf(statics, list(B.MASTER_WEIGHTS), False, tmp_path)
    before = deepcopy(font)
    aliases = vf_ladder.reuse_identical_outlines(font)
    assert aliases == {"alias": "base"}
    assert not statics[400]["glyf"]["alias"].isComposite()
    path = tmp_path / "shared.ttf"
    font.save(path)
    with TTFont(path) as saved:
        for weight in (
            *B.MASTER_WEIGHTS,
            325,
            375,
            425,
            475,
            550,
            650,
            388.25,
            615.125,
        ):
            a = instantiateVariableFont(before, {"wght": weight})
            b = instantiateVariableFont(saved, {"wght": weight})
            for name in a.getGlyphOrder():
                assert list(a["glyf"][name].getCoordinates(a["glyf"])[0]) == list(
                    b["glyf"][name].getCoordinates(b["glyf"])[0]
                ), (weight, name)
                assert a["hmtx"][name] == b["hmtx"][name], (weight, name)


def test_ladder_measure_without_fontspector(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    old_interpolation = '{"remaining": 0, "source": "previous inspection"}\n'
    (tmp_path / "interpolation.json").write_text(old_interpolation)
    for italic in (False, True):
        statics = local_test_fonts()
        for weight, font in statics.items():
            font.save(tmp_path / f"{B.weight_style(weight, italic)}.ttf")
        suffix = "-Italic" if italic else ""
        statics[400].save(tmp_path / f"MachineMadeWarp{suffix}[wght].ttf")

    def worker(target: Callable[..., object], *args: object) -> object:
        if target is vf_ladder.rebuild_aligned_slope:
            return None
        assert target is vf_ladder.measure_slope
        return (
            {str(w): {"max_units": 0.02 if w == 400 else 0.52} for w in B.WEIGHTS},
            {"325": {"max_percent": 4.99, "passed": True}},
        )

    def forbid_inspection(*args: object) -> None:
        pytest.fail("Fontspector must not run in measurement mode")

    monkeypatch.setattr(vf_ladder, "worker_process", worker)
    monkeypatch.setattr(vf_ladder, "inspect_font", forbid_inspection)
    monkeypatch.setattr(vf_ladder, "proof_sheet", lambda paths, out: "sheet.png")
    assert (
        vf_ladder.main(
            ["--out", str(tmp_path), "--skip-fontspector", "--reuse-aligned-sources"]
        )
        == 0
    )
    report = json.loads((tmp_path / "ladder.json").read_text())
    assert report["numerical_passed"]
    assert report["verdict"] == "not verified"
    for row in report["styles"].values():
        assert not row["fontspector_complete"]
        assert not row["passed"]
        assert all(v is None for v in row["fontspector"].values())
        assert len(row["source_hashes_sha256"]) == 7
    assert (tmp_path / "interpolation.json").read_text() == old_interpolation
    source = tmp_path / "Light.ttf"
    original = source.read_bytes()
    source.write_bytes(original + b"\0")
    argv = ["--out", str(tmp_path), "--skip-fontspector", "--reuse-aligned-sources"]
    with pytest.raises(ValueError, match="Saved aligned source changed: Light.ttf"):
        vf_ladder.main(argv)
    failed = json.loads((tmp_path / "ladder.json").read_text())
    assert failed["verdict"] == "not verified"
    for slope in ("Roman", "Italic"):
        assert (
            failed["aligned_sources"][slope]["source_hashes_sha256"]
            == (report["styles"][slope]["source_hashes_sha256"])
        )
    source.write_bytes(original)
    assert vf_ladder.main(argv) == 0
    retried = json.loads((tmp_path / "ladder.json").read_text())
    for slope in ("Roman", "Italic"):
        assert (
            retried["styles"][slope]["source_hashes_sha256"]
            == (report["styles"][slope]["source_hashes_sha256"])
        )


@pytest.mark.parametrize("italic", (False, True))
def test_ladder_full_font_size(
    italic: bool, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import json

    import vf_ladder

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1793059200")
    report = json.loads(
        (Path(__file__).resolve().parents[2] / "proofs/warp/ladder.json").read_text()
    )["styles"]["Italic" if italic else "Roman"]
    # Reuse this process's heap rather than duplicating the compatibility
    # caches beside a source compiler. Release sweeps before varLib runs.
    vf_ladder.release_sources()
    vf_ladder.compile_sources(italic, tmp_path)
    vf_ladder.release_sources()
    statics = {
        weight: TTFont(tmp_path / f"{B.weight_style(weight, italic)}-source.ttf")
        for weight in B.MASTER_WEIGHTS
    }
    for weight, font in statics.items():
        if weight != 400:
            rotations = vf_ladder.align_static(
                font, statics[400], B.weight_style(weight, italic)
            )
            assert rotations == report["initial_rotations"][str(weight)]
    for _, batch in groupby(
        report["start_point_corrections"], key=lambda row: row["attempt"]
    ):
        vf_ladder.apply_corrections(statics, list(batch))
    font, path = vf_ladder.build_vf(statics, list(B.MASTER_WEIGHTS), italic, tmp_path)
    assert len(font.getGlyphOrder()) == 890
    assert path.stat().st_size <= 9_437_184
    # The frozen inputs predate the PANOSE metadata fix. Compare every compiled
    # outline and metric; the measurement-mode test guards saved file bytes.
    for name, expected in report["source_outline_hashes_sha256"].items():
        assert vf_ladder.source_outline_hash(tmp_path / name) == expected


def test_ladder_failed_run_invalidates_proof(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1793059200")
    for filename in ("ladder.json", "interpolation.json"):
        (tmp_path / filename).write_text('{"verdict": "verified"}')

    def fail(*args: object) -> None:
        raise ValueError("test failure")

    monkeypatch.setattr(vf_ladder, "run_slope", fail)
    with pytest.raises(ValueError, match="test failure"):
        vf_ladder.main(["--out", str(tmp_path / "build"), "--fontspector", "unused"])
    for filename in ("ladder.json", "interpolation.json"):
        report = json.loads((tmp_path / filename).read_text())
        assert report["verdict"] == "not verified"
        if filename == "interpolation.json":
            assert "baseline" not in report
            assert report["two_master_findings"] == 770
            assert report["two_master_source"] == vf_ladder.TWO_MASTER_SOURCE


def test_ladder_keeps_findings_when_second_slope_fails(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
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

    def run(italic: bool, *args: object) -> tuple[Record, list[Record], Path]:
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


def test_ladder_rejects_compiled_mismatch() -> None:
    from copy import deepcopy

    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable
    from loom.compatible import CompatibilityError
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
    with pytest.raises(
        CompatibilityError, match="compiled master structure differs"
    ) as caught:
        check_master_structure([font, other])
    rows = caught.value.diagnostics
    assert rows is not None
    assert [r["glyph"] for r in rows] == ["test", "test"]
    assert rows[0]["flags"] != rows[1]["flags"]


def local_test_fonts() -> dict[int, TTFont]:
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


def test_ladder_local_tuples_reproduce_composites(tmp_path: Path) -> None:
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.varLib.models import supportScalar
    from vf_ladder import build_vf
    from vf_spike import endpoint_difference

    statics = local_test_fonts()
    font, _ = build_vf(statics, list(B.MASTER_WEIGHTS), False, tmp_path)
    for weight in B.MASTER_WEIGHTS:
        instance = instantiateVariableFont(font, {"wght": weight})
        # The card allows 1.0 font unit; the measured ladder maximum is 0.547.
        assert endpoint_difference(instance, statics[weight])["max_units"] <= 1.0
        for name in instance.getGlyphOrder():
            assert instance["hmtx"][name][0] == statics[weight]["hmtx"][name][0]
    variations = font["gvar"].variations["accented"]
    # Seven sources need six local tuples around the default master.
    assert len(variations) == 6
    for variation in variations:
        assert None not in variation.coordinates
        peak = variation.axes["wght"][1]
        assert sum(supportScalar({"wght": peak}, v.axes) for v in variations) == 1


def test_ladder_axis_rounding_does_not_thin_midpoint_bar(tmp_path: Path) -> None:
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


def test_ladder_cpu_features() -> None:
    code = """
import hashlib
import json
from loom import build as B
from loom.compatible import aligned_start
import compat
h = hashlib.sha256()
for style in B.MASTER_STYLES:
    for name in (
        'a', 'iota', 'Xi', 'L', 'hungarumlautcomb.case', 'l.sc', 'hbar.sc',
        'theta.sc', 'ellipsis', 'eta', 'etatonos', 'u1D6EF', 'u1D702',
    ):
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


def test_ladder_midpoints_come_from_master_list() -> None:
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


def test_ladder_resolve_composite_keeps_translated_contours(tmp_path: Path) -> None:
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


@pytest.mark.parametrize("base_first", [True, False])
def test_ladder_replayed_corrections_rotate_composite_once(
    base_first: bool,
) -> None:
    import vf_ladder

    statics = local_test_fonts()
    glyf = statics[350]["glyf"]
    before = {
        name: list(glyf[name].getCoordinates(glyf)[0]) for name in ("base", "accented")
    }
    names = ("base", "accented") if base_first else ("accented", "base")
    corrections: list[Record] = [
        {"weight": 350, "glyph": name, "contour": 0, "shift": 1} for name in names
    ]
    vf_ladder.apply_corrections(statics, corrections)
    for name in ("base", "accented"):
        expected = before[name][1:4] + before[name][:1] + before[name][4:]
        assert list(glyf[name].coordinates) == expected, name
    assert all(not font["glyf"]["accented"].isComposite() for font in statics.values())


@pytest.mark.parametrize("base_first", [True, False])
def test_ladder_correction_rotates_base_and_composite_once(
    tmp_path: Path, monkeypatch: MonkeyPatch, base_first: bool
) -> None:
    import vf_ladder

    statics = local_test_fonts()
    weight = 350
    glyf = statics[weight]["glyf"]
    before = {
        name: list(glyf[name].getCoordinates(glyf)[0]) for name in ("base", "accented")
    }
    names = ("base", "accented") if base_first else ("accented", "base")
    rows: list[Record] = [
        {
            "weight": weight,
            "glyph": name,
            "slope": "Roman",
            "actual": {"contour_index": 0},
            "expected": {"reverse_contour": False, "proposed_start_point": 1},
        }
        for name in names
    ]

    def read(*args: object) -> dict[int, TTFont]:
        return statics

    builds = []

    def build(*args: object) -> None:
        builds.append(args)

    monkeypatch.setattr(vf_ladder, "read_aligned_sources", read)
    monkeypatch.setattr(vf_ladder, "build_vf", build)
    corrections = vf_ladder.correct_slope(rows, B.MASTER_WEIGHTS, False, tmp_path, 0)
    assert [row["glyph"] for row in corrections] == list(names)
    assert len(builds) == 1
    for name in ("base", "accented"):
        # Each synthetic square has four points; rotate its first contour once.
        expected = before[name][1:4] + before[name][:1] + before[name][4:]
        assert list(glyf[name].coordinates) == expected, name
    assert all(not f["glyf"]["accented"].isComposite() for f in statics.values())


def test_ladder_stroke_union_keeps_iota_ink() -> None:
    from loom import outline as O
    from loom.compatible import incremental_stroke_contours, polygon

    d = B.drawn(B.weight_style(450), "iota")
    batch_area = sum(abs(O.signed_area(polygon(c)[0])) for c in d.contours)
    repaired = incremental_stroke_contours(d, "iota")
    # The batch union splits iota; joining hulls in order must keep one stroke.
    assert len(d.contours) == 2
    assert len(repaired) == 1
    area = abs(O.signed_area(polygon(repaired[0])[0]))
    # The independent hull union measures 41063.531 square font units.
    assert 41000 < area < 41100
    # The cancelled stroke loses over 15000 square font units in the batch union.
    assert area > batch_area + 15000


def test_ladder_new_warning_blocks_verdict_and_keeps_baseline(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
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

    def sheet(*args: object) -> str:
        return "proof.png"

    monkeypatch.setattr(vf_ladder, "proof_sheet", sheet)

    def run(italic: bool, *args: object) -> tuple[Record, list[Record], Path]:
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


def test_ladder_fontspector_keeps_font_problem_glyphs() -> None:
    from vf_ladder import fontspector_findings

    def report(names: list[str]) -> Record:
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
    # Adding one unreachable glyph must add exactly one warning identity.
    assert len(added) == 1
    assert added[0]["glyph"] == "newpart"


def test_ladder_worker_returns_results_and_errors() -> None:
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


def test_ladder_failed_inspection_keeps_measurements(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import vf_ladder

    instances = {str(w): {"max_units": 0.02} for w in B.WEIGHTS}
    fidelities = {"325": {"passed": True}}

    def worker(
        target: Callable[..., object], *args: object
    ) -> dict[str, Record] | tuple[dict[str, Record], dict[str, Record]]:
        if target is vf_ladder.prepare_slope:
            return {}
        assert target is vf_ladder.measure_slope
        return instances, fidelities

    def inspect(*args: object) -> None:
        raise RuntimeError("no report (exit -9)")

    monkeypatch.setattr(vf_ladder, "worker_process", worker)
    monkeypatch.setattr(vf_ladder, "inspect_font", inspect)
    statics = local_test_fonts()
    for weight, font in statics.items():
        font.save(tmp_path / f"{B.weight_style(weight)}.ttf")
    statics[400].save(tmp_path / "MachineMadeWarp[wght].ttf")
    report, findings, _ = vf_ladder.run_slope(False, tmp_path, "unused")
    assert report["instances"] == instances
    assert report["fidelity"] == fidelities
    assert not report["fontspector_complete"]
    assert all(value is None for value in report["fontspector"].values())
    assert "exit -9" in report["fontspector_error"]
    assert not report["passed"]
    assert findings == []


def test_ladder_incomplete_inspection_does_not_claim_zero_findings(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    import json

    import vf_ladder

    monkeypatch.setattr(vf_ladder, "PROOFS", tmp_path)

    def sheet(*args: object) -> str:
        return "proof.png"

    monkeypatch.setattr(vf_ladder, "proof_sheet", sheet)

    def incomplete_slope(*args: object) -> tuple[Record, list[Record], Path]:
        return (
            {"passed": False, "fontspector_complete": False},
            [],
            tmp_path / "font.ttf",
        )

    monkeypatch.setattr(vf_ladder, "run_slope", incomplete_slope)
    assert vf_ladder.main(["--out", str(tmp_path), "--fontspector", "unused"]) == 1
    report = json.loads((tmp_path / "interpolation.json").read_text())
    assert not report["complete"]
    assert report["remaining"] is None
    assert report["start_point_count"] is None
