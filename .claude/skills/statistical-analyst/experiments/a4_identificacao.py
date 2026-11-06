"""
AUDITORIA A4 — identificação do deck: a regra que o programa usa DE VERDADE (decks.identificar: NB2 se confiança ≥ 0,5,
senão ícones) contra cada método sozinho; e a confiança do NB2 é uma probabilidade honesta (calibração)?
O experimento 2 mediu o NB antigo combinado com os ícones, não o NB2. Aqui são as funções do programa, com os modelos montados
SÓ com os torneios de treino (o banco.consultar usado por decks é filtrado: listas de torneios de teste não entram).
Limitação conhecida: o cadastro de arquétipos (ícones, nº de jogadores para desempate) vem de todos os torneios.
Cartas "vistas" = sorteadas da lista (como no e2), sem Energias Básicas. Só lê. Semente 7.
Uso:  python -I a4_identificacao.py <CÓPIA do programa>
"""
import random
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
D, B = t.decks, t.banco
rng = random.Random(7)
rows = B.consultar(
    "SELECT t.data, j.arquetipo AS arq, l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta "
    "FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id JOIN torneios t ON t.id=l.torneio "
    "WHERE j.arquetipo != ''")
listas = defaultdict(lambda: {"arq": "", "data": "", "cartas": set()})
for r in rows:
    L = listas[(r["torneio"], r["labs_id"])]
    L["arq"], L["data"] = r["arq"], r["data"] or ""
    if not t.cartas.eh_energia_basica(r["carta"]):
        L["cartas"].add(r["carta"])
datas_t = {}
for (tid, _), L in listas.items():
    datas_t[tid] = min(datas_t.get(tid, "9999"), L["data"])
ordem = sorted(datas_t, key=datas_t.get)
treino_t = set(ordem[:int(len(ordem) * 0.7)])
teste = [L for (tid, _), L in sorted(listas.items()) if tid not in treino_t and L["cartas"]]

consultar_original = D.banco.consultar


def consultar_treino(sql, params=()):
    linhas = consultar_original(sql, params)
    if linhas and "lista" in linhas[0]:
        return [x for x in linhas if x["lista"].split("/")[0] in treino_t]
    return linhas


D.banco.consultar = consultar_treino
D._cache.clear()
m = D._modelo_nb()
D._assinaturas()
D._cache["nb"] = (D._cache["nb"][0] + 10 ** 9, D._cache["nb"][1])   # sem versão: vale pelo tempo (ver decks._em_dia)
D._cache["ass"] = (D._cache["ass"][0] + 10 ** 9, D._cache["ass"][1])
print(f"{len(listas)} listas, {len(ordem)} torneios; modelo com {m['total']} listas de treino; teste {len(teste)} listas")

res = {"por_cartas": {}, "teste": len(teste)}
pares_conf = []
print("\ncartas | ícones | NB2 sozinho | programa (NB2 ≥ 0,5 senão ícones) | NB2 decide em | acerto quando decide")
for k in (2, 3, 5, 8, 12):
    amostra = rng.sample(teste, min(1500, len(teste)))
    ac = {"icones": 0, "nb2": 0, "programa": 0}
    decide = acerto_decide = 0
    for L in amostra:
        vistas = rng.sample(sorted(L["cartas"]), min(k, len(L["cartas"])))
        D._cache.pop("ident", None)
        s_nb, conf = D.identificar_nb({t.leitor.normalizar_nome_carta(c) for c in vistas})
        s_ic = D._identificar_por_icones(vistas)
        s_pr = D.identificar(vistas)
        ac["icones"] += s_ic == L["arq"]
        ac["nb2"] += s_nb == L["arq"]
        ac["programa"] += s_pr == L["arq"]
        if s_nb:
            pares_conf.append((conf, 1 if s_nb == L["arq"] else 0))
        if s_nb and conf >= D.CONFIANCA_NB:
            decide += 1
            acerto_decide += s_nb == L["arq"]
    n = len(amostra)
    linha = {x: round(100 * v / n, 1) for x, v in ac.items()}
    linha.update(nb2_decide=round(100 * decide / n, 1), acerto_quando_decide=round(100 * acerto_decide / max(decide, 1), 1))
    res["por_cartas"][k] = linha
    print(f"  {k:4} | {linha['icones']:5.1f}% |    {linha['nb2']:5.1f}%   |              {linha['programa']:5.1f}%"
          f"               |    {linha['nb2_decide']:5.1f}%    |   {linha['acerto_quando_decide']:5.1f}%")

cal = T.calibracao(pares_conf, 10)
res["calibracao_nb2"] = cal
print(f"\nCalibração da confiança do NB2 (todas as quantidades de cartas juntas): erro médio {cal['ece']:.3f}")
for f in cal["faixas"]:
    print(f"   confiança {f['de']:.1f}–{f['ate']:.1f}: n {f['n']:5}  diz {100 * f['previsto']:5.1f}%  acerta {100 * f['real']:5.1f}%")
D.banco.consultar = consultar_original
arq = T.registrar("a4_identificacao", res, t.pasta, AQUI / "resultados", semente=7, parametros={"corte": 0.7, "amostra": 1500})
print(f"\nresultado gravado em {arq.name}")
