"""
EFEITO DE CADA CARTA (regressão logística), para um deck, a partir das partidas dos campeonatos importados.

Pergunta: com os mesmos confrontos, ter uma cópia a mais (ou a menos) desta carta muda a chance de vencer?
A tabela "Vitória com / Vitória sem" (Uso de cartas) compara as listas brutas e mistura tudo: quem usa a carta
pode ter enfrentado decks diferentes, ou usar junto outra carta que é a que faz diferença.

Como a conta é feita (uma linha por partida do deck nos torneios):
  chance de vencer = logística( confronto + ajuste do deck + soma de efeito_c × (cópias_c − cópias mais comuns_c) )
  - confronto: o confronto ajustado contra o deck daquela partida (tracker/estrategia.py) entra fixo, como ponto
    de partida. Assim a carta não leva o crédito de ter enfrentado adversários mais fáceis;
  - só entram as cartas cujo número de cópias muda entre as listas (pelo menos MIN_LISTAS listas fora do comum).
    Cada efeito é "por cópia, a partir do número de cópias mais comum";
  - todas as cartas entram juntas, então o efeito de uma desconta o das outras que costumam vir junto;
  - "freio" contra exagero (regularização L2, PESO): com poucas partidas o efeito fica perto de zero.
    O valor foi escolhido no testes/experimentos/e10_regressao_cartas.py, que compara com o método atual.

Leia como associação, não como prova: quem coloca uma carta pode ser um jogador melhor. "Efeito provável" só
quando o efeito é maior que duas vezes a incerteza (como um teste de 5%).
"""
import math
from collections import Counter, defaultdict

from . import analises, banco, estrategia

PESO = 300.0       # freio (L2) nos efeitos das cartas: o melhor no experimento 10 (log-loss 0,6665 contra 0,6674 sem cartas)
PESO_DECK = 1.0    # freio leve no ajuste do deck inteiro
MIN_LISTAS = 12    # listas com número de cópias diferente do mais comum, para a carta entrar


def _logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def _sig(x):
    return 1 / (1 + math.exp(-x)) if x > -30 else 0.0


def dados(arq, torneios=None):
    """Listas e partidas do deck. Devolve (listas {chave: Counter(carta->cópias)}, partidas [(chave, adv, venceu, torneio)],
    confrontos {(a, b): p})."""
    if torneios is None:
        torneios = analises.torneios_da_fonte("todos")
    if not torneios:
        return {}, [], {}
    marcas = ",".join("?" * len(torneios))
    listas = defaultdict(Counter)
    for r in banco.consultar(
            f"SELECT l.torneio, l.labs_id, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta, l.qtd FROM t_listas l "
            f"JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id "
            f"WHERE j.arquetipo=? AND l.torneio IN ({marcas})", (arq, *torneios)):
        listas[(r["torneio"], r["labs_id"])][r["carta"]] += r["qtd"]
    jog = {(r["torneio"], r["nome_norm"]): r["labs_id"] for r in banco.consultar(
        f"SELECT torneio, nome_norm, labs_id FROM t_jogadores WHERE arquetipo=? AND torneio IN ({marcas})", (arq, *torneios))}
    partidas = []
    for r in banco.consultar(
            f"SELECT torneio, j1, j2, arq1, arq2, res1 FROM t_partidas WHERE torneio IN ({marcas}) "
            f"AND (arq1=? OR arq2=?) AND res1 IN ('W','L') AND arq1 != '' AND arq2 != ''", (*torneios, arq, arq)):
        for eu, adv, venceu in ((r["j1"], r["arq2"], r["res1"] == "W"), (r["j2"], r["arq1"], r["res1"] == "L")):
            if (r["arq1"] if eu == r["j1"] else r["arq2"]) != arq:
                continue
            chave = (r["torneio"], jog.get((r["torneio"], eu)))
            if chave in listas:
                partidas.append((chave, adv, 1 if venceu else 0, r["torneio"]))
    todas = estrategia._partidas(torneios, com_empates=True)
    decks = {p["arq1"] for p in todas} | {p["arq2"] for p in todas} | {arq}
    conf = {k: v["p"] for k, v in estrategia.confrontos_ajustados(todas, decks).items()}
    return dict(listas), partidas, conf


def variaveis(listas, min_listas=MIN_LISTAS):
    """Cartas que entram: as que mudam de número de cópias em pelo menos `min_listas` listas.
    Devolve [(carta, cópias mais comuns)]."""
    copias = defaultdict(Counter)
    todas = set().union(*(set(l) for l in listas.values())) if listas else set()
    for lst in listas.values():
        for carta in todas:
            copias[carta][lst.get(carta, 0)] += 1
    saida = []
    for carta, dist in copias.items():
        comum, n_comum = dist.most_common(1)[0]
        if len(listas) - n_comum >= min_listas:
            saida.append((carta, comum))
    return sorted(saida)


