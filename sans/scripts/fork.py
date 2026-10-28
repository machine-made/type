"""Make the machine-made Sans sources from the upstream Plus Jakarta Sans sources.

Usage:
    python sans/scripts/fork.py UPSTREAM_SOURCES_DIR OUT_DIR [--skip-forms]

UPSTREAM_SOURCES_DIR holds PlusJakartaSans.glyphs and
PlusJakartaSans-Italic.glyphs from the pinned upstream commit (see
sans/upstream/UPSTREAM.txt). OUT_DIR receives MachineMadeSans.glyphs and
MachineMadeSans-Italic.glyphs. The result is deterministic: CI runs this
script again and compares the output with the committed sources.

Steps:
1. Names: family name, copyright, designer, description, vendor, version.
2. Line metrics: typo and hhea 906/-281/0, for one line with Weft.
3. Default forms (not with --skip-forms): the Lurus (straight)
   alternate becomes the default glyph (a, j, r, y, p, q and their
   accented forms). The old default stays in the font as X.ss01. All
   Lancip (sharp) alternates go to X.ss02 (ss02). Glyphs with only a
   Lancip alternate keep the upstream default form.

The script does not change outlines. It renames glyphs, moves glyph data
between names, and changes advance widths, anchors and component offsets
only where a composite glyph now refers to a glyph with other metrics.
"""

from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extend  # noqa: E402
import glyphsfmt  # noqa: E402

FAMILY = "machine-made Sans"
PS_FAMILY = "MachineMadeSans"
VERSION = (0, 200)
UPSTREAM_COPYRIGHT = (
    "Copyright 2020 The Plus Jakarta Sans Project Authors "
    "(https://github.com/tokotype/PlusJakartaSans)"
)
FORK_COPYRIGHT = (
    "Copyright 2026 The machine-made Sans Project Authors "
    "(https://github.com/machine-made/type)"
)
DESIGNER = "Gumpita Rahayu (Tokotype); modified by machine-made"
DESCRIPTION = (
    "machine-made Sans is a modified version of Plus Jakarta Sans. "
    "Based on Plus Jakarta Sans by Gumpita Rahayu, Tokotype."
)
LICENSE = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
VENDOR = "NONE"

# Line metrics. Weft 0.1 uses 1000 UPM and typo/hhea 906/-281/0. The win
# values stay as upstream: they must cover the tallest and deepest glyph
# (yMax 1294, yMin -263 in ExtraBold) to prevent clipping on Windows.
METRICS = {
    "typoAscender": 906,
    "typoDescender": -281,
    "typoLineGap": 0,
    "hheaAscender": 906,
    "hheaDescender": -281,
    "hheaLineGap": 0,
    "winAscent": 1296,
    "winDescent": 356,
}

SET_LABELS = {
    "ss01": "Round forms (original defaults)",
    "ss02": "Lancip: sharp forms",
    "ss03": "Lingkar: swirl",
}

# Ligature glyphs that keep the round forms. f, i and l keep the upstream
# round default, so liga makes them from default text, as upstream.
KEEP_ROUND = {"f_f", "f_f_i", "f_f_l", "fi", "fl"}

SOURCES = {
    "PlusJakartaSans.glyphs": "MachineMadeSans.glyphs",
    "PlusJakartaSans-Italic.glyphs": "MachineMadeSans-Italic.glyphs",
}

UPRIGHT, ITALIC = SOURCES

SUB_RE = re.compile(r"sub (\S+) by (\S+);")
TOKEN_RE = re.compile(r"[A-Za-z0-9_.@]+")


class ForkError(Exception):
    pass


# --------------------------------------------------------------------------
# Step 1 and 2: names and metrics
# --------------------------------------------------------------------------


def _property(key: str, value: str, multi: bool) -> dict:
    if multi:
        return {"key": key, "values": [{"language": "dflt", "value": value}]}
    return {"key": key, "value": value}


def set_names(font: dict, italic: bool) -> None:
    font["familyName"] = FAMILY
    font["versionMajor"], font["versionMinor"] = VERSION
    copyright_text = f"{UPSTREAM_COPYRIGHT}. {FORK_COPYRIGHT}."
    wanted = [
        ("copyrights", copyright_text, True),
        ("designers", DESIGNER, True),
        ("designerURL", "https://www.tokotype.com", False),
        ("manufacturers", "machine-made", True),
        ("manufacturerURL", "https://github.com/machine-made", False),
        ("descriptions", DESCRIPTION, True),
        ("licenses", LICENSE, True),
        ("licenseURL", LICENSE_URL, False),
        ("vendorID", VENDOR, False),
    ]
    old = {p["key"]: i for i, p in enumerate(font.get("properties", []))}
    props = font.setdefault("properties", [])
    for key, value, multi in wanted:
        prop = _property(key, value, multi)
        if key in old:
            props[old[key]] = prop
        else:
            props.append(prop)
    if italic:
        # Remove the upstream "Generated with" note. It is not a credit.
        font.pop("note", None)


