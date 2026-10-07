# Task 16 addendum — the two-copy replica bound, executed

## Scope

The decisive mathematical step identified by the Task 15 attack: the
two-copy replica bound on the within-bin loop — the pinching-locked object
that single-copy traces cannot reach. The K15/K17 resumable states are
untouched (turnkey); the overnight polish was not run — the decision
record is in the worklog: the certification tier is decision-empty
(discovery complete, tier priced, item (j) already carries the honest
record), while the replica bound is the step that separates "reduced to
the profile-margin statement" from a certified lower bound.

## The construction (`c4_msector_replica.py`, staged driver
`run_replica_stages.py`)

**Replica identities (exact, real-symmetric sector).**
- The loop `sum_{j in W} a_j^2` is the zero-frequency mass of the window
  two-point measure `mu = sum_{j,k in W} |X_jk|^2 delta_{E_k - E_j}` with
  `X = 1_W K 1_W`.
- The Fejer family `A_T = int_0^T (1 - t/T) Tr[X e^{iHt} X e^{-iHt}] dt`
  satisfies `A_T/T = sum |X_jk|^2 F_T(E_k - E_j)/T` (the positive kernel,
  `F_T(0) = T`), converging to the loop plus the sub-resolution mass.
- The commutant (pinching) projector `Pit~_W` is the dephased
  twist-exchange: the long-time average of
  `e^{i(H(x)I - I(x)H)t} SWAP` restricted to the window — the twist
  carries `|psi_a psi_b>` to `e^{i(E_b - E_a)t}` under the exchange, so
  the time average selects the energy-matched subspace.
- The difference moments `M_p = int d^{2p} dmu = ||(ad_H)^p X||^2_HS`
  are single-copy traces; the layer-graded insertion recursion (the
  block-column propagation of the committed moment machinery, extended to
  operator insertions) computes them exactly.

**The replica sandwich.** For every threshold `delta` and averaging time
`T`, with `m(delta)` the near-diagonal mass, `g(delta)` the frequency
floor, and `M_0 = Tr[X^2]` the surrogate:
`A_T/T - m(delta) - 4 M_0/(T^2 g(delta)^2) <= loop <= A_T/T`, the tail
from `F_T(d)/T <= min(1, 4/(T^2 d^2))`; the near-diagonal mass capped a
priori by the quantum variances (`|X_jk|^2 <= v_j`).

**Validation (dense platforms, d3 S=60 / d4 S=16).**
- The difference-moment identity: 4.2e-16 / 8.8e-16 / 4.3e-16 (d3, p<=2);
  2.0e-16-class at d4.
- The insertion recursion vs dense traces (K, K^2, [H,K] insertions):
  <= 2.1e-16; `[H,K]` equals the layer off-diagonal difference of `H`
  entry by entry.
- The pair census: the near-degenerate off-diagonal mass is at the
  1e-20 level of the surrogate at S=60 — the occupation-constant pairs
  are also K-decoupled (the sharpest form of the multiplet protection);
  the a priori v-cap holds.

**The frequency gap (the structural reason the bound closes).** At
d3 S=60 the off-diagonal mass (31.8% of the surrogate) has 99.9% of its
mass above frequency 0.1 (the 10th percentile of the mass-weighted
frequency distribution at 7.7), against a pair scale of 1e-8 — seven
orders of magnitude of separation. The sandwich at `(delta, c_T = 300)`
consumes 6.3–6.9e-5 of the loop.

**The closure (the exact tier, every dense-reachable rung).**

| rung | loop | measured ratio | certified ratio | margin | certified margin |
|---|---|---|---|---|---|
| d3 S=40 | 63,535 | 6.08 | 6.03 | 8.15% | 8.14% |
| d3 S=60 | 143,111 | 8.08 | 8.05 | 6.63% | 6.62% |
| d3 S=80 | 253,035 | 9.95 | 9.93 | 5.60% | 5.59% |
| d3 S=100 | 398,236 | 12.48 | 12.46 | 5.67% | 5.66% |
| d3 S=116 | 535,719 | 14.43 | 14.44 | 5.74% | 5.73% |
| d4 S=16 | 5,770 | 5.16 | 5.18 | 6.20% | 6.19% |

The certified ratio is stated at the population level of the binning
(conservative for the committed sample-binned protocol). **The
obstruction theorem's finite-dimensional instances:**
`kappa/B_count >= c_3 >= 6.0` (d3, S=40→116, growing) and `>= c_4 >= 5.2`;
the profile-margin statement certified at 5.6–8.1% of `sigma_L^2`.

**The propagation tier (eigensolver-free, validated and priced).** The
discrete-Fejer time correlator by stepwise Chebyshev propagation of the
two probe families with the bipartite Hutchinson estimator
`(v^T e^{-iHmdt} w)(w^T X e^{iHmdt} X v)` (unbiased for the correlator),
the aliasing budget from the folded-distance census, resumable
checkpoints: at S=60 the estimate `142,044 ± 4,127` (4 resamples × 16
probes) against the exact discrete-kernel value `143,113`; the folded
tail 5.1; the Bessel truncation below 1e-59. The closing statistical
precision (probe budget `s·R ≈ 256`) is priced at the overnight
wall-clock class. The extension of the certified constants beyond the
dense tier rides this machinery.

## Paper

- sec_dynamics.tex: Proposition (prop:replica) — the replica identities,
  the sandwich, the frequency gap — with the proof sketch; the validation
  paragraph; Remark (rem:replica) — the replica route executed; the
  rewritten Remark (rem:obstruction) (the completion routes, with the
  replica route now pointing at the executed proposition); rem:numerics
  item (n).
- sec_register.tex: the falsifier-classes passage (the replica-bound
  execution, the certified constants); mathprograms item 1 (the executed
  route; the thermalization side must overturn a certified constant); the
  C4 row closing clause; the Assessment.
- sec_intro.tex: the abstract clause.
- Compile: tectonic clean (0 overfull, 0 undefined, 0 "??"); the flattened
  manuscript.tex (4104 lines) compiles identically in a clean directory
  (68 pp body); final.pdf 69 pp with cover. The flatten script's relative
  path was repaired (the repo layout had moved since Task 15).
- Deployed: download/ PDF + manuscript package; the results JSON and the
  propagation checkpoints in the pilots; scripts mirrored.
