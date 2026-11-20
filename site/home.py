"""The home page, the 404 page and the shared parts of the type site, in the design system of the four sites.

The style is assets/system.css, copied unchanged from machine-made/machine-made.github.io (its first line names the
commit). Every page carries the same two bars and footer as the three house sites. The home page holds the type
line, Latest (the newest release of each family), the tester, the families, the release table built from the
release files, and the houses row (the newest release of each house).

The facts come from the GitHub API through gh: fetch_facts() raises BuildError on any failure, so a page with stale
facts is never written. The build checks what it writes: contrast, one h1 and heading order, banned words,
homebrew-tap, Latest with no repeat, and font subsets that keep their axes and the features the style uses.
"""

from __future__ import annotations

import datetime
import html
import io
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
TYPE_URL = "https://machine-made.github.io/type/"
REPO = "machine-made/type"
REPO_URL = f"https://github.com/{REPO}"
LINE = "Four typefaces, made by code."
TITLE = "machine-made type: Weft, Sans, Heddle and Warp"
# Bar 1 and the footer: the three houses, then type.
SITES = (
    ("machine-made", "https://machine-made.github.io/"),
    ("openfluids", "https://openfluids.github.io/"),
    ("BoringQuantSystems", "https://boringquantsystems.github.io/"),
    ("type", TYPE_URL),
)
ORGS = {"machine-made": "machine-made", "openfluids": "openfluids", "BoringQuantSystems": "BoringQuantSystems"}
NEVER = {"homebrew-tap"}
# The type site uses the machine-made palette.
THEME = {"ground": "#0a0a0b", "surface": "#141416", "line": "#26262a", "text": "#ecebe6", "muted": "#8b8b90", "accent": "#e5251c"}
PAIRS = (("text", "ground", 7.0), ("muted", "ground", 4.5), ("text", "surface", 7.0), ("muted", "surface", 4.5), ("accent", "ground", 3.0))
SECTIONS = (("Weft", "weft/"), ("Sans", "sans/"), ("Heddle", "heddle/"), ("Warp", "warp/"), ("Download", "download/"))
FAMILY_CSS = {
    "weft": ('"mm Weft"', "font-weight:100 900"),
    "sans": ('"mm Sans"', "font-weight:200 800"),
    "heddle": ('"mm Heddle"', "font-weight:100 900;font-stretch:70% 140%"),
    "warp": ('"mm Warp"', "font-weight:400"),
}
# family key, name, description, tile specimen
FAMILIES = (
    ("weft", "Weft", "a monospace on a grid, for code and tables", "Rg 0042"),
    ("sans", "Sans", "a sans for long reading", "Rg Ka 0042"),
    ("heddle", "Heddle", "a Swiss grotesk for posters and headlines", "Grotesk 1958"),
    ("warp", "Warp", "a serif drawn by a pen, for papers and maths", "Warp αβγ ∂∫"),
)
# The tester: one slider per axis of each family (label, axis, min, max, start).
CONTROLS = {
    "weft": (("Weight", "wght", 100, 900, 400), ("FRAG", "FRAG", 0, 100, 0)),
    "sans": (("Weight", "wght", 200, 800, 400),),
    "heddle": (("Weight", "wght", 100, 900, 400), ("Width", "wdth", 70, 140, 100)),
    "warp": (),
}
KEEP = "0123456789 ·–"
USED_FEATURES = {"ss01", "tnum", "onum", "pnum", "smcp", "c2sc", "kern"}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
BANNED = re.compile(r"\b(founder|brief|jac|card|session|codex)\b", re.I)
PLATE_SIZES = "(min-width: 1264px) 282px, (min-width: 1000px) 22vw, (min-width: 520px) 46vw, calc(100vw - 32px)"
HOUSE_BANNERS = {"machine-made": "machine-made", "openfluids": "openfluids", "BoringQuantSystems": "boringquantsystems"}
BANNER_SIZE = (1408, 469)
BANNER_WIDTHS = (704, 1408)
MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30"><style>.k{fill:#0a0a0b}.r{fill:#e5251c}'
    "@media (prefers-color-scheme:dark){.k{fill:#ecebe6}}</style>"
    + "".join(f'<rect class="{"r" if (x, y) == (11, 11) else "k"}" x="{x}" y="{y}" width="8" height="8"/>' for y in (0, 11, 22) for x in (0, 11, 22))
    + "</svg>\n"
)
MK = (
    '<svg class="mk" viewBox="0 0 30 30" aria-hidden="true" focusable="false">'
    + "".join(f'<rect class="{"on" if (x, y) == (11, 11) else "o"}" x="{x}" y="{y}" width="8" height="8"/>' for y in (0, 11, 22) for x in (0, 11, 22))
    + "</svg>"
)
RED_CELL = ' class="r"'
CURRENT = ' aria-current="page"'
LOGO = (
    '<svg viewBox="0 0 30 30" aria-hidden="true" focusable="false">'
    + "".join(f'<rect{RED_CELL if (x, y) == (11, 11) else ""} x="{x}" y="{y}" width="8" height="8"/>' for y in (0, 11, 22) for x in (0, 11, 22))
    + "</svg>"
)


