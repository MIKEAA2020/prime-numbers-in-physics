# Task 15 addendum — the obstruction attack, the 2026 listing cycle, and the K15/K17 rerun

## Scope

The three items from the forward queue: (a) the K15/K17 median-window
Chebyshev rerun (RAM/wall-clock gated), (b) the C9 dictionary on new
precision branching tables (data gated), (c) the obstruction bound itself —
the moment recursions on the layer-graded blocks.

## (c) The obstruction attack

**Machinery (new, validated).**

- `c4_msector_moments.py`: the layer-content moments
  `t_m(l) = Tr(H^m P_l)` computed exactly by block-column propagation in
  the layer grading (from each source layer `l0`, `X_{m+1} = H X_m`; the
  trace of the `(l0, l0)` block of `H^m` — the cross-layer block traces
  vanish by cyclicity of the trace with orthogonal projectors). Validated
  against dense powers: 3.4e-16 relative (d3, S=60, n=1891, m<=24) and
  1.4e-19 (d4, S=16, n=969, m<=16); trace sums to 1.9e-16.
- The trace formulas: every aggregate layer statistic of an energy window
  is a trace functional of the joint (E, l) measure; the exact variance
  splitting `Tr(rho_W (Delta K)^2) = E_W[v_layer] + Var_W(a)` holds to
  2e-13 (the S=60 window: 226.8 = 211.8 quantum + 15.0 classical).
- The loop obstruction: the within-bin classical variance is the pinching
  object `sum_j a_j^2 = Tr(Pi~_W (K x I) Pi~_W (K x I))` in the two-copy
  space; the single-copy surrogate `Tr(K Pi_W K Pi_W)` exceeds the loop by
  the window off-diagonal fraction (31.8% d3, 35.4% d4).
- `c4_msector_symmetry.py`: the kinetic term is exactly S_d-invariant
  (commutators 0.0 identically for all 5/23 nontrivial permutations at
  d=3/d=4); the tau-even part `H_+ = (H + tau H tau)/2` commutes with tau
  exactly; the Burnside isotypic counts check exactly; the isotypic
  occupation identity: trivial/sign-restricted `<K> - S/d` bounded by
  1.4e-13 while the standard-restricted dipoles carry the full window
  spread (std 2.85 vs the window dipole std 3.88 at S=60).

**Architecture measured along the ladder.**

- The eigenstate layer profiles are broad (std 0.24S) but are shifted
  copies of one another and of the aggregate (profile-shape correlation
  0.72 across spectrum ends); the classical variance is exactly the spread
  of the shifts: margins 6.6% (S=60) and 5.5% (S=120) of the window layer
  variance — the ladder plateau in decomposed form.
- The multiplet census: kinetic-only doublets = the standard multiplicity
  exactly at S=20 (77 = 77); surviving full-H pairs grow 0 -> 4 -> 48 ->
  725 (S=20/40/60/120), refined median splittings 2.1e-9 -> 1.9e-10 ->
  3.6e-12, within-pair occupation gaps at the 1e-9..1e-12 floor; the
  median-window pair fraction grows to 28% at S=480 as <r> falls to 0.10;
  inter-pair occupation jumps reach 0.2S.
- Window eigenstates distribute over the isotypic components at the
  dimension fractions (0.16/0.17/0.67): the permutation symmetry is fully
  broken in the eigenstates while its multiplet skeleton organizes the
  spectrum.

**Result.** The obstruction theorem (kappa/B_count >= c_d > 1 along the
fixed-V ladders) is reduced to the profile-margin statement with two
completion routes (a two-copy replica bound on the within-bin loop, or a
multiplet-dipole control); the within-bin tier is a loop object by
construction — no single-copy trace can close it. Paper: Proposition 3.11
(prop:moments), the validation paragraph, Remark 3.12 (rem:obstruction),
and rem:numerics item (m); the register, mathprograms item 1, and the
abstract are bound to it.

## (b) C9 on the 2026 PDG listings

