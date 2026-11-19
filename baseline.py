"""Baseline: signed-digit Horner, taban M=2D+1, rakamlar 1..D register'larda.
Kullanım: python baseline.py puzzles.csv out.csv"""
import csv, json, sys

def sd_digits(t, M, D):
    ds = []
    while t:
        r = t % M
        if r > D: r -= M
        ds.append(r); t = (t - r) // M
    return ds[::-1]  # en anlamlı önce, ilk rakam > 0

def solve(start, targets, limit, D):
    k = len(start)
    prog = []
    ONE = k
    prog.append(["/", 0, 0, ONE])
    reg = {1: ONE}  # değer -> register
    for i, v in enumerate(start): reg.setdefault(v, i)
    nxt = k + 1
    for v in range(2, D + 1):  # 1..D rakamları
        if v not in reg:
            prog.append(["+", reg[v - 1], ONE, nxt]); reg[v] = nxt; nxt += 1
    M = 2 * D + 1
    if M not in reg:
        prog.append(["+", reg[D], reg[D + 1] if D + 1 in reg else reg[D], nxt])
        if D + 1 not in reg:  # 2D, sonra +1
            prog.append(["+", nxt, ONE, nxt])
        reg[M] = nxt; nxt += 1
    MR = reg[M]; ACC = nxt
    assert ACC < 48
    have = set(start)
    for t in targets:
        if t in have or t in reg: continue
        ds = sd_digits(t, M, D)
        cur = ds[0]; src = reg[ds[0]]
        first = True
        for d in ds[1:]:
            prog.append(["*", src, MR, ACC]); src = ACC; cur *= M
            if d > 0: prog.append(["+", ACC, reg[d], ACC]); cur += d
            elif d < 0: prog.append(["-", ACC, reg[-d], ACC]); cur += d
        assert cur == t
        if len(ds) == 1:
            prog.append(["+", src, src, ACC]); prog.append(["/", ACC, reg[2], ACC])
        have.add(t)
    return prog

def main(pz, out):
    from validate import run
    rows, total = [], 0
    for p in csv.DictReader(open(pz)):
        s, T, L = json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"])
        best = None
        for D in range(2, 48 - len(s) - 3):
            try: prog = solve(s, T, L, D)
            except (AssertionError, KeyError): continue
            ok, info = run(prog, s, T, L)
            if ok and (best is None or len(prog) < len(best)): best = prog
        assert best is not None, p["id"]
        total += len(best)
        rows.append((p["id"], json.dumps(best, separators=(",", ":"))))
    w = csv.writer(open(out, "w", newline="")); w.writerow(["id", "program"]); w.writerows(rows)
    print("score", total)

if __name__ == "__main__": main(*sys.argv[1:3])
