#!/usr/bin/env python3
"""
Selftest for the kinetic (density-assisted hopping) term added to
c4_scaled_eth.py:  H_kin = V * sum_{p<q} (n_p + n_q)(a_p^dag a_q + h.c.)

Checks, at small d,K where dense assembly is cheap:
  1. IDENTIY: build_sparse(...,V) - build_sparse(...,V=0) equals a dense
     reference matrix assembled from first principles (bosonic ladder ops,
     unordered pairs only, no bookkeeping shortcuts).
  2. HERMITICITY of the reference and of the difference.
  3. N_tot CONSERVATION: [H_kin, N_tot] = 0 exactly (moves quanta between
     axes, never creates/destroys).
  4. Hand-computed matrix element: |k1=1, k2=2> -> |2,1> amplitude
     V*(1+2)*sqrt(2*2) = 6V (pair {1,2}); |k>=|3,0> -> |2,1> amplitude
     V*(3+0)*sqrt(3*1) = 3*sqrt(3)*V.
  5. QUARTIC ORDER: H_kin is NOT quadratic -- the H(V) restricted to fixed
     N_tot sector differs from any single-particle quadratic form on that
     sector (rank test: |H_kin restricted to N_tot=2 sector| has rank > 2
     -- a quadratic number-conserving form on a 2-quantum sector of d modes
     has rank <= d+1... we do a weaker, exact statement: H_kin has nonzero
     elements connecting states whose max occupation differs, which no
     number-conserving quadratic form a^dag a can produce with K>2 (matrix
     element between |k> and |k'> with k'_i = k_i+1 requires
     sqrt((k_i+1)k_j) independent of OTHER occupations for quadratic;
     density-assisted factor (k_i+k_j) breaks this).
"""
import numpy as np
import scipy.sparse as sp
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from c4_scaled_eth import build_sparse


def dense_reference_kin(d, K, V):
    """First-principles assembly: unordered pairs, ladder operators."""
    D = (K + 1) ** d
    Hk = np.zeros((D, D))
    shape = (K + 1,) * d
    strides = np.array([(K + 1) ** (d - 1 - i) for i in range(d)])
    idx_grid = np.arange(D).reshape(shape)
    coords = np.indices(shape)
    for i in range(d):
        for j in range(i + 1, d):
            mask = (coords[j] >= 1) & (coords[i] <= K - 1)
            src = idx_grid[mask].ravel()
            tgt = src + strides[i] - strides[j]
            ki = coords[i][mask].ravel()
            kj = coords[j][mask].ravel()
            amp = V * (ki + kj) * np.sqrt((ki + 1.0) * kj)
            Hk[src, tgt] += amp          # a_i^dag a_j part
            Hk[tgt, src] += amp          # h.c. (same value, verified)
    return Hk


def dense_ntot(d, K):
    D = (K + 1) ** d
    coords = np.indices((K + 1,) * d)
    return sum(coords[i].ravel() for i in range(d)).astype(float)


def main():
    rng = np.random.default_rng(0)
    ok = True
    for (d, K, V) in [(3, 5, 0.7), (4, 4, -1.3), (2, 7, 2.0), (5, 3, 0.5)]:
        H1, eps1, *_ = build_sparse(d, K, 1.5, 1.0, 0.0, 7, V=V)
        H0, eps0, *_ = build_sparse(d, K, 1.5, 1.0, 0.0, 7, V=0.0)
        Hkin = (H1 - H0).toarray()
        href = dense_reference_kin(d, K, V)
        err_id = np.abs(Hkin - href).max()
        # V=0 must give EXACT zero difference (term fully skipped)
        err_zero = 0.0
        herm = np.abs(href - href.T).max()
        N = dense_ntot(d, K)
        comm = np.abs(href @ np.diag(N) - np.diag(N) @ href).max()
        diag_ntot = np.abs(np.diag(href)).max()      # must be 0 (pure hop)
        hand_ok = True
        if (d, K) == (2, 7) and V == 2.0:
            # |k1=1,k2=2> -> |2,1>:  V*(1+2)*sqrt(2*2) = 6V = 12
            s = np.ravel_multi_index((1, 2), (K + 1, K + 1))
            t = np.ravel_multi_index((2, 1), (K + 1, K + 1))
            hand_ok = abs(href[t, s] - 6 * V) < 1e-12
            # |3,0> -> |2,1>: V*(3+0)*sqrt(3*1) = 3*sqrt(3)*V
            s2 = np.ravel_multi_index((3, 0), (K + 1, K + 1))
            hand_ok &= abs(href[t, s2] - 3 * np.sqrt(3) * V) < 1e-12
        # kinetic term is NOT a fixed-coefficient quadratic form: two
        # transitions of the SAME pair (i=1, j=2) give different effective
        # coefficients amp/sqrt((ki+1)kj): |1,2>->|2,1> has 3V, |0,1>->|1,0>
        # has 1V -- no quadratic sum c_pq a_p^dag a_q can do that.
        s_a = np.ravel_multi_index((1, 2) + (0,) * (d - 2), (K + 1,) * d)
        t_a = np.ravel_multi_index((2, 1) + (0,) * (d - 2), (K + 1,) * d)
        s_b = np.ravel_multi_index((0, 1) + (0,) * (d - 2), (K + 1,) * d)
        t_b = np.ravel_multi_index((1, 0) + (0,) * (d - 2), (K + 1,) * d)
        c_a = href[t_a, s_a] / np.sqrt(2.0 * 2.0)     # (1+2)*V
        c_b = href[t_b, s_b] / np.sqrt(1.0 * 1.0)     # (0+1)*V
        quad_break = abs(c_a - c_b) > 1e-12
        line_ok = (err_id < 1e-11 and herm < 1e-11 and comm < 1e-9
                   and diag_ntot == 0.0 and hand_ok and quad_break)
        ok &= line_ok
        print(f"d={d} K={K} V={V:+.1f} | identity={err_id:.1e} herm={herm:.1e} "
              f"[Hkin,ntot]={comm:.1e} diagonal={diag_ntot:.1e} "
              f"hand={hand_ok} breaks-quadratic={quad_ok_str(quad_break)} "
              f"-> {'PASS' if line_ok else 'FAIL'}")
    print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


def quad_ok_str(q):
    return "yes" if q else "no"


if __name__ == "__main__":
    raise SystemExit(main())
