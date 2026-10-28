"""Glyphs that machine-made Sans 0.2 adds to the forked sources.

fork.py calls these functions after the default forms are set. They make
new glyphs only from glyph data that is already in the upstream sources:

- longs (U+017F) and napostrophe (U+0149) in both styles, to complete
  Latin Extended-A. longs is the upstream f outline without its
  crossbar; napostrophe is quoteright followed by n (components).
- The Cyrillic of the italic. Upstream added Cyrillic to the upright
  source only. The upstream Latin italic is the upright Latin slanted by
  8 degrees about half the x-height, with the same advance widths (see
  sans/STATUS.md). The italic Cyrillic is made the same way from the
  upright Cyrillic: outlines and anchors are slanted, components keep
  their reference (so the Cyrillic a, e, o, p, c, y, x use the italic
  Latin glyphs), and component offsets are slanted.

No outline is drawn by hand. Each step checks the structure of its
input and stops with an error when the input is not as expected.
"""

from __future__ import annotations

import copy
import math


class ExtendError(Exception):
    pass


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _num(v: float):
    v = round(v)
    return int(v)


def glyph_map(font: dict) -> dict:
    return {g["glyphname"]: g for g in font["glyphs"]}


def master_ids(font: dict) -> list[str]:
    return [m["id"] for m in font["fontMaster"]]


def master_layers(glyph: dict, font: dict) -> dict:
    ids = set(master_ids(font))
    return {l["layerId"]: l for l in glyph["layers"] if l["layerId"] in ids}


def metric(font: dict, master: dict, kind: str) -> float:
    for i, m in enumerate(font["metrics"]):
        if m.get("type") == kind:
            return master["metricValues"][i].get("pos", 0)
    raise ExtendError(f"Metric {kind} is missing.")


def anchor_xy(a: dict) -> tuple[float, float]:
    if "position" in a:
        x, y = (float(v) for v in a["position"].strip("{}").split(","))
        return x, y
    x, y = (list(a.get("pos", [])) + [0, 0])[:2]
    return x, y


def make_anchor(name: str, x: float, y: float, italic_style: bool) -> dict:
    x, y = _num(x), _num(y)
    if italic_style:
        a = {"name": name}
        if x or y:
            a["pos"] = [x, y]
        return a
    return {"name": name, "position": "{%d, %d}" % (x, y)}


def sorted_glyph(g: dict) -> dict:
    return {"glyphname": g["glyphname"], **{k: g[k] for k in sorted(g) if k != "glyphname"}}


def sorted_dict(d: dict) -> dict:
    return {k: d[k] for k in sorted(d)}


def insert_glyph(font: dict, glyph: dict, after: str) -> None:
    names = [g["glyphname"] for g in font["glyphs"]]
    if glyph["glyphname"] in names:
        raise ExtendError(f"{glyph['glyphname']} exists already.")
    font["glyphs"].insert(names.index(after) + 1, glyph)
    for p in font.get("customParameters", []):
        if p["name"] == "glyphOrder":
            order = p["value"]
            order.insert(order.index(after) + 1 if after in order else len(order), glyph["glyphname"])


def italic_style(font: dict) -> bool:
    """The italic source uses the newer Glyphs 3 keys (kernLeft, pos)."""
    return "kerningLTR" in font


KEY_NEW = {
    "leftKerningGroup": "kernLeft",
    "rightKerningGroup": "kernRight",
    "leftMetricsKey": "metricLeft",
    "rightMetricsKey": "metricRight",
    "widthMetricsKey": "metricWidth",
}


def group_keys(font: dict) -> tuple[str, str]:
    return ("kernLeft", "kernRight") if italic_style(font) else ("leftKerningGroup", "rightKerningGroup")


# --------------------------------------------------------------------------
# Latin Extended-A: longs and napostrophe
# --------------------------------------------------------------------------

# Node indices of the f crossbar in the upstream f (one contour, 24
# nodes): the right end of the bar is 1-4, the left end is 19-22.
F_BAR_RIGHT = (1, 2, 3, 4)
F_BAR_LEFT = (19, 20, 21, 22)


