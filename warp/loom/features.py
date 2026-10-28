"""OpenType feature code for machine-made Warp (GSUB).

ufo2ft writes kern, mark, mkmk and GDEF from the UFO kerning, anchors
and glyph categories. This module writes the substitutions:

* ccmp: i and j lose their dot before a combining mark above.
* liga: ff, fi, fl, ffi, ffl.
* Figures. Default: lining, tabular (the sketch's figures, for tables
  and papers). onum: old-style, proportional (as in the sketch's running
  text). lnum, pnum, tnum switch each property. The lookups run in the
  order onum, lnum, pnum, tnum, so onum + tnum gives tabular old-style.
* smcp: lowercase to small capitals (ß to two small-cap S). c2sc:
  capitals to small capitals.

Apache-2.0.
"""

from __future__ import annotations

from loom import charset as CS

FIG = CS.FIG_NAMES


def _cls(suffix: str) -> str:
    return "[" + " ".join(f"{n}{suffix}" for n in FIG) + "]"


def features(st) -> str:
    sm = CS.smcp_pairs()
    c2 = CS.c2sc_pairs()
    top_marks = " ".join(n for n in CS.ORDER if CS.BY_NAME[n].category == "mark"
                         and not n.endswith(".case") and n != "cedillacomb")
    lines = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem grek dflt;",
        "",
        f"@CombTop = [{top_marks}];",
        "@Fig = " + _cls("") + ";",
        "@FigLf = " + _cls(".lf") + ";",
        "@FigOsf = " + _cls(".osf") + ";",
        "@FigTosf = " + _cls(".tosf") + ";",
        "@Lower = [" + " ".join(a for a, _ in sm) + "];",
        "@LowerSc = [" + " ".join(b for _, b in sm) + "];",
        "@Upper = [" + " ".join(a for a, _ in c2) + "];",
        "@UpperSc = [" + " ".join(b for _, b in c2) + "];",
        "",
        "feature ccmp {",
        "    lookup dotless {",
        "        sub [i j]' @CombTop by [dotlessi dotlessj];",
        "    } dotless;",
        "} ccmp;",
        "",
        "feature smcp {",
        "    sub germandbls by s.sc s.sc;",
        "    sub f_f_i by f.sc f.sc i.sc;",
        "    sub f_f_l by f.sc f.sc l.sc;",
        "    sub f_f by f.sc f.sc;",
        "    sub fi by f.sc i.sc;",
        "    sub fl by f.sc l.sc;",
        "    sub dotlessj by j.sc;",
        "    sub micro by mu.sc;",
        "    sub @Lower by @LowerSc;",
        "} smcp;",
        "",
        "feature c2sc {",
        "    sub @Upper by @UpperSc;",
        "} c2sc;",
        "",
        "feature liga {",
        "    sub f f i by f_f_i;",
        "    sub f f l by f_f_l;",
        "    sub f f by f_f;",
        "    sub f i by fi;",
        "    sub f l by fl;",
        "} liga;",
        "",
        "feature onum {",
        "    sub @Fig by @FigOsf;",
        "    sub @FigLf by @FigOsf;",
        "} onum;",
        "",
        "feature lnum {",
        "    sub @FigOsf by @FigLf;",
        "    sub @FigTosf by @Fig;",
        "} lnum;",
        "",
        "feature pnum {",
        "    sub @Fig by @FigLf;",
        "    sub @FigTosf by @FigOsf;",
        "} pnum;",
        "",
        "feature tnum {",
        "    sub @FigLf by @Fig;",
        "    sub @FigOsf by @FigTosf;",
        "} tnum;",
        "",
    ]
    return "\n".join(lines)
