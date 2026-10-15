# -*- coding: utf-8 -*-
"""Motorul de algebră booleană: parser, simplificare cu legi, tabele, forme canonice, cod MATLAB."""
import re
import itertools


class EroareSintaxa(Exception):
    pass


# ======================= AST =======================
# ('var',n) ('const',0/1) ('not',x) ('and',(..)) ('or',(..)) ('xor',(a,b))
def mk(op, args):
    flat = []
    for a in args:
        flat.extend(a[1]) if a[0] == op else flat.append(a)
    if not flat:
        return ('const', 1 if op == 'and' else 0)
    return flat[0] if len(flat) == 1 else (op, tuple(flat))


def kids(e):
    t = e[0]
    return [e[1]] if t == 'not' else list(e[1]) if t in ('and', 'or', 'xor') else []


def rebuild(e, ch):
    t = e[0]
    if t == 'not':
        return ('not', ch[0])
    if t in ('and', 'or'):
        return mk(t, ch)
    if t == 'xor':
        return ('xor', tuple(ch))
    return e


def neg(x):
    return x[1] if x[0] == 'not' else ('not', x)


def variables(e):
    return {e[1]} if e[0] == 'var' else set().union(*[variables(c) for c in kids(e)]) if kids(e) else set()


def nlit(e):
    return 1 if e[0] == 'var' else sum(nlit(c) for c in kids(e))


# ======================= Parser =======================
TOK = re.compile(
    r"(?P<word>(?<![A-Z])(?:ȘI|ŞI|SAU|NU|AND|OR|NOT|XOR)(?![A-Z]))"
    r"|(?P<var>[A-Z])|(?P<const>[01])|(?P<op>[()×*·∙&+|∨∪!~¬'’^⊕])")
WORDS = {'ȘI': 'AND', 'ŞI': 'AND', 'SAU': 'OR', 'NU': 'NOT', 'AND': 'AND', 'OR': 'OR', 'NOT': 'NOT', 'XOR': 'XOR'}
OPS = {**{c: 'AND' for c in '×*·∙&'}, **{c: 'OR' for c in '+|∨∪'}, **{c: 'NOT' for c in '!~¬'},
       "'": 'POST', '’': 'POST', '^': 'XOR', '⊕': 'XOR', '(': '(', ')': ')'}


def tokenize(s):
    s = re.sub(r"([A-Za-z])[\u0305\u0304\u0332]", r"\1'", s).upper()  # A̅ -> A'
    out, i = [], 0
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        m = TOK.match(s, i)
        if not m:
            raise EroareSintaxa(f"Caracter necunoscut: '{s[i]}' la poziția {i + 1}.")
        k, t = m.lastgroup, m.group(m.lastgroup)
        out.append((WORDS[t], t) if k == 'word' else ('VAR', t) if k == 'var'
                   else ('CONST', int(t)) if k == 'const' else (OPS[t], t))
        i = m.end()
    return out


class Parser:
    def __init__(s, toks):
        s.t, s.i = toks, 0

    def peek(s):
        return s.t[s.i][0] if s.i < len(s.t) else None

    def take(s):
        s.i += 1
        return s.t[s.i - 1]

    def parse(s):
        if not s.t:
            raise EroareSintaxa("Expresia este goală.")
        e = s.or_()
        if s.i < len(s.t):
            raise EroareSintaxa(f"Simbol neașteptat: '{s.t[s.i][1]}'.")
        return e

    def or_(s):
        a = [s.xor()]
        while s.peek() == 'OR':
            s.take()
            a.append(s.xor())
        return mk('or', a)

    def xor(s):
        e = s.and_()
        while s.peek() == 'XOR':
            s.take()
            e = ('xor', (e, s.and_()))
        return e

    def and_(s):
        a = [s.un()]
        while True:
            p = s.peek()
            if p == 'AND':
                s.take()
                a.append(s.un())
            elif p in ('VAR', 'CONST', '(', 'NOT'):  # înmulțire implicită: AB, A(B+C)
                a.append(s.un())
            else:
                break
        return mk('and', a)

    def un(s):
        if s.peek() == 'NOT':
            s.take()
            return ('not', s.un())
        e = s.prim()
        while s.peek() == 'POST':
            s.take()
            e = ('not', e)
        return e

    def prim(s):
        p = s.peek()
        if p == 'VAR':
            return ('var', s.take()[1])
        if p == 'CONST':
            return ('const', s.take()[1])
        if p == '(':
            s.take()
            e = s.or_()
            if s.peek() != ')':
                raise EroareSintaxa("Lipsește o paranteză ')'.")
            s.take()
            return e
        raise EroareSintaxa("Expresie incompletă sau simbol neașteptat.")


