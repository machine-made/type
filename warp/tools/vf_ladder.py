# SPDX-License-Identifier: Apache-2.0
"""Build and measure the Roman and Italic weight ladders. Apache-2.0."""

from __future__ import annotations

import argparse
import functools
import gc
import hashlib
import json
import math
import multiprocessing
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from copy import deepcopy
from io import BytesIO
from itertools import pairwise
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, TypeVar

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.otlLib.builder import buildStatTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.ttLib.tables._g_l_y_f import (
    OVERLAP_COMPOUND,
    Glyph,
    GlyphCoordinates,
    flagOverlapSimple,
)
from fontTools.ttLib.tables._g_v_a_r import compileGlyph_
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib import build as build_variable
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.varLib.iup import iup_delta
from PIL import Image, ImageDraw, ImageFont
from ufo2ft import compileTTF

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fidelity
from loom import build as B
from loom.compatible import CompatibilityError, aligned_start, ladder, pair
from vf_spike import endpoint_difference

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/warp-vf"
PROOFS = ROOT / "proofs/warp"
TWO_MASTER_SOURCE = "warp/STATUS.md#regular-and-bold-variable-font-test-2026-11-07"
MAX_VF_BYTES = 9_437_184
# Reserve 0.02 units for flattening and extra room for the stored 600 peak.
# Keep the frozen Bold endpoint bound; source-only weights have the raster gate.
IUP_TOLERANCES = {300: 0.98, 350: 1.0, 450: 1.0, 500: 0.98, 600: 0.95, 700: 0.5}

# Inspector JSON carries check-specific metadata alongside shared fields.
type Record = dict[str, Any]
type Sources = dict[int, TTFont]
type Rotations = list[dict[str, str | int]]
Result = TypeVar("Result")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def source_outline_hash(path: Path) -> str:
    """Fingerprint outline indexing and metrics independently of style metadata."""
    with TTFont(path) as font:
        schema = (
            font["head"].unitsPerEm,
            font["head"].indexToLocFormat,
            font["maxp"].numGlyphs,
            font["hhea"].numberOfHMetrics,
        )
        digest = hashlib.sha256(json.dumps((font.getGlyphOrder(), schema)).encode())
        for tag in ("glyf", "loca", "hmtx"):
            digest.update(font.getTableData(tag))
        return digest.hexdigest()


def release_sources() -> None:
    """Keep compiled references; free source sweeps before the next gate."""
    B.drawn.cache_clear()
    ladder.cache_clear()
    pair.cache_clear()
    gc.collect()


def gap_midpoints(weights: Sequence[float]) -> list[float]:
    """Test the middle of every gap between adjacent source masters."""
    return [(left + right) / 2 for left, right in pairwise(weights)]


def fidelity_weights(weights: Sequence[float]) -> list[float]:
    """Retain the earlier checks as well as every gap midpoint."""
    return sorted(set(gap_midpoints(weights)) | {350, 450, 550, 650})


def resolve_composite(font: TTFont, name: str) -> None:
    """Keep the resolved contour order and vertices, including all offsets."""
    glyph = font["glyf"][name]
    if not glyph.isComposite():
        return
    coordinates, ends, flags = glyph.getCoordinates(font["glyf"])
    simple = Glyph()
    simple.numberOfContours = len(ends)
    simple.coordinates = GlyphCoordinates(coordinates)
    simple.endPtsOfContours = list(ends)
    simple.flags = flags[:]
    simple.program = Program()
    font["glyf"][name] = simple
    simple.recalcBounds(font["glyf"])


def resolve_composite_sources(statics: Sources, name: str) -> None:
    for source in statics.values():
        resolve_composite(source, name)


def apply_corrections(statics: Sources, corrections: Sequence[Record]) -> None:
    """Freeze reported composites, then rotate each contour in one correction batch."""
    # A base-first row order would otherwise rotate a composite twice.
    for row in corrections:
        name, weight = row["glyph"], row["weight"]
        if statics[weight]["glyf"][name].isComposite():
            resolve_composite_sources(statics, name)
    for row in corrections:
        name, weight = row["glyph"], row["weight"]
        rotate_contour(statics[weight]["glyf"][name], row["contour"], row["shift"])


def read_aligned_sources(weights: Sequence[int], italic: bool, out: Path) -> Sources:
    return {
        weight: TTFont(out / f"{B.weight_style(weight, italic)}.ttf")
        for weight in weights
    }


def rotate_contour(glyph: Glyph, contour: int, shift: int) -> None:
    start = 0 if contour == 0 else glyph.endPtsOfContours[contour - 1] + 1
    end = glyph.endPtsOfContours[contour] + 1
    points = list(glyph.coordinates[start:end])
    flags = glyph.flags[start:end]
    shift %= len(points)
    glyph.coordinates[start:end] = GlyphCoordinates(points[shift:] + points[:shift])
    glyph.flags[start:end] = flags[shift:] + flags[:shift]


