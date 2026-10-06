# Prime Numbers in Physics — The Prime-Spectral Framework

Repository persisting the full research line: the 48-turn source conversation
("Prime Numbers and Universe", Qwen, October 2026), the research paper built
from it, and the complete numerical program for its conjecture register.

## Contents

| Path | Description |
|---|---|
| `transcript/qwen_chat_transcript_full.txt` | Full 48-turn source transcript (9,891 lines) |
| `transcript/*.json` | Raw DOM extraction (user turns, assistant turns, page data) |
| `paper/latex/` | LaTeX sources of the paper (Tectonic) |
| `paper/output/prime_spectral_framework_rigorous_reconstruction.pdf` | **Main deliverable** — the research paper |
| `paper/output/prime_spectral_framework_cover.html` | Cover page source (HTML/Playwright, Template 03) |
| `pilots/` | **Numerical programs for the register**: C4-ETH (dense pilot, sparse scaled run, kinetic completion, matched-dose ladder) and C9-Chebotarev protocol calibration — scripts, results, figures |
| `review/` | **Conjecture-register review** (§10 audit that located the repairs folded into the paper) |
| `scripts/merge_transcript.py` | Transcript merge pipeline |
| `worklog.md` | Multi-agent work log |

## The paper

The paper develops the prime-spectral framework in three epistemic tiers:

- **Theorems** (proved or cited exactly): primon Hilbert space as l2(F);
  self-adjoint primon Hamiltonian with simple spectrum hbar*omega0*log n;
  partition function = zeta; Hagedorn temperature T_H = hbar*omega0/kB with
  exact asymptotics; log-count law S(E) = E/T_H + O(1); Erdos-Kac cascade
  statistics; zeta clock kernel and its Bohr almost-periodicity; uniform
  recurrence of the free flow; product-basis structure of occupation states.
- **Constructions**: the interaction sector (multiplication operators, prime
  lattice, walk/hop dynamics, diagonal and kinetic completions); arithmetic
  entanglement across prime-mode bipartitions; the recurrence trichotomy.
- **Conjectures C1-C12** with evidence grades, dependencies, and falsifiers —
  from the zeta/black-hole identification to the Galois-Langlands dictionary.
  C1 is the root on the physical plane; C4, C5 and C9's computational content
  are autonomous mathematical problems (two-plane register).

## Numerical programs

- **C4-ETH** (`pilots/c4_eth/`): dense pilot (D=625-4096); sparse
  shift-invert eigen-windows (350 interior eigenpairs, eigenpair-residual
  certified) to D=59,319 in d=3; restarted-Lanczos Krylov equilibration to
  D≈10^5 (step size from a Lanczos-estimated spectral radius, validated
  against exact propagation to 1e-12); the kinetic (density-assisted hopping)
  completion; and the **matched-dose ladder** at fixed effective coupling
  VK^2≈36, which removes the dose confound while the truncation widens
  (D=3,375→59,319 in d=3, D=4,096→20,736 in d=4).
  Verdicts: level statistics GOE at generic coupling everywhere; the
  eigenstate fluctuation ratio sigma_ETH/std(a) is flat (0.95-0.98) across the
  whole ladder — no strong-ETH scaling; at D≤10^4 the finite-time plateau
  equals the exact diagonal ensemble to 0.005·K (dephasing identity), but the
  diagonal ensemble itself stays 0.04-0.09·K away from microcanonical with no
  closing trend; the D=20,736 V=0.3 trajectory extended to tau=300 saturates
  at diag≈4.40 vs micro 3.35 — the short-horizon (tau≤22) agreement with
  microcanonical was a transient.
- **C9-Chebotarev** (`pilots/c9_chebotarev/`): dictionary-protocol
  calibration in under 30 s; Z-pole data admit no common-group-order fit —
  the signature is absent below unification, as C9 requires.

See `pilots/README.md` for per-program detail.

## Register review

A line-level audit of the conjecture register
(`review/conjecture_register_review.md`) located one genuine error and
several hygiene defects, all folded back into the paper: conservation
structure corrected (H_W is the nucleation sector); C4 retyped to the
interacting completion with a scaling falsifier; C9 falsifier recalibrated;
dependencies column and two-plane DAG added.

## License

See LICENSE.

## Three-audit adjudication (2026-10-05)

