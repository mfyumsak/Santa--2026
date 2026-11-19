"""Program <-> değer-seviyesi dönüşüm ve register ataması.
to_text: submission.csv -> C++ girdisi; from_text: C++ çıktısı -> submission.csv (register atamalı, doğrulanmış)."""
import csv, json, sys
sys.path.insert(0, '/mnt/project-files/santa2026')
from validate import run
csv.field_size_limit(10**9)

def to_values(prog, start):
    reg = [None]*48
    for i, v in enumerate(start): reg[i] = v
    out = []
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        r = {"+": lambda: x+y, "-": lambda: x-y, "*": lambda: x*y, "/": lambda: x//y}[op]()
        out.append((op, x, y, r)); reg[d] = r
    return out

def allocate(vops, start):
    """vops: [(op, va, vb, vr)] topolojik sırada. Hedefsiz ölü kod olmadığı varsayılır."""
    last = {}
    for i, (op, a, b, r) in enumerate(vops):
        last[a] = i; last[b] = i
    where = {}
    free = []
    regval = [None]*48
    for i, v in enumerate(start):
        if v in where: continue
        where[v] = i; regval[i] = v
    for i in range(len(start), 48): free.append(i)
    # kullanılmayan başlangıç değerlerini serbest bırak
    for v, r in list(where.items()):
        if v not in last: free.append(r); del where[v]
    prog = []
    for i, (op, a, b, r) in enumerate(vops):
        ra, rb = where[a], where[b]
        for v in {a, b}:
            if last[v] == i and v in where:
                free.append(where.pop(v))
        if r in where:  # zaten var (tekrar) — yine de yaz
            d = where[r]
        else:
            if not free: return None
            d = free.pop()
            if last.get(r, -1) > i: where[r] = d
            else: free.append(d)  # sonra kullanılmıyor
        prog.append([op, ra, rb, d])
    return prog

if __name__ == "__main__":
    mode = sys.argv[1]
    P = {r["id"]: r for r in csv.DictReader(open(sys.argv[2]))}
    if mode == "to":
        out = open(sys.argv[4], "w")
        for r in csv.DictReader(open(sys.argv[3])):
            p = P[r["id"]]; s = json.loads(p["starting_values"]); T = json.loads(p["targets"])
            v = to_values(json.loads(r["program"]), s)
            out.write(f"{r['id']} {p['value_limit']} {len(s)} {len(T)} {len(v)}\n")
            out.write(" ".join(map(str, s)) + "\n" + " ".join(map(str, T)) + "\n")
            for op, a, b, c in v: out.write(f"{op} {a} {b} {c}\n")
    else:  # from: puzzles.csv cpp_out.txt prev_sub.csv out.csv
        prev = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(sys.argv[4]))}
        lines = open(sys.argv[3]).read().split("\n"); i = 0; best = dict(prev); gain = 0
        while i < len(lines) and lines[i].strip():
            pid, n = lines[i].split(); n = int(n); i += 1
            vops = []
            for _ in range(n):
                op, a, b, c = lines[i].split(); vops.append((op, int(a), int(b), int(c))); i += 1
            p = P[pid]; s = json.loads(p["starting_values"]); T = json.loads(p["targets"]); L = int(p["value_limit"])
            prog = allocate(vops, s)
            if prog and len(prog) < len(best[pid]) and run(prog, s, T, L)[0]:
                gain += len(best[pid]) - len(prog); best[pid] = prog
        w = csv.writer(open(sys.argv[5], "w", newline="")); w.writerow(["id", "program"])
        for pid in sorted(P): w.writerow([pid, json.dumps(best[pid], separators=(",", ":"))])
        print("gain", gain, "score", sum(map(len, best.values())))
