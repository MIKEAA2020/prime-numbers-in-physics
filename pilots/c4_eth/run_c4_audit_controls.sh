#!/bin/bash
# Audit-response runs: label-scrambled controls + generic-coupling quantile sweep
cd /home/z/my-project/scripts
PY=python

# --- label-scrambled controls (window stage) ---
# baseline res_d4K11V0:   r=0.5812 sig=0.363  PR/D=0.2384
$PY c4_scaled_eth.py --tag d4K11V0scr   --d 4 --K 11 --g0 1.5 --h0 1.0 --V 0   --seed 7 --stage window --pivot diag --scramble
# baseline res_d4K11V03:  r=0.518  sig=1.087  PR/D=0.1364
$PY c4_scaled_eth.py --tag d4K11V03scr --d 4 --K 11 --g0 1.5 --h0 1.0 --V 0.3 --seed 7 --stage window --pivot diag --scramble
# matched unscrambled baseline for d3K28 at pivot=diag (old res_d3K28 was auto)
$PY c4_scaled_eth.py --tag d3K28diag   --d 3 --K 28 --g0 1.5 --h0 1.0 --V 0   --seed 7 --stage window --pivot diag
$PY c4_scaled_eth.py --tag d3K28V0scr  --d 3 --K 28 --g0 1.5 --h0 1.0 --V 0   --seed 7 --stage window --pivot diag --scramble
# baseline res_L36d4K11 (matched dose V=36/121): r=0.5088
$PY c4_scaled_eth.py --tag L36d4K11scr --d 4 --K 11 --g0 1.5 --h0 1.0 --V 0.2975207 --seed 7 --stage window --pivot diag --scramble

# --- generic-coupling full quantile sweep (d3K28, mirrors the weak sweep) ---
for q in 0.02 0.10 0.15 0.25 0.75 0.90 0.98; do
  $PY c4_scaled_eth.py --tag d3K28gq$(echo $q | tr -d '.') --d 3 --K 28 --g0 1.5 --h0 1.0 --V 0 --seed 7 --stage window --pivot diag --sigma-quantile $q
done

echo "ALL RUNS DONE"
