#!/usr/bin/env python3
"""Matched-dose (VK^2 = 36) analysis and figures for the C4 kinetic completion.

Ladder legs:
  (a) window sigma_rel = sigma_ETH / std(a) vs D at fixed effective dose
      (d=3: D=3375..59319; d=4: D=4096..20736; dense full-spectrum values at
      D<=10^4) -- the strong-ETH scaling diagnostic.
  (b) |diag - micro| / K vs D at fixed dose: exact diagonal-ensemble values
      (D<=10^4) plus the D=20736 long-time trajectory average.
  (c) the D=20736 V=0.3 trajectory: observable, running time average, nested
      late-time window averages (diagonal-ensemble estimate), microcanonical
      line, and the early transient that coincides with it.
  (d) finite-T plateau vs exact diagonal ensemble at D<=10^4 (identity line).

Outputs: fig_c4_ladder.png, c4_ladder_results.json, summary.txt section.
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

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SCALED = "/home/z/my-project/download/pilot_c4_eth_scaled"
R_GOE, R_POIS = 0.5359, 2 * np.log(2) - 1
COL_3, COL_4, COL_D = "#1a6faa", "#6a3d9a", "#c2512d"
COL_K = "#2d7d46"

LADDER_3 = ["L36d3K14", "L36d3K18", "L36d3K20", "L36d3K22", "L36d3K26",
            "L36d3K28", "L36d3K30", "L36d3K34", "L36d3K38"]
LADDER_4 = ["L36d4K7", "L36d4K9", "L36d4K11"]
DENSE = ["L36d3K14", "L36d3K18", "L36d3K20", "L36d4K7", "L36d4K9"]
PAIRS = ["L36d3K14", "L36d3K18", "L36d4K7", "L36d4K9"]


def load(tag):
    p = os.path.join(SCALED, f"res_{tag}.json")
    r = json.load(open(p))
    npz = os.path.join(SCALED, f"win_{tag}.npz")
    if os.path.exists(npz) and r.get("sigma_eth") is not None:
        z = np.load(npz)
        r["sigma_rel"] = float(r["sigma_eth"] / np.std(z["a1"]))
    return r


def main():
    res = {t: load(t) for t in set(LADDER_3 + LADDER_4 + DENSE + PAIRS +
                                   ["d4K11V03x", "d4K11V03", "d3K28V005"])}
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.8), constrained_layout=True)
    ax_a, ax_b, ax_c, ax_d = axes.flat

    # ---------------- (a) sigma_rel vs D at matched dose ----------------
    for fam, col, mk, lbl in [(LADDER_3, COL_3, "o", r"$d=3$ window ($k=350$)"),
                              (LADDER_4, COL_4, "v", r"$d=4$ window ($k=350$)")]:
        xs = [res[t]["D"] for t in fam if res[t].get("sigma_rel")]
        ys = [res[t]["sigma_rel"] for t in fam if res[t].get("sigma_rel")]
        ax_a.plot(xs, ys, mk, ms=7, color=col, label=lbl)
        ax_a.plot(xs, ys, "-", lw=1, color=col, alpha=.45)
    xs = [res[t]["D"] for t in DENSE if res[t].get("dense")]
    ys = [res[t]["dense"]["sigma_rel_full"] for t in DENSE if res[t].get("dense")]
    ax_a.plot(xs, ys, "s", ms=7, mfc="none", mec=COL_D, ls="",
              label="dense, full spectrum ($D\\leq10^4$)")
    ax_a.set_xscale("log")
    ax_a.set_xlabel("truncation dimension $D$")
    ax_a.set_ylabel(r"$\sigma_{\mathrm{ETH}}\,/\,\mathrm{std}(a)$")
    ax_a.set_ylim(0.55, 1.05)
    ax_a.set_title("(a) eigenstate fluctuation ratio at fixed dose $VK^2\\!\\approx\\!36$:\n"
                   "no decay with $D$ (window tier flat at $0.95$--$0.98$)", fontsize=10)
    ax_a.legend(fontsize=8, loc="lower right")
    ax_a.annotate("$D$ span $\\times 17.6$\n(3375 $\\to$ 59319)", (6000, 0.99),
                  fontsize=7.5, color="#333")

    # ---------------- (b) |diag - micro|/K vs D at matched dose ----------------
    b3 = [(res[t]["D"], res[t]["dense"]["diag_vs_micro"] / res[t]["K"]) for t in DENSE[:3]]
    b4 = [(res[t]["D"], res[t]["dense"]["diag_vs_micro"] / res[t]["K"]) for t in DENSE[3:]]
    ev = res["d4K11V03x"]["evolution"]
    b4.append((res["d4K11V03x"]["D"], ev["diag_vs_micro"] / res["d4K11V03x"]["K"]))
    for fam, col, mk, lbl in [(b3, COL_3, "o", "$d=3$ (exact diag.)"),
                              (b4, COL_4, "v", "$d=4$ (exact / long-$T$)")]:
        xs, ys = zip(*fam)
        ax_b.plot(xs, ys, mk, ms=8, color=col, label=lbl)
        ax_b.plot(xs, ys, "-", lw=1, color=col, alpha=.45)
    old = res["d4K11V03"]["evolution"]
    ax_b.plot([20736], [old["diag_vs_micro"] / 11], "x", ms=9, color="#888",
              label="$T\\!\\leq\\!22.5$ transient (same config)")
    ax_b.set_xscale("log")
    ax_b.set_xlabel("truncation dimension $D$")
    ax_b.set_ylabel(r"$|\langle a\rangle_{\mathrm{diag}}-\langle a\rangle_{\mathrm{micro}}|\,/\,K$")
    ax_b.set_title("(b) diagonal ensemble vs microcanonical at fixed dose:\n"
                   "$O(1)$ gaps with no closing trend", fontsize=10)
    ax_b.legend(fontsize=8, loc="upper left")
    ax_b.annotate("the $T\\!\\leq\\!22.5$ estimate sits at the\nmicrocanonical value; the "
                   "$T\\!\\leq\\!300$\naverage does not", (20736, 0.0039),
                  xytext=(5200, 0.030), fontsize=7, color="#555",
                  arrowprops=dict(arrowstyle="->", lw=.7, color="#999"))

    # ---------------- (c) extended trajectory at D=20736 ----------------
    z = np.load(os.path.join(SCALED, "evol_d4K11V03x.npz"))
    tau, tr = z["tau"], z["trace"]
    ax_c.plot(tau, tr, "-", lw=.5, color="#9db8d2", label=r"$\langle \hat n_d\rangle(\tau)$")
    run = np.cumsum(tr) / (np.arange(len(tr)) + 1.0)
    ax_c.plot(tau, run, "-", lw=2, color=COL_K,
              label=r"running time average $\frac{1}{\tau}\!\int_0^\tau$")
    micro = ev["micro_d"]
    ax_c.axhline(micro, color="k", ls="--", lw=1.2,
                 label=f"microcanonical ({micro:.2f})")
    T = tau[-1]
    pw = ev["plateau_windows"]
    ax_c.plot([T / 2, T], [pw["T2"]] * 2, "-", lw=2.5, color=COL_K, alpha=.8)
    ax_c.plot([T / 4 * 3, T], [pw["T4"]] * 2, "-", lw=2, color=COL_K, alpha=.55)
    ax_c.plot([T * 7 / 8, T], [pw["T8"]] * 2, "-", lw=1.5, color=COL_K, alpha=.4)
    ax_c.annotate(r"nested late-time averages $\to$ diagonal ensemble "
                  f"$\\approx {pw['T4']:.2f}$",
                  (T * 0.42, pw["T4"] + 0.12), fontsize=8, color=COL_K)
    ax_c.axvspan(0, 22.5, color="#eee", alpha=.8)
    ax_c.annotate("early transient:\n$T\\!\\leq\\!22.5$ average\nlands near micro-\ncanonical "
                  "by coincidence", (30, 8.6), fontsize=7.5, color="#555")
    ax_c.set_xlim(0, T)
    ax_c.set_ylim(0, 11.5)
    ax_c.set_xlabel(r"time $\tau$ (lattice units)")
    ax_c.set_ylabel(r"$\hat n_d$ occupation")
    ax_c.set_title("(c) $d=4$, $K=11$, $D=20736$, $V=0.3$ ($VK^2\\!\\approx\\!36$): extended "
                   "Krylov\ntrajectory to $\\tau=300$ (9 wall-clock chunks, resumed)", fontsize=10)
    ax_c.legend(fontsize=8, loc="upper right")

    # ---------------- (d) plateau vs exact diagonal ensemble ----------------
    for t in PAIRS:
        r = res[t]
        dn, evo = r["dense"], r["evolution"]
        ax_d.plot([dn["diag_d"]], [evo["time_avg"]], "o", ms=9,
                  color=COL_3 if r["d"] == 3 else COL_4)
        ax_d.annotate(f"$D\\!=\\!{r['D']}$", (dn["diag_d"], evo["time_avg"]),
                      xytext=(8, 4), textcoords="offset points", fontsize=7)
    lims = [1.5, 9.5]
    ax_d.plot(lims, lims, "k--", lw=1, label="identity")
    ax_d.set_xlim(lims); ax_d.set_ylim(lims)
    ax_d.plot([], [], "o", ms=8, color=COL_3, label="$d=3$")
    ax_d.plot([], [], "o", ms=8, color=COL_4, label="$d=4$")
    ax_d.legend(fontsize=8, loc="upper left")
    ax_d.set_xlabel(r"exact diagonal ensemble $\langle a\rangle_{\mathrm{diag}}$")
    ax_d.set_ylabel(r"finite-$T$ plateau $\frac{1}{T}\!\int_{T/2}^{T}\!\langle a(t)\rangle dt$")
    ax_d.set_title("(d) plateau equals the diagonal ensemble\n"
                   r"($|\,\mathrm{plateau}-\mathrm{diag}\,|/K \leq 0.005$ at $D\leq10^4$)",
                   fontsize=10)

    fig.suptitle("C4 kinetic completion at matched dose $VK^2\\approx36$: window ladder and "
                 "diagonal-ensemble confirmation\n"
                 "windows certified by eigenpair residuals $\\leq 6\\times10^{-8}$; "
                 "trajectories by norm drift $\\leq 10^{-13}$", fontsize=11.5)
    out = os.path.join(SCALED, "fig_c4_ladder.png")
    fig.savefig(out, dpi=165)
    print("figure ->", out)

    # ---------------- machine-readable summary ----------------
    def ladder_row(t):
        r = res[t]
        return dict(tag=t, d=r["d"], K=r["K"], D=r["D"], V=r["V"],
                    r_mean=r.get("r_mean"), sigma_rel=r.get("sigma_rel"),
                    pr_over_D=r.get("pr_over_D"),
                    eig_resid_max=r.get("eig_resid_max"))

    def pair_row(t):
        r = res[t]
        dn, evo = r["dense"], r.get("evolution")
        row = dict(tag=t, d=r["d"], K=r["K"], D=r["D"], V=r["V"],
                   diag_d=dn["diag_d"], micro_d=dn["micro_d"],
                   diag_vs_micro_over_K=dn["diag_vs_micro"] / r["K"],
                   delta=dn["delta"], n_micro_states=dn["n_micro_states"],
                   sigma_rel_full=dn["sigma_rel_full"])
        if evo:
            row.update(tau=evo["tau_reached"], plateau=evo["time_avg"],
                       plateau_vs_diag_over_K=evo.get("plateau_vs_diag", float("nan")) / r["K"],
                       plateau_drift=evo["plateau_drift"])
        return row

    outj = dict(
        program="matched-dose ladder: VK^2 = 36 held fixed, truncation widened",
        dose_convention="effective (occupation-weighted) coupling ~ V*K^2; "
                        "V = 36/K^2 at every grid; seed 7, g0=1.5, h0=1.0",
        window_ladder_d3=[ladder_row(t) for t in LADDER_3],
        window_ladder_d4=[ladder_row(t) for t in LADDER_4],
        window_ladder_d4_infeasible=["L36d4K13", "L36d4K15", "L36d4K17"],
        dense_pairs=[pair_row(t) for t in DENSE],
        d4K11_V03_extended=dict(
            D=20736, V=0.3, tau=ev["tau_reached"],
            running_time_average=ev["time_avg"],
            plateau_windows=ev["plateau_windows"],
            plateau_drift=ev["plateau_drift"], resid_fluct=ev["resid_fluct"],
            micro_d=ev["micro_d"], delta=ev["delta"],
            n_micro_states=ev["n_micro_states"],
            diag_estimate=ev["plateau_windows"]["T4"],
            transient_T22=dict(plateau=res["d4K11V03"]["evolution"]["time_avg"],
                               tau=res["d4K11V03"]["evolution"]["tau_reached"]),
        ),
        verdict=dict(
            sigma_rel="flat: 0.9486-0.9837 (window, d=3, D=3375-59319), "
                      "0.9478-0.9712 (window, d=4, D=4096-20736), "
                      "0.68-0.83 (dense full spectrum, D<=10^4); no downward "
                      "trend at fixed dose -- the strong-ETH leg of C4 has no "
                      "positive evidence at accessible scales",
            diag_vs_micro="O(1) at fixed dose: d=3 stable ~0.87 absolute "
                          "(0.043-0.059 of K); d=4 grows 0.040 -> 0.061 -> 0.092 "
                          "of K across D=4096-20736; no closing trend",
            plateau_is_diag="verified exactly at D<=10^4 "
                            "(|plateau-diag|/K = 0.0003-0.0046, within the "
                            "nested-window drift); at D=20736 the T<=22.5 "
                            "average (3.394) was a transient that coincides "
                            "with the microcanonical value (3.351); the "
                            "extended trajectory's nested averages saturate "
                            "at 4.40 +/- 0.03, which is the diagonal ensemble",
            relaxation="fast initial decay (11 -> 3.5 by tau~20) followed by a "
                       "slow secular tail (still +0.03 per 35 tau at tau=300); "
                       "the relaxation spectrum is broad, consistent with the "
                       "occupation-weighted coupling structure",
        ),
    )
    with open(os.path.join(SCALED, "c4_ladder_results.json"), "w") as f:
        json.dump(outj, f, indent=1, default=float)
    print("json ->", os.path.join(SCALED, "c4_ladder_results.json"))

    with open(os.path.join(SCALED, "summary.txt"), "a") as f:
        f.write("\n\n=== MATCHED-DOSE LADDER (VK^2 = 36) ===\n")
        f.write("window ladder: sigma_rel flat 0.95-0.98 across D=3375-59319 (d=3) "
                "and D=4096-20736 (d=4); PR/D rises 0.087->0.153 with D\n")
        f.write("dense pairs (D<=1e4): |plateau - diag|/K = 0.0003-0.0046 "
                "(plateau IS the diagonal ensemble)\n")
        f.write("diag vs micro at fixed dose: d=3 ~0.87 absolute (stable); d=4 grows "
                "0.040->0.092 of K (D=4096->20736); no closing trend\n")
        f.write("d4K11 V=0.3 extended to tau=300: running avg 4.368, nested windows "
                "saturate ~4.40 (diagonal ensemble); T<=22.5 average 3.394 near "
                "micro 3.351 was a transient\n")
    print("summary.txt appended")


if __name__ == "__main__":
    main()
