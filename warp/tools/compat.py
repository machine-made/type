# SPDX-License-Identifier: Apache-2.0
"""Compare the Regular and Bold outline structure. Apache-2.0."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build as Bd
from loom import charset as CS
from loom import outline as O
from loom.compatible import contour_key, polygon

HARD = [CS.glyph_name(c) for c in "gaesß&?@ﬁﬄΞΣ∫∑√ıȷQRk"]
REPORT = Path(__file__).resolve().parents[2] / "proofs/warp/compat.json"


def contours(style, name, compatible=False, method="sample"):
    gl = CS.BY_NAME[name]
    if gl.comps:
        parts, _ = Bd.component_offsets(style, gl)
        result = []
        for base, dx, dy in Bd.flatten(style, parts):
            for contour in contours(style, base, compatible, method):
                result.append(
                    [
                        (s[0], s[1] + (dx, dy), s[2] + (dx, dy))
                        if s[0] == "line"
                        else (s[0], s[1] + (dx, dy))
                        for s in contour
                    ]
                )
        return result
    return Bd.drawn(style, name, compatible=compatible, method=method).contours


def structure(cs):
    result = []
    polygons = [polygon(c)[0] for c in cs]
    ordered = sorted(range(len(cs)), key=lambda i: contour_key(polygons[i]))
    for i, (c, points) in enumerate(zip(cs, polygons)):
        area = O.signed_area(points)
        result.append(
            {
                "order": ordered.index(i),
                "points": sum(1 if s[0] == "line" else 3 for s in c),
                "segments": [
                    [kind, sum(1 for _ in group)]
                    for kind, group in groupby(s[0] for s in c)
                ],
                "winding": 1 if area > 0 else -1 if area < 0 else 0,
            }
        )
    return result


def compare(names=None, compatible=False, method="sample"):
    rows = []
    for name in CS.ORDER if names is None else names:
        pair = [
            structure(contours(style, name, compatible, method))
            for style in ("Regular", "Bold")
        ]
        a, b = pair
        mismatch = None
        contour_ok = len(a) == len(b)
        if not contour_ok:
            mismatch = {"reason": "different contour count"}
        for i, (ca, cb) in enumerate(zip(a, b)):
            if ca["winding"] != cb["winding"]:
                contour_ok = False
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different winding or contour order",
                }
            elif ca["order"] != cb["order"]:
                contour_ok = False
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different contour order",
                }
            elif ca["points"] != cb["points"]:
                mismatch = mismatch or {"contour": i, "reason": "different point count"}
            elif ca["segments"] != cb["segments"]:
                mismatch = mismatch or {
                    "contour": i,
                    "reason": "different segment types",
                }
        rows.append(
            {
                "name": name,
                "contour_counts": [len(a), len(b)],
                "masters": dict(zip(("Regular", "Bold"), pair)),
                "contours_compatible": contour_ok,
                "point_compatible": mismatch is None,
                "first_mismatch": mismatch,
            }
        )
    return {
        "method": method if compatible else "default",
        "scope": "full" if names is None else list(names),
        "glyphs": len(rows),
        "contours_compatible": sum(r["contours_compatible"] for r in rows),
        "point_compatible": sum(r["point_compatible"] for r in rows),
        "rows": rows,
    }


def summary(report):
    return (
        f"glyphs {report['glyphs']}, contours-compatible {report['contours_compatible']}, "
        f"point-compatible {report['point_compatible']}"
    )


def write_report(path, data):
    """Keep one glyph per line so that changes in the proof can be read."""
    sections = []
    for mode, report in data.items():
        counts = {key: value for key, value in report.items() if key != "rows"}
        head = json.dumps(counts, ensure_ascii=False)[:-1]
        rows = ",\n".join(
            "  " + json.dumps(row, ensure_ascii=False) for row in report["rows"]
        )
        sections.append(f' "{mode}": {head}, "rows": [\n{rows}\n ]}}')
    path.write_text("{\n" + ",\n".join(sections) + "\n}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixed", "--compatible", action="store_true")
    ap.add_argument("--method", choices=("sample", "refit"), default="sample")
    ap.add_argument(
        "--glyphs",
        help="Comma-separated glyph names; the default is the full glyph set.",
    )
    ap.add_argument("--out", type=Path, default=REPORT)
    args = ap.parse_args(argv)
    report = compare(
        args.glyphs.split(",") if args.glyphs else None, args.fixed, args.method
    )
    print(summary(report), flush=True)
    data = json.loads(args.out.read_text()) if args.out.exists() else {}
    data["fixed" if args.fixed else "default"] = report
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_report(args.out, data)
    return int(args.fixed and report["point_compatible"] != report["glyphs"])


if __name__ == "__main__":
    raise SystemExit(main())