def set_metrics(font: dict) -> None:
    for master in font["fontMaster"]:
        params = master.setdefault("customParameters", [])
        index = {p["name"]: i for i, p in enumerate(params)}
        for name, value in METRICS.items():
            if name in index:
                params[index[name]]["value"] = value
            else:
                params.append({"name": name, "value": value})


def set_instances(font: dict) -> None:
    kept = []
    seen = set()
    for inst in font["instances"]:
        if inst.get("type") == "variable":
            kept.append(inst)
            continue
        name = inst["name"]
        if name in seen:
            # Upstream has a second, unused "Regular" instance at wght 200
            # in the upright source. It would make a second Regular file.
            continue
        seen.add(name)
        if name == "Bold" and not inst.get("isBold"):
            # Upstream does not mark the upright Bold as bold. Then
            # fsSelection and macStyle do not show Bold, and Bold is not
            # style-linked to Regular. The italic source does it already.
            inst["isBold"] = 1
            inst["linkStyle"] = "Regular"
        style = name.replace(" ", "")
        params = inst.setdefault("customParameters", [])
        params[:] = [p for p in params if p["name"] != "fileName"]
        params.append({"name": "fileName", "value": f"{PS_FAMILY}-{style}"})
        props = inst.setdefault("properties", [])
        props[:] = [p for p in props if p.get("key") != "postscriptFontName"]
        props.append({"key": "postscriptFontName", "value": f"{PS_FAMILY}-{style}"})
        ordered = {k: inst[k] for k in sorted(inst)}
        inst.clear()
        inst.update(ordered)
        kept.append(inst)
    font["instances"] = kept


# --------------------------------------------------------------------------
# Step 3: default forms
# --------------------------------------------------------------------------


def feature(font: dict, tag: str) -> dict:
    for f in font["features"]:
        if f["tag"] == tag:
            return f
    raise ForkError(f"Feature {tag} is missing.")


def plan_forms(font: dict):
    """Return (slots, rename, chosen).

    slots: slot names in feature order.
    rename: old glyph name -> new glyph name (a permutation, except for
    the names that are only in one set).
    chosen: slot -> "Lurus" (the straight form is the new default) or
    "Round" (the upstream default stays; the sharp form is X.ss02).
    """
    s1 = dict(SUB_RE.findall(feature(font, "ss01")["code"]))
    s2 = dict(SUB_RE.findall(feature(font, "ss02")["code"]))
    slots = list(s1) + [x for x in s2 if x not in s1]
    names = {g["glyphname"] for g in font["glyphs"]}
    rename, chosen = {}, {}
    for x in slots:
        alt1, alt2 = s1.get(x), s2.get(x)
        for alt in (alt1, alt2):
            if alt is not None and alt not in names:
                raise ForkError(f"Glyph {alt} is in a feature but not in the font.")
        if alt1 is not None and alt1 != f"{x}.ss01":
            raise ForkError(f"Unexpected ss01 name {alt1} for {x}.")
        if alt2 is not None and alt2 != f"{x}.ss02":
            raise ForkError(f"Unexpected ss02 name {alt2} for {x}.")
        if alt2 is not None:
            chosen[x] = "Lurus"
            rename[alt2] = x
            rename[x] = f"{x}.ss01"
            if alt1 is not None:
                rename[alt1] = f"{x}.ss02"
        else:
            # Only a Lancip alternate: keep the default, move the sharp
            # form from X.ss01 to X.ss02.
            chosen[x] = "Round"
            if f"{x}.ss02" in names:
                raise ForkError(f"{x}.ss02 exists already.")
            rename[alt1] = f"{x}.ss02"
    return slots, rename, chosen


def master_ids(font: dict) -> list[str]:
    return [m["id"] for m in font["fontMaster"]]


def layer_by_id(glyph: dict, layer_id: str) -> dict | None:
    for layer in glyph["layers"]:
        if layer["layerId"] == layer_id:
            return layer
    return None


