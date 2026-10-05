#!/usr/bin/env python3
"""Freeze the PDG 2024 Z-boson extract for the C9 k=7 dictionary variant.

The extract is frozen (written + committed to the repository) BEFORE the k=7
dictionary fit is run, with the pre-registered analysis protocol embedded in
the file.  Channels are the seven-flavour decomposition of the Z width:

    ee, mumu, tautau, invisible(nunu), cc, bb, light(uds)

Leptonic branching fractions are derived from the OUR FIT partial widths and
the OUR EVALUATION total width; the hadronic sub-channels are taken directly
from the PDG branching-fraction block; the light-jet fraction is
hadrons - cc - bb with independent-error propagation.

Source (all values):
  S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024),
  "Z boson" particle listing, rpp2024-list-z-boson.pdf,
  https://pdg.lbl.gov/2024/listings/rpp2024-list-z-boson.pdf
  (downloaded 2026-10-05; file sha256 recorded below)

Pre-registered k=7 protocol (fixed at freeze time, before any fit):
  P1. Null calibration FIRST: 3000 structureless Dirichlet(7) draws with the
      exact heterogeneous sigma pattern of this table; each draw is fitted
      with the common-N divisor scan (N in [2, 5000], c_i | N) and the
      minimum chi2 recorded.  The decision threshold is the chi2(7) 95%
      point; the empirical false-positive rate at that threshold is
      reported.
  P2. Injection check: a known 7-channel rational table (N=60,
      c = {6,5,10,20,3,7,4}) with binomial event noise at
      n = 3e3/3e4/3e5 must recover N=60 at the two larger event counts.
  P3. Real-data fit LAST: the frozen table is fitted with the same scan;
      the signature is declared present iff min-chi2 < chi2_0.95(7) AND the
      empirical p-value against the P1 null is < 0.05.
  P4. Regime note: the cc and light-jet channels carry sigma_rel of 1.7%
      and 0.5%, outside the sigma <= 0.3% validity regime calibrated at
      k=5; these channels contribute weak constraints and the null
      calibration carries the same weakness, so the false-positive rate
      is controlled but the power is concentrated in the five precise
      channels.
"""
import hashlib
import json
import os

OUT_DIR = "/home/z/my-project/repo-push/pilots/c9_chebotarev"
SRC_PDF = "/tmp/zboson24.pdf"

GAMMA_TOTAL = 2495.5   # MeV, OUR EVALUATION 2.4955 +- 0.0023 GeV
SIGMA_TOTAL = 2.3      # MeV

# PDG 2024 values: partial widths (MeV, OUR FIT) and branching fractions
pw = {
    "ee":   (83.91, 0.12),
    "mumu": (83.99, 0.18),
    "tautau": (84.08, 0.22),
}
fr = {
    "invisible": (0.20000, 0.00055),
    "hadrons":   (0.69911, 0.00056),
    "cc":        (0.1203, 0.0021),
    "bb":        (0.1512, 0.0005),
}

channels = []
for name, (g, sg) in pw.items():
    f = g / GAMMA_TOTAL
    sf = (sg ** 2 + (g * SIGMA_TOTAL / GAMMA_TOTAL) ** 2) ** 0.5 / GAMMA_TOTAL
    channels.append((name, f, sf))
f_light = fr["hadrons"][0] - fr["cc"][0] - fr["bb"][0]
s_light = (fr["hadrons"][1] ** 2 + fr["cc"][1] ** 2 + fr["bb"][1] ** 2) ** 0.5
channels.append(("invisible", fr["invisible"][0], fr["invisible"][1]))
channels.append(("cc", fr["cc"][0], fr["cc"][1]))
channels.append(("bb", fr["bb"][0], fr["bb"][1]))
channels.append(("light_uds", f_light, s_light))

labels = [c[0] for c in channels]
fs = [c[1] for c in channels]
ss = [c[2] for c in channels]

pdf_sha = ""
if os.path.exists(SRC_PDF):
    pdf_sha = hashlib.sha256(open(SRC_PDF, "rb").read()).hexdigest()

extract = {
    "frozen": "2026-10-05",
    "source": {
        "citation": "S. Navas et al. (Particle Data Group), Phys. Rev. D 110, "
                    "030001 (2024), Z boson listing",
        "url": "https://pdg.lbl.gov/2024/listings/rpp2024-list-z-boson.pdf",
        "downloaded": "2026-10-05",
        "pdf_sha256": pdf_sha,
        "total_width_MeV": [GAMMA_TOTAL, SIGMA_TOTAL],
        "note": "OUR FIT partial widths for leptons; branching-fraction "
                "block for hadrons/invisible/cc/bb; light = hadrons-cc-bb",
    },
    "k": 7,
    "labels": labels,
    "f": fs,
    "sigma": ss,
    "sigma_rel": [round(s / f, 5) for s, f in zip(ss, fs)],
    "protocol": {
        "P1_null_first": "3000 Dirichlet(7) draws, matched sigma pattern, "
                         "common-N scan N in [2,5000]; threshold chi2_0.95(7)",
        "P2_injection": "N=60 truth c={6,5,10,20,3,7,4}, binomial noise "
                        "n=3e3/3e4/3e5",
        "P3_decision": "signature present iff min-chi2 < chi2_0.95(7) AND "
                       "empirical p < 0.05 vs the P1 null",
        "P4_regime": "cc (1.7%) and light (0.5%) sigma_rel exceed the 0.3% "
                     "validity regime; power concentrated in the five "
                     "precise channels",
    },
}

os.makedirs(OUT_DIR, exist_ok=True)
path = os.path.join(OUT_DIR, "pdg_z_extract_2024.json")
with open(path, "w") as fh:
    json.dump(extract, fh, indent=1)
print("frozen extract ->", path)
for l, f, s in zip(labels, fs, ss):
    print(f"  {l:12s} f={f:.5f} sigma={s:.5f} sigma_rel={s/f:.4%}")
print(f"  sum(f) = {sum(fs):.6f}")
