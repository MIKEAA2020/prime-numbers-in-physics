#!/usr/bin/env python3
"""C9 dictionary fit on frozen tables: the table-agnostic runner of the
pre-registered protocol (P1 null calibration first, P2 injection check,
P3 real-data fit last; P4 regime recorded in each extract).

Applies the committed machinery to the W-boson (k=4) and Higgs (k=7)
extracts frozen in pdg_w_extract_2024.json / pdg_higgs_extract_2024.json
(committed before this run).  The statistic is the minimum chi2 over all
common group orders N <= Nmax with integer assignments c_i | N; the
dictionary hypothesis constrains each measured fraction f_i = c_i / N
(not the partition of the total).

Outputs -> /home/z/my-project/download/pilot_c9_chebotarev/
           c9_ktable_w_results.json, c9_ktable_higgs_results.json
"""
import json
import os
import time

import numpy as np
from scipy import stats

BASE = ("/home/z/my-project/repo-push/pilots/c9_chebotarev")
OUT = "/home/z/my-project/download/pilot_c9_chebotarev"
os.makedirs(OUT, exist_ok=True)

NMAX = 5000
TRIALS = 3000
INJ_REPS = 100


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


def rational_match(c_fit, N_fit, c_true, N_true):
    if N_fit is None:
        return False
    return all(abs(ci / N_fit - ct / N_true) < 1e-9
               for ci, ct in zip(c_fit, c_true))


def run_table(extract_path, out_name, seed):
    ex = json.load(open(extract_path))
    f_z = np.array(ex["f"])
    s_z = np.array(ex["sigma"])
    k = ex["k"]
    labels = ex["labels"]
    total = float(f_z.sum())
    print(f"frozen extract: {os.path.basename(extract_path)} k={k} "
          f"Nmax={NMAX} total={total:.4f}", flush=True)
    print("channels:", {l: (round(f, 5), round(s, 5))
                        for l, f, s in zip(labels, f_z, s_z)}, flush=True)

    t0 = time.time()
    divlists = {N: divisor_list(N) for N in range(2, NMAX + 1)}
    print(f"divisor tables to {NMAX}: {time.time() - t0:.1f}s", flush=True)

    # ---- P1: null calibration (BEFORE the data fit) ----
    print(f"P1: null calibration, {TRIALS} matched-sigma Dirichlet({k}) "
          f"draws (total mass {total:.4f})...", flush=True)
    t0 = time.time()
    rng = np.random.default_rng(seed)
    null_chi2 = np.empty(TRIALS)
    for i in range(TRIALS):
        f = rng.dirichlet(np.ones(k)) * total
        null_chi2[i] = fit_dictionary(f, s_z, divlists, NMAX)[0]
    thresh95 = float(np.quantile(null_chi2, 0.95))
    chi2_95 = float(stats.chi2.ppf(0.95, k))
    fpr = float((null_chi2 < chi2_95).mean())
    print(f"  null: median={np.median(null_chi2):.3f} q95={thresh95:.3f} "
          f"chi2_0.95(k={k})={chi2_95:.3f} FPR@chi2_0.95={fpr:.4f} "
          f"({time.time() - t0:.0f}s)", flush=True)

    # ---- P2: injection check (pipeline power at the table's sigma) ----
    inj = ex["injection"]
    c_true = np.array(inj["c"], dtype=float)
    N_true = inj["N"]
    f_true = c_true / N_true
    rng2 = np.random.default_rng(seed + 1)
    rec = 0
    chi2s = []
    for r in range(INJ_REPS):
        f_hat = f_true + rng2.standard_normal(k) * s_z
        c2, N, c = fit_dictionary(f_hat, s_z, divlists, NMAX)
        chi2s.append(c2)
        if rational_match(c, N, c_true, N_true):
            rec += 1
    inj_res = dict(N=N_true, c=inj["c"], reps=INJ_REPS,
                   rational_recovery=rec / INJ_REPS,
                   median_chi2=float(np.median(chi2s)),
                   note=inj["note"])
    print(f"P2: injection N={N_true} c={inj['c']}: rational-identity "
          f"recovery {rec}/{INJ_REPS} ({rec / INJ_REPS:.1%}), "
          f"median min-chi2={np.median(chi2s):.2f}", flush=True)

    # ---- P3: real-data fit (LAST) ----
    print("P3: frozen-extract dictionary fit ...", flush=True)
    c2, N, c = fit_dictionary(f_z, s_z, divlists, NMAX)
    p_emp = float((null_chi2 <= c2).mean())
    decision = dict(
        min_chi2=c2, best_N=N, best_c=c,
        chi2_095=chi2_95, empirical_p=p_emp,
        passes_threshold=bool(c2 < chi2_95),
        passes_p=bool(p_emp < 0.05),
        signature_present=bool(c2 < chi2_95 and p_emp < 0.05),
    )
    print(f"  best N={N} c={c} chi2={c2:.3f} empirical p={p_emp:.4f} "
          f"-> signature_present={decision['signature_present']}",
          flush=True)

    res = dict(
        extract=extract_path, frozen=ex["frozen"], k=k, Nmax=NMAX,
        labels=labels, f=f_z.tolist(), sigma=s_z.tolist(),
        null=dict(trials=TRIALS, seed=seed,
                  median=float(np.median(null_chi2)), q95=thresh95,
                  chi2_095_k=chi2_95, FPR_at_chi2_095=fpr,
                  min=float(null_chi2.min()),
                  n_below_data=int((null_chi2 <= c2).sum())),
        injection=inj_res,
        fit=decision,
        regime_note=ex["protocol"]["P4_regime"],
    )
    out = os.path.join(OUT, out_name)
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print("saved", out, flush=True)
    return res


def main():
    for name, extract, seed in (
            ("c9_ktable_w_results.json", "pdg_w_extract_2024.json",
             20261006),
            ("c9_ktable_higgs_results.json", "pdg_higgs_extract_2024.json",
             20261007)):
        run_table(os.path.join(BASE, extract), name, seed)
        print()


if __name__ == "__main__":
    main()
