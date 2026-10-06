#!/usr/bin/env python3
"""
Amendment A1 to the fixed-V d>=3 sector-ladder decision rule: tightened
classification and realization replication (extends c4_msector_extend.py;
the base rule and its committed rungs are untouched).

PURPOSE (registered).  The base rule (c3d55fb) adjudicates each family by a
point-estimate tail slope with a 0.05 plateau threshold and a seed-
substitution stability check.  At the measured realization scatter
(3-28% in kappa between coupling draws) point classes can flip under
substitution, the d=3 tail slope (+/-0.065, registered sign convention
kappa ~ n^-alpha) sits at the threshold, and the d=5 <r> exits the GOE
band at exactly the top rung.  This amendment adds rungs where the
shift-invert platform admits them, replicates coupling realizations at
the tail rungs, and replaces point thresholds with interval containment.
The falsifier's two branches (crossing to the Haar line vs obstruction)
are unchanged; the amendment only tightens how the measured ladders map
to a verdict.

PRE-REGISTERED AMENDMENT (committed before execution of the new rungs):

New rungs (fixed V=0.3, U=0, h0=1, k=350 median window, 30-bin protocol):
  d3 seed-7: S = 520, 560, 600, 640 (RAM-guard-adjudicated; skip records
             document the platform ceiling)
  d4 seed-7: S = 75, 80 (guard-adjudicated)
  d5 seed-7: S = 30 (guard-adjudicated; expected skip on this platform)
  replicates: d3 seeds {8,9,10} x S {400,480,520,560};
              d4 seeds {8,9,10} x S {55,60,65,70};
              d5 seeds {8,9,10,11} x S {20,24,26,28}
              (seed-8 already holds d5 S=20,24)
  Scaffold: rss target 3.0 GB (address-space cap unchanged at 3.4 GB,
  physical 4.1 GB); guard model unchanged, fill seeded from the peaks
  recorded in c4_msector_results.json.

(A1a) Tail set T_d per family: the completed seed-7 window-protocol rungs
      with S >= 400 (d=3), S >= 55 (d=4), all window rungs (d=5).
(A1b) Slope statistics on seed-mean values (mean over seeds with a
      completed rung at that S): alpha = WLS slope of ln kappa-bar vs
      ln n over T_d with weights = seed counts; gamma = WLS slope of
      ln(kappa/B)_bar vs ln n over T_d.
(A1c) 95% interval: the wider of (i) the WLS residual t-interval and
      (ii) the t-interval over per-seed OLS slopes on the rungs of T_d
      common to each seed (seeds with >= 3 common rungs; else (i)).
(A1d) Classes by interval containment:
      DIVERGENT  alpha_ci entirely <= -0.05 (kappa rising; kappa/B grows
                 as n^(1/2-alpha) with 1/2-alpha >= 0.55: crossing
                 excluded in the power-law model)
      PLATEAU    alpha_ci within [-0.05, 0.05]
      SEPARATED  alpha_ci within (0.05, 0.45)
      THERMAL    alpha_ci entirely >= 0.45 (finite crossing scale n*)
      else       sub-class unresolved (interval reported)
      All classes except THERMAL and CROSSING map to the obstruction side.
(A1e) Crossing branch: kappa <= B_count checked directly at every rung
      and every seed (families + replicates); the thermal verdict
      additionally requires seed-mean <r> in the GOE band
      [0.506, 0.566] at a crossing rung.
(A1f) Ratio extrapolation: gamma_ci entirely < 0 (ratio decaying toward
      the Haar line): report the fitted crossing scale n* with interval;
      gamma_ci >= 0: the ratio is non-decreasing under the fit - crossing
      excluded in-model at the measured level (report the minimum
      kappa/B over all seeds and rungs).
(A1g) d5 GOE-transit closure: seed-mean <r>-bar ladder with between-seed
      SEM.  RESOLVED-EXIT: the slope CI of <r>-bar vs ln n is entirely
      negative AND the top-rung interval lies below the GOE band center
      0.5359.  RESOLVED-PERSISTENT: the slope CI spans zero AND the
      top-rung interval lies inside the band.  Else: band-edge (interval
      reported).  The transit resolution refines the report; the
      crossing branch (A1e) is what settles the falsifier.
(A1h) Settled report: settled toward the obstruction side iff (i) no
      crossing at any seed/rung, (ii) every family's alpha_ci excludes
      THERMAL, and (iii) every family's gamma_ci >= 0 or its fitted n*
      interval lies entirely above 10^6 x n_max.  Sub-classes and the
      d5 transit resolution are reported with their intervals.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_results.json (+ per-rung msec_*.npz, ext_guard log)
"""
import argparse
import json
import math
import os
import resource
import time
import traceback

