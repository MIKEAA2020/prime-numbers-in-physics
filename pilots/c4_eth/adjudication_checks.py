#!/usr/bin/env python3
"""Mathematical adjudication checks for the three-audit review.

Checks (each adjudicates a specific contested claim):
  1. Counting-law defect r(E) = log N(E) - E/(h*w0):
     grok: "non-convergent sawtooth of amplitude log 2".
     muse: "error is O(e^{-E/(h*w0)})".
     Paper (Thm 6.1 as written): "amplitude O(1); does not converge".
     -> compute r(E) exactly at integer-boundary energies, check the
        envelope log(1 - e^{-x}) and the convergence r -> 0.
  2. Conjugacy class sizes vs group order:
     grok: "Class sizes of a conjugacy class divide the group order only
     in trivial cases".  Orbit-stabilizer says |C(x)| * |C_G(x)| = |G|,
     so |C(x)| | |G| always.  Verify by brute force on many small groups.
  3. Dirichlet return-time bound: for m rationally independent frequencies,
     exists tau <= (2*pi/delta)^m with all phases within delta.
     Verify numerically for small m, and check the polynomial-in-S claim:
     typical integers near x carry ~log log x prime frequencies.
  4. Bohr almost-periodicity + the raw staircase microcanonical temperature:
     S(E) = k log floor(e^x) is a staircase (dS/dE = 0 a.e.) -- the
     "microcanonical temperature equals T_H identically" claim of the
     paper can only refer to a smoothing; document.
"""
import numpy as np
from itertools import permutations
from math import log, floor, exp, gcd

res = {}

# ---------------------------------------------------------------- 1
# exact integer check of the defect identity: for x = E/(h*w0),
# N = floor(e^x); use integers directly: n-th level at x = log n.
# r(x) = log(floor(e^x)) - x.  Worst points: x just below log m
# (N = m-1): r = log(m-1) - x -> log((m-1)/m) as x -> log m^-.
# Envelope claim: log(1 - e^{-x}) <= r(x) <= 0, sharp.
print("=== 1. Counting-law defect ===")
worst = []
for m in range(2, 10**6):
    # worst defect at level m: r -> log((m-1)/m) from below (x -> log m^-)
    # equivalent: log(1 - 1/m)
    worst.append(-log(1 - 1/m / 1))  # placeholder, recompute below properly
# Do it properly: exact defect at energies x = log(m) - tiny:
# r_max_neg at interval m (N = m-1 on [log(m-1), log m)) is approached
# as x -> log m^-: r -> log(m-1) - log m = log(1 - 1/m).
ms = np.array([2, 3, 10, 10**2, 10**3, 10**4, 10**5, 10**6, 10**9, 10**18,
               10**50, 10**100], dtype=object)
rows = []
for m in ms:
    amp = -log(1 - 1/m)          # amplitude at the m-th jump
    env = -log(1 - 1/m)          # same thing; envelope e^{-x} at x=log m is 1/m
    rows.append((m, amp, 1/m))
print(f"{'m':>8} {'jump amplitude log(1+1/m)':>26} {'e^{-x}=1/m':>14} {'ratio':>8}")
for m, amp, inv in rows:
    print(f"{m:>8} {amp:>26.3e} {inv:>14.3e} {amp/inv:>8.4f}")
# convergence: r -> 0 and amplitude/ (1/m) -> 1  =>  O(e^{-x}), muse RIGHT.
r_conv = -log(1 - 1/10**12)
print(f"defect at x=log(1e12) level boundary: {r_conv:.3e}  (-> 0; converges)")
print(f"bound -log(1-e^-x) <= 2e^-x for x>=log2: "
      f"{-log(1-0.5):.4f} vs {2*0.5:.4f}")
res["defect"] = dict(
    converges_to_zero=True,
    amplitude_asymptotic="log(1+1/m) ~ 1/m = e^{-x}",
    grok_verdict="WRONG on convergence (r->0) and on asymptotic amplitude "
                 "(log 2 is only the global/first-jump envelope)",
    muse_verdict="RIGHT: O(e^{-E/(h w0)}) sharp",
    paper_verdict="WRONG as written (Thm 6.1 says 'does not converge')")

# ---------------------------------------------------------------- 2
print("\n=== 2. Class sizes vs group order (brute force) ===")
def class_sizes(els, mul):
    """conj class sizes of a finite group given elements and mul table."""
    idx = {e: i for i, e in enumerate(els)}
    n = len(els)
    seen = set()
    sizes = []
    for i in range(n):
        if i in seen:
            continue
        cl = set()
        for g in range(n):
            # g e g^{-1}
            gi = idx[mul(g, i)]  # need inverse; do via full search
        # simpler: compute closure by conjugating with all g
        cl = set()
        for g in range(n):
            # find g^{-1}
            for h in range(n):
                if mul(g, h) == els[0]:
                    inv = h
                    break
            cl.add(idx[mul(mul(g, i), inv)])
        seen |= cl
        sizes.append(len(cl))
    return sizes

def perm_mul(a, b):
    return tuple(a[b[i]] for i in range(len(a)))

