"""Build the specimen and release site for machine-made/type.

Usage:
    python site/build.py                     # writes site/_site/; reads the GitHub facts through gh
    python site/build.py --out DIR           # writes DIR/
    python site/build.py --facts FILE        # reads the facts from FILE instead of the GitHub API
    python site/build.py --save-facts FILE   # also writes the facts it read to FILE

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
5. Reads the live facts from the GitHub API (home.py): the newest
   release of each family and of each house, the release files, the
   licence and the workflows. It stops with an error when a call fails,
   so a page with stale facts is never written.
6. Writes the home page and the 404 page in the design system of the
   four sites (assets/system.css, home.py), and fills the family and
   download pages into the same two bars and footer.

Needs Python 3.11+, fontTools with brotli (for WOFF2), Pillow (for the
images) and gh with a token (GH_TOKEN) for the facts.
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

from fontTools.ttLib import TTFont

import home
from home import BuildError

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent

REPO_URL = "https://github.com/machine-made/type"
RELEASE_VERSION = "0.2.0"
RELEASES = {fam: f"{REPO_URL}/releases/tag/{fam}-v{RELEASE_VERSION}"
            for fam in ("weft", "sans", "heddle", "warp")}
# Files of a release: the zip holds every font file, SHA256SUMS lists their hashes.
RELEASE_ZIPS = {fam: f"{REPO_URL}/releases/download/{fam}-v{RELEASE_VERSION}/machine-made-{fam}-{RELEASE_VERSION}.zip"
                for fam in RELEASES}
RELEASE_SUMS = {fam: f"{REPO_URL}/releases/download/{fam}-v{RELEASE_VERSION}/SHA256SUMS"
                for fam in RELEASES}

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
    "heddle": {
        "dir": ROOT / "fonts" / "heddle" / "webfonts",
        "files": {
            "vf": "MachineMadeHeddle[wdth,wght].woff2",
            "bold": "MachineMadeHeddle-Bold.woff2",
        },
        "licence": ROOT / "heddle" / "OFL.txt",
        "planned_axes": {"wght": [100, 400, 900], "wdth": [70, 100, 140]},
    },
    # Warp 0.2 is six static fonts; "vf" is the Regular (the pages read
    # its character map). The variable font comes in the next release.
    "warp": {
        "dir": ROOT / "fonts" / "warp" / "webfonts",
        "files": {
            "vf": "MachineMadeWarp-Regular.woff2",
            "italic": "MachineMadeWarp-Italic.woff2",
            "bold": "MachineMadeWarp-Bold.woff2",
            "bolditalic": "MachineMadeWarp-BoldItalic.woff2",
            "display": "MachineMadeWarpDisplay-Regular.woff2",
            "displayitalic": "MachineMadeWarpDisplay-Italic.woff2",
        },
        "licence": ROOT / "warp" / "OFL.txt",
        "planned_axes": {},
    },
}

# Heddle rows on its page: width names from the STAT table of the font.
HEDDLE_WEIGHTS = [(100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"),
                   (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"),
                   (900, "Black")]

READABILITY = ROOT / "proofs" / "weft" / "readability.json"


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
    if 0x370 <= cp <= 0x3FF:
        return "Greek"
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
               "Accented and other letters", "Greek", "Other figures", "Other symbols"]


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

# The family and download pages, filled into templates/layout.html. The home page and the 404 page come from
# home.py.
PAGES = ["weft/index.html", "sans/index.html", "heddle/index.html", "warp/index.html", "download/index.html"]
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


def stat_widths(font: TTFont) -> list:
    """Return [(value, name), ...] of the wdth axis values in STAT."""
    if "STAT" not in font or font["STAT"].table.AxisValueArray is None:
        return []
    axes = [a.AxisTag for a in font["STAT"].table.DesignAxisRecord.Axis]
    out = []
    for v in font["STAT"].table.AxisValueArray.AxisValue:
        if hasattr(v, "AxisIndex") and axes[v.AxisIndex] == "wdth":
            out.append((v.Value, font["name"].getDebugName(v.ValueNameID)))
    return sorted(out)


def heddle_rows(axis: str, values: list, text: str, fixed: str) -> str:
    """Return <li> rows of Heddle at each value of one axis."""
    rows = []
    for v, name in values:
        settings = f'"{axis}" {v:g}, {fixed}'
        rows.append(
            f'<li><span class="row-k"><span class="row-v">{v:g}</span>{html.escape(name)}</span>'
            f'<span class="row-t heddle" style="font-variation-settings:{html.escape(settings)}">'
            f"{html.escape(text)}</span></li>"
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
    sh = info["heddle"]["axes"]
    sh_w = sh.get("wght") or [400, 400, 400]
    sh_d = sh.get("wdth") or [100, 100, 100]
    out.append(
        "@font-face{font-family:\"mm Heddle\";"
        f"src:url(\"../fonts/heddle/{url_path(chosen['heddle']['files']['vf'].name)}\") format(\"woff2\");"
        f"font-weight:{sh_w[0]:g} {sh_w[2]:g};font-stretch:{sh_d[0]:g}% {sh_d[2]:g}%;"
        "font-style:normal;font-display:swap}"
    )
    # Warp: six static fonts in two families. Text: Regular, Italic, Bold,
    # Bold Italic (opsz 10). Display: Regular, Italic (opsz 60).
    wf = chosen["warp"]["files"]
    for fam_name, role, weight, style in (
        ("mm Warp", "vf", 400, "normal"), ("mm Warp", "italic", 400, "italic"),
        ("mm Warp", "bold", 700, "normal"), ("mm Warp", "bolditalic", 700, "italic"),
        ("mm Warp Display", "display", 400, "normal"), ("mm Warp Display", "displayitalic", 400, "italic"),
    ):
        out.append(
            f"@font-face{{font-family:\"{fam_name}\";"
            f"src:url(\"../fonts/warp/{url_path(wf[role].name)}\") format(\"woff2\");"
            f"font-weight:{weight};font-style:{style};font-display:swap}}"
        )
    # machine-made Sans has the straight forms as the default, so no
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

def build(out: Path, facts_file: Path | None = None, save_facts: Path | None = None) -> None:
    chosen = select_fonts()
    report = readability()
    facts = home.load_facts(facts_file) if facts_file else home.fetch_facts()
    if save_facts:
        save_facts.write_text(json.dumps(facts, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    # Copy the CSS, JS and images. The fonts go to fonts/ (below).
    # system.css goes into each page through home.system_css(), not as a file.
    shutil.copytree(SITE / "assets", out / "assets", ignore=shutil.ignore_patterns("fonts", "system.css"))

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
    heddle_font = TTFont(chosen["heddle"]["files"]["vf"])
    info["heddle"]["glyphs"] = glyph_map(heddle_font)
    warp_font = TTFont(chosen["warp"]["files"]["vf"])
    info["warp"]["glyphs"] = glyph_map(warp_font)
    info["warp"]["styles"] = {role: "fonts/warp/" + url_path(p.name) for role, p in chosen["warp"]["files"].items()}
    heddle_widths = stat_widths(heddle_font)
    if not heddle_widths:
        raise BuildError("The Heddle font has no wdth values in STAT.")

    (out / "data" / "weft.json").write_text(json.dumps(info["weft"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "sans.json").write_text(json.dumps(info["sans"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "heddle.json").write_text(json.dumps(info["heddle"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "warp.json").write_text(json.dumps(info["warp"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "data" / "readability.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (out / "assets" / "fonts.css").write_text(font_face_css(chosen, info), encoding="utf-8")

    (out / ".nojekyll").write_text("", encoding="utf-8")
    home.build_images(out)

    weft_axes = info["weft"]["axes"]
    sans_axes = info["sans"]["axes"]
    heddle_axes = info["heddle"]["axes"]
    planned_sh = FAMILIES["heddle"]["planned_axes"]
    planned_w = FAMILIES["weft"]["planned_axes"]
    values = {
        "REPO_URL": REPO_URL,
        "WEFT_RELEASE": RELEASES["weft"],
        "SANS_RELEASE": RELEASES["sans"],
        "HEDDLE_RELEASE": RELEASES["heddle"],
        "WARP_RELEASE": RELEASES["warp"],
        "RELEASE_VERSION": RELEASE_VERSION,
        "WEFT_ZIP": RELEASE_ZIPS["weft"],
        "SANS_ZIP": RELEASE_ZIPS["sans"],
        "HEDDLE_ZIP": RELEASE_ZIPS["heddle"],
        "WARP_ZIP": RELEASE_ZIPS["warp"],
        "WEFT_SUMS": RELEASE_SUMS["weft"],
        "SANS_SUMS": RELEASE_SUMS["sans"],
        "HEDDLE_SUMS": RELEASE_SUMS["heddle"],
        "WARP_SUMS": RELEASE_SUMS["warp"],
        "WARP_VERSION": html.escape(short_version(info["warp"])),
        "WARP_CHAR_COUNT": info["warp"]["char_count"],
        "WARP_GLYPH_COUNT": info["warp"]["glyph_count"],
        "HEDDLE_VERSION": html.escape(short_version(info["heddle"])),
        "HEDDLE_CHAR_COUNT": info["heddle"]["char_count"],
        "HEDDLE_WGHT_RANGE": fmt_range(heddle_axes.get("wght") or planned_sh["wght"]),
        "HEDDLE_WDTH_RANGE": fmt_range(heddle_axes.get("wdth") or planned_sh["wdth"]),
        "HEDDLE_WIDTH_ROWS": heddle_rows("wdth", heddle_widths, "Grotesk 1958", '"wght" 700'),
        "HEDDLE_WEIGHT_ROWS": heddle_rows("wght", HEDDLE_WEIGHTS, "Hamburgefonstiv", '"wdth" 100'),
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
        "SANS_FORMS_NOTE": "The default forms of machine-made Sans: straight a j p q r y. No feature is on.",
    }

    # The home page and the 404 page: the system pages, with font subsets and the tester.
    axes = {fam: {"axes": [(t, int(v[0]), int(v[2])) for t, v in info[fam]["axes"].items()],
                  "statics": len(home.statics(facts["assets"][fam]))} for fam in chosen}
    full = {fam: sel["files"]["vf"].name for fam, sel in chosen.items()}
    pages = home.build_fonts(list(home.home_pages(facts, axes, full)),
                             {fam: sel["files"]["vf"] for fam, sel in chosen.items()}, out)
    written = {"index.html": pages[0], "404.html": pages[1]}

    layout = (SITE / "templates" / "layout.html").read_text(encoding="utf-8")
    system = home.system_css()
    for rel in PAGES:
        src = (SITE / "pages" / rel).read_text(encoding="utf-8")
        meta, body = page_meta(src)
        root = "../" * rel.count("/")
        scripts = "".join(f'<script src="{root}assets/{s.strip()}" defer></script>'
                          for s in meta.get("scripts", "").split(",") if s.strip())
        page_values = dict(values, ROOT=root, SYSTEM=system, TOKENS=home.tokens(), GROUND=home.THEME["ground"],
                           BAR1=home.bar1(), BAR2=home.bar2(root, rel.split("/")[0] + "/"), FOOTER=home.footer(),
                           TITLE=meta.get("title", "machine-made fonts"),
                           DESCRIPTION=meta.get("description", ""),
                           BODY_CLASS=meta.get("class", ""),
                           SCRIPTS=scripts)
        # Preload the fonts that the first screen of the page uses.
        page_values["PRELOAD"] = "".join(
            f'<link rel="preload" href="{root}{info[fam]["file"]}" as="font" type="font/woff2" crossorigin>'
            for fam in meta.get("preload", "sans").split(",") if fam.strip() in info
        )
        page_values["BODY"] = render(body, page_values, rel)
        written[rel] = render(layout, page_values, "layout.html")
    home.check_pages(written)
    for rel, text in written.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    print(f"Built the site in {out}.")
    for fam, sel in chosen.items():
        print(f"  {fam}: {sel['files']['vf'].name}, axes {info[fam]['axes'] or 'none'}")
    print(f"  readability: {len(report['rows'])} FRAG rows from {READABILITY.relative_to(ROOT)}")
    print(f"  heddle widths: {', '.join(f'{v:g} {n}' for v, n in heddle_widths)}")
    print(f"  warp: {len(chosen['warp']['files'])} styles, {info['warp']['char_count']} characters")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the machine-made/type site.")
    ap.add_argument("--out", type=Path, default=SITE / "_site", help="output folder (default: site/_site)")
    ap.add_argument("--facts", type=Path, help="read the GitHub facts from this file instead of the API")
    ap.add_argument("--save-facts", type=Path, help="also write the GitHub facts to this file")
    args = ap.parse_args(argv)
    try:
        build(args.out.resolve(), args.facts, args.save_facts)
    except BuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
