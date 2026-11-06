"""
EXPERIMENTOS ESTRATÉGICOS P1–P7 — roteiro PRONTO, para rodar quando houver partidas suficientes (06/11/2026).
Desenho de cada um: `knowledge/PRIZE_ANALYSIS.md` §5 (P1–P4), `CONTROL_AND_DISRUPTION.md` §4 (P5, P6), `DECISION_ANALYSIS.md` §6 (P7).
Funções: `tools/estrategia.py` (puras) + do Coletor pela ponte (só leitura): `replay.gerar`, `probabilidades.hipergeometrica`,
`regressao.ajustar`, `decks.ler_lista`, `analises.wilson`; contas novas do `sa_tools` (log-loss, Brier, calibração, bootstrap,
Holm/BH, registro).

TRAVA DE AMOSTRA: cada experimento tem um mínimo de unidades (MINIMOS). Abaixo dele o roteiro só CONTA, avisa e para — não calcula
e não grava nada. `--exploratorio` roda mesmo abaixo do mínimo e marca o resultado como exploratório (não use para decidir nada).
Em 06/11/2026 (83 partidas) os experimentos NÃO foram aplicados à base, por decisão do Pedro (poucos jogos).

Uso:  python -I p_estrategia.py <CÓPIA do programa> <p1|p2|p3|p4|p5|p6|p7|todos> [--exploratorio] [--minimo N]
Previsão (P2, P4): treino = 70% das partidas mais antigas (data de captura), teste = 30% mais novas; nada do teste no treino.
Bootstrap agrupado por PARTIDA (as linhas de uma partida não são independentes). Saída sem nicks (jogador "A"/"B"/"exportou").
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import estrategia as E  # noqa: E402
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

MINIMOS = {"p1": 50, "p2": 300, "p3": 100, "p4": 300, "p5": 300, "p6": 300, "p7": 300}
SEMENTE, CORTE, REPETICOES = 3131, 0.7, 1000
UNIDADE = {"p1": "partidas com vencedor", "p2": "partidas com vencedor", "p3": "partidas de quem exportou com lista ligada e sem mulligan",
           "p4": "partidas com vencedor", "p5": "partidas com vencedor", "p6": "partidas", "p7": "partidas com vencedor"}


def argumentos(argv):
    if len(argv) < 3 or argv[2] not in (*MINIMOS, "todos"):
        sys.exit(__doc__)
    exp = list(MINIMOS) if argv[2] == "todos" else [argv[2]]
    explor = "--exploratorio" in argv
    minimo = int(argv[argv.index("--minimo") + 1]) if "--minimo" in argv else None
    return argv[1], exp, explor, minimo


def carregar_partidas(t):
    """Partidas com dados lidos, em ordem de captura: [{"id", "data", "texto", "dados", "deck_id"}]."""
    saida = []
    for p in t.banco.consultar("SELECT id, capturada_em, texto, dados_json, deck_id FROM partidas ORDER BY capturada_em, id"):
        try:
            d = json.loads(p["dados_json"] or "{}")
        except ValueError:
            continue
        if d.get("resumo"):
            saida.append({"id": p["id"], "data": p["capturada_em"] or "", "texto": p["texto"] or "", "dados": d, "deck_id": p["deck_id"]})
    return saida


class Contexto:
    def __init__(self, t):
        self.t = t
        self.regras = t.config.ler_regras()
        self.partidas = carregar_partidas(t)
        self._rep = {}

    def rep(self, p):
        if p["id"] not in self._rep:
            self._rep[p["id"]] = self.t.replay.gerar(p["texto"], self.regras)
        return self._rep[p["id"]]

    def com_vencedor(self):
        return [p for p in self.partidas if p["dados"]["resumo"].get("vencedor")]


def separar_no_tempo(partidas):
    corte = int(len(partidas) * CORTE)
    return partidas[:corte], partidas[corte:]


def faixa_partidas(linhas_por_partida, estat):
    """Bootstrap agrupado por partida para a estatística `estat` (lista de linhas -> número)."""
    grupos = {k: v for k, v in linhas_por_partida.items() if v}
    if len(grupos) < 2:
        return None
    return T.bootstrap_agrupado(grupos, estat, REPETICOES, SEMENTE)


# ------------------------------------------------------------------ P1 — rotas de prêmios
def unidades_p1(c):
    return c.com_vencedor()


def p1(c, ps):
    mapas = Counter()
    ko_ok = ko_n = 0
    estados = dentro = 0
    n_rotas = []
    for p in ps:
        r = p["dados"]["resumo"]
        rep = c.rep(p)
        rota = E.rota_executada(rep)
        if r.get("motivo") == "Pegou todos os prêmios" and r["vencedor"] in rota:
            mapas[E.mapa(rota[r["vencedor"]])] += 1
        for k in r.get("nocautes") or []:
            ko_n += 1
            ko_ok += k.get("premios") == E.valor_premio(k.get("carta"))
        # rotas possíveis com os alvos EM JOGO no começo de cada tomada × resto da rota executada
        tks = E.tomadas(rep)
        js = rep["jogadores"]
        for i, tk in enumerate(tks):
            outro = next(j for j in js if j != tk["jogador"])
            q = rep["quadros"][max(tk["quadro"] - 1, 0)]["estado"]["mesa"]
            alvos = Counter(E.valor_premio(x["nome"]) for x in ([q[outro]["ativo"]] if q[outro]["ativo"] else []) + q[outro]["banco"])
            restantes = q[tk["jogador"]]["premios"]
            try:
                possiveis = set(E.rotas_possiveis(restantes, alvos))
            except ValueError:
                continue
            estados += 1
            n_rotas.append(len(possiveis))
            resto = tuple(x["n"] for x in tks[i:] if x["jogador"] == tk["jogador"])
            dentro += resto in possiveis
    n_rotas.sort()
    return {"rotas_executadas_vitorias_por_premios": dict(mapas.most_common()),
            "nocautes": ko_n, "coerencia_premio_por_nome": ko_ok / ko_n if ko_n else None,
            "estados_avaliados": estados, "rotas_possiveis_mediana": n_rotas[len(n_rotas) // 2] if n_rotas else None,
            "resto_executado_entre_as_possiveis_com_alvos_atuais": dentro / estados if estados else None,
            "leitura": "rota possível com os alvos atuais ≠ executável (dano/Energia) ≠ planejada (não observável)"}


# ------------------------------------------------------------------ P2 — corrida
def linhas_corrida(c, ps):
    """Uma linha por (partida, fim de turno) do ponto de vista do jogador A = o primeiro da lista do replay."""
    out = defaultdict(list)
    for p in ps:
        rep = c.rep(p)
        js = rep["jogadores"]
        if len(js) != 2:
            continue
        a, b = js
        y = 1 if p["dados"]["resumo"]["vencedor"] == a else 0
        cor = E.corrida(rep)
        hist = []
        for item in cor:
            ra, rb = item["restantes"][a], item["restantes"][b]
            hist.append((ra, rb))
            ritmo_a = (hist[-3][0] - ra) if len(hist) >= 3 else (6 - ra)
            ritmo_b = (hist[-3][1] - rb) if len(hist) >= 3 else (6 - rb)
            out[p["id"]].append({"turno": item["turno"], "D": rb - ra, "ritmo": ritmo_a - ritmo_b, "y": y})
    return out


def unidades_p2(c):
    return c.com_vencedor()


def ajustar(c, linhas, vars_):
    lin = [(0.0, {0: 1.0, **{i + 1: l[v] for i, v in enumerate(vars_)}}, l["y"]) for l in linhas]
    b, _ = c.t.regressao.ajustar(lin, len(vars_) + 1, peso=1e-3, peso_deck=1e-3)
    return b


def prever(b, l, vars_):
    eta = b[0] + sum(b[i + 1] * l[v] for i, v in enumerate(vars_))
    return min(max(1 / (1 + math.exp(-eta)), 1e-6), 1 - 1e-6)


def p2(c, ps):
    treino, teste = separar_no_tempo(ps)
    lt, le = linhas_corrida(c, treino), linhas_corrida(c, teste)
    tr = [l for v in lt.values() for l in v]
    if not tr or not le:
        return {"erro": "sem linhas de treino ou teste"}
    modelos = {"so_D": ["D"], "D_e_ritmo": ["D", "ritmo"]}
    coef = {m: ajustar(c, tr, v) for m, v in modelos.items()}
    res = {"treino_partidas": len(treino), "teste_partidas": len(teste), "modelos": {}, "comparacao": None, "kaplan_meier": None}
    perdas = {}
    for m, v in modelos.items():
        pares = [(prever(coef[m], l, v), l["y"]) for ls in le.values() for l in ls]
        res["modelos"][m] = {"coeficientes": coef[m], "logloss": T.logloss(pares), "brier": T.brier(pares),
                             "calibracao": T.calibracao_detalhada(pares, [pid for pid, ls in le.items() for _ in ls], repeticoes=200)}
        perdas[m] = [(pid, -(l["y"] * math.log(prever(coef[m], l, v)) + (1 - l["y"]) * math.log(1 - prever(coef[m], l, v))))
                     for pid, ls in le.items() for l in ls]
    res["comparacao"] = T.diferenca_pareada([(g, a, b) for (g, a), (_, b) in zip(perdas["D_e_ritmo"], perdas["so_D"])], REPETICOES, SEMENTE)
    # tempo até vencer por prêmios, com desistência/sem Pokémon como censura (todas as partidas)
    tempos = [p["dados"]["resumo"].get("turnos") or 0 for p in ps]
    eventos = [1 if p["dados"]["resumo"].get("motivo") == "Pegou todos os prêmios" else 0 for p in ps]
    res["kaplan_meier"] = E.kaplan_meier(tempos, eventos)
    return res


# ------------------------------------------------------------------ P3 — prêmios checados
def unidades_p3(c):
    listas = {r["id"]: r["lista"] for r in c.t.banco.consultar("SELECT id, lista FROM meus_decks")}
    out = []
    for p in c.com_vencedor():
        exp = p["dados"]["resumo"].get("exportou")
        if exp and p["deck_id"] in listas and E.mao_inicial(p["texto"], exp) is not None:
            out.append(p | {"lista": listas[p["deck_id"]], "exportou": exp})
    return out


def p3(c, ps):
    hg = c.t.probabilidades.hipergeometrica
    por_k = defaultdict(lambda: [0, 0.0, 0.0, 0])
    ao_menos, grupos_am = [], []
    usadas = descartadas = 0
    for p in ps:
        itens, _ = c.t.decks.ler_lista(p["lista"])
        deck = Counter()
        for it in itens:
            deck[it["nome"]] += it["qtd"]
        mao = E.mao_inicial(p["texto"], p["exportou"])
        try:
            z = E.zonas_desconhecidas(deck, mao)
        except ValueError:
            descartadas += 1
            continue
        rep = c.rep(p)
        pegos = Counter(q["destaque"]["carta"] for q in rep["quadros"]
                        if q["destaque"].get("tipo") == "premio" and q["destaque"].get("jogador") == p["exportou"] and q["destaque"].get("carta"))
        k = sum(pegos.values())
        if not k:
            continue
        usadas += 1
        N = z["N"]
        for nome, m in z["m"].items():
            e_ = k * m / N
            var = k * (m / N) * (1 - m / N) * (N - k) / (N - 1)
            x = por_k[min(m, 4)]
            x[0] += pegos.get(nome, 0)
            x[1] += e_
            x[2] += var
            x[3] += 1
            prev = E.premio_checado(N, m, k, hg)      # P(≥1 cópia entre os k pegos) — os k pegos são amostra dos prêmios
            ao_menos.append((prev, 1 if pegos.get(nome, 0) else 0))
            grupos_am.append(p["id"])
    if not ao_menos:
        return {"erro": "nenhuma partida utilizável"}
    return {"partidas_usadas": usadas, "descartadas_lista_nao_confere": descartadas,
            "por_copias_restantes": {K: {"n": x[3], "observado": x[0], "esperado": x[1],
                                         "z_aprox": (x[0] - x[1]) / math.sqrt(x[2]) if x[2] else None} for K, x in sorted(por_k.items())},
            "ao_menos_uma_entre_os_pegos": T.calibracao_detalhada(ao_menos, grupos_am, repeticoes=200),
            "premissas": "estado = depois da mão inicial (N = 60 − 7); prêmios pegos = amostra dos 6, escolhidos virados"}


# ------------------------------------------------------------------ P4 — troca de prêmios
def unidades_p4(c):
    return c.com_vencedor()


def p4(c, ps):
    por_partida = defaultdict(list)
    for p in ps:
        rep = c.rep(p)
        js = rep["jogadores"]
        tks = E.tomadas(rep)
        if len(js) != 2 or len({tk["jogador"] for tk in tks}) < 2:
            continue
        v = p["dados"]["resumo"]["vencedor"]
        for j in js:
            tr = E.trocas(tks, j)
            fechadas = [x for x in tr if not x["aberta"]]
            if fechadas:
                por_partida[p["id"]].append({"saldo_medio": sum(x["saldo"] for x in fechadas) / len(fechadas),
                                             "venceu": 1 if j == v else 0})
    if not por_partida:
        return {"erro": "sem trocas"}

    def dif(linhas):
        g = [l["saldo_medio"] for l in linhas if l["venceu"]]
        p_ = [l["saldo_medio"] for l in linhas if not l["venceu"]]
        return (sum(g) / len(g) - sum(p_) / len(p_)) if g and p_ else 0.0
    return {"partidas": len(por_partida), "saldo_medio_vencedor_menos_perdedor": faixa_partidas(por_partida, dif),
            "leitura": "associação esperada por construção (quem vence pega mais prêmios); não prova que buscar trocas causa vitória"}


# ------------------------------------------------------------------ P5 — disrupção
def unidades_p5(c):
    return c.com_vencedor()


def p5(c, ps):
    por_cat = defaultdict(lambda: defaultdict(list))   # categoria -> partida -> [(estrato, tratado, y)]
    for p in ps:
        ev = p["dados"].get("eventos") or []
        js = p["dados"].get("jogadores") or []
        if len(js) != 2:
            continue
        disr = E.categorias_disrupcao(ev)
        cats_turno = defaultdict(set)
        for d in disr:
            cats_turno[(d["jogador"], d["turno"])].add(d["categoria"])
        for j in js:
            outro = next(x for x in js if x != j)
            meus = E.turnos_do_jogador(ev, j)
            dele = E.turnos_do_jogador(ev, outro)
            for t_ in meus:
                prox = [x for x in dele if x > t_][:1]
                if not prox:
                    continue
                y = E.desenvolvimento(ev, outro, prox)["acoes"]
                estrato = (min(t_, 10),)
                for cat in set(E.CATEGORIAS.values()):
                    por_cat[cat][p["id"]].append((estrato, cat in cats_turno[(j, t_)], y))
    res, pvals, nomes = {}, [], []
    for cat, por_partida in por_cat.items():
        linhas = [l for v in por_partida.values() for l in v]
        if not any(tr for _, tr, _ in linhas):
            continue
        est = E.diferenca_por_estrato(linhas)
        fx = faixa_partidas(por_partida, lambda ls: E.diferenca_por_estrato(ls)["diferenca"] or 0.0)
        res[cat] = {"estimativa": est, "ic95": [fx["baixo"], fx["alto"]] if fx else None}
        if fx:
            nomes.append(cat)
            se = (fx["alto"] - fx["baixo"]) / (2 * 1.96) or 1e-9
            pvals.append(math.erfc(abs((est["diferenca"] or 0) / se) / math.sqrt(2)))
    if pvals:
        for cat, h, q in zip(nomes, T.holm(pvals), T.benjamini_hochberg(pvals)):
            res[cat]["p_holm"], res[cat]["q_bh"] = h, q
    res["leitura"] = "diferença de ações do adversário no turno seguinte, pareada por turno; associação (CONTROL_AND_DISRUPTION.md §5)"
    return res


# ------------------------------------------------------------------ P6 — stall e mill
def unidades_p6(c):
    return c.partidas


def p6(c, ps):
    fins = E.fins(p["dados"]["resumo"] for p in ps)
    secas = []
    for p in ps:
        ev = p["dados"].get("eventos") or []
        kos = sorted({e["turno"] for e in ev if e.get("tipo") == "nocaute" and e.get("turno")})
        turnos = p["dados"]["resumo"].get("turnos") or 0
        marcos = [0] + kos + [turnos]
        secas.append(max(b - a for a, b in zip(marcos, marcos[1:])) if turnos else 0)
    secas.sort()
    tempos = [p["dados"]["resumo"].get("turnos") or 0 for p in ps]
    eventos = [0 if p["dados"]["resumo"].get("motivo") == "Desistência" else 1 for p in ps]
    return {"motivos_de_fim": dict(fins), "maior_sequencia_de_turnos_sem_nocaute": {"mediana": secas[len(secas) // 2] if secas else None,
                                                                                    "p90": secas[int(0.9 * len(secas))] if secas else None},
            "duracao_kaplan_meier_desistencia_censurada": E.kaplan_meier(tempos, eventos) if ps else None}


# ------------------------------------------------------------------ P7 — sequência
PADROES = (("energia", "jogada"), ("evolucao", "energia"), ("jogada", "evolucao"))


def unidades_p7(c):
    return [p for p in c.com_vencedor() if p["dados"]["resumo"].get("exportou")]


def p7(c, ps):
    por_padrao = {f"{a}_antes_de_{b}": defaultdict(list) for a, b in PADROES}
    ngr = Counter()
    for p in ps:
        ev = p["dados"].get("eventos") or []
        exp = p["dados"]["resumo"]["exportou"]
        for t_ in E.turnos_do_jogador(ev, exp):
            seq = E.acoes_do_turno(ev, exp, t_)
            ngr.update(E.ngramas(seq, 2))
            atacou = 1 if "ataque" in seq else 0
            for a, b in PADROES:
                ordem = E.antes_de(seq, a, b)
                if ordem is not None:
                    por_padrao[f"{a}_antes_de_{b}"][p["id"]].append(((min(t_, 10),), ordem, atacou))
    res, pvals, nomes = {"bigramas_mais_comuns": {"→".join(k): v for k, v in ngr.most_common(15)}}, [], []
    for nome, por_partida in por_padrao.items():
        linhas = [l for v in por_partida.values() for l in v]
        if not linhas:
            continue
        est = E.diferenca_por_estrato(linhas)
        fx = faixa_partidas(por_partida, lambda ls: E.diferenca_por_estrato(ls)["diferenca"] or 0.0)
        res[nome] = {"estimativa": est, "ic95": [fx["baixo"], fx["alto"]] if fx else None}
        if fx:
            nomes.append(nome)
            se = (fx["alto"] - fx["baixo"]) / (2 * 1.96) or 1e-9
            pvals.append(math.erfc(abs((est["diferenca"] or 0) / se) / math.sqrt(2)))
    for nome, h in zip(nomes, T.holm(pvals) if pvals else []):
        res[nome]["p_holm"] = h
    res["leitura"] = "taxa de ataque no turno com o padrão − sem o padrão, pareada por turno; associação, a mão explica parte"
    return res


EXPERIMENTOS = {"p1": (unidades_p1, p1), "p2": (unidades_p2, p2), "p3": (unidades_p3, p3), "p4": (unidades_p4, p4),
                "p5": (unidades_p5, p5), "p6": (unidades_p6, p6), "p7": (unidades_p7, p7)}


def main(argv):
    pasta, lista, explor, minimo = argumentos(argv)
    t = carregar(pasta)
    c = Contexto(t)
    for nome in lista:
        unidades, rodar = EXPERIMENTOS[nome]
        ps = unidades(c)
        precisa = minimo if minimo is not None else MINIMOS[nome]
        print(f"{nome}: {len(ps)} {UNIDADE[nome]} (mínimo {precisa})")
        if len(ps) < precisa and not explor:
            print(f"   amostra insuficiente: {nome} NÃO foi rodado e nada foi gravado (use --exploratorio só para testar)")
            continue
        res = rodar(c, ps)
        res["exploratorio"] = len(ps) < MINIMOS[nome]
        arq = T.registrar(f"{nome}_estrategia", res, t.pasta, AQUI / "resultados", semente=SEMENTE,
                          parametros={"minimo": precisa, "minimo_padrao": MINIMOS[nome], "corte": CORTE, "repeticoes": REPETICOES,
                                      "exploratorio_pedido": explor},
                          filtros={"unidade": UNIDADE[nome]},
                          dados_usados={"unidades": len(ps), "impressao": T.impressao_objeto(sorted(p["id"] for p in ps))},
                          copia=t.identificacao)
        print(f"   {'EXPLORATÓRIO — ' if res['exploratorio'] else ''}resultado gravado em {arq.name}")


if __name__ == "__main__":
    main(sys.argv)
