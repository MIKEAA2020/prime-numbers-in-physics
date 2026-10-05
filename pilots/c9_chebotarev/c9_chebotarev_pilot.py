#!/usr/bin/env python3
"""
C9 (Galois-gauge dictionary) pilot attack -- the Chebotarev dictionary check.

Part A: arithmetic substrate.
  A1. Q(i):  split (p=1 mod 4) / inert (p=3 mod 4), Chebotarev 1/2 - 1/2.
      Includes the Chebyshev-bias measurement (finite-X deviation structure).
  A2. S_3 extension Q(2^(1/3)) (x^3-2): splitting types
      (111)<->id: 1/6, (21)<->transpositions: 1/2, (3)<->3-cycles: 1/3.
      Convergence calibration by decade.

Part B: the dictionary-fit protocol (physics side).
  B1. Protocol: k measured branching fractions f_i +/- sigma_i;
      fit a COMMON group order N and class sizes c_i | N with f_i ~ c_i/N.
      Threshold calibrated by Monte Carlo under the generic (structureless)
      null  ->  false-positive rate.
  B2. Injection test: truth = S_3 table {1/6, 1/2, 1/3}.
  B3. Real-data demonstration: Z-boson branching fractions (PDG).

Outputs -> /home/z/my-project/download/pilot_c9_chebotarev/
"""
import json
import os
import numpy as np
from scipy import stats

OUT = "/home/z/my-project/download/pilot_c9_chebotarev"
os.makedirs(OUT, exist_ok=True)


def sieve_primes(xmax):
    """Bool sieve, returns array of primes <= xmax."""
    sieve = np.ones(xmax + 1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(xmax)) + 1):
        if sieve[i]:
            sieve[i * i:: i] = False
    return np.flatnonzero(sieve)


