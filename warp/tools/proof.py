"""Render the Warp proof sheets into proofs/warp/.

Usage:
    python tools/proof.py [--only NAME,...]

Sheets:
    warp-sketch-vs-font-<style>.png   the sketch engine (red) and the font (blue) overlaid,
                                      for the sketch charset; dark where they agree
    sketch-compare.json               IoU of sketch and font per glyph and style
    warp-paragraph.png                a paragraph from a paper at 9 to 12 pt
    warp-greek.png                    the Greek set in every style
    warp-equations.png                equations set by the sketch's maths setter with the font's glyphs
    warp-kerning.png                  pairs without and with kerning
    warp-accents.png                  accented letters and small caps
    warp-smallcaps-figures.png        small caps and the four figure styles
    warp-styles.png                   Regular, Italic, Bold, Bold Italic, Display, Display Italic
    warp-charset-<style>.png          every character of the font
    warp-latin-ext.png                Latin Extended-A, Ș ș Ț ț, Greek tonos: texts per language (0.2)
    warp-italic-caps.png              the italic capitals with their own forms (0.2)
    warp-before-after.png             0.1 and 0.2: the forms that changed, the word space (0.2)
    warp-math.png                     formulas set by LuaLaTeX with the MATH table (tools/math_proof.py; 0.2)

The sketch parts need node (tools/sketch_node.py). Text is set with
FreeType and Raqm through Pillow, so the OpenType features apply.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from loom import build as Bd  # noqa: E402
from loom import charset as CS  # noqa: E402
from loom.raster import PolyPen, fill_glyph, fill_sweep  # noqa: E402
import sketch_node as SN  # noqa: E402

ROOT = HERE.parents[1]
FONTS = ROOT / "fonts" / "warp" / "ttf"
OUT = ROOT / "proofs" / "warp"

PAPER = (246, 241, 231)
INK = (28, 26, 22)
BLUE = (31, 58, 107)
RED = (192, 57, 43)
RULE = (205, 196, 178)
MUTED = (120, 112, 98)

VER = "0.2"
STYLE_ORDER = ["Regular", "Italic", "Bold", "BoldItalic", "Display", "DisplayItalic"]
LABEL = {"Regular": "Regular", "Italic": "Italic", "Bold": "Bold", "BoldItalic": "Bold Italic",
         "Display": "Display", "DisplayItalic": "Display Italic"}


def font_path(key: str) -> Path:
    return FONTS / f"{Bd.ps_name(Bd.STYLES[key])}.ttf"


def F(key: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path(key)), size=round(size), layout_engine=ImageFont.Layout.RAQM)


def label(draw, xy, text, size=22, fill=MUTED, key="Regular", features=("smcp", "c2sc")):
    draw.text(xy, text, font=F(key, size), fill=fill, features=list(features))


def sketch_params(key: str) -> dict:
    st = Bd.STYLES[key]
    prm = dict(st.params)
    # The sketch engine knows stem, contrast and serif; serifw and width
    # are new in the font (the bold styles), so the sketch draws without them.
    return {k: v for k, v in prm.items() if k in ("opsz", "ital", "stem", "contrast", "serif")}


# ------------------------------------------------------------ overlay

def overlay(key: str, report: dict) -> None:
    chars = CS.SKETCH_CHARS
    sk = SN.glyphs(sketch_params(key), list(chars))
    tt = TTFont(font_path(key))
    gs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    em, cols = 120, 16
    s = em / 1000
    cell_w, cell_h = int(em * 1.05), int(em * 1.45)
    rows = (len(chars) + cols - 1) // cols
    W, H = cols * cell_w + 60, rows * cell_h + 110
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (30, 22), f"warp {VER} · {LABEL[key].lower()} · sketch 0.2 engine (red) and font (blue); dark where they agree",
          size=24, fill=INK)
    ious = {}
    for i, ch in enumerate(chars):
        r, c = divmod(i, cols)
        x0, base = 30 + c * cell_w, 80 + r * cell_h + int(em * 1.05)
        if ch not in sk:
            continue
        g = sk[ch]
        k = min(1.0, (cell_w - 8) / max(g["adv"], 1) / s)
        sc = s * k
        tr = lambda p: (x0 + p[0] * sc, base - p[1] * sc)  # noqa: E731
        size = (cell_w, cell_h + 40)
        ms = Image.new("L", (W, H), 0)
        fill_sweep(ImageDraw.Draw(ms), g["polys"], tr)
        mf = Image.new("L", (W, H), 0)
        name = cmap.get(ord(ch))
        if name:
            pen = PolyPen(gs)
            gs[name].draw(pen)
            fill_glyph(ImageDraw.Draw(mf), pen.polys, tr)
        box = (x0 - 4, base - int(em * 1.15), x0 + cell_w, base + int(em * 0.35))
        a = np.asarray(ms.crop(box), dtype=float) / 255
        b = np.asarray(mf.crop(box), dtype=float) / 255
        inter, union = np.minimum(a, b).sum(), np.maximum(a, b).sum()
        ious[ch] = round(float(inter / union), 4) if union else 1.0
        both = np.minimum(a, b)
        only_s, only_f = a - both, b - both
        reg = np.asarray(img.crop(box), dtype=float)
        for col, m in ((INK, both), (RED, only_s), (BLUE, only_f)):
            reg = reg * (1 - m[..., None]) + np.array(col) * m[..., None]
        img.paste(Image.fromarray(reg.astype("uint8")), box[:2])
        d.text((x0, base + int(em * 0.2)), f"{ious[ch]:.2f}", font=F("Regular", 13), fill=MUTED)
    vals = list(ious.values())
    report[key] = {"params_sketch": sketch_params(key), "mean_iou": round(float(np.mean(vals)), 4),
                   "min_iou": round(float(min(vals)), 4), "min_glyph": min(ious, key=ious.get), "iou": ious}
    img.save(OUT / f"warp-sketch-vs-font-{key.lower()}.png", optimize=True)


# ------------------------------------------------------------ text helpers

def set_runs(d, runs, x, y, width, size, lead, styles=("Regular", "Italic")):
    """Set [(text, italic)] in a column. Returns the y after the last line."""
    words = []
    for text, it in runs:
        for w in text.split(" "):
            if w:
                words.append((w, styles[1] if it else styles[0]))
    fonts = {k: F(k, size) for k in set(styles)}
    space = fonts[styles[0]].getlength(" ")
    cx = x
    for w, k in words:
        wl = fonts[k].getlength(w)
        if cx > x and cx + wl > x + width:
            cx = x
            y += lead
        d.text((cx, y), w, font=fonts[k], fill=INK)
        cx += wl + space
    return y + lead


ABSTRACT = [
    ("Abstract.", True),
    ("We study the drawing of a thin viscous thread from a heated preform. When the draw ratio exceeds a "
     "critical value near 20.2, the steady state loses stability through a Hopf bifurcation and the radius "
     "of the fibre oscillates, a regime known as", False),
    ("draw resonance.", True),
    ("Writing the axial velocity as a base flow plus a small perturbation, we obtain a linear eigenvalue "
     "problem for the growth rate λ, whose spectrum we compute by Chebyshev collocation on 128 points. "
     "The leading mode depends only weakly on the capillary number", False), ("Ca;", True),
    ("inertia and cooling, not surface tension, set the threshold (Fig. 3, Table 1).", False),
]


def paragraph() -> None:
    W = 2200
    img = Image.new("RGB", (W, 2350), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · a paragraph from a paper · text styles at opsz 10", 26, INK)
    y = 80
    for pt in (9, 10, 11, 12):
        px = pt * 2  # 144 dpi
        label(d, (40, y), f"{pt} pt at 144 dpi ({px} px), regular and italic", 20)
        y = set_runs(d, ABSTRACT, 40, y + 34, 1040, px, px * 1.45)
        y += 28
    y2 = 80
    for pt in (9, 10, 11, 12):
        px = round(pt * 4 / 3)  # 96 dpi
        label(d, (1160, y2), f"{pt} pt at 96 dpi ({px} px)", 20)
        y2 = set_runs(d, ABSTRACT, 1160, y2 + 34, 640, px, px * 1.45)
        y2 += 28
    y = max(y, y2) + 20
    d.line([(40, y), (W - 40, y)], fill=RULE)
    label(d, (40, y + 16), "bold and bold italic, 10 pt at 144 dpi", 20)
    y = set_runs(d, ABSTRACT, 40, y + 50, 1040, 20, 29, styles=("Bold", "BoldItalic"))
    label(d, (1160, y - 400 if y > 1200 else y + 16), "", 20)
    img = img.crop((0, 0, W, min(img.height, y + 40)))
    img.save(OUT / "warp-paragraph.png", optimize=True)


def greek() -> None:
    caps = "".join(ch for ch in CS.GREEK if ch.isupper())
    low = "".join(ch for ch in CS.GREEK if ch.islower())
    img = Image.new("RGB", (2300, 1500), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · greek: 24 capitals, 24 lowercase and final sigma", 26, INK)
    y = 80
    for key in STYLE_ORDER:
        label(d, (40, y + 30), LABEL[key].lower(), 20)
        d.text((260, y), caps, font=F(key, 64), fill=INK)
        d.text((260, y + 92), low, font=F(key, 64), fill=INK)
        y += 210
    d.line([(40, y), (2260, y)], fill=RULE)
    d.text((40, y + 20), "λ μ σ ω ρ: ∂u/∂t + (u·∇)u = −∇p/ρ + ν∇²u · αβγ aα oο uυ vν nη", font=F("Regular", 44), fill=INK)
    img = img.crop((0, 0, 2300, y + 100))
    img.save(OUT / "warp-greek.png", optimize=True)


EQS = [
    ("Navier–Stokes", r"\rho\left(\frac{\partial u}{\partial t}+u\cdot\nabla u\right)=-\nabla p+\mu\nabla^2u+f"),
    ("Euler", r"e^{i\pi}+1=0"),
    ("Gauss", r"\int_{-\infty}^{\infty}e^{-x^2}\,dx=\sqrt{\pi}"),
    ("Basel", r"\sum_{n=1}^{\infty}\frac{1}{n^2}=\frac{\pi^2}{6}"),
    ("Resolvent", r"R(\omega)=\left(i\omega-L\right)^{-1}"),
]


def equations() -> None:
    size = 64
    params = {"opsz": 24}
    regular, italic = TTFont(font_path("Regular")), TTFont(font_path("Italic"))
    fonts = {False: (regular.getGlyphSet(), regular.getBestCmap()), True: (italic.getGlyphSet(), italic.getBestCmap())}
    boxes = [(n, SN.math(t, size, params)) for n, t in EQS]
    W = 2000
    H = 90 + sum(int(b["h"] + b["d"]) + 70 for _, b in boxes)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · equations set by the sketch 0.2 setter with the font's glyphs (text, opsz 10); "
                       "grey: the sketch's own radicals and delimiters (the font's MATH table: warp-math.png)", 22, INK)
    y = 80
    missing = set()
    for name, b in boxes:
        base = y + b["h"] + 10
        label(d, (40, base - 30), name.lower(), 22)
        x0 = 380
        for it in b["items"]:
            if it["t"] == "r":
                d.rectangle([x0 + it["x"], base - it["y"] - it["h"], x0 + it["x"] + it["w"], base - it["y"]], fill=INK)
            elif it["t"] == "p":
                fill_sweep(d, it["polys"], lambda p: (x0 + p[0], base - p[1]), ink=(110, 104, 94))
            else:
                gs, cmap = fonts[it["it"]]
                gname = cmap.get(ord(it["ch"]))
                if gname is None:
                    missing.add(it["ch"])
                    continue
                k = it["s"]
                pen = PolyPen(gs, dx=0, dy=0)
                gs[gname].draw(pen)
                fill_glyph(d, pen.polys, lambda p, k=k, it=it: (x0 + it["x"] + p[0] * k, base - it["y"] - p[1] * k),
                           ink=INK, paper=PAPER)
        y = base + b["d"] + 60
        d.line([(40, y - 25), (W - 40, y - 25)], fill=RULE)
    if missing:
        raise SystemExit(f"Characters missing from the font: {sorted(missing)}")
    img.save(OUT / "warp-equations.png", optimize=True)


KERN_SAMPLES = ["To Ta Te Ty TA T. Va Vo VA V. Ya Yo YA Y.", "AV AT AY Av Aw Ay A’ LT LV LY L’ Ly",
                "P. P, PA F. Fa r. y. v. w. f’ f) ’s ’A", "Τα Το ΤΑ ΓΑ Γο ΥΑ ΑΤ ΑΥ Κο Λ.",
                "ro xo ox ev ex vs ka Tx · το τα τυ γο νο χο · Ťa Ŧo Ŵa Ŷo",
                "7. 74 · 7. 74 (old-style)"]


def kerning() -> None:
    # 4 styles x (heading 34 + 6 lines x 140 + 10) + 80 top = 3616 px
    img = Image.new("RGB", (2300, 3700), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · kerning: each pair line without kerning (grey) and with kerning (ink)", 26, INK)
    y = 80
    for key in ("Regular", "Italic", "Bold", "Display"):
        label(d, (40, y), LABEL[key].lower(), 20)
        y += 34
        f = F(key, 56)
        for line in KERN_SAMPLES:
            feats = ["onum"] if "old-style" in line else []
            text = line.replace(" (old-style)", "")
            d.text((60, y), text, font=f, fill=(150, 142, 128), features=feats + ["-kern"])
            d.text((60, y + 64), text, font=f, fill=INK, features=feats + ["kern"])
            y += 140
        y += 10
    img = img.crop((0, 0, 2300, y + 20))
    img.save(OUT / "warp-kerning.png", optimize=True)


def accents() -> None:
    acc = "".join(ch for ch in CS.LATIN1_LETTERS + "Ÿ" if unicodedata.decomposition(ch)
                  and not unicodedata.decomposition(ch).startswith("<"))
    upper = "".join(c for c in acc if c.isupper())
    lower = "".join(c for c in acc if c.islower())
    img = Image.new("RGB", (2300, 2000), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · accents: marks drawn by the pen, composites; small caps below", 26, INK)
    y = 80
    for key in STYLE_ORDER:
        label(d, (40, y + 26), LABEL[key].lower(), 20)
        d.text((260, y), upper, font=F(key, 52), fill=INK)
        d.text((260, y + 92), lower, font=F(key, 52), fill=INK)
        y += 200
    d.text((260, y), lower, font=F("Regular", 52), fill=INK, features=["smcp"])
    label(d, (40, y + 26), "small caps", 20)
    y += 100
    d.text((260, y), "í ï ĵ ã́ ȫ ě ñ À Ô", font=F("Regular", 52), fill=INK)
    label(d, (40, y + 26), "mark, mkmk", 20)
    img = img.crop((0, 0, 2300, y + 110))
    img.save(OUT / "warp-accents.png", optimize=True)


def smallcaps_figures() -> None:
    img = Image.new("RGB", (2300, 2400), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · small caps (smcp, c2sc) and figures", 26, INK)
    y = 80
    for key in ("Regular", "Italic", "Bold", "Display"):
        f = F(key, 52)
        label(d, (40, y + 22), LABEL[key].lower(), 20)
        d.text((300, y), "Small Caps for Labels: Fig. 3, Table 1", font=f, fill=INK, features=["smcp"])
        d.text((300, y + 70), "NASA, ESA AND CERN · ÉTÉ", font=f, fill=INK, features=["c2sc", "smcp"])
        y += 160
    d.line([(40, y), (2260, y)], fill=RULE)
    y += 20
    rows = [("default: lining, tabular", []), ("onum: old-style, proportional", ["onum"]),
            ("pnum: lining, proportional", ["pnum"]), ("onum tnum: old-style, tabular", ["onum", "tnum"])]
    for key in ("Regular", "Italic", "Bold"):
        f = F(key, 52)
        for name, feats in rows:
            label(d, (40, y + 22), f"{LABEL[key].lower()} · {name}", 18)
            d.text((620, y), "0123456789 · 1.25 × 10³ · 2026 · ¼ ½ ¾", font=f, fill=INK, features=feats or ["-onum"])
            y += 74
        y += 14
    for name, text, feats in (("sups", "x2 + y2 = r2 · 10-15 · 123456789", ["sups"]),
                              ("subs", "H2O, CO2, x0 x1 x9", ["subs"]),
                              ("frac", "1/2 3/4 17/32 355/113", ["frac"]),
                              ("unicode", "x² ⁰¹²³⁴⁵⁶⁷⁸⁹ ₀₁₂₃₄₅₆₇₈₉", [])):
        label(d, (40, y + 22), name, 18)
        d.text((620, y), text, font=F("Regular", 52), fill=INK, features=feats)
        y += 74
    d.text((620, y), "1111 / 7777 / 0000", font=F("Regular", 52), fill=INK)
    d.text((1300, y), "1111 / 7777 / 0000", font=F("Regular", 52), fill=INK, features=["pnum"])
    label(d, (40, y + 22), "tabular vs proportional", 18)
    img = img.crop((0, 0, 2300, y + 100))
    img.save(OUT / "warp-smallcaps-figures.png", optimize=True)


def styles() -> None:
    img = Image.new("RGB", (2300, 1700), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · the six styles", 26, INK)
    y = 80
    for key in STYLE_ORDER:
        label(d, (40, y + 40), LABEL[key].lower(), 20)
        d.text((300, y), "Hamburgefonstiv 1972 αβγ ∂∫", font=F(key, 96), fill=INK)
        y += 150
    d.line([(40, y), (2260, y)], fill=RULE)
    y += 20
    for key in STYLE_ORDER[:4]:
        label(d, (40, y + 6), LABEL[key].lower(), 18)
        d.text((300, y), "The steady state loses stability through a Hopf bifurcation (Re ≈ 47).",
               font=F(key, 34), fill=INK)
        y += 56
    img = img.crop((0, 0, 2300, y + 30))
    img.save(OUT / "warp-styles.png", optimize=True)


def charset(key: str) -> None:
    tt = TTFont(font_path(key))
    chars = [chr(u) for u in sorted(tt.getBestCmap()) if unicodedata.category(chr(u))[0] not in "CZ"]
    cols, cw, ch_ = 24, 92, 118
    rows = (len(chars) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw + 80, rows * ch_ + 100), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · {LABEL[key].lower()} · {len(chars)} characters", 26, INK)
    f = F(key, 64)
    for i, c in enumerate(chars):
        r, k = divmod(i, cols)
        x, y = 40 + k * cw, 80 + r * ch_
        d.line([(x, y + 96), (x + cw - 8, y + 96)], fill=RULE)
        w = f.getlength(c)
        d.text((x + (cw - 8 - w) / 2, y + 10), c, font=f, fill=INK, features=["-liga"])
        d.text((x, y + 98), f"{ord(c):04X}", font=F("Regular", 13), fill=MUTED)
    img.save(OUT / f"warp-charset-{key.lower()}.png", optimize=True)


LANG_SAMPLES = [
    ("Polish", "Zażółć gęślą jaźń. Łódź, Gdańsk, Kraków"),
    ("Czech", "Příliš žluťoučký kůň úpěl ďábelské ódy"),
    ("Slovak", "Kŕdeľ ďatľov učí koňa žrať kôru. Ľubovňa"),
    ("Hungarian", "Árvíztűrő tükörfúrógép. Győr, Pécs"),
    ("Romanian", "Șase știuleți și țânțari în Țara Românească"),
    ("Turkish", "Pijamalı hasta yağız şoföre çabucak güvendi. İzmir"),
    ("Croatian", "Đurđevac, Čakovec, Šibenik, Žminj, Ćićarija"),
    ("Latvian", "Glāžšķūņa rūķīši dzērumā ņieka ģīģeli"),
    ("Lithuanian", "Įlinkdama fechtuotojo špaga sublykčiojusi pragręžė apvalų arbūzą"),
    ("Maltese, Esperanto", "Ħ ħ Ġ ġ Ċ ċ Ż ż · Ĉ ĉ Ĝ ĝ Ĥ ĥ Ĵ ĵ Ŝ ŝ Ŭ ŭ"),
    ("Sámi, other", "Ŋ ŋ Ŧ ŧ ĸ ſ Ĳ ĳ Ŀ ŀ ŉ Ő ő Ű ű"),
    ("Greek", "Ταχίστη αλώπηξ βαφής ψημένη γη, δρασκελίζει υπέρ νωθρού κυνός. Ϊ Ϋ ΐ ΰ"),
]


def latin_ext() -> None:
    img = Image.new("RGB", (2300, 4200), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · latin extended-a, ș ț, greek tonos: Central European texts", 26, INK)
    y = 80
    for key in ("Regular", "Italic", "Bold"):
        label(d, (40, y), LABEL[key].lower(), 20)
        y += 34
        for lang, text in LANG_SAMPLES:
            label(d, (40, y + 12), lang.lower(), 16)
            d.text((340, y), text, font=F(key, 46), fill=INK)
            y += 64
        y += 16
    d.line([(40, y), (2260, y)], fill=RULE)
    y += 16
    ext = "".join(chr(c) for c in range(0x100, 0x180)) + "ȘșȚț"
    for key in ("Regular", "Italic"):
        for k in range(0, len(ext), 44):
            d.text((40, y), ext[k:k + 44], font=F(key, 46), fill=INK)
            y += 66
    y += 10
    d.text((40, y), "ą́ ę̄ ĺ ș̆ · ‰ † ‡ ℓ ℎ ℏ ˘ ˛ ˝ ΄ ΅", font=F("Regular", 46), fill=INK)
    img = img.crop((0, 0, 2300, y + 90))
    img.save(OUT / "warp-latin-ext.png", optimize=True)


def italic_caps() -> None:
    img = Image.new("RGB", (2300, 1600), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp {VER} · italic capitals: own cursive forms (0.1 slanted the roman for B D E F H I J K L P R S T U X Y Z and &)", 22, INK)
    y = 80
    for key in ("Italic", "BoldItalic", "DisplayItalic"):
        label(d, (40, y + 30), LABEL[key].lower(), 20)
        d.text((300, y), "ABCDEFGHIJKLM", font=F(key, 92), fill=INK)
        d.text((300, y + 120), "NOPQRSTUVWXYZ &", font=F(key, 92), fill=INK)
        y += 260
    d.line([(40, y), (2260, y)], fill=RULE)
    y += 20
    for key in ("Italic", "BoldItalic"):
        d.text((40, y), "Bessel, Fourier, Hilbert, Jacobi, Kepler, Laplace, Riemann, Stokes, Taylor, Young, Zermelo",
               font=F(key, 44), fill=INK)
        y += 70
    img = img.crop((0, 0, 2300, y + 30))
    img.save(OUT / "warp-italic-caps.png", optimize=True)


BEFORE = ROOT / "warp" / "build" / "before-0.1"


def before_fonts() -> bool:
    """The 0.1 fonts from the last commit on main that has them (for before/after sheets)."""
    import subprocess
    BEFORE.mkdir(parents=True, exist_ok=True)
    ok = True
    for key in STYLE_ORDER:
        nm = f"{Bd.ps_name(Bd.STYLES[key])}.ttf"
        dst = BEFORE / nm
        if dst.exists():
            continue
        res = subprocess.run(["git", "-C", str(ROOT), "show", f"warp-v0.1-fonts:fonts/warp/ttf/{nm}"],
                             capture_output=True)
        if res.returncode != 0:
            res = subprocess.run(["git", "-C", str(ROOT), "show", f"7a8b6b2:fonts/warp/ttf/{nm}"], capture_output=True)
        if res.returncode != 0:
            ok = False
            continue
        dst.write_bytes(res.stdout)
    return ok


def FB(key, size):
    return ImageFont.truetype(str(BEFORE / f"{Bd.ps_name(Bd.STYLES[key])}.ttf"), size=round(size),
                              layout_engine=ImageFont.Layout.RAQM)


def before_after() -> None:
    if not before_fonts():
        print("before/after: the 0.1 fonts are not in git; skipped")
        return
    img = Image.new("RGB", (2300, 2600), PAPER)
    d = ImageDraw.Draw(img)
    label(d, (40, 24), f"warp 0.1 (grey) and {VER} (ink): the forms that changed", 26, INK)
    y = 80
    rows = [("Regular", "g f fi fl ff ffi ffl Ξ Σ", 110), ("Italic", "fi fl BDEFHIJKLPRSTUXYZ &", 96),
            ("Bold", "g f fi fl Ξ Σ", 110), ("Display", "g f fi fl Ξ Σ √", 110)]
    for key, text, size in rows:
        label(d, (40, y + 10), LABEL[key].lower(), 20)
        d.text((300, y), text, font=FB(key, size), fill=(150, 142, 128))
        d.text((300, y + size * 1.25), text, font=F(key, size), fill=INK)
        y += int(size * 2.6)
    d.line([(40, y), (2260, y)], fill=RULE)
    y += 20
    label(d, (40, y), "word space at text size: 270 (0.1) and 310 (0.2), 10 pt at 144 dpi", 20)
    y += 36
    text = ("We study the drawing of a thin viscous thread from a heated preform. When the draw ratio "
            "exceeds a critical value, the steady state loses stability through a Hopf bifurcation.")
    for f, col in ((FB("Regular", 20), (150, 142, 128)), (F("Regular", 20), INK)):
        words, cx, yy = text.split(" "), 40, y
        for w in words:
            wl = f.getlength(w)
            if cx + wl > 1500:
                cx, yy = 40, yy + 30
            d.text((cx, yy), w, font=f, fill=col)
            cx += wl + f.getlength(" ")
        y = yy + 46
    img = img.crop((0, 0, 2300, y + 20))
    img.save(OUT / "warp-before-after.png", optimize=True)


def maths_page() -> None:
    import math_proof
    rc = math_proof.main(["--out", str(OUT / "warp-math.png")])
    if rc:
        raise SystemExit("the LuaLaTeX maths proof failed")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render the Warp proofs.")
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    only = set(filter(None, args.only.split(",")))
    OUT.mkdir(parents=True, exist_ok=True)

    def want(n):
        return not only or n in only

    if want("overlay"):
        report = {}
        for key in STYLE_ORDER:
            overlay(key, report)
            print(f"overlay {key}: mean IoU {report[key]['mean_iou']}, min {report[key]['min_iou']} "
                  f"({report[key]['min_glyph']})")
        (OUT / "sketch-compare.json").write_text(json.dumps(
            {"about": "IoU of the sketch 0.2 engine and the font, per character, at 120 px per em "
                      "(1.0 = the same pixels). See warp/tools/proof.py.", "styles": report},
            ensure_ascii=False, indent=1) + "\n")
    steps = {"paragraph": paragraph, "greek": greek, "equations": equations, "kerning": kerning,
             "accents": accents, "smallcaps": smallcaps_figures, "styles": styles, "latin_ext": latin_ext,
             "italic_caps": italic_caps, "before_after": before_after}
    if want("math"):
        if __import__("shutil").which("lualatex"):
            maths_page()
            print("math: done")
        else:
            print("math: lualatex is not installed; skipped (run tools/math_proof.py where it is)")
    for n, fn in steps.items():
        if want(n):
            fn()
            print(f"{n}: done")
    if want("charset"):
        for key in STYLE_ORDER:
            charset(key)
        print("charset: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
