"""
EXPERIMENTO 9: a ACE SPEC separa versões de um deck? Qual jeito de agrupar as listas prevê melhor?

Parte 1 (descrição): para os decks mais jogados, desempenho de cada ACE SPEC (taxa de vitória com faixa de
confiança e teste de diferença contra o resto do deck) e quanto os grupos por semelhança (k-medoides, modelo
anterior) coincidem com a ACE SPEC.
Parte 2 (confrontos): para os 2 decks mais jogados, taxa de cada ACE SPEC contra os principais adversários.
Parte 3 (previsão): torneios mais antigos treinam, os mais novos testam. Para cada deck, cada modelo atribui um
grupo à lista de teste e prevê a taxa de vitória pelo grupo (puxada para a taxa do deck com peso de 20 jogos).
Mede o log-loss nos jogos reais dos jogadores de teste (menor = previsão melhor).
  M0 deck inteiro | M1 k-medoides (anterior) | M2 só ACE SPEC | M3 ACE SPEC + pequenas aglutinadas na mais parecida
  M4 M3 + sub-versões por semelhança dentro da ACE | M5 M3 + junta ACE SPECs com o resto da lista quase igual
Uso:  python testes/experimentos/e9_ace_spec.py <pasta do programa com dados>
"""
import math
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, sys.argv[1])
from tracker import analises, banco, decks, variantes  # noqa: E402

random.seed(11)
ids = analises.torneios_da_fonte("todos")
marcas = ",".join("?" * len(ids))
datas = {t["id"]: t["data"] or "" for t in banco.listar_torneios()}
rows = banco.consultar(
    f"SELECT j.torneio, j.labs_id, j.arquetipo AS arq, j.ace_spec AS ace, j.v, j.d, j.e, "
    f"COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd FROM t_listas l JOIN t_jogadores j "
    f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo != '' AND j.ace_spec IS NOT NULL AND l.torneio IN ({marcas})",
    tuple(ids))
listas = {}
for r in rows:
    L = listas.setdefault((r["torneio"], r["labs_id"]), {"arq": r["arq"], "ace": r["ace"] or "(sem ACE SPEC)", "t": r["torneio"],
                                                          "v": r["v"] or 0, "n": (r["v"] or 0) + (r["d"] or 0) + (r["e"] or 0), "cartas": Counter()})
    L["cartas"][r["carta"]] += r["qtd"]
por_arq = defaultdict(list)
for L in listas.values():
    por_arq[L["arq"]].append(L)
principais = [a for a, ls in sorted(por_arq.items(), key=lambda x: -len(x[1])) if len(ls) >= 80][:8]


def placar(v, n):
    p = analises.placar(v, n - v)
    return p["taxa"], p["ic_baixo"], p["ic_alto"]


def z_teste(v1, n1, v2, n2):
    """Valor-p bilateral da diferença entre duas proporções."""
    if not n1 or not n2:
        return 1.0
    p = (v1 + v2) / (n1 + n2)
    ep = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) or 1e-9
    z = (v1 / n1 - v2 / n2) / ep
    return math.erfc(abs(z) / math.sqrt(2))


# ------------------------------------------------------------ parte 1
print("PARTE 1 — desempenho por ACE SPEC (listas com resultado)\n")
for arq in principais:
    ls = por_arq[arq]
    vt, nt = sum(L["v"] for L in ls), sum(L["n"] for L in ls)
    print(f"{decks.nome_deck(arq)}: {len(ls)} listas, deck {placar(vt, nt)[0]}%")
    for ace, q in Counter(L["ace"] for L in ls).most_common():
        g = [L for L in ls if L["ace"] == ace]
        v, n = sum(L["v"] for L in g), sum(L["n"] for L in g)
        if len(g) < 5:
            continue
        taxa, lo, hi = placar(v, n)
        pv = z_teste(v, n, vt - v, nt - n)
        print(f"   {ace:22} {len(g):4} listas ({100 * len(g) / len(ls):4.1f}%) | {taxa}% ({lo}–{hi}) em {n} jogos | "
              f"diferença do resto: p={pv:.3f}{' ← significativa' if pv < 0.05 else ''}")
    kv = variantes.variantes_por_semelhanca(arq, ids)
    if kv["grupos"]:
        print(f"   k-medoides (modelo anterior) achou {len(kv['grupos'])} grupos: tamanhos {[g['listas'] for g in kv['grupos']]}")

