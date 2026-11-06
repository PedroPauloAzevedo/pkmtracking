"""
A10 (06/11/2026, para D-040 e D-042) — com a regra nova (NB2 sempre que houver modelo), a partir de que confiança o deck do
adversário deve aparecer como "incerto"?
Reaproveita o a8 SEM alterá-lo: roda o a8 inteiro (mesma semente, mesmos dados, saída dele desviada para uma pasta temporária) e
analisa as linhas que ele produz. Para cada limiar candidato: quanto das identificações fica marcado e qual o acerto de cada lado.
Critério escolhido ANTES de olhar: o menor limiar em que o acerto das NÃO marcadas é ≥ 90% (a marca protege o que é confiável) —
e, entre os que cumprem, o que marca menos. Parte real (18 partidas) só para conferência.
Só lê. Uso:  python -I a10_limiar_incerto.py <CÓPIA do programa>
"""
import os
import runpy
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402

LIMIARES = (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98)
ALVO_ACERTO = 0.90
REGRA = "nb2_senao_icones_so_sem_modelo"     # = D-040

saida_a8 = tempfile.mkdtemp(prefix="a8_para_a10_")
antes = os.environ.get("SA_SAIDA")
os.environ["SA_SAIDA"] = saida_a8
sys.argv = [str(AQUI / "a8_identificacao_cartas_vistas.py"), sys.argv[1]]
g = runpy.run_path(str(AQUI / "a8_identificacao_cartas_vistas.py"), run_name="__main__")
if antes is None:
    os.environ.pop("SA_SAIDA", None)
else:
    os.environ["SA_SAIDA"] = antes
linhas, linhas_r, t = g["linhas"], g.get("linhas_r", []), g["t"]

res = {"regra": REGRA, "alvo_acerto_nao_marcadas": ALVO_ACERTO, "limiares": {}, "por_faixa_confianca": {}, "real": {}}
decididas = [(T_, tid, v, k, p[REGRA], conf) for T_, tid, v, k, p, conf in linhas if p[REGRA]]
print(f"\n=== A10: {len(decididas)} identificações (regra D-040) nas listas de teste do a8")
print(" limiar | marcadas | acerto marcadas | acerto não marcadas | (turno 1-2: marcadas)")
for lim in LIMIARES:
    m = [x for x in decididas if x[5] < lim]
    nm = [x for x in decididas if x[5] >= lim]
    cedo = [x for x in decididas if x[0] <= 2]
    r = {"marcadas": len(m) / len(decididas), "acerto_marcadas": sum(x[2] == x[4] for x in m) / len(m) if m else None,
         "acerto_nao_marcadas": sum(x[2] == x[4] for x in nm) / len(nm) if nm else None,
         "marcadas_turno_1_2": sum(1 for x in cedo if x[5] < lim) / len(cedo)}
    res["limiares"][lim] = r
    print(f"  {lim:4}  |  {100 * r['marcadas']:5.1f}%  |      {100 * (r['acerto_marcadas'] or 0):5.1f}%     |"
          f"       {100 * (r['acerto_nao_marcadas'] or 0):5.1f}%       |   {100 * r['marcadas_turno_1_2']:5.1f}%")
ok = [lim for lim, r in res["limiares"].items() if r["acerto_nao_marcadas"] and r["acerto_nao_marcadas"] >= ALVO_ACERTO]
res["limiar_escolhido"] = min(ok) if ok else None
print(f"limiar escolhido pelo critério: {res['limiar_escolhido']}")

faixas = defaultdict(lambda: [0, 0])
for _, _, v, _, s, conf in decididas:
    f = min(int(conf * 10), 9) / 10
    faixas[f][0] += v == s
    faixas[f][1] += 1
res["por_faixa_confianca"] = {f"{f:.1f}": {"n": n, "acerto": a / n} for f, (a, n) in sorted(faixas.items())}
for f, x in res["por_faixa_confianca"].items():
    print(f"   confiança {f}: n {x['n']:5}  acerto {100 * x['acerto']:5.1f}%")

if linhas_r and res["limiar_escolhido"]:
    lim = res["limiar_escolhido"]
    rr = [(T_, v, p[REGRA], conf) for T_, _, v, _, p, conf in linhas_r if p[REGRA]]
    m = [x for x in rr if x[3] < lim]
    nm = [x for x in rr if x[3] >= lim]
    res["real"] = {"identificacoes": len(rr), "marcadas": len(m), "acerto_marcadas": sum(x[1] == x[2] for x in m) / len(m) if m else None,
                   "acerto_nao_marcadas": sum(x[1] == x[2] for x in nm) / len(nm) if nm else None}
    print(f"Real (18 partidas, 1 deck, todos os turnos): {res['real']}")

arq = T.registrar("a10_limiar_incerto", res, t.pasta, AQUI / "resultados", semente=g["SEMENTE"],
                  parametros={"limiares": LIMIARES, "alvo": ALVO_ACERTO, "regra": REGRA},
                  filtros={"base": "linhas do a8 (mesma semente e dados)"},
                  dados_usados={"identificacoes": len(decididas), "impressao_linhas": T.impressao_objeto(
                      [(x[0], x[1], x[2], x[4], round(x[5], 9)) for x in decididas])},
                  copia=t.identificacao)
print(f"resultado gravado em {arq.name}")
