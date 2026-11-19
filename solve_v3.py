"""v3: her bulmaca için birkaç sabit kümesi dener, en kısa geçerli programı alır; mevcut en iyi submission ile birleştirir.
Kullanım: python solve_v3.py puzzles.csv out.csv best_so_far.csv"""
import csv, json, sys
from multiprocessing import Pool
import solve_v2
from validate import run

PR = [p for p in range(2, 2000) if all(p % q for q in range(2, int(p**.5) + 1))]
DESIGNS = [
    list(range(1, 25)) + [p for p in PR if p > 24][::2][:22],
    list(range(1, 17)) + [p for p in PR if p > 16][:30],
    list(range(1, 21)) + [p for p in PR if p > 20][:20] + [32, 64, 128, 256, 512, 1024],
    list(range(1, 25)) + [p for p in PR if p > 24][:22],
    list(range(1, 13)) + [p for p in PR if p > 12][::2][:34],
]

def work(p):
    s, T, L = json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"])
    best = None
    for C in DESIGNS:
        solve_v2.BASE = C
        try:
            prog = solve_v2.build(s, T, L, 16)
            if run(prog, s, T, L)[0] and (best is None or len(prog) < len(best)): best = prog
        except Exception: pass
    return p["id"], best

def main(pz, out, prev):
    B = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(prev))}
    with Pool() as pool: res = pool.map(work, list(csv.DictReader(open(pz))), chunksize=4)
    rows, total = [], 0
    for pid, prog in res:
        if prog is None or len(B[pid]) <= len(prog): prog = B[pid]
        total += len(prog); rows.append((pid, json.dumps(prog, separators=(",", ":"))))
    w = csv.writer(open(out, "w", newline="")); w.writerow(["id", "program"]); w.writerows(rows)
    print("score", total)

if __name__ == "__main__": main(*sys.argv[1:])