import c4_msector_extend as ext1
import c4_msector_jacobi as mj

OUT = ext1.OUT
ADDR_LIMIT = 3.4e9
RSS_TARGET_DEFAULT = 3.0e9     # scaffold change: 2.7 -> 3.0 (cap 3.4 kept)
BASE_RSS_ASSUMED = 0.35e9      # fill-seed base for recorded peaks

# (d, S, seed) -- cheap first, guard-risky ceiling probes last
RUNGS2 = [
    (5, 20, 9), (5, 20, 10), (5, 20, 11),
    (5, 24, 9), (5, 24, 10), (5, 24, 11),
    (5, 26, 8), (5, 26, 9), (5, 26, 10), (5, 26, 11),
    (3, 520, 7),
    (4, 75, 7),
    (3, 560, 7),
    (3, 400, 8), (3, 400, 9), (3, 400, 10),
    (3, 480, 8), (3, 480, 9), (3, 480, 10),
    (5, 28, 8), (5, 28, 9), (5, 28, 10), (5, 28, 11),
    (3, 520, 8), (3, 520, 9), (3, 520, 10),
    (4, 55, 8), (4, 55, 9), (4, 55, 10),
    (4, 60, 8), (4, 60, 9), (4, 60, 10),
    (3, 560, 8), (3, 560, 9), (3, 560, 10),
    (4, 65, 8), (4, 65, 9), (4, 65, 10),
    (4, 70, 8), (4, 70, 9), (4, 70, 10),
    # ceiling probes (RAM-guard-adjudicated; recorded, not run, if over)
    (3, 600, 7), (3, 640, 7), (4, 80, 7), (5, 30, 7),
]


def seed_fill_from_json(res):
    """Initialize the per-family fill estimate from the peak RSS values
    recorded in the results JSON (same two-term model as ext1)."""
    fill = {d: ext1.FILL_PRIOR for d in (3, 4, 5)}
    pools = [(f"d{d}_fixed", d) for d in (3, 4, 5)]
    pools.append(("seed_controls", None))
    for key, dmap in pools:
        for e in res.get(key, []):
            if dmap is None:
                d = e.get("d")
            else:
                d = dmap
            pk = e.get("peak_rss_mb")
            if (pk is None or d not in fill
                    or e.get("protocol") != "median-window-k350"):
                continue
            n, S = e["n"], e["S"]
            bw = ext1.layer_bw_est(d, S)
            f = (pk * 1e6 - BASE_RSS_ASSUMED - ext1.WS_PER_N * n) \
                / (16.0 * n * bw)
            fill[d] = max(fill[d], min(1.5, f))
    return fill


