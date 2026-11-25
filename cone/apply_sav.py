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
FITN = int(os.environ.get('FITN', '40'))
FITT = int(os.environ.get('FITT', '6'))
ANNEAL = int(os.environ.get('ANNEAL', '4'))
ANNIT = int(os.environ.get('ANNIT', '20000'))

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

def list_sched(rec, order, st, R=48, jitter=0.0, rng=None, slack=2):
    """Register baskısını gözeten liste zamanlayıcı: canlı değer sayısı R'yi aşmayacak topolojik sıra (yoksa None)."""
    key = {v: i + (rng.random() * jitter if rng else 0) for i, v in enumerate(order)}
    cons = collections.Counter(); users = collections.defaultdict(list); deps = {}
    stset = set(st)
    for v in order:
        op, a, b = rec[v]; ops = {a, b}
        for x in ops: cons[x] += 1; users[x].append(v)
        deps[v] = len([x for x in ops if x in rec])
    rem = dict(cons)
    live = {v for v in stset if rem.get(v, 0) > 0}
    ready = {v for v in order if deps[v] == 0}
    out = []
    while ready:
        best = None
        for v in ready:
            op, a, b = rec[v]
            dying = sum(1 for x in {a, b} if rem[x] == 1)
            during = len(live) - dying + 1
            if during > R: continue
            delta = (1 if cons.get(v, 0) > 0 else 0) - dying
            sc = (delta, key[v]) if len(live) >= R - slack else (0, key[v])
            if best is None or sc < best[0]: best = (sc, v)
        if best is None: return None
        v = best[1]; ready.discard(v); out.append(v)
        op, a, b = rec[v]
        for x in {a, b}:
            rem[x] -= 1
            if rem[x] == 0: live.discard(x)
        if cons.get(v, 0) > 0: live.add(v)
        for u in users[v]:
            deps[u] -= 1
            if deps[u] == 0: ready.add(u)
    return out if len(out) == len(order) else None

def rev_sched(rec, order, st, R=48, jitter=0.0, rng=None, slack=2):
    """Sondan başa liste zamanlayıcı: canlı küme L (ileri yönde 'sonra kullanılacak' değerler)."""
    key = {v: i + (rng.random() * jitter if rng else 0) for i, v in enumerate(order)}
    users = collections.defaultdict(set)
    for v in order:
        op, a, b = rec[v]
        users[a].add(v); users[b].add(v)
    left = {v: len(users[v]) for v in order}   # henüz zamanlanmamış kullanıcı sayısı
    ready = {v for v in order if left[v] == 0}
    L = set(); out = []
    while ready:
        best = None
        for v in ready:
            op, a, b = rec[v]
            Lm = L - {v}
            live_in = Lm | {a, b}
            if len(live_in) > R or len(Lm) + 1 > R: continue
            delta = len(live_in) - len(L)
            sc = (delta, -key[v]) if len(L) >= R - slack else (0, -key[v])
            if best is None or sc < best[0]: best = (sc, v)
        if best is None: return None
        v = best[1]; ready.discard(v); out.append(v)
        op, a, b = rec[v]
        L.discard(v); L |= {a, b}
        for x in {a, b}:
            if x in left:
                left[x] -= 1
                if left[x] == 0: ready.add(x)
    if len(out) != len(order): return None
    if len(L) > R: return None
    return out[::-1]

def overflow(rec, order, st, R=48):
    last = {}
    for i, v in enumerate(order):
        op, a, b = rec[v]; last[a] = i; last[b] = i
    live = sum(1 for v in set(st) if v in last); ov = 0
    for i, v in enumerate(order):
        op, a, b = rec[v]
        dying = sum(1 for x in {a, b} if last.get(x) == i)
        peak = live - dying + 1
        if peak > R: ov += peak - R
        live = live - dying + (1 if last.get(v, -1) > i else 0)
    return ov

def anneal_fit(rec, order, st, R=48, iters=20000, seed=0):
    """Sırayı rastgele geçerli taşımalarla değiştirerek register taşmasını sıfırla (yerel arama)."""
    import random
    rng = random.Random(seed)
    order = list(order); cur = overflow(rec, order, st, R)
    users = collections.defaultdict(set)
    for v in order:
        op, a, b = rec[v]; users[a].add(v); users[b].add(v)
    for it in range(iters):
        if cur == 0: return order
        pos = {v: i for i, v in enumerate(order)}
        v = rng.choice(order); i = pos[v]
        op, a, b = rec[v]
        lo = max([pos[x] for x in (a, b) if x in pos], default=-1) + 1
        hi = min([pos[u] for u in users[v]], default=len(order)) - 1
        if hi <= lo: continue
        j = rng.randint(lo, hi)
        if j == i: continue
        o2 = order[:i] + order[i+1:]
        o2.insert(j if j < i else j, v) if j < i else o2.insert(j, v)
        new = overflow(rec, o2, st, R)
        if new <= cur or rng.random() < 0.02:
            order, cur = o2, new
    return order if cur == 0 else None

