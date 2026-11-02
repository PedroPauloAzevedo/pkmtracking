"""
VARIANTES DE UM DECK: agrupa as listas de um mesmo deck por semelhança e compara o desempenho.

- Distância entre duas listas: 1 - (cartas em comum, contando cópias) / (cartas das duas juntas)
  (Jaccard ponderado; 0 = listas iguais, 1 = nada em comum).
- Grupos: k-medoides (cada grupo é representado por uma lista real, a "mais central"), com k de 1 a 4.
- Quantos grupos: o k com maior "silhueta" (mede se cada lista está mais perto do próprio grupo do que
  dos outros). Abaixo de 0,25 não há variantes de verdade e o deck aparece como um grupo só.
Testado em testes/experimentos/e5_variantes.py com listas reais: grupos nítidos nos decks mais jogados,
e em N's Zoroark uma variante com taxa de vitória claramente menor (faixas de confiança separadas).
"""
import random
from collections import Counter, defaultdict

from . import banco

MAX_LISTAS = 300        # acima disso, sorteia 300 listas (a conta cresce com o quadrado do número de listas)
SILHUETA_MINIMA = 0.25  # abaixo disso, não mostra variantes
FRACAO_MINIMA = 0.08    # cada variante precisa ter pelo menos 8% das listas (e 8 listas): uma lista esquisita não é variante
TENTATIVAS = 5          # o k-medoides depende do sorteio inicial: roda algumas vezes e fica com o melhor


def _distancia(a, b, tam_a, tam_b):
    comum = sum(min(q, b.get(c, 0)) for c, q in a.items())
    return 1 - comum / max(tam_a + tam_b - comum, 1)


def _kmedoides(D, k, rng, voltas=30):
    n = len(D)
    med = rng.sample(range(n), k)
    for _ in range(voltas):
        grupos = [min(range(k), key=lambda g: D[i][med[g]]) for i in range(n)]
        novos = []
        for g in range(k):
            membros = [i for i in range(n) if grupos[i] == g] or [med[g]]
            novos.append(min(membros, key=lambda m: sum(D[m][i] for i in membros)))
        if novos == med:
            break
        med = novos
    return [min(range(k), key=lambda g: D[i][med[g]]) for i in range(n)], med


def _silhueta(D, grupos, k):
    n = len(D)
    membros = [[j for j in range(n) if grupos[j] == g] for g in range(k)]
    total = 0.0
    for i in range(n):
        proprio = [D[i][j] for j in membros[grupos[i]] if j != i]
        a = sum(proprio) / len(proprio) if proprio else 0.0
        b = min((sum(D[i][j] for j in membros[g]) / len(membros[g]) for g in range(k) if g != grupos[i] and membros[g]), default=0.0)
        total += (b - a) / max(a, b) if max(a, b) else 0.0
    return total / n


