"""
EXPERIMENTO 2: identificar o deck pelas cartas reveladas.

Compara o método atual (decks.identificar: ícone do deck + "assinatura" de cartas) com um
classificador Naive Bayes (probabilidade de cada carta aparecer nas listas de cada deck).

Dados: listas reais de torneios importados, com o deck já classificado pelo Limitless.
Torneios mais antigos treinam; os mais novos testam (nada do teste é usado no treino).
Para cada lista de teste, sorteamos k cartas como se fossem as reveladas numa partida.
Uso:  python testes/experimentos/e2_identificar_deck.py <pasta do programa com dados>
"""
import math
import random
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, sys.argv[1])
from tracker import banco, cartas, decks  # noqa: E402
from tracker.leitor import normalizar_nome_carta  # noqa: E402

random.seed(7)
rows = banco.consultar(
    "SELECT t.data, j.arquetipo AS arq, l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta "
    "FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id "
    "JOIN torneios t ON t.id=l.torneio WHERE j.arquetipo != ''")
listas = defaultdict(lambda: {"arq": "", "data": "", "cartas": set(), "nomes": {}})
for r in rows:
    L = listas[(r["torneio"], r["labs_id"])]
    L["arq"], L["data"] = r["arq"], r["data"] or ""
    n = normalizar_nome_carta(r["carta"])
    if not cartas.eh_energia_basica(r["carta"]):
        L["cartas"].add(n)
        L["nomes"][n] = r["carta"]
torneios = sorted({k[0] for k in listas}, key=lambda t: min(L["data"] for k, L in listas.items() if k[0] == t))
corte = int(len(torneios) * 0.7)
treino_t, teste_t = set(torneios[:corte]), set(torneios[corte:])
treino = [L for k, L in listas.items() if k[0] in treino_t]
teste = [L for k, L in listas.items() if k[0] in teste_t and L["cartas"]]
print(f"{len(listas)} listas de {len(torneios)} torneios; treino {len(treino)} listas ({len(treino_t)} torneios), teste {len(teste)}")

# ---- perfis do treino (usados pelos dois métodos)
por_arq = defaultdict(list)
for L in treino:
    por_arq[L["arq"]].append(L["cartas"])
perfil = {a: {c: q / len(ls) for c, q in Counter(c for s in ls for c in s).items()} for a, ls in por_arq.items()}
comum_em = Counter(c for p in perfil.values() for c, f in p.items() if f >= 0.3)
decks._cache["ass"] = (time.time() + 10 ** 9, (perfil, comum_em, len(perfil)))  # método atual só enxerga o treino
priori = {a: len(ls) / len(treino) for a, ls in por_arq.items()}
n_listas = {a: len(ls) for a, ls in por_arq.items()}
contagem = {a: Counter(c for s in ls for c in s) for a, ls in por_arq.items()}


def naive_bayes(reveladas, alfa=0.5):
    """Devolve (deck, confiança 0-1). Só as cartas vistas contam: não ver uma carta não prova que ela não está no deck."""
    notas = {}
    for a in por_arq:
        n = n_listas[a]
        notas[a] = math.log(priori[a]) + sum(math.log((contagem[a].get(c, 0) + alfa) / (n + 2 * alfa)) for c in reveladas)
    melhor = max(notas, key=notas.get)
    m = notas[melhor]
    soma = sum(math.exp(v - m) for v in notas.values())
    return melhor, 1 / soma


def atual(reveladas_nomes):
    return decks.identificar({nome: 1 for nome in reveladas_nomes})


print(f"\n{'cartas vistas':>13} | {'atual':>7} | {'Naive Bayes':>11} | {'NB com confiança ≥ 90%':>24} | tempo médio (atual / NB)")
for k in (2, 3, 5, 8, 12):
    ok_a = ok_nb = conf_n = conf_ok = 0
    t_a = t_nb = 0.0
    amostra = random.sample(teste, min(len(teste), 1500))
    for L in amostra:
        vistas = random.sample(sorted(L["cartas"]), min(k, len(L["cartas"])))
        t0 = time.perf_counter(); ra = atual([L["nomes"][c] for c in vistas]); t_a += time.perf_counter() - t0
        t0 = time.perf_counter(); rn, conf = naive_bayes(vistas); t_nb += time.perf_counter() - t0
        ok_a += ra == L["arq"]
        ok_nb += rn == L["arq"]
        if conf >= 0.9:
            conf_n += 1
            conf_ok += rn == L["arq"]
    n = len(amostra)
    print(f"{k:>13} | {100 * ok_a / n:6.1f}% | {100 * ok_nb / n:10.1f}% | {100 * conf_ok / max(conf_n, 1):6.1f}% de acerto em {100 * conf_n / n:5.1f}% dos casos"
          f" | {1000 * t_a / n:.2f} / {1000 * t_nb / n:.2f} ms")

# ---- combinação: Naive Bayes quando ele está confiante; senão, o método atual
print(f"\n{'cartas vistas':>13} | " + " | ".join(f"NB se conf ≥ {c:.1f}" for c in (0.0, 0.3, 0.5, 0.7)))
for k in (2, 3, 5, 8):
    amostra = random.sample(teste, min(len(teste), 1500))
    acertos = {c: 0 for c in (0.0, 0.3, 0.5, 0.7)}
    for L in amostra:
        vistas = random.sample(sorted(L["cartas"]), min(k, len(L["cartas"])))
        rn, conf = naive_bayes(vistas)
        ra = None
        for c in acertos:
            if conf >= c:
                acertos[c] += rn == L["arq"]
            else:
                ra = ra if ra is not None else atual([L["nomes"][x] for x in vistas])
                acertos[c] += ra == L["arq"]
    print(f"{k:>13} | " + " | ".join(f"{100 * acertos[c] / len(amostra):14.1f}%" for c in acertos))

# ---- NB2: suavização pela frequência geral da carta e só decks com pelo menos 3 listas
geral = Counter(c for L in treino for c in L["cartas"])


def naive_bayes2(reveladas, beta=2.0, minimo=3):
    notas = {}
    for a in por_arq:
        n = n_listas[a]
        if n < minimo:
            continue
        notas[a] = math.log(priori[a]) + sum(
            math.log((contagem[a].get(c, 0) + beta * (geral.get(c, 0) + 1) / (len(treino) + 2)) / (n + beta)) for c in reveladas)
    melhor = max(notas, key=notas.get)
    m = notas[melhor]
    return melhor, 1 / sum(math.exp(v - m) for v in notas.values())


print(f"\n{'cartas vistas':>13} | {'atual':>7} | {'NB':>6} | {'NB2':>6}")
for k in (2, 3, 5, 8, 12):
    amostra = random.sample(teste, min(len(teste), 1500))
    a = b = c = 0
    for L in amostra:
        vistas = random.sample(sorted(L["cartas"]), min(k, len(L["cartas"])))
        a += atual([L["nomes"][x] for x in vistas]) == L["arq"]
        b += naive_bayes(vistas)[0] == L["arq"]
        c += naive_bayes2(vistas)[0] == L["arq"]
    n = len(amostra)
    print(f"{k:>13} | {100 * a / n:6.1f}% | {100 * b / n:5.1f}% | {100 * c / n:5.1f}%")
