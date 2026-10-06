#!/usr/bin/env python3
"""
Factorization-free interior eigen-windows for the C4 strong-ETH fluctuation
ladder.

The shift-invert window tier is bounded by LU fill: beyond D = 20736 in d = 4
and D = 59319 in d = 3 the factorization exceeds the address-space guard, so
the k = 350 median-energy eigenpairs -- the input of the kappa diagnostic --
cannot be produced by that route.  This script computes the SAME selection
with a factorization-free method: block subspace iteration on

    B = (H - c)^2,   c = median of the diagonal energies,

whose smallest eigenvalues are the eigenvalues of H nearest c (exactly the
shift-invert selection at sigma = c).  The acceleration polynomial is the
classical low-pass Chebyshev on [0, b_high],

    p(b) = T_M(xi(b)),   xi(b) = 1 + 2 (b_w - b) / (b_high - b_w),

with b_w = t^2 the squared passband half-width: eigenvalues of B below b_w
(H within +-t of c) are amplified by cosh(M acosh(xi(0))), everything above
b_w stays bounded by 1.  Composition law T_m o T_n = T_{mn}: the total degree
M is applied in resumable chunks, with the block checkpointed after every
chunk.

Block hygiene (the boundary of a contiguous interior block never converges):
after each Rayleigh-Ritz pass the converged Ritz vectors are kept and the
remaining directions are replaced by fresh random vectors orthogonalized
against them, so no stalled pair holds a seat; the final selection is made
among certified pairs only.

Precision: discovery sweeps filter in float32 (span-preserving; per-column
rescaling keeps the three-term recurrence exact); the final polish sweep
filters in float64, which removes the span error that float32 rounding
imposes on the weaker block directions (~eps_32 * amplification contrast).
Rayleigh-Ritz, rotation and residual certification are float64 throughout.

Validation: --validate recomputes platforms that have cached LU windows
(L36d4K11, L36d3K28) and compares eigenvalue sets, kappa, PR/D and <r>
against the LU tier.

Outputs -> /home/z/my-project/download/pilot_c4_eth_scaled/
           res_krylov_{tag}.json, win_krylov_{tag}.npz,
           krs_{tag}.npz (resumable state, removed on success),
           c4_kappa_krylov_results.json (accumulated)
"""
import argparse
import json
import math
import os
import time

import numpy as np
from scipy.sparse.linalg import eigsh

import c4_scaled_eth as base

OUT = base.OUT


def spectral_edges(H):
    """Converged extremal eigenvalues via ARPACK (no factorization)."""
    hi = eigsh(H, k=4, which="LA", return_eigenvectors=False,
               tol=0, maxiter=20000)
    lo = eigsh(H, k=4, which="SA", return_eigenvectors=False,
               tol=0, maxiter=20000)
    return float(lo.min()), float(hi.max())


def eps_to_eigen_ratio(d, D):
    """eps-count-to-eigenvalue-count ratio in the median window, from the
    cached strong-ETH results; log-log extrapolated in D per family.
    Fallback 3.0."""
    fp = os.path.join(OUT, "c4_strongeth_results.json")
    if not os.path.exists(fp):
        return 3.0
    try:
        rows = json.load(open(fp))["rows"]
    except Exception:
        return 3.0
    pts = [(r["D"], r["N_shell"] / 350.0) for r in rows
           if r["tag"].startswith("L36") and r["d"] == d and r["N_shell"]]
    if len(pts) < 2:
        return 3.0
    xs = np.log([p[0] for p in pts])
    ys = np.log([p[1] for p in pts])
    A = np.vstack([xs, np.ones_like(xs)]).T
    coef = np.linalg.lstsq(A, ys, rcond=None)[0]
    return float(np.exp(coef[0] * math.log(D) + coef[1]))


