"""Shared fixtures for the machine-made Sans tests.

Set SANS_UPSTREAM to a checkout of tokotype/PlusJakartaSans at the
pinned commit (sans/upstream/UPSTREAM.txt). Tests that need it skip
when it is not set.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SANS = ROOT / "sans"
FONTS = ROOT / "fonts" / "sans"
sys.path.insert(0, str(SANS / "scripts"))

UPSTREAM_COMMIT = "18d1cd2f7ea10481919d2f05c1f7064b7307fc26"


@pytest.fixture(scope="session")
def upstream() -> Path:
    value = os.environ.get("SANS_UPSTREAM")
    if not value:
        pytest.skip("SANS_UPSTREAM is not set.")
    path = Path(value)
    if not (path / "sources" / "PlusJakartaSans.glyphs").exists():
        pytest.fail(f"SANS_UPSTREAM={path} has no sources/PlusJakartaSans.glyphs.")
    return path