def make_longs(font: dict) -> None:
    """Add longs (U+017F): the upstream f without the crossbar.

    The bar nodes are removed, so the stem runs straight from the
    baseline to the hook. The glyph moves left so that its stem has the
    left side bearing of l; the right side bearing of the hook stays as
    in f.
    """
    G = glyph_map(font)
    f, l = G["f"], G["l"]
    left_key, right_key = group_keys(font)
    new = {"glyphname": "longs", "unicode": 0x017F, "layers": []}
    if f.get(right_key):
        new[right_key] = f[right_key]
    if l.get(left_key):
        new[left_key] = l[left_key]
    f_layers, l_layers = master_layers(f, font), master_layers(l, font)
    for mid in master_ids(font):
        fl = f_layers[mid]
        shapes = fl.get("shapes", [])
        if len(shapes) != 1 or "nodes" not in shapes[0] or len(shapes[0]["nodes"]) != 24:
            raise ExtendError("f is not one contour of 24 nodes; longs cannot be made.")
        nodes = shapes[0]["nodes"]
        bottom = {nodes[i][1] for i in (1, 2, 21, 22)}
        top = {nodes[i][1] for i in (3, 4, 19, 20)}
        if len(bottom) != 1 or len(top) != 1 or bottom == top:
            raise ExtendError(f"The f crossbar is not at nodes {F_BAR_RIGHT} and {F_BAR_LEFT}.")
        if any(nodes[i][2] != "l" for i in F_BAR_RIGHT + F_BAR_LEFT):
            raise ExtendError("The f crossbar nodes are not line nodes.")
        keep = [n for i, n in enumerate(nodes) if i not in F_BAR_RIGHT + F_BAR_LEFT]
        # Left side bearing: the stem foot (node 23 of f) goes to the
        # leftmost point of l.
        stem_x = nodes[23][0]
        l_min = min(n[0] for s in l_layers[mid]["shapes"] for n in s.get("nodes", []))
        dx = l_min - stem_x
        out_nodes = [[n[0] + dx, n[1], n[2]] for n in keep]
        layer = {"layerId": mid, "shapes": [{"closed": 1, "nodes": out_nodes}], "width": fl["width"] + dx}
        if fl.get("anchors"):
            ital = italic_style(font)
            layer["anchors"] = [
                make_anchor(a["name"], anchor_xy(a)[0] + dx, anchor_xy(a)[1], ital) for a in fl["anchors"]
            ]
        new["layers"].append(sorted_dict(layer))
    insert_glyph(font, sorted_glyph(new), after="f")


def make_napostrophe(font: dict) -> None:
    """Add napostrophe (U+0149): quoteright and n side by side, as typed."""
    G = glyph_map(font)
    q, n = G["quoteright"], G["n"]
    left_key, right_key = group_keys(font)
    new = {"glyphname": "napostrophe", "unicode": 0x0149, "layers": []}
    if q.get(left_key):
        new[left_key] = q[left_key]
    if n.get(right_key):
        new[right_key] = n[right_key]
    ql, nl = master_layers(q, font), master_layers(n, font)
    ital = italic_style(font)
    for mid in master_ids(font):
        w = ql[mid]["width"]
        first = {"ref": "quoteright"}
        second = {"pos": [w, 0], "ref": "n"}
        if not ital:
            first = {"alignment": -1, **first}
            second = {"alignment": -1, **second}
        layer = {"layerId": mid, "shapes": [first, second], "width": w + nl[mid]["width"]}
        new["layers"].append(sorted_dict(layer))
    insert_glyph(font, sorted_glyph(new), after="n")


# --------------------------------------------------------------------------
# Italic Cyrillic
# --------------------------------------------------------------------------

CYRILLIC_RANGES = ((0x0400, 0x052F), (0x1C80, 0x1C8F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F))


def is_cyrillic(glyph: dict) -> bool:
    u = glyph.get("unicode")
    if isinstance(u, int) and any(a <= u <= b for a, b in CYRILLIC_RANGES):
        return True
    base = glyph["glyphname"].split(".")[0]
    return base.endswith("cyr")


def italic_transform(font: dict):
    """Return {master id: (tan(angle), y0)} for the italic source."""
    out = {}
    for m in font["fontMaster"]:
        angle = metric(font, m, "italic angle")
        if not angle:
            raise ExtendError("The italic master has no italic angle.")
        out[m["id"]] = (math.tan(math.radians(angle)), metric(font, m, "x-height") / 2)
    return out


def _segments(nodes: list) -> tuple[list, list]:
    """Split a closed Glyphs contour into segments.

    Returns (start, segments): each segment is (type, offcurves, node),
    where node is the on-curve node that ends the segment.
    """
    on = [i for i, n in enumerate(nodes) if n[2] != "o"]
    if not on:
        raise ExtendError("A contour has no on-curve node.")
    last = on[-1]
    rot = nodes[last + 1 :] + nodes[: last + 1]
    segs, offs = [], []
    for n in rot:
        if n[2] == "o":
            offs.append(n)
        else:
            segs.append((n[2].rstrip("s"), offs, n))
            offs = []
    return rot[-1], segs


def reverse_contour(nodes: list) -> list:
    """Reverse the direction of a closed Glyphs contour."""
    _, segs = _segments(nodes)
    m = len(segs)
    out = []
    for k in range(m - 1, -1, -1):
        kind, offs, _end = segs[k]
        start = segs[k - 1][2]  # k - 1 = -1 is the last node: the contour is closed
        out += [list(o) for o in reversed(offs)]
        smooth = "s" if start[2].endswith("s") else ""
        out.append([start[0], start[1], kind + smooth])
    return out


