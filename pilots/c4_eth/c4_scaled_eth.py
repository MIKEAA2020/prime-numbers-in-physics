#!/usr/bin/env python3
"""
C4 (Cascade/ETH) SCALED attack -- sparse methods on the prime lattice, D ~ 10^4-10^5.

Couplings: g0 (H_W box drive), h0 (H_hop quadratic hops), U (diagonal quartic
U sum_{p<q} n_p n_q -- localizes), V (KINETIC completion: density-assisted
hopping V sum_{p<q} (n_p + n_q)(a_p^dag a_q + h.c.) -- off-diagonal quartic,
N_tot-preserving; the one-term addition that tests the kinetic candidate).

Extends the dense pilot (D <= 4096, c4_eth_pilot.py) in two tiers:
  * WINDOW tier: sparse CSR assembly + interior eigen-windows via shift-invert
    Lanczos (scipy splu + eigsh, MMD_AT_PLUS_A). LU fill caps this tier at
    D ~ 2.4e4 on 4 GB RAM; RLIMIT_AS makes the failure a catchable MemoryError.
  * EVOLVE tier: restarted-Lanczos Krylov time evolution (matvecs only, no
    factorization) -> equilibration diagnostics at D ~ 1e5. Complex Lanczos on
    the real-symmetric H; one full reorthogonalization pass per restart;
    restart step dt chosen adaptively so (||H||*dt)^(m+1)/(m+1)! <= 1e-10
    w.r.t. a Gershgorin norm. Validated against dense expm to 1e-13.

Stages (one process each, so wall-clock chunks always fit):
  --stage window : build + LU + eigsh + ETH diagnostics  -> res_{tag}.json
  --stage evolve : build + Krylov equilibration          -> appends to res_{tag}.json
  --stage both   : both in one process (small configs only)

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/res_{tag}.json (+ npz)
"""
import argparse
import json
import math
import os
import resource
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy.linalg import eigh_tridiagonal

OUT = "/home/z/my-project/download/pilot_c4_eth_scaled"
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

R_POISSON = 2 * np.log(2) - 1   # 0.3863
R_GOE = 0.5359
R_GUE = 0.5996

# Laptop RAM guard: allocation failure becomes a catchable MemoryError instead
# of an OOM kill, so the config falls back to the evolve-only tier.
_ADDR_LIMIT = 3.4e9
try:
    resource.setrlimit(resource.RLIMIT_AS, (int(_ADDR_LIMIT), int(_ADDR_LIMIT)))
except Exception:
    pass

_START = time.perf_counter()


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