def align_static(
    font: TTFont, reference: TTFont, style: str | None = None
) -> Rotations:
    """Keep all compiled vertices and choose corresponding contour starts."""
    rotations: Rotations = []
    for name in reference.getGlyphOrder():
        a, b = reference["glyf"][name], font["glyf"][name]
        mixed = a.isComposite() != b.isComposite()
        if mixed or (
            not a.isComposite()
            and getattr(a, "endPtsOfContours", []) != getattr(b, "endPtsOfContours", [])
        ):
            raise CompatibilityError(
                f"{name}: {'component' if mixed else 'point'} structure differs",
                [
                    {
                        "glyph": name,
                        "style": key,
                        "weight": source["OS/2"].usWeightClass,
                        "contours": glyph.numberOfContours,
                        "end_points": list(getattr(glyph, "endPtsOfContours", [])),
                    }
                    for source, glyph, key in (
                        (
                            reference,
                            a,
                            "Italic" if style and B.STYLES[style].italic else "Regular",
                        ),
                        (font, b, style),
                    )
                ],
            )
        if a.isComposite() or b.isComposite():
            continue
        if a.numberOfContours == b.numberOfContours == 0:
            continue
        start = 0
        for i, end in enumerate(a.endPtsOfContours):
            shift = aligned_start(
                a.coordinates[start : end + 1], b.coordinates[start : end + 1]
            )
            if shift:
                rotate_contour(b, i, shift)
                rotations.append({"glyph": name, "contour": i, "shift": shift})
            start = end + 1
    return rotations


def mark_overlaps(font: TTFont) -> None:
    for name in font.getGlyphOrder():
        glyph = font["glyf"][name]
        if not glyph.isComposite() and glyph.numberOfContours > 0:
            for i in range(len(glyph.flags)):
                glyph.flags[i] &= ~flagOverlapSimple
            glyph.flags[0] |= flagOverlapSimple


def local_variations(font: TTFont, statics: Sources, weights: Sequence[int]) -> None:
    """Use one delta to the default at each non-default master.

    Each support ends at the adjacent master. Only one tuple contributes
    at a named weight. Rounded residuals and IUP errors thus cannot add
    across several tuples at an interior master. Keep component offsets
    exact; their error would add to the error in the component outline.
    Include the four phantom points so that instance metrics agree too.
    """
    # Store supports on the axis grid before interpolation. Rounding a
    # peak up can put a gap midpoint just below half a font unit and
    # round both edges of a thin stroke inward.
    locations = {
        w: math.floor((w - 400) / (100 if w < 400 else 300) * 16384) / 16384
        for w in weights
    }
    for name in font.getGlyphOrder():
        base, control = font["glyf"]._getCoordinatesAndControls(
            name, font["hmtx"].metrics
        )
        variations = []
        for i, weight in enumerate(weights):
            if weight == 400:
                continue
            source = statics[weight]
            coordinates, _ = source["glyf"]._getCoordinatesAndControls(
                name, source["hmtx"].metrics
            )
            delta = coordinates - base
            if not any(x != 0 or y != 0 for x, y in delta):
                continue
            support = (
                locations[weights[max(0, i - 1)]],
                locations[weight],
                locations[weights[min(len(weights) - 1, i + 1)]],
            )
            variation = TupleVariation({"wght": support}, delta)
            if control.numberOfContours >= 0:
                variation.optimize(
                    base, control.endPts, tolerance=IUP_TOLERANCES[weight]
                )
                # A one-unit tolerance can omit both moving edges of a thin
                # contour. Keep such contours exact, using run boundaries.
                start, restored = 0, False
                for end in control.endPts:
                    if all(
                        v is None for v in variation.coordinates[start : end + 1]
                    ) and any(x or y for x, y in delta[start : end + 1]):
                        restored = True
                        for j in range(start, end + 1):
                            previous = end if j == start else j - 1
                            following = start if j == end else j + 1
                            if (
                                delta[j] != delta[previous]
                                or delta[j] != delta[following]
                            ):
                                variation.coordinates[j] = delta[j]
                        if all(
                            v is None for v in variation.coordinates[start : end + 1]
                        ):
                            variation.coordinates[start] = delta[start]
                    start = end + 1
                if restored:
                    dense = TupleVariation(variation.axes, delta)
                    if sum(map(len, dense.compile(["wght"]))) < sum(
                        map(len, variation.compile(["wght"]))
                    ):
                        variation = dense
            variations.append(variation)
        font["gvar"].variations[name] = variations


