# Review of §10 — The Consolidated Conjecture Register

**Scope**: `sec_register.tex` (§10 Conjecture Register + §11 Falsifiability) of
*prime_spectral_framework_rigorous_reconstruction.pdf*, cross-audited against
`sec_intro.tex` (C1), `sec_dynamics.tex` (C4 / `conj:cascade`), `sec_galois.tex`
(C9 / `conj:gut`), `sec_time.tex` (C3 / C11 hooks).

**Method**: line-level audit of grades, dependencies, and falsifiers; both
"cheapest attacks" were **executed** as pilots (C4: ETH simulations on finite
truncations, D = 625–4096; C9: Chebotarev dictionary check — substrate to 10^7
primes, protocol calibrated by Monte Carlo, real-data demo).

---

## 1. Executive verdict

| Claim under review | Verdict |
|---|---|
| C1 is the root of the register | **Confirmed** on the physical plane; recommend a two-plane DAG (mathematical attackability vs. physical dependency) — C4/C5 survive C1's failure as autonomous mathematical problems |
| ETH simulations of C4 are the cheapest attack | **Confirmed by execution** (full 6-config scan < 1 min laptop) — but C4 is **mis-typed as stated** (no interaction sector) and its falsifier cell must be restated as a finite-size scaling criterion |
| Chebotarev dictionary check (C9) is the cheapest attack | **Confirmed by execution** (< 30 s for all three components) — but the check is **calibration without purchase**: the protocol is validated and its discriminating regime quantified (≥5 channels, σ ≤ 0.3%, \|G\| ≲ few×10², common-N divisor fit), while the conjecture's own hook needs unification-scale data that does not exist |

**Bonus**: the C4 simulations deliver the C5 proxy for free — generic couplings
give GOE level statistics (⟨r⟩ = 0.515–0.548 vs. GOE 0.5359); weak-coupling
control gives exactly Poisson (0.388). The "banded incommensurate system" claim
of §11.2 attack path 2 is verified at pilot scale.

---

## 2. Register hygiene (internal defects to fix)

1. **Missing dependencies column.** The preamble promises "Dependencies list
   register entries whose failure collapses the entry", but the longtable has
   only ID / Statement / Grade / Falsifier. Dependencies appear piecemeal
   inside falsifier cells (C7: "constrained by C1, C4"; C12: "tethered to C4").
2. **C2 is orphaned** in the stated depth ordering
   (C1 ⇒ {C3,C5,C6} ⇒ {C4,C7,C8} ⇒ {C9,C10,C11} ⇒ C12) — the arithmetic
   cutoff is never placed. It is downstream of C1 and feeds the recurrence
   phenomenology; it belongs in layer 2 or explicitly orthogonal.
3. **The depth ordering overstates C4's downstream-ness.** C4's statement is
   well-posed without C3/C5/C6 (the arithmetic sector and H_tot exist
   unconditionally). Its layer-2 dependency is interpretive, not logical —
   which is precisely why C4 is attackable now.
4. **Hidden cross-layer edges**: C11 ← C3 (its falsifier invokes C3's horizon
   temperature), C10 ← C4 (ratchet compounds along the cascade).
5. **Genuine internal error** (sec_dynamics, "Conservation structure" remark):
   the claim "H_W conserves N̂_tot (each M_p changes one occupation by ±1)" is
   false — changing one occupation by ±1 changes the *total* by ±1 — and is
   contradicted by the paper's own nucleation proposition
   (d⟨N̂_tot⟩/dτ = 2τΣg_p²/ℏ² > 0). Corrected hierarchy: H_P conserves
   everything; H_hop conserves N̂_tot but not N̂; **H_W conserves neither — it
   is the nucleation/entropy engine**. This has register weight: C10's ratchet
   lives in the non-conserving sector.
6. **Typo-level slip** (proof of Prop. wellposed): the displayed commutator's
   second term should be n(1 − 1/p)|n/p⟩, not (p−1)n|n/p⟩ (sign/coefficient
   slips; the conclusion [H_tot, N̂] ≠ 0 is unaffected).
7. **Grade asymmetries**: C1's "partial evidence" is a single reported program
   [hartnollyang2026]; C3's grade-A cites mismatch risk (a falsifier) as if it
   were positive evidence.

