#!/bin/bash
# Gizli Kaggle LNS döngüsü: kernel bitmişse dataset'i güncel en iyiyle yeniler ve kerneli yeniden başlatır.
# update.sh'den SONRA çalıştırılır (update.sh bitmiş kernelin çıktısını zaten birleştirmiş olur).
REPO=$(cd "$(dirname "$0")/.." && pwd)
K=mfurkanyumsak/santa2026-dag-lns-private; DS=mfurkanyumsak/santa2026-best-programs
ST=$(kaggle kernels status $K 2>&1); echo "$ST"
if echo "$ST" | grep -qiE "running|queued"; then echo "kernel hâlâ çalışıyor"; exit 0; fi
D=$(mktemp -d); cp /mnt/project-files/santa2026/submission_best.csv $D/best.csv
echo "{\"title\": \"santa2026 best programs\", \"id\": \"$DS\", \"licenses\": [{\"name\": \"CC0-1.0\"}]}" > $D/dataset-metadata.json
kaggle datasets version -p $D -m "best $(date -u +%F_%H%M)" 2>&1 | tail -1
for i in $(seq 1 30); do kaggle datasets status $DS 2>&1 | grep -q ready && break; sleep 20; done
kaggle kernels push -p $REPO/kaggle_lns 2>&1 | tail -1
rm -rf $D
