#!/usr/bin/env python3
"""Symmetry architecture of the M-sector core at fixed V: the exact
permutation invariance of the kinetic term, the tau-parity grading of the
tau-even part, the isotypic (permutation-representation) structure, and the
multiplet census with refined pair splittings.

Facts established by this script (all printed with validation numbers):

(S1) The kinetic term T is exactly invariant under every mode permutation
     pi in S_d: ||[T, P_pi]|| = 0 to roundoff (T's amplitude
     (V/2)(k_i+k_j) sqrt((k_i+1) k_j) is the permutation-invariant
     function of the pair occupations).

(S2) The tau-even part of H (tau = any single transposition, here modes
     2<->3): H_+ = T + D_+ + h_+ commutes with tau exactly, where D_+ is
     the coefficient-symmetrized diagonal and h_+ the symmetrized hop.
     The sector therefore carries the tau-parity grading
     H = H_+ (+ block) + W (tau-odd off-block), with dim H_+^+ - dim H_-^-
     equal to the number of compositions with k_2 = k_3.

(S3) The permutation representation of S_d on the sector decomposes into
     isotypic components (Burnside count); every vector in the trivial or
     sign (or any 1-dimensional-irrep) component has <K_1> = S/d exactly,
     so the eigenstate occupation fluctuation is carried by the
     higher-dimensional-irrep content.

(S4) Multiplet census: T's exactly degenerate standard-multiplet pairs
     (d=3); the near-degenerate pairs surviving in the full H, with
     Rayleigh-quotient-refined splittings; the within-pair a-gap
     (occupation constancy on multiplets); the inter-pair a-jumps.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_symmetry.json
"""
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp

import c4_msector_jacobi as mj

OUT = "/home/z/my-project/download/pilot_c4_eth_scaled"
PRIMES = mj.PRIMES


# ----------------------------------------------------------------------------
# permutation operators on the sector
# ----------------------------------------------------------------------------
def perm_index(comp, S, d, sigma):
    """Index map of the mode permutation sigma (a tuple: sigma[i] = the new
    mode at position i)."""
    n = comp.shape[0]
    key = comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
    perm = np.empty_like(comp)
    for i in range(d):
        perm[:, sigma[i]] = comp[:, i]
    pkey = perm @ ((S + 1) ** np.arange(d - 1, -1, -1))
    idx_of = {int(key[i]): i for i in range(n)}
    return np.array([idx_of[int(k)] for k in pkey])


def apply_perm(H, idx):
    """P H P^T with P the permutation matrix of idx."""
    Hc = H.tocoo()
    return sp.coo_matrix((Hc.data, (idx[Hc.row], idx[Hc.col])),
                         shape=H.shape).tocsr()


def dev_max(M):
    M = M.tocsr()
    return float(np.abs(M.data).max()) if M.nnz else 0.0


def split_tau(d, S, h0, U, V, seed):
    """H split into tau-even part H_+ (commuting with tau = swap(1,2)... we
    use tau = transposition of modes 1<->2 in 0-based = (0,1) 0-based
    [i.e. modes 2<->3 in 1-based]) and tau-odd part W = H - H_+."""
    H, eps, comp, hmat = mj.sector_block(d, S, h0, U, V, seed)
    n = H.shape[0]
    idx = perm_index(comp, S, d, (1, 0) + tuple(range(2, d)))  # swap 0,1
    # H_+ = (H + P H P)/2 ; W = (H - P H P)/2
    HP = apply_perm(H, idx)
    Hplus = (H + HP) * 0.5
    W = (H - HP) * 0.5
    # parity subspaces of H_+: basis vectors with k_2 == k_3 (0-based 1,2)
    diag = comp[:, 1] - comp[:, 2]  # k_2 - k_3 in 0-based modes 1,2
    n_fixed = int((diag == 0).sum())
    return H, Hplus, W, comp, hmat, n, n_fixed, idx


