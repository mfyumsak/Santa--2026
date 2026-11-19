// Zincir yeniden sentezi: her düğümün özel konisini (yalnızca ona hizmet eden ara değerler)
// 1-3 talimatlık daha kısa bir ifadeyle değiştirmeye çalışır. Girdi/çıktı: değer seviyesinde program.
#include <bits/stdc++.h>
using namespace std;
typedef long long ll; typedef __int128 LL;
struct Ins { char op; ll a, b, r; };
static ll LIMIT; static int MAXD = 3; static int MODE = 1;
static inline bool apply(char op, ll x, ll y, ll &r) {
    LL v;
    switch (op) {
        case '+': v = (LL)x + y; break;
        case '-': v = (LL)x - y; break;
        case '*': v = (LL)x * y; break;
        default: if (y == 0 || x % y) return false; v = x / y;
    }
    if (v <= 0 || v > LIMIT) return false;
    r = (ll)v; return true;
}
struct Puzzle { string id; ll limit; vector<ll> start, targets; vector<Ins> prog; };

// Program temizliği: tekrarları ve ölü kodu at.
vector<Ins> clean(const vector<Ins>& p, const vector<ll>& start, const vector<ll>& targets) {
    unordered_set<ll> have(start.begin(), start.end());
    vector<Ins> q;
    for (auto& i : p) if (!have.count(i.r)) { have.insert(i.r); q.push_back(i); }
    unordered_set<ll> need(targets.begin(), targets.end());
    vector<char> keep(q.size(), 0);
    for (int i = (int)q.size() - 1; i >= 0; i--) {
        if (need.count(q[i].r)) { keep[i] = 1; need.insert(q[i].a); need.insert(q[i].b); }
    }
    vector<Ins> o; for (size_t i = 0; i < q.size(); i++) if (keep[i]) o.push_back(q[i]);
    return o;
}
// Register baskısı kontrolü (en fazla 48 canlı değer).
bool fits(const vector<Ins>& p, const vector<ll>& start) {
    unordered_map<ll,int> last;
    for (int i = 0; i < (int)p.size(); i++) { last[p[i].a] = i; last[p[i].b] = i; }
    int live = 0; unordered_set<ll> s;
    for (ll v : start) if (last.count(v) && s.insert(v).second) live++;
    if (live > 48) return false;
    for (int i = 0; i < (int)p.size(); i++) {
        int dying = 0;
        for (ll v : {p[i].a, p[i].b}) if (last[v] == i && s.erase(v)) dying++;
        live -= dying;
        if (live + 1 > 48) return false;
        if (last.count(p[i].r) && last[p[i].r] > i && s.insert(p[i].r).second) live++;
    }
    return true;
}
// Topolojik sıralama, anahtar = konum önceliği.
bool topo(vector<pair<double,Ins>>& items, const vector<ll>& start, vector<Ins>& out) {
    unordered_map<ll,int> prod;
    for (int i = 0; i < (int)items.size(); i++) prod[items[i].second.r] = i;
    unordered_set<ll> st(start.begin(), start.end());
    int n = items.size(); vector<int> indeg(n, 0); vector<vector<int>> adj(n);
    for (int i = 0; i < n; i++) {
        set<int> deps;
        for (ll v : {items[i].second.a, items[i].second.b}) {
            if (st.count(v)) continue;
            auto it = prod.find(v); if (it == prod.end()) return false;
            deps.insert(it->second);
        }
        for (int d : deps) { adj[d].push_back(i); indeg[i]++; }
    }
    priority_queue<pair<double,int>, vector<pair<double,int>>, greater<>> pq;
    for (int i = 0; i < n; i++) if (!indeg[i]) pq.push({items[i].first, i});
    out.clear();
    while (!pq.empty()) {
        int i = pq.top().second; pq.pop(); out.push_back(items[i].second);
        for (int j : adj[i]) if (--indeg[j] == 0) pq.push({items[j].first, j});
    }
    return (int)out.size() == n;
}
static const char OPS[4] = {'+','-','*','/'};
// t'yi A kümesinden en fazla maxd talimatla kur. Bulunursa talimatları döndür.
bool synth(ll t, const vector<ll>& A, int maxd, vector<Ins>& res) {
    unordered_set<ll> As(A.begin(), A.end());
    auto inA = [&](ll v){ return As.count(v) > 0; };
    // derinlik 1
    for (ll a : A) for (ll b : A) for (char op : OPS) { ll r; if (apply(op, a, b, r) && r == t) { res = {{op,a,b,t}}; return true; } }
    if (maxd < 2) return false;
    // P1: A'dan bir talimatla yeni değerler
    unordered_map<ll, Ins> P1; P1.reserve(A.size()*A.size()*3);
    for (ll a : A) for (ll b : A) for (char op : OPS) {
        if ((op=='+'||op=='*') && a > b) continue;
        ll r; if (apply(op, a, b, r) && !inA(r) && !P1.count(r)) P1[r] = {op,a,b,r};
    }
    // derinlik 2: t = x op a, a op x, x op x
    auto check2 = [&](ll x, Ins& last)->bool {
        ll r;
        for (ll a : A) for (char op : OPS) {
            if (apply(op, x, a, r) && r == t) { last = {op,x,a,t}; return true; }
            if (apply(op, a, x, r) && r == t) { last = {op,a,x,t}; return true; }
        }
        for (char op : OPS) if (apply(op, x, x, r) && r == t) { last = {op,x,x,t}; return true; }
        return false;
    };
    // hızlı derinlik 2: t'nin tersinden aday x'ler
    for (ll a : A) {
        ll cands[5]; int nc = 0; LL v;
        v = (LL)t - a; if (v > 0) cands[nc++] = (ll)v;           // t = x + a
        v = (LL)t + a; if (v <= LIMIT) cands[nc++] = (ll)v;      // t = x - a
        v = (LL)a - t; if (v > 0) cands[nc++] = (ll)v;           // t = a - x
        if (t % a == 0) cands[nc++] = t / a;                     // t = x * a
        v = (LL)t * a; if (v <= LIMIT) cands[nc++] = (ll)v;      // t = x / a
        if (a % t == 0) cands[nc++] = a / t;                     // t = a / x
        for (int k = 0; k < nc; k++) {
            auto it = P1.find(cands[k]);
            if (it != P1.end()) { Ins last; if (check2(it->first, last)) { res = {it->second, last}; return true; } }
        }
    }
    for (auto& [x, ins] : P1) { ll r; for (char op : OPS) if (apply(op, x, x, r) && r == t) { res = {ins, {op,x,x,t}}; return true; } }
    if (maxd < 3) return false;
    // derinlik 3a: t = x op y, x,y ∈ P1
    for (auto& [x, ix] : P1) {
        ll c[6]; int nc = 0; LL v;
        v = (LL)t - x; if (v > 0) c[nc++] = (ll)v;
        v = (LL)t + x; if (v <= LIMIT) c[nc++] = (ll)v;
        v = (LL)x - t; if (v > 0) c[nc++] = (ll)v;
        if (t % x == 0) c[nc++] = t / x;
        v = (LL)t * x; if (v <= LIMIT) c[nc++] = (ll)v;
        if (x % t == 0) c[nc++] = x / t;
        for (int k = 0; k < nc; k++) {
            auto it = P1.find(c[k]); if (it == P1.end()) continue;
            ll y = it->first; ll r;
            for (char op : OPS) {
                if (apply(op, x, y, r) && r == t) { res = {ix, it->second, {op,x,y,t}}; return true; }
                if (apply(op, y, x, r) && r == t) { res = {ix, it->second, {op,y,x,t}}; return true; }
            }
        }
    }
    // derinlik 3b: t = (x op a) op b, x ∈ P1, a,b ∈ A  — t'den iki kez geriye git
    auto inv = [&](ll t0, ll a, ll* c, char* ops, bool* left)->int {
        int nc = 0; LL v;
        v = (LL)t0 - a; if (v > 0) { c[nc]=(ll)v; ops[nc]='+'; left[nc]=true; nc++; }
        v = (LL)t0 + a; if (v <= LIMIT) { c[nc]=(ll)v; ops[nc]='-'; left[nc]=true; nc++; }
        v = (LL)a - t0; if (v > 0) { c[nc]=(ll)v; ops[nc]='-'; left[nc]=false; nc++; }
        if (t0 % a == 0) { c[nc]=t0/a; ops[nc]='*'; left[nc]=true; nc++; }
        v = (LL)t0 * a; if (v <= LIMIT) { c[nc]=(ll)v; ops[nc]='/'; left[nc]=true; nc++; }
        if (a % t0 == 0) { c[nc]=a/t0; ops[nc]='/'; left[nc]=false; nc++; }
        return nc;
    };
    for (ll b : A) {
        ll c1[6]; char o1[6]; bool l1[6]; int n1 = inv(t, b, c1, o1, l1);
        for (int i = 0; i < n1; i++) {
            ll w = c1[i]; if (inA(w)) continue;
            for (ll a : A) {
                ll c2[6]; char o2[6]; bool l2[6]; int n2 = inv(w, a, c2, o2, l2);
                for (int j = 0; j < n2; j++) {
                    auto it = P1.find(c2[j]); if (it == P1.end()) continue;
                    ll x = it->first;
                    Ins s2 = l2[j] ? Ins{o2[j], x, a, w} : Ins{o2[j], a, x, w};
                    Ins s3 = l1[i] ? Ins{o1[i], w, b, t} : Ins{o1[i], b, w, t};
                    res = {it->second, s2, s3}; return true;
                }
            }
        }
    }
    if (maxd < 4) return false;
    // derinlik 4: t = (x op y) op a, x,y ∈ P1, a ∈ A
    for (ll a : A) {
        ll c1[6]; char o1[6]; bool l1[6]; int n1 = inv(t, a, c1, o1, l1);
        for (int i = 0; i < n1; i++) {
            ll w = c1[i]; if (inA(w) || P1.count(w)) continue;
            for (auto& [x, ix] : P1) {
                ll c2[6]; char o2[6]; bool l2[6]; int n2 = inv(w, x, c2, o2, l2);
                for (int j = 0; j < n2; j++) {
                    auto it = P1.find(c2[j]); if (it == P1.end()) continue;
                    ll y = it->first;
                    Ins s2 = l2[j] ? Ins{o2[j], y, x, w} : Ins{o2[j], x, y, w};
                    Ins s3 = l1[i] ? Ins{o1[i], w, a, t} : Ins{o1[i], a, w, t};
                    res = {ix, it->second, s2, s3}; return true;
                }
            }
        }
    }
    // derinlik 4 zincir: t = ((x op a) op b) op c, x ∈ P1 — geriye iki adım (B2), ileriye bir adım
    {
        struct BE { ll w; Ins s2, s3; };
        vector<BE> B2;
        for (ll c : A) {
            ll c1[6]; char o1[6]; bool l1[6]; int n1 = inv(t, c, c1, o1, l1);
            for (int i = 0; i < n1; i++) {
                ll y = c1[i]; if (inA(y) || P1.count(y)) continue;
                Ins s3 = l1[i] ? Ins{o1[i], y, c, t} : Ins{o1[i], c, y, t};
                for (ll b : A) {
                    ll c2[6]; char o2[6]; bool l2[6]; int n2 = inv(y, b, c2, o2, l2);
                    for (int j = 0; j < n2; j++) {
                        ll w = c2[j]; if (inA(w)) continue;
                        Ins s2 = l2[j] ? Ins{o2[j], w, b, y} : Ins{o2[j], b, w, y};
                        B2.push_back({w, s2, s3});
                    }
                }
            }
        }
        // açık adresleme tablo
        size_t cap = 1; while (cap < B2.size() * 2 + 16) cap <<= 1;
        vector<ll> key(cap, 0); vector<int> idx(cap, -1);
        auto slot = [&](ll v) { uint64_t h = (uint64_t)v * 0x9e3779b97f4a7c15ULL; h ^= h >> 31; return (size_t)(h & (cap - 1)); };
        for (int k = 0; k < (int)B2.size(); k++) { size_t i = slot(B2[k].w); while (key[i] && key[i] != B2[k].w) i = (i + 1) & (cap - 1); if (!key[i]) { key[i] = B2[k].w; idx[i] = k; } }
        auto get = [&](ll v)->int { size_t i = slot(v); while (key[i]) { if (key[i] == v) return idx[i]; i = (i + 1) & (cap - 1); } return -1; };
        for (auto& [x, ix] : P1) {
            for (ll a : A) for (char op : OPS) {
                ll w;
                if (apply(op, x, a, w)) { int k = get(w); if (k >= 0) { res = {ix, {op, x, a, w}, B2[k].s2, B2[k].s3}; return true; } }
                if ((op == '-' || op == '/') && apply(op, a, x, w)) { int k = get(w); if (k >= 0) { res = {ix, {op, a, x, w}, B2[k].s2, B2[k].s3}; return true; } }
            }
        }
    }
    return false;
}