def anchors(layer: dict) -> dict:
    out = {}
    for a in layer.get("anchors", []):
        pos = a.get("pos", a.get("position"))
        if isinstance(pos, str):  # "{292, 0}"
            x, y = (float(v) for v in pos.strip("{}").split(","))
        elif pos is None:
            x, y = 0, 0
        else:
            x, y = (list(pos) + [0, 0])[:2]
        out[a["name"]] = (x, y)
    return out


def _num(v: float):
    return int(v) if float(v).is_integer() else v


def move_anchor(a: dict, dx: float, dy: float) -> None:
    if "position" in a:
        x, y = (float(v) for v in a["position"].strip("{}").split(","))
        a["position"] = "{%s, %s}" % (_num(x + dx), _num(y + dy))
    else:
        x, y = (list(a.get("pos", [])) + [0, 0])[:2]
        nx, ny = _num(x + dx), _num(y + dy)
        if nx == 0 and ny == 0:
            a.pop("pos", None)
        else:
            a["pos"] = [nx, ny]


def components(layer: dict) -> list[dict]:
    return [s for s in layer.get("shapes", []) if "ref" in s]


def has_paths(layer: dict) -> bool:
    return any("ref" not in s for s in layer.get("shapes", []))


def apply_forms(font: dict, report: list) -> None:
    slots, rename, chosen = plan_forms(font)
    slot_set = set(slots)
    alt_names = {n for n in rename if n not in slot_set}
    old = {g["glyphname"]: g for g in font["glyphs"]}
    inverse = {new: o for o, new in rename.items()}
    masters = master_ids(font)

    def origin(name: str) -> str:
        return inverse.get(name, name)

    # Names that go away and names that are new: an alternate that was
    # only in ss02 (p.ss02) becomes the default and the old default takes
    # the name p.ss01; a sharp form that was only in ss01 (f.ss01) takes
    # the name f.ss02. The new name takes the place of the old name.
    removed = {n for n in rename if n not in inverse}
    added = {n for n in inverse if n not in old}
    place = {}
    for n in removed:
        base = n.rsplit(".", 1)[0]
        targets = [a for a in added if a.rsplit(".", 1)[0] == base]
        if len(targets) != 1:
            raise ForkError(f"No new name for the place of {n}.")
        place[n] = targets[0]
    if set(place.values()) != added:
        raise ForkError("Added and removed glyph names do not match.")

    # 1. Build the new glyphs. Unicode values stay with the name.
    new = {}
    for name in [n for n in old if n not in removed] + sorted(added):
        src_name = origin(name)
        g = copy.deepcopy(old[src_name])
        g["glyphname"] = name
        unicode_value = old[name].get("unicode") if name in old else None
        g.pop("unicode", None)
        if unicode_value is not None:
            g["unicode"] = unicode_value
        # Keep the key order of Glyphs: glyphname, then sorted keys.
        new[name] = {"glyphname": name, **{k: g[k] for k in sorted(g) if k != "glyphname"}}

    # 2. Component references.
    def new_ref(owner_origin: str, owner_new: str, ref: str) -> str:
        if owner_new in KEEP_ROUND:
            return rename.get(ref, ref)
        if owner_origin in slot_set:
            # Old default glyph data: all its parts are the old forms.
            return rename.get(ref, ref)
        if owner_origin in alt_names:
            # Alternate glyph data: a plain slot name meant "the default".
            # It means the new default now.
            return ref if ref in slot_set else rename.get(ref, ref)
        # Other glyphs follow the new defaults.
        return ref

    for name, g in new.items():
        src = origin(name)
        for layer in g["layers"]:
            for comp in components(layer):
                comp["ref"] = new_ref(src, name, comp["ref"])

    # 3. Metrics keys (Glyphs.app spacing links). Rename them with the
    # glyph data so that "update metrics" in Glyphs.app gives no change.
    for g in new.values():
        for key in ("leftMetricsKey", "rightMetricsKey", "widthMetricsKey"):
            if key in g:
                m = re.match(r"^(=?\|?)([A-Za-z0-9_.]+)(.*)$", str(g[key]))
                if m and m.group(2) in rename:
                    g[key] = m.group(1) + rename[m.group(2)] + m.group(3)

    # 4. Fix the metrics of composites whose parts changed.
    #    shape_changed[name] is True when the outline of the new glyph is
    #    not the outline of its origin glyph upstream.
    order = topo_order(new)
    shape_changed: dict[str, bool] = {}
    for name in order:
        g = new[name]
        src = old[origin(name)]
        changed = False
        for mid in masters:
            nl, ol = layer_by_id(g, mid), layer_by_id(src, mid)
            if nl is None or ol is None:
                continue
            pairs = []
            for nc, oc in zip(components(nl), components(ol)):
                same = origin(nc["ref"]) == oc["ref"] and not shape_changed.get(nc["ref"], False)
                pairs.append((nc, oc, same))
            if all(p[2] for p in pairs):
                continue
            changed = True
            fix_layer(name, mid, nl, ol, pairs, new, old, report)
        shape_changed[name] = changed

    # 5. Glyph list in the original order of names. A name that went
    #    away (p.ss02, f.ss01) is replaced by its new name (p.ss01, f.ss02).
    out = [new[place.get(g["glyphname"], g["glyphname"])] for g in font["glyphs"]]
    names_out = [g["glyphname"] for g in out]
    if len(set(names_out)) != len(names_out) or set(names_out) != set(new):
        raise ForkError("Glyph list after the swap is not complete.")
    font["glyphs"] = out

    # 6. glyphOrder parameter: replace the names that do not exist now.
    for p in font.get("customParameters", []):
        if p["name"] == "glyphOrder":
            p["value"] = [place.get(n, n) for n in p["value"]]

    # 7. Features and classes.
    rewrite_features(font, slots, rename, chosen, new)

    for x in slots:
        report.append(("form", x, chosen[x], f"{x}.ss01" if chosen[x] == "Lurus" else f"{x}.ss02"))


