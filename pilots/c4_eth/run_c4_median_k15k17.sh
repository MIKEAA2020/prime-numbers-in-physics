#!/bin/bash
# Median-window Chebyshev tier at K15/K17 (d=4, matched dose VK^2 = 36):
# the turnkey rerun of the committed machinery on a machine with more RAM
# (and wall-clock) than the 3 GB / 2-core laptop on which the K13 platform
# (D = 38416, M = 3400, 14 sweeps, ~2.5 h in resumable chunks) was run.
#
# Machinery (unchanged, committed): c4_kappa_krylov.py -- block Chebyshev
# subspace iteration on (H - c)^2 with c the eps median, float32 discovery
# + float64 polish, Rayleigh-Ritz certification, stochastic-Lanczos count
# probe, resumable chunk state krs_{tag}.npz (a chunk boundary is an
# ordinary degree restart, so a chunked run equals a single run).
#
# Calibration carried over from the K13 platform:
#   * passband target 1.02 s (s = k + 66); the count probe overestimates
#     by 20-30% at the extreme narrowness (t/R ~ 1/460 at K13) -- if the
#     first Rayleigh-Ritz pass reports count_est >> count_in, apply the
#     K13-style correction:  --t-scale 0.78  (K13: t 1.236 -> 0.96).
#   * degree M = ln(1e4) R / (2 t): M grows ~ linearly in D
#     (888 at D = 1.0e4, 1500 at 2.4e4, 3400 at 3.8e4; extrapolated
#     ~5.5e3 at K15, ~9e3 at K17).
#   * m_chunk = 90, tol = 2e-6, max_sweeps = 16.
#
# Budget (K13-calibrated):
#   RAM: working set < 1.5 GB (block V D x s, count probes Q D x 360, H);
#        the 3.4 GB laptop guard is sufficient, --addr-limit 8 lifts it on
#        larger machines.
#   wall: ~7 h (K15), ~19 h (K17) at 2 cores; every invocation is capped
#        by --deadline and resumes from the checkpoint, so any chunk size
#        (laptop overnight included) makes the same trajectory.
#
# Usage:
#   ./run_c4_median_k15k17.sh k15     # the K15 platform
#   ./run_c4_median_k15k17.sh k17     # the K17 platform
#   ./run_c4_median_k15k17.sh both
#   ./run_c4_median_k15k17.sh demo    # 3-minute resume-cycle proof at
#                                     # d=3 K18 (the calibrated platform)
set -u
cd "$(dirname "$0")"
OUT=/home/z/my-project/download/pilot_c4_eth_scaled
mkdir -p "$OUT"

CHUNK_DEADLINE=${CHUNK_DEADLINE:-3600}
MAX_CHUNKS=${MAX_CHUNKS:-240}
TS=${TS:-1.0}
ADDR=${ADDR:-8}

done_tag() {   # a platform is done when its result json exists and the
  local tag=$1          # resumable state was removed on success
  [ -f "$OUT/res_krylov_$tag.json" ] && [ ! -f "$OUT/krs_$tag.npz" ]
}

run_median() {   # run_median <tag> <d> <K> <V> [extra args...]
  local tag=$1 d=$2 K=$3 V=$4; shift 4
  if done_tag "$tag"; then
    echo "$tag: already certified (res_krylov_$tag.json present, no state)"
    return 0
  fi
  echo "=== $tag (d=$d K=$K D=$(( (K + 1) ** d )), V=$V, dose 36) ==="
  local i=0
  while [ $i -lt $MAX_CHUNKS ]; do
    if [ -f "$OUT/krs_$tag.npz" ]; then
      python3 c4_kappa_krylov.py --tag "$tag" --d "$d" --K "$K" --V "$V" \
          --resume --deadline "$CHUNK_DEADLINE" --t-scale "$TS" \
          --addr-limit "$ADDR" "$@" || true
    else
      python3 c4_kappa_krylov.py --tag "$tag" --d "$d" --K "$K" --V "$V" \
          --deadline "$CHUNK_DEADLINE" --addr-limit "$ADDR" "$@" || true
    fi
    if done_tag "$tag"; then
      echo "$tag: certified."
      return 0
    fi
    i=$(( i + 1 ))
  done
  echo "$tag: MAX_CHUNKS ($MAX_CHUNKS) reached without certification."
  return 1
}

case ${1:-both} in
  k15)
    run_median L36d4K15kr 4 15 0.16
    ;;
  k17)
    run_median L36d4K17kr 4 17 0.1245675
    ;;
  both)
    run_median L36d4K15kr 4 15 0.16
    run_median L36d4K17kr 4 17 0.1245675
    ;;
  demo)
    # resume-cycle proof on the calibrated d=3 K18 platform (D=6859,
    # M=548, ~3 min): short deadlines force several chunk boundaries.
    rm -f "$OUT/krs_L36d3K18demo.npz" "$OUT/res_krylov_L36d3K18demo.json" \
          "$OUT/win_krylov_L36d3K18demo.npz"
    CHUNK_DEADLINE=130 MAX_CHUNKS=12 run_median L36d3K18demo 3 18 0.1111111
    ;;
  *)
    echo "usage: $0 {k15|k17|both|demo}" >&2
    exit 2
    ;;
esac
