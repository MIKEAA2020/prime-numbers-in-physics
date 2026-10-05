#!/bin/bash
# Driver for the C4 KINETIC completion program (density-assisted hopping)
# + the --sigma-quantile sweep that sharpens the weak-coupling <r> protocol note.
#
# Kinetic term:  H_kin = V sum_{p<q} (n_p + n_q)(a_p^dag a_q + h.c.)
#   -- validated by c4_kinetic_selftest.py (identity vs first-principles dense
#      reference 1e-15; Hermitian; [H_kin, N_tot] = 0 exactly; non-quadratic)
#   -- effective dose is occupation-weighted: ~ V*K^2
#
# Platform history: the dose family was first planned on d3K25, but the kinetic
# couplings destroy SuperLU's diagonal dominance and default partial pivoting
# triples the shift-invert fill (d3K25 V=0.3: splu > 240 s, timeout). The fix --
# diag_pivot_thresh = 0 (diagonal pivoting on the symmetric pattern) -- restores
# factorization in seconds AND lifts the old LU ceiling, so the dose family moved
# to the U-family platform d4K11 (D = 20736, same seed), where the V = 0 anchor
# was also measured for the first time (the auto-pivot window there used to fail).
# All eigen-windows are certified by eigenpair residuals <= 1.2e-7.
#
# One PROCESS per stage so every call fits a foreground wall-clock chunk; stages
# whose res_{tag}.json already contains their output are skipped (re-running this
# script is a no-op that regenerates kinetic_scan.log).
cd /home/z/my-project/scripts
OUT=/home/z/my-project/download/pilot_c4_eth_scaled
mkdir -p "$OUT"
LOG="$OUT/kinetic_scan.log"
FAIL="$OUT/kinetic_failures.log"
touch "$FAIL"

runstage() {   # runstage <tag> <d> <K> <stage> [extra args...]
  tag=$1; d=$2; K=$3; stage=$4; shift 4
  echo "=== $tag ($stage, D=$(( (K + 1) ** d )) ) ===" >> "$LOG"
  python3 c4_scaled_eth.py --tag "$tag" --d "$d" --K "$K" --stage "$stage" "$@" \
      >> "$LOG" 2>&1 || echo "FAILED: $tag $stage $*" >> "$FAIL"
}

# ---- 1. kinetic V-dose + V=0 anchor on the d4K11 platform (diag pivots) ----
runstage d4K11V0  4 11 window --pivot diag
runstage d4K11V01 4 11 window --V 0.1 --pivot diag
runstage d4K11V03 4 11 window --V 0.3 --pivot diag
runstage d4K11V10 4 11 window --V 1.0 --pivot diag
runstage d4K11V01 4 11 evolve --V 0.1
runstage d4K11V03 4 11 evolve --V 0.3
runstage d4K11V10 4 11 evolve --V 1.0

# ---- 2. pivot-mode control (d4K10 has an auto-pivot baseline) ----
runstage d4K10diag 4 10 window --pivot diag

# ---- 3. kinetic scaling / directions at V = 0.3 (+ matched-dose 3D point) ----
runstage d4K9V03   4 9  window --V 0.3 --pivot diag
runstage d6K4V03   6 4  window --V 0.3 --pivot diag
runstage d3K28V03  3 28 window --V 0.3 --pivot diag
runstage d3K28V03  3 28 evolve --V 0.3
runstage d3K28V005 3 28 window --V 0.05 --pivot diag   # matched dose: V*K^2 ~ 39

# ---- 4. kinetic Krylov equilibration to D ~ 1e5 (V = 0.3) ----
runstage d4K12V03 4 12 evolve --no-window --V 0.3
runstage d4K14V03 4 14 evolve --no-window --V 0.3
runstage d4K17V03 4 17 evolve --no-window --V 0.3

# ---- 5. sigma-quantile sweep at weak coupling (d=3, K=28, g0=0.05, h0=0.03) ----
for q in 002 010 015 025 075 090 098; do
  runstage d3K28wq$q 3 28 window --g0 0.05 --h0 0.03 --sigma-quantile 0.$q
done
# (q = 0.5 -> d3K28weak and q = 0.15 -> d3K28weakedge already on record; wq015 is
#  the independent re-verification that reproduced 0.4361 exactly)

# ---- 6. generic-coupling window-robustness controls + D-robustness of weak median ----
runstage d3K28q005 3 28 window --sigma-quantile 0.05 --pivot diag
runstage d3K28q095 3 28 window --sigma-quantile 0.95 --pivot diag
runstage d4K11weak 4 11 window --g0 0.05 --h0 0.03

echo "KINETIC_DONE" >> "$LOG"