- The 2026 W and Higgs listing PDFs (rpp2026-list-w-boson.pdf 51 pp,
  rpp2026-list-higgs-boson.pdf 75 pp; citation F. Takahashi et al., Int.
  J. Mod. Phys. A 41, 2630011 (2026)) were downloaded, the tables
  extracted, and the extracts frozen and committed (f7100fe) BEFORE any
  fit. New precision content: the Higgs mu mu channel moves to
  (3.0 +- 0.9)e-4 (sigma_rel 50% -> 30%), the only changed channel; the W
  fractions are unchanged (the width OUR AVERAGE moves to 2.14 +- 0.05
  GeV with ATLAS 24CJ in the combination).
- The Higgs injection truth is amended to the minimum-chi2 valid
  dictionary of the frozen vector (N=3168, c=[1584, 792, 88, 198, 8, 11,
  1], within one sigma in every channel). The 2024 recorded truth (2800
  at N=5040) was not a valid dictionary (2800 does not divide 5040), so
  the 2024 zero-recovery injection read was confounded; with the valid
  truth the power measurement is clean: recovery 0/100.
- Refits: W reproduces the exclusion identically (chi2 = 4176 at N=18,
  p = 0.80, injection 100/100). Higgs fires the rule again (chi2 = 0.386
  at N=3168, p < 1/3000), post-hoc bootstrap around the data P = 10.5%
  (2024: 3.5%) — recorded exploratory, outside the pre-registered
  decision. Verdict unchanged in form: flagged, not confirmed.

## (a) K15/K17 median-window rerun

- The checkpoint save in `c4_kappa_krylov.py` is hardened to atomic
  (write-then-rename), backward-compatible (an external kill can no
  longer truncate the resumable state; the first save attempt exposed
  and fixed an np.savez extension pitfall en route).
- The rerun was executed on the available hardware (3.9 GB / 2 cores —
  the same class as the original platform): 25 resumable chunks at K15
  (D=65536). The platform build, spectral edges, passband discovery,
  sweep loop, and resume cycle run cleanly end-to-end, and the DISCOVERY
  PHASE COMPLETES on this hardware class: the passband fills at the
  calibrated 1.15 rate per Rayleigh-Ritz pass (count_in 8 -> 21 -> 50 ->
  132 -> 246 -> 336 -> 391 over sweeps 5-11), the block reaching full
  coverage at sweep 11 (count 391 -> 416 of 416 at sweeps 12-13), with
  the state checkpointed atomically after every chunk.
- The certification tier is what the committed degree cap walls: the cap
  (M <= 1500, against the ln(1e4) R/(2t) ~ 7e3 the initial band
  narrowness t/R ~ 1/1500 prices) holds after the passband adaptation,
  and the f64 polish decays the Ritz residuals at only ~3x per sweep at
  the capped degree (sweep 12: [1.5, 2.8, 4.7]; sweep 13: [0.34, 0.86,
  1.6] at the 10/50/90 percentiles) — pricing the 2e-6 certification at
  roughly eleven further polish sweeps, overnight-class wall-clock. The
  K13 partial-certification record (276/370 at degree 3400) marks the
  tier the cap lift restores. The resumable state `krs_L36d4K15kr.npz`
  (sweep 13, phase 1) and the run log accompany the pilots; continuation
  is turnkey (the committed runner picks the state up).

## Paper

- sec_dynamics.tex: Proposition (prop:moments) with items (i)-(iv) and
  proof sketch; the validation paragraph; Remark (rem:obstruction);
  rem:numerics item (m) (the architecture along the ladder); item (j)
  extension (the K15/K17 rerun record).
- sec_register.tex: mathprograms item 1 (the executed venue, the two
  structural facts, the profile-margin reduction, the completion routes);
  the falsifier-classes third fact extension; the C4 row closing clause;
  the C9 row (the 2026 cells); mathprograms item 4 (the 2026 cycle).
- sec_intro.tex: the abstract carries the attack and the 2026 cycle.
- Compile: tectonic clean (0 overfull, 0 undefined, 0 "??"); the
  flattened manuscript.tex (3909 lines) compiles identically in a clean
  directory (66 pp body); final.pdf 67 pp with cover. All new cells
  verified to render in the extracted PDF text.
