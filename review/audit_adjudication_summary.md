# Three-Audit Adjudication — Summary

Full adjudication: `review/audit_adjudication.tex` / `audit_adjudication.pdf`
(10 pp). Audits adjudicated: astra (13 points), grok (13 flaws + 7-row
inconsistency table + 7 improvements), muse (8 subsections + minors + plan).

## Nine cross-audit oppositions, resolved

| # | Opposition | Resolution |
|---|------------|------------|
| O1 | grok "defect does not converge, amplitude log 2" vs muse "O(e^{-x})" | **muse right** (computed: r→0 like e^{-x}; log 2 is only the global envelope); theorem sharpened to a two-sided bound with exponential decay |
| O2 | grok "Baker/Lindemann–Weierstrass" vs muse "unique factorization suffices" | **muse right**; the paper's proof is UFT; lemma restated finite-support |
| O3 | grok "partition asymptotics cited (category error)" vs muse "normal/maximal order conflated" | **both misread** — the 1917 normal-order paper is cited; abstract disambiguated anyway |
| O4 | grok "class sizes divide \|G\| only in trivial cases" vs protocol c_i\|N | **paper right** (orbit–stabilizer; brute-force on 12 groups); grok's analyst-dof / absence-as-confirmation / single-channel subpoints adopted |
| O5 | grok "circular smoothing" vs muse "no phase transition proved" vs astra "interpretive" | all converge → demoted to a growth-rate statement; "exactly critical" removed; staircase explicit |
| O6 | grok "no ensemble at the pole; no bridge theorem" | valid → **new ensemble-bridge proposition** (Z = Laplace–Stieltjes transform of the counting function; pole = transform of the exponential law; ζ − 1/(σ−1) entire) |
| O7 | grok "O(1) cannot absorb log(A)" | right → dictionary slot s(A) = O(log(A/ℓ²)); area coefficient exact; pure (s=O(1)) form falsifiable |
| O8 | grok "default GOE expectation; demand controls" vs muse "pre-asymptotic" | **executed**: matched-dose GOE scramble-insensitive (grok's reading confirmed for statistics); generic-family delocalization IS arithmetic (PR/D collapse 2–12×); 1/log D fits; asymptotic distance quantified |
| O9 | grok "split the paper" vs muse "quarantine" vs astra "ledger" | muse+astra adopted (register = ledger; two-plane quarantine); split recorded as a publishing option |

## Verdict counts

- astra: 4 applied, 3 partial, 4 already-satisfied, 2 satisfied-in-part
- grok: 5 applied, 5 partial, 2 rebutted (G3 Hardy–Ramanujan misread; G10 divisibility), 1 applied+run (G11: all three demanded diagnostics executed)
- muse: 6 applied, 3 partial, 4 already-satisfied, 1 rebutted (Q_{>0} unbounded-below charge — the Gaussian extension uses norms only)

## New content folded into the manuscript

1. Log-count theorem: sharp two-sided defect bound, exponential decay, smoothing item
2. Ensemble-bridge proposition (canonical pole ↔ microcanonical counting law)
3. Quantitative return-time proposition + C2 scaling falsifier (poly-in-S vs double-exp-in-S)
4. Ray-periodicity classification
5. C3 dictionary slot s(A); BH theorem: area coefficient exact, corrections carried by s
6. Clock regulator ν disambiguated; no-directional-limit addendum; kinematical scoping
7. Commutator [H_P, M_m] identity; "selected, not derived" provenance remark
8. Rem (f) label-scrambled controls, (g) finite-size scaling; Figure (controls)
9. Register: C2/C3/C4/C5/C9/C10 updated; §1.2 operational testability + interpretive exemption; falsify items 2 and 4 rewritten
10. Arithmetic sector: incomplete-tensor-product/Fock unitary, D(H_P), units paragraph, "not implied" boundary
11. Galois section: dictionary bookkeeping boundary (no gauge dynamics constructed)

## Residual open items

1. C9 has no pre-registered application on real data (compatibility, not confirmation)
2. Strong-ETH leg of C4 flat; ⟨r⟩ scaling limit unsettled in the computed range
3. Math/physical falsifier separation in §11 only partial
4. Infinite-volume self-adjointness of the kinetic completion (unbounded coefficients) open