def parse_functie(text):
    """'F = A×B + A' -> ('F', ast)"""
    text, nume = text.strip(), 'F'
    if '=' in text:
        st, text = text.split('=', 1)
        st = re.sub(r"\(.*\)", "", st).strip().upper()
        if st:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", st):
                raise EroareSintaxa("Numele funcției (stânga lui '=') nu este valid.")
            nume = st
    e = Parser(tokenize(text)).parse()
    vs = variables(e)
    if len(vs) > 8:
        raise EroareSintaxa("Sunt permise cel mult 8 variabile.")
    if nume in vs:
        nume = next(n for n in "FYZWDQ" if n not in vs)
    return nume, e


# ======================= Afișare =======================
def sstr(e, par=0):
    t = e[0]
    if t == 'var':
        return e[1]
    if t == 'const':
        return str(e[1])
    if t == 'not':
        return sstr(e[1], 9) + "'"
    pr = {'or': 1, 'xor': 2, 'and': 3}[t]
    s = {'or': ' + ', 'xor': ' ⊕ ', 'and': '·'}[t].join(sstr(a, pr) for a in e[1])
    return '(' + s + ')' if pr <= par else s


def ltx(e, par=0):
    t = e[0]
    if t in ('var', 'const'):
        return str(e[1])
    if t == 'not':
        return r'\overline{' + ltx(e[1]) + '}'
    pr = {'or': 1, 'xor': 2, 'and': 3}[t]
    s = {'or': ' + ', 'xor': r' \oplus ', 'and': r' \cdot '}[t].join(ltx(a, pr) for a in e[1])
    return '(' + s + ')' if pr <= par else s


# ======================= Evaluare =======================
def ev(e, env):
    t = e[0]
    if t == 'var':
        return env[e[1]]
    if t == 'const':
        return e[1]
    if t == 'not':
        return 1 - ev(e[1], env)
    v = [ev(a, env) for a in e[1]]
    return int(all(v)) if t == 'and' else int(any(v)) if t == 'or' else sum(v) % 2


def rows(vs):
    return list(itertools.product((0, 1), repeat=len(vs)))


def tabel(e, vs):
    return [ev(e, dict(zip(vs, r))) for r in rows(vs)]


def echivalent(a, b):
    vs = sorted(variables(a) | variables(b))
    return tabel(a, vs) == tabel(b, vs)


def tabel_cols(e, vs, nume, interm=True):
    R, subs = rows(vs), []

    def col(x):
        for c in kids(x):
            col(c)
        if x[0] not in ('var', 'const') and x not in subs and x != e:
            subs.append(x)
    col(e)
    data = {v: [r[k] for r in R] for k, v in enumerate(vs)}
    if interm:
        for s in subs:
            data[sstr(s)] = [ev(s, dict(zip(vs, r))) for r in R]
    data[nume] = [ev(e, dict(zip(vs, r))) for r in R]
    return data


def pas_eval(e, env):
    """Substituție + evaluare pas cu pas (de jos în sus)."""
    def sub(x):
        return ('const', env[x[1]]) if x[0] == 'var' else rebuild(x, [sub(c) for c in kids(x)]) if kids(x) else x

    def ready(x):
        k = kids(x)
        if all(c[0] == 'const' for c in k):
            return ('const', ev(x, {}))
        return rebuild(x, [c if c[0] == 'const' else ready(c) for c in k])
    cur = sub(e)
    out = [cur]
    while cur[0] != 'const':
        cur = ready(cur)
        out.append(cur)
    return out


def forme_canonice(e, vs):
    t, n = tabel(e, vs), len(vs)
    mi = [i for i, v in enumerate(t) if v]
    Ma = [i for i, v in enumerate(t) if not v]
    bits = lambda i: [(i >> (n - 1 - k)) & 1 for k in range(n)]
    ov = lambda v: r"\overline{%s}" % v
    mt = lambda i: r"\,".join(v if b else ov(v) for v, b in zip(vs, bits(i)))
    mx = lambda i: "(" + " + ".join(ov(v) if b else v for v, b in zip(vs, bits(i))) + ")"
    return mi, Ma, ("0" if not mi else " + ".join(mt(i) for i in mi)), \
        ("1" if not Ma else r" \cdot ".join(mx(i) for i in Ma))