def topo_order(glyphs: dict) -> list[str]:
    seen, out = set(), []

    def visit(n: str, stack: tuple = ()):
        if n in seen:
            return
        if n in stack:
            raise ForkError(f"Component loop at {n}.")
        for layer in glyphs[n]["layers"]:
            for c in components(layer):
                if c["ref"] in glyphs:
                    visit(c["ref"], stack + (n,))
        seen.add(n)
        out.append(n)

    for n in glyphs:
        visit(n)
    return out


def fix_layer(name, mid, nl, ol, pairs, new, old, report) -> None:
    """Change width, anchors and offsets of one master layer of a composite."""

    def part(glyphs, ref):
        layer = layer_by_id(glyphs[ref], mid)
        if layer is None:
            raise ForkError(f"{ref} has no layer {mid}.")
        return layer

    comps = [p[0] for p in pairs]
    if has_paths(nl):
        raise ForkError(f"{name}: a composite with outlines has a changed part. Fix it by hand.")

    old_parts = [part(old, oc["ref"]) for _, oc, _ in pairs]
    new_parts = [part(new, nc["ref"]) for nc, _, _ in pairs]
    old_w = [p["width"] for p in old_parts]
    new_w = [p["width"] for p in new_parts]
    pos = [list(c.get("pos", [0, 0])) for c in comps]

    # Alias: one part at the origin with the same width.
    if len(comps) == 1 and pos[0] == [0, 0] and ol["width"] == old_w[0]:
        nl["width"] = new_w[0]
        delta_anchors(nl, anchors(old_parts[0]), anchors(new_parts[0]), report, name)
        report.append(("alias", name, mid, comps[0]["ref"]))
        return

    # Sequence: parts side by side (ij, IJ, Lj, Nj, lj, nj).
    cum = [sum(old_w[:i]) for i in range(len(comps))]
    if all(p[0] == c for p, c in zip(pos, cum)) and ol["width"] == sum(old_w):
        x = 0
        for c, w, p in zip(comps, new_w, pos):
            set_pos(c, x, p[1])
            x += w
        nl["width"] = x
        report.append(("sequence", name, mid, "+".join(c["ref"] for c in comps)))
        return

    # Base and marks: the first part changed, the other parts are marks.
    if not pairs[0][2] and all(p[2] for p in pairs[1:]):
        oa, na = anchors(old_parts[0]), anchors(new_parts[0])
        dw = new_w[0] - old_w[0]
        if ol["width"] == old_w[0]:
            nl["width"] = ol["width"] + dw
        for (c, _, _), mark_layer, p in zip(pairs[1:], old_parts[1:], pos[1:]):
            attach = [a[1:] for a in anchors(mark_layer) if a.startswith("_")]
            key = next((a for a in attach if a in oa and a in na), None)
            if key is not None:
                dx, dy = na[key][0] - oa[key][0], na[key][1] - oa[key][1]
            else:
                dx, dy = round(dw / 2), 0
            set_pos(c, p[0] + dx, p[1] + dy)
        delta_anchors(nl, oa, na, report, name)
        report.append(("marks", name, mid, comps[0]["ref"]))
        return

    raise ForkError(f"{name}: no rule fits the changed composite in layer {mid}. Fix it by hand.")


