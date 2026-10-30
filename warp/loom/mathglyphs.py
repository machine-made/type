"""Glyphs for the OpenType MATH table (Warp 0.2).

Every size variant and every assembly part is drawn by the pen at its
own height: the centre-lines are laid out for that height and swept by
the same nib. Nothing is scaled.

* Size variants: four per delimiter or operator (`<name>.size1` to
  `.size4`) for ( ) [ ] { } | ‖ ⟨ ⟩ √ ∫ ∑ ∏.
* Assemblies (`<name>.top`, `.ext`, `.mid`, `.bot`) for ( ) [ ] { } | ‖
  √ ∫. ⟨ ⟩ ∑ ∏ have no assembly: their strokes are diagonal and cannot
  be extended by a straight piece.
* New base glyphs: ‖ ⟨ ⟩.

Parts of one assembly share their horizontal placement (the glyph
function returns {"dx", "adv"}), so that the stems line up when the
shaper stacks them. Straight ends ("connectors") are drawn with the
full-pressure stem, so that overlapping parts join without a seam as
long as they overlap by more than a hairline (MinConnectorOverlap).

This file defines outlines of machine-made Warp: SIL Open Font License
1.1, Reserved Font Name "machine-made" (see ../OFL.txt).
"""

from __future__ import annotations

from loom.engine import GlyphDef
from loom.sketch import AX, G, Rw, brack, paren, rom, rule, vbeak
from loom.extended import brace

# Ink heights of the size variants, centred on the maths axis.
DELIM_SIZES = (1250, 1550, 1950, 2450)
BIGOP_SIZES = (1400, 1750, 2150, 2600)
INTEGRAL_SIZES = (1900, 2350, 2850, 3400)
BASE_DELIM_H = 1020        # ( ) [ ] { } | ‖ ⟨ ⟩: 770 to -250
CONN = 220                 # straight centre-line length at a connecting end
EXT = 500                  # ink height of an extender

MATH_GLYPHS: list[str] = []          # every new unencoded glyph, in order
VARIANTS: dict[str, list[str]] = {}  # base glyph name -> variant names
ASSEMBLY: dict[str, list[tuple]] = {}  # base -> [(part, extender, start_role, end_role)], bottom to top


def _reg(name, fn, **o):
    G[name] = GlyphDef(fn=fn, upright=True, **o)
    MATH_GLYPHS.append(name)


def _w(base_w, H, base_h=BASE_DELIM_H, e=0.45):
    return base_w * (H / base_h) ** e


# ------------------------------------------------------- new base glyphs

def angle(g, x0, w, top, bot, dir):
    """⟨ (dir 1) or ⟩ (dir -1): two pen strokes meeting at the middle."""
    m = (top + bot) / 2
    xr = x0 + w * dir
    # one pressure along each stroke: straight edges
    g.P(xr, top - g.B / 2, 0.55).l(x0, m, 0.55).draw()
    g.P(x0, m, 0.55).l(xr, bot + g.B / 2, 0.55).draw()


def dblbar(g, top, bot, gap=150):
    for x in (0, gap):
        g.P(x, top, 0.3).l(x, bot, 0.3).draw()


@rom("⟨", l=0.9, r=0.7, upright=True)
def _angleleft(g):
    angle(g, 0, 170, 770, -250, 1)


@rom("⟩", l=0.7, r=0.9, upright=True)
def _angleright(g):
    angle(g, 170, 170, 770, -250, -1)


@rom("‖", l=1.0, r=1.0)
def _dblverticalbar(g):
    dblbar(g, 770, -250)


# ---------------------------------------------------------- size variants

def _centre(H):
    return AX + H / 2, AX - H / 2


def radical_at(g, top, bot, bar=40, wide=None):
    """√ at any height. The diagonal gets steeper as the sign grows."""
    B, r = g.B, Rw(g)
    H = top - bot
    mid = bot + H * 0.42 if H <= 1100 else bot + 1010 * 0.42
    xb = 165 + min(H, 1010) * 0.05
    xt = xb + (wide if wide is not None else 262 * (H / 1010) ** 0.45)
    g.P(0, mid - 12, 0).l(62, mid + 30, 0.2).draw({"a": r * 0.9, "b": r * 0.9, "ne": 3})
    g.P(62, mid + 30, 0.9).l(xb, bot + B / 2, 1).draw()
    g.P(xb, bot + B / 2, 0).l(xt, top - r / 2, 0).draw()
    rule(g, xt, top - r / 2, xt + bar, top - r / 2)
    return xt


