# Worklog

---
Task ID: 1
Agent: Main agent (Super Z)
Task: Read https://chat.qwen.ai/s/ac002fa1-606e-488d-99ac-6280f9109b41 thoroughly at line-level till end

Work Log:
- page_reader (z-ai CLI) fetched static HTML (1.5MB) — contained only skeleton; chat content loads via JS
- agent-browser rendered the share page; extracted title "Prime Numbers and Universe" (Oct 04, 2026), 24 user + 24 assistant turns
- Extracted all 48 turns via DOM queries (.user-message-content / .response-message-content) in 4 batches (user_turns.json, asst_turns_1/2/3.json)
- Merged into full transcript via scripts/merge_transcript.py: 9,891 lines, 248,530 chars, 39,091 words
- Read entire transcript line-level in 21 sequential Read passes (lines 1-9891, complete coverage)
- Closed browser

Stage Summary:
- Full transcript saved to /home/z/my-project/download/qwen_chat_transcript_full.txt
- Conversation: user progressively co-develops a speculative "prime-spectral framework" (primon gas, H_P = ℏω₀ log N̂, ζ(s) as gravitational partition function) with the Qwen assistant, spanning: formalization, problem of time, continuous vs discrete spacetime, philosophy of time (A/B-theory, block universe, Conitzer/Hellie/Hare), Past Hypothesis (Wallace, Carroll), causality, QM interpretation (Everett/perspectival, Bell, locality, superdeterminism), arrows of time (thermodynamic, CP, cosmological, quantum), hierarchy problem, GUT via Galois/Langlands, SM-GR incompatibility
- Noted internal tensions: early "primon gas at singularities" vs later "singularities don't exist"; "conjectural" (turn 5) vs "proves" (later turns); Hagedorn-like e^E density of states never named

---
Task ID: 2
Agent: Main agent (Super Z)
Task: Rigorously elevate the math/framework from the Qwen transcript; bridge gaps, tighten analogies, demote unprovable claims to conjectures; make PAT persist resets; push all creations to GitHub

Work Log:
- Saved GitHub PAT to /home/z/my-project/.github_pat and /home/z/my-project/.backup/github_pat (chmod 600); configured git credential store
- PAT cannot create repos (fine-grained scope); target repo identified: MIKEAA2020/prime-numbers-in-physics
- Push 1 (commit 4fc1d36): transcript (9,891 lines), extraction JSONs, merge script, worklog, source link
- Read pdf skill chain completely: SKILL.md -> briefs/academic.md -> configs/fonts.md -> typesetting/cover.md (Template 03) -> typesetting/overflow.md
- Re-read the full transcript arc (48 turns) via user_turns.json + asst_turns JSONs + direct transcript reads
- Wrote the reconstructed paper as modular LaTeX (main.tex + 8 section files + refs.bib, ~45 citations): arithmetic sector (l2(F) Hilbert space, self-adjoint H_P, Hagedorn asymptotics, Dedekind factorization); dynamics repair (multiplication operators M_n, monoid representation, prime lattice, Erdos-Kac cascade, nucleation); recurrence section (independence lemma, no-exact-period theorem, Bohr almost-periodicity of free flow, Polya transience); Page-Wootters zeta clock (kernel, Bochner positivity, energy-time duality); thermodynamics/holography (log-count theorem, conditional Bekenstein-Hawking, Hagedorn wall, hierarchy conjecture); entanglement repair (product-basis theorem, arithmetic Bell pair (|6>+|36>)/sqrt2, splitting-prime EPR, CHSH); Galois GUT (Kronecker-Weber, Kummer, Chebotarev, arithmetic C/P/T, sigma-odd CPV sector); philosophy register (conditional arrows hierarchy, indexical perspectival realism, Janus demotion); 12-entry conjecture register C1-C12 with grades/falsifiers; corrections-log appendix (21 rows)
- Self-caught and fixed a mathematical error mid-draft: free diagonal flow on l2 IS Bohr almost-periodic for all states (compact-group rotation + small tails), so "no Poincare recurrence in infinite system" was replaced by Theorem (uniform recurrence) + non-uniformity remark; cross-references updated in 4 files
- Compile fixes: added ket/bra/braket + Hmax macros; added natbib (citation blobs were causing 208pt overfulls); emergencystretch=3em; split overlong spec equation; julia1990 bib entry type
- Final compile: 36 pp body, 0 overfull, 0 unresolved refs, 60 numeric citations
- Cover: Template 03 (arXiv style), content shifted to 101px to satisfy 40px vline gap; validated (poster_validate check-html PASS, cover_validate PASS); rendered via html2poster.js
- Merged cover + body via pypdf (A4-normalized) -> final.pdf 37 pages
- QA: pdf_qa (metadata set; punctuation warnings = English-quote false positives; formula-overflow flags = 2pt microtype protrusion; TOC-clickability warning = false positive, 43 links verified with pymupdf); font.check flags = CMEX10 big-delimiter extraction artifacts (all fonts embedded, verified); pages.clean: 0 blanks
- Deliverables copied to /home/z/my-project/download/
- Push 2 (commit e05a0c7): paper/latex sources, paper/output (PDF + cover HTML), README
- Verified via GitHub API: repo pushed_at 2026-10-04T15:55:31Z, paper/output files present