def fit(rec, order, st, tg, L, tries=FITT):
    """Sırayı 48 register'a sığdır: önce olduğu gibi, sonra liste zamanlayıcı (birkaç rastgele deneme)."""
    import random
    for t in range(tries + 1):
        if t == 0: o = order
        else: o = list_sched(rec, order, st, jitter=0 if t == 1 else 4.0 * (t % 10), rng=random.Random(t) if t > 1 else None, slack=1 + t % 7)
        os_ = [o, rev_sched(rec, order, st, jitter=0 if t <= 1 else 4.0 * (t % 10), rng=random.Random(1000 + t) if t > 1 else None, slack=1 + t % 7)]
        for o in os_:
            if o is None: continue
            vops = [(rec[v][0], rec[v][1], rec[v][2], v) for v in o]
            prog = allocate(vops, st)
            if prog is not None and run(prog, st, tg, L)[0]: return o, prog
    return None

def apply_one(st, tg, L, rec, order, sav):
    """Koniyi değiştir; yeni bloğu 48 register'a sığacak bir sıra bul. (rec2, order2) ya da None."""
    import random
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
    kept = [v for v in order if v not in c]
    base = (set(kept) | stset) - d
    last = {}
    for i, v in enumerate(order):
        if v in c: continue
        op, a, b = rec[v]; last[a] = i; last[b] = i
    pos = {v: idx[v] for v in kept}
    for v in stset: pos[v] = -1
    rng = random.Random(len(new) * 7919 + T % 1000)
    variants = []
    for mode in range(6):
        blk = {}; rem = [x for x in new if x not in base] + [T]
        while rem:
            prog = False
            for v in list(rem):
                D = derive_all(v, (base | set(blk)) - {T}, L)
                if not D: continue
                if mode == 0: r = min(D, key=lambda t: (max(pos.get(t[1], -1), pos.get(t[2], -1))))
                elif mode == 1: r = max(D, key=lambda t: (min(last.get(t[1], 10**9) if t[1] not in blk else 10**9, last.get(t[2], 10**9) if t[2] not in blk else 10**9)))
                else: r = rng.choice(D)
                blk[v] = r; rem.remove(v); prog = True
            if not prog: break
        if rem: continue
        if blk not in variants: variants.append(blk)
    if not variants: return None
    tries = []
    for blk in variants:
        rec2 = {v: rec[v] for v in kept}; rec2.update(blk)
        for q in sorted({idx[T] - 0.5, 0.5} | {i + 0.5 for i in range(0, len(order), max(1, len(order) // 12))}, reverse=True):
            key = {v: idx[v] for v in kept}
            for j, v in enumerate(blk): key[v] = q + j * 1e-3
            o = topo(rec2, key)
            if o: tries.append((rec2, o))
    for rec2, o in tries:
        vops = [(rec2[v][0], rec2[v][1], rec2[v][2], v) for v in o]
        prog = allocate(vops, st)
        if prog is not None and run(prog, st, tg, L)[0]: return rec2, o
    for rec2, o in tries[:FITN]:
        r = fit(rec2, o, st, tg, L)
        if r: return rec2, r[0]
    if ANNEAL:
        tries.sort(key=lambda t: overflow(t[0], t[1], st))
        for k, (rec2, o) in enumerate(tries[:ANNEAL]):
            o2 = anneal_fit(rec2, o, st, iters=ANNIT, seed=k)
            if o2:
                vops = [(rec2[v][0], rec2[v][1], rec2[v][2], v) for v in o2]
                prog = allocate(vops, st)
                if prog is not None and run(prog, st, tg, L)[0]: return rec2, o2
    return None

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
        p = P[pid.split("@")[0]]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
        bestp = None; bestapp = 0
        for strat in (0,):
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
    for pid in sorted(best): w.writerow([pid, json.dumps(best[pid], separators=(",", ":"))])
    print("puzzles", nwin, "gain", gain, "score", sum(map(len, best.values())))
