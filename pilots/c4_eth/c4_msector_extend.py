#!/usr/bin/env python3
"""
Fixed-V d>=3 sector-ladder extension: the registered decision object of the
C4 sector falsifier (extends c4_msector_jacobi.py; protocol unchanged).

The register (sec_register.tex, C4 row) fixes the decision object: the
fixed-V occupation-sector ladder in d >= 3, kappa(S) plateau versus crossing
to the Haar line with GOE <r>.  This extension adds rungs to the d=3 and
d=4 fixed-V ladders and opens the d=5 family, all at fixed V=0.3, U=0,
h0=1, k=350 median window, 30-bin quantile protocol, seed-7 coupling draw,
plus seed-8 replicate controls at two rungs per family.

PRE-REGISTERED DECISION RULE (committed before execution of these rungs):
(D1) CROSSING: a rung with kappa <= B_count is a crossing to the Haar line;
     the thermal verdict additionally requires <r> in the GOE band
     [0.506, 0.566] (0.5359 +/- 0.03) at that rung.
(D2) PLATEAU: the OLS slope alpha of log kappa vs log n over the last four
     window-protocol rungs of the family satisfies |alpha| <= 0.05.
(D3) SEPARATED DECAY: 0.05 < alpha < 0.45 over the window-protocol rungs:
     kappa / B_count grows as n^(1/2 - alpha); no crossing occurs in the
     power-law model.
(D4) THERMAL-RATE DECAY: alpha >= 0.45: a finite crossing scale
     n* = (A/c)^(1/(alpha - 1/2)) from the kappa and B_count power-law fits.
(D5) Verdict mapping: (D2)/(D3) settle the falsifier toward the obstruction
     side; (D1)/(D4) toward the thermal side; anything else (non-monotone
     kappa, slope uncertainty spanning the 0.45 boundary, crossing without
     the GOE band) is reported as open.  The seed-8 controls must leave the
     classification unchanged for a "settled" report.

Rungs (fixed V=0.3, U=0):
  d=3 window: S = 200, 240, 280, 320, 400, 480    (n to 115921)
  d=4 window: S = 55, 60, 65, 70                  (n to 62196)
  d=5 family: S = 12, 16 (dense), 20, 24, 26, 28  (n to 35960)
  seed-8 controls: d3 {200, 280}, d4 {55, 60}, d5 {20, 24}

Each rung is checkpointed (JSON save per rung; msec_<tag>.npz per point);
reruns skip rungs already recorded in the JSON.  RAM guard: address-space
cap 3.4 GB (proven on this platform), per-rung peak-RSS monitor, adaptive
fill-factor estimate per family (gamma = peak_RSS / (16 n bw_est)); a rung
is skipped and recorded when the estimated peak exceeds 2.7 GB or
MemAvailable < 1.0 GB.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_results.json (+ per-rung msec_*.npz, ext_guard log)
"""
import argparse
import json
import math
import os
import resource
import threading
import time
import traceback

import c4_msector_jacobi as mj
import c4_scaled_eth as base

OUT = base.OUT
V_FIXED = 0.3
ADDR_LIMIT = 3.4e9          # proven address-space cap on this platform
RSS_TARGET = 2.7e9          # skip if the estimated per-rung peak exceeds this
MEMAVAIL_MIN = 1.0e9        # skip if /proc/meminfo MemAvailable below this
GAMMA0 = 1.0                # pessimistic full-band fill prior

RUNGS = [
    # (d, S, seed) -- execution order: cheap first, guard-risky last
    (5, 12, 7), (5, 16, 7),
    (3, 200, 7), (3, 240, 7), (3, 280, 7),
    (4, 55, 7),
    (5, 20, 7), (5, 24, 7),
    (5, 20, 8), (5, 24, 8),
    (3, 200, 8), (3, 280, 8),
    (4, 55, 8),
    (3, 320, 7), (3, 400, 7),
    (4, 60, 7),
    (5, 26, 7),
    (4, 60, 8),
    (4, 65, 7),
    (3, 480, 7),
    (5, 28, 7),
    (4, 70, 7),
]