int improve(Puzzle& P, mt19937& rng) {
    LIMIT = P.limit;
    vector<Ins> prog = clean(P.prog, P.start, P.targets);
    int gained = (int)P.prog.size() - (int)prog.size();
    unordered_set<ll> startS(P.start.begin(), P.start.end()), targS(P.targets.begin(), P.targets.end());
    bool any = true;
    while (any) {
        any = false;
        int n = prog.size();
        unordered_map<ll,int> pos; for (int i = 0; i < n; i++) pos[prog[i].r] = i;
        // tüketiciler
        vector<vector<int>> cons(n);
        for (int i = 0; i < n; i++) for (ll v : {prog[i].a, prog[i].b}) { auto it = pos.find(v); if (it != pos.end() && (cons[it->second].empty() || cons[it->second].back() != i)) cons[it->second].push_back(i); }
        vector<int> order(n); iota(order.begin(), order.end(), 0); shuffle(order.begin(), order.end(), rng);
        for (int vi : order) {
            // özel koni: v'ye geriye doğru, tüm tüketicileri konide olan hedef olmayan düğümler
            vector<char> inC(n, 0); inC[vi] = 1; vector<int> cone;
            bool grew = true;
            // geriye doğru: v'nin atalarını tara (büyükten küçüğe indeks)
            for (int i = vi - 1; i >= 0; i--) {
                if (targS.count(prog[i].r)) continue;
                bool allIn = !cons[i].empty();
                for (int c : cons[i]) if (!inC[c]) { allIn = false; break; }
                if (allIn) { inC[i] = 1; cone.push_back(i); }
            }
            (void)grew;
            int cost = cone.size() + 1;
            if (cost < 2) continue;
            // v'nin torunları (döngü olmasın)
            vector<char> desc(n, 0); desc[vi] = 1;
            for (int i = vi + 1; i < n; i++) for (ll v : {prog[i].a, prog[i].b}) { auto it = pos.find(v); if (it != pos.end() && desc[it->second]) { desc[i] = 1; break; } }
            vector<ll> A(P.start.begin(), P.start.end());
            for (int i = 0; i < n; i++) if (!inC[i] && !desc[i]) A.push_back(prog[i].r);
            sort(A.begin(), A.end()); A.erase(unique(A.begin(), A.end()), A.end());
            if (A.size() > 400) continue;
            vector<Ins> rep;
            if (!synth(prog[vi].r, A, min(cost - 1, MAXD), rep)) continue;
            if ((int)rep.size() >= cost) continue;
            // yeni program
            vector<pair<double,Ins>> items;
            for (int i = 0; i < n; i++) if (!inC[i]) items.push_back({(double)i, prog[i]});
            for (int k = 0; k < (int)rep.size(); k++) items.push_back({vi - 0.5 + 0.01 * k, rep[k]});
            vector<Ins> np;
            if (!topo(items, P.start, np)) continue;
            np = clean(np, P.start, P.targets);
            if (np.size() >= prog.size() || !fits(np, P.start)) continue;
            gained += prog.size() - np.size(); prog = np; any = true; break;
        }
    }
    P.prog = prog; return gained;
}