# ======================= Legi (nume, formulă LaTeX) =======================
LEGI = {
    'dn': ("Dubla negație", r"\overline{\overline{A}}=A"),
    'dm_and': ("Legile lui DeMorgan", r"\overline{A\cdot B}=\overline{A}+\overline{B}"),
    'dm_or': ("Legile lui DeMorgan", r"\overline{A+B}=\overline{A}\cdot\overline{B}"),
    'xor': ("Definiția SAU-EXCLUSIV (XOR)", r"A\oplus B=\overline{A}\cdot B+A\cdot\overline{B}"),
    'nc': ("Negația constantelor", r"\overline{0}=1;\ \overline{1}=0"),
    'int_or': ("Intersecție", r"A+1=1"), 'int_and': ("Intersecție", r"A\cdot 0=0"),
    'reu_or': ("Reuniune", r"A+0=A"), 'reu_and': ("Reuniune", r"A\cdot 1=A"),
    'comp_or': ("Complementaritate", r"A+\overline{A}=1"),
    'comp_and': ("Complementaritate", r"A\cdot\overline{A}=0"),
    'idem_or': ("Idempotență", r"A+A=A"), 'idem_and': ("Idempotență", r"A\cdot A=A"),
    'abs_or': ("Absorbție", r"A+A\cdot B=A"), 'abs_and': ("Absorbție", r"A\cdot(A+B)=A"),
    'abs2_or': ("Absorbție", r"A+\overline{A}\cdot B=A+B"),
    'abs2_and': ("Absorbție", r"A\cdot(\overline{A}+B)=A\cdot B"),
    'dist_exp': ("Distributivitate", r"A\cdot(B+C)=A\cdot B+A\cdot C"),
    'fact': ("Distributivitate (factor comun)", r"A\cdot B+A\cdot C=A\cdot(B+C)"),
    'adj': ("Distributivitate (factor comun)", r"P\cdot X+P\cdot\overline{X}=P\cdot(X+\overline{X})"),
    'com': ("Comutativitate (ordonare)", r"A+B=B+A;\ A\cdot B=B\cdot A"),
    'qm': ("Minimizare Quine–McCluskey (termeni adiacenți / consens)", r"P\cdot X+P\cdot\overline{X}=P"),
}


# ======================= Reguli de rescriere =======================
def r_not(e):
    if e[0] != 'not':
        return None
    x = e[1]
    if x[0] == 'not':
        return x[1], 'dn'
    if x[0] == 'const':
        return ('const', 1 - x[1]), 'nc'
    if x[0] in ('and', 'or'):
        return mk('or' if x[0] == 'and' else 'and', [('not', a) for a in x[1]]), 'dm_' + x[0]


def r_xor(e):
    if e[0] == 'xor':
        a, b = e[1]
        return mk('or', [mk('and', [neg(a), b]), mk('and', [a, neg(b)])]), 'xor'


def r_const(e):
    t = e[0]
    if t not in ('and', 'or'):
        return None
    z = 0 if t == 'or' else 1
    if ('const', 1 - z) in e[1]:
        return ('const', 1 - z), 'int_' + t
    if ('const', z) in e[1]:
        return mk(t, [x for x in e[1] if x != ('const', z)]), 'reu_' + t


def r_comp(e):
    if e[0] in ('and', 'or'):
        s = set(e[1])
        if any(neg(a) in s for a in e[1]):
            return ('const', 1 if e[0] == 'or' else 0), 'comp_' + e[0]


def r_idem(e):
    if e[0] in ('and', 'or'):
        seen = []
        for a in e[1]:
            if a not in seen:
                seen.append(a)
        if len(seen) < len(e[1]):
            return mk(e[0], seen), 'idem_' + e[0]


def fset(x, op):
    return set(x[1]) if x[0] == op else {x}


def r_abs(e):
    t = e[0]
    if t not in ('and', 'or'):
        return None
    d = 'and' if t == 'or' else 'or'
    for i, x in enumerate(e[1]):
        for j, y in enumerate(e[1]):
            if i != j and fset(x, d) < fset(y, d):
                return mk(t, [z for k, z in enumerate(e[1]) if k != j]), 'abs_' + t


def r_abs2(e):
    t = e[0]
    if t not in ('and', 'or'):
        return None
    d = 'and' if t == 'or' else 'or'
    for i, x in enumerate(e[1]):
        for j, y in enumerate(e[1]):
            if i != j and y[0] == d and neg(x) in y[1]:
                new = mk(d, [z for z in y[1] if z != neg(x)])
                return mk(t, [new if k == j else z for k, z in enumerate(e[1])]), 'abs2_' + t


