// Hcub tarzı küresel planlayıcı; çekirdek Tony Li'nin "Elf Calculator With Register Reuse" çözücüsünden uyarlandı (Apache 2.0).
// Değişiklikler: palet (2'nin kuvvetleri ve tek sabitler), yaprak sınırları ve genişlik komut satırından.
#include <string>
#include <sstream>
#include <stdexcept>
// Signed quotient/remainder search over expressions available in the current puzzle.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <unordered_map>
#include <vector>
using namespace std;
using Int = int64_t;
static vector<int> G_POW = {1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 24, 32, 40, 48};
static vector<Int> G_ODD = {3, 5, 7, 9, 11, 13, 15, 17, 19, 23, 31};
static int G_DONE = 52, G_LEAVES = 56;
static double G_RANK = 0.18;
static int G_K = 1, G_MODE = 0, G_LAZY = 0;
static double G_W = 2.0;
static vector<int> parse_list(const string& s){ vector<int> v; stringstream ss(s); string t; while(getline(ss,t,',')) if(!t.empty()) v.push_back(stoi(t)); return v; }

struct Expr {
    Int v;
    int a = -1, b = -1;
    char op = 0;
    int cost = 0, extra = 0;
};
Int apply(char op, Int a, Int b) {
    if (op == '+')
        return a + b;
    if (op == '-')
        return a - b;
    if (op == '/')
        return a / b;
    return a * b; // All callers check the puzzle limit before multiplying.
}

// Integer-key index reused between targets. Zero is outside the calculator domain.
struct Index {
    vector<Int> keys;
    vector<int> ids, used;
    size_t mask;
    Index(int bits) : keys(1u << bits), ids(keys.size()), mask(keys.size() - 1) {}
    size_t slot(Int v) const {
        uint64_t h = uint64_t(v) * 0x9e3779b97f4a7c15ULL;
        h ^= h >> 31;
        size_t i = h & mask;
        while (keys[i] && keys[i] != v)
            i = (i + 1) & mask;
        return i;
    }
    int get(Int v) const {
        size_t i = slot(v);
        return keys[i] ? ids[i] : -1;
    }
    bool insert(Int v, int id) {
        size_t i = slot(v);
        if (keys[i])
            return false;
        used.push_back(i);
        keys[i] = v;
        ids[i] = id;
        return true;
    }
    void clear() {
        for (int i : used)
            keys[i] = 0;
        used.clear();
    }
};

struct Dictionary {
    Int limit;
    Index index{24};
    vector<Expr> e;
    array<vector<pair<Int, int>>, 3> sorted;
    int n0 = 0, n1 = 0;
    explicit Dictionary(Int limit) : limit(limit) {}
    void add(Int v, int a, int b, char op, int cost, int extra = -1) {
        if (extra < 0)
            extra = a < 0 ? 0 : e[a].extra + (a == b ? 0 : e[b].extra);
        if (v > 0 && v <= limit && index.insert(v, e.size()))
            e.push_back({v, a, b, op, cost, extra});
    }
    void combine(int i, int j, int cost) {
        Int a = e[i].v, b = e[j].v;
        add(a + b, i, j, '+', cost);
        if (a != b)
            add(abs(a - b), a > b ? i : j, a > b ? j : i, '-', cost);
        if (a <= limit / b)
            add(a * b, i, j, '*', cost);
        if (a > b && a % b == 0)
            add(a / b, i, j, '/', cost);
        if (b > a && b % a == 0)
            add(b / a, j, i, '/', cost);
    }
    void build(const vector<Int> &leaves, const vector<int> &lc = {}) {
        index.clear();
        e.clear();
        for (auto &s : sorted)
            s.clear();
        for (size_t k = 0; k < leaves.size(); k++)
            add(leaves[k], -1, -1, 0, 0, lc.empty() ? 0 : lc[k]);
        n0 = e.size();
        for (int i = 0; i < n0; i++)
            for (int j = 0; j <= i; j++)
                combine(i, j, 1);
        n1 = e.size();
        for (int i = n0; i < n1; i++)
            for (int j = 0; j < n0; j++)
                combine(i, j, 2);
        for (int i = 0; i < int(e.size()); i++)
            sorted[e[i].cost].emplace_back(e[i].v, i);
        for (auto &s : sorted)
            sort(s.begin(), s.end());
    }
};
// A reduction encodes parent = (child * factor) +/- atom, or atom - child.
struct Link {
    int factor = -1, atom = -1;
    char op = '+';
};
struct State {
    Int v;
    int cost = 0, parent = -1;
    Link link;
    double rank = 0;
};

