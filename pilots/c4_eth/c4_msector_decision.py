#!/usr/bin/env python3
"""
Adjudication of the fixed-V d>=3 sector ladders under the pre-registered
decision rule (c4_msector_extend.py, committed c3d55fb BEFORE execution):

(D1) CROSSING: a rung with kappa <= B_count is a crossing to the Haar line;
     the thermal verdict additionally requires <r> in the GOE band
     [0.506, 0.566] (0.5359 +/- 0.03) at that rung.
(D2) PLATEAU: |slope| <= 0.05 in the OLS fit of log kappa vs log n over the
     last four window-protocol rungs of the family.
(D3) SEPARATED DECAY: 0.05 < decay rate alpha < 0.45 over the window-protocol
     rungs: kappa/B_count grows as n^(1/2 - alpha); no crossing in the
     power-law model.
(D4) THERMAL-RATE DECAY: alpha >= 0.45: finite crossing scale n* from the
     kappa and B_count power-law fits.
(D5) Verdict mapping: (D2)/(D3) -> obstruction side; (D1)/(D4) -> thermal
     side; else open.  Seed-8 controls must leave the class unchanged for a
     "settled" report.

Inputs:  c4_msector_results.json (base ladders + extension + seed_controls)
Output:  c4_msector_decision.json + printed verdict table
"""
import json
import math
import os

import numpy as np

import c4_scaled_eth as base

OUT = base.OUT
R_GOE = 0.5359
GOE_HALF = 0.03
FAMILIES = ("d3_fixed", "d4_fixed", "d5_fixed")


