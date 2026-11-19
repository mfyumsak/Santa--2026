"""Tony çözücüsünü farklı palet/ayarlarla çalıştırır, bulmaca bazında mevcut en iyiyle kıyaslar.
Kullanım: python run_variants.py variants.json subset_size out_dir"""
import csv, json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/mnt/project-files/santa2026')
from validate import run
csv.field_size_limit(10**9)
HERE = os.path.dirname(os.path.abspath(__file__))
P = {r["id"]: r for r in csv.DictReader(open('/mnt/project-files/santa2026/data/puzzles.csv'))}
BEST = {r["id"]: len(json.loads(r["program"])) for r in csv.DictReader(open('/mnt/project-files/santa2026/submission_best.csv'))}

def solve(args, ids):
    lines = []
    for pid in ids:
        p = P[pid]; s = json.loads(p["starting_values"]); T = sorted(json.loads(p["targets"]))
        lines.append(" ".join(map(str, (pid, p["value_limit"], len(s), len(T), *s, *T))))
    r = subprocess.run([os.path.join(HERE, "tony_solver"), *map(str, args)], input="\n".join(lines),
                       text=True, capture_output=True, timeout=36000)
    out = {}
    for line in r.stdout.splitlines():
        pid, prog = line.split(" ", 1); prog = json.loads(prog)
        p = P[pid]
        if run(prog, json.loads(p["starting_values"]), json.loads(p["targets"]), int(p["value_limit"]))[0]:
            out[pid] = prog
    return out

if __name__ == "__main__":
    variants = json.load(open(sys.argv[1])); n = int(sys.argv[2]); od = sys.argv[3]
    os.makedirs(od, exist_ok=True)
    ids = sorted(P)[::max(1, 1000 // n)][:n]
    batches = [ids[i::4] for i in range(4)]
    for name, args in variants.items():
        with ThreadPoolExecutor(4) as ex: parts = list(ex.map(lambda b: solve(args, b), batches))
        res = {k: v for d in parts for k, v in d.items()}
        tot = sum(len(v) for v in res.values()); best = sum(BEST[k] for k in res)
        wins = sum(len(res[k]) < BEST[k] for k in res)
        print(f"{name}: solved {len(res)}/{len(ids)} total {tot} vs best {best} wins {wins}", flush=True)
        with open(os.path.join(od, name + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["id", "program"])
            for k, v in res.items(): w.writerow([k, json.dumps(v, separators=(",", ":"))])