def r_adj(e):
    if e[0] != 'or':
        return None
    a = e[1]
    fs = [list(x[1]) if x[0] == 'and' else [x] for x in a]
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            fi, fj = fs[i], fs[j]
            di, dj = [x for x in fi if x not in fj], [x for x in fj if x not in fi]
            if len(fi) == len(fj) and len(di) == 1 and len(dj) == 1 and neg(di[0]) == dj[0]:
                com = [x for x in fi if x in fj]
                new = mk('and', com + [mk('or', [di[0], dj[0]])])
                return mk('or', [new if k == i else z for k, z in enumerate(a) if k != j]), 'adj'


def r_expand(e):
    if e[0] != 'and':
        return None
    for i, g in enumerate(e[1]):
        if g[0] == 'or':
            rest = [z for k, z in enumerate(e[1]) if k != i]
            return mk('or', [mk('and', rest + [t]) for t in g[1]]), 'dist_exp'


def r_fact(e):
    if e[0] != 'or':
        return None
    a = e[1]
    fs = [list(x[1]) if x[0] == 'and' else [x] for x in a]
    for f in [f for l in fs for f in l]:
        g = [k for k, l in enumerate(fs) if f in l and len(l) > 1]
        if len(g) >= 2:
            parts = [mk('and', [z for z in fs[k] if z != f]) for k in g]
            new = mk('and', [mk('or', parts), f])
            out = [new if k == g[0] else x for k, x in enumerate(a) if k not in g[1:]]
            return mk('or', out), 'fact'


T1 = [r_not, r_xor, r_const, r_comp, r_idem, r_abs, r_abs2]


def apply_first(e, rules):
    for i, c in enumerate(kids(e)):
        r = apply_first(c, rules)
        if r:
            ch = kids(e)
            ch[i] = r[0]
            return rebuild(e, ch), r[1]
    for f in rules:
        r = f(e)
        if r:
            return r
    return None


def _loop(e, steps, tiers, maxn=70):
    seen = {e}
    while len(steps) < maxn:
        for tier in tiers:
            r = apply_first(e, tier)
            if r:
                break
        else:
            return e
        if r[0] in seen:
            return e
        seen.add(r[0])
        steps.append((r[1], r[0]))
        e = r[0]
    return e


def _run(e0, expand):
    steps = []
    tiers = [T1, [r_adj]] + ([[r_expand]] if expand else [])
    e = _loop(e0, steps, tiers)
    for _ in range(10):
        r = apply_first(e, [r_fact])
        if not r or nlit(r[0]) >= nlit(e):
            break
        steps.append((r[1], r[0]))
        e = _loop(r[0], steps, [T1, [r_adj]])
    return steps, e


# ---- Quine–McCluskey (plasă de siguranță pentru forma minimă) ----
def qm_expr(e, vs):
    n, t = len(vs), tabel(e, vs)
    mint = [i for i, v in enumerate(t) if v]
    if not mint:
        return ('const', 0)
    if len(mint) == 2 ** n:
        return ('const', 1)
    grup, primi = {(m, 0) for m in mint}, set()
    while grup:
        gl, noi, fol = list(grup), set(), set()
        for i in range(len(gl)):
            for j in range(i + 1, len(gl)):
                (a, ma), (b, mb) = gl[i], gl[j]
                d = a ^ b
                if ma == mb and d and d & (d - 1) == 0:
                    noi.add((a & ~d, ma | d))
                    fol |= {gl[i], gl[j]}
        primi |= grup - fol
        grup = noi
    cov = lambda p: {x for x in mint if x & ~p[1] == p[0]}
    alesi, ram = [], set(mint)
    for x in mint:
        ps = [p for p in primi if x in cov(p)]
        if len(ps) == 1 and ps[0] not in alesi:
            alesi.append(ps[0])
    for p in alesi:
        ram -= cov(p)
    while ram:
        p = max(sorted(primi), key=lambda p: (len(cov(p) & ram), bin(p[1]).count('1')))
        alesi.append(p)
        ram -= cov(p)
    terms = []
    for v, m in sorted(alesi):
        lits = [('var', vs[k]) if (v >> (n - 1 - k)) & 1 else ('not', ('var', vs[k]))
                for k in range(n) if not (m >> (n - 1 - k)) & 1]
        terms.append(mk('and', lits))
    return mk('or', terms)


def ordonare(e):
    ch = [ordonare(c) for c in kids(e)]
    if e[0] in ('and', 'or'):
        ch = sorted(ch, key=lambda x: (sstr(x).replace("'", ""), sstr(x)))
    return rebuild(e, ch)


def simplifica(e):
    """Returnează (pași, rezultat); pași = [(cheie_lege, expresie_după_pas)]."""
    vs = sorted(variables(e))
    pas, fin = min([_run(e, False), _run(e, True)], key=lambda c: (nlit(c[1]), len(c[0])))
    q = qm_expr(e, vs)
    if not echivalent(e, fin):
        pas, fin = [], e
    if nlit(q) < nlit(fin):
        pas, fin = pas + [('qm', q)], q
    o = ordonare(fin)
    if o != fin:
        pas, fin = pas + [('com', o)], o
    return pas, fin


