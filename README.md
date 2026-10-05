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
