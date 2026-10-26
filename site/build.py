"""Build the specimen and release site for machine-made/type.

Usage:
    python site/build.py            # writes site/_site/
    python site/build.py --out DIR  # writes DIR/

The script:

1. Selects the font files (see FONT_SOURCE below).
2. Copies the fonts and the static assets into the output folder.
3. Reads the fonts with fontTools and writes JSON for the pages:
   axes, character map, features, version.
4. Reads proofs/weft/readability.json if it exists.
5. Draws the "machine-made" wordmark and the favicon as SVG from the
   Weft outlines.
6. Fills the page templates and writes the HTML.

Needs Python 3.11+ and fontTools with brotli (for WOFF2).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------------------
# FONT SOURCE: the one switch between the stand-in fonts and the real fonts.
#
#   "auto"    : for each family, use the real webfonts in fonts/<family>/
#               webfonts/ when they exist, else use the stand-ins.
#   "release" : use only the real webfonts. Stop with an error if one is
#               missing.
#   "standin" : use only the stand-ins in site/assets/fonts/standin/.
# ---------------------------------------------------------------------------
FONT_SOURCE = "auto"

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
STANDIN = SITE / "assets" / "fonts" / "standin"

REPO_URL = "https://github.com/machine-made/type"
ORG_URL = "https://github.com/machine-made"
RELEASES = {
    "weft": REPO_URL + "/releases/tag/weft-v0.1.0",
    "sans": REPO_URL + "/releases/tag/sans-v0.1.0",
}

# Font files per family. "vf" is the file the pages use. "extra" files are
# copied too, so that the site also serves them.
FAMILIES = {
    "weft": {
        "release_dir": ROOT / "fonts" / "weft" / "webfonts",
        "release": {
            "vf": "MachineMadeWeft[FRAG,wght].woff2",
            "bold": "MachineMadeWeft-Bold.woff2",
        },
        "standin": {
            "vf": STANDIN / "standin-Weft-phase1-Regular.woff2",
        },
        # Planned values, shown when the loaded font does not have the axis.
        "planned_axes": {"wght": [100, 400, 900], "FRAG": [0, 0, 100]},
    },
    "sans": {
        "release_dir": ROOT / "fonts" / "sans" / "webfonts",
        "release": {
            "vf": "MachineMadeSans[wght].woff2",
            "italic": "MachineMadeSans-Italic[wght].woff2",
        },
        "standin": {
            "vf": STANDIN / "standin-PlusJakartaSans[wght].woff2",
            "italic": STANDIN / "standin-PlusJakartaSans-Italic[wght].woff2",
        },
        "planned_axes": {"wght": [200, 400, 800]},
    },
}

READABILITY = ROOT / "proofs" / "weft" / "readability.json"

# Weft metrics in font units (BRIEF.md): 1 design unit = 62.5 units.
WEFT_UNIT = 62.5
WEFT_X_HEIGHT = 500
WORDMARK_WGHT = 700


class BuildError(Exception):
    """A build step cannot continue."""


# ---------------------------------------------------------------------------
# Font selection
# ---------------------------------------------------------------------------

def select_fonts(source: str) -> dict:
    """Return the selected files per family and the source of each family."""
    if source not in ("auto", "release", "standin"):
        raise BuildError(f'FONT_SOURCE must be "auto", "release" or "standin", not "{source}".')
    chosen = {}
    for fam, spec in FAMILIES.items():
        rel_dir = spec["release_dir"]
        rel_vf = rel_dir / spec["release"]["vf"]
        use_release = source == "release" or (source == "auto" and rel_vf.is_file())
        if use_release:
            files = {}
            for role, name in spec["release"].items():
                path = rel_dir / name
                if path.is_file():
                    files[role] = path
                elif role == "vf" or (fam == "sans" and role == "italic"):
                    raise BuildError(f"Font file not found: {path}. Build the fonts first, or set FONT_SOURCE.")
            # Copy every webfont of the family, also the ones the pages do not use.
            extra = sorted(p for p in rel_dir.glob("*.woff2") if p not in files.values())
            chosen[fam] = {"source": "release", "files": files, "extra": extra}
        else:
            files = {role: path for role, path in spec["standin"].items()}
            for path in files.values():
                if not path.is_file():
                    raise BuildError(f"Stand-in font not found: {path}.")
            chosen[fam] = {"source": "standin", "files": files, "extra": []}
    return chosen


# ---------------------------------------------------------------------------
# Font inspection
# ---------------------------------------------------------------------------

def font_name(font: TTFont, *ids: int) -> str:
    for i in ids:
        value = font["name"].getDebugName(i)
        if value:
            return value
    return ""


def axes_of(font: TTFont) -> dict:
    if "fvar" not in font:
        return {}
    return {a.axisTag: [a.minValue, a.defaultValue, a.maxValue] for a in font["fvar"].axes}


def stylistic_sets(font: TTFont) -> dict:
    """Return {"ss01": "UI name", ...} for the stylistic sets in GSUB."""
    out = {}
    if "GSUB" not in font or font["GSUB"].table.FeatureList is None:
        return out
    for rec in font["GSUB"].table.FeatureList.FeatureRecord:
        tag = rec.FeatureTag
        if re.fullmatch(r"ss\d\d", tag) and tag not in out:
            params = rec.Feature.FeatureParams
            label = ""
            if params is not None and hasattr(params, "UINameID"):
                label = font["name"].getDebugName(params.UINameID) or ""
            out[tag] = label
    return dict(sorted(out.items()))


def char_group(cp: int) -> str:
    ch = chr(cp)
    cat = unicodedata.category(ch)
    if cp < 0x80:
        if cat == "Lu":
            return "Uppercase"
        if cat == "Ll":
            return "Lowercase"
        if cat == "Nd":
            return "Figures"
        return "Punctuation and symbols"
    if cat.startswith("L"):
        return "Accented and other letters"
    if cat.startswith("N"):
        return "Other figures"
    return "Other symbols"


GROUP_ORDER = ["Uppercase", "Lowercase", "Figures", "Punctuation and symbols",
               "Accented and other letters", "Other figures", "Other symbols"]


def glyph_map(font: TTFont) -> list:
    """Return the character map, grouped, for the glyph map on the page."""
    groups: dict[str, list] = {g: [] for g in GROUP_ORDER}
    for cp, gname in sorted(font.getBestCmap().items()):
        cat = unicodedata.category(chr(cp))
        if cat.startswith("C") or cat in ("Zs", "Zl", "Zp"):
            continue  # No visible glyph to show.
        try:
            uname = unicodedata.name(chr(cp))
        except ValueError:
            uname = ""
        groups[char_group(cp)].append({"u": cp, "g": gname, "n": uname.title()})
    return [{"name": g, "chars": c} for g, c in groups.items() if c]


def inspect(path: Path) -> dict:
    font = TTFont(path)
    cmap = font.getBestCmap()
    return {
        "family": font_name(font, 16, 1),
        "version": font_name(font, 5),
        "axes": axes_of(font),
        "features": stylistic_sets(font),
        # Count the characters with a visible glyph (no controls, no spaces).
        "char_count": sum(1 for cp in cmap if unicodedata.category(chr(cp))[0] not in "CZ"),
        "glyph_count": len(font.getGlyphOrder()),
        "upm": font["head"].unitsPerEm,
    }


# ---------------------------------------------------------------------------
# Wordmark and favicon (SVG drawn from the Weft outlines)
# ---------------------------------------------------------------------------

def weft_for_wordmark(chosen: dict) -> TTFont:
    files = chosen["weft"]["files"]
    if "bold" in files:
        return TTFont(files["bold"])
    font = TTFont(files["vf"])
    axes = axes_of(font)
    if axes:
        from fontTools.varLib import instancer
        pins = {tag: v[1] for tag, v in axes.items()}
        if "wght" in axes:
            pins["wght"] = max(axes["wght"][0], min(axes["wght"][2], WORDMARK_WGHT))
        if "FRAG" in axes:
            pins["FRAG"] = 0
        font = instancer.instantiateVariableFont(font, pins)
    return font


def contours(recording: list) -> list:
    """Split a recorded pen value into one list per contour."""
    out, cur = [], []
    for op, args in recording:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def replay(ops: list, pen) -> None:
    for op, args in ops:
        getattr(pen, op)(*args)


def contour_ymin(ops: list) -> float:
    ys = [pt[1] for _, args in ops for pt in args]
    return min(ys) if ys else 0


def hyphen_ops(stroke_w: float) -> list:
    """Draw a hyphen from the loom stroke table when the font has none.

    Stroke table: open line (1.5, 4.6) to (5.5, 4.6), square caps, box
    offset 2.5. Phase 1 fonts have no hyphen glyph.
    """
    half = stroke_w / 2
    x0 = (2.5 + 1.5) * WEFT_UNIT - half
    x1 = (2.5 + 5.5) * WEFT_UNIT + half
    y0, y1 = 4.6 * WEFT_UNIT - half, 4.6 * WEFT_UNIT + half
    return [("moveTo", ((x0, y0),)), ("lineTo", ((x0, y1),)), ("lineTo", ((x1, y1),)),
            ("lineTo", ((x1, y0),)), ("closePath", ())]


def stroke_width_units(font: TTFont) -> float:
    """Return the stem width of the font, measured from the 'l' stem."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    name = cmap.get(ord("i"))
    if name is None:
        return 84
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    dots = [c for c in contours(rec.value) if contour_ymin(c) > WEFT_X_HEIGHT]
    if dots:
        bp = BoundsPen(gs)
        replay(dots[0], bp)
        if bp.bounds:
            return bp.bounds[2] - bp.bounds[0]
    return 84


