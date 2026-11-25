"""Bulmaca başına en iyiye eşit ya da +SLACK uzunlukta, değer kümesi farklı doğrulanmış alternatif programlar.
Kullanım: python alt_collect.py puzzles.csv best.csv out_alt.csv slack a.csv b.csv ..."""
import sys, csv, json
sys.path.insert(0, '/mnt/project-files/santa2026'); sys.path.insert(0, '/home/user/santa--2026/opt')
from validate import run
from vio import to_values
csv.field_size_limit(10**9)
P = {r["id"]: r for r in csv.DictReader(open(sys.argv[1]))}
B = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(sys.argv[2]))}
slack = int(sys.argv[4]); MAXK = 6
sig = {}
for pid in P:
    st = json.loads(P[pid]["starting_values"])
    sig[pid] = {frozenset(r for *_, r in to_values(B[pid], st))}
alts = {pid: [] for pid in P}
for f in sys.argv[5:]:
    try: rows = list(csv.DictReader(open(f, errors="replace")))
    except Exception: continue
    if not rows or "id" not in rows[0] or "program" not in rows[0]: continue
    for r in rows:
        pid = r["id"]
        if pid not in P or not r["program"] or len(alts[pid]) >= MAXK: continue
        try: prog = json.loads(r["program"])
        except Exception: continue
        if not isinstance(prog, list) or len(prog) > len(B[pid]) + slack: continue
        p = P[pid]; st = json.loads(p["starting_values"])
        try:
            ok, _ = run(prog, st, json.loads(p["targets"]), int(p["value_limit"]))
            if not ok: continue
            s = frozenset(r_ for *_, r_ in to_values(prog, st))
        except Exception: continue
        if s in sig[pid]: continue
        sig[pid].add(s); alts[pid].append(prog)
w = csv.writer(open(sys.argv[3], "w", newline="")); w.writerow(["id", "program"]); n = 0
for pid, lst in alts.items():
    for k, prog in enumerate(lst):
        w.writerow([f"{pid}@{k}", json.dumps(prog, separators=(",", ":"))]); n += 1
print("alternatives", n, "puzzles", sum(1 for l in alts.values() if l))