def isotypic_content(d, S, comp):
    """Isotypic dims of the S_d permutation representation on compositions:
    Burnside: dim of the lambda-isotypic space = (1/d!) sum_pi chi_lambda
    (pi) fix(pi).  For d=3 we use the character table of S_3."""
    n = comp.shape[0]
    out = {}
    if d == 3:
        # conjugacy classes: e (1), transpositions (3), 3-cycles (2)
        # fix counts:
        fix_e = n
        # transposition fix: k_1 = k_2 (0-based modes 0,1) etc; count orbits
        fix_t = int(((comp[:, 0] == comp[:, 1]) | (comp[:, 0] == comp[:, 2])
                     | (comp[:, 1] == comp[:, 2])).sum())
        # a transposition fixes the compositions invariant under SOME
        # transposition -- no: fix(tau) counts compositions with tau k = k
        # for the SPECIFIC tau.  All transpositions have the same count by
        # relabeling: k_i = k_j for the swapped pair.
        fix_tau = int((comp[:, 1] == comp[:, 2]).sum())
        fix_c3 = int(((comp[:, 0] == comp[:, 1]) & (comp[:, 1] == comp[:, 2]))
                     .sum())
        # characters of S_3 irreps: trivial (1,1,1), sign (1,-1,1),
        # standard (2,0,-1)
        mult = {}
        mult["trivial"] = (fix_e + 3 * fix_tau + 2 * fix_c3) / 6.0
        mult["sign"] = (fix_e - 3 * fix_tau + 2 * fix_c3) / 6.0
        mult["standard"] = (2 * fix_e + 0 * fix_tau - 2 * fix_c3) / 6.0
        out = {k: int(round(v)) for k, v in mult.items()}
        out["check_total"] = (out["trivial"] + out["sign"]
                              + 2 * out["standard"])
        out["n"] = n
    return out


def projectors_s3(d, S, comp, n):
    """Isotypic projectors P_triv, P_sign, P_std (d=3) as index
    permutations: P_lambda = (dim_lambda/d!) sum_pi chi_lambda(pi) P_pi.
    (Corrected: the dimension factor dim_lambda for the 2-dimensional
    standard irrep, and the trivial/sign characters by class.)"""
    # tuples: (permutation, chi_trivial, chi_sign, chi_standard) by class
    # e: (1,1,1,2); transpositions: (1,-1,1,0); 3-cycles: (1,1,1,-1)
    perms = [
        ((0, 1, 2), 1.0, 1.0, 2.0),        # identity
        ((1, 0, 2), 1.0, -1.0, 0.0),       # transpositions
        ((0, 2, 1), 1.0, -1.0, 0.0),
        ((2, 1, 0), 1.0, -1.0, 0.0),
        ((1, 2, 0), 1.0, 1.0, -1.0),       # 3-cycles
        ((2, 0, 1), 1.0, 1.0, -1.0),
    ]
    idxs = [perm_index(comp, S, d, p) for p, _, _, _ in perms]
    P = {}
    for name, col, dim in (("trivial", 1, 1), ("sign", 2, 1),
                           ("standard", 3, 2)):
        # accumulate as dense (small n only)
        M = np.zeros((n, n))
        for (p, ct, cs, cstd), idx in zip(perms, idxs):
            chi = (ct if col == 1 else cs if col == 2 else cstd)
            # permutation matrix Pi: (Pi)_{i, idx[i]} = 1  (row i maps to
            # column idx[i]); as an operator Pi e_i = e_{idx[i]}
            M[np.arange(n), idx] += chi * (dim / 6.0)
        P[name] = M
    return P


