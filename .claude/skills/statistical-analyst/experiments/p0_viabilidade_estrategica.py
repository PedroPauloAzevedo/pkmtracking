"""
P0 (06/11/2026) — VIABILIDADE da análise estratégica com os logs do Coletor (prêmios, corrida, prêmios checados, disrupção, mill,
sequência). Não valida nenhum indicador estratégico: mede o que os registros PERMITEM reconstruir, para a matriz de observabilidade
(`knowledge/STRATEGIC_CONCEPTS.md`) e o desenho dos experimentos P1–P7 (`knowledge/PRIZE_ANALYSIS.md`, `CONTROL_AND_DISRUPTION.md`,
`DECISION_ANALYSIS.md`). Usa `replay.gerar` e `leitor` do Coletor pela ponte (só leitura).

  P1  rota de prêmios executada: sequência de "took N" de cada jogador (observado) e coerência da atribuição de prêmios por nocaute
      (`resumo.nocautes`, inferido) com o valor esperado pelo nome (Mega ... ex = 3, ... ex = 2, resto = 1; regra sem efeitos de carta)
  P2  corrida: quem tem mais prêmios pegos ao fim de cada turno × vencedor (descritivo; desistências dominam o fim das partidas)
  P3  prêmios checados: nas partidas com lista conhecida (Meus decks) e mão inicial listada (sem mulligan), os prêmios pegos por quem
      exportou são uma amostra dos 6 prêmios, que são 6 das 53 cartas fora da mão → hipergeométrica. Compara contagens observadas
      com as esperadas por classe de cópias restantes (1..4). Premissa: o jogador não escolhe QUAL prêmio pegar (viradas).
  D   frequência de cartas de disrupção conhecidas, partidas terminadas por deck acabado, tamanho dos turnos (sequência)
Semente: não há sorteio. Saída sem nicks (agregados).  Uso:  python -I p0_viabilidade_estrategica.py <CÓPIA do programa>
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
B, D, R = t.banco, t.decks, t.replay
regras = t.config.ler_regras()
C = t.cartas

# cartas de disrupção/controle conhecidas no Standard recente (lista de trabalho, não exaustiva; categoria entre parênteses)
DISRUPCAO = {"Iono": "mão", "Judge": "mão", "Unfair Stamp": "mão", "Xerosic's Machinations": "mão", "Eri": "mão",
             "Crushing Hammer": "energia", "Enhanced Hammer": "energia", "Team Rocket's Watchtower": "habilidade (estádio)",
             "Path to the Peak": "habilidade (estádio)", "Boss's Orders": "banco (puxar)", "Prime Catcher": "banco (puxar)",
             "Counter Catcher": "banco (puxar)", "Lost Vacuum": "ferramenta/estádio", "Tool Scrapper": "ferramenta"}


def valor_premio(nome):
    n = nome or ""
    if n.startswith("Mega ") and n.endswith(" ex"):
        return 3
    if n.endswith(" ex"):
        return 2
    return 1


res = {"partidas": 0, "p1": {}, "p2": {}, "p3": {}, "d": {}}
mapas = Counter()
ko_ok = ko_total = 0
ko_div = Counter()
lider = defaultdict(lambda: [0, 0])          # turno -> [líder venceu, partidas com líder]
disr = Counter()
disr_partidas = Counter()
eventos_por_turno = []
p3_linhas = []                                # (classe K, k pegos, observado, esperado, variancia)
p3_partidas = p3_completas = 0
p3_ao_menos_um = []                           # (prob prevista, aconteceu) para cartas com K>=1 nas partidas com 6 prêmios pegos
deck_lista = {r["id"]: r["lista"] for r in B.consultar("SELECT id, lista FROM meus_decks")}

for p in B.consultar("SELECT id, texto, dados_json, deck_id FROM partidas ORDER BY id"):
    try:
        dados = json.loads(p["dados_json"] or "{}")
    except ValueError:
        continue
    r = dados.get("resumo") or {}
    if not r.get("vencedor"):
        continue
    res["partidas"] += 1
    rep = R.gerar(p["texto"], regras)
    js = rep["jogadores"]
    # ---- P1: rota executada = sequência de prêmios pegos (das quedas em mesa[j]["premios"] entre quadros)
    antes = {j: 6 for j in js}
    seq = {j: [] for j in js}
    fim_turno = defaultdict(dict)
    for q in rep["quadros"]:
        for j in js:
            agora = q["estado"]["mesa"][j]["premios"]
            if agora < antes[j]:
                seq[j].append(antes[j] - agora)
            antes[j] = agora
            fim_turno[q["turno"]][j] = agora
    v = r["vencedor"]
    if r.get("motivo") == "Pegou todos os prêmios" and v in seq:
        mapas["-".join(str(x) for x in seq[v])] += 1
    for k in r.get("nocautes") or []:
        ko_total += 1
        esp = valor_premio(k.get("carta"))
        ok = k.get("premios") == esp
        ko_ok += ok
        if not ok:
            ko_div[f"esperado {esp}, registrado {k.get('premios')}"] += 1
    # ---- P2: líder em prêmios pegos ao fim de cada turno
    for turno, m in fim_turno.items():
        if len(m) == 2 and turno >= 1:
            a, b = js
            if m[a] != m[b]:
                quem = a if m[a] < m[b] else b
                lider[turno][1] += 1
                lider[turno][0] += quem == v
    # ---- D: disrupção, deck acabado, eventos por turno
    vistas_d = Counter()
    for e in dados.get("eventos") or []:
        c = e.get("carta") or ""
        if e.get("tipo") == "jogada" and c in DISRUPCAO:
            disr[DISRUPCAO[c]] += 1
            vistas_d[DISRUPCAO[c]] += 1
    for cat in vistas_d:
        disr_partidas[cat] += 1
    por_turno = Counter((e.get("turno"), e.get("jogador")) for e in dados.get("eventos") or [] if e.get("tipo") in ("jogada", "compra", "energia", "evolucao", "ataque", "recuo"))
    eventos_por_turno.extend(por_turno.values())
    # ---- P3: prêmios checados (quem exportou, lista conhecida, sem mulligan)
    exp = rep.get("exportou")
    if not (exp and p["deck_id"] in deck_lista):
        continue
    texto = p["texto"]
    if re.search(rf"^{re.escape(exp)} took a mulligan", texto, re.M):
        continue
    mm = re.search(rf"^{re.escape(exp)} drew 7 cards for the opening hand\.\s*\n- 7 drawn cards\.\s*\n\s*•\s*(.+)$", texto, re.M)
    if not mm:
        continue
    mao = Counter(x.strip() for x in mm.group(1).split(","))
    itens, _ = D.ler_lista(deck_lista[p["deck_id"]])
    deck = Counter()
    for it in itens:
        deck[it["nome"]] += it["qtd"]
    if sum(deck.values()) != 60 or any(mao[c] > deck.get(c, 0) for c in mao):
        continue                                  # lista não confere com a mão: fora (gabarito duvidoso)
    primeiro = rep["quadros"][0]["estado"]["mesa"][exp]
    pegos = Counter()
    for q in rep["quadros"]:
        d = q["destaque"]
        if d.get("tipo") == "premio" and d.get("jogador") == exp and d.get("carta"):
            pegos[d["carta"]] += 1
    k = sum(pegos.values())
    if not k:
        continue
    p3_partidas += 1
    N = 53
    for nome, c in deck.items():
        K = c - mao.get(nome, 0)
        if K <= 0:
            continue
        e_ = k * K / N
        var = k * (K / N) * (1 - K / N) * (N - k) / (N - 1)
        p3_linhas.append((min(K, 4), k, pegos.get(nome, 0), e_, var))
    if k == 6:
        p3_completas += 1
        for nome, c in deck.items():
            K = c - mao.get(nome, 0)
            if K > 0:
                prev = 1 - math.comb(N - K, 6) / math.comb(N, 6)
                p3_ao_menos_um.append((prev, 1 if pegos.get(nome, 0) else 0))

res["p1"] = {"mapas_executados_por_quem_venceu_por_premios": dict(mapas.most_common()),
             "nocautes": ko_total, "premios_iguais_ao_valor_pelo_nome": ko_ok,
             "fracao_coerente": round(ko_ok / ko_total, 3) if ko_total else None, "divergencias": dict(ko_div.most_common())}
res["p2"] = {f"T{tu}": {"partidas_com_lider": n, "lider_venceu": v_, "taxa": round(v_ / n, 3), "wilson": t.analises.wilson(v_, n)}
             for tu, (v_, n) in sorted(lider.items()) if n >= 5}
if p3_linhas:
    por_k = defaultdict(lambda: [0, 0.0, 0.0, 0])
    for K, k, o, e_, var in p3_linhas:
        x = por_k[K]
        x[0] += o
        x[1] += e_
        x[2] += var
        x[3] += 1
    res["p3"] = {"partidas": p3_partidas, "partidas_com_6_premios_revelados": p3_completas,
                 "por_copias_restantes": {K: {"cartas_partida": x[3], "observado": x[0], "esperado": round(x[1], 2),
                                               "z_aprox": round((x[0] - x[1]) / math.sqrt(x[2]), 2) if x[2] else None}
                                          for K, x in sorted(por_k.items())},
                 "total_observado": sum(x[0] for x in por_k.values()), "total_esperado": round(sum(x[1] for x in por_k.values()), 2)}
    if p3_ao_menos_um:
        res["p3"]["ao_menos_uma_copia_premiada"] = {"n": len(p3_ao_menos_um), "brier": round(T.brier(p3_ao_menos_um), 4),
                                                   "previsto_medio": round(sum(a for a, _ in p3_ao_menos_um) / len(p3_ao_menos_um), 4),
                                                   "real": round(sum(b for _, b in p3_ao_menos_um) / len(p3_ao_menos_um), 4)}
motivos = Counter(json.loads(x["dados_json"])["resumo"].get("motivo") for x in B.consultar("SELECT dados_json FROM partidas"))
eventos_por_turno.sort()
res["d"] = {"motivos_de_fim": dict(motivos), "jogadas_de_disrupcao_por_categoria": dict(disr),
            "partidas_com_categoria": dict(disr_partidas), "acoes_por_turno_mediana": eventos_por_turno[len(eventos_por_turno) // 2] if eventos_por_turno else None,
            "acoes_por_turno_p90": eventos_por_turno[int(0.9 * len(eventos_por_turno))] if eventos_por_turno else None,
            "lista_disrupcao_usada": DISRUPCAO}

print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:6000])
arq = T.registrar("p0_viabilidade_estrategica", res, t.pasta, AQUI / "resultados", semente=None,
                  parametros={"valor_premio": "Mega ex 3, ex 2, resto 1", "N_p3": 53},
                  filtros={"partidas": "com vencedor", "p3": "lista ligada, mão inicial listada, sem mulligan, lista de 60 que contém a mão"},
                  dados_usados={"partidas": res["partidas"], "p3_partidas": p3_partidas}, copia=t.identificacao)
print(f"resultado gravado em {arq.name}")