def lanczos_count(H, c, t, D, probes=12, steps=360, seed=4242):
    """Eigenvalue count in [c-t, c+t] by stochastic Lanczos quadrature:
    D * mean_p <z_p, f(H) z_p> with f the raised cosine on the band
    (integral 2t: exact for a flat density).  Block-independent, so the
    passband can be sized even when the block cannot see past its own
    boundary.  ~360 Lanczos steps keep the quadrature bias below ~2% for
    bands of relative width t/R ~ 1/170 (validated against dense counts:
    100 steps bias +30-70%, 250 steps +10%, 360 steps under 2%)."""
    from scipy.linalg import eigh_tridiagonal
    rng = np.random.default_rng(seed)
    total = 0.0
    for p in range(probes):
        q = rng.standard_normal(D)
        q /= np.linalg.norm(q)
        Q = np.empty((D, steps))
        alpha = np.empty(steps)
        beta = np.empty(steps - 1)
        jj = steps
        for j in range(steps):
            Q[:, j] = q
            z = H @ q
            alpha[j] = float(q @ z)
            if j < steps - 1:
                z = z - alpha[j] * q - (beta[j - 1] * Q[:, j - 1] if j > 0
                                        else 0.0)
                z -= Q[:, : j + 1] @ (Q[:, : j + 1].T @ z)
                nb = float(np.linalg.norm(z))
                if nb < 1e-12:
                    jj = j + 1
                    break
                beta[j] = nb
                q = z / nb
        ev, U = eigh_tridiagonal(alpha[:jj], beta[: jj - 1])
        wts = U[0, :] ** 2
        x = ev - c
        f = np.where(np.abs(x) <= t,
                     1.0 + np.cos(np.pi * np.clip(x / t, -1.0, 1.0)), 0.0)
        total += float(wts @ f)
    return total / probes * D


def initial_passband(d, D, eps, c, s, H=None):
    """t such that the passband [c-t, c+t] holds ~ s eigenvalues: eps-count
    estimate refined by two Lanczos-quadrature count iterations (the
    eps/eigen density ratio is only accurate to ~20%)."""
    ratio = eps_to_eigen_ratio(d, D)
    want = min(max(int(math.ceil(s * ratio)), 8), int(0.9 * eps.size))
    dd = np.sort(np.abs(eps - c))
    t = float(dd[min(want - 1, dd.size - 1)]) * 1.15
    if H is not None:
        for _ in range(2):
            cnt = lanczos_count(H, c, t, D)
            if cnt <= 0:
                break
            t *= float(np.clip(1.02 * s / cnt, 0.7, 1.4))
    return t, ratio


def degree_for(t, R, target=1.0e4):
    """Total Chebyshev degree M such that the rank-~0.84 s member of the
    passband (b ~ 0.64 b_w against a stopband bounded by 1) is amplified by
    ~`target` in one sweep."""
    u = 0.72 * t * t / max(R * R - t * t, 1e-12)
    ac = math.acosh(1.0 + u)
    return int(np.clip(math.log(target) / max(ac, 1e-9), 60, 1500))


def apply_filter_chunk(Hf, c, V, m, b_w, b_high, renorm_every=20,
                       counter=None):
    """T_m(xi(B)) V, B = (H-c)^2, via the three-term recurrence.

    V: (D, s) block.  Per-column rescaling every `renorm_every` steps keeps
    the recurrence exact (y_{j-1} and y_j scaled by the same factor) and the
    magnitudes in range.  Returns a block spanning the filtered subspace.
    """
    dt = V.dtype
    if dt == np.float32:
        a1 = np.float32(2.0 / (b_high - b_w))
        beta = np.float32(1.0 + float(a1) * b_w)
        cf = np.float32(c)
    else:
        a1 = 2.0 / (b_high - b_w)
        beta = 1.0 + float(a1) * b_w
        cf = c

    def Hc(X):
        if counter is not None:
            counter[0] += 1
        Y = Hf @ X
        Y -= cf * X
        return Y

    y_prev = V                                   # take ownership
    T1 = Hc(y_prev)
    T2 = Hc(T1)
    y_cur = beta * y_prev - a1 * T2              # T_1(xi(B)) V
    del T1, T2
    for j in range(2, m + 1):
        T1 = Hc(y_cur)
        T2 = Hc(T1)
        # y_new = 2*(beta*y_cur - a1*T2) - y_prev, written into y_prev
        y_prev *= -1.0
        y_prev += (2.0 * beta) * y_cur
        y_prev -= (2.0 * a1) * T2
        y_prev, y_cur = y_cur, y_prev
        del T1, T2
        if renorm_every and (j % renorm_every) == 0:
            sc = np.linalg.norm(y_cur, axis=0)
            sc[sc == 0] = 1.0
            y_cur /= sc
            y_prev /= sc
    return y_cur


