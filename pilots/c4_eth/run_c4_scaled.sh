#!/bin/bash
# Driver for the scaled C4 ETH scan: small -> large, one PROCESS per stage
# (window / evolve), so every call fits a foreground wall-clock chunk.
# Skips stages whose res_{tag}.json already contains their output.
cd /home/z/my-project/scripts
OUT=/home/z/my-project/download/pilot_c4_eth_scaled
mkdir -p "$OUT"
LOG="$OUT/scan.log"
FAIL="$OUT/failures.log"
touch "$FAIL"

runstage() {   # runstage <tag> <d> <K> <stage> [extra args...]
  tag=$1; d=$2; K=$3; stage=$4; shift 4
  echo "=== $tag ($stage, D=$(( (K + 1) ** d )) ) ===" >> "$LOG"
  python3 c4_scaled_eth.py --tag "$tag" --d "$d" --K "$K" --stage "$stage" "$@" \
      >> "$LOG" 2>&1 || echo "FAILED: $tag $stage $*" >> "$FAIL"
}

# ---- window tier (LU expected to fit), three truncation directions ----
runstage d4K9   4 9  window;  runstage d4K9   4 9  evolve
runstage d6K4   6 4  window;  runstage d6K4   6 4  evolve
runstage d5K6   5 6  window;  runstage d5K6   5 6  evolve
runstage d4K11  4 11 window;  runstage d4K11  4 11 evolve
runstage d3K28  3 28 window;  runstage d3K28  3 28 evolve

# ---- evolve tier (LU fill known to exceed laptop RAM) ----
runstage d4K12  4 12 evolve --no-window
runstage d3K35  3 35 evolve --no-window
runstage d6K5   6 5  evolve --no-window
runstage d4K14  4 14 evolve --no-window
runstage d5K8   5 8  evolve --no-window
runstage d3K45  3 45 evolve --no-window
runstage d4K16  4 16 evolve --no-window
runstage d4K17  4 17 evolve --no-window

# ---- quartic completion (dose-response + growth) ----
runstage d4K9U    4 9  window --U 2.0; runstage d4K9U    4 9  evolve --U 2.0
runstage d4K11U   4 11 window --U 2.0; runstage d4K11U   4 11 evolve --U 2.0
runstage d4K11U05 4 11 window --U 0.5; runstage d4K11U05 4 11 evolve --U 0.5
runstage d4K12U   4 12 evolve --no-window --U 2.0
runstage d4K14U   4 14 evolve --no-window --U 2.0

# ---- weak-coupling control at scale ----
runstage d3K28weak 3 28 window --g0 0.05 --h0 0.03
runstage d3K28weak 3 28 evolve --g0 0.05 --h0 0.03

echo "ALL_DONE" >> "$LOG"