def est_time_s(res, d, S):
    """Wall-clock estimate for a rung from the family's largest completed
    rung (t_win scaled by n*bw)."""
    best = None
    for e in res.get(f"d{d}_fixed", []) + res.get("seed_controls", []):
        if e.get("d") == d and e.get("t_win"):
            if best is None or e["S"] > best[0]:
                best = (e["S"], e["n"], e["t_win"], e.get("protocol"))
    if best is None:
        return 600.0
    _, n_c, t_c, proto = best
    if proto != "median-window-k350":
        return 600.0
    n = math.comb(S + d - 1, d - 1)
    return t_c * (n * ext1.layer_bw_est(d, S)) / (n_c * ext1.layer_bw_est(d, best[0]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--addr-limit-gb", type=float, default=3.4)
    p.add_argument("--rss-target-gb", type=float, default=3.0)
    p.add_argument("--deadline-s", type=float, default=None,
                   help="clean exit between rungs once elapsed exceeds this")
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

    base_rss = ext1.current_rss()
    fill = seed_fill_from_json(res)
    print("fill seeds:", {d: round(f, 3) for d, f in fill.items()},
          flush=True)

    t_start = time.perf_counter()
    n_run = 0
    for d, S, seed in RUNGS2:
        n = math.comb(S + d - 1, d - 1)
        tag = ext1.rung_tag(d, S, seed)
        fam = res.get(ext1.family_key(d), [])
        ctrl = res.get("seed_controls", [])
        guard = res.get("ext_guard", [])
        done = any(e.get("tag") == tag for e in (fam + ctrl + guard))
        if done:
            print(f"  skip (done): {tag} n={n}", flush=True)
            continue
        if a.deadline_s is not None:
            elapsed = time.perf_counter() - t_start
            t_est = est_time_s(res, d, S)
            # a fresh chunk can absorb one big rung (outer timeout covers it)
            if elapsed > 30.0 and elapsed + 1.15 * t_est > a.deadline_s:
                print(f"  deadline exit before {tag} "
                      f"(est {t_est:.0f}s)", flush=True)
                break
        bw = ext1.layer_bw_est(d, S)
        est = fill[d] * 16.0 * n * bw + ext1.WS_PER_N * n + base_rss \
            + ext1.MARGIN
        avail = ext1.mem_available()
        if est > rss_target or avail < ext1.MEMAVAIL_MIN:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n, bw_est=bw,
                       est_bytes=round(est), mem_avail=round(avail),
                       reason="RAM guard (A1 ceiling probe)")
            res["ext_guard"].append(rec)
            ext1._save(res, res_path)
            print(f"  GUARD-SKIP {tag}: n={n} est={est/1e9:.2f}GB "
                  f"avail={avail/1e9:.2f}GB (fill[{d}]={fill[d]:.3f})",
                  flush=True)
            continue
        print(f"  run {tag}: n={n} est={est/1e9:.2f}GB "
              f"(fill[{d}]={fill[d]:.3f})", flush=True)
        try:
            out, peak = ext1.run_rung(d, S, seed)
            out["peak_rss_mb"] = round(peak / 1e6, 1)
            print(f"  {tag}: n={n} kappa={out['kappa']:.4f} "
                  f"<r>={out['r_mean']:.4f} PR/n={out['pr_over_n']:.4f} "
                  f"B={out['B_count']:.5f} peak={peak/1e9:.2f}GB "
                  f"({out.get('t_win', out.get('t_diag'))}s)", flush=True)
            if 16.0 * n * bw > 0:
                f_meas = (peak - base_rss - ext1.WS_PER_N * n) \
                    / (16.0 * n * bw)
                if f_meas > 0:
                    fill[d] = min(1.5, max(fill[d], f_meas))
                print(f"    fill[{d}] -> {fill[d]:.3f}", flush=True)
            if seed == 7:
                res.setdefault(ext1.family_key(d), []).append(out)
            else:
                res.setdefault("seed_controls", []).append(out)
            ext1._save(res, res_path)
            n_run += 1
        except MemoryError:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n, bw_est=bw,
                       reason="MemoryError under the address-space cap")
            res["ext_guard"].append(rec)
            ext1._save(res, res_path)
            print(f"  MEMORY-SKIP {tag} (n={n})", flush=True)
            fill[d] = min(1.5, fill[d] * 1.5)
        except Exception as exc:
            rec = dict(d=d, S=S, seed=seed, tag=tag, n=n,
                       reason=f"{type(exc).__name__}: {exc}",
                       trace=traceback.format_exc()[-800:])
            res["ext_guard"].append(rec)
            ext1._save(res, res_path)
            print(f"  FAIL {tag}: {type(exc).__name__}: {exc}", flush=True)
    ext1._save(res, res_path)
    print(f"amendment pass complete: {n_run} rungs this pass", flush=True)


if __name__ == "__main__":
    main()
