# Prime Numbers in Physics — The Prime-Spectral Framework

Repository persisting the full research line: the 48-turn source conversation
("Prime Numbers and Universe", Qwen, October 2026) and its rigorous reconstruction.

## Contents

| Path | Description |
|---|---|
| `transcript/qwen_chat_transcript_full.txt` | Full 48-turn source transcript (9,891 lines) |
| `transcript/*.json` | Raw DOM extraction (user turns, assistant turns, page data) |
| `paper/latex/` | LaTeX sources of the reconstructed paper (Tectonic) |
| `paper/output/prime_spectral_framework_rigorous_reconstruction.pdf` | **Main deliverable** — the research paper |
| `paper/output/prime_spectral_framework_cover.html` | Cover page source (HTML/Playwright, Template 03) |
| `pilots/` | **Executed register attacks**: C4-ETH simulations (dense pilot + sparse scaled run to D≈10⁵) and C9-Chebotarev protocol calibration — scripts, results, figures |
| `review/` | **Conjecture-register review** (§10 audit that located the repairs folded into the paper) |
| `scripts/merge_transcript.py` | Transcript merge pipeline |
| `worklog.md` | Multi-agent work log |

## The reconstruction

The paper elevates, repairs, and demotes the source framework:

- **Elevated to theorems**: primon Hilbert space as l2(F); self-adjoint primon
  Hamiltonian with simple spectrum hbar*omega0*log n; partition function = zeta;
  Hagedorn temperature T_H = hbar*omega0/kB with exact asymptotics; log-count law
  S(E) = E/T_H + O(1); Erdos-Kac cascade statistics; zeta clock kernel and its
  Bohr almost-periodicity; uniform recurrence of the free flow.
- **Repaired**: frozen-Hamiltonian gap (multiplication operators, prime lattice,
  walk/hop dynamics); composite-!=-entangled correction (occupation basis is a
  product basis; arithmetic entanglement is superpositional); recurrence claims
  (exact periodicity forbidden; epsilon-recurrence universal; Polya transience).
- **Demoted to conjectures**: C1-C12 register with evidence grades, dependencies,
  and falsifiers — from the zeta/black-hole identification to the Galois-Langlands
  dictionary. C1 is the root on the physical plane; C4, C5 and C9's computational
  content are autonomous mathematical problems (two-plane register).

## Register review and executed attacks

A line-level audit of the conjecture register (`review/conjecture_register_review.md`)
found one genuine error and several hygiene defects, all folded back into the paper:

- **Conservation structure corrected**: `H_W` does *not* conserve the total primon
  number — it is the nucleation sector (contradicted the nucleation proposition);
  commutator coefficients in Prop. well-posedness fixed.
- **C4 retyped**: the bare `H_tot` has no quartic sector (quasi-single-particle on the
  exponent lattice) — thermalization is now conjectured for an interacting completion,
  with a finite-size *scaling* falsifier instead of an unfalsifiable E→∞ statement.
- **C9 falsifier recalibrated**: Monte-Carlo-calibrated common-group-order divisor
  protocol (≥5 channels, σ≤0.3%, |G|≲ few·10²); Z-pole data admits no fit — the
  signature is absent below unification, as C9 requires.
- **Dependencies column added** to the register; two-plane (physical/mathematical) DAG.

Both "cheapest attacks" were *executed* (`pilots/`): the C4-ETH program from D=625
(dense) to D≈10⁵ (sparse interior eigensolvers, laptop-scale), and the C9-Chebotarev
dictionary check in under 30 seconds. See `pilots/README.md`.

## License

See LICENSE.
