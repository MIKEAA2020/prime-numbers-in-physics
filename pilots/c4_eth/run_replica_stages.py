#!/usr/bin/env python3
"""Staged driver for the replica-bound run (foreground chunks, partial JSON
as the resumable state).  Usage: python3 run_replica_stages.py <stage>."""
import json
import os
import sys
import time

import numpy as np

import c4_msector_jacobi as mj
import c4_msector_replica as mr

OUT = mr.OUT
STATE = os.path.join(OUT, "c4_msector_replica.json")


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {}


def save(out):
    with open(STATE, "w") as f:
        json.dump(out, f, indent=1)
    print("saved", STATE, flush=True)


def stage_platforms(rungs):
    out = load()
    out.setdefault("platforms", {})
    for (d, S) in rungs:
        key = f"d{d}_S{S}"
        if key in out["platforms"]:
            print("skip", key, flush=True)
            continue
        res, ex = mr.run_platform(d=d, S=S, V=0.3,
                                  m_op=(S <= 60 or d == 4))
        out["platforms"][key] = res
        save(out)


def stage_insertion():
    out = load()
    if "insertion_validation" in out:
        return
    H, eps, comp, hmat = mj.sector_block(3, 60, 1.0, 0.0, 0.3, 7)
    layer = (60 - comp[:, 0]).astype(int)
    Hd = H.toarray()
    out["insertion_validation"] = mr.validate_insertion(H, Hd, layer, 60)
    iv = {k: (v.get("rel", v) if isinstance(v, dict) else v)
          for k, v in out["insertion_validation"].items()}
    print("insertion:", {k: (('%.1e' % v) if isinstance(v, float) else v)
                         for k, v in iv.items()}, flush=True)
    save(out)


def stage_propagation(r_tag, budget=520.0):
    out = load()
    prop = out.get("propagation_d3_S60", {})
    vals = prop.get("G_M_values", [])
    want = int(r_tag)
    if len(vals) >= want:
        print("skip propagation resample", r_tag, flush=True)
        return
    # rebuild the d3 S=60 platform (cheap) for the exact cross-checks
    res, ex = mr.run_platform(d=3, S=60, V=0.3, m_op=False)
    cen = res["census"]
    gv = cen["grid"]["0.1"]["g"]
    T_prop = 30.0 / gv
    ck = os.path.join(OUT, f"krs_replica_prop_r{want}.npz")
    run = mr.propagate_fejer(ex["H"], ex["KW"], ex["Wb"],
                             float(ex["w"][0]), float(ex["w"][ -1]),
                             T_prop, s=16, seed=11 + 1000 * (want - 1),
                             t_budget=budget, dt_limit=cen["dt_prop"],
                             ckpt=ck)
    if not run["complete"]:
        print(f"  incomplete ({run['n_done']}/{run['M']}); re-run the stage "
              f"to resume from the checkpoint", flush=True)
        return
    vals.append(run["G_M"])
    prop.update(G_M_values=[float(v) for v in vals],
                G_M_mean=float(np.mean(vals)),
                G_M_spread=float(np.std(vals)),
                detail=run, delta=0.1, c_T=30.0, g_ref=gv, T=T_prop)
    out["propagation_d3_S60"] = prop
    save(out)


def stage_budget():
    out = load()
    prop = out["propagation_d3_S60"]
    # exact cross-checks from the rebuilt platform
    res, ex = mr.run_platform(d=3, S=60, V=0.3, m_op=False)
    cen = res["census"]
    s60 = res
    T_prop = prop["T"]
    det = prop["detail"]
    ATn = float(mr.exact_fejer(ex["KW"], ex["dlt"], T_prop)[1])
    GM_disc = float((ex["KW"] ** 2 * mr.fejer_disc(
        ex["dlt"], det["M"], det["dt"])).sum() / det["M"])
    fh = cen["fold_hist"]
    tail = float(sum(mm * min(1.0, np.pi ** 2 / (T_prop ** 2 * dd ** 2))
                     for dd, mm in zip(fh["d_centers"], fh["masses"]))) \
        + fh["below_floor"]
    loop = s60["identities"]["loop"]
    prop.update(exact_AT_over_T=ATn, exact_G_M_disc=GM_disc,
                hutch_ci95=2.0 * prop["G_M_spread"],
                tail_bound_disc=tail,
                lb=prop["G_M_mean"] - 2.0 * prop["G_M_spread"] - tail,
                loop_exact=loop)
    prop["lb_rel"] = prop["lb"] / loop
    out["propagation_d3_S60"] = prop
    print(f"propagation budget: G_M {prop['G_M_mean']:.1f} "
          f"+- {prop['G_M_spread']:.1f} vs exact disc {GM_disc:.1f} "
          f"(cont {ATn:.1f}); tail {tail:.1f}; lb_rel "
          f"{prop['lb_rel']:.4f} (complete {det['complete']}, "
          f"wall {det['wall_s']:.0f}s)", flush=True)
    save(out)


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "p1":
        stage_platforms([(3, 40), (3, 60), (4, 16)])
    elif stage == "p2":
        stage_platforms([(3, 80), (3, 100)])
    elif stage == "p3":
        stage_platforms([(3, 116)])
    elif stage == "ins":
        stage_insertion()
    elif stage.startswith("prop"):
        stage_propagation(stage[-1], budget=500.0)
    elif stage == "budget":
        stage_budget()
    else:
        raise SystemExit(f"unknown stage {stage}")
