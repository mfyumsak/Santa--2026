"""Sığmayan SAVING'ler için: önce bir EQUAL hamlesi uygula (yapıyı değiştir), sonra SAVING'i dene.
Kullanım: python combo.py puzzles.csv best.csv out.csv sav*.txt"""
import sys, csv, json, collections, os
os.environ.setdefault('ANNEAL', '2'); os.environ.setdefault('FITN', '40')
sys.path.insert(0, '/home/user/santa--2026/cone')
import apply_sav as A
from gen_queries import dag
csv.field_size_limit(10**9)
P = {r["id"]: r for r in csv.DictReader(open(sys.argv[1]))}
best = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(sys.argv[2]))}
SV = collections.defaultdict(list); EQL = collections.defaultdict(list)
for f in sys.argv[4:]:
    for l in open(f):
        w = l.split()
        if "SAVING" in w: SV[w[0]].append((int(w[1]), list(map(int, w[w.index("new") + 1:]))))
        elif "EQUAL" in w: EQL[w[0]].append((int(w[1]), list(map(int, w[w.index("new") + 1:]))))
gain = 0
for pid, svs in SV.items():
    p = P[pid]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
    done = False
    for Te, ne in EQL.get(pid, []):
        rec, order, _ = dag(best[pid], st)
        A.EQ = 1
        r = A.apply_one(st, tg, L, rec, order, (Te, ne))
        A.EQ = 0
        if not r: continue
        for T, new in svs:
            r2 = A.apply_one(st, tg, L, r[0], r[1], (T, new))
            if not r2: continue
            prog = A.materialize(st, tg, L, r2[0], r2[1])
            if prog and len(prog) < len(best[pid]):
                print(pid, len(best[pid]), "->", len(prog), "via EQ at", Te, flush=True)
                gain += len(best[pid]) - len(prog); best[pid] = prog; done = True; break
        if done: break
    if not done: print(pid, "sığmadı;", len(EQL.get(pid, [])), "EQUAL denendi", flush=True)
w = csv.writer(open(sys.argv[3], "w", newline="")); w.writerow(["id", "program"])
for pid in sorted(P): w.writerow([pid, json.dumps(best[pid], separators=(",", ":"))])
print("gain", gain, "score", sum(map(len, best.values())))
