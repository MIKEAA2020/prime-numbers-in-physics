# Pilots — the register's cheapest attacks, executed

Companion numerical studies for the paper's conjecture register (§10). Both pilots were
run on the *exact* systems defined in the paper's LaTeX (same couplings, same seeds,
same truncations), so every number is reproducible from these scripts.

## `c4_eth/` — C4 (Cascade/ETH) and the C5 proxy on the prime lattice

**System**: `H_tot = H_P + H_W + H_hop` on truncations of the arithmetic Hilbert space
(`d` active prime modes, occupation cap `K`, dimension `D = (K+1)^d`), exactly as in
`sec_dynamics.tex` (Eq. `eq:fullH`).

| Stage | Script | Scale | Method |
|---|---|---|---|
| Pilot | `c4_eth_pilot.py`, `c4_eth_pilot2.py`, `c4_pilot3_pr.py` | D = 625–4096 | dense `eigh` |
| **Scaled** | `c4_scaled_eth.py` (+ `run_c4_scaled.sh` driver) | **D ≈ 10⁴–10⁵** | sparse CSR assembly, shift-invert Lanczos interior windows (`splu` + `eigsh`), restarted-Lanczos Krylov time evolution |
| **Kinetic completion** | same worker, `--V` flag (+ `run_c4_kinetic.sh`, `c4_kinetic_selftest.py`, `c4_kinetic_figures.py`) | D ≈ 10⁴–10⁵ | one-term density-assisted hopping; diagonal-pivot shift-invert (residual-certified) |

Diagnostics: level-spacing ratio ⟨r⟩ (Poisson 0.3863 / GOE 0.5359 — the **C5 proxy**),
ETH fluctuation σ_ETH of local occupation observables with microcanonical reference,
participation ratios, diagonal-ensemble vs microcanonical equilibration, quartic
completion `U·Σ n_i n_j` and kinetic completion `V·Σ (n_i+n_j)(a_i†a_j + h.c.)`
(dose–response and D-scaling), weak-coupling control with σ-quantile sweep.

The sparse pipeline was validated against the dense pilot (extreme-eigenvalue agreement
2·10⁻¹⁴; ⟨r⟩ = 0.537 vs 0.538 at D = 4096; PR/D 0.26 vs 0.27).

