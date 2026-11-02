"""
PROBABILIDADES DE UMA LISTA (consistência do deck), com as regras do Standard:

  - 60 cartas; mão inicial de 7; sem Pokémon Básico na mão = mulligan (embaralha e compra 7 de novo);
  - depois, 6 cartas do topo viram prêmios;
  - os dois jogadores compram 1 carta no começo de cada turno, inclusive quem começa no 1º turno.

As contas são EXATAS (distribuição hipergeométrica: sortear sem reposição), não simulação.
O mulligan é tratado como condição: a mão que vale é sempre uma mão com pelo menos um Básico.

Ideia geral: as cartas do deck são divididas em categorias (ex.: "a carta X", "outros Básicos",
"o resto"). Para uma mão de n cartas, percorremos todas as combinações de quantas cartas de cada
categoria vieram (são poucas) e somamos as probabilidades. Depois da mão, os prêmios e as compras
saem das 53 cartas que sobraram, e por simetria tanto faz a ordem em que isso acontece.
"""
from functools import lru_cache
from itertools import product
from math import comb

DECK, MAO, PREMIOS = 60, 7, 6


def hipergeometrica(total, sucessos, amostra, k):
    """P(exatamente k sucessos ao tirar `amostra` cartas de `total`, das quais `sucessos` são o alvo)."""
    if k < 0 or k > sucessos or k > amostra or amostra - k > total - sucessos or amostra > total:
        return 0.0  # impossível (ex.: 9 cópias de uma Energia não cabem todas nos 6 prêmios)
    return comb(sucessos, k) * comb(total - sucessos, amostra - k) / comb(total, amostra)


def ao_menos_um(total, sucessos, amostra):
    return 1.0 - hipergeometrica(total, sucessos, amostra, 0)


def _maos(categorias, n):
    """Todas as maneiras de uma mão de n cartas se dividir entre as categorias, com a probabilidade de cada.
    categorias: tamanhos (somam o total do deck). Devolve [(contagens, probabilidade)]."""
    total = sum(categorias)
    saida = []
    for cont in product(*(range(min(c, n) + 1) for c in categorias[:-1])):
        resto = n - sum(cont)
        if resto < 0 or resto > categorias[-1]:
            continue
        maneiras = comb(categorias[-1], resto)
        for c, k in zip(categorias, cont):
            maneiras *= comb(c, k)
        saida.append((cont + (resto,), maneiras / comb(total, n)))
    return saida


def mulligan(basicos, deck=DECK):
    """Chance de uma mão de 7 sem nenhum Pokémon Básico."""
    return hipergeometrica(deck, basicos, MAO, 0)


def mulligans_esperados(basicos, deck=DECK):
    """Média de mulligans por partida (cada nova mão é independente: distribuição geométrica)."""
    p = mulligan(basicos, deck)
    return p / (1 - p) if p < 1 else float("inf")


@lru_cache(maxsize=4096)
def carta(copias, basicos, eh_basico, compras=0, deck=DECK):
    """Probabilidades de UMA carta (com `copias` cópias) numa lista com `basicos` Pokémon Básicos.

    eh_basico: a carta é um Pokémon Básico (então ela mesma conta para evitar o mulligan).
    compras: cartas compradas depois da mão (ex.: começando, no seu 1º turno = 1; indo em segundo = 1 também,
             e no seu 2º turno = 2). Devolve um dicionário com:
      na_mao      - pelo menos 1 cópia na mão inicial (já sem mulligan);
      ate_compras - pelo menos 1 cópia entre a mão e as `compras` compras seguintes;
      todas_premio- todas as cópias presas nos prêmios;
      alguma_premio - pelo menos 1 cópia nos prêmios.
    """
    if copias <= 0:
        return {"na_mao": 0.0, "ate_compras": 0.0, "todas_premio": 0.0, "alguma_premio": 0.0}
    outros_basicos = basicos - copias if eh_basico else basicos
    resto = deck - copias - outros_basicos
    # mãos válidas: pelo menos um Básico (a própria carta, se ela for Básica, ou outro Básico)
    validas = [(c, p) for c, p in _maos((copias, outros_basicos, resto), MAO)
               if c[1] > 0 or (eh_basico and c[0] > 0)]
    p_valida = sum(p for _, p in validas)
    sobra = deck - MAO
    na_mao = ate = todas = alguma = 0.0
    for (x, _, _), p in validas:
        w = p / p_valida
        faltam = copias - x  # cópias que ficaram nas 53 cartas restantes
        if x > 0:
            na_mao += w
            ate += w
        else:
            ate += w * ao_menos_um(sobra, faltam, compras)  # compras saem das 53 (prêmios à parte, por simetria)
        todas += w * (hipergeometrica(sobra, faltam, PREMIOS, faltam) if x == 0 else 0.0)
        alguma += w * ao_menos_um(sobra, faltam, PREMIOS)
    return {"na_mao": na_mao, "ate_compras": ate, "todas_premio": todas, "alguma_premio": alguma}


