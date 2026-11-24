#!/bin/bash
# Güncel public notebook çıktılarını indir, en iyi programlarla birleştir, optimize et, daha iyiyse submit et.
# Gereken: ~/.kaggle/kaggle.json, /mnt/project-files/santa2026/data/puzzles.csv, opt/resynth (derlenmiş).
set -e
ROOT=/mnt/project-files/santa2026
REPO=$(cd "$(dirname "$0")/.." && pwd)
W=${WORK:-/tmp/santa_pub}; mkdir -p $W
cd $W
# notebook çıktıları: en son çalışan 60 + oy/popülerlik sırasındakiler
for s in dateRun voteCount hotness; do kaggle kernels list --competition santa-2026 --sort-by $s --page-size 60 2>/dev/null | awk 'NR>2{print $1}'; done | sort -u > refs.txt
for k in $(cat refs.txt); do d=$(echo $k | tr / _); mkdir -p $d; timeout 120 kaggle kernels output $k -p $d >/dev/null 2>&1 || true; done
# public dataset'ler (program paylaşılan dataset'ler, son güncellenenler)
for q in "santa 2026" "santa-2026" "elf calculator"; do for pg in 1 2; do kaggle datasets list -s "$q" --sort-by updated --page $pg 2>/dev/null | awk 'NR>2{print $1}'; done; done | grep -iE "santa|elf" | grep -viE "squares|202[2-5]|leaderboard" | sort -u > dsrefs.txt
for k in $(cat dsrefs.txt); do d=ds_$(echo $k | tr / _); mkdir -p $d; timeout 180 kaggle datasets download -d $k -p $d --unzip >/dev/null 2>&1 || true; done
# kendi gizli Kaggle LNS çalıştırmamızın son tamamlanan çıktısı
for kk in santa2026-dag-lns-private santa2026-dag-lns-private-2; do mkdir -p own_$kk; timeout 300 kaggle kernels output mfurkanyumsak/$kk -p own_$kk >/dev/null 2>&1 || true; done
cd $ROOT
python3 merge.py data/puzzles.csv $W/merged.csv submission_best.csv $(find $W -name "*.csv" -size +100k ! -name merged.csv ! -name opt.csv) | sed 's/Counter.*//'
python3 $REPO/opt/vio.py to data/puzzles.csv $W/merged.csv $W/m.txt
$REPO/opt/resynth $W/m.txt $W/mo.txt 5 3 3
python3 $REPO/opt/vio.py from data/puzzles.csv $W/mo.txt $W/merged.csv $W/opt.csv
NEW=$(python3 validate.py data/puzzles.csv $W/opt.csv | tail -1 | sed 's/.*score=//')
OLD=$(python3 validate.py data/puzzles.csv submission_best.csv | tail -1 | sed 's/.*score=//')
echo "old=$OLD new=$NEW"
if [ "$NEW" -lt "$OLD" ]; then
  cp $W/opt.csv submission_best.csv
  kaggle competitions submit -c santa-2026 -f submission_best.csv -m "auto: public merge + resynth ($NEW)" | tail -1
fi