def reuse_identical_outlines(font: TTFont) -> dict[str, str]:
    """Share only byte-identical outlines, metrics and full variation stores.

    Matching every tuple preserves the entire interpolant, including IUP.
    Retain the alias's phantom deltas for its own metrics. Sources stay intact.
    """
    seen = {}
    aliases = {}
    for name in font.getGlyphOrder():
        glyph = font["glyf"][name]
        if glyph.isComposite() or glyph.numberOfContours == 0:
            continue
        if glyph.program.getBytecode():
            continue
        base, control = font["glyf"]._getCoordinatesAndControls(
            name, font["hmtx"].metrics
        )
        variations = font["gvar"].variations[name]
        key = (
            font["hmtx"][name],
            glyph.compile(font["glyf"]),
            compileGlyph_(2, variations, len(base), ["wght"], {}),
        )
        if key not in seen:
            seen[key] = name
            continue
        target = seen[key]
        pen = TTGlyphPen(font.getGlyphSet())
        pen.addComponent(target, (1, 0, 0, 1, 0, 0))
        font["glyf"][name] = pen.glyph()
        font["glyf"][name].components[0].flags |= OVERLAP_COMPOUND
        compact = []
        for variation in variations:
            deltas = iup_delta(variation.coordinates, base, control.endPts)
            phantom = [(0, 0), *deltas[-4:]]
            if any(x or y for x, y in phantom):
                compact.append(TupleVariation(variation.axes, phantom))
        font["gvar"].variations[name] = compact
        aliases[name] = target
    return aliases


def build_vf(
    statics: Sources,
    weights: Sequence[int],
    italic: bool,
    out: Path,
    *,
    write_sources: bool = True,
) -> tuple[TTFont, Path]:
    suffix = "-Italic" if italic else ""
    ds = DesignSpaceDocument()
    ds.addAxis(
        AxisDescriptor(name="Weight", tag="wght", minimum=300, default=400, maximum=700)
    )
    for weight in weights:
        mark_overlaps(statics[weight])
    ascent = max(
        B.TYPO_ASCENDER,
        max(
            getattr(f["glyf"][n], "yMax", 0)
            for f in statics.values()
            for n in f.getGlyphOrder()
        ),
    )
    descent = max(
        -B.TYPO_DESCENDER,
        max(
            -getattr(f["glyf"][n], "yMin", 0)
            for f in statics.values()
            for n in f.getGlyphOrder()
        ),
    )
    for font in statics.values():
        font["OS/2"].usWinAscent = ascent
        font["OS/2"].usWinDescent = descent
    check_master_structure(
        [statics[w] for w in weights], [B.weight_style(w, italic) for w in weights]
    )
    for weight in weights:
        style = B.STYLES[B.weight_style(weight, italic)]
        path = out / f"{style.key}.ttf"
        if write_sources:
            statics[weight].save(path)
        ds.addSource(
            SourceDescriptor(
                path=str(path),
                name=style.key,
                familyName=B.FAMILY,
                styleName=style.style,
                location={"Weight": weight},
            )
        )
    for weight in B.WEIGHTS:
        style = B.STYLES[B.weight_style(weight, italic)]
        ds.addInstance(
            InstanceDescriptor(
                name=style.key,
                familyName=B.FAMILY,
                styleName=style.style,
                postScriptFontName=B.ps_name(style),
                location={"Weight": weight},
            )
        )
    ds.write(out / f"Warp{suffix}.designspace")
    font, _, _ = build_variable(ds, optimize=False)
    local_variations(font, statics, weights)
    buildStatTable(
        font,
        [
            {
                "tag": "wght",
                "name": "Weight",
                "values": [
                    dict(
                        value=w,
                        name=("Demi" if w == 600 else word),
                        **({"flags": 2} if w == 400 else {}),
                    )
                    for w, word in B.WEIGHTS.items()
                ],
            }
        ],
        macNames=False,
    )
    mark_overlaps(font)
    reuse_identical_outlines(font)
    path = out / f"MachineMadeWarp{suffix}[wght].ttf"
    font.save(path)
    return TTFont(path), path


def check_master_structure(
    fonts: Sequence[TTFont], styles: Sequence[str] | None = None
) -> None:
    """Reject a compiled mismatch before varLib can omit its variations."""
    order = fonts[0].getGlyphOrder()
    if any(font.getGlyphOrder() != order for font in fonts[1:]):
        raise ValueError("Master glyph orders differ")
    for name in order:
        controls = [
            font["glyf"]._getCoordinatesAndControls(name, font["hmtx"].metrics)[1]
            for font in fonts
        ]
        if any(value != controls[0] for value in controls[1:]):
            raise CompatibilityError(
                f"{name}: compiled master structure differs",
                [
                    {
                        "glyph": name,
                        "style": styles[i] if styles else None,
                        "weight": font["OS/2"].usWeightClass
                        if "OS/2" in font
                        else None,
                        "contours": control.numberOfContours,
                        "end_points": list(control.endPts),
                        "flags": list(control.flags)
                        if control.flags is not None
                        else None,
                        "components": control.components,
                    }
                    for i, (font, control) in enumerate(zip(fonts, controls))
                ],
            )