def set_pos(comp: dict, x, y) -> None:
    x, y = _num(x), _num(y)
    if x == 0 and y == 0:
        comp.pop("pos", None)
    else:
        # Keep "pos" before "ref" in the key order of Glyphs.
        items = {k: v for k, v in comp.items() if k != "pos"}
        comp.clear()
        for k in sorted(list(items) + ["pos"]):
            comp[k] = [x, y] if k == "pos" else items[k]


def delta_anchors(layer: dict, old_a: dict, new_a: dict, report, name) -> None:
    """Move each anchor of LAYER as the same anchor of its base moved."""
    for a in layer.get("anchors", []):
        n = a["name"]
        if n in old_a and n in new_a:
            dx, dy = new_a[n][0] - old_a[n][0], new_a[n][1] - old_a[n][1]
            if dx or dy:
                move_anchor(a, dx, dy)


def rewrite_features(font, slots, rename, chosen, glyphs) -> None:
    names = set(glyphs)
    lurus = [x for x in slots if chosen[x] == "Lurus"]

    # ss01: the upstream default of each glyph whose default is now Lurus.
    ss01 = "\n".join(f"sub {x} by {x}.ss01;" for x in lurus)
    # ss02: every sharp form. For a Lurus glyph, also from the round form.
    rules2 = []
    for x in slots:
        if f"{x}.ss02" not in names:
            continue
        if chosen[x] == "Lurus":
            rules2.append(f"sub [{x} {x}.ss01] by {x}.ss02;")
        else:
            rules2.append(f"sub {x} by {x}.ss02;")
    ss02 = "\n".join(rules2)
    f3 = feature(font, "ss03")
    rules = []
    for x, y in SUB_RE.findall(f3["code"]):
        inputs = [x] + [n for n in (f"{x}.ss01", f"{x}.ss02") if n in names]
        rules.append(f"sub [{' '.join(inputs)}] by {y};" if len(inputs) > 1 else f"sub {x} by {y};")
    ss03 = "\n".join(rules)

    multiline = glyphsfmt.LITERAL_BREAKS
    for tag, code in (("ss01", ss01), ("ss02", ss02), ("ss03", ss03)):
        f = feature(font, tag)
        f["code"] = code + ("\n" if multiline else "")
        f["labels"] = [{"language": "dflt", "value": SET_LABELS[tag]}]
        for k in list(f):
            if k not in ("automatic", "code", "labels", "tag", "disabled"):
                f.pop(k)
        # Glyphs.app must not write these features again from the glyph names.
        f.pop("automatic", None)
        ordered = {k: f[k] for k in sorted(f)}
        f.clear()
        f.update(ordered)

    # liga: the upstream rules on the default f, i and l (round forms).
    # Put liga after the sets: with ss02 on, f, i and l are sharp and no
    # round ligature replaces them.
    liga = feature(font, "liga")
    liga["code"] = TOKEN_RE.sub(lambda m: rename.get(m.group(0), m.group(0)), liga["code"])
    liga.pop("automatic", None)
    feats = font["features"]
    feats.remove(liga)
    feats.insert(feats.index(feature(font, "ss03")) + 1, liga)

    # Classes and class prefixes: rename the glyph names.
    def ren(text: str) -> str:
        return TOKEN_RE.sub(lambda m: rename.get(m.group(0), m.group(0)), text)

    for c in font.get("classes", []):
        c["code"] = ren(c["code"])
    for p in font.get("featurePrefixes", []):
        p["code"] = ren(p["code"])


def fix_ss04(font: dict) -> None:
    """Repair the upstream ss04 (Bulgarian Cyrillic) feature code.

    Upstream (commit 18d1cd2) writes the feature name as \\"...\\" with
    backslashes. feaLib does not accept that, so the upstream source does
    not build. Put the name in the feature label and keep the two lookup
    references.
    """
    for f in font["features"]:
        if f["tag"] != "ss04":
            continue
        name = re.search(r'name 3 1 0x409 \\?"([^"\\]*)\\?";', f["code"])
        label = name.group(1) if name else "Bulgarian Cyrillic"
        lines = [
            "script latn;",
            "lookup locl_BGR;",
            "script cyrl;",
            "lookup locl_BGR;",
        ]
        f["code"] = "\n".join(lines)
        f["labels"] = [{"language": "dflt", "value": label}]
        ordered = {k: f[k] for k in sorted(f)}
        f.clear()
        f.update(ordered)


