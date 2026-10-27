"""Compare the approved sketch engine with the built variable font.

Usage:
    python tools/sketch_compare.py [--font FONT] [--out ../proofs/heddle]

Renders the same lines twice in Chromium (Playwright): once with the
sketch engine (reference/heddle-sketch-0.1.js, canvas, no hairline) and
once with the variable font at the same weight and width. The proof
shows sketch, font and an overlay (sketch red, font blue, both dark
where they agree). It also writes the ink agreement (soft IoU of the
two renders) per location to sketch-compare.json.

Needs Playwright with Chromium. CI does not run this tool; the PNGs and
the JSON in proofs/heddle/ are committed.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
HEDDLE = HERE.parent
ROOT = HEDDLE.parent
ENGINE = HEDDLE / "reference" / "heddle-sketch-0.1.js"
FONT = ROOT / "fonts" / "heddle" / "variable" / "MachineMadeHeddle[wdth,wght].ttf"

PANGRAM = ["Sphinx of black quartz, judge my vow.", "THE QUICK BROWN FOX JUMPS"]
CHARSET = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789 .,:!'-–/"]

# Corners of the designspace, the default, and points between masters.
CORNERS = [(100, 70), (900, 70), (400, 100), (100, 140), (900, 140)]
BETWEEN = [(250, 85), (700, 100), (650, 120)]

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
@font-face{font-family:"Heddle";src:url("heddle.ttf");}
body{margin:0;padding:24px 28px;background:#fff;font:14px/1.3 "DejaVu Sans",sans-serif;color:#333;width:%(width)dpx}
h1{font-size:18px;margin:0 0 4px}
p.k{margin:0 0 18px;color:#666}
.block{margin:0 0 22px}
.lab{font-size:13px;color:#555;margin:0 0 4px}
.row{display:flex;align-items:flex-start;gap:10px}
.row b{display:inline-block;width:60px;font-size:11px;font-weight:normal;color:#888;padding-top:4px}
canvas,svg{display:block;background:#fff}
.ov{position:relative}
.ov svg{position:absolute;left:0;top:0;mix-blend-mode:multiply;background:transparent}
</style></head><body>
<h1>%(title)s</h1><p class="k">%(key)s</p>
<div id="blocks"></div>
<script>var module={exports:{}};</script>
<script src="engine.js"></script>
<script>
const SPEC=%(spec)s;
// The sketch engine puts its API on module.exports when `module` exists.
const Sh=module.exports;
function sketchCanvas(lines,o,color,bg){
  const s=o.size/1000, W=o.w, Hh=o.h;
  const cv=document.createElement('canvas'); cv.width=W; cv.height=Hh;
  const ctx=cv.getContext('2d');
  if(bg){ctx.fillStyle=bg;ctx.fillRect(0,0,W,Hh);}
  const p=Sh.params({wght:o.wght,wdth:o.wdth});
  lines.forEach((line,i)=>{
    let pen=o.left; const y=o.top+i*o.step;
    for(const ch of line){const b=Sh.glyphBox(ch,p); if(!b){pen+=260*s;continue;}
      ctx.save();ctx.translate(pen,y);ctx.scale(s,-s);ctx.fillStyle=color;Sh.drawGlyph(ctx,ch,p);ctx.restore();
      pen+=b.adv*s;}
  });
  return cv;
}
function fontSvg(lines,o,color,bg){
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg'); svg.setAttribute('width',o.w); svg.setAttribute('height',o.h);
  if(bg){const r=document.createElementNS(ns,'rect');r.setAttribute('width',o.w);r.setAttribute('height',o.h);r.setAttribute('fill',bg);svg.appendChild(r);}
  lines.forEach((line,i)=>{
    const t=document.createElementNS(ns,'text'); t.setAttribute('x',o.left); t.setAttribute('y',o.top+i*o.step);
    t.setAttribute('fill',color);
    t.setAttribute('style',`font-family:Heddle;font-size:${o.size}px;font-kerning:none;font-feature-settings:"kern" 0;font-variation-settings:"wght" ${o.wght},"wdth" ${o.wdth};white-space:pre`);
    t.textContent=line; svg.appendChild(t);
  });
  return svg;
}
document.fonts.load('40px Heddle').then(()=>{
  const root=document.getElementById('blocks');
  SPEC.blocks.forEach((b,k)=>{
    const div=document.createElement('div'); div.className='block';
    div.innerHTML=`<div class="lab">${b.label}</div>`;
    const r1=document.createElement('div');r1.className='row';r1.innerHTML='<b>sketch</b>';
    const c=sketchCanvas(b.lines,b,'#111','#fff'); c.id='sk'+k; r1.appendChild(c);
    const r2=document.createElement('div');r2.className='row';r2.innerHTML='<b>font</b>';
    const f=fontSvg(b.lines,b,'#111','#fff'); f.id='fo'+k; r2.appendChild(f);
    const r3=document.createElement('div');r3.className='row';r3.innerHTML='<b>overlay</b>';
    const ov=document.createElement('div');ov.className='ov';
    ov.appendChild(sketchCanvas(b.lines,b,'#e8202a','#fff'));
    ov.appendChild(fontSvg(b.lines,b,'#1d6fe0',null));
    r3.appendChild(ov);
    div.appendChild(r1);div.appendChild(r2);div.appendChild(r3);root.appendChild(div);
  });
  document.body.dataset.ready='1';
});
</script></body></html>"""