struct Search {
    Dictionary &d;
    int width, best = 1000, end = -1, terminal = -1;
    vector<State> history, next;
    unordered_map<Int, int> visited;
    Search(Dictionary &d, int width) : d(d), width(width) {}
    int expr_cost(int id) const { return id < 0 ? 0 : 1 + d.e[id].cost + d.e[id].extra; }
    void offer(int p, Int v, int f, int a, char op) {
        if (v <= 0 || v > d.limit)
            return;
        int cost = history[p].cost + expr_cost(f) + expr_cost(a);
        if (cost >= best)
            return;
        int t = d.index.get(v);
        if (t >= 0) {
            if (cost + d.e[t].cost + d.e[t].extra < best) {
                best = cost + d.e[t].cost + d.e[t].extra;
                end = history.size();
                terminal = t;
                history.push_back({v, cost, p, {f, a, op}});
            }
            return;
        }
        if (cost + 3 >= best || v >= history[p].v)
            return;
        // Comparisons happen across instruction costs and residual sizes.
        double rank = cost + G_RANK * log2(double(v));
        if (int(next.size()) == width && rank >= next.back().rank)
            return;
        auto prev = visited.find(v);
        if (prev != visited.end() && prev->second <= cost)
            return;
        for (auto it = next.begin(); it != next.end(); ++it)
            if (it->v == v) {
                if (it->cost <= cost)
                    return;
                next.erase(it);
                break;
            }
        State s{v, cost, p, {f, a, op}, rank};
        auto it = upper_bound(next.begin(), next.end(), rank,
                              [](double k, const State &x) { return k < x.rank; });
        next.insert(it, s);
        if (int(next.size()) > width)
            next.pop_back();
    }
    void expand(int p) {
        Int v = history[p].v;
        for (auto &arr : d.sorted) {
            auto it = lower_bound(arr.begin(), arr.end(), make_pair(v, -1));
            for (int k = -4; k < 4; k++) {
                auto pos = (it - arr.begin()) + k;
                if (pos < 0 || pos >= int(arr.size()))
                    continue;
                auto [a, id] = arr[pos];
                offer(p, abs(v - a), -1, id, v > a ? '+' : 'r');
            }
        }
        for (int i = 0; i < d.n1; i++) {
            Int a = d.e[i].v;
            if (a == 1)
                continue;
            Int diff = abs(v - a);
            if (diff) {
                if (d.index.get(diff) >= 0)
                    offer(p, diff, -1, i, v > a ? '+' : 'r');
                if (v > a && (diff & 15) == 0)
                    shifted(p, diff, i, '+');
                if (a > v && (diff & 15) == 0)
                    shifted(p, diff, i, 'r');
            }
            if (a + v <= d.limit) {
                if (d.index.get(a + v) >= 0)
                    offer(p, a + v, -1, i, '-');
                if (((a + v) & 15) == 0)
                    shifted(p, a + v, i, '-');
            }
            if (a >= v)
                continue;
            Int q = v / a, r = v % a;
            if (!r) {
                offer(p, q, i, -1, '+');
                continue;
            }
            int rid = d.index.get(r);
            if (rid >= 0)
                offer(p, q, i, rid, '+');
            if (a - r <= d.limit - v) {
                rid = d.index.get(a - r);
                if (rid >= 0)
                    offer(p, q + 1, i, rid, '-');
            }
            // Approximate the quotient by a cached expression, then synthesize the error.
            if (i < d.n0 && q > 64) {
                for (auto &arr : d.sorted) {
                    auto it = lower_bound(arr.begin(), arr.end(), make_pair(q, -1));
                    for (int k = -1; k <= 0; k++) {
                        auto pos = (it - arr.begin()) + k;
                        if (pos < 0 || pos >= int(arr.size()))
                            continue;
                        auto [b, bi] = arr[pos];
                        if (b > d.limit / a)
                            continue;
                        Int mul = a * b;
                        if (mul == v)
                            continue;
                        int id = d.index.get(mul);
                        if (id >= 0)
                            offer(p, abs(mul - v), -1, id, mul < v ? '+' : 'r');
                    }
                }
            }
        }
    }
    void shifted(int p, Int diff, int atom, char op) {
        int k = __builtin_ctzll(diff);
        while (k >= 4) {
            int f = d.index.get(Int(1) << k);
            if (f >= 0) {
                offer(p, diff >> k, f, atom, op);
                break;
            }
            k--;
        }
    }
    void run(Int target) {
        history.push_back({target, 0, -1, {}});
        int id = d.index.get(target);
        if (id >= 0) {
            end = 0;
            terminal = id;
            best = d.e[id].cost + d.e[id].extra;
            return;
        }
        vector<int> front{0};
        for (int depth = 0; depth < 20 && !front.empty(); depth++) {
            next.clear();
            for (int p : front)
                if (history[p].cost + 3 < best)
                    expand(p);
            front.clear();
            for (State s : next) {
                if (s.cost + 3 >= best)
                    continue;
                visited[s.v] = s.cost;
                front.push_back(history.size());
                history.push_back(s);
            }
        }
    }
};
struct Puzzle {
    Int limit;
    vector<Int> starts, targets, palette;
    map<Int, Expr> defs;
    vector<Int> order, torder;
    int width;
    Puzzle(Int limit, int width) : limit(limit), width(width) {}
    Int make(char op, Int a, Int b) {
        Int v = apply(op, a, b);
        if (v <= 0 || v > limit)
            throw runtime_error("invalid construction");
        if (!defs.count(v)) {
            defs[v] = {v, -1, -1, op};
            args[v] = {a, b};
            order.push_back(v);
        }
        return v;
    }
    map<Int, pair<Int, Int>> args;
    Int power(int k) {
        Int v = Int(1) << k;
        if (defs.count(v))
            return v;
        if (k == 1)
            return make('+', 1, 1);
        Int right = power(k - k / 2);
        Int left = power(k / 2);
        return make('*', left, right);
    }
    void setup() {
        for (Int v : starts)
            defs[v] = {v};
        if (!defs.count(1))
            make('/', starts[0], starts[0]);
        palette = {1};
        for (int k : G_POW) {
            if ((Int(1) << k) <= limit)
                palette.push_back(power(k));
        }
        for (Int i : G_ODD)
            if (i <= limit) {
                if (!defs.count(i)) {
                    // en ucuz: mevcut iki değerin toplamı/farkı, yoksa ikili açılım
                    bool ok = false;
                    for (auto& [a, ea] : defs) { if (a >= i) break; if (defs.count(i - a)) { make('+', a, i - a); ok = true; break; } }
                    if (!ok) for (auto& [a, ea] : defs) { if (a <= i) continue; if (defs.count(a - i)) { make('-', a, a - i); ok = true; break; } }
                    if (!ok) binary(i);
                }
                palette.push_back(i);
            }
    }
    Int materialize(Dictionary &d, int id) {
        const Expr &e = d.e[id];
        if (defs.count(e.v))
            return e.v;
        Int right = materialize(d, e.b);
        Int left = materialize(d, e.a);
        return make(e.op, left, right);
    }
    Int binary(Int v) {
        if (defs.count(v))
            return v;
        Int h = binary(v / 2);
        Int twice = make('+', h, h);
        return v % 2 ? make('+', twice, 1) : twice;
    }