---

## 3. C4 pilot — findings (download/pilot_c4_eth/)

System exactly as defined in sec_dynamics: H_tot = H_P + H_W + H_hop on
truncations (d modes, cap K), generic couplings (seed-controlled).

| config | D | ⟨r⟩ | σ_ETH | micro-RMSE | diag vs micro |
|---|---|---|---|---|---|
| d4K4 | 625 | 0.515 | 0.540 | 0.533 | — |
| d5K3 | 1024 | 0.548 | 0.437 | 0.263 | — |
| d4K6 | 2401 | 0.531 | 1.029 | 0.561 | 3.00 vs 1.82 |
| d5K4 | 3125 | 0.526 | 0.547 | 0.434 | 2.00 vs 0.91 |
| d4K7 | 4096 | 0.538 | 1.282 | 0.574 | — |
| d6K3 | 4096 | 0.536 | 0.450 | 0.211 | — |
| d5K4 weak | 3125 | **0.388** | 1.150 | 0.774 | 0.44 vs 0.91 |
| d5K4 + U | 3125 | 0.537 | 0.911 | 0.965 | 1.99 vs 0.87 |

Participation-ratio ladder (d5K4): H_P 0.0003 → +H_W (Stark chains) 0.049 →
full H_tot 0.27 → +quartic U 0.058 → weak 0.0005.

**Findings**:
1. **C5 proxy positive** (GOE at generic coupling; Poisson control).
2. **ETH fails at pilot scale for a structural reason**: H_tot is (essentially)
   a **single-particle tight-binding problem on the exponent lattice ℤ^d** —
   H_P is a separable linear ramp; H_W is separable per-axis adjacency
   (Wannier–Stark chains: the walk alone does *not* un-freeze the cascade;
   propagation along the p-axis is Stark-suppressed when g_p ≲ ln p, i.e.
   blocked along large-prime modes at paper-typical couplings); H_hop is
   quadratic (a†a); **no quartic interaction exists anywhere in H_tot**.
   Delocalization without ergodicity: PR/D = 0.27, yet eigenstate fluctuations
   of local occupation observables are O(1) and the diagonal ensemble retains
   O(1) memory (2.0 vs 0.91 microcanonical). Dephasing itself is fast
   (time-averaged fluctuations ~ 0.03–0.05).
3. **The minimal Bose–Hubbard completion (U Σ n̂_i n̂_j) does not rescue ETH at
   pilot scale** — it *localizes* (PR/D drops to 0.058; ⟨r⟩ → 0.446 at U = 2).
   If ETH holds for the completed system, it lives at much larger D.
4. **Cost measured**: 8 s dense diagonalization at D = 4096; full scan < 1 min.

**Required repair to C4**: (i) specify an interacting completion (quartic term
or equivalent) — as stated the thermalization conjecture is mis-typed for a
quasi-quadratic object; (ii) restate the falsifier as a finite-size *scaling*
criterion (σ_ETH(D) decay; |diag − micro| → 0 along a specified truncation
sequence) — an E → ∞ statement cannot be falsified by finite-D simulation, so
the present cell ("failure of equilibration in simulations falsifies") is both
too strong and too weak; (iii) keep the pilot data as the baseline.

---

## 4. C9 pilot — findings (download/pilot_c9_chebotarev/)

1. **Arithmetic substrate verified**, both abelian and non-abelian:
   Q(i) split/inert at 10^7: 0.49984 / 0.50016 (χ² = 0.07, p = 0.79);
   S₃ = Gal(Q(∛2)) types at 10^7: (111) = 0.16640, (21) = 0.50014,
   (3) = 0.33346 vs 1/6, 1/2, 1/3 (χ² = 0.3, p = 0.85).
2. **Convergence + bias calibration**: at X = 10³ the (111) fraction is 13% off
   its density; percent-level needs π(X) ~ 10⁵–10⁶. The Q(i) counts carry the
   Chebyshev bias (inert − split = +218 at 10⁷, persistent and structured).
   A finite-scale dictionary check must model both 1/√N noise and arithmetic
   bias, or it is unfalsifiable at every finite scale.