def divisor_list(n):
    ds = [1]
    d = 2
    while d * d <= n:
        if n % d == 0:
            ds.append(d)
            if d != n // d:
                ds.append(n // d)
        d += 1
    ds.append(n)
    return np.array(sorted(ds))


# ============================================================ Part A
def part_a():
    res = {}

    # A1: Q(i)
    print("A1: Q(i) split/inert statistics ...", flush=True)
    X = 10 ** 7
    ps = sieve_primes(X)
    ps = ps[ps > 2]  # exclude ramified prime 2
    res_mod = ps % 4
    n_split = int((res_mod == 1).sum())
    n_inert = int((res_mod == 3).sum())
    N = n_split + n_inert
    chi2 = (n_split - N / 2) ** 2 / (N / 2) + (n_inert - N / 2) ** 2 / (N / 2)
    res["Qi"] = dict(
        X=X, n_split=n_split, n_inert=n_inert,
        f_split=n_split / N, f_inert=n_inert / N,
        chi2=chi2, p_value=float(1 - stats.chi2.cdf(chi2, 1)),
    )
    # Chebyshev bias by decade
    bias = []
    for k in range(2, 8):
        xk = 10 ** k
        pk = ps[ps <= xk]
        r = pk % 4
        bias.append(dict(X=xk, n_split=int((r == 1).sum()), n_inert=int((r == 3).sum()),
                         imbalance=int((r == 3).sum() - (r == 1).sum())))
    res["Qi_bias_decades"] = bias

    # A2: S3 = Gal(Q(2^(1/3)))
    print("A2: S3 splitting types for x^3-2 ...", flush=True)
    out = {}
    for k in range(3, 8):
        xk = 10 ** k
        pk = ps[ps <= xk]
        pk = pk[(pk != 2) & (pk != 3)]  # ramified (disc = -108)
        r3 = pk % 3
        m2 = r3 == 2
        m1 = r3 == 1
        # cubic residue test for p = 1 mod 3
        idx = np.flatnonzero(m1)
        n111 = 0
        for p in pk[idx].tolist():
            if pow(2, (p - 1) // 3, p) == 1:
                n111 += 1
        n21 = int(m2.sum())
        n3 = int(m1.sum()) - n111
        Nt = n111 + n21 + n3
        e = np.array([Nt / 6, Nt / 2, Nt / 3])
        o = np.array([n111, n21, n3])
        chi2 = float(((o - e) ** 2 / e).sum())
        out[str(xk)] = dict(X=xk, n111=n111, n21=n21, n3=n3, total=Nt,
                            f=[n111 / Nt, n21 / Nt, n3 / Nt],
                            chi2=chi2, p=float(1 - stats.chi2.cdf(chi2, 2)))
        print(f"   X=10^{k}: (111)={n111/Nt:.5f} (21)={n21/Nt:.5f} (3)={n3/Nt:.5f} "
              f"chi2={chi2:.1f} p={out[str(xk)]['p']:.3f}", flush=True)
    res["S3"] = out
    return res


# ============================================================ Part B
def fit_dictionary(f_hat, sigma, divlists, Nmax):
    """Scan group orders N <= Nmax; c_i must be a divisor of N.
    Returns best (chi2, N, c_list)."""
    best = (np.inf, None, None)
    k = len(f_hat)
    for N in range(2, Nmax + 1):
        ds = divlists[N]
        if len(ds) < 2:
            continue
        targets = f_hat * N
        # nearest divisor value to each target
        c = np.searchsorted(ds, targets)
        c = np.clip(c, 0, len(ds) - 1)
        cand = np.stack([ds[np.clip(c - 1, 0, len(ds) - 1)], ds[c]], axis=1)
        pick = np.argmin(np.abs(cand - targets[:, None]), axis=1)
        ci = cand[np.arange(k), pick]
        chi2 = float((((f_hat - ci / N) / sigma) ** 2).sum())
        if chi2 < best[0]:
            best = (chi2, N, ci.tolist())
    return best


def part_b():
    res = {}

    Nmax = 360
    print(f"B: precomputing divisors to {Nmax} ...", flush=True)
    divlists = {N: divisor_list(N) for N in range(2, Nmax + 1)}

    # ---- B1: null calibration (false-positive rate) ----
    print("B1: null calibration ...", flush=True)
    null_res = {}
    rng = np.random.default_rng(11)
    for k in (3, 5, 8):
        for sigma in (0.01, 0.003, 0.001):
            trials = 400
            best_chi2 = []
            for _ in range(trials):
                f = rng.dirichlet(np.ones(k))
                best_chi2.append(fit_dictionary(f, np.full(k, sigma), divlists, Nmax)[0])
            best_chi2 = np.array(best_chi2)
            null_res[f"k{k}_sig{sigma}"] = dict(
                k=k, sigma=sigma, Nmax=Nmax,
                thresh95=float(np.quantile(best_chi2, 0.95)),
                median=float(np.median(best_chi2)),
                frac_below_k=float((best_chi2 < stats.chi2.ppf(0.95, k)).mean()),
            )
            print(f"   k={k} sigma={sigma}: median min-chi2={np.median(best_chi2):.1f} "
                  f"95% thresh={np.quantile(best_chi2, 0.95):.1f}", flush=True)
    res["null"] = null_res

    # effective discriminating rule: Nmax*sigma
    rule = {}
    for sigma in (0.01, 0.003, 0.001):
        for nm in (60, 360):
            divs = {N: divlists[N] for N in range(2, nm + 1)}
            rng = np.random.default_rng(5)
            trials = 300
            hit = 0
            for _ in range(trials):
                f = rng.dirichlet(np.ones(5))
                c2 = fit_dictionary(f, np.full(5, sigma), divs, nm)[0]
                if c2 < stats.chi2.ppf(0.95, 5):
                    hit += 1
            rule[f"sig{sigma}_Nmax{nm}"] = hit / trials
    res["null_FPR_scan"] = rule
    print("   FPR scan:", {kk: round(v, 3) for kk, v in rule.items()}, flush=True)

    # ---- B2: injection test (S3 truth) ----
    print("B2: injection test ...", flush=True)
    inj = {}
    for sigma in (0.01, 0.003):
        c2, N, c = fit_dictionary(np.array([1 / 6, 1 / 2, 1 / 3]),
                                  np.full(3, sigma), divlists, Nmax)
        inj[f"clean_sig{sigma}"] = dict(chi2=c2, N=N, c=c)
    # noisy injection: n events per channel, binomial
    rng = np.random.default_rng(3)
    noisy = []
    for n_ev in (300, 3000, 30000):
        f_true = np.array([1 / 6, 1 / 2, 1 / 3])
        cnt = rng.multinomial(n_ev, f_true)
        f_hat = cnt / n_ev
        sig = np.sqrt(np.maximum(f_hat * (1 - f_hat), 1e-6) / n_ev)
        c2, N, c = fit_dictionary(f_hat, sig, divlists, Nmax)
        hit = dict(n_events=n_ev, f_hat=f_hat.tolist(), chi2=c2, N=N, c=c,
                   thresh=null_res[f"k3_sig0.01"]["thresh95"],
                   recovered=(N == 6))
        noisy.append(hit)
        print(f"   n={n_ev}: best N={N} c={c} chi2={c2:.2f} recovered={N == 6}", flush=True)
    res["injection"] = dict(**inj, noisy=noisy)

    # ---- B3: real data (Z boson, PDG) ----
    print("B3: Z-boson branching fractions dictionary fit ...", flush=True)
    f_z = np.array([0.6991, 0.03363, 0.03366, 0.03370, 0.2017])
    s_z = np.array([0.0009, 0.00004, 0.00007, 0.00009, 0.0006])
    labels = ["had", "e", "mu", "tau", "invisible"]
    Nmax_z = 5000
    divs_z = {N: divisor_list(N) for N in range(2, Nmax_z + 1)}
    c2, N, c = fit_dictionary(f_z, s_z, divs_z, Nmax_z)
    # null calibration at this (k, sigma, Nmax) for a fair p-value
    rng = np.random.default_rng(17)
    null_chi2 = []
    for _ in range(300):
        f = rng.dirichlet(np.ones(5))
        # match the heterogeneous sigma pattern
        null_chi2.append(fit_dictionary(f, s_z, divs_z, Nmax_z)[0])
    p_emp = float((np.array(null_chi2) <= c2).mean())
    res["Zboson"] = dict(labels=labels, f=f_z.tolist(), sigma=s_z.tolist(),
                         best_chi2=c2, best_N=N, best_c=c, Nmax=Nmax_z,
                         empirical_p=p_emp,
                         null_chi2_median=float(np.median(null_chi2)))
    print(f"   best N={N} c={c} chi2={c2:.1f} empirical p={p_emp:.3f}", flush=True)

    # minimal events needed: resolution vs |G|
    res["resolution"] = dict(
        note="to resolve density 1/N against neighbours at z sigma: n_events ~ z^2 N^2",
        events_for_N60_z3=9 * 3600,
        events_for_N360_z3=9 * 3600 ** 2,
    )
    return res


def main():
    A = part_a()
    B = part_b()
    with open(os.path.join(OUT, "c9_results.json"), "w") as f:
        json.dump(dict(partA=A, partB=B), f, indent=1)
    print("saved", os.path.join(OUT, "c9_results.json"))


if __name__ == "__main__":
    main()
