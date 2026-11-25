"""EQUAL satırlarından (eşit uzunlukta koni değişimi) alternatif programlar üret; LNS zinciri için.
Kullanım: python eq_alts.py puzzles.csv best.csv out_alt.csv per_puzzle sav*.txt"""
import sys, csv, json, collections, random, os
os.environ.setdefault('EQ_OK', '1'); os.environ.setdefault('ANNEAL', '0'); os.environ.setdefault('FITN', '10')
sys.path.insert(0, '/home/user/santa--2026/cone')
import apply_sav as A
from gen_queries import dag
csv.field_size_limit(10**9)
A.EQ = 1
P = {r["id"]: r for r in csv.DictReader(open(sys.argv[1]))}
best = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(sys.argv[2]))}
K = int(sys.argv[4])
E = collections.defaultdict(list)
for f in sys.argv[5:]:
    for l in open(f):
        w = l.split()
        if "EQUAL" not in w: continue
        E[w[0]].append((int(w[1]), list(map(int, w[w.index("new") + 1:]))))
rng = random.Random(1)
out = csv.writer(open(sys.argv[3], "w", newline="")); out.writerow(["id", "program"]); n = 0
for pid, lst in E.items():
    p = P[pid.split("@")[0]]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
    rng.shuffle(lst); seenT = set(); k = 0
    for T, new in lst:
        if k >= K: break
        if T in seenT: continue
        rec, order, _ = dag(best[pid], st)
        r = A.apply_one(st, tg, L, rec, order, (T, new))
        if not r: continue
        prog = A.materialize(st, tg, L, r[0], r[1])
        if prog and len(prog) <= len(best[pid]):
            out.writerow([f"{pid}@e{k}", json.dumps(prog, separators=(",", ":"))]); k += 1; n += 1; seenT.add(T)
print("eq alternatives", n, "puzzles", len(E))
