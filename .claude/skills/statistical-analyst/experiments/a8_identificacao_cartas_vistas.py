"""
AUDITORIA A8 (06/11/2026, rodada de "hardening") — identificação do deck com cartas VISTAS (não sorteadas ao acaso), sem vazamento.
Complementa o a4 (que fica como está). Pergunta: qual método acerta mais o deck do jogador a partir das cartas reveladas até o
turno T — ícones, NB2, a regra do programa (NB2 ≥ 0,5 senão ícones), NB2 com abstenção, NB2 com prior uniforme?

Desenho:
  PARTE R (real): partidas do banco com gabarito INDEPENDENTE da identificação — partidas ligadas a uma lista de "Meus decks"
     (ligação por cobertura das cartas reveladas ≥ 90% da lista, `decks.vincular_automatico`), arquétipo = o da lista. Cartas do dono
     do log reveladas até o turno T (eventos do log). Modelos montados com os torneios de data ANTERIOR à 1ª partida avaliada.
     Limitação: hoje é 1 arquétipo e 1 jogador (mede só a revocação desse deck; não há precisão nem matriz de confusão útil).
  PARTE S (sintética realista): listas dos 30% de torneios mais recentes (teste); "cartas vistas até o turno T" sorteadas com a chance
     de revelação MEDIDA nos logs reais (por categoria — Pokémon/Treinador/Energia especial — e nº de cópias, por turno), reescalada
     para o nº médio de cartas reveladas por turno em TODOS os logs (os dois jogadores). Treino = 70% mais antigos, com corte que não
     divide uma data; NADA do teste no treino: listas (NB2 e assinaturas), contagem de jogadores por deck (desempate dos ícones) e
     cadastro de arquétipos/ícones (só os decks que aparecem no treino). Para medir o vazamento do a4, os ícones e a regra do
     programa também rodam com o cadastro de TODOS os torneios (condição do a4), nos mesmos sorteios.
  Métricas: acurácia, taxa de erro e de inconclusivo, precisão/revocação/F1 macro e ponderado, acurácia balanceada, matriz de
     confusão (10 decks mais comuns + outros), revocação por arquétipo, por turno e por nº de cartas vistas; diferença pareada
     (programa − NB2) com bootstrap por torneio; calibração da confiança do NB2 (para o a9 e o relatório).
Só lê. Semente 2611. Uso:  python -I a8_identificacao_cartas_vistas.py <CÓPIA do programa>
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

SEMENTE, CORTE, TURNOS = 2611, 0.7, (1, 2, 3, 4, 6, 8)
t = carregar(sys.argv[1])
D, B, C = t.decks, t.banco, t.cartas
rng = random.Random(SEMENTE)
norm = t.leitor.normalizar_nome_carta
_cat = {}


def categoria(nome):
    if nome not in _cat:
        e = C.por_nome(nome) or {}
        c = (e.get("categoria") or "").lower()
        _cat[nome] = "pokemon" if c.startswith("pok") else "energia" if c.startswith("ener") else "treinador" if c else "?"
    return _cat[nome]


def balde(q):
    return min(int(q), 4)


# ------------------------------------------------------------------ dados: listas de torneio
rows = B.consultar(
    "SELECT t.data, j.arquetipo AS arq, l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd "
    "FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id JOIN torneios t ON t.id=l.torneio "
    "WHERE j.arquetipo != ''")
listas = defaultdict(lambda: {"arq": "", "data": "", "torneio": "", "cartas": Counter()})
for r in rows:
    L = listas[(r["torneio"], r["labs_id"])]
    L["arq"], L["data"], L["torneio"] = r["arq"], r["data"] or "", r["torneio"]
    if not C.eh_energia_basica(r["carta"]):
        L["cartas"][r["carta"]] += r["qtd"] or 1
data_t = {}
for L in listas.values():
    data_t[L["torneio"]] = min(data_t.get(L["torneio"], "9999"), L["data"])
ordem = sorted(data_t, key=lambda x: (data_t[x], x))
n_tr = int(len(ordem) * CORTE)
while 0 < n_tr < len(ordem) and data_t[ordem[n_tr]] == data_t[ordem[n_tr - 1]]:
    n_tr -= 1                          # não dividir uma data entre treino e teste
treino_t, teste_t = set(ordem[:n_tr]), set(ordem[n_tr:])
assert max(data_t[x] for x in treino_t) < min(data_t[x] for x in teste_t), "treino e teste se sobrepõem no tempo"

consultar_original = D.banco.consultar


def montar_modelos(torneios_ok: set):
    """Monta NB2, assinaturas e cadastro SÓ com `torneios_ok`; devolve (cadastro_restrito, cadastro_todos)."""
    lista_ok = ",".join("'" + x.replace("'", "''") + "'" for x in sorted(torneios_ok))

    def consultar_filtrado(sql, params=()):
        if "FROM t_jogadores WHERE arquetipo != '' GROUP BY arquetipo" in sql:          # contagem de jogadores (desempate)
            sql = sql.replace("WHERE arquetipo != ''", f"WHERE arquetipo != '' AND torneio IN ({lista_ok})")
        linhas = consultar_original(sql, params)
        if linhas and "lista" in linhas[0]:                                              # listas: NB2 e assinaturas
            return [x for x in linhas if x["lista"].split("/")[0] in torneios_ok]
        return linhas

    D.banco.consultar = consultar_original
    D._cache.clear()
    cad_todos = {k: dict(v) for k, v in D.arquetipos().items()}
    D.banco.consultar = consultar_filtrado
    D._cache.clear()
    D._modelo_nb()
    D._assinaturas()
    arq = D.arquetipos()
    decks_ok = {r["arquetipo"] for r in consultar_original(
        f"SELECT DISTINCT arquetipo FROM t_jogadores WHERE arquetipo != '' AND torneio IN ({lista_ok})")}
    cad_restrito = {k: v for k, v in arq.items() if k in decks_ok}                       # cadastro: só decks do treino
    for chave in ("nb", "ass"):
        D._cache[chave] = (D._cache[chave][0] + 10 ** 9, D._cache[chave][1])             # vale pelo tempo (como no a4)
    return cad_restrito, cad_todos


def usar_cadastro(cad):
    D._cache["arq"] = (D._cache.get("arq", (0,))[0] + 10 ** 9, cad)
    D._cache.pop("ident", None)


def nb2_prior_uniforme(reveladas):
    m = D._modelo_nb()
    if m["total"] < D.MINIMO_LISTAS_NB or not reveladas or not m["base"]:
        return "", 0.0
    k = len(reveladas)
    notas = {a: -k * m["log_n"][a] for a in m["base"]}
    for c in reveladas:
        for a, extra in m["indice"].get(c, {}).items():
            notas[a] += extra
    melhor = max(notas, key=notas.get)
    return melhor, 1 / sum(math.exp(v - notas[melhor]) for v in notas.values())


def avaliar(vistas, cad_restrito, cad_todos):
    """Todos os métodos para um conjunto de cartas vistas (nomes como no log, sem Energia Básica)."""
    rev = {norm(c) for c in vistas}
    s_nb, conf = D.identificar_nb(rev)
    s_un, _ = nb2_prior_uniforme(rev)
    usar_cadastro(cad_restrito)
    s_ic, s_pr = D._identificar_por_icones(list(vistas)), D.identificar(list(vistas))
    usar_cadastro(cad_todos)
    s_ic_t, s_pr_t = D._identificar_por_icones(list(vistas)), D.identificar(list(vistas))
    usar_cadastro(cad_restrito)
    return {"icones": s_ic, "nb2": s_nb, "programa": s_pr, "nb2_abstem": s_nb if conf >= D.CONFIANCA_NB else "",
            "nb2_senao_icones_so_sem_modelo": s_nb or s_ic, "nb2_prior_uniforme": s_un,
            "icones_cadastro_todos": s_ic_t, "programa_cadastro_todos": s_pr_t}, conf


METODOS = ("icones", "nb2", "programa", "nb2_abstem", "nb2_senao_icones_so_sem_modelo", "nb2_prior_uniforme",
           "icones_cadastro_todos", "programa_cadastro_todos")


def metricas(pares):
    """pares = [(verdade, previsto)], previsto '' = inconclusivo. Classes desbalanceadas: macro, ponderado e balanceada."""
    n = len(pares)
    if not n:
        return {}
    certo = sum(v == p for v, p in pares)
    inc = sum(p == "" for _, p in pares)
    classes = sorted({v for v, _ in pares})
    tp, prev_n, real_n = Counter(), Counter(), Counter()
    for v, p in pares:
        real_n[v] += 1
        if p:
            prev_n[p] += 1
        if v == p:
            tp[v] += 1
    prec = {c: tp[c] / prev_n[c] if prev_n[c] else 0.0 for c in classes}
    rec = {c: tp[c] / real_n[c] for c in classes}
    f1 = {c: 2 * prec[c] * rec[c] / (prec[c] + rec[c]) if prec[c] + rec[c] else 0.0 for c in classes}
    return {"n": n, "acuracia": certo / n, "erro": (n - certo - inc) / n, "inconclusivo": inc / n,
            "precisao_macro": sum(prec.values()) / len(classes), "revocacao_macro": sum(rec.values()) / len(classes),
            "f1_macro": sum(f1.values()) / len(classes), "f1_ponderado": sum(f1[c] * real_n[c] for c in classes) / n,
            "acuracia_balanceada": sum(rec.values()) / len(classes), "classes": len(classes),
            "acerto_quando_decide": certo / (n - inc) if n - inc else None}


saida = {"parametros": {"corte": CORTE, "turnos": TURNOS, "semente": SEMENTE},
         "particao": {"torneios_treino": len(treino_t), "torneios_teste": len(teste_t),
                      "treino_ate": max(data_t[x] for x in treino_t), "teste_desde": min(data_t[x] for x in teste_t)}}

# ------------------------------------------------------------------ logs: cartas reveladas por turno
nick = (t.config.ler_config() or {}).get("nick", "")
deck_arq = {r["id"]: r["arquetipo"] for r in B.consultar("SELECT id, arquetipo FROM meus_decks")}
deck_lista = {r["id"]: r["lista"] for r in B.consultar("SELECT id, lista FROM meus_decks")}
jogos = []          # (capturada_em, dono_do_log, {jogador: {turno: set(cartas)}}, deck_id)
for r in B.consultar("SELECT capturada_em, dono, deck_id, dados_json FROM partidas ORDER BY capturada_em, id"):
    try:
        d = json.loads(r["dados_json"] or "{}")
    except ValueError:
        continue
    res = d.get("resumo") or {}
    eu = res.get("exportou") or (r["dono"] or nick)
    por_turno = defaultdict(dict)
    for e in d.get("eventos") or []:
        c, j = e.get("carta"), e.get("jogador")
        if c and j and not C.eh_energia_basica(c):
            por_turno[j].setdefault(c, e.get("turno") or 0)                 # 1º turno em que a carta apareceu
    jogos.append((r["capturada_em"], eu, por_turno, r["deck_id"]))


def vistas_ate(primeira_vez: dict, turno):
    return {c for c, tt in primeira_vez.items() if turno is None or tt <= turno}


# k médio (cartas distintas reveladas) por turno, em TODOS os logs e jogadores
k_todos = {T_: [] for T_ in TURNOS}
for _, _, pt, _ in jogos:
    for j, prim in pt.items():
        for T_ in TURNOS:
            k_todos[T_].append(len(vistas_ate(prim, T_)))
saida["k_medio_todos_logs"] = {T_: round(sum(v) / len(v), 2) for T_, v in k_todos.items() if v}

# chance de revelação medida nas partidas com lista conhecida, por (categoria, cópias, turno)
contagem = defaultdict(lambda: [0, 0])
rotulados = [(cap, eu, pt[eu], did) for cap, eu, pt, did in jogos if did in deck_lista and eu in pt]
for _, _, prim, did in rotulados:
    itens, _ = D.ler_lista(deck_lista[did])
    copias = Counter()
    for it in itens:
        if not C.eh_energia_basica(it["nome"]):
            copias[it["nome"]] += it["qtd"]
    revel = {norm(c): tt for c, tt in prim.items()}
    for nome, q in copias.items():
        for T_ in TURNOS:
            ch = (categoria(nome), balde(q), T_)
            contagem[ch][0] += norm(nome) in revel and revel[norm(nome)] <= T_
            contagem[ch][1] += 1
p_revel = {ch: v[0] / v[1] for ch, v in contagem.items() if v[1]}


def p_carta(cat, q, T_):
    for qq in (balde(q), 4, 3, 2, 1):                                     # cópias sem medida: a mais próxima
        if (cat, qq, T_) in p_revel:
            return p_revel[(cat, qq, T_)]
    return sum(v for (c, _, tt), v in p_revel.items() if tt == T_) / max(1, sum(1 for (_, _, tt) in p_revel if tt == T_))


# reescala por turno: média de k da lista rotulada (pelo modelo) -> média de k de todos os logs
escala = {}
for T_ in TURNOS:
    if rotulados:
        itens, _ = D.ler_lista(deck_lista[rotulados[0][3]])
        cop = Counter()
        for it in itens:
            if not C.eh_energia_basica(it["nome"]):
                cop[it["nome"]] += it["qtd"]
        esperado = sum(p_carta(categoria(n), q, T_) for n, q in cop.items())
        escala[T_] = (saida["k_medio_todos_logs"].get(T_, esperado) / esperado) if esperado else 1.0
    else:
        escala[T_] = 1.0
saida["modelo_revelacao"] = {"partidas_rotuladas": len(rotulados),
                             "p_revelacao": {f"{c}|{q}|T{T_}": round(v, 3) for (c, q, T_), v in sorted(p_revel.items())},
                             "escala_por_turno": {T_: round(v, 3) for T_, v in escala.items()},
                             "aviso": "medido em 1 deck de 1 jogador; reescalado ao nº médio de cartas reveladas em todos os logs"}

# ------------------------------------------------------------------ PARTE S (sintética realista)
cad_r, cad_t = montar_modelos(treino_t)
teste = [L for (tid, _), L in sorted(listas.items()) if tid in teste_t and L["cartas"]]
decks_treino = set(cad_r)
saida["particao"].update(listas_teste=len(teste), listas_treino=sum(1 for (tid, _) in listas if tid in treino_t),
                         listas_teste_com_deck_fora_do_treino=sum(L["arq"] not in decks_treino for L in teste),
                         decks_no_cadastro_todos=len(cad_t), decks_no_cadastro_treino=len(cad_r))
print(f"PARTE S: {len(teste)} listas de teste ({len(teste_t)} torneios desde {saida['particao']['teste_desde']}); "
      f"treino {len(treino_t)} torneios até {saida['particao']['treino_ate']}. "
      f"{saida['particao']['listas_teste_com_deck_fora_do_treino']} listas de teste têm deck que não existe no treino.")
linhas = []        # (turno, torneio, verdade, k, {metodo: previsto}, conf)
for L in teste:
    for T_ in TURNOS:
        vistas = [c for c, q in sorted(L["cartas"].items()) if rng.random() < min(1.0, p_carta(categoria(c), q, T_) * escala[T_])]
        if not vistas:
            linhas.append((T_, L["torneio"], L["arq"], 0, {m: "" for m in METODOS}, 0.0))
            continue
        prev, conf = avaliar(vistas, cad_r, cad_t)
        linhas.append((T_, L["torneio"], L["arq"], len(vistas), prev, conf))

res_s = {"por_turno": {}, "por_k": {}, "comparacoes": {}, "por_arquetipo": {}, "fora_do_treino": {}}
print("\nturno |  k méd | " + " | ".join(f"{m[:14]:>14}" for m in METODOS[:6]) + "   (acurácia; inconclusivo conta como erro)")
for T_ in TURNOS:
    ls = [x for x in linhas if x[0] == T_]
    res_s["por_turno"][T_] = {m: metricas([(v, p[m]) for _, _, v, _, p, _ in ls]) for m in METODOS}
    res_s["por_turno"][T_]["k_medio"] = sum(x[3] for x in ls) / len(ls)
    print(f"  {T_:3} | {res_s['por_turno'][T_]['k_medio']:5.1f}  | " +
          " | ".join(f"{100 * res_s['por_turno'][T_][m]['acuracia']:13.1f}%" for m in METODOS[:6]))
for nome, f in (("0", lambda k: k == 0), ("1-2", lambda k: 1 <= k <= 2), ("3-5", lambda k: 3 <= k <= 5),
                ("6-9", lambda k: 6 <= k <= 9), ("10+", lambda k: k >= 10)):
    ls = [x for x in linhas if f(x[3])]
    if ls:
        res_s["por_k"][nome] = {m: metricas([(v, p[m]) for _, _, v, _, p, _ in ls]) for m in METODOS}
for T_ in TURNOS:
    ls = [x for x in linhas if x[0] == T_]
    for a, b in (("programa", "nb2"), ("nb2", "icones"), ("nb2_prior_uniforme", "nb2"), ("icones_cadastro_todos", "icones")):
        r = T.diferenca_pareada([(tid, 1 - (p[a] == v), 1 - (p[b] == v)) for _, tid, v, _, p, _ in ls], 1000, SEMENTE)
        res_s["comparacoes"][f"T{T_}:{a}-{b}"] = {"diferenca_erro": r["estimativa"], "ic95": [r["baixo"], r["alto"]],
                                                    "provavel": r["provavel"], "torneios": r["grupos"]}
fora = [x for x in linhas if x[2] not in decks_treino]
res_s["fora_do_treino"] = {m: metricas([(v, p[m]) for _, _, v, _, p, _ in fora]) for m in METODOS} if fora else {}
comuns = [a for a, _ in Counter(L["arq"] for L in teste).most_common(10)]
for a in comuns:
    ls = [x for x in linhas if x[2] == a and x[0] in (2, 4)]
    res_s["por_arquetipo"][a] = {"n": len(ls), **{m: round(sum(p[m] == a for *_, p, _ in ls) / len(ls), 3)
                                                     for m in ("icones", "nb2", "programa")}}
mat = defaultdict(Counter)
for T_, _, v, _, p, _ in linhas:
    if T_ == 2:
        mat[v if v in comuns else "(outros)"][p["programa"] if p["programa"] in comuns or not p["programa"]
                                              else "(outros)"] += 1
res_s["matriz_confusao_programa_T2"] = {v: dict(c) for v, c in mat.items()}
pares_conf = [(conf, 1 if p["nb2"] == v else 0) for _, _, v, k, p, conf in linhas if p["nb2"]]
grupos_conf = [tid for _, tid, v, k, p, conf in linhas if p["nb2"]]
res_s["calibracao_nb2"] = T.calibracao_detalhada(pares_conf, grupos_conf, repeticoes=300, semente=SEMENTE)
res_s["calibracao_nb2_por_turno"] = T.calibracao_por_grupo([(f"T{T_}", conf, 1 if p["nb2"] == v else 0)
                                                           for T_, _, v, _, p, conf in linhas if p["nb2"]])
res_s["calibracao_nb2_por_arquetipo"] = T.calibracao_por_grupo([(v if v in comuns else "(outros)", conf, 1 if p["nb2"] == v else 0)
                                                               for _, _, v, _, p, conf in linhas if p["nb2"]], minimo=50)
saida["parte_s"] = res_s
c = res_s["calibracao_nb2"]
print(f"\nCalibração do NB2 (cartas vistas): ECE10 {c['por_faixas'][10]['ece_largura']:.3f} "
      f"[{c['ece10_ic95']['baixo']:.3f}; {c['ece10_ic95']['alto']:.3f}], piso de ruído {c['por_faixas'][10]['piso_ruido_medio']:.3f}; "
      f"inclinação {c['recalibracao']['inclinacao']:.2f} ± {c['recalibracao']['ep_inclinacao']:.2f}")
for k_, v in res_s["comparacoes"].items():
    print(f"   {k_:34} {v['diferenca_erro']:+.3f} [{v['ic95'][0]:+.3f}; {v['ic95'][1]:+.3f}] {'provável' if v['provavel'] else 'sem diferença clara'}")

# ------------------------------------------------------------------ PARTE R (real)
D.banco.consultar = consultar_original
res_r = {}
if rotulados:
    primeira = min(cap for cap, *_ in rotulados)[:10]
    anteriores = {x for x in ordem if data_t[x] < primeira}
    cad_r2, cad_t2 = montar_modelos(anteriores)
    linhas_r = []
    for cap, eu, prim, did in rotulados:
        verdade = deck_arq.get(did, "")
        for T_ in TURNOS + (None,):
            vistas = sorted(vistas_ate(prim, T_))
            prev, conf = avaliar(vistas, cad_r2, cad_r2) if vistas else ({m: "" for m in METODOS}, 0.0)
            linhas_r.append(("fim" if T_ is None else T_, cap[:10], verdade, len(vistas), prev, conf))
    res_r = {"partidas": len(rotulados), "arquetipos_distintos": len({deck_arq.get(d) for *_, d in rotulados}),
             "torneios_no_treino": len(anteriores), "treino_ate": max(data_t[x] for x in anteriores) if anteriores else None,
             "primeira_partida": primeira, "por_turno": {}}
    print(f"\nPARTE R: {len(rotulados)} partidas reais com gabarito ({res_r['arquetipos_distintos']} arquétipo), "
          f"modelos com {len(anteriores)} torneios até {res_r['treino_ate']}")
    for T_ in TURNOS + ("fim",):
        ls = [x for x in linhas_r if x[0] == T_]
        linha = {"k_medio": sum(x[3] for x in ls) / len(ls)}
        for m in ("icones", "nb2", "programa", "nb2_abstem", "nb2_prior_uniforme"):
            ac = [1 if p[m] == v else 0 for _, _, v, _, p, _ in ls]
            b = T.bootstrap_agrupado({i: [a] for i, a in enumerate(ac)}, lambda xs: sum(xs) / len(xs), 1000, SEMENTE) \
                if len(set(ac)) > 1 else {"baixo": sum(ac) / len(ac), "alto": sum(ac) / len(ac)}
            linha[m] = {"revocacao": sum(ac) / len(ac), "ic95": [b["baixo"], b["alto"]],
                        "inconclusivo": sum(p[m] == "" for *_, p, _ in ls) / len(ls)}
        res_r["por_turno"][T_] = linha
        print(f"   turno {T_!s:3}: k {linha['k_medio']:4.1f}  " + "  ".join(
            f"{m} {100 * linha[m]['revocacao']:5.1f}%" for m in ("icones", "nb2", "programa", "nb2_prior_uniforme")))
saida["parte_r"] = res_r

impr = T.impressao_objeto(sorted((L["torneio"], L["arq"], sorted(L["cartas"].items())) for L in teste))
arq = T.registrar("a8_identificacao_cartas_vistas", saida, t.pasta, AQUI / "resultados", semente=SEMENTE,
                  parametros={"corte": CORTE, "turnos": TURNOS, "confianca_nb": D.CONFIANCA_NB, "beta_nb": D.BETA_NB},
                  filtros={"listas": "com arquétipo; sem Energia Básica", "parte_r": "partidas ligadas a Meus decks"},
                  dados_usados={"listas_teste": len(teste), "periodo_teste": [saida["particao"]["teste_desde"], max(data_t.values())],
                                "impressao_listas_teste": impr, "partidas_rotuladas": len(rotulados)},
                  copia=t.identificacao)
print(f"\nresultado gravado em {arq.name}")
