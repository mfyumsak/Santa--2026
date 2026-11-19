"""v2: küçük sabitler + asal çarpanlar register'da, her hedef beam search ile (t = q*m ± d).
Kullanım: python solve_v2.py puzzles.csv out.csv [baseline.csv]"""
import csv, json, sys
from multiprocessing import Pool
from beam import decompose
from validate import run

BASE = list(range(1, 25)) + [29,31,37,41,43,47,53,59,61,64,67,71,73,79,83,89,97,101,103,107,109,113]

def build(start, targets, limit, beam=16):
    k = len(start)
    reg = {}
    for i, v in enumerate(start): reg.setdefault(v, i)
    nxt = k
    prog = []
    if 1 not in reg:
        prog.append(["/", 0, 0, nxt]); reg[1] = nxt; nxt += 1
    room = 47 - nxt  # ACC için 1 bırak
    C = [c for c in BASE if c not in reg]
    C = C[:room]
    for c in C:
        vals = sorted(reg)
        done = False
        for a in vals:
            if a >= c: break
            if c - a in reg:
                prog.append(["+", reg[a], reg[c - a], nxt]); done = True; break
        if not done:
            for a in vals:
                if a > 1 and c % a == 0 and c // a in reg:
                    prog.append(["*", reg[a], reg[c // a], nxt]); done = True; break
        if not done:  # +1 zinciri
            m = max(v for v in reg if v < c)
            prog.append(["+", reg[m], reg[1], nxt])
            for _ in range(c - m - 1): prog.append(["+", nxt, reg[1], nxt])
        reg[c] = nxt; nxt += 1
    ACC = nxt
    Cl = sorted(reg); Cs = set(Cl)
    for t in targets:
        if t in Cs: continue
        cost, steps, q = decompose(t, Cl, Cs, beam)
        src = reg[q]
        for m, d in reversed(steps):
            prog.append(["*", src, reg[m], ACC]); src = ACC
            if d > 0: prog.append(["+", ACC, reg[d], ACC])
            elif d < 0: prog.append(["-", ACC, reg[-d], ACC])
    return prog

def work(p):
    s, T, L = json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"])
    prog = build(s, T, L)
    ok, info = run(prog, s, T, L)
    return p["id"], (prog if ok else None), info

def main(pz, out, base=None):
    P = list(csv.DictReader(open(pz)))
    B = {}
    if base:
        B = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(base))}
    with Pool() as pool: res = pool.map(work, P, chunksize=4)
    rows, total, fails, better = [], 0, 0, 0
    for pid, prog, info in res:
        alt = B.get(pid)
        if prog is None: fails += 1
        if prog is None or (alt is not None and len(alt) < len(prog)): prog = alt
        else: better += 1
        total += len(prog)
        rows.append((pid, json.dumps(prog, separators=(",", ":"))))
    w = csv.writer(open(out, "w", newline="")); w.writerow(["id", "program"]); w.writerows(rows)
    print(f"score={total} fails={fails} v2_better={better}")

if __name__ == "__main__": main(*sys.argv[1:])
