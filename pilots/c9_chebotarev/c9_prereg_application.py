#!/usr/bin/env python3
"""
C9 pre-registered application: Chebotarev dictionary fit to the Z-pole
branching table under the protocol frozen in
repo-push/review/c9_preregistration.md (commits d3b1160 / 9f30553).

Statistic:  T = min_{N in [5,360], c_i | N, sum c_i = N} sum_i (f_i - c_i/N)^2 / sigma_i^2
(class equation enforced; exact DP over integer partial sums).

Stages:
  0. self-test of the DP against brute-force enumeration (k=3, N<=24).
  1. null calibration: 5000 Dirichlet(1,..,1) tables at the actual sigma
     pattern -> null distribution, 5% threshold, FPR at chi2_0.95(4).
  2. Z-pole application: T_obs, best (N, c), decision, per-channel minimum
     normalized deviations, precision-inflation factor lambda.
  3. power: registered truth tables (N=6/36/360) x noise at sigma x
     {1, 1e-1, 1e-2, 3.3e-3} x 2000 draws: detection fraction and N-recovery.
  4. sensitivity: the unconstrained N<=5000 variant (earlier protocol).

Outputs -> /home/z/my-project/download/pilot_c9_chebotarev/
           c9_prereg_results.json, fig_c9_prereg.png, prereg_summary.txt
"""
import json
import os
import numpy as np
from scipy import stats

OUT = "/home/z/my-project/download/pilot_c9_chebotarev"
os.makedirs(OUT, exist_ok=True)

# ---- frozen primary-ensemble data (pre-registration section 2) ----
LABELS = ["had", "e", "mu", "tau", "invisible"]
F_Z = np.array([0.6991, 0.03363, 0.03366, 0.03370, 0.2017])
S_Z = np.array([0.0009, 0.00004, 0.00007, 0.00009, 0.0006])
K = 5
NMIN, NMAX = 5, 360
CHI2_CRIT = float(stats.chi2.ppf(0.95, K - 1))          # 9.4877
TRUTHS = {"N6": (6, [2, 1, 1, 1, 1]),
          "N36": (36, [18, 6, 6, 4, 2]),
          "N360": (360, [180, 90, 45, 36, 9])}
SIG_SCALES = [("current", 1.0), ("x1e-1", 1e-1), ("x1e-2", 1e-2),
              ("Zfactory_stat_floor", 3.3e-3)]
NPOWER = 2000
NNULL = 5000
RNG_NULL = np.random.default_rng(20261005)
RNG_POWER = np.random.default_rng(20261006)


