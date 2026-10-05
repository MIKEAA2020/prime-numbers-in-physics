#!/usr/bin/env python3
"""Validation of the extended evolve machinery in c4_scaled_eth.py:

  1. Lanczos-estimated ||H|| and the resulting restart step: Krylov trace vs
     an exact eigendecomposition propagation, at pilot scale, for both norm
     modes (lanczos / gershgorin). Requirement: max deviation <= 1e-7.
  2. Spectral-radius estimator vs the exact extreme eigenvalues (the safety
     factor 1.15 must cover the Ritz underestimate).
  3. Checkpoint/resume chunking: one-shot trajectory vs two-chunk resumed
     trajectory. A chunk boundary is an ordinary Lanczos restart, so the two
     must agree to roundoff (<= 1e-12).
  4. Diagonal ensemble: exact sum_n |<n|psi0>|^2 <n|a|n> from full
     diagonalization vs the long-time Krylov time average (dephasing
     identity), plus the microcanonical reference -- at matched dose.
  5. dense_stage code path on a throwaway tag (fields + files, then removed).

Run: python3 c4_extend_validation.py
"""
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
from scipy.linalg import eigh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c4_scaled_eth as m

DOSE = 36.0     # matched-dose convention: V = DOSE / K^2
FAIL = []


def check(name, ok, detail):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)
    if not ok:
        FAIL.append(name)


def setup(d, K, V):
    H, eps, g, hmat, coords = m.build_sparse(d, K, 1.5, 1.0, 0.0, 7, V=V)
    D = H.shape[0]
    obsd = coords[d - 1].ravel().astype(float)
    i0 = int(np.ravel_multi_index(tuple(0 if a != d - 1 else K for a in range(d)),
                                  (K + 1,) * d))
    E0 = float(eps[i0])
    psi0 = np.zeros(D)
    psi0[i0] = 1.0
    H_shift = (H - E0 * sp.identity(D, format="csr")).tocsr()
    return H, H_shift, eps, coords, obsd, psi0, E0, D


def exact_propagate(H_shift, psi0, obs, taus):
    w, V = eigh(H_shift.toarray())
    c = V.T @ psi0
    return np.array([float((np.abs(V @ (np.exp(-1j * w * t) * c))) ** 2 @ obs)
                     for t in taus]), w, V