def orthonormalize(V):
    from scipy.linalg import qr
    Q, _ = qr(V, mode="economic", overwrite_a=True)
    return Q


def refresh_block(V, theta, resid, tol, D, rng):
    """Keep converged Ritz vectors; replace the rest with fresh random
    vectors orthogonalized against them.  Returns (V, n_conv, conv_theta)."""
    conv = resid <= tol
    nc = int(conv.sum())
    nf = V.shape[1] - nc
    if nf == 0:
        return V, nc, theta[conv]
    R = rng.standard_normal((D, nf))
    Vc = V[:, conv]
    R -= Vc @ (Vc.T @ R)
    R = orthonormalize(R)
    Vn = np.empty_like(V)
    Vn[:, :nc] = Vc
    Vn[:, nc:] = R
    return Vn, nc, theta[conv]


def rayleigh_ritz(H, V):
    """Rotate the block to Ritz vectors; return (V, theta, residuals)."""
    HV = H @ V
    W = V.T @ HV
    W = 0.5 * (W + W.T)
    theta, U = np.linalg.eigh(W)
    V = V @ U
    HV = HV @ U
    resid = np.linalg.norm(HV - V * theta[None, :], axis=0)
    return V, theta, resid


def initial_block(D, s, eps, c, seed):
    """Half nearest-eps basis vectors (head start: the median-energy
    eigenstates carry a large fraction of their weight on the near-resonant
    shell), half Gaussian random."""
    rng = np.random.default_rng(seed + 1)
    n_basis = s // 2
    idx = np.argsort(np.abs(eps - c))[:n_basis]
    V0 = np.zeros((D, s))
    V0[idx, np.arange(n_basis)] = 1.0
    V0[:, n_basis:] = rng.standard_normal((D, s - n_basis))
    return orthonormalize(V0)


def state_path(tag):
    return os.path.join(OUT, f"krs_{tag}.npz")


def save_state(tag, V, meta):
    np.savez_compressed(state_path(tag), V=V, **meta)


def load_state(tag):
    z = np.load(state_path(tag))
    meta = {k: (z[k].item() if z[k].shape == () else z[k])
            for k in z.files if k != "V"}
    return z["V"], meta


def select_converged(theta, resid, c, k, tol):
    conv = np.where(resid <= tol)[0]
    order = conv[np.argsort(np.abs(theta[conv] - c))]
    return order[:k]


