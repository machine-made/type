"""Build the specimen and release site for machine-made/type.

Usage:
    python site/build.py            # writes site/_site/
    python site/build.py --out DIR  # writes DIR/

The script:

1. Selects the committed webfonts in fonts/<family>/webfonts/. It stops
   with an error when a file is missing, so a deploy never ships
   without the real fonts.
2. Copies the fonts, their licences and the static assets into the
   output folder.
3. Reads the fonts with fontTools and writes JSON for the pages:
   axes, character map, features, version.
4. Reads proofs/weft/readability.json (written by
   weft/tools/readability.py). It stops with an error when the file is
   missing or has no FRAG rows.
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

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent

REPO_URL = "https://github.com/machine-made/type"
ORG_URL = "https://github.com/machine-made"
RELEASES = {
    "weft": REPO_URL + "/releases/tag/weft-v0.1.0",
    "sans": REPO_URL + "/releases/tag/sans-v0.1.0",
}

# Font files per family, in fonts/<family>/webfonts/. Every role is
# required. "vf" is the file the pages use. The other WOFF2 files in the
# folder are copied too, so that the site also serves them. "licence" is
# copied next to the fonts as OFL.txt.
FAMILIES = {
    "weft": {
        "dir": ROOT / "fonts" / "weft" / "webfonts",
        "files": {
            "vf": "MachineMadeWeft[FRAG,wght].woff2",
            "bold": "MachineMadeWeft-Bold.woff2",
        },
        "licence": ROOT / "weft" / "OFL.txt",
        # Shown only when the loaded font does not have the axis.
        "planned_axes": {"wght": [100, 400, 900], "FRAG": [0, 0, 100]},
    },
    "sans": {
        "dir": ROOT / "fonts" / "sans" / "webfonts",
        "files": {
            "vf": "MachineMadeSans[wght].woff2",
            "italic": "MachineMadeSans-Italic[wght].woff2",
        },
        "licence": ROOT / "sans" / "OFL.txt",
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

def select_fonts() -> dict:
    """Return the font files per family. Stop when a file is missing."""
    chosen = {}
    for fam, spec in FAMILIES.items():
        files = {}
        for role, name in spec["files"].items():
            path = spec["dir"] / name
            if not path.is_file():
                raise BuildError(f"Font file not found: {path}. Build the fonts with "
                                 f"{fam}/scripts/build.sh and commit fonts/{fam}/.")
            files[role] = path
        if not spec["licence"].is_file():
            raise BuildError(f"Font licence not found: {spec['licence']}.")
        # Copy every webfont of the family, also the ones the pages do not use.
        extra = sorted(p for p in spec["dir"].glob("*.woff2") if p not in files.values())
        chosen[fam] = {"files": files, "extra": extra, "licence": spec["licence"]}
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
    """Return [{"frag": n, "cer": fraction}, ...] from the report.

    The report is the output of weft/tools/readability.py:
      {"weft": {"paragraph": {"FRAG 0": {"cer_mean": 0.0023, ...}, ...}}, ...}
    "cer_mean" is a fraction (0.0023 = 0.23 %), the mean over the sizes
    in "sizes_px".
    """
    if not isinstance(raw, dict):
        return []
    para = (raw.get("weft") or {}).get("paragraph") or {}
    out = []
    for key, row in para.items():
        m = re.fullmatch(r"FRAG\s+(\d+(?:\.\d+)?)", str(key))
        cer = row.get("cer_mean") if isinstance(row, dict) else None
        if m and isinstance(cer, (int, float)):
            frag = float(m.group(1))
            out.append({"frag": int(frag) if frag.is_integer() else frag, "cer": float(cer)})
    return sorted(out, key=lambda r: r["frag"])


def readability() -> dict:
    """Return the readability table for the Weft page. Stop when it is missing."""
    if not READABILITY.is_file():
        raise BuildError(f"{READABILITY} not found. Run weft/tools/readability.py and commit the report.")
    try:
        raw = json.loads(READABILITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"Cannot read {READABILITY}: {exc}.") from exc
    rows = normalise_readability(raw)
    if not rows:
        raise BuildError(f'No "weft.paragraph" FRAG rows in {READABILITY}.')
    meta = {}
    engine = raw.get("tesseract")
    if isinstance(engine, str):
        meta["engine"] = engine.replace("tesseract", "Tesseract", 1)
    sizes = raw.get("sizes_px")
    if isinstance(sizes, list) and sizes:
        meta["size_px"] = ", ".join(str(s) for s in sizes)
    ref = ((raw.get("reference") or {}).get("paragraph") or {}).get("static") or {}
    if isinstance(ref.get("cer_mean"), (int, float)):
        meta["reference_cer"] = float(ref["cer_mean"])
        meta["reference_font"] = "DejaVu Sans Mono"
    gate = raw.get("gate") or {}
    if isinstance(gate.get("pass"), bool):
        meta["gate_pass"] = gate["pass"]
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
    # machine-made Sans 0.1 has the straight forms as the default, so no
    # feature is on. The sharp forms are in ss02.
    out.append(":root{--sans-features:normal}")
    return "\n".join(out) + "\n"


def short_version(fam_info: dict) -> str:
    """Return "version 0.100" from the name table."""
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

def build(out: Path) -> None:
    chosen = select_fonts()
    report = readability()

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
        shutil.copy2(sel["licence"], dest / "OFL.txt")

    info = {fam: inspect(sel["files"]["vf"]) for fam, sel in chosen.items()}
    for fam, sel in chosen.items():
        info[fam]["file"] = "fonts/" + fam + "/" + url_path(sel["files"]["vf"].name)
        info[fam]["planned_axes"] = FAMILIES[fam]["planned_axes"]
        info[fam]["release_url"] = RELEASES[fam]
    weft_font = TTFont(chosen["weft"]["files"]["vf"])
    info["weft"]["glyphs"] = glyph_map(weft_font)
    info["weft"]["commits"] = commits()

    (out / "data" / "weft.json").write_text(json.dumps(info["weft"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "sans.json").write_text(json.dumps(info["sans"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "readability.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (out / "assets" / "fonts.css").write_text(font_face_css(chosen, info), encoding="utf-8")

    mark_font = weft_for_wordmark(chosen)
    wordmark = wordmark_svg(mark_font)
    (out / "assets" / "favicon.svg").write_text(favicon_svg(mark_font), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    weft_axes = info["weft"]["axes"]
    sans_axes = info["sans"]["axes"]
    planned_w = FAMILIES["weft"]["planned_axes"]
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
        "SANS_FORMS_NOTE": "The default forms of machine-made Sans 0.1: straight a j p q r y. No feature is on.",
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
        print(f"  {fam}: {sel['files']['vf'].name}, axes {info[fam]['axes'] or 'none'}")
    print(f"  readability: {len(report['rows'])} FRAG rows from {READABILITY.relative_to(ROOT)}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the machine-made/type site.")
    ap.add_argument("--out", type=Path, default=SITE / "_site", help="output folder (default: site/_site)")
    args = ap.parse_args(argv)
    try:
        build(args.out.resolve())
    except BuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
