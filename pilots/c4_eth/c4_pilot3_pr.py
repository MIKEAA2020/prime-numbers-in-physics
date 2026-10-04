#!/usr/bin/env python3
"""C4 pilot, part 3: eigenvector localization structure (participation ratios).

Compares PR of eigenstates in the occupation basis for:
  - H_P alone (diagonal: PR = 1)
  - H_P + H_W (separable Wannier-Stark chains per prime mode)
  - H_tot (full: + H_hop)
  - H_tot + U (quartic completion)
PR/D -> 0 means localized (no equilibration possible); PR/D ~ O(0.1-1) extended.
"""
import sys
import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
from c4_eth_pilot import build_H, PRIMES
from c4_eth_pilot2 import build_H_int


def pr_stats(H, label, window=(0.3, 0.7)):
    w, V = np.linalg.eigh(H)
    n = len(w)
    lo, hi = int(window[0] * n), int(window[1] * n)
    P2 = (V[lo:hi] ** 4).sum(axis=1)      # sum |v|^4 per eigenstate
    PR = 1.0 / P2                          # participation ratio
    frac = PR / n
    print(f"{label:>22}: median PR/D = {np.median(frac):.4f}  "
          f"[PR/D 10%={np.quantile(frac,0.1):.4f}, 90%={np.quantile(frac,0.9):.4f}]")
    return np.median(frac)


def main():
    d, K = 5, 4
    rng = np.random.default_rng(7)
    H, eps, g, hmat = build_H(d, K, 1.5, 1.0, rng)
    D = (K + 1) ** d
    print(f"d={d}, K={K}, D={D}")

    # H_P alone
    HP = np.diag(eps)
    pr_stats(HP, "H_P (diagonal)")

    # H_P + H_W (Stark chains, no inter-mode coupling)
    HW = H - np.diag(eps) - build_hop(d, K, hmat)
    pr_stats(HP + HW, "H_P + H_W (Stark)")

    # full H_tot
    pr_stats(H, "H_tot (full)")

    # interacting completion
    rng2 = np.random.default_rng(7)
    HU, epsU, _, _ = build_H_int(d, K, 1.5, 1.0, 1.5, rng2)
    pr_stats(HU, "H_tot + U n_i n_j")

    # weak coupling
    rng3 = np.random.default_rng(7)
    Hw, epsw, _, _ = build_H(d, K, 0.05, 0.03, rng3)
    pr_stats(Hw, "weak control")


def build_hop(d, K, hmat):
    """Isolate the H_hop block (used to subtract from H)."""
    shape = (K + 1,) * d
    D = (K + 1) ** d
    strides = np.array([(K + 1) ** (d - 1 - i) for i in range(d)])
    idx_grid = np.arange(D).reshape(shape)
    coords = np.indices(shape)
    H = np.zeros((D, D))
    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            hij = hmat[i, j]
            if hij == 0.0:
                continue
            mask = (coords[j] >= 1) & (coords[i] <= K - 1)
            src = idx_grid[mask].ravel()
            tgt = src + strides[i] - strides[j]
            ki = coords[i][mask].ravel()
            kj = coords[j][mask].ravel()
            vals = hij * np.sqrt((ki + 1.0) * kj)
            H[src, tgt] += vals
            H[tgt, src] += vals
    return H


if __name__ == "__main__":
    main()
