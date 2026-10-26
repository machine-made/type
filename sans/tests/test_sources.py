"""Tests for the sources and the fork script."""

from __future__ import annotations

import re
import subprocess
import sys

import glyphsfmt
import pytest
from conftest import ROOT, SANS, UPSTREAM_COMMIT

SOURCES = [SANS / "sources" / "MachineMadeSans.glyphs", SANS / "sources" / "MachineMadeSans-Italic.glyphs"]


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_writer_round_trip(path):
    text = path.read_text(encoding="utf-8")
    assert glyphsfmt.dumps(glyphsfmt.loads(text), text) == text


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_no_upstream_family_name(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    assert data["familyName"] == "machine-made Sans"
    for prop in data["properties"]:
        if prop["key"] == "copyrights":
            continue  # The upstream copyright line must stay.
        values = [prop.get("value")] + [v["value"] for v in prop.get("values", [])]
        for v in values:
            if prop["key"] == "descriptions" or prop["key"] == "designers":
                continue  # Credit text names the upstream.
            assert not v or "Jakarta" not in v, prop


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_copyright_lines(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    text = next(p for p in data["properties"] if p["key"] == "copyrights")["values"][0]["value"]
    assert "Copyright 2020 The Plus Jakarta Sans Project Authors (https://github.com/tokotype/PlusJakartaSans)" in text
    assert "Copyright 2026 The machine-made Sans Project Authors" in text


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_line_metrics(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    for master in data["fontMaster"]:
        params = {p["name"]: p["value"] for p in master["customParameters"]}
        assert params["typoAscender"] == 875
        assert params["typoDescender"] == -281
        assert params["typoLineGap"] == 0
        assert params["hheaAscender"] == 875
        assert params["hheaDescender"] == -281
        assert params["hheaLineGap"] == 0


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_stylistic_sets_named(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    feats = {f["tag"]: f for f in data["features"]}
    for tag in ("ss01", "ss02", "ss03"):
        assert feats[tag]["labels"][0]["value"], tag
        assert "automatic" not in feats[tag], tag


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_every_component_exists(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    names = {g["glyphname"] for g in data["glyphs"]}
    for g in data["glyphs"]:
        for layer in g["layers"]:
            for s in layer.get("shapes", []):
                if "ref" in s:
                    assert s["ref"] in names, (g["glyphname"], s["ref"])


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.name)
def test_feature_glyphs_exist(path):
    data = glyphsfmt.loads(path.read_text(encoding="utf-8"))
    names = {g["glyphname"] for g in data["glyphs"]}
    for f in data["features"]:
        if f["tag"] not in ("ss01", "ss02", "ss03", "liga"):
            continue
        for tok in re.findall(r"[A-Za-z][A-Za-z0-9_.]*", f["code"]):
            if tok in ("sub", "by", "lookupflag", "IgnoreMarks"):
                continue
            assert tok in names, (f["tag"], tok)


def test_upstream_commit_recorded():
    text = (SANS / "upstream" / "UPSTREAM.txt").read_text(encoding="utf-8")
    assert UPSTREAM_COMMIT in text


def test_fork_is_reproducible(upstream, tmp_path):
    """The committed sources are the output of fork.py on the pinned upstream."""
    head = subprocess.run(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert head == UPSTREAM_COMMIT
    subprocess.run(
        [sys.executable, str(SANS / "scripts" / "fork.py"), str(upstream / "sources"), str(tmp_path)],
        check=True,
        cwd=ROOT,
    )
    for path in SOURCES:
        made = (tmp_path / path.name).read_text(encoding="utf-8")
        assert made == path.read_text(encoding="utf-8"), f"{path.name} differs from the fork.py output."
