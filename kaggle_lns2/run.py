"""Santa 2026: goodpjw2008'in açık kaynak DAG-LNS motorunu (elfopt.cpp) bizim en iyi programlarımız
üzerinde turlar halinde çalıştırır. Her tur sonunda doğrulanmış daha kısa programlar submission.csv'ye yazılır."""
import csv, json, os, subprocess, random, time
from pathlib import Path
csv.field_size_limit(10**9)
T0 = time.time(); BUDGET = float(os.environ.get("BUDGET", 10.3 * 3600))
INP = Path("/kaggle/input"); WORK = Path("/kaggle/working")

def pick(name, prefer=""):
    hits = sorted(INP.rglob(name))
    pref = [h for h in hits if prefer in str(h)]
    return (pref or hits)[0]

PUZ = pick("puzzles.csv", "santa-2026/puzzles.csv"); SRC = pick("elfopt.cpp"); BEST = pick("best.csv", "santa2026-best-programs")
print("inputs:", PUZ, SRC, BEST, flush=True)
P = {r["id"]: r for r in csv.DictReader(open(PUZ))}
B = {r["id"]: json.loads(r["program"]) for r in csv.DictReader(open(BEST))}

def replay(p, prog):
    R = int(p["registers"]); st = json.loads(p["starting_values"]); L = int(p["value_limit"])
    if len(prog) > 4096: return False
    regs = list(st) + [None] * (R - len(st)); need = set(json.loads(p["targets"])) - set(st)
    for ins in prog:
        if not (isinstance(ins, list) and len(ins) == 4): return False
        op, i, j, d = ins
        if not all(type(r) is int and 0 <= r < R for r in (i, j, d)): return False
        a, b = regs[i], regs[j]
        if a is None or b is None: return False
        if op == "+": v = a + b
        elif op == "-": v = a - b
        elif op == "*": v = a * b
        elif op == "/":
            if a % b: return False
            v = a // b
        else: return False
        if not 1 <= v <= L: return False
        regs[d] = v; need.discard(v)
    return not need

assert all(replay(P[k], B[k]) for k in P), "başlangıç programları geçersiz"
def total(): return sum(len(B[k]) for k in P)
print("start total", total(), flush=True)

exe = WORK / "elfopt"
subprocess.run(["g++", "-std=c++17", "-O3", "-march=native", "-o", str(exe), str(SRC)], check=True)
jobs = os.cpu_count() or 4

def enc(pid):
    p = P[pid]; st = json.loads(p["starting_values"]); T = json.loads(p["targets"]); prog = B[pid]
    head = ["P", pid, str(len(st)), *map(str, st), str(len(T)), *map(str, T), p["value_limit"], p["registers"], str(len(prog))]
    return " ".join(head) + "\n" + "".join(f"{o} {i} {j} {d}\n" for o, i, j, d in prog)

def write_out():
    with open(WORK / "submission.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "program"])
        for pid in sorted(P): w.writerow([pid, json.dumps(B[pid], separators=(",", ":"))])

write_out(); hist = []
rnd = 0; tper = float(os.environ.get("TPER", 30))
while True:
    remaining = BUDGET - (time.time() - T0)
    est = len(P) * tper / jobs
    if est * 1.15 + 300 > remaining:
        tper = (remaining - 600) * jobs / len(P) / 1.15
        if tper < 3: break
        est = len(P) * tper / jobs
    ids = sorted(P, key=lambda k: -len(B[k]))
    d = WORK / f"r{rnd}"; d.mkdir(exist_ok=True); procs = []
    for s in range(jobs):
        (d / f"in{s}.txt").write_text("".join(enc(k) for k in ids[s::jobs]))
        seed = random.randrange(1, 10**9)
        cmd = f"{exe} --time {tper:.1f} --seed {seed} < {d}/in{s}.txt > {d}/out{s}.txt 2> {d}/log{s}.txt"
        procs.append(subprocess.Popen(cmd, shell=True))
    deadline = time.time() + est * 1.5 + 120
    for pr in procs:
        try: pr.wait(timeout=max(1, deadline - time.time()))
        except subprocess.TimeoutExpired: pr.kill()
    gain = imp = 0
    for s in range(jobs):
        L = (d / f"out{s}.txt").read_text().split("\n"); k = 0
        while k < len(L):
            t = L[k].split()
            if t and t[0] == "R" and k + 1 + int(t[3]) <= len(L):
                pid, n = t[1], int(t[3])
                try: prog = [[o, int(i), int(j), int(dd)] for o, i, j, dd in (L[k + 1 + q].split() for q in range(n))]
                except ValueError: prog = None
                k += n + 1
                if prog and pid in P and len(prog) < len(B[pid]) and replay(P[pid], prog):
                    gain += len(B[pid]) - len(prog); imp += 1; B[pid] = prog
            else: k += 1
    write_out()
    hist.append({"round": rnd, "tper": round(tper, 1), "improved": imp, "gain": gain, "total": total(), "elapsed_h": round((time.time() - T0) / 3600, 2)})
    (WORK / "history.json").write_text(json.dumps(hist, indent=1))
    print(hist[-1], flush=True)
    for f in d.glob("in*.txt"): f.unlink()
    rnd += 1
print("final total", total(), flush=True)
