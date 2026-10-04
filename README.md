# Prime Numbers in Physics — The Prime-Spectral Framework

Repository persisting the full research line: the 48-turn source conversation
("Prime Numbers and Universe", Qwen, October 2026) and its rigorous reconstruction.

## Contents

| Path | Description |
|---|---|
| `transcript/qwen_chat_transcript_full.txt` | Full 48-turn source transcript (9,891 lines) |
| `transcript/*.json` | Raw DOM extraction (user turns, assistant turns, page data) |
| `paper/latex/` | LaTeX sources of the reconstructed paper (Tectonic) |
| `paper/output/prime_spectral_framework_rigorous_reconstruction.pdf` | **Main deliverable** — 37-page research paper |
| `paper/output/prime_spectral_framework_cover.html` | Cover page source (HTML/Playwright, Template 03) |
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
  dictionary.

## License

See LICENSE.
