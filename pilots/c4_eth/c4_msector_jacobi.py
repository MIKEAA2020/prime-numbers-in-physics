#!/usr/bin/env python3
"""
M-sector (fixed total occupation S) Jacobi structure of the C4
number-conserving core: the mathematical falsifier object for the strong-ETH
diagnostic.

Structure established and measured by this pilot:
(J1) Layer grading.  Order the compositions of S into d parts by the layer
     l = S - k_1 (the hop distance from the corner (S,0,...,0)).  Every
     number-conserving hop either moves one quantum between modes 2..d
     (layer unchanged) or exchanges one quantum with mode 1 (l -> l +- 1):
     the sector block is EXACTLY block-tridiagonal in this grading, and the
     diagonal block at layer l is the (d-1, l) sector of the modes
     p_2 .. p_d (same h, V), affinely shifted by (S-l)(log p_1 + U l).  The
     recursion bottoms out at d = 2, where the sector is the Jacobi
     (tridiagonal) matrix
         a_k = k log p_1 + (S-k) log p_2 + U k (S-k),
         b_k = (2 h_12 + V S) sqrt((k+1)(S-k)).
(J2) Two-mode solvability (U = 0).  With Delta = log(p_1/p_2) and
     C = 2 h_12 + V S the block is the spin-S/2 rotation problem
     Delta S_z + 2 C S_x + (S/2) log(p_1 p_2) I: the spectrum is the picket
     fence E_j = (S/2) log(p_1 p_2) + sqrt(Delta^2 + 4C^2) (S/2 - j), the
     eigenvectors are the Krawtchouk (rotated-spin) vectors, the eigenstate
     occupation is exactly linear in the eigenvalue, and the binned
     fluctuation is pure bin-width artifact: kappa(S) -> |Delta| /
     (30 sqrt(Delta^2 + 4 C^2)), an S-independent floor, while the Haar
     benchmark decays as n^{-1/2}.  At fixed V the floor itself decays
     like 1/S; the picket ratio statistic <r> = 1 survives at every scale.
(J3) Free reduction.  H_P and H_hop are one-body operators: their sector
     blocks are the S-fold symmetric representations of a fixed d x d
     Hermitian matrix, exactly solvable at every S.  The kinetic term is
     the only interaction in the sector problem.  At matched dose
     V S^2 = 36 its share of the sector bandwidth decays like 1/S (the
     sector ladder approaches the free limit); at fixed V it dominates the
     bandwidth (row-sum bound |V| (d-1) S (S+1)).

Ladders measured (g0 = 0, h0 = 1, seed 7, the committed coupling draw):
  * matched dose   V = 36/S^2, U in {0, 2}, d = 2, 3, 4
  * fixed V = 0.3  (the d4K11 equilibrating point), U = 0, d = 2, 3, 4
Diagnostics per point: kappa = sigma_ETH / sqrt(S(S+2)/12) in the 30-bin
quantile protocol (full spectrum where dense, k=350 median window where
sparse), the Haar-in-shell benchmark B_count, the fixed-fraction benchmark
B_frac, <r> (trimmed), PR/n, the kinetic share of the bandwidth, and the
corner-state Lanczos betas.  The d=2 closed forms are validated to
roundoff; the assembly is validated against the full-grid extraction.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_results.json (+ per-point npz)
"""
import argparse
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy.linalg import eigh_tridiagonal

import c4_scaled_eth as base

OUT = base.OUT
PRIMES = base.PRIMES
N_DENSE = 7000          # dense eigendecomposition cap (RAM)
R_POISSON = 2 * np.log(2) - 1
R_GOE = 0.5359

_START = time.perf_counter()


# ----------------------------------------------------------------------------
# sector assembly
# ----------------------------------------------------------------------------
def compositions(d, S):
    """All k in N^d with sum k = S, ordered with k_1 descending (row 0 =
    the corner (S,0,...,0))."""
    if d == 2:
        out = np.empty((S + 1, 2), dtype=np.int64)
        out[:, 0] = np.arange(S, -1, -1)
        out[:, 1] = S - out[:, 0]
        return out
    # d >= 3: recurse on the first coordinate
    blocks = []
    for k1 in range(S, -1, -1):
        sub = compositions(d - 1, S - k1)
        blk = np.empty((sub.shape[0], d), dtype=np.int64)
        blk[:, 0] = k1
        blk[:, 1:] = sub
        blocks.append(blk)
    return np.vstack(blocks)