def fix_noexport(font: dict) -> None:
    """Remove the unused @noexport class from the upstream class prefix.

    The class lists glyphs that are not exported. No rule uses it, and
    feaLib stops on a class with glyphs that are not in the font.
    """
    for p in font.get("featurePrefixes", []):
        p["code"] = re.sub(r"^@noexport = \[[^\]]*\];\n?", "", p["code"], flags=re.M)


def fix_zero_scale(font: dict) -> list:
    """Remove "scale = (0,0)" from rotated components.

    Upstream upDownArrow (U+2195) rotates leftRightArrow by -90 degrees
    and writes scale = (0,0). Glyphs.app ignores that value, but
    glyphsLib applies it, and the glyph becomes empty in the static
    fonts. Without the key, the scale is 1.
    """
    fixed = []
    for g in font["glyphs"]:
        for layer in g["layers"]:
            for comp in components(layer):
                if comp.get("scale") == [0, 0]:
                    del comp["scale"]
                    fixed.append(g["glyphname"])
    return sorted(set(fixed))


# --------------------------------------------------------------------------


def copy_stems(upright: dict, italic: dict) -> None:
    """Give the upright source the stem values of the italic source.

    Upstream defines stems (for PostScript hinting) only in the italic
    source. The italic is the upright slanted by a horizontal shear,
    which keeps horizontal distances, so the stem widths are the same.
    The OTF autohinter (otfautohint) needs them in the CFF Private dict.
    """
    if "stems" in upright or "stems" not in italic:
        return
    stems = copy.deepcopy(italic["stems"])
    by_weight = {tuple(m["axesValues"]): m for m in italic["fontMaster"]}
    for m in upright["fontMaster"]:
        src = by_weight.get(tuple(m["axesValues"]))
        if src is None or "stemValues" not in src:
            raise ForkError(f"No italic stem values for the master at {m['axesValues']}.")
        m["stemValues"] = list(src["stemValues"])
    # Glyphs writes "stems" just before "unitsPerEm".
    items = list(upright.items())
    upright.clear()
    for k, v in items:
        if k == "unitsPerEm":
            upright["stems"] = stems
        if k != "stems":
            upright[k] = v


def fork_font(src: Path, skip_forms: bool) -> tuple[dict, str, list]:
    text = src.read_text(encoding="utf-8")
    font = glyphsfmt.loads(text)
    italic = "Italic" in src.name
    report: list = []
    set_names(font, italic)
    set_metrics(font)
    set_instances(font)
    fix_ss04(font)
    fix_noexport(font)
    for name in fix_zero_scale(font):
        report.append(("scale", name, "removed scale (0,0)", ""))
    if not skip_forms:
        apply_forms(font, report)
    return font, text, report


# --------------------------------------------------------------------------
# Kerning (0.2)
# --------------------------------------------------------------------------