def ajustar(linhas, k, peso=PESO, peso_deck=PESO_DECK, iteracoes=25):
    """Regressão logística com ponto de partida fixo (offset) e freio L2, por Newton (IRLS).
    linhas: [(offset, {índice: valor}, y)]; índice 0 = ajuste do deck. Devolve (coeficientes, inversa da Hessiana)."""
    b = [0.0] * k
    lam = [peso_deck] + [peso] * (k - 1)
    H = None
    for _ in range(iteracoes):
        g = [-lam[i] * b[i] for i in range(k)]
        H = [[0.0] * k for _ in range(k)]
        for i in range(k):
            H[i][i] = lam[i]
        for off, x, y in linhas:
            eta = off + sum(b[i] * v for i, v in x.items())
            p = _sig(eta)
            w = p * (1 - p)
            itens = list(x.items())
            for i, vi in itens:
                g[i] += (y - p) * vi
                for j, vj in itens:
                    H[i][j] += w * vi * vj
        passo = _resolver(H, g)
        b = [b[i] + passo[i] for i in range(k)]
        if max(abs(s) for s in passo) < 1e-7:
            break
    inv = [_resolver(H, [1.0 if i == j else 0.0 for i in range(k)]) for j in range(k)]
    return b, inv


def _resolver(A, v):
    """Resolve A·x = v (eliminação de Gauss com pivô; A simétrica e positiva por causa do freio)."""
    n = len(v)
    M = [list(A[i]) + [v[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


def montar_linhas(partidas, listas, vars_, conf, arq):
    """Uma linha por partida: (logit do confronto ajustado, {variável: cópias − comum}, venceu)."""
    pos = {c: i + 1 for i, (c, _) in enumerate(vars_)}
    comum = dict(vars_)
    linhas = []
    for chave, adv, y, _ in partidas:
        x = {0: 1.0}
        for carta, i in pos.items():
            d = listas[chave].get(carta, 0) - comum[carta]
            if d:
                x[i] = float(d)
        linhas.append((_logit(conf.get((arq, adv), 0.5)), x, y))
    return linhas


def efeito_cartas(arq, torneios=None, peso=PESO, min_listas=MIN_LISTAS):
    """Para a tela Uso de cartas: efeito de cada carta (por cópia) na chance de vencer, já descontados os confrontos."""
    listas, partidas, conf = dados(arq, torneios)
    if len(listas) < 2 * min_listas or len(partidas) < 50:
        return {"listas": len(listas), "partidas": len(partidas), "cartas": [],
                "aviso": "Poucas listas deste deck com partidas registradas para estimar o efeito das cartas "
                         f"(precisa de pelo menos {2 * min_listas} listas e 50 partidas)."}
    vars_ = variaveis(listas, min_listas)
    linhas = montar_linhas(partidas, listas, vars_, conf, arq)
    b, inv = ajustar(linhas, len(vars_) + 1, peso)
    media = sum(off for off, _, _ in linhas) / len(linhas) + b[0]  # chance típica do deck, em logit
    base = _sig(media)
    contagem = {c: Counter(l.get(c, 0) for l in listas.values()) for c, _ in vars_}
    saida = []
    for i, (carta, comum) in enumerate(vars_, start=1):
        se = math.sqrt(max(inv[i][i], 0.0))
        efeito = 100 * (_sig(media + b[i]) - base)
        saida.append({
            "carta": carta, "comum": comum, "distribuicao": dict(sorted(contagem[carta].items())),
            "fora_do_comum": len(listas) - contagem[carta][comum],
            "efeito_pp": round(efeito, 1),  # pontos percentuais por cópia a mais
            "faixa_pp": [round(100 * (_sig(media + b[i] - 1.96 * se) - base), 1), round(100 * (_sig(media + b[i] + 1.96 * se) - base), 1)],
            "provavel": abs(b[i]) > 1.96 * se,
        })
    saida.sort(key=lambda c: -abs(c["efeito_pp"]))
    esperada = 100 * sum(_sig(off) for off, _, _ in linhas) / len(linhas)
    real = 100 * sum(y for _, _, y in linhas) / len(linhas)
    return {"listas": len(listas), "partidas": len(partidas), "taxa_real": round(real, 1), "taxa_pelos_confrontos": round(esperada, 1),
            "base": round(100 * base, 1), "cartas": saida}
