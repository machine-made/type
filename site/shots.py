"""Browser check of the built site, by hand before a merge (CI builds the site but does not run a browser).

  uv run --with playwright==1.65.1 python3 site/shots.py [--site site/_site] [--out DIR] [--chrome PATH] [--axe FILE]

Serves the built site at /type/, as GitHub Pages does, with 404.html for a missing path. For every page, at 320, 360, 390,
1280 and 1920 px: no sideways scroll and no element past the right edge outside a scrolling or clipping box, one h1
and no skipped heading level, every image loaded, no request outside the site. At 390 px, every link in the two bars
and the footer is at least 44 px high. On the home page and the 404 page: no text drawn in a system font. With --axe
(axe-core's axe.min.js), axe runs at 1280 px on every page and every violation fails. Writes <page>-390.png,
<page>-1280.png and report.json to --out. Exits 1 on any problem.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import shutil
import sys
import tempfile
import threading
from itertools import pairwise
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, sync_playwright

PAGES = {"home": "", "weft": "weft/", "sans": "sans/", "heddle": "heddle/", "warp": "warp/", "download": "download/", "404": "no/such/page"}
WIDTHS = (320, 360, 390, 1280, 1920)
SHOTS = (390, 1280)
SCROLL_ALL = "async () => { for (let y = 0; y < document.body.scrollHeight; y += innerHeight / 2) { scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } scrollTo(0, 0); }"
BYTES = """() => { const t = {font: 0, image: 0};
  for (const e of performance.getEntriesByType('resource')) {
    if (/\\.woff2$/.test(e.name)) t.font += e.encodedBodySize; else if (/\\.(avif|jpg|png|svg)$/.test(e.name)) t.image += e.encodedBodySize; }
  return t; }"""
PROBE = """() => {
  const W = document.documentElement.clientWidth, past = [];
  const clipped = el => { for (let p = el.parentElement; p; p = p.parentElement) {
    const s = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) return true; } return false; };
  for (const el of document.body.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > W + 0.5 && !clipped(el) && !el.closest('.skip, .vh, .visually-hidden')) past.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right));
  }
  const links = [...document.querySelectorAll('.b1 a, .b1 [aria-current], .secs a, .logo, footer a')]
    .map(a => [a.textContent.trim() || a.className, a.getBoundingClientRect().height]);
  return {scroll: document.documentElement.scrollWidth, width: innerWidth, past: past.slice(0, 6),
          levels: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]),
          images: [...document.images].every(i => i.complete && i.naturalWidth > 0), links,
          dark: getComputedStyle(document.body).backgroundColor};
}"""


class Pages(http.server.SimpleHTTPRequestHandler):
    """GitHub Pages: a missing path gets /type/404.html with status 404."""

    def log_message(self, *args: object) -> None:
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        page = Path(self.directory) / "type" / "404.html"
        if code != 404 or not page.is_file():
            super().send_error(code, message, explain)
            return
        body = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def system_fonts(context: BrowserContext, page: Page) -> list[str]:
    """Every text node drawn, even in part, in a font that is not a web font of the page."""
    cdp = context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    root = cdp.send("DOM.getDocument", {"depth": -1, "pierce": False})["root"]
    bad: list[str] = []

    def walk(node: dict[str, Any]) -> None:
        if node.get("nodeName") in ("SCRIPT", "STYLE", "HEAD", "TITLE", "NOSCRIPT"):
            return
        kids = node.get("children", [])
        if any(c.get("nodeType") == 3 and c.get("nodeValue", "").strip() for c in kids):
            fonts = cdp.send("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]})["fonts"]
            text = "".join(c.get("nodeValue", "") for c in kids if c.get("nodeType") == 3).strip()
            bad.extend(f'{f["familyName"]} x{f["glyphCount"]} in "{text[:30]}"' for f in fonts if not f.get("isCustomFont"))
        for c in kids:
            walk(c)

    walk(root)
    cdp.detach()
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", type=Path, default=Path(__file__).resolve().parent / "_site")
    ap.add_argument("--out", type=Path, default=Path("shots"))
    ap.add_argument("--chrome", default=None)
    ap.add_argument("--axe", type=Path, default=None)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    axe = args.axe.read_text(encoding="utf-8") if args.axe else None
    top = Path(tempfile.mkdtemp())
    (top / "type").symlink_to(args.site.resolve())
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Pages, directory=str(top)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/type/"
    report, problems = [], []
    try:
        with sync_playwright() as pw:
            launch = {"executable_path": args.chrome, "args": ["--no-sandbox"]} if args.chrome else {}
            browser = pw.chromium.launch(**launch)
            for name, path in PAGES.items():
                for width in WIDTHS:
                    ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme="dark", device_scale_factor=1)
                    page = ctx.new_page()
                    outside: list[str] = []
                    page.on("request", lambda req, outside=outside: req.url.startswith(base) or req.url.startswith("data:") or outside.append(req.url))
                    answer = page.goto(base + path, wait_until="networkidle")
                    page.evaluate("document.fonts.ready")
                    page.evaluate(SCROLL_ALL)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(200)
                    p = page.evaluate(PROBE)
                    tag = f"{name} {width}"
                    entry = {"page": name, "width": width, "status": answer.status if answer else None, "scroll": p["scroll"], "dark": p["dark"]}
                    if (name == "404") != (entry["status"] == 404):
                        problems.append(f"{tag}: status {entry['status']}")
                    if p["scroll"] > p["width"]:
                        problems.append(f"{tag}: scrolls sideways ({p['scroll']} > {p['width']})")
                    if p["past"]:
                        problems.append(f"{tag}: past the right edge: {p['past']}")
                    lv = p["levels"]
                    if lv.count(1) != 1 or lv[0] != 1 or any(b - a > 1 for a, b in pairwise(lv)):
                        problems.append(f"{tag}: headings {lv}")
                    if not p["images"]:
                        problems.append(f"{tag}: an image failed to load")
                    if outside:
                        problems.append(f"{tag}: requests outside the site: {outside[:3]}")
                    if width == 390:
                        short = [(t, round(h, 1)) for t, h in p["links"] if h < 44]
                        if short:
                            problems.append(f"{tag}: links below 44 px: {short}")
                    if width in SHOTS:
                        shot = args.out / f"{name}-{width}.png"
                        page.screenshot(path=str(shot), full_page=True)
                        entry["shot"] = str(shot)
                        entry["bytes"] = page.evaluate(BYTES)
                        if name in ("home", "404"):
                            misses = system_fonts(ctx, page)
                            entry["system_fonts"] = misses
                            if misses:
                                problems.append(f"{tag}: text in a system font: {misses[:4]}")
                    if width == 1280 and axe:
                        page.add_script_tag(content=axe)
                        found = page.evaluate("async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => [v.id, v.nodes.length])")
                        entry["axe"] = found
                        if found:
                            problems.append(f"{tag}: axe {found}")
                    report.append(entry)
                    ctx.close()
            browser.close()
    finally:
        server.shutdown()
        shutil.rmtree(top)
    (args.out / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        return 1
    print(f"SHOTS OK ({len(report)} renders)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
