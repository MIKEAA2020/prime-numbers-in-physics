#!/usr/bin/env python3
"""C9 dictionary fit on the frozen PDG 2026 tables (committed at f7100fe
before this run): the table-agnostic runner of the pre-registered
protocol applied to pdg_w_extract_2026.json / pdg_higgs_extract_2026.json.

Identical machinery to the 2024 run (P1 null first, P2 injection, P3
data fit last); additionally the Higgs exploratory post-hoc
bootstrap-around-data diagnostic is recomputed and recorded outside the
pre-registered decision, as in the 2024 run.

Outputs -> /home/z/my-project/download/pilot_c9_chebotarev/
           c9_ktable_w2026_results.json, c9_ktable_higgs2026_results.json
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c9_ktable_fit import (BASE, OUT, divisor_list, fit_dictionary,
                           rational_match, NMAX, TRIALS, INJ_REPS)


def posthoc_bootstrap(f_z, s_z, data_chi2, seed, draws=200):
    """Exploratory (NOT part of the pre-registered decision): bootstrap
    null around the data vector -- Gaussian noise at the table sigma,
    same scan.  Measures the scan-selection effect at the data's channel
    hierarchy; the pre-registered Dirichlet null is not shape-matched to
    a 2000:1 channel-magnitude hierarchy."""
    divlists = {N: divisor_list(N) for N in range(2, NMAX + 1)}
    rng = np.random.default_rng(seed)
    chi2 = np.empty(draws)
    for i in range(draws):
        f = f_z + rng.standard_normal(len(f_z)) * s_z
        chi2[i] = fit_dictionary(f, s_z, divlists, NMAX)[0]
    return dict(note="NOT part of the pre-registered decision: bootstrap "
                     "null around the data vector (Gaussian noise at the "
                     "table sigma, same scan).  The pre-registered null "
                     "(structureless Dirichlet at matched sigma and total) "
                     "does not match the channel-magnitude hierarchy of "
                     "this table.",
                draws=draws, median=float(np.median(chi2)),
                q05=float(np.quantile(chi2, 0.05)),
                min=float(chi2.min()),
                P_below_data=float((chi2 <= data_chi2).mean()))


def run_2026(extract_name, out_name, seed, posthoc_seed=None):
    import c9_ktable_fit as kt
    res = kt.run_table(os.path.join(BASE, extract_name), out_name, seed)
    if posthoc_seed is not None:
        f_z = np.array(res["f"])
        s_z = np.array(res["sigma"])
        ph = posthoc_bootstrap(f_z, s_z, res["fit"]["min_chi2"],
                               posthoc_seed)
        path = os.path.join(OUT, out_name)
        d = json.load(open(path))
        d["exploratory_posthoc"] = ph
        with open(path, "w") as fh:
            json.dump(d, fh, indent=1)
        print(f"post-hoc bootstrap: P(chi2 <= data) = "
              f"{ph['P_below_data']:.3f}", flush=True)
    return res


def main():
    t0 = time.time()
    run_2026("pdg_w_extract_2026.json", "c9_ktable_w2026_results.json",
             20261008)
    run_2026("pdg_higgs_extract_2026.json",
             "c9_ktable_higgs2026_results.json", 20261009,
             posthoc_seed=20261010)
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
