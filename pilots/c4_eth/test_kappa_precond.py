#!/usr/bin/env python3
"""Preconditioner probe for the kappa stage at L36d4K11 (D=20736).

Variants:
  P1  spilu(H-sigma, diag_pivot_thresh=0)  double-solve  (failed: NaNs)
  P2  spilu(H-sigma, default pivoting)     double-solve
  P3  spilu(A) with A=(H-sigma)^2 explicitly assembled (PSD, stable?)
  P4  no preconditioner
  P5  ARPACK eigsh on -A (no preconditioner at all)
Each: run lobpcg ~10 iterations, report block A-residual + wall time.
"""
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

import sys
sys.path.insert(0, "/home/z/my-project/scripts")
from c4_scaled_eth import build_sparse

d, K, V, seed = 4, 11, 0.2975207, 7
H, eps, g, hmat, coords = build_sparse(d, K, 1.5, 1.0, 0.0, seed, V=V)
D = H.shape[0]
sigma = float(np.quantile(eps, 0.5))
print(f"D={D} sigma={sigma:.3f} nnzH={H.nnz}")
Hs = (H - sigma * sp.identity(D, format="csr")).tocsr()

A_mv = lambda v: Hs @ (Hs @ v)
A_op = spl.LinearOperator((D, D), matvec=A_mv, matmat=lambda W: Hs @ (Hs @ W),
                          dtype=np.float64)
rng = np.random.default_rng(8)
X0 = rng.standard_normal((D, 100))
X0, _ = np.linalg.qr(X0)

from scipy.sparse.linalg import lobpcg

def check(tag, X):
    # exact Rayleigh-Ritz on H + residual
    Q, _ = np.linalg.qr(X)
    HQ = H @ Q
    S = Q.T @ HQ; S = 0.5 * (S + S.T)
    ew, W = np.linalg.eigh(S)
    rj = np.linalg.norm(HQ @ W - (Q @ W) * ew[None, :], axis=0)
    scale = max(abs(ew).max(), 1.0)
    cert = int((rj <= 1e-6 * scale).sum())
    # A-residual of the block
    AX = Hs @ (Hs @ X)
    rA = np.linalg.norm(AX - X * (np.sum(X * AX, axis=0))[None, :], axis=0)
    print(f"  {tag}: certified={cert}/{X.shape[1]} residmax={rj.max():.2e} "
          f"A-resid med={np.median(rA):.2e}")
    return cert

# P1: diag pivot double solve
print("P1: spilu diag-pivot, double solve")
try:
    lu = spl.spilu(Hs.tocsc(), permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0,
                   drop_tol=1e-4, fill_factor=15.0)
    M1 = spl.LinearOperator((D, D), matvec=lambda v: lu.solve(lu.solve(v)),
                            matmat=lambda W: lu.solve(lu.solve(W)), dtype=np.float64)
    t0 = time.time()
    wA, VA = lobpcg(A_op, X0, M=M1, tol=1e-6, maxiter=10, largest=False)
    print(f"  P1 lobpcg {time.time()-t0:.1f}s")
    check("P1", np.asarray(VA))
except Exception as e:
    print(f"  P1 FAILED: {type(e).__name__}: {e}")

# P2: default pivoting double solve
print("P2: spilu default pivot, double solve")
try:
    lu2 = spl.spilu(Hs.tocsc(), permc_spec="MMD_AT_PLUS_A",
                    drop_tol=1e-4, fill_factor=15.0)
    M2 = spl.LinearOperator((D, D), matvec=lambda v: lu2.solve(lu2.solve(v)),
                            matmat=lambda W: lu2.solve(lu2.solve(W)), dtype=np.float64)
    t0 = time.time()
    wA, VA = lobpcg(A_op, X0, M=M2, tol=1e-6, maxiter=10, largest=False)
    print(f"  P2 lobpcg {time.time()-t0:.1f}s")
    check("P2", np.asarray(VA))
except Exception as e:
    print(f"  P2 FAILED: {type(e).__name__}: {e}")

# P3: ILU of the assembled folded matrix A (PSD)
print("P3: spilu(A) single solve, A assembled")
try:
    t0 = time.time()
    Aex = (Hs @ Hs).tocsc()
    print(f"  A assembled: nnz={Aex.nnz} ({time.time()-t0:.1f}s)")
    lu3 = spl.spilu(Aex, drop_tol=1e-4, fill_factor=10.0)
    print(f"  spilu(A) {time.time()-t0:.1f}s nnzILU={lu3.L.nnz+lu3.U.nnz}")
    M3 = spl.LinearOperator((D, D), matvec=lu3.solve, matmat=lu3.solve,
                            dtype=np.float64)
    t0 = time.time()
    wA, VA = lobpcg(A_op, X0, M=M3, tol=1e-6, maxiter=10, largest=False)
    print(f"  P3 lobpcg {time.time()-t0:.1f}s")
    check("P3", np.asarray(VA))
except Exception as e:
    print(f"  P3 FAILED: {type(e).__name__}: {e}")

# P4: no preconditioner
print("P4: no preconditioner")
try:
    t0 = time.time()
    wA, VA = lobpcg(A_op, X0, tol=1e-6, maxiter=10, largest=False)
    print(f"  P4 lobpcg {time.time()-t0:.1f}s")
    check("P4", np.asarray(VA))
except Exception as e:
    print(f"  P4 FAILED: {type(e).__name__}: {e}")

# P5: ARPACK on -A
print("P5: ARPACK eigsh on -A, k=100")
try:
    t0 = time.time()
    negA = spl.LinearOperator((D, D), matvec=lambda v: -(Hs @ (Hs @ v)),
                              dtype=np.float64)
    wA, VA = spl.eigsh(negA, k=100, which="LM", ncv=180,
                       v0=rng.standard_normal(D), maxiter=3000, tol=1e-8)
    print(f"  P5 eigsh {time.time()-t0:.1f}s")
    check("P5", np.asarray(VA))
except Exception as e:
    print(f"  P5 FAILED: {type(e).__name__}: {e}")
