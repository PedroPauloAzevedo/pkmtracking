"""
EXPERIMENTO 5: variantes de um mesmo deck (agrupar listas parecidas).

Para os decks com mais listas, agrupa as listas por semelhança (distância de Jaccard ponderada pelas
cópias: quanto das 60 cartas as duas listas têm em comum) com k-medoides, escolhendo k de 1 a 4 pela
"silhueta" (mede se os grupos são bem separados: perto de 0 = não há grupos de verdade; acima de 0,25 = há).
Para cada variante: tamanho, cartas que a distinguem e taxa de vitória (com a faixa de confiança).
Uso:  python testes/experimentos/e5_variantes.py <pasta do programa com dados> [decks]
"""
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, sys.argv[1])
from tracker import analises, banco, decks  # noqa: E402

random.seed(3)
qtd_decks = int(sys.argv[2]) if len(sys.argv) > 2 else 4
ids = analises.torneios_da_fonte("todos")
marcas = ",".join("?" * len(ids))
rows = banco.consultar(
    f"SELECT j.arquetipo AS arq, l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd, j.v, j.d, j.e "
    f"FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo != '' AND l.torneio IN ({marcas})", tuple(ids))
listas = defaultdict(lambda: {"cartas": Counter(), "v": 0, "d": 0, "e": 0, "arq": ""})
for r in rows:
    L = listas[(r["torneio"], r["labs_id"])]
    L["cartas"][r["carta"]] += r["qtd"]
    L.update(arq=r["arq"], v=r["v"] or 0, d=r["d"] or 0, e=r["e"] or 0)
por_arq = defaultdict(list)
for L in listas.values():
    por_arq[L["arq"]].append(L)


def dist(a, b):
    comum = sum(min(q, b.get(c, 0)) for c, q in a.items())
    return 1 - comum / max(sum(a.values()) + sum(b.values()) - comum, 1)


def kmedoides(D, k, voltas=30):
    n = len(D)
    med = random.sample(range(n), k)
    for _ in range(voltas):
        grupos = [min(range(k), key=lambda g: D[i][med[g]]) for i in range(n)]
        novos = []
        for g in range(k):
            membros = [i for i in range(n) if grupos[i] == g] or [med[g]]
            novos.append(min(membros, key=lambda m: sum(D[m][i] for i in membros)))
        if novos == med:
            break
        med = novos
    return [min(range(k), key=lambda g: D[i][med[g]]) for i in range(n)], med


def silhueta(D, grupos, k):
    if k == 1:
        return 0.0
    total = 0.0
    for i in range(len(D)):
        mesmo = [D[i][j] for j in range(len(D)) if grupos[j] == grupos[i] and j != i]
        a = sum(mesmo) / len(mesmo) if mesmo else 0
        b = min((sum(D[i][j] for j in range(len(D)) if grupos[j] == g) / max(1, sum(1 for j in range(len(D)) if grupos[j] == g))
                 for g in range(k) if g != grupos[i]), default=0)
        total += (b - a) / max(a, b) if max(a, b) else 0
    return total / len(D)


for arq, ls in sorted(por_arq.items(), key=lambda x: -len(x[1]))[:qtd_decks]:
    ls = ls if len(ls) <= 300 else random.sample(ls, 300)
    D = [[dist(a["cartas"], b["cartas"]) for b in ls] for a in ls]
    melhor = max(((silhueta(D, g, k), k, g, m) for k in (1, 2, 3, 4) for g, m in [kmedoides(D, k)]), key=lambda x: x[0])
    sil, k, grupos, med = melhor
    print(f"\n{decks.nome_deck(arq)}: {len(ls)} listas, distância média {sum(map(sum, D)) / len(D) ** 2:.2f}; "
          f"melhor k = {k} (silhueta {sil:.2f}{', grupos nítidos' if sil >= 0.25 else ', grupos fracos'})")
    if k == 1:
        continue
    media_geral = {c: sum(L["cartas"].get(c, 0) for L in ls) / len(ls) for c in {c for L in ls for c in L["cartas"]}}
    for g in range(k):
        membros = [ls[i] for i in range(len(ls)) if grupos[i] == g]
        v, d, e = (sum(L[x] for L in membros) for x in ("v", "d", "e"))
        pl = analises.placar(v, d, e)
        media = {c: sum(L["cartas"].get(c, 0) for L in membros) / len(membros) for c in media_geral}
        dif = sorted(media, key=lambda c: -abs(media[c] - media_geral[c]))[:4]
        marca = ", ".join(f"{c} {media[c]:.1f} (geral {media_geral[c]:.1f})" for c in dif)
        print(f"  variante {g + 1}: {len(membros)} listas, vitória {pl['taxa']}% (provável {pl['ic_baixo']}–{pl['ic_alto']}%, {pl['n']} jogos) | {marca}")
