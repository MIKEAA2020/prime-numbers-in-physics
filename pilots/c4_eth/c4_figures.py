#!/usr/bin/env python3
"""Figures for the C4 (Cascade/ETH) pilot attack."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/z/my-project/download/pilot_c4_eth"

plt.rcParams.update({
    "font.size": 9.5, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
})

C_STRONG = "#1f77b4"; C_WEAK = "#d62728"; C_MICRO = "#2ca02c"
C_INT = "#ff7f0e"; C_GRAY = "#7f7f7f"

# ---------------- Fig 1: ETH + equilibration ----------------
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), constrained_layout=True)

# (a) ETH scatter d5K4
d = np.load(f"{OUT}/data_d5K4.npz")
E, a = d["eth_E"], d["eth_a"]
ax = axes[0]
ax.scatter(E, a, s=1.5, alpha=0.25, color=C_STRONG, rasterized=True, label="eigenstates")
bc, bs, mi = d["bin_centers"], d["bin_smooth"], d["micro"]
ax.plot(bc, bs, "-", color="#08306b", lw=2.2, label="ETH smooth curve")
ax.plot(bc, mi, "--", color=C_MICRO, lw=2.0, label="microcanonical")
ax.set_xlabel(r"$E$  [$\hbar\omega_0$]")
ax.set_ylabel(r"$\langle n_{2}\rangle$  (occupation of prime-2 mode)")
ax.set_title(r"(a) ETH test, $d{=}5,\ K{=}4,\ D{=}3125$", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False, loc="upper left")
ax.set_ylim(-0.2, 4.4)

# (b) relaxation trace
ax = axes[1]
ax.plot(d["tau"], d["trace"], lw=0.8, color=C_STRONG, label=r"$\langle \hat n_{11}(\tau)\rangle$ (generic $H_{\rm tot}$)")
ev = json.load(open(f"{OUT}/c4_results.json"))
ev5 = [r for r in ev if r["tag"] == "d5K4"][0]["evolution"]
ax.axhline(ev5["diagonal"], color="#08306b", ls="-", lw=1.6, label=f"diagonal ens. = {ev5['diagonal']:.2f}")
ax.axhline(ev5["micro_d"], color=C_MICRO, ls="--", lw=1.6, label=f"microcanonical = {ev5['micro_d']:.2f}")
dw = np.load(f"{OUT}/data_d5K4weak.npz")
ax.plot(dw["tau"], dw["trace"], lw=0.8, color=C_WEAK, alpha=0.8, label="weak-coupling control")
evw = [r for r in ev if r["tag"] == "d5K4weak"][0]["evolution"]
ax.axhline(evw["diagonal"], color=C_WEAK, ls=":", lw=1.4)
ax.set_xlabel(r"$\tau$  [$1/\omega_0$]")
ax.set_ylabel(r"$\langle \hat n_{11}\rangle$")
ax.set_title(r"(b) Equilibration from $|K\,e_{11}\rangle$", fontsize=9.5)
ax.legend(fontsize=7.2, frameon=False, loc="center right")
ax.set_xlim(0, 150)

# (c) ETH fluctuation comparison
ax = axes[2]
tags = ["d4K4", "d5K3", "d4K6", "d5K4", "d4K7", "d6K3"]
x = np.arange(len(tags))
sig = [[r for r in ev if r["tag"] == t][0]["sigma_eth"] for t in tags]
sigw = [r for r in ev if r["tag"] == "d5K4weak"][0]["sigma_eth"]
sigi = [r for r in json.load(open(f"{OUT}/c4_results_interacting.json")) if r["tag"] == "d5K4U15"][0]["sigma_eth"]
ax.bar(x, sig, color=C_STRONG, alpha=0.85, label="generic $H_{\\rm tot}$")
ax.bar([len(tags)], sigi, color=C_INT, alpha=0.9, label="+ quartic $U{=}1.5$")
ax.bar([len(tags) + 1], sigw, color=C_WEAK, alpha=0.9, label="weak control")
ax.set_xticks(list(x) + [len(tags), len(tags) + 1])
ax.set_xticklabels([t.replace("d", "").replace("K", ",") for t in tags] + ["U", "wk"], fontsize=7.5)
ax.set_ylabel(r"$\sigma_{\rm ETH}$ (within-bin fluct.)")
ax.set_title(r"(c) ETH fluctuations vs. system/coupling", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False)
ax.axhline(0, color="k", lw=0.6)

fig.suptitle("C4 pilot: ETH on the prime lattice — extended but not thermal at pilot scale", fontsize=11, y=1.04)
fig.savefig(f"{OUT}/fig_c4_eth.png", dpi=200, bbox_inches=None)
plt.close(fig)

# ---------------- Fig 2: level stats + localization ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2), constrained_layout=True)

ax = axes[0]
rv = d["rvals"]
bins = np.linspace(0, 1, 40)
ax.hist(rv, bins=bins, density=True, color=C_STRONG, alpha=0.75, label=f"generic $H_{{\\rm tot}}$  $\\langle r\\rangle$=0.526")
dwv = dw["rvals"]
ax.hist(dwv, bins=bins, density=True, histtype="step", lw=1.8, color=C_WEAK, label="weak control  $\\langle r\\rangle$=0.388")

def wigner_surmise(r, beta):
    Z = (27.0 / 8.0) if beta == 1 else 0
    # use the standard ratio-distribution P_beta(r) (Atas et al.)
    if beta == 1:
        return (27 / 4.0) * (r + r * r) / (1 + r + r * r) ** 2.5
    if beta == 2:
        from scipy.special import gamma as G
        c = 8 / (3 * np.sqrt(3) * np.pi)
        return (81 * np.sqrt(3) / (8 * np.pi)) * (r + r * r) ** 2 / (1 + r + r * r) ** 4
    # Poisson: 2/(1+r)^2
rr = np.linspace(0.001, 1, 400)
ax.plot(rr, 2.0 / (1 + rr) ** 2, "k--", lw=1.2, label="Poisson")
ax.plot(rr, (27 / 4.0) * (rr + rr * rr) / (1 + rr + rr * rr) ** 2.5, color="#444", ls="-.", lw=1.2, label="GOE")
ax.plot(rr, (81 * np.sqrt(3) / (8 * np.pi)) * (rr + rr * rr) ** 2 / (1 + rr + rr * rr) ** 4,
        color="#444", ls=":", lw=1.2, label="GUE")
ax.set_xlabel(r"level-spacing ratio $r=s_n/s_{n+1}$")
ax.set_ylabel("density")
ax.set_title("(a) C5 proxy: level statistics", fontsize=9.5)
ax.legend(fontsize=7.2, frameon=False)
ax.set_xlim(0, 1)

ax = axes[1]
labels = [r"$H_P$", r"$H_P+H_W$" + "\n(Stark chains)", r"$H_{\rm tot}$" + "\n(full)",
          r"$H_{\rm tot}+U\,nn$" + "\n(quartic)", "weak\ncontrol"]
vals = [0.0003, 0.0489, 0.2705, 0.0582, 0.0005]
cols = [C_GRAY, "#9ecae1", C_STRONG, C_INT, C_WEAK]
x = np.arange(len(vals))
ax.bar(x, vals, color=cols)
for xi, v in zip(x, vals):
    ax.text(xi, v + 0.006, f"{v:.4f}" if v < 0.01 else f"{v:.3f}", ha="center", fontsize=7.5)
ax.set_yscale("log")
ax.set_ylim(1e-4, 0.8)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
ax.set_ylabel(r"median PR$/D$ (occupation basis)")
ax.set_title("(b) Delocalization ladder", fontsize=9.5)

fig.suptitle("C4 pilot: structure of the prime-lattice Hamiltonian ($d{=}5, K{=}4$)", fontsize=11, y=1.03)
fig.savefig(f"{OUT}/fig_c4_structure.png", dpi=200)
plt.close(fig)

print("figures written")
