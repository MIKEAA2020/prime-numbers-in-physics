#!/usr/bin/env python3
"""Two-copy replica bound for the M-sector obstruction (the within-bin loop).

The obstruction theorem of the register (kappa/B_count >= c_d along the
fixed-V ladders) reduces to the profile-margin statement, whose missing step
is the within-bin loop

    loop = sum_{j in W} a_j^2 = Tr[Pit~_W (K (x) K)]

-- the pinching (two-copy) object that no single-copy trace reaches.  This
module executes the replica route.

(R1) Replica identities (exact, real-symmetric sector block H, nondegenerate
    window W, K the mode-1 occupation, X = 1_W K 1_W):
    mu = sum_{j,k in W} |X_jk|^2 delta_{E_k - E_j}   (two-point measure),
    loop = mu({0}) = Tr[Pit~_W (K (x) K)],
    A_T := sum_{j,k in W} |X_jk|^2 F_T(E_k - E_j)
         = int_0^T (1 - t/T) Tr[X e^{iHt} X e^{-iHt}] dt,
    F_T(d) = (1/T) (sin(Td/2)/(d/2))^2 >= 0,  F_T(0) = T  (Fejer kernel).
    A_T/T -> loop + P as T -> inf (the pair mass P survives at every finite
    T; the far off-diagonal decays).  Pit~_W is the long-time average of the
    twist-SWAP e^{i(H(x)I - I(x)H)t} SWAP restricted to the window: the
    dephased twist-SWAP is the commutant projector, and the Fejer family is
    its positive-kernel approximation.  The difference moments
    M_p = int d^{2p} dmu(d) = ||(ad_H)^p X||^2_HS are single-copy traces
    (layer-graded insertion recursions, validated here).

(R2) The replica sandwich.  With the pair threshold delta_c, the pair mass
    P = sum_{0<|E_j-E_k|<=delta_c} |X_jk|^2, the frequency floor
    g = min{|E_j-E_k| : |E_j-E_k| > delta_c}, and M_0 = Tr[X^2]:

        A_T/T - P - 4 M_0/(T^2 g^2)  <=  loop  <=  A_T/T

    (continuous kernel; the discrete-kernel implementation carries the
    constant pi^2 in place of 4 and the aliasing control dt <= pi/(2 width)).
    The pair mass is censused and capped: |X_jk|^2 <= v_j (the intra-eigenstate
    quantum variance of either partner, v_j = sum_{m != j} |<psi_m|K|psi_j>|^2).

(R3) Execution tiers: (a) dense validation platforms (d3 S=60, S=100; d4
    S=16): the identity chain, the pair/frequency census, the exact Fejer
    family, the closure read against the profile margin and kappa/B_count;
    (b) the insertion recursion Tr[H^m1 A H^m2 B] exactly (sparse or
    layer-diagonal insertions), validated against dense operators;
    (c) the eigensolver-free tier: the discrete-Fejer time-correlator by
    stepwise Chebyshev propagation with bipartite Hutchinson estimation
    (probe stacks: backward family of w, forward family of Xv; the estimator
    (v^T e^{-iHt} w)(w^T X e^{iHt} X v) is unbiased for the correlator),
    with the error budget.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           c4_msector_replica.json
"""
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp
from scipy.special import jv

import c4_msector_jacobi as mj

OUT = "/home/z/my-project/download/pilot_c4_eth_scaled"
DELTA_C = 1e-8                      # pair threshold (committed convention)
CT_FAMILY = (10.0, 20.0, 30.0)      # pre-registered T = c_T / g family


# ----------------------------------------------------------------------------
# window, two-point measure, Fejer kernel, census
# ----------------------------------------------------------------------------
def window_select(w, eps, k=350):
    """Committed window: the k eigenvalues closest to the eps median."""
    med = float(np.median(eps))
    return np.sort(np.argsort(np.abs(w - med))[:k])


def two_point(w, V, sel, obs):
    """Window K-matrix, its diagonal, and the difference matrix."""
    Wb = V[:, sel]
    KW = Wb.T @ (obs[:, None] * Wb)
    a = np.diag(KW).copy()
    dlt = w[sel][:, None] - w[sel][None, :]
    return KW, a, dlt


