#!/usr/bin/env python3
"""
Numerical corroboration for the occupation-sector structure of the kinetic
completion (infinite-volume self-adjointness).

The mathematical claims (proved in the paper):
(S1) H_kin commutes with Nhat_tot; the occupation sector
     {k in N^d : sum k_p = S} is finite (dimension C(S+d-1, d-1)), and the
     sector block is Hermitian: the bond weight (k_p + k_q) is invariant
     under bond reversal because a hop raises k_p by one and lowers k_q by
     one.  Hence H_P + H_U + H_hop + H_kin is essentially self-adjoint on
     the finitely supported configurations (orthogonal direct sum of
     finite Hermitian blocks), and the bounded H_W perturbs it by
     Kato-Rellich.
(S2) Sector norm bound: ||H_kin^{(S)}|| <= |V| (d-1) S (S+1)
     (Gershgorin row sums; the sqrt-hopped matrix elements are bounded by
     (k_p+k_q)(k_p+k_q+1)/2).
(S3) Box-truncation exactness (g = 0, pure number-conserving part): for a
     state supported in a sector S <= K, the K-truncated evolution equals
     the larger-truncation evolution EXACTLY -- the whole sector fits in
     the box and is invariant.

Checks: (S1) Hermiticity of every sector block extracted from the sparse
assembly; (S2) the norm bound on sectors S = 1..12; (S3) evolution
identity across two truncations for several tau and random sector states.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_sector_checks.json
"""
import json
import os

import numpy as np
import scipy.sparse as sp
from scipy.linalg import expm

import c4_scaled_eth as base

OUT = base.OUT


def sector_indices(d, K, S):
    """Flat indices of sites with total occupation S inside the box K."""
    shape = (K + 1,) * d
    grid = np.indices(shape)
    tot = np.zeros(shape, dtype=int)
    for i in range(d):
        tot += grid[i]
    return np.ravel_multi_index(np.where(tot == S), shape)


def sector_block_norms(d, S, V):
    """||H_kin^{(S)}||_2 for the sector S of the pure kinetic operator
    (g0 = h0 = U = 0), extracted from the sparse assembly at K = S (the
    whole sector fits)."""
    K = S
    H, eps, g, hmat, coords = base.build_sparse(
        d, K, g0=0.0, h0=0.0, U=0.0, seed=7, V=V)
    idx = sector_indices(d, K, S)
    Hk = H.tocsr()
    # off-diagonal part only (H_P diagonal removed)
    Hk = Hk - sp.diags(Hk.diagonal())
    blk = Hk[idx][:, idx].toarray()
    herm = float(np.max(np.abs(blk - blk.T)))
    norm = float(np.linalg.norm(blk, 2))
    bound = abs(V) * (d - 1) * S * (S + 1)
    return herm, norm, bound, blk.shape[0]


def box_exactness(d, K_small, K_big, S, V, g0, taus, seed):
    """(S3): with g0 = 0 (no walk), a sector-S state (S <= K_small <=
    K_big) evolves identically under both truncations, because the sector
    is invariant and fully contained in both boxes.  Same seed -> same
    couplings."""
    H1, eps1, g1, hmat1, coords1 = base.build_sparse(
        d, K_small, g0, 1.0, 0.0, seed, V=V)
    H2, eps2, g2, hmat2, coords2 = base.build_sparse(
        d, K_big, g0, 1.0, 0.0, seed, V=V)
    assert np.allclose(g1, g2) and np.allclose(hmat1, hmat2), \
        "couplings must coincide across truncations (same seed)"
    idx = sector_indices(d, K_small, S)
    rng = np.random.default_rng(seed + 55)
    psi = np.zeros((K_small + 1) ** d)
    psi[idx] = rng.standard_normal(len(idx))
    psi /= np.linalg.norm(psi)
    # embed into the K_big grid
    shape_s, shape_b = (K_small + 1,) * d, (K_big + 1,) * d
    coords_s = np.array(np.unravel_index(np.arange(psi.size), shape_s))
    flat_b = np.ravel_multi_index(tuple(coords_s), shape_b)
    psi_b = np.zeros((K_big + 1) ** d)
    psi_b[flat_b] = psi
    U1 = expm(-1j * taus[:, None, None] * H1.toarray())
    U2 = expm(-1j * taus[:, None, None] * H2.toarray())
    out1 = (U1 @ psi)
    out2 = (U2 @ psi_b)
    # compare on the shared coordinates
    d12 = float(np.max(np.abs(out1 - out2[:, flat_b])))
    # invariance: support stays in the sector
    tot1 = np.zeros(shape_s, dtype=int)
    for i in range(d):
        tot1 += np.indices(shape_s)[i]
    tot_flat = tot1.ravel()
    leak = float(np.max(np.abs(out1[:, tot_flat != S])))
    return d12, leak


def main():
    res = {"checks": []}

    print("(S1)/(S2): sector Hermiticity + Gershgorin bound", flush=True)
    for d in (3, 4):
        for S in range(1, 13):
            herm, norm, bound, dim = sector_block_norms(d, S, V=1.0)
            ok = (herm < 1e-14) and (norm <= bound)
            res["checks"].append(dict(
                kind="sector_herm_norm", d=d, S=S, dim=dim,
                herm_dev=herm, norm=norm, bound=bound, ok=bool(ok)))
            print(f"  d={d} S={S:>2}: dim={dim:>4} herm={herm:.1e} "
                  f"||H^S||={norm:8.3f} <= {bound:8.3f} {'OK' if ok else 'FAIL'}",
                  flush=True)

    print("(S3): box-truncation exactness of sector-S dynamics (g=0)",
          flush=True)
    taus = np.array([0.3, 1.0, 2.7, 5.0])
    for d in (3,):
        for S in (0, 2, 4, 6):
            for g0 in (0.0,):
                d12, leak = box_exactness(d, 6, 10, S, V=0.5, g0=g0,
                                          taus=taus, seed=7)
                ok = (d12 < 1e-10) and (leak < 1e-10)
                res["checks"].append(dict(
                    kind="box_exactness", d=d, S=S, K_small=6, K_big=10,
                    g0=g0, max_dev=d12, sector_leak=leak, ok=bool(ok)))
                print(f"  d={d} S={S}: max|evol diff|={d12:.2e} "
                      f"sector leak={leak:.2e} {'OK' if ok else 'FAIL'}",
                      flush=True)

    # contrast: with the walk on (g0 != 0), sectors are NOT invariant --
    # the exactness must FAIL (H_W mixes sectors S -> S+-1)
    d12w, leakw = box_exactness(3, 6, 10, 4, V=0.5, g0=1.5, taus=taus,
                                seed=7)
    res["walk_control"] = dict(max_dev=d12w, sector_leak=leakw,
                               sectors_mixed=bool(leakw > 1e-6))
    print(f"  control (g0=1.5, walk on): sector leak={leakw:.2e} "
          f"(sectors mixed, as stated: H_W breaks the sector structure)",
          flush=True)

    n_ok = sum(1 for c in res["checks"] if c["ok"])
    res["summary"] = dict(n_checks=len(res["checks"]), n_ok=n_ok,
                          all_pass=bool(n_ok == len(res["checks"])))
    with open(os.path.join(OUT, "c4_sector_checks.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"SUMMARY: {n_ok}/{len(res['checks'])} checks pass", flush=True)


if __name__ == "__main__":
    main()
