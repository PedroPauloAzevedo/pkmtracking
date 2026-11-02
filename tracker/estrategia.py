"""
ESTRATÉGIA: qual deck levar para o torneio, a partir dos confrontos dos campeonatos importados.

1. Força de cada deck (modelo de Bradley-Terry): uma nota por deck tal que a chance de A vencer B
   é forçaA / (forçaA + forçaB). Usa TODAS as partidas, então funciona até para pares com poucos jogos.
2. Confronto ajustado (empirical Bayes): p = (vitórias + k * previsão_da_força) / (jogos + k).
   Com muitos jogos vale o resultado real do confronto; com poucos, a previsão pela força geral.
   (Testado em testes/experimentos/e3_matchups.py: prevê melhor que a taxa bruta.)
3. Taxa esperada contra o campo: média dos confrontos ajustados, pesada pela presença de cada deck.
4. Equilíbrio do meta (teoria dos jogos, jogo de soma zero): a mistura de decks que nenhum outro deck
   consegue explorar. Calculado por "fictitious play" (cada rodada, todo mundo responde à média
   das escolhas anteriores), que converge para o equilíbrio nesse tipo de jogo.
"""
import math
from collections import Counter, defaultdict

from . import banco

K_PADRAO = 24  # peso da previsão pela força, em "jogos imaginários": escolhido por validação no experimento 3


def _partidas(torneios, com_empates=False):
    if not torneios:
        return []
    marcas = ",".join("?" * len(torneios))
    resultados = "('W', 'L', 'T')" if com_empates else "('W', 'L')"
    return banco.consultar(f"SELECT arq1, arq2, res1 FROM t_partidas WHERE torneio IN ({marcas}) "
                           f"AND arq1 != '' AND arq2 != '' AND arq1 != arq2 AND res1 IN {resultados}", tuple(torneios))


def forcas(partidas, iteracoes=200, prior=2.0):
    """Bradley-Terry pelo algoritmo MM (Hunter, 2004), com um puxão leve para a média em decks raros."""
    vit = defaultdict(float)
    jogos = defaultdict(lambda: defaultdict(float))
    for p in partidas:
        a, b = p["arq1"], p["arq2"]
        vit[a if p["res1"] == "W" else b] += 1
        jogos[a][b] += 1
        jogos[b][a] += 1
    s = {d: 1.0 for d in jogos}
    for _ in range(iteracoes):
        novo = {}
        for d in s:
            den = sum(n / (s[d] + s[o]) for o, n in jogos[d].items()) + prior / (s[d] + 1.0)
            novo[d] = (vit[d] + prior / 2) / den
        media = math.exp(sum(math.log(v) for v in novo.values()) / len(novo)) if novo else 1.0
        s = {d: v / media for d, v in novo.items()}
    return s


def confrontos_ajustados(partidas, decks, k=K_PADRAO):
    """{(a, b): {"p": chance de a vencer b, "n": jogos reais}} para todos os pares de `decks`.

    Com empates nas partidas (res1 = 'T'), segue a conta do Limitless e da tabela de Matchups:
    vitórias / (vitórias + derrotas + empates); a previsão pela força é reduzida pela taxa geral de empates."""
    s = forcas([p for p in partidas if p["res1"] in ("W", "L")])
    empates = sum(1 for p in partidas if p["res1"] == "T") / len(partidas) if partidas else 0.0
    reais = defaultdict(lambda: [0, 0])
    for p in partidas:
        a, b, r = p["arq1"], p["arq2"], p["res1"]
        reais[(a, b)][0] += r == "W"
        reais[(a, b)][1] += 1
        reais[(b, a)][0] += r == "L"
        reais[(b, a)][1] += 1
    saida = {}
    for a in decks:
        for b in decks:
            if a == b:
                saida[(a, b)] = {"p": 0.5, "n": 0}
                continue
            sa, sb = s.get(a, 1.0), s.get(b, 1.0)
            v, n = reais.get((a, b), (0, 0))
            saida[(a, b)] = {"p": (v + k * (1 - empates) * sa / (sa + sb)) / (n + k), "n": n}
    return saida


def equilibrio(decks, p, iteracoes=20000):
    """Mistura de equilíbrio do jogo simétrico de soma zero com ganho p(a,b) - 0,5.
    Devolve ({deck: peso}, folga): folga = quanto o melhor contra-ataque ainda ganha (0 = equilíbrio exato)."""
    n = len(decks)
    if not n:
        return {}, 0.0
    m = [[p[(a, b)]["p"] - 0.5 for b in decks] for a in decks]
    contagem = [0] * n
    valor = [0.0] * n  # ganho acumulado de cada deck contra o histórico de escolhas
    i = 0
    for _ in range(iteracoes):
        contagem[i] += 1
        for a in range(n):
            valor[a] += m[a][i]
        i = max(range(n), key=valor.__getitem__)  # melhor resposta à média até aqui
    total = sum(contagem)
    mistura = [c / total for c in contagem]
    folga = max(sum(m[a][b] * mistura[b] for b in range(n)) for a in range(n))
    return {decks[a]: mistura[a] for a in range(n) if mistura[a] >= 0.005}, folga


def qual_deck(torneios, k_decks=12, k=K_PADRAO):
    """Para a tela "Qual deck jogar?": taxa esperada contra o campo, pior confronto e equilíbrio."""
    partidas = _partidas(torneios)
    if not partidas:
        return {"decks": [], "equilibrio": {}, "folga": None, "partidas": 0}
    presenca = Counter()
    for p in partidas:
        presenca[p["arq1"]] += 1
        presenca[p["arq2"]] += 1
    decks = [d for d, _ in presenca.most_common(k_decks)]
    total = sum(presenca[d] for d in decks)
    campo = {d: presenca[d] / total for d in decks}
    ajust = confrontos_ajustados(partidas, decks, k)
    mistura, folga = equilibrio(decks, ajust)
    linhas = []
    for a in decks:
        esperada = sum(campo[b] * ajust[(a, b)]["p"] for b in decks)
        pior = min((b for b in decks if b != a), key=lambda b: ajust[(a, b)]["p"], default=None)
        linhas.append({"arquetipo": a, "campo": round(100 * campo[a], 1), "esperada": round(100 * esperada, 1),
                       "contra_equilibrio": round(100 * sum(mistura.get(b, 0) * ajust[(a, b)]["p"] for b in decks), 1),
                       "pior": pior, "pior_p": round(100 * ajust[(a, pior)]["p"], 1) if pior else None,
                       "pior_n": ajust[(a, pior)]["n"] if pior else 0,
                       "equilibrio": round(100 * mistura.get(a, 0), 1)})
    linhas.sort(key=lambda x: -x["esperada"])
    return {"decks": linhas, "folga": round(100 * folga, 2), "partidas": len(partidas), "k": k}
