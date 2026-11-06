"""
AUDITORIA A1 — os dados dos torneios: seleção das listas, empates, lado do jogador 1 e dependência entre partidas.
Perguntas:
  1. Quem tem lista importada vence mais que o resto? (viés de seleção das análises que usam listas)
  2. Quantos empates há, por fonte?  3. Por que res1 tem muito mais W que L?
  4. Quanto as partidas de um mesmo jogador "andam juntas" (ICC) e qual o efeito de desenho?
Só lê. Uso:  python -I a1_dados_e_selecao.py <CÓPIA do programa>
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
B = t.banco
res = {}

# 1. seleção: placar final de quem tem lista × quem não tem, por fonte e por deck
com_lista = {(r["torneio"], r["labs_id"]) for r in B.consultar("SELECT DISTINCT torneio, labs_id FROM t_listas")}
fonte = {r["id"]: (r["fonte"] or "labs") for r in B.consultar("SELECT id, fonte FROM torneios")}
agg = defaultdict(lambda: [0, 0, 0, 0])  # v, n, jogadores, com resultado
por_deck = defaultdict(lambda: {"com": [0, 0], "todos": [0, 0]})
for j in B.consultar("SELECT torneio, labs_id, arquetipo, v, d, e FROM t_jogadores"):
    n = (j["v"] or 0) + (j["d"] or 0) + (j["e"] or 0)
    tem = (j["torneio"], j["labs_id"]) in com_lista
    a = agg[(fonte.get(j["torneio"]), tem)]
    a[0] += j["v"] or 0
    a[1] += n
    a[2] += 1
    if j["arquetipo"]:
        por_deck[j["arquetipo"]]["todos"][0] += j["v"] or 0
        por_deck[j["arquetipo"]]["todos"][1] += n
        if tem:
            por_deck[j["arquetipo"]]["com"][0] += j["v"] or 0
            por_deck[j["arquetipo"]]["com"][1] += n
res["selecao"] = {f"{f}/{'com lista' if tem else 'sem lista'}": {"jogadores": a[2], "partidas": a[1],
                                                                   "taxa": round(100 * a[0] / a[1], 1) if a[1] else None}
                  for (f, tem), a in sorted(agg.items(), key=str)}
print("1. Taxa de vitória pelo placar final do jogador")
for k, v in res["selecao"].items():
    print(f"   {k:22} {v['jogadores']:6} jogadores  {v['partidas']:7} partidas  {v['taxa']}%")
grandes = sorted(por_deck, key=lambda a: -por_deck[a]["todos"][1])[:12]
res["selecao_por_deck"] = {}
print("\n   Deck (12 mais jogados)        todos     só com lista   diferença (pp)")
for a in grandes:
    d = por_deck[a]
    tt = 100 * d["todos"][0] / d["todos"][1]
    tc = 100 * d["com"][0] / d["com"][1] if d["com"][1] else float("nan")
    res["selecao_por_deck"][a] = {"todos": round(tt, 1), "com_lista": round(tc, 1), "n_todos": d["todos"][1], "n_com": d["com"][1]}
    print(f"   {a:28} {tt:5.1f}%       {tc:5.1f}%        {tc - tt:+5.1f}")

# 2 e 3. empates e lado do jogador 1
lado = defaultdict(Counter)
por_rodada = defaultdict(Counter)
for r in B.consultar("SELECT p.torneio, p.rodada, p.res1, p.arq2, p.j2 FROM t_partidas p"):
    f = fonte.get(r["torneio"])
    lado[f][r["res1"]] += 1
    lado[f]["sem_adversario"] += not r["j2"]
    try:
        por_rodada[min(int(r["rodada"]), 20)][r["res1"]] += 1
    except (TypeError, ValueError):
        por_rodada["?"][r["res1"]] += 1
res["resultados_por_fonte"] = {f: dict(c) for f, c in lado.items()}
print("\n2/3. res1 por fonte (W = jogador 1 venceu):")
for f, c in lado.items():
    tot = c["W"] + c["L"] + c["T"]
    print(f"   {f:7} W {c['W']:6}  L {c['L']:6}  T {c['T']:5} ({100 * c['T'] / tot:4.1f}% empates)  sem adversário: {c['sem_adversario']}")
print("   por rodada (W / L / T):", {k: (v["W"], v["L"], v["T"]) for k, v in sorted(por_rodada.items(), key=lambda x: str(x[0]).zfill(3))})
res["por_rodada"] = {str(k): dict(v) for k, v in por_rodada.items()}

# 4. dependência: resultados de cada jogador com lista (partida a partida, sem empates)
nome_para_id = {(r["torneio"], r["nome_norm"]): r["labs_id"] for r in B.consultar("SELECT torneio, nome_norm, labs_id FROM t_jogadores")}
grupos = defaultdict(list)
for r in B.consultar("SELECT torneio, j1, j2, res1 FROM t_partidas WHERE res1 IN ('W','L')"):
    for jog, ganhou in ((r["j1"], r["res1"] == "W"), (r["j2"], r["res1"] == "L")):
        ch = (r["torneio"], nome_para_id.get((r["torneio"], jog)))
        if ch in com_lista:
            grupos[ch].append(1 if ganhou else 0)
gs = [g for g in grupos.values() if len(g) >= 2]
icc = T.icc_binario(gs)
m = sum(len(g) for g in gs) / len(gs)
ef = T.efeito_desenho(m, icc)
res["dependencia"] = {"jogadores": len(gs), "partidas_por_jogador": round(m, 2), "icc": round(icc, 4), "efeito_desenho": round(ef, 3)}
print(f"\n4. Jogadores com lista: {len(gs)}, {m:.1f} partidas cada (W/L). ICC = {icc:.3f} -> efeito de desenho {ef:.2f}:")
print(f"   {ef:.2f} partidas valem como 1 independente; faixas e valores-p feitos por partida ficam ~{100 * (1 - 1 / ef ** 0.5):.0f}% estreitas demais.")

arq = T.registrar("a1_dados_e_selecao", res, t.pasta, AQUI / "resultados")
print(f"\nresultado gravado em {arq.name}")