# ----------------------------------------------------------------------------
# guards
# ----------------------------------------------------------------------------
class PeakRSS:
    """Sample /proc/self/statm to track the true per-rung peak RSS."""

    def __init__(self, interval=0.4):
        self.peak = 0
        self._ev = threading.Event()
        self._th = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        while not self._ev.is_set():
            try:
                with open("/proc/self/statm") as fh:
                    rss = int(fh.read().split()[1]) * 4096
                if rss > self.peak:
                    self.peak = rss
            except (OSError, ValueError, IndexError):
                pass
            self._ev.wait(self._interval)

    def __enter__(self):
        self._interval = 0.4
        self._th.start()
        return self

    def __exit__(self, *exc):
        self._ev.set()
        self._th.join(timeout=2)


def current_rss():
    with open("/proc/self/statm") as fh:
        return int(fh.read().split()[1]) * 4096


def mem_available():
    with open("/proc/meminfo") as fh:
        for ln in fh:
            if ln.startswith("MemAvailable:"):
                return float(ln.split()[1]) * 1e3
    return 0.0


def layer_bw_est(d, S):
    """Upper bound on the band width of the layer-grading ordering: max over
    adjacent layer pairs of (size(l) + size(l+1)), size(l) = C(l+d-2, d-2)."""
    sizes = [math.comb(l + d - 2, d - 2) for l in range(S + 1)]
    return max(sizes[l] + sizes[l + 1] for l in range(S))


# ----------------------------------------------------------------------------
# rung execution
# ----------------------------------------------------------------------------
def family_key(d):
    return f"d{d}_fixed"


def rung_tag(d, S, seed):
    return (f"d{d}_fixed_U0_S{S}" if seed == 7
            else f"d{d}_fixed_U0_S{S}_sd{seed}")


def validate_d5_assembly(res):
    """d = 5 assembly check against the full-grid extraction (the committed
    validation covered d <= 4).  Runs once; skipped on reruns."""
    import numpy as np
    if res.get("assembly_validation_d5"):
        return res["assembly_validation_d5"]
    checks = res.setdefault("assembly_validation_d5", [])
    for U, V in ((0.0, 0.3), (2.0, 0.0)):
        d, S = 5, 4
        H, eps, comp, hmat = mj.sector_block(d, S, 1.0, U, V, 7)
        Hf, epsf, g, hmatf, coords = base.build_sparse(
            d, S, 0.0, 1.0, U, 7, V=V)
        shape = (S + 1,) * d
        grid = np.indices(shape)
        tot = np.zeros(shape, dtype=int)
        for i in range(d):
            tot += grid[i]
        sec = np.array(np.where(tot == S))
        keys_grid = sec.T @ ((S + 1) ** np.arange(d - 1, -1, -1))
        flat = np.ravel_multi_index(tuple(sec), shape)
        ogrid = np.argsort(keys_grid)
        rows_grid = flat[ogrid]
        keys_comp = comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
        ocomp = np.argsort(keys_comp)
        blk = Hf.tocsr()[rows_grid][:, rows_grid].toarray()
        Hperm = H.toarray()[ocomp][:, ocomp]
        dev = float(np.abs(Hperm - blk).max())
        ok = dev < 1e-13 and np.allclose(hmat, hmatf)
        checks.append(dict(d=5, S=S, U=U, V=V, max_dev=dev, ok=bool(ok)))
        print(f"  d5 assembly check U={U} V={V}: max_dev={dev:.2e} ok={ok}",
              flush=True)
    return checks


