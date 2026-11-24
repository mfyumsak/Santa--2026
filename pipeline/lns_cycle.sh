#!/bin/bash
# Gizli Kaggle LNS döngüsü: biten kernel(ler) için dataset'i güncel en iyiyle yeniler ve kerneli yeniden başlatır.
# update.sh'den SONRA çalıştırılır (update.sh bitmiş kernellerin çıktısını zaten birleştirmiş olur).
REPO=$(cd "$(dirname "$0")/.." && pwd)
DS=mfurkanyumsak/santa2026-best-programs
declare -A DIRS=([santa2026-dag-lns-private]=kaggle_lns [santa2026-dag-lns-private-2]=kaggle_lns2)
done_list=()
for k in "${!DIRS[@]}"; do
  ST=$(kaggle kernels status mfurkanyumsak/$k 2>&1); echo "$ST"
  echo "$ST" | grep -qiE "running|queued" || done_list+=("$k")
done
[ ${#done_list[@]} -eq 0 ] && { echo "tüm kerneller çalışıyor"; exit 0; }
D=$(mktemp -d); cp /mnt/project-files/santa2026/submission_best.csv $D/best.csv
echo "{\"title\": \"santa2026 best programs\", \"id\": \"$DS\", \"licenses\": [{\"name\": \"CC0-1.0\"}]}" > $D/dataset-metadata.json
kaggle datasets version -p $D -m "best $(date -u +%F_%H%M)" 2>&1 | tail -1
for i in $(seq 1 30); do kaggle datasets status $DS 2>&1 | grep -q ready && break; sleep 20; done
for k in "${done_list[@]}"; do kaggle kernels push -p $REPO/${DIRS[$k]} 2>&1 | tail -1; done
rm -rf $D