class BuildError(Exception):
    """A build step cannot continue."""


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# ---------------------------------------------------------------------------
# The facts
# ---------------------------------------------------------------------------

def gh(*args: str) -> str:
    try:
        done = subprocess.run(["gh", *args], capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(f"gh {' '.join(args[:2])} could not run ({exc.__class__.__name__}); set GH_TOKEN and install gh.") from exc
    if done.returncode != 0:
        raise BuildError(f"gh {' '.join(args[:2])} failed: {done.stderr.strip()[:200]}")
    return done.stdout


RELEASE = "tagName publishedAt url isDraft isPrerelease"
TYPE_RELEASES = (
    'releases(first:100{after}, orderBy:{{field:CREATED_AT, direction:DESC}})'
    "{{pageInfo{{hasNextPage endCursor}} nodes{{" + RELEASE + "}}}}"
)


def graphql(query: str) -> dict:
    try:
        answer = json.loads(gh("api", "graphql", "-f", f"query={query}"))
    except ValueError as exc:
        raise BuildError("gh api graphql did not return JSON") from exc
    if answer.get("errors") or not answer.get("data"):
        raise BuildError("graphql errors: " + json.dumps(answer.get("errors"))[:200])
    return answer["data"]


def stable(r: dict | None) -> bool:
    return bool(r) and not r.get("isDraft") and not r.get("isPrerelease") and bool(r.get("publishedAt"))


def fetch_facts() -> dict:
    """The live facts of the home page, from the GitHub API. Any failure stops the build."""
    org_parts = [
        f'o{i}: organization(login:"{login}"){{ description repositories(first:100, privacy:PUBLIC, isArchived:false)'
        "{pageInfo{hasNextPage} nodes{name latestRelease{" + RELEASE + "} "
        "releases(first:5, orderBy:{field:CREATED_AT, direction:DESC}){nodes{" + RELEASE + "}}}} }"
        for i, login in enumerate(ORGS.values())
    ]
    data = graphql('query{ typerepo: repository(owner:"machine-made", name:"type"){ ' + TYPE_RELEASES.format(after="")
                   + " } " + " ".join(org_parts) + " }")
    facts: dict = {"fetched": datetime.datetime.now(datetime.UTC).date().isoformat(), "families": {}, "houses": {}}
    # Every page of type releases: the newest publication of each family wins, whatever the creation order.
    page = data["typerepo"]["releases"]
    nodes = list(page["nodes"])
    while page["pageInfo"]["hasNextPage"]:
        after = ', after:"' + page["pageInfo"]["endCursor"] + '"'
        page = graphql('query{ typerepo: repository(owner:"machine-made", name:"type"){ '
                       + TYPE_RELEASES.format(after=after) + " } }")["typerepo"]["releases"]
        nodes += page["nodes"]
    for r in nodes:
        fam = r["tagName"].split("-v")[0]
        if fam in CONTROLS and stable(r) and (fam not in facts["families"] or r["publishedAt"] > facts["families"][fam]["publishedAt"]):
            facts["families"][fam] = {k: r[k] for k in ("tagName", "publishedAt", "url")}
    if set(facts["families"]) != set(CONTROLS):
        raise BuildError(f"no release found for {sorted(set(CONTROLS) - set(facts['families']))}")
    for i, name in enumerate(ORGS):
        org = data[f"o{i}"]
        if org["repositories"]["pageInfo"]["hasNextPage"]:
            raise BuildError(f"{name} has more than 100 public repositories; read the next page before building")
        newest = []
        for repo in org["repositories"]["nodes"]:
            if repo["name"] in NEVER:
                continue
            # The five newest releases may all be prereleases; the latest stable release still counts.
            rels = [r for r in [*repo["releases"]["nodes"], repo["latestRelease"]] if stable(r)]
            if rels:
                r = max(rels, key=lambda x: x["publishedAt"])
                newest.append((r["publishedAt"], repo["name"], r["tagName"]))
        newest.sort(reverse=True)
        facts["houses"][name] = {"line": org["description"] or "", "newest": newest[0] if newest else None}
    facts["assets"] = {fam: gh("api", f"repos/{REPO}/releases/tags/{rel['tagName']}", "--jq", ".assets[].name").split()
                       for fam, rel in facts["families"].items()}
    # The licences come from the checkout, like the workflows below.
    licence = (ROOT / "LICENSE").read_text(encoding="utf-8")
    facts["licence"] = "Apache-2.0" if "Apache License" in licence and "Version 2.0" in licence else "unknown"
    facts["ofl"] = "SIL Open Font License 1.1" in (ROOT / "LICENSING.md").read_text(encoding="utf-8")
    # The workflows come from the checkout: the site workflow may read contents only, not actions.
    facts["workflows"] = {}
    for fam in CONTROLS:
        path = ROOT / ".github" / "workflows" / f"{fam}.yml"
        if path.is_file():
            body = path.read_text(encoding="utf-8")
            facts["workflows"][fam] = {"build": "build" in body.lower(), "test": bool(re.search(r"pytest|\btests?\b", body))}
    return facts


def load_facts(path: Path) -> dict:
    try:
        facts = json.loads(path.read_text(encoding="utf-8"))
        datetime.date.fromisoformat(facts["fetched"])
        if set(facts["families"]) != set(CONTROLS) or set(facts["houses"]) != set(ORGS):
            raise KeyError("families or houses")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BuildError(f"cannot read the facts file {path}: {exc}") from exc
    return facts


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------

def date_text(iso: str, fetched: str) -> str:
    d = datetime.date.fromisoformat(iso[:10])
    return f"{d.day} {MONTHS[d.month - 1]}" + ("" if d.year == datetime.date.fromisoformat(fetched).year else f" {d.year}")


def time_html(iso: str, fetched: str) -> str:
    return f'<time datetime="{iso[:10]}">{date_text(iso, fetched)}</time>'


def facts_html(parts: list[str]) -> str:
    return '<p class="facts"><span>' + "".join(f"<span>{p}</span>" for p in parts) + "</span></p>"


def label(text: str, ident: str) -> str:
    return f'<h2 class="lbl" id="{ident}">{MK}<span>{esc(text)}</span></h2>'


def row(ident: str, text: str, inner: str, cls: str = "row") -> str:
    return f'<section class="{cls}" aria-labelledby="{ident}">{label(text, ident)}{inner}</section>'


def bar1() -> str:
    lis = "".join(
        f'<li><span aria-current="page">{esc(n)}</span></li>' if u == TYPE_URL else f'<li><a href="{esc(u)}">{esc(n)}</a></li>'
        for n, u in SITES
    )
    return f'<nav class="b1" aria-label="Sites"><ul class="wrap">{lis}</ul></nav>'


def bar2(root: str, current: str = "") -> str:
    """The logo (the mark and the word type, a link home) and the sections. On the home page and the 404 page the
    sections are full addresses, as in the approved page; on a family page the current one is marked."""
    secs = "".join(
        f'<a href="{root}{path}"{CURRENT if path == current else ""}>{name}</a>'
        for name, path in SECTIONS
    )
    secs += f'<a href="{REPO_URL}">GitHub</a>'
    return (
        f'<header class="b2"><div class="wrap"><a class="logo" href="{root or "./"}">{LOGO}<span class="wm">type</span></a>'
        f'<nav class="secs" aria-label="Sections">{secs}</nav></div></header>'
    )


def footer() -> str:
    return '<footer class="wrap"><div class="fl"><ul>' + "".join(f'<li><a href="{esc(u)}">{esc(n)}</a></li>' for n, u in SITES) + "</ul></div></footer>"


def tokens() -> str:
    return ":root{" + ";".join(f"--{k}:{v}" for k, v in THEME.items()) + "}"


def system_css() -> str:
    text = (SITE / "assets" / "system.css").read_text(encoding="utf-8")
    if not re.match(r"/\* Copied unchanged from machine-made/machine-made\.github\.io, src/system\.css at commit\n   [0-9a-f]{40}\.", text):
        raise BuildError("assets/system.css must start with the comment that names its source commit.")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip()) + "\n"


