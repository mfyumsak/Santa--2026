#!/bin/bash
# Kullanım: run20.sh in.txt out_prefix [tony args...]  (HK/HMODE/HW env)
IN=$1; OUT=$2; shift 2
D=$(dirname $OUT); mkdir -p $D
split -n l/4 -d $IN $OUT.part
for p in $OUT.part0[0-3]; do
  /home/user/santa--2026/hcub/${SOLVER:-hcub_solver} "$@" plan < $p > $p.plan 2>/dev/null &
done
wait
cat $OUT.part0[0-3].plan > $OUT.plan; rm -f $OUT.part0[0-3] $OUT.part0[0-3].plan
COSTPOW=2 python3 /home/user/santa--2026/hcub/cmp.py $OUT.plan
