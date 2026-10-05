#!/usr/bin/env python3
"""
C4 (Cascade/ETH) pilot attack -- finite-truncation ETH simulation on the prime lattice.

System (sec_dynamics.tex, Eq. fullH):
    H_tot = H_P + H_W + H_hop
    H_P   = diag(hbar*w0*log n),  n = prod p_i^{k_i}          (hbar*w0 = 1)
    H_W   = sum_i g_i (M_i + M_i^dagger)   (box adjacency per axis)
    H_hop = sum_{i!=j} h_ij (a_i^dagger a_j + h.c.), h_ij = h_ji (real)

Truncation: d active modes (first d primes), occupation cap K -> D = (K+1)^d.

Diagnostics:
  1. Level-spacing ratio statistic <r> (Poisson 0.3863, GOE 0.5359, GUE 0.5996)
     -> C5 proxy (arithmetic-chaos correspondence).
  2. ETH of local observable A = n_hat_1 (occupation of prime-2 mode):
     eigenstate values a_j = <E_j|A|E_j>, binned smooth curve, within-bin
     fluctuation sigma_ETH, comparison to truncated microcanonical reference.
  3. Equilibration: initial state |K e_d> (all quanta in highest prime mode),
     time evolution, diagonal ensemble vs microcanonical at E0.
  4. Finite-size trend across (d,K).
  5. Weak-coupling control (falsifier-side discriminacy check).

Outputs -> /home/z/my-project/download/pilot_c4_eth/
"""
import json
import time
import numpy as np

OUT = "/home/z/my-project/download/pilot_c4_eth"
import os
os.makedirs(OUT, exist_ok=True)

PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23]

# Reference values for the ratio statistic (Atas et al. 2013)
R_POISSON = 2 * np.log(2) - 1  # 0.3863
R_GOE = 0.5359
R_GUE = 0.5996


def build_H(d, K, g0, h0, rng):
    """Assemble dense H_tot on the truncated arithmetic Hilbert space."""
    shape = (K + 1,) * d
    D = (K + 1) ** d
    ln_p = np.log(np.array(PRIMES[:d], dtype=float))

    # flat index raveled C-order; per-axis strides
    strides = np.array([(K + 1) ** (d - 1 - i) for i in range(d)])
    idx_grid = np.arange(D).reshape(shape)
    coords = np.indices(shape)  # (d, K+1, ..., K+1)

    # site energies: log n = sum_i k_i log p_i
    eps = np.zeros(D)
    for i in range(d):
        eps += coords[i].ravel() * ln_p[i]

    H = np.zeros((D, D))

    # ---- H_W: g_i (M_i + M_i^dagger) = axis adjacency ----
    g = g0 * (1.0 + 0.3 * rng.uniform(-1, 1, size=d))
    for i in range(d):
        mask = coords[i] <= K - 1
        src = idx_grid[mask].ravel()
        tgt = src + strides[i]
        H[src, tgt] += g[i]
        H[tgt, src] += g[i]

    # ---- H_hop: h_ij (a_i^dag a_j + h.c.) ----
    hmat = np.zeros((d, d))
    for i in range(d):
        for j in range(d):
            if i != j:
                hmat[i, j] = h0 * rng.uniform(-1, 1)
    hmat = 0.5 * (hmat + hmat.T)  # enforce real symmetry h_ij = h_ji
    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            hij = hmat[i, j]
            if hij == 0.0:
                continue
            # source k with k_j >= 1 and k_i <= K-1 ; target k + e_i - e_j
            mask = (coords[j] >= 1) & (coords[i] <= K - 1)
            src = idx_grid[mask].ravel()
            tgt = src + strides[i] - strides[j]
            ki = coords[i][mask].ravel()
            kj = coords[j][mask].ravel()
            vals = hij * np.sqrt((ki + 1.0) * kj)
            H[src, tgt] += vals
            H[tgt, src] += vals

    H[np.diag_indices(D)] += eps  # H_P
    return H, eps, g, hmat