def finalize(res, H, eps, coords, d, K, D, tag, V, theta, resid, c, tol,
             meta_wall):
    obs1 = coords[0].ravel().astype(float)
    obsd = coords[d - 1].ravel().astype(float)
    sel = select_converged(theta, resid, c, res["k"], tol)
    n_ok = len(sel)
    if n_ok < res["k"]:
        print(f"  WARNING {tag}: only {n_ok}/{res['k']} certified pairs -- "
              f"run more sweeps", flush=True)
    w = np.sort(theta[sel])
    Vsel = V[:, sel][:, np.argsort(theta[sel])]
    rj = resid[sel]
    r_mean, r_err = base.ratio_statistic(w)
    eth1 = base.eth_window(w, Vsel, obs1)
    ethd = base.eth_window(w, Vsel, obsd)
    micro1 = base.micro_reference(eps, obs1, eth1["edges"])
    microd = base.micro_reference(eps, obsd, ethd["edges"])
    v1 = np.isfinite(micro1) & np.isfinite(eth1["smooth"])
    vd = np.isfinite(microd) & np.isfinite(ethd["smooth"])
    res.update(
        n_certified=int(n_ok),
        tier="krylov-window",
        window=[float(w[0]), float(w[-1])],
        band_est=[float(eps.min()), float(eps.max())],
        eig_resid_max=float(rj.max()), eig_resid_med=float(np.median(rj)),
        r_mean=r_mean, r_sem=r_err,
        sigma_eth=eth1["sigma_eth"], sigma_eth_d=ethd["sigma_eth"],
        micro_rmse=float(np.sqrt(np.mean(
            (eth1["smooth"][v1] - micro1[v1]) ** 2))) if v1.sum() else None,
        micro_rmse_d=float(np.sqrt(np.mean(
            (ethd["smooth"][vd] - microd[vd]) ** 2))) if vd.sum() else None,
        pr_over_D=base.participation(Vsel),
    )
    res["method"].update(**meta_wall)
    np.savez_compressed(
        os.path.join(OUT, f"win_krylov_{tag}.npz"),
        w=w, a1=eth1["a"], ad=ethd["a"],
        centers=eth1["centers"], smooth1=eth1["smooth"], micro1=micro1,
        smoothd=ethd["smooth"], microd=microd,
    )
    with open(os.path.join(OUT, f"res_krylov_{tag}.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    acc_path = os.path.join(OUT, "c4_kappa_krylov_results.json")
    acc = json.load(open(acc_path)) if os.path.exists(acc_path) else {}
    acc[tag] = res
    with open(acc_path, "w") as fh:
        json.dump(acc, fh, indent=1)
    print(f"  FINAL {tag}: window=[{w[0]:.4f},{w[-1]:.4f}] n={n_ok} "
          f"<r>={r_mean:.4f} sigma_ETH={res['sigma_eth']:.4f} "
          f"PR/D={res['pr_over_D']:.4f} resid_max={rj.max():.2e} "
          f"sweeps={res['method']['sweeps']}", flush=True)
    return res


class DeadlineHit(Exception):
    pass


def run(tag, d, K, g0, h0, U, seed, Vc, scramble, k, s, m_chunk,
        max_sweeps, tol, deadline, resume, f32):
    t_start = time.perf_counter()
    D = (K + 1) ** d
    if resume and os.path.exists(state_path(tag)):
        V, state = load_state(tag)
        c = float(state["c"]); t = float(state["t"])
        a = float(state["a"]); b = float(state["b"])
        M = int(state["M"]); sweeps = int(state["sweeps"])
        chunks = int(state["chunks"]); matmats = int(state["matmats"])
        phase = int(state["phase"])
        H, eps, g, hmat, coords = base.build_sparse(
            d, K, g0, h0, U, seed, V=Vc, scramble=scramble)
        print(f"[{tag}] resume: D={D} sweeps={sweeps} chunks={chunks} "
              f"M={M} t={t:.3f} phase={phase}", flush=True)
    else:
        H, eps, g, hmat, coords = base.build_sparse(
            d, K, g0, h0, U, seed, V=Vc, scramble=scramble)
        c = float(np.median(eps))
        a, b = spectral_edges(H)
        marg = 0.02 * (b - a)
        a, b = a - marg, b + marg
        R = max(c - a, b - c)
        t, ratio = initial_passband(d, D, eps, c, s, H=H)
        M = degree_for(t, R)
        sweeps, chunks, matmats, phase = 0, 0, 0, 0
        V = initial_block(D, s, eps, c, seed)
        state = dict(c=c, t=t, a=a, b=b, M=M, sweeps=0, chunks=0,
                     matmats=0, phase=0)
        print(f"[{tag}] D={D} nnz={H.nnz} c={c:.3f} edges=[{a:.2f},{b:.2f}] "
              f"t={t:.3f} (eps-ratio {ratio:.2f}) M={M} s={s}", flush=True)
    R = max(c - float(state["a"]), float(state["b"]) - c)
    b_high = R * R
    # discovery tolerance: above the float32 filter floor (~eps_32 * sqrt(M)
    # * contrast * ||H||) -- discovery only needs span inclusion; the f64
    # polish sweep certifies
    tol_loose = max(tol, 2e-4 * R)
    H32 = H.astype(np.float32) if f32 else H
    rmax_sel, count_in, n_conv_band = float("inf"), -1, -1
    chunk_est = 60.0

    res = dict(tag=tag, d=d, K=K, D=D, g0=g0, h0=h0, U=U, seed=seed,
               V=Vc, scramble=scramble, k=k, s=s,
               sigma=c, sigma_quantile=0.5,
               method=dict(filter_dtype=("float32+f64 polish" if f32
                                         else "float64"),
                           m_chunk=m_chunk, t=float(state["t"]),
                           R=float(R), edges=[float(state["a"]),
                                              float(state["b"])]))
    counter = [0]
    rngf = np.random.default_rng(seed + 9173)

    try:
        while sweeps < max_sweeps:
            # ---- phase 1 (float32 discovery) / phase 2 (float64 polish) --
            while chunks * m_chunk < int(state["M"]):
                now = time.perf_counter()
                if now - t_start + chunk_est + 45.0 > deadline:
                    raise DeadlineHit()
                t_ch = time.perf_counter()
                if phase == 0 and f32:
                    Vin = V.astype(np.float32)
                    V = apply_filter_chunk(H32, c, Vin, m_chunk,
                                           float(state["t"]) ** 2, b_high,
                                           counter=counter)
                else:
                    Vin = V.astype(np.float64)
                    V = apply_filter_chunk(H, c, Vin, m_chunk,
                                           float(state["t"]) ** 2, b_high,
                                           counter=counter)
                chunk_est = max(chunk_est, time.perf_counter() - t_ch)
                chunks += 1
                matmats += 2 * m_chunk
            # ---- Rayleigh-Ritz in float64 ----
            V = V.astype(np.float64)
            V = orthonormalize(V)
            V, theta, resid = rayleigh_ritz(H, V)
            matmats += s
            sweeps += 1
            chunks = 0
            count_in = int((np.abs(theta - c) <= float(state["t"])).sum())
            count_est = lanczos_count(H, c, float(state["t"]), D)
            tol_eff = tol_loose if (phase == 0 and f32) else tol
            n_conv_band = int(((resid <= tol_eff) &
                               (np.abs(theta - c) <= float(state["t"]))).sum())
            sel = select_converged(theta, resid, c, k, tol_eff)
            rmax_sel = float(resid[sel].max()) if len(sel) else float("inf")
            print(f"  sweep {sweeps} phase {phase}: M={state['M']} "
                  f"count_in={count_in} "
                  f"count_est={(f'{count_est:.0f}' if count_est else '--')} "
                  f"conv_band={n_conv_band} "
                  f"resid_q={np.percentile(resid, [10, 50, 90]).round(3)} "
                  f"theta_near_c={np.sort(np.abs(theta - c))[:5].round(3)}",
                  flush=True)
            # discovery = span inclusion (count-based: the float32 filter's
            # residual floor grows like ||H|| * sqrt(M) * amplification
            # contrast and can sit above any tolerance-based criterion at
            # the large platforms; certification is the polish phase's job)
            disc_done = (sweeps >= 3) and (count_in >= 0.85 * s)
            if phase == 0 and f32 and disc_done:
                phase = 1                  # discovery done -> polish
                state["phase"] = 1
                print(f"  discovery complete (count_in={count_in}) -> "
                      f"f64 polish (M={state['M']})", flush=True)
            elif n_conv_band >= k:
                break                      # certified: done
            elif sweeps >= max_sweeps:
                break
            # ---- passband adaptivity: dead band around 1.02 s; the probe
            #      noise is ~10% at narrow bands, so correct in small steps
            if phase == 0:
                cnt = count_est
                if cnt > 0:
                    fac = 1.02 * s / cnt
                    if fac > 1.08:
                        state["t"] = float(state["t"]) * min(fac, 1.12)
                    elif fac < 0.92:
                        state["t"] = float(state["t"]) * max(fac, 0.90)
                elif count_in < 0.95 * s:
                    state["t"] = float(state["t"]) * 1.15
                state["M"] = degree_for(float(state["t"]), R)
                state["sweeps"] = sweeps
                state["chunks"] = 0
                state["matmats"] = matmats
                save_state(tag, V, state)
                res["method"].update(t=float(state["t"]),
                                     M=int(state["M"]), count_est=cnt)
            elif count_in < 0.85 * s:
                # polish phase but the block cannot fill: passband too
                # narrow; widen and note the new degree
                state["t"] = float(state["t"]) * 1.15
                state["M"] = degree_for(float(state["t"]), R)
                state["sweeps"] = sweeps
                state["chunks"] = 0
                state["matmats"] = matmats
                save_state(tag, V, state)
                res["method"].update(t=float(state["t"]),
                                     M=int(state["M"]))
    except DeadlineHit:
        save_state(tag, V, dict(c=c, t=float(state["t"]), a=float(state["a"]),
                                b=float(state["b"]), M=int(state["M"]),
                                sweeps=sweeps, chunks=chunks,
                                matmats=matmats, phase=int(phase)))
        print(f"  deadline: state saved (sweeps={sweeps}, chunks={chunks}, "
              f"phase={phase}) -- rerun with --resume", flush=True)
        return None

    wall = time.perf_counter() - t_start
    meta_wall = dict(sweeps=sweeps, M=int(state["M"]), m_chunk=m_chunk,
                     matmats_total=int(matmats),
                     filter_matmats_this_run=counter[0],
                     wall_s=round(wall, 1),
                     converged=bool(n_conv_band >= k),
                     n_conv_band=int(n_conv_band), count_in_band=count_in,
                     t=float(state["t"]), phase=int(phase))
    res["method"].update(**meta_wall)
    out = finalize(res, H, eps, coords, d, K, D, tag, V, theta, resid, c,
                   tol, meta_wall)
    try:
        if out is None or out.get("n_certified", 0) >= k:
            os.remove(state_path(tag))
    except OSError:
        pass
    return out


def binned_sigma(w, a, n_bins=30):
    qs = np.quantile(w, np.linspace(0, 1, n_bins + 1))
    qs[0] -= 1e-9
    qs[-1] += 1e-9
    ib = np.clip(np.searchsorted(qs, w, side="right") - 1, 0, n_bins - 1)
    fl = [a[ib == b_].std() for b_ in range(n_bins) if (ib == b_).sum() >= 3]
    return float(np.sqrt(np.mean(np.square(fl))))


def validate(tags):
    """Recompute LU-window platforms with the Krylov estimator and compare."""
    rows = []
    for tag in tags:
        rp = os.path.join(OUT, f"res_{tag}.json")
        wp = os.path.join(OUT, f"win_{tag}.npz")
        if not (os.path.exists(rp) and os.path.exists(wp)):
            print(f"  validate: {tag} has no cached LU window -- skipped",
                  flush=True)
            continue
        r = json.load(open(rp))
        z = np.load(wp)
        for p in (os.path.join(OUT, f"res_krylov_{tag}val.json"),
                  os.path.join(OUT, f"win_krylov_{tag}val.npz"),
                  state_path(tag + "val")):
            if os.path.exists(p):
                os.remove(p)
        kval = r.get("k") or 350
        kw = dict(d=r["d"], K=r["K"], g0=r["g0"], h0=r["h0"],
                  U=r.get("U", 0.0), seed=r["seed"], Vc=r.get("V", 0.0),
                  scramble=r.get("scramble", False), k=kval,
                  s=kval + 66, m_chunk=90, max_sweeps=8, tol=2e-6)
        out = run(tag + "val", resume=False, f32=True,
                  deadline=500.0, **kw)
        if out is None:      # deadline hit mid-sweep: resume until done
            for _ in range(6):
                out = run(tag + "val", resume=True, f32=True,
                          deadline=560, **kw)
                if out is not None:
                    break
        if out is None:
            print(f"  validate {tag}: deadline hit repeatedly -- manual "
                  f"rerun needed", flush=True)
            return rows
        wl = np.sort(np.asarray(z["w"]))
        rk = json.load(open(os.path.join(OUT, f"res_krylov_{tag}val.json")))
        zk = np.load(os.path.join(OUT, f"win_krylov_{tag}val.npz"))
        wk = np.sort(np.asarray(zk["w"]))
        n = min(len(wl), len(wk))
        dw = float(np.max(np.abs(wl[:n] - wk[:n])))
        sig_l = binned_sigma(np.asarray(z["w"]), np.asarray(z["a1"]))
        sig_k = binned_sigma(np.asarray(zk["w"]), np.asarray(zk["a1"]))
        rows.append(dict(tag=tag, D=r["D"], dw_max=dw,
                         sigma_LU=sig_l, sigma_krylov=sig_k,
                         ratio=sig_k / sig_l if sig_l else None,
                         pr_LU=r.get("pr_over_D"),
                         pr_krylov=rk.get("pr_over_D"),
                         r_LU=r.get("r_mean"), r_krylov=rk.get("r_mean"),
                         resid_max=rk["eig_resid_max"],
                         sweeps=rk["method"]["sweeps"],
                         wall_s=rk["method"]["wall_s"]))
        print(f"  VALIDATE {tag}: max|dw|={dw:.2e} "
              f"sigma_LU={sig_l:.4f} sigma_krylov={sig_k:.4f} "
              f"ratio={sig_k / sig_l:.4f} "
              f"PR {r.get('pr_over_D'):.4f}->{rk['pr_over_D']:.4f} "
              f"<r> {r.get('r_mean'):.4f}->{rk['r_mean']:.4f}", flush=True)
        del z, zk
    with open(os.path.join(OUT, "c4_kappa_krylov_validation.json"), "w") \
            as fh:
        json.dump(rows, fh, indent=1)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default=None)
    p.add_argument("--d", type=int, default=None)
    p.add_argument("--K", type=int, default=None)
    p.add_argument("--g0", type=float, default=1.5)
    p.add_argument("--h0", type=float, default=1.0)
    p.add_argument("--U", type=float, default=0.0)
    p.add_argument("--V", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--k", type=int, default=350)
    p.add_argument("--s", type=int, default=0, help="block size (default k+66)")
    p.add_argument("--m-chunk", type=int, default=90)
    p.add_argument("--max-sweeps", type=int, default=16)
    p.add_argument("--tol", type=float, default=2e-6)
    p.add_argument("--deadline", type=float, default=430.0)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--f64", action="store_true",
                   help="filter in float64 throughout (reference precision)")
    p.add_argument("--validate", action="store_true")
    a = p.parse_args()
    if a.validate:
        validate(["L36d4K11", "L36d3K28"])
        return
    if not (a.tag and a.d and a.K):
        p.error("--tag --d --K required (or --validate)")
    s = a.s or (a.k + 66)
    run(a.tag, a.d, a.K, a.g0, a.h0, a.U, a.seed, a.V, False, a.k, s,
        a.m_chunk, a.max_sweeps, a.tol, a.deadline, a.resume,
        not a.f64)


if __name__ == "__main__":
    main()