def integral_at(g, H, slant_dx=None):
    """∫ at any height: the sketch's hooks and drops on a longer stem."""
    bd, A = g.bd, g.A
    d = max(bd, A * 0.9) * 0.92
    t, b = AX + H / 2, AX - H / 2
    k = H / 1360
    sx = 55 * k if slant_dx is None else slant_dx
    xt, xb = 150 + sx, 150
    (g.P(xt + 147, t - 80, 0.25).c(xt + 147, t - 25, xt + 110, t, xt + 75, t, 0.35)
     .c(xt + 27, t, xt + 7, t - 50, xt, t - 160, 1)
     .l(xb, b + 160, 1).c(xb - 7, b + 50, xb - 27, b, xb - 75, b, 0.35)
     .c(xb - 110, b, xb - 147, b + 25, xb - 147, b + 80, 0.25).draw())
    g.ball(xt + 147, t - 80, d); g.ball(xb - 147, b + 80, d)


def summation_at(g, H):
    A, B, S = g.A, g.B, g.S
    top, bot = _centre(H)
    W = 820 * (H / 1040) ** 0.55
    k = (H / 1040) ** 0.5
    t = B * k
    from loom.latin_ext import hbar
    hbar(g, 0, W, top - t / 2, k); vbeak(g, W - S * 0.7, top, top - 160 * k)
    g.P(40, top - t, 1).l(W * 0.524, AX, 1).draw()
    g.P(W * 0.524, AX, 0).l(30, bot + t, 0).draw()
    hbar(g, 0, W + 30, bot + t / 2, k); vbeak(g, W + 30 - S * 0.7, bot, bot + 170 * k)


def product_at(g, H):
    B, h = g.B, g.h
    top, bot = _centre(H)
    W = 580 * (H / 1040) ** 0.55
    x0, x1 = 60, 60 + W
    k = (H / 1040) ** 0.5
    g.stem(x0, bot, top); g.stem(x1, bot, top)
    from loom.latin_ext import hbar
    hbar(g, x0 - h - 40, x1 + h + 40, top - B * k / 2, k)
    g.serif(x0, bot, 1, "b"); g.serif(x1, bot, 1, "b")


def _variant_fns():
    out = {}
    for i, H in enumerate(DELIM_SIZES, 1):
        top, bot = _centre(H)
        wp, wb, wa = _w(150, H), _w(170, H), _w(170, H)
        arm = _w(130, H, e=0.3)
        out[f"parenleft.size{i}"] = (lambda g, t=top, b=bot, w=wp: paren(g, 0, w, t, b, 1), 0.9, 0.6)
        out[f"parenright.size{i}"] = (lambda g, t=top, b=bot, w=wp: paren(g, w, w, t, b, -1), 0.6, 0.9)
        out[f"bracketleft.size{i}"] = (lambda g, t=top, b=bot, a=arm: _brack(g, 0, t, b, 1, a), 0.9, 0.6)
        out[f"bracketright.size{i}"] = (lambda g, t=top, b=bot, a=arm: _brack(g, a, t, b, -1, a), 0.6, 0.9)
        out[f"braceleft.size{i}"] = (lambda g, t=top, b=bot, w=wb: brace(g, 0, w, t, b, 1), 0.9, 0.6)
        out[f"braceright.size{i}"] = (lambda g, t=top, b=bot, w=wb: brace(g, w, w, t, b, -1), 0.6, 0.9)
        out[f"bar.size{i}"] = (lambda g, t=top, b=bot: g.P(0, t, 0.3).l(0, b, 0.3).draw(), 1.0, 1.0)
        out[f"uni2016.size{i}"] = (lambda g, t=top, b=bot: dblbar(g, t, b), 1.0, 1.0)
        out[f"uni27E8.size{i}"] = (lambda g, t=top, b=bot, w=wa: angle(g, 0, w, t, b, 1), 0.9, 0.7)
        out[f"uni27E9.size{i}"] = (lambda g, t=top, b=bot, w=wa: angle(g, w, w, t, b, -1), 0.7, 0.9)
        out[f"radical.size{i}"] = (lambda g, t=top - 10, b=bot + 10: radical_at(g, t, b), 0.5, 0.0)
    for i, H in enumerate(BIGOP_SIZES, 1):
        out[f"summation.size{i}"] = (lambda g, H=H: summation_at(g, H), 0.6, 0.6)
        out[f"product.size{i}"] = (lambda g, H=H: product_at(g, H), 0.6, 0.6)
    for i, H in enumerate(INTEGRAL_SIZES, 1):
        out[f"integral.size{i}"] = (lambda g, H=H: integral_at(g, H), 0.6, 0.6)
    return out


def _brack(g, x, top, bot, dir, arm):
    B = g.B
    g.stem(x, bot, top, 1)
    g.bar(x - dir * g.h, x + dir * arm, top - B / 2)
    g.bar(x - dir * g.h, x + dir * arm, bot + B / 2)


