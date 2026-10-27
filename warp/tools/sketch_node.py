"""Run the approved sketch engine (reference/warp-sketch-0.2.js) in node.

Used by the proofs (sketch vs font overlay, equations set by the
sketch's maths setter) and by the tests (advances and bounds).

The engine file is read as it is. For the maths setter, the loader adds
one statement (`gd.it=!!p.ital`) so that each set glyph says whether it
is italic; the file on disk does not change.

Apache-2.0.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "reference" / "warp-sketch-0.2.js"

LOADER = """
const fs=require('fs');
let src=fs.readFileSync(%s,'utf8');
src=src.replace('gd.ch=ch;','gd.ch=ch;gd.it=!!p.ital;');
const m={exports:{}}; (new Function('module','exports',src))(m,m.exports); const W=m.exports;
"""


def node() -> str | None:
    return shutil.which("node")


def run(js: str) -> object:
    exe = node()
    if exe is None:
        raise RuntimeError("node is not installed")
    code = LOADER % json.dumps(str(ENGINE)) + js
    res = subprocess.run([exe, "-e", code], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def glyphs(params: dict, names: list[str], polys: bool = True) -> dict:
    """{name: {adv, dx, xmin, xmax, ymin, ymax, polys?}} for glyph names of the engine
    (characters, "0.os" old-style figures, "sc:A" small caps)."""
    js = (
        f"const p=W.params({json.dumps(params)});const out={{}};"
        f"for(const nm of {json.dumps(names)}){{const g=W.glyph(nm,p);if(!g)continue;"
        "const r={adv:g.adv,dx:g.dx,xmin:g.xmin,xmax:g.xmax,ymin:g.ymin,ymax:g.ymax};"
        + ("r.polys=g.polys.map(q=>q.map(v=>[Math.round((v[0]+g.dx)*10)/10,Math.round(v[1]*10)/10]));" if polys else "")
        + "out[nm]=r;}console.log(JSON.stringify(out));"
    )
    return run(js)


def math(tex: str, size: float, params: dict) -> dict:
    """Set a formula with the sketch's setter. Returns the box: w, h, d and items.

    Glyph items: {t:'g', ch, it, x, y, s} for font glyphs, or
    {t:'p', polys} for shapes the setter draws at size (radicals,
    stretched delimiters). Rule items: {t:'r', x, y, w, h}.
    """
    js = (
        f"const b=W.math({json.dumps(tex)},{{size:{size},params:{json.dumps(params)}}});"
        "const items=b.items.map(it=>{if(it.t==='r')return it;"
        "if(it.gd.ch)return {t:'g',ch:it.gd.ch,it:!!it.gd.it,x:it.x,y:it.y,s:it.s};"
        "return {t:'p',polys:it.gd.polys.map(q=>q.map(v=>[it.x+(v[0]+it.gd.dx)*it.s,it.y+v[1]*it.s]))};});"
        "console.log(JSON.stringify({w:b.w,h:b.h,d:b.d,items}));"
    )
    return run(js)
