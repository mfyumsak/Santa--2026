"""resynth çıktısını (id n + satırlar) plan biçimine çevirir; başlangıç/hedefleri girdi planından alır."""
import sys
sys.path.insert(0, '/home/user/santa--2026/sched')
from sched import read_plans
meta = {pid: (lim, st, T) for pid, lim, st, T, plan in read_plans(sys.argv[1])}
L = open(sys.argv[2]).read().split('\n'); i = 0; out = []
while i < len(L) and L[i].strip():
    pid, n = L[i].split(); n = int(n); lim, st, T = meta[pid]
    out.append(f"{pid} {lim} {len(st)} {len(T)} {n}\n{' '.join(map(str, st))}\n{' '.join(map(str, T))}")
    out.extend(L[i+1:i+1+n]); i += 1 + n
open(sys.argv[3], 'w').write('\n'.join(out) + '\n')