# ------------------------------------------------------------ parte 2
print("\nPARTE 2 — ACE SPEC contra os principais adversários (mesas com 30+ jogos)\n")
jog = banco.consultar(f"SELECT torneio, nome_norm, arquetipo, ace_spec FROM t_jogadores WHERE torneio IN ({marcas})", tuple(ids))
info = {(j["torneio"], j["nome_norm"]): j for j in jog}
mesas = banco.consultar(f"SELECT torneio, j1, j2, res1 FROM t_partidas WHERE torneio IN ({marcas}) AND res1 IN ('W','L','T')", tuple(ids))
for arq in principais[:2]:
    tab = defaultdict(lambda: [0, 0])
    for m in mesas:
        for eu, adv, venci in ((m["j1"], m["j2"], m["res1"] == "W"), (m["j2"], m["j1"], m["res1"] == "L")):
            a, b = info.get((m["torneio"], eu)), info.get((m["torneio"], adv))
            if a and b and a["arquetipo"] == arq and a["ace_spec"] and b["arquetipo"] and b["arquetipo"] != arq:
                tab[(a["ace_spec"], b["arquetipo"])][0] += venci
                tab[(a["ace_spec"], b["arquetipo"])][1] += 1
    advs = [d for d, _ in Counter(k[1] for k, x in tab.items() for _ in range(x[1])).most_common(5)]
    aces = [a for a, _ in Counter(k[0] for k, x in tab.items() for _ in range(x[1])).most_common(4)]
    print(f"{decks.nome_deck(arq)}:" + "".join(f" | {decks.nome_deck(d)[:16]:>16}" for d in advs))
    for a in aces:
        print(f"   {a[:20]:20}" + "".join(f" | {(f'{100 * tab[(a, d)][0] / tab[(a, d)][1]:5.1f}% ({tab[(a, d)][1]})' if tab[(a, d)][1] >= 30 else '–'):>16}" for d in advs))

# ------------------------------------------------------------ parte 3
print("\nPARTE 3 — previsão nos torneios mais novos (log-loss por jogo; menor é melhor)\n")
ordem = sorted({L["t"] for L in listas.values()}, key=lambda t: (datas.get(t, ""), t))  # sempre a mesma divisão
treino_t = set(ordem[:int(0.7 * len(ordem))])
K = 20  # peso da taxa do deck (jogos imaginários) ao estimar a taxa de cada grupo


def dist(a, b):
    comum = sum(min(q, b.get(c, 0)) for c, q in a.items())
    return 1 - comum / max(sum(a.values()) + sum(b.values()) - comum, 1)


def sem(cartas, carta):
    return {c: q for c, q in cartas.items() if c != carta}


def medoide(ls):
    amostra = ls if len(ls) <= 120 else random.sample(ls, 120)
    return min(amostra, key=lambda m: sum(dist(m["cartas"], o["cartas"]) for o in amostra))["cartas"]


def modelo_ace(tr, aglutinar, juntar=False, subdividir=False):
    """Devolve (função que dá o grupo de uma lista, descrição dos grupos)."""
    minimo = max(8, 0.08 * len(tr))
    grupos = defaultdict(list)
    for L in tr:
        grupos[L["ace"]].append(L)
    grandes = {a: g for a, g in grupos.items() if len(g) >= minimo} or {max(grupos, key=lambda a: len(grupos[a])): tr}
    med = {a: medoide(g) for a, g in grandes.items()}
    destino = {a: a for a in grandes}
    for a, g in grupos.items():
        if a not in grandes:  # ACE SPEC rara: vai para a versão com o resto da lista mais parecido (ou "outras")
            destino[a] = min(med, key=lambda b: sum(dist(sem(L["cartas"], a), sem(med[b], b)) for L in g) / len(g)) if aglutinar else "outras"
    if juntar:  # duas ACE SPEC com o resto da lista quase igual viram uma versão só
        for a in list(med):
            for b in list(med):
                if a < b and destino[a] == a and destino[b] == b and dist(sem(med[a], a), sem(med[b], b)) < 0.12:
                    for x, d in list(destino.items()):
                        if d == b:
                            destino[x] = a
    subgrupos = {}
    if subdividir:
        for a in set(destino.values()):
            g = [L for L in tr if destino.get(L["ace"], "outras") == a]
            if len(g) >= 2 * minimo:
                amostra = g if len(g) <= 150 else random.sample(g, 150)
                D = [[dist(x["cartas"], y["cartas"]) for y in amostra] for x in amostra]
                rng = random.Random(1)
                gs, ms = variantes._kmedoides(D, 2, rng)
                if min(Counter(gs).values()) >= minimo and variantes._silhueta(D, gs, 2) >= 0.25:
                    subgrupos[a] = [amostra[m]["cartas"] for m in ms]

    def grupo(L):
        a = destino.get(L["ace"], "outras")
        if a in subgrupos:
            return (a, min(range(2), key=lambda i: dist(L["cartas"], subgrupos[a][i])))
        return a
    return grupo


