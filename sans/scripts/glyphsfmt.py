"""Read and write Glyphs 3 source files as text.

The writer gives the same text as Glyphs.app: a file that is read and
written again without changes is byte-identical. Thus a changed source
has a small, reviewable diff against the original.
"""

from __future__ import annotations

import re

import openstep_plist

_BARE = re.compile(r"^[A-Za-z0-9._]+$", re.ASCII)
_NUMBER = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
# Keys whose list value Glyphs writes on one line, for example pos = (92,0);
INLINE_KEYS = {"pos", "scale", "target", "origin"}

# Glyphs writes line breaks in strings as "\n" or as real line breaks,
# depending on the file. LITERAL_BREAKS selects the second form.
LITERAL_BREAKS = False
# Some files quote dictionary keys that are numbers ("8" = 10;).
QUOTE_NUMERIC_KEYS = False


def quote(s: str, key: bool = False) -> str:
    if s and _BARE.match(s) and not (_NUMBER.match(s) and (QUOTE_NUMERIC_KEYS or not key)):
        return s
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    if not LITERAL_BREAKS:
        out = out.replace("\n", "\\n").replace("\t", "\\t")
    return f'"{out}"'


def scalar(v) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return quote(v)


def _inline_item(x) -> str:
    if isinstance(x, dict):
        return "{" + "".join(f"{quote(k, key=True)} = {_inline_item(v)};" for k, v in x.items()) + "}"
    return scalar(x)


def _inline(items) -> str:
    return "(" + ",".join(_inline_item(x) for x in items) + ")"


def dump(v, key: str | None = None) -> str:
    if isinstance(v, dict):
        lines = ["{"]
        for k, val in v.items():
            lines.append(f"{quote(k, key=True)} = {dump(val, k)};")
        lines.append("}")
        return "\n".join(lines)
    if isinstance(v, list):
        if key in INLINE_KEYS:
            return _inline(v)
        if key == "nodes":
            return "(\n" + ",\n".join(_inline(n) for n in v) + "\n)"
        if not v:
            return "(\n)"
        return "(\n" + ",\n".join(dump(x) for x in v) + "\n)"
    return scalar(v)


def detect_style(text: str) -> None:
    """Set the writer options so that the output follows the style of TEXT."""
    global LITERAL_BREAKS, QUOTE_NUMERIC_KEYS
    LITERAL_BREAKS = "\\n" not in text
    QUOTE_NUMERIC_KEYS = re.search(r'^"[0-9]+" = ', text, re.M) is not None


def loads(text: str):
    detect_style(text)
    return openstep_plist.loads(text, use_numbers=True)


def dumps(data, like: str) -> str:
    """Write DATA in the style of the source text LIKE."""
    detect_style(like)
    out = dump(data)
    return out + "\n" if like.endswith("\n") else out
