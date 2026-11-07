# SPDX-License-Identifier: Apache-2.0
"""Compatibility gates and the default build guard. Apache-2.0."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from fontmake.font_project import FontProject
from fontTools.ttLib import TTFont
from loom import build as Bd

WARP = Path(__file__).resolve().parents[1]
ROOT = WARP.parent
sys.path.insert(0, str(WARP / "tools"))

import compat
from finish import finish_static


def test_compat_default_counts():
    report = compat.compare(["a", "g", "Xi"])
    assert (
        report["glyphs"],
        report["contours_compatible"],
        report["point_compatible"],
    ) == (3, 2, 0)
    assert [r["contour_counts"] for r in report["rows"]] == [[2, 2], [3, 3], [3, 3]]
    assert report["rows"][2]["first_mismatch"] == {
        "contour": 0,
        "reason": "different contour order",
    }
    counts = [
        [[c["points"] for c in row["masters"][style]] for style in ("Regular", "Bold")]
        for row in report["rows"]
    ]
    assert counts == [
        [[79, 19], [81, 23]],
        [[104, 38, 33], [112, 34, 21]],
        [[42, 42, 58], [42, 42, 46]],
    ]


def test_compat_hard_glyphs():
    report = compat.compare(compat.HARD, compatible=True)
    bad = [r["name"] for r in report["rows"] if not r["point_compatible"]]
    assert report["point_compatible"] == report["glyphs"], (
        f"Incompatible glyphs: {', '.join(bad)}"
    )


def test_compat_default_build_bytes(tmp_path, monkeypatch):
    """Compile one full style with the release's shared family metrics."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1793059200")
    reference = ROOT / "fonts/warp/ttf/MachineMadeWarp-Regular.ttf"
    ufo = Bd.build_font("Regular")
    # The release gets these two fields from all six styles. Keep that
    # family metadata for this one-style check; rebuild every outline.
    with TTFont(reference) as committed:
        ufo.info.openTypeOS2WinAscent = committed["OS/2"].usWinAscent
        ufo.info.openTypeOS2WinDescent = committed["OS/2"].usWinDescent
    raw, hinted = tmp_path / "raw.ttf", tmp_path / "Regular.ttf"
    FontProject().run_from_ufos(
        [ufo], output=("ttf",), remove_overlaps=False, output_path=str(raw)
    )
    subprocess.run(
        [sys.executable, "-m", "ttfautohint", "--no-info", str(raw), str(hinted)],
        check=True,
        capture_output=True,
    )
    finish_static(hinted)
    actual = hashlib.sha256(hinted.read_bytes()).hexdigest()
    expected = hashlib.sha256(reference.read_bytes()).hexdigest()
    assert actual == expected, "Fresh Regular bytes differ from the committed font"


def test_compat_cpu_features():
    """Check both methods, all hard contours, and rounding on both CPU paths."""
    code = """
import hashlib
from loom import build as B
from loom.compatible import pair
from compat import HARD
h = hashlib.sha256()
for method in ('sample', 'refit'):
    for name in HARD:
        for cs in pair(name, method):
            for c in cs:
                for s in c:
                    h.update(s[0].encode())
                    for p in s[1:]:
                        h.update(p.tobytes())
print(h.hexdigest())
"""
    hashes = []
    for disabled in (False, True):
        env = dict(os.environ)
        env.pop("NPY_DISABLE_CPU_FEATURES", None)
        if disabled:
            env["NPY_DISABLE_CPU_FEATURES"] = "X86_V4 AVX512_ICL AVX512_SKX AVX512F"
        env["PYTHONPATH"] = os.pathsep.join((str(WARP), str(WARP / "tools")))
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        hashes.append(result.stdout.strip())
    assert hashes[0] == hashes[1], "Compatible outlines depend on CPU features"


def test_compat_preserves_contour_topology():
    """A change in winding must not be hidden by adding a zero-area contour."""
    for name in ("germandbls", "fi", "f_f_l"):
        for style in ("Regular", "Bold"):
            default = compat.structure(Bd.drawn(style, name).contours)
            fixed = compat.structure(Bd.drawn(style, name, compatible=True).contours)
            assert default == fixed


def test_compat_detects_contour_order():
    import numpy as np

    def square(y):
        p = np.array([(0, y), (10, y), (10, y + 10), (0, y + 10)], dtype=float)
        return [("line", p[i], p[(i + 1) % 4]) for i in range(4)]

    a, b = square(0), square(20)
    assert compat.structure([a, b]) != compat.structure([b, a])


def test_compat_cli(tmp_path):
    output = tmp_path / "compat.json"
    result = subprocess.run(
        [
            sys.executable,
            str(WARP / "tools/compat.py"),
            "--glyphs",
            "a,g,Xi",
            "--out",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        result.stdout.strip() == "glyphs 3, contours-compatible 2, point-compatible 0"
    )
    assert output.is_file()


def test_compat_invalid_styles_keep_output(tmp_path):
    import pytest

    out = tmp_path / "ufo"
    out.mkdir()
    marker = out / "keep"
    marker.write_text("keep")
    with pytest.raises(SystemExit):
        Bd.main(["--compatible", "--out", str(tmp_path)])
    assert marker.read_text() == "keep"


def test_compat_difference_has_error_bound(monkeypatch):
    import vf_spike

    class Font:
        def getGlyphOrder(self):
            return ["a"]

    monkeypatch.setattr(vf_spike, "boundary", lambda font, name: [])
    monkeypatch.setattr(vf_spike, "directed_distance", lambda source, target: 1.0)
    result = vf_spike.difference(Font(), Font())
    assert result["sampled_max_units"] == 1.0
    assert result["max_units"] > 1.0
