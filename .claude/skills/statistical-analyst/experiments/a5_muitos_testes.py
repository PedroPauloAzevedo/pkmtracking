"""
AUDITORIA A5 — muitos testes ao mesmo tempo: quantas "diferenças prováveis" (variantes) e "efeitos prováveis" (regressão)
as telas mostram, quantas seriam esperadas só por acaso e quantas sobrevivem a Holm / Benjamini-Hochberg.
Usa as funções do programa como estão (variantes.variantes, regressao.efeito_cartas), em todos os torneios. Só lê.
Uso:  python -I a5_muitos_testes.py <CÓPIA do programa> [decks]
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
n_decks = int(sys.argv[2]) if len(sys.argv) > 2 else 12
ids = t.analises.torneios_da_fonte("todos")
cont = Counter(r["arquetipo"] for r in t.banco.consultar(
    "SELECT DISTINCT j.torneio, j.labs_id, j.arquetipo FROM t_jogadores j JOIN t_listas l ON l.torneio=j.torneio AND l.labs_id=j.labs_id "
    "WHERE j.arquetipo != ''"))
principais = [a for a, _ in cont.most_common(n_decks)]

res = {"variantes": {}, "regressao": {}}
pv_var, pv_reg = [], []
for arq in principais:
    v = t.variantes.variantes(arq, ids)
    linhas = [x for x in v["aces"] if x["p_valor"] is not None] + [x for x in v["grupos"] if x["p_valor"] is not None]
    marcadas = sum(1 for x in linhas if x["diferenca"])
    pv_var += [(arq, x["p_valor"], x["diferenca"]) for x in linhas]
    r = t.regressao.efeito_cartas(arq, ids)
    cartas = r.get("cartas", [])
    for c in cartas:
        # valor-p aproximado a partir da faixa de 95% em pontos percentuais (efeito/erro, escala logit ~ linear perto da base)
        lo, hi = c["faixa_pp"]
        se = (hi - lo) / (2 * 1.96) if hi > lo else None
        z = c["efeito_pp"] / se if se else 0.0
        pv_reg.append((arq, math.erfc(abs(z) / math.sqrt(2)), c["provavel"]))
    res["variantes"][arq] = {"testes": len(linhas), "marcadas": marcadas}
    res["regressao"][arq] = {"cartas": len(cartas), "provaveis": sum(c["provavel"] for c in cartas)}
    print(f"{arq:28} variantes: {marcadas}/{len(linhas)} marcadas | cartas: {res['regressao'][arq]['provaveis']}/{len(cartas)} prováveis")


def resumo(nome, lista):
    ps = [p for _, p, _ in lista]
    if not ps:
        return {}
    h, bh = T.holm(ps), T.benjamini_hochberg(ps)
    r = {"testes": len(ps), "marcadas_pela_tela": sum(m for *_, m in lista), "p_abaixo_005": sum(p < 0.05 for p in ps),
         "esperadas_por_acaso": round(0.05 * len(ps), 1), "sobrevivem_holm": sum(x < 0.05 for x in h),
         "sobrevivem_bh_q010": sum(x < 0.10 for x in bh)}
    print(f"\n{nome}: {r['testes']} testes; a tela marca {r['marcadas_pela_tela']}; p < 0,05 em {r['p_abaixo_005']} "
          f"(só por acaso seriam ~{r['esperadas_por_acaso']}); sobrevivem a Holm {r['sobrevivem_holm']}; "
          f"a Benjamini-Hochberg (q < 0,10) {r['sobrevivem_bh_q010']}")
    return r


res["resumo_variantes"] = resumo("Variantes (ACE SPEC e versões)", pv_var)
res["resumo_regressao"] = resumo("Efeito de cada carta (valor-p aproximado pela faixa)", pv_reg)
arq = T.registrar("a5_muitos_testes", res, t.pasta, AQUI / "resultados", parametros={"decks": n_decks})
print(f"\nresultado gravado em {arq.name}")