# Kerning exceptions found with scripts/kernaudit.py (see sans/STATUS.md).
# Each pair touched or overlapped in at least one master. The value is
# the kerning in each master (wght 200, 400, 800) that leaves at least
# 20 units between the inks; in the other masters it keeps the old
# value. A left key "@MMK_L_x" is the right side group x, a right key
# "@MMK_R_x" the left side group x; other keys are glyph names.
KERN_FIXES: dict[str, dict[tuple[str, str], tuple[int, int, int]]] = {
    "upright": {
        ("@MMK_L_E", "yukrcyr"): (0, 5, 60),
        ("@MMK_L_F", "ibreve"): (40, 60, 85),
        ("@MMK_L_F", "icircumflex"): (40, 60, 100),
        ("@MMK_L_F", "idblgrave"): (50, 80, 145),
        ("@MMK_L_F", "igrave"): (0, 5, 25),
        ("@MMK_L_F", "iinvertedbreve"): (40, 60, 105),
        ("@MMK_L_F", "itilde"): (20, 50, 100),
        ("@MMK_L_K", "yukrcyr"): (0, 10, 60),
        ("@MMK_L_P", "iinvertedbreve"): (0, 0, 50),
        ("@MMK_L_P", "itilde"): (0, 0, 40),
        ("@MMK_L_T", "idblgrave"): (75, 100, 145),
        ("@MMK_L_T", "igrave"): (0, 25, 25),
        ("@MMK_L_T", "itilde"): (40, 70, 100),
        ("@MMK_L_T", "yukrcyr"): (0, 35, 70),
        ("@MMK_L_W", "idblgrave"): (70, 100, 140),
        ("@MMK_L_W", "igrave"): (0, 25, 20),
        ("@MMK_L_W", "itilde"): (25, 50, 85),
        ("@MMK_L_Y", "idblgrave"): (70, 100, 140),
        ("@MMK_L_Y", "igrave"): (0, 25, 20),
        ("@MMK_L_Y", "itilde"): (15, 40, 80),
        ("@MMK_L_f", "idblgrave"): (60, 80, 140),
        ("@MMK_L_f", "igrave"): (-10, 5, 20),
        ("@MMK_L_f", "itilde"): (10, 40, 90),
        ("@MMK_L_j", "idblgrave"): (40, 70, 100),
        ("@MMK_L_j", "itilde"): (0, 5, 60),
        ("Gecyr", "yukrcyr"): (0, 35, 70),
        ("Hacyr", "yukrcyr"): (0, 20, 70),
        ("Lcaron", "@MMK_R_T"): (-60, -60, 25),
        ("Lcaron", "@MMK_R_W"): (-70, -70, 25),
        ("Lcaron", "@MMK_R_Y"): (-90, -90, 25),
        ("Lcaron", "V"): (-70, -70, 25),
        ("Lcaron", "X"): (0, 0, 25),
        ("Ucyr", "yukrcyr"): (0, 30, 70),
        ("V", "idblgrave"): (70, 100, 140),
        ("V", "igrave"): (0, 25, 20),
        ("V", "itilde"): (25, 45, 85),
        ("Zhecyr", "yukrcyr"): (0, 10, 60),
        ("dcaron", "idblgrave"): (65, 85, 135),
        ("dcaron", "itilde"): (20, 30, 65),
        ("geupcyr", "yukrcyr"): (0, 35, 70),
        ("lcaron", "idblgrave"): (65, 85, 135),
        ("lcaron", "itilde"): (20, 30, 65),
        ("tcaron", "idblgrave"): (60, 95, 145),
        ("tcaron", "igrave"): (0, 20, 25),
        ("tcaron", "itilde"): (15, 40, 75),
        ("yukrcyr", "djecyr"): (20, 50, 85),
        ("yukrcyr", "tshecyr"): (20, 50, 85),
    },
    "italic": {
        ("@MMK_L_E", "yukrcyr"): (0, 5, 60),
        ("@MMK_L_F", "idblgrave"): (50, 75, 145),
        ("@MMK_L_K", "yukrcyr"): (0, 10, 60),
        ("@MMK_L_P", "icircumflex"): (0, 10, 55),
        ("@MMK_L_P", "iinvertedbreve"): (0, 0, 35),
        ("@MMK_L_P", "itilde"): (0, 0, 30),
        ("@MMK_L_T", "idblgrave"): (75, 100, 145),
        ("@MMK_L_T", "igrave"): (0, 25, 20),
        ("@MMK_L_T", "yukrcyr"): (0, 35, 70),
        ("@MMK_L_W", "idblgrave"): (75, 100, 140),
        ("@MMK_L_W", "igrave"): (0, 25, 20),
        ("@MMK_L_Y", "idblgrave"): (70, 95, 140),
        ("@MMK_L_Y", "rcaron"): (-65, -45, -65),
        ("@MMK_L_f", "idblgrave"): (60, 75, 130),
        ("Gecyr", "yukrcyr"): (0, 40, 70),
        ("Hacyr", "yukrcyr"): (0, 20, 65),
        ("Lcaron", "@MMK_R_T"): (-60, -60, 25),
        ("Lcaron", "@MMK_R_W"): (-70, -70, 25),
        ("Lcaron", "@MMK_R_Y"): (-90, -90, 25),
        ("Lcaron", "V"): (-70, -70, 25),
        ("Ucyr", "yukrcyr"): (0, 35, 70),
        ("V", "idblgrave"): (70, 100, 140),
        ("V", "igrave"): (0, 25, 20),
        ("Zhecyr", "yukrcyr"): (0, 10, 60),
        ("dcaron", "idblgrave"): (60, 85, 135),
        ("geupcyr", "yukrcyr"): (0, 35, 70),
        ("lcaron", "idblgrave"): (60, 85, 135),
        ("tcaron", "idblgrave"): (70, 95, 145),
        ("tcaron", "igrave"): (0, 20, 25),
        ("yukrcyr", "djecyr"): (20, 50, 85),
        ("yukrcyr", "tshecyr"): (20, 50, 85),
    },
}

MARK_SUFFIX = "comb"


