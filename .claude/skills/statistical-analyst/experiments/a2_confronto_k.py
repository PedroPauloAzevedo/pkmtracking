"""
AUDITORIA A2 — confronto ajustado (estrategia.confrontos_ajustados): o k = 24 ainda é bom? Com poucos jogos, ganha do 50%?
Mesmo desenho do experimento 3 (70% dos torneios mais antigos treinam; só W/L; sem espelho), mas:
  - mede TODOS os k no teste (o e3 só mostra o k escolhido) e a diferença para k = 24;
  - faixa de incerteza por bootstrap AGRUPADO POR TORNEIO para "ajustada − chute de 50%" e "k = 16 − k = 24";
  - usa a função do programa (estrategia.confrontos_ajustados), não uma cópia.
Só lê. Uso:  python -I a2_confronto_k.py <CÓPIA do programa>
"""
import math
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
ps = t.banco.consultar(
    "SELECT p.arq1, p.arq2, p.res1, t.data, t.id FROM t_partidas p JOIN torneios t ON t.id = p.torneio "
    "WHERE p.arq1 != '' AND p.arq2 != '' AND p.arq1 != p.arq2 AND p.res1 IN ('W', 'L') "
    "AND COALESCE(t.formato, '') IN ('', 'standard')")
ps = [dict(p) for p in ps]
ids = [i for i, _ in sorted({p["id"]: p["data"] or "" for p in ps}.items(), key=lambda x: x[1])]
corte = int(len(ids) * 0.7)
tr_ids = set(ids[:corte])
treino = [p for p in ps if p["id"] in tr_ids]
teste = [p for p in ps if p["id"] not in tr_ids]
decks = sorted({p["arq1"] for p in ps} | {p["arq2"] for p in ps})
n_treino = defaultdict(int)
for p in treino:
    n_treino[(p["arq1"], p["arq2"])] += 1
    n_treino[(p["arq2"], p["arq1"])] += 1
print(f"{len(ps)} partidas, {len(ids)} torneios; treino {len(treino)}, teste {len(teste)}; {len(decks)} decks")

KS = (1, 4, 8, 12, 16, 24, 32, 48, 64, 96)
prev = {}
for k in KS:
    c = t.estrategia.confrontos_ajustados(treino, decks, k)
    prev[k] = [min(max(c[(p["arq1"], p["arq2"])]["p"], 0.01), 0.99) for p in teste]
y = [1 if p["res1"] == "W" else 0 for p in teste]


def perda(q, yy):
    return -(yy * math.log(q) + (1 - yy) * math.log(1 - q))


res = {"k": {}, "partidas_teste": len(teste)}
print("\n   k | log-loss (todas) | log-loss (< 10 jogos no treino) | (≥ 30 jogos)")
faixas = {"todas": lambda p: True, "poucos": lambda p: n_treino[(p["arq1"], p["arq2"])] < 10,
          "muitos": lambda p: n_treino[(p["arq1"], p["arq2"])] >= 30}
for k in KS:
    linha = {}
    for nome, f in faixas.items():
        idx = [i for i, p in enumerate(teste) if f(p)]
        linha[nome] = sum(perda(prev[k][i], y[i]) for i in idx) / len(idx)
        linha["n_" + nome] = len(idx)
    res["k"][k] = linha
    print(f"  {k:2} |      {linha['todas']:.4f}      |            {linha['poucos']:.4f}             |  {linha['muitos']:.4f}")
print(f"  chute 50% = {math.log(2):.4f}   (partidas: todas {res['k'][24]['n_todas']}, poucos {res['k'][24]['n_poucos']}, "
      f"muitos {res['k'][24]['n_muitos']})")

comp = {}
for nome, f in faixas.items():
    idx = [i for i, p in enumerate(teste) if f(p)]
    comp[f"k24_menos_50pct_{nome}"] = T.diferenca_pareada([(teste[i]["id"], perda(prev[24][i], y[i]), math.log(2)) for i in idx], 2000, 11)
    comp[f"k16_menos_k24_{nome}"] = T.diferenca_pareada([(teste[i]["id"], perda(prev[16][i], y[i]), perda(prev[24][i], y[i])) for i in idx], 2000, 11)
print("\nDiferenças de log-loss por partida (negativo = o primeiro é melhor), faixa de 95% por bootstrap de torneios:")
for nome, r in comp.items():
    print(f"   {nome:28} {r['estimativa']:+.4f}  [{r['baixo']:+.4f}, {r['alto']:+.4f}]  {'provável' if r['provavel'] else 'sem diferença clara'}"
          f"  ({r['grupos']} torneios)")
res["comparacoes"] = comp

# calibração da ajustada (k = 24) no teste. Cada partida entra PELOS DOIS LADOS: nos torneios do Labs o jogador 1 é quase
# sempre quem venceu (a1), então a tabela vista só pelo lado do jogador 1 pareceria descalibrada sem estar. (O log-loss de um
# modelo simétrico é o mesmo pelos dois lados; a tabela de calibração, não.)
cal = T.calibracao(list(zip(prev[24], y)) + [(1 - q, 1 - yy) for q, yy in zip(prev[24], y)], 10)
res["calibracao_k24"] = cal
print(f"\nCalibração (k = 24): erro médio |previsto − real| = {cal['ece']:.3f}")
for f in cal["faixas"]:
    print(f"   {f['de']:.1f}–{f['ate']:.1f}: n {f['n']:5}  previsto {f['previsto']:.3f}  real {f['real']:.3f}")
arq = T.registrar("a2_confronto_k", res, t.pasta, AQUI / "resultados", semente=11, parametros={"ks": KS, "corte": 0.7})
print(f"\nresultado gravado em {arq.name}")