3. **Protocol calibrated** (the constructive fix): the weak form (each ratio
   near some rational) is nearly vacuous — rationals are dense. The strong
   form requires a **common group order N** with class sizes c_i | N fitting
   all channels simultaneously. Monte Carlo null calibration (k = 5 channels,
   N ≤ 360):
   - σ = 1%: FPR 27–29% (vacuous);
   - σ = 0.3%: FPR 0.3–0.7%;
   - σ = 0.1%: FPR < 0.3%.
   The divisor constraint (class sizes divide |G|) is what saves the test;
   without it one needs |G|·σ ≲ 0.3.
4. **Injection (power)**: the S₃ table {1/6, 1/2, 1/3} is recovered exactly
   (N = 6, c = {1, 3, 2}) from ≥ 300 events per channel.
5. **Real-data demo**: the Z-pole branching table (5 channels, PDG errors)
   admits no acceptable common-N divisor fit (best χ² = 4.9 × 10⁴). The
   signature is absent at the Z scale — consistent with C9 being a
   unification-scale claim — and the check runs in seconds.
6. **Honest limit**: the cheap attack validates and calibrates the protocol,
   but the conjecture's own hook (unification-scale branching statistics) is
   data we do not have. C9's cheapest attack is confirmed cheap but is
   *calibration without purchase*: it specifies what would decide C9
   (≥5 channels, sub-0.3% precision, |G| ≲ few hundred, common-denominator
   structure across independent tables) and proves current data cannot.

**Required repair to C9**: replace the falsifier cell with the calibrated
protocol above; keep proton-decay absence (§11.1 item 1) as the cleanest dated
falsifier.

---

## 5. Recommended priority order for the register's next revision

1. Fix the conservation-structure remark (genuine error, contradicts the
   nucleation proposition).
2. Re-type C4 with an interacting completion + scaling falsifier; cite pilot
   baselines (this review, §3).
3. Re-specify C9's falsifier with the calibrated common-N protocol (§4).
4. Add the promised dependencies column; draw the two-plane DAG; place C2.
5. Scale the ETH program to D ~ 10⁴–10⁵ with sparse eigensolvers
   (interior windows) — still laptop-scale; the C5 proxy comes free.

---

*Artifacts*: `download/pilot_c4_eth/` (fig_c4_eth.png, fig_c4_structure.png,
c4_results.json, c4_results_interacting.json, per-config npz),
`download/pilot_c9_chebotarev/` (fig_c9_chebotarev.png, c9_results.json),
scripts in `/home/z/my-project/scripts/` (c4_eth_pilot.py, c4_eth_pilot2.py,
c4_pilot3_pr.py, c4_figures.py, c9_chebotarev_pilot.py, c9_figures.py).

---

# Addendum: Task 5 — the kinetic completion pass (C4) and the σ-quantile sweep

*Session date: 2026-10-05. One-term addition to `c4_scaled_eth.py`, executed at the
same laptop scale; all artifacts in `download/pilot_c4_eth_scaled/` (tags below),
figures `fig_c4_kinetic.png` (new, 4 panels) and `fig_c4_scaled.png` (regenerated,
dose panel extended), machine summary `c4_kinetic_results.json`.*

## A. The kinetic (density-assisted hopping) completion — C4's real candidate, tested

**Term**: `H_kin = V Σ_{p<q} (n̂_p + n̂_q)(a_p† a_q + a_q† a_p)` — quartic yet
off-diagonal, `N̂_tot`-preserving, matrix elements `V(k_p+k_q)√((k_p+1)k_q)`.
Validated against a first-principles dense assembly to 10⁻¹⁵ (Hermitian,
`[H_kin, N̂_tot] = 0` exactly, non-quadratic effective coefficients —
`c4_kinetic_selftest.py`, 4 platforms, all PASS).

**Dose-response, identical platform as the U-family (d4K11, D = 20736, seed 7):**

| coupling | ⟨r⟩ | σ_rel | PR/D | evolve: \|dev\|/K (τ) |
|---|---|---|---|---|
| V = 0 (anchor) | 0.581 | 0.898 | 0.238 | 0.103 (202)* |
| V = 0.1 | 0.493 | 0.942 | 0.218 | 0.178 (63) |
| **V = 0.3** | **0.518** | 0.962 | **0.136** | **0.004 (22)** |
| V = 1.0 | 0.412 | 0.971 | 0.046 | 0.032 (7) |
| U = 0.5 | 0.502 | 0.944 | 0.029 | 0.153 (44) |
| U = 2.0 | 0.387 | 0.974 | 0.001 | 0.796 (11) |