**Headline results** (see `results/c4_scaled_results.json`, `results/scaled/summary.txt`
and the paper's Remark on numerical status):

| diagnostic | result |
|---|---|
| Level statistics (C5 proxy) | GOE, ⟨r⟩ = 0.51–0.54, at every scale D = 625 → 2.4·10⁴ (generic coupling) |
| Normalized ETH fluctuation | σ_ETH/std(a_j) = 0.94–0.99, **flat in D** (all couplings) |
| Equilibration memory | \|diag − micro\|/K ≈ 6–24%, flat from D = 10⁴ to 10⁵ (Krylov tier) |
| Quartic completion (U Σ n̂ₚn̂q) | monotone **localization**: ⟨r⟩ 0.514 → 0.502 → 0.387 (U = 0 → 0.5 → 2); PR/D 0.18 → 0.03 → 0.001 |
| Weak-coupling control | PR/D → 10⁻⁴, σ_ETH inflated ×10, \|diag − micro\|/K ≈ 0.5–1 (frozen) |
| Cost | dense eigh: 8 s @ D = 4096 (D^2.4 scaling); sparse window tier: minutes, LU-fill-capped at D ≈ 2.4·10⁴; Krylov tier: minutes, reached D = 104,976 |

The bare `H_tot` is quasi-single-particle on the exponent lattice (no quartic sector):
delocalized but not ergodic. The diagonal quartic completion does **not** rescue
thermalization — it localizes. The kinetic completion was tested next (below) and is
the first to equilibrate.

### Kinetic (density-assisted hopping) completion — `--V`

**Term**: `H_kin = V Σ_{p<q} (n̂_p + n̂_q)(a_p† a_q + a_q† a_p)` — quartic yet
off-diagonal, `N̂_tot`-preserving; validated against a first-principles dense assembly
to 10⁻¹⁵ (`c4_kinetic_selftest.py`: identity, Hermiticity, commutator, non-quadratic
effective coefficients). Effective dose is occupation-weighted, ~ `V·K²`.

**Dose-response at the U-family platform (d4K11, D = 20736, seed 7):**

| coupling | ⟨r⟩ | σ_ETH/std | PR/D | evolve \|diag−micro\|/K (τ) |
|---|---|---|---|---|
| V = 0 (anchor) | 0.581 | 0.90 | 0.238 | 0.103 (202)¹ |
| V = 0.1 | 0.493 | 0.94 | 0.218 | 0.178 (63) |
| **V = 0.3** | **0.518** | 0.96 | **0.136** | **0.004 (22)** |
| V = 1.0 | 0.412 | 0.97 | 0.046 | 0.032 (7) |
| U = 0.5 | 0.502 | 0.94 | 0.029 | 0.153 (44) |
| U = 2.0 | 0.387 | 0.97 | 0.001 | 0.796 (11) |

¹ bare d4K11 evolve from the scaled program (V = U = 0).

**Findings** (details and per-config JSONs in `results/scaled/`;
`c4_kinetic_results.json`, `fig_c4_kinetic.png`):

1. **First equilibration in the program** — at V ≈ 0.3 the Krylov trace from
   `|K e_d⟩` settles at the microcanonical value (\|dev\|/K = 0.0039; bare 0.10,
   quartic 0.81) with residual fluctuations 0.064.
2. **Dose phenomenon** — V = 0.1 plateaus away from micro (0.178, the bare value);
   equilibration is optimal near V·K² ≈ 36; V = 1 localizes (⟨r⟩ → 0.41, PR/D → 0.05).
3. **σ-quantile sweep (weak coupling, d3K28)**: ⟨r⟩ spans 0.42–0.56, non-monotone
   (q = 0.15 dip 0.4361 reproduced exactly on re-run); generic coupling is flat
   0.505–0.514 across quantiles; the weak median is direction-dependent (d = 3:
   0.527; d = 4: 0.441). PR/D ≈ 10⁻⁴ is the robust weak diagnostic.
4. **Strong-ETH leg still flat** — σ_ETH/std = 0.94–0.99 at every kinetic dose and
   scale; the scaling falsifier remains unfalsified on the eigenstate leg while the
   equilibration leg now has positive evidence.

**Numerical note**: kinetic couplings destroy SuperLU diagonal dominance (default
partial pivoting triples fill: generic d3K28 257 s → timeout). The fix —
`diag_pivot_thresh = 0` (`--pivot diag`) — factors the same matrices in seconds
(3.1 s) and lifts the old LU ceiling; every window is certified by eigenpair
residuals ≤ 1.2·10⁻⁷, cross-checked against auto pivoting (d4K10: 0.5157 vs
0.5134, within SEM).

## `c9_chebotarev/` — C9 (Galois–gauge dictionary) protocol calibration

Three components, each < 30 s:
1. **Substrate verification**: Chebotarev densities for Q(i) (split/inert) and
   S₃ = Gal(Q(∛2)) (three conjugacy classes) at 10⁷ primes; Chebyshev bias calibration.
2. **Protocol calibration by Monte Carlo null**: common-group-order divisor fit
   (k ≥ 5 channels, N ≤ 360) — false-positive rates 27–29% at σ = 1%,
   0.3–0.7% at σ = 0.3%, < 0.3% at σ = 0.1%.
3. **Real-data demo**: S₃ table injection recovered exactly from ≥ 300 events/channel;
   the Z-pole branching table admits **no** common-N fit (χ² ≈ 4.9·10⁴) — the signature
   is absent below unification, consistent with C9.

**Verdict**: C9's cheapest attack is *calibration without purchase* — the instrument is
built and its discriminating regime quantified (≥ 5 channels, σ ≤ 0.3%,
|G| ≲ few·10²); the unification-scale data that could decide C9 does not exist.

## Reproducing

```bash
# C4 pilots (dense, < 1 min total)
python3 c4_eth/c4_eth_pilot.py
# kinetic-term validation (4 platforms, seconds)
python3 c4_eth/c4_kinetic_selftest.py
# C4 scaled (sparse; ~2 h total on 4 GB / 2 cores). The driver is resumable:
# each configuration runs as its own process with a wall-clock deadline, so it
# can be run in foreground chunks (re-invoke until scan.log ends with ALL_DONE).
bash c4_eth/run_c4_scaled.sh
# kinetic completion + sigma-quantile sweep (~2 h; resumable the same way)
bash c4_eth/run_c4_kinetic.sh
# matched-dose ladder + diagonal-ensemble confirmation (~2.5 h; groups:
# small mid large dense evolve ext/extloop; resumable the same way)
bash c4_eth/run_c4_ladder.sh small
# machinery validation (Lanczos-norm step size vs exact propagation,
# checkpoint/resume equivalence, dense diagonal ensemble; ~9 min)
python3 c4_eth/c4_extend_validation.py
# merge + figures
python3 c4_eth/c4_scaled_figures.py
python3 c4_eth/c4_kinetic_figures.py
python3 c4_eth/c4_ladder_figures.py
# C9 (< 30 s)
python3 c9_chebotarev/c9_chebotarev_pilot.py
```

Requirements: numpy, scipy, matplotlib. The scaled worker validates itself against
the dense pilot (exact eigenvalue agreement at D = 4096) and against dense `expm`
for the Krylov propagator (agreement to 10⁻¹³; norm drift ≤ 10⁻¹³ per trace).

## Matched-dose ladder (VK^2 = 36)

Holds the occupation-weighted effective coupling fixed while the truncation
widens, so the ETH scaling diagnostics are not confounded by the dose:

- **Window ladder** (`L36d3K*`, `L36d4K*`): sigma_ETH/std(a) flat at
  0.95-0.98 across D=3,375-59,319 (d=3) and D=4,096-20,736 (d=4); PR/D rises
  with D at fixed dose; the 4D window tier is LU-fill-limited beyond
  D=20,736.
- **Dense pairs** (D<=10^4): exact diagonal ensemble vs microcanonical vs
  finite-T Krylov plateau; the plateau equals the diagonal ensemble to
  0.005*K (dephasing identity verified), while the diagonal ensemble stays
  0.04-0.09*K from microcanonical with no closing trend.
- **Extended trajectory** (`d4K11V03x`): D=20,736, V=0.3, tau=0-300 in 9
  checkpointed chunks (a chunk boundary is an ordinary Lanczos restart;
  agreement with an independent step size: 2e-4 in the observable). Nested
  late-time averages saturate at diag ~ 4.40 vs micro 3.35; the tau<=22
  average (3.39, near micro) was a transient.

Artifacts: `figures/fig_c4_ladder.png`, `results/c4_ladder_results.json`,
`results/ladder_scan.log`, per-configuration `results/scaled/` files.

## Audit-response controls (label-scrambled diagonal + generic quantile sweep)

Controls for the null hypothesis "the diagonal's arithmetic arrangement is
irrelevant once the density of states and the graph are fixed"
(`--scramble`: permute the on-site energies among the vertices of the same
graph, preserving the exact diagonal multiset and every off-diagonal matrix
element):

- **Scramble pairs** (`res_*scr`): matched-dose level statistics are
  scramble-insensitive (r 0.518->0.512 at V=0.3; 0.509->0.502 matched) - the
  GOE band is graph-generic; the generic-family (V=0) delocalization is not
  (PR/D 0.238->0.113 at d=4; 0.182->0.015 at d=3, sigma_ETH 1.8->4.5): the
  arithmetic diagonal is a transport organizer, not a source of level
  repulsion.
- **Generic-coupling quantile sweep** (`res_d3K28gq*`): full eight-quantile
  sweep gives 0.464-0.540 (compression at the band edges); the earlier
  three-interior-quantile flatness (0.505-0.514) sampled only the flat middle.
- **Finite-size scaling** (`c4_audit_results.json`): 1/log D fits of
  <r>-r_GOE along the matched-dose ladders (pooled: -1.66/log D + 0.141);
  residuals large, limiting value unsettled in the computed range.

Artifacts: `figures/fig_c4_controls.png`, `results/c4_audit_results.json`,
per-configuration `results/scaled/` files, `adjudication_checks.py` (exact
math checks: counting-defect convergence, class-size divisibility on 12
groups, Dirichlet return-time bound, Erdos-Kac simulation ->
`results/adjudication_math.json`).

## Strong-ETH fluctuation scaling (absolute normalization)

The eigenstate fluctuation re-measured in absolute units
(`c4_strong_eth.py`): kappa = sigma_ETH / std_basis with
std_basis = sqrt(K(K+2)/12) the a-priori spread of the local occupation
over the (K+1)^d product basis, against two calibrated benchmarks
(B_count: Haar-random eigenstates in the basis shell the 350-state
eigen-window actually spans; B_frac: a fixed 5% quantile shell, the
D^{-1/2} strong-ETH scaling with the exact prefactor).

- **Decay**: kappa = 0.50 -> 0.29 along the d=3 matched-dose ladder
  (D = 3375 -> 59319): kappa ~ D^{-0.185 +/- 0.021} (n=9, R^2=0.92);
  D^{-0.222 +/- 0.003} along d=4 - two and a half times slower than the
  thermal D^{-1/2}. Exact full-spectrum diagonalizations reproduce the
  window protocol to <= 11% (fixed-fraction exponents -0.10 / -0.21).
- **Distance from the strong-ETH scaling grows**: kappa/B_frac rises
  4.6 -> 11.3 (d=3) and 4.6 -> 7.2 (d=4); kappa/B_count falls 15.0 -> 6.4
  (the protocol shell is not the entropy scale); effective
  random-combination dimension N_eff = N_shell/R^2 ~ 8 -> 23 vs shells of
  ~10^3 states.
- **The decay is arithmetic-organized**: label-scrambled controls at
  matched dose hold kappa flat at 0.43-0.46 while PR/D falls
  (0.082 -> 0.035; `res_*scr`, `win_*scr` in `results/scaled/`).
- **Slow-mode structure**: kappa*sqrt(PR) grows 8.5 -> 28 (support-uniform
  level sqrt(2)); within one median-energy window the eigenstate values of
  n_1 span [0.3K, 0.94K]; <r> shows no size trend (slope 0.013 +/- 0.020
  in log D, mean 0.500).

Artifacts: `figures/fig_c4_strongeth.png`,
`results/c4_strongeth_results.json`, `results/strongeth_summary.txt`,
per-configuration `results/scaled/` files (incl. the three scrambled
matched-dose windows).

## C9 pre-registered dictionary application

The Chebotarev dictionary protocol, frozen in
`review/c9_preregistration.md` (commit 9f30553, corrected rule) before the
fit was run, and applied once to the exhaustive five-channel Z-pole
branching table (`c9_prereg_application.py`):

- Statistic: T = min over N in [5,360], c_i | N, sum c_i = N (class
  equation, enforced by exact dynamic programming) of the chi-square; the
  DP is validated against brute-force enumeration (60 cases) and
  batch==single==backtrack to roundoff.
- Null: 5000 Dirichlet tables at the actual uncertainty pattern (median
  2.8e5, 5% quantile 2.9e4; false-positive rate at chi2_0.95(4) is 0/5000).
- **Decision: signature absent.** T_obs = 4.1e5 (best N=48,
  c=(24,2,3,3,16)) at the null's 59th percentile; per-channel exclusion
  depth 221/7/5/4/2.8 sigma (had/e/mu/tau/invisible); precision-inflation
  factor lambda = 208.
- **Power = 1.000** at the registered threshold for every injected truth
  table (N = 6, 36, 360) at current Z-pole precision (also at x1e-1,
  x1e-2, and the Z-factory statistical floor 3.3e-3): the absence is an
  exclusion over the whole registered range, not an under-powered null.
  Recovery of the group order is up to common factors (primitive
  representative).
- Sensitivity: the unconstrained N<=5000 variant of the earlier
  compatibility check returns chi2 = 4.9e4 (N=30), consistent with the
  constrained statistic.

Artifacts: `figures/fig_c9_prereg.png`,
`results/c9_prereg_results.json`, `results/prereg_summary.txt`,
`results/prereg_app.log`; protocol document `review/c9_preregistration.md`.

## c4_eth: factorization-free window tier and sector checks (residuals)

Two additions close the audit-adjudication residuals:

- `c4_kappa_krylov.py` - block Chebyshev subspace iteration on
  B = (H - c)^2 (c = median of the diagonal energies, the shift-invert
  target): low-pass Chebyshev T_M(xi(B)), xi(b) = 1 + 2(b_w - b)/(b_high
  - b_w), passband +-t sized by stochastic Lanczos quadrature (8-12
  probes x 360 fully reorthogonalized steps; the block cannot see past
  its own boundary), float32 filtering with a float64 polish, Rayleigh-
  Ritz after every sweep, every selected pair certified by ||Hv - wv||.
  Resumable in degree-chunks (state checkpoints after every chunk).
  Validation against the LU tier (results/c4_kappa_krylov_validation.json):
  eigenvalue sets identical to machine precision at D = 9.3e3 and 1e4
  (max |dlambda| <= 4e-11), kappa within 0.6% at D = 6.9e3, 289/350
  pairs certified at the near-ceiling D = 2.4e4 with kappa within 2.4%.
  Extension: L36d4K13 (D = 3.84e4, M = 3400) gives kappa = 0.250 with
  276/350 certified pairs at residuals <= 1.8e-6, <r> = 0.511 (GOE),
  PR/D = 0.148; the d=4 ladder reads 0.449 -> 0.367 -> 0.313 -> 0.250 and
  the four-point fit is kappa ~ D^{-0.255} against the thermal D^{-1/2},
  with the fixed-fraction benchmark distance still growing (7.2 -> 7.8).
  Cost ceiling: Chebyshev degree ~ ln(eps) R/(2t) with the radius R
  dose-pinned (~570 at VK^2 = 36 in d = 4; the fully occupied corners
  carry row sums proportional to VK^2 (d-1)), so the degree grows
  linearly in D at fixed protocol - the LU fill ceiling is replaced by a
  compute-degree ceiling about one rung higher.
- `c4_sector_checks.py` - numerical corroboration of the occupation-
  sector proposition: every sector block Hermitian to machine precision
  and within the row-sum norm bound ||H_kin^(S)|| <= |V|(d-1)S(S+1) for
  S <= 12 at d = 3,4; box-truncation exactness of sector-supported
  dynamics to 7e-15 across truncations (same seed -> same couplings);
  the walk control leaks out of the sector as H_W's non-conservation
  requires (results/c4_sector_checks.json, 28/28 checks).

Artifacts: `results/res_krylov_*.json`, `results/win_krylov_*.npz`,
`results/c4_kappa_krylov_results.json`,
`results/c4_kappa_krylov_validation.json`,
`results/c4_sector_checks.json`, `figures/fig_c4_strongeth.png`
(regenerated with the Krylov-tier point).

## Edge-window kappa stage + the k=7 variant (the K15/K17 leg)

The `--stage kappa` worker (edge window) complements `c4_kappa_krylov.py`
(the Chebyshev median-window tier, degree-walled at K13):

```bash
# upper-edge window at any grid (minutes, single process, residuals <= 1.3e-11)
python3 c4_eth/c4_scaled_eth.py --tag L36d4K17 --d 4 --K 17 \
    --V 0.1245675 --stage kappa
# matched-dose trajectory chunk (repeat with --resume)
python3 c4_eth/c4_scaled_eth.py --tag L36d4K17 --d 4 --K 17 \
    --V 0.1245675 --stage evolve --tau-max 100 --resume
```

- d=4 edge ladder (D=4,096-104,976): sigma_rel = 0.871/0.887/0.886/0.894/
  0.895/0.888 (FLAT); d=3: 0.839/0.835/0.838 (FLAT); edge sector
  Poisson-like (<r>_edge 0.38-0.43, PR/D 0.054->0.009).
- Median-window factorization-free routes measured as closed at these
  scales: ARPACK-fold (ncv 240/460/700: 0/160), ILU^2 LOBPCG (NaN),
  unpreconditioned LOBPCG (0.96/iter), soft filters (degree ~5e3).
- Matched-dose trajectories at the three largest grids: K13 tau=96 (secular
  climb 3.96->4.79 vs micro 3.956), K15 tau=44, K17 tau=36 (horizon-limited).
- C9 k=7: `c9_freeze_pdg.py` (frozen 2024 extract, committed pre-fit) +
  `c9_k7_variant.py` (null -> injection -> fit): no common-N table at the Z
  scale at seven channels (chi2 = 1394.68 vs 14.07; p = 0.032).
