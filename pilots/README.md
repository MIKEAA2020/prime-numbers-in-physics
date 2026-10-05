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
