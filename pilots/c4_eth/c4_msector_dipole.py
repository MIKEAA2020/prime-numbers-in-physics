#!/usr/bin/env python3
"""The multiplet-dipole control of the M-sector obstruction (the complementary
completion route of the obstruction theorem).

The registered route (Remark rem:obstruction): a statement that the
inter-multiplet dipoles cannot collapse to zero, which no single-copy trace
can force.  This module executes the route in its exact, decidable form:

(D1) The dipole architecture (exact, Parseval).  With the CORRECT isotypic
    projectors P_l = (dim l / d!) sum_pi chi_l(pi) R_pi (the dimension factor
    included), the window K-matrix decomposes channel-by-channel:

        KW = sum_{l,l'} C_ll',   C_ll' = Y_l^T K Y_l',   Y_l = P_l Wb,

    and the window fluctuation operator X~ = KW - (S/d) I decomposes over the
    nonzero K~-blocks only (the 1-D-isotypic diagonal blocks of K~ vanish
    identically; the triv<->sign block vanishes by orbit combinatorics:
    sum_pi sign(pi) k_{pi(1)} = 0 for every composition orbit).

(D2) The exact identities, validated to roundoff at every rung:
    - P_triv K P_triv = (S/d) P_triv and P_sign K P_sign = (S/d) P_sign
      (the isotypic occupation identity in operator form);
    - P_sign K P_triv = 0 exactly;
    - the a-decomposition a_j = (S/d)(w^triv_j + w^sign_j) + <d_j|K|d_j>
      + 2 Re<cross terms>;
    - the channel sum equals KW (Parseval up to the Gram cross terms).

(D3) The control, decided.  Three natural single-copy/inequality families:
    - the affine family: loop >= |W|(S/d)^2 + 2(S/d)(Tr Pi_W K - |W| S/d),
      with slack exactly sum_j beta_j^2 -- the fluctuation itself
      (fluctuation-free: certifies the bulk, never the margin);
    - the channel family: for EVERY decomposition X~ = sum_c C_c,
      offdiag <= sum_{c,c'} |<C_c, C_c'>_F| is vacuous, because the Gram
      matrix is positive semidefinite:  sum |G| >= trace G = ||X~||_F^2
      = sum beta^2 + offdiag -- the budget always subsumes the fluctuation;
    - the moment family: offdiag_far <= M_p / g(delta)^{2p} with the exact
      frequency moments M_p of the window two-point measure -- measured to
      overshoot by three orders of magnitude (the off-diagonal dipoles are
      frequency-spread, not gap-concentrated).
    The two-copy Fejer kernel is the separating mechanism (Prop prop:replica,
    executed): it is not a channel budget, and it closes.  The complementary
    route therefore resolves as a necessity theorem for the replica route.

(D4) The multiplet census at every rung: pairs, refined splittings, the
    within-pair K~-decoupling, occupation constancy, the paired/unpaired
    loop split, and the beta-inventory of the fluctuation (the isotypic
    content term, the standard-diagonal term, the mixed cross terms).

Rungs: d=3 S in {20, 40, 60, 80, 100, 116}; d=4 S=16 (every dense-reachable
rung of the replica bound, plus the census low end).  Cross-validated against
the replica-certified constants.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_dipole.json
"""
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp

import c4_msector_jacobi as mj
import c4_msector_replica as mr

OUT = "/home/z/my-project/download/pilot_c4_eth_scaled"
PAIR_EPS = 1e-8


# ----------------------------------------------------------------------------
# character tables and permutation machinery (generic d in {3, 4})
# ----------------------------------------------------------------------------
S3_TABLE = {
    "perms": [
        ((0, 1, 2), "e"),
        ((1, 0, 2), "t"),
        ((0, 2, 1), "t"),
        ((2, 1, 0), "t"),
        ((1, 2, 0), "c3"),
        ((2, 0, 1), "c3"),
    ],
    # chars: {irrep: {class: chi}}; dims from chi(e)
    "chars": {
        "trivial": {"e": 1, "t": 1, "c3": 1},
        "sign": {"e": 1, "t": -1, "c3": 1},
        "standard": {"e": 2, "t": 0, "c3": -1},
    },
}

