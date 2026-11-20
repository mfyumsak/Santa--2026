#!/bin/bash
# Hcub portföy eğrisi: aynı girdide farklı ayarlarla çalıştır, her çalıştırmanın planını sakla.
IN=$1; OD=$2; mkdir -p $OD
PA="1,2,3,4,5,6,7,8,10,12,16,20,24,32,40,48"; OA="3,5,7,9,11,13,15,17,19,23,31"
PB="1,2,3,4,5,6,7,8,9,10,11,12,14,16,18,20,24,28,32,36,40,48"; OB="3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,37,41,43,47"
PC="1,2,3,4,5,6,8,10,12,16,20,24,32,48"; OC="3,5,7,9,11,13,17,19,23,29,31,37"
i=0
while read K LZ W D L R PS; do
  case $PS in A) P=$PA; O=$OA;; B) P=$PB; O=$OB;; C) P=$PC; O=$OC;; esac
  i=$((i+1)); name=r$(printf %02d $i)_K${K}L${LZ}W${W}_${D}_${L}_${R}_$PS
  HK=$K HLAZY=$LZ /home/user/santa--2026/hcub/run20.sh $IN $OD/$name $W $D $L $P $O $R | sed "s/^/$name /"
done <<'CFG'
1 0 3 72 88 0.18 A
1 1 3 72 88 0.18 A
1 0 3 56 64 0.18 A
1 0 3 90 110 0.18 A
1 0 3 72 88 0.14 A
1 0 3 72 88 0.22 A
1 0 3 72 88 0.18 B
1 0 3 72 88 0.18 C
1 0 5 72 88 0.18 A
1 1 3 90 110 0.18 B
1 0 3 64 80 0.16 B
1 1 3 64 80 0.20 C
1 0 4 80 96 0.18 A
1 1 4 56 72 0.16 A
1 0 3 100 130 0.20 C
1 1 5 72 88 0.22 B
CFG