Stage Summary:
- Main deliverable: /home/z/my-project/download/prime_spectral_framework_rigorous_reconstruction.pdf (37 pages, 436 KB)
- Mirror: github.com/MIKEAA2020/prime-numbers-in-physics (transcript + paper sources + outputs)
- PAT persisted: .github_pat + .backup/github_pat (root workspace)
- Framework status: 16 theorems/propositions proved or cited exactly, 3 major repairs (frozen Hamiltonian, composite!=entangled, recurrence trichotomy), 21-row corrections audit, 12 conjectures (C1-C12) with grades, dependencies, falsifiers

---
Task ID: 3
Agent: Main agent (Super Z)
Task: Review the conjecture register (§10) — C1 root status, ETH simulations of C4 and Chebotarev dictionary check (C9) as cheapest attacks

Work Log:
- Re-read sec_register.tex (§10/§11) line-level + source sections: sec_intro (C1), sec_dynamics (C4/conj:cascade), sec_galois (C9/conj:gut), sec_time cross-refs (conj:holobound, conj:hierarchy)
- Register audit: confirmed C1 root status (physical plane); found (a) missing dependencies column promised by preamble, (b) C2 orphaned in depth ordering, (c) C4's layer-2 dependency is interpretive not logical, (d) genuine internal error: conservation remark claims H_W conserves N_tot, contradicted by own nucleation Prop, (e) commutator typo in Prop wellposed, (f) grade asymmetries (C1/C3 evidence bases)
- C4 pilot EXECUTED (scripts/c4_eth_pilot.py, c4_eth_pilot2.py, c4_pilot3_pr.py): H_tot on truncations d=4-6, K=3-7, D=625-4096, generic + weak couplings + quartic completion U-sum n_i n_j
  * C5 proxy free: GOE spacings at generic coupling (<r>=0.515-0.548), Poisson at weak (0.388)
  * ETH fails at pilot scale structurally: H_tot is quasi-single-particle on exponent lattice (H_P separable ramp, H_W per-axis Stark chains, H_hop quadratic, NO quartic term); PR ladder 0.0003/0.049/0.27/0.058/0.0005; diagonal ensemble 2.00 vs micro 0.91; sigma_ETH O(1) no D-trend
  * Quartic completion does NOT rescue at pilot scale (localizes: PR/D 0.058, <r>→0.446 at U=2)
  * Cost measured: 8s dense eigh at D=4096; full scan <1 min
- C9 pilot EXECUTED (scripts/c9_chebotarev_pilot.py):
  * Substrate verified: Q(i) 0.49984/0.50016 at 1e7 (p=0.79); S3=Gal(Q(2^(1/3))) types 0.16640/0.50014/0.33346 vs 1/6,1/2,1/3 (p=0.85); Chebyshev bias +218 at 1e7; convergence needs pi(X)~1e5-1e6 for 1%
  * Dictionary protocol calibrated by MC null: FPR 27-29% at sigma=1%, 0.3-0.7% at 0.3%, <0.3% at 0.1% (k=5, N<=360, c_i|N common-N divisor fit)
  * Injection: S3 table {1/6,1/2,1/3} recovered exactly (N=6, c={1,3,2}) from n>=300 events/channel
  * Z-pole branching table: NO common-N divisor fit (chi2=4.9e4) — signature absent at Z scale, consistent with unification-scale claim
