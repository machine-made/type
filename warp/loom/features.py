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
* 0.2: sups (superior figures), subs and sinf (inferior figures), numr,
  dnom, and frac (figures before a slash or fraction slash become
  numerators, after it denominators; the slash becomes the fraction
  slash).

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
    from loom.extended import BELOW
    top_marks = " ".join(n for n in CS.ORDER if CS.BY_NAME[n].category == "mark" and CS.BY_NAME[n].unicodes
                         and not n.endswith(".case") and n not in BELOW and n not in ("cedillacomb", "ogonekcomb"))
    sups = " ".join(CS.glyph_name(chr(CS.SUPERIORS[f])) for f in CS.FIGURES)
    infs = " ".join(CS.glyph_name(chr(CS.INFERIORS[f])) for f in CS.FIGURES)
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
        f"@Sups = [{sups}];",
        f"@Infs = [{infs}];",
        "@Numr = " + _cls(".numr") + ";",
        "@Dnom = " + _cls(".dnom") + ";",
        "@FigAll = [@Fig @FigLf @FigOsf @FigTosf];",
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
        "    sub ij by i.sc j.sc;",
        "    sub napostrophe by quoteright n.sc;",
        "    sub @Lower by @LowerSc;",
        "} smcp;",
        "",
        "feature c2sc {",
        "    sub IJ by i.sc j.sc;",
        "    sub Idotaccent by i.sc;",
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
        "feature sups {",
        "    sub @Fig by @Sups;",
        "    sub @FigLf by @Sups;",
        "    sub @FigOsf by @Sups;",
        "    sub @FigTosf by @Sups;",
        "} sups;",
        "",
        "feature subs {",
        "    sub @Fig by @Infs;",
        "    sub @FigLf by @Infs;",
        "    sub @FigOsf by @Infs;",
        "    sub @FigTosf by @Infs;",
        "} subs;",
        "",
        "feature sinf {",
        "    sub @Fig by @Infs;",
        "    sub @FigLf by @Infs;",
        "    sub @FigOsf by @Infs;",
        "    sub @FigTosf by @Infs;",
        "} sinf;",
        "",
        "feature numr {",
        "    sub @Fig by @Numr;",
        "    sub @FigLf by @Numr;",
        "    sub @FigOsf by @Numr;",
        "    sub @FigTosf by @Numr;",
        "} numr;",
        "",
        "feature dnom {",
        "    sub @Fig by @Dnom;",
        "    sub @FigLf by @Dnom;",
        "    sub @FigOsf by @Dnom;",
        "    sub @FigTosf by @Dnom;",
        "} dnom;",
        "",
        "feature frac {",
        "    lookup frac_slash {",
        "        sub slash by fraction;",
        "    } frac_slash;",
        "    lookup frac_numr {",
        "        sub @Fig by @Numr;",
        "        sub @FigLf by @Numr;",
        "        sub @FigOsf by @Numr;",
        "        sub @FigTosf by @Numr;",
        "    } frac_numr;",
        "    lookup frac_dnom {",
        "        sub [fraction @Dnom] @Numr' by @Dnom;",
        "    } frac_dnom;",
        "} frac;",
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
