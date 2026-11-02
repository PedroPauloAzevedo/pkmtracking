"""
EXPERIMENTO 10: o efeito de cada carta por regressão logística (tracker/regressao.py) prevê melhor que o método atual?

Para cada deck com pelo menos 80 listas: os torneios mais antigos (70%) treinam e os mais novos testam.
Os confrontos ajustados também são calculados só com os torneios de treino (sem "espiar" o teste).
Modelos, todos com o confronto ajustado como ponto de partida:
  M0 só o confronto | M1 + ajuste do deck | M2(peso) + efeito de cada carta (regressão, freio L2 = peso)
  M3 + efeito bruto de cada carta ("Vitória com/sem" da tela Uso de cartas, em logit, por cópia)
Mede o log-loss médio nas partidas de teste (menor = previsão melhor) e o Brier (erro quadrático).
Uso:  python testes/experimentos/e10_regressao_cartas.py <pasta do programa com dados>
"""
import math
import sys
from collections import Counter, defaultdict

sys.path.insert(0, sys.argv[1])
from tracker import analises, banco, estrategia, regressao  # noqa: E402

PESOS = [1, 3, 10, 30, 100, 300, 1000]
ids = analises.torneios_da_fonte("todos")
datas = {t["id"]: t["data"] or "" for t in banco.listar_torneios()}
ordem = sorted(ids, key=lambda t: datas.get(t, ""))
corte = int(len(ordem) * 0.7)
treino_t, teste_t = set(ordem[:corte]), set(ordem[corte:])
print(f"torneios: {len(ordem)} (treino {len(treino_t)}, teste {len(teste_t)}); teste a partir de {datas.get(ordem[corte], '?')}")

todas = estrategia._partidas(sorted(treino_t), com_empates=True)
decks_todos = {r["arquetipo"] for r in banco.consultar("SELECT DISTINCT arquetipo FROM t_jogadores WHERE arquetipo != ''")}
conf = {k: v["p"] for k, v in estrategia.confrontos_ajustados(todas, decks_todos).items()}

contagem = Counter(r["arquetipo"] for r in banco.consultar(
    f"SELECT DISTINCT j.torneio, j.labs_id, j.arquetipo FROM t_jogadores j JOIN t_listas l ON l.torneio=j.torneio AND l.labs_id=j.labs_id "
    f"WHERE j.arquetipo != '' AND j.torneio IN ({','.join('?' * len(ids))})", tuple(ids)))
principais = [a for a, n in contagem.most_common() if n >= 80]


def perda(ps_ys):
    ll = -sum(y * math.log(max(p, 1e-9)) + (1 - y) * math.log(max(1 - p, 1e-9)) for p, y in ps_ys) / len(ps_ys)
    br = sum((p - y) ** 2 for p, y in ps_ys) / len(ps_ys)
    return ll, br


total = defaultdict(lambda: [0.0, 0.0, 0])
for arq in principais:
    listas, partidas, _ = regressao.dados(arq, ids)
    tr = [p for p in partidas if p[3] in treino_t]
    te = [p for p in partidas if p[3] in teste_t]
    listas_tr = {k: v for k, v in listas.items() if k[0] in treino_t}
    if len(te) < 30 or len(listas_tr) < 40:
        continue
    vars_ = regressao.variaveis(listas_tr)
    L_tr = regressao.montar_linhas(tr, listas, vars_, conf, arq)
    L_te = regressao.montar_linhas(te, listas, vars_, conf, arq)
    k = len(vars_) + 1
    res = {}
    res["M0 confronto"] = perda([(regressao._sig(off), y) for off, _, y in L_te])
    b1, _ = regressao.ajustar([(o, {0: 1.0}, y) for o, _, y in L_tr], 1)
    res["M1 + deck"] = perda([(regressao._sig(o + b1[0]), y) for o, _, y in L_te])
    for peso in PESOS:
        b, _ = regressao.ajustar(L_tr, k, peso)
        res[f"M2 regressão peso {peso}"] = perda([(regressao._sig(o + sum(b[i] * v for i, v in x.items())), y) for o, x, y in L_te])
    # M3: efeito bruto por carta: logit(taxa das partidas com cópias fora do comum) - logit(taxa com o comum), por cópia
    bruto = {}
    for i, (carta, comum) in enumerate(vars_, start=1):
        fora = [(y, x[i]) for o, x, y in L_tr if i in x]
        dentro = [y for o, x, y in L_tr if i not in x]
        if fora and dentro:
            tf = (sum(y for y, _ in fora) + 1) / (len(fora) + 2)
            td = (sum(dentro) + 1) / (len(dentro) + 2)
            passo = sum(d for _, d in fora) / len(fora) or 1.0
            bruto[i] = (regressao._logit(tf) - regressao._logit(td)) / passo
    res["M3 bruto com/sem"] = perda([(regressao._sig(o + b1[0] + sum(bruto.get(i, 0) * v for i, v in x.items() if i)), y) for o, x, y in L_te])
    print(f"\n{arq}: {len(listas_tr)} listas de treino, {len(vars_)} cartas variáveis, {len(tr)} partidas de treino, {len(te)} de teste")
    melhor = min(res.items(), key=lambda kv: kv[1][0])[0]
    for nome, (ll, br) in res.items():
        print(f"   {nome:26} log-loss {ll:.4f}  Brier {br:.4f}{'  <- melhor' if nome == melhor else ''}")
        total[nome][0] += ll * len(te)
        total[nome][1] += br * len(te)
        total[nome][2] += len(te)

print("\nTODOS OS DECKS (média ponderada pelas partidas de teste)")
for nome, (ll, br, n) in total.items():
    print(f"   {nome:26} log-loss {ll / n:.4f}  Brier {br / n:.4f}  ({n} partidas)")