def ols(x, y):
    """OLS slope, intercept, slope SE, residual RMS."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 2:
        return None, None, None, None
    A = np.vstack([x, np.ones_like(x)]).T
    coef, res, rank, sv = np.linalg.lstsq(A, y, rcond=None)
    slope, icept = float(coef[0]), float(coef[1])
    yhat = A @ coef
    ss = float(np.sum((y - yhat) ** 2))
    sxx = float(np.sum((x - x.mean()) ** 2))
    if sxx == 0 or len(x) == 2:
        return slope, icept, None, None
    se = math.sqrt(ss / (len(x) - 2) / sxx)
    return slope, icept, se, math.sqrt(ss / len(x))


def classify(wr):
    """Apply (D1)-(D4) to the window rungs wr (dict list, sorted by n)."""
    n = np.array([r["n"] for r in wr], float)
    kap = np.array([r["kappa"] for r in wr], float)
    B = np.array([r["B_count"] for r in wr], float)
    rmean = np.array([r["r_mean"] for r in wr], float)
    rsem = np.array([r.get("r_sem") or 0.0 for r in wr], float)
    ratio = kap / B

    cross = bool((kap <= B).any())
    cross_rung = [int(wr[i]["S"]) for i in range(len(wr)) if kap[i] <= B[i]]
    tail = wr[-min(4, len(wr)):]
    s_tail, _, se_tail, _ = ols([math.log(r["n"]) for r in tail],
                                [math.log(r["kappa"]) for r in tail])
    s_all, i_all, se_all, _ = ols(np.log(n), np.log(kap))
    s_B, i_B, se_B, _ = ols(np.log(n), np.log(B))
    alpha = (-s_all) if s_all is not None else None
    alpha_tail = (-s_tail) if s_tail is not None else None

    # crossing scale under the two power laws (finite iff alpha > 1/2)
    n_star = None
    if s_all is not None and s_B is not None and s_B != s_all:
        log_ns = (i_B - i_all) / (s_all - s_B)
        if log_ns > math.log(n.max()):
            n_star = float(math.exp(log_ns))

    r_last = float(rmean[-1])
    r_in_goe = abs(r_last - R_GOE) <= GOE_HALF
    r_band = [float(rmean[-1] - rsem[-1]), float(rmean[-1] + rsem[-1])]

    if cross:
        cls = "crossing" if r_in_goe else "crossing-noGOE"
    elif alpha_tail is not None and abs(alpha_tail) <= 0.05:
        cls = "plateau"
    elif alpha is not None and alpha >= 0.45:
        cls = "thermal-rate-decay"
    elif alpha is not None and 0.05 < alpha < 0.45:
        cls = "separated-decay"
    else:
        cls = "open"
    side = ("thermal" if cls in ("crossing", "thermal-rate-decay")
            else "obstruction" if cls in ("plateau", "separated-decay")
            else "open")   # crossing-noGOE and unclassified stay open (D5)
    return dict(
        window_rungs=len(wr), n_max=float(n.max()),
        kappa_last=float(kap[-1]), kappa_min=float(kap.min()),
        B_last=float(B[-1]), ratio_min=float(ratio.min()),
        ratio_last=float(ratio[-1]), ratio_growth_slope=(
            float(s_all - s_B) if (s_all is not None and s_B is not None)
            else None),
        alpha=alpha, alpha_se=(se_all if se_all is not None else None),
        alpha_tail=alpha_tail,
        alpha_tail_se=(se_tail if se_tail is not None else None),
        slope_B=(s_B if s_B is not None else None),
        crossing=cross, crossing_rungs=cross_rung, n_star=n_star,
        r_last=r_last, r_sem_last=float(rsem[-1]), r_band=r_band,
        r_in_goe_band=bool(r_in_goe), klass=cls, side=side,
        table=[dict(S=int(r["S"]), n=int(r["n"]), protocol=r["protocol"],
                    kappa=float(r["kappa"]), B_count=float(r["B_count"]),
                    ratio=float(r["kappa"] / r["B_count"]),
                    r=float(r["r_mean"]),
                    r_sem=float(r.get("r_sem") or 0.0),
                    pr=float(r["pr_over_n"])) for r in wr])


def seed_stability(res, fam_report):
    """(D5): substitute the seed-8 values at the control rungs and recheck
    the family class."""
    ctrls = res.get("seed_controls", [])
    out = []
    for fam in FAMILIES:
        d = int(fam[1])
        base_rungs = [r for r in res.get(fam, [])]
        sub = {c["S"]: c for c in ctrls
               if c.get("d") == d and c.get("seed", 8) == 8}
        if not sub:
            out.append(dict(family=fam, controls=0, stable=None))
            continue
        wr = [r for r in base_rungs
              if r.get("protocol") == "median-window-k350"
              and r.get("kappa") is not None]
        deltas = []
        for c in sub.values():
            match = [r for r in wr if r["S"] == c["S"]]
            if match:
                deltas.append(dict(
                    S=int(c["S"]),
                    kappa7=float(match[0]["kappa"]),
                    kappa8=float(c["kappa"]),
                    r7=float(match[0]["r_mean"]), r8=float(c["r_mean"]),
                    dk_rel=abs(c["kappa"] - match[0]["kappa"])
                    / match[0]["kappa"]))
        merged = {r["S"]: dict(r) for r in wr}
        for c in sub.values():
            if c["S"] in merged:
                m = dict(merged[c["S"]])
                m["kappa"] = c["kappa"]
                m["r_mean"] = c["r_mean"]
                merged[c["S"]] = m
        wr2 = [merged[S] for S in sorted(merged)]
        cls2 = classify(wr2) if len(wr2) >= 3 else None
        stable = (cls2["klass"] == fam_report[fam]["klass"]
                  if cls2 else None)
        out.append(dict(family=fam, controls=len(sub), deltas=deltas,
                        klass_subst=(cls2["klass"] if cls2 else None),
                        stable=stable))
    return out


def main():
    res = json.load(open(os.path.join(OUT, "c4_msector_results.json")))
    report = {}
    for fam in FAMILIES:
        rows = [r for r in res.get(fam, [])
                if r.get("kappa") is not None]
        rows.sort(key=lambda r: r["n"])
        wr = [r for r in rows
              if r.get("protocol") == "median-window-k350"]
        dense = [r for r in rows if r.get("protocol") == "full-spectrum"]
        if len(wr) >= 3:
            report[fam] = classify(wr)
            report[fam]["dense_rungs"] = [
                dict(S=int(r["S"]), n=int(r["n"]), kappa=float(r["kappa"]),
                     r=float(r["r_mean"])) for r in dense]
        else:
            report[fam] = dict(klass="pending", side="open",
                               window_rungs=len(wr),
                               dense_rungs=len(dense))

    seed = seed_stability(res, report)

    sides = [report[f]["side"] for f in FAMILIES
             if report[f]["side"] != "open"]
    settled = (len(sides) == len(FAMILIES) and len(set(sides)) == 1
               and all(s["stable"] is not False for s in seed if s))
    overall = (f"settled: {sides[0]} side"
               if settled else "open (mixed or pending)")

    out = dict(families=report, seed_stability=seed,
               overall=overall, settled=bool(settled))
    path = os.path.join(OUT, "c4_msector_decision.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)

    for fam in FAMILIES:
        rp = report[fam]
        print(f"== {fam}: {rp.get('klass')} ({rp.get('side')} side)")
        for k in ("window_rungs", "n_max", "kappa_last", "B_last",
                  "ratio_last", "ratio_min", "alpha", "alpha_se",
                  "alpha_tail", "slope_B", "crossing", "n_star",
                  "r_last", "r_in_goe_band"):
            if k in rp and rp[k] is not None:
                print(f"   {k}: {rp[k]}")
        for row in rp.get("table", []):
            print(f"   S={row['S']:>3} n={row['n']:>6} kappa={row['kappa']:.4f}"
                  f" B={row['B_count']:.5f} ratio={row['ratio']:.1f}"
                  f" r={row['r']:.4f}+-{row['r_sem']:.4f}"
                  f" PR/n={row['pr']:.3f}")
    for s in seed:
        for dd in s.get("deltas", []):
            print(f"seed ctrl {s['family']} S={dd['S']}: "
                  f"kappa7={dd['kappa7']:.4f} kappa8={dd['kappa8']:.4f} "
                  f"(|dk|={dd['dk_rel']*100:.1f}%) r7={dd['r7']:.3f} "
                  f"r8={dd['r8']:.3f} stable={s['stable']}")
    print("OVERALL:", overall)
    print("saved", path)


if __name__ == "__main__":
    main()
