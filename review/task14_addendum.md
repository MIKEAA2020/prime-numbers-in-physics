# Task 14 addendum — the settled decision object in the Section 11 falsifier split; register rendering repair

## Scope

The remaining open program item after the Task 13 settle: the settled fixed-V
d>=3 sector ladder (the decision object) feeds the M-sector Jacobi
thermalization proof-or-obstruction, and that object is to be slotted into the
Section 11 mathematical/physical falsifier split.

## What was done

1. **Falsifier classes (Section 11.2).** The classification table's C4
   decisive instance now names the sector ladder and its verdict ("settled,
   obstruction side"). The narrative's structural-fact count is three; the
   third fact carries the adjudication of the settled decision object as a
   table in the split itself — per family, the decay-exponent interval
   (thermal rate 1/2), the ratio-slope interval of log(kappa/B_count), the
   realization-mean level statistic, and the admitted crossing scale — with
   the interval construction stated (95% t-intervals, the wider of the
   regression and between-realization components). The passage records the
   verdict's reach (no crossing under any realization; ratio 3.9–71 over the
   77 rungs and realizations; crossing floor n ~ 8e10), the d=5 signature
   split (GOE level statistics coexisting with a factor ~7 super-Haar
   fluctuation ratio), the M-class operative advantage (noiseless, repeatable,
   pre-registered; residual uncertainty is reach, not measurement), and the
   residual program the verdict feeds.

2. **Mathematical test programs (Section 11.3, item 1).** The closing replaces
   the one-line settle statement with the dichotomy the settled object fixes:
   an obstruction theorem — a rigorous lower bound
   kappa(S)/B_count(S) >= c_d > 1 along the fixed-V ladders, the two-mode
   sector the proved instance, the block-tridiagonal Jacobi structure the
   venue (layer-graded moment recursions, trace formulas of the binned
   occupation observable) — versus a thermalization proof, which must operate
   beyond every admitted trend (no admitted trend crosses at all in d=3/d=4;
   the steepest d=5 trend crosses only beyond n ~ 8e10) or overturn the
   fitted decays. Both routes are statements about finite matrices; the
   obstruction bound is the route within reach of proof.

3. **Register (Section 10).** The C4 row's falsifier cell closes with the
   binding clause: adjudication table reference, survival range = the
   asymptotic reach beyond the crossing floor, residual-program pointer. The
   structural observations record that one mathematical falsifier has been
   executed to a settled verdict. The Assessment records that one of the two
   numerically testable entries is decided.

4. **Dynamics pointer and abstract.** The post-Proposition validation
   paragraph points to the dichotomy; the abstract carries the
   residual-program clause.

## Rendering defect found and repaired

A PDF-level extraction audit (the same audit that verifies "??"-free
references) found that the C4 and C9 register rows exceeded one page in
height, and longtable silently clipped their falsifier cells at the page
boundary — the defect predates this task (present in the Task 12/13 deployed
PDFs). The C4 row lost everything from "Strong dose (VK^2 >= 80) localizes"
onward: the level-statistics and label-scrambled paragraphs, the sector-form
paragraph, the pre-registered extension, the interval amendment, and the
settled verdict. The C9 row lost everything from the k=7 record onward: the
rejection record, the W and Higgs applications, the primitive-representative
note, and the proton-decay pointer. The LaTeX sources always contained the
full text; only the rendered PDF was truncated.

Repair: both rows are restructured as longtable continuation rows — the
falsifier cell text is split at sentence (or semicolon) boundaries into
twelve physical rows (C4) and seven (C9), with empty ID/Statement/Grade/
Depends cells in the continuation rows and no rules between them, so the
column reads as one continuous entry while the table can break pages between
rows. No text was changed. Post-repair audit: all sixteen C4/C9 tail probes
found in the rendered text, 0 overfull boxes, 0 undefined references, 0
rendered "??"; the body grows from 55 to 61 pages, all of it previously
clipped register content; the flattened single-file manuscript compiles
identically in a clean directory (61 pp); final.pdf (with cover) is 62 pages.

## Verification checklist

- [x] Adjudication table values cross-checked against
      `results/c4_msector_decision2.json` (alpha, gamma, r-bar, n_star_lo,
      ratio minima, 77 rungs/realizations, overall verdict).
- [x] Interval construction described as implemented (`hw = max(hw_wls,
      hw_seed)`, t95 multipliers).
- [x] All register row tails render in the PDF (extraction audit, hyphen- and
      whitespace-normalized probes).
- [x] Tectonic clean: 0 overfull, 0 undefined, 61 pp body; manuscript.tex
      clean-dir compile identical; final.pdf 62 pp; 0 "??".
- [x] Deliverables deployed: download/ PDF + manuscript package.

## Open items (gated, unchanged)

- K15/K17 median-window Chebyshev rerun: turnkey (`run_c4_median_k15k17.sh`),
  gated on RAM/wall-clock.
- New precision branching tables (W-class, Higgs-class) for the C9
  dictionary: turnkey (`c9_ktable_fit.py`), gated on data.
