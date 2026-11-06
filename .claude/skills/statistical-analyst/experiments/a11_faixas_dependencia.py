"""
A11 (06/11/2026, para D-041) — as faixas de Wilson do Meta/Matchups (por partida) são estreitas demais? Qual correção acerta?
Teste de "metades independentes": para cada deck (taxa geral) e cada célula da matriz (deck × deck, 12 mais jogados), os
JOGADORES (jogador + torneio) são sorteados em duas metades. Se a variância usada pela faixa estiver certa, a diferença entre as
taxas das metades, dividida pelo erro previsto, passa de 1,96 em ~5% dos sorteios (cobertura ~95%). Faixa estreita demais →
cobertura < 95%. Compara, nos mesmos sorteios:
  ingenua      variância por partida (o programa hoje)
  fixa_1_25    largura × 1,25 (variância × 1,5625; o efeito de desenho do Labs, a7)
  icc_global   efeito de desenho 1 + (m − 1)·ICC, ICC dos resultados de TODOS os jogadores da seleção (≥ 0), m = partidas por
               jogador NAQUELA conta (deck ou célula)
  icc_deck     o mesmo, com o ICC dos jogadores daquele deck (≥ 0)
Recortes: todos os torneios; só Labs; só online. Empate conta como não-vitória (como no programa). Semente 4111, 200 sorteios.
Só lê. Uso:  python -I a11_faixas_dependencia.py <CÓPIA do programa>
"""
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

SEMENTE, SORTEIOS, K_MATRIZ = 4111, 200, 12
t = carregar(sys.argv[1])
rng = random.Random(SEMENTE)
fonte = {r["id"]: (r["fonte"] or "labs") for r in t.banco.consultar("SELECT id, fonte FROM torneios")}
rows = t.banco.consultar("SELECT torneio, j1, j2, res1, arq1, arq2 FROM t_partidas WHERE arq1 != '' AND arq2 != '' AND res1 IN ('W','L','T')")


def montar(filtro):
    """jogador (torneio, nome) -> lista de (deck, adversário, vitória 0/1); só partidas fora do espelho."""
    jog = defaultdict(list)
    todos = defaultdict(list)   # todos os resultados do jogador (para o ICC global)
    for r in rows:
        if not filtro(fonte.get(r["torneio"], "labs")):
            continue
        for nome, deck, adv, y in ((r["j1"], r["arq1"], r["arq2"], 1 if r["res1"] == "W" else 0),
                                   (r["j2"], r["arq2"], r["arq1"], 1 if r["res1"] == "L" else 0)):
            if not nome:
                continue
            todos[(r["torneio"], nome)].append(y)
            if deck != adv:
                jog[(r["torneio"], nome)].append((deck, adv, y))
    return jog, todos


def icc0(grupos):
    gs = [g for g in grupos if len(g) >= 2]
    return max(0.0, T.icc_binario(gs)) if len(gs) >= 2 else 0.0


def cobertura(unidades, icc_glob, icc_dk, nome):
    """unidades = {chave: {jogador: [y...]}}: para cada chave, 200 divisões em metades por jogador."""
    acertos = Counter()
    total = 0
    for chave, por_jog in unidades.items():
        clusters = [ys for ys in por_jog.values() if ys]
        if len(clusters) < 20:
            continue
        n_tot = sum(len(c) for c in clusters)
        m = n_tot / len(clusters)
        deffs = {"ingenua": 1.0, "fixa_1_25": 1.5625, "icc_global": 1 + (m - 1) * icc_glob,
                 "icc_deck": 1 + (m - 1) * icc_dk.get(chave[0] if isinstance(chave, tuple) else chave, 0.0)}
        for _ in range(SORTEIOS):
            rng.shuffle(clusters)
            a, b = clusters[:len(clusters) // 2], clusters[len(clusters) // 2:]
            na, nb = sum(len(c) for c in a), sum(len(c) for c in b)
            va, vb = sum(sum(c) for c in a), sum(sum(c) for c in b)
            p = (va + vb) / (na + nb)
            if p in (0, 1):
                continue
            base = p * (1 - p) * (1 / na + 1 / nb)
            dif = va / na - vb / nb
            total += 1
            for k, d in deffs.items():
                acertos[k] += abs(dif) <= 1.959964 * math.sqrt(base * d)
    return {k: v / total for k, v in acertos.items()} | {"sorteios": total}


res = {"recortes": {}}
for nome_r, filtro in (("todos", lambda f: True), ("labs", lambda f: f == "labs"), ("online", lambda f: f == "online")):
    jog, todos = montar(filtro)
    icc_glob = icc0(todos.values())
    por_deck = defaultdict(lambda: defaultdict(list))
    por_cel = defaultdict(lambda: defaultdict(list))
    jogos_deck = Counter()
    for j, lst in jog.items():
        for deck, adv, y in lst:
            por_deck[deck][j].append(y)
            jogos_deck[deck] += 1
    principais = [d for d, _ in jogos_deck.most_common(K_MATRIZ)]
    for j, lst in jog.items():
        for deck, adv, y in lst:
            if deck in principais and adv in principais:
                por_cel[(deck, adv)][j].append(y)
    icc_dk = {d: icc0(por_deck[d].values()) for d in jogos_deck}
    m_deck = {d: sum(len(v) for v in por_deck[d].values()) / len(por_deck[d]) for d in principais}
    m_cel = [sum(len(v) for v in c.values()) / len(c) for c in por_cel.values() if c]
    r = {"icc_global": round(icc_glob, 4), "partidas_por_jogador_no_deck": {d: round(m_deck[d], 2) for d in principais},
         "partidas_por_jogador_na_celula_media": round(sum(m_cel) / len(m_cel), 2) if m_cel else None,
         "decks": cobertura({d: por_deck[d] for d in jogos_deck if jogos_deck[d] >= 100}, icc_glob, icc_dk, "decks"),
         "celulas": cobertura(por_cel, icc_glob, icc_dk, "celulas")}
    res["recortes"][nome_r] = r
    print(f"\n{nome_r}: ICC global {r['icc_global']}; partidas por jogador num deck ~{sum(m_deck.values()) / len(m_deck):.1f}, "
          f"numa célula ~{r['partidas_por_jogador_na_celula_media']}")
    for alvo in ("decks", "celulas"):
        c = r[alvo]
        print(f"   {alvo:8} ({c['sorteios']} sorteios): cobertura ingênua {100 * c['ingenua']:.1f}% | ×1,25 {100 * c['fixa_1_25']:.1f}%"
              f" | ICC global {100 * c['icc_global']:.1f}% | ICC do deck {100 * c['icc_deck']:.1f}%   (alvo 95%)")

arq = T.registrar("a11_faixas_dependencia", res, t.pasta, AQUI / "resultados", semente=SEMENTE,
                  parametros={"sorteios": SORTEIOS, "k_matriz": K_MATRIZ, "minimo_jogadores": 20, "minimo_partidas_deck": 100},
                  filtros={"partidas": "W/L/T, empate = não-vitória, sem espelho na taxa do deck"},
                  dados_usados={"partidas": len(rows), "impressao": T.impressao_objeto(sorted((r["torneio"], r["j1"], r["j2"], r["res1"],
                                                                                                r["arq1"], r["arq2"]) for r in rows))},
                  copia=t.identificacao)
print(f"\nresultado gravado em {arq.name}")