// İki düğüm (u, v) için ortak yeni ara değer h: h = A op A, u = f(A_u ∪ {h}), v = g(A_v ∪ {h}).
// Maliyet 3 talimat; eski maliyet cost_u + cost_v.
struct NodeInfo { int idx; int cost; vector<char> inC; unordered_set<ll> As; vector<ll> A; unordered_map<ll, Ins> H; };
static void invAll(ll t0, ll a, vector<pair<ll,Ins>>& out) {
    LL v;
    v = (LL)t0 - a; if (v > 0) out.push_back({(ll)v, {'+', (ll)v, a, t0}});
    v = (LL)t0 + a; if (v <= LIMIT) out.push_back({(ll)v, {'-', (ll)v, a, t0}});
    v = (LL)a - t0; if (v > 0) out.push_back({(ll)v, {'-', a, (ll)v, t0}});
    if (t0 % a == 0) out.push_back({t0 / a, {'*', t0 / a, a, t0}});
    v = (LL)t0 * a; if (v <= LIMIT) out.push_back({(ll)v, {'/', (ll)v, a, t0}});
    if (a % t0 == 0) out.push_back({a / t0, {'/', a, a / t0, t0}});
}
int pairshare(Puzzle& P, mt19937& rng) {
    LIMIT = P.limit;
    vector<Ins> prog = clean(P.prog, P.start, P.targets);
    int gained = (int)P.prog.size() - (int)prog.size();
    unordered_set<ll> targS(P.targets.begin(), P.targets.end());
    bool any = true;
    while (any) {
        any = false;
        int n = prog.size();
        unordered_map<ll,int> pos; for (int i = 0; i < n; i++) pos[prog[i].r] = i;
        vector<vector<int>> cons(n);
        for (int i = 0; i < n; i++) for (ll v : {prog[i].a, prog[i].b}) { auto it = pos.find(v); if (it != pos.end() && (cons[it->second].empty() || cons[it->second].back() != i)) cons[it->second].push_back(i); }
        vector<NodeInfo> N(n);
        for (int vi = 0; vi < n; vi++) {
            NodeInfo& X = N[vi]; X.idx = vi; X.inC.assign(n, 0); X.inC[vi] = 1; int c = 1;
            for (int i = vi - 1; i >= 0; i--) {
                if (targS.count(prog[i].r)) continue;
                bool allIn = !cons[i].empty();
                for (int cc : cons[i]) if (!X.inC[cc]) { allIn = false; break; }
                if (allIn) { X.inC[i] = 1; c++; }
            }
            X.cost = c;
            vector<char> desc(n, 0); desc[vi] = 1;
            for (int i = vi + 1; i < n; i++) for (ll v : {prog[i].a, prog[i].b}) { auto it = pos.find(v); if (it != pos.end() && desc[it->second]) { desc[i] = 1; break; } }
            X.A.assign(P.start.begin(), P.start.end());
            for (int i = 0; i < n; i++) if (!X.inC[i] && !desc[i]) X.A.push_back(prog[i].r);
            sort(X.A.begin(), X.A.end()); X.A.erase(unique(X.A.begin(), X.A.end()), X.A.end());
            X.As = unordered_set<ll>(X.A.begin(), X.A.end());
            ll t = prog[vi].r;
            vector<pair<ll,Ins>> cand;
            for (ll a : X.A) invAll(t, a, cand);
            if (t % 2 == 0) cand.push_back({t / 2, {'+', t / 2, t / 2, t}});
            { ll r = (ll)sqrtl((long double)t); for (ll q = max(1LL, r - 1); q <= r + 1; q++) if ((LL)q * q == t) cand.push_back({q, {'*', q, q, t}}); }
            for (auto& [h, ins] : cand) if (!X.As.count(h) && !X.H.count(h)) X.H[h] = ins;
        }
        vector<int> order(n); iota(order.begin(), order.end(), 0); shuffle(order.begin(), order.end(), rng);
        for (int ui : order) {
            for (int vi = 0; vi < n && !any; vi++) {
                if (vi == ui) continue;
                NodeInfo &U = N[ui], &V = N[vi];
                if (U.cost + V.cost < 4) continue;
                if (U.inC[vi] || V.inC[ui]) continue;
                const NodeInfo &S = U.H.size() < V.H.size() ? U : V, &L = U.H.size() < V.H.size() ? V : U;
                for (auto& [h, insS] : S.H) {
                    auto it = L.H.find(h); if (it == L.H.end()) continue;
                    // h = a op b, a,b ∈ A_u ∩ A_v
                    Ins hi; bool ok = false;
                    vector<pair<ll,Ins>> c2;
                    for (ll a : U.A) { if (!V.As.count(a)) continue; c2.clear(); invAll(h, a, c2);
                        for (auto& [b, ins] : c2) if (U.As.count(b) && V.As.count(b)) { hi = ins; ok = true; break; }
                        if (ok) break; }
                    if (!ok) continue;
                    vector<pair<double,Ins>> items;
                    for (int i = 0; i < n; i++) if (!U.inC[i] && !V.inC[i]) items.push_back({(double)i, prog[i]});
                    items.push_back({min(ui, vi) - 0.6, hi});
                    items.push_back({ui - 0.4, U.H.at(h)});
                    items.push_back({vi - 0.4, V.H.at(h)});
                    vector<Ins> np;
                    if (!topo(items, P.start, np)) continue;
                    np = clean(np, P.start, P.targets);
                    if (np.size() >= prog.size() || !fits(np, P.start)) continue;
                    gained += prog.size() - np.size(); prog = np; any = true; break;
                }
            }
            if (any) break;
        }
    }
    P.prog = prog; return gained;
}

