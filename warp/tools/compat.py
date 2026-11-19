# SPDX-License-Identifier: Apache-2.0
"""Compare outline structure for two masters or all text styles. Apache-2.0."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import groupby
from pathlib import Path
from typing import Any, NotRequired, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loom import build as Bd
from loom import charset as CS
from loom import outline as O
from loom.compatible import (
    ITALIC_TOPOLOGY,
    TOPOLOGY,
    UNION_REPAIRS,
    Contour,
    contour_key,
    polygon,
)

HARD = [CS.glyph_name(c) for c in "gaesß&?@ﬁﬄΞΣ∫∑√ıȷQRk"]
REPORT = Path(__file__).resolve().parents[2] / "proofs/warp/compat.json"
CAUSES = {
    "germandbls": "The lower bowl joins the stem foot and encloses a counter.",
    "f_f": "The two foot serifs join and enclose a second counter below the bar.",
    "fi": "The foot serifs of f and i join the two outer contours.",
    "fl": "The f terminal joins the l stem, joining the two outer contours.",
    "f_f_i": "The two f feet join and enclose a second counter; then the i foot joins the f feet.",
    "f_f_l": "The two f feet join and enclose a second counter; then the f terminal joins the l stem.",
    "gamma": "The loop counter falls below the 40 square unit area filter; this is not its geometric closure.",
    "kappa": "The stem and two arms enclose a counter at their junction.",
    "dieresistonos": "The tonos joins the right dot, joining two outer contours.",
    "dieresistonoscomb": "The tonos joins the right dot, joining two outer contours.",
    "u1D43F": "The foot curl joins the stem turn and encloses a counter.",
    "u1D6FE": "The loop counter falls below the 40 square unit area filter; this is not its geometric closure.",
    "u1D705": "The stem and two arms enclose a counter at their junction.",
}


def topology_measurements() -> dict[str, TopologyMeasurements]:
    """Locate union changes along a stated engine-parameter path.

    Scan every integer weight, then bracket each change to 1/128 weight
    unit. These are generated sweeps, not interpolated VF outlines.
    """
    from loom import engine as E
    from loom.latin_ext import mathit_def

    result: dict[str, TopologyMeasurements] = {}
    for name in sorted(TOPOLOGY):
        gl = CS.BY_NAME[name]

        def state(weight: float, gl: CS.Glyph = gl) -> list[TopologyShape]:
            p = E.params(opsz=Bd.TEXT_OPSZ, **Bd.weight_params(weight))
            if gl.variant == "mathit":
                key = Bd.mathit_key(gl.key)
                definition = mathit_def(key)
                mods = {"p": {"bk": 0}} if definition.cap and key not in Bd.GI else {}
            else:
                definition = Bd.table_def(gl.key, False)
                mods = Bd.variant_mods(gl, p)
            sw = E.compose(definition, p, mods)
            shapes: list[TopologyShape] = []
            for points in O.path_polygons(O.union(sw.polys)):
                area = O.signed_area(points)
                if abs(area) < O.MIN_AREA:
                    continue
                shapes.append(
                    {
                        "winding": 1 if area > 0 else -1,
                        "area": round(area, 3),
                        "bounds": [
                            round(v, 3)
                            for v in (
                                min(float(q[0]) for q in points),
                                min(float(q[1]) for q in points),
                                max(float(q[0]) for q in points),
                                max(float(q[1]) for q in points),
                            )
                        ],
                    }
                )
            return sorted(shapes, key=lambda s: (-s["winding"], s["bounds"]))

        def signature(shapes: list[TopologyShape]) -> list[int]:
            return [s["winding"] for s in shapes]

        first = previous = state(400)
        events: list[TopologyTransition] = []
        for weight in range(401, 701):
            current = state(weight)
            if signature(current) != signature(previous):
                lo, hi = float(weight - 1), float(weight)
                left, right = previous, current
                for _ in range(7):
                    mid = (lo + hi) / 2
                    middle = state(mid)
                    if signature(middle) == signature(left):
                        lo, left = mid, middle
                    else:
                        hi, right = mid, middle
                events.append(
                    {"weight_interval": [lo, hi], "before": left, "after": right}
                )
            previous = current
        result[name] = {
            "cause": CAUSES[name],
            "policy": "a: separate overlapping stroke contours",
            "parts": (
                "Split the loop stroke at its bottom node; keep both runs and the diagonal separate"
                if name in ("gamma", "u1D6FE")
                else "Keep each source stroke, dot, terminal and bracket separate"
            ),
            "weight_path": "Linear engine parameters from Regular to Bold at opsz 10; integer scan, brackets at 1/128 weight unit",
            "area_filter": O.MIN_AREA,
            "contour_counts": [len(first), len(previous)],
            "endpoints": {"400": first, "700": previous},
            "transitions": events,
        }
    for name in ("iotadieresistonos", "upsilondieresistonos"):
        mark = result["dieresistonoscomb"]
        result[name] = {
            **mark,
            "policy": "a: separate mark strokes in the existing composite",
            "base": CS.BY_NAME[name].comps[0],
            "contour_counts": [n + 1 for n in mark["contour_counts"]],
            "measurement_scope": "Mark only; the base keeps its one outer contour",
        }
    return result


def contours(
    style: str, name: str, compatible: bool = False, method: str = "sample"
) -> list[Contour]:
    gl = CS.BY_NAME[name]
    if gl.variant == "mathit" and Bd.STYLES[style].italic:
        return contours(style, CS.glyph_name(gl.key), compatible, method)
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


def structure(cs: list[Contour]) -> list[ContourStructure]:
    result: list[ContourStructure] = []
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


def compare(
    names: list[str] | None = None, compatible: bool = False, method: str = "sample"
) -> ComparisonReport:
    rows: list[ComparisonRow] = []
    for name in CS.ORDER if names is None else names:
        pair = [
            structure(contours(style, name, compatible, method))
            for style in ("Regular", "Bold")
        ]
        a, b = pair
        mismatch: ComparisonMismatch | None = None
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


def summary(report: ComparisonReport | LadderReport) -> str:
    return (
        f"glyphs {report['glyphs']}, contours-compatible {report['contours_compatible']}, "
        f"point-compatible {report['point_compatible']}"
    )


class ContourStructure(TypedDict):
    order: int
    points: int
    segments: list[list[str | int]]
    winding: int


class TopologyShape(TypedDict):
    winding: int
    area: float
    bounds: list[float]


class TopologyTransition(TypedDict):
    weight_interval: list[float]
    before: list[TopologyShape]
    after: list[TopologyShape]


class TopologyMeasurements(TypedDict):
    cause: str
    policy: str
    parts: str
    weight_path: str
    area_filter: float
    contour_counts: list[int]
    endpoints: dict[str, list[TopologyShape]]
    transitions: list[TopologyTransition]
    base: NotRequired[str]
    measurement_scope: NotRequired[str]


class ComparisonMismatch(TypedDict):
    reason: str
    contour: NotRequired[int]


class ComparisonRow(TypedDict):
    name: str
    contour_counts: list[int]
    masters: dict[str, list[ContourStructure]]
    contours_compatible: bool
    point_compatible: bool
    first_mismatch: ComparisonMismatch | None
    topology: NotRequired[TopologyMeasurements]


class ComparisonReport(TypedDict):
    method: str
    scope: str | list[str]
    glyphs: int
    contours_compatible: int
    point_compatible: int
    rows: list[ComparisonRow]


class TopologyReport(TypedDict):
    policy: str
    source_glyphs: list[str]
    default_contours: int
    fixed_contours: int
    weight: float
    cause: NotRequired[str]


class LadderRow(TypedDict):
    name: str
    contours: int
    contours_compatible: bool
    point_compatible: bool
    error: str | None
    union_repair: NotRequired[TopologyReport]
    topology: NotRequired[TopologyReport]


class LadderReport(TypedDict):
    method: str
    rows: list[LadderRow]
    glyphs: int
    contours_compatible: int
    point_compatible: int


def compare_ladder(names: list[str] | None = None) -> dict[str, LadderReport]:
    """Compare each text weight with its Regular in the same slope."""
    reports: dict[str, LadderReport] = {
        style: {
            "method": "sample",
            "rows": [],
            "glyphs": 0,
            "contours_compatible": 0,
            "point_compatible": 0,
        }
        for style in Bd.MASTER_STYLES
    }
    for name in CS.ORDER if names is None else names:
        for italic in (False, True):
            styles = [Bd.weight_style(w, italic) for w in Bd.MASTER_WEIGHTS]
            structures: dict[str, list[ContourStructure]] = {}
            errors = {}
            for style in styles:
                try:
                    structures[style] = structure(contours(style, name, True))
                    # The ladder matches source contours by size and centre.
                    # Their rounded vertical order can change with weight.
                    for i, contour in enumerate(structures[style]):
                        contour["order"] = i
                except ValueError as error:
                    structures[style] = []
                    errors[style] = str(error)
            reference = structures[Bd.weight_style(400, italic)]
            for style in styles:
                actual = structures[style]
                contour_ok = (
                    style not in errors
                    and len(actual) == len(reference)
                    and [c["winding"] for c in actual]
                    == [c["winding"] for c in reference]
                )
                point_ok = contour_ok and actual == reference
                reports[style]["rows"].append(
                    {
                        "name": name,
                        "contours": len(actual),
                        "contours_compatible": contour_ok,
                        "point_compatible": point_ok,
                        "error": errors.get(style),
                    }
                )
                gl = CS.BY_NAME[name]
                if italic and gl.variant == "mathit":
                    sources = [(CS.glyph_name(gl.key), 0, 0)]
                elif gl.comps:
                    sources = Bd.component_offsets(style, gl)[0]
                else:
                    sources = [(name, 0, 0)]
                source_names = {n for n, _, _ in Bd.flatten(style, sources)}
                separate = source_names & (ITALIC_TOPOLOGY if italic else TOPOLOGY)
                repairs = source_names & UNION_REPAIRS if not italic else set()
                if repairs and Bd.STYLES[style].weight not in (400, 700):
                    reports[style]["rows"][-1]["union_repair"] = {
                        "policy": "a: preserve each source stroke; union its hulls in fixed order",
                        "source_glyphs": sorted(repairs),
                        "default_contours": len(contours(style, name)),
                        "fixed_contours": len(actual),
                        "weight": Bd.STYLES[style].weight,
                        "cause": "The batch union cancels ink at coincident hull edges at weight 450",
                    }
                if separate:
                    reports[style]["rows"][-1]["topology"] = {
                        "policy": "a: separate overlapping stroke contours",
                        "source_glyphs": sorted(separate),
                        "default_contours": len(contours(style, name)),
                        "fixed_contours": len(actual),
                        "weight": Bd.STYLES[style].weight,
                    }
    for report in reports.values():
        report["glyphs"] = len(report["rows"])
        report["contours_compatible"] = sum(
            row["contours_compatible"] for row in report["rows"]
        )
        report["point_compatible"] = sum(
            row["point_compatible"] for row in report["rows"]
        )
    return reports


def write_report(path: Path, data: dict[str, Any]) -> None:
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixed", "--compatible", action="store_true")
    ap.add_argument("--method", choices=("sample", "refit"), default="sample")
    ap.add_argument("--all-styles", action="store_true")
    ap.add_argument(
        "--glyphs",
        help="Comma-separated glyph names; the default is the full glyph set.",
    )
    ap.add_argument("--out", type=Path, default=REPORT)
    args = ap.parse_args(argv)
    if args.glyphs and args.out.resolve() == REPORT.resolve():
        # A subset must never replace the committed full report.
        args.out = REPORT.parents[2] / "build/compat-subset.json"
    if args.all_styles:
        if not args.fixed or args.method != "sample":
            ap.error("--all-styles needs --fixed and arc sampling")
        reports = compare_ladder(args.glyphs.split(",") if args.glyphs else None)
        data = json.loads(args.out.read_text()) if args.out.exists() else {}
        for style, report in reports.items():
            print(f"{style}: {summary(report)}", flush=True)
            data[style] = report
        args.out.parent.mkdir(parents=True, exist_ok=True)
        write_report(args.out, data)
        return int(any(r["point_compatible"] != r["glyphs"] for r in reports.values()))
    report = compare(
        args.glyphs.split(",") if args.glyphs else None, args.fixed, args.method
    )
    print(summary(report), flush=True)
    if args.fixed and not args.glyphs:
        measurements = topology_measurements()
        for row in report["rows"]:
            if row["name"] in measurements:
                row["topology"] = measurements[row["name"]]
    data = json.loads(args.out.read_text()) if args.out.exists() else {}
    data["fixed" if args.fixed else "default"] = report
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_report(args.out, data)
    return int(args.fixed and report["point_compatible"] != report["glyphs"])


if __name__ == "__main__":
    raise SystemExit(main())