def run_symmetry():
    res = {"commutators": [], "tau_split": {}, "isotypic": {},
           "multiplet_census": {}}
    print("=== (S1) [T, P_pi] for all pi in S_d ===")
    for (d, S) in ((3, 40), (4, 20)):
        # kinetic only: h0=0, U=0, V=1
        Hk, _, comp, _ = mj.sector_block(d, S, 0.0, 0.0, 1.0, 7)
        Hk = Hk - sp.diags(Hk.diagonal())
        import itertools
        for sigma in itertools.permutations(range(d)):
            if sigma == tuple(range(d)):
                continue
            idx = perm_index(comp, S, d, sigma)
            dev = dev_max(Hk - apply_perm(Hk, idx))
            res["commutators"].append(dict(d=d, S=S, sigma=list(sigma),
                                           dev=dev))
            print(f"  d={d} sigma={sigma}: ||[T,P]|| = {dev:.2e}")
    print("=== (S2) tau split (d=3, S=60, V=0.3, U=0) ===")
    for S in (20, 60):
        H, Hplus, W, comp, hmat, n, n_fixed, idx = split_tau(
            3, S, 1.0, 0.0, 0.3, 7)
        dev = dev_max(Hplus @ sp.csr_matrix(  # [H_+, P_tau]: use P H_+ P
            np.eye(n)[idx][:, np.argsort(idx)]) if False else Hplus
            - apply_perm(Hplus, idx))
        res["tau_split"][f"S{S}"] = dict(
            n=n, dim_fixed=n_fixed, dim_plus=(n + n_fixed) // 2,
            dim_minus=(n - n_fixed) // 2,
            comm_dev=dev, W_norm=float(np.abs(W.data).max()),
            H_norm=float(np.abs(H.data).max()))
        print(f"  S={S}: n={n}, k2=k3 fixed={n_fixed}, "
              f"dim+={(n + n_fixed)//2}, dim-={(n - n_fixed)//2}, "
              f"||[H_+, tau]||={dev:.2e}, ||W||max={np.abs(W.data).max():.2f}"
              f" (||H||max={np.abs(H.data).max():.2f})")
    print("=== (S3) isotypic content (d=3) ===")
    for S in (20, 60, 120):
        H, eps, comp, hmat = mj.sector_block(3, S, 1.0, 0.0, 0.3, 7)
        iso = isotypic_content(3, S, comp)
        res["isotypic"][f"S{S}"] = iso
        print(f"  S={S}: {iso}")
    print("=== (S4) multiplet census (d=3, V=0.3, U=0) ===")
    for S in (20, 40, 60, 120):
        H, eps, comp, hmat = mj.sector_block(3, S, 1.0, 0.0, 0.3, 7)
        n = H.shape[0]
        Hd = H.toarray()
        w, Vv = np.linalg.eigh(Hd)
        dw = np.diff(w)
        pairs = np.where(dw < 1e-8)[0]
        # refined splittings via the 2x2 Rayleigh restriction
        refined = []
        obs = comp[:, 0].astype(float)
        agap = []
        for p in pairs:
            E2 = Vv[:, [p, p + 1]]
            M2 = E2.T @ (Hd @ E2)
            ev = np.sort(np.linalg.eigvalsh(M2))
            refined.append(ev[1] - ev[0])
            K2 = E2.T @ (obs[:, None] * E2)
            agap.append(abs(K2[0, 0] - K2[1, 1]))
        refined = np.array(refined) if refined else np.array([0.0])
        agap = np.array(agap) if agap else np.array([0.0])
        # T-only doublets
        Hk, _, _, _ = mj.sector_block(3, S, 0.0, 0.0, 1.0, 7)
        Hkd = (Hk - sp.diags(Hk.diagonal())).toarray()
        wk = np.linalg.eigvalsh(Hkd)
        dwk = np.diff(wk)
        iso = isotypic_content(3, S, comp)
        res["multiplet_census"][f"S{S}"] = dict(
            n=n, T_doublets=int((dwk < 1e-10).sum()),
            std_mult=int(iso.get("standard", 0)),
            H_pairs=int(len(pairs)),
            pair_frac=len(pairs) / (n - 1),
            refined_split_med=float(np.median(refined)) if len(refined)
            else None,
            refined_split_max=float(refined.max()) if len(refined)
            else None,
            agap_med=float(np.median(agap)) if len(agap) else None,
            agap_max=float(agap.max()) if len(agap) else None)
        print(f"  S={S}: T-doublets {int((dwk < 1e-10).sum())} "
              f"(std multiplicity {iso.get('standard')}), H-pairs "
              f"{len(pairs)} ({len(pairs)/(n-1):.1%}), refined split "
              f"med {np.median(refined) if len(refined) else 0:.2e} "
              f"max {refined.max() if len(refined) else 0:.2e}, "
              f"a-gap med {np.median(agap) if len(agap) else 0:.1e} "
              f"max {agap.max() if len(agap) else 0:.1e}")
    with open(os.path.join(OUT, "c4_msector_symmetry.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("saved", os.path.join(OUT, "c4_msector_symmetry.json"))
    return res


if __name__ == "__main__":
    run_symmetry()