# ======================= Cod MATLAB =======================
def mstr(e):
    t = e[0]
    if t in ('var', 'const'):
        return str(e[1])
    if t == 'not':
        return '~' + (mstr(e[1]) if e[1][0] in ('var', 'const') else '(' + mstr(e[1]) + ')')
    if t == 'xor':
        return 'xor(' + ', '.join(mstr(a) for a in e[1]) + ')'
    w = lambda c: '(' + mstr(c) + ')' if c[0] in ('and', 'or') else mstr(c)
    return (' & ' if t == 'and' else ' | ').join(w(a) for a in e[1])


def cod_matlab(nume, e, vs):
    R = rows(vs)
    L = [f"% {nume} = {sstr(e)}", "% Algebră booleană - verificare în MATLAB", "clear; clc;", "",
         "% Vectorii de intrare (toate combinațiile, ca la Constant din Simulink)"]
    L += [f"{v} = [{' '.join(str(r[k]) for r in R)}];" for k, v in enumerate(vs)]
    L += ["", "% Funcția logică (& = ȘI, | = SAU, ~ = NU, xor = SAU-EXCLUSIV)"]
    L.append(f"{nume} = {e[1]}*ones(1,{len(R)});" if e[0] == 'const' else f"{nume} = double({mstr(e)});")
    L += ["", "% Tabela de adevăr",
          "T = table(" + ", ".join(f"{v}'" for v in vs + [nume]) + ", 'VariableNames', {" +
          ", ".join(f"'{v}'" for v in vs + [nume]) + "});", "disp(T);"]
    return "\n".join(L)


def cod_simulink(nume, e, vs):
    R, op = rows(vs), {'and': 'AND', 'or': 'OR', 'not': 'NOT', 'xor': 'XOR'}
    M = f"Model_{nume}"
    L = [f"% Construiește automat în Simulink schema pentru {nume} = {sstr(e)}",
         f"model = '{M}';", "if bdIsLoaded(model), close_system(model,0); end",
         "new_system(model); open_system(model);", ""]
    vy = {v: 40 + 70 * k for k, v in enumerate(vs)}
    for v in vs:
        val = '[' + ' '.join(str(r[vs.index(v)]) for r in R) + ']'
        L.append(f"add_block('simulink/Sources/Constant',[model '/{v}'],'Value','{val}','Position',[30 {vy[v]} 130 {vy[v] + 30}]);")
    ctr, used, lines = itertools.count(1), {}, []

    def emit(x):
        t = x[0]
        if t == 'var':
            return x[1], 0, vy[x[1]]
        if t == 'const':
            n, y = f"K{next(ctr)}", 40 + 70 * (len(vs) + next(ctr))
            L.append(f"add_block('simulink/Sources/Constant',[model '/{n}'],'Value','{x[1]}','Position',[30 {y} 130 {y + 30}]);")
            return n, 0, y
        ch = [emit(a) for a in kids(x)]
        lvl, y = 1 + max(c[1] for c in ch), sum(c[2] for c in ch) / len(ch)
        while any(abs(y - u) < 50 for u in used.setdefault(lvl, [])):
            y += 55
        used[lvl].append(y)
        n, xx, hh = f"{op[t]}{next(ctr)}", 120 + 130 * lvl, max(40, 18 * len(ch))
        inp = f"'Inputs','{len(ch)}'," if t != 'not' else ""
        L.append(f"add_block('simulink/Logic and Bit Operations/Logical Operator',[model '/{n}'],"
                 f"'Operator','{op[t]}',{inp}'IconShape','distinctive','Position',[{xx} {int(y - hh / 2)} {xx + 50} {int(y + hh / 2)}]);")
        for i, c in enumerate(ch):
            lines.append(f"add_line(model,'{c[0]}/1','{n}/{i + 1}','autorouting','on');")
        return n, lvl, y
    r = emit(e)
    L.append(f"add_block('simulink/Sinks/Display',[model '/{nume}'],'Position',[{120 + 130 * (r[1] + 1)} {int(r[2]) - 20} "
             f"{120 + 130 * (r[1] + 1) + 120} {int(r[2]) + max(20, 9 * len(R))}]);")
    L += lines + [f"add_line(model,'{r[0]}/1','{nume}/1','autorouting','on');", "",
                  "set_param(model,'StopTime','0');", "sim(model);   % valorile apar în blocul Display"]
    return "\n".join(L)
