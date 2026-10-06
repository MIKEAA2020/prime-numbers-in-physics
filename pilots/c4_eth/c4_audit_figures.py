#!/usr/bin/env python3
"""Audit-response analysis and figure: label-scrambled controls, generic
quantile sweep, finite-size scaling of <r> - r_GOE vs 1/log D.

Outputs:
  figures/fig_c4_controls.png  (3 panels)
  results/c4_audit_results.json
"""
import json, glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
for fp in ['/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
    try:
        fm.fontManager.addfont(fp)
    except Exception:
        pass
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT = "/home/z/my-project/download/pilot_c4_eth_scaled"
R_GOE = 0.5307

def load(tag):
    p = os.path.join(OUT, f"res_{tag}.json")
    return json.load(open(p)) if os.path.exists(p) else None

# ---------------------------------------------------------------- data
# 1. matched-dose ladder scaling
ladder = []
for f in sorted(glob.glob(OUT + "/res_L36*.json")):
    r = json.load(open(f))
    if r.get("r_mean") is None or r["tag"].endswith("scr"):
        continue
    ladder.append(dict(tag=r["tag"], d=r["d"], K=r["K"], D=r["D"],
                       r=r["r_mean"], sem=r.get("r_sem"),
                       pr=r.get("pr_over_D")))
ladder.sort(key=lambda x: x["D"])

# 2. scrambled vs arithmetic pairs
pairs = [
    ("d4K11V0",   "d4K11V0scr",   "generic V=0,  d=4 K=11 (D=20736)"),
    ("d4K11V03",  "d4K11V03scr",  "kinetic V=0.3, d=4 K=11 (D=20736)"),
    ("L36d4K11",  "L36d4K11scr",  "matched dose,  d=4 K=11 (D=20736)"),
    ("d3K28diag", "d3K28V0scr",   "generic V=0,  d=3 K=28 (D=24389)"),
]
pair_rows = []
for base, scr, label in pairs:
    a, s = load(base), load(scr)
    if not (a and s and a.get("r_mean") and s.get("r_mean")):
        continue
    pair_rows.append(dict(label=label, base=base, scr=scr,
        r_arith=a["r_mean"], r_scr=s["r_mean"],
        pr_arith=a.get("pr_over_D"), pr_scr=s.get("pr_over_D"),
        sig_arith=a.get("sigma_eth"), sig_scr=s.get("sigma_eth"),
        sem_arith=a.get("r_sem"), sem_scr=s.get("r_sem")))

# 3. quantile sweeps at d3K28: weak vs generic
weak_q  = {"0.02":0.4879,"0.10":0.5306,"0.15":0.4361,"0.25":0.5563,
           "0.50":0.5274,"0.75":0.4215,"0.90":0.4208,"0.98":0.4182}
gen_q   = {"0.02":None,"0.10":None,"0.15":None,"0.25":None}
# generic sweep from tags d3K28gq*
gen = {}
for q in ["002","010","015","025","075","090","098"]:
    r = load(f"d3K28gq{q}")
    if r and r.get("r_mean"):
        gen[q] = r["r_mean"]
rmed = load("d3K28diag")
if rmed and rmed.get("r_mean"):
    gen["050"] = rmed["r_mean"]

qs = [0.02, 0.10, 0.15, 0.25, 0.50, 0.75, 0.90, 0.98]
weak_vals = [weak_q.get(f"{q:.2f}".rstrip("0").rstrip(".") if q != 0.10 and q != 0.25 and q != 0.50 else {0.10:"0.10",0.25:"0.25",0.50:"0.50",0.02:"0.02",0.15:"0.15",0.75:"0.75",0.90:"0.90",0.98:"0.98"}[q], None) for q in qs]
# simpler: rebuild dicts with float keys
weak_map = {0.02:0.4879, 0.10:0.5306, 0.15:0.4361, 0.25:0.5563,
            0.50:0.5274, 0.75:0.4215, 0.90:0.4208, 0.98:0.4182}
gen_map = {}
tagmap = {"002":0.02, "010":0.10, "015":0.15, "025":0.25, "075":0.75,
          "090":0.90, "098":0.98}
for t, q in tagmap.items():
    r = load(f"d3K28gq{t}")
    if r and r.get("r_mean"):
        gen_map[q] = r["r_mean"]
rmed = load("d3K28diag")
if rmed and rmed.get("r_mean"):
    gen_map[0.50] = rmed["r_mean"]

# ---------------------------------------------------------------- fits
dev = [(1.0/np.log(x["D"]), x["r"] - R_GOE, x["d"]) for x in ladder]
xs = np.array([d[0] for d in dev]); ys = np.array([d[1] for d in dev])
A = np.vstack([xs, np.ones_like(xs)]).T
coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
fit_txt = (f"dev = {coef[0]:+.2f}(1/log D) {coef[1]:+.3f}; "
           f"extrapolated D->oo: {'+' if coef[1]>=0 else ''}{coef[1]:.3f}")
# per-dimension fits
d3 = [(1/np.log(x["D"]), x["r"]-R_GOE) for x in ladder if x["d"] == 3]
d4 = [(1/np.log(x["D"]), x["r"]-R_GOE) for x in ladder if x["d"] == 4]
c3, *_ = np.linalg.lstsq(np.vstack([np.array(d3)[:,0], np.ones(len(d3))]).T,
                         np.array(d3)[:,1], rcond=None)
c4, *_ = np.linalg.lstsq(np.vstack([np.array(d4)[:,0], np.ones(len(d4))]).T,
                         np.array(d4)[:,1], rcond=None)
print("pooled fit:", fit_txt)
print(f"d=3 fit: dev = {c3[0]:+.2f}(1/logD) {c3[1]:+.3f}")
print(f"d=4 fit: dev = {c4[0]:+.2f}(1/logD) {c4[1]:+.3f}")

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.1), constrained_layout=True)