# ----------------------------------------------------------------------------
# sparse assembly (faithful replica of the pilot's dense build)
# ----------------------------------------------------------------------------
def build_sparse(d, K, g0, h0, U, seed, V=0.0):
    rng = np.random.default_rng(seed)
    shape = (K + 1,) * d
    D = (K + 1) ** d
    ln_p = np.log(np.array(PRIMES[:d], dtype=float))
    strides = np.array([(K + 1) ** (d - 1 - i) for i in range(d)])
    idx_grid = np.arange(D).reshape(shape)
    coords = np.indices(shape)

    eps = np.zeros(D)
    for i in range(d):
        eps += coords[i].ravel() * ln_p[i]
    if U != 0.0:
        cross = np.zeros(D)
        for i in range(d):
            ki = coords[i].ravel()
            for j in range(i + 1, d):
                cross += ki * coords[j].ravel()
        eps = eps + U * cross

    rows, cols, vals = [], [], []

    # ---- H_W: g_i (M_i + M_i^dag) = per-axis box adjacency ----
    g = g0 * (1.0 + 0.3 * rng.uniform(-1, 1, size=d))
    for i in range(d):
        mask = coords[i] <= K - 1
        src = idx_grid[mask].ravel()
        tgt = src + strides[i]
        rows.append(src); cols.append(tgt); vals.append(np.full(src.size, g[i]))
        rows.append(tgt); cols.append(src); vals.append(np.full(src.size, g[i]))

    # ---- H_hop: h_ij (a_i^dag a_j + h.c.), ordered-pair loop as in the pilot ----
    hmat = np.zeros((d, d))
    for i in range(d):
        for j in range(d):
            if i != j:
                hmat[i, j] = h0 * rng.uniform(-1, 1)
    hmat = 0.5 * (hmat + hmat.T)
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
            v = hij * np.sqrt((ki + 1.0) * kj)
            rows.append(src); cols.append(tgt); vals.append(v)
            rows.append(tgt); cols.append(src); vals.append(v)

    # ---- H_kin: density-assisted hopping  V (n_i + n_j)(a_i^dag a_j + h.c.) ----
    # (n_i + n_j) commutes with a_i^dag a_j (one quantum up, one down), so the
    # hop |k> -> |k + e_i - e_j> carries amplitude (k_i + k_j) sqrt((k_i+1) k_j)
    # regardless of operator ordering.  Ordered-pair loop + both directions
    # double-counts each unordered pair; the 0.5 prefactor cancels it, so the
    # effective operator is exactly V sum_{p<q} (n_p + n_q)(a_p^dag a_q + h.c.).
    if V != 0.0:
        for i in range(d):
            for j in range(d):
                if i == j:
                    continue
                mask = (coords[j] >= 1) & (coords[i] <= K - 1)
                src = idx_grid[mask].ravel()
                tgt = src + strides[i] - strides[j]
                ki = coords[i][mask].ravel()
                kj = coords[j][mask].ravel()
                v = 0.5 * V * (ki + kj) * np.sqrt((ki + 1.0) * kj)
                rows.append(src); cols.append(tgt); vals.append(v)
                rows.append(tgt); cols.append(src); vals.append(v)

    # ---- H_P (+ U) diagonal ----
    rows.append(np.arange(D)); cols.append(np.arange(D)); vals.append(eps)

    H = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(D, D),
    ).tocsr()
    H.sum_duplicates()
    return H, eps, g, hmat, coords


# ----------------------------------------------------------------------------
# diagnostics
# ----------------------------------------------------------------------------
def ratio_statistic(w, trim=0.2):
    n = len(w)
    lo, hi = int(trim * n), int((1 - trim) * n)
    s = np.diff(w[lo:hi])
    r = np.minimum(s[:-1], s[1:]) / np.maximum(s[:-1], s[1:])
    return float(np.mean(r)), float(np.std(r) / np.sqrt(len(r)))


