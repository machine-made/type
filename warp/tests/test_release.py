# SPDX-License-Identifier: Apache-2.0
"""Exercise the release archive and reject missing or altered variable fonts."""

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def package(root, out):
    return subprocess.run(
        [
            "bash",
            str(root / ".github/scripts/package_release.sh"),
            "warp",
            "0.3.0",
            str(out),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def readability_report(tmp_path_factory):
    report = tmp_path_factory.mktemp("ocr") / "readability.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "warp/tools/readability.py"),
            "--gate",
            "--out",
            str(report),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return report


def test_release_archive(tmp_path, readability_report):
    out = tmp_path / "release"
    out.mkdir()
    shutil.copy2(readability_report, out / "readability.json")
    result = package(ROOT, out)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(out / "machine-made-warp-0.3.0.zip") as archive:
        archive.extractall(tmp_path / "unpacked")
    folder = tmp_path / "unpacked/machine-made-warp-0.3.0"
    expected = {
        p.relative_to(ROOT / "fonts/warp").as_posix()
        for p in (ROOT / "fonts/warp").rglob("*")
        if p.suffix in {".ttf", ".otf", ".woff2"}
    }
    assert len(expected) == 22
    sums = dict(
        line.split("  ", 1)[::-1]
        for line in (folder / "SHA256SUMS").read_text().splitlines()
    )
    assert set(sums) == expected
    for name, digest in sums.items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
        assert (folder / name).read_bytes() == (ROOT / "fonts/warp" / name).read_bytes()
    for name in ("OFL.txt", "RELEASE-NOTES.md", "readability.json"):
        assert (folder / name).is_file()
    pins = json.loads((ROOT / "proofs/warp/release.json").read_text())
    for name, row in pins["variable_fonts"].items():
        assert sums[f"vf/{name}"] == row["sha256"]
    first_zip = (out / "machine-made-warp-0.3.0.zip").read_bytes()
    assert package(ROOT, out).returncode == 0  # Repeat in the same output folder.
    assert (out / "machine-made-warp-0.3.0.zip").read_bytes() == first_zip
    subprocess.run(
        ["sha256sum", "-c", "SHA256SUMS"],
        cwd=out,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("damage", ["missing", "hash", "web", "ladder"])
def test_release_rejects_damaged_variable_font(tmp_path, damage, readability_report):
    root = tmp_path / "tree"
    for rel in ("fonts/warp", "proofs/warp", "warp"):
        # The fonts and proofs are small compared with build intermediates.
        source = ROOT / rel
        if rel == "warp":
            (root / rel).mkdir(parents=True)
            for name in ("OFL.txt", "RELEASE-NOTES-0.3.md"):
                shutil.copy2(source / name, root / rel / name)
        else:
            shutil.copytree(source, root / rel)
    script = root / ".github/scripts/package_release.sh"
    script.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".github/scripts/package_release.sh", script)
    out = tmp_path / "release"
    out.mkdir()
    shutil.copy2(readability_report, out / "readability.json")
    font = root / "fonts/warp/vf/MachineMadeWarp[wght].ttf"
    if damage == "missing":
        font.unlink()
    elif damage == "hash":
        data = bytearray(font.read_bytes())
        data[-1] ^= 1  # Keep the size unchanged to exercise the hash check.
        font.write_bytes(data)
    elif damage == "web":
        shutil.copy2(
            root / "fonts/warp/vf/MachineMadeWarp-Italic[wght].woff2",
            font.with_suffix(".woff2"),
        )
    else:
        path = root / "proofs/warp/ladder.json"
        proof = json.loads(path.read_text())
        proof["styles"]["Roman"]["file_size_bytes"] += 1
        path.write_text(json.dumps(proof))
    result = package(root, out)
    assert result.returncode != 0
    assert "error:" in result.stderr
    assert not (out / "machine-made-warp-0.3.0.zip").exists()


@pytest.mark.parametrize("passed", [True, False])
def test_clean_measurement_preserves_inspected_proofs(tmp_path, monkeypatch, passed):
    sys.path.insert(0, str(ROOT / "warp/tools"))
    import vf_ladder

    proofs, out = tmp_path / "proofs", tmp_path / "output"
    shutil.copytree(ROOT / "proofs/warp", proofs)
    originals = {p.name: p.read_bytes() for p in proofs.iterdir() if p.is_file()}
    monkeypatch.setattr(vf_ladder, "PROOFS", proofs)
    seen = []

    def measure(italic, folder, executable, release_proof):
        assert executable is None
        seen.append(release_proof)
        path = folder / f"test-{italic}.ttf"
        path.write_bytes(b"measured")
        return (
            dict(
                source_hashes_sha256={},
                source_outline_hashes_sha256={},
                file_size_bytes=8,
                instances={},
                fidelity={},
                numerical_passed=passed,
            ),
            [],
            path,
        )

    monkeypatch.setattr(vf_ladder, "run_slope", measure)
    assert vf_ladder.main(["--skip-fontspector", "--out", str(out)]) == int(not passed)
    assert len(seen) == 2
    assert {
        p.name: p.read_bytes() for p in proofs.iterdir() if p.is_file()
    } == originals
    measured = json.loads((out / "release.json").read_text())
    assert "verdict" not in measured
    assert all("fontspector" not in row for row in measured["styles"].values())