def _layers_by_master(font: dict, glyph: dict) -> list[dict]:
    ids = {m["id"] for m in font["fontMaster"]}
    return [l for l in glyph["layers"] if l["layerId"] in ids]


def cyrillic_kerning_groups(font: dict, report: list) -> None:
    """Give Cyrillic look-alikes the kerning groups of their Latin base.

    A Cyrillic glyph that is one Latin glyph (Cyrillic A = A) or a Latin
    glyph with marks (yo = e with dieresis) draws the same outline as
    that Latin glyph, so it kerns with the same groups. Upstream gives the
    Cyrillic no groups, so Cyrillic text had no kerning.
    """
    left_key, right_key = extend.group_keys(font)
    glyphs = {g["glyphname"]: g for g in font["glyphs"]}

    def latin_base(name: str, depth: int = 0) -> str | None:
        g = glyphs[name]
        if depth > 4:
            return None
        if not extend.is_cyrillic(g):
            return name if g.get(left_key) or g.get(right_key) else None
        layers = _layers_by_master(font, g)
        bases = set()
        for layer in layers:
            shapes = layer.get("shapes", [])
            if not shapes or any("ref" not in s for s in shapes):
                return None
            first, rest = shapes[0], shapes[1:]
            if first.get("pos") or first.get("scale") or first.get("angle"):
                return None
            if any(not s["ref"].endswith(MARK_SUFFIX) for s in rest):
                return None
            bases.add(first["ref"])
        if len(bases) != 1:
            return None
        return latin_base(bases.pop(), depth + 1)

    for g in font["glyphs"]:
        if not extend.is_cyrillic(g) or g.get(left_key) or g.get(right_key):
            continue
        base = latin_base(g["glyphname"])
        if base is None:
            continue
        b = glyphs[base]
        for key in (left_key, right_key):
            if b.get(key):
                g[key] = b[key]
        ordered = extend.sorted_glyph(g)
        g.clear()
        g.update(ordered)
        report.append(("kern-group", g["glyphname"], base, ""))


def apply_kern_fixes(font: dict, style: str) -> None:
    table_key = "kerningLTR" if extend.italic_style(font) else "kerning"
    kerning = font.setdefault(table_key, {})
    masters = sorted(font["fontMaster"], key=lambda m: m["axesValues"][0])
    if [m["axesValues"][0] for m in masters] != [200, 400, 800]:
        raise ForkError("Kerning fixes expect masters at wght 200, 400 and 800.")
    for (left, right), values in KERN_FIXES[style].items():
        for master, value in zip(masters, values):
            row = kerning.setdefault(master["id"], {}).setdefault(left, {})
            row[right] = value


def extend_fonts(upright: dict, italic: dict, report_up: list, report_it: list) -> None:
    """Glyphs added in 0.2 (see extend.py)."""
    try:
        for font in (upright, italic):
            extend.make_longs(font)
            extend.make_napostrophe(font)
        extend.add_italic_cyrillic(italic, upright, report_it)
    except extend.ExtendError as e:
        raise ForkError(str(e)) from e
    copy_stems(upright, italic)
    cyrillic_kerning_groups(upright, report_up)
    cyrillic_kerning_groups(italic, report_it)
    apply_kern_fixes(upright, "upright")
    apply_kern_fixes(italic, "italic")
    report_up += [("added", "longs", "", ""), ("added", "napostrophe", "", "")]
    report_it += [("added", "longs", "", ""), ("added", "napostrophe", "", "")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("upstream", type=Path, help="Directory with the upstream .glyphs files.")
    ap.add_argument("out", type=Path, help="Output directory.")
    ap.add_argument("--skip-forms", action="store_true", help="Do not change the default forms.")
    ap.add_argument("--report", type=Path, help="Write a TSV report of the changes.")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    done = {}
    try:
        for up in SOURCES:
            done[up] = fork_font(args.upstream / up, args.skip_forms)
        (upright, up_text, rep_up), (italic, it_text, rep_it) = done[UPRIGHT], done[ITALIC]
        if not args.skip_forms:
            extend_fonts(upright, italic, rep_up, rep_it)
    except ForkError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for up, mine in SOURCES.items():
        font, text, rep = done[up]
        (args.out / mine).write_text(glyphsfmt.dumps(font, text), encoding="utf-8")
        rows += [(mine,) + r for r in rep]
    if args.report:
        lines = ["source\tkind\tglyph\tdetail\tmore"]
        lines += ["\t".join(str(v) for v in r) for r in rows]
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