def variantes_por_semelhanca(arq, torneios):
    """Modelo anterior (só semelhança de listas, sem olhar a ACE SPEC). Mantido para comparação no experimento 9."""
    from .analises import placar
    if not torneios:
        return {"grupos": [], "listas": 0, "silhueta": None}
    marcas = ",".join("?" * len(torneios))
    rows = banco.consultar(
        f"SELECT l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd, j.v, j.d, j.e "
        f"FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id "
        f"WHERE j.arquetipo=? AND l.torneio IN ({marcas})", (arq, *torneios))
    listas = defaultdict(lambda: {"cartas": Counter(), "vde": (0, 0, 0)})
    for r in rows:
        L = listas[(r["torneio"], r["labs_id"])]
        L["cartas"][r["carta"]] += r["qtd"]
        L["vde"] = (r["v"] or 0, r["d"] or 0, r["e"] or 0)
    ls = sorted(listas.values(), key=lambda L: sorted(L["cartas"].items()))
    rng = random.Random(42)  # mesmo resultado a cada abertura da tela
    if len(ls) > MAX_LISTAS:
        ls = rng.sample(ls, MAX_LISTAS)
    if len(ls) < 12:
        return {"grupos": [], "listas": len(ls), "silhueta": None}
    tam = [sum(L["cartas"].values()) for L in ls]
    D = [[_distancia(a["cartas"], b["cartas"], tam[i], tam[j]) for j, b in enumerate(ls)] for i, a in enumerate(ls)]
    minimo = max(8, FRACAO_MINIMA * len(ls))
    candidatos = []
    for k in (2, 3, 4):
        # melhor de várias tentativas: a de menor soma de distâncias até o centro do grupo
        g, med = min((_kmedoides(D, k, rng) for _ in range(TENTATIVAS)),
                     key=lambda gm: sum(D[i][gm[1][gm[0][i]]] for i in range(len(D))))
        if min(Counter(g).values()) >= minimo and len(set(g)) == k:
            candidatos.append((_silhueta(D, g, k), k, g))
    sil, k, grupos = max(candidatos, key=lambda x: x[0]) if candidatos else (0.0, 1, [])
    if sil < SILHUETA_MINIMA:
        return {"grupos": [], "listas": len(ls), "silhueta": round(sil, 2)}
    media_geral = {c: sum(L["cartas"].get(c, 0) for L in ls) / len(ls) for c in {c for L in ls for c in L["cartas"]}}
    saida = []
    for g in range(k):
        membros = [ls[i] for i in range(len(ls)) if grupos[i] == g]
        v, d, e = (sum(L["vde"][x] for L in membros) for x in range(3))
        media = {c: sum(L["cartas"].get(c, 0) for L in membros) / len(membros) for c in media_geral}
        dif = sorted(media, key=lambda c: -abs(media[c] - media_geral[c]))[:5]
        saida.append({"listas": len(membros), **placar(v, d, e),
                      "marcas": [{"carta": c, "media": round(media[c], 1), "geral": round(media_geral[c], 1)} for c in dif]})
    saida.sort(key=lambda x: -x["listas"])
    return {"grupos": saida, "listas": len(ls), "silhueta": round(sil, 2)}



# ------------------------------------------------------------------ versões pela ACE SPEC (modelo atual)
#
# Cada deck só pode ter 1 ACE SPEC, e a escolha dela costuma definir a versão do deck. O modelo:
#   1. separa as listas pela ACE SPEC (gravada em t_jogadores.ace_spec na importação);
#   2. aglutina as ACE SPEC raras (menos de 8% das listas, ou de 8 listas) na versão com o resto da lista mais parecido;
#   3. junta duas versões quando, tirando a ACE SPEC, as listas típicas são quase iguais (distância < 0,12);
#   4. marca a versão cuja taxa de vitória difere do resto do deck com p < 0,05 ("diferença provável").
# Comparado no experimento 9 (testes/experimentos/e9_ace_spec.py) com o modelo anterior e outras 5 alternativas:
# nenhuma divisão prevê o resultado de uma lista nova melhor que o deck inteiro (diferenças de 1 milésimo);
# entre as que usam a ACE SPEC, esta foi a de melhor previsão, e é a que mostra as diferenças reais
# (ex.: Dragapult com Hero's Cape vence 44% contra 57% com Unfair Stamp).

DISTANCIA_JUNTAR = 0.12
MIN_JOGOS_DIFERENCA = 30  # com menos jogos que isso, nem marca "diferença provável" (o teste fica frágil)
SEM_ACE = "(sem ACE SPEC)"


def _sem_carta(cartas, carta):
    return {c: q for c, q in cartas.items() if c != carta}


def _medoide(ls, rng):
    amostra = ls if len(ls) <= 120 else rng.sample(ls, 120)
    tam = [sum(L["cartas"].values()) for L in amostra]
    return min(range(len(amostra)), key=lambda i: sum(_distancia(amostra[i]["cartas"], o["cartas"], tam[i], tam[j])
                                                   for j, o in enumerate(amostra)))


def _valor_p(v1, n1, v2, n2):
    """Teste de diferença entre duas proporções (bilateral)."""
    import math
    if not n1 or not n2:
        return None
    p = (v1 + v2) / (n1 + n2)
    ep = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return math.erfc(abs((v1 / n1 - v2 / n2) / ep) / math.sqrt(2)) if ep else None