    vector<Int> leaves_for(const set<Int> &done) const {
        vector<Int> leaves;
        set<Int> used;
        auto add = [&](Int v) {
            if (used.insert(v).second)
                leaves.push_back(v);
        };
        for (Int v : palette)
            add(v);
        for (Int v : starts)
            add(v);
        for (auto it = done.rbegin(); it != done.rend() && (int)leaves.size() < G_DONE; ++it)
            add(*it);
        for (auto it = order.rbegin(); it != order.rend() && (int)leaves.size() < G_LEAVES; ++it)
            add(*it);
        return leaves;
    }
    // Tembel palet: henüz hiçbir kurulmuş hedefin bağımlılığı olmayan değerler bedava değil.
    set<Int> paid_set() const {
        set<Int> paid(starts.begin(), starts.end());
        vector<Int> st(torder.begin(), torder.end());
        while (!st.empty()) {
            Int v = st.back();
            st.pop_back();
            if (!paid.insert(v).second)
                continue;
            auto it = args.find(v);
            if (it != args.end()) {
                st.push_back(it->second.first);
                st.push_back(it->second.second);
            }
        }
        return paid;
    }
    int cone_cost(Int v, const set<Int> &paid, set<Int> &seen) const {
        if (paid.count(v) || !seen.insert(v).second)
            return 0;
        auto it = args.find(v);
        if (it == args.end())
            return 0;
        return 1 + cone_cost(it->second.first, paid, seen) + cone_cost(it->second.second, paid, seen);
    }
    void build_dict(Dictionary &d, const set<Int> &done) const {
        vector<Int> leaves = leaves_for(done);
        if (!G_LAZY) {
            d.build(leaves);
            return;
        }
        set<Int> paid = paid_set();
        vector<int> lc;
        for (Int v : leaves) {
            set<Int> seen;
            lc.push_back(min(G_LAZY, cone_cost(v, paid, seen)));
        }
        d.build(leaves, lc);
    }
    int cost_of(Dictionary &d, Int t) const {
        if (defs.count(t))
            return 0;
        Search s(d, width);
        s.run(t);
        return s.end < 0 ? 999 : s.best;
    }
    void realize(Dictionary &d, Int target) {
        if (defs.count(target))
            return;
        Search s(d, width);
        s.run(target);
        if (s.end < 0)
            binary(target);
        else {
            Int v = materialize(d, s.terminal);
            for (int p = s.end; s.history[p].parent >= 0; p = s.history[p].parent) {
                Link l = s.history[p].link;
                if (l.factor >= 0)
                    v = make('*', v, materialize(d, l.factor));
                if (l.atom >= 0) {
                    Int a = materialize(d, l.atom);
                    v = l.op == 'r' ? make('-', a, v) : make(l.op, v, a);
                }
            }
            if (v != target)
                throw runtime_error("search reconstruction failed");
        }
    }
    // Hcub tarzı küresel açgözlü: her turda kalan tüm hedeflerin maliyeti hesaplanır;
    // en ucuz K aday için "bunu kurarsam kalanların toplam maliyeti ne olur" ileri bakışı yapılır.
    void solve(Dictionary &d, Dictionary &d2) {
        setup();
        set<Int> done;
        torder.clear();
        vector<Int> rem;
        for (Int t : targets)
            if (!defs.count(t))
                rem.push_back(t);
            else {
                done.insert(t);
                torder.push_back(t);
            }
        while (!rem.empty()) {
            build_dict(d, done);
            vector<pair<int, Int>> c;
            for (Int t : rem)
                c.push_back({cost_of(d, t), t});
            sort(c.begin(), c.end());
            map<Int, double> amort;
            if (G_MODE == 2) {
                // Hcub paylaşım: her hedefin planındaki yeni düğümler; birden çok planda geçen düğümün maliyeti bölüşülür
                map<Int, vector<Int>> nodes;
                map<Int, int> demand;
                for (auto &[ct, t] : c) {
                    Puzzle q = *this;
                    size_t before = q.order.size();
                    q.realize(d, t);
                    nodes[t].assign(q.order.begin() + before, q.order.end());
                    for (Int v : nodes[t])
                        demand[v]++;
                }
                for (auto &[ct, t] : c) {
                    double a = 0;
                    for (Int v : nodes[t])
                        a += 1.0 / demand[v];
                    amort[t] = a;
                }
                sort(c.begin(), c.end(), [&](auto &x, auto &y) {
                    return amort[x.second] != amort[y.second] ? amort[x.second] < amort[y.second] : x.first < y.first;
                });
            }
            Int pick = c[0].second;
            if (G_K > 1 && rem.size() > 2) {
                double bestf = 1e18;
                int K = min<int>(G_K, c.size());
                for (int k = 0; k < K; k++) {
                    Puzzle q = *this;
                    set<Int> qd = done;
                    q.realize(d, c[k].second);
                    qd.insert(c[k].second);
                    q.torder.push_back(c[k].second);
                    q.build_dict(d2, qd);
                    double f = G_MODE == 2 ? amort[c[k].second] : c[k].first;
                    for (auto &[ct, t] : c)
                        if (t != c[k].second) {
                            int nc = q.cost_of(d2, t);
                            f += G_MODE != 1 ? nc : -(ct - nc) * pow(G_W, -nc);
                        }
                    if (G_MODE == 1) f = c[k].first + f - c[k].first; // benefit-weighted
                    if (f < bestf) {
                        bestf = f;
                        pick = c[k].second;
                    }
                }
            }
            realize(d, pick);
            torder.push_back(pick);
            done.insert(pick);
            rem.erase(find(rem.begin(), rem.end(), pick));
            // önceden ara değer olarak kurulmuş hedefler
            for (size_t i = 0; i < rem.size();)
                if (defs.count(rem[i])) {
                    torder.push_back(rem[i]);
                    done.insert(rem[i]);
                    rem.erase(rem.begin() + i);
                } else
                    i++;
        }
    }
    vector<Int> plan_sequence() {
        set<Int> placed(starts.begin(), starts.end());
        vector<Int> sequence;
        auto visit = [&](auto &&self, Int v) -> void {
            if (!placed.insert(v).second) return;
            auto [a, b] = args.at(v);
            self(self, a); self(self, b);
            sequence.push_back(v);
        };
        for (Int t : torder) visit(visit, t);
        return sequence;
    }
    // Walk dependencies on demand, then allocate registers by their next use.
    // An evicted value can always be rebuilt from its expression or a protected seed.
    vector<array<int, 4>> compile() {
        set<Int> placed(starts.begin(), starts.end());
        vector<Int> sequence;
        auto visit = [&](auto &&self, Int v) -> void {
            if (!placed.insert(v).second)
                return;
            auto [a, b] = args.at(v);
            self(self, a);
            self(self, b);
            sequence.push_back(v);
        };
        for (Int t : targets)
            visit(visit, t);
        map<Int, vector<int>> uses;
        for (int i = int(sequence.size()) - 1; i >= 0; --i) {
            auto [a, b] = args.at(sequence[i]);
            uses[a].push_back(i);
            if (a != b)
                uses[b].push_back(i);
        }
        array<Int, 48> bank{};
        set<Int> seeds(starts.begin(), starts.end());
        copy(starts.begin(), starts.end(), bank.begin());
        vector<array<int, 4>> program;
        auto emit = [&](auto &&self, Int v, uint64_t locked) -> int {
            auto found = find(bank.begin(), bank.end(), v);
            if (found != bank.end())
                return found - bank.begin();
            auto [a, b] = args.at(v);
            int ra = self(self, a, locked), rb = self(self, b, locked | (1ULL << ra));
            int rd = -1, latest = -1;
            for (int k = 0; k < 48; k++) {
                Int old = bank[k];
                if ((locked >> k & 1) || seeds.count(old))
                    continue;
                int nextuse = uses[old].empty() ? 1000000 : uses[old].back();
                if (!old) {
                    rd = k;
                    break;
                }
                if (nextuse > latest) {
                    rd = k;
                    latest = nextuse;
                }
            }
            if (rd < 0)
                throw runtime_error("register allocation failed");
            bank[rd] = v;
            program.push_back({defs.at(v).op, ra, rb, rd});
            return rd;
        };
        for (Int v : sequence) {
            auto [a, b] = args.at(v);
            uses[a].pop_back();
            if (a != b)
                uses[b].pop_back();
            emit(emit, v, 0);
        }
        cerr << "PLAN " << sequence.size() << " PROG " << program.size() << "\n";
        return program;
    }
};