def draw_couplings(d, h0, seed):
    """Replicate base.build_sparse's rng stream exactly (g drawn first,
    then the ordered-pair h draws, then symmetrization)."""
    rng = np.random.default_rng(seed)
    _g = 0.0 * (1.0 + 0.3 * rng.uniform(-1, 1, size=d))   # g0 = 0, stream kept
    hmat = np.zeros((d, d))
    for i in range(d):
        for j in range(d):
            if i != j:
                hmat[i, j] = h0 * rng.uniform(-1, 1)
    return 0.5 * (hmat + hmat.T)


def sector_block(d, S, h0, U, V, seed, p_offset=0, hmat_override=None,
                  Vpairs=None):
    """Sparse CSR sector block of the number-conserving core at total
    occupation S, plus the diagonal energies and the k_1 observable.
    p_offset selects the mode family PRIMES[off:off+d]; hmat_override
    replaces the coupling draw (used by the recursion check, where the
    sub-block carries the h-submatrix of the parent family).  Vpairs: a
    (d, d) symmetric matrix of per-pair kinetic couplings replacing the
    single V (the anisotropic control family)."""
    comp = compositions(d, S)
    n = comp.shape[0]
    ln_p = np.log(np.array(PRIMES[p_offset:p_offset + d], dtype=float))
    eps = comp @ ln_p
    if U != 0.0:
        cross = np.zeros(n)
        for i in range(d):
            for j in range(i + 1, d):
                cross += comp[:, i] * comp[:, j]
        eps = eps + U * cross
    hmat = (hmat_override if hmat_override is not None
            else draw_couplings(d, h0, seed))
    # vectorized index map
    key = comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
    order = np.argsort(key)
    keys_sorted = key[order]
    idx_of_key = np.empty(n, dtype=np.int64)
    idx_of_key[order] = np.arange(n)

    rows, cols, vals = [], [], []
    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            hij = hmat[i, j]
            mask = comp[:, j] >= 1
            src = np.where(mask)[0]
            if src.size == 0:
                continue
            ki = comp[src, i].astype(float)
            kj = comp[src, j].astype(float)
            amp = np.sqrt((ki + 1.0) * kj)
            Veff = (Vpairs[i, j] if Vpairs is not None else V)
            v = (hij + 0.5 * Veff * (ki + kj)) * amp
            tgt_comp = comp[src].copy()
            tgt_comp[:, i] += 1
            tgt_comp[:, j] -= 1
            tgt_key = tgt_comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
            tgt = idx_of_key[np.searchsorted(keys_sorted, tgt_key)]
            rows.append(src); cols.append(tgt); vals.append(v)
            rows.append(tgt); cols.append(src); vals.append(v)
    rows.append(np.arange(n)); cols.append(np.arange(n)); vals.append(eps)
    H = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n, n)).tocsr()
    H.sum_duplicates()
    return H, eps, comp, hmat


def validate_assembly():
    """The sector assembly must equal the full-grid extraction of
    base.build_sparse at K = S (the box is inactive in the sector).
    Both matrices are put in a common order (sorted by the unique
    composition key) before comparison."""
    checks = []
    for (d, S) in ((2, 10), (3, 8), (4, 6)):
        for U, V in ((0.0, 0.3), (2.0, 0.0)):
            H, eps, comp, hmat = sector_block(d, S, 1.0, U, V, 7)
            Hf, epsf, g, hmatf, coords = base.build_sparse(
                d, S, 0.0, 1.0, U, 7, V=V)
            # sector states of the full grid, keyed like the compositions
            shape = (S + 1,) * d
            grid = np.indices(shape)
            tot = np.zeros(shape, dtype=int)
            for i in range(d):
                tot += grid[i]
            sec = np.array(np.where(tot == S))          # (d, m) in C-order
            keys_grid = sec.T @ ((S + 1) ** np.arange(d - 1, -1, -1))
            flat = np.ravel_multi_index(tuple(sec), shape)
            ogrid = np.argsort(keys_grid)
            rows_grid = flat[ogrid]                     # key-sorted grid rows
            keys_comp = comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
            ocomp = np.argsort(keys_comp)
            blk = Hf.tocsr()[rows_grid][:, rows_grid].toarray()
            Hperm = H.toarray()[ocomp][:, ocomp]
            dev = float(np.abs(Hperm - blk).max())
            ok = dev < 1e-13 and np.allclose(hmat, hmatf)
            checks.append(dict(d=d, S=S, U=U, V=V, max_dev=dev, ok=bool(ok)))
            print(f"  assembly check d={d} S={S} U={U} V={V}: "
                  f"max|H_sector-H_extract|={dev:.2e} "
                  f"hmat match={np.allclose(hmat, hmatf)}", flush=True)
    return checks