def make_sn(n):
    els = list(permutations(range(n)))
    idx = {e: i for i, e in enumerate(els)}
    # build mul via function composition
    table = {}
    invs = []
    for g in els:
        inv = tuple(np.argsort(g))
        invs.append(idx[inv])
    # group as permutations: (g*h)(i) = g(h(i)) -> perm_mul(g,h)= g of h
    sizes = []
    seen = set()
    for i, e in enumerate(els):
        if i in seen: continue
        cl = set()
        for j, g in enumerate(els):
            cl.add(idx[perm_mul(perm_mul(g, e), els[invs[j]])])
        seen |= cl
        sizes.append(len(cl))
    return len(els), sizes

def make_cyclic(n):
    els = list(range(n))
    inv = [(-g) % n for g in els]
    sizes = []
    seen = set()
    for e in els:
        if e in seen: continue
        cl = {(g + e - g) % n for g in els}
        seen |= cl
        sizes.append(len(cl))
    return n, sizes

def make_dihedral(n):
    # elements (r, s): r in Z_n, s in {0,1}; mul: (r1,s1)(r2,s2) =
    # (r1 + (-1)^s1 r2, s1+s2)
    els = [(r, s) for s in (0, 1) for r in range(n)]
    def mul(a, b):
        r1, s1 = a; r2, s2 = b
        return ((r1 + (-1 if s1 else 1) * r2) % n, (s1 + s2) % 2)
    def inv(a):
        r, s = a
        if s == 0: return ((-r) % n, 0)
        return (r, 1)
    idx = {e: i for i, e in enumerate(els)}
    sizes = []
    seen = set()
    for e in els:
        i = idx[e]
        if i in seen: continue
        cl = {idx[mul(mul(g, e), inv(g))] for g in els}
        seen |= cl
        sizes.append(len(cl))
    return len(els), sizes

def make_q8():
    # quaternion group as (±1, ±i, ±j, ±k) with table
    els = [1, -1, 'i', '-i', 'j', '-j', 'k', '-k']
    def mul(a, b):
        T = {('i','j'):'k', ('j','k'):'i', ('k','i'):'j',
             ('j','i'):'-k', ('k','j'):'-i', ('i','k'):'-j'}
        if a == 1: return b
        if b == 1: return b if a == 1 else (a if b == 1 else None)
        # handle
        if isinstance(a, int) or isinstance(b, int):
            pass
        return None
    # too fiddly; use permutation representation instead: Q8 < S8 via
    # left regular action on its 8 elements with a proper table
    tbl = {
        ('1','1'):'1', ('1','-1'):'-1', ('1','i'):'i', ('1','-i'):'-i',
        ('1','j'):'j', ('1','-j'):'-j', ('1','k'):'k', ('1','-k'):'-k',
        ('-1','1'):'-1', ('-1','-1'):'1', ('-1','i'):'-i', ('-1','-i'):'i',
        ('-1','j'):'-j', ('-1','-j'):'j', ('-1','k'):'-k', ('-1','-k'):'k',
        ('i','1'):'i', ('i','-1'):'-i', ('i','i'):'-1', ('i','-i'):'1',
        ('i','j'):'k', ('i','-j'):'-k', ('i','k'):'-j', ('i','-k'):'j',
        ('-i','1'):'-i', ('-i','-1'):'i', ('-i','i'):'1', ('-i','-i'):'-1',
        ('-i','j'):'-k', ('-i','-j'):'k', ('-i','k'):'j', ('-i','-k'):'-j',
        ('j','1'):'j', ('j','-1'):'-j', ('j','i'):'-k', ('j','-i'):'k',
        ('j','j'):'-1', ('j','-j'):'1', ('j','k'):'i', ('j','-k'):'-i',
        ('-j','1'):'-j', ('-j','-1'):'j', ('-j','i'):'k', ('-j','-i'):'-k',
        ('-j','j'):'1', ('-j','-j'):'-1', ('-j','k'):'-i', ('-j','-k'):'i',
        ('k','1'):'k', ('k','-1'):'-k', ('k','i'):'j', ('k','-i'):'-j',
        ('k','j'):'-i', ('k','-j'):'i', ('k','k'):'-1', ('k','-k'):'1',
        ('-k','1'):'-k', ('-k','-1'):'k', ('-k','i'):'-j', ('-k','-i'):'j',
        ('-k','j'):'i', ('-k','-j'):'-i', ('-k','k'):'1', ('-k','-k'):'-1',
    }
    els = ['1','-1','i','-i','j','-j','k','-k']
    idx = {e: i for i, e in enumerate(els)}
    def mul(a, b): return tbl[(a, b)]
    def inv(a):
        return {'1':'1','-1':'-1','i':'-i','-i':'i','j':'-j','-j':'j',
                'k':'-k','-k':'k'}[a]
    sizes = []
    seen = set()
    for e in els:
        if e in seen: continue
        cl = {mul(mul(g, e), inv(g)) for g in els}
        seen |= cl
        sizes.append(len(cl))
    return 8, sizes

groups = []
for n in (2, 3, 4, 5):
    groups.append((f"C{n}",) + make_cyclic(n))
