"""Plan yapısı analizi: küçük sabit sayısı, paylaşılan/özel düğümler, hedef başına özel maliyet."""
import sys, math, collections
sys.path.insert(0, '/home/user/santa--2026/sched')
from sched import read_plans
def stats(path, ids=None):
    out = {}
    for pid, lim, st, T, plan in read_plans(path):
        if ids and pid not in ids: continue
        Ts = set(T); rec = {r: (a, b) for op, a, b, r in plan}
        cons = collections.Counter()
        for op, a, b, r in plan: cons[a] += 1; cons[b] += 1 if b != a else 0
        small = sum(1 for op, a, b, r in plan if r < 1 << 16)
        mid = sum(1 for op, a, b, r in plan if 1 << 16 <= r < 1 << 36 and r not in Ts)
        big = sum(1 for op, a, b, r in plan if r >= 1 << 36 and r not in Ts)
        shared = sum(1 for op, a, b, r in plan if cons[r] >= 2)
        bits = sum(math.log2(t) for t in T) / len(T)
        out[pid] = dict(n=len(plan), nt=len(T), small=small, mid=mid, big=big, tgt=sum(1 for op,a,b,r in plan if r in Ts), shared=shared, bits=round(bits,1))
    return out
if __name__ == "__main__":
    A = stats(sys.argv[1]); B = stats(sys.argv[2], set(A))
    keys = ['n','small','mid','big','tgt','shared']
    print('totals A', {k: sum(v[k] for v in A.values()) for k in keys})
    print('totals B', {k: sum(v[k] for v in B.values()) for k in keys})
    for pid in list(A)[:20]:
        print(pid, A[pid]['nt'], A[pid]['bits'], ' A', [A[pid][k] for k in keys], ' B', [B[pid][k] for k in keys])
