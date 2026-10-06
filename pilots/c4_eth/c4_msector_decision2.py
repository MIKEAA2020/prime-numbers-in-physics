#!/usr/bin/env python3
"""
Adjudication of the fixed-V d>=3 sector ladders under Amendment A1
(c4_msector_extend2.py, committed before execution of its rungs).

Applies (A1a)-(A1h): seed-mean tail statistics with interval containment
(DIVERGENT / PLATEAU / SEPARATED / THERMAL), direct crossing checks over
every rung and seed, the kappa/B ratio extrapolation, and the d5
GOE-transit closure.  The base rule's outputs (c4_msector_decision.json)
are untouched; this writes c4_msector_decision2.json.

Inputs:  c4_msector_results.json (base ladders + extension + replicates)
Output:  c4_msector_decision2.json + printed verdict table
"""
import json
import math
import os

import numpy as np
from scipy import stats

import c4_scaled_eth as base

OUT = base.OUT
R_GOE = 0.5359
GOE_HALF = 0.03
GOE_EDGE_LO = R_GOE - GOE_HALF          # 0.5059
FAMILIES = ("d3_fixed", "d4_fixed", "d5_fixed")
TAIL_SPEC = {3: 400, 4: 55, 5: 0}       # (A1a): S >= threshold (0 = all)


def wls(x, y, w):
    """Weighted least squares; returns slope, icept, se_slope, k."""
    x, y, w = map(np.asarray, (x, y, w))
    k = len(x)
    sw = w.sum()
    xb = (w * x).sum() / sw
    yb = (w * y).sum() / sw
    sxx = (w * (x - xb) ** 2).sum()
    sxy = (w * (x - xb) * (y - yb)).sum()
    slope = sxy / sxx
    icept = yb - slope * xb
    resid = y - (icept + slope * x)
    se = (math.sqrt((w * resid ** 2).sum() / (k - 2) / sxx)
          if k > 2 else None)
    return float(slope), float(icept), se, k


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    A = np.vstack([x, np.ones_like(x)]).T
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    ss = float(np.sum((y - A @ coef) ** 2))
    sxx = float(np.sum((x - x.mean()) ** 2))
    se = math.sqrt(ss / (len(x) - 2) / sxx) if len(x) > 2 else None
    return float(coef[0]), float(coef[1]), se


def t95(dof):
    return float(stats.t.ppf(0.975, dof)) if dof > 0 else 2.0


def collect(res, d):
    """Window-protocol rows for family d: {S: {seed: row}}."""
    fam = {r["S"]: {7: r} for r in res.get(f"d{d}_fixed", [])
           if r.get("kappa") is not None
           and r.get("protocol") == "median-window-k350"}
    for c in res.get("seed_controls", []):
        if c.get("d") == d and c.get("kappa") is not None \
                and c.get("protocol") == "median-window-k350":
            fam.setdefault(c["S"], {})[c.get("seed", 8)] = c
    return fam


def all_rows(res, d):
    rows = [r for r in res.get(f"d{d}_fixed", []) if r.get("kappa") is not None]
    rows += [c for c in res.get("seed_controls", [])
             if c.get("d") == d and c.get("kappa") is not None]
    return rows