def main():
    t_all = time.perf_counter()
    for (d, K) in [(3, 8), (4, 7)]:
        V = DOSE / K ** 2
        print(f"\n=== config d={d} K={K} V={V:.4f} (matched dose {DOSE}) ===",
              flush=True)
        H, H_shift, eps, coords, obsd, psi0, E0, D = setup(d, K, V)

        # ---- 2. spectral radius estimator vs exact extremes ----
        v0 = np.random.default_rng(12345).standard_normal(D)
        ritz = m._spectral_radius(H_shift, v0)
        w_ex, V_ex = eigh(H_shift.toarray())
        true_rad = float(np.max(np.abs(w_ex)))
        gersh = m._gershgorin_norm(H_shift)
        check("spectral radius", ritz <= true_rad * (1 + 1e-9) and ritz >= 0.9 * true_rad,
              f"ritz={ritz:.3f} exact={true_rad:.3f} ratio={ritz/true_rad:.4f} "
              f"gershgorin={gersh:.1f} (gersh/exact={gersh/true_rad:.2f})")

        # ---- 1. Krylov trace vs exact propagation, both norm modes ----
        tau_ref = 40.0 if (d, K) == (3, 8) else 20.0
        modes = ("lanczos", "gershgorin") if (d, K) == (3, 8) else ("lanczos",)
        for mode in modes:
            ev = m.krylov_trace(H_shift, psi0, obsd, tau_max=tau_ref, m=48,
                                deadline=1e9, norm_mode=mode)
            ref, _, _ = exact_propagate(H_shift, psi0, obsd, ev["tau"])
            dev = float(np.max(np.abs(ev["trace"] - ref)))
            check(f"krylov vs exact propagation [{mode}]",
                  dev <= 1e-7 and ev["norm_drift"] <= 1e-8,
                  f"dt={ev['dt']:.4f} n={len(ev['tau'])} max|dev|={dev:.2e} "
                  f"normdrift={ev['norm_drift']:.1e}")

        # ---- 3. chunked resume == one-shot ----
        T = 40.0 if (d, K) == (3, 8) else 20.0
        one = m.krylov_trace(H_shift, psi0, obsd, T, 48, 1e9, norm_mode="lanczos")
        half = m.krylov_trace(H_shift, psi0, obsd, T / 2, 48, 1e9,
                              norm_mode="lanczos")
        two = m.krylov_trace(H_shift, half["psi"], obsd, T, 48, 1e9,
                             tau0=float(half["tau"][-1]), norm_mode="lanczos")
        cat = np.concatenate([half["trace"], two["trace"][1:]])
        cat_tau = np.concatenate([half["tau"], two["tau"][1:]])
        dev = float(np.max(np.abs(cat - one["trace"])))
        dtau = float(np.max(np.abs(cat_tau - one["tau"])))
        check("checkpoint/resume equivalence", dev <= 1e-12 and dtau <= 1e-12,
              f"max|dev|={dev:.2e} max|dtau|={dtau:.1e} (dt={one['dt']:.4f})")

    # ---- 4. diagonal ensemble vs long-time average (matched dose) ----
    d, K = 3, 8
    V = DOSE / K ** 2
    print(f"\n=== diagonal ensemble: d={d} K={K} V={V:.4f}, D={(K+1)**d} ===",
          flush=True)
    H, H_shift, eps, coords, obsd, psi0, E0, D = setup(d, K, V)
    w, Ve = eigh(H_shift.toarray())
    c = Ve.T @ psi0
    a_n = (Ve ** 2).T @ obsd
    diag = float((np.abs(c) ** 2) @ a_n)
    micro, delta, nmic = m._micro_window(eps, obsd, E0)
    T = 600.0
    ev = m.krylov_trace(H_shift, psi0, obsd, T, 48, 1e9, norm_mode="lanczos")
    sel = ev["tau"] >= T / 2
    tavg = float(ev["trace"][sel].mean())
    resid = float(ev["trace"][sel].std())
    check("plateau = diagonal ensemble", abs(tavg - diag) <= max(resid, 0.02),
          f"time_avg={tavg:.4f} diag={diag:.4f} |diff|={abs(tavg-diag):.4f} "
          f"resid_fluct={resid:.4f} micro={micro:.4f} (delta={delta}, "
          f"n={nmic}) |diag-micro|={abs(diag-micro):.4f}")
    check("weight sum", abs(float(np.sum(np.abs(c) ** 2)) - 1.0) <= 1e-12,
          f"sum|c|^2={float(np.sum(np.abs(c)**2)):.12f}")

    # ---- 5. dense_stage code path on a throwaway tag ----
    d, K = 3, 6
    V = DOSE / K ** 2
    H, H_shift, eps, coords, obsd, psi0, E0, D = setup(d, K, V)
    res = dict(tag="valtmp", d=d, K=K, g0=1.5, h0=1.0, U=0.0, seed=7, k=0, V=V)
    m.dense_stage(res, H, eps, coords, d, K, D, "valtmp")
    dn = res.get("dense", {})
    # independent re-computation
    w2, Ve2 = eigh(H.toarray())
    a2 = (Ve2 ** 2).T @ obsd
    i0_ = int(np.ravel_multi_index(tuple(0 if a != d - 1 else K for a in range(d)),
                                   (K + 1,) * d))
    c2 = Ve2[i0_, :]
    diag2 = float((c2 ** 2) @ a2)
    ok = "diag_d" in dn and abs(dn["diag_d"] - diag2) <= 1e-10
    check("dense_stage fields", ok,
          f"diag_d={dn.get('diag_d')} vs {diag2:.6f}, sigma_rel_full="
          f"{dn.get('sigma_rel_full')}, t_dense={dn.get('t_dense')}s")
    for f in (os.path.join(m.OUT, "dense_valtmp.npz"),):
        if os.path.exists(f):
            os.remove(f)

    print(f"\n{'ALL PASS' if not FAIL else 'FAILURES: ' + ', '.join(FAIL)} "
          f"({time.perf_counter() - t_all:.0f}s)", flush=True)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
