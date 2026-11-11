"""
EVOLUÇÃO DAS LISTAS E APROVEITAMENTO (métodos trazidos do painel Indigo Plateau; pedido do Pedro, 11/11/2026; D-053).

Quatro contas sobre os torneios importados, todas só com a biblioteca padrão:

1. aproveitamento_por_deck: pontos que os jogadores do deck fizeram no suíço (3 por vitória, 1 por empate) divididos pelos
   pontos possíveis (3 × rodadas suíças do torneio). Compara torneios de tamanhos diferentes e conta quem desistiu no meio
   (as rodadas que faltaram valem zero). Rodadas que contam: o suíço sem o top cut (achado de trás para a frente: 1, 2, 4, 8…
   mesas) e, nos grandes eventos, só o Dia 1 (que todos jogam; ver rodadas_suicas). Folgas (bye) não estão no banco: quem teve folga perde 3 pontos possíveis (subestima um pouco).
   Só entram jogadores com pelo menos uma partida achada (nomes que não casam entre a classificação e as rodadas ficam fora).

2. lista_base: cada lista pesa os pontos finais do jogador (3V + E): uma 10-3-1 (31) pesa quase o dobro de uma 5-4-0 (15); lista
   sem pontos não pesa. Por carta: % do peso das listas que a usam; núcleo ≥ 75%, opções de 10% a 75%; quantidade = a mais comum
   (pesada) entre as listas que usam. Impressões diferentes contam juntas (pelo nome). Precisa de 5 listas.

3. inovacoes: compara as listas do deck no período recente (últimos `dias_recentes` dias da seleção) com o período anterior
   (os `dias_anteriores` dias antes). Cada contagem de carta vira "pelo menos k cópias" e, para cartas que eram padrão (≥ 75% das
   listas antes), "menos de k" (um corte). Inovação quando: (1) ficou ≥ 25 pontos mais comum, com teste binomial p < 0,005
   (rigoroso: cada deck testa centenas de características); (2) as listas recentes com ela têm aproveitamento por partida
   (3V + E) / 3(V + D + E) maior que as sem ela (mudança que dá resultado, não só moda); (3) pelo menos 5 listas recentes a têm.
   Diferença do Indigo: lá o critério (2) é "chegou mais ao top 64", que aqui não dá para medir (só baixamos listas do topo).
   Mudanças que aparecem nas mesmas listas (Jaccard ≥ 0,6) formam um pacote; pacotes ordenados por a · ln(a / b) (a = fração
   agora, b = antes), alto quando é comum agora e era rara antes.

4. estabilidade: quantas cartas a lista média do deck mudou entre os dois períodos (metade da soma de |diferença de cópias|:
   trocar 1 carta por outra = 1), menos o que a variação natural entre jogadores explica (teste de permutação: listas dos dois
   períodos misturadas e divididas ao acaso 200 vezes, semente 42, 95º percentil). Menos de 1 carta além do ruído = estável.
   Precisa de 15 listas em cada período.

Cuidado (achado 1 da auditoria): as listas importadas são só as do topo de cada torneio; "lista base", inovações e estabilidade
descrevem quem foi bem, não o deck inteiro.
"""
import math
import random
from collections import Counter, defaultdict
from datetime import date, timedelta

from . import banco

QUEDA_DIA2 = 0.4
MIN_JOGADORES_APROV = 20
NUCLEO, OPCAO = 0.75, 0.10
MIN_LISTAS_BASE = 5
SUBIDA_MIN, P_MAX, MIN_LISTAS_INOV = 0.25, 0.005, 5
PADRAO_ANTES = 0.75
JACCARD_PACOTE = 0.6
MIN_LISTAS_ESTAB, PERMUTACOES, SEMENTE = 15, 200, 42


def _marcas(ids):
    return ",".join("?" * len(ids))


# ------------------------------------------------------------------ 1. aproveitamento no suíço

def rodadas_suicas(partidas_por_rodada, grande_evento=True):
    """{rodada: mesas} -> conjunto das rodadas suíças que todos podiam jogar.
    1) Top cut, de trás para a frente: a última rodada tem no máximo 1 mesa, a anterior 2, depois 4, 8, 16 (eliminatória).
    2) Dia 2 dos grandes eventos: se o número de mesas cai mais de 40% de uma rodada para a seguinte, só o que vem antes conta
       (quem não passou não podia jogar o resto; nos online as desistências tiram poucas mesas por rodada)."""
    rodadas = sorted(r for r in partidas_por_rodada if r is not None)
    if not rodadas:
        return set()
    i, limite = len(rodadas) - 1, 1
    while i > 0 and partidas_por_rodada[rodadas[i]] <= limite and limite <= 16:
        i, limite = i - 1, limite * 2
    suicas = rodadas[:i + 1]
    for k in range(1, len(suicas) if grande_evento else 0):
        if partidas_por_rodada[suicas[k]] < (1 - QUEDA_DIA2) * partidas_por_rodada[suicas[k - 1]]:
            return set(suicas[:k])
    return set(suicas)


