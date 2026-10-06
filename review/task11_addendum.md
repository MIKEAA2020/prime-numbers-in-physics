# Addendum — Task 11 (2026-10-06): the M-sector falsifier, the turnkey K15/K17 rerun, and the table-agnostic dictionary

Working register (not the paper). Records the execution of the three
forward items after the Task 10 reconciliation.

## 1. The occupation-sector Jacobi structure (C4 mathematical falsifier)

Built `pilots/c4_eth/c4_msector_jacobi.py` (sector assembly from
compositions, validated against the full-grid extraction to 4e-15 with the
faithful seed-7 coupling stream) and measured:

- **J1 (layer grading)**: block-tridiagonal in l = S − k₁, max |Δl| = 1 at
  every tested (d, S); the diagonal block at layer l IS the (d−1, l) sector
  of {p₂..p_d} + affine shift — recursion equality to 3.6e-15 (after the
  p-offset/h-submatrix fix; the first attempt compared against a fresh draw,
  which was wrong).
- **J2 (two-mode solvability)**: closed form validated to 4e-13 against
  `eigh_tridiagonal` (after fixing a sort-order bug in the comparison: the
  analytic spectrum is descending, `np.sort` ascending). Analytic κ floor
  |Δ|/(30√(Δ²+4C²)) matched numerically at both conventions:
  dose κ → 0.0333 = 1/30 exactly (h₁₂ ≈ 8.9e-4 for the seed-7 draw, so
  C → V·S at dose, Ω → |Δ|); fixed V: κ ~ 1/S. ⟨r⟩ = 1 (picket) at every S.
  The d=2 obstruction is total at U=0 for every (h, V).
- **J3 (free reduction + covariance)**: kinetic off-diagonal commutators
  with mode permutations = 0.0 EXACTLY at h=0 (the first check had a broken
  permutation-matrix construction — pos indexed by sorted key; fixed).
  Diagonal breaking norms 10–37.
- **Ladders**: d=3 dose: Poisson + decaying κ (free limit); d=4 dose: κ
  turns around and RISES (permutation-cluster growth the candidate
  mechanism; not finally attributed); d=3 fixed: plateau 0.196 +
  sub-Poisson 0.148; d=4 fixed: n^{−0.22}, ⟨r⟩ → 0.40. Anisotropic control
  (±30%, one realization): unchanged — covariance not the mechanism.
- **Classical limits** (`c4_msector_classical.py`): one-body flow validated
  against `expm` (the first attempt used elementwise exp — wrong; fixed);
  kinetic flow chaotic at d≥3 (d=3 mixed 0.003–0.114 with a dt-halved
  stability run; d=4 uniform 0.116–0.137); integrator floor 0.003–0.004
  from the 1-d.o.f. d=2 case.
- **Decision**: no leg shows the joint thermalization signature
  (GOE ⟨r⟩ + κ on the Haar line) at accessible n; the two-mode sector is a
  proved obstruction; the fixed-V d≥3 ladder is the open decision object.
  Paper: Prop. `prop:jacobi` + Remark numerics (l) + fig_c4_msector.png.

## 2. K15/K17 median-window rerun (turnkey)

`run_c4_median_k15k17.sh` with the loop: repeat `c4_kappa_krylov.py
--resume --deadline CHUNK_DEADLINE` until the result json exists and the
`krs_` state is removed. Added two backward-compatible CLI options to the
committed machinery: `--t-scale` (rescale the resumed passband — the K13
calibration route) and `--addr-limit` (lift the 3.4 GB laptop guard on
bigger machines). The demo (d=3 K18, 130 s chunks) certified 350/350 over
six chunk boundaries; σ ratio 0.994, ⟨r⟩ 0.5008 vs 0.4999, PR/D 0.1010 vs
0.1008 against the committed platform — the chunked trajectory is
statistically identical, and the loop mechanics are proven end-to-end.
Projected budgets: ~7 h (K15), ~19 h (K17) at 2 cores; working set < 1.5 GB.

## 3. C9 table-agnostic dictionary (W, Higgs)

PDG 2024 listings downloaded (W: rpp2024-list-w-boson.pdf, 48 pp; Higgs:
rpp2024-list-higgs-boson.pdf, 60 pp — the first Higgs URL tried was a 404
HTML page that got mistaken for a PDF; caught by `file`). Extracts frozen
and committed BEFORE any fit (commit 38f7ad3): W k=4 (granularity
amendment), Higgs k=7 (the seven measured channels; SM-coupled provenance;
σ_rel 8–50%). Runner `c9_ktable_fit.py` (P1/P2/P3, minutes per table):

- **W**: FPR 0.001; injection 100/100; min-χ² = 4176 (N=18), p = 0.80 —
  exclusion, no common-N table at W precision.
- **Higgs**: the rule FIRES (min-χ² = 0.333 at N = 3672, p = 0/3000).
  Honest handling: recovery power 0/100; the Dirichlet null is not
  shape-matched to a 2000:1 channel hierarchy; a clearly-labeled post-hoc
  bootstrap-around-data diagnostic (200 draws) gives P(≤ data) = 3.5% —
  recorded as `exploratory_posthoc`, OUTSIDE the pre-registered decision.
  Verdict carried in the paper: flagged, not confirmed; needs precision and
  a shape-matched pre-registered null.

## 4. Paper and deployment

Prop. `prop:jacobi` (+ proof sketch, validation paragraph), Remark numerics
item (l), figure fig:msector, register C4/C9 rows, falsify item 2,
mathprograms items 1 and 4, abstract touch. Tectonic compile: 53 pp body,
0 overfull, no undefined references; flattened manuscript verified to
compile identically in a clean dir (53 pp); final.pdf 54 pp with cover.
All artifacts synced (repo, scripts mirror, download/manuscript,
download/pilot_* mirrors, READMEs).

## Open items carried forward

- The fixed-V sector ladder in d ≥ 3 at larger S (the falsifier's decision
  object: κ plateau vs Haar crossing) — the d=3 plateau and the d=4 slow
  decay are the current endpoints.
- The K15/K17 median-window runs await a machine with the wall-clock (the
  runbook is turnkey; budgets documented).
- The Higgs anomaly awaits precision and a shape-matched pre-registered
  null; the Z-pole exclusions remain the calibrated anchor.
