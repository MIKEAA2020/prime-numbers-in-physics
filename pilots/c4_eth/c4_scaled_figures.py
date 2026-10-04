#!/usr/bin/env python3
"""
Merge + figures for the scaled C4 ETH scan (download/pilot_c4_eth_scaled/).

Panels:
  (a) <r> vs D               -- C5 proxy (GOE at generic coupling)
  (b) sigma_rel vs D         -- normalized ETH fluctuation (no decay)
  (c) PR/D vs D              -- delocalization without ergodicity
  (d) |diag-micro| vs D      -- C4 equilibration memory (Krylov tier, to ~1e5)
  (e) U dose-response        -- quartic completion localizes monotonically
  (f) wall time vs D         -- dense vs sparse cost (laptop-scale)

Protocol notes:
  * sigma_rel = sigma_ETH / std(a_j) with a_j = <E_j|n_1|E_j> in the interior
    window -- protocol-independent (pilot used full-spectrum middle 50%).
  * evolution: Krylov restarts from |K e_d>; diag-ensemble proxy = time average
    over the second half of the trace; micro = adaptive window at E0.
    Truncated flags mean the wall-clock deadline cut the trace (tau_reached
    recorded); K-relative deviation |dev|/K is also reported.
"""
import glob
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
PILOT = "/home/z/my-project/download/pilot_c4_eth"
R_GOE, R_POIS = 0.5359, 2 * np.log(2) - 1

GENERIC = ["d4K7sp", "d6K3sp", "d4K8", "d3K25", "d4K10", "d4K9", "d6K4",
           "d3K28", "d4K12", "d3K35", "d6K5", "d4K14", "d5K8", "d3K45",
           "d4K16", "d4K17"]
U_CONF = ["d4K9U", "d4K11U", "d4K11U05", "d4K12U", "d4K14U"]
WEAK = ["d3K28weak", "d3K28weakedge"]
EVOLVE_ONLY = {"d5K6", "d4K11"}   # window failed (SuperLU C-level alloc)
ALL = GENERIC + U_CONF + WEAK + sorted(EVOLVE_ONLY)


