#!/usr/bin/env python3
"""
C4 pilot, part 2: interaction completion.

Finding from part 1: H_tot = H_P + H_W + H_hop is (up to amplitude modulation)
a SINGLE-PARTICLE tight-binding problem on the exponent lattice Z^d_{>=0}:
  - H_P: separable linear ramp  sum_i ln(p_i) k_i
  - H_W: per-axis adjacency (separable 1D chains)
  - H_hop: quadratic number-conserving hopping
No quartic interaction -> no genuine many-body chaos -> ETH structurally mis-typed
(O(1) eigenstate fluctuations, diagonal != microcanonical).

Here we add the minimal Bose-Hubbard density-density interaction
    H_int = U * sum_{i<j} n_i n_j   (diagonal, NON-separable quadratic potential)
which breaks separability, and re-run the same diagnostics.
If ETH diagnostics improve and diagonal -> micro, this identifies the minimal
repair under which C4 becomes a well-posed thermalization problem.
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
from c4_eth_pilot import (PRIMES, build_H, ratio_statistic, eth_diagnostics,
                          micro_reference, OUT)


def build_H_int(d, K, g0, h0, U, rng):
    H, eps, g, hmat = build_H(d, K, g0, h0, rng)
    coords = np.indices((K + 1,) * d)
    quad = np.zeros_like(eps)
    for i in range(d):
        for j in range(i + 1, d):
            quad += coords[i].ravel() * coords[j].ravel()
    H[np.diag_indices(len(eps))] += U * quad
    eps2 = eps + U * quad
    return H, eps2, g, hmat


def run_config_int(d, K, g0, h0, U, seed=7, evolve=True, tau_max=150.0, n_tau=1500, tag=""):
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    H, eps, g, hmat = build_H_int(d, K, g0, h0, U, rng)
    t_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    w, V = np.linalg.eigh(H)
    t_eig = time.perf_counter() - t0
    D = (K + 1) ** d

    coords = np.indices((K + 1,) * d)
    k1 = coords[0].ravel().astype(float)
    kd = coords[d - 1].ravel().astype(float)

    r_mean, rvals = ratio_statistic(w)
    eth = eth_diagnostics(w, V, k1)

    centers = np.array(eth["bin_centers"])
    smooth = np.array(eth["bin_smooth"])
    n = len(w); lo, hi = int(0.3 * n), int(0.7 * n)
    edges = np.quantile(w[lo:hi], np.linspace(0, 1, len(smooth) + 1))
    edges[0] -= 1e-9; edges[-1] += 1e-9
    micro = micro_reference(eps, k1, edges)
    valid = np.isfinite(micro) & np.isfinite(smooth)
    micro_rmse = float(np.sqrt(np.mean((smooth[valid] - micro[valid]) ** 2))) if valid.sum() else np.nan

    res = dict(tag=tag, d=d, K=K, D=D, g0=g0, h0=h0, U=U, seed=seed,
               t_build_s=round(t_build, 2), t_eigh_s=round(t_eig, 2),
               band=[float(w[0]), float(w[-1])],
               r_mean=r_mean, sigma_eth=eth["sigma_eth"], micro_rmse=micro_rmse)

    if evolve:
        e0 = np.zeros(D)
        i0 = tuple(0 if a != d - 1 else K for a in range(d))
        i0_flat = int(np.ravel_multi_index(i0, (K + 1,) * d))
        e0[i0_flat] = 1.0
        E0 = float(eps[i0_flat])
        c = V.T @ e0
        ad = V ** 2 @ kd
        diagonal = float(np.sum(c ** 2 * ad))
        win = (eps >= E0 - 1.0) & (eps <= E0 + 1.0)
        micro_d = float(kd[win].mean()) if win.sum() > 0 else np.nan
        taus = np.linspace(0, tau_max, n_tau)
        trace = np.empty(n_tau)
        for t_i, tau in enumerate(taus):
            psi = V @ (np.exp(-1j * tau * w) * c)
            trace[t_i] = float(np.abs(psi) ** 2 @ kd)
        half = n_tau // 2
        resid_fluct = float(np.std(trace[half:] - trace[half:].mean()))
        res["evolution"] = dict(E0=E0, diagonal=diagonal, micro_d=micro_d,
                                n_micro_states=int(win.sum()),
                                resid_fluct=resid_fluct,
                                dev_diag_vs_micro=abs(diagonal - micro_d) if np.isfinite(micro_d) else np.nan)
        np.savez_compressed(os.path.join(OUT, f"data_{tag}.npz"),
                            w=w, eth_E=np.array(eth["E_win"]), eth_a=np.array(eth["a_win"]),
                            bin_centers=centers, bin_smooth=smooth, micro=micro,
                            rvals=rvals, kd=kd, k1=k1, eps=eps,
                            tau=taus, trace=trace)
    else:
        np.savez_compressed(os.path.join(OUT, f"data_{tag}.npz"),
                            w=w, eth_E=np.array(eth["E_win"]), eth_a=np.array(eth["a_win"]),
                            bin_centers=centers, bin_smooth=smooth, micro=micro,
                            rvals=rvals, kd=kd, k1=k1, eps=eps)
    return res


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="comma-separated tags to run")
    args = ap.parse_args()

    all_configs = [
        (5, 4, 0.5, "d5K4U05"),
        (5, 4, 1.5, "d5K4U15"),
        (6, 3, 1.0, "d6K3U10"),
        (4, 6, 2.0, "d4K6U20"),
    ]
    only = set(args.only.split(",")) if args.only else None
    results = []
    for d, K, U, tag in all_configs:
        if only and tag not in only:
            continue
        print(f"[{tag}] d={d} K={K} U={U} ...", flush=True)
        r = run_config_int(d, K, g0=1.5, h0=1.0, U=U, tag=tag, evolve=True)
        results.append(r)
        ev = r.get("evolution", {})
        print(f"   eigh {r['t_eigh_s']}s | <r>={r['r_mean']:.3f} | sigma_ETH={r['sigma_eth']:.3f} | "
              f"micro_RMSE={r['micro_rmse']:.3f} | diag={ev.get('diagonal', float('nan')):.3f} "
              f"micro_d={ev.get('micro_d', float('nan')):.3f}", flush=True)

    outpath = os.path.join(OUT, "c4_results_interacting.json")
    if os.path.exists(outpath) and only:
        with open(outpath) as f:
            results = json.load(f) + results
    with open(outpath, "w") as f:
        json.dump(results, f, indent=1)
    print("saved", outpath)


if __name__ == "__main__":
    main()
