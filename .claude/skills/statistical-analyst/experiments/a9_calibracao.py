"""
AUDITORIA A9 (06/11/2026, rodada de "hardening") — calibração a fundo das previsões de partida (confronto ajustado).
O a2 mostrou ECE ≈ 1,5 pp para o k = 24. Um ECE baixo sozinho não prova calibração (depende do nº de faixas, quase todas as
previsões ficam perto de 50%, há um piso de ruído). Aqui, no MESMO desenho do a2 (70% dos torneios mais antigos treinam; só W/L;
sem espelho; cada partida pelos DOIS lados, porque no Labs o jogador 1 é quase sempre quem venceu — a1):
  - log-loss, Brier e ECE com 5/10/15/20 faixas, por largura e por massa, observações por faixa, piso de ruído e faixa de 95%
    (bootstrap por TORNEIO) — `sa_tools.calibracao_detalhada`;
  - recalibração logística (inclinação/intercepto);
  - calibração "no atacado" por arquétipo (10 mais jogados), por período (cada torneio de teste, em ordem de data) e por grupo de
    jogadores (com lista = topo × sem lista; Labs × online);
  - comparação entre modelos nos mesmos dados: k = 24 (programa), k = 16, k = 1 (quase a taxa bruta), força geral (Bradley-Terry)
    e chute de 50%; diferença pareada de log-loss com bootstrap por torneio.
Nenhuma métrica do programa muda: isto só mede. Só lê. Semente 909.
Uso:  python -I a9_calibracao.py <CÓPIA do programa>
"""
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

SEMENTE, CORTE = 909, 0.7
t = carregar(sys.argv[1])
E = t.estrategia
ps = [dict(p) for p in t.banco.consultar(
    "SELECT p.arq1, p.arq2, p.res1, p.j1, p.j2, t.data, t.id, COALESCE(t.fonte, 'labs') AS fonte "
    "FROM t_partidas p JOIN torneios t ON t.id = p.torneio "
    "WHERE p.arq1 != '' AND p.arq2 != '' AND p.arq1 != p.arq2 AND p.res1 IN ('W', 'L') "
    "AND COALESCE(t.formato, '') IN ('', 'standard')")]
ids = [i for i, _ in sorted({p["id"]: p["data"] or "" for p in ps}.items(), key=lambda x: (x[1], x[0]))]
tr_ids = set(ids[:int(len(ids) * CORTE)])
treino = [p for p in ps if p["id"] in tr_ids]
teste = [p for p in ps if p["id"] not in tr_ids]
decks = sorted({p["arq1"] for p in ps} | {p["arq2"] for p in ps})
com_lista = set()
nome_id = {(r["torneio"], r["nome_norm"]): r["labs_id"] for r in t.banco.consultar("SELECT torneio, nome_norm, labs_id FROM t_jogadores")}
for r in t.banco.consultar("SELECT DISTINCT torneio, labs_id FROM t_listas"):
    com_lista.add((r["torneio"], r["labs_id"]))

clip = lambda q: min(max(q, 0.01), 0.99)  # noqa: E731  (o mesmo corte do a2)
modelos = {}
for k in (24, 16, 1):
    c = E.confrontos_ajustados(treino, decks, k)
    modelos[f"k{k}"] = lambda a, b, c=c: clip(c[(a, b)]["p"])
s = E.forcas(treino)
modelos["forca_geral"] = lambda a, b: clip(s.get(a, 1.0) / (s.get(a, 1.0) + s.get(b, 1.0)))
modelos["chute_50"] = lambda a, b: 0.5

# cada partida pelos dois lados: (torneio, data, fonte, deck do lado, adversário, grupo do jogador do lado, resultado do lado)
lados = []
for p in teste:
    for a, b, jog, y in ((p["arq1"], p["arq2"], p["j1"], 1 if p["res1"] == "W" else 0),
                         (p["arq2"], p["arq1"], p["j2"], 1 if p["res1"] == "L" else 0)):
        grupo = "com_lista" if (p["id"], nome_id.get((p["id"], jog))) in com_lista else "sem_lista"
        lados.append((p["id"], p["data"], p["fonte"], a, b, grupo, y))
print(f"{len(ps)} partidas; treino {len(treino)} ({len(tr_ids)} torneios), teste {len(teste)} ({len(ids) - len(tr_ids)} torneios); "
      f"{len(lados)} previsões (dois lados)")

saida = {"particao": {"partidas_treino": len(treino), "partidas_teste": len(teste), "torneios_teste": len(ids) - len(tr_ids),
                      "previsoes": len(lados)}, "modelos": {}, "comparacoes": {}, "por_arquetipo": {}, "por_periodo": {},
         "por_grupo_jogador": {}, "por_fonte": {}}
prev = {m: [f(a, b) for _, _, _, a, b, _, _ in lados] for m, f in modelos.items()}
ys = [x[6] for x in lados]
grupos_torneio = [x[0] for x in lados]
print("\nmodelo       | log-loss | Brier  | ECE10 (largura) [faixa 95%] | piso ruído | ECE10 massa | inclinação ± ep | intercepto")
for m in modelos:
    pares = list(zip(prev[m], ys))
    if m == "chute_50":
        saida["modelos"][m] = {"logloss": T.logloss(pares), "brier": T.brier(pares)}
        print(f"{m:12} |  {saida['modelos'][m]['logloss']:.4f}  | {saida['modelos'][m]['brier']:.4f} | (constante: calibração não se aplica)")
        continue
    cd = T.calibracao_detalhada(pares, grupos_torneio, repeticoes=300, semente=SEMENTE)
    saida["modelos"][m] = cd
    f10 = cd["por_faixas"][10]
    rc = cd["recalibracao"]
    print(f"{m:12} |  {cd['logloss']:.4f}  | {cd['brier']:.4f} | {f10['ece_largura']:.4f} [{cd['ece10_ic95']['baixo']:.4f}; "
          f"{cd['ece10_ic95']['alto']:.4f}] |   {f10['piso_ruido_medio']:.4f}   |   {f10['ece_massa']:.4f}    | "
          f"{rc['inclinacao']:.2f} ± {rc['ep_inclinacao']:.2f}     | {rc['intercepto']:+.3f}")