def eth_window(w, V, obs, n_bins=30):
    """V: (D, k) eigenvectors; obs: (D,) local observable."""
    a = (V ** 2).T @ obs                    # (k,) eigenstate values
    qs = np.quantile(w, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9; qs[-1] += 1e-9
    ibin = np.clip(np.searchsorted(qs, w, side="right") - 1, 0, n_bins - 1)
    smooth = np.full(n_bins, np.nan)
    fluct = []
    for b in range(n_bins):
        sel = ibin == b
        if sel.sum() >= 3:
            smooth[b] = a[sel].mean()
            fluct.append(a[sel].std())
    fluct = np.array([f for f in fluct if np.isfinite(f)])
    sigma_eth = float(np.sqrt(np.mean(fluct ** 2))) if len(fluct) else np.nan
    centers = 0.5 * (qs[:-1] + qs[1:])
    return dict(a=a, centers=centers, smooth=smooth,
                sigma_eth=sigma_eth, edges=qs)


def micro_reference(eps, obs, edges):
    ibin = np.clip(np.searchsorted(edges, eps, side="right") - 1, 0, len(edges) - 2)
    out = np.full(len(edges) - 1, np.nan)
    for b in range(len(edges) - 1):
        sel = ibin == b
        if sel.sum() > 0:
            out[b] = obs[sel].mean()
    return out


def participation(V):
    """Mean inverse participation ratio of eigenvectors, normalized by D."""
    ipr = np.einsum("ij,ij->j", V ** 2, V ** 2)      # sum_i |v|^4 per column
    return float(np.mean(1.0 / ipr) / V.shape[0])


# ----------------------------------------------------------------------------
# Krylov time evolution (restarted complex Lanczos, one full reorth pass)
# ----------------------------------------------------------------------------
def _gershgorin_norm(H):
    """Upper bound on ||H||_2 from row sums (H real symmetric)."""
    absrow = np.abs(H).sum(axis=1).A.ravel()
    return float(absrow.max())


def _choose_dt(hnorm, m, tol=1e-10, dt_max=0.25):
    """Largest dt <= dt_max with (hnorm*dt)^(m+1)/(m+1)! <= tol (one-restart bound)."""
    logfact = math.lgamma(m + 2)
    lo, hi = 1e-4, dt_max
    if (hnorm * hi) ** (m + 1) * math.exp(-logfact) <= tol:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        val = (m + 1) * math.log(max(hnorm * mid, 1e-300)) - logfact
        if val <= math.log(tol):
            lo = mid
        else:
            hi = mid
    return lo


def krylov_trace(H_shift, psi0, obs, tau_max, m, deadline):
    psi = psi0.astype(complex).copy()
    psi /= np.linalg.norm(psi)
    hnorm = _gershgorin_norm(H_shift)
    dt = _choose_dt(hnorm, m)
    n_steps = max(1, int(round(tau_max / dt)))
    trace = np.empty(n_steps + 1)
    trace[0] = float((np.abs(psi) ** 2) @ obs)
    Q = np.empty((psi.size, m), dtype=complex)
    alpha = np.empty(m); beta = np.empty(m - 1)
    t0 = time.perf_counter()
    truncated = False
    for step in range(n_steps):
        if step % 25 == 0 and time.perf_counter() - _START > deadline:
            truncated = True
            trace = trace[: step + 1]
            print(f"    [krylov] deadline reached at step {step}/{n_steps} "
                  f"(tau={step * dt:.0f})", flush=True)
            break
        # complex Lanczos on the real-symmetric H_shift
        q = psi / np.linalg.norm(psi)
        Q[:, 0] = q
        j = 0
        for j in range(m):
            z = H_shift @ Q[:, j]
            alpha[j] = float(np.real(np.vdot(Q[:, j], z)))
            if j < m - 1:
                z = z - alpha[j] * Q[:, j] - (beta[j - 1] * Q[:, j - 1] if j > 0 else 0.0)
                z -= Q[:, : j + 1] @ (Q[:, : j + 1].conj().T @ z)   # one reorth pass
                nrm = np.linalg.norm(z)
                if nrm < 1e-12:            # invariant subspace hit
                    break
                beta[j] = nrm
                Q[:, j + 1] = z / nrm
        jj = j + 1
        ev, evec = eigh_tridiagonal(alpha[:jj], beta[: jj - 1])
        c = evec[0, :] * np.linalg.norm(psi)      # psi = ||psi|| * Q[:,0]
        psi = Q[:, :jj] @ (evec @ (np.exp(-1j * dt * ev) * c))
        trace[step + 1] = float((np.abs(psi) ** 2) @ obs)
    t_evol = time.perf_counter() - t0
    norm_drift = abs(np.linalg.norm(psi) - 1.0)
    taus = np.arange(len(trace)) * dt
    half = len(taus) // 2
    return dict(tau=taus, trace=trace, t_evol=t_evol, norm_drift=float(norm_drift),
                dt=dt, m=m, hnorm=hnorm, truncated=truncated,
                time_avg=float(trace[half:].mean()),
                resid_fluct=float(trace[half:].std()))


# ----------------------------------------------------------------------------
# stages
# ----------------------------------------------------------------------------
def evolve_stage(res, H, eps, coords, d, K, D, tag, deadline):
    """Krylov equilibration from |K e_d> (shared by both tiers)."""
    obsd = coords[d - 1].ravel().astype(float)
    i0_flat = int(np.ravel_multi_index(tuple(0 if a != d - 1 else K for a in range(d)),
                                       (K + 1,) * d))
    E0 = float(eps[i0_flat])
    psi0 = np.zeros(D); psi0[i0_flat] = 1.0
    H_shift = (H - E0 * sp.identity(D, format="csr")).tocsr()
    m = 40 if D > 25000 else 48
    if D <= 25000:      tau_max = 250.0
    elif D <= 60000:    tau_max = 150.0
    else:               tau_max = 75.0
    ev = krylov_trace(H_shift, psi0, obsd, tau_max, m, deadline)
    # microcanonical reference at E0 (adaptive half-width, >=300 states)
    delta = 0.5
    while True:
        win = np.abs(eps - E0) <= delta
        if win.sum() >= 300 or delta >= 3.0:
            break
        delta *= 1.5
    micro_at_E0 = float(obsd[win].mean()) if win.sum() else float("nan")
    res["evolution"] = dict(
        E0=E0, delta=delta, n_micro_states=int(win.sum()),
        micro_d=micro_at_E0,
        time_avg=ev["time_avg"], resid_fluct=ev["resid_fluct"],
        norm_drift=ev["norm_drift"], t_evolve=round(ev["t_evol"], 1),
        diag_vs_micro=abs(ev["time_avg"] - micro_at_E0),
        m=m, dt=ev["dt"], hnorm=ev["hnorm"], tau_reached=float(ev["tau"][-1]),
        truncated=ev["truncated"],
    )
    print(f"  evolve {ev['t_evol']:.0f}s (dt={ev['dt']:.3f}, tau<={ev['tau'][-1]:.0f}) | "
          f"timeavg={ev['time_avg']:.3f} vs micro={micro_at_E0:.3f} "
          f"(|dev|={res['evolution']['diag_vs_micro']:.3f}) | "
          f"residfluct={ev['resid_fluct']:.4f} | normdrift={ev['norm_drift']:.1e}",
          flush=True)
    np.savez_compressed(os.path.join(OUT, f"evol_{tag}.npz"),
                        tau=ev["tau"], trace=ev["trace"])


def window_stage(res, H, eps, coords, d, K, D, tag, k, ncv, seed,
                 sigma_quantile=0.5, pivot="auto"):
    """Interior eigen-window via shift-invert Lanczos (LU-based).

    pivot='diag' passes diag_pivot_thresh=0.0 to SuperLU (always take the
    diagonal pivot).  For these symmetric-pattern matrices the default
    partial pivoting is VALUE-dependent and explodes on the kinetic (V)
    family -- off-diagonal row sums comparable to the diagonal destroy
    diagonal dominance, and SuperLU expands pivots, tripling+ the fill
    (generic d3K28: 257 s -> 3 s with diag pivots; solve residuals 1e-8).
    Diagonal pivoting can be unstable for indefinite matrices, so every
    window now records eigenpair residuals  max_j ||H v_j - w_j v_j||
    (certification; Rayleigh-Ritz in eigsh projects onto H itself).
    """
    import gc
    obs1 = coords[0].ravel().astype(float)
    obsd = coords[d - 1].ravel().astype(float)
    sigma = float(np.quantile(eps, sigma_quantile))
    res["sigma"] = sigma
    res["sigma_quantile"] = sigma_quantile
    t0 = time.perf_counter()
    A = (H - sigma * sp.identity(D, format="csr")).tocsc()
    try:
        try:
            if pivot == "diag":
                lu = spl.splu(A, permc_spec="MMD_AT_PLUS_A",
                              diag_pivot_thresh=0.0)
            else:
                lu = spl.splu(A, permc_spec="MMD_AT_PLUS_A")
        except MemoryError:
            res["tier"] = "evolve-only (LU fill exceeded RAM guard)"
            res["window"] = None
            del A; gc.collect()
            print("  LU memory-limited -> evolve-only tier", flush=True)
            return False
    except Exception as e:
        res["tier"] = f"evolve-only (splu failed: {type(e).__name__})"
        res["window"] = None
        res["splu_error"] = str(e)[:200]
        print(f"  FAILED splu: {e} -> classified evolve-only", flush=True)
        return False
    try:
        nnz_lu = lu.L.nnz + lu.U.nnz
    except MemoryError:
        nnz_lu = None      # L/U materialization exceeds RAM; lu.solve still works
    if nnz_lu is not None and nnz_lu > 2.0e8:
        res["tier"] = "evolve-only (LU fill guard, nnz_LU > 2e8)"
        res["window"] = None
        del lu, A; gc.collect()
        print("  SKIP window: LU fill guard -> evolve-only tier", flush=True)
        return False
    res["tier"] = "window"
    res.update(nnz_LU=(int(nnz_lu) if nnz_lu is not None else None),
               t_splu=round(time.perf_counter() - t0, 2),
               peak_rss_mb=round(peak_rss_mb(), 1))
    print(f"  splu {res['t_splu']}s nnzLU="
          f"{(nnz_lu / 1e6 if nnz_lu is not None else float('nan')):.1f}M "
          f"rss={res['peak_rss_mb']}MB", flush=True)

    OPinv = spl.LinearOperator((D, D), matvec=lu.solve, matmat=lu.solve,
                               dtype=np.float64)
    v0 = np.random.default_rng(seed + 1).standard_normal(D)
    t0 = time.perf_counter()
    try:
        w, V = spl.eigsh(H, k=k, sigma=sigma, which="LM", OPinv=OPinv,
                         ncv=ncv, v0=v0, maxiter=20000, tol=0)
    except Exception as e:
        res["error"] = f"eigsh failed: {type(e).__name__}: {e}"
        print(f"  FAILED eigsh: {e}", flush=True)
        return False
    t_eigsh = time.perf_counter() - t0
    order = np.argsort(w)
    w = w[order]; V = V[:, order]
    # eigenpair residual certification (max/median column norms of Hv - wv)
    R = H @ V - V * w[None, :]
    rj = np.linalg.norm(R, axis=0)
    res.update(t_eigsh=round(t_eigsh, 2), window=[float(w[0]), float(w[-1])],
               band_est=[float(eps.min()), float(eps.max())],
               eig_resid_max=float(rj.max()), eig_resid_med=float(np.median(rj)),
               pivot=pivot)

    r_mean, r_err = ratio_statistic(w)
    res["r_mean"], res["r_sem"] = r_mean, r_err

    eth1 = eth_window(w, V, obs1)
    ethd = eth_window(w, V, obsd)
    micro1 = micro_reference(eps, obs1, eth1["edges"])
    microd = micro_reference(eps, obsd, ethd["edges"])
    v1 = np.isfinite(micro1) & np.isfinite(eth1["smooth"])
    vd = np.isfinite(microd) & np.isfinite(ethd["smooth"])
    res.update(
        sigma_eth=eth1["sigma_eth"], sigma_eth_d=ethd["sigma_eth"],
        micro_rmse=float(np.sqrt(np.mean((eth1["smooth"][v1] - micro1[v1]) ** 2))) if v1.sum() else None,
        micro_rmse_d=float(np.sqrt(np.mean((ethd["smooth"][vd] - microd[vd]) ** 2))) if vd.sum() else None,
        pr_over_D=participation(V),
    )
    print(f"  eigsh {t_eigsh:.1f}s | <r>={r_mean:.4f}+-{r_err:.4f} | "
          f"sigma_ETH={res['sigma_eth']:.3f} | PR/D={res['pr_over_D']:.4f} | "
          f"microRMSE={res['micro_rmse']}", flush=True)

    np.savez_compressed(
        os.path.join(OUT, f"win_{tag}.npz"),
        w=w, a1=eth1["a"], ad=ethd["a"],
        centers=eth1["centers"], smooth1=eth1["smooth"], micro1=micro1,
        smoothd=ethd["smooth"], microd=microd,
    )
    return True


def _save(tag, res):
    with open(os.path.join(OUT, f"res_{tag}.json"), "w") as f:
        json.dump(res, f, indent=1)


def _load(tag):
    p = os.path.join(OUT, f"res_{tag}.json")
    return json.load(open(p)) if os.path.exists(p) else None


# ----------------------------------------------------------------------------
# main per-config driver
# ----------------------------------------------------------------------------
def run(tag, d, K, g0, h0, U, seed, k, ncv, stage, no_window, deadline,
        selftest=False, sigma_quantile=0.5, V=0.0, pivot="auto"):
    os.makedirs(OUT, exist_ok=True)
    res = _load(tag) or dict(tag=tag, d=d, K=K, g0=g0, h0=h0, U=U, seed=seed,
                             k=k, ncv=ncv, V=V)

    t0 = time.perf_counter()
    H, eps, g, hmat, coords = build_sparse(d, K, g0, h0, U, seed, V=V)
    D = H.shape[0]
    res.update(D=D, nnz_H=int(H.nnz), t_build=round(time.perf_counter() - t0, 2),
               g=[round(x, 4) for x in g])
    print(f"[{tag}] D={D} nnz={H.nnz} build {res['t_build']}s "
          f"(stage={stage})", flush=True)

    if selftest:
        # dense cross-check at pilot scale (pipeline validation)
        w_dense = np.linalg.eigvalsh(H.toarray())
        w_sp, _ = spl.eigsh(H, k=min(300, D - 2), which="LM")
        print(f"  selftest |w_dense_max-w_sp_max| = {abs(w_dense.max() - w_sp.max()):.2e}",
              flush=True)

    if stage in ("window", "both"):
        if "r_mean" in res or res.get("window") is None and "tier" in res:
            print("  window stage already done (r_mean present or classified evolve-only)", flush=True)
        elif no_window:
            res.setdefault("tier", "evolve-only (LU infeasible at this D; pre-classified)")
            res["window"] = None
            print("  --no-window: evolve tier", flush=True)
        else:
            window_stage(res, H, eps, coords, d, K, D, tag, k, ncv, seed,
                         sigma_quantile, pivot)
        _save(tag, res)

    if stage in ("evolve", "both"):
        if "evolution" in res:
            print("  evolve stage already done", flush=True)
        else:
            evolve_stage(res, H, eps, coords, d, K, D, tag, deadline)
        _save(tag, res)

    res["peak_rss_mb"] = round(peak_rss_mb(), 1)
    _save(tag, res)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--d", type=int, required=True)
    p.add_argument("--K", type=int, required=True)
    p.add_argument("--g0", type=float, default=1.5)
    p.add_argument("--h0", type=float, default=1.0)
    p.add_argument("--U", type=float, default=0.0)
    p.add_argument("--V", type=float, default=0.0,
                   help="kinetic completion: density-assisted hopping "
                        "V sum_{p<q} (n_p+n_q)(a_p^dag a_q + h.c.)")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--k", type=int, default=0)
    p.add_argument("--stage", choices=("window", "evolve", "both"), default="both")
    p.add_argument("--no-window", action="store_true")
    p.add_argument("--sigma-quantile", type=float, default=0.5)
    p.add_argument("--pivot", choices=("auto", "diag"), default="auto",
                   help="splu pivoting: 'diag' = diag_pivot_thresh 0 (fast,"
                        " symmetric-pattern; needed for the V-kinetic family)")
    p.add_argument("--deadline", type=float, default=430.0,
                   help="wall-clock budget in seconds from process start")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    D = (a.K + 1) ** a.d
    if a.k == 0:
        if D <= 12000:    k, ncv = 600, 700
        elif D <= 26000:  k, ncv = 350, 430
        elif D <= 50000:  k, ncv = 350, 430
        else:             k, ncv = 300, 370
    else:
        k, ncv = a.k, a.k + 100
    run(a.tag, a.d, a.K, a.g0, a.h0, a.U, a.seed, k, ncv, a.stage,
        a.no_window, a.deadline, a.selftest, sigma_quantile=a.sigma_quantile,
        V=a.V, pivot=a.pivot)


if __name__ == "__main__":
    main()
