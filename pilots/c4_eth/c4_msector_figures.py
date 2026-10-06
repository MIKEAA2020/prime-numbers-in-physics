#!/usr/bin/env python3
"""Figures for the M-sector Jacobi program (fig_c4_msector.png)."""
import json
import os

import numpy as np

import c4_scaled_eth as base

OUT = base.OUT


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    for fp in ("/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(fp):
            fm.fontManager.addfont(fp)
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Noto Sans SC"]
    plt.rcParams["axes.unicode_minus"] = False

    res = json.load(open(os.path.join(OUT, "c4_msector_results.json")))
    cla = json.load(open(os.path.join(OUT, "c4_msector_classical.json")))

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6),
                             constrained_layout=True)

    # (a) kappa vs sector dimension n
    ax = axes[0, 0]
    fams = [
        ("d2_dose", "o", "#4c72b0", "d=2, matched dose (closed form)"),
        ("d2_fixed", "o", "#4c72b0", "d=2, fixed V (closed form)"),
        ("d3_dose", "s", "#dd8452", "d=3, matched dose"),
        ("d3_fixed", "s", "#dd8452", "d=3, fixed V"),
        ("d4_dose", "D", "#55a868", "d=4, matched dose"),
        ("d4_fixed", "D", "#55a868", "d=4, fixed V"),
        ("d5_fixed", "v", "#8172b2", "d=5, fixed V"),
        ("d3_aniso", "^", "#c44e52", "d=3, anisotropic $V_{pq}$"),
        ("d4_aniso", "^", "#c44e52", "d=4, anisotropic $V_{pq}$"),
    ]
    for key, m, c, lab in fams:
        rows = res.get(key, [])
        xs = [r["n"] for r in rows if r.get("kappa") is not None]
        ys = [r["kappa"] for r in rows if r.get("kappa") is not None]
        ls = "-" if "dose" in key or "fixed" in key else ":"
        ax.loglog(xs, ys, marker=m, ls=ls, lw=0.8, color=c, ms=5,
                  alpha=0.9, label=lab)
    # seed-8 replicate controls (open markers on the family colors)
    for ctr in res.get("seed_controls", []):
        col = {3: "#dd8452", 4: "#55a868", 5: "#8172b2"}.get(ctr["d"])
        if col and ctr.get("kappa") is not None:
            ax.loglog([ctr["n"]], [ctr["kappa"]], marker="o", ls="none",
                      mfc="none", mec=col, ms=6, mew=1.1, alpha=0.9)
    # d=2 analytic floor
    d2d = res.get("d2_dose", [])
    if d2d:
        xs = [r["n"] for r in d2d if r.get("kappa_floor") is not None]
        ys = [r["kappa_floor"] for r in d2d
              if r.get("kappa_floor") is not None]
        ax.loglog(xs, ys, "--", color="#4c72b0", lw=1.2,
                  label=r"d=2 floor $|\Delta|/(30\,\Omega)$")
    nn = np.logspace(2, 5.1, 40)
    ax.loglog(nn, np.sqrt(2.0 / nn), "k-.", lw=0.9,
              label=r"Haar $\sqrt{2/n}$")
    ax.set_xlabel(r"sector dimension $n=\binom{S+d-1}{d-1}$")
    ax.set_ylabel(r"$\kappa = \sigma_{\rm ETH}/\mathrm{std}_{\rm basis}$")
    ax.set_title("(a) Sector fluctuation ladders")
    ax.set_xlim(1e2, 1.5e5)
    ax.set_ylim(2e-5, 3)
    ax.legend(fontsize=6.5, loc="lower left", ncol=1)

    # (b) <r> vs n
    ax = axes[0, 1]
    for key, m, c, lab in fams:
        rows = res.get(key, [])
        xs = [r["n"] for r in rows if r.get("r_mean") is not None]
        ys = [r["r_mean"] for r in rows if r.get("r_mean") is not None]
        ax.semilogx(xs, ys, marker=m, ls="none", color=c, ms=5, label=lab)
    for ctr in res.get("seed_controls", []):
        col = {3: "#dd8452", 4: "#55a868", 5: "#8172b2"}.get(ctr["d"])
        if col and ctr.get("r_mean") is not None:
            ax.semilogx([ctr["n"]], [ctr["r_mean"]], marker="o",
                        ls="none", mfc="none", mec=col, ms=6, mew=1.1)
    ax.axhline(2 * np.log(2) - 1, color="k", ls="--", lw=0.9)
    ax.annotate("Poisson", xy=(200, 0.395), fontsize=7)
    ax.axhspan(0.5359 - 0.03, 0.5359 + 0.03, color="k", alpha=0.10)
    ax.axhline(0.5359, color="k", ls=":", lw=0.9)
    ax.annotate("GOE band", xy=(200, 0.548), fontsize=7)
    ax.annotate("picket fence ($d=2$)", xy=(200, 1.02), fontsize=7)
    ax.set_xlabel(r"sector dimension $n$")
    ax.set_ylabel(r"$\langle r\rangle$")
    ax.set_xlim(1e2, 1.5e5)
    ax.set_ylim(0.0, 1.12)
    ax.set_title("(b) Sector level statistics")
    ax.legend(fontsize=6.5, loc="center left")

    # (c) classical Lyapunov exponents
    ax = axes[1, 0]
    runs = cla["runs"]
    modes = ["onebody", "kinetic", "full"]
    labels = {"onebody": "one-body (matched-dose limit)",
              "kinetic": "kinetic (fixed-$V$ limit)",
              "full": "full symbol"}
    width = 0.25
    for i, mode in enumerate(modes):
        ds = [r["d"] for r in runs
              if r["mode"] == mode and "U" not in r]
        lams = [r["lambda_max"] for r in runs
                if r["mode"] == mode and "U" not in r]
        full_rows = [r for r in runs
                     if r["mode"] == mode and r.get("U") == 0.0]
        ds = [r["d"] for r in full_rows]
        lams = [r["lambda_max"] for r in full_rows]
        ax.bar(np.array(ds) + (i - 1) * width, np.maximum(lams, 1e-11),
               width=width, label=labels[mode], alpha=0.85)
    floor = max(r["lambda_max"] for r in runs if r["mode"] == "onebody")
    kin2 = [r["lambda_max"] for r in runs
            if r["mode"] == "kinetic" and r["d"] == 2]
    if kin2:
        floor = max(floor, kin2[0])
    ax.axhline(floor, color="k", ls="--", lw=0.9)
    ax.annotate("integrator floor ($d=2$, 1 d.o.f.)", xy=(2.05, floor * 1.5),
                fontsize=7)
    ax.set_yscale("log")
    ax.set_xticks([2, 3, 4])
    ax.set_xlabel(r"mode count $d$")
    ax.set_ylabel(r"$\lambda_{\max}$ (classical, $CP^{d-1}$)")
    ax.set_title("(c) Classical sector limits: Lyapunov")
    ax.legend(fontsize=6.5, loc="upper left")

    # (d) corner-state Lanczos betas
    ax = axes[1, 1]
    cor = res.get("corner_lanczos", {})
    for key, (c, lab) in {
            "d2_S128_V0.3000": ("#4c72b0", "d=2, $S$=128, $V$=0.3"),
            "d3_S40_V0.3000": ("#dd8452", "d=3, $S$=40, $V$=0.3"),
            "d4_S24_V0.3000": ("#55a868", "d=4, $S$=24, $V$=0.3")}.items():
        if key in cor:
            b = np.array(cor[key]["beta"])
            ax.plot(np.arange(1, len(b) + 1), b, color=c, lw=0.9,
                    label=lab)
    S = 128
    h12 = res.get("d2_h12", 0.0)
    C = 2 * h12 + 0.3 * S
    nn = np.arange(1, min(S, 400))
    ax.plot(nn, C * np.sqrt(nn * (S + 1 - nn)), "k--", lw=0.8,
            label=r"binomial $\beta_n=C\sqrt{n(S+1-n)}$")
    ax.set_xlabel(r"Lanczos step $n$")
    ax.set_ylabel(r"$\beta_n$")
    ax.set_title("(d) Corner-state Krylov growth")
    ax.legend(fontsize=6.5)

    fig.savefig(os.path.join(OUT, "fig_c4_msector.png"), dpi=170)
    print("saved", os.path.join(OUT, "fig_c4_msector.png"))


if __name__ == "__main__":
    main()
