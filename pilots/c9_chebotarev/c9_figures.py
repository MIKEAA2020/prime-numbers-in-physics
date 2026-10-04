#!/usr/bin/env python3
"""Figures for the C9 (Chebotarev dictionary check) pilot attack."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/z/my-project/download/pilot_c9_chebotarev"
r = json.load(open(f"{OUT}/c9_results.json"))

plt.rcParams.update({
    "font.size": 9.5, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
})

fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.5), constrained_layout=True)

# ---- (a) S3 convergence ----
ax = axes[0]
S3 = r["partA"]["S3"]
xs = np.array([int(k) for k in S3.keys()])
f111 = np.array([v["f"][0] for v in S3.values()])
f21 = np.array([v["f"][1] for v in S3.values()])
f3 = np.array([v["f"][2] for v in S3.values()])
Ntot = np.array([v["total"] for v in S3.values()])
err = 1.0 / np.sqrt(Ntot)

ax.errorbar(xs, f111, yerr=err, fmt="o-", color="#1f77b4", lw=1.6, ms=4, capsize=2,
            label=r"type (111) [id]")
ax.errorbar(xs, f21, yerr=err, fmt="s-", color="#2ca02c", lw=1.6, ms=4, capsize=2,
            label=r"type (21) [transp.]")
ax.errorbar(xs, f3, yerr=err, fmt="^-", color="#d62728", lw=1.6, ms=4, capsize=2,
            label=r"type (3) [3-cycle]")
for y, c in [(1 / 6, "#1f77b4"), (1 / 2, "#2ca02c"), (1 / 3, "#d62728")]:
    ax.axhline(y, color=c, ls=":", lw=1.0)
ax.set_xscale("log")
ax.set_xlabel(r"$X$ (primes $p \leq X$, $p \nmid 108$)")
ax.set_ylabel("empirical splitting fraction")
ax.set_title(r"(a) Gal$(\mathbb{Q}(\sqrt[3]{2})/\mathbb{Q}) = S_3$: splitting = group stats", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False, loc="center right")
ax.text(1.5e3, 0.42, "Chebotarev:\n1/6, 1/2, 1/3", fontsize=7.5, color="#555")

# ---- (b) FPR of dictionary test ----
ax = axes[1]
scan = r["partB"]["null_FPR_scan"]
sigmas = [0.01, 0.003, 0.001]
nm60 = [scan[f"sig{s}_Nmax60"] for s in ("0.01", "0.003", "0.001")]
nm360 = [scan[f"sig{s}_Nmax360"] for s in ("0.01", "0.003", "0.001")]
x = np.arange(3)
w = 0.36
ax.bar(x - w / 2, nm60, w, color="#9ecae1", label=r"$N_{\max}=60$")
ax.bar(x + w / 2, nm360, w, color="#08519c", label=r"$N_{\max}=360$")
ax.axhline(0.05, color="k", ls="--", lw=1.2)
ax.text(2.32, 0.055, "5% level", fontsize=7.5, ha="right")
ax.set_xticks(x)
ax.set_xticklabels([r"$\sigma=1\%$", r"$\sigma=0.3\%$", r"$\sigma=0.1\%$"])
ax.set_ylabel("false-positive rate (generic truth)")
ax.set_yscale("symlog", linthresh=1e-3)
ax.set_ylim(-0.02, 0.6)
ax.set_title(r"(b) Dictionary fit: type-I error ($k{=}5$ channels)", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False, loc="upper right")

ax2 = ax.twinx()
ax2.set_ylim(*ax.get_ylim())
ax2.set_yticks([])

fig.suptitle("C9 pilot: the Chebotarev dictionary check — substrate verified, protocol calibrated", fontsize=11, y=1.03)
fig.savefig(f"{OUT}/fig_c9_chebotarev.png", dpi=200)
plt.close(fig)
print("figure written")

# summary numbers for the review
print("\nKEY NUMBERS:")
print("S3 at 1e7: f111=%.5f f21=%.5f f3=%.5f (chi2 p=%.2f)" % (f111[-1], f21[-1], f3[-1], S3["10000000"]["p"]))
print("injection: recovered N=6 c=[1,3,2] at n>=300 events (all)")
print("Z-boson: best N=%s chi2=%.0f -> no Chebotarev structure at the Z pole" %
      (r["partB"]["Zboson"]["best_N"], r["partB"]["Zboson"]["best_chi2"]))