def modelo_significativo(tr, limite=0.05):
    """M6: cada ACE SPEC fica separada só se a taxa dela for diferente do resto do deck com p < limite no treino;
    as outras são aglutinadas numa versão "padrão"."""
    vt, nt = sum(L["v"] for L in tr), sum(L["n"] for L in tr)
    separadas = set()
    for a in {L["ace"] for L in tr}:
        g = [L for L in tr if L["ace"] == a]
        v, n = sum(L["v"] for L in g), sum(L["n"] for L in g)
        if z_teste(v, n, vt - v, nt - n) < limite:
            separadas.add(a)
    return lambda L: L["ace"] if L["ace"] in separadas else "padrão"


def modelo_kmedoides(tr):
    amostra = tr if len(tr) <= 200 else random.sample(tr, 200)
    D = [[dist(x["cartas"], y["cartas"]) for y in amostra] for x in amostra]
    rng = random.Random(1)
    minimo = max(8, 0.08 * len(amostra))
    melhor = None
    for k in (2, 3, 4):
        gs, ms = min((variantes._kmedoides(D, k, rng) for _ in range(5)), key=lambda gm: sum(D[i][gm[1][gm[0][i]]] for i in range(len(D))))
        if min(Counter(gs).values()) >= minimo:
            s = variantes._silhueta(D, gs, k)
            if not melhor or s > melhor[0]:
                melhor = (s, [amostra[m]["cartas"] for m in ms])
    if not melhor or melhor[0] < 0.25:
        return lambda L: 0
    meds = melhor[1]
    return lambda L: min(range(len(meds)), key=lambda i: dist(L["cartas"], meds[i]))


def avaliar(grupo, tr, te):
    vt, nt = sum(L["v"] for L in tr), sum(L["n"] for L in tr)
    base = vt / nt if nt else 0.5
    soma = defaultdict(lambda: [0, 0])
    for L in tr:
        g = grupo(L)
        soma[g][0] += L["v"]
        soma[g][1] += L["n"]
    perda = jogos = 0
    for L in te:
        v, n = soma.get(grupo(L), (0, 0))
        p = min(max((v + K * base) / (n + K), 0.02), 0.98)
        perda -= L["v"] * math.log(p) + (L["n"] - L["v"]) * math.log(1 - p)
        jogos += L["n"]
    return perda, jogos


modelos = {"M0 deck inteiro": lambda tr: (lambda L: 0), "M1 k-medoides": modelo_kmedoides,
           "M2 só ACE": lambda tr: modelo_ace(tr, aglutinar=False), "M3 ACE+aglutina": lambda tr: modelo_ace(tr, aglutinar=True),
           "M4 M3+sub-versões": lambda tr: modelo_ace(tr, aglutinar=True, subdividir=True),
           "M5 M3+junta iguais": lambda tr: modelo_ace(tr, aglutinar=True, juntar=True),
           "M6 ACE se signif.": modelo_significativo}
totais = {m: [0.0, 0] for m in modelos}
print(f"{'deck':22}" + "".join(f" | {m:>17}" for m in modelos))
for arq in [a for a, ls in sorted(por_arq.items(), key=lambda x: -len(x[1])) if len(ls) >= 60]:
    tr = [L for L in por_arq[arq] if L["t"] in treino_t and L["n"]]
    te = [L for L in por_arq[arq] if L["t"] not in treino_t and L["n"]]
    if len(tr) < 40 or len(te) < 15:
        continue
    linha = f"{decks.nome_deck(arq)[:22]:22}"
    for m, f in modelos.items():
        perda, jogos = avaliar(f(tr), tr, te)
        totais[m][0] += perda
        totais[m][1] += jogos
        linha += f" | {perda / jogos:17.4f}"
    print(linha)
print(f"{'TODOS (média por jogo)':22}" + "".join(f" | {totais[m][0] / totais[m][1]:17.4f}" for m in modelos))
print(f"\nGanho sobre M0 (deck inteiro), em milésimos de log-loss por jogo:" +
      "".join(f"\n   {m}: {1000 * (totais['M0 deck inteiro'][0] / totais['M0 deck inteiro'][1] - totais[m][0] / totais[m][1]):+.2f}" for m in modelos))