def fontspector_findings(raw: Record) -> list[Record]:
    """Record each non-pass finding by check, code, glyph and location."""
    rows = []
    for sections in raw["results"].values():
        for checks in sections.values():
            for check in checks:
                for sub in check["subresults"]:
                    if sub["severity"] in ("PASS", "SKIP"):
                        continue
                    problems = [
                        m["GlyphProblem"]
                        for m in sub.get("metadata", [])
                        if "GlyphProblem" in m
                    ]
                    for metadata in sub.get("metadata", []):
                        if "FontProblem" not in metadata:
                            continue
                        context = dict(metadata["FontProblem"].get("context", {}))
                        problems.extend(
                            {"glyph_name": name}
                            for name in context.pop("unreachable_glyphs", [])
                        )
                        if context:
                            problems.append({"context": context})
                    for problem in problems or [{}]:
                        rows.append(
                            {
                                "check_id": check["check_id"],
                                "code": sub.get("code"),
                                "severity": sub["severity"],
                                "glyph": problem.get("glyph_name"),
                                "location": problem.get("userspace_location", {}),
                                **(
                                    {"context": problem["context"]}
                                    if "context" in problem
                                    else {}
                                ),
                            }
                        )
    return rows


def interpolation_findings(raw: Record, slope: str) -> list[Record]:
    rows = []
    for sections in raw["results"].values():
        for checks in sections.values():
            for check in checks:
                if "interpol" not in check["check_id"]:
                    continue
                for sub in check["subresults"]:
                    if sub["severity"] == "PASS":
                        continue
                    problems = [
                        m["GlyphProblem"]
                        for m in sub.get("metadata", [])
                        if "GlyphProblem" in m
                    ]
                    if not problems:
                        raise ValueError("Interpolation finding has no glyph metadata")
                    for problem in problems:
                        message = problem["message"]
                        kind = (
                            "start_point"
                            if "start point" in message.lower()
                            else "underweight"
                            if "underweight" in message.lower()
                            else "overweight"
                            if "overweight" in message.lower()
                            else "contour_order"
                            if "contour order" in message.lower()
                            else "other"
                        )
                        rows.append(
                            {
                                "slope": slope,
                                "kind": kind,
                                "check_id": check["check_id"],
                                "glyph": problem["glyph_name"],
                                "weight": problem.get("userspace_location", {}).get(
                                    "wght"
                                ),
                                "actual": problem.get("actual"),
                                "expected": problem.get("expected"),
                                "message": message,
                            }
                        )
    return rows


def interpolation_report(findings: list[Record], complete: bool = False) -> Record:
    """Keep every finding, including results from a partly completed run."""
    grouped = defaultdict(list)
    for row in findings:
        grouped[row["kind"]].append(row)
    causes = {}
    for kind, rows in grouped.items():
        if kind in ("underweight", "overweight"):
            ratios = [
                r["expected"]["value_master2"] / r["actual"]["value_master1"]
                for r in rows
                if r["actual"]["value_master1"] != 0
            ]
            causes[kind] = (
                f"Contour area changes with weight; reported area ratios range "
                f"from {min(ratios):.6f} to {max(ratios):.6f}."
                if ratios
                else "All reported reference contour areas are zero."
            )
        elif kind == "start_point":
            causes[kind] = "Fontspector requests a different cyclic contour start."
        elif kind == "contour_order":
            causes[kind] = "Fontspector requests a different contour order."
        else:
            causes[kind] = "; ".join(sorted({r["message"] for r in rows}))
    return {
        "two_master_findings": 770,
        "two_master_source": TWO_MASTER_SOURCE,
        "remaining": len(findings),
        "start_point_count": len(grouped.get("start_point", [])),
        "complete": complete,
        "kinds": dict(grouped),
        "glyph_counts": {
            k: len({(r["slope"], r["glyph"]) for r in rows})
            for k, rows in grouped.items()
        },
        "causes": causes,
    }