def decompose(glyphs: dict, ref: str, layer_id: str, sx=1, sy=1, px=0, py=0) -> list:
    """Outline contours of component REF in layer LAYER_ID, transformed."""
    layer = next((l for l in glyphs[ref]["layers"] if l["layerId"] == layer_id), None)
    if layer is None:
        raise ExtendError(f"{ref} has no layer {layer_id}.")
    out = []
    for s in layer.get("shapes", []):
        if "nodes" in s:
            nodes = [[sx * n[0] + px, sy * n[1] + py] + list(n[2:]) for n in s["nodes"]]
            if sx * sy < 0:
                nodes = reverse_contour(nodes)
            out.append({"closed": s.get("closed", 1), "nodes": nodes})
        else:
            if s.get("angle"):
                raise ExtendError(f"{ref}: rotated components are not supported.")
            csx, csy = (list(s.get("scale", [])) + [1, 1])[:2]
            cpx, cpy = (list(s.get("pos", [])) + [0, 0])[:2]
            out += decompose(glyphs, s["ref"], layer_id, sx * csx, sy * csy, sx * cpx + px, sy * cpy + py)
    return out


def _master_by_weight(font: dict) -> dict:
    return {tuple(m["axesValues"]): m["id"] for m in font["fontMaster"]}


def add_italic_cyrillic(italic: dict, upright: dict, report: list) -> list[str]:
    """Copy the upright Cyrillic into the italic source, slanted.

    Returns the names of the glyphs that were added.
    """
    up_glyphs = upright["glyphs"]
    it_names = {g["glyphname"] for g in italic["glyphs"]}
    up_by_name = glyph_map(upright)
    todo = [g for g in up_glyphs if is_cyrillic(g) and g["glyphname"] not in it_names]
    if not todo:
        return []
    todo_names = {g["glyphname"] for g in todo}

    # Every component must exist in the italic, or be copied too.
    for g in todo:
        for layer in g["layers"]:
            for s in layer.get("shapes", []):
                if "ref" in s and s["ref"] not in it_names and s["ref"] not in todo_names:
                    raise ExtendError(f"{g['glyphname']} uses {s['ref']}, which the italic does not have.")

    it_map = _master_by_weight(italic)
    up_to_it = {}
    for m in upright["fontMaster"]:
        key = tuple(m["axesValues"])
        if key not in it_map:
            raise ExtendError(f"No italic master at {key}.")
        up_to_it[m["id"]] = it_map[key]
    xf = italic_transform(italic)
    it_glyphs = glyph_map(italic)
    up_master_ids = set(up_to_it)

    def width_of(name: str, mid: str, glyphs: dict, layers_new: dict | None = None) -> float:
        if layers_new is not None and name in layers_new:
            return layers_new[name][mid]["width"]
        for l in glyphs[name]["layers"]:
            if l["layerId"] == mid:
                return l["width"]
        raise ExtendError(f"{name} has no layer {mid}.")

    added_layers: dict[str, dict] = {}
    new_glyphs = []
    for g in todo:
        name = g["glyphname"]
        out = {"glyphname": name}
        for k, v in g.items():
            if k in ("glyphname", "layers"):
                continue
            out[KEY_NEW.get(k, k)] = copy.deepcopy(v)
        layers = []
        per_master = {}
        for layer in g["layers"]:
            if layer["layerId"] not in up_master_ids:
                continue  # Backup layers (not masters) are not copied.
            mid = up_to_it[layer["layerId"]]
            t, y0 = xf[mid]

            def sx(x, y):
                return x + t * (y - y0)

            nl = {"layerId": mid, "width": layer["width"]}
            shapes = []
            # Mirrored components (Cyrillic Ya is a mirrored R, E reversed
            # a mirrored C) are made outlines first: a mirrored italic
            # glyph would slant the wrong way.
            src_shapes = []
            for s in layer.get("shapes", []):
                if "ref" in s and (s.get("scale") or s.get("angle")):
                    sx_, sy_ = (list(s.get("scale", [])) + [1, 1])[:2]
                    px_, py_ = (list(s.get("pos", [])) + [0, 0])[:2]
                    if s.get("angle"):
                        raise ExtendError(f"{name}: rotated components are not supported.")
                    src_shapes += decompose(up_by_name, s["ref"], layer["layerId"], sx_, sy_, px_, py_)
                    report.append(("italic-cyrillic-decomposed", name, s["ref"], ""))
                else:
                    src_shapes.append(s)
            for s in src_shapes:
                if "nodes" in s:
                    ns = {k: v for k, v in s.items() if k != "nodes"}
                    ns["nodes"] = [[_num(sx(n[0], n[1])), n[1]] + list(n[2:]) for n in s["nodes"]]
                    shapes.append(sorted_dict(ns))
                else:
                    ns = {k: copy.deepcopy(v) for k, v in s.items() if k != "pos"}
                    if "scale" in s or "angle" in s:
                        raise ExtendError(f"{name}: scaled or rotated components are not supported.")
                    px, py = (list(s.get("pos", [])) + [0, 0])[:2]
                    # A component moved by (px, py) in the upright: the
                    # slanted copy of the composite has the slanted
                    # component moved by (px + t * py, py).
                    qx, qy = _num(px + t * py), _num(py)
                    if qx or qy:
                        ns["pos"] = [qx, qy]
                    shapes.append(sorted_dict(ns))
            if shapes:
                nl["shapes"] = shapes
            if layer.get("anchors"):
                nl["anchors"] = [
                    make_anchor(a["name"], sx(*anchor_xy(a)), anchor_xy(a)[1], True) for a in layer["anchors"]
                ]
            comps = [s for s in src_shapes if "ref" in s]
            if comps and len(comps) == len(src_shapes):
                first = comps[0]
                up_w = width_of(first["ref"], layer["layerId"], up_by_name)
                if not first.get("pos") and layer["width"] == up_w:
                    # An alias of one glyph (Cyrillic a = Latin a): take
                    # the width of the italic glyph.
                    nl["width"] = width_of(first["ref"], mid, it_glyphs, added_layers)
            per_master[mid] = nl
            layers.append(sorted_dict(nl))
        if set(per_master) != set(xf):
            raise ExtendError(f"{name}: not every master has a layer.")
        added_layers[name] = per_master
        out["layers"] = layers
        new_glyphs.append(sorted_glyph(out))
        report.append(("italic-cyrillic", name, "slanted" if any("nodes" in s for l in layers for s in l.get("shapes", [])) else "components", ""))

    # Glyph order: after the upright predecessor that the italic has.
    order = [g["glyphname"] for g in up_glyphs]
    placed = set()
    for ng in new_glyphs:
        i = order.index(ng["glyphname"])
        after = None
        for j in range(i - 1, -1, -1):
            cand = order[j]
            if cand in it_names or cand in placed:
                after = cand
                break
        insert_glyph(italic, ng, after=after)
        placed.add(ng["glyphname"])

    copy_cyrillic_features(italic, upright, todo_names)
    copy_cyrillic_kerning(italic, upright, todo_names, up_to_it)
    return [g["glyphname"] for g in new_glyphs]


