"""Lokal doğrulayıcı/skorlayıcı. Varsayımlar (Data sayfası ile teyit edilecek):
- Başlangıç değerleri register 0..k-1'de, diğerleri tanımsız.
- Her sonuç pozitif tam sayı ve <= value_limit; '/' tam bölünmeli.
- Her hedef programın herhangi bir anında bir register'a yazılmış olmalı.
Kullanım: python validate.py puzzles.csv submission.csv"""
import csv, json, sys

def run(prog, start, targets, limit):
    if len(prog) > 4096: return False, "too many instructions"
    reg = [None]*48
    for i, v in enumerate(start): reg[i] = v
    need = set(targets) - set(start)
    for n, ins in enumerate(prog):
        op, a, b, d = ins
        if op not in "+-*/" or not all(isinstance(x, int) and 0 <= x < 48 for x in (a, b, d)):
            return False, f"bad instr {n}: {ins}"
        x, y = reg[a], reg[b]
        if x is None or y is None: return False, f"undefined src at {n}"
        if op == "+": r = x + y
        elif op == "-": r = x - y
        elif op == "*": r = x * y
        else:
            if x % y: return False, f"inexact division at {n}"
            r = x // y
        if r <= 0 or r > limit: return False, f"value out of range at {n}: {r}"
        reg[d] = r
        need.discard(r)
    if need: return False, f"{len(need)} targets missing"
    return True, len(prog)

def main(pz, sub):
    P = {r["id"]: r for r in csv.DictReader(open(pz))}
    total, bad = 0, 0
    seen = set()
    for r in csv.DictReader(open(sub)):
        p = P[r["id"]]; seen.add(r["id"])
        ok, info = run(json.loads(r["program"]), json.loads(p["starting_values"]),
                       json.loads(p["targets"]), int(p["value_limit"]))
        if ok: total += info
        else: bad += 1; print(r["id"], info)
    missing = set(P) - seen
    print(f"invalid={bad} missing={len(missing)} score={total}")

if __name__ == "__main__": main(*sys.argv[1:3])