def head(title: str, root: str, preload: str) -> str:
    social = "".join(
        f'<meta {a}="{k}" content="{esc(v)}">'
        for a, k, v in (
            ("property", "og:type", "website"), ("property", "og:title", TITLE), ("property", "og:description", LINE),
            ("property", "og:url", TYPE_URL), ("property", "og:image", f"{TYPE_URL}og.jpg"), ("property", "og:image:width", "1200"),
            ("property", "og:image:height", "630"), ("property", "og:image:alt", "type"), ("name", "twitter:card", "summary_large_image"),
        )
    )
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        f'<title>{esc(title)}</title><meta name="description" content="{esc(LINE)}">'
        f'<meta name="color-scheme" content="dark"><meta name="theme-color" content="{THEME["ground"]}">'
        f'<link rel="icon" href="{root}assets/mark.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{root}assets/touch.png">'
        f"{social}{preload}"
    )


def picture(root: str, stem: str, widths: tuple[int, int], size: tuple[int, int]) -> str:
    avif = ", ".join(f"{root}img/{stem}-{w}.avif {w}w" for w in widths)
    jpeg = ", ".join(f"{root}img/{stem}-{w}.jpg {w}w" for w in widths)
    return (
        f'<picture><source type="image/avif" srcset="{avif}" sizes="{PLATE_SIZES}">'
        f'<img src="{root}img/{stem}-{widths[1]}.jpg" srcset="{jpeg}" sizes="{PLATE_SIZES}" width="{size[0]}" height="{size[1]}" alt="" loading="lazy" decoding="async"></picture>'
    )