int main(int argc, char** argv) {
    ios::sync_with_stdio(false);
    ifstream in(argv[1]); ofstream out(argv[2]);
    int seed = argc > 3 ? atoi(argv[3]) : 1; if (argc > 4) MAXD = atoi(argv[4]); if (argc > 5) MODE = atoi(argv[5]);
    vector<Puzzle> Ps; string id;
    while (in >> id) {
        Puzzle P; P.id = id; int k, nt, n; in >> P.limit >> k >> nt >> n;
        P.start.resize(k); for (auto& x : P.start) in >> x;
        P.targets.resize(nt); for (auto& x : P.targets) in >> x;
        P.prog.resize(n); for (auto& i : P.prog) { string op; in >> op >> i.a >> i.b >> i.r; i.op = op[0]; }
        Ps.push_back(P);
    }
    long total = 0;
    #pragma omp parallel for schedule(dynamic) reduction(+:total)
    for (int i = 0; i < (int)Ps.size(); i++) {
        mt19937 rng(seed * 1000003 + i);
        int g = 0; int prev; do { prev = g; if (MODE != 2) g += improve(Ps[i], rng); if (MODE != 1) g += pairshare(Ps[i], rng); } while (MODE == 3 && g > prev); total += g;
    }
    for (auto& P : Ps) {
        out << P.id << " " << P.prog.size() << "\n";
        for (auto& i : P.prog) out << i.op << " " << i.a << " " << i.b << " " << i.r << "\n";
    }
    fprintf(stderr, "total gain %ld\n", total);
}
