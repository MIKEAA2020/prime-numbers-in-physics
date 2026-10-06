#!/usr/bin/env python3
"""
Classical limit of the M-sector problem: the coherent-state flow on
CP^{d-1} and its Lyapunov exponents -- the classical side of the C4
mathematical falsifier.

The S-sector of the number-conserving core, evaluated on normalized
coherent states alpha (sum |alpha_i|^2 = 1, x_i = |alpha_i|^2), has the
symbol

    h(alpha) = sum_i log p_i x_i + U sum_{i<j} x_i x_j
               + sum_{i != j} h_ij conj(alpha)_i alpha_j
               + V sum_{i<j} (x_i + x_j) 2 Re(conj(alpha)_i alpha_j),

and the classical (S -> infinity) flow is i alpha_dot = dh / d conj(alpha)
on the unit sphere of C^d.  The leading intensive scalings select three
classical limits:

  * one-body flow (matched dose, leading /S part: H_P + H_hop): linear,
    alpha(t) = exp(-i M t) alpha(0) with M = diag(log p) + hmat --
    integrable at every d; the numerical flow is validated against the
    exact solution.
  * kinetic flow (fixed V, leading /S^2 part: the kinetic completion):
    the quartic (x_i + x_j) 2 Re(alpha_i-bar alpha_j) symbol; d = 2 is
    one degree of freedom (integrable, lambda = 0); d >= 3 is the
    interaction-dominated classical problem whose ergodicity the Lyapunov
    exponent measures.
  * full symbol at the family couplings (finite-S classical problem).

Lyapunov: Benettin two-particle renormalization.  Outputs -> OUT/
           c4_msector_classical.json
"""
import json
import math
import os
import time

import numpy as np
from scipy.linalg import expm

import c4_scaled_eth as base
from c4_msector_jacobi import draw_couplings

OUT = base.OUT
PRIMES = base.PRIMES


def symbol_parts(d, hmat, ln_p, U, V):
    """Return (h, grad) for the full symbol; mode flags select limits."""
    pairs = [(i, j) for i in range(d) for j in range(i + 1, d)]

    def h_full(a):
        x = np.abs(a) ** 2
        val = float(np.dot(ln_p, x))
        if U != 0.0:
            val += U * sum(x[i] * x[j] for i, j in pairs)
        val += float(np.real(np.vdot(a, hmat @ a)))
        for i, j in pairs:
            val += 2.0 * V * (x[i] + x[j]) * np.real(
                np.conj(a[i]) * a[j])
        return val

    def grad_full(a):
        x = np.abs(a) ** 2
        g = ln_p * a
        if U != 0.0:
            g += U * (np.sum(x) - x) * a
        g += hmat @ a
        for i, j in pairs:
            c = np.conj(a[i]) * a[j]
            r = c + np.conj(c)                     # 2 Re(conj a_i a_j)
            xi, xj = x[i], x[j]
            gi = (a[j] * r) + (a[j] * (xi + xj))   # d/d conj a_i
            gj = (a[i] * r) + (a[i] * (xi + xj))
            g[i] += 2.0 * V * gi
            g[j] += 2.0 * V * gj
        return g

    return h_full, grad_full


def make_flow(d, hmat, ln_p, U, V, mode):
    """Select the classical limit; return (h, grad) with the couplings
    rescaled per the intensive leading part."""
    if mode == "onebody":
        # leading /S part at matched dose: H_P + H_hop only
        V_eff, U_eff = 0.0, 0.0
    elif mode == "kinetic":
        # leading /S^2 part at fixed V: kinetic (+ U/V quartic)
        V_eff, U_eff = V, U
    elif mode == "full":
        V_eff, U_eff = V, U
    else:
        raise ValueError(mode)
    h, g = symbol_parts(d, hmat, ln_p, U_eff, V_eff)
    if mode == "onebody":
        M = np.diag(ln_p) + hmat

        def h1(a):
            return float(np.real(np.vdot(a, M @ a)))
        return h1, lambda a: M @ a, M
    return h, g, None


def rk4_flow(grad, a, dt, steps):
    """Integrate i a_dot = grad(a) (flow: a_dot = -i grad) with RK4."""
    def f(a):
        return -1j * grad(a)
    for _ in range(steps):
        k1 = f(a)
        k2 = f(a + 0.5 * dt * k1)
        k3 = f(a + 0.5 * dt * k2)
        k4 = f(a + dt * k3)
        a = a + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    return a


