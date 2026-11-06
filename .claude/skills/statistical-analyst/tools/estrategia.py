"""
FERRAMENTAS DE ANÁLISE ESTRATÉGICA (prêmios, corrida, troca, disrupção, sequência) — funções PURAS (só biblioteca padrão).

Recebem o que o Coletor já produz (o dicionário de `replay.gerar` e a lista de `eventos` do leitor) e devolvem indicadores. Não
importam o Coletor nem abrem o banco: quem chama (o roteiro `experiments/p_estrategia.py`) usa a `ponte` e passa os dados.
O que já existe no programa é reaproveitado por parâmetro, não copiado: a hipergeométrica (`probabilidades.hipergeometrica`) entra
como `hg`; a regressão logística (`regressao.ajustar`) é chamada pelo roteiro.

Conceitos, premissas e observabilidade de cada indicador: `../knowledge/STRATEGIC_CONCEPTS.md` (matriz), `PRIZE_ANALYSIS.md`,
`CONTROL_AND_DISRUPTION.md`, `DECISION_ANALYSIS.md`. Classe de cada função em `CLASSE` (todas leitura). Testes: `../tests/test_estrategia.py`.

  valor_premio, rota_executada, mapa, tomadas, corrida, rotas_possiveis   prize mapping / racing (P1, P2)
  mao_inicial, zonas_desconhecidas, premio_checado, alguma_premiada       prize checking (P3)
  trocas, eficiencia                                                       prize trade (P4)
  categorias_disrupcao, desenvolvimento, fins                             disrupção, stall, mill (P5, P6)
  acoes_do_turno, ngramas                                                  sequência (P7)
  kaplan_meier, diferenca_por_estrato                                      tempo até evento com censura; comparação pareada por estado
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Callable, Hashable, Iterable, Sequence

# ------------------------------------------------------------------ prize mapping e corrida (P1, P2)


def valor_premio(nome: str) -> int:
    """Prêmios que o Pokémon dá ao ser nocauteado, PELA REGRA DO NOME (Mega ... ex = 3; ... ex = 2; resto = 1).
    Não vê cartas que mudam o valor (o log não diz): é INFERIDO. Para o que aconteceu, use `tomadas` (os "took N")."""
    n = (nome or "").strip()
    if n.startswith("Mega ") and n.endswith(" ex"):
        return 3
    if n.endswith(" ex"):
        return 2
    return 1


def tomadas(rep: dict) -> list[dict]:
    """Prêmios pegos, em ordem: [{"turno", "jogador", "n", "quadro"}], pela queda de `mesa[j]["premios"]` entre quadros
    consecutivos do replay. OBSERVADO (é o "took N" do log)."""
    js = rep.get("jogadores") or []
    antes = {j: 6 for j in js}
    saida = []
    for i, q in enumerate(rep.get("quadros") or []):
        mesa = q["estado"]["mesa"]
        for j in js:
            agora = mesa[j]["premios"]
            if agora < antes[j]:
                saida.append({"turno": q["turno"], "jogador": j, "n": antes[j] - agora, "quadro": i})
            antes[j] = agora
    return saida


def rota_executada(rep: dict) -> dict[str, list[int]]:
    """Rota de prêmios EXECUTADA por jogador: {jogador: [2, 2, 2]}. Única rota observável (a planejada não está no log)."""
    rota = {j: [] for j in rep.get("jogadores") or []}
    for tk in tomadas(rep):
        rota[tk["jogador"]].append(tk["n"])
    return rota


def mapa(seq: Sequence[int]) -> str:
    """[1, 1, 2, 2] -> '1-1-2-2'."""
    return "-".join(str(x) for x in seq)


def corrida(rep: dict) -> list[dict]:
    """Prêmios restantes de cada jogador ao FIM de cada turno: [{"turno", "restantes": {j: r}}] (último quadro de cada turno)."""
    js = rep.get("jogadores") or []
    por_turno = {}
    for q in rep.get("quadros") or []:
        por_turno[q["turno"]] = {j: q["estado"]["mesa"][j]["premios"] for j in js}
    return [{"turno": t, "restantes": r} for t, r in sorted(por_turno.items())]


def rotas_possiveis(restantes: int, alvos: Counter | dict, limite: int = 5000) -> list[tuple[int, ...]]:
    """Rotas MATEMATICAMENTE POSSÍVEIS com os alvos disponíveis: sequências ordenadas de valores de prêmio (cada alvo usado no
    máximo uma vez, `alvos` = {valor: quantos Pokémon com esse valor}) cuja soma alcança `restantes`; a rota termina no nocaute
    que alcança. Não verifica dano, Energia nem respostas do adversário (isso é "executável"/"robusta": DECISION_ANALYSIS.md §4).
    Para no `limite` (levanta ValueError se passar: diga ao usuário que a enumeração explodiu)."""
    if restantes < 1:
        return [()]
    disp = {int(v): int(q) for v, q in dict(alvos).items() if q > 0 and v > 0}
    saida: list[tuple[int, ...]] = []

    def andar(falta, usados, rota):
        for v in sorted(disp):
            if usados.get(v, 0) >= disp[v]:
                continue
            nova = rota + (v,)
            if v >= falta:
                saida.append(nova)
                if len(saida) > limite:
                    raise ValueError(f"mais de {limite} rotas: reduza os alvos ou aumente o limite")
            else:
                usados[v] = usados.get(v, 0) + 1
                andar(falta - v, usados, nova)
                usados[v] -= 1
    andar(restantes, {}, ())
    return saida


# ------------------------------------------------------------------ prize checking (P3)

def mao_inicial(texto: str, jogador: str) -> Counter | None:
    """Mão inicial listada no log para quem exportou. None se houve mulligan (a mão nova não aparece no log) ou se não há lista
    (o adversário nunca tem). Formato em PROJECT_KNOWLEDGE/02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md §2–3."""
    if re.search(rf"^{re.escape(jogador)} took a mulligan", texto, re.M):
        return None
    m = re.search(rf"^{re.escape(jogador)} drew 7 cards for the opening hand\.\s*\n- 7 drawn cards\.\s*\n\s*•\s*(.+)$", texto, re.M)
    if not m:
        return None
    mao = Counter(x.strip() for x in m.group(1).split(",") if x.strip())
    return mao if sum(mao.values()) == 7 else None


def zonas_desconhecidas(deck: Counter | dict, vistas: Counter | dict) -> dict:
    """Zona desconhecida de quem exportou = baralho + prêmios restantes. N = 60 − cartas já vistas (mão, mesa, descarte, prêmios
    pegos, fora de jogo); m[carta] = cópias da lista − cópias vistas. Levanta ValueError se a lista não tiver 60 cartas ou se uma
    carta vista não couber na lista (lista errada para a partida: não use a hipergeométrica)."""
    deck = Counter(deck)
    vistas = Counter(vistas)
    if sum(deck.values()) != 60:
        raise ValueError(f"lista com {sum(deck.values())} cartas (precisa de 60)")
    sobra = [c for c, q in vistas.items() if q > deck.get(c, 0)]
    if sobra:
        raise ValueError(f"cartas vistas que não cabem na lista: {sobra[:5]} — a lista não é a desta partida")
    m = {c: q - vistas.get(c, 0) for c, q in deck.items() if q - vistas.get(c, 0) > 0}
    return {"N": 60 - sum(vistas.values()), "m": m}


def premio_checado(N: int, m: int, k: int, hg: Callable[[int, int, int, int], float]) -> float:
    """P(pelo menos 1 das m cópias está entre os k prêmios), com N cartas desconhecidas (baralho + prêmios restantes):
    1 − hg(N, m, k, 0) = 1 − C(N−m, k)/C(N, k). `hg` = `probabilidades.hipergeometrica` do Coletor (pela ponte).
    Também serve para "chance de tirar X ao pegar j prêmios agora": k = j (os pegos são uma amostra dos restantes, viradas)."""
    if not (0 <= m <= N and 0 <= k <= N):
        raise ValueError(f"estado impossível: N={N}, m={m}, k={k} (precisa 0 ≤ m ≤ N e 0 ≤ k ≤ N)")
    return 1.0 - hg(N, m, k, 0)


def alguma_premiada(N: int, copias_do_grupo: Iterable[int], k: int, hg: Callable[[int, int, int, int], float]) -> float:
    """P(pelo menos uma carta de um GRUPO está nos prêmios): soma as cópias do grupo (ex.: as essenciais; ou cartas que fazem o
    mesmo serviço). Classificar essencial/substituível/pouco relevante é decisão do analista (PRIZE_ANALYSIS.md §3)."""
    return premio_checado(N, sum(copias_do_grupo), k, hg)


# ------------------------------------------------------------------ prize trade (P4)

def trocas(seq_tomadas: Sequence[dict], jogador: str) -> list[dict]:
    """Trocas do ponto de vista de `jogador`: cada vez que um lado pega prêmios e o outro responde, uma troca =
    {"turno", "ganhei", "cedi", "saldo"}. Definição escolhida (registrar nos resultados): blocos consecutivos de tomadas do mesmo
    lado são somados; a troca fecha quando os dois lados pegaram. Tomada sem resposta no fim fica como troca aberta (cedi/ganhei 0)."""
    blocos = []
    for tk in seq_tomadas:
        if blocos and blocos[-1]["jogador"] == tk["jogador"]:
            blocos[-1]["n"] += tk["n"]
        else:
            blocos.append({"jogador": tk["jogador"], "n": tk["n"], "turno": tk["turno"]})
    saida = []
    i = 0
    while i < len(blocos):
        a = blocos[i]
        b = blocos[i + 1] if i + 1 < len(blocos) else None
        ganhei = (a["n"] if a["jogador"] == jogador else 0) + (b["n"] if b and b["jogador"] == jogador else 0)
        cedi = (a["n"] if a["jogador"] != jogador else 0) + (b["n"] if b and b["jogador"] != jogador else 0)
        saida.append({"turno": a["turno"], "ganhei": ganhei, "cedi": cedi, "saldo": ganhei - cedi, "aberta": b is None})
        i += 2
    return saida


def eficiencia(seq_tomadas: Sequence[dict], jogador: str) -> list[dict]:
    """Eficiência acumulada por turno: prêmios pegos por `jogador` ÷ prêmios cedidos (None enquanto não cedeu nada)."""
    ganhos = cedidos = 0
    saida = []
    for tk in seq_tomadas:
        if tk["jogador"] == jogador:
            ganhos += tk["n"]
        else:
            cedidos += tk["n"]
        saida.append({"turno": tk["turno"], "ganhos": ganhos, "cedidos": cedidos, "eficiencia": ganhos / cedidos if cedidos else None})
    return saida


# ------------------------------------------------------------------ disrupção, stall, mill (P5, P6)

# Lista de TRABALHO (Standard recente; incompleta; conferir a cada coleção — lacuna G23). Categoria por carta.
CATEGORIAS = {"Iono": "mão", "Judge": "mão", "Unfair Stamp": "mão", "Xerosic's Machinations": "mão", "Eri": "mão",
              "Crushing Hammer": "energia", "Enhanced Hammer": "energia",
              "Team Rocket's Watchtower": "habilidade (estádio)", "Path to the Peak": "habilidade (estádio)",
              "Boss's Orders": "puxar alvo", "Prime Catcher": "puxar alvo", "Counter Catcher": "puxar alvo",
              "Lost Vacuum": "ferramenta/estádio", "Tool Scrapper": "ferramenta"}
TIPOS_ACAO = ("jogada", "compra", "energia", "evolucao", "ataque", "recuo")


def categorias_disrupcao(eventos: Sequence[dict], tabela: dict | None = None) -> list[dict]:
    """Jogadas de disrupção: [{"turno", "jogador", "carta", "categoria"}] (eventos de tipo "jogada" com carta na tabela)."""
    tab = CATEGORIAS if tabela is None else tabela
    return [{"turno": e.get("turno"), "jogador": e.get("jogador"), "carta": e.get("carta"), "categoria": tab[e.get("carta")]}
            for e in eventos if e.get("tipo") == "jogada" and e.get("carta") in tab]


def desenvolvimento(eventos: Sequence[dict], jogador: str, turnos: Iterable[int]) -> dict:
    """O que `jogador` fez nos `turnos` dados: contagem por tipo de ação + se atacou. OBSERVADO; "travou" é interpretação."""
    ts = set(turnos)
    c = Counter(e["tipo"] for e in eventos if e.get("jogador") == jogador and e.get("turno") in ts and e.get("tipo") in TIPOS_ACAO)
    return {"acoes": sum(c.values()), "por_tipo": dict(c), "atacou": c.get("ataque", 0) > 0}


def turnos_do_jogador(eventos: Sequence[dict], jogador: str) -> list[int]:
    """Turnos em que `jogador` agiu, em ordem (no log cada turno tem um dono; o número é global)."""
    return sorted({e["turno"] for e in eventos if e.get("jogador") == jogador and e.get("tipo") in TIPOS_ACAO and e.get("turno")})


def fins(resumos: Iterable[dict]) -> Counter:
    """Contagem dos motivos de fim (prêmios, desistência, sem Pokémon, sem cartas para comprar = deck acabado)."""
    return Counter((r or {}).get("motivo") or "?" for r in resumos)


# ------------------------------------------------------------------ sequência (P7)

def acoes_do_turno(eventos: Sequence[dict], jogador: str, turno: int) -> list[str]:
    """Sequência de tipos de ação de `jogador` no `turno`, na ordem do log (só ações; compra do turno incluída)."""
    return [e["tipo"] for e in sorted(eventos, key=lambda e: e.get("linha", 0))
            if e.get("jogador") == jogador and e.get("turno") == turno and e.get("tipo") in TIPOS_ACAO]


def ngramas(seq: Sequence[str], n: int = 2) -> Counter:
    """n-gramas consecutivos de uma sequência de ações (padrões de ordem)."""
    if n < 1:
        raise ValueError("n deve ser >= 1")
    return Counter(tuple(seq[i:i + n]) for i in range(len(seq) - n + 1))


def antes_de(seq: Sequence[str], a: str, b: str) -> bool | None:
    """A primeira ação `a` vem antes da primeira `b` no turno? None se uma das duas não aconteceu."""
    if a not in seq or b not in seq:
        return None
    return seq.index(a) < seq.index(b)


# ------------------------------------------------------------------ tempo até evento e comparação pareada

def kaplan_meier(tempos: Sequence[float], eventos: Sequence[int]) -> list[dict]:
    """Estimador de Kaplan-Meier: S(t) = Π (1 − d_i/n_i). `eventos[i]` = 1 se o evento aconteceu em `tempos[i]` (ex.: venceu por
    prêmios no turno t), 0 se foi CENSURADO ali (ex.: desistência). Devolve [{"t", "em_risco", "eventos", "S"}]."""
    if len(tempos) != len(eventos) or not tempos:
        raise ValueError("tempos e eventos com o mesmo tamanho, não vazios")
    pares = sorted(zip(tempos, eventos))
    n = len(pares)
    S = 1.0
    saida = []
    i = 0
    while i < n:
        t = pares[i][0]
        d = c = 0
        while i < n and pares[i][0] == t:
            d += pares[i][1] == 1
            c += pares[i][1] == 0
            i += 1
        em_risco = n - (i - d - c)
        if d:
            S *= 1 - d / em_risco
        saida.append({"t": t, "em_risco": em_risco, "eventos": d, "censurados": c, "S": S})
    return saida


def diferenca_por_estrato(linhas: Sequence[tuple[Hashable, bool, float]]) -> dict:
    """Comparação PAREADA POR ESTADO: linhas = [(estrato, tratado, y)]. Em cada estrato com tratados e controles, diferença das
    médias; resultado = média ponderada pelo nº de tratados. Estratos sem os dois lados ficam fora (contados). Associação, não
    causa (CONTROL_AND_DISRUPTION.md §5). Faixa: chamar `sa_tools.bootstrap_agrupado` com esta função sobre grupos (partidas)."""
    por = defaultdict(lambda: ([], []))
    for estrato, tratado, y in linhas:
        por[estrato][0 if tratado else 1].append(y)
    num = peso = 0.0
    usados = fora = 0
    for t_, c_ in por.values():
        if t_ and c_:
            num += len(t_) * (sum(t_) / len(t_) - sum(c_) / len(c_))
            peso += len(t_)
            usados += 1
        else:
            fora += 1
    return {"diferenca": num / peso if peso else None, "estratos_usados": usados, "estratos_fora": fora, "tratados": int(peso)}


CLASSE = {n: "leitura" for n in ("valor_premio", "tomadas", "rota_executada", "mapa", "corrida", "rotas_possiveis", "mao_inicial",
                                 "zonas_desconhecidas", "premio_checado", "alguma_premiada", "trocas", "eficiencia",
                                 "categorias_disrupcao", "desenvolvimento", "turnos_do_jogador", "fins", "acoes_do_turno",
                                 "ngramas", "antes_de", "kaplan_meier", "diferenca_por_estrato")}