def combo(copias_a, copias_b, basicos, a_basico=False, b_basico=False, compras=0, deck=DECK):
    """Chance de ter pelo menos 1 de A E pelo menos 1 de B entre a mão inicial (válida) e as compras.
    A e B são cartas (ou grupos de cartas) diferentes."""
    outros_basicos = basicos - (copias_a if a_basico else 0) - (copias_b if b_basico else 0)
    resto = deck - copias_a - copias_b - outros_basicos
    ok = p_valida = 0.0
    sobra = deck - MAO
    for (a, b, o, _), p in _maos((copias_a, copias_b, outros_basicos, resto), MAO):
        if not (o > 0 or (a_basico and a > 0) or (b_basico and b > 0)):
            continue  # mulligan: essa mão não vale
        p_valida += p
        if a and b:
            ok += p
            continue
        fa, fb = copias_a - a, copias_b - b
        # compras das 53 restantes: precisa achar o que faltou (inclusão-exclusão)
        sem_a = hipergeometrica(sobra, fa, compras, 0) if not a else 0.0
        sem_b = hipergeometrica(sobra, fb, compras, 0) if not b else 0.0
        sem_ambos = hipergeometrica(sobra, fa + fb, compras, 0) if (not a and not b) else 0.0
        ok += p * (1 - sem_a - sem_b + sem_ambos)
    return ok / p_valida if p_valida else 0.0


def resumo_lista(cartas_lista, compras_turno=(1, 2, 3)):
    """Consistência de uma lista: [{nome, qtd, basico}] -> mulligan e, por carta, as chances principais.
    compras_turno: compras feitas até o seu 1º, 2º e 3º turno (iguais começando ou indo em segundo,
    porque os dois compram no próprio turno)."""
    deck = sum(c["qtd"] for c in cartas_lista)
    basicos = sum(c["qtd"] for c in cartas_lista if c.get("basico"))
    agrupadas = {}
    for c in cartas_lista:  # versões diferentes da mesma carta somam
        g = agrupadas.setdefault(c["nome"], {"nome": c["nome"], "qtd": 0, "basico": bool(c.get("basico")), "secao": c.get("secao", "")})
        g["qtd"] += c["qtd"]
    linhas = []
    for g in agrupadas.values():
        r = carta(g["qtd"], basicos, g["basico"], 0, deck)
        turnos = [carta(g["qtd"], basicos, g["basico"], t, deck)["ate_compras"] for t in compras_turno]
        linhas.append({**g, "na_mao": r["na_mao"], "ate_turno": turnos, "alguma_premio": r["alguma_premio"],
                       "todas_premio": r["todas_premio"]})
    esperados = mulligans_esperados(basicos, deck)
    return {"deck": deck, "basicos": basicos, "mulligan": mulligan(basicos, deck),
            # sem Básico toda mão é mulligan (infinito); JSON não aceita infinito: vai None e o painel mostra "–"
            "mulligans_esperados": None if esperados == float("inf") else esperados, "cartas": linhas}
