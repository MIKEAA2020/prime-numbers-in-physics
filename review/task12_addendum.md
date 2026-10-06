# Addendum — Task 12 (2026-10-06): the fixed-V d≥3 sector-ladder extension (the decision object, executed)

Working register (not the paper). Records the extension of the fixed-V
sector ladders and the adjudication under the pre-registered rule.

## 1. Pre-registration

The quantitative decision rule was frozen and committed (c3d55fb) BEFORE
any extension rung executed:

- (D1) crossing: kappa <= B_count at any rung (thermal verdict additionally
  requires <r> in the GOE band 0.5359 ± 0.03 at that rung);
- (D2) plateau: |slope| <= 0.05 over the last four window-protocol rungs;
- (D3) separated decay: 0.05 < alpha < 0.45 (kappa/B grows as n^(1/2-alpha),
  no crossing in the power-law model);
- (D4) thermal-rate decay: alpha >= 0.45 (finite crossing scale);
- (D5) mapping: (D2)/(D3) → obstruction side, (D1)/(D4) → thermal side,
  else open; seed-8 controls must leave the class unchanged for "settled".

## 2. Execution (`c4_msector_extend.py`)

- Rungs: d3 S = 200-480 (n → 115921), d4 S = 55-70 (n → 62196), new d5
  family (dense S = 12/16; window S = 20, 24, 26, 28; n → 35960); seed-8
  controls at two rungs per family (d3 200/280, d4 55/60, d5 20/24).
- d = 5 assembly validated against the full-grid extraction (8.9e-16 and
  exact at the two (U, V) checks) — the committed validation had covered
  d ≤ 4 only.
- Resumable per rung (npz + JSON save); address-space cap 3.4 GB; per-rung
  peak-RSS monitor. First execution attempt died silently as a background
  process (this platform reaps detached processes — the same constraint
  behind the Task 10 "resumable chunk sessions"); rerun in 9.3-minute
  foreground chunks, six chunks total. The RAM-guard model was refined
  mid-execution from a conflated (peak/(16·n·bw)) factor to a two-term
  estimate (LU band fill + eigsh workspace) after the workspace overhead
  wrongly threatened the large d3 rungs; the decision rule itself was not
  touched. All 21 rungs + 5 controls executed; zero guard skips; peak RSS
  2.26 GB (d5, S = 28).

## 3. Adjudication (`c4_msector_decision.py` → c4_msector_decision.json)

- Crossing excluded at every rung of every family and both seeds; minimum
  separation 5.1× (d5, seed 8, S = 20).
- d3: flat window ladder (kappa 0.185-0.201 over 13.4× in n; all-rung slope
  −0.0007 ± 0.012; last-four +0.065 rising → formally the non-monotone/open
  case of the rule); kappa/B 15.9 → 59.4; <r> 0.10-0.15; PR/n 0.20-0.25.
- d4: plateau per (D2) (0.137-0.151 over 6.8×; tail −0.009; alpha
  0.037 ± 0.017); kappa/B → 31.8; <r> 0.40-0.42. The protocol-homogeneous
  window fit is flat; the committed n^−0.22 reading spans the dense-to-window
  protocol change at S = 36.
- d5: separated slow decay (alpha = 0.195 ± 0.082 vs 1/2); kappa/B flat at
  6.9-7.9; <r> transits the GOE band downward (0.541 → 0.499, below the
  0.506 edge at the top rung). GOE level statistics coexist with super-Haar
  fluctuations at a fixed factor ~7 — and do not persist as n grows.
- Controls: kappa 3.2-28.4% scatter, <r> ≤ 0.02; the fine class labels flip
  under substitution (d3 open↔plateau, d4 plateau↔open, d5
  separated↔open) → the registered class-stability requirement fails; the
  verdict is obstruction-consistent at the computed scales, not closed.

## 4. Paper and deployment

- sec_dynamics.tex: item (l) amended (protocol-homogeneous d4 reading) and
  extended with the rung record and adjudication; the fig:msector figure
  environment ADDED — the reference existed since Task 11 but the figure
  block did not, and the deployed PDF rendered "Figure ??" (caught by
  text-extracting the final PDF; the compile warnings had been missed).
  fig_c4_msector.png regenerated (d5 family, extension rungs, seed-8 open
  markers, GOE band, Haar line to 1.2e5) and VLM-verified panel-by-panel.
- sec_register.tex C4 row, sec_intro.tex abstract: the extension outcome.
- READMEs (root + pilots): the extension record.
- Compile: tectonic clean (0 overfull, 161 underfull, 0 undefined; "??"
  count 0 in the rendered text); flatten → manuscript.tex (3502 lines)
  compiles identically in a clean dir (54 pp); final.pdf 55 pp with cover.
- Deployed: download/manuscript/ (tex + figs + pdfs), download/
  pilot_c4_eth_scaled/ (new msec_*.npz, c4_msector_results.json,
  c4_msector_decision.json, fig_c4_msector.png, ext_ladder.log), repo
  pilots synced, scripts mirrored; committed and pushed.