def adjudicate_family(res, d):
    fam = collect(res, d)
    S_tail = sorted(S for S in fam if S >= TAIL_SPEC[d])
    if len(S_tail) < 2:
        return dict(klass="pending", side="open")
    tab = []
    for S in S_tail:
        seeds = fam[S]
        kaps = [r["kappa"] for r in seeds.values()]
        rats = [r["kappa"] / r["B_count"] for r in seeds.values()]
        rs = [r["r_mean"] for r in seeds.values()]
        entry = dict(S=int(S), n=int(next(iter(seeds.values()))["n"]),
                     m=len(seeds), kappa_bar=float(np.mean(kaps)),
                     kappa_sd=float(np.std(kaps, ddof=1)) if len(kaps) > 1 else 0.0,
                     ratio_bar=float(np.mean(rats)),
                     r_bar=float(np.mean(rs)),
                     r_sem=(float(np.std(rs, ddof=1) / math.sqrt(len(rs)))
                            if len(rs) > 1 else 0.0),
                     kappa_seeds={str(sd): float(r["kappa"])
                                  for sd, r in sorted(seeds.items())})
        tab.append(entry)
    x = [math.log(e["n"]) for e in tab]
    w = [e["m"] for e in tab]

    # (A1b) alpha: kappa ~ n^-alpha  =>  slope of ln kappa = -alpha
    s_k, i_k, se_k, kk = wls(x, [math.log(e["kappa_bar"]) for e in tab], w)
    alpha = -s_k
    # (A1b) gamma: slope of ln(kappa/B)
    s_g, i_g, se_g, _ = wls(x, [math.log(e["ratio_bar"]) for e in tab], w)
    gamma = s_g

    # (A1c) interval: wider of WLS-t and per-seed-t
    def per_seed(stat):
        slopes = {}
        for sd in sorted({sd for e in tab
                          for sd in map(int, e["kappa_seeds"])}):
            pts = [(math.log(e["n"]), e["kappa_seeds"][str(sd)])
                   for e in tab if str(sd) in e["kappa_seeds"]]
            if len(pts) >= 3:
                slopes[sd] = ols([p[0] for p in pts],
                                 [math.log(p[1]) for p in pts])[0]
        return slopes

    ps_k = per_seed(tab)
    intervals = {}
    for name, pt, se, slopes, conv in (
            ("alpha", alpha, se_k, ps_k, -1.0),
            ("gamma", gamma, se_g, None, 1.0)):
        hw_wls = (t95(kk - 2) * se) if se is not None else None
        hw_seed = None
        if slopes and len(slopes) >= 2:
            vals = np.array([conv * v for v in slopes.values()])
            m_sd = float(vals.std(ddof=1))
            hw_seed = t95(len(vals) - 1) * m_sd / math.sqrt(len(vals))
            pt = float(np.mean(vals)) if name == "alpha" else pt
            # point estimate: seed-mean slope when available (realization-
            # centered); the WLS point is also reported
        hw = max([h for h in (hw_wls, hw_seed) if h is not None])
        intervals[name] = dict(point=pt, half=hw, hw_wls=hw_wls,
                               hw_seed=hw_seed,
                               per_seed={str(k): float(conv * v)
                                         for k, v in slopes.items()}
                               if slopes else {})
        if hw is not None:
            intervals[name]["ci"] = [pt - hw, pt + hw]
    ci_a = intervals["alpha"].get("ci")
    ci_g = intervals["gamma"].get("ci")

    # (A1d) class by containment (sign convention alpha = decay exponent)
    cls, sub_ok = "unresolved", False
    if ci_a is not None:
        lo, hi = ci_a
        if hi <= -0.05:
            cls, sub_ok = "divergent", True
        elif lo >= 0.05 and hi < 0.45:
            cls, sub_ok = "separated-decay", True
        elif lo >= -0.05 and hi <= 0.05:
            cls, sub_ok = "plateau", True
        elif lo >= 0.45:
            cls, sub_ok = "thermal-rate-decay", True
    side = ("thermal" if cls == "thermal-rate-decay" else
            "obstruction" if sub_ok else "open-subclass")

    # (A1e) direct crossing rows for this family (all seeds, all rungs)
    rows = all_rows(res, d)
    cross_rows = [dict(S=int(r["S"]), seed=r.get("seed", 7),
                       kappa=float(r["kappa"]), B=float(r["B_count"]))
                  for r in rows if r["kappa"] <= r["B_count"]]
    ratio_min = min(float(r["kappa"] / r["B_count"]) for r in rows)

    # (A1f) ratio extrapolation.  The committed text branches on
    # "gamma_ci entirely < 0" vs "gamma_ci >= 0"; the second branch is the
    # complement (the CI admits non-decay).  The n* alternative of (A1h) is
    # evaluated under both readings so the verdict is reading-robust.
    #   n*(g): scale at which the fitted power law rho(n) = rho_top
    #   (n/n_hi)^g reaches 1 (only finite for g < 0).
    n_hi = tab[-1]["n"]
    rho_top = tab[-1]["ratio_bar"]
    reach = 1e6 * n_hi

    def nstar(g):
        return float("inf") if g >= 0 else n_hi * rho_top ** (1.0 / (-g))

    n_star, n_star_lo, gamma_ok, gamma_ok_strict = \
        None, None, None, None
    if ci_g is not None:
        # complement reading: CI admits gamma >= 0
        gamma_ok = ci_g[1] >= 0
        # strict reading: CI entirely non-negative
        gamma_ok_strict = ci_g[0] >= 0
        if ci_g[1] < 0:                 # entirely negative: n* interval
            n_star_lo, n_star = nstar(ci_g[0]), nstar(ci_g[1])
            ok_nstar = n_star_lo > reach
            gamma_ok = gamma_ok_strict = ok_nstar
        elif ci_g[0] < 0:               # spans zero: worst admitted decay
            n_star_lo = nstar(ci_g[0])
            n_star = float("inf")
            if n_star_lo <= reach:
                gamma_ok_strict = False   # strict reading rescued only by
                # an n* beyond the reach bound; here it is not
            else:
                gamma_ok_strict = True    # rescued by the (A1h) n* clause

    # (A1g) transit (applies to d5; reported for all)
    transit = None
    y_r = [e["r_bar"] for e in tab]
    s_r, _, se_r, kr = wls(x, y_r, w)
    top = tab[-1]
    hw_r = t95(kr - 2) * se_r if se_r is not None else None
    top_ci = [top["r_bar"] - 2.78 * top["r_sem"],
              top["r_bar"] + 2.78 * top["r_sem"]] if top["r_sem"] else None
    if d == 5 and hw_r is not None and top_ci is not None:
        r_slope_ci = [s_r - t95(kr - 2) * se_r, s_r + t95(kr - 2) * se_r]
        if r_slope_ci[1] < 0 and top_ci[1] < R_GOE:
            transit = "exit"
        elif r_slope_ci[0] <= 0 <= r_slope_ci[1] \
                and top_ci[0] >= GOE_EDGE_LO and top_ci[1] <= R_GOE + GOE_HALF:
            transit = "persistent"
        else:
            transit = "band-edge"

    return dict(klass=cls, side=side, sub_class_resolved=sub_ok,
                tail=dict(spec=f"S>={TAIL_SPEC[d]}", rungs=len(tab),
                          n_lo=int(tab[0]["n"]), n_hi=int(n_hi)),
                alpha=dict(point=alpha, wls_point=-s_k,
                           ci=ci_a, **{k: intervals["alpha"][k]
                                       for k in ("hw_wls", "hw_seed",
                                                 "per_seed")}),
                gamma=dict(point=gamma, ci=ci_g,
                           hw_wls=intervals["gamma"]["hw_wls"],
                           hw_seed=intervals["gamma"]["hw_seed"]),
                crossing_rows=cross_rows, ratio_min=ratio_min,
                n_star=(None if n_star == float("inf") else n_star),
                n_star_lo=(None if n_star_lo in (None, float("inf"))
                           else n_star_lo),
                reach_bound=float(reach),
                gamma_ok=gamma_ok, gamma_ok_strict=gamma_ok_strict,
                r_slope=float(s_r), r_slope_ci=(float(s_r - t95(kr - 2) * se_r),
                                                float(s_r + t95(kr - 2) * se_r))
                if se_r is not None else None,
                transit=transit, top_r=dict(bar=top["r_bar"],
                                            sem=top["r_sem"], ci=top_ci),
                table=tab)


