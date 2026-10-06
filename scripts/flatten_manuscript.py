#!/usr/bin/env python3
"""Flatten the modular LaTeX sources into the single-file manuscript.tex.

Inlines every \\input{sec_*} and embeds the compiled .bbl as the
bibliography, producing a standalone file that compiles identically
(tectonic or pdflatex) given only the figure PNGs.
"""
import os
import re

LATEX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "repo-push", "paper", "latex")


def flatten():
    src = open(os.path.join(LATEX, "main.tex")).read()
    out = []
    for line in src.split("\n"):
        m = re.match(r"\\input\{(.+?)\}", line.strip())
        if m:
            name = m.group(1)
            body = open(os.path.join(LATEX, name + ".tex")).read()
            out.append(body.rstrip())
            continue
        if line.strip() in ("\\bibliographystyle{unsrtnat}",
                            "\\bibliography{refs}"):
            if "\\begin{thebibliography}" not in "\n".join(out):
                bbl = open(os.path.join(LATEX, "main.bbl")).read()
                out.append("% ---- bibliography (inlined from compiled .bbl) ----")
                out.append(bbl.rstrip())
            continue
        out.append(line)
    txt = "\n".join(out)
    header = ("% ======================================================================\n"
              "% The Prime-Spectral Framework: Theorems, Conjectures, and Numerical Tests\n"
              "% Single-file manuscript (flattened from the modular sources).\n"
              "% Compiles with tectonic or pdflatex; requires the figure files\n"
              "% fig_c4_ladder.png, fig_c4_controls.png, fig_c4_strongeth.png and\n"
              "% fig_c9_prereg.png in the same directory.\n"
              "% ======================================================================\n")
    # drop the original comment header (first block of comment lines)
    lines = txt.split("\n")
    i = 0
    while i < len(lines) and (lines[i].startswith("%") or not lines[i].strip()):
        i += 1
    txt = header + "\n".join(lines[i:])
    open(os.path.join(LATEX, "manuscript.tex"), "w").write(txt)
    print("flattened ->", os.path.join(LATEX, "manuscript.tex"),
          f"({txt.count(chr(10)) + 1} lines)")


if __name__ == "__main__":
    flatten()
