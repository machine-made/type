"""Choose the drift attempt of every glyph and write loom/drift_lock.json.

Usage:
    python tools/relock.py

Run this after a change to the stroke tables or to loom/pieces.py. For
each glyph it takes the first drift attempt that passes the fontTools
interpolatable check (see loom/interp.py). The build reads the file, so
it does not need to search again. The tests check that the file is
current.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build, interp, pieces  # noqa: E402


def main() -> int:
    attempts = {}
    for name in build.drawn_names():
        gp = pieces.plan_glyph(name, build.strokes_of(name))
        attempt = interp.make_clean(gp, build.to_font, contours=build.plan_contours)
        if attempt:
            attempts[name] = attempt
    out = Path(build.__file__).with_name("drift_lock.json")
    out.write_text(json.dumps({
        "about": "Drift attempt per glyph (0 if not listed). Made by tools/relock.py.",
        "seed": pieces.SEED,
        "attempts": dict(sorted(attempts.items())),
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out} ({len(attempts)} glyphs need a new drift attempt).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
