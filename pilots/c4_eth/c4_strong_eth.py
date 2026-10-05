#!/usr/bin/env python3
"""
Strong-ETH fluctuation scaling for C4 at matched kinetic dose.

Diagnostic question: the within-window eigenstate fluctuation sigma_ETH was
previously reported as the RATIO sigma_ETH/std(a) (flat at 0.94-0.98 along
the truncation ladder).  A ratio against the window's own spread conflates
the smooth energy trend with the fluctuation and depends on the window
width, so it is not itself an ETH scaling diagnostic.  This script measures
the fluctuation in absolute, convention-free units and compares it with the
thermal-shell benchmark:

  kappa(D)   = sigma_ETH / std_basis,
               std_basis = sqrt(K(K+2)/12): the a priori spread of the
               local occupation over the (K+1)^d product basis.
  B_count(D) = sqrt(2/N_shell) * sigma_A_shell / std_basis,
               N_shell = number of basis states with diagonal energy inside
               the eigen-window's range [w_min, w_max]; sigma_A_shell = std
               of the local occupation over that shell.  This is the
               eigenstate fluctuation a thermal (strong-ETH) system would
               show if its eigenstates were Haar-random inside the shell the
               window actually probes -- the benchmark matched to the
               protocol (fixed count, k = 350).
  B_frac(D)  = same with a FIXED-FRACTION shell (5% quantile band at the
               median), N_frac = 0.05 D -> the D^{-1/2} reference line with
               the exact prefactor.
  kappa_Haar = sqrt(2/D): Haar-random vectors in the full basis.

Data: cached eigen-windows (win_{tag}.npz: w, a1) and exact full spectra
(dense_{tag}.npz: w, a1) from the matched-dose program; shells rebuilt
exactly from the stored build parameters (seed -> identical couplings;
rebuild validated against the stored band endpoints).

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_strongeth_results.json, fig_c4_strongeth.png
"""
import json
import os
import numpy as np

import c4_scaled_eth as base

OUT = base.OUT

L36_3D = ["L36d3K14", "L36d3K18", "L36d3K20", "L36d3K22", "L36d3K26",
          "L36d3K28", "L36d3K30", "L36d3K34", "L36d3K38"]
L36_4D = ["L36d4K7", "L36d4K9", "L36d4K11"]
L36_KRY = ["L36d4K13kr"]     # factorization-free tier past the LU ceiling
L36_SCR = ["L36d3K14scr", "L36d3K28scr", "L36d3K38scr", "L36d4K11scr"]
DENSE = ["L36d3K14", "L36d3K18", "L36d3K20", "L36d4K7", "L36d4K9"]
# zoo for the delocalization-mass panel: everything with a window result
ZOO_EXCLUDE = {"win_selftest_d4K7"}


def load(tag):
    res = json.load(open(os.path.join(OUT, f"res_{tag}.json")))
    z = np.load(os.path.join(OUT, f"win_{tag}.npz"))
    return res, z