int main(int argc, char **argv) {
    int width = argc > 1 ? stoi(argv[1]) : 3;
    if (argc > 2) G_DONE = stoi(argv[2]);
    if (argc > 3) G_LEAVES = stoi(argv[3]);
    if (argc > 4) G_POW = parse_list(argv[4]);
    if (argc > 5) { auto o = parse_list(argv[5]); G_ODD.assign(o.begin(), o.end()); }
    if (argc > 6) G_RANK = stod(argv[6]);
    if (getenv("HLAZY")) G_LAZY = atoi(getenv("HLAZY"));
    if (getenv("HK")) G_K = atoi(getenv("HK"));
    if (getenv("HMODE")) G_MODE = atoi(getenv("HMODE"));
    if (getenv("HW")) G_W = atof(getenv("HW"));
    static Dictionary D1(0), D2(0);
    string id;
    Int limit;
    int ns, nt;
    while (cin >> id >> limit >> ns >> nt) {
        Puzzle p(limit, width);
        p.starts.resize(ns);
        p.targets.resize(nt);
        for (auto &x : p.starts)
            cin >> x;
        for (auto &x : p.targets)
            cin >> x;
        D1.limit = limit; D2.limit = limit;
        p.solve(D1, D2);
        if (argc > 7 && string(argv[7]) == "plan") {
            auto seq = p.plan_sequence();
            cout << id << " " << limit << " " << ns << " " << nt << " " << seq.size() << "\n";
            for (size_t k = 0; k < p.starts.size(); k++) cout << (k ? " " : "") << p.starts[k];
            cout << "\n";
            for (size_t k = 0; k < p.targets.size(); k++) cout << (k ? " " : "") << p.targets[k];
            cout << "\n";
            for (Int v : seq) { auto [a, b] = p.args.at(v); cout << char(p.defs.at(v).op) << " " << a << " " << b << " " << v << "\n"; }
            cout << flush;
            continue;
        }
        auto prog = p.compile();
        cout << id << " [";
        for (size_t k = 0; k < prog.size(); k++) {
            auto [op, a, b, c] = prog[k];
            if (k)
                cout << ',';
            cout << "[\"" << char(op) << "\"," << a << ',' << b << ',' << c << ']';
        }
        cout << "]\n" << flush;
    }
}