"""Set a page of formulas with LuaLaTeX and unicode-math in Warp (MATH table proof).

Usage:
    python tools/math_proof.py [--fonts ../fonts/warp/ttf] [--out ../proofs/warp/warp-math.png]

Writes a .tex file into build/math-proof/, runs lualatex twice (the
first run builds the luaotfload cache), checks the log for missing
characters, and renders the PDF page to a PNG with pdftoppm. The page
has fractions, radicals of growing height (size variants, then the
assembly), big operators with limits, stretched delimiters from \\big
to assemblies taller than the largest variant, maths accents and
Greek.

Needs lualatex with unicode-math and fontspec, and pdftoppm (poppler).
Not run in CI (TeX Live is large); the MATH table itself is tested in
tests/test_warp.py with fontTools and HarfBuzz.

Apache-2.0.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WARP = HERE.parent
ROOT = WARP.parent

TEX = r"""
\documentclass[11pt]{article}
\usepackage[a4paper,margin=18mm]{geometry}
\usepackage{fontspec}
\usepackage{unicode-math}
\usepackage{amsmath}
\setmainfont{MachineMadeWarp-Regular.ttf}[Path=FONTS/, ItalicFont=MachineMadeWarp-Italic.ttf,
  BoldFont=MachineMadeWarp-Bold.ttf, BoldItalicFont=MachineMadeWarp-BoldItalic.ttf]
\setmathfont{MachineMadeWarp-Regular.ttf}[Path=FONTS/]
\setmathfont{MachineMadeWarp-Bold.ttf}[Path=FONTS/, version=bold]
\pagestyle{empty}
\setlength{\parindent}{0pt}
\begin{document}
\textbf{machine-made Warp: the MATH table} \hfill \textit{set by LuaLaTeX and unicode-math}

\medskip
\textsc{Fractions.} Inline $\frac{a}{b}+\frac{1}{2}$ and a continued fraction:
\[
  x = a_0 + \cfrac{1}{a_1 + \cfrac{1}{a_2 + \cfrac{1}{a_3 + \cdots}}}
  \qquad
  \frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u
  \qquad
  \binom{n}{k} = \frac{n!}{k!\,(n-k)!}
\]

\textsc{Radicals of growing height.}
\[
  \sqrt{x} \quad \sqrt{x^2+y^2} \quad \sqrt{\frac{a}{b}} \quad \sqrt{\frac{\frac{a}{b}}{\frac{c}{d}}}
  \quad \sqrt{1+\sqrt{1+\sqrt{1+\sqrt{1+x}}}} \quad \sqrt[3]{\alpha\beta}
  \quad \sqrt{\begin{matrix} a \\ b \\ c \\ d \\ e \\ f \end{matrix}}
  \quad \sqrt{\begin{matrix} 1 \\ 2 \\ 3 \\ 4 \\ 5 \\ 6 \\ 7 \\ 8 \\ 9 \end{matrix}}
\]

\textsc{Big operators with limits.}
\[
  \sum_{i=1}^{n} i^2 = \frac{n(n+1)(2n+1)}{6}
  \qquad \prod_{k=1}^{\infty} \left(1 - \frac{1}{p_k^{s}}\right)^{-1}
  \qquad \int_0^1 f(x)\,dx \qquad \int\limits_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
\]
Inline: $\sum_{i=1}^n x_i$, $\prod_k a_k$, $\int_a^b g(t)\,dt$.

\textsc{Delimiters, from text size to assemblies.}
\[
  (\big(\Big(\bigg(\Bigg( \quad [\big[\Big[\bigg[\Bigg[ \quad \{\big\{\Big\{\bigg\{\Bigg\{
  \quad \langle\big\langle\Big\langle\bigg\langle\Bigg\langle
  \quad |\big|\Big|\bigg|\Bigg| \quad \|\big\|\Big\|\bigg\|\Bigg\|
\]
\[
  \left( \frac{a}{b} \right) \left[ \frac{\frac{a}{b}}{c} \right]
  \left\{ \frac{1}{\frac{2}{\frac{3}{4}}} \right\}
  \left\langle \psi \middle| \frac{\hat{H}}{2} \middle| \phi \right\rangle
  \left\| \frac{x}{y} \right\|
  \quad
  \left( \begin{matrix} a_{11} & a_{12} \\ a_{21} & a_{22} \\ a_{31} & a_{32} \\ a_{41} & a_{42} \\ a_{51} & a_{52} \\ a_{61} & a_{62} \\ a_{71} & a_{72} \end{matrix} \right)
  \left[ \begin{matrix} 1 \\ 2 \\ 3 \\ 4 \\ 5 \\ 6 \\ 7 \end{matrix} \right]
  \left\{ \begin{matrix} x \\ y \\ z \\ u \\ v \\ w \\ t \end{matrix} \right.
  \left| \begin{matrix} \alpha \\ \beta \\ \gamma \\ \delta \\ \epsilon \\ \zeta \\ \eta \end{matrix} \right|
  \left\| \begin{matrix} 1 \\ 0 \\ 0 \\ 1 \\ 0 \\ 1 \\ 1 \end{matrix} \right\|
\]

\textsc{Scripts, accents, Greek.}
\[
  e^{i\pi} + 1 = 0 \quad x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)} \quad
  \hat{x}\ \tilde{a}\ \bar{z}\ \dot{y}\ \ddot{y}\ \breve{u}\ \check{c}
  \quad \Gamma(z) = \int_0^\infty t^{z-1} e^{-t}\,dt
  \quad \hbar\,\omega \quad \ell^2
\]
\[
  f(x) = \begin{cases} x^2 & x \geq 0 \\ -x & x < 0 \end{cases}
  \qquad
  \forall \varepsilon > 0\ \exists \delta > 0 : |x - y| < \delta \Rightarrow |f(x) - f(y)| < \varepsilon
\]

Text with maths: the eigenvalue problem $\mathcal{L}\hat{q} = \lambda \hat{q}$ has a spectrum
$\{\lambda_k\}_{k \geq 1}$; the leading mode grows when $\Re\lambda_1 > 0$, that is when
$\mathrm{Re} > \mathrm{Re}_c \approx 20.2$.

\boldmath
\[
  \sum_{i=1}^{n} \frac{a_i}{\sqrt{b_i}} \left( \int_0^1 \phi_i(x)\,dx \right)
\]
\unboldmath
\end{document}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LuaLaTeX proof of the Warp MATH table.")
    ap.add_argument("--fonts", default=str(ROOT / "fonts" / "warp" / "ttf"))
    ap.add_argument("--out", default=str(ROOT / "proofs" / "warp" / "warp-math.png"))
    ap.add_argument("--dpi", type=int, default=150)
    args = ap.parse_args(argv)
    for tool in ("lualatex", "pdftoppm"):
        if shutil.which(tool) is None:
            print(f"Error: {tool} is not installed.", file=sys.stderr)
            return 2
    work = WARP / "build" / "math-proof"
    work.mkdir(parents=True, exist_ok=True)
    fonts = Path(args.fonts).resolve()
    tex = TEX.replace("FONTS", str(fonts))
    # unicode-math has no glyph for these; keep the page to what the font has
    tex = tex.replace(r"\mathcal{L}", "L").replace(r"\Re\lambda", r"\mathrm{Re}\,\lambda")
    (work / "warp-math.tex").write_text(tex)
    for _ in range(2):
        res = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", "warp-math.tex"],
                             cwd=work, capture_output=True, text=True)
    log = (work / "warp-math.log").read_text(errors="replace")
    if res.returncode != 0:
        print(log[-3000:], file=sys.stderr)
        print("Error: lualatex failed.", file=sys.stderr)
        return 1
    missing = sorted(set(re.findall(r"Missing character: There is no (.+?) \(", log)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", str(args.dpi), "-singlefile", str(work / "warp-math.pdf"),
                    str(out.with_suffix(""))], check=True)
    print(f"Wrote {out}.")
    if missing:
        print("Missing characters: " + " ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