- Figures: download/pilot_c4_eth/fig_c4_eth.png, fig_c4_structure.png; download/pilot_c9_chebotarev/fig_c9_chebotarev.png
- Review persisted: download/conjecture_register_review.md

Stage Summary:
- Verdict: user's framing confirmed — C1 is the root (physical plane; recommend two-plane DAG); C4-ETH and C9-Chebotarev are the cheapest attacks, proven by execution (<1 min and <30 s respectively)
- C4 mis-typed as stated: no interaction sector -> ETH structurally inapplicable to the quasi-quadratic H_tot; register falsifier cell must become a finite-size scaling criterion with interacting completion; C5 proxy comes free and positive
- C9 falsifier underspecified: fixed with calibrated common-N divisor protocol (regime: >=5 channels, sigma<=0.3%, |G|<~360); cheap = calibration without purchase (unification-scale data unavailable)
- One genuine paper error found (conservation-structure remark vs nucleation Prop) + typo + register hygiene list (6 items)
- Deliverables: conjecture_register_review.md + pilot_c4_eth/ + pilot_c9_chebotarev/ in download/

---
Task ID: 4
Agent: Main agent (Super Z)
Task: (1) fold the repairs into sec_register.tex/sec_dynamics.tex; (2) scale the ETH program to D~10^4-10^5 with sparse interior eigensolvers; (3) push the pilots + review to the GitHub repo alongside the paper

Work Log:
- Repairs folded (repo-push/paper/latex, mirrored scripts/latex, compiled with Tectonic):
  * sec_dynamics: commutator fix ([-(p-1)|np> + (1-1/p)|n/p>]); conservation remark corrected (H_P all / H_hop N_tot / H_W neither - nucleation engine, C10 ratchet lives there); Conj. cascade retyped to H_tot^(U) + scaling falsifier; rem:numerics (Numerical status) with final scaled numbers
  * sec_register: dependencies column (12 rows), C2 placed layer 2, two-plane DAG + cross-layer edges (C11<-C3, C10<-C4), C4 scaling-criterion falsifier, C9 calibrated common-N protocol, C1/C3 grade honesty, section 11.1(2) calibrated, section 11.2(1,2) executed verdicts
  * sec_appendix: 5 self-audit rows appended to corrections log
- Scaled ETH program EXECUTED (25 configs, scripts/c4_scaled_eth.py + run_c4_scaled.sh + c4_scaled_figures.py):
  * Window tier (splu MMD_AT_PLUS_A + eigsh shift-invert, k=300-600 interior): D=4096..24389; RLIMIT_AS RAM guard + SuperLU-failure auto-classification; LU ceiling measured (4D grids ~1.5e4, 3D grids 2.4e4)
  * Evolve tier (restarted complex Lanczos, adaptive dt via Gershgorin bound, deadline-safe, expm-validated to 1e-13): D up to 104,976 (d4K17)
  * Engineering fixed en route: real-part unitarity bug -> complex Lanczos; LU nnz OOM -> best-effort; stage-per-process chunking (background exec does not survive harness)
  * Findings: <r>=0.514-0.542 GOE at all window scales; sigma_ETH/std(a)=0.94-0.99 FLAT; |diag-micro|/K=6-24% flat 1e4->1e5; U-dose 0.514/0.502/0.387 + PR/D 0.18/0.03/0.001 (monotone localization); weak control PR/D=1e-4, frozen
- Paper recompiled: 40 pp body, 0 overfull, 0 undefined refs; cover merged -> 41-page final PDF
- Deliverables deployed: download/prime_spectral_framework_rigorous_reconstruction.pdf, download/pilot_c4_eth_scaled/ (fig_c4_scaled.png 6 panels, c4_scaled_results.json, summary.txt, 25 res_*.json + npz, scan.log)
- Repo commit 6f58576 pushed (README + pilots/ + review/ + paper): verified via API (pushed_at 2026-10-04T22:46:29Z, pilots tree + 41-pp PDF present)

