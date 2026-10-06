#!/usr/bin/env python3
"""Freeze the PDG 2024 W-boson and Higgs extracts for the C9 dictionary
protocol (the table-agnostic k-variant of the pre-registered machinery).

Both extracts are frozen (written + committed to the repository) BEFORE
any dictionary fit is run, with the analysis protocol embedded in each
file.  The channel count k is set by the frozen table; the protocol
structure (null calibration first, injection check, real-data fit last,
matched-sigma null) is the committed one.

  W table (k = 4 -- the natural granularity; the k = 5/7 calibrated
  granularity does not exist for W, since only four channels are
  measured; recorded as a granularity amendment):
      e nu, mu nu, tau nu (OUR FIT), hadrons (OUR FIT).
      Gamma_W = 2.085 +- 0.042 GeV (OUR FIT) is recorded for provenance;
      the dictionary statistic uses the fractions only.

  Higgs table (k = 7 -- the seven measured channels of the listing's
  decay-mode table):
      bb, WW*, ZZ*, tau tau (asymmetric error symmetrized), gamma gamma,
      Z gamma, mu mu.  These are signal-strength-constrained evaluations
      with Standard Model theory input (the listing's own provenance);
      sigma_rel = 8-50%, two orders of magnitude outside the
      sigma <= 0.3% regime in which the k = 5/k = 7 protocol was
      calibrated at the Z pole.  The application is therefore
      power-limited by design; the P2 injection quantifies by how much.

Pre-registered protocol (identical structure for both tables, fixed at
freeze time, before any fit):
  P1. Null calibration FIRST: 3000 structureless Dirichlet(k) draws with
      the exact sigma pattern and total mass of the frozen table; common-N
      divisor scan (N in [2, 5000], c_i | N); minimum chi2 per draw; the
      decision threshold is the chi2(k) 95% point; the empirical
      false-positive rate at that threshold is reported.
  P2. Injection check (pipeline power at the table's own sigma):
        W:     truth c = {3, 3, 6, 12} at N = 24 (a W-like shape; every
               c_i divides 24, sum = 24).
        Higgs: truth = the divisor-nearest dictionary to the measured
               vector at N = 5040 (frozen below), i.e. a valid dictionary
               table located at the measured values within every channel
               sigma; the criterion is the rational identity c'_i/N' =
               c_i/N for all i.
      For each: f_hat = truth + Gaussian noise at the table's sigma
      (100 repetitions); recovery = the scan's best fit reproduces the
      rational identity.
  P3. Real-data fit LAST: the frozen table is fitted with the same scan;
      the signature is declared present iff min-chi2 < chi2_0.95(k) AND
      the empirical p-value against the P1 null is < 0.05.
  P4. Regime notes: per-table (recorded in each extract).

Sources (all values):
  S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024),
  "W boson" listing, rpp2024-list-w-boson.pdf, and
  "Higgs" listing, rpp2024-list-higgs-boson.pdf,
  https://pdg.lbl.gov/2024/listings/ (downloaded 2026-10-06; file
  sha256 recorded below).
"""
import hashlib
import json
import os

OUT_DIR = "/home/z/my-project/repo-push/pilots/c9_chebotarev"
W_PDF = "/tmp/wboson24.pdf"
H_PDF = "/tmp/higgs_boson24.pdf"


