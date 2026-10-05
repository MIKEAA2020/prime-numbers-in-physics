#!/bin/bash
# Matched-dose program for the C4 kinetic completion: VK^2 = 36 (the d4K11
# V=0.3 equilibrating point) held FIXED while the truncation ladder widens.
#
# Two legs:
#   (A) WINDOW LADDER -- interior eigen-windows at fixed dose across
#       d=3 (K=14..38, D=3375..59319) and d=4 (K=7..17, D=4096..104976),
#       k=350 eigenpairs everywhere, window at the median of the density of
#       states, diagonal pivoting in the shift-invert factorization.
#       Question: does sigma_rel = sigma_ETH / std(a) fall with D at fixed
#       effective dose (strong-ETH scaling), or stay flat?
#   (B) DIAGONAL-ENSEMBLE CONFIRMATION -- at grids where full
#       diagonalization fits in RAM (D <= 10000): the exact diagonal ensemble
#       sum_n |<n|psi0>|^2 <n|a|n>, the exact microcanonical reference, and
#       Krylov trajectories long enough that the nested late-time window
#       averages have converged; the finite-time plateau must equal the exact
#       diagonal ensemble. The d4K11 V=0.3 trajectory is extended to tau=1000
#       in wall-clock chunks (--resume; a chunk boundary is an ordinary
#       Lanczos restart, validated to roundoff in c4_extend_validation.py).
#
# Usage:  ./run_c4_ladder.sh <group>      group in: small mid large dense
#                                         evolve ext extloop
# One process per stage; stages already present in res_{tag}.json are
# skipped, so re-running a group is a no-op.
cd /home/z/my-project/scripts
OUT=/home/z/my-project/download/pilot_c4_eth_scaled
mkdir -p "$OUT"
LOG="$OUT/ladder_scan.log"
FAIL="$OUT/ladder_failures.log"
touch "$FAIL"

runstage() {   # runstage <tag> <d> <K> <V> <stage> [extra args...]
  tag=$1; d=$2; K=$3; Vv=$4; stage=$5; shift 5
  echo "=== $tag ($stage, D=$(( (K + 1) ** d )), V=$Vv, dose=36) ===" >> "$LOG"
  python3 c4_scaled_eth.py --tag "$tag" --d "$d" --K "$K" --V "$Vv" \
      --stage "$stage" --pivot diag --k 350 "$@" >> "$LOG" 2>&1 \
      || echo "FAILED: $tag $stage $*" >> "$FAIL"
}

grp=${1:-small}

case "$grp" in
small)   # fast window configs (D <= 1e4) -- one call
  runstage L36d3K14 3 14 0.1836735 window
  runstage L36d3K18 3 18 0.1111111 window
  runstage L36d3K20 3 20 0.09       window
  runstage L36d4K7  4 7  0.7346939  window
  runstage L36d4K9  4 9  0.4444444  window
  ;;
mid)     # one config per call (D ~ 1.2e4-3e4)
  runstage L36d3K22 3 22 0.0743802 window
  runstage L36d3K26 3 26 0.0532544 window
  runstage L36d3K28 3 28 0.0459184 window
  runstage L36d4K11 4 11 0.2975207 window
  ;;
large)   # one config per call (D >= 3.5e4); LU guard classifies infeasible
  runstage L36d3K30 3 30 0.04      window
  runstage L36d3K34 3 34 0.0311419 window
  runstage L36d4K13 4 13 0.2130178 window
  runstage L36d4K15 4 15 0.16      window
  runstage L36d3K38 3 38 0.0249307 window
  runstage L36d4K17 4 17 0.1245675 window
  ;;
dense)   # exact diagonal ensemble at D <= 10000 (one process each)
  runstage L36d3K14 3 14 0.1836735 dense
  runstage L36d3K18 3 18 0.1111111 dense
  runstage L36d3K20 3 20 0.09       dense
  runstage L36d4K7  4 7  0.7346939  dense
  runstage L36d4K9  4 9  0.4444444  dense
  ;;
evolve)  # Krylov trajectories at matched dose (plateau vs exact diag)
  runstage L36d3K14 3 14 0.1836735 evolve --tau-max 600 --deadline 500
  runstage L36d3K18 3 18 0.1111111 evolve --tau-max 600 --deadline 500
  runstage L36d3K20 3 20 0.09       evolve --tau-max 600 --deadline 500
  runstage L36d4K7  4 7  0.7346939  evolve --tau-max 600 --deadline 500
  runstage L36d4K9  4 9  0.4444444  evolve --tau-max 600 --resume --deadline 500
  runstage L36d4K11 4 11 0.2975207 evolve --tau-max 250 --deadline 500
  ;;
ext)     # d4K11 V=0.3 trajectory extension: ONE chunk toward tau=1000
  runstage d4K11V03x 4 11 0.3 evolve --tau-max 1000 --resume --deadline 500
  ;;
extloop) # extension until tau=1000 (up to 10 chunks in this call)
  for i in $(seq 1 10); do
    tau=$(python3 - <<'EOF'
import json
try:
    r = json.load(open("/home/z/my-project/download/pilot_c4_eth_scaled/res_d4K11V03x.json"))
    print(r.get("evolution", {}).get("tau_reached", 0.0))
except Exception:
    print(0.0)
EOF
)
    echo "chunk $i: tau_reached=$tau" >> "$LOG"
    if python3 -c "import sys; sys.exit(0 if float('$tau') >= 999.0 else 1)"; then
      break
    fi
    runstage d4K11V03x 4 11 0.3 evolve --tau-max 1000 --resume --deadline 500
  done
  ;;
*)
  echo "usage: $0 {small|mid|large|dense|evolve|ext|extloop}" >&2
  exit 2
  ;;
esac
echo "GROUP $grp DONE" >> "$LOG"