# The base glyph of each family (glyph names).
BASES = ("parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright", "bar",
         "uni2016", "uni27E8", "uni27E9", "radical", "summation", "product", "integral")

for _name, (_fn, _l, _r) in _variant_fns().items():
    slanted = _name.startswith("integral")
    if slanted:
        G[_name] = GlyphDef(fn=_fn, l=_l, r=_r, slant=0.2, yc=AX)
        MATH_GLYPHS.append(_name)
    else:
        _reg(_name, _fn, l=_l, r=_r)
    VARIANTS.setdefault(_name.split(".")[0], []).append(_name)


# ---------------------------------------------------------------- parts
#
# Each part function draws at fixed design coordinates and returns the
# placement {"dx", "adv"} shared by all parts of its assembly. The
# vertical layout: bottom parts end at the top in a connector, top parts
# start at the bottom in a connector; the extender is all connector.

def _place(g, xmin, xmax, l=0.9, r=0.6):
    """dx and advance for ink from xmin to xmax (design units, unslanted)."""
    sb = g.p.sb
    dx = sb * l - xmin * g.p.wd
    return {"dx": dx, "adv": dx + xmax * g.p.wd + sb * r}


def paren_parts(dir):
    w = _w(150, 2000)
    hk = 620
    x0 = 0 if dir > 0 else w
    xr = x0 + w * dir

    def ext_x(g):
        a = g.A
        lo, hi = (x0 - a / 2, xr + g.B / 2) if dir > 0 else (xr - g.B / 2, x0 + a / 2)
        return _place(g, lo, hi, *((0.9, 0.6) if dir > 0 else (0.6, 0.9)))

    def top(g):
        t = 1000
        (g.P(xr, t - g.B / 2, 0).c(xr - dir * w * 0.82, t - hk * 0.42, x0, t - hk * 0.55, x0, t - hk, 1)
         .l(x0, t - hk - CONN, 1).draw())
        return ext_x(g)

    def bot(g):
        b = -500
        (g.P(x0, b + hk + CONN, 1).l(x0, b + hk, 1).c(x0, b + hk * 0.55, xr - dir * w * 0.82, b + hk * 0.42, xr, b + g.B / 2, 0)
         .draw())
        return ext_x(g)

    def ext(g):
        g.stem(x0, 0, EXT, 1)
        return ext_x(g)

    return top, ext, bot


def brack_parts(dir):
    arm = _w(130, 2000, e=0.3)
    x = 0 if dir > 0 else arm

    def place(g):
        lo, hi = (x - g.A / 2, x + arm) if dir > 0 else (x - arm, x + g.A / 2)
        return _place(g, lo, hi, *((0.9, 0.6) if dir > 0 else (0.6, 0.9)))

    def top(g):
        t = 1000
        g.stem(x, t - CONN - g.B / 2 - 200, t, 1)
        g.bar(x - dir * g.h, x + dir * arm, t - g.B / 2)
        return place(g)

    def bot(g):
        b = -500
        g.stem(x, b, b + 200 + CONN + g.B / 2, 1)
        g.bar(x - dir * g.h, x + dir * arm, b + g.B / 2)
        return place(g)

    def ext(g):
        g.stem(x, 0, EXT, 1)
        return place(g)

    return top, ext, bot


def brace_parts(dir):
    w = _w(170, 2000)
    x0 = 0 if dir > 0 else w
    xr, xs = x0 + w * dir, x0 + w * 0.45 * dir
    pr = 0.55

    def place(g):
        lo, hi = (x0 - 10, xr + g.B / 2) if dir > 0 else (xr - g.B / 2, x0 + 10)
        return _place(g, lo, hi, *((0.9, 0.6) if dir > 0 else (0.6, 0.9)))

    def top(g):
        t = 1000
        (g.P(xr, t - g.B / 2, 0).c(xs + w * 0.2 * dir, t - 8, xs, t - 50, xs, t - 140, pr)
         .l(xs, t - 140 - CONN, pr).draw())
        return place(g)

    def bot(g):
        b = -500
        (g.P(xs, b + 140 + CONN, pr).l(xs, b + 140, pr).c(xs, b + 50, xs + w * 0.2 * dir, b + 8, xr, b + g.B / 2, 0)
         .draw())
        return place(g)

    def mid(g):
        m = AX
        (g.P(xs, m + 110 + CONN, pr).l(xs, m + 110, pr).c(xs, m + 40, x0 + w * 0.2 * dir, m + 6, x0, m, 0.1).draw())
        (g.P(x0, m, 0.1).c(x0 + w * 0.2 * dir, m - 6, xs, m - 40, xs, m - 110, pr).l(xs, m - 110 - CONN, pr).draw())
        return place(g)

    def ext(g):
        g.P(xs, 0, pr).l(xs, EXT, pr).draw()
        return place(g)

    return top, ext, bot, mid