def numword(n: int) -> str:
    return "zero one two three four five six seven eight nine ten".split()[n] if n <= 10 else str(n)


def statics(names: list[str]) -> list[str]:
    out = []
    for n in names:
        m = re.match(r"MachineMade[A-Z][a-z]+(Display)?-([A-Za-z]+)\.woff2$", n)
        if m:
            out.append(("Display " if m.group(1) else "") + re.sub(r"(?<=[a-z])(?=[A-Z])", " ", m.group(2)))
    order = ["Regular", "Italic", "Bold", "Bold Italic", "Display Regular", "Display Italic"]
    return sorted(out, key=lambda s: order.index(s) if s in order else 99)


def formats(names: list[str]) -> str:
    ext = sorted({n.rsplit(".", 1)[1].upper() for n in names if n.endswith((".ttf", ".otf", ".woff2"))}, key=["TTF", "OTF", "WOFF2"].index)
    return " and ".join([", ".join(ext[:-1]), ext[-1]] if len(ext) > 1 else ext)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def latest(facts: dict) -> str:
    items = sorted(((v["publishedAt"], k.capitalize(), v) for k, v in facts["families"].items()), key=lambda x: (x[0], x[1]), reverse=True)
    if len({n for _, n, _ in items}) != len(items):
        raise BuildError("Latest repeats a family.")
    lis = "".join(
        f'<li><a href="{esc(r["url"])}">{esc(n)}</a>{facts_html([esc(re.sub(r"^[a-z]+-(?=v)", "", r["tagName"])), time_html(r["publishedAt"], facts["fetched"])])}</li>'
        for _, n, r in items
    )
    return row("g-latest", "Latest", f'<ol class="latest n{len(items)}">{lis}</ol>', "row tight")


def houses_row(facts: dict) -> str:
    lis = []
    for name, url in SITES[:3]:
        house = facts["houses"][name]
        if house["newest"]:
            _, repo, tag = house["newest"][:3]
            fx = facts_html([f"{esc(repo)} {esc(tag)}", time_html(house["newest"][0], facts["fetched"])])
        else:
            fx = facts_html(["unreleased"])
        img = picture("", f"banner-{HOUSE_BANNERS[name]}", BANNER_WIDTHS, BANNER_SIZE)
        lis.append(f'<li class="plate"><a class="pic" href="{url}" aria-label="{name}">{img}</a><p class="ds">{esc(house["line"])}</p>{fx}</li>')
    return row("g-houses", "The houses", f'<ul class="grid g3">{"".join(lis)}</ul>')