def aproveitamento_jogadores(torneios):
    """{(torneio, nome_norm): (pontos, possiveis)} só de quem tem partida suíça achada."""
    if not torneios:
        return {}
    linhas = banco.consultar(f"SELECT torneio, rodada, j1, j2, res1 FROM t_partidas WHERE torneio IN ({_marcas(torneios)})",
                             tuple(torneios))
    por_torneio = defaultdict(list)
    for r in linhas:
        por_torneio[r["torneio"]].append(r)
    online = {r["id"] for r in banco.consultar(f"SELECT id FROM torneios WHERE fonte = 'online' AND id IN ({_marcas(torneios)})", tuple(torneios))}
    saida = {}
    for t, ps in por_torneio.items():
        suicas = rodadas_suicas(Counter(p["rodada"] for p in ps), grande_evento=t not in online)
        possiveis = 3 * len(suicas)
        if not possiveis:
            continue
        pontos = defaultdict(int)
        for p in ps:
            if p["rodada"] not in suicas:
                continue
            for nome, res in ((p["j1"], p["res1"]), (p["j2"], {"W": "L", "L": "W", "T": "T"}.get(p["res1"]))):
                if nome:
                    pontos[nome] += {"W": 3, "T": 1}.get(res, 0)
        for nome, pt in pontos.items():
            saida[(t, nome)] = (pt, possiveis)
    return saida


_cache_aprov = {}


def aproveitamento_por_deck(torneios):
    """{arquetipo: {aproveitamento, ic_baixo, ic_alto, jogadores}} (em %); a faixa é a da média (1,96 × erro padrão).
    Guarda o resultado enquanto os torneios importados não mudarem (chave: torneios escolhidos + quantidade de linhas e a
    importação mais recente), porque a tela Meta pede de novo a cada clique."""
    if not torneios:
        return {}
    marca = banco.consultar("SELECT (SELECT COUNT(*) FROM t_partidas) AS p, (SELECT COUNT(*) FROM t_jogadores) AS j, "
                            "(SELECT MAX(importado_em) FROM torneios) AS i")[0]
    chave = (tuple(sorted(torneios)), marca["p"], marca["j"], marca["i"])
    if chave not in _cache_aprov:
        if len(_cache_aprov) > 32:
            _cache_aprov.clear()
        _cache_aprov[chave] = _aproveitamento_por_deck(torneios)
    return _cache_aprov[chave]


def _aproveitamento_por_deck(torneios):
    por_jog = aproveitamento_jogadores(torneios)
    js = banco.consultar(f"SELECT torneio, nome_norm, labs_id, arquetipo FROM t_jogadores WHERE arquetipo != '' AND torneio IN ({_marcas(torneios)})",
                         tuple(torneios))
    valores = defaultdict(list)
    for j in js:
        x = por_jog.get((j["torneio"], j["nome_norm"])) or por_jog.get((j["torneio"], (j["labs_id"] or "").lower()))
        if x:
            valores[j["arquetipo"]].append(x[0] / x[1])
    saida = {}
    for arq, xs in valores.items():
        n = len(xs)
        m = sum(xs) / n
        dp = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
        e = 1.96 * dp / math.sqrt(n) if n > 1 else None
        saida[arq] = {"aproveitamento": round(100 * m, 1), "jogadores_aprov": n,
                      "aprov_baixo": round(100 * max(0.0, m - e), 1) if e is not None else None,
                      "aprov_alto": round(100 * min(1.0, m + e), 1) if e is not None else None}
    return saida


# ------------------------------------------------------------------ listas do deck

def _nome_carta(nome):
    """Mesmo nome para a mesma carta nas duas fontes: o Labs escreve "Fire Energy" e os online "Basic Fire Energy"."""
    nome = (nome or "").strip()
    if nome.startswith("Basic ") and nome.endswith(" Energy"):
        return nome[6:]
    return nome