def check_block_tridiag(d, S, h0, U, V, seed):
    """(J1): in the layer grading l = S - k_1 the block is exactly block
    tridiagonal (all couplings satisfy |l(src)-l(tgt)| <= 1)."""
    H, eps, comp, hmat = sector_block(d, S, h0, U, V, seed)
    Hc = H.tocoo()
    lsrc = S - comp[Hc.row, 0]
    ltgt = S - comp[Hc.col, 0]
    off = np.abs(lsrc - ltgt)
    # diagonal entries have lsrc == ltgt; hops never exceed |dl| = 1
    max_dl = int(off.max())
    # layer sizes and the recursion: diagonal block at layer l
    layers = np.bincount(S - comp[:, 0], minlength=S + 1)
    # recursion check: the diagonal block at layer l vs the (d-1, l) sector
    # of the mode family p_2..p_d with the h-submatrix, affinely shifted
    rec_dev = None
    if d >= 3 and S >= 4:
        l = S // 2
        sel = (S - comp[:, 0]) == l
        rows_l = np.where(sel)[0]
        blk = H.tocsr()[rows_l][:, rows_l].toarray()
        sub, eps_sub, comp_sub, _ = sector_block(
            d - 1, l, h0, U, V, seed, p_offset=1,
            hmat_override=hmat[1:, 1:])
        # affine shift: + (S-l)(log p_1 + U l) on the diagonal
        shift = (S - l) * (math.log(PRIMES[0]) + U * l)
        if blk.shape == sub.shape:
            rec_dev = float(np.abs(blk - (sub.toarray() + shift
                                           * np.eye(blk.shape[0]))).max())
    return dict(d=d, S=S, max_dl=max_dl,
                layer_sizes=[int(x) for x in layers],
                recursion_full_dev=rec_dev,
                block_tridiag=bool(max_dl <= 1))


# ----------------------------------------------------------------------------
# d = 2 closed forms
# ----------------------------------------------------------------------------
def d2_jacobi(S, U, V, h12):
    """a, b of the two-mode sector Jacobi matrix (k = 0..S)."""
    k = np.arange(S + 1, dtype=float)
    a = k * math.log(2.0) + (S - k) * math.log(3.0) + U * k * (S - k)
    b = (2.0 * h12 + V * S) * np.sqrt((k[:-1] + 1.0) * (S - k[:-1]))
    return a, b


def d2_analytic(S, V, h12):
    """U = 0 closed form: spectrum, eigenstate occupations, Omega, kappa
    floor."""
    Delta = math.log(2.0 / 3.0)
    C = 2.0 * h12 + V * S
    Om = math.sqrt(Delta * Delta + 4.0 * C * C)
    j = np.arange(S + 1, dtype=float)
    E = 0.5 * S * math.log(6.0) + Om * (0.5 * S - j)
    avals = 0.5 * S + (0.5 * S - j) * Delta / Om
    kappa_floor = abs(Delta) / (30.0 * Om)
    return dict(E=E, a=avals, Omega=Om, Delta=Delta, C=C,
                kappa_floor=kappa_floor)


