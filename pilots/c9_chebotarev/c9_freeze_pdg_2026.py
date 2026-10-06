#!/usr/bin/env python3
"""Freeze the PDG 2026 W-boson and Higgs extracts for the C9 dictionary
protocol (the table-agnostic k-variant of the pre-registered machinery).

New precision content of the 2026 listings relative to the 2024 freeze:
  W:  the four OUR FIT branching fractions are unchanged (e, mu, tau,
      hadrons); the total-width OUR AVERAGE moves to 2.14 +- 0.05 GeV
      (the ATLAS 24CJ result enters the combination).  The dictionary
      statistic uses the fractions only, so the 2026 W fit is a
      provenance refresh of an unchanged vector.
  Higgs: the mu mu channel moves to (3.0 +- 0.9)e-4 (sigma_rel 50% ->
      30%); every other measured channel is unchanged.

Injection truth (frozen here, before any null calibration or data fit):
  W:      c = {3, 3, 6, 12} at N = 24 (every c_i divides 24).
  Higgs:  the minimum-chi2 common-N dictionary of THIS frozen vector
          (c_i | N, N <= 5000), required to lie within one sigma in
          every channel; computed deterministically below and frozen.
          The truth-construction rule is amended from the 2024 extract:
          the 2024 recorded truth {2800, ...} at N = 5040 was not a
          valid dictionary (2800 does not divide 5040), so the 2024
          zero-recovery injection read was confounded; the amendment
          restores a well-posed power measurement.

Pre-registered protocol (identical structure to the 2024 tables, fixed
at freeze time, before any fit):
  P1. Null calibration FIRST: 3000 structureless Dirichlet(k) draws with
      the exact sigma pattern and total mass of the frozen table; common-N
      divisor scan (N in [2, 5000], c_i | N); minimum chi2 per draw; the
      decision threshold is the chi2(k) 95% point; the empirical
      false-positive rate at that threshold is reported.
  P2. Injection check (pipeline power at the table's own sigma): truth =
      the frozen dictionary above; f_hat = truth + Gaussian noise at the
      table's sigma (100 repetitions); recovery = the scan's best fit
      reproduces the rational identity c'_i/N' = c_i/N for all i.
  P3. Real-data fit LAST: the frozen table is fitted with the same scan;
      the signature is declared present iff min-chi2 < chi2_0.95(k) AND
      the empirical p-value against the P1 null is < 0.05.
  P4. Regime notes: per-table (recorded in each extract).

Source (all values):
  F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41,
  2630011 (2026), "W boson" listing, rpp2026-list-w-boson.pdf, and
  "Higgs" listing, rpp2026-list-higgs-boson.pdf,
  https://pdg.lbl.gov/2026/listings/ (downloaded 2026-10-07; file
  sha256 recorded below).
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c9_ktable_fit import divisor_list, fit_dictionary  # noqa: E402

OUT_DIR = "/home/z/my-project/repo-push/pilots/c9_chebotarev"
W_PDF = "/tmp/wboson26.pdf"
H_PDF = "/tmp/higgs_boson26.pdf"
NMAX = 5000


def sha(path):
    if os.path.exists(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    return ""


def best_valid_dictionary(f, sigma, nmax):
    """Minimum-chi2 common-N dictionary (c_i | N, N <= nmax) of the frozen
    vector, required to lie within one sigma in every channel.  Returns
    (chi2, N, c) or None."""
    divlists = {N: divisor_list(N) for N in range(2, nmax + 1)}
    best = (np.inf, None, None)
    k = len(f)
    f = np.asarray(f, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    for N in range(2, nmax + 1):
        ds = divlists[N]
        if len(ds) < 2:
            continue
        targets = f * N
        c = np.searchsorted(ds, targets)
        c = np.clip(c, 0, len(ds) - 1)
        cand = np.stack([ds[np.clip(c - 1, 0, len(ds) - 1)], ds[c]], axis=1)
        pick = np.argmin(np.abs(cand - targets[:, None]), axis=1)
        ci = cand[np.arange(k), pick]
        dev = np.abs(f - ci / N) / sigma
        if dev.max() > 1.0:
            continue
        chi2 = float((((f - ci / N) / sigma) ** 2).sum())
        if chi2 < best[0]:
            best = (chi2, N, ci.tolist())
    return None if best[1] is None else best


import numpy as np  # noqa: E402

# ---- W table (2026): OUR FIT branching fractions ----
W = {
    "labels": ["e_nu", "mu_nu", "tau_nu", "hadrons"],
    "f": [0.1071, 0.1063, 0.1138, 0.6741],
    "sigma": [0.0016, 0.0015, 0.0021, 0.0027],
    "total_width_GeV": [2.14, 0.05],
    "injection": {"N": 24, "c": [3, 3, 6, 12],
                  "note": "W-like shape; every c_i divides 24 (unchanged "
                          "from the 2024 truth, which is a valid "
                          "dictionary)"},
}

# ---- Higgs table (2026): the listing's decay-mode fractions ----
H = {
    "labels": ["bb", "WW", "ZZ", "tautau", "gammagamma", "Zgamma", "mumu"],
    "f": [0.53, 0.257, 0.0280, 0.060, 0.00250, 0.0034, 0.00030],
    "sigma": [0.08, 0.025, 0.0030, 0.0075, 0.00020, 0.0011, 0.00009],
}

hb = best_valid_dictionary(H["f"], H["sigma"], NMAX)
if hb is None:
    raise SystemExit("no valid within-one-sigma dictionary for the 2026 "
                     "Higgs vector: cannot freeze an injection truth")
H["injection"] = {
    "N": hb[1], "c": hb[2],
    "note": "minimum-chi2 common-N dictionary of this frozen vector "
            f"(N = {hb[1]}, chi2 = {hb[0]:.3f}), within one sigma in "
            "every channel; rule amended from the 2024 extract, whose "
            "recorded truth was not a valid dictionary (2800 does not "
            "divide 5040)",
}

PROTOCOL = {
    "P1_null_first": "3000 Dirichlet(k) draws, matched sigma pattern and "
                     "total mass, common-N scan N in [2,5000]; threshold "
                     "chi2_0.95(k)",
    "P2_injection": "truth frozen in this file (valid dictionary, every "
                    "c_i divides N), Gaussian noise at the table sigma, "
                    "100 repetitions, recovery = rational identity of "
                    "proportions",
    "P3_decision": "signature present iff min-chi2 < chi2_0.95(k) AND "
                   "empirical p < 0.05 vs the P1 null",
    "P4_regime": None,      # per-table, set below
}

W_PROTOCOL = dict(PROTOCOL)
W_PROTOCOL["P4_regime"] = (
    "k = 4 granularity amendment: only four W channels are measured, so "
    "the k = 5/7 calibrated granularity does not exist for this table; "
    "the null calibration runs at k = 4 with the table's own sigma, so "
    "the false-positive rate is controlled.  sigma_rel = 1.4-1.8% on "
    "the leptonic channels and 0.4% on hadrons, above the Z-pole "
    "regime; the four-channel fit has three independent constraints, "
    "and the power is correspondingly limited (P2 quantifies it).  The "
    "2026 listing carries the same OUR FIT fractions as 2024; the "
    "total-width OUR AVERAGE moves to 2.14 +- 0.05 GeV (ATLAS 24CJ "
    "enters the combination) and the dictionary statistic is unchanged "
    "because it uses the fractions only.")

H_PROTOCOL = dict(PROTOCOL)
H_PROTOCOL["P4_regime"] = (
    "sigma_rel = 8-30% (the mu mu channel improves from 50% to 30% in "
    "the 2026 listing), two orders of magnitude above the calibrated "
    "sigma <= 0.3% regime: the channels are signal-strength-constrained "
    "evaluations with Standard Model theory input, not direct fraction "
    "measurements.  The null calibration carries the same weakness, so "
    "the false-positive rate is controlled but the power is minimal; "
    "the P2 injection (a valid dictionary truth, amended per the note "
    "above) quantifies the loss.  The seven measured channels sum to "
    "0.8813 of the width (gg, cc, and rare modes are unmeasured); the "
    "dictionary hypothesis constrains only the measured f_i = c_i/N "
    "with c_i | N, not the partition of the total.")

CITATION = ("F. Takahashi et al. (Particle Data Group), Int. J. Mod. "
            "Phys. A 41, 2630011 (2026)")

extracts = {
    "pdg_w_extract_2026.json": dict(
        frozen="2026-10-07",
        source=dict(citation=CITATION,
                    url="https://pdg.lbl.gov/2026/listings/"
                        "rpp2026-list-w-boson.pdf",
                    downloaded="2026-10-07", pdf_sha256=sha(W_PDF),
                    total_width_GeV=W["total_width_GeV"],
                    note="OUR FIT branching fractions for e/mu/tau and "
                         "hadrons (values unchanged from the 2024 "
                         "listing); width OUR AVERAGE 2.14 +- 0.05 GeV"),
        k=4, labels=W["labels"], f=W["f"], sigma=W["sigma"],
        sigma_rel=[round(s / f, 5) for s, f in zip(W["sigma"], W["f"])],
        injection=W["injection"],
        protocol=W_PROTOCOL,
    ),
    "pdg_higgs_extract_2026.json": dict(
        frozen="2026-10-07",
        source=dict(citation=CITATION,
                    url="https://pdg.lbl.gov/2026/listings/"
                        "rpp2026-list-higgs-boson.pdf",
                    downloaded="2026-10-07", pdf_sha256=sha(H_PDF),
                    note="decay-mode table of the 2026 Higgs listing: "
                         "signal-strength-constrained evaluations with SM "
                         "theory input; tau tau error symmetrized "
                         "(6.0 +0.8/-0.7)%; mu mu updated to "
                         "(3.0 +- 0.9)e-4"),
        k=7, labels=H["labels"], f=H["f"], sigma=H["sigma"],
        sigma_rel=[round(s / f, 5) for s, f in zip(H["sigma"], H["f"])],
        injection=H["injection"],
        protocol=H_PROTOCOL,
    ),
}

os.makedirs(OUT_DIR, exist_ok=True)
for name, ex in extracts.items():
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as fh:
        json.dump(ex, fh, indent=1)
    print("frozen extract ->", path)
    for l, f, s in zip(ex["labels"], ex["f"], ex["sigma"]):
        print(f"  {l:12s} f={f:.5f} sigma={s:.5f} "
              f"sigma_rel={s / f:.2%}")
    print(f"  sum(f) = {sum(ex['f']):.6f}")
    print(f"  injection: N={ex['injection']['N']} "
          f"c={ex['injection']['c']}")