def tester(axes: dict) -> str:
    rows = []
    for k, n, _, _ in FAMILIES:
        cs = "".join(
            f'<label class="ctl"><span>{lab}</span><input type="range" min="{a}" max="{b}" value="{v}" data-t="t-{k}" data-p="{p}" '
            f'aria-label="{n} {lab.lower()}"><output class="n">{v}</output></label>'
            for lab, p, a, b, v in CONTROLS[k]
        )
        if not CONTROLS[k]:
            cs = f"<span>No weight axis: {numword(axes[k]['statics'])} static fonts</span>"
        rows.append(f'<div class="trow"><div class="tmeta"><b>{n}</b>{cs}</div><p class="tline {k}" id="t-{k}">{esc(LINE)}</p></div>')
    return (
        f'<section class="row" aria-labelledby="g-try">{label("Type here", "g-try")}'
        f'<div><label class="vh" for="tt">Text to set in the four families</label><input class="tin" id="tt" type="text" placeholder="{esc(LINE)}" autocomplete="off" spellcheck="false"></div>'
        f'<div class="tester">{"".join(rows)}</div></section>'
    )


def families(axes: dict) -> str:
    tiles = []
    for k, n, d, s in FAMILIES:
        fx = [f"{t} {a}–{z}" for t, a, z in axes[k]["axes"]] or [f"{numword(axes[k]['statics']).capitalize()} static fonts"]
        tiles.append(
            f'<li class="plate" id="f-{k}"><a class="pic" href="{TYPE_URL}{k}/"><span class="tile {k}"><span class="vh">{n} specimen: </span>{esc(s)}</span></a>'
            f'<p class="ds">{n}, {esc(d)}</p>{facts_html(fx)}</li>'
        )
    return row("g-families", "Families", f'<ul class="grid g2">{"".join(tiles)}</ul>')


def release(facts: dict, axes: dict) -> str:
    versions = {facts["families"][k]["tagName"].split("-v")[1] for k, *_ in FAMILIES}
    title = f"Release {versions.pop()}" if len(versions) == 1 else "Releases"
    rows = []
    if facts["licence"] == "Apache-2.0" and facts["ofl"]:
        rows.append(("Licence", "Fonts: SIL Open Font License 1.1. Code: Apache-2.0."))
    for k, n, *_ in FAMILIES:
        names = facts["assets"][k]
        st = statics(names)
        parts = []
        if axes[k]["axes"]:
            ax = ", ".join(f"{t} {a}–{z}" for t, a, z in axes[k]["axes"])
            parts.append(f"Variable ({ax})" + (", upright and italic" if any("Italic" in a for a in names) else ""))
            if st:
                parts.append("static " + " and ".join(st))
        else:
            parts.append(f"{numword(len(st)).capitalize()} static fonts: " + ", ".join(st))
        rows.append((n, ". ".join(p[0].upper() + p[1:] for p in parts) + f". {formats(names)}."))
    wf = facts["workflows"]
    if all(wf.get(k, {}).get("build") for k, *_ in FAMILIES):
        rows.append(("Built by", "CI, one workflow per family" + (", with its tests." if all(wf[k]["test"] for k, *_ in FAMILIES) else ".")))
    items = "".join(f'<li><span class="k">{k}</span><p>{esc(v)}</p></li>' for k, v in rows)
    items += f'<li><span class="k">Source</span><p><a class="u" href="{REPO_URL}">github.com/{REPO}</a></p></li>'
    return row("g-release", title, f'<div><ul class="table">{items}</ul><p class="more"><a class="u" href="{TYPE_URL}download/">Download and install</a></p></div>')


def script(full: dict) -> str:
    """The tester: the field sets the four lines; a slider sets one axis. The page ships subsets; the full fonts load
    once, the first time the visitor types."""
    urls = json.dumps({k: f"fonts/{k}/{quote(v, safe='')}" for k, v in full.items()})
    return (
        "<script>(function(){var d=document;d.documentElement.classList.add('js');"
        "d.addEventListener('DOMContentLoaded',function(){"
        "var i=d.getElementById('tt');if(!i){return;}var L=d.querySelectorAll('.tline'),f=i.getAttribute('placeholder');"
        f"var U={urls};"
        "var full=false;function F(){if(full||!window.FontFace){return;}full=true;"
        "[['weft','100 900',''],['sans','200 800',''],['heddle','100 900','70% 140%'],['warp','400','']].forEach(function(a){"
        "var n='mm '+a[0].charAt(0).toUpperCase()+a[0].slice(1)+' Full',o={weight:a[1]};if(a[2]){o.stretch=a[2];}"
        "new FontFace(n,'url('+U[a[0]]+')',o).load().then(function(x){d.fonts.add(x);d.documentElement.classList.add('full');}).catch(function(){});});}"
        "i.addEventListener('input',function(){F();for(var k=0;k<L.length;k++){L[k].textContent=i.value||f;}});"
        "var S=d.querySelectorAll('.ctl input');for(var k=0;k<S.length;k++){(function(s){s.addEventListener('input',function(){"
        "var l=d.getElementById(s.getAttribute('data-t')),p=s.getAttribute('data-p');"
        "if(p==='wght'){l.style.fontWeight=s.value;}else if(p==='wdth'){l.style.fontStretch=s.value+'%';}else{l.style.fontVariationSettings='\"FRAG\" '+s.value;}"
        "s.nextElementSibling.value=s.value;});})(S[k]);}});})();</script>"
    )