\* bare d4K11 evolve (V = U = 0), recorded in the scaled program.

**Findings**

1. **First equilibration in the program.** At V ≈ 0.3 the Krylov trace from
   `|K e_d⟩` settles on a plateau *at* the microcanonical value: |diag−micro|/K =
   0.0039 (vs 0.10 bare, 0.81 quartic), residual fluctuations 0.064 over the
   plateau, norm drift 2.7·10⁻¹⁴. The equilibration leg of C4 now has positive
   accessible-scale evidence — the arrow-of-time engine works for this completion.
2. **Dose phenomenon, not monotone onset.** V = 0.1 (longer horizon, τ ≤ 63)
   plateaus *away* from micro (0.178 ≈ bare); V = 1.0 is transient/truncated.
   Equilibration-to-microcanonical is optimal near V·K² ≈ 36.
3. **Occupation-weighted coupling.** Effective dose is V·K²: fixed V = 0.3 is mild
   on d4K11 (K = 11) but strong on d3K28 (K = 28, V·K² ≈ 235) where it localizes
   (⟨r⟩ = 0.364, PR/D = 0.016, frozen evolve). The matched-dose 3D point (V = 0.05,
   V·K² ≈ 39) is intermediate: ⟨r⟩ = 0.474, PR/D = 0.123.
4. **Strong-ETH leg still flat.** σ_rel = 0.94–0.99 at every kinetic dose and every
   scale (D = 10⁴–2.4·10⁴, four truncation directions; evolve tier to 10⁵
   horizon-limited by the Gershgorin-inflated step size: τ = 22 → 15 → 6 → 2 as
   D = 2·10⁴ → 10⁵). The scaling falsifier rejects nothing yet: eigenstate
   fluctuations do not decay for bare, quartic, or kinetic.
5. **Localization contrast.** PR/D: kinetic decays monotonically in V but stays
   10–100× above the quartic family; strong dose localizes both, the quartic at
   10⁻³, the kinetic at 5·10⁻².

**Engineering discovered en route (now in the corrections log):** the kinetic
couplings destroy diagonal dominance, and SuperLU's default partial pivoting
triples the shift-invert fill (generic d3K28: 257 s → >240 s timeout at V = 0.3).
`diag_pivot_thresh = 0` (diagonal pivoting on the symmetric pattern) restores
factorization in seconds (d3K28: 3.1 s) — this also lifts the old LU ceiling
(the d4K11 U = 0 window, previously impossible, now factors in 56 s). Every window
is certified by eigenpair residuals ≤ 1.2·10⁻⁷, with a pivot-mode cross-check
(d4K10: auto 0.5157 vs diag 0.5134, within SEM).

## B. The σ-quantile sweep — the weak-coupling ⟨r⟩ protocol note, sharpened

Weak control (g₀ = 0.05, h₀ = 0.03, d = 3, K = 28, D = 24389, k = 350 levels per
window), σ-quantile swept over the whole DOS:

| q | 0.02 | 0.10 | 0.15 | 0.25 | 0.50 | 0.75 | 0.90 | 0.98 |
|---|---|---|---|---|---|---|---|---|
| ⟨r⟩ | 0.488 | 0.531 | 0.436 | 0.556 | 0.527 | 0.422 | 0.421 | 0.418 |

- **Non-monotone, DOS-structured**: the q = 0.15 dip (0.4361) is reproduced exactly
  on independent re-run (same seed/k/ncv) — density-of-states cluster gaps, not
  solver noise. The earlier "0.44–0.53 window-placement-sensitive" note is
  superseded: the full curve spans 0.42–0.56.
- **Generic control is flat**: d3K28 at q = 0.05/0.50/0.95 → 0.511/0.514/0.505.
  Window-robustness at generic coupling, window-*dependence* at weak coupling.
- **Direction dependence**: the weak *median* value itself is d-dependent
  (d = 3: 0.527; d = 4 at D = 20736: 0.441).