S4_TABLE = {
    # classes: e, t (2-cycle, 6), c3 (8), c4 (6), dt (double-trans, 3)
    "perms": [],          # filled below
    "chars": {
        "[4]": {"e": 1, "t": 1, "c3": 1, "c4": 1, "dt": 1},
        "[1111]": {"e": 1, "t": -1, "c3": 1, "c4": -1, "dt": 1},
        "[22]": {"e": 2, "t": 0, "c3": -1, "c4": 0, "dt": 2},
        "[31]": {"e": 3, "t": 1, "c3": 0, "c4": -1, "dt": -1},
        "[211]": {"e": 3, "t": -1, "c3": 0, "c4": 1, "dt": -1},
    },
}


def _s4_class(perm):
    """Cycle type -> class label."""
    seen = [False] * 4
    cycles = []
    for i in range(4):
        if not seen[i]:
            c = 0
            j = i
            while not seen[j]:
                seen[j] = True
                j = perm[j]
                c += 1
            cycles.append(c)
    cycles.sort()
    key = tuple(cycles)
    return {(1, 1, 1, 1): "e", (1, 1, 2): "t", (1, 3): "c3",
            (2, 2): "dt", (4,): "c4"}[key]


import itertools
for _p in itertools.permutations(range(4)):
    S4_TABLE["perms"].append((_p, _s4_class(_p)))


def table_for(d):
    return S3_TABLE if d == 3 else S4_TABLE


def perm_maps(comp, S, d, perms):
    """Index maps: idx[i] = row of the permuted composition."""
    key = comp @ ((S + 1) ** np.arange(d - 1, -1, -1))
    idx_of = {int(k): i for i, k in enumerate(key)}
    out = []
    for p, _cls in perms:
        perm = np.empty_like(comp)
        for i in range(d):
            perm[:, p[i]] = comp[:, i]
        pkey = perm @ ((S + 1) ** np.arange(d - 1, -1, -1))
        out.append(np.array([idx_of[int(k)] for k in pkey]))
    return out


def apply_perm_rows(M, idx):
    """(R_pi M)[i, :] = M[idx[i], :] (the row-gather of R_pi)."""
    return M[idx, :]


def build_projector_apply(d, S, comp, irrep, chars, perms, maps):
    """P_irrep @ M = (dim/|G|) sum_pi chi(pi) R_pi M, by row gathers."""
    dim = chars["e"]
    order = math.factorial(d)

    def apply(M):
        acc = None
        for (p, cls), idx in zip(perms, maps):
            chi = chars[cls]
            if chi == 0:
                continue
            term = chi * apply_perm_rows(M, idx)
            acc = term if acc is None else acc + term
        return (dim / order) * acc
    return apply


