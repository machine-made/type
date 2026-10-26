"""Add a STAT table to the compiled static fonts.

Usage:
    python tools/finish.py ../fonts/weft/Weft-Regular.ttf ../fonts/weft/Weft-Regular.otf

Phase 1 has one static master. The STAT table names its position on the
future wght axis (400, Regular, elidable). Phase 2 builds the variable
font, and fontmake then writes STAT from the designspace.
"""

from __future__ import annotations

import sys

from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont

AXES = [
    {
        "tag": "wght",
        "name": "Weight",
        "values": [
            {"value": 400, "name": "Regular", "flags": 0x2},
        ],
    },
]


def finish(path: str) -> None:
    font = TTFont(path)
    buildStatTable(font, AXES, elidedFallbackName=2, macNames=False)
    font.save(path)
    print(f"Added STAT to {path}.")


def main(argv: list[str]) -> int:
    if not argv:
        print("Error: give one or more font files.", file=sys.stderr)
        return 2
    for path in argv:
        finish(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
