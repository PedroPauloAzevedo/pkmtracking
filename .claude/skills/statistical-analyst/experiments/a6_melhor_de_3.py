"""
AUDITORIA A6 — "seu resultado × meta" compara jogos do Ladder (1 jogo) com partidas de torneio (melhor de 3).
Mede, nos grandes eventos (Labs, melhor de 3 conhecido), quanto a taxa de PARTIDA de cada confronto se afasta da taxa por JOGO
que a produziria (q tal que q²(3 − 2q) = taxa da partida; jogos independentes, sem empates). Só W/L; confrontos dos 12 decks mais
presentes com ≥ 30 partidas. Os torneios online não guardam se foram melhor de 1 ou de 3 (lacuna registrada). Só lê.
Uso:  python -I a6_melhor_de_3.py <CÓPIA do programa>
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
labs = t.analises.torneios_da_fonte("grandes")
mu = t.analises.matchups_por_slug(labs)
meta = t.analises.meta(labs)
top = [d["arquetipo"] for d in meta["divisao"][:12]]
difs = []
for a in top:
    for b in top:
        c = mu.get((a, b))
        if a == b or not c or c["v"] + c["d"] < 30:
            continue
        p = c["v"] / (c["v"] + c["d"])
        q = T.jogo_de_bo3(p)
        difs.append((abs(p - 0.5) - abs(q - 0.5), p, q, a, b))
difs.sort(reverse=True)
media = sum(d[0] for d in difs) / len(difs)
res = {"confrontos": len(difs), "afastamento_medio_pp": round(100 * media, 2),
       "maior": [{"a": a, "b": b, "partida": round(100 * p, 1), "jogo": round(100 * q, 1)} for _, p, q, a, b in difs[:5]],
       "exemplos_formula": {f"{int(100 * q)}%": round(100 * T.bo3_de_jogo(q), 1) for q in (0.45, 0.55, 0.6, 0.65)}}
print(f"{len(difs)} confrontos (Labs, ≥ 30 partidas W/L). A taxa de partida fica, em média, {100 * media:.2f} pp mais longe de 50%"
      " do que a taxa por jogo equivalente.")
for x in res["maior"]:
    print(f"   {x['a']} × {x['b']}: partida {x['partida']}%  ->  por jogo {x['jogo']}%")
print("Fórmula: chance por jogo -> melhor de 3:", res["exemplos_formula"])
arq = T.registrar("a6_melhor_de_3", res, t.pasta, AQUI / "resultados")
print(f"resultado gravado em {arq.name}")