def binned_sigma(w, a, n_bins=30):
    """Reproduce the window protocol: n_bins energy-quantile bins, RMS of
    within-bin stds.  Also return per-bin stds and bin centers."""
    qs = np.quantile(w, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9
    qs[-1] += 1e-9
    ib = np.clip(np.searchsorted(qs, w, side="right") - 1, 0, n_bins - 1)
    fl, cen = [], []
    for b in range(n_bins):
        s = ib == b
        if s.sum() >= 3:
            fl.append(a[s].std())
            cen.append(np.median(w[s]))
    fl = np.array(fl)
    return float(np.sqrt(np.mean(fl ** 2))), fl, np.array(cen)


def rebuild_shell(d, K, g0, h0, U, seed, V, scramble, w):
    """Rebuild the diagonal energies + local observable exactly (same seed
    -> same couplings) and measure the shell statistics at the window."""
    H, eps, g, hmat, coords = base.build_sparse(
        d, K, g0, h0, U, seed, V=V, scramble=scramble)
    obs = coords[0].ravel().astype(float)
    return eps, obs


def main():
    print("=" * 70, flush=True)
    rows = []

    # ---------- window tier: ladder + scrambled + krylov ----------
    for tag in L36_3D + L36_4D + L36_SCR:
        if not (os.path.exists(os.path.join(OUT, f"res_{tag}.json"))
                and os.path.exists(os.path.join(OUT, f"win_{tag}.npz"))):
            print(f"  skip {tag} (no cached result)", flush=True)
            continue
        res, z = load(tag)
        w, a = np.asarray(z["w"]), np.asarray(z["a1"])
        d, K, D = res["d"], res["K"], res["D"]
        sig, fl, cen = binned_sigma(w, a)
        # validate recomputation against the stored value
        assert abs(sig - res["sigma_eth"]) < 2e-6 * max(1, sig), \
            (tag, sig, res["sigma_eth"])
        std_basis = float(np.sqrt(K * (K + 2) / 12.0))
        raw_std = float(a.std())
        eps, obs = rebuild_shell(d, K, res["g0"], res["h0"], res.get("U", 0.0),
                                 res["seed"], res.get("V", 0.0),
                                 res.get("scramble", False), w)
        # rebuild exactness check: band endpoints
        be = res.get("band_est")
        assert be is not None and abs(eps.min() - be[0]) < 1e-9 \
            and abs(eps.max() - be[1]) < 1e-9, (tag, eps.min(), eps.max(), be)
        # count-matched shell: basis states inside the eigen-window range
        inwin = (eps >= w.min()) & (eps <= w.max())
        N_shell = int(inwin.sum())
        sig_shell = float(obs[inwin].std()) if N_shell >= 10 else float("nan")
        B_count = float(np.sqrt(2.0 / N_shell) * sig_shell / std_basis) \
            if N_shell >= 10 else float("nan")
        # fixed-fraction shell: 5% quantile band at the median
        lo, hi = np.quantile(eps, [0.475, 0.525])
        infrac = (eps >= lo) & (eps <= hi)
        N_frac = int(infrac.sum())
        sig_frac = float(obs[infrac].std())
        B_frac = float(np.sqrt(2.0 / N_frac) * sig_frac / std_basis)
        kappa = sig / std_basis
        PR = res.get("pr_over_D")
        R_count = kappa / B_count if B_count == B_count else None
        rows.append(dict(
            tag=tag, family=("L36-3D" if tag in L36_3D else
                             "L36-4D" if tag in L36_4D else "scrambled"),
            d=d, K=K, D=D, V=res.get("V"), PR_over_D=PR,
            sigma_eth=sig, raw_std=raw_std, std_basis=std_basis,
            kappa=kappa, kappa_x_sqrtD=kappa * np.sqrt(D),
            N_shell=N_shell, sigma_A_shell=sig_shell, B_count=B_count,
            N_frac=N_frac, B_frac=B_frac,
            R_count=R_count, R_frac=kappa / B_frac,
            N_eff=(N_shell / R_count ** 2 if R_count else None),
            kappa_Haar=float(np.sqrt(2.0 / D)),
            kappa_x_sqrtPR=(kappa * np.sqrt(PR * D) if PR else None),
            r_mean=res.get("r_mean"),
        ))
        print(f"  {tag}: D={D} kappa={kappa:.4f} B_count={B_count:.4f} "
              f"B_frac={B_frac:.4f} R_count={kappa/B_count:.2f} "
              f"N_shell={N_shell}", flush=True)

    # ---------- factorization-free (Krylov) tier: past the LU ceiling ----------
    for tag in L36_KRY:
        rp = os.path.join(OUT, f"res_krylov_{tag}.json")
        zp = os.path.join(OUT, f"win_krylov_{tag}.npz")
        if not (os.path.exists(rp) and os.path.exists(zp)):
            print(f"  skip {tag} (no krylov result)", flush=True)
            continue
        res = json.load(open(rp))
        z = np.load(zp)
        w, a = np.asarray(z["w"]), np.asarray(z["a1"])
        d, K, D = res["d"], res["K"], res["D"]
        sig, fl, cen = binned_sigma(w, a)
        assert abs(sig - res["sigma_eth"]) < 2e-6 * max(1, sig), \
            (tag, sig, res["sigma_eth"])
        std_basis = float(np.sqrt(K * (K + 2) / 12.0))
        eps, obs = rebuild_shell(d, K, res["g0"], res["h0"], res.get("U", 0.0),
                                 res["seed"], res.get("V", 0.0),
                                 res.get("scramble", False), w)
        be = res.get("band_est")
        assert be is not None and abs(eps.min() - be[0]) < 1e-9 \
            and abs(eps.max() - be[1]) < 1e-9, (tag, eps.min(), eps.max(), be)
        inwin = (eps >= w.min()) & (eps <= w.max())
        N_shell = int(inwin.sum())
        sig_shell = float(obs[inwin].std()) if N_shell >= 10 else float("nan")
        B_count = float(np.sqrt(2.0 / N_shell) * sig_shell / std_basis) \
            if N_shell >= 10 else float("nan")
        lo, hi = np.quantile(eps, [0.475, 0.525])
        infrac = (eps >= lo) & (eps <= hi)
        N_frac = int(infrac.sum())
        B_frac = float(np.sqrt(2.0 / N_frac) * obs[infrac].std() / std_basis)
        kappa = sig / std_basis
        PR = res.get("pr_over_D")
        rows.append(dict(
            tag=tag, family="L36-4D-krylov",
            d=d, K=K, D=D, V=res.get("V"), PR_over_D=PR,
            n_certified=res.get("n_certified"),
            sigma_eth=sig, raw_std=float(a.std()), std_basis=std_basis,
            kappa=kappa, kappa_x_sqrtD=kappa * np.sqrt(D),
            N_shell=N_shell, sigma_A_shell=sig_shell, B_count=B_count,
            N_frac=N_frac, B_frac=B_frac,
            R_count=(kappa / B_count if B_count == B_count else None),
            R_frac=kappa / B_frac,
            N_eff=(N_shell / (kappa / B_count) ** 2
                   if B_count == B_count else None),
            kappa_Haar=float(np.sqrt(2.0 / D)),
            kappa_x_sqrtPR=(kappa * np.sqrt(PR * D) if PR else None),
            r_mean=res.get("r_mean"),
        ))
        print(f"  {tag}: D={D} kappa={kappa:.4f} B_count={B_count:.4f} "
              f"B_frac={B_frac:.4f} R_frac={kappa/B_frac:.2f} "
              f"N_shell={N_shell} n_cert={res.get('n_certified')}", flush=True)

    # ---------- dense tier: exact full spectra ----------
    dense_rows = []
    for tag in DENSE:
        res = json.load(open(os.path.join(OUT, f"res_{tag}.json")))
        z = np.load(os.path.join(OUT, f"dense_{tag}.npz"))
        w, a = np.asarray(z["w"]), np.asarray(z["a1"])
        d, K, D = res["d"], res["K"], res["D"]
        std_basis = float(np.sqrt(K * (K + 2) / 12.0))
        # window-protocol selection: the k=350 eigenstates nearest the median
        med = np.median(w)
        sel = np.argsort(np.abs(w - med))[:350]
        sel.sort()
        sig350, _, _ = binned_sigma(w[sel], a[sel])
        # middle-50% quantile detrending (fixed fraction, 15 bins)
        q0, q1 = np.quantile(w, [0.25, 0.75])
        mid = (w >= q0) & (w <= q1)
        sig50, _, _ = binned_sigma(w[mid], a[mid], n_bins=15)
        eps, obs = rebuild_shell(d, K, res["g0"], res["h0"],
                                 res.get("U", 0.0), res["seed"],
                                 res.get("V", 0.0), res.get("scramble", False),
                                 w)
        lo, hi = np.quantile(eps, [0.475, 0.525])
        infrac = (eps >= lo) & (eps <= hi)
        N_frac = int(infrac.sum())
        B_frac = float(np.sqrt(2.0 / N_frac) * obs[infrac].std() / std_basis)
        dense_rows.append(dict(
            tag=tag, d=d, K=K, D=D, std_basis=std_basis,
            sigma_eth_350=sig350, kappa_350=sig350 / std_basis,
            sigma_eth_50=sig50, kappa_50=sig50 / std_basis,
            B_frac=B_frac, R_50=(sig50 / std_basis) / B_frac,
            window_sigma=res["sigma_eth"],
            window_vs_dense=sig350 / res["sigma_eth"],
        ))
        print(f"  dense {tag}: kappa_350={sig350/std_basis:.4f} "
              f"(window {res['sigma_eth']/std_basis:.4f}, ratio "
              f"{sig350/res['sigma_eth']:.3f}) kappa_50={sig50/std_basis:.4f} "
              f"B_frac={B_frac:.4f}", flush=True)

    # ---------- fits ----------
    def slope(fam, key="kappa"):
        xs = np.array([r["D"] for r in rows if r["family"] == fam])
        ys = np.array([r[key] for r in rows if r["family"] == fam])
        if len(xs) < 3:
            return None
        lx, ly = np.log(xs), np.log(ys)
        A = np.vstack([lx, np.ones_like(lx)]).T
        coef, res_, rank, sv = np.linalg.lstsq(A, ly, rcond=None)
        pred = A @ coef
        ss_res = float(((ly - pred) ** 2).sum())
        ss_tot = float(((ly - ly.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        return dict(alpha=float(coef[0]), r2=r2, n=int(len(xs)),
                    D_range=[float(xs.min()), float(xs.max())])

    fits = {fam: slope(fam) for fam in ("L36-3D", "L36-4D")}
    # 4D ladder including the Krylov-tier point past the LU ceiling
    all4 = [r for r in rows if r["family"] in ("L36-4D", "L36-4D-krylov")]
    if len(all4) >= 4:
        xs = np.array([r["D"] for r in all4])
        ys = np.array([r["kappa"] for r in all4])
        lx, ly = np.log(xs), np.log(ys)
        A = np.vstack([lx, np.ones_like(lx)]).T
        coef = np.linalg.lstsq(A, ly, rcond=None)[0]
        pred = A @ coef
        ss_res = float(((ly - pred) ** 2).sum())
        ss_tot = float(((ly - ly.mean()) ** 2).sum())
        fits["L36-4D+kr"] = dict(alpha=float(coef[0]),
                                 r2=1 - ss_res / ss_tot, n=len(all4),
                                 D_range=[float(xs.min()), float(xs.max())])
    # dense fixed-fraction slopes
    for fam, dsel in (("dense-3D", 3), ("dense-4D", 4)):
        xs = np.array([r["D"] for r in dense_rows if r["d"] == dsel])
        ys = np.array([r["kappa_50"] for r in dense_rows if r["d"] == dsel])
        if len(xs) >= 2:
            lx, ly = np.log(xs), np.log(ys)
            A = np.vstack([lx, np.ones_like(lx)]).T
            coef = np.linalg.lstsq(A, ly, rcond=None)[0]
            fits[fam] = dict(alpha=float(coef[0]), n=int(len(xs)),
                             D_range=[float(xs.min()), float(xs.max())])
    # <r> trend along the 3D ladder
    xs = np.array([r["D"] for r in rows if r["family"] == "L36-3D"])
    ys = np.array([r["r_mean"] for r in rows if r["family"] == "L36-3D"])
    A = np.vstack([np.log(xs), np.ones_like(xs)]).T
    coef = np.linalg.lstsq(A, ys, rcond=None)[0]
    r_trend = dict(slope_logD=float(coef[0]), mean=float(ys.mean()),
                   std=float(ys.std()))
    print("fits:", {k: (v["alpha"] if v else None) for k, v in fits.items()},
          flush=True)
    print("r trend:", r_trend, flush=True)

    # ---------- zoo: kappa*sqrt(PR) vs PR/D for every cached window ----------
    zoo = []
    for fn in sorted(os.listdir(OUT)):
        if not fn.startswith("win_") or not fn.endswith(".npz"):
            continue
        tag = fn[4:-4]
        if tag in ZOO_EXCLUDE or tag in {r["tag"] for r in rows}:
            continue
        rp = os.path.join(OUT, f"res_{tag}.json")
        if not os.path.exists(rp):
            continue
        try:
            res = json.load(open(rp))
            z = np.load(os.path.join(OUT, fn))
            if "a1" not in z or res.get("pr_over_D") is None:
                continue
            w, a = np.asarray(z["w"]), np.asarray(z["a1"])
            sig, _, _ = binned_sigma(w, a)
            K = res["K"]
            std_basis = float(np.sqrt(K * (K + 2) / 12.0))
            prd = res["pr_over_D"]
            zoo.append(dict(tag=tag, D=res["D"], K=K, V=res.get("V", 0.0),
                            U=res.get("U", 0.0), PR_over_D=prd,
                            kappa=sig / std_basis,
                            kappa_x_sqrtPR=sig / std_basis * np.sqrt(prd * res["D"])))
        except Exception as e:
            print(f"  zoo skip {tag}: {type(e).__name__}", flush=True)
    print(f"zoo: {len(zoo)} additional window configs", flush=True)

    # ---------- energy-resolved fluctuation ----------
    eres = {}
    for tag in ("L36d3K14", "L36d3K28", "L36d3K38"):
        res, z = load(tag)
        w, a = np.asarray(z["w"]), np.asarray(z["a1"])
        std_basis = float(np.sqrt(res["K"] * (res["K"] + 2) / 12.0))
        sig, fl, cen = binned_sigma(w, a)
        # normalized energy coordinate
        span = w.max() - w.min()
        eres[tag] = dict(D=res["D"], x=((cen - np.median(w)) / span).tolist(),
                         y=(fl / std_basis).tolist())

    out = dict(rows=rows, dense=dense_rows, fits=fits, r_trend=r_trend,
               zoo=zoo, energy_resolved=eres,
               definitions=dict(
                   kappa="sigma_ETH / std_basis, std_basis = sqrt(K(K+2)/12)",
                   B_count="sqrt(2/N_shell) * sigma_A_shell / std_basis "
                           "(N_shell: basis states inside the eigen-window "
                           "range; Haar-in-shell thermal benchmark, "
                           "count-matched to the protocol)",
                   B_frac="same with a 5% quantile shell (N = 0.05 D): "
                          "the D^{-1/2} strong-ETH reference",
                   kappa_Haar="sqrt(2/D)"))
    with open(os.path.join(OUT, "c4_strongeth_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("saved c4_strongeth_results.json", flush=True)

    # ---------------- figure ----------------
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

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6),
                             constrained_layout=True)
    col = {"L36-3D": ("o", "#4c72b0"), "L36-4D": ("s", "#dd8452"),
           "L36-4D-krylov": ("D", "#dd8452"), "scrambled": ("x", "#c44e52")}

    # (a) kappa vs D with benchmarks
    ax = axes[0, 0]
    for fam, (m, c) in col.items():
        xs = [r["D"] for r in rows if r["family"] == fam]
        ys = [r["kappa"] for r in rows if r["family"] == fam]
        if not xs:
            continue
        ax.loglog(xs, ys, marker=m, ls="none" if fam != "L36-3D" else "-",
                  lw=0 if fam != "L36-3D" else 0.9, color=c, ms=5,
                  mfc=("none" if fam == "L36-4D-krylov" else None),
                  label=fam + (f" (slope {fits[fam]['alpha']:.2f})"
                               if fits.get(fam) else ""))
    xs = [r["D"] for r in dense_rows]
    ax.loglog(xs, [r["kappa_350"] for r in dense_rows], "o", mfc="none",
              mec="#55a868", ms=7, label="exact 350-window")
    # benchmarks from the 3D ladder
    r3 = [r for r in rows if r["family"] == "L36-3D"]
    ax.loglog([r["D"] for r in r3], [r["B_count"] for r in r3], "k--", lw=1,
              label=r"$B_{\rm count}$ (thermal, protocol-matched)")
    ax.loglog([r["D"] for r in r3], [r["B_frac"] for r in r3], "k:", lw=1.2,
              label=r"$B_{\rm frac}$ (thermal, $5\%$ shell $\propto D^{-1/2}$)")
    ax.loglog([r["D"] for r in r3], [r["kappa_Haar"] for r in r3], "k-.",
              lw=0.9, label=r"$\sqrt{2/D}$ (Haar in full basis)")
    ax.set_ylim(0.004, 2.2)
    ax.set_xlabel(r"truncation dimension $D$")
    ax.set_ylabel(r"$\kappa = \sigma_{\rm ETH}/\mathrm{std}_{\rm basis}$")
    ax.set_title("(a) Absolute eigenstate fluctuation vs. benchmarks")
    ax.legend(fontsize=6.5, loc="upper left")

    # (b) ratio to the thermal benchmarks: protocol-shell (solid) and
    #     fixed-fraction / strong-ETH scaling (dotted)
    ax = axes[0, 1]
    for fam, (m, c) in col.items():
        xs = [r["D"] for r in rows if r["family"] == fam]
        ys = [r["R_count"] for r in rows if r["family"] == fam]
        ax.loglog(xs, ys, marker=m, ls="-", lw=0.8, color=c, ms=5,
                  label=fam + r" ($R_{\rm count}$)")
        ys2 = [r["R_frac"] for r in rows if r["family"] == fam]
        ax.loglog(xs, ys2, marker=m, ls=":", lw=1.1, color=c, ms=4,
                  alpha=0.8)
    xs = [r["D"] for r in dense_rows]
    ax.loglog(xs, [r["R_50"] for r in dense_rows], "o", mfc="none",
              mec="#55a868", ms=7, label="exact, $50\\%$ shell")
    ax.axhline(1.0, color="k", ls=":", lw=0.9)
    ax.annotate(r"dotted: $R_{\rm frac}$ vs. $D^{-1/2}$ scaling"
                " (strong ETH)", xy=(4000, 2.2), fontsize=6.5)
    kr = [r for r in rows if r["family"] == "L36-4D-krylov"]
    if kr:
        ax.loglog([r["D"] for r in kr], [r["R_frac"] for r in kr], "D",
                  mfc="none", mec="#dd8452", ms=8, ls="none")
        ax.annotate("Krylov tier (276/350 certified)",
                    xy=(kr[0]["D"], kr[0]["R_frac"]),
                    xytext=(0.62, 0.30), textcoords="axes fraction",
                    fontsize=6.5, color="#dd8452",
                    arrowprops=dict(arrowstyle="-", color="#dd8452", lw=0.6))
    ax.set_xlabel(r"truncation dimension $D$")
    ax.set_ylabel(r"$\kappa / B$")
    ax.set_title("(b) Distance from the thermal-shell benchmark")
    ax.legend(fontsize=7)

    # (c) kappa*sqrt(PR) vs PR/D across the zoo
    ax = axes[1, 0]
    allz = rows + zoo
    for r in allz:
        if r.get("PR_over_D") and r.get("kappa_x_sqrtPR") \
                and r["PR_over_D"] > 1e-6:
            is_l36 = r["tag"].startswith("L36")
            is_scr = "scr" in r["tag"]
            is_weak = "weak" in r["tag"]
            m, c, a = (("o", "#4c72b0", 0.9) if is_l36 and not is_scr else
                       ("x", "#c44e52", 0.9) if is_scr else
                       ("^", "#937860", 0.6) if is_weak else
                       (".", "#8172b2", 0.5))
            ax.loglog(r["PR_over_D"], r["kappa_x_sqrtPR"], m, color=c,
                      ms=8 if m in "ox^" else 7, alpha=a,
                      label=None)
    ax.axhline(np.sqrt(2.0), color="k", ls="--", lw=1,
               label=r"support-uniform ($\kappa\sqrt{PR}=\sqrt{2}$)")
    ax.set_ylim(0.2, 80)
    ax.set_xlabel(r"eigenstate participation $\mathrm{PR}/D$")
    ax.set_ylabel(r"$\kappa\sqrt{PR}$")
    ax.set_title("(c) Fluctuation vs. delocalization mass\n"
                 "(circles: matched dose; x: scrambled; dots: all others)")
    ax.legend(fontsize=7, loc="upper left")

    # (d) energy-resolved fluctuation
    ax = axes[1, 1]
    for tag, c in (("L36d3K14", "#4c72b0"), ("L36d3K28", "#dd8452"),
                   ("L36d3K38", "#c44e52")):
        e = eres[tag]
        ax.plot(e["x"], e["y"], "-o", color=c, ms=3, lw=0.8,
                label=f"$D={e['D']:.0f}$")
    ax.set_xlabel(r"normalized window energy "
                  r"$(E-\mathrm{median})/\mathrm{span}$")
    ax.set_ylabel(r"per-bin $\sigma / \mathrm{std}_{\rm basis}$")
    ax.set_title("(d) Energy-resolved fluctuation in the window")
    ax.legend(fontsize=7)

    fig.savefig(os.path.join(OUT, "fig_c4_strongeth.png"), dpi=170)
    print("saved fig_c4_strongeth.png", flush=True)

    with open(os.path.join(OUT, "strongeth_summary.txt"), "w") as fh:
        fh.write("Strong-ETH fluctuation scaling (matched dose VK^2=36)\n\n")
        fh.write("kappa = sigma_ETH/std_basis; B = thermal-shell benchmark\n")
        for r in rows:
            fh.write(f"{r['tag']:>14}: D={r['D']:>6} kappa={r['kappa']:.4f} "
                     f"B_count={r['B_count']:.4f} B_frac={r['B_frac']:.4f} "
                     f"R={r['R_count']:.2f} N_shell={r['N_shell']}"
                     + (f" n_cert={r['n_certified']}"
                        if r.get("n_certified") else "") + "\n")
        fh.write("\ndense tier:\n")
        for r in dense_rows:
            fh.write(f"{r['tag']:>14}: kappa_350={r['kappa_350']:.4f} "
                     f"window_ratio={r['window_vs_dense']:.3f} "
                     f"kappa_50={r['kappa_50']:.4f} R_50={r['R_50']:.2f}\n")
        fh.write("\nfits (alpha in kappa ~ D^alpha):\n")
        for k, v in fits.items():
            if v:
                fh.write(f"  {k}: alpha={v['alpha']:.3f} (n={v['n']})\n")
        fh.write(f"\n<r> trend: slope={r_trend['slope_logD']:.4f} "
                 f"mean={r_trend['mean']:.3f} std={r_trend['std']:.3f}\n")


if __name__ == "__main__":
    main()