def variantes(arq, torneios):
    """Versões de um deck pela ACE SPEC: {"aces": tabela de cada ACE SPEC, "grupos": versões, "listas": n}."""
    from .analises import placar
    if not torneios:
        return {"aces": [], "grupos": [], "listas": 0}
    marcas = ",".join("?" * len(torneios))
    rows = banco.consultar(
        f"SELECT l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd, j.v, j.d, j.e, j.ace_spec "
        f"FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id "
        f"WHERE j.arquetipo=? AND j.ace_spec IS NOT NULL AND l.torneio IN ({marcas})", (arq, *torneios))
    listas = defaultdict(lambda: {"cartas": Counter(), "vde": (0, 0, 0), "ace": SEM_ACE})
    for r in rows:
        L = listas[(r["torneio"], r["labs_id"])]
        L["cartas"][r["carta"]] += r["qtd"]
        L["vde"] = (r["v"] or 0, r["d"] or 0, r["e"] or 0)
        L["ace"] = r["ace_spec"] or SEM_ACE
    ls = sorted(listas.values(), key=lambda L: sorted(L["cartas"].items()))
    if not ls:
        return {"aces": [], "grupos": [], "listas": 0}
    total = [sum(L["vde"][i] for L in ls) for i in range(3)]

    def resumo(grupo):
        v, d, e = (sum(L["vde"][i] for L in grupo) for i in range(3))
        pv = _valor_p(v, v + d + e, total[0] - v, sum(total) - (v + d + e))
        return {"listas": len(grupo), "pct": round(100 * len(grupo) / len(ls), 1), **placar(v, d, e),
                "p_valor": round(pv, 3) if pv is not None else None,
                "diferenca": pv is not None and pv < 0.05 and v + d + e >= MIN_JOGOS_DIFERENCA}

    por_ace = defaultdict(list)
    for L in ls:
        por_ace[L["ace"]].append(L)
    tabela = sorted(({"ace": a, **resumo(g)} for a, g in por_ace.items()), key=lambda x: -x["listas"])
    if len(ls) < 12:
        return {"aces": tabela, "grupos": [], "listas": len(ls)}

    rng = random.Random(42)  # mesmo resultado a cada abertura da tela
    minimo = max(8, FRACAO_MINIMA * len(ls))
    grandes = {a: g for a, g in por_ace.items() if len(g) >= minimo} or {tabela[0]["ace"]: por_ace[tabela[0]["ace"]]}
    med = {}
    for a, g in grandes.items():
        amostra = g if len(g) <= 120 else rng.sample(g, 120)
        med[a] = amostra[_medoide(amostra, rng)]["cartas"]
    destino = {a: a for a in grandes}
    for a, g in por_ace.items():  # 2. ACE SPEC rara: vai para a versão mais parecida (sem contar a própria ACE SPEC)
        if a not in grandes:
            def media_dist(b):
                mb = _sem_carta(med[b], b)
                return sum(_distancia(_sem_carta(L["cartas"], a), mb, sum(L["cartas"].values()), sum(mb.values())) for L in g) / len(g)
            destino[a] = min(med, key=media_dist)
    for a in sorted(med):  # 3. versões com o resto da lista quase igual viram uma só
        for b in sorted(med):
            if a < b and destino[a] == a and destino[b] == b:
                ma, mb = _sem_carta(med[a], a), _sem_carta(med[b], b)
                if _distancia(ma, mb, sum(ma.values()), sum(mb.values())) < DISTANCIA_JUNTAR:
                    for x, d in list(destino.items()):
                        if d == b:
                            destino[x] = a
    versoes = defaultdict(list)
    for L in ls:
        versoes[destino[L["ace"]]].append(L)
    nomes_ace = set(por_ace)
    media_geral = {c: sum(L["cartas"].get(c, 0) for L in ls) / len(ls) for c in {c for L in ls for c in L["cartas"]}}
    grupos = []
    for chave, g in versoes.items():
        media = {c: sum(L["cartas"].get(c, 0) for L in g) / len(g) for c in media_geral if c not in nomes_ace}
        dif = sorted(media, key=lambda c: -abs(media[c] - media_geral[c]))[:5]
        grupos.append({**resumo(g), "aces": [{"ace": a, "listas": q} for a, q in Counter(L["ace"] for L in g).most_common()],
                       "marcas": [{"carta": c, "media": round(media[c], 1), "geral": round(media_geral[c], 1)} for c in dif]})
    grupos.sort(key=lambda x: -x["listas"])
    return {"aces": tabela, "grupos": grupos if len(grupos) > 1 else [], "listas": len(ls)}