def copy_cyrillic_features(italic: dict, upright: dict, names: set) -> None:
    """Copy the Cyrillic feature code (classes, locl BGR, ss04)."""
    up_classes = {c["name"]: c for c in upright.get("classes", [])}
    it_classes = {c["name"] for c in italic.get("classes", [])}
    for cname in ("cyrDFLT", "cyrBGR"):
        if cname in up_classes and cname not in it_classes:
            italic["classes"].append(copy.deepcopy(up_classes[cname]))

    up_feats = {f["tag"]: f for f in upright["features"]}
    it_feats = {f["tag"]: f for f in italic["features"]}
    marker = "\nscript cyrl;"
    up_locl = up_feats["locl"]["code"]
    if marker in up_locl and marker not in it_feats["locl"]["code"]:
        head, block = up_locl.split(marker, 1)
        it_code = it_feats["locl"]["code"]
        if it_code.rstrip("\n") != head.rstrip("\n"):
            raise ExtendError("The italic locl code is not the upright locl code without Cyrillic.")
        loc = it_feats["locl"]
        loc["code"] = head + marker + block
        # Glyphs.app must not write locl again from the glyph names.
        loc.pop("automatic", None)
    if "ss04" in up_feats and "ss04" not in it_feats:
        feats = italic["features"]
        after = [f["tag"] for f in upright["features"]].index("ss04") - 1
        prev_tag = upright["features"][after]["tag"]
        idx = [f["tag"] for f in feats].index(prev_tag) + 1
        feats.insert(idx, copy.deepcopy(up_feats["ss04"]))


def copy_cyrillic_kerning(italic: dict, upright: dict, names: set, up_to_it: dict) -> None:
    """Copy the kerning pairs of the copied glyphs (glyph pairs, as upstream)."""
    up_kern = upright.get("kerning", {})
    it_kern = italic.setdefault("kerningLTR", {})
    for up_mid, table in up_kern.items():
        it_mid = up_to_it.get(up_mid)
        if it_mid is None:
            continue
        dest = it_kern.setdefault(it_mid, {})
        for left, row in table.items():
            for right, value in row.items():
                if left in names or right in names:
                    dest.setdefault(left, {})[right] = value