def ratio_statistic(w):
    """Nearest-neighbor ratio statistic on the middle 50% of the spectrum."""
    n = len(w)
    lo, hi = int(0.25 * n), int(0.75 * n)
    s = np.diff(w[lo:hi])
    r = np.minimum(s[:-1], s[1:]) / np.maximum(s[:-1], s[1:])
    return float(np.mean(r)), r


def eth_diagnostics(w, V, obs_vec, n_bins=40, window=(0.3, 0.7)):
    """ETH diagnostics for local observable A (given as diagonal obs_vec)."""
    n = len(w)
    lo, hi = int(window[0] * n), int(window[1] * n)
    ww = w[lo:hi]
    # eigenstate expectation values
    P = V[lo:hi, :] ** 2 @ obs_vec  # a_j for j in window
    # quantile bins on eigen-energies
    qs = np.quantile(ww, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9; qs[-1] += 1e-9
    ibin = np.clip(np.searchsorted(qs, ww, side="right") - 1, 0, n_bins - 1)
    smooth = np.full(n_bins, np.nan)
    fluct = []
    for b in range(n_bins):
        sel = ibin == b
        if sel.sum() >= 3:
            smooth[b] = P[sel].mean()
            fluct.append(P[sel].std())
    fluct = np.array([f for f in fluct if np.isfinite(f)])
    sigma_eth = float(np.sqrt(np.mean(fluct ** 2))) if len(fluct) else np.nan
    centers = 0.5 * (qs[:-1] + qs[1:])
    return dict(
        E_win=ww.tolist(), a_win=P.tolist(),
        bin_centers=centers[np.isfinite(smooth)].tolist(),
        bin_smooth=smooth[np.isfinite(smooth)].tolist(),
        sigma_eth=sigma_eth,
    )


def micro_reference(eps, obs_vec, edges):
    """Truncated microcanonical mean of obs over basis states per energy bin."""
    ibin = np.clip(np.searchsorted(edges, eps, side="right") - 1, 0, len(edges) - 2)
    out = []
    for b in range(len(edges) - 1):
        sel = ibin == b
        out.append(float(obs_vec[sel].mean()) if sel.sum() > 0 else np.nan)
    return np.array(out, dtype=float)


def run_config(d, K, g0, h0, seed=7, evolve=False, tau_max=150.0, n_tau=4000, tag=""):
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    H, eps, g, hmat = build_H(d, K, g0, h0, rng)
    t_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    w, V = np.linalg.eigh(H)
    t_eig = time.perf_counter() - t0
    D = (K + 1) ** d

    # local observables: occupation of mode 1 (prime 2) and mode d (largest prime)
    coords = np.indices((K + 1,) * d)
    k1 = coords[0].ravel().astype(float)
    kd = coords[d - 1].ravel().astype(float)

    r_mean, rvals = ratio_statistic(w)

    # ETH for A = n_1
    eth = eth_diagnostics(w, V, k1)
    # microcanonical reference on the same bin edges as the ETH bins
    centers = np.array(eth["bin_centers"])
    smooth = np.array(eth["bin_smooth"])
    # rebuild edges as quantiles of eigenvalues across full spectrum window:
    n = len(w); lo, hi = int(0.3 * n), int(0.7 * n)
    edges = np.quantile(w[lo:hi], np.linspace(0, 1, len(smooth) + 1))
    edges[0] -= 1e-9; edges[-1] += 1e-9
    micro = micro_reference(eps, k1, edges)
    valid = np.isfinite(micro) & np.isfinite(smooth)
    micro_rmse = float(np.sqrt(np.mean((smooth[valid] - micro[valid]) ** 2))) if valid.sum() else np.nan

    res = dict(
        tag=tag, d=d, K=K, D=D, g0=g0, h0=h0, seed=seed,
        g=[round(x, 4) for x in g],
        t_build_s=round(t_build, 2), t_eigh_s=round(t_eig, 2),
        band=[float(w[0]), float(w[-1])],
        r_mean=r_mean,
        sigma_eth=eth["sigma_eth"],
        micro_rmse=micro_rmse,
    )

    evol = None
    if evolve:
        # initial state |K e_d>: all quanta in the highest-prime mode
        e0 = np.zeros(D)
        i0 = tuple(0 if a != d - 1 else K for a in range(d))
        i0_flat = int(np.ravel_multi_index(i0, (K + 1,) * d))
        e0[i0_flat] = 1.0
        E0 = float(eps[i0_flat])
        c = V.T @ e0
        ad = V ** 2 @ kd  # <E_j| n_d |E_j> for all j
        diagonal = float(np.sum(c ** 2 * ad))
        # microcanonical reference at E0 (bin with basis energies near E0)
        win = (eps >= E0 - 1.0) & (eps <= E0 + 1.0)
        micro_d = float(kd[win].mean()) if win.sum() > 0 else np.nan
        # time trace
        taus = np.linspace(0, tau_max, n_tau)
        trace = np.empty(n_tau)
        for t_i, tau in enumerate(taus):
            psi = V @ (np.exp(-1j * tau * w) * c)
            trace[t_i] = float(np.abs(psi) ** 2 @ kd)
        half = n_tau // 2
        resid_fluct = float(np.std(trace[half:] - trace[half:].mean()))
        evol = dict(E0=E0, i0=i0_flat, diagonal=diagonal, micro_d=micro_d,
                    n_micro_states=int(win.sum()),
                    tau=taus.tolist(), trace=trace.tolist(),
                    resid_fluct=resid_fluct,
                    dev_diag_vs_micro=abs(diagonal - micro_d) if np.isfinite(micro_d) else np.nan)
        res["evolution"] = dict(E0=E0, diagonal=diagonal, micro_d=micro_d,
                                n_micro_states=evol["n_micro_states"],
                                resid_fluct=resid_fluct,
                                dev_diag_vs_micro=evol["dev_diag_vs_micro"])

    # persist raw arrays for figures
    np.savez_compressed(
        os.path.join(OUT, f"data_{tag}.npz"),
        w=w, eth_E=np.array(eth["E_win"]), eth_a=np.array(eth["a_win"]),
        bin_centers=centers, bin_smooth=smooth, micro=micro,
        rvals=rvals, kd=kd, k1=k1, eps=eps,
        **({} if evol is None else
           {"tau": np.array(evol["tau"]), "trace": np.array(evol["trace"])}))
    res["_eth_arrays"] = dict(bin_centers=eth["bin_centers"], bin_smooth=eth["bin_smooth"])
    return res


def main():
    results = []

    # finite-size scan (strong coupling, generic)
    configs = [
        (4, 4, 625, "d4K4"),
        (5, 3, 1024, "d5K3"),
        (4, 6, 2401, "d4K6"),
        (5, 4, 3125, "d5K4"),
        (4, 7, 4096, "d4K7"),
        (6, 3, 4096, "d6K3"),
    ]
    for d, K, D, tag in configs:
        print(f"[{tag}] d={d} K={K} D={D} ...", flush=True)
        evolve = tag in ("d5K4", "d4K6")
        r = run_config(d, K, g0=1.5, h0=1.0, tag=tag, evolve=evolve)
        results.append(r)
        print(f"   eigh {r['t_eigh_s']}s | <r>={r['r_mean']:.3f} | "
              f"sigma_ETH={r['sigma_eth']:.3f} | micro_RMSE={r['micro_rmse']:.3f}", flush=True)

    # weak-coupling control on d5K4
    print("[d5K4weak] weak coupling control ...", flush=True)
    rw = run_config(5, 4, g0=0.05, h0=0.03, tag="d5K4weak", evolve=True)
    results.append(rw)
    print(f"   eigh {rw['t_eigh_s']}s | <r>={rw['r_mean']:.3f} | "
          f"sigma_ETH={rw['sigma_eth']:.3f} | micro_RMSE={rw['micro_rmse']:.3f}", flush=True)

    with open(os.path.join(OUT, "c4_results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("saved", os.path.join(OUT, "c4_results.json"))


if __name__ == "__main__":
    main()
