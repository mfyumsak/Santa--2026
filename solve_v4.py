"""v4: v3 + önceki hedefleri yeniden kullanma. Hedefler artan sırada; son K hedef register'da tutulur.
t = u*m + d (u önceki hedef, m küçük, d sabit ya da ayrı kurulan değer) seçeneği beam ile kıyaslanır."""
import csv, json, sys
from multiprocessing import Pool
from beam import decompose
from validate import run
from solve_v3 import DESIGNS

def build(start, targets, limit, BASE, K=6, beam=16, M=256):
    k = len(start)
    reg = {}
    for i, v in enumerate(start): reg.setdefault(v, i)
    nxt = k; prog = []
    if 1 not in reg:
        prog.append(["/", 0, 0, nxt]); reg[1] = nxt; nxt += 1
    room = 47 - nxt - 1 - K  # ACC, ACC2, K hedef yuvası
    C = [c for c in BASE if c not in reg][:max(room, 0)]
    for c in C:
        done = False
        for a in sorted(reg):
            if a >= c: break
            if c - a in reg: prog.append(["+", reg[a], reg[c - a], nxt]); done = True; break
        if not done:
            for a in sorted(reg):
                if a > 1 and c % a == 0 and c // a in reg: prog.append(["*", reg[a], reg[c // a], nxt]); done = True; break
        if not done:
            m = max(v for v in reg if v < c)
            prog.append(["+", reg[m], reg[1], nxt])
            for _ in range(c - m - 1): prog.append(["+", nxt, reg[1], nxt])
        reg[c] = nxt; nxt += 1
    ACC, ACC2 = nxt, nxt + 1
    slots = list(range(nxt + 2, nxt + 2 + K)); slot_i = 0
    Cl = sorted(reg); Cs = set(Cl)
    kept = {}  # değer -> register (önceki hedefler)

    def emit(t, dst):
        cost, steps, q = decompose(t, Cl, Cs, beam)
        src = reg[q]
        if not steps:
            prog.append(["+", src, src, dst]); prog.append(["/", dst, reg[2], dst]); return
        for m, d in reversed(steps):
            prog.append(["*", src, reg[m], dst]); src = dst
            if d > 0: prog.append(["+", dst, reg[d], dst])
            elif d < 0: prog.append(["-", dst, reg[-d], dst])

    for t in sorted(set(targets)):
        if t in Cs or t in kept: continue
        base_cost = decompose(t, Cl, Cs, beam)[0]
        best = (base_cost, None)
        for u, ur in kept.items():
            for m in range(1, M):
                d = t - m * u
                if m > 1 and m not in Cs: continue
                ad = abs(d)
                if d == 0: c = (m > 1)
                elif ad in Cs: c = (m > 1) + 1
                else:
                    if ad < 2: continue
                    c = (m > 1) + 1 + decompose(ad, Cl, Cs, 4)[0] + 0
                if c < best[0] and (m * u <= limit): best = (c, (u, ur, m, d))
                if m * u > t + (1 << 40): break
        dst = slots[slot_i % K] if K else ACC
        if best[1] is None:
            emit(t, dst)
        else:
            u, ur, m, d = best[1]; ad = abs(d)
            if ad and ad not in Cs: emit(ad, ACC2)
            dreg = reg.get(ad, ACC2)
            if m > 1:
                prog.append(["*", ur, reg[m], ACC])
                if d > 0: prog.append(["+", ACC, dreg, dst])
                elif d < 0: prog.append(["-", ACC, dreg, dst])
                else: prog.append(["+", ACC, ACC, dst]); prog.append(["/", dst, reg[2], dst])  # nadir
            else:
                prog.append(["+" if d > 0 else "-", ur, dreg, dst])
        if K:
            old = [v for v, r in kept.items() if r == dst]
            for v in old: del kept[v]
            kept[t] = dst; slot_i += 1
    return prog

def work(p):
    s, T, L = json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"])
    best = None
    for B in DESIGNS:
        for K in (4, 8):
            try:
                prog = build(s, T, L, B, K)
                if run(prog, s, T, L)[0] and (best is None or len(prog) < len(best)): best = prog
            except Exception: pass
    return p["id"], best

def main(pz, out, prev):
    Bp = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(prev))}
    P = list(csv.DictReader(open(pz)))
    with Pool() as pool: res = pool.map(work, P, chunksize=2)
    rows, total = [], 0
    for pid, prog in res:
        if prog is None or (pid in Bp and len(Bp[pid]) <= len(prog)): prog = Bp[pid]
        total += len(prog); rows.append((pid, json.dumps(prog, separators=(",", ":"))))
    w = csv.writer(open(out, "w", newline="")); w.writerow(["id", "program"]); w.writerows(rows)
    print("score", total)

if __name__ == "__main__": main(*sys.argv[1:])
