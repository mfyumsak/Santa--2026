"""Santa 2026: tkm2261/nagiss'in açık GPU koni aramasını (ag_gpu_factor_cone_v4.py) bizim en iyi
programlarımızdan üretilen sorgularda çalıştırır. Çıktı: sav*.txt (SAVING satırları) + loglar.
Uygulama/doğrulama yerelde cone/apply_sav.py ile yapılır."""
import os, sys, csv, json, subprocess, time, shutil
from pathlib import Path
csv.field_size_limit(10**9)
T0 = time.time(); BUDGET = float(os.environ.get("BUDGET", 3.3 * 3600))
INP = Path("/kaggle/input"); WORK = Path("/kaggle/working")

def pick(name, prefer=""):
    hits = sorted(INP.rglob(name)); pref = [h for h in hits if prefer in str(h)]
    return (pref or hits)[0]

PUZ = pick("puzzles.csv", "santa-2026"); BEST = pick("best.csv", "santa2026-best-programs")
PY = pick("ag_gpu_factor_cone_v4.py"); CPP = pick("ag_factor_helper_v2.cpp")
print("inputs:", PUZ, BEST, PY, CPP, flush=True)
AG = WORK / "ag"; (AG / "build").mkdir(parents=True, exist_ok=True)
shutil.copy(PY, AG / "cone.py")
subprocess.run(["g++", "-O3", "-shared", "-fPIC", "-std=c++17", str(CPP), "-o", str(AG / "build" / "ag_factor_helper_v2.so")], check=True)
try:
    import cupy  # noqa
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cupy-cuda12x"], check=True)

# --- sorgu üretimi (cone/gen_queries.py ile aynı) ---
def to_values(prog, st):
    reg = [None] * 48
    for i, v in enumerate(st): reg[i] = v
    out = []
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        r = x + y if op == "+" else x - y if op == "-" else x * y if op == "*" else x // y
        out.append((op, x, y, r)); reg[d] = r
    return out

def dag(prog, st):
    stset = set(st); rec = {}; order = []
    for op, a, b, r in to_values(prog, st):
        if r in stset or r in rec: continue
        rec[r] = (op, a, b); order.append(r)
    users = {}
    for r in order:
        op, a, b = rec[r]
        users.setdefault(a, set()).add(r); users.setdefault(b, set()).add(r)
    return rec, order, users

def cone_of(T, rec, users, stset, tgset, idx):
    cone = {T}; anc = set(); stack = [T]
    while stack:
        v = stack.pop(); op, a, b = rec[v]
        for x in (a, b):
            if x in rec and x not in anc: anc.add(x); stack.append(x)
    for x in sorted(anc, key=lambda v: -idx[v]):
        if x in tgset or x in stset: continue
        if users.get(x, set()) <= cone: cone.add(x)
    return cone

def desc_of(T, users):
    d = set(); stack = [T]
    while stack:
        v = stack.pop()
        for u in users.get(v, ()):
            if u not in d: d.add(u); stack.append(u)
    return d

P = {r["id"]: r for r in csv.DictReader(open(PUZ))}
Q = []
for r in csv.DictReader(open(BEST)):
    p = P[r["id"]]; st = json.loads(p["starting_values"]); tg = json.loads(p["targets"]); L = int(p["value_limit"])
    rec, order, users = dag(json.loads(r["program"]), st)
    idx = {v: i for i, v in enumerate(order)}; stset, tgset = set(st), set(tg); allv = set(order) | stset
    for T in order:
        c = cone_of(T, rec, users, stset, tgset, idx)
        if len(c) < 5: continue
        base = sorted(allv - c - desc_of(T, users))
        Q.append((len(c), f"{r['id']} {T} {len(c)} {L} {len(base)} " + " ".join(map(str, base))))
Q.sort(key=lambda x: -x[0])
print("queries", len(Q), flush=True)

ng = max(1, len([l for l in subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout.splitlines() if l.startswith("GPU")]))
print("gpus", ng, flush=True)
subprocess.run([sys.executable, str(AG / "cone.py"), "--selftest"], cwd=str(AG), env=dict(os.environ, CUDA_VISIBLE_DEVICES="0"))
procs = []
for g in range(ng):
    qf = WORK / f"q{g}.txt"
    with open(qf, "w") as f:
        for i, (_, line) in enumerate(Q):
            if i % ng == g: f.write(line + "\n")
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(g), ALLOW_EQ="0")
    log = open(WORK / f"log{g}.txt", "w")
    procs.append(subprocess.Popen([sys.executable, str(AG / "cone.py"), str(qf), str(WORK / f"sav{g}.txt"), "5", "99"],
                                  cwd=str(AG), env=env, stdout=log, stderr=subprocess.STDOUT))
while any(p.poll() is None for p in procs):
    if time.time() - T0 > BUDGET:
        print("bütçe doldu, durduruluyor", flush=True)
        for p in procs:
            if p.poll() is None: p.kill()
        break
    time.sleep(30)
n = sum(1 for g in range(ng) if (WORK / f"sav{g}.txt").exists() for l in open(WORK / f"sav{g}.txt") if "SAVING" in l)
print("SAVING lines", n, "elapsed", round(time.time() - T0), flush=True)
for g in range(ng):
    print(f"--- log{g} tail ---"); print("".join(open(WORK / f"log{g}.txt").readlines()[-5:]), flush=True)
shutil.rmtree(AG / "build", ignore_errors=True)