def _listas(arq, torneios):
    """[{chave, data, pontos, partidas, cartas: {nome: cópias}}] das listas do deck nos torneios."""
    if not torneios:
        return []
    marcas = _marcas(torneios)
    datas = {r["id"]: (r["data"] or "")[:10] for r in banco.consultar(f"SELECT id, data FROM torneios WHERE id IN ({marcas})", tuple(torneios))}
    jogs = {(r["torneio"], r["labs_id"]): r for r in banco.consultar(
        f"SELECT torneio, labs_id, v, d, e FROM t_jogadores WHERE arquetipo=? AND torneio IN ({marcas})", (arq, *torneios))}
    cartas = defaultdict(Counter)
    for r in banco.consultar(
            f"SELECT l.torneio, l.labs_id, l.carta, l.carta_base, l.qtd FROM t_listas l JOIN t_jogadores j "
            f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo=? AND l.torneio IN ({marcas})", (arq, *torneios)):
        cartas[(r["torneio"], r["labs_id"])][_nome_carta(r["carta_base"] or r["carta"])] += r["qtd"] or 0
    saida = []
    for ch, cs in cartas.items():
        j = jogs.get(ch) or {}
        v, d, e = j.get("v") or 0, j.get("d") or 0, j.get("e") or 0
        saida.append({"chave": ch, "data": datas.get(ch[0], ""), "pontos": 3 * v + e, "partidas": v + d + e, "cartas": dict(cs)})
    return saida


# ------------------------------------------------------------------ 2. lista base

def lista_base(arq, torneios):
    listas = _listas(arq, torneios)
    total = sum(l["pontos"] for l in listas)
    if len(listas) < MIN_LISTAS_BASE or not total:
        return {"listas": len(listas), "nucleo": [], "opcoes": [], "minimo": MIN_LISTAS_BASE}
    peso, qtds = Counter(), defaultdict(Counter)
    for l in listas:
        for c, q in l["cartas"].items():
            peso[c] += l["pontos"]
            qtds[c][q] += l["pontos"]
    linhas = []
    for c, p in peso.items():
        f = p / total
        if f < OPCAO:
            continue
        linhas.append({"carta": c, "peso": round(100 * f, 1), "copias": qtds[c].most_common(1)[0][0],
                       "listas": sum(1 for l in listas if c in l["cartas"])})
    linhas.sort(key=lambda x: (-x["peso"], x["carta"]))
    return {"listas": len(listas), "minimo": MIN_LISTAS_BASE,
            "nucleo": [x for x in linhas if x["peso"] >= 100 * NUCLEO],
            "opcoes": [x for x in linhas if x["peso"] < 100 * NUCLEO]}


# ------------------------------------------------------------------ 3 e 4. períodos, inovações, estabilidade

def _periodos(listas, dias_recentes, dias_anteriores):
    datas = [l["data"] for l in listas if l["data"]]
    if not datas:
        return [], [], None
    fim = date.fromisoformat(max(datas))
    corte = fim - timedelta(days=dias_recentes)
    inicio = corte - timedelta(days=dias_anteriores)
    recentes = [l for l in listas if l["data"] and date.fromisoformat(l["data"]) > corte]
    antes = [l for l in listas if l["data"] and inicio < date.fromisoformat(l["data"]) <= corte]
    return recentes, antes, {"recente_de": (corte + timedelta(days=1)).isoformat(), "recente_ate": fim.isoformat(),
                             "antes_de": (inicio + timedelta(days=1)).isoformat(), "antes_ate": corte.isoformat()}


def binomial_cauda_superior(k, n, p):
    """P(X ≥ k) com X ~ Binomial(n, p), exata (soma dos termos, em log para não estourar)."""
    if k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    lp, lq = math.log(p), math.log(1 - p)
    termos = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(k, n + 1)]
    m = max(termos)
    return min(1.0, math.exp(m) * sum(math.exp(t - m) for t in termos))


def _aproveit_lista(l):
    return l["pontos"] / (3 * l["partidas"]) if l["partidas"] else None