- **Register consequence**: any protocol claim about weak-coupling statistics must
  pin quantile and direction; PR/D ≈ 10⁻⁴ (frozen) is the only robust
  weak-coupling diagnostic. Folded into the C4 falsifier cell and
  Remark rem:numerics(a); self-audit row appended to the corrections log.

## C. Paper changes (recompiled, 41 pp body + cover, 0 overfull, 0 undefined refs)

- `conj:cascade` restated with both completions (eq:completions): diagonal
  `U Σ n̂_p n̂_q` and kinetic `V Σ (n̂_p+n̂_q)(a_p†a_q + h.c.)`.
- `rem:numerics`: four attack programs; (a) sweep-folded level statistics; new (d)
  with the full kinetic verdict and the honest dose/horizon qualifications; pivot
  note with residual certification.
- Register C4 row: H_tot^(U,V), executed kinetic evidence, quantile protocol note;
  §11.2 attack path 1 rewritten with the executed verdict.
- Corrections log: two new self-audit rows (sweep supersession; LU-ceiling
  restatement). Notation table: H_kin(V) added.

## D. What remains cheapest, now

1. **Strong-ETH leg**: the kinetic completion at matched dose (V·K² ≈ 36) across a
   *wider D ladder* (d4K9 → d4K13 windows; the diag-pivot path makes this
   minutes-per-config) — does σ_rel ever bend down?
2. **Horizon extension for the equilibration leg**: longer-deadline Krylov traces
   (or Chebyshev trace filtering) at V ≈ 0.3 to confirm the plateau is the diagonal
   ensemble, not a transient.
3. C9 dictionary check unchanged (no new physics input this pass).

---

# Task 8 — C9 pre-registered application; strong-ETH flatness resolved

## A. C9: from calibrated protocol to pre-registered, powered application

- Protocol frozen in `review/c9_preregistration.md` (commit d3b1160; decision-rule
  direction corrected in 9f30553 *before* the fit was run) — statistic, data,
  null, decision rule, truth tables, sigma scenarios, interpretation policy.
- Statistic strengthened: class-equation constraint sum c_i = N (the earlier fit
  left the c_i unconstrained — an analyst degree of freedom); exact DP minimization,
  brute-force validated (60 cases), batch==single==backtrack to roundoff.
- Execution: null 5000 Dirichlet tables at the Z uncertainty pattern (median
  2.8e5, q05 2.9e4, FPR at chi2_crit 0/5000); T_obs = 4.1e5, p = 0.59 ->
  ABSENT; power 1.000 at the registered threshold for N = 6/36/360 at *current*
  precision (0.90 at the chi2_crit variant = the Prob(chi2_5 <= 9.49) floor);
  per-channel exclusion 221/7/5/4/2.8 sigma; lambda = 208; primitive-N recovery.
- Verdict upgrade: "compatibility, not confirmation" -> "exclusion at the Z
  scale with unit power over the registered range; frozen prospective protocol
  for precision tables". Residual: the confirmatory content must come from
  unification-scale data; the k=7 granularity variant deferred (needs a frozen
  PDG extract).

## B. C4 strong-ETH leg: the flatness was a normalization artifact; the
   absolute diagnostic decays too slowly