def line_html(tag: str, extra: str = "") -> str:
    t = re.sub(r"\b\w+(?:-\w+)+\b", lambda w: '<span class="nb">' + w.group(0) + "</span>", esc(LINE))
    return f'<{tag} class="line heddle{extra}">{t}</{tag}>'


def page(body: str, title: str, root: str, preload: str, faces: str, system: str, js: str = "", nf: bool = False) -> str:
    return (
        head(title, root, preload) + f"<style>{faces}\n{tokens()}</style><style>{system}</style>{js}</head>\n"
        f'<body><a class="skip" href="#main">Skip to content</a>{bar1()}{bar2(root)}'
        f'<main id="main" class="wrap{" nf" if nf else ""}">{body}</main>{footer()}</body></html>\n'
    )


def home_pages(facts: dict, axes: dict, full: dict) -> tuple[str, str]:
    """The home page and the 404 page, with the @font-face rules left as a mark for build_fonts()."""
    system = system_css()
    body = line_html("h1", " fit1") + latest(facts) + tester(axes) + families(axes) + release(facts, axes) + houses_row(facts)
    home = page(body, TITLE, "", "<!--PRELOAD-->", "/*FACES*/", system, script(full))
    nf_body = (
        '<h1 class="line heddle">Not found</h1><p class="ds">This page does not exist.</p>'
        '<p class="more"><a class="u" href="/type/">Back to type</a></p>'
    )
    missing = page(nf_body, "Not found \u2013 type", "/type/", "<!--PRELOAD-->", "/*FACES*/", system, nf=True)
    return home, missing


# ---------------------------------------------------------------------------
# Fonts and images
# ---------------------------------------------------------------------------

class FaceText(HTMLParser):
    VOID = {"img", "input", "br", "meta", "link", "source", "rect", "hr"}

    def __init__(self, face: str) -> None:
        super().__init__(convert_charrefs=True)
        self.face, self.stack, self.out = face, [], set()

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            cls = (dict(attrs).get("class") or "").split()
            self.stack.append(self.face in cls or (self.face == "heddle" and "wm" in cls))

    def handle_endtag(self, tag):
        if tag not in self.VOID and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if any(self.stack):
            self.out |= set(data)


def strip_code(text: str) -> str:
    return re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S)