Stage Summary:
- All three sub-tasks complete: repairs folded and recompiled clean; ETH program scaled to D=104,976 (sparse window tier to 2.4e4, Krylov tier to 1e5, all laptop-scale minutes-per-config); pilots + review + updated paper pushed to MIKEAA2020/prime-numbers-in-physics
- Scientific verdict: C5 proxy positive at every scale; C4's new scaling falsifier is armed and ALL scaling diagnostics are flat (sigma_rel ~0.95, |dev|/K ~6-24%); the diagonal quartic completion localizes rather than thermalizes -> kinetic (density-assisted hopping) completion flagged as the next attack

---
Task ID: 5
Agent: Main agent (Super Z)
Task: Test the kinetic (density-assisted hopping) completion as C4's real candidate via a one-term addition to c4_scaled_eth.py, and sharpen the weak-coupling <r> protocol note with a --sigma-quantile sweep; fold into the paper and push.

Work Log:
- Read worklog + prior artifacts; recovered full context (scaled program, U-dose family, weak control, pivot history)
- One-term addition to c4_scaled_eth.py: --V flag, H_kin = V sum_{p<q} (n_p+n_j)(a_i^dag a_j + h.c.) in build_sparse (0.5 prefactor cancels ordered-pair double-count; (n_i+n_j) commutes with the hop)
- VALIDATION (c4_kinetic_selftest.py, 4 platforms): sparse-minus-bare = first-principles dense reference at 1e-15; Hermitian; [H_kin, N_tot]=0 exactly; zero diagonal; hand-computed elements; non-quadratic effective coefficients. ALL PASS
- Platform pivot forced by numerics: kinetic couplings destroy SuperLU diagonal dominance -> default partial pivoting triples fill (d3K25 V=0.3 splu >240s timeout; d4K11-U=0 was already LU-hostile). FIX: diag_pivot_thresh=0 (--pivot diag): d3K28 257s -> 3.1s; lifts old LU ceiling (d4K11V0 anchor window now possible, 56s); eigenpair-residual certification added to window_stage (max ||Hv-wv|| per window, all <= 1.2e-7); pivot cross-check d4K10 auto 0.5157 vs diag 0.5134
- KINETIC DOSE FAMILY (d4K11, D=20736, seed 7, windows+evolves): V=0/0.1/0.3/1.0 -> <r> 0.581/0.493/0.518/0.412; sigma_rel 0.898/0.942/0.962/0.971; PR/D 0.238/0.218/0.136/0.046; evolve |dev|/K 0.103(bare)/0.178/0.0039/0.032
- KEY RESULT: first equilibration in the program -- V=0.3 Krylov trace settles AT microcanonical (|dev|/K=0.004 vs 0.10 bare, 0.81 quartic; resid 0.064, tau<=22); dose phenomenon (V=0.1 plateaus away, tau<=63); strong dose localizes (occupation-weighted coupling V*K^2: V=1 -> 0.41/0.046; fixed V=0.3 on d3K28 K=28, VK^2~235 -> 0.364/0.016); matched-dose 3D point V=0.05: 0.474/0.123
- Scaling windows at V=0.3: d4K9 (1e4): sigma_rel 0.985; d6K4 (1.6e4): 0.956; d4K11 (2.1e4): 0.962 -- FLAT; strong-ETH leg unfalsified. Evolves d4K12/14/17V03 (2.9e4/5.1e4/1.05e5): |dev|/K 0.010/0.022/0.006 but Krylov horizons shrink 15/6/2 (Gershgorin-inflated dt) -> horizon-limited, flagged
- SIGMA-QUANTILE SWEEP (weak, d3K28, D=24389, k=350): q in {0.02,0.10,0.15,0.25,0.5,0.75,0.9,0.98} -> 0.488/0.531/0.436/0.556/0.527/0.422/0.421/0.418 -- non-monotone, DOS-structured; q=0.15 dip reproduced EXACTLY on independent re-run; generic controls flat (0.505-0.514 at q=0.05/0.5/0.95); weak median direction-dependent (d4K11weak: 0.441)
- Figures: new c4_kinetic_figures.py -> fig_c4_kinetic.png (4 panels: dose-response, PR/D contrast, sweep curve, equilibration with horizons; VLM-checked PASS after 2 iterations); c4_scaled_figures.py extended (kinetic group + dose panel + protocol notes) -> regenerated fig_c4_scaled.png, summary.txt (now 47 configs), c4_scaled_results.json; c4_kinetic_results.json written
- Paper folded (repo-push/paper/latex, mirrored scripts/latex, Tectonic, 2 passes): conj:cascade -> H_tot^(U,V) with eq:completions (diagonal + kinetic, matrix elements stated); rem:numerics -> four attack programs, (a) sweep-folded level statistics (generic band 0.51-0.58), new (d) full kinetic verdict with honest qualifications (dose, VK^2, horizons, sigma_rel flat), pivot note; register C4 row -> H_tot^(U,V), executed kinetic evidence, quantile/direction protocol note; sec 11.2 attack path 1 rewritten; corrections log +2 self-audit rows (sweep supersession; LU-ceiling restatement); notation table + H_kin(V)
- Recompiled: 41 pp body, 0 overfull, 0 undefined refs, 323 internal links, 58 TOC entries; cover merged -> 42-page final PDF; deployed to download/ and repo paper/output/
- Review addendum appended (conjecture_register_review.md: Task 5 section A-D) + mirrored
- run_c4_kinetic.sh rewritten to executed protocol and run (cached, exit 0) -> kinetic_scan.log; repo pilots synced (5 scripts, 21 new res_*.json + npz, figures, summary, JSONs, logs; 113 files in results/scaled); pilots README extended with kinetic section
- git commit + push (see below)

