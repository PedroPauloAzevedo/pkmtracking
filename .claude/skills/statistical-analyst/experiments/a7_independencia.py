"""
AUDITORIA A7 (06/11/2026, rodada de "hardening") — independência entre partidas: até onde vale o "ICC ≈ 0" do a1?
O a1 mediu ICC = −0,015 SÓ em jogadores com lista importada (o topo de cada torneio), sem faixa de incerteza. Aqui:
  1. ICC com faixa de 95% por bootstrap de JOGADORES, em recortes: com lista (repete o a1), sem lista, todos, Labs × online;
  2. "mão quente" direta: chance de vencer a rodada seguinte depois de vitória × depois de derrota (mesmo jogador, mesmo torneio);
  3. partidas pessoais (Ladder, jogo único): sequência de resultados de cada dono de log, em ordem de captura — teste de
     sequências (Wald-Wolfowitz) e a mesma diferença depois de vitória × derrota. Amostra pequena: só serve para "não deu para ver".
  4. NÃO mensurável com estes dados: jogos dentro de uma partida melhor de 3 (o banco só guarda o resultado da partida).
Desenho: só leitura; sem separação treino/teste (é descrição, não previsão). Semente 17 (bootstrap). Saída sem nick (jogador A/B).
Uso:  python -I a7_independencia.py <CÓPIA do programa>
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

SEMENTE, REPETICOES = 17, 300
t = carregar(sys.argv[1])
B = t.banco
rng = random.Random(SEMENTE)


def icc_com_faixa(grupos: list[list[int]]) -> dict:
    gs = [g for g in grupos if len(g) >= 2]
    est = T.icc_binario(gs)
    vals = sorted(T.icc_binario([gs[rng.randrange(len(gs))] for _ in gs]) for _ in range(REPETICOES))
    m = sum(len(g) for g in gs) / len(gs)
    return {"jogadores": len(gs), "partidas_por_jogador": round(m, 2), "icc": round(est, 4),
            "ic95": [round(vals[int(0.025 * (REPETICOES - 1))], 4), round(vals[int(0.975 * (REPETICOES - 1))], 4)],
            "efeito_desenho_no_limite_superior": round(T.efeito_desenho(m, max(vals[int(0.975 * (REPETICOES - 1))], 0)), 3)}


# ---------------------------------------------------------------- 1 e 2. torneios
fonte = {r["id"]: (r["fonte"] or "labs") for r in B.consultar("SELECT id, fonte FROM torneios")}
com_lista = {(r["torneio"], r["labs_id"]) for r in B.consultar("SELECT DISTINCT torneio, labs_id FROM t_listas")}
nome_para_id = {(r["torneio"], r["nome_norm"]): r["labs_id"] for r in B.consultar("SELECT torneio, nome_norm, labs_id FROM t_jogadores")}
seq = defaultdict(list)       # (torneio, jogador) -> [(rodada, 1/0)]
for r in B.consultar("SELECT torneio, rodada, j1, j2, res1 FROM t_partidas WHERE res1 IN ('W','L')"):
    for jog, ganhou in ((r["j1"], r["res1"] == "W"), (r["j2"], r["res1"] == "L")):
        if not jog:
            continue
        seq[(r["torneio"], jog)].append((r["rodada"] if isinstance(r["rodada"], int) else 0, 1 if ganhou else 0))

recortes = defaultdict(list)
for (tid, jog), s in seq.items():
    tem = (tid, nome_para_id.get((tid, jog))) in com_lista
    res = [y for _, y in sorted(s)]
    recortes["todos"].append(res)
    recortes["com_lista"if tem else "sem_lista"].append(res)
    recortes[f"fonte_{fonte.get(tid, '?')}"].append(res)
saida = {"icc": {}, "mao_quente": {}, "pessoal": {}, "nao_mensuravel": ["jogos dentro de uma partida melhor de 3 (só o resultado da partida é guardado)"]}
print("1. ICC dos resultados W/L de um mesmo jogador num torneio (faixa de 95% por bootstrap de jogadores)")
for nome in ("com_lista", "sem_lista", "todos", "fonte_labs", "fonte_online"):
    if len(recortes[nome]) > 10:
        r = icc_com_faixa(recortes[nome])
        saida["icc"][nome] = r
        print(f"   {nome:12} {r['jogadores']:6} jogadores  {r['partidas_por_jogador']:4} part./jog.  ICC {r['icc']:+.4f} "
              f"[{r['ic95'][0]:+.4f}; {r['ic95'][1]:+.4f}]  efeito de desenho no limite superior {r['efeito_desenho_no_limite_superior']}")

print("\n2. Mão quente: P(vencer a rodada seguinte | venceu a anterior) − P(... | perdeu a anterior), mesmo jogador e torneio")
for nome in ("com_lista", "sem_lista", "todos"):
    c = {1: [0, 0], 0: [0, 0]}
    for res in recortes[nome]:
        for a, b in zip(res, res[1:]):
            c[a][0] += b
            c[a][1] += 1
    pv, pd = c[1][0] / c[1][1], c[0][0] / c[0][1]
    ep = math.sqrt(pv * (1 - pv) / c[1][1] + pd * (1 - pd) / c[0][1])
    saida["mao_quente"][nome] = {"depois_de_vitoria": round(pv, 4), "depois_de_derrota": round(pd, 4), "diferenca": round(pv - pd, 4),
                                 "ic95_aprox": [round(pv - pd - 1.96 * ep, 4), round(pv - pd + 1.96 * ep, 4)],
                                 "pares": c[1][1] + c[0][1]}
    print(f"   {nome:10} depois de V {100 * pv:5.1f}%  depois de D {100 * pd:5.1f}%  diferença {100 * (pv - pd):+5.1f} pp "
          f"[{100 * (pv - pd - 1.96 * ep):+.1f}; {100 * (pv - pd + 1.96 * ep):+.1f}]  (pares {c[1][1] + c[0][1]})")
print("   (no suíço, quem vence enfrenta adversários mais fortes: a diferença tende a ser negativa POR DESENHO, não por falta de habilidade)")

# ---------------------------------------------------------------- 3. partidas pessoais (Ladder)
nick = (t.config.ler_config() or {}).get("nick", "")
donos = defaultdict(list)
for r in B.consultar("SELECT capturada_em, dono, dados_json FROM partidas ORDER BY capturada_em, id"):
    try:
        res = json.loads(r["dados_json"] or "{}").get("resumo") or {}
    except ValueError:
        continue
    eu = r["dono"] or nick
    if not eu or not res.get("vencedor"):
        continue
    donos[r["dono"] or ""].append(1 if res["vencedor"] == eu else 0)


def sequencias(xs):
    n1, n0 = sum(xs), len(xs) - sum(xs)
    if not n1 or not n0:
        return None
    runs = 1 + sum(a != b for a, b in zip(xs, xs[1:]))
    mu = 1 + 2 * n1 * n0 / (n1 + n0)
    var = 2 * n1 * n0 * (2 * n1 * n0 - n1 - n0) / ((n1 + n0) ** 2 * (n1 + n0 - 1))
    z = (runs - mu) / math.sqrt(var)
    return {"sequencias": runs, "esperado": round(mu, 2), "z": round(z, 3), "p": round(math.erfc(abs(z) / math.sqrt(2)), 3)}


print("\n3. Partidas pessoais (jogo único, Ladder), em ordem de captura")
for i, (dono, xs) in enumerate(sorted(donos.items(), key=lambda kv: -len(kv[1]))):
    rotulo = f"jogador_{chr(65 + i)}"
    pares = list(zip(xs, xs[1:]))
    v = [b for a, b in pares if a == 1]
    d = [b for a, b in pares if a == 0]
    r = {"partidas": len(xs), "taxa": round(sum(xs) / len(xs), 3), "teste_sequencias": sequencias(xs),
         "depois_de_vitoria": round(sum(v) / len(v), 3) if v else None, "depois_de_derrota": round(sum(d) / len(d), 3) if d else None}
    saida["pessoal"][rotulo] = r
    print(f"   {rotulo}: {r['partidas']} partidas, taxa {r['taxa']}, sequências {r['teste_sequencias']}, "
          f"depois de V {r['depois_de_vitoria']}, depois de D {r['depois_de_derrota']}")

arq = T.registrar("a7_independencia", saida, t.pasta, AQUI / "resultados", semente=SEMENTE,
                  parametros={"repeticoes": REPETICOES, "minimo_partidas_por_jogador": 2},
                  filtros={"resultados": "só W/L (empates fora)", "torneios": "todos os importados (sem filtro de formato, como o a1)"},
                  dados_usados={"jogadores_torneio": len(seq), "partidas_pessoais": sum(len(x) for x in donos.values()),
                                "impressao_sequencias": T.impressao_objeto(sorted(recortes["todos"]))},
                  copia=t.identificacao)
print(f"\nresultado gravado em {arq.name}")
