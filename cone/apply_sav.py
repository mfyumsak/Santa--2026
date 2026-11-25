"""Koni-arama SAVING satırlarını programlara uygula, register ata, doğrula.
Kullanım: python apply_sav.py puzzles.csv best.csv out.csv sav1.txt [sav2.txt ...]"""
import sys, csv, json, heapq, collections
sys.path.insert(0, '/home/user/santa--2026/opt'); sys.path.insert(0, '/home/user/santa--2026/sched')
sys.path.insert(0, '/mnt/project-files/santa2026')
from vio import allocate
from sched import schedule
from validate import run
from gen_queries import dag, cone_of, desc_of
csv.field_size_limit(10**9)
import os
EQ = int(os.environ.get('EQ_OK', '0'))
STRAT = 0

def derive_all(v, S, L):
    res = []
    for a in S:
        b = v - a
        if b in S and a <= b: res.append(('+', a, b))
        b = a - v
        if b > 0 and b in S: res.append(('-', a, b))
        if a > 1 and v % a == 0 and v // a in S and a <= v // a: res.append(('*', a, v // a))
        b = a * v
        if b <= L and b in S: res.append(('/', b, a))
    return res

def topo(rec, key):
    deps = {v: {x for x in rec[v][1:] if x in rec} for v in rec}
    users = collections.defaultdict(list)
    for v, d in deps.items():
        for x in d: users[x].append(v)
    cnt = {v: len(d) for v, d in deps.items()}
    h = [(key[v], v) for v in rec if cnt[v] == 0]; heapq.heapify(h); out = []
    while h:
        _, v = heapq.heappop(h); out.append(v)
        for u in users[v]:
            cnt[u] -= 1
            if cnt[u] == 0: heapq.heappush(h, (key[u], u))
    return out if len(out) == len(rec) else None

def apply_one(st, tg, L, rec, order, sav):
    stset, tgset = set(st), set(tg)
    users = {}
    for r in order:
        op, a, b = rec[r]
        users.setdefault(a, set()).add(r); users.setdefault(b, set()).add(r)
    idx = {v: i for i, v in enumerate(order)}
    T, new = sav
    if T not in rec: return None
    c = cone_of(T, rec, order, users, stset, tgset, idx)
    if len(new) + 1 >= len(c) + EQ: return None
    d = desc_of(T, users)
    if any(v in d for v in new): return None
    base = (set(order) | stset) - c - d
    pos = {v: idx[v] for v in base if v in idx}
    for v in stset: pos[v] = -1
    known = set(base); rem = list(new) + [T]; nrec = {}
    while rem:
        prog = False
        for v in list(rem):
            if v in known and v != T: rem.remove(v); prog = True; continue
            S = known - {T}
            if v in rec and v != T and rec[v][1] in S and rec[v][2] in S: r = rec[v]
            else:
                D = derive_all(v, S, L)
                r = min(D, key=lambda t: (max(pos[t[1]], pos[t[2]]), pos[t[1]] + pos[t[2]])) if D else None
            if r:
                nrec[v] = r; known.add(v); rem.remove(v); prog = True
                pos[v] = max(pos[r[1]], pos[r[2]]) + 0.001
        if not prog: return None
    rec2 = {v: rec[v] for v in rec if v not in c}
    key = {v: idx[v] for v in rec2}
    for j, v in enumerate(nrec):
        rec2[v] = nrec[v]
        key[v] = (pos[v] if STRAT == 1 else idx[T] - 1 + (j + 1) / (len(nrec) + 1))
    key[T] = max(idx[T], pos[T]) if STRAT != 1 else pos[T]
    o = topo(rec2, key)
    return (rec2, o) if o else None

def materialize(st, tg, L, rec, order):
    vops = [(rec[v][0], rec[v][1], rec[v][2], v) for v in order]
    prog = allocate(vops, st)
    if prog is None or not run(prog, st, tg, L)[0]:
        prog = schedule(st, tg, vops)
    ok, _ = run(prog, st, tg, L)
    return prog if ok else None

if __name__ == "__main__":
    P = {r["id"]: r for r in csv.DictReader(open(sys.argv[1]))}
    best = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(sys.argv[2]))}
    S = collections.defaultdict(list)
    for f in sys.argv[4:]:
        for l in open(f):
            w = l.split()
            if "SAVING" not in w: continue
            T = int(w[1]); new = list(map(int, w[w.index("new") + 1:]))
            S[w[0]].append((int(w[3]) - int(w[w.index("emitted") + 1]), T, new))
    gain = 0; nwin = 0
    for pid, lst in S.items():
        p = P[pid]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
        bestp = None; bestapp = 0
        for strat in (0, 1):
            STRAT = strat
            rec, order, _ = dag(best[pid], st)
            applied = 0
            for g, T, new in sorted(lst, key=lambda x: -x[0]):
                r = apply_one(st, tg, L, rec, order, (T, new))
                if r: rec, order = r; applied += 1
            if not applied: continue
            prog = materialize(st, tg, L, rec, order)
            if prog and (bestp is None or len(prog) < len(bestp)): bestp, bestapp = prog, applied
        prog = bestp
        if prog and len(prog) < len(best[pid]) + EQ:
            gain += len(best[pid]) - len(prog); nwin += 1
            print(pid, len(best[pid]), "->", len(prog), "applied", bestapp, flush=True)
            best[pid] = prog
    w = csv.writer(open(sys.argv[3], "w", newline="")); w.writerow(["id", "program"])
    for pid in sorted(P): w.writerow([pid, json.dumps(best[pid], separators=(",", ":"))])
    print("puzzles", nwin, "gain", gain, "score", sum(map(len, best.values())))