def wordmark_svg(font: TTFont, text: str = "machine-made", label: str = "machine-made") -> str:
    """Return an inline SVG of text in Weft. The dot of each i is red."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    ink, dots = SVGPathPen(gs), SVGPathPen(gs)
    bounds = BoundsPen(gs)
    sw = stroke_width_units(font)
    x = 0
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None and ch == "-":
            ops, adv = hyphen_ops(sw), 750
            groups = [(ops, False)]
        elif name is None:
            raise BuildError(f"The Weft font has no glyph for {ch!r}; the wordmark needs it.")
        else:
            rec = DecomposingRecordingPen(gs)
            gs[name].draw(rec)
            adv = hmtx[name][0]
            groups = [(c, ch == "i" and contour_ymin(c) > WEFT_X_HEIGHT) for c in contours(rec.value)]
        for ops, is_dot in groups:
            # Flip y for SVG: font y goes up, SVG y goes down.
            target = dots if is_dot else ink
            replay(ops, TransformPen(target, (1, 0, 0, -1, x, 0)))
            replay(ops, TransformPen(bounds, (1, 0, 0, -1, x, 0)))
        x += adv
    x0, y0, x1, y1 = bounds.bounds
    pad = 0
    vb = f"{x0 - pad:.0f} {y0 - pad:.0f} {x1 - x0 + 2 * pad:.0f} {y1 - y0 + 2 * pad:.0f}"
    return (
        f'<svg class="wordmark" viewBox="{vb}" role="img" aria-label="{html.escape(label)}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<path fill="currentColor" d="{ink.getCommands()}"/>'
        f'<path class="wordmark-dot" fill="var(--red, #DE2A1F)" d="{dots.getCommands()}"/>'
        f"</svg>"
    )


def favicon_svg(font: TTFont) -> str:
    """Return a favicon: the Weft i, white on black, with a red dot."""
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord("i")]
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    stem, dot = SVGPathPen(gs), SVGPathPen(gs)
    # Centre the 750-unit advance in a 1000-unit square; baseline at 820.
    tr = (1, 0, 0, -1, 125, 840)
    for c in contours(rec.value):
        replay(c, TransformPen(dot if contour_ymin(c) > WEFT_X_HEIGHT else stem, tr))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">'
        '<rect width="1000" height="1000" rx="120" fill="#121314"/>'
        f'<path fill="#F4F5F3" d="{stem.getCommands()}"/>'
        f'<path fill="#DE2A1F" d="{dot.getCommands()}"/>'
        "</svg>\n"
    )


# ---------------------------------------------------------------------------
# Readability report and commit list
# ---------------------------------------------------------------------------

def normalise_readability(raw) -> list:
    """Return [{"frag": n, "cer": fraction}, ...] from the accepted shapes.

    Accepted input:
      {"levels": [{"frag": 0, "cer": 0.004}, ...], ...}   (also "results")
      [{"frag": 0, "cer": 0.004}, ...]
      {"0": 0.004, "15": 0.006}  or  {"cer": {"0": 0.004, ...}}
    "cer" is a fraction (0.004 = 0.4 %). "cer_percent" is also accepted.
    """
    rows = None
    if isinstance(raw, dict):
        for key in ("levels", "results", "rows", "data"):
            if isinstance(raw.get(key), list):
                rows = raw[key]
                break
        if rows is None:
            table = raw.get("cer") if isinstance(raw.get("cer"), dict) else raw
            pairs = [(k, v) for k, v in table.items() if re.fullmatch(r"\d+(\.\d+)?", str(k))]
            rows = [{"frag": float(k), "cer": v} for k, v in pairs]
    elif isinstance(raw, list):
        rows = raw
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        frag = r.get("frag", r.get("FRAG", r.get("level")))
        if "cer" in r:
            cer = r["cer"]
        elif "cer_percent" in r:
            cer = float(r["cer_percent"]) / 100
        else:
            cer = r.get("char_error_rate")
        if isinstance(cer, (int, float)) and isinstance(frag, (int, float)):
            out.append({"frag": frag, "cer": float(cer)})
    return sorted(out, key=lambda r: r["frag"])


def readability() -> dict:
    if not READABILITY.is_file():
        return {"status": "pending"}
    try:
        raw = json.loads(READABILITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: cannot read {READABILITY}: {exc}. The page shows 'report pending'.", file=sys.stderr)
        return {"status": "pending"}
    rows = normalise_readability(raw)
    if not rows:
        print(f"Warning: no FRAG and CER rows in {READABILITY}. The page shows 'report pending'.", file=sys.stderr)
        return {"status": "pending"}
    meta = {}
    if isinstance(raw, dict):
        for key in ("engine", "ocr", "size_px", "sample", "date", "threshold", "font_version"):
            if key in raw and isinstance(raw[key], (str, int, float)):
                meta[key] = raw[key]
    return {"status": "ok", "rows": rows, "meta": meta}


AGENT_AUTHORS = {"claude", "jac"}


def commits(limit: int = 10) -> list:
    """Return the latest commits: subject, short hash, date, agent flag.

    Author names are not published.
    """
    fmt = "%H%x1f%s%x1f%cs%x1f%an%x1f%b%x1e"
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", f"-n{limit}", f"--format={fmt}"],
                             capture_output=True, text=True, check=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for rec in out.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) < 5:
            continue
        sha, subject, date, author, body = parts
        agent = author.strip().lower() in AGENT_AUTHORS or "co-authored-by: claude" in body.lower()
        rows.append({"sha": sha, "short": sha[:7], "subject": subject, "date": date, "agent": agent})
    return rows


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

PAGES = ["index.html", "weft/index.html", "sans/index.html", "download/index.html", "404.html"]
TOKEN = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")
META = re.compile(r"\A<!--(.*?)-->\s*", re.S)


def render(text: str, values: dict, where: str) -> str:
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise BuildError(f"Unknown template value {{{{{key}}}}} in {where}.")
        return str(values[key])
    return TOKEN.sub(sub, text)


def page_meta(text: str) -> tuple[dict, str]:
    m = META.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def url_path(name: str) -> str:
    return quote(name, safe="/")


def fmt_range(axis: list | None) -> str:
    if not axis:
        return ""
    lo, hi = axis[0], axis[2]
    return f"{lo:g}–{hi:g}"


def sans_waterfall(axis: list, italic: bool) -> str:
    lo, hi = int(axis[0]), int(axis[2])
    steps = [w for w in range(100, 1000, 100) if lo <= w <= hi]
    if lo not in steps:
        steps.insert(0, lo)
    if hi not in steps:
        steps.append(hi)
    style = "italic" if italic else "normal"
    rows = []
    for w in steps:
        rows.append(
            f'<li><span class="wf-label">{w}</span>'
            f'<span class="wf-text" style="font-weight:{w};font-style:{style}">Proven for machines</span></li>'
        )
    return "\n".join(rows)


def font_face_css(chosen: dict, info: dict) -> str:
    """Return the @font-face rules for the site, with URLs from the CSS file."""
    out = ["/* Made by site/build.py. Do not edit. */"]
    w = info["weft"]["axes"].get("wght")
    weft_w = f"{w[0]:g} {w[2]:g}" if w else "400"
    out.append(
        "@font-face{font-family:\"mm Weft\";"
        f"src:url(\"../fonts/weft/{url_path(chosen['weft']['files']['vf'].name)}\") format(\"woff2\");"
        f"font-weight:{weft_w};font-style:normal;font-display:swap}}"
    )
    s = info["sans"]["axes"].get("wght") or [400, 400, 400]
    sans_w = f"{s[0]:g} {s[2]:g}"
    for role, style in (("vf", "normal"), ("italic", "italic")):
        name = chosen["sans"]["files"][role].name
        out.append(
            "@font-face{font-family:\"mm Sans\";"
            f"src:url(\"../fonts/sans/{url_path(name)}\") format(\"woff2\");"
            f"font-weight:{sans_w};font-style:{style};font-display:swap}}"
        )
    # machine-made Sans 0.1 makes the sharp (ss01) and straight (ss02) forms
    # the default. The upstream stand-in needs the features on to look the same.
    ff = '"ss01" 1, "ss02" 1' if chosen["sans"]["source"] == "standin" else "normal"
    out.append(f":root{{--sans-features:{ff}}}")
    return "\n".join(out) + "\n"


def short_version(fam_info: dict) -> str:
    """Return "version 0.100" from the name table, or "stand-in" for a stand-in."""
    if fam_info["source"] == "standin":
        return "stand-in font"
    m = re.search(r"(\d+\.\d+)", fam_info["version"])
    return f"version {m.group(1)}" if m else "version 0.1"


def swirl_tag(features: dict) -> str:
    """Return the tag of the swirl (Lingkar) stylistic set. Default: ss03."""
    for tag, label in features.items():
        if re.search(r"swirl|lingkar", label, re.I):
            return tag
    return "ss03" if "ss03" in features else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build(out: Path, source: str) -> None:
    chosen = select_fonts(source)

    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    # Copy the CSS, JS and images. The fonts go to fonts/ (below).
    shutil.copytree(SITE / "assets", out / "assets", ignore=shutil.ignore_patterns("fonts"))

    # Fonts.
    for fam, sel in chosen.items():
        dest = out / "fonts" / fam
        dest.mkdir(parents=True, exist_ok=True)
        for path in list(sel["files"].values()) + sel["extra"]:
            shutil.copy2(path, dest / path.name)
        if sel["source"] == "standin" and fam == "sans":
            shutil.copy2(STANDIN / "standin-PlusJakartaSans-OFL.txt", dest / "OFL.txt")

    info = {fam: inspect(sel["files"]["vf"]) for fam, sel in chosen.items()}
    for fam, sel in chosen.items():
        info[fam]["source"] = sel["source"]
        info[fam]["file"] = "fonts/" + fam + "/" + url_path(sel["files"]["vf"].name)
        info[fam]["planned_axes"] = FAMILIES[fam]["planned_axes"]
        info[fam]["release_url"] = RELEASES[fam]
    weft_font = TTFont(chosen["weft"]["files"]["vf"])
    info["weft"]["glyphs"] = glyph_map(weft_font)
    info["weft"]["commits"] = commits()

    (out / "data" / "weft.json").write_text(json.dumps(info["weft"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "sans.json").write_text(json.dumps(info["sans"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "readability.json").write_text(json.dumps(readability(), indent=1), encoding="utf-8")
    (out / "assets" / "fonts.css").write_text(font_face_css(chosen, info), encoding="utf-8")

    mark_font = weft_for_wordmark(chosen)
    wordmark = wordmark_svg(mark_font)
    (out / "assets" / "favicon.svg").write_text(favicon_svg(mark_font), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    weft_axes = info["weft"]["axes"]
    sans_axes = info["sans"]["axes"]
    planned_w = FAMILIES["weft"]["planned_axes"]
    standin_note = {
        "weft": ("Stand-in: this page uses the Weft phase 1 build (Regular only, a–z, A–Z, 0–9). "
                 "The 0.1 variable font replaces it when it is built."),
        "sans": ("Stand-in: this page uses upstream Plus Jakarta Sans. "
                 "The machine-made Sans 0.1 files replace it when they are built."),
    }
    values = {
        "REPO_URL": REPO_URL,
        "ORG_URL": ORG_URL,
        "WEFT_RELEASE": RELEASES["weft"],
        "SANS_RELEASE": RELEASES["sans"],
        "WORDMARK": wordmark,
        "WEFT_VERSION": html.escape(short_version(info["weft"])),
        "SANS_VERSION": html.escape(short_version(info["sans"])),
        "WEFT_CHAR_COUNT": info["weft"]["char_count"],
        "SANS_CHAR_COUNT": info["sans"]["char_count"],
        "WEFT_WGHT_RANGE": fmt_range(weft_axes.get("wght") or planned_w["wght"]),
        "WEFT_FRAG_RANGE": fmt_range(weft_axes.get("FRAG") or planned_w["FRAG"]),
        "WEFT_WGHT_CSS": " ".join(f"{v:g}" for v in (weft_axes.get("wght") or planned_w["wght"])[::2]),
        "SANS_WGHT_RANGE": fmt_range(sans_axes.get("wght") or FAMILIES["sans"]["planned_axes"]["wght"]),
        "SANS_WGHT_CSS": " ".join(f"{v:g}" for v in (sans_axes.get("wght") or FAMILIES["sans"]["planned_axes"]["wght"])[::2]),
        "SANS_WATERFALL": sans_waterfall(sans_axes.get("wght") or [400, 400, 400], italic=False),
        "SANS_WATERFALL_ITALIC": sans_waterfall(sans_axes.get("wght") or [400, 400, 400], italic=True),
        "SANS_SWIRL_TAG": swirl_tag(info["sans"]["features"]),
        "WEFT_STANDIN_NOTE": (f'<p class="standin" role="note">{standin_note["weft"]}</p>'
                              if chosen["weft"]["source"] == "standin" else ""),
        "SANS_STANDIN_NOTE": (f'<p class="standin" role="note">{standin_note["sans"]}</p>'
                              if chosen["sans"]["source"] == "standin" else ""),
        "SANS_FORMS_NOTE": ("The stand-in is upstream Plus Jakarta Sans, so this row turns on ss01 and ss02 "
                            "to show the forms that 0.1 makes default."
                            if chosen["sans"]["source"] == "standin" else
                            "These are the default forms of machine-made Sans 0.1. No feature is on."),
    }

    layout = (SITE / "templates" / "layout.html").read_text(encoding="utf-8")
    for rel in PAGES:
        src = (SITE / "pages" / rel).read_text(encoding="utf-8")
        meta, body = page_meta(src)
        depth = rel.count("/")
        root = "../" * depth if depth else "./"
        nav = {f"NAV_{k}": ' aria-current="page"' if meta.get("nav") == k.lower() else ""
               for k in ("HOME", "WEFT", "SANS", "DOWNLOAD")}
        scripts = "".join(f'<script src="{root}assets/{s.strip()}" defer></script>'
                          for s in meta.get("scripts", "").split(",") if s.strip())
        # The 404 page can open at any depth, so it uses absolute paths.
        if rel == "404.html":
            root = "/type/"
        page_values = dict(values, ROOT=root, **nav,
                           TITLE=meta.get("title", "machine-made type"),
                           DESCRIPTION=meta.get("description", ""),
                           BODY_CLASS=meta.get("class", ""),
                           SCRIPTS=scripts)
        # Preload the fonts that the first screen of the page uses.
        page_values["PRELOAD"] = "".join(
            f'<link rel="preload" href="{root}{info[fam]["file"]}" as="font" type="font/woff2" crossorigin>'
            for fam in meta.get("preload", "sans").split(",") if fam.strip() in info
        )
        page_values["BODY"] = render(body, page_values, rel)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(layout, page_values, "layout.html"), encoding="utf-8")

    print(f"Built the site in {out}.")
    for fam, sel in chosen.items():
        print(f"  {fam}: {sel['source']} font {sel['files']['vf'].name}, axes {info[fam]['axes'] or 'none'}")
    print(f"  readability: {readability()['status']}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the machine-made/type site.")
    ap.add_argument("--out", type=Path, default=SITE / "_site", help="output folder (default: site/_site)")
    args = ap.parse_args(argv)
    try:
        build(args.out.resolve(), FONT_SOURCE)
    except BuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