def bar_parts(n):
    gap = 150

    def place(g):
        a = g.B + (g.A - g.B) * 0.3
        return _place(g, -a / 2, (gap if n == 2 else 0) + a / 2, 1.0, 1.0)

    def ext(g):
        for k in range(n):
            g.P(k * gap, 0, 0.3).l(k * gap, EXT, 0.3).draw()
        return place(g)

    return ext


RAD_V = 0.25   # pressure of the upright of a stacked √: a little more than a hairline


def radical_parts():
    xt = 165 + 50.5 + 262 * (2000 / 1010) ** 0.45
    bar = 40

    def place(g):
        return _place(g, -g.A * 0.4, xt + bar + Rw(g) / 2, 0.5, 0.0)

    def bot(g):
        """The tick, the heavy down stroke and the hairline, which turns upright."""
        B, r = g.B, Rw(g)
        b = -500
        mid = b + 1010 * 0.42
        xb = 165 + 1010 * 0.05
        g.P(0, mid - 12, 0).l(62, mid + 30, 0.2).draw({"a": r * 0.9, "b": r * 0.9, "ne": 3})
        g.P(62, mid + 30, 0.9).l(xb, b + B / 2, 1).draw()
        yv = b + 1010 * 0.95
        g.P(xb, b + B / 2, 0).l(xt, yv, RAD_V).l(xt, yv + CONN, RAD_V).draw()
        return place(g)

    def ext(g):
        g.P(xt, g.B / 2, RAD_V).l(xt, EXT - g.B / 2, RAD_V).draw()
        return place(g)

    def top(g):
        r = Rw(g)
        t = 1000
        g.P(xt, t - r / 2 - CONN - 200, RAD_V).l(xt, t - r / 2, RAD_V).draw()
        rule(g, xt, t - r / 2, xt + bar, t - r / 2)
        return place(g)

    return top, ext, bot


def integral_parts():
    def place(g):
        return _place(g, -147 - g.bd, 147 + g.bd, 0.6, 0.6)

    def top(g):
        bd, A = g.bd, g.A
        d = max(bd, A * 0.9) * 0.92
        t = 1000
        (g.P(147, t - 80, 0.25).c(147, t - 25, 110, t, 75, t, 0.35).c(27, t, 7, t - 50, 0, t - 160, 1)
         .l(0, t - 160 - CONN, 1).draw())
        g.ball(147, t - 80, d)
        return place(g)

    def bot(g):
        bd, A = g.bd, g.A
        d = max(bd, A * 0.9) * 0.92
        b = -500
        (g.P(0, b + 160 + CONN, 1).l(0, b + 160, 1).c(-7, b + 50, -27, b, -75, b, 0.35)
         .c(-110, b, -147, b + 25, -147, b + 80, 0.25).draw())
        g.ball(-147, b + 80, d)
        return place(g)

    def ext(g):
        g.stem(0, 0, EXT, 1)
        return place(g)

    return top, ext, bot


def _parts():
    for base, d in (("parenleft", 1), ("parenright", -1)):
        top, ext, bot = paren_parts(d)
        yield base, [("bot", bot, False), ("ext", ext, True), ("top", top, False)]
    for base, d in (("bracketleft", 1), ("bracketright", -1)):
        top, ext, bot = brack_parts(d)
        yield base, [("bot", bot, False), ("ext", ext, True), ("top", top, False)]
    for base, d in (("braceleft", 1), ("braceright", -1)):
        top, ext, bot, mid = brace_parts(d)
        yield base, [("bot", bot, False), ("ext", ext, True), ("mid", mid, False), ("ext", ext, True),
                     ("top", top, False)]
    yield "bar", [("ext", bar_parts(1), False), ("ext", bar_parts(1), True)]
    yield "uni2016", [("ext", bar_parts(2), False), ("ext", bar_parts(2), True)]
    top, ext, bot = radical_parts()
    yield "radical", [("bot", bot, False), ("ext", ext, True), ("top", top, False)]
    top, ext, bot = integral_parts()
    yield "integral", [("bot", bot, False), ("ext", ext, True), ("top", top, False)]


for _base, _list in _parts():
    seq = []
    for role, fn, extender in _list:
        name = f"{_base}.{role}"
        if name not in G:
            _reg(name, fn)
        seq.append((name, extender, role))
    ASSEMBLY[_base] = seq


def connectors(role: str, B: float, height: float) -> tuple[float, float]:
    """(start, end) connector lengths of a part: start is its bottom end, end its top end."""
    c = CONN + B / 2
    if role == "ext":
        return height, height
    if role == "bot":
        return 0.0, c
    if role == "top":
        return c, 0.0
    if role == "mid":
        return c, c
    raise ValueError(role)