def block(lines, wght, wdth, size, width, label):
    step = round(size * 1.15)
    top = round(size * 0.95)
    h = top + step * (len(lines) - 1) + round(size * 0.32)
    return {"lines": lines, "wght": wght, "wdth": wdth, "size": size, "w": width,
            "h": h, "left": 8, "top": top, "step": step, "label": label}


def coverage(img: Image.Image) -> Image.Image:
    return img.convert("L").point(lambda v: 255 - v)


def soft_iou(a: Image.Image, b: Image.Image) -> float:
    a, b = coverage(a), coverage(b)
    lo = ImageChops.darker(a, b)
    hi = ImageChops.lighter(a, b)
    s_lo = sum(i * n for i, n in enumerate(lo.histogram()))
    s_hi = sum(i * n for i, n in enumerate(hi.histogram()))
    return s_lo / s_hi if s_hi else 1.0


def render(font: Path, title: str, key: str, blocks: list, out_png: Path, width: int) -> list[float]:
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(font, tmp / "heddle.ttf")
        shutil.copy(ENGINE, tmp / "engine.js")
        html = PAGE % {"width": width + 80, "title": title, "key": key,
                       "spec": json.dumps({"blocks": blocks})}
        (tmp / "page.html").write_text(html, encoding="utf-8")
        scores = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width + 136, "height": 800}, device_scale_factor=1)
            page.goto((tmp / "page.html").as_uri())
            page.wait_for_selector("body[data-ready='1']")
            page.wait_for_timeout(200)
            page.screenshot(path=str(out_png), full_page=True)
            for k in range(len(blocks)):
                a, b = tmp / f"a{k}.png", tmp / f"b{k}.png"
                page.locator(f"#sk{k}").screenshot(path=str(a))
                page.locator(f"#fo{k}").screenshot(path=str(b))
                scores.append(round(soft_iou(Image.open(a), Image.open(b)), 4))
            browser.close()
    return scores


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--font", type=Path, default=FONT)
    ap.add_argument("--out", type=Path, default=ROOT / "proofs" / "heddle")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    report = {}
    key = ("Each block: the sketch engine (canvas), the variable font (SVG text, no kerning), "
           "and both on top of each other: red is sketch only, blue is font only.")

    width = 1800
    blocks = [block(PANGRAM, w, d, 60, width, f"wght {w}, wdth {d}" + (" (between masters)" if (w, d) in BETWEEN else ""))
              for w, d in CORNERS + BETWEEN]
    s = render(args.font, "Heddle 0.1: sketch engine and font, pangram", key, blocks,
               args.out / "heddle-sketch-vs-font-pangram.png", width)
    report["pangram"] = {f"{b['wght']},{b['wdth']}": v for b, v in zip(blocks, s)}

    blocks = [block(CHARSET, w, d, 56, width, f"wght {w}, wdth {d}") for w, d in CORNERS]
    s = render(args.font, "Heddle 0.1: sketch engine and font, the 70 sketch characters", key, blocks,
               args.out / "heddle-sketch-vs-font-charset.png", width)
    report["charset"] = {f"{b['wght']},{b['wdth']}": v for b, v in zip(blocks, s)}

    report["note"] = ("Soft IoU of the ink of the sketch render and the font render "
                      "(1.0 = the same pixels). Rendered by tools/sketch_compare.py.")
    (args.out / "sketch-compare.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