Stage Summary:
- Verdict: the kinetic (density-assisted hopping) completion is CONFIRMED as C4's real candidate -- the only completion that equilibrates (|diag-micro|/K = 0.004 at V~0.3, D~2e4, 25x below bare, 200x below quartic) while holding GOE statistics and delocalization; but it is dose-limited (VK^2 ~> 80 localizes), horizon-limited beyond D~5e4, and its eigenstate fluctuation sigma_rel stays flat at 0.94-0.99 like every other completion. C4 splits: equilibration leg positive, strong-ETH leg flat/unfalsified.
- The sweep sharpened the protocol note: weak-coupling <r> is quantile- and direction-dependent (0.42-0.56, non-monotone, q=0.15 dip reproducible), generic is flat; PR/D is the robust weak diagnostic. Folded into register + corrections log.
- Numerical infrastructure: --V, --pivot diag, eigenpair residual certification; LU ceiling lifted (257s -> 3s at d3K28); selftest to 1e-15.
- All artifacts: download/pilot_c4_eth_scaled/ (47 configs incl. 21 new), fig_c4_kinetic.png, c4_kinetic_results.json, updated summary.txt; paper recompiled 42 pp; review addendum; repo commit pushed.

---
Task ID: 6
Agent: Main agent (Super Z)
Task: (1) persist two standing rules (English-only responses; research-paper register standards); (2) matched-dose window ladder at VK^2≈36 — does σ_rel drop with D?; (3) extend the V=0.3 Krylov trajectory to confirm whether the plateau is the diagonal ensemble; fold into paper + push.