def main():
    res = json.load(open(os.path.join(OUT, "c4_msector_results.json")))
    report = {f: adjudicate_family(res, int(f[1])) for f in FAMILIES}

    any_cross = any(report[f]["crossing_rows"] for f in FAMILIES)
    alpha_ok = all(
        (report[f]["alpha"].get("ci") or [0, 1e9])[1] < 0.45
        for f in FAMILIES)
    n_max = max((report[f]["tail"]["n_hi"] for f in FAMILIES
                 if report[f].get("tail")), default=1)
    gamma_ok = all(report[f]["gamma_ok"] for f in FAMILIES
                   if report[f]["gamma_ok"] is not None)
    gamma_ok_strict = all(report[f]["gamma_ok_strict"] for f in FAMILIES
                          if report[f]["gamma_ok_strict"] is not None)
    ratio_min = min(report[f]["ratio_min"] for f in FAMILIES)
    settled = (not any_cross) and alpha_ok and gamma_ok and gamma_ok_strict
    overall = ("settled: obstruction side" if settled
               else "open (see branches)")

    out = dict(amendment="A1 (c4_msector_extend2.py, committed before "
                         "execution)",
               families=report, any_crossing=any_cross,
               alpha_thermal_excluded=alpha_ok, gamma_ok=gamma_ok,
               ratio_min_all=ratio_min, overall=overall,
               settled=bool(settled))
    path = os.path.join(OUT, "c4_msector_decision2.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)

    for f in FAMILIES:
        rp = report[f]
        print(f"== {f}: {rp['klass']} ({rp['side']}; "
              f"sub-class resolved: {rp['sub_class_resolved']})")
        if rp.get("alpha", {}).get("ci"):
            a = rp["alpha"]
            print(f"   alpha = {a['point']:+.4f}  CI95 "
                  f"[{a['ci'][0]:+.4f}, {a['ci'][1]:+.4f}] "
                  f"(hw_wls={a['hw_wls']}, hw_seed={a['hw_seed']})")
            if a.get("per_seed"):
                print(f"   per-seed alpha: "
                      + " ".join(f"{k}:{v:+.3f}"
                                 for k, v in a["per_seed"].items()))
        if rp.get("gamma", {}).get("ci"):
            g = rp["gamma"]
            print(f"   gamma = {g['point']:+.4f}  CI95 "
                  f"[{g['ci'][0]:+.4f}, {g['ci'][1]:+.4f}]")
        print(f"   kappa/B min over all seeds/rungs: {rp['ratio_min']:.2f}"
              f"   crossing rows: {len(rp['crossing_rows'])}")
        if rp.get("n_star_lo"):
            print(f"   n* (worst admitted decay): {rp['n_star_lo']:.2e} "
                  f"(reach bound {rp['reach_bound']:.2e})")
        if rp.get("transit"):
            print(f"   <r> slope {rp['r_slope']:+.4f} "
                  f"CI {['%.4f' % v for v in rp['r_slope_ci']]}; "
                  f"top-rung <r>bar = {rp['top_r']['bar']:.4f} "
                  f"+- {rp['top_r']['sem']:.4f} -> transit: "
                  f"{rp['transit']}")
        for e in rp.get("table", []):
            print(f"   S={e['S']:>3} n={e['n']:>6} m={e['m']} "
                  f"kappa_bar={e['kappa_bar']:.4f}"
                  f"+-{e['kappa_sd']:.4f} ratio_bar={e['ratio_bar']:.1f} "
                  f"r_bar={e['r_bar']:.4f}")
    print(f"OVERALL: {overall} (any_crossing={any_cross}, "
          f"alpha_ok={alpha_ok}, gamma_ok={gamma_ok}, "
          f"gamma_ok_strict={gamma_ok_strict}, "
          f"ratio_min={ratio_min:.2f})")
    print("saved", path)


if __name__ == "__main__":
    main()
