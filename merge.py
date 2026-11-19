"""Birden çok submission'ı birleştirir: her bulmaca için doğrulanmış en kısa programı alır.
Kullanım: python merge.py puzzles.csv out.csv sub1.csv sub2.csv ..."""
import csv, json, sys
from validate import run
csv.field_size_limit(10**9)

def main(pz, out, *subs):
    P = {r["id"]: r for r in csv.DictReader(open(pz))}
    best, src = {}, {}
    for f in subs:
        for r in csv.DictReader(open(f)):
            if r["id"] not in P: continue
            p = P[r["id"]]
            try: prog = json.loads(r["program"])
            except Exception: continue
            if r["id"] in best and len(best[r["id"]]) <= len(prog): continue
            ok, _ = run(prog, json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"]))
            if ok: best[r["id"]] = prog; src[r["id"]] = f
    assert len(best) == len(P), f"missing {len(P) - len(best)}"
    w = csv.writer(open(out, "w", newline="")); w.writerow(["id", "program"])
    for pid in sorted(P): w.writerow([pid, json.dumps(best[pid], separators=(",", ":"))])
    from collections import Counter
    print("score", sum(map(len, best.values())), Counter(src.values()))

if __name__ == "__main__": main(*sys.argv[1:])