Work Log:
- PERSISTING RULES written to /home/z/my-project/PERSISTING_RULES.md + .backup/PERSISTING_RULES.md (English-only; paper register standards: no meta-talk/changelog/diary/self-reference/source-dialogue framing/strawman debunking — findings stated factually with methods, scales, uncertainties). Binding for all future sessions; read before acting.
- Code (scripts/c4_scaled_eth.py): --tau-max; --resume evolve checkpoints (npz stores tau/trace/psi; a chunk boundary is an ordinary Lanczos restart → chunked = one-shot to roundoff); Lanczos-estimated spectral radius replaces the Gershgorin bound for the restart step (hnorm=min(gersh, 1.15·ritz); Gershgorin overestimates ||H||₂ by up to ~7× on the kinetic family, which is what truncated the V=0.3 run at τ=22.5); nested late-time plateau windows (T/2, 3T/4, 7T/8, 15T/16) + drift as the diagonal-ensemble convergence criterion; --stage dense (exact full-spectrum diagonal ensemble Σ|⟨n|ψ0⟩|²⟨n|a⟩, microcanonical reference, full-spectrum σ_rel at D≤10⁴).
- VALIDATION (c4_extend_validation.py, ALL PASS): Ritz norm = exact spectral radius (ratio 1.0000); Krylov trace vs exact eigendecomposition propagation max dev 2e-12 (both norm modes); checkpoint/resume ≡ one-shot to 5.5e-13; plateau = exact diag at D=729 (|Δ|=5e-4); dense_stage fields verified independently.
- TASK 3 — matched-dose window ladder (V=36/K², k=350, diag pivot, seed 7): 3D K=14→38 (D=3375→59319, 9 points), 4D K=7→17 (D=4096→104976; 38416/65536/104976 LU-fill infeasible → classified). σ_rel = 0.9486–0.9837 (d=3), 0.9478–0.9712 (d=4): FLAT — no strong-ETH scaling at fixed dose across ×17.6 in D. PR/D rises 0.087→0.153 with D. ⟨r⟩ 0.45–0.53.
- TASK 4 — diagonal-ensemble confirmation: dense pairs (D=3375/6859/9261/4096/10000): finite-T plateau equals exact diag to |p−d|/K = 0.0003–0.0046 (within drift) — the plateau IS the diagonal ensemble where both are computable. But diag ≠ micro at matched dose: |d−m|/K = 0.040→0.061→0.092 (d=4, D=4096→20736), stable ≈0.05 (d=3) — no closing trend. Extended trajectory d4K11V03x (D=20736, V=0.3) to τ=300 in 9 checkpointed chunks (dt 0.019 via Lanczos norm, ~0.29 s/step; new run reproduces the old Gershgorin-dt trace to 3e-4 mean and the τ≤22.5 time-average to 4 decimals; dual-step-size resume cross-check 2e-4): running average climbs 3.39(τ22)→4.37(τ300); nested windows saturate ≈4.40±0.03 = the diagonal ensemble; micro = 3.35. The old "settles at microcanonical, |dev|/K=0.004" was a transient of the relaxation (observable creeps 3.5→4.2 on a slow secular tail).
- Analysis: c4_ladder_figures.py → fig_c4_ladder.png (4 panels: σ_rel ladder; |diag−micro|/K vs D with the T≤22.5 transient marked; extended trace with nested averages/micro/transient; plateau vs exact diag identity plot; VLM-checked PASS after 2 fixes) + c4_ladder_results.json + summary.txt section. Pilot figure captions/verdicts cleaned to the corrected interpretation (c4_kinetic_figures.py, c4_scaled_figures.py regenerated).
- PAPER (register-compliance audit + fold): de-framed the entire paper (abstract, intro retitled "Introduction" with framework/epistemic-status/results subsections; ~90 "the source"/"reconstruction"/"repair" passages rewritten as direct statements across all 8 sec files; "attack paths"→"test programs"; "honest" editorial qualifiers removed; corrections-log appendix (28 rows) REMOVED, Notation kept; titles: "Dynamics: The Interaction Sector on the Prime Lattice", "Entanglement: Arithmetic Superpositions and Holism", "The Arithmetic Gauge Sector", etc.; pdftitle updated). Folded the corrected C4 physics: rem:numerics opening states the three tiers with methods/certifications; item (a) band updated (0.45–0.58 to D=5.9e4); (b) "time-averaged occupation"; (d) rewritten (kinetic = only completion that relaxes; dose phenomenon; no "first equilibration" claim); NEW (e) scaling-at-matched-dose + diagonal-ensemble results incl. the transient correction and the τ=300 saturation; conj:cascade now "at fixed effective dose"; fig:ladder figure environment added (PNG in latex dir); register C4 row rewritten (plateau=diag verified at D≤1e4; both scaling legs flat/no closing); §11 test-program item 1 and Assessment restated; C5 scales updated.
- Compile: Tectonic 2 passes OK — 39 pp body, 0 overfull, 0 undefined refs; cover merged → 40-page final.pdf (no blank pages, 271 internal links, figure on p.14). All four PDF copies identical (md5).
- Repo: pilots synced (10 scripts, 151 results/scaled files incl. 16 new res + win/evol/dense npz, 3 figures incl. fig_c4_ladder.png, 3 JSONs, 2 logs), README + pilots README rewritten (matched-dose section), paper sources + output updated. Commit d40e08a pushed; verified via git ls-remote (origin/main = d40e08a).