def divisors_of(n):
    ds = [1]
    d = 2
    while d * d <= n:
        if n % d == 0:
            ds.append(d)
            if d != n // d:
                ds.append(n // d)
        d += 1
    ds.append(n)
    return np.array(sorted(set(ds)))


DIVS = {N: divisors_of(N) for N in range(2, NMAX + 1)}


# ----------------------------------------------------------------------------
# constrained dictionary fit: exact DP, vectorized over tables
# ----------------------------------------------------------------------------
def fit_batch(F, S):
    """F: (M, k) tables; S: (M, k) or (k,) sigmas.
    Returns T (M,) = min over N of the class-equation-constrained chi2,
    and argN (M,) int (the minimizing N; 0 if infeasible)."""
    F = np.atleast_2d(np.asarray(F, float))
    M, k = F.shape
    S = np.broadcast_to(np.asarray(S, float), (M, k))
    best_T = np.full(M, np.inf)
    best_N = np.zeros(M, dtype=int)
    for N in range(max(NMIN, k), NMAX + 1):
        ds = DIVS[N]
        dp = np.full((M, N + 1), np.inf)
        dp[:, 0] = 0.0
        for j in range(k):
            new = np.full((M, N + 1), np.inf)
            sj = S[:, j]
            fj = F[:, j]
            for c in ds:
                cost = ((fj - c / N) / sj) ** 2
                tgt = new[:, c:]
                cand = dp[:, : N + 1 - c] + cost[:, None]
                np.minimum(tgt, cand, out=tgt)
            dp = new
        tN = dp[:, N]
        better = tN < best_T
        best_T[better] = tN[better]
        best_N[better] = N
    return best_T, best_N


def fit_single_backtrack(f, s):
    """Single table; returns (T, N, c_list)."""
    k = len(f)
    bT, bN, bC = np.inf, None, None
    for N in range(max(NMIN, k), NMAX + 1):
        ds = DIVS[N]
        dp = np.full(N + 1, np.inf)
        dp[0] = 0.0
        choice = np.full((k, N + 1), -1, dtype=int)
        for j in range(k):
            new = np.full(N + 1, np.inf)
            for c in ds:
                cost = ((f[j] - c / N) / s[j]) ** 2
                cand = dp[: N + 1 - c] + cost
                tgt = new[c:]
                upd = cand < tgt
                tgt[upd] = cand[upd]
                # record choice where updated
                idx = np.flatnonzero(upd)
                if idx.size:
                    choice[j][c + idx] = c
            dp = new
        if dp[N] < bT:
            bT = float(dp[N])
            bN = N
            # backtrack
            cs = []
            ssum = N
            for j in range(k - 1, -1, -1):
                c = int(choice[j][ssum])
                cs.append(c)
                ssum -= c
            bC = cs[::-1]
    return bT, bN, bC


# ----------------------------------------------------------------------------
# stage 0: self-test against brute force
# ----------------------------------------------------------------------------
def selftest():
    rng = np.random.default_rng(99)
    for trial in range(60):
        k = 3
        f = rng.dirichlet(np.ones(k)) * rng.uniform(0.2, 3.0)
        s = rng.uniform(0.01, 0.2, size=k)
        # brute force
        bf = np.inf
        for N in range(5, 25):
            ds = DIVS[N]
            for c0 in ds:
                for c1 in ds:
                    for c2 in ds:
                        if c0 + c1 + c2 == N:
                            chi = sum((f[i] - [c0, c1, c2][i] / N) ** 2 / s[i] ** 2
                                      for i in range(k))
                            bf = min(bf, chi)
        t_dp, _ = fit_batch(f[None, :], s[None, :])
        assert abs(t_dp[0] - bf) < 1e-9 * max(1.0, bf), (trial, t_dp[0], bf)
    # batch vs single + backtrack consistency
    f = F_Z
    tB, nB = fit_batch(f[None, :], S_Z[None, :])
    tS, nS, cS = fit_single_backtrack(f, S_Z)
    assert abs(tB[0] - tS) < 1e-9 and nB[0] == nS
    assert sum(cS) == nS and all(nS % c == 0 for c in cS)
    print(f"selftest PASS (60 brute-force cases; batch==single==backtrack; "
          f"T={tS:.1f}, N={nS}, c={cS})", flush=True)
    return tS, nS, cS


# ----------------------------------------------------------------------------
# stage 1: null calibration
# ----------------------------------------------------------------------------
def null_calibration():
    F = RNG_NULL.dirichlet(np.ones(K), size=NNULL)
    T, _ = fit_batch(F, S_Z[None, :])
    res = dict(
        trials=NNULL, seed=20261005,
        median=float(np.median(T)), mean=float(T.mean()),
        q05=float(np.quantile(T, 0.05)), q50=float(np.quantile(T, 0.50)),
        q95=float(np.quantile(T, 0.95)), min=float(T.min()),
        max=float(T.max()),
        chi2_crit=CHI2_CRIT,
        FPR_at_chi2crit=float((T <= CHI2_CRIT).mean()),
    )
    print(f"null: median={res['median']:.1f} q05={res['q05']:.1f} "
          f"q95={res['q95']:.1f} FPR(chi2crit)={res['FPR_at_chi2crit']:.4f}",
          flush=True)
    return res, T


# ----------------------------------------------------------------------------
# stage 3: power
# ----------------------------------------------------------------------------
def power(thr_q05):
    out = {}
    for name, (Nt, cs) in TRUTHS.items():
        truth = np.array(cs) / Nt
        for sname, sc in SIG_SCALES:
            S = S_Z * sc
            F = truth[None, :] + RNG_POWER.normal(0, S, size=(NPOWER, K))
            assert (F > 0).all()
            T, Nb = fit_batch(F, S)
            out[f"{name}_{sname}"] = dict(
                N_truth=Nt, c_truth=cs, sigma_scale=sc, draws=NPOWER,
                T_median=float(np.median(T)),
                detect_chi2crit=float((T <= CHI2_CRIT).mean()),
                detect_q05=float((T <= thr_q05).mean()),
                recover_N=float((Nb == Nt).mean()),
            )
            print(f"power {name} {sname}: medT={np.median(T):.1f} "
                  f"detect@chi2={out[f'{name}_{sname}']['detect_chi2crit']:.3f} "
                  f"recoverN={out[f'{name}_{sname}']['recover_N']:.3f}", flush=True)
    return out


# ----------------------------------------------------------------------------
# stage 4: sensitivity (unconstrained, N<=5000) -- the earlier protocol
# ----------------------------------------------------------------------------
def fit_unconstrained(f, s, Nmax):
    best = (np.inf, None, None)
    k = len(f)
    for N in range(2, Nmax + 1):
        ds = DIVS.get(N)
        if ds is None:
            ds = divisors_of(N)
        if len(ds) < 2:
            continue
        targets = f * N
        idx = np.searchsorted(ds, targets)
        idx = np.clip(idx, 0, len(ds) - 1)
        cand = np.stack([ds[np.clip(idx - 1, 0, len(ds) - 1)], ds[idx]], axis=1)
        pick = np.argmin(np.abs(cand - targets[:, None]), axis=1)
        ci = cand[np.arange(k), pick]
        chi2 = float((((f - ci / N) / s) ** 2).sum())
        if chi2 < best[0]:
            best = (chi2, N, ci.tolist())
    return best


def make_figure(t_obs, n_best, c_best, thr, T_null, per_ch, pw):
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

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.1),
                             constrained_layout=True)
    # (a) null distribution + T_obs
    ax = axes[0]
    ax.hist(np.log10(np.asarray(T_null)), bins=60, color="#9ecae1",
            edgecolor="none", density=True, label="structureless null (5000)")
    ax.axvline(np.log10(thr), color="#f28e2b", ls="--",
               label=f"registered 5% threshold = {thr:.0f}")
    ax.axvline(np.log10(t_obs), color="#d62728", lw=2,
               label=f"$T_{{\\mathrm{{obs}}}}$ = {t_obs:.0f}")
    ax.set_xlabel("$\\log_{10} T$ (constrained dictionary fit)")
    ax.set_ylabel("density")
    ax.set_title("(a) Null calibration and the $Z$-pole fit")
    ax.legend(fontsize=7, loc="upper left")

    # (b) power vs sigma scale: registered MC threshold (solid) and
    #     asymptotic chi2 threshold (dotted)
    ax = axes[1]
    xs = [sc for _, sc in SIG_SCALES]
    marks = {"N6": ("o", "#4c72b0"), "N36": ("s", "#dd8452"),
             "N360": ("^", "#55a868")}
    for name, (m, col) in marks.items():
        ys = [pw[f"{name}_{sn}"]["detect_q05"] for sn, _ in SIG_SCALES]
        ax.plot(xs, ys, marker=m, color=col, label=f"truth $N={name[1:]}$")
        ys2 = [pw[f"{name}_{sn}"]["detect_chi2crit"] for sn, _ in SIG_SCALES]
        ax.plot(xs, ys2, marker=m, ms=3, color=col, ls=":", alpha=0.55,
                lw=0.9)
    ax.axhline(1.0, color="k", ls=":", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("$\\sigma$ scale (1 = current $Z$-pole precision)")
    ax.set_ylabel("detection fraction")
    ax.set_ylim(0, 1.08)
    ax.set_title("(b) Power: registered threshold (solid),\n"
                 "$\\chi^2_{0.95}(4)$ threshold (dotted)")
    ax.legend(fontsize=8, loc="center right")
    ax.annotate("Z-factory stat. floor", xy=(3.3e-3, 0.5), fontsize=7,
                rotation=90, xytext=(4.5e-3, 0.35),
                arrowprops=dict(arrowstyle="->", lw=0.7))

    # (c) per-channel minimum normalized deviation
    ax = axes[2]
    pos = np.arange(K)
    ax.bar(pos, per_ch, color="#d62728", alpha=0.85)
    ax.axhline(2, color="k", ls="--", lw=0.8, label="$2\\sigma$")
    ax.set_yscale("log")
    ax.set_xticks(pos)
    ax.set_xticklabels(LABELS)
    ax.set_ylabel("min$_{N\\leq360,\\,c|N}$ $|f_i - c/N|/\\sigma_i$")
    ax.set_title("(c) Per-channel exclusion depth")
    for i, d in enumerate(per_ch):
        ax.text(i, d * 1.15, f"{d:.0f}$\\sigma$", ha="center", fontsize=7)
    ax.legend(fontsize=8)
    fig.savefig(os.path.join(OUT, "fig_c9_prereg.png"), dpi=170)
    print("saved", os.path.join(OUT, "fig_c9_prereg.png"), flush=True)


def main():
    import sys
    fig_only = "--fig-only" in sys.argv
    jpath = os.path.join(OUT, "c9_prereg_results.json")
    if fig_only and os.path.exists(jpath):
        with open(jpath) as fh:
            prev = json.load(fh)
        t_obs = prev["z"]["T_obs"]
        n_best = prev["z"]["best_N"]
        c_best = prev["z"]["best_c"]
        thr = prev["null"]["q05"]
        T_null = np.asarray(prev.get("T_null"))
        per_ch = prev["z"]["per_channel_min_dev"]
        pw = prev["power"]
        make_figure(t_obs, n_best, c_best, thr, T_null, per_ch, pw)
        return

    print("=" * 70, flush=True)
    print("STAGE 0: DP self-test", flush=True)
    t_obs, n_best, c_best = selftest()

    print("STAGE 1: null calibration (5000 Dirichlet tables, actual sigma)", flush=True)
    null, T_null = null_calibration()
    thr = null["q05"]

    print("STAGE 2: Z-pole application", flush=True)
    p_emp = float((T_null <= t_obs).mean())
    p_absent = float((T_null >= t_obs).mean())
    lam = float(np.sqrt(t_obs / CHI2_CRIT))
    # per-channel minimum normalized deviation at N<=360
    per_ch = []
    for i in range(K):
        d = np.inf
        for N in range(NMIN, NMAX + 1):
            for c in DIVS[N]:
                d = min(d, abs(F_Z[i] - c / N) / S_Z[i])
        per_ch.append(float(d))
    # sum rule check
    sum_dev = float(abs(F_Z.sum() - 1.0) / np.sqrt((S_Z ** 2).sum()))
    # decision
    present = p_emp <= 0.05
    z_res = dict(
        labels=LABELS, f=F_Z.tolist(), sigma=S_Z.tolist(),
        T_obs=float(t_obs), best_N=n_best, best_c=c_best,
        threshold_q05=thr, chi2_crit=CHI2_CRIT,
        p_present=float(p_emp), p_absent_side=float(p_absent),
        decision="present" if present else "absent",
        lambda_inflation=lam,
        per_channel_min_dev=per_ch,
        sum_rule_dev_sigma=sum_dev,
    )
    print(f"Z: T_obs={t_obs:.1f} best N={n_best} c={c_best} "
          f"threshold(q05)={thr:.1f} p={p_emp:.4f} -> {z_res['decision']}; "
          f"lambda={lam:.1f}; per-channel min dev {['%.0f' % d for d in per_ch]} sigma",
          flush=True)

    print("STAGE 3: power", flush=True)
    pw = power(thr)

    print("STAGE 4: sensitivity (unconstrained, N<=5000)", flush=True)
    c2u, Nu, cu = fit_unconstrained(F_Z, S_Z, 5000)
    sens = dict(unconstrained_Nmax5000=dict(chi2=c2u, N=Nu, c=cu))
    print(f"unconstrained: chi2={c2u:.1f} N={Nu} c={cu}", flush=True)

    results = dict(preregistration="review/c9_preregistration.md",
                   freeze_commit="9f30553 (corrected rule; original d3b1160)",
                   null=null, T_null=T_null.tolist(), z=z_res, power=pw,
                   sensitivity=sens,
                   thresholds=dict(chi2_crit=CHI2_CRIT, null_q05=thr))
    with open(os.path.join(OUT, "c9_prereg_results.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    print("saved", os.path.join(OUT, "c9_prereg_results.json"), flush=True)

    make_figure(t_obs, n_best, c_best, thr, T_null, per_ch, pw)

    with open(os.path.join(OUT, "prereg_summary.txt"), "w") as fh:
        fh.write(f"""C9 pre-registered application (freeze 9f30553)
decision rule: present iff p = Prob(T_null <= T_obs) <= 0.05
T_obs = {t_obs:.1f} (best N={n_best}, c={c_best})
null: median={null['median']:.1f} q05={thr:.1f} q95={null['q95']:.1f}
p = {p_emp:.4f} -> {z_res['decision']}
lambda = {lam:.1f} (uncertainties would need to grow by this factor)
per-channel min deviations (sigma): {['%.0f' % d for d in per_ch]}
sum-rule deviation: {sum_dev:.2f} sigma
FPR at chi2_crit: {null['FPR_at_chi2crit']:.4f}
power (current sigma):
""" + "\n".join(
            f"  {k}: detect={v['detect_chi2crit']:.3f} recoverN={v['recover_N']:.3f}"
            for k, v in pw.items() if k.endswith("current")) + f"""
unconstrained N<=5000 sensitivity: chi2={c2u:.1f} (N={Nu})
""")


if __name__ == "__main__":
    main()