def sha(path):
    if os.path.exists(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    return ""


# ---- W table: OUR FIT branching fractions (%) ----
W = {
    "labels": ["e_nu", "mu_nu", "tau_nu", "hadrons"],
    "f": [0.1071, 0.1063, 0.1138, 0.6741],
    "sigma": [0.0016, 0.0015, 0.0021, 0.0027],
    "total_width_GeV": [2.085, 0.042],
    "injection": {"N": 24, "c": [3, 3, 6, 12],
                  "note": "W-like shape; every c_i divides 24"},
}

# ---- Higgs table: the listing's decay-mode fractions ----
H = {
    "labels": ["bb", "WW", "ZZ", "tautau", "gammagamma", "Zgamma", "mumu"],
    "f": [0.53, 0.257, 0.0280, 0.060, 0.00250, 0.0034, 0.00026],
    "sigma": [0.08, 0.025, 0.0030, 0.0075, 0.00020, 0.0011, 0.00013],
    "injection": {"N": 5040, "c": [2800, 1260, 140, 315, 12, 18, 1],
                  "note": "divisor-nearest dictionary to the measured "
                          "vector at N = 5040 (each c_i divides 5040; "
                          "within every channel sigma)"},
}

PROTOCOL = {
    "P1_null_first": "3000 Dirichlet(k) draws, matched sigma pattern and "
                     "total mass, common-N scan N in [2,5000]; threshold "
                     "chi2_0.95(k)",
    "P2_injection": "table-specific truth (frozen in this file), Gaussian "
                    "noise at the table sigma, 100 repetitions, recovery = "
                    "rational identity of proportions",
    "P3_decision": "signature present iff min-chi2 < chi2_0.95(k) AND "
                   "empirical p < 0.05 vs the P1 null",
    "P4_regime": None,      # per-table, set below
}

W_PROTOCOL = dict(PROTOCOL)
W_PROTOCOL["P4_regime"] = (
    "k = 4 granularity amendment: only four W channels are measured, so "
    "the k = 5/7 calibrated granularity does not exist for this table; "
    "the null calibration runs at k = 4 with the table's own sigma, so "
    "the false-positive rate is controlled.  sigma_rel = 1.4-1.8% on the "
    "leptonic channels and 0.4% on hadrons, above the Z-pole regime; the "
    "four-channel fit has three independent constraints, and the power "
    "is correspondingly limited (P2 quantifies it).")

H_PROTOCOL = dict(PROTOCOL)
H_PROTOCOL["P4_regime"] = (
    "sigma_rel = 8-50%, two orders of magnitude above the calibrated "
    "sigma <= 0.3% regime: the channels are signal-strength-constrained "
    "evaluations with Standard Model theory input, not direct fraction "
    "measurements.  The null calibration carries the same weakness, so "
    "the false-positive rate is controlled but the power is minimal; the "
    "P2 injection quantifies the loss.  The seven measured channels sum "
    "to 0.881 of the width (gg, cc, and rare modes are unmeasured); the "
    "dictionary hypothesis constrains only the measured f_i = c_i/N with "
    "c_i | N, not the partition of the total.")

CITATION = ("S. Navas et al. (Particle Data Group), Phys. Rev. D 110, "
            "030001 (2024)")

extracts = {
    "pdg_w_extract_2024.json": dict(
        frozen="2026-10-06",
        source=dict(citation=CITATION,
                    url="https://pdg.lbl.gov/2024/listings/"
                        "rpp2024-list-w-boson.pdf",
                    downloaded="2026-10-06", pdf_sha256=sha(W_PDF),
                    total_width_GeV=W["total_width_GeV"],
                    note="OUR FIT branching fractions for e/mu/tau and "
                         "hadrons; width from OUR FIT"),
        k=4, labels=W["labels"], f=W["f"], sigma=W["sigma"],
        sigma_rel=[round(s / f, 5) for s, f in zip(W["sigma"], W["f"])],
        injection=W["injection"],
        protocol=W_PROTOCOL,
    ),
    "pdg_higgs_extract_2024.json": dict(
        frozen="2026-10-06",
        source=dict(citation=CITATION,
                    url="https://pdg.lbl.gov/2024/listings/"
                        "rpp2024-list-higgs-boson.pdf",
                    downloaded="2026-10-06", pdf_sha256=sha(H_PDF),
                    note="decay-mode table of the Higgs listing: "
                         "signal-strength-constrained evaluations with SM "
                         "theory input; tau tau error symmetrized "
                         "(6.0 +0.8/-0.7)%"),
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