# (a) scaling
ax = axes[0]
for dd, c, mk in ((3, "C0", "o"), (4, "C1", "s")):
    pts = [(x, y) for x, y, ddd in dev if ddd == dd]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], mk, color=c,
            ms=6, label=f"matched dose, d={dd}")
    cf = c3 if dd == 3 else c4
    xx = np.linspace(0.085, 0.13, 10)
    ax.plot(xx, cf[0]*xx + cf[1], "-", color=c, alpha=0.5,
            lw=1.2)
ax.axhline(0, color="k", lw=0.8, ls=":")
ax.axhline(0.5307-0.5307, color="k", lw=0.8)
ax.set_xlabel(r"$1/\log D$")
ax.set_ylabel(r"$\langle r\rangle - r_{\mathrm{GOE}}$")
ax.set_title("(a) Level statistics finite-size scaling")
ax.legend(loc="lower right", fontsize=8)
ax.text(0.05, 0.06, f"d=3: dev $\\to$ {c3[1]:+.3f}\nd=4: dev $\\to$ {c4[1]:+.3f}",
        transform=ax.transAxes, fontsize=8,
        bbox=dict(fc="white", ec="0.6", alpha=0.9))

# (b) scrambled vs arithmetic
ax = axes[1]
labels = [p["label"].split("(")[0].strip() for p in pair_rows]
x = np.arange(len(pair_rows))
w = 0.38
ax.bar(x - w/2, [p["r_arith"] for p in pair_rows], w,
       color="C0", label="arithmetic diagonal")
ax.bar(x + w/2, [p["r_scr"] for p in pair_rows], w,
       color="C3", label="scrambled diagonal")