def inspect_font(
    executable: str, path: Path, out: Path, slope: str
) -> tuple[dict[str, int], list[Record]]:
    gc.collect()
    report_path = out / f"fontspector-{slope}.json"
    report_path.unlink(missing_ok=True)
    # The interpolation check frees large buffers between glyphs. Let
    # glibc return those pages rather than keep them in its heap arenas.
    environment = dict(
        os.environ,
        MALLOC_ARENA_MAX="2",
        MALLOC_TRIM_THRESHOLD_="65536",
        MALLOC_MMAP_THRESHOLD_="65536",
    )
    result = subprocess.run(
        [
            executable,
            "-p",
            "universal",
            "--jobs",
            "1",
            "--skip-network",
            "--full-lists",
            "--json",
            str(report_path),
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if not report_path.exists():
        raise RuntimeError(
            f"Fontspector did not write its report (exit {result.returncode}): "
            f"{result.stderr[-2000:]}"
        )
    raw = json.loads(report_path.read_text())
    counts = {
        key: raw["summary"].get(key, 0)
        for key in ("SKIP", "INFO", "PASS", "WARN", "FAIL", "FATAL", "ERROR")
    }
    if result.returncode not in (0, 1) or (
        result.returncode and not any(counts[k] for k in ("FAIL", "FATAL", "ERROR"))
    ):
        raise RuntimeError(f"Fontspector exited with status {result.returncode}")
    print(
        f"Fontspector {slope}: " + ", ".join(f"{v} {k}" for k, v in counts.items()),
        flush=True,
    )
    return counts, interpolation_findings(raw, slope)


def fidelity_at(font: TTFont, weight: float, italic: bool) -> Record:
    # Read the compiled instance, including TrueType integer rounding.
    # Fractional coincident edges can make the ink union omit a stroke.
    buffer = BytesIO()
    font.save(buffer)
    buffer.seek(0)
    raster_font = TTFont(buffer)
    # The gate draws simple glyphs and the italic aliases of those
    # glyphs. Resolve their ink without unioning unrelated composites.
    removeOverlaps(
        raster_font,
        [
            n
            for n in raster_font.getGlyphOrder()
            if not raster_font["glyf"][n].isComposite()
        ],
    )
    glyphs = fidelity.compare(B.weight_style(weight, italic), raster_font)
    maximum, glyph, size = max(
        (v, name, size) for name, row in glyphs.items() for size, v in row.items()
    )
    return {
        "max_percent": 100 * maximum,
        "glyph": glyph,
        "ppem": int(size),
        "passed": all(
            v <= fidelity.TOLERANCE[int(s)]
            for row in glyphs.values()
            for s, v in row.items()
        ),
        "glyphs": glyphs,
    }


def endpoint_regression(instances: Mapping[str, Record]) -> bool:
    """Keep the measured bounds of the earlier Roman endpoint test."""
    return all(
        abs(instances[str(w)]["max_units"] - expected) <= 1e-8
        for w, expected in ((400, 0.020), (700, 0.520))
    )


def master_weight(value: float, weights: Collection[int]) -> int:
    """Map an F2Dot14 peak back to its source, within one axis grid step."""
    nearest = min(weights, key=lambda w: abs(w - value))
    bound = max(abs(w - 400) for w in weights) / 16384
    if abs(nearest - value) > bound + 1e-9:
        raise ValueError(f"No source master at reported weight {value}")
    return nearest


def finding_identity(row: Record) -> Record:
    """Compare source weights despite one stored axis-grid step of error."""
    result = deepcopy(row)
    location = result["location"]
    if "wght" in location:
        try:
            location["wght"] = master_weight(location["wght"], B.MASTER_WEIGHTS)
        except ValueError:
            # Keep locations away from a source exact: they can identify
            # a new finding between sources.
            return result
    return result


def proof_sheet(paths: Mapping[str, Path], out: Path) -> str:
    text = "Hamburgefonstiv ß fi ffl γ κ ∑"
    canvas = Image.new("RGB", (1900, 1750), "white")
    draw = ImageDraw.Draw(canvas)
    y = 15
    for slope, path in paths.items():
        draw.text((20, y), slope, fill="black")
        y += 25
        for weight in B.WEIGHTS:
            draw.text((20, y), str(weight), fill="black")
            for size in (20, 40, 80):
                font = ImageFont.truetype(str(path), size)
                font.set_variation_by_axes([weight])
                draw.text((85, y), text, font=font, fill="black")
                y += size + 8
    path = out / "weight-ladder.png"
    canvas.crop((0, 0, 1900, y + 15)).save(path)
    return path.name


def compile_sources(italic: bool, out: Path) -> None:
    """Build in a child so all source memory leaves before validation."""
    slope = "Italic" if italic else "Roman"
    try:
        for weight in B.MASTER_WEIGHTS:
            style = B.weight_style(weight, italic)
            print(f"Compile {style}", flush=True)
            font = compileTTF(
                B.build_font(style, compatible=True), removeOverlaps=False
            )
            mark_overlaps(font)
            font.save(out / f"{style}-source.ttf")
    except Exception as error:
        write_json(
            out / f"{slope}-compile-error.json",
            {"reason": str(error), "diagnostics": getattr(error, "diagnostics", None)},
        )
        raise


def compiled_sources(italic: bool, out: Path) -> Sources:
    slope = "Italic" if italic else "Roman"
    error_path = out / f"{slope}-compile-error.json"
    error_path.unlink(missing_ok=True)
    process = multiprocessing.get_context("spawn").Process(
        target=compile_sources, args=(italic, out)
    )
    process.start()
    process.join()
    status = process.exitcode
    process.close()
    if status:
        if error_path.exists():
            error = json.loads(error_path.read_text())
            raise CompatibilityError(error["reason"], error["diagnostics"])
        raise RuntimeError(f"{slope} source compiler exited with status {status}")
    return {
        weight: TTFont(out / f"{B.weight_style(weight, italic)}-source.ttf")
        for weight in B.MASTER_WEIGHTS
    }


def worker_entry(
    connection: Connection, target: Callable[..., object], args: tuple[object, ...]
) -> None:
    """Return only measurements; let the process release all font memory."""
    try:
        connection.send({"result": target(*args)})
    except Exception as error:
        connection.send(
            {
                "error": str(error),
                "compatibility_error": isinstance(error, CompatibilityError),
                "diagnostics": getattr(error, "diagnostics", None),
            }
        )
        raise
    finally:
        connection.close()


def worker_process(target: Callable[..., Result], *args: object) -> Result:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=worker_entry, args=(sender, target, args))
    process.start()
    sender.close()
    try:
        try:
            result = receiver.recv()
        except EOFError:
            result = None
        process.join()
        status = process.exitcode
    finally:
        receiver.close()
        if process.is_alive():
            process.terminate()
            process.join()
        process.close()
    if result is not None and "error" in result:
        if result["compatibility_error"]:
            raise CompatibilityError(result["error"], result["diagnostics"])
        raise RuntimeError(f"{target.__name__}: {result['error']}")
    if status or result is None:
        raise RuntimeError(f"{target.__name__} worker exited with status {status}")
    return result["result"]


def prepare_slope(italic: bool, out: Path) -> dict[str, Rotations]:
    statics = compiled_sources(italic, out)
    rotations = {}
    for weight, font in statics.items():
        if weight != 400:
            rotations[str(weight)] = align_static(
                font, statics[400], B.weight_style(weight, italic)
            )
    weights = list(B.MASTER_WEIGHTS)
    slope = "Italic" if italic else "Roman"
    print(f"{slope} masters: {weights}", flush=True)
    build_vf(statics, weights, italic, out)
    return rotations


def rebuild_aligned_slope(italic: bool, out: Path) -> None:
    """Re-encode saved, corrected masters without inspecting or rotating them."""
    weights = list(B.MASTER_WEIGHTS)
    build_vf(
        read_aligned_sources(weights, italic, out),
        weights,
        italic,
        out,
        write_sources=False,
    )


def correct_slope(
    starts: list[Record], weights: Sequence[int], italic: bool, out: Path, attempt: int
) -> list[Record]:
    statics = read_aligned_sources(weights, italic, out)
    corrections = []
    changes = set()
    for row in starts:
        weight, name = master_weight(row["weight"], weights), row["glyph"]
        expected = row["expected"]
        if expected["reverse_contour"]:
            raise ValueError(f"{row['slope']} {name} {weight}: winding differs")
        contour = row["actual"]["contour_index"]
        key = (weight, name, contour)
        if key in changes:
            continue
        changes.add(key)
        shift = expected["proposed_start_point"]
        corrections.append(
            {
                "attempt": attempt,
                "weight": weight,
                "glyph": name,
                "contour": contour,
                "shift": shift,
            }
        )
    if changes:
        apply_corrections(statics, corrections)
        build_vf(statics, weights, italic, out)
    return corrections


def measure_slope(
    weights: Sequence[int], italic: bool, out: Path
) -> tuple[dict[str, Record], dict[str, Record]]:
    statics = read_aligned_sources(weights, italic, out)
    slope = "Italic" if italic else "Roman"
    suffix = "-Italic" if italic else ""
    path = out / f"MachineMadeWarp{suffix}[wght].ttf"
    font = TTFont(path)
    instances = {}
    for weight in B.WEIGHTS:
        instance = instantiateVariableFont(font, {"wght": weight})
        instances[str(weight)] = result = endpoint_difference(instance, statics[weight])
        print(
            f"{path.name} instance {weight}: max difference {result['max_units']:.3f} units",
            flush=True,
        )
    fidelities = {}
    write_json(out / f"{slope}-instances.json", instances)
    for weight in fidelity_weights(weights):
        instance = instantiateVariableFont(font, {"wght": weight})
        fidelities[f"{weight:g}"] = result = fidelity_at(instance, weight, italic)
        release_sources()
        print(
            f"{path.name} weight {weight}: fidelity {result['max_percent']:.3f} percent ({result['glyph']})",
            flush=True,
        )
        write_json(out / f"{slope}-fidelity.json", fidelities)
    return instances, fidelities


def source_hashes(weights: Sequence[int], italic: bool, out: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((out / name).read_bytes()).hexdigest()
        for name in (f"{B.weight_style(weight, italic)}.ttf" for weight in weights)
    }


def verify_saved_sources(saved: Record, slope: str, italic: bool, out: Path) -> None:
    """Fail unless the saved proof names every master and each file still matches."""
    hashes = saved.get("source_hashes_sha256", {})
    expected_names = {f"{B.weight_style(w, italic)}.ttf" for w in B.MASTER_WEIGHTS}
    if set(hashes) != expected_names:
        raise ValueError(f"Missing aligned source hashes for {slope}")
    for name, digest in source_hashes(B.MASTER_WEIGHTS, italic, out).items():
        if digest != hashes[name]:
            raise ValueError(f"Saved aligned source changed: {name}")


def checkpoint_corrections(
    report: Record, saved: Record, italic: bool, out: Path, changes: list[Record]
) -> None:
    """Keep the saved provenance equal to the files on disk after a correction,
    so a failed measurement can be retried."""
    saved["start_point_corrections"] = (
        saved.get("start_point_corrections", []) + changes
    )
    saved["source_hashes_sha256"] = source_hashes(B.MASTER_WEIGHTS, italic, out)
    write_json(PROOFS / "ladder.json", report)


def run_slope(
    italic: bool,
    out: Path,
    executable: str | None,
    reuse_aligned_sources: bool = False,
    on_correction: Callable[[list[Record]], None] | None = None,
) -> tuple[Record, list[Record], Path]:
    slope = "Italic" if italic else "Roman"
    weights = list(B.MASTER_WEIGHTS)
    suffix = "-Italic" if italic else ""
    path = out / f"MachineMadeWarp{suffix}[wght].ttf"
    # Each builder exits before inspection. Clearing Python objects alone
    # can leave its allocator holding gigabytes of unused font memory.
    if reuse_aligned_sources:
        worker_process(rebuild_aligned_slope, italic, out)
        rotations = {}
    else:
        rotations = worker_process(prepare_slope, italic, out)
    corrections = []
    inspection_error = None if executable else "Fontspector was not run"
    counts = {
        key: None for key in ("SKIP", "INFO", "PASS", "WARN", "FAIL", "FATAL", "ERROR")
    }
    findings = []
    for attempt in range(9) if executable else ():
        try:
            counts, findings = inspect_font(executable, path, out, slope)
        except RuntimeError as error:
            inspection_error = str(error)
            counts = dict.fromkeys(counts)
            findings = []
            print(f"Fontspector {slope}: incomplete: {error}", flush=True)
            break
        starts = [row for row in findings if row["kind"] == "start_point"]
        if not starts or attempt == 8:
            break
        changes = worker_process(correct_slope, starts, weights, italic, out, attempt)
        corrections.extend(changes)
        if not changes:
            break
        if on_correction:
            # The correction rewrote the aligned masters on disk.
            on_correction(changes)
    instances, fidelities = worker_process(measure_slope, weights, italic, out)
    numerical_passed = (
        path.stat().st_size <= MAX_VF_BYTES
        and all(row["max_units"] <= 1.0 for row in instances.values())
        and all(row["passed"] for row in fidelities.values())
        and endpoint_regression(instances)
    )
    passed = (
        numerical_passed
        and inspection_error is None
        and not any(counts[k] for k in ("FAIL", "FATAL", "ERROR"))
        and not findings
    )
    with (
        TTFont(path) as built,
        TTFont(out / f"{B.weight_style(400, italic)}.ttf") as default,
    ):
        aliases = {
            name: built["glyf"][name].components[0].glyphName
            for name in built.getGlyphOrder()
            if not default["glyf"][name].isComposite()
            and built["glyf"][name].isComposite()
        }
    print(
        f"{path.name}: {path.stat().st_size} bytes; numerical gates {numerical_passed}",
        flush=True,
    )
    report = {
        "masters": weights,
        "midpoint_weights": gap_midpoints(weights),
        "legacy_test_weights": [350, 450, 550, 650],
        "file_size_bytes": path.stat().st_size,
        "file_size_limit_bytes": MAX_VF_BYTES,
        "iup_tolerances": IUP_TOLERANCES,
        "identical_outline_aliases": aliases,
        "source_hashes_sha256": source_hashes(weights, italic, out),
        "source_outline_hashes_sha256": {
            name: source_outline_hash(out / name)
            for weight in weights
            for name in (f"{B.weight_style(weight, italic)}.ttf",)
        },
        "instances": instances,
        "fidelity": fidelities,
        "initial_rotations": rotations,
        "start_point_corrections": corrections,
        "fontspector": counts,
        "fontspector_complete": inspection_error is None,
        "fontspector_error": inspection_error,
        "new_fontspector_findings": None,
        "fontspector_findings": fontspector_findings(
            json.loads((out / f"fontspector-{slope}.json").read_text())
        )
        if inspection_error is None
        else [],
        "passed": passed,
        "numerical_passed": numerical_passed,
    }
    return report, findings, path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--fontspector", default=shutil.which("fontspector"))
    ap.add_argument(
        "--skip-fontspector",
        action="store_true",
        help="Measure without inspection; the verdict stays not verified",
    )
    ap.add_argument(
        "--reuse-aligned-sources",
        action="store_true",
        help="Rebuild from the saved, corrected source TTFs in --out",
    )
    args = ap.parse_args(argv)
    if args.skip_fontspector and not args.reuse_aligned_sources:
        ap.error("--skip-fontspector requires --reuse-aligned-sources")
    if not args.skip_fontspector and not args.fontspector:
        ap.error("Fontspector is required; put it on PATH or use --fontspector")
    os.environ["SOURCE_DATE_EPOCH"] = "1793059200"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "styles": {},
        "incompatible": [],
        "verdict": "not verified",
        "previous_fontspector_findings": {
            slope: fontspector_findings(json.loads(path.read_text()))
            for slope in ("Roman", "Italic")
            if (path := out / f"fontspector-{slope}.json").exists()
        },
        "previous_file_sizes_bytes": {
            path.name: path.stat().st_size
            for path in (
                out / "MachineMadeWarp[wght].ttf",
                out / "MachineMadeWarp-Italic[wght].ttf",
            )
            if path.exists()
        },
    }
    # Keep the first comparison baseline if a measurement needs another run.
    previous_path = PROOFS / "ladder.json"
    prior_report = {}
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        prior_report = previous
        for key in ("previous_fontspector_findings", "previous_file_sizes_bytes"):
            if key in previous:
                report[key] = previous[key]
    if args.reuse_aligned_sources:
        # Keep both slopes' provenance while a failed or partial run replaces
        # the proof. A retry must still verify every saved source hash.
        report["aligned_sources"] = {}
        for slope in ("Roman", "Italic"):
            old_style = prior_report.get("styles", {}).get(slope) or prior_report.get(
                "aligned_sources", {}
            ).get(slope, {})
            report["aligned_sources"][slope] = {
                key: old_style[key]
                for key in (
                    "initial_rotations",
                    "start_point_corrections",
                    "source_hashes_sha256",
                )
                if key in old_style
            }
    write_json(PROOFS / "ladder.json", report)
    if not args.skip_fontspector:
        write_json(
            PROOFS / "interpolation.json",
            {
                "two_master_findings": 770,
                "two_master_source": TWO_MASTER_SOURCE,
                "remaining": None,
                "start_point_count": None,
                "verdict": "not verified",
                "kinds": {},
            },
        )
    findings, paths = [], {}
    for italic in (False, True):
        slope = "Italic" if italic else "Roman"
        try:
            if args.reuse_aligned_sources:
                old_style = report["aligned_sources"][slope]
                verify_saved_sources(old_style, slope, italic, out)
                saved_corrections = list(old_style.get("start_point_corrections", []))

                result, rows, path = run_slope(
                    italic,
                    out,
                    None if args.skip_fontspector else args.fontspector,
                    reuse_aligned_sources=True,
                    on_correction=functools.partial(
                        checkpoint_corrections, report, old_style, italic, out
                    ),
                )
                result["alignment_source"] = "saved aligned masters"
                result["initial_rotations"] = old_style.get("initial_rotations", {})
                result["start_point_corrections"] = (
                    saved_corrections + result["start_point_corrections"]
                )
            else:
                result, rows, path = run_slope(italic, out, args.fontspector)
        except Exception as error:
            report["reason"] = f"{slope}: {error}"
            # A build error does not prove that the glyphs are compatible.
            report["incompatible"] = getattr(error, "diagnostics", None)
            write_json(PROOFS / "ladder.json", report)
            raise
        previous = report["previous_fontspector_findings"].get(slope)
        if previous is not None and result.get("fontspector_complete", True):
            previous_ids = [finding_identity(row) for row in previous]
            result["new_fontspector_findings"] = [
                row
                for row in result["fontspector_findings"]
                if finding_identity(row) not in previous_ids
            ]
            result["passed"] &= not result["new_fontspector_findings"]
        report["styles"][slope] = result
        findings.extend(rows)
        paths[slope] = path
        write_json(PROOFS / "ladder.json", report)
        if args.skip_fontspector:
            continue
        partial = interpolation_report(findings)
        if any(
            not row.get("fontspector_complete", True)
            for row in report["styles"].values()
        ):
            partial["findings_observed"] = len(findings)
            partial["remaining"] = None
            partial["start_point_count"] = None
        partial["verdict"] = "not verified"
        write_json(PROOFS / "interpolation.json", partial)
    if args.skip_fontspector:
        report.pop("aligned_sources", None)
        report["interpolation"] = {
            "complete": False,
            "remaining": None,
            "start_point_count": None,
            "previous_report": "proofs/warp/interpolation.json",
        }
        report["proof_sheet"] = proof_sheet(paths, out)
        report["numerical_passed"] = all(
            row["numerical_passed"] for row in report["styles"].values()
        )
        write_json(PROOFS / "ladder.json", report)
        print("Fontspector not run; current interpolation findings are unknown.")
        print("Verdict: not verified")
        return int(not report["numerical_passed"])
    inspection_complete = all(
        row.get("fontspector_complete", True) for row in report["styles"].values()
    )
    interpolation = interpolation_report(findings, complete=inspection_complete)
    if not inspection_complete:
        interpolation["findings_observed"] = len(findings)
        interpolation["remaining"] = None
        interpolation["start_point_count"] = None
    write_json(PROOFS / "interpolation.json", interpolation)
    report["proof_sheet"] = proof_sheet(paths, out)
    passed = all(row["passed"] for row in report["styles"].values())
    report["verdict"] = "verified" if passed else "not verified"
    report.pop("aligned_sources", None)
    write_json(PROOFS / "ladder.json", report)
    print(
        f"770 findings in the two-master spike report; "
        f"{interpolation['remaining']} in the seven-master ladder; "
        f"starts {interpolation['start_point_count']}"
    )
    print(f"Verdict: {report['verdict']}")
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