def inovacoes(arq, torneios, dias_recentes=14, dias_anteriores=28):
    listas = _listas(arq, torneios)
    recentes, antes, per = _periodos(listas, dias_recentes, dias_anteriores)
    base = {"periodos": per, "listas_recentes": len(recentes), "listas_antes": len(antes)}
    if len(recentes) < MIN_LISTAS_INOV or len(antes) < MIN_LISTAS_INOV:
        return {**base, "pacotes": [], "estabilidade": None, "motivo": f"precisa de {MIN_LISTAS_INOV} listas em cada período"}
    cartas = set(c for l in recentes + antes for c in l["cartas"])
    moda_antes = {}
    for c in cartas:
        qs = Counter(l["cartas"].get(c, 0) for l in antes)
        moda_antes[c] = qs.most_common(1)[0][0]
    candidatas = []
    for c in cartas:
        maximo = max(l["cartas"].get(c, 0) for l in recentes + antes)
        testes = [(f"{c} ≥ {k}", c, "≥", k, (lambda l, c=c, k=k: l["cartas"].get(c, 0) >= k)) for k in range(1, maximo + 1)]
        uso_antes = sum(1 for l in antes if c in l["cartas"]) / len(antes)
        if uso_antes >= PADRAO_ANTES and moda_antes[c] >= 1:
            k = moda_antes[c]
            testes.append((f"{c} < {k}", c, "<", k, (lambda l, c=c, k=k: l["cartas"].get(c, 0) < k)))
        for rotulo, carta, op, k, tem in testes:
            com = [l for l in recentes if tem(l)]
            a, b = len(com) / len(recentes), sum(1 for l in antes if tem(l)) / len(antes)
            if len(com) < MIN_LISTAS_INOV or a - b < SUBIDA_MIN:
                continue
            p = binomial_cauda_superior(len(com), len(recentes), min(0.99, max(0.01, b)))
            if p >= P_MAX:
                continue
            sem = [l for l in recentes if not tem(l)]
            ap_com = [x for x in map(_aproveit_lista, com) if x is not None]
            ap_sem = [x for x in map(_aproveit_lista, sem) if x is not None]
            m_com = sum(ap_com) / len(ap_com) if ap_com else None
            m_sem = sum(ap_sem) / len(ap_sem) if ap_sem else None
            if m_com is None or (m_sem is not None and m_com <= m_sem):
                continue
            de = Counter(l["cartas"].get(carta, 0) for l in antes).most_common(1)[0][0]
            para = Counter(l["cartas"].get(carta, 0) for l in com).most_common(1)[0][0]
            candidatas.append({"rotulo": rotulo, "carta": carta, "op": op, "k": k, "agora": round(100 * a, 1), "antes": round(100 * b, 1),
                               "p": p, "aprov_com": round(100 * m_com, 1), "aprov_sem": round(100 * m_sem, 1) if m_sem is not None else None,
                               "de": de, "para": para, "_listas": {l["chave"] for l in com},
                               "peso": a * math.log(a / max(b, 0.01))})
    # uma característica por carta: a de maior peso (≥ 1 e ≥ 2 da mesma carta contam a mesma história)
    melhor = {}
    for x in candidatas:
        if x["carta"] not in melhor or x["peso"] > melhor[x["carta"]]["peso"]:
            melhor[x["carta"]] = x
    itens = sorted(melhor.values(), key=lambda x: -x["peso"])
    pacotes = []
    for x in itens:
        for pac in pacotes:
            uniao = pac["_listas"] | x["_listas"]
            if uniao and len(pac["_listas"] & x["_listas"]) / len(uniao) >= JACCARD_PACOTE:
                pac["mudancas"].append(x)
                pac["_listas"] &= x["_listas"]
                break
        else:
            pacotes.append({"mudancas": [x], "_listas": set(x["_listas"])})
    saida = []
    for pac in pacotes:
        ms = [{k: v for k, v in m.items() if not k.startswith("_")} for m in pac["mudancas"]]
        for m in ms:
            m["p"] = float(f"{m['p']:.2g}")
            m["peso"] = round(m["peso"], 3)
        saida.append({"mudancas": ms, "listas": len(pac["_listas"]), "peso": round(max(m["peso"] for m in ms), 3)})
    saida.sort(key=lambda p: -p["peso"])
    return {**base, "pacotes": saida, "estabilidade": estabilidade(recentes, antes)}


def _media(listas, cartas):
    n = len(listas)
    return {c: sum(l["cartas"].get(c, 0) for l in listas) / n for c in cartas}


def _distancia(a, b, cartas):
    ma, mb = _media(a, cartas), _media(b, cartas)
    return sum(abs(ma[c] - mb[c]) for c in cartas) / 2


def estabilidade(recentes, antes, permutacoes=PERMUTACOES, semente=SEMENTE):
    """{mudou, ruido, alem_do_ruido, estavel} em cartas; None com menos de 15 listas num dos períodos."""
    if len(recentes) < MIN_LISTAS_ESTAB or len(antes) < MIN_LISTAS_ESTAB:
        return None
    cartas = set(c for l in recentes + antes for c in l["cartas"])
    obs = _distancia(recentes, antes, cartas)
    todas = recentes + antes
    rnd = random.Random(semente)
    dists = []
    for _ in range(permutacoes):
        rnd.shuffle(todas)
        dists.append(_distancia(todas[:len(recentes)], todas[len(recentes):], cartas))
    dists.sort()
    p95 = dists[int(0.95 * (len(dists) - 1))]
    alem = obs - p95
    return {"mudou": round(obs, 2), "ruido": round(p95, 2), "alem_do_ruido": round(alem, 2), "estavel": alem < 1}