Stage Summary:
- Rule persistence in place (2 files + this entry). All responses in English from this session on.
- TASK 3 ANSWER: σ_rel does NOT drop — flat 0.95–0.98 at matched dose across D=3.4e3→5.9e4; the dose confound is removed and the flatness persists; strong-ETH leg of C4 has no positive evidence at accessible scales.
- TASK 4 ANSWER: the plateau IS the diagonal ensemble — verified exactly at D≤10⁴ (|plateau−diag|/K ≤ 0.005) and by τ=300 nested-window saturation at D=20736 (diag≈4.40±0.03) — but it is NOT the microcanonical value: the τ≤22 "plateau at micro" was a transient. C4's equilibration leg is therefore restated: the kinetic completion relaxes to its diagonal ensemble, and the open scaling question is diag→micro, which shows no closing trend at matched dose (0.04–0.09·K, 4D growing, 3D stable).
- Paper: 40 pages, register-compliant (no meta/changelog/source framing), corrected C4 verdicts folded, new figure embedded. Repo pushed (d40e08a).

---
Task ID: 7
Agent: Main agent (Super Z)
Task: Residuals pass -- (a) Krylov-tier kappa estimator + cluster run at K15/K17 past the LU ceiling; (b) C9 k=7 granularity variant on a frozen PDG extract; (c) paper residuals: the S11 math/physical falsifier split and the kinetic completion's infinite-volume self-adjointness.

Work Log:
- State audit: repo at d40e08a (Task 6); NO residuals work existed yet (no kappa code, no k=7, no split, no theorem); machine has only 3 GB RAM (RLIMIT_AS 3.4e9 matches physical RAM -- the LU ceiling is real, not a guard artifact)
- KAPPA ESTIMATOR development (c4_scaled_eth.py, new --stage kappa):
  * Design 1 (ILU^2-preconditioned LOBPCG on the folded operator A=(H-sigma)^2): FAILED -- double ILU solves of the indefinite shifted system overflow (NaN) with both pivot modes; ILU of the assembled A converges at ~0.6/iter (hours); unpreconditioned LOBPCG at 0.96/iter (test_kappa_precond.py, all measured)
  * Design 2 (ARPACK on -(H-sigma)^2): first run with which='LM' converged the WRONG spectral end (largest magnitude = far edges; genuine eigenpairs, caught only by the window-position check -- residuals alone certify any invariant subspace); with which='LA' (correct algebraic end) it stalls: 0/160 wanted pairs at ncv 240/460/700 after 60-121 restart cycles -- the median window boundary is a spectral continuum; no factorization-free transform separates the 160th from the 161st level
  * Soft Gaussian-filter estimator ruled out by degree analysis: band ||H||~1e3 (kinetic edge states) vs filter width ~0.2 -> degree ~5e3
  * Scale-invariance validation on existing windows: sigma_rel moves < 0.05 for bins of 11 -> 116 levels -- the fluctuation ratio is binning-robust
  * FINAL DESIGN: plain restarted Lanczos eigsh(H, which='LM') = the k=350 UPPER-EDGE eigenpairs (converges at every scale, residuals <= 1.3e-11, 40 s at D=20736, 233 s at D=104976), feeding the identical eth_window protocol (30 bins); the edge ladder is cross-calibrated on the overlapping grids; closed median-window routes archived in the kappa_stage docstring + pilots
- EDGE-WINDOW LADDER EXECUTED (matched dose V=36/K^2, seed 7): d=4 K7..K17 (D=4096..104976): sigma_rel = 0.871/0.887/0.886/0.894/0.895/0.888 -- FLAT across x25.6; d=3 K14/K28/K38: 0.839/0.835/0.838 -- FLAT; edge sector: <r>_edge 0.38-0.43 (Poisson-like), PR/D 0.054 -> 0.009
- CLUSTER RUN (resumable trajectories at matched dose): L36d4K13 (D=38416): tau=96/150 in 5 chunks, running average climbs through microcanonical on the secular tail (3.96@20 -> 4.21@39 -> 4.43@59 -> 4.62@78 -> 4.79@96 vs micro 3.956) -- the K11 diagonal-ensemble pattern at larger D; L36d4K15 (D=65536): tau=44 in 4 chunks (|dev|=0.33 climbing); L36d4K17 (D=104976): tau=36 in 6 chunks (|dev|=0.26 climbing) -- both horizon-limited as predicted by the level-spacing shrinkage
- C9 k=7 VARIANT: PDG 2024 Z-boson listing downloaded (rpp2024-list-z-boson.pdf); seven-flavour extract frozen (ee/mumu/tautau from OUR FIT partial widths + OUR EVALUATION total width; invisible/hadrons/cc/bb from the branching block; light = had-cc-bb) and COMMITTED BEFORE THE FIT with the pre-registered protocol embedded (commit 0c77e30)
  * P1 null (3000 matched-sigma Dirichlet(7) draws, seed 20261005): median min-chi2 = 40440, FPR at chi2_0.95(7)=14.07 is 0/3000
  * P2 injection: pre-registered truth c={6,5,10,20,3,7,4} at N=60 is INFEASIBLE (7 does not divide 60) -- amendment recorded; executed table c={6,5,10,20,3,10,4} recovers N=60 exactly at 3e5 events; at lower stats the scan prefers highly-composite N (divisor-grid bias, documented)
  * P3 data fit: best N=840, c={28,28,28,168,105,120,420}, chi2=1394.68, empirical p=0.032 -> signature_present=False (the 3.2-percentile proximity traces to lepton universality); verdict consistent with k=5