Three independent audits (astra, grok, muse) were adjudicated jointly
(`review/audit_adjudication.tex` / `audit_adjudication.pdf`): every claim was
verified against the manuscript, the checkable mathematics was re-derived or
computed (`pilots/c4_eth/adjudication_checks.py`), and the demanded numerics
were executed (label-scrambled controls, generic-coupling quantile sweep,
1/log D scaling fits). Nine cross-audit oppositions were resolved on the
mathematics - notably: the counting-law defect decays exponentially (muse
right, grok's non-convergence description wrong); conjugacy-class sizes always
divide the group order (grok's divisibility charge rebutted by
orbit-stabilizer); matched-dose GOE statistics are graph-generic while the
generic-family delocalization is arithmetic (new positive finding). The
surviving fixes were folded into the paper: sharpened log-count theorem,
ensemble-bridge proposition, quantitative return-time proposition (C2 scaling
falsifier), dictionary error slot s(A) for C3, pre-registration conditions for
C9, and the audit-response controls in the numerics section.

Two register entries carry completed test programs with power statements:

- **C4 strong-ETH leg (fluctuation scaling)**: in absolute units the
  eigenstate fluctuation decays as D^{-0.185 +/- 0.021} (d=3, D up to
  5.9e4) against the strong-ETH D^{-1/2}, with the distance to the
  fixed-fraction thermal benchmark growing (4.6 -> 11.3) and effective
  random-combination dimensions of only ~8-23 states; label-scrambled
  controls hold the fluctuation flat, so the slow decay is organized by the
  arithmetic diagonal (`pilots/c4_eth/c4_strong_eth.py`).
- **C9 dictionary application (pre-registered)**: the protocol frozen in
  `review/c9_preregistration.md` (class-equation-constrained divisor fit,
  Monte-Carlo null, decision rule, power tables) applied to the Z-pole
  branching table: signature absent at the 59th percentile of the null,
  with detection power 1.000 over group orders N <= 360 at current
  precision - an exclusion at the Z scale, compatible with the conjecture's
  unification-scale placement (`pilots/c9_chebotarev/c9_prereg_application.py`).

A single-file LaTeX manuscript (`paper/latex/manuscript.tex`) is generated
from the modular sources and verified to compile identically (47 pp).

## Residual items closed (this revision)

- **Falsifier classes (math/physical split).** The conjecture register's
  falsifier column is typed: M (decidable by proof or certified finite
  computation), P (decidable by measured data), M/P; 8 of 12 entries are
  decidable without any experiment, the physical surface is concentrated in
  C9 (proton decay, precision branching) and C7-C8 (cosmological
  statistics). Section 11 develops the classification, the epistemic
  distinction (noiseless/repeatable vs statistical/one-shot), and the
  pre-registration discipline it imposes on the physical side.
- **Infinite-volume self-adjointness of the kinetic completion.** A
  proposition (occupation sectors) proves essential self-adjointness of
  H_P + H_U + H_hop + H_kin(V) on the finitely supported configurations
  via the N_tot-conserving sector decomposition (finite Hermitian blocks;
  bond-reversal weight invariance), self-adjointness of the full
  H_tot^(U,V) by Kato-Rellich with the bounded H_W (no coupling
  smallness), exactness of box truncations on contained sectors, and
  Trotter-Kato convergence in general; the d -> infinity mode-count limit
  is shown to be singular. Corroborated by 28/28 numerical sector checks
  (`pilots/c4_eth/c4_sector_checks.py`).
- **Factorization-free kappa ladder past the LU ceiling.** A block
  Chebyshev subspace-iteration window tier (on (H-c)^2, passband sized by
  stochastic Lanczos quadrature, residual-certified pairs) reproduces the
  LU windows to machine precision (max |dlambda| <= 4e-11) and extends the
  d=4 fluctuation ladder to D = 3.84e4, past the LU fill ceiling: kappa =
  0.250 (276/350 pairs certified), four-point fit D^{-0.255} vs thermal
  D^{-1/2}, benchmark distance still growing. The tier's own ceiling is
  quantitative: Chebyshev degree ~ ln(eps) R/(2t) with the dose-pinned
  radius R ~ 570 (VK^2 = 36, d = 4), i.e. degree growing linearly in D at
  fixed protocol (`pilots/c4_eth/c4_kappa_krylov.py`).

The single-file LaTeX manuscript (`paper/latex/manuscript.tex`) is
regenerated from the modular sources and verified to compile identically
(51 pp body).
