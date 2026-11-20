"""Plan dosyasını 48 register'a zamanla, doğrula, submission_best ile bulmaca bazında kıyasla."""
import sys, csv, json
sys.path.insert(0, '/home/user/santa--2026/sched'); sys.path.insert(0, '/mnt/project-files/santa2026')
from sched import read_plans, schedule
from validate import run
csv.field_size_limit(10**9)
BEST = {r["id"]: len(json.loads(r["program"])) for r in csv.DictReader(open('/mnt/project-files/santa2026/submission_best.csv'))}
tp = ts = tb = wins = 0; rows = []
for pid, lim, st, T, plan in read_plans(sys.argv[1]):
    prog = schedule(st, T, plan); ok, info = run(prog, st, T, lim); assert ok, (pid, info)
    tp += len(plan); ts += len(prog); tb += BEST[pid]; wins += len(prog) < BEST[pid]
    rows.append((pid, len(plan), len(prog), BEST[pid]))
print(f"n={len(rows)} plan {tp} sched {ts} best {tb} gap {100*(ts-tb)/tb:+.1f}% wins {wins}")
if len(sys.argv) > 2:
    for r in rows: print(*r)
