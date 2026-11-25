"""submission.csv -> koni-arama sorguları (biçim: pid T nR L nb base...).
Her düğüm T için: koni = T'ye özel ara değerler (yalnızca koni içinde kullanılan, hedef/başlangıç olmayan),
base = tüm değerler - koni - T'nin torunları. nR = |koni|. Kullanım:
python gen_queries.py puzzles.csv sub.csv out.txt [min_nr=5]"""
import sys, csv, json
sys.path.insert(0, '/home/user/santa--2026/opt')
from vio import to_values
csv.field_size_limit(10**9)

def dag(prog, st):
    stset = set(st); rec = {}; order = []
    for op, a, b, r in to_values(prog, st):
        if r in stset or r in rec: continue
        rec[r] = (op, a, b); order.append(r)
    users = {}
    for r in order:
        op, a, b = rec[r]
        users.setdefault(a, set()).add(r); users.setdefault(b, set()).add(r)
    return rec, order, users

def cone_of(T, rec, order, users, stset, tgset, idx):
    cone = {T}; anc = set(); stack = [T]
    while stack:
        v = stack.pop(); op, a, b = rec[v]
        for x in (a, b):
            if x in rec and x not in anc: anc.add(x); stack.append(x)
    for x in sorted(anc, key=lambda v: -idx[v]):
        if x in tgset or x in stset: continue
        if users.get(x, set()) <= cone: cone.add(x)
    return cone

def desc_of(T, users):
    d = set(); stack = [T]
    while stack:
        v = stack.pop()
        for u in users.get(v, ()):
            if u not in d: d.add(u); stack.append(u)
    return d

if __name__ == "__main__":
    P = {r["id"]: r for r in csv.DictReader(open(sys.argv[1]))}
    min_nr = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    out = open(sys.argv[3], "w"); n = 0
    for r in csv.DictReader(open(sys.argv[2])):
        p = P[r["id"].split("@")[0]]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
        rec, order, users = dag(json.loads(r["program"]), st)
        idx = {v: i for i, v in enumerate(order)}
        stset, tgset = set(st), set(tg)
        allv = set(order) | stset
        for T in order:
            c = cone_of(T, rec, order, users, stset, tgset, idx)
            if len(c) < min_nr: continue
            base = sorted(allv - c - desc_of(T, users))
            out.write(f"{r['id']} {T} {len(c)} {L} {len(base)} " + " ".join(map(str, base)) + "\n"); n += 1
    print("queries", n)
