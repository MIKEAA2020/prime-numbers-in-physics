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

Diagnostics: level-spacing ratio ⟨r⟩ (Poisson 0.3863 / GOE 0.5359 — the **C5 proxy**),
ETH fluctuation σ_ETH of local occupation observables with microcanonical reference,
participation ratios, diagonal-ensemble vs microcanonical equilibration, quartic
completion `U·Σ n_i n_j` (dose–response and D-scaling), weak-coupling control.

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
thermalization — it localizes. Next candidate: kinetic (density-assisted hopping)
completions, testable with the same infrastructure.

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
# C4 scaled (sparse; ~2 h total on 4 GB / 2 cores). The driver is resumable:
# each configuration runs as its own process with a wall-clock deadline, so it
# can be run in foreground chunks (re-invoke until scan.log ends with ALL_DONE).
bash c4_eth/run_c4_scaled.sh
# merge + figures
python3 c4_eth/c4_scaled_figures.py
# C9 (< 30 s)
python3 c9_chebotarev/c9_chebotarev_pilot.py
```

Requirements: numpy, scipy, matplotlib. The scaled worker validates itself against
the dense pilot (exact eigenvalue agreement at D = 4096) and against dense `expm`
for the Krylov propagator (agreement to 10⁻¹³; norm drift ≤ 10⁻¹³ per trace).
