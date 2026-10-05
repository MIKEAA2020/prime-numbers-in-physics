#!/usr/bin/env python3
"""
Figures for the C4 KINETIC completion program (density-assisted hopping)
+ the --sigma-quantile sweep.  Companion to fig_c4_scaled.png (the baseline
scaled program); reads the same res_*.json / win_*.npz / evol_*.npz files.

Panels:
  (a) completion dose-response, <r> vs coupling at D ~ 2x10^4:
      diagonal quartic (U) vs kinetic (V) families, shared V=0 anchor
  (b) PR/D vs coupling (log): quartic localizes 10^2-10^3 x faster
  (c) <r> vs sigma-quantile: weak coupling is window-placement-dependent
      (0.42-0.56, non-monotone, DOS structure); generic is flat GOE
  (d) equilibration |diag-micro|/K: kinetic V=0.3 dips 25x below every
      other family at D~2x10^4; Krylov horizons annotated

Kinetic term: H_kin = V sum_{p<q} (n_p+n_q)(a_p^dag a_q + h.c.)
  -- validated to machine precision (c4_kinetic_selftest.py)
  -- occupation-weighted: effective dose is V*K^2 (the d3K28 V=0.3 point
     is STRONG dose, V*K^2 ~ 235, and localizes; d4K11 V=0.3 is V*K^2 ~ 36)
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
try:
    fm.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
except Exception:
    pass
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SCALED = "/home/z/my-project/download/pilot_c4_eth_scaled"
R_GOE, R_POIS = 0.5359, 2 * np.log(2) - 1
COL_G, COL_U, COL_W, COL_V = "#1a6faa", "#c2512d", "#7a7a7a", "#6a3d9a"


def load(tag):
    p = os.path.join(SCALED, f"res_{tag}.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))
    npz = os.path.join(SCALED, f"win_{tag}.npz")
    if os.path.exists(npz) and "r_mean" in r:
        z = np.load(npz)
        if r.get("sigma_eth") is not None:
            r["sigma_rel"] = float(r["sigma_eth"] / np.std(z["a1"]))
    return r


def main():
    res = {t: load(t) for t in [
        # dose families on the d4K11 platform (D = 20736, seed 7)
        "d4K11V0", "d4K11V01", "d4K11V03", "d4K11V10",
        "d4K11U05", "d4K11U",
        # scaling / directions at V = 0.3 (and matched-dose 3D)
        "d4K9V03", "d6K4V03", "d3K28V03", "d3K28V005",
        # evolve family
        "d4K12V03", "d4K14V03", "d4K17V03",
        # bare baselines + quartic evolves for panel (d)
        "d4K11", "d4K12", "d4K14", "d4K17", "d3K28",
        "d4K12U", "d4K14U", "d3K28weak",
        # sweep
        "d3K28wq002", "d3K28wq010", "d3K28wq015", "d3K28wq025",
        "d3K28wq075", "d3K28wq090", "d3K28wq098", "d3K28weak", "d3K28weakedge",
        "d3K28q005", "d3K28q095", "d4K11weak",
    ]}
    res = {t: r for t, r in res.items() if r}

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.6), constrained_layout=True)
    ax_r, ax_p, ax_q, ax_d = axes.flat

    # ---------------- (a) dose-response: <r> ----------------
    fam_v = [(0.0, "d4K11V0"), (0.1, "d4K11V01"), (0.3, "d4K11V03"), (1.0, "d4K11V10")]
    fam_u = [(0.0, "d4K11V0"), (0.5, "d4K11U05"), (2.0, "d4K11U")]
    for fam, col, mk, lbl in [(fam_v, COL_V, "v", "kinetic $V$ (density-assisted hop)"),
                              (fam_u, COL_U, "^", "diagonal quartic $U$")]:
        xs = [x for x, t in fam if res.get(t) and "r_mean" in res[t]]
        ys = [res[t]["r_mean"] for x, t in fam if res.get(t) and "r_mean" in res[t]]
        es = [res[t].get("r_sem", 0) for x, t in fam if res.get(t) and "r_mean" in res[t]]
        ax_r.errorbar(xs, ys, yerr=es, fmt=mk, ms=8, color=col, capsize=3,
                      ecolor=col, label=lbl)
        ax_r.plot(xs, ys, "-", lw=1, color=col, alpha=.5)
    ax_r.axhline(R_GOE, color="k", ls="--", lw=1)
    ax_r.axhline(R_POIS, color="k", ls=":", lw=1)
    ax_r.text(1.55, R_GOE + .006, "GOE", fontsize=8)
    ax_r.text(1.55, R_POIS - .022, "Poisson", fontsize=8)
    ax_r.annotate("V=0 anchor: $\\langle r\\rangle$=0.581\n(first window at d4K11;\ndiag-pivot LU)",
                  (0.0, 0.581), xytext=(0.25, 0.605), fontsize=7, color="#333")
    ax_r.annotate("strong dose localizes\n(V$K^2\\gtrsim$80)", (1.0, 0.4122),
                  xytext=(0.55, 0.355), fontsize=7, color=COL_V,
                  arrowprops=dict(arrowstyle="->", lw=.8, color=COL_V))
    ax_r.set_xlabel(r"completion coupling ($V$ kinetic / $U$ quartic)")
    ax_r.set_ylabel(r"level-spacing ratio $\langle r\rangle$")
    ax_r.set_title("(a) dose-response at $D=20736$ (d4K11, seed 7):\n"
                   "kinetic holds GOE at intermediate dose", fontsize=10)
    ax_r.legend(fontsize=8, loc="lower left")
    ax_r.set_ylim(0.32, 0.64)

    # ---------------- (b) dose-response: PR/D ----------------
    for fam, col, mk in [(fam_v, COL_V, "v"), (fam_u, COL_U, "^")]:
        xs = [x for x, t in fam if res.get(t) and "pr_over_D" in res[t]]
        ys = [res[t]["pr_over_D"] for x, t in fam if res.get(t) and "pr_over_D" in res[t]]
        ax_p.plot(xs, ys, mk, ms=8, color=col)
        ax_p.plot(xs, ys, "-", lw=1, color=col, alpha=.5)
    ax_p.set_yscale("log")
    ax_p.set_xlabel(r"completion coupling ($V$ kinetic / $U$ quartic)")
    ax_p.set_ylabel("mean PR / D of window eigenstates")
    ax_p.set_title("(b) localization dose-response:\n"
                   "quartic collapses $10^{2}$--$10^{3}\\times$ faster than kinetic", fontsize=10)
    ax_p.annotate("U=2: PR/D $=1.1\\times10^{-3}$", (2.0, 0.0011), xytext=(1.0, 0.004),
                  fontsize=7, color=COL_U,
                  arrowprops=dict(arrowstyle="->", lw=.7, color=COL_U))
    ax_p.annotate("V=1: PR/D $=4.6\\times10^{-2}$", (1.0, 0.0455), xytext=(0.45, 0.10),
                  fontsize=7, color=COL_V,
                  arrowprops=dict(arrowstyle="->", lw=.7, color=COL_V))

    # ---------------- (c) sigma-quantile sweep ----------------
    sweep_weak = [(0.02, "d3K28wq002"), (0.10, "d3K28wq010"), (0.15, "d3K28wq015"),
                  (0.25, "d3K28wq025"), (0.50, "d3K28weak"), (0.75, "d3K28wq075"),
                  (0.90, "d3K28wq090"), (0.98, "d3K28wq098")]
    sweep_gen = [(0.05, "d3K28q005"), (0.50, "d3K28"), (0.95, "d3K28q095")]
    for pts, col, mk, lbl in [(sweep_weak, COL_W, "s", "weak ($g_0$=0.05, $h_0$=0.03), $D$=24389"),
                              (sweep_gen, COL_G, "o", "generic ($g_0$=1.5, $h_0$=1.0), $D$=24389")]:
        xs = [q for q, t in pts if res.get(t) and "r_mean" in res[t]]
        ys = [res[t]["r_mean"] for q, t in pts if res.get(t) and "r_mean" in res[t]]
        es = [res[t].get("r_sem", 0) for q, t in pts if res.get(t) and "r_mean" in res[t]]
        ax_q.errorbar(xs, ys, yerr=es, fmt=mk, ms=7, color=col, capsize=3,
                      ecolor=col, label=lbl)
        ax_q.plot(xs, ys, "-", lw=1, color=col, alpha=.45)
    if res.get("d4K11weak", {}).get("r_mean"):
        ax_q.plot([0.5], [res["d4K11weak"]["r_mean"]], "D", ms=8, color="#b08ad0",
                  label="weak, $d$=4, $D$=20736 (median)")
    ax_q.axhline(R_GOE, color="k", ls="--", lw=1)
    ax_q.axhline(R_POIS, color="k", ls=":", lw=1)
    ax_q.text(0.015, R_GOE + .006, "GOE", fontsize=8)
    ax_q.text(0.03, R_POIS - .028, "Poisson", fontsize=8)
    ax_q.annotate("q=0.15 dip reproduced\nexactly on re-run\n(DOS cluster gap)",
                  (0.15, 0.4361), xytext=(0.18, 0.398), fontsize=6.5, color="#555",
                  arrowprops=dict(arrowstyle="->", lw=.6, color="#999"))
    ax_q.set_xlabel(r"window placement $\sigma$-quantile of the DOS")
    ax_q.set_ylabel(r"$\langle r\rangle$")
    ax_q.set_title("(c) sharpened protocol note: weak-coupling $\\langle r\\rangle$ is "
                   "window-placement-dependent\n(0.42--0.56, non-monotone); generic is flat GOE",
                   fontsize=10)
    ax_q.legend(fontsize=7.5, loc="upper right")
    ax_q.set_ylim(0.36, 0.62)

    # ---------------- (d) equilibration |dev|/K ----------------
    kin_scale = [("d4K11V03", 20736), ("d4K12V03", 28561), ("d4K14V03", 50625),
                 ("d4K17V03", 104976)]
    bare_scale = [("d4K11", 20736), ("d4K12", 28561), ("d4K14", 50625), ("d4K17", 104976)]
    quartic_scale = [("d4K12U", 28561), ("d4K14U", 50625)]
    for fam, col, mk, lbl in [
            (kin_scale, COL_V, "v", "kinetic $V$=0.3"),
            (bare_scale, COL_G, "o", "bare ($U$=$V$=0)"),
            (quartic_scale, COL_U, "^", "quartic $U$=2")]:
        xs, ys, taus = [], [], []
        for t, D in fam:
            r = res.get(t)
            if r and r.get("evolution"):
                ev = r["evolution"]
                xs.append(D); ys.append(ev["diag_vs_micro"] / r["K"])
                taus.append(ev.get("tau_reached", 0))
        ax_d.plot(xs, ys, mk, ms=8, color=col, label=lbl)
        ax_d.plot(xs, ys, "-", lw=1, color=col, alpha=.45)
        if col == COL_V:
            for x, y, tau in zip(xs, ys, taus):
                ax_d.annotate(f"$\\tau$={tau:.0f}", (x, y), xytext=(4, -11),
                              textcoords="offset points", fontsize=6.5, color=COL_V)
    # kinetic dose points at D=20736
    for tag, v, lbl in [("d4K11V01", 0.1, "V=0.1"), ("d4K11V10", 1.0, "V=1.0")]:
        r = res.get(tag)
        if r and r.get("evolution"):
            ax_d.plot([20736], [r["evolution"]["diag_vs_micro"] / r["K"]], "v",
                      ms=7, color=COL_V, mfc="none", mec=COL_V)
            ax_d.annotate(f"{lbl} ($\\tau$={r['evolution']['tau_reached']:.0f})",
                          (20736, r["evolution"]["diag_vs_micro"] / r["K"]),
                          xytext=(6, 4), textcoords="offset points", fontsize=6.5,
                          color=COL_V)
    r = res.get("d3K28weak")
    if r and r.get("evolution"):
        ax_d.plot([24389], [r["evolution"]["diag_vs_micro"] / r["K"]], "s",
                  ms=7, color=COL_W, label="weak control")
    r = res.get("d3K28V03")
    if r and r.get("evolution"):
        ax_d.plot([24389], [r["evolution"]["diag_vs_micro"] / r["K"]], "x",
                  ms=9, color="#3d1f5c", label="kinetic V=0.3, $VK^2\\!\\approx\\!235$ (localized)")
    ax_d.set_xscale("log"); ax_d.set_yscale("log")
    ax_d.set_xlabel("truncation dimension $D$")
    ax_d.set_ylabel(r"$|$diag ensemble $-$ microcanonical$|\,/\,K$")
    ax_d.set_title("(d) kinetic $V\\!\\approx\\!0.3$ ($VK^2\\!\\approx\\!36$): the only completion "
                   "that\nequilibrates ($25\\times$ below bare); Krylov horizons annotated",
                   fontsize=10)
    ax_d.legend(fontsize=7.5, loc="upper right")

    handles = [
        mlines.Line2D([], [], color=COL_V, marker="v", ls="", label="kinetic $V$"),
        mlines.Line2D([], [], color=COL_U, marker="^", ls="", label="quartic $U$"),
        mlines.Line2D([], [], color=COL_G, marker="o", ls="", label="bare / generic"),
        mlines.Line2D([], [], color=COL_W, marker="s", ls="", label="weak control"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, 0.965))
    fig.suptitle("C4 kinetic completion (density-assisted hopping): dose-response, equilibration, "
                 "and the $\\sigma$-quantile protocol\n"
                 "all windows certified: eigenpair residuals $\\leq 1.2\\times10^{-7}$ "
                 "(diag-pivot shift-invert)", fontsize=11.5, y=1.0)
    out = os.path.join(SCALED, "fig_c4_kinetic.png")
    fig.savefig(out, dpi=165)
    print("figure ->", out)

    # ---- machine-readable summary of the new program ----
    def row(tag):
        r = res.get(tag)
        if not r:
            return None
        ev = r.get("evolution")
        d = dict(tag=tag, D=r["D"], d=r["d"], K=r["K"], U=r.get("U"), V=r.get("V"),
                 g0=r.get("g0"), h0=r.get("h0"),
                 r_mean=r.get("r_mean"), sigma_rel=r.get("sigma_rel"),
                 pr_over_D=r.get("pr_over_D"),
                 sigma_quantile=r.get("sigma_quantile"),
                 eig_resid_max=r.get("eig_resid_max"), pivot=r.get("pivot"))
        if ev:
            d.update(dev_over_K=ev["diag_vs_micro"] / r["K"],
                     tau=ev.get("tau_reached"), truncated=ev.get("truncated"),
                     resid_fluct=ev.get("resid_fluct"))
        return d

    outj = dict(
        kinetic_term=r"H_kin = V sum_{p<q} (n_p + n_q)(a_p^dag a_q + h.c.)",
        validation="c4_kinetic_selftest.py: identity vs first-principles dense 1e-15, "
                   "Hermitian, [H_kin, N_tot]=0, non-quadratic effective coefficients",
        effective_dose="coupling is occupation-weighted: effective dose ~ V*K^2 "
                       "(V=0.3 at K=11 is mild/intermediate; at K=28 it is strong -> localizes)",
        pivot_note="diag_pivot_thresh=0 (diagonal pivoting) rescues shift-invert for the "
                   "V-family: generic d3K28 splu 257s -> 3s; eigenpair residuals <= 1.2e-7 "
                   "certify every window; d4K10 cross-check: auto 0.5157 vs diag 0.5134",
        dose_family_d4K11=[row("d4K11V0"), row("d4K11V01"), row("d4K11V03"),
                           row("d4K11V10")],
        quartic_family_d4K11=[row("d4K11U05"), row("d4K11U")],
        scaling_V03=[row("d4K9V03"), row("d6K4V03"), row("d4K11V03"),
                     row("d3K28V03"), row("d3K28V005")],
        evolve_family=[row(t) for t in ["d4K11V01", "d4K11V03", "d4K11V10",
                                        "d3K28V03", "d4K12V03", "d4K14V03", "d4K17V03"]],
        sweep_weak=[row(t) for _, t in sweep_weak],
        sweep_generic=[row(t) for _, t in sweep_gen],
        sweep_robustness=[row("d4K11weak")],
        verdict=dict(
            sigma_rel="flat 0.94-0.99 at every kinetic dose and scale -- strong-ETH "
                      "eigenstate fluctuation does NOT decay at accessible scales",
            equilibration="kinetic V=0.3 (VK^2~36) at D=20736: |diag-micro|/K = 0.0039 "
                          "(bare 0.10, quartic 0.81), settled plateau, resid 0.064, "
                          "tau<=22 horizon-limited; V=0.1 (tau<=63) plateaus AWAY from "
                          "micro (0.178) -- equilibration is a dose phenomenon",
            localization="PR/D: kinetic monotone down in V (0.24->0.22->0.14->0.05) but "
                         "10-100x above quartic (0.001-0.029); strong dose (V=1 or "
                         "VK^2>~80) localizes with Poisson statistics",
            level_statistics="kinetic V<=0.3: GOE-class (0.49-0.52); V=1: 0.41; "
                             "3D matched-dose V=0.05: 0.474",
            sweep="weak <r> spans 0.42-0.56 across sigma-quantiles (non-monotone, "
                  "q=0.15 dip reproduced exactly); generic flat 0.505-0.514; "
                  "median weak value is d-dependent (d=3: 0.527, d=4: 0.441)",
        ),
    )
    with open(os.path.join(SCALED, "c4_kinetic_results.json"), "w") as f:
        json.dump(outj, f, indent=1, default=float)
    print("json ->", os.path.join(SCALED, "c4_kinetic_results.json"))


if __name__ == "__main__":
    main()
