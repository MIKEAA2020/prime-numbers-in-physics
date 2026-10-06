#!/usr/bin/env python3
"""C9 k=7 granularity variant: the Chebotarev dictionary check at seven
channels against the frozen PDG 2024 Z-boson extract.

Pre-registered order (pdg_z_extract_2024.json, committed before this run):
  P1 null calibration FIRST (3000 matched-sigma Dirichlet(7) draws),
  P2 injection check,
  P3 real-data fit LAST, decision by the P1 null.

The dictionary hypothesis: a measured k-channel branching table f_i +/-
sigma_i realizes class proportions of a common group order N,
f_i = c_i / N with integers c_i | N.  The statistic is the minimum
chi2 over all N <= Nmax and all divisor assignments c_i.  Finer
granularity (k=5 -> k=7) tightens the integer constraints; the null
calibration measures how much of that tightening is generic.
"""
import json
import os
import time

import numpy as np
from scipy import stats

EXTRACT = ("/home/z/my-project/repo-push/pilots/c9_chebotarev/"
           "pdg_z_extract_2024.json")
OUT = "/home/z/my-project/download/pilot_c9_chebotarev"
os.makedirs(OUT, exist_ok=True)


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


def fit_dictionary(f_hat, sigma, divlists, Nmax):
    """Scan group orders N <= Nmax; c_i must be a divisor of N."""
    best = (np.inf, None, None)
    k = len(f_hat)
    for N in range(2, Nmax + 1):
        ds = divlists[N]
        if len(ds) < 2:
            continue
        targets = f_hat * N
        c = np.searchsorted(ds, targets)
        c = np.clip(c, 0, len(ds) - 1)
        cand = np.stack([ds[np.clip(c - 1, 0, len(ds) - 1)], ds[c]], axis=1)
        pick = np.argmin(np.abs(cand - targets[:, None]), axis=1)
        ci = cand[np.arange(k), pick]
        chi2 = float((((f_hat - ci / N) / sigma) ** 2).sum())
        if chi2 < best[0]:
            best = (chi2, N, ci.tolist())
    return best


def main():
    ex = json.load(open(EXTRACT))
    f_z = np.array(ex["f"])
    s_z = np.array(ex["sigma"])
    k = ex["k"]
    labels = ex["labels"]
    Nmax = 5000
    print(f"frozen extract: k={k} channels, Nmax={Nmax}", flush=True)
    print("channels:", {l: (round(f, 5), round(s, 5))
                        for l, f, s in zip(labels, f_z, s_z)}, flush=True)

    t0 = time.time()
    divlists = {N: divisor_list(N) for N in range(2, Nmax + 1)}
    print(f"divisor tables to {Nmax}: {time.time() - t0:.1f}s", flush=True)

    # ---- P1: null calibration (BEFORE the data fit) ----
    print("P1: null calibration, 3000 matched-sigma Dirichlet draws...",
          flush=True)
    t0 = time.time()
    rng = np.random.default_rng(20261005)
    trials = 3000
    null_chi2 = np.empty(trials)
    for i in range(trials):
        f = rng.dirichlet(np.ones(k))
        null_chi2[i] = fit_dictionary(f, s_z, divlists, Nmax)[0]
    thresh95 = float(np.quantile(null_chi2, 0.95))
    chi2_95 = float(stats.chi2.ppf(0.95, k))
    fpr = float((null_chi2 < chi2_95).mean())
    p_floor = 1.0 / trials
    print(f"  null: median={np.median(null_chi2):.2f} q95={thresh95:.2f} "
          f"chi2_0.95(k={k})={chi2_95:.2f} FPR@chi2_0.95={fpr:.4f} "
          f"({time.time() - t0:.0f}s)", flush=True)

    # ---- P2: injection check (pipeline power) ----
    # AMENDMENT (recorded): the pre-registered spec c={6,5,10,20,3,7,4} at
    # N=60 is infeasible -- c=7 does not divide 60, so no dictionary table
    # exists at that N.  The executed injection uses the nearest VALID table
    # c={6,5,10,20,3,10,4} (every c_i divides 60, sum 58 <= 60), and the
    # recovery criterion is the rational identity c'_i/N' = c_i/N for all i
    # (the scan is known to prefer highly-composite N whose finer divisor
    # grids absorb noise better; the minimal-N representative is reported).
    print("P2: injection (N=60 truth c={6,5,10,20,3,10,4}) ...", flush=True)
    c_true = np.array([6, 5, 10, 20, 3, 10, 4])
    f_true = c_true / 60.0
    rng2 = np.random.default_rng(77)
    inj = []
    for n_ev in (3000, 30000, 300000):
        cnt = rng2.multinomial(n_ev, f_true)
        f_hat = cnt / n_ev
        sig = np.sqrt(np.maximum(f_hat * (1 - f_hat), 1e-12) / n_ev)
        c2, N, c = fit_dictionary(f_hat, sig, divlists, Nmax)
        # rational identity: every recovered c'/N' equals the truth c_i/60
        prop_match = bool(N is not None and all(
            abs(ci / N - ct / 60.0) < 1e-9 for ci, ct in zip(c, c_true)))
        # minimal representative of the recovered table
        g = 0
        for ci in c:
            g = np.gcd(g, ci)
        g = np.gcd(g, N) if g > 0 else 1
        n_min = N // g if g > 0 else N
        inj.append(dict(n_events=n_ev, chi2=c2, N=N, c=c,
                        rational_match=prop_match, N_minimal=int(n_min),
                        recovered=(N == 60)))
        print(f"  n={n_ev}: N={N} chi2={c2:.2f} rational_match={prop_match} "
              f"N_minimal={n_min}", flush=True)

    # ---- P3: real-data fit (LAST) ----
    print("P3: frozen-extract dictionary fit ...", flush=True)
    c2, N, c = fit_dictionary(f_z, s_z, divlists, Nmax)
    p_emp = float((null_chi2 <= c2).mean())
    decision = dict(
        min_chi2=c2, best_N=N, best_c=c,
        chi2_095=chi2_95, empirical_p=p_emp,
        passes_threshold=bool(c2 < chi2_95),
        passes_p=bool(p_emp < 0.05),
        signature_present=bool(c2 < chi2_95 and p_emp < 0.05),
    )
    print(f"  best N={N} c={c} chi2={c2:.2f} empirical p={p_emp:.4f} "
          f"-> signature_present={decision['signature_present']}",
          flush=True)

    res = dict(
        extract=EXTRACT,
        frozen=ex["frozen"],
        k=k, Nmax=Nmax,
        labels=labels, f=f_z.tolist(), sigma=s_z.tolist(),
        null=dict(trials=trials, seed=20261005,
                  median=float(np.median(null_chi2)),
                  q95=thresh95, chi2_095_k=chi2_95, FPR_at_chi2_095=fpr,
                  min=float(null_chi2.min()),
                  n_below_data=int((null_chi2 <= c2).sum())),
        injection=inj,
        injection_amendment=("pre-registered c={6,5,10,20,3,7,4} at N=60 is "
                              "infeasible (7 does not divide 60); executed "
                              "with the valid table c={6,5,10,20,3,10,4}; "
                              "criterion = rational identity of proportions"),
        fit=decision,
        regime_note=ex["protocol"]["P4_regime"],
    )
    out = os.path.join(OUT, "c9_k7_results.json")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print("saved", out)


if __name__ == "__main__":
    main()