def run_rung(d, S, seed, gamma):
    """Build and solve one rung; returns (res_dict, peak_rss)."""
    n = math.comb(S + d - 1, d - 1)
    tag = rung_tag(d, S, seed)
    H, eps, comp, _ = mj.sector_block(d, S, 1.0, 0.0, V_FIXED, seed)
    t0 = time.perf_counter()
    with PeakRSS() as mon:
        if n <= mj.N_DENSE:
            res = mj.full_diag_diag(H, eps, comp, S, tag)
            res.update(d=d, S=S, U=0, V=V_FIXED, tag=tag, seed=seed,
                       t_diag=round(time.perf_counter() - t0, 1))
        else:
            res = mj.window_diag(H, eps, comp, S, tag, k=350, seed=seed)
            res.update(d=d, S=S, U=0, V=V_FIXED, tag=tag, seed=seed,
                       t_win=round(time.perf_counter() - t0, 1))
    del H
    return res, mon.peak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--addr-limit-gb", type=float, default=3.4,
                   help="address-space cap (proven 3.4 on this platform)")
    p.add_argument("--rss-target-gb", type=float, default=2.7)
    a = p.parse_args()

    try:
        resource.setrlimit(
            resource.RLIMIT_AS,
            (int(a.addr_limit_gb * 1e9), int(a.addr_limit_gb * 1e9)))
        print(f"RLIMIT_AS set to {a.addr_limit_gb:.1f} GB", flush=True)
    except (ValueError, OSError) as exc:
        print(f"RLIMIT_AS not set ({exc}); running unguarded", flush=True)
    rss_target = a.rss_target_gb * 1e9

    os.makedirs(OUT, exist_ok=True)
    res_path = os.path.join(OUT, "c4_msector_results.json")
    res = json.load(open(res_path))
    res.setdefault("ext_guard", [])

    validate_d5_assembly(res)

    base_rss = current_rss()
    gamma = {d: GAMMA0 for d in (3, 4, 5)}
    # calibrate gamma from any window rungs measured in this process
    for d, S, seed in RUNGS:
        n = math.comb(S + d - 1, d - 1)
        tag = rung_tag(d, S, seed)
        fam = res.get(family_key(d), [])
        ctrl = res.get("seed_controls", [])
        done = any(e.get("tag") == tag for e in (fam + ctrl))
        if done:
            print(f"  skip (done): {tag} n={n}", flush=True)
            continue
        bw = layer_bw_est(d, S)
        if n <= mj.N_DENSE:
            est = 24.0 * n * n          # dense eigh workspace
        else:
            est = gamma[d] * 16.0 * n * bw
        avail = mem_available()
        if est + 300e6 > rss_target or avail < MEMAVAIL_MIN:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n, bw_est=bw,
                       est_bytes=round(est), mem_avail=round(avail),
                       reason="RAM guard (adaptive fill estimate)")
            res["ext_guard"].append(rec)
            _save(res, res_path)
            print(f"  GUARD-SKIP {tag}: n={n} bw_est={bw} "
                  f"est={est/1e9:.2f}GB avail={avail/1e9:.2f}GB", flush=True)
            continue
        print(f"  run {tag}: n={n} bw_est={bw} est={est/1e9:.2f}GB "
              f"(gamma[{d}]={gamma[d]:.3f})", flush=True)
        try:
            out, peak = run_rung(d, S, seed, gamma[d])
            out["peak_rss_mb"] = round(peak / 1e6, 1)
            print(f"  {tag}: n={n} kappa={out['kappa']:.4f} "
                  f"<r>={out['r_mean']:.4f} PR/n={out['pr_over_n']:.4f} "
                  f"B_count={out['B_count']:.5f} "
                  f"peak={peak/1e9:.2f}GB "
                  f"({out.get('t_win', out.get('t_diag'))}s)", flush=True)
            if n > mj.N_DENSE and 16.0 * n * bw > 0:
                g_meas = max(0.05, (peak - base_rss) / (16.0 * n * bw))
                gamma[d] = max(gamma[d], g_meas)
                print(f"    gamma[{d}] -> {gamma[d]:.3f}", flush=True)
            if seed == 7:
                res.setdefault(family_key(d), []).append(out)
            else:
                res.setdefault("seed_controls", []).append(out)
            _save(res, res_path)
        except MemoryError:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n, bw_est=bw,
                       reason="MemoryError under the address-space cap")
            res["ext_guard"].append(rec)
            _save(res, res_path)
            print(f"  MEMORY-SKIP {tag} (n={n})", flush=True)
            gamma[d] = min(4.0, gamma[d] * 2)   # stay conservative
        except Exception as exc:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n,
                       reason=f"{type(exc).__name__}: {exc}",
                       trace=traceback.format_exc()[-800:])
            res["ext_guard"].append(rec)
            _save(res, res_path)
            print(f"  FAIL {tag}: {type(exc).__name__}: {exc}", flush=True)
    _save(res, res_path)
    print("extension complete", flush=True)


def _save(res, res_path):
    res["ext_wall_s"] = round(time.perf_counter(), 1)
    with open(res_path, "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