print("\nSensibilidade do ECE ao nº de faixas (k24): " + "; ".join(
    f"{k} faixas: {v['ece_largura']:.4f} (massa {v['ece_massa']:.4f}, piso {v['piso_ruido_medio']:.4f}, menor faixa {v['n_min_largura']} obs.)"
    for k, v in saida["modelos"]["k24"]["por_faixas"].items()))


def perda(q, y):
    return -(y * math.log(q) + (1 - y) * math.log(1 - q))


print("\nDiferença de log-loss por previsão (negativo = o primeiro é melhor), faixa de 95% por bootstrap de torneios:")
for a, b in (("k24", "chute_50"), ("k24", "forca_geral"), ("k24", "k16"), ("k24", "k1")):
    r = T.diferenca_pareada([(g, perda(pa, y), perda(pb, y)) for g, pa, pb, y in zip(grupos_torneio, prev[a], prev[b], ys)], 1000, SEMENTE)
    saida["comparacoes"][f"{a}-{b}"] = {"estimativa": r["estimativa"], "ic95": [r["baixo"], r["alto"]], "provavel": r["provavel"]}
    print(f"   {a} − {b:12} {r['estimativa']:+.4f} [{r['baixo']:+.4f}; {r['alto']:+.4f}] {'provável' if r['provavel'] else 'sem diferença clara'}")

comuns = [d for d, _ in Counter(x[3] for x in lados).most_common(10)]
saida["por_arquetipo"] = T.calibracao_por_grupo([(x[3] if x[3] in comuns else "(outros)", q, x[6]) for x, q in zip(lados, prev["k24"])])
datas = {x[0]: x[1] for x in lados}
saida["por_grupo_jogador"] = T.calibracao_por_grupo([(x[5], q, x[6]) for x, q in zip(lados, prev["k24"])])


def dentro_do_grupo(rotulo):
    """Período e fonte contêm as DUAS pontas de cada partida: a média prevista e a real dão 50% por construção. Por isso, aqui
    se mede a calibração DENTRO do grupo (log-loss × chute, ECE de 5 faixas com piso, inclinação), não a média."""
    por = defaultdict(list)
    for x, q in zip(lados, prev["k24"]):
        por[rotulo(x)].append((q, x[6]))
    out = {}
    for g, pares in sorted(por.items()):
        rc = T.recalibracao_logistica(pares)
        e5 = T.ece(pares, 5)
        piso = []
        for i in range(100):
            rr = __import__("random").Random(SEMENTE + i)
            piso.append(T.ece([(q, 1 if rr.random() < q else 0) for q, _ in pares], 5)["ece"])
        out[g] = {"n": len(pares), "logloss": T.logloss(pares), "ganho_sobre_50": T.logloss(pares) - math.log(2),
                  "ece5": e5["ece"], "piso_ece5_p95": sorted(piso)[94], "inclinacao": rc["inclinacao"], "ep_inclinacao": rc["ep_inclinacao"]}
    return out


saida["por_periodo"] = dentro_do_grupo(lambda x: f"{datas[x[0]]} {x[0]}")
saida["por_fonte"] = dentro_do_grupo(lambda x: x[2])
for titulo, chave in (("período (torneio de teste)", "por_periodo"), ("fonte", "por_fonte")):
    print(f"\nPor {titulo} (calibração dentro do grupo; média é 50% por construção):")
    for g, v in saida[chave].items():
        print(f"   {g[:34]:34} n {v['n']:5}  log-loss {v['logloss']:.4f} ({v['ganho_sobre_50']:+.4f} × chute)  ECE5 {v['ece5']:.3f}"
              f" (piso p95 {v['piso_ece5_p95']:.3f})  inclinação {v['inclinacao']:.2f} ± {v['ep_inclinacao']:.2f}")
for titulo, chave in (("arquétipo", "por_arquetipo"), ("grupo de jogadores", "por_grupo_jogador")):
    fora = [g for g, v in saida[chave].items() if not v["previsto_dentro_da_faixa"]]
    print(f"\nPor {titulo}: {len(fora)} de {len(saida[chave])} grupos com o previsto FORA da faixa de 95% do real")
    for g, v in saida[chave].items():
        print(f"   {g[:34]:34} n {v['n']:6}  previsto {100 * v['previsto']:5.1f}%  real {100 * v['real']:5.1f}% "
              f"[{100 * v['real_baixo']:5.1f}; {100 * v['real_alto']:5.1f}]{'  <- fora' if not v['previsto_dentro_da_faixa'] else ''}")

arq = T.registrar("a9_calibracao", saida, t.pasta, AQUI / "resultados", semente=SEMENTE,
                  parametros={"corte": CORTE, "ks": [24, 16, 1], "faixas": [5, 10, 15, 20], "repeticoes": 300, "corte_prob": [0.01, 0.99]},
                  filtros={"partidas": "W/L, sem espelho, formato standard ou não confirmado", "lados": "as duas pontas de cada partida"},
                  dados_usados={"partidas_teste": len(teste), "periodo_teste": [min(datas.values()), max(datas.values())],
                                "impressao_teste": T.impressao_objeto(sorted((p["id"], p["arq1"], p["arq2"], p["res1"]) for p in teste))},
                  copia=t.identificacao)
print(f"\nresultado gravado em {arq.name}")