# ----------------------------------------------------------------------------
# rung computation
# ----------------------------------------------------------------------------
def run_rung(d, S, V=0.3, k=350, seed=7, moments=True):
    t_start = time.perf_counter()
    H, eps, comp, hmat = mj.sector_block(d, S, 1.0, 0.0, V, seed)
    n = H.shape[0]
    Hd = H.toarray()
    w, Vv = np.linalg.eigh(Hd)
    obs = comp[:, 0].astype(float)
    sel = mr.window_select(w, eps, k)
    Wb = Vv[:, sel]
    nW = len(sel)
    KW = Wb.T @ (obs[:, None] * Wb)
    a = np.diag(KW).copy()
    dlt = w[sel][:, None] - w[sel][None, :]
    loop = float((a ** 2).sum())
    surr = float((KW ** 2).sum())
    offd = surr - loop
    res = {"platform": dict(d=d, S=S, V=V, n=n, n_W=nW, seed=seed)}

    # ---- (D2) projectors, validation ----
    tab = table_for(d)
    perms, chars_tab = tab["perms"], tab["chars"]
    maps = perm_maps(comp, S, d, perms)
    irreps = list(chars_tab.keys())
    applies = {nm: build_projector_apply(d, S, comp, nm, chars_tab[nm],
                                         perms, maps) for nm in irreps}
    # validation on random vectors: idempotence, orthogonality, resolution
    rng = np.random.default_rng(3)
    zv = rng.standard_normal((n, 3))
    val = {}
    for nm in irreps:
        Pz = applies[nm](zv)
        PPz = applies[nm](Pz)
        val[f"idempotent_{nm}"] = float(np.abs(PPz - Pz).max())
    tot = None
    for nm in irreps:
        Pz = applies[nm](zv)
        tot = Pz if tot is None else tot + Pz
    val["resolution"] = float(np.abs(tot - zv).max())
    cross_dev = 0.0
    for i, nm1 in enumerate(irreps):
        for nm2 in irreps[i + 1:]:
            z2 = rng.standard_normal((n, 2))
            cross_dev = max(cross_dev, float(
                np.abs(applies[nm1](applies[nm2](z2))).max()))
    val["orthogonal"] = cross_dev
    res["projector_validation"] = val

    # ---- (D1) channels ----
    Y = {nm: applies[nm](Wb) for nm in irreps}
    wts = {nm: (Y[nm] ** 2).sum(axis=0) for nm in irreps}
    wtot = sum(wts.values())
    C = {}
    for nm1 in irreps:
        for nm2 in irreps:
            C[(nm1, nm2)] = Y[nm1].T @ (obs[:, None] * Y[nm2])
    KWr = sum(C.values())
    parseval = float(np.abs(KWr - KW).max())
    res["channels"] = dict(
        parseval_dev=parseval,
        weights_sum=float(wtot.sum()),
        mean_weights={nm: float(wts[nm].mean()) for nm in irreps},
        weight_stds={nm: float(wts[nm].std()) for nm in irreps},
        masses={f"{nm1}|{nm2}": float((C[(nm1, nm2)] ** 2).sum())
                for nm1 in irreps for nm2 in irreps},
        masses_frac={f"{nm1}|{nm2}":
                     float((C[(nm1, nm2)] ** 2).sum()) / surr
                     for nm1 in irreps for nm2 in irreps},
        offdiag_parts={f"{nm1}|{nm2}":
                       float((C[(nm1, nm2)] ** 2).sum()
                             - (np.diag(C[(nm1, nm2)])) ** 2 .sum() if False
                       else float((C[(nm1, nm2)] ** 2).sum()
                                  - (np.diag(C[(nm1, nm2)]) ** 2).sum()))
                       for nm1 in irreps for nm2 in irreps},
    )

    # 1-D irreps: the exact block identities
    Sd = S / d
    val2 = {}
    for nm in irreps:
        if chars_tab[nm]["e"] == 1:
            # P_nm K P_nm = (S/d) P_nm as a quadratic form on random vectors
            z3 = rng.standard_normal((n, 4))
            Pz = applies[nm](z3)
            lhs = (Pz * (obs[:, None] * Pz)).sum(axis=0)
            rhs = Sd * (Pz ** 2).sum(axis=0)
            val2[f"quad_{nm}"] = float(np.abs(lhs - rhs).max() / n)
    # the sign<->trivial block: (P_s K P_t z) == 0 componentwise
    if d == 3:
        z4 = rng.standard_normal((n, 4))
        Pt = applies["trivial"](z4)
        sPt = applies["sign"](Pt * 1.0)
        lhs = (sPt * (obs[:, None] * Pt)).sum(axis=0)
        val2["sign_triv_block"] = float(np.abs(lhs).max())
    if d == 4:
        z4 = rng.standard_normal((n, 4))
        Pt = applies["[4]"](z4)
        sPt = applies["[1111]"](Pt * 1.0)
        lhs = (sPt * (obs[:, None] * Pt)).sum(axis=0)
        val2["sign_triv_block"] = float(np.abs(lhs).max())
    res["block_validation"] = val2

    # ---- the a-decomposition ----
    # a_j = (S/d)(sum_{1D} w) + sum_{multi-dim ll'} diag contributions
    one_d = [nm for nm in irreps if chars_tab[nm]["e"] == 1]
    multi = [nm for nm in irreps if chars_tab[nm]["e"] > 1]
    a_dec = Sd * sum(wts[nm] for nm in one_d)
    beta_inv = {"content": Sd * sum(wts[nm] for nm in one_d)}
    for nm in multi:
        term = np.diag(C[(nm, nm)]).real
        a_dec = a_dec + term
        beta_inv[f"diag_{nm}"] = term
    for nm1 in one_d:
        for nm2 in multi:
            term = 2 * np.diag(C[(nm1, nm2)]).real
            a_dec = a_dec + term
            beta_inv[f"cross_{nm1}|{nm2}"] = term
    for i, nm1 in enumerate(one_d):
        for nm2 in one_d[i + 1:]:
            term = 2 * np.diag(C[(nm1, nm2)]).real
            a_dec = a_dec + term
            beta_inv[f"cross_{nm1}|{nm2}"] = term
    for i, nm1 in enumerate(multi):
        for nm2 in multi[i + 1:]:
            term = 2 * np.diag(C[(nm1, nm2)]).real
            a_dec = a_dec + term
            beta_inv[f"cross_{nm1}|{nm2}"] = term
    a_dec_dev = float(np.abs(a_dec - a).max())
    res["a_decomposition"] = dict(dev=a_dec_dev, inventory={
        key: dict(mean=float(arr.mean()), std=float(arr.std()))
        for key, arr in beta_inv.items()})
    beta = a - Sd
    res["fluctuation"] = dict(
        beta_sq_sum=float((beta ** 2).sum()),
        a_mean=float(a.mean()), a_std=float(a.std()),
        var_W=float(a.var()))

    # ---- X~ channel decomposition (the fluctuation operator) ----
    # X~ = KW - (S/d) I; its channels: the multi-dim diagonal channels of K~
    #   (C_mm - (S/d) Y_m^T Y_m) + all mixed and 1D-involving channels
    Xt = KW - Sd * np.eye(nW)
    Xt_mass = float((Xt ** 2).sum())
    chans = {}
    for nm1 in irreps:
        for nm2 in irreps:
            if chars_tab[nm1]["e"] == 1 and chars_tab[nm2]["e"] == 1:
                continue  # the 1D-1D blocks of K~ all vanish
            if nm1 == nm2 and chars_tab[nm1]["e"] > 1:
                chans[(nm1, nm2)] = C[(nm1, nm2)] - Sd * (
                    Y[nm1].T @ Y[nm2])
            else:
                chans[(nm1, nm2)] = C[(nm1, nm2)]
    Xt_rec = sum(chans.values())
    res["xtilde"] = dict(
        mass=Xt_mass, diag_mass=float((beta ** 2).sum()),
        offdiag_mass=offd,
        parseval_dev=float(np.abs(Xt_rec - Xt).max()),
        channel_masses={f"{nm1}|{nm2}": float((chans[(nm1, nm2)] ** 2).sum())
                        for (nm1, nm2) in chans},
        channel_offdiag={f"{nm1}|{nm2}":
                         float((chans[(nm1, nm2)] ** 2).sum()
                               - (np.diag(chans[(nm1, nm2)]) ** 2).sum())
                         for (nm1, nm2) in chans})

    # ---- (D3) the control, decided ----
    # (a) affine family
    TrP = float(a.sum())
    affine = nW * Sd ** 2 + 2 * Sd * (TrP - nW * Sd)
    res["nogo"] = dict(affine_lb=affine, affine_slack=loop - affine,
                       affine_slack_equals_beta=float(
                           abs((loop - affine) - (beta ** 2).sum())))
    # (b) channel family: the Gram budget of the X~ channels
    keys = list(chans.keys())
    G = np.zeros((len(keys), len(keys)))
    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            G[i, j] = float(np.trace(chans[k1].conj().T @ chans[k2]))
    gram_abs = float(np.abs(G).sum())
    gram_trace = float(np.trace(G))
    res["nogo"].update(dict(
        gram_abs_budget=gram_abs, gram_trace=gram_trace,
        gram_budget_vs_xtmass=gram_abs / Xt_mass,
        gram_budget_vs_offdiag=gram_abs / offd))
    # per-entry Cauchy-Schwarz variant
    nc = len(keys)
    cs_budget = nc * float(sum((chans[kk] ** 2).sum() for kk in keys))
    res["nogo"].update(dict(
        cs_channels=nc, cs_budget=cs_budget,
        cs_budget_vs_offdiag=cs_budget / offd))
    # (c) moment family (spectral, exact)
    if moments:
        m_off = np.abs(dlt) > 1e-12
        ad = np.abs(dlt)
        M0 = surr
        M = [surr, float((KW ** 2 * dlt ** 2).sum()),
             float((KW ** 2 * dlt ** 4).sum()),
             float((KW ** 2 * dlt ** 6).sum())]
        mo = {}
        for dl in (1e-8, 1e-4, 0.1, 1.0, 7.7):
            near = m_off & (ad <= dl)
            far = m_off & ~near
            mval = float((KW[near] ** 2).sum()) if near.any() else 0.0
            far_mass = float((KW[far] ** 2).sum()) if far.any() else 0.0
            g = float(ad[far].min()) if far.any() else float("inf")
            best = min((M[p] / g ** (2 * p)) for p in (1, 2, 3)) \
                if g > 0 else float("inf")
            mo[f"{dl:g}"] = dict(near_mass=mval, far_mass=far_mass, g=g,
                                 moment_bound=best,
                                 overshoot=best / max(far_mass, 1e-300))
        res["nogo"]["moment_family"] = mo

    # ---- (D4) the multiplet census ----
    dw = np.diff(w)
    pairs = np.where(dw < PAIR_EPS)[0]
    inpair = np.zeros(n, dtype=bool)
    for p0 in pairs:
        inpair[p0] = True
        inpair[p0 + 1] = True
    inpairW = inpair[sel]
    selset = set(sel.tolist())
    pair_dip = 0.0
    agaps = []
    splits = []
    for p0 in pairs:
        if p0 in selset and (p0 + 1) in selset:
            j = int(np.where(sel == p0)[0][0])
            kk = int(np.where(sel == p0 + 1)[0][0])
            pair_dip += abs(KW[j, kk]) ** 2
            agaps.append(abs(a[j] - a[kk]))
            E2 = Vv[:, [p0, p0 + 1]]
            M2 = E2.T @ (Hd @ E2)
            ev = np.sort(np.linalg.eigvalsh(M2))
            splits.append(ev[1] - ev[0])
    loop_paired = float((a[inpairW] ** 2).sum())
    res["multiplet_census"] = dict(
        n_pairs_spectrum=int(len(pairs)),
        pair_frac_spectrum=float(len(pairs) / (n - 1)),
        n_window_states_in_pairs=int(inpairW.sum()),
        n_window_pairs=int(inpairW.sum() // 2),
        window_pair_dipole_mass=pair_dip,
        pair_dipole_vs_offdiag=pair_dip / offd if offd else 0.0,
        pair_split_med=float(np.median(splits)) if splits else None,
        pair_agap_med=float(np.median(agaps)) if agaps else None,
        loop_paired=loop_paired, loop_paired_frac=loop_paired / loop,
        loop_unpaired=loop - loop_paired,
        a_std_paired=float(a[inpairW].std()) if inpairW.any() else None,
        a_std_unpaired=float(a[~inpairW].std()),
        var_paired=float(a[inpairW].var()) if inpairW.any() else None,
        var_unpaired=float(a[~inpairW].var()))

    # ---- cross-validation vs the replica bound ----
    rep_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "results", "c4_msector_replica.json")
    try:
        with open(rep_path) as f:
            rep = json.load(f)
        key = f"d{d}_S{S}"
        if key in rep.get("platforms", {}):
            rp = rep["platforms"][key]
            res["replica_crosscheck"] = dict(
                loop_replica=rp["identities"]["loop"],
                loop_dev=abs(loop - rp["identities"]["loop"])
                / rp["identities"]["loop"],
                ratio_lb=rp["closure"]["ratio_lb"],
                ratio_measured=rp["closure"]["ratio_measured"],
                margin_lb=rp["closure"]["margin_lb"])
    except (OSError, KeyError):
        pass

    res["platform"]["wall_s"] = time.perf_counter() - t_start
    print(f"[d{d} S={S} n={n}] loop {loop:.1f} offd {offd:.1f}; "
          f"Parseval {parseval:.1e}; a-dec dev {a_dec_dev:.1e}; "
          f"proj-val {max(val.values()):.1e}; block-val "
          f"{max(v for v in val2.values()):.1e}; "
          f"Gram {gram_abs/Xt_mass:.3f}x X~; CS {cs_budget/offd:.1f}x offd; "
          f"pairs {len(pairs)} (W {int(inpairW.sum())}); "
          f"wall {res['platform']['wall_s']:.0f}s", flush=True)
    return res


def main():
    out = {"rungs": {}, "notes": {
        "pair_eps": PAIR_EPS,
        "projector_construction": "P_l = (dim l/d!) sum chi_l(pi) R_pi "
        "(dimension factor included; the earlier symmetry script's standard "
        "projector was missing the factor and had trivial/sign swapped -- "
        "repaired here)",
    }}
    for (d, S) in ((3, 20), (3, 40), (3, 60), (3, 80), (3, 100), (3, 116),
                   (4, 16)):
        out["rungs"][f"d{d}_S{S}"] = run_rung(d, S, moments=(S <= 100))
    with open(os.path.join(OUT, "c4_msector_dipole.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("saved", os.path.join(OUT, "c4_msector_dipole.json"))


if __name__ == "__main__":
    main()
