"""Plan (değer seviyesi, sınırsız register) -> 48 register'lık program.
Belady tahliyesi + gerektiğinde yeniden hesaplama. Kullanım: python sched.py plan.txt out.csv"""
import sys, json, csv, bisect, os
COSTPOW = float(os.environ.get('COSTPOW', '1'))
sys.setrecursionlimit(10000)

def apply(op, x, y):
    return {'+': x + y, '-': x - y, '*': x * y, '/': x // y}[op]

def schedule(starts, targets, plan, R=48, evict_cost_weight=0.0):
    recipe = {r: (op, a, b) for op, a, b, r in plan}
    order = [r for op, a, b, r in plan]
    uses = {}
    for i, (op, a, b, r) in enumerate(plan):
        uses.setdefault(a, []).append(i); uses.setdefault(b, []).append(i)
    startset = set(starts)
    regs = [None] * R
    where = {}
    for i, v in enumerate(starts):
        if v not in where: regs[i] = v; where[v] = i
    prog = []
    pos = [0]
    def next_use(v):
        u = uses.get(v)
        if not u: return 10**9
        k = bisect.bisect_left(u, pos[0])
        return u[k] if k < len(u) else 10**9
    def victim(lock):
        best, bkey = None, None
        for k in range(R):
            if k in lock: continue
            v = regs[k]
            if v is None: return k
            if v in startset or v not in recipe: continue  # tohumlar korunur
            nu = next_use(v)
            if nu >= 10**9: return k
            op_, a_, b_ = recipe[v]
            c = 1 + (0 if a_ in where else 2) + (0 if b_ in where else 2)
            key = (nu - pos[0]) / (c ** COSTPOW)
            if bkey is None or key > bkey: best, bkey = k, key
        if best is None: raise RuntimeError("no register")
        return best
    def ensure(v, lock):
        if v in where: return where[v]
        op, a, b = recipe[v]
        ra = ensure(a, lock); lock2 = lock | {ra}
        rb = ensure(b, lock2); lock3 = lock2 | {rb}
        d = victim(lock3)
        old = regs[d]
        if old is not None: where.pop(old, None)
        prog.append([op, ra, rb, d]); regs[d] = v; where[v] = d
        return d
    for i, (op, a, b, r) in enumerate(plan):
        pos[0] = i
        if r in where: continue
        ra = ensure(a, set()); rb = ensure(b, {ra})
        pos[0] = i + 1
        d = victim({ra, rb}) if True else None
        # okunan kaynaklar yazmadan önce okunur: hedef kaynaklardan biri olabilir
        old = regs[d]
        if old is not None: where.pop(old, None)
        prog.append([op, ra, rb, d]); regs[d] = r; where[r] = d
    return prog

def read_plans(path):
    L = open(path).read().split('\n'); i = 0
    while i < len(L) and L[i].strip():
        pid, lim, k, nt, n = L[i].split(); n = int(n)
        st = list(map(int, L[i+1].split())); T = list(map(int, L[i+2].split()))
        plan = []
        for l in L[i+3:i+3+n]:
            op, a, b, r = l.split(); plan.append((op, int(a), int(b), int(r)))
        yield pid, int(lim), st, T, plan
        i += 3 + n

if __name__ == "__main__":
    sys.path.insert(0, '/mnt/project-files/santa2026')
    from validate import run
    tot_plan = tot = 0; rows = []
    for pid, lim, st, T, plan in read_plans(sys.argv[1]):
        prog = schedule(st, T, plan)
        ok, info = run(prog, st, T, lim)
        assert ok, (pid, info)
        tot_plan += len(plan); tot += len(prog); rows.append((pid, prog))
    print("plan", tot_plan, "scheduled", tot)
    if len(sys.argv) > 2:
        w = csv.writer(open(sys.argv[2], "w", newline="")); w.writerow(["id", "program"])
        for pid, prog in rows: w.writerow([pid, json.dumps(prog, separators=(",", ":"))])
