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
