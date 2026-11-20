"""Portföy eğrisi: dizindeki *.plan dosyaları (sıralı) için bulmaca bazında min'in çalıştırma sayısına göre seyri."""
import sys, glob, csv, json, os
sys.path.insert(0, '/home/user/santa--2026/sched')
os.environ.setdefault('COSTPOW', '2')
from sched import read_plans, schedule
csv.field_size_limit(10**9)
BEST = {r["id"]: len(json.loads(r["program"])) for r in csv.DictReader(open('/mnt/project-files/santa2026/submission_best.csv'))}
files = sorted(f for f in glob.glob(os.path.join(sys.argv[1], '*.plan')) if '.part' not in f)
cur = {}; runs = []
for k, f in enumerate(files, 1):
    res = {pid: len(schedule(st, T, plan)) for pid, lim, st, T, plan in read_plans(f)}
    runs.append(res)
    for pid, n in res.items(): cur[pid] = min(cur.get(pid, 10**9), n)
    tb = sum(BEST[p] for p in cur); tc = sum(cur.values())
    print(f"{k:2d} {os.path.basename(f)[:-5]:32s} run {sum(res.values())} min {tc} best {tb} gap {100*(tc-tb)/tb:+.1f}% wins {sum(cur[p] < BEST[p] for p in cur)}")
