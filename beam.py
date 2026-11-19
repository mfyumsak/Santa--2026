"""Sabit kümesi C ile beam search: t = q*m + d (m∈C, d∈±C∪{0}), q'ya özyineleme, q∈C'de dur."""
import math

def decompose(t, C, Cs, beam=16):
    # durum: (tahmini, maliyet, q, adımlar)
    Cl = sorted(C)
    states = [(0, 0, t, ())]
    best = None
    rate = 0.30
    while states:
        nxt = []
        for _, cost, q, steps in states:
            if q in Cs:
                if best is None or cost < best[0]: best = (cost, steps, q)
                continue
            if best is not None and cost >= best[0]: continue
            for m in Cl:
                if m < 2 or m > q: continue
                r = q % m
                cands = []
                if r == 0: cands.append(0)
                if r in Cs: cands.append(r)
                if (m - r) in Cs: cands.append(r - m)
                for d in cands:
                    nq = (q - d) // m
                    if nq <= 0: continue
                    c = cost + 1 + (d != 0)
                    nxt.append((c + rate * math.log2(nq + 1), c, nq, steps + ((m, d),)))
        nxt.sort(key=lambda x: x[0])
        seen = set(); states = []
        for s in nxt:
            if s[2] in seen: continue
            seen.add(s[2]); states.append(s)
            if len(states) >= beam: break
    return best  # (maliyet, adımlar (son adım önce), başlangıç q)