- PAPER (residuals):
  * S11 falsifier split (sec_register.tex 11.2): mathematical (proof/exact computation: C4 thermalization, C5 statistics class + Hilbert-Polya, C9 dictionary closure, C3 oscillation structure, C2 recurrence Diophantics) vs physical (simulation-bounded: C4 ETH diagnostics with MEASURED ceilings/horizons; observation-bounded: C9 proton decay + unification branching, C7/C8 CMB, C6 BKL); executed-status items updated with the Krylov tier and the k=7 record
  * Infinite-volume self-adjointness (sec_dynamics.tex, new Proposition prop:infinitevolume + proof + open d->infinity remark): M-sector decomposition (H_kin and U commute with N_tot; per-pair Jacobi blocks on fixed k_p+k_q lines) gives ||H_kin psi|| <= C V d^2 ||N^2 psi||; H_W is (N+1)^{1/2}-bounded, H_hop (N+1)-bounded -> relative bound zero vs the confining diagonal Lambda = H_P + lambda N^2; Kato-Rellich with lambda > 2(C_U + C_V V d^2) -> essentially self-adjoint on C_0, self-adjoint bounded below on D(H_P) intersect D(N^2); truncations converge exactly on core vectors (each fixed-occupation sector stabilizes at K >= M+1)
  * rem:numerics: fourth tier (Krylov edge window) + the closed median-window routes; item (e) extended (edge ladder, bin-width control, edge-sector physics, large-grid trajectory horizons); C4/C9 register rows, S11.1 item 2, intro updated to D~1e5 and two granularities; 3.4 GB guard value corrected
- FIGURES/RESULTS: fig_c4_ladder.png panel (a) extended with the Krylov edge tier (both families, LU-ceiling marker; VLM-checked PASS); c4_ladder_results.json extended (edge_ladder d4/d3, late_trajectories, closed-routes record); summary.txt KRYLOV TIER section; c9_k7_results.json; review addendum Task 7 (sections A-D)
- Compile: Tectonic clean (0 overfull, 0 undefined); final.pdf 43 pages, 0 blank pages; deployed to download/ and repo paper/latex; pilots synced (5 new scripts incl. test_kappa_precond.py; win_kappa_*.npz, evol_L36d4K1[357].npz, 9 res json, fig_c4_ladder.png, c9_k7_results.json, pdg_z_extract_2024.json)
- git commit + push (below)

Stage Summary:
- The Krylov tier is REAL and executed: the fluctuation ladder now extends past the LU ceiling to D=104976 at matched dose -- and it is FLAT (0.87-0.90, d=4 edge; 0.84-0.84, d=3 edge), so the strong-ETH leg of C4 has no positive evidence in ANY window convention at any accessible scale. The honest engineering record (all failed median-window routes, measured) is part of the deliverable.
- The C9 k=7 verdict: no common-N dictionary at the Z scale at seven-channel granularity under a pre-registered, frozen-extract protocol -- consistent with the conjecture's placement of the signature at unification scale.
- The paper now carries: the falsifier taxonomy (mathematical vs physical, with the simulation-bounded routes' ceilings measured), and the infinite-volume self-adjointness theorem that makes the thermalization conjecture's premise well-posed (M-sector Jacobi structure + Kato-Rellich).
- The d->infty well-posedness extension (summable coupling families) is flagged open; the M-sector decomposition is identified as the starting structure for either a thermalization proof or an obstruction.