def load(tag):
    p = os.path.join(SCALED, f"res_{tag}.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))
    npz = os.path.join(SCALED, f"win_{tag}.npz")
    if os.path.exists(npz) and "r_mean" in r:
        z = np.load(npz)
        a = z["a1"]
        if r.get("sigma_eth") is not None:
            r["sigma_rel"] = float(r["sigma_eth"] / np.std(a))
    return r


def pilot_norm_sigma():
    out = {}
    for p in glob.glob(os.path.join(PILOT, "data_*.npz")):
        tag = os.path.basename(p)[5:-4]
        try:
            out[tag] = float(np.std(np.load(p)["eth_a"]))
        except Exception:
            pass
    return out


def main():
    results = {t: load(t) for t in ALL}
    results = {t: r for t, r in results.items() if r}
    pil_norm = pilot_norm_sigma()
    pilot = json.load(open(os.path.join(PILOT, "c4_results.json")))
    try:
        pil_int = json.load(open(os.path.join(PILOT, "c4_results_interacting.json")))
    except Exception:
        pil_int = []
    pil_rows = list(pilot) + list(pil_int)

    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9), constrained_layout=True)
    ax_r, ax_s, ax_p, ax_d, ax_u, ax_t = axes.flat
    col_g, col_u, col_w = "#1a6faa", "#c2512d", "#7a7a7a"

    def grp(tag):
        if tag in U_CONF: return "u"
        if tag in WEAK: return "w"
        return "g"

    # (a) ratio statistic vs D
    for r in pil_rows:
        if r["tag"].endswith("weak"):
            ax_r.plot(r["D"], r["r_mean"], "s", ms=5, color=col_w, alpha=.8)
        elif "U" in r["tag"]:
            ax_r.plot(r["D"], r["r_mean"], "^", ms=6, color=col_u, alpha=.8)
        else:
            ax_r.plot(r["D"], r["r_mean"], "s", ms=5, color=col_g, alpha=.55)
    for tag, r in results.items():
        if "r_mean" not in r:
            continue
        c = {"g": col_g, "u": col_u, "w": col_w}[grp(tag)]
        mk = {"g": "o", "u": "^", "w": "s"}[grp(tag)]
        ax_r.errorbar(r["D"], r["r_mean"], yerr=r.get("r_sem", 0), fmt=mk, ms=6,
                      color=c, ecolor=c, capsize=2)
    ax_r.axhline(R_GOE, color="k", ls="--", lw=1)
    ax_r.axhline(R_POIS, color="k", ls=":", lw=1)
    ax_r.text(700, R_GOE + .008, "GOE 0.536", fontsize=8)
    ax_r.text(700, R_POIS - .025, "Poisson 0.386", fontsize=8)
    ax_r.set_xscale("log")
    ax_r.set_xlabel("truncation dimension D")
    ax_r.set_ylabel(r"level-spacing ratio $\langle r\rangle$")
    ax_r.set_title("(a) C5 proxy: GOE at generic coupling, all window scales", fontsize=10)

    # (b) normalized ETH fluctuation vs D
    for tag, r in results.items():
        if "sigma_rel" in r:
            c = {"g": col_g, "u": col_u, "w": col_w}[grp(tag)]
            mk = {"g": "o", "u": "^", "w": "s"}[grp(tag)]
            ax_s.plot(r["D"], r["sigma_rel"], mk, ms=6, color=c)
    for r in pil_rows:
        t = r["tag"]
        if t in pil_norm and r.get("sigma_eth"):
            c = col_w if t.endswith("weak") else (col_u if "U" in t else col_g)
            ax_s.plot(r["D"], r["sigma_eth"] / pil_norm[t], "s", ms=5, color=c, alpha=.55)
    ax_s.set_xscale("log")
    ax_s.set_xlabel("truncation dimension D")
    ax_s.set_ylabel(r"$\sigma_{\mathrm{ETH}}\,/\,\mathrm{std}(a_j)$")
    ax_s.set_title("(b) C4 ETH fluctuation: flat in D (no decay, all couplings)", fontsize=10)
    ax_s.set_ylim(0, 1.6)

    # (c) participation ratio
    for tag, r in results.items():
        if "pr_over_D" in r:
            c = {"g": col_g, "u": col_u, "w": col_w}[grp(tag)]
            mk = {"g": "o", "u": "^", "w": "s"}[grp(tag)]
            ax_p.plot(r["D"], r["pr_over_D"], mk, ms=6, color=c)
    for r in pil_rows:
        if r.get("pr_over_D"):
            c = col_w if r["tag"].endswith("weak") else (col_u if "U" in r["tag"] else col_g)
            ax_p.plot(r["D"], r["pr_over_D"], "s", ms=5, color=c, alpha=.55)
    ax_p.set_xscale("log"); ax_p.set_yscale("log")
    ax_p.set_xlabel("truncation dimension D")
    ax_p.set_ylabel("mean PR / D of window eigenstates")
    ax_p.set_title("(c) delocalization: generic ~0.2; weak/quartic ~$10^{-4}$", fontsize=10)

    # (d) equilibration memory |diag - micro| vs D (Krylov tier)
    for tag, r in results.items():
        ev = r.get("evolution")
        if not ev:
            continue
        c = col_w if tag in WEAK else (col_u if tag in U_CONF else col_g)
        mk = {"g": "o", "u": "^", "w": "s"}[grp(tag)] if grp(tag) != "g" else "o"
        if tag in WEAK: mk = "s"
        trunc = ev.get("truncated", False)
        ax_d.errorbar(r["D"], ev["diag_vs_micro"], yerr=ev.get("resid_fluct", 0),
                      fmt=mk, ms=6, color=c, ecolor=c, capsize=2,
                      mfc=("none" if trunc else c), mec=c)
    for r in pil_rows:
        if r.get("evolution"):
            dev = r["evolution"].get("dev_diag_vs_micro",
                                     r["evolution"].get("diag_vs_micro"))
            ax_d.errorbar(r["D"], dev,
                          yerr=r["evolution"].get("resid_fluct", 0),
                          fmt="s", ms=5, color=col_g, alpha=.5, capsize=2)
    ax_d.set_xscale("log")
    ax_d.set_xlabel("truncation dimension D")
    ax_d.set_ylabel(r"$|$diag ensemble $-$ microcanonical$|$")
    ax_d.set_title("(d) C4 equilibration: O(1) memory retained up to $D\\approx10^5$", fontsize=10)
    ax_d.annotate("weak: frozen (no equilibration)", (2.4e4, 15.0), fontsize=7,
                  color=col_w, ha="center")

    # (e) quartic dose-response at D ~ 2e4 (pilot family at 3125 for contrast)
    fam = [("d4K11U05", 0.5), ("d4K11U", 2.0)]
    ax_u.plot([0.0], [results["d3K28"]["r_mean"]], "o", ms=7, color=col_g)
    ax_u.annotate("U=0 (d3K28, D=24389)", (0.02, results["d3K28"]["r_mean"] + .006),
                  fontsize=7, color=col_g)
    for tag, uval in fam:
        r = results[tag]
        ax_u.plot([uval], [r["r_mean"]], "^", ms=7, color=col_u)
    ax_u.plot([0.5, 2.0], [results["d4K11U05"]["r_mean"], results["d4K11U"]["r_mean"]],
              "-", lw=1, color=col_u, alpha=.6)
    for r in pil_rows:
        if "U" in r["tag"] and r["tag"][0] == "d" and "U" in r["tag"]:
            uval = float(r["tag"].split("U")[1]) / 10.0
            ax_u.plot([uval], [r["r_mean"]], "^", ms=4, color="#e0a090", alpha=.8)
    ax_u.axhline(R_GOE, color="k", ls="--", lw=1)
    ax_u.axhline(R_POIS, color="k", ls=":", lw=1)
    ax_u.set_xlabel(r"quartic coupling $U$  ($U\sum_{p<q}\hat n_p\hat n_q$)")
    ax_u.set_ylabel(r"$\langle r\rangle$")
    ax_u.set_title("(e) quartic completion: monotone localization\n(scaled $D\\approx2\\times10^4$; pale: pilot $D=3125$)", fontsize=10)

    # (f) cost: dense vs sparse
    for r in pil_rows:
        if r.get("t_eigh_s") and r["D"] <= 4200:
            ax_t.plot(r["D"], r["t_eigh_s"], "s", ms=5, color="#444", alpha=.6)
    for tag, r in results.items():
        tot = 0.0
        if r.get("t_splu"): tot += r["t_splu"]
        if r.get("t_eigsh"): tot += r["t_eigsh"]
        if r.get("evolution", {}).get("t_evolve"): tot += r["evolution"]["t_evolve"]
        if tot > 0:
            c = col_w if tag in WEAK else (col_u if tag in U_CONF else col_g)
            ax_t.plot(r["D"], tot, "o", ms=6, color=c)
    ds = np.array([600.0, 1.2e5])
    ax_t.plot(ds, 8.0 * (ds / 4096.0) ** 2.37, "k--", lw=.8)
    ax_t.text(950, 700, "dense $D^{2.4}$ extrapolation", fontsize=7, rotation=13)
    ax_t.text(2.5e4, 350, "LU ceiling\n(window tier)", fontsize=7, color="#1a6faa")
    ax_t.set_xscale("log"); ax_t.set_yscale("log")
    ax_t.set_xlabel("truncation dimension D")
    ax_t.set_ylabel("wall time per configuration (s)")
    ax_t.set_title("(f) cost: sparse tiers keep $D\\sim10^5$ laptop-scale", fontsize=10)

    handles = [
        mlines.Line2D([], [], color=col_g, marker="o", ls="", label="generic $H_{tot}^{(U=0)}$"),
        mlines.Line2D([], [], color=col_u, marker="^", ls="", label="quartic completion"),
        mlines.Line2D([], [], color=col_w, marker="s", ls="", label="weak coupling"),
        mlines.Line2D([], [], color="#444", marker="s", ls="", ms=4, label="dense pilot"),
        mlines.Line2D([], [], color="k", marker="o", ls="", mfc="none",
                      label="Krylov trace truncated by deadline"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=9)
    fig.suptitle("C4 scaled attack: ETH on the prime lattice, $D \\leq 10^5$ "
                 "(sparse interior eigensolvers + Krylov equilibration; 4 GB / 2 cores)",
                 fontsize=12)
    fig.savefig(os.path.join(SCALED, "fig_c4_scaled.png"), dpi=165)
    print("figure ->", os.path.join(SCALED, "fig_c4_scaled.png"))

    out = dict(
        protocol=dict(
            window="k levels nearest sigma=quantile(eps) (default median), shift-invert Lanczos",
            sigma_eth="RMS within-quantile-bin std of a_j=<E_j|n_1|E_j> (interior window)",
            sigma_rel="sigma_ETH / std(a_j) -- protocol-independent",
            evolution="restarted complex Lanczos from |K e_d>; diag proxy = 2nd-half time average; micro = adaptive window at E0 (>=300 states)",
            pilot_note="dense pilot used middle 50% of full spectrum; trends are the datum",
            weakedge="d3K28weakedge uses sigma at the 15% quantile (sparse edge of the DOS)",
        ),
        results=results,
    )
    with open(os.path.join(SCALED, "c4_scaled_results.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)

    # summary text
    lines = [f"{'tag':16s} {'D':>7s} {'tier':>9s} {'<r>':>7s} {'sig_rel':>8s} {'PR/D':>8s} "
             f"{'|dev|':>7s} {'|dev|/K':>8s} {'resid':>7s} {'tau':>5s} {'t_tot':>7s} {'rss':>6s}"]
    for tag in ALL:
        r = results.get(tag)
        if not r:
            continue
        ev = r.get("evolution")
        tot = (r.get("t_splu") or 0) + (r.get("t_eigsh") or 0) + \
              ((ev or {}).get("t_evolve") or 0)
        def s(v, fmt):
            return (fmt % v) if v is not None else "-"
        r_mean = r["r_mean"] if "r_mean" in r else None
        sig = r["sigma_rel"] if "sigma_rel" in r else None
        pr = r["pr_over_D"] if "pr_over_D" in r else None
        dev = ev["diag_vs_micro"] if ev else None
        devk = (ev["diag_vs_micro"] / r["K"]) if ev else None
        res = ev["resid_fluct"] if ev else None
        tau = ev["tau_reached"] if ev else None
        lines.append(
            f"{tag:16s} {r['D']:7d} {('window' if 'r_mean' in r else 'evolve'):>9s} "
            f"{s(r_mean, '%.4f'):>7s} {s(sig, '%.3f'):>8s} {s(pr, '%.4f'):>8s} "
            f"{s(dev, '%.3f'):>7s} {s(devk, '%.3f'):>8s} {s(res, '%.4f'):>7s} "
            f"{s(tau, '%.0f'):>5s} {tot:7.0f} {r.get('peak_rss_mb', 0):6.0f}")
    txt = "\n".join(lines)
    open(os.path.join(SCALED, "summary.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