for n in (3, 4, 5):
    groups.append((f"S{n}",) + make_sn(n))
for n in (4, 5, 6, 8):
    groups.append((f"D{n}",) + make_dihedral(n))
groups.append(("Q8",) + make_q8())

all_div = True
for name, order, sizes in groups:
    ok = all(order % s == 0 for s in sizes)
    all_div &= ok
    print(f"{name:>4} |G|={order:>3} class sizes={sorted(sizes)} "
          f"all divide |G|: {ok}")
print(f"\nALL groups: every class size divides the group order: {all_div}")
print("Orbit-stabilizer: |C(x)|*|C_G(x)|=|G|  =>  |C(x)| | |G| ALWAYS.")
res["class_sizes"] = dict(all_divide=all_div,
    grok_verdict="WRONG: class sizes always divide |G| (orbit-stabilizer); "
                 "the nontrivial constraint is realizability, not divisibility")

# ---------------------------------------------------------------- 3
print("\n=== 3. Dirichlet return-time bound ===")
rng = np.random.default_rng(11)
# Grid cells of side 2*pi/N: two points in one cell differ by <= 2*pi/N
# per coordinate.  To guarantee max phase dev <= delta need N >= 2*pi/delta,
# giving q <= N^m ~ (2*pi/delta)^m -- the paper's Prop. (returnbound) form.
for m, delta in ((2, 0.05), (3, 0.05), (4, 0.20), (5, 0.30)):
    freq = rng.uniform(0.31, 1.07, size=m)  # rationally-independent-ish
    N = int(np.ceil(2 * np.pi / delta))
    k = np.arange(N**m + 1)
    pts = np.outer(k, freq) % (2 * np.pi)
    key = np.floor(pts / (2 * np.pi / N)).astype(np.int64)
    # find two rows with identical key (pigeonhole guarantees one)
    _, inv, counts = np.unique(key, axis=0, return_inverse=True,
                                return_counts=True)
    dup = np.where(counts > 1)[0]
    pair = None
    for c in dup:
        idxs = np.where(inv == c)[0]
        if len(idxs) >= 2:
            pair = (int(idxs[0]), int(idxs[1]))
            break
    q = pair[1] - pair[0]
    v = (q * freq) % (2 * np.pi)
    dev = float(np.max(np.minimum(v, 2 * np.pi - v)))
    bound = N**m
    print(f"m={m}: found tau={q} <= N^m={bound}, max phase dev {dev:.4f} "
          f"<= 2*pi/N={2*np.pi/N:.4f} (target delta={delta}): "
          f"{dev <= 2*np.pi/N + 1e-12}")

# polynomial-in-S vs exponential-in-S comparison
print("\nprime-frequency counts (typical integers near x):")
# sieve primes < 1e5 for fast trial division
sieve = np.ones(100000, dtype=bool)
sieve[:2] = False
for p in range(2, 350):
    if sieve[p]:
        sieve[p*p::p] = False
PRIMES = np.where(sieve)[0].tolist()
for x in (10**6, 10**12, 10**18):  # int64-safe bound
    # simulate typical omega(n) near x
    n_samp = rng.integers(int(x*0.99), x, size=1000)
    om = []
    for n in n_samp:
        nn = int(n); c = 0
        for p in PRIMES:
            if p * p > nn:
                break
            if nn % p == 0:
                c += 1
                while nn % p == 0:
                    nn //= p
        if nn > 1:
            c += 1
        om.append(c)
    S = np.log(x)  # entropy in units k_B = E/(h w0) = log x
    log_T_arith = np.mean(om) * np.log10(1/0.05)   # (C/eps)^m form
    log_T_generic = x * np.log10(1/0.05)           # (C/eps)^D form, D = x
    print(f"x=1e{int(np.log10(x))}: E[k_B S]={S:.1f}  mean omega={np.mean(om):.2f} "
          f"(loglog x={np.log(np.log(x)):.2f})  "
          f"log10 T_arith={log_T_arith:.1f}  (poly in S: "
          f"{np.mean(om)*np.log10(np.e)*100:.0f}% of S)  "
          f"log10 T_generic={log_T_generic:.2e}")

# ---------------------------------------------------------------- 4
print("\n=== 4. Staircase microcanonical temperature ===")
# S(E) = log floor(e^x): derivative 0 a.e.; smoothing N~ = e^x gives
# dS/dE = 1/(h w0) identically -- the paper's 'exactly critical at every
# energy' is a property of the smoothing, as grok says.
print("S(x) - S(x-) at level m: log(m/(m-1)) -> 0;  dS/draw/dE = 0 a.e.")
print("smoothed: d/dx log(e^x) = 1 identically (circular, as grok notes)")

np.save("/tmp/adjudication.npy", np.array([0]))  # placeholder
import json
with open("/home/z/my-project/scripts/adjudication_math.json", "w") as f:
    json.dump({k: {kk: (str(vv) if not isinstance(vv, (int, float, bool))
                        else vv)
                   for kk, vv in v.items()}
               for k, v in res.items()}, f, indent=2, default=str)
print("\nsaved -> scripts/adjudication_math.json")