# ----------------------------------------------------------------------------
# diagnostics (sector versions of the ladder protocol)
# ----------------------------------------------------------------------------
def binned_sigma(w, a, n_bins=30):
    qs = np.quantile(w, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9; qs[-1] += 1e-9
    ib = np.clip(np.searchsorted(qs, w, side="right") - 1, 0, n_bins - 1)
    fl = [a[ib == b].std() for b in range(n_bins) if (ib == b).sum() >= 3]
    return float(np.sqrt(np.mean(np.square(fl)))) if fl else float("nan")


def std_basis(S):
    return math.sqrt(S * (S + 2.0) / 12.0)


def shell_benchmarks(eps, obs, wlo, whi, S, frac=0.05):
    """B_count: Haar-random eigenstates in the eps shell of the window;
    B_frac: same on the fixed 5%-quantile band at the eps median."""
    sb = std_basis(S)
    shell = (eps >= wlo) & (eps <= whi)
    n_sh = int(shell.sum())
    b_count = (math.sqrt(2.0 / n_sh) * float(obs[shell].std()) / sb
               if n_sh > 2 else None)
    lo, hi = np.quantile(eps, [0.5 - frac / 2, 0.5 + frac / 2])
    fshell = (eps >= lo) & (eps <= hi)
    n_fr = int(fshell.sum())
    b_frac = (math.sqrt(2.0 / n_fr) * float(obs[fshell].std()) / sb
              if n_fr > 2 else None)
    return dict(n_shell=n_sh, B_count=b_count, n_frac=n_fr, B_frac=b_frac)


def full_diag_diag(H, eps, comp, S, tag):
    """Dense full diagonalization + full-spectrum protocol."""
    n = H.shape[0]
    Hd = H.toarray()
    w, V = np.linalg.eigh(Hd)
    del Hd
    obs = comp[:, 0].astype(float)
    a = (V ** 2).T @ obs
    sig = binned_sigma(w, a)
    sb = std_basis(S)
    r_mean, r_err = base.ratio_statistic(w)
    pr = float(np.mean(1.0 / np.einsum("ij,ij->j", V ** 2, V ** 2)) / n)
    bench = shell_benchmarks(eps, obs, w[0], w[-1], S)
    # kinetic share of the bandwidth: off-diagonal Gershgorin row-sum norm
    kin = H - sp.diags(H.diagonal())
    gersh = float(np.abs(kin).sum(axis=1).max()) if kin.nnz else 0.0
    res = dict(n=n, protocol="full-spectrum", sigma_eth=sig,
               kappa=sig / sb, r_mean=r_mean, r_sem=r_err, pr_over_n=pr,
               band=[float(w[0]), float(w[-1])], **bench,
               gersh_off=float(gersh))
    np.savez_compressed(os.path.join(OUT, f"msec_{tag}.npz"),
                        w=w, a=a, obs=obs, eps=eps)
    del V
    return res


def window_diag(H, eps, comp, S, tag, k=350, seed=7):
    """k eigenpairs at the eps median (shift-invert; the sector blocks are
    small enough for the LU)."""
    n = H.shape[0]
    sigma = float(np.median(eps))
    v0 = np.random.default_rng(seed + 2).standard_normal(n)
    t0 = time.perf_counter()
    w, V = spl.eigsh(H, k=k, sigma=sigma, which="LM", v0=v0,
                     maxiter=10000, tol=0)
    t_eig = time.perf_counter() - t0
    HV = H @ V
    rj = np.linalg.norm(HV - V * w[None, :], axis=0)
    cert = rj <= 1e-7 * max(abs(w[0]), abs(w[-1]), 1.0)
    order = np.argsort(w)
    w, V = w[order], V[:, order]
    obs = comp[:, 0].astype(float)
    a = (V ** 2).T @ obs
    sig = binned_sigma(w, a)
    sb = std_basis(S)
    r_mean, r_err = base.ratio_statistic(w)
    Vc = V[:, cert]
    pr = (float(np.mean(1.0 / np.einsum("ij,ij->j", Vc ** 2, Vc ** 2)) / n)
          if cert.sum() > 100 else None)
    bench = shell_benchmarks(eps, obs, float(w.min()), float(w.max()), S)
    res = dict(n=n, protocol="median-window-k350", sigma_eth=sig,
               kappa=sig / sb, r_mean=r_mean, r_sem=r_err, pr_over_n=pr,
               n_cert=int(cert.sum()), resid_max=float(rj.max()),
               band=[float(w[0]), float(w[-1])], t_eigsh=round(t_eig, 1),
               **bench)
    np.savez_compressed(os.path.join(OUT, f"msec_{tag}.npz"),
                        w=w, a=a, obs=obs, eps=eps, resid=rj)
    del V
    return res


def corner_lanczos(H, comp, S, steps):
    """Lanczos betas from the corner state (S, 0, ..., 0)."""
    n = H.shape[0]
    corner = np.zeros(n)
    corner[0] = 1.0            # compositions() puts the corner at row 0
    q = corner.copy()
    Q = np.empty((n, steps))
    alpha = np.empty(steps)
    beta = np.empty(steps - 1)
    got = steps
    for j in range(steps):
        Q[:, j] = q
        z = H @ q
        alpha[j] = float(q @ z)
        if j < steps - 1:
            z = z - alpha[j] * q - (beta[j - 1] * Q[:, j - 1] if j > 0 else 0.0)
            z -= Q[:, : j + 1] @ (Q[:, : j + 1].T @ z)
            nb = float(np.linalg.norm(z))
            if nb < 1e-12:
                got = j + 1
                break
            beta[j] = nb
            q = z / nb
    b = beta[: got - 1]
    return dict(steps=int(got), beta=b.tolist(),
                beta_max=float(b.max()) if b.size else None,
                beta_end=float(b[-1]) if b.size else None)


# ----------------------------------------------------------------------------
# legs
# ----------------------------------------------------------------------------
def leg_d2_closed(V_mode, S_list, U_list, h0=1.0, seed=7):
    """d = 2 legs.  U = 0: closed forms (no eigensolve).  U != 0: Jacobi
    eigensolve with vectors (S <= 2048)."""
    hmat = draw_couplings(2, h0, seed)
    h12 = float(hmat[0, 1])
    rows = []
    for U in U_list:
        for S in S_list:
            Vv = 36.0 / (S * S) if V_mode == "dose" else 0.3
            tag = f"d2_{V_mode}_U{int(U)}_S{S}"
            if U == 0.0:
                an = d2_analytic(S, Vv, h12)
                # validate against the tridiagonal eigensolve at small S
                val_dev = None
                if S <= 512:
                    a, b = d2_jacobi(S, 0.0, Vv, h12)
                    wv = eigh_tridiagonal(a, b, eigvals_only=True,
                                           check_finite=False)
                    val_dev = float(np.abs(np.sort(wv)
                                         - np.sort(an["E"])).max())
                sig = binned_sigma(an["E"], an["a"])
                sb = std_basis(S)
                comp = compositions(2, S)
                eps = comp @ np.log([2.0, 3.0])
                bench = shell_benchmarks(eps, comp[:, 0].astype(float),
                                         float(an["E"].min()),
                                         float(an["E"].max()), S)
                # spacing uniformity
                sp = np.diff(np.sort(an["E"]))
                rows.append(dict(
                    tag=tag, d=2, S=S, n=S + 1, U=U, V=Vv, h12=h12,
                    protocol="closed-form", kappa=sig / sb,
                    sigma_eth=sig, r_mean=1.0, r_sem=0.0,
                    pr_over_n=None, Omega=an["Omega"], C=an["C"],
                    kappa_floor=an["kappa_floor"],
                    spacing_rel_dev=float(sp.std() / sp.mean()) if S > 1 else 0.0,
                    eig_val_dev=val_dev, **bench))
                print(f"  {tag}: n={S+1} kappa={sig/sb:.5f} "
                      f"floor={an['kappa_floor']:.5f} "
                      f"<r>=1.000 (picket) B_count={bench['B_count']:.5f}"
                      f" val_dev={val_dev}", flush=True)
            else:
                if S > 2048:
                    continue
                a, b = d2_jacobi(S, U, Vv, h12)
                w, V = eigh_tridiagonal(a, b, check_finite=False)
                k = np.arange(S + 1, dtype=float)
                aa = (V ** 2).T @ k
                sig = binned_sigma(w, aa)
                sb = std_basis(S)
                r_mean, r_err = base.ratio_statistic(w)
                pr = float(np.mean(1.0 / np.einsum("ij,ij->j", V ** 2,
                                                   V ** 2)) / (S + 1))
                comp = compositions(2, S)
                eps = comp @ np.log([2.0, 3.0]) + U * comp[:, 0] * comp[:, 1]
                bench = shell_benchmarks(eps, comp[:, 0].astype(float),
                                         float(w.min()), float(w.max()), S)
                rows.append(dict(
                    tag=tag, d=2, S=S, n=S + 1, U=U, V=Vv, h12=h12,
                    protocol="jacobi-eig", kappa=sig / sb, sigma_eth=sig,
                    r_mean=r_mean, r_sem=r_err, pr_over_n=pr,
                    band=[float(w[0]), float(w[-1])], **bench))
                print(f"  {tag}: n={S+1} kappa={sig/sb:.5f} "
                      f"<r>={r_mean:.4f} PR/n={pr:.5f}", flush=True)
                np.savez_compressed(os.path.join(OUT, f"msec_{tag}.npz"),
                                    w=w, a=aa,
                                    obs=comp[:, 0].astype(float), eps=eps)
                del V
    return rows, h12


def anisotropic_Vpairs(d, seed, mean=0.3, spread=0.3):
    """Per-pair kinetic couplings V_pq = mean (1 + spread u), u ~ U(-1,1):
    the symmetry-breaking control at the same mean dose."""
    rng = np.random.default_rng(seed + 31415)
    Vp = np.eye(d) * 0.0
    for i in range(d):
        for j in range(i + 1, d):
            val = mean * (1.0 + spread * rng.uniform(-1, 1))
            Vp[i, j] = Vp[j, i] = val
    return Vp


def leg_aniso(d, S_list, h0=1.0, seed=7, Nwin=()):
    rows = []
    Vp = anisotropic_Vpairs(d, seed)
    for S in S_list:
        n = math.comb(S + d - 1, d - 1)
        tag = f"d{d}_aniso_U0_S{S}"
        H, eps, comp, _ = sector_block(d, S, h0, 0.0, 0.0, seed,
                                       Vpairs=Vp)
        t0 = time.perf_counter()
        if n <= N_DENSE:
            res = full_diag_diag(H, eps, comp, S, tag)
            res.update(d=d, S=S, U=0, V=0.3, Vpairs=[[float(x) for x in r]
                          for r in Vp], tag=tag,
                       t_diag=round(time.perf_counter() - t0, 1))
        else:
            res = window_diag(H, eps, comp, S, tag, k=350, seed=seed)
            res.update(d=d, S=S, U=0, V=0.3, Vpairs=[[float(x) for x in r]
                          for r in Vp], tag=tag,
                       t_win=round(time.perf_counter() - t0, 1))
        rows.append(res)
        print(f"  {tag}: n={n} kappa={res['kappa']:.5f} "
              f"<r>={res['r_mean']:.4f} PR/n={res['pr_over_n']:.5f} "
              f"B_count={res['B_count']:.5f}", flush=True)
        del H
    return rows


def leg_dense(d, S_list, V_mode, U, h0=1.0, seed=7):
    rows = []
    for S in S_list:
        n = math.comb(S + d - 1, d - 1)
        if n > N_DENSE:
            continue
        Vv = 36.0 / (S * S) if V_mode == "dose" else 0.3
        tag = f"d{d}_{V_mode}_U{int(U)}_S{S}"
        H, eps, comp, _ = sector_block(d, S, h0, U, Vv, seed)
        t0 = time.perf_counter()
        res = full_diag_diag(H, eps, comp, S, tag)
        res.update(d=d, S=S, U=U, V=Vv, tag=tag,
                   t_diag=round(time.perf_counter() - t0, 1))
        rows.append(res)
        print(f"  {tag}: n={n} kappa={res['kappa']:.5f} "
              f"<r>={res['r_mean']:.4f} PR/n={res['pr_over_n']:.5f} "
              f"B_count={res['B_count']:.5f} "
              f"({res['t_diag']}s)", flush=True)
        del H
    return rows


def leg_window(d, S_list, V_mode, U, h0=1.0, seed=7, k=350):
    rows = []
    for S in S_list:
        n = math.comb(S + d - 1, d - 1)
        Vv = 36.0 / (S * S) if V_mode == "dose" else 0.3
        tag = f"d{d}_{V_mode}_U{int(U)}_S{S}"
        H, eps, comp, _ = sector_block(d, S, h0, U, Vv, seed)
        t0 = time.perf_counter()
        res = window_diag(H, eps, comp, S, tag, k=k, seed=seed)
        res.update(d=d, S=S, U=U, V=Vv, tag=tag,
                   t_win=round(time.perf_counter() - t0, 1))
        rows.append(res)
        print(f"  {tag}: n={n} kappa={res['kappa']:.5f} "
              f"<r>={res['r_mean']:.4f} PR/n={res['pr_over_n']:.5f} "
              f"B_count={res['B_count']:.5f} "
              f"({res['t_win']}s, cert {res['n_cert']}/{k})", flush=True)
        del H
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--leg", default="all",
                   choices=("all", "validate", "structure", "d2", "d3",
                            "d4", "corner", "aniso"))
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    res_path = os.path.join(OUT, "c4_msector_results.json")
    res = json.load(open(res_path)) if os.path.exists(res_path) else {}

    if a.leg in ("all", "validate"):
        res["assembly_validation"] = validate_assembly()
    if a.leg in ("all", "structure"):
        res["structure"] = [check_block_tridiag(d, S, 1.0, 0.0, 0.3, 7)
                            for d, S in ((2, 64), (3, 24), (4, 12))]
        for c in res["structure"]:
            print(f"  J1 d={c['d']} S={c['S']}: max|dl|={c['max_dl']} "
                  f"(block-tridiag={c['block_tridiag']}) "
                  f"recursion dev={c['recursion_full_dev']}", flush=True)
    if a.leg in ("all", "d2"):
        S_dose = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
        res["d2_dose"], h12 = leg_d2_closed("dose", S_dose, [0.0, 2.0])
        res["d2_fixed"], _ = leg_d2_closed(
            "fixed", [8, 16, 32, 64, 128, 256, 512, 1024, 2048], [0.0, 2.0])
        res["d2_h12"] = h12
    def _save():
        res["wall_s"] = round(time.perf_counter() - _START, 1)
        with open(res_path, "w") as fh:
            json.dump(res, fh, indent=1)
    if a.leg in ("all", "d3"):
        res["d3_dose"] = (leg_dense(3, [20, 40, 60, 80, 100, 116], "dose", 0.0)
                          + leg_window(3, [130, 160, 200], "dose", 0.0))
        _save()
        res["d3_fixed"] = (leg_dense(3, [20, 40, 60, 80, 100, 116], "fixed", 0.0)
                           + leg_window(3, [130, 160], "fixed", 0.0))
        _save()
    if a.leg in ("all", "d4"):
        res["d4_dose"] = (leg_dense(4, [12, 20, 28, 32], "dose", 0.0)
                          + leg_window(4, [36, 40, 45, 50], "dose", 0.0))
        _save()
        res["d4_fixed"] = (leg_dense(4, [12, 20, 28, 32], "fixed", 0.0)
                           + leg_window(4, [36, 40, 45], "fixed", 0.0))
        _save()
    if a.leg in ("all", "aniso"):
        res["d3_aniso"] = (leg_aniso(3, [20, 40, 60, 80, 100, 116, 130, 160]))
        _save()
        res["d4_aniso"] = (leg_aniso(4, [12, 20, 28, 32, 36, 40, 45, 50]))
        _save()
    if a.leg in ("all", "corner"):
        cor = {}
        for d, S, Vv in ((2, 128, 36.0 / 128 ** 2), (2, 128, 0.3),
                         (3, 40, 36.0 / 40 ** 2), (3, 40, 0.3),
                         (4, 24, 36.0 / 24 ** 2), (4, 24, 0.3)):
            H, eps, comp, _ = sector_block(d, S, 1.0, 0.0, Vv, 7)
            steps = min(400, H.shape[0] - 1)
            cor[f"d{d}_S{S}_V{Vv:.4f}"] = corner_lanczos(H, comp, S, steps)
            print(f"  corner d={d} S={S} V={Vv:.4f}: beta_max="
                  f"{cor[f'd{d}_S{S}_V{Vv:.4f}']['beta_max']:.2f} "
                  f"beta_end={cor[f'd{d}_S{S}_V{Vv:.4f}']['beta_end']:.2f}",
                  flush=True)
            del H
        res["corner_lanczos"] = cor

    print("saved", res_path, f"({res['wall_s']}s)", flush=True)


if __name__ == "__main__":
    main()
