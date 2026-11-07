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
import json
import numpy as np
import vf_spike
from loom import build as B
from loom.compatible import TOPOLOGY, pair
from compat import HARD
h = hashlib.sha256()
for method in ('sample', 'refit'):
    for name in sorted(set(HARD) | TOPOLOGY):
        for cs in pair(name, method):
            for c in cs:
                for s in c:
                    h.update(s[0].encode())
                    for p in s[1:]:
                        h.update(p.tobytes())
class Font:
    def getGlyphOrder(self):
        return ['a']
a, b = Font(), Font()
square = np.array([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], dtype=float)
vf_spike.boundary = lambda f, n: [square + (0.6 if f is a else 0)]
h.update(json.dumps(vf_spike.endpoint_difference(a, b), sort_keys=True).encode())
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


def test_compat_keeps_previous_875_outlines():
    """Frozen float-coordinate hashes from the first sampling experiment."""
    from loom import charset as CS
    from loom.compatible import TOPOLOGY

    changed = TOPOLOGY | {"iotadieresistonos", "upsilondieresistonos"}
    names = sorted(set(CS.ORDER) - changed)
    assert len(names) == 875
    expected = {
        "Regular": "c6a2ee0e36f73b7aa505f3c0bce59c67ea44e72ff0447a5157502b60bd99024f",
        "Bold": "37d277bfa532d1e428fb560ace6e87433d02d30f0454edc3d9ff77c812cd3038",
    }
    for style, digest in expected.items():
        total = hashlib.sha256()
        for name in names:
            h = hashlib.sha256()
            for contour in compat.contours(style, name, True):
                for segment in contour:
                    h.update(segment[0].encode())
                    for points in segment[1:]:
                        h.update(points.tobytes())
            total.update(f"{style}/{name}".encode())
            total.update(h.hexdigest().encode())
        assert total.hexdigest() == digest, style


def test_compat_preserves_contour_topology():
    """Use real stroke contours, with every source hull kept exactly once."""
    from loom import outline as O
    from loom.compatible import (
        TOPOLOGY,
        contour_key,
        polygon,
        stroke_contours,
        stroke_groups,
    )

    for name in TOPOLOGY:
        report = compat.compare([name], compatible=True)
        assert report["point_compatible"] == 1
        source_orders = []
        for style in ("Regular", "Bold"):
            d = Bd.drawn(style, name)
            hulls = [p for group in stroke_groups(d, name) for p in group]
            assert hulls == d.sweep.polys
            fixed = Bd.drawn(style, name, compatible=True).contours
            assert all(O.signed_area(polygon(c)[0]) > 0 for c in fixed)
            source = stroke_contours(d, name)
            source_orders.append(
                sorted(
                    range(len(source)), key=lambda i: contour_key(polygon(source[i])[0])
                )
            )
        assert source_orders[0] == source_orders[1], name


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

    import numpy as np

    instance, static = Font(), Font()
    monkeypatch.setattr(
        vf_spike, "boundary", lambda font, name: [np.array([[font is instance, 0]])]
    )
    monkeypatch.setattr(vf_spike, "directed_distance", lambda source, target: 1.0)
    result = vf_spike.difference(instance, static)
    assert result["sampled_max_units"] == 1.0
    assert result["max_units"] > 1.0


def test_compat_identical_boundaries(monkeypatch):
    import numpy as np
    import vf_spike

    class Font:
        def getGlyphOrder(self):
            return ["a"]

    monkeypatch.setattr(vf_spike, "boundary", lambda font, name: [np.array([[1, 2]])])
    result = vf_spike.difference(Font(), Font())
    assert result["sampled_max_units"] == 0


def test_compat_fidelity_subset(monkeypatch):
    """The hard-glyph trial contains only part of the full glyph set."""
    import ufoLib2
    import vf_spike
    from ufo2ft import compileTTF

    ufo = ufoLib2.Font()
    Bd.set_info(ufo, Bd.STYLES["Regular"])
    ufo.newGlyph(".notdef")
    font = compileTTF(ufo, removeOverlaps=False)
    monkeypatch.setattr(
        vf_spike.fidelity, "compare", lambda style, f: {"a": {"16": 0.0}}
    )
    assert vf_spike.fidelity_report([font], ["Regular"])["Regular"]["pass"]


def test_compat_endpoint_bound(monkeypatch):
    import numpy as np
    import pytest
    import vf_spike

    class Font:
        def getGlyphOrder(self):
            return ["a"]

    a, b = Font(), Font()
    square = np.array([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], dtype=float)
    monkeypatch.setattr(
        vf_spike, "boundary", lambda f, n: [square + (0.6 if f is a else 0)]
    )
    result = vf_spike.endpoint_difference(a, b)
    assert result["vertex_bound_units"] == pytest.approx(0.6 * 2**0.5)
    assert result["max_units"] > result["vertex_bound_units"]
    monkeypatch.setattr(
        vf_spike, "boundary", lambda f, n: [square if f is a else square[:3]]
    )
    with pytest.raises(ValueError, match="Endpoint structure differs"):
        vf_spike.endpoint_difference(a, b)