for i, p in enumerate(pair_rows):
    ax.errorbar(i - w/2, p["r_arith"], yerr=p.get("sem_arith") or 0.018,
                fmt="none", ecolor="k", lw=0.8, capsize=2)
    ax.errorbar(i + w/2, p["r_scr"], yerr=p.get("sem_scr") or 0.018,
                fmt="none", ecolor="k", lw=0.8, capsize=2)
ax.axhline(R_GOE, color="k", ls=":", lw=1)
ax.text(0.02, R_GOE + 0.004, "GOE", fontsize=8, transform=ax.get_yaxis_transform())
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=7, rotation=14, ha="right")
ax.set_ylabel(r"$\langle r\rangle$")
ax.set_ylim(0.40, 0.62)
ax.set_title("(b) Level statistics: arithmetic vs scrambled")
ax.legend(fontsize=8)

# inset: PR/D comparison (log)
axi = ax.inset_axes([0.60, 0.24, 0.37, 0.30])
axi.bar(x - w/2, [p["pr_arith"] for p in pair_rows], w, color="C0")
axi.bar(x + w/2, [p["pr_scr"] for p in pair_rows], w, color="C3")
axi.set_yscale("log")
axi.set_xticks(x); axi.set_xticklabels([])
axi.tick_params(labelsize=6)
axi.set_title("PR/D", fontsize=7)

# (c) quantile sweeps
ax = axes[2]
ax.plot(list(weak_map.keys()), list(weak_map.values()), "o-", color="C1",
        ms=5, label="weak coupling ($g_0=0.05$)")
qg = sorted(gen_map.keys())
ax.plot(qg, [gen_map[q] for q in qg], "s-", color="C0",
        ms=5, label="generic coupling ($g_0=1.5$)")
ax.axhline(R_GOE, color="k", ls=":", lw=1)
ax.text(0.02, R_GOE + 0.004, "GOE", fontsize=8)
ax.axhline(0.3863, color="C7", ls="--", lw=1)
ax.text(0.02, 0.3863 + 0.004, "Poisson", fontsize=8, color="C7")
ax.set_xlabel(r"window quantile of the density of states $\sigma$")
ax.set_ylabel(r"$\langle r\rangle$")
ax.set_title("(c) Window-placement sweep, d=3 K=28 (D=24389)")
ax.legend(fontsize=8, loc="lower left")

fig.suptitle("C4 diagnostics: label-scrambled controls, window sweeps, "
             "and finite-size scaling", fontsize=11)
fig.savefig(os.path.join(OUT, "fig_c4_controls.png"), dpi=160)
fig.savefig("/home/z/my-project/repo-push/paper/latex/fig_c4_controls.png",
            dpi=160)
print("figure -> fig_c4_controls.png")

# ---------------------------------------------------------------- json
result = dict(
    R_GOE=R_GOE,
    scaling=dict(ladder=ladder, pooled=[float(coef[0]), float(coef[1])],
                 d3=[float(c3[0]), float(c3[1])], d4=[float(c4[0]), float(c4[1])],
                 fit_text=fit_txt),
    scramble_pairs=pair_rows,
    quantile_sweep=dict(weak=weak_map, generic={str(k): v for k, v in gen_map.items()},
                        note="generic band 0.464-0.540 at d3K28 full sweep; "
                             "earlier 3-quantile flatness was interior-only"),
)
with open(os.path.join(OUT, "c4_audit_results.json"), "w") as f:
    json.dump(result, f, indent=1)
print("json -> c4_audit_results.json")

# summary table
print("\n=== scrambled vs arithmetic ===")
for p in pair_rows:
    print(f"{p['label']:38s} r: {p['r_arith']:.4f} -> {p['r_scr']:.4f} | "
          f"PR/D: {p['pr_arith']:.4f} -> {p['pr_scr']:.4f} | "
          f"sig: {p['sig_arith']:.2f} -> {p['sig_scr']:.2f}")
print("\n=== generic sweep (d3K28) ===")
for q in sorted(gen_map):
    print(f"q={q}: {gen_map[q]:.4f}")