def visible_text(text: str) -> str:
    text = strip_code(text)
    text = re.sub(r'(?:aria-label|alt|placeholder|title|content)="([^"]*)"', lambda m: " " + m.group(1) + " ", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def face_text(text: str, face: str) -> set[str]:
    p = FaceText(face)
    p.feed(strip_code(text))
    return p.out


def build_fonts(pages: list[str], sources: dict[str, Path], out: Path) -> list[str]:
    """Cut one subset of each family for the home page and the 404 page (fonts/home/<family>.woff2). Weft and Sans
    keep the text of the pages and its capitals; Heddle and Warp keep the text set in them. Returns the pages with
    their @font-face rules and the preload of Heddle, the face of the type line."""
    from fontTools import subset as fts

    text = "".join(visible_text(p) for p in pages) + KEEP
    text = "".join(sorted(set(text + text.upper())))
    (out / "fonts" / "home").mkdir(parents=True, exist_ok=True)
    for fam, src in sources.items():
        chars = text
        if fam in ("heddle", "warp"):
            keep = set(KEEP)
            for p in pages:
                keep |= face_text(p, fam)
            chars = "".join(sorted(keep))
        opts = fts.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.hinting = False
        opts.desubroutinize = True
        opts.name_IDs = ["*"]
        font = fts.load_font(str(src), opts)
        before = meta(font)
        sub = fts.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        after = meta(font)
        lost = (before[1] & USED_FEATURES) - after[1]
        if after[0] != before[0] or lost:
            raise BuildError(f"the subset of {src.name} lost an axis or the features {sorted(lost)}")
        fts.save_font(font, str(out / "fonts" / "home" / f"{fam}.woff2"), opts)
    done = []
    for p, root in zip(pages, ("", "/type/"), strict=True):
        faces = "".join(
            f'@font-face{{font-family:{FAMILY_CSS[f][0]};src:url({root}fonts/home/{f}.woff2) format("woff2");{FAMILY_CSS[f][1]};font-style:normal;font-display:swap}}'
            for f in sources
        )
        preload = f'<link rel="preload" href="{root}fonts/home/heddle.woff2" as="font" type="font/woff2" crossorigin>'
        done.append(p.replace("/*FACES*/", faces, 1).replace("<!--PRELOAD-->", preload, 1))
    return done


def meta(font) -> tuple[list, set]:
    axes = [(a.axisTag, a.minValue, a.maxValue) for a in font["fvar"].axes] if "fvar" in font else []
    feats = {r.FeatureTag for t in ("GSUB", "GPOS") if t in font for r in font[t].table.FeatureList.FeatureRecord}
    return axes, feats


def build_images(out: Path) -> None:
    """The house banners of the houses row (AVIF and JPEG at 704 and 1408 px), the touch icon and the favicon."""
    from PIL import Image, ImageDraw

    (out / "img").mkdir(parents=True, exist_ok=True)
    for stem in HOUSE_BANNERS.values():
        src = SITE / "img" / f"banner-{stem}.jpg"
        if not src.is_file():
            raise BuildError(f"{src} is missing.")
        im = Image.open(src).convert("RGB")
        for w in BANNER_WIDTHS:
            r = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            r.save(out / "img" / f"banner-{stem}-{w}.avif", quality=62, speed=4)
            r.save(out / "img" / f"banner-{stem}-{w}.jpg", quality=82, optimize=True, progressive=True)
    big = 360
    ground = tuple(int(THEME["ground"][i : i + 2], 16) for i in (1, 3, 5))
    im = Image.new("RGB", (big, big), ground)
    draw = ImageDraw.Draw(im)
    pad, unit = big * 0.2, big * 0.6 / 30
    for y in (0, 11, 22):
        for x in (0, 11, 22):
            colour = THEME["accent"] if (x, y) == (11, 11) else THEME["text"]
            draw.rectangle([pad + x * unit, pad + y * unit, pad + (x + 8) * unit - 1, pad + (y + 8) * unit - 1], fill=colour)
    buf = io.BytesIO()
    im.resize((180, 180), Image.LANCZOS).save(buf, format="PNG", optimize=True)
    (out / "assets" / "touch.png").write_bytes(buf.getvalue())
    (out / "assets" / "mark.svg").write_text(MARK_SVG, encoding="utf-8")
    og = SITE / "img" / "og.jpg"
    if not og.is_file():
        raise BuildError(f"{og} is missing.")
    (out / "og.jpg").write_bytes(og.read_bytes())


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def luminance(colour: str) -> float:
    c = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_pages(pages: dict[str, str], own: tuple[str, ...] = ("index.html", "404.html")) -> None:
    """Contrast, one h1, heading order and homebrew-tap on every page the build writes; banned words on the pages
    whose text this module writes (own)."""
    for fg, bg, floor in PAIRS:
        if contrast(THEME[fg], THEME[bg]) < floor:
            raise BuildError(f"{fg} on {bg} is {contrast(THEME[fg], THEME[bg]):.2f}, below {floor}")
    for rel, text in pages.items():
        if len(re.findall(r"<h1[ >]", text)) != 1:
            raise BuildError(f"{rel} needs exactly one h1")
        levels = [int(x) for x in re.findall(r"<h([1-6])[ >]", text)]
        if levels[0] != 1 or any(b - a > 1 for a, b in zip(levels, levels[1:], strict=False)):
            raise BuildError(f"{rel} skips a heading level: {levels}")
        hit = BANNED.search(visible_text(text)) if rel in own else None
        if hit:
            raise BuildError(f"{rel} has the word {hit.group(0)!r}")
        if "homebrew-tap" in text:
            raise BuildError(f"{rel} names homebrew-tap, which is never listed")