def lyapunov(grad, a0, T, dt, renorm_every, seed):
    """Benettin two-particle method: maximal Lyapunov exponent."""
    rng = np.random.default_rng(seed)
    a = a0.copy()
    d0 = rng.standard_normal(a0.size) + 1j * rng.standard_normal(a0.size)
    d0 = d0 / np.linalg.norm(d0) * 1e-8
    b = a + d0
    n_steps = int(T / dt)
    acc = 0.0
    n_ren = 0
    for s in range(0, n_steps, renorm_every):
        m = min(renorm_every, n_steps - s)
        a = rk4_flow(grad, a, dt, m)
        b = rk4_flow(grad, b, dt, m)
        delta = b - a
        nd = np.linalg.norm(delta)
        if nd < 1e-300:
            break
        acc += math.log(nd / 1e-8)
        n_ren += 1
        b = a + delta / nd * 1e-8
    return acc / (n_ren * renorm_every * dt) if n_ren else 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"runs": [], "meta": {}}
    seed = 7
    h0 = 1.0
    T, dt, ren = 2000.0, 0.02, 25
    t_start = time.time()

    for d in (2, 3, 4):
        hmat = draw_couplings(d, h0, seed)
        ln_p = np.log(np.array(PRIMES[:d], dtype=float))
        rng = np.random.default_rng(seed + 500 + d)
        # one-body validation: numerical flow vs exp(-iMt) alpha0
        h1, g1, M = make_flow(d, hmat, ln_p, 0.0, 0.0, "onebody")
        a0 = rng.standard_normal(d) + 1j * rng.standard_normal(d)
        a0 /= np.linalg.norm(a0)
        a_num = rk4_flow(g1, a0.copy(), 0.02, 200)          # t = 4
        a_ex = expm(-1j * 4.0 * np.asarray(M)) @ a0
        dev = float(np.linalg.norm(a_num - a_ex))
        lam1 = lyapunov(g1, a0, T, dt, ren, seed)
        res["runs"].append(dict(d=d, mode="onebody", lambda_max=lam1,
                                linear_validation_dev=dev))
        print(f"  d={d} one-body: exp(-iMt) deviation={dev:.2e} "
              f"lambda={lam1:.2e}", flush=True)
        # kinetic flow (fixed-V leading part, V=0.3, U=0)
        for Vc in (0.3,):
            hk, gk, _ = make_flow(d, hmat, ln_p, 0.0, Vc, "kinetic")
            lams = []
            for trial in range(5):
                a0k = rng.standard_normal(d) + 1j * rng.standard_normal(d)
                a0k /= np.linalg.norm(a0k)
                lams.append(lyapunov(gk, a0k, T, dt, ren, seed + trial))
            lams = np.array(lams)
            # d = 2 is one degree of freedom: lambda = 0 analytically; its
            # measured value calibrates the integrator floor
            stab = None
            if d == 3:
                a0k = rng.standard_normal(d) + 1j * rng.standard_normal(d)
                a0k /= np.linalg.norm(a0k)
                stab = lyapunov(gk, a0k, 2 * T, 0.5 * dt, ren, seed + 991)
            res["runs"].append(dict(
                d=d, mode="kinetic", V=Vc, U=0.0,
                lambda_max=float(lams.max()), lambda_mean=float(lams.mean()),
                lambda_min=float(lams.min()),
                lambda_all=[float(x) for x in lams],
                dt_halved_T_doubled=(float(stab) if stab is not None
                                      else None)))
            print(f"  d={d} kinetic V={Vc}: lambda_max={lams.max():.4f} "
                  f"mean={lams.mean():.4f} min={lams.min():.4f}"
                  + (f" stability={stab:.4f}" if stab is not None else ""),
                  flush=True)
        # full symbol at the family couplings (V=0.3, U=0; and U=2 leg)
        for Uc in (0.0, 2.0):
            hf, gf, _ = make_flow(d, hmat, ln_p, Uc, 0.3, "full")
            lams = []
            for trial in range(3):
                a0f = rng.standard_normal(d) + 1j * rng.standard_normal(d)
                a0f /= np.linalg.norm(a0f)
                lams.append(lyapunov(gf, a0f, T, dt, ren, seed + 77 + trial))
            lams = np.array(lams)
            # norm conservation check
            a_chk = rk4_flow(gf, a0f.copy(), 0.02, 500)
            nrm = abs(np.linalg.norm(a_chk) - 1.0)
            res["runs"].append(dict(
                d=d, mode="full", V=0.3, U=Uc,
                lambda_max=float(lams.max()), lambda_mean=float(lams.mean()),
                norm_drift_10t=float(nrm)))
            print(f"  d={d} full V=0.3 U={Uc}: lambda_max={lams.max():.4f} "
                  f"mean={lams.mean():.4f} norm_drift={nrm:.1e}",
                  flush=True)

    res["meta"] = dict(T=T, dt=dt, renorm_every=ren, seed=seed,
                       integrator="RK4", benettin_delta=1e-8,
                       wall_s=round(time.time() - t_start, 1))
    path = os.path.join(OUT, "c4_msector_classical.json")
    with open(path, "w") as fh:
        json.dump(res, fh, indent=1)
    print("saved", path, flush=True)


if __name__ == "__main__":
    main()