def fejer_T(d, T):
    """F_T(d) = (1/T)(sin(Td/2)/(d/2))^2 with F_T(0) = T, vectorized."""
    x = 0.5 * T * np.asarray(d, dtype=float)
    out = np.full_like(x, T, dtype=float)
    nz = np.abs(x) > 1e-12
    out[nz] = T * (np.sin(x[nz]) / x[nz]) ** 2
    return out


def census(KW, dlt, V, sel, obs, delta_c=DELTA_C,
           delta_grid=(1e-8, 1e-4, 0.1, 1.0)):
    """Pair mass, frequency census at the threshold grid, quantum-variance
    caps.  m(delta) = the off-diagonal mass at 0 < |d| <= delta; g(delta) =
    the minimum frequency above delta; the a priori cap m(delta) <=
    sum_j n_j(delta) v_j (n_j = partners within delta, v_j the intra-state
    quantum variance of either partner)."""
    m = np.abs(dlt) > 1e-12                       # off-diagonal
    ad = np.abs(dlt)
    near = m & (ad <= delta_c)
    far = m & ~near
    P = float((KW[near] ** 2).sum()) if near.any() else 0.0
    g0 = float(ad[far].min()) if far.any() else float("inf")
    a = np.diag(KW)
    K2 = (V[:, sel] ** 2).T @ (obs ** 2)          # <K^2>_j over the spectrum
    v = K2 - a ** 2                               # intra-state variance
    grid = {}
    for dl in delta_grid:
        msk = m & (ad <= dl)
        mval = float((KW[msk] ** 2).sum()) if msk.any() else 0.0
        ab = m & (ad > dl)
        gv = float(ad[ab].min()) if ab.any() else float("inf")
        n_j = (msk).sum(axis=1)
        cap = float((n_j * v).sum())
        grid[f"{dl:g}"] = dict(m=mval, g=gv, cap=cap)
    # frequency histogram of the off-diagonal mass (the gap census)
    edges = (0.0, 1e-8, 1e-4, 0.1, 1.0, 10.0, float("inf"))
    hist = []
    for e0, e1 in zip(edges[:-1], edges[1:]):
        msk = m & (ad > e0) & (ad <= e1)
        hist.append(float((KW[msk] ** 2).sum()) if msk.any() else 0.0)
    # aliasing census at the propagation step dt: the folded distance
    # d(D) = min_k |D - 2 pi k / dt|; the mass-weighted folded histogram
    # (64 log-bins over [1e-6, pi/dt]) drives the sharp discrete tail.
    dt_prop = 0.1
    per = 2.0 * math.pi / dt_prop
    d_fold = np.abs(((ad[m] + per / 2) % per) - per / 2)
    m_fold = (KW[m] ** 2).ravel()
    edges_f = np.logspace(-6, math.log10(math.pi / dt_prop), 65)
    hh, _ = np.histogram(d_fold, bins=edges_f, weights=m_fold)
    dc = 0.5 * (edges_f[:-1] + edges_f[1:])
    zero_mass = float(m_fold[d_fold < edges_f[0]].sum())
    fold_hist = dict(d_centers=[float(x) for x in dc],
                     masses=[float(x) for x in hh],
                     below_floor=zero_mass)
    wts = (KW[far] ** 2).ravel() if far.any() else np.array([0.0])
    frq = ad[far].ravel() if far.any() else np.array([1.0])
    order = np.argsort(frq)
    cw = np.cumsum(wts[order]) / max(wts.sum(), 1e-300)
    dec = [float(frq[order][np.searchsorted(cw, q)]) for q in
           (0.1, 0.5, 0.9)] if far.any() else [float("inf")] * 3
    return dict(P=P, g=g0, n_pairs=int(near.sum() // 2),
                v_cap=grid[f"{delta_c:g}"]["cap"],
                v_mean=float(v.mean()), far_mass=float(wts.sum()),
                far_deciles=dec, n_far=int(far.sum()),
                grid=grid, freq_hist=hist,
                hist_edges=[float(e) for e in edges],
                dt_prop=dt_prop, fold_hist=fold_hist)


def exact_fejer(KW, dlt, T):
    """A_T (continuous kernel) and A_T/T."""
    AT = float((KW ** 2 * fejer_T(dlt, T)).sum())
    return AT, AT / T


# ----------------------------------------------------------------------------
# dense validation platform
# ----------------------------------------------------------------------------
def run_platform(d=3, S=60, V=0.3, k=350, m_op=True):
    t_start = time.perf_counter()
    H, eps, comp, hmat = mj.sector_block(d, S, 1.0, 0.0, V, 7)
    n = H.shape[0]
    Hd = H.toarray()
    w, Vv = np.linalg.eigh(Hd)
    obs = comp[:, 0].astype(float)
    sel = window_select(w, eps, k)
    KW, a, dlt = two_point(w, Vv, sel, obs)
    n_W = len(sel)
    Wb = Vv[:, sel]
    X = Wb @ KW @ Wb.T                    # 1_W K 1_W as a dense operator
    res = {"platform": dict(d=d, S=S, V=V, U=0.0, n=n, k=k, n_W=n_W)}

    # ---- (R1) identities ----
    loop = float((a ** 2).sum())
    surrogate = float((KW ** 2).sum())
    d2 = dlt ** 2
    M_spec = [surrogate, float((KW ** 2 * d2).sum()),
              float((KW ** 2 * d2 ** 2).sum())]
    res["identities"] = dict(
        loop=loop, surrogate=surrogate,
        offdiag_fraction=(surrogate - loop) / surrogate,
        M_spectral=M_spec, time_avg=None)
    if m_op:
        A1 = H @ X - X @ H
        A2 = H @ A1 - A1 @ H
        M_op = [float((X ** 2).sum()), float((A1 ** 2).sum()),
                float((A2 ** 2).sum())]
        res["identities"]["M_operator"] = M_op
        res["identities"]["M_dev"] = [abs(x - y) / max(1.0, abs(x))
                                      for x, y in zip(M_spec, M_op)]
        del A1, A2

    # ---- (R2) census ----
    cen = census(KW, dlt, Vv, sel, obs)
    res["census"] = cen
    res["window"] = dict(wlo=float(w[sel][0]), whi=float(w[sel][-1]),
                         width=float(w[sel][-1] - w[sel][0]))

    # ---- the Fejer sandwich on the pre-registered (delta, c_T) grid ----
    fam = []
    surrogate0 = res["identities"]["surrogate"]
    for dl_key, dl_rec in cen["grid"].items():
        dl = float(dl_key)
        gv = dl_rec["g"]
        if not math.isfinite(gv):
            continue
        for c_T in (10.0, 30.0, 100.0, 300.0):
            T = c_T / gv
            AT, ATn = exact_fejer(KW, dlt, T)
            tail = 4.0 * surrogate0 / (T ** 2 * gv ** 2)
            lb = ATn - dl_rec["m"] - tail
            fam.append(dict(delta=dl, c_T=c_T, T=T, AT_over_T=ATn,
                            m=dl_rec["m"], tail_bound=tail, lb=lb,
                            ub=ATn, lb_rel=lb / loop))
    res["fejer"] = fam

    # ---- the margin, kappa chain, closure ----
    a_bar = float(a.mean())
    var_W = loop / n_W - a_bar ** 2
    sig_eth = mj.binned_sigma(w[sel], a)
    # between-bin (population, 30 quantile bins of the window): bin means
    qs = np.quantile(w[sel], np.linspace(0, 1, 31))
    qs[0] -= 1e-9
    qs[-1] += 1e-9
    ib = np.clip(np.searchsorted(qs, w[sel], side="right") - 1, 0, 29)
    between = float(sum((ib == b).sum() * (a[ib == b].mean() - a_bar) ** 2
                        for b in range(30)) / n_W)
    K2w = (Wb ** 2).T @ (obs ** 2)
    tot = float(K2w.mean() - a_bar ** 2)          # Tr(rho_W (dK)^2)
    sb = mj.std_basis(S)
    bench = mj.shell_benchmarks(eps, obs, float(w[sel][0]), float(w[sel][-1]),
                                S)
    lb_best = max(f["lb"] for f in fam)
    var_lb = lb_best / n_W - a_bar ** 2
    kappa_lb = math.sqrt(max(0.0, var_lb - between)) / sb
    kappa = sig_eth / sb
    res["closure"] = dict(
        a_bar=a_bar, var_W_a=var_W, total_K_var=tot,
        margin=var_W / tot, sigma_eth=sig_eth, kappa=kappa,
        between_pop=between, within_pop=var_W - between,
        B_count=bench["B_count"], n_shell=bench["n_shell"],
        var_lb=var_lb, kappa_lb=kappa_lb,
        ratio_measured=kappa / bench["B_count"],
        ratio_lb=kappa_lb / bench["B_count"],
        margin_lb=var_lb / tot)
    res["platform"]["wall_s"] = time.perf_counter() - t_start
    print(f"[d{d} S={S} n={n}] loop {loop:.1f} surrogate {surrogate:.1f} "
          f"(offdiag {res['identities']['offdiag_fraction']:.1%}); "
          f"pairs {cen['n_pairs']} P {cen['P']:.2f} (cap {cen['v_cap']:.1f}) "
          f"g {cen['g']:.2e}; M_dev "
          f"{['%.1e' % x for x in res['identities'].get('M_dev', [])]}; "
          f"lb_rel {[round(f['lb_rel'], 4) for f in fam]}; "
          f"kappa_lb/B {res['closure']['ratio_lb']:.2f} "
          f"(measured {res['closure']['ratio_measured']:.1f})",
          flush=True)
    return res, dict(H=H, Hd=Hd, w=w, Vv=Vv, eps=eps, comp=comp, obs=obs,
                     sel=sel, KW=KW, a=a, dlt=dlt, X=X, Wb=Wb)


# ----------------------------------------------------------------------------
# (R3b) insertion recursion: Tr[H^m1 A H^m2 B ...] exactly
# ----------------------------------------------------------------------------
def ins_trace(H, layer, blocks, ops):
    """Tr[H^m1 A H^m2 B ...] by block-column propagation.

    blocks = [m1, m2, ..., m_{r+1}] (H-powers); ops = [(kind, data)] x r
    applied between them; kind 'diag' scales rows by the per-row diagonal
    values (layer-diagonal operators), 'sparse'/'dense' left-multiplies.
    """
    n = H.shape[0]
    n_l = int(layer.max()) + 1
    idx = [np.where(layer == l)[0] for l in range(n_l)]
    total = 0.0
    for l0 in range(n_l):
        i0 = idx[l0]
        N0 = len(i0)
        if N0 == 0:
            continue
        Xc = np.zeros((n, N0))
        Xc[i0, :] = np.eye(N0)
        # M = H^{b0} A_1 H^{b1} ... A_r H^{br}; we propagate M^T P_{l0}
        # (equal block traces by symmetry of the trace), i.e. apply
        # H^{b0}, A_1, H^{b1}, ..., A_r, H^{br} in the forward order.
        for i, (kind, data) in enumerate(ops):
            for _ in range(blocks[i]):
                Xc = H @ Xc
            if kind == "diag":
                Xc = Xc * data[:, None]      # diagonal operator, per-row
            else:
                Xc = data @ Xc
        for _ in range(blocks[-1]):
            Xc = H @ Xc
        total += float(np.trace(Xc[i0, :]))
    return total


def validate_insertion(H, Hd, layer, S):
    """Insertion recursion vs dense powers (K, K^2, [H,K])."""
    out = {}
    K_layer = (S - layer).astype(float)
    K2_layer = K_layer ** 2
    KC = (H @ sp.diags(K_layer) - sp.diags(K_layer) @ H).tocsr()
    for (m1, m2) in ((2, 3), (4, 1), (6, 6)):
        rec = ins_trace(H, layer, [m1, m2, 0],
                        [("diag", K_layer), ("diag", K_layer)])
        dns = float(np.trace(np.linalg.matrix_power(Hd, m1)
                             @ np.diag(K_layer)
                             @ np.linalg.matrix_power(Hd, m2)
                             @ np.diag(K_layer)))
        out[f"H{m1}K_H{m2}K"] = dict(rec=rec, dense=dns,
                                     rel=abs(rec - dns) / max(1.0, abs(dns)))
    for m in (3, 8):
        rec = ins_trace(H, layer, [m, 0], [("diag", K2_layer)])
        dns = float(np.trace(np.linalg.matrix_power(Hd, m) @ np.diag(K2_layer)))
        out[f"H{m}K2"] = dict(rec=rec, dense=dns,
                              rel=abs(rec - dns) / max(1.0, abs(dns)))
    for (m1, m2) in ((2, 1), (1, 2), (3, 3)):
        rec = ins_trace(H, layer, [m1, m2, 0], [("sparse", KC),
                                                ("sparse", KC)])
        KCd = KC.toarray()
        dns = float(np.trace(np.linalg.matrix_power(Hd, m1) @ KCd
                             @ np.linalg.matrix_power(Hd, m2) @ KCd))
        out[f"H{m1}C_H{m2}C"] = dict(rec=rec, dense=dns,
                                     rel=abs(rec - dns) / max(1.0, abs(dns)))
    # [H,K] = the layer off-diagonal difference exactly: each hop entry
    # H_{c'c} carries the factor (l_{c'} - l_c) in {0, +-1}
    C = (H - sp.diags(H.diagonal())).tocoo()
    Cexp = C.copy().astype(float)
    Cexp.data = Cexp.data * (layer[C.row] - layer[C.col])
    out["comm_equals_layerdiff"] = float(
        abs(KC - Cexp.tocsr()).max()) if KC.nnz else 0.0
    return out


# ----------------------------------------------------------------------------
# (R3c) Chebyshev propagation tier (discrete Fejer, bipartite Hutchinson)
# ----------------------------------------------------------------------------
def cheb_coeffs(tau, eps=1e-13):
    """Bessel coefficients c_k of exp(i tau x) on [-1, 1]; c_0 carries 1/2.
    The degree is set by the last-coefficient tail (the Airy-region decay
    J_k(tau) ~ exp(-c (k-tau)^{3/2}) makes tau + O(tau^{1/3}) sufficient)."""
    kmax = int(tau + 12.0 * max(1.0, tau) ** (1.0 / 3.0)) + 40
    while True:
        ks = np.arange(kmax + 1)
        b = jv(ks, tau)
        tail = float(np.abs(b[max(int(tau) + 10, kmax - 15):]).sum())
        if tail < eps or kmax > 300000:
            break
        kmax = int(kmax * 1.4) + 10
    c = b * (1j) ** ks
    c[1:] *= 2.0
    return c, tail


def cheb_apply(c, Hn, M):
    """sum_k c_k T_k(Hn) M by the three-term recurrence (complex M ok)."""
    out = c[0] * M
    if len(c) > 1:
        Y1 = Hn @ M
        out = out + c[1] * Y1
        Yk, Yk1 = M, Y1
        for ck in c[2:]:
            Yk2 = 2.0 * (Hn @ Yk1) - Yk
            out = out + ck * Yk2
            Yk, Yk1 = Yk1, Yk2
    return out


def propagate_fejer(H, KW, Wb, lam_lo, lam_hi, T, s=32, seed=11,
                    dt_limit=None, t_budget=480.0, ckpt=None):
    """Discrete-Fejer replica integral A_T/T by stepwise Chebyshev
    propagation with bipartite Hutchinson probes (resumable via ckpt).

    G_M = (1/M^2) sum_{m,m'} C((m-m')dt) = sum_{jk} |X_jk|^2 Fdisc(dlt)/M,
    Fdisc(0) = M, estimated via the unbiased bipartite estimator
        C(m dt) = E[(v^T e^{-iHmdt} w)(w^T X e^{iHmdt} X v)]
    with backward family u_m = e^{-iHmdt} W0 and forward family
    f_m = e^{iHmdt} (X V0).  X = Wb KW Wb^T (window-block application).
    """
    t_start = time.perf_counter()
    n = H.shape[0]
    width = lam_hi - lam_lo
    mid = 0.5 * (lam_hi + lam_lo)
    half = 0.5 * width
    Hn = (H - sp.diags(np.full(n, mid, dtype=float))) * (1.0 / half)
    # dt: the committed census step when given (the folded-distance census
    # at that step carries the aliasing budget); else the Nyquist step
    dt = dt_limit if dt_limit is not None \
        else math.pi / 2.0 / max(width, 1e-12)
    M = int(math.ceil(T / dt))
    tau = half * dt
    c, bessel_tail = cheb_coeffs(tau)
    cF = np.conj(c)
    rng = np.random.default_rng(seed)
    V0 = rng.choice([-1.0, 1.0], size=(n, s))
    W0 = rng.choice([-1.0, 1.0], size=(n, s))

    def apply_X(Mm):
        return Wb @ (KW @ (Wb.T @ Mm))

    U = W0.astype(complex)          # backward family of the w probes
    F = apply_X(V0).astype(complex)  # forward family of the X v probes
    lag_w = np.zeros(M)
    m_start = 0
    if ckpt is not None and os.path.exists(ckpt):
        z = np.load(ckpt)
        if int(z["M"]) == M and int(z["s"]) == s and int(z["seed"]) == seed:
            U = z["U"]
            F = z["F"]
            lag_w[:len(z["lag"])] = z["lag"]
            m_start = int(z["mstep"])
            print(f"  resumed at mstep {m_start}/{M}", flush=True)

    def corr(Uc, Fc):
        """C(m dt) = E_j[(v_j^T u_m[:,j]) (w_j^T X f_m[:,j])]: unbiased
        bipartite estimate (per-probe products, then the probe mean)."""
        XF = apply_X(Fc)
        f1 = np.einsum("ij,ij->j", V0, Uc)     # v_j^T e^{-iHmdt} w_j
        f2 = np.einsum("ij,ij->j", W0, XF)     # w_j^T X e^{iHmdt} X v_j
        return float(np.mean(f1 * f2).real)

    if m_start == 0:
        lag_w[0] = corr(W0.astype(complex), F)
    t_last = time.perf_counter()
    for mstep in range(max(1, m_start), M):
        U = cheb_apply(cF, Hn, U)
        F = cheb_apply(c, Hn, F)
        lag_w[mstep] = corr(U, F)
        if (time.perf_counter() - t_start) > t_budget:
            if ckpt is not None:
                np.savez_compressed(ckpt, U=U, F=F, lag=lag_w,
                                    mstep=mstep + 1, M=M, s=s, seed=seed,
                                    dt=dt, T=T)
            break
        if ckpt is not None and mstep % 500 == 0:
            np.savez_compressed(ckpt, U=U, F=F, lag=lag_w,
                                mstep=mstep + 1, M=M, s=s, seed=seed,
                                dt=dt, T=T)
    n_done = int((lag_w != 0.0).sum())
    complete = bool(n_done == M)
    # discrete Fejer: G_M = (1/M^2) sum_{r} (M - |r|) C(r dt) * 2 (r>0) + C(0)
    tri = (M - np.arange(M)) / (M ** 2)
    GM = float((2.0 * (tri[1:n_done] * lag_w[1:n_done]).sum()
                + tri[0] * lag_w[0]))
    return dict(G_M=GM, M=M, dt=dt, tau=tau, n_done=n_done, complete=complete,
                bessel_tail=bessel_tail, T=M * dt,
                wall_s=time.perf_counter() - t_start,
                C0=lag_w[0], C_last=float(lag_w[n_done - 1]) if n_done else 0.0)


def fejer_disc(dlt, M, dt):
    """Discrete Fejer kernel (1/M)|sum_{m<M} e^{i d m dt}|^2, F(0) = M."""
    x = 0.5 * np.asarray(dlt, dtype=float) * dt
    den = np.sin(np.where(np.abs(x) < 1e-12, 1.0, x))
    num = np.where(np.abs(x) < 1e-12, 1.0, np.sin(M * x))
    out = np.ones_like(x) * M
    nz = np.abs(x) >= 1e-12
    out[nz] = (num[nz] / den[nz]) ** 2 / M
    return out


def propagate_resampled(H, KW, Wb, lam_lo, lam_hi, T, s=32, R=2,
                        t_budget=480.0):
    """R independent probe resamples of the discrete-Fejer integral."""
    vals = []
    runinfo = None
    for r in range(R):
        runinfo = propagate_fejer(H, KW, Wb, lam_lo, lam_hi, T, s=s,
                                  seed=11 + 1000 * r, t_budget=t_budget)
        vals.append(runinfo["G_M"])
        runinfo["resample"] = r
    return dict(G_M_mean=float(np.mean(vals)),
                G_M_spread=float(np.std(vals)),
                G_M_values=[float(v) for v in vals], detail=runinfo)


def main():
    out = {}
    # ---- (R3a) dense validation platforms (the dense-reachable rungs) ----
    plat = {}
    extras = {}
    for (d, S) in ((3, 40), (3, 60), (3, 80), (3, 100), (3, 116), (4, 16)):
        res, ex = run_platform(d=d, S=S, V=0.3, m_op=(S <= 60 or d == 4))
        plat[f"d{d}_S{S}"] = res
        extras[f"d{d}_S{S}"] = ex
    out["platforms"] = plat

    # ---- (R3b) insertion recursion validation (d3 S=60) ----
    H60, eps, comp, hmat = mj.sector_block(3, 60, 1.0, 0.0, 0.3, 7)
    layer60 = (60 - comp[:, 0]).astype(int)
    Hd60 = H60.toarray()
    out["insertion_validation"] = validate_insertion(H60, Hd60, layer60, 60)
    iv = {k: (v.get("rel", v) if isinstance(v, dict) else v)
          for k, v in out["insertion_validation"].items()}
    print("insertion:", {k: (('%.1e' % v) if isinstance(v, float) else v)
                         for k, v in iv.items()}, flush=True)

    # ---- (R3c) propagation tier at d3 S=60 (delta = 0.1, c_T = 30,
    #      step dt = 0.1 with the folded-distance census) ----
    ex = extras["d3_S60"]
    s60 = plat["d3_S60"]
    cen = s60["census"]
    gv = cen["grid"]["0.1"]["g"]
    mv = cen["grid"]["0.1"]["m"]
    T_prop = 30.0 / gv
    prop = propagate_resampled(ex["H"], ex["KW"], ex["Wb"],
                               float(ex["w"][0]), float(ex["w"][-1]),
                               T_prop, s=16, R=2, t_budget=540.0,
                               dt_limit=cen["dt_prop"])
    # budget vs the exact spectral values (continuous AND discrete kernels)
    ATn_prop = float(exact_fejer(ex["KW"], ex["dlt"], T_prop)[1])
    det = prop["detail"]
    GM_exact_disc = float((ex["KW"] ** 2 * fejer_disc(
        ex["dlt"], det["M"], det["dt"])).sum() / det["M"])
    prop["delta"] = 0.1
    prop["c_T"] = 20.0
    prop["g_ref"] = gv
    prop["T"] = T_prop
    prop["exact_AT_over_T"] = ATn_prop
    prop["exact_G_M_disc"] = GM_exact_disc
    prop["hutch_ci95"] = 2.0 * prop["G_M_spread"]
    # the sharp discrete tail from the folded histogram:
    #   sum_bins m(bin) * min(1, pi^2/(T^2 d(bin)^2))
    fh = cen["fold_hist"]
    tail_disc = float(sum(mm * min(1.0, math.pi ** 2
                                    / (T_prop ** 2 * dd ** 2))
                          for dd, mm in zip(fh["d_centers"],
                                            fh["masses"]))) \
        + fh["below_floor"]
    prop["tail_bound_disc"] = tail_disc
    prop["m_delta"] = mv
    prop["lb"] = (prop["G_M_mean"] - prop["hutch_ci95"]
                  - prop["tail_bound_disc"])
    prop["loop_exact"] = s60["identities"]["loop"]
    prop["lb_rel"] = prop["lb"] / s60["identities"]["loop"]
    out["propagation_d3_S60"] = prop
    print(f"propagation (d=0.1, c_T=30, T={T_prop:.1f}, M={det['M']}, "
          f"dt={det['dt']:.3f}): "
          f"G_M {prop['G_M_mean']:.1f} +- {prop['G_M_spread']:.1f}"
          f" vs exact disc {GM_exact_disc:.1f} (cont {ATn_prop:.1f}); "
          f"lb_rel {prop['lb_rel']:.4f} "
          f"(wall {prop['detail']['wall_s']:.0f}s, complete "
          f"{det['complete']})", flush=True)

    with open(os.path.join(OUT, "c4_msector_replica.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("saved", os.path.join(OUT, "c4_msector_replica.json"))


if __name__ == "__main__":
    main()