- The reported flatness was the RATIO sigma_ETH/std(a) — window-width-dependent
  (compares fluctuation to the window's own spread incl. trend), not an ETH
  scaling test.
- Absolute diagnostic kappa = sigma_ETH/std_basis: 0.50 -> 0.29 (d=3 ladder,
  D 3375 -> 59319), kappa ~ D^{-0.185 +/- 0.021} (n=9, R^2=0.92);
  D^{-0.222 +/- 0.003} (d=4); dense tier validates the window protocol
  (<= 11%) and gives fixed-fraction exponents -0.10 / -0.21.
- Benchmarks (exact, from rebuilt shells): B_frac (5% shell, D^{-1/2}
  strong-ETH scaling) — kappa/B_frac GROWS 4.6 -> 11.3 (d=3), 4.6 -> 7.2 (d=4);
  B_count (protocol shell, ~10^3 states) — kappa/B_count falls 15.0 -> 6.4;
  N_eff = N_shell/R^2 ~ 8 -> 23 (D^{0.3}): eigenstates are random
  combinations of ~10 states, not ~10^3.
- Structure: kappa*sqrt(PR) grows 8.5 -> 28 (support-uniform level sqrt(2));
  a1 spans [0.3K, 0.94K] in one window — the slow mode; scrambled matched-dose
  controls hold kappa flat 0.43-0.46 while PR/D falls 0.082 -> 0.035: the
  decay is arithmetic-organized. <r>: no size trend (0.013 +/- 0.020).
- Register update: strong-ETH leg now "quantitative negative evidence at
  accessible scales" (was: flat/unfalsified); falsifier criterion restated as
  approach-to-thermal-scaling. New figure fig_c4_strongeth.png; paper 47 pp.

## C. Residual open items after this task

1. Math/physical falsifier separation in §11 only partial (unchanged).
2. Infinite-volume self-adjointness of the kinetic completion (unchanged).
3. C9 k=7 Z-granularity variant needs a frozen PDG extract (protocol update).
4. kappa at D > 6e4 (window tier LU-limited); a Krylov-tier estimator of the
   eigenstate fluctuation would extend the ladder.

# Task 9: the three residuals (falsifier split, self-adjointness, Krylov kappa)

## A. Math/physical falsifier separation (residual 1)

- Register falsifier column typed: M (proof / certified computation),
  P (measured data), M/P; legend in the section 10 preamble, markers in
  every row, closing observation updated (8 of 12 entries M-decidable).
- New section 11 subsection "Falsifier classes" (sec:classes): class
  definitions (noiseless/repeatable vs statistical/one-shot), a 12-row
  classification table (entry / class / decisive instance / uncertainty),
  and the structural observation that the framework's falsifier surface is
  predominantly mathematical while the physical surface is concentrated,
  dated, and pre-registered.
- New subsection "Physical test programs" (sec:physical): proton decay
  (dated), unification-scale precision branching (frozen protocol), CMB
  low-entropy statistics (C7/C8), scale identification (C11 input side) -
  each with its data source and decision instrument; the mathematical
  programs subsection renumbered (sec:mathprograms). Assessment updated.

## B. Infinite-volume self-adjointness (residual 2)

- Prop wellposed repaired: a_p^dag a_q is unbounded on l^2(F) (matrix
  elements ~ occupation); the proof route is now the occupation-sector
  decomposition, not a boundedness claim, and the domain statement is the
  closure of H_P + H_hop (Kato-Rellich with bounded H_W only).
- New Proposition (prop:sector, occupation sectors): (i) H_nc^(U,V) =
  H_P + H_U + H_hop + H_kin commutes with N_tot and the outside-mode
  occupations; orthogonal direct sum of finite Hermitian blocks of
  dimension C(S+d-1, d-1); the kinetic block is Hermitian by bond-reversal
  weight invariance ((n_p + n_q) commutes with the hop); row-sum norm
  bound ||H_kin^(S)|| <= |V|(d-1)S(S+1). (ii) Essential self-adjointness
  on the finitely supported configurations; H_tot^(U,V) self-adjoint for
  every U, V (Kato-Rellich, relative bound 0). (iii) Box truncations exact
  on contained sectors (H_W = 0); Trotter-Kato uniform strong convergence
  with the walk. Proof sketch + numerical corroboration (28/28 checks,
  c4_sector_checks.py: Hermiticity 0.0e+00, norm bound satisfied with the
  expected slack, box-exactness 7e-15, walk control leaks).
- New Remark (rem:modecount): the d -> infinity limit is singular - the
  hops reach infinitely many unoccupied modes with matrix elements
  sqrt(k_q) >= 1, so a finite mode cutoff is an ingredient of the
  conjecture, not an optional regularization.

## C. Krylov-tier kappa estimator (residual 4 of task 8)

- c4_kappa_krylov.py: block Chebyshev subspace iteration on (H-c)^2,
  passband by stochastic Lanczos quadrature (block-independent - the Ritz
  count cannot see past the block boundary), float32 filtering + float64
  polish, residual certification, resumable degree-chunk checkpoints.
- En-route engineering findings: the boundary of a contiguous interior
  block never converges (selection is converged-only); the Lanczos count
  probe needs ~360 steps at relative band widths ~1/200 (100 steps bias
  +30-70%, 250 steps +10%, 360 steps < 2% vs dense ground truth); the
  float32 residual floor grows with ||H|| sqrt(M) x amplification
  contrast, so the discovery phase is count-based (span inclusion) and
  only the polish phase certifies; the spectral radius is dose-pinned
  (R ~ 570 at VK^2 = 36, d = 4: fully occupied corners), which sets the
  degree wall.
- Validation (4 platforms vs LU): machine-precision eigenvalue sets at
  D = 9.3e3, 1e4 (max |dlambda| <= 4e-11), kappa ratio 1.006 at 6.9e3,
  289/350 certified at 2.4e4 with kappa within 2.4% (central-subset bias
  measured, not assumed).
- Extension: L36d4K13, D = 3.84e4 (first LU-infeasible 4D point), M = 3400,
  14 sweeps: kappa = 0.250 (276/350 certified, resid <= 1.8e-6, <r> =
  0.511, PR/D = 0.148). d=4 ladder 0.449 -> 0.367 -> 0.313 -> 0.250;
  four-point fit kappa ~ D^{-0.255} (3-point -0.222); benchmark distance
  7.2 -> 7.8. Subset-bias-corrected kappa ~ 0.256. The slow decay
  persists past the LU ceiling.
- Cost ceiling: total filter work ~ ln(eps) R/(2t) block-matvecs; at fixed
  dose R is constant and t ~ 1/D, so the degree grows linearly in D - the
  LU fill ceiling (2.1e4 in d=4) is replaced by a compute-degree ceiling
  ~ one rung higher (hours per configuration here). K15/K17 4D and K42+ 3D
  remain beyond this platform's budget; the machinery is in place.

Paper: 51 pp body (0 overfull, 0 undefined, 330 links); manuscript.tex
regenerated and verified to compile identically; final.pdf 52 pp with
cover. fig_c4_strongeth.png regenerated with the Krylov-tier point.


---

# Task 10. The two remaining items: K15/K17 Krylov cluster and the k=7 variant

## A. K15/K17 past both ceilings

- The Chebyshev tier (Task 9) is degree-walled at K13 (degree linear in D at
  dose-pinned R ~ 570). The remaining factorization-free median-window routes
  were implemented and measured: ARPACK which='LA' on -(H-sigma)^2 stalls at
  ncv 240/460/700 (0/160 pairs; continuum at the window edge; a which='LM'
  first attempt silently returned the far-edge end and was caught by a
  window-position check); ILU^2 LOBPCG overflows; unpreconditioned LOBPCG
  contracts at 0.96/iter; soft filters need degree ~5e3.
- Executed: the UPPER-EDGE window (eigsh(H, 'LM'), k=350, 30 bins, residuals
  <= 1.3e-11). d=4 edge ladder to D=104976: sigma_rel = 0.871-0.895 FLAT
  (x25.6 in D); d=3 edge ladder: 0.835-0.839 FLAT; <r>_edge 0.38-0.43
  (Poisson-like edge sector), PR/D 0.054->0.009. The fluctuation RATIO is
  flat past both ceilings in both window conventions; the absolute-units
  kappa (Task 9) decays on the slow D^-0.255 track at the median.
- Matched-dose trajectories: K13 tau=96 (secular climb through micro:
  3.96->4.79 vs micro 3.956), K15 tau=44, K17 tau=36 -- horizon-limited,
  ~2.2 h across 12 resumable chunks.

## B. C9 k=7 on the frozen 2024 PDG extract

- Extract frozen and committed BEFORE the fit (seven-flavour Z-width
  decomposition, protocol embedded; null first, injection second, fit last).
- Null: FPR 0/3000 at chi2_0.95(7) = 14.07. Injection: pre-registered truth
  infeasible (7 does not divide 60) -- amendment recorded; the valid table
  recovers N=60 at 3e5 events with the highly-composite-N scan bias
  documented. Fit: best chi2 = 1394.68, p = 0.032 (lepton universality);
  no common-N table -- the five-channel exclusion confirmed at k=7.

## C. Reconciliation

- Both parallel sessions' residuals work is merged into one line (Tasks 7-9
  as base; this session's K15/K17 edge tier, k=7 record, and closed-routes
  measurement as extensions). Paper items (j)/(k) added to rem:numerics;
  register C4/C9 rows, falsify items, and the intro updated.
