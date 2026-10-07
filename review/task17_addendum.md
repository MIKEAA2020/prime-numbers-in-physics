# Task 17 addendum — the multiplet-dipole control, executed

## Scope

The complementary completion route of the obstruction theorem, left open by
the Task 16 replica bound. The choice among the three offered continuations
was resolved on the record: the K15/K17 polish is decision-empty against
the executed bound (Task 16's own decision record); the propagation
extension past the dense tier widens the certified scale of an already
settled verdict at priced overnight wall-clock; the multiplet-dipole
control completes the theorem by an independent mechanism and carries the
explanation of the obstruction. This route was executed.

## The construction (`c4_msector_dipole.py`)

**The operator-isotypic selection rule (new, exact).** K - (S/d)I lies in
the rho_d-isotypic component of the operator space under conjugation, with
rho_d the (d-1)-dimensional simplex irrep (the standard irrep at d=3, [31]
at d=4): the conjugation orbit of the diagonal operator k_1 spans
{k_1, ..., k_d} with the mean removed. Hence the isotypic block
P_l K P_m vanishes unless l is contained in m (x) rho_d, and the diagonal
block P_l (K - (S/d)I) P_l vanishes on every non-self-coupled isotypic —
trivial and sign at d=3, additionally [22] at d=4: the occupation identity
<K> = S/d extends beyond the one-dimensional isotypics. The
trivial<->sign block vanishes identically. Confirmed block by block: the
d=4 vanishing blocks ([1111]|[4], [1111]|[22], [1111]|[31], [22]|[4],
[211]|[4], and the diagonal [22] block) at the 1e-17 level; every identity
to 5e-14; the a-decomposition to 2e-13 at every rung.

**The channel decomposition (Parseval-exact).** With the corrected
projectors P_l = (dim l/d!) sum_pi chi_l(pi) P_pi (the earlier
c4_msector_symmetry.py projectors_s3 built the standard projector without
the dimension factor and with the trivial/sign characters swapped —
repaired and re-validated: resolution exact, idempotence 4e-16, K-blocks
9e-16), the window K-matrix decomposes as KW = sum_{l,m} Y_l^T K Y_m and
the fluctuation operator X~ = KW - (S/d)I over the selection-rule channels
(5 at d=3: the std-std channel of K~ plus the four 1-D<->standard mixed;
10 at d=4). Measured architecture, scale-invariant along the ladder:
X~'s Hilbert-Schmidt mass splits at 33% standard-internal / 67% mixed
1-D<->standard dipoles at every d=3 rung (S=20 -> 116); the aggregate
isotypic content tracks the dimension fractions at every rung.

**The budget obstruction (the no-go).** Three natural families, each
decided:

- Affine: the strongest single-copy-affine lower bound on the loop has
  slack exactly sum_j (a_j - S/d)^2 — the fluctuation itself (validated to
  1e-11). It certifies the bulk (97.8% of the loop at S=60) and never the
  margin: the certified variance from it is identically <= 0.
- Channel: for EVERY channel decomposition X~ = sum_c C_c, the Gram budget
  sum_{c,c'} |Tr(C_c^dagger C_c')| bounds the off-diagonal mass but is
  vacuous for the fluctuation — the Gram matrix is positive semidefinite,
  so the budget is at least ||X~||_HS^2 = fluctuation + off-diagonal.
  Measured: the budget exceeds the mass by at most 0.6% (the cross-channel
  interference) at every rung while the fluctuation is 7-15% of the mass;
  the per-entry Cauchy-Schwarz variant by factors 5.2-5.9 (d=3) and 20.9
  (d=4).
- Moment: offdiag_far <= M_p / g(delta)^{2p} with the exact difference
  moments M_p of the two-point measure overshoots the far mass by 3.3-4.0
  at the optimal threshold (delta at the mass-weighted decile) and by
  1.9e2-6.4e18 across the pre-registered delta grid: the off-diagonal
  dipoles are frequency-spread, not gap-concentrated.

Consequence (the necessity theorem): a certified lower bound on the
inter-multiplet dipole spread requires data outside all three families;
the two-copy Fejer kernel of the replica bound is such data and closes.
The replica route is necessary, not merely convenient.

**The multiplet census (every rung).** The surviving full-H pairs grow
0 -> 4 -> 48 -> 184 -> 412 -> 665 over S=20-116 (9.6% of the spectrum at
S=116; 64 of the 350 window states); the within-window pair dipoles carry
1e-16-1e-15 of the off-diagonal mass (the K-decoupling); the refined
splittings decay 1.4e-9 -> 2.4e-12 with within-pair occupation gaps at
the same floor; the paired subpopulation is fluctuation-silent (occupation
variance 1.8e-4 (S=60) to 6.5e-5 (S=116) of the unpaired variance). The
fluctuation is the unpaired inter-multiplet spread, carried by the
self-coupled isotypic content.

**Cross-validation.** The loop and surrogate reproduce the replica values
identically at every shared rung (63,535.2 / 143,111.4 / 253,035.4 /
398,236.1 / 535,719.3 / 5,770.3).

## Paper

- sec_dynamics.tex: new Proposition (prop:dipole) — the selection rule,
  the channel decomposition, the budget obstruction — with the proof
  sketch and the validation paragraph; rem:obstruction rewritten (the
  control executed, the necessity statement); rem:replica extended (the
  complementary route resolved); rem:numerics item (o).
- sec_register.tex: the C4 row (both completion routes executed; the
  residual program is the reach); the classes subsection (the budget
  theorem resolution); mathprograms item 1 (both routes executed, the
  necessity theorem); the Assessment.
- sec_intro.tex: the abstract clause.
- Compile: tectonic clean (0 overfull, 0 undefined, 0 "??"); 70 pp body;
  clean-dir flatten identical (70 pp); final.pdf 71 pp with cover.
- Deployed: download/ PDF + manuscript package; results
  pilots/c4_eth/results/c4_msector_dipole.json (+ the download mirror);
  the symmetry-script projector repair.

## Decision record

The three offered routes were adjudicated before execution: (iii)
K15/K17 is recorded by Task 16 as decision-empty against the executed
bound (the discovery phase completes; the certification tier is priced;
no decision changes); (i) the propagation extension carries certified
scale, not new content, at overnight wall-clock; (ii) the
multiplet-dipole control completes the theorem by the complementary
mechanism, cross-validates the certified constants, and explains the
obstruction. Route (ii) was executed; its outcome upgrades the register
from "the complementary route remains" to "the complementary route is
resolved as the necessity theorem for the two-copy route."
