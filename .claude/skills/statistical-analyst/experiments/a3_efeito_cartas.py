"""
AUDITORIA A3 — efeito de cada carta (tracker/regressao.py): as cartas acrescentam previsão ao "deck sozinho"?
Mesmo desenho do experimento 10 (70% dos torneios mais antigos treinam; confronto ajustado só com o treino), usando as funções
do programa (regressao.dados, variaveis, montar_linhas, ajustar). Acrescenta:
  - diferença de log-loss por partida M2 (peso 300) − M1 (só o deck), com faixa por bootstrap AGRUPADO por torneio e por jogador;
  - quanto do ganho do M1 sobre o M0 é "quem tem lista vence mais" (taxa real × taxa esperada pelos confrontos, no teste).
Só lê. Uso:  python -I a3_efeito_cartas.py <CÓPIA do programa>
"""
import math
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
A, B, E, R = t.analises, t.banco, t.estrategia, t.regressao
ids = A.torneios_da_fonte("todos")
datas = {x["id"]: x["data"] or "" for x in B.listar_torneios()}
ordem = sorted(ids, key=lambda i: datas.get(i, ""))
corte = int(len(ordem) * 0.7)
treino_t, teste_t = set(ordem[:corte]), set(ordem[corte:])
todas = E._partidas(sorted(treino_t), com_empates=True)
decks_todos = {r["arquetipo"] for r in B.consultar("SELECT DISTINCT arquetipo FROM t_jogadores WHERE arquetipo != ''")}
conf = {k: v["p"] for k, v in E.confrontos_ajustados(todas, decks_todos).items()}
# o mesmo confronto só com vitórias e derrotas: separa o efeito da convenção "empate = não-vitória" (o teste só tem W/L)
conf_wl = {k: v["p"] for k, v in E.confrontos_ajustados([x for x in todas if x["res1"] in ("W", "L")], decks_todos).items()}
contagem = Counter(r["arquetipo"] for r in B.consultar(
    f"SELECT DISTINCT j.torneio, j.labs_id, j.arquetipo FROM t_jogadores j JOIN t_listas l ON l.torneio=j.torneio AND l.labs_id=j.labs_id "
    f"WHERE j.arquetipo != '' AND j.torneio IN ({','.join('?' * len(ids))})", tuple(ids)))
principais = [a for a, n in contagem.most_common() if n >= 80]


def perda(p, y):
    p = min(max(p, 1e-9), 1 - 1e-9)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


por_torneio, por_jogador, m0m1 = [], [], []
real = esperada = esperada_wl = n_te = 0
for arq in principais:
    listas, partidas, _ = R.dados(arq, ids)
    tr = [p for p in partidas if p[3] in treino_t]
    te = [p for p in partidas if p[3] in teste_t]
    listas_tr = {k: v for k, v in listas.items() if k[0] in treino_t}
    if len(te) < 30 or len(listas_tr) < 40:
        continue
    vars_ = R.variaveis(listas_tr)
    L_tr = R.montar_linhas(tr, listas, vars_, conf, arq)
    L_te = R.montar_linhas(te, listas, vars_, conf, arq)
    b1, _ = R.ajustar([(o, {0: 1.0}, y) for o, _, y in L_tr], 1)
    b2, _ = R.ajustar(L_tr, len(vars_) + 1, R.PESO)
    for (chave, _adv, y, torneio), (o, x, _) in zip(te, L_te):
        l0 = perda(R._sig(o), y)
        l1 = perda(R._sig(o + b1[0]), y)
        l2 = perda(R._sig(o + sum(b2[i] * v for i, v in x.items())), y)
        por_torneio.append((torneio, l2, l1))
        por_jogador.append((chave, l2, l1))
        m0m1.append((torneio, l1, l0))
        real += y
        esperada += R._sig(o)
        esperada_wl += conf_wl.get((arq, _adv), 0.5)
        n_te += 1

res = {"decks": len(principais), "partidas_teste": n_te,
       "taxa_real_teste": round(100 * real / n_te, 2), "taxa_esperada_pelos_confrontos": round(100 * esperada / n_te, 2),
       "taxa_esperada_confrontos_sem_empates": round(100 * esperada_wl / n_te, 2),
       "M2_menos_M1_por_torneio": T.diferenca_pareada(por_torneio, 2000, 21),
       "M2_menos_M1_por_jogador": T.diferenca_pareada(por_jogador, 2000, 21),
       "M1_menos_M0_por_torneio": T.diferenca_pareada(m0m1, 2000, 21)}
print(f"{n_te} partidas de teste de jogadores com lista ({len(principais)} decks com ≥ 80 listas)")
print(f"Taxa real no teste {res['taxa_real_teste']}% × esperada só pelos confrontos {res['taxa_esperada_pelos_confrontos']}%"
      f"; sem contar empates no confronto: {res['taxa_esperada_confrontos_sem_empates']}%"
      " (o que sobra = quanto quem tem lista vence acima do esperado)")
for k in ("M1_menos_M0_por_torneio", "M2_menos_M1_por_torneio", "M2_menos_M1_por_jogador"):
    r = res[k]
    print(f"   {k:26} {r['estimativa']:+.4f}  [{r['baixo']:+.4f}, {r['alto']:+.4f}]  "
          f"{'provável' if r['provavel'] else 'sem diferença clara'}  ({r['grupos']} grupos)")
arq = T.registrar("a3_efeito_cartas", res, t.pasta, AQUI / "resultados", semente=21, parametros={"peso": R.PESO, "corte": 0.7})
print(f"\nresultado gravado em {arq.name}")
