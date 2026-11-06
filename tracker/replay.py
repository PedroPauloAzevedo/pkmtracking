"""
REPLAY: reconstrói a mesa linha a linha a partir do log.

Para cada linha do log guardamos uma "foto" (quadro): Pokémon Ativo e Banco de cada
jogador (com dano, energias e ferramentas), prêmios restantes (e quais deles já se sabe
quais são), Estádio, Pokémon nocauteados, a mão de cada jogador e o que aconteceu naquela
linha (o "destaque"). O painel só desenha essas fotos, uma depois da outra.

O log não mostra tudo, então só aparece com a face o que ele revela:
  - mão: a de quem exportou o log, carta a carta; a do adversário fica virada, menos o que
    ele buscou no baralho ou recebeu com o nome à vista (ver _Maos);
  - prêmios: os que quem exportou o log pegou, porque o jogo escreve o nome de cada um. Como
    os prêmios são separados na preparação, eles aparecem desde o começo (ver _premios_conhecidos).
    Os prêmios do adversário vêm como "A card" e ficam virados.
"""
import copy
import re

from . import cartas, leitor, regras_jogo

# Cartas que pegam Pokémon do descarte ou da mão ("X moved X's Y to their hand"), nunca da mesa.
CARTAS_FORA_DA_MESA = ("Night Stretcher", "Super Rod", "Lillie's Determination")


def _tipo_anexo(nome):
    e = cartas.por_nome(nome)
    if e and e["categoria"]:
        return "energia" if e["categoria"].lower() == "energy" else "ferramenta"
    return "energia" if re.search(r"\bEnergy\b", nome) else "ferramenta"


def _tipo_energia(nome):
    for t in cartas.TIPOS_ENERGIA:
        if re.search(rf"\b{t}\b", nome):
            return t
    e = cartas.por_nome(nome)
    if e and e["tipos"]:
        return e["tipos"][0]
    return "Special"


_custos = {}


def _custo_ataque(nome, golpe):
    """Quantas Energias o golpe pede (a menor entre as versões da carta), pela biblioteca de cartas; None se não souber."""
    if not _custos:
        _custos[None] = 0  # marca de "já lido" (também quando não há biblioteca)
        import json as _json
        for arq in sorted(cartas.PASTA_SETS.glob("*.json")) if cartas.PASTA_SETS.exists() else []:
            try:
                for c in _json.loads(arq.read_text(encoding="utf-8")).get("cards", []):
                    for a in c.get("attacks") or []:
                        k = (cartas.normalizar(c.get("name", "")), a.get("name", ""))
                        _custos[k] = min(_custos.get(k, 99), len(a.get("cost") or []))
            except (OSError, ValueError):
                continue
    return _custos.get((cartas.normalizar(nome), golpe))


def _ps_minimo(nome, golpes=()):
    """Menor PS entre as versões da carta que valem no Standard (Dunsparce: 60 e 70 -> 60).
    Usar o menor evita "achar" falta de dano num Pokémon que era a versão mais fraca.
    golpes: ataques/habilidades que ele usou na partida; ficam só as versões que têm todos eles
    (Dhelmise que usou Vengeful Anchor é a de 140 PS, não a de 120)."""
    ind = cartas.indice()
    chaves = ind.get("por_nome", {}).get(cartas.normalizar(nome)) or []
    validas = [k for k in chaves if cartas.legal_chave(k) is not False] or chaves
    if golpes:
        validas = [k for k in validas if set(golpes) <= set(",".join(k.split("|")[2:]).split(","))] or validas
    ps = [int(k.split("|")[1]) for k in validas if k.count("|") >= 1 and k.split("|")[1].isdigit()]
    return min(ps) if ps else 0


# ------------------------------------------------------------------ mão de cada jogador

# Cartas e golpes que descartam do BARALHO (não da mão).
DESCARTA_DO_BARALHO = ("Brilliant Blender", "Seek Inspiration")
# Habilidades que ligam Energia DA MÃO (as outras ligações em sublinha vêm do descarte ou do baralho, ex.: Rosa's Encouragement).
LIGA_DA_MAO = ("Teal Dance", "Ripening Charge")
# Cartas que embaralham a mão INTEIRA no baralho: o número de cartas da linha é o tamanho real da mão (serve de conferência).
MAO_INTEIRA = ("Judge", "Lillie's Determination", "Unfair Stamp", "Iono", "Xerosic's Machinations")


class _Maos:
    """MÃO DE CADA JOGADOR, montada a partir do log.

    Quem exportou o log vê o nome de tudo o que compra ("drew Dudunsparce", "drew 4 cards" + lista), então a mão
    dele é conhecida carta a carta. Do adversário o log só diz "drew a card": a carta fica virada, a não ser
    que ele a tenha BUSCADO no baralho ("Bia drew Meowth ex.") ou recebido de um efeito que mostra o nome.
    Toda carta jogada, ligada, evoluída, descartada ou devolvida ao baralho sai da mão.

    Mulligan de quem exportou: o log lista a primeira mão (a descartada) e não a nova. As 7 cartas ficam viradas
    e vão sendo descobertas quando ele as joga; no fim, `revelar_no_passado` mostra a face delas desde o começo
    (só para quem exportou: todas as outras compras dele têm nome, então a carta só pode ter vindo dessa mão).
    """

    def __init__(self, jogadores, exportou, P):
        self.P, self.exportou = P, exportou
        self.maos = {j: [] for j in jogadores}
        self.proximo = 0
        self.pendente = None     # ("nomear", j, [ids]) ou ("tirar", j, n, [nomes])
        self.reveladas = {}      # id -> nome: cartas viradas de quem exportou, descobertas quando ele as jogou
        self.estadio_saindo = None
        self.conferencia = []    # (jogador, tamanho montado, tamanho real) nas cartas que embaralham a mão inteira
        self.sem_explicacao = 0  # jogadas de quem exportou que a mão montada não explicava

    def _nova(self, j, nome=None):
        self.proximo += 1
        self.maos[j].append({"id": self.proximo, "nome": nome})
        return self.proximo

    def _tirar(self, j, nome):
        mao = self.maos.get(j)
        if mao is None:
            return
        for i, c in enumerate(mao):
            if c["nome"] == nome:
                mao.pop(i)
                return
        virada = next((i for i, c in enumerate(mao) if c["nome"] is None), None)
        if virada is not None:
            c = mao.pop(virada)
            if j == self.exportou:
                self.reveladas[c["id"]] = nome
        elif j == self.exportou:
            self.sem_explicacao += 1

    def _tirar_qualquer(self, j):
        mao = self.maos.get(j)
        if mao:
            virada = next((i for i, c in enumerate(mao) if c["nome"] is None), 0)
            mao.pop(virada)

    def fechar_pendente(self):
        """Linha nova sem a lista de nomes: o que estava pendente vale sem nomes (cartas viradas)."""
        if self.pendente and self.pendente[0] == "tirar":
            _, j, n, nomes, inteira = self.pendente
            for nome in nomes:
                self._tirar(j, nome)
            for _ in range(n - len(nomes)):
                self._tirar_qualquer(j)
            if inteira:  # a mão toda foi para o baralho
                self.maos[j] = []
        self.pendente = None

    def lista(self, itens):
        """Lista "• A, B, C" logo depois de uma compra/descarte/embaralhada: dá nome às cartas. Devolve True se usou."""
        if not self.pendente:
            return False
        if self.pendente[0] == "nomear":
            _, j, ids = self.pendente
            por_id = {c["id"]: c for c in self.maos[j]}
            for id_, nome in zip(ids, itens):
                if id_ in por_id:
                    por_id[id_]["nome"] = nome
            self.pendente = None
        else:
            self.pendente[3].extend(itens)
            self.fechar_pendente()
        return True

    def linha(self, l, sublinha, ultima_principal, estadio, em_jogo, embaralhou_poder):
        P = self.P
        m = re.match(rf"^{P} drew (a card|\d+ cards?)(?: for the opening hand)?\.$", l)
        if m:
            n = 1 if m.group(2) == "a card" else int(m.group(2).split()[0])
            ids = [self._nova(m.group(1)) for _ in range(n)]
            if n > 1 or m.group(2) != "a card":
                self.pendente = ("nomear", m.group(1), ids)
            return
        m = re.match(rf"^{P} drew (.+?)\.$", l)
        if m and " because " not in l and " and played " not in l:
            self._nova(m.group(1), m.group(2))  # comprou com nome (sua compra, ou busca no baralho)
            return
        m = re.match(rf"^{P} took a mulligan\.$", l)
        if m:
            self.maos[m.group(1)] = []
            for _ in range(7):
                self._nova(m.group(1))
            return
        m = re.match(rf"^(A card|.+?) was added to {P}'s hand\.$", l)
        if m:
            self._nova(m.group(2), None if m.group(1) == "A card" else m.group(1))
            return
        m = re.match(rf"^{P} moved {P}'s (.+?) (?:and all attached cards )?to their hand\.?$", l)
        if m:
            self._nova(m.group(2), m.group(3))
            return
        m = re.match(rf"^{P} played (.+?) to the (Bench|Active Spot|Stadium spot)\.$", l)
        if m and not sublinha:
            if m.group(3) == "Stadium spot":
                self.estadio_saindo = estadio["nome"] if estadio else None
            self._tirar(m.group(1), m.group(2))
            return
        m = re.match(rf"^{P} played (.+?)\.$", l)
        if m and not sublinha:
            # "played <Estádio em jogo>." = usou o efeito do Estádio (o que ele faz com a mão vem na linha seguinte,
            # ex.: Academy at Night "put a card on top of their deck"); "played <Pokémon em jogo>." = habilidade
            if not (estadio and estadio["nome"] == m.group(2)) and not em_jogo(m.group(1), m.group(2)):
                self._tirar(m.group(1), m.group(2))
            return
        m = re.match(rf"^{P} evolved .+? to (.+?) (?:in the Active Spot|on the Bench)\.$", l)
        if m:  # inclusive em sublinha (Rare Candy: a evolução sai da mão)
            self._tirar(m.group(1), m.group(2))
            return
        m = re.match(rf"^{P} attached (.+?) to .+? (?:in the Active Spot|on the Bench)\.$", l)
        if m:
            da_mao = not sublinha or re.search(rf"used (?:{'|'.join(map(re.escape, LIGA_DA_MAO))})\b", ultima_principal or "")
            if da_mao:
                self._tirar(m.group(1), m.group(2))
            return
        m = re.match(rf"^{P} discarded (\d+ cards|.+?)\.$", l)
        if m:
            if re.search(rf"(?:played|used) (?:{'|'.join(map(re.escape, DESCARTA_DO_BARALHO))})\.$", ultima_principal or ""):
                return
            j, o_que = m.group(1), m.group(2)
            if re.fullmatch(r"\d+ cards", o_que):
                self.pendente = ("tirar", j, int(o_que.split()[0]), [], False)
            elif o_que != self.estadio_saindo:  # Estádio trocado: "discarded <Estádio antigo>" sai da mesa, não da mão
                self._tirar(j, o_que)
            self.estadio_saindo = None
            return
        m = re.match(rf"^{P} (?:shuffled (a card|\d+ cards|.+?) into their deck|put (a card|\d+ cards) on (?:the )?(?:top|bottom) of their deck)\.$", l)
        if m and not embaralhou_poder and not re.match(rf"^{P} shuffled {P}'s ", l):  # "X's <Pokémon>" vem da mesa
            j, qtd = m.group(1), m.group(2) or m.group(3)
            nomes = []
            if re.fullmatch(r"a card|\d+ cards", qtd):
                n = 1 if qtd == "a card" else int(qtd.split()[0])
            else:  # "shuffled Rosa's Encouragement into their deck." = uma carta, com nome
                n, nomes = 1, [qtd]
            inteira = bool(re.match(rf"^{P} played (?:{'|'.join(map(re.escape, MAO_INTEIRA))})\.$", ultima_principal or ""))
            if inteira:
                self.conferencia.append((j, len(self.maos[j]), n))
            self.pendente = ("tirar", j, n, nomes, inteira)

    def revelar_no_passado(self, quadros):
        for q in quadros:
            for c in q["estado"]["maos"].get(self.exportou, []):
                if c["nome"] is None and c["id"] in self.reveladas:
                    c["nome"], c["inferida"] = self.reveladas[c["id"]], True


def gerar(texto, regras, _correcoes=None):
    """_correcoes: {linha do log: uid} da segunda passada (ver "contadores ambíguos" no fim)."""
    correcoes = _correcoes or {}
    ambiguos = []        # contadores postos num Pokémon com irmãos de mesmo nome: (linha, uid escolhido, dano, uids possíveis)
    novas_correcoes = {}
    golpes_vistos = {}   # (jogador, Pokémon) -> ataques/habilidades usados na partida
    atingidos = set()
    dados = leitor.ler_partida(texto, regras)
    jogadores = dados["jogadores"]
    if not jogadores:
        return {"jogadores": [], "quadros": []}
    P = "(" + "|".join(re.escape(j) for j in sorted(jogadores, key=len, reverse=True)) + ")"

    def outro(j):
        return next((x for x in jogadores if x != j), j)

    proximo_uid = [0]

    def novo_pokemon(nome, turno):
        proximo_uid[0] += 1
        return {"uid": proximo_uid[0], "nome": nome, "dano": 0, "anexos": [], "entrou": turno, "seq": proximo_uid[0] * 1000}

    seq = [10 ** 9]

    def mais_recente(j, nome):
        """Entre Pokémon com o mesmo nome, o que entrou ou evoluiu por último (quem acabou de agir)."""
        m = estado["mesa"][j]
        refs = ([(j, "ativo", None)] if m["ativo"] and m["ativo"]["nome"] == nome else []) + \
               [(j, "banco", i) for i, x in enumerate(m["banco"]) if x["nome"] == nome]
        return max(refs, key=lambda r: pegar(r)["seq"]) if refs else None

    def achar_uid(uid):
        for j, m in estado["mesa"].items():
            if m["ativo"] and m["ativo"]["uid"] == uid:
                return j, "ativo", None
            for i, x in enumerate(m["banco"]):
                if x["uid"] == uid:
                    return j, "banco", i
        return None

    maos = _Maos(jogadores, dados["resumo"].get("exportou"), P)
    estado = {
        "turno": 0, "vez": None, "estadio": None, "resultado": None,
        "mesa": {j: {"ativo": None, "banco": [], "premios": regras_jogo.PREMIOS_PARTIDA, "nocauteados": []} for j in jogadores},
        "maos": maos.maos,
    }

    def achar(j, nome, zona=None, procurar_no_outro=True):
        m = estado["mesa"][j]
        if zona in (None, "ativo") and m["ativo"] and m["ativo"]["nome"] == nome:
            return j, "ativo", None
        if zona in (None, "banco"):
            for i, p in enumerate(m["banco"]):
                if p["nome"] == nome:
                    return j, "banco", i
        if zona == "banco" and m["ativo"] and m["ativo"]["nome"] == nome:
            return j, "ativo", None
        if zona == "ativo":
            return achar(j, nome, "banco", procurar_no_outro)
        if procurar_no_outro:  # o log às vezes erra o dono (ex.: "put damage counters on X's ...")
            r = achar(outro(j), nome, None, False)
            if r:
                return r
        return None

    def pegar(ref):
        j, zona, i = ref
        m = estado["mesa"][j]
        return m["ativo"] if zona == "ativo" else m["banco"][i]

    def achar_evoluivel(j, nome, zona):
        """Regra do jogo: não se evolui um Pokémon que entrou em jogo (ou evoluiu) neste turno.
        Com vários Pokémon de mesmo nome, prefere um que já estava em jogo antes deste turno."""
        m = estado["mesa"][j]
        cands = ([(j, "ativo", None)] if zona == "ativo" and m["ativo"] and m["ativo"]["nome"] == nome else []) + \
                ([(j, "banco", i) for i, p in enumerate(m["banco"]) if p["nome"] == nome] if zona == "banco" else [])
        if not cands:
            return achar(j, nome, zona, False)
        prontos = [r for r in cands if pegar(r)["entrou"] < estado["turno"]]
        return (prontos or cands)[0]

    def remover(ref):
        j, zona, i = ref
        m = estado["mesa"][j]
        if zona == "ativo":
            p, m["ativo"] = m["ativo"], None
        else:
            p = m["banco"].pop(i)
        return p

    def dono_dos_contadores(n_linha, j, dono_escrito, alvo):
        """O jogo escreve "X put N damage counters on X's Y" mesmo quando Y é do ADVERSÁRIO
        (ex.: Cursed Blast do Dusclops, Phantom Dive do Dragapult ex). Quem é o dono de verdade:
          1. se Y é nocauteado logo em seguida, o dono é quem perdeu o Pokémon;
          2. se veio de um ataque ou habilidade de X ("X's ... used ...") e o adversário tem um Y, é do adversário;
          3. senão, vale o que está escrito.
        Exceção: o Estádio Risky Ruins ("Risky Ruins was activated.") põe contadores no Básico que X acabou de jogar no Banco,
        e o jogo escreve como dono quem pôs o ESTÁDIO em jogo (ex.: "Bia put 2 damage counters on Ana's Budew." logo depois de
        "Bia played Budew to the Bench.", com o Risky Ruins da Ana). O dono é sempre X."""
        if ultima_principal == "Risky Ruins was activated.":
            return j
        if dono_escrito != j:
            return dono_escrito
        for seguinte in linhas[n_linha:n_linha + 6]:
            s = leitor.limpar_linha(seguinte)
            ko = re.match(rf"^{P}'s (.+?) (?:is now|was) Knocked Out", s)
            if ko and ko.group(2) == alvo:
                return ko.group(1)
            if re.match(rf"^(?:Turn # \d+ - )?{P}'s Turn$", s) or re.search(r" damage counters? (?:on|from) ", s):
                break
        if ultima_principal and re.match(rf"^{re.escape(j)}'s .+? used ", ultima_principal) and achar(outro(j), alvo, None, False):
            return outro(j)
        return dono_escrito

    def achar_nocauteado(j, nome):
        """Com dois Pokémon de mesmo nome do mesmo lado, cai o que está mais perto (ou além) dos PS,
        não sempre o Ativo (ex.: o Phantom Dive nocauteia o do Banco). Empate: o Ativo."""
        m = estado["mesa"][j]
        cands = ([(j, "ativo", None)] if m["ativo"] and m["ativo"]["nome"] == nome else []) + \
                [(j, "banco", i) for i, p in enumerate(m["banco"]) if p["nome"] == nome]
        if len(cands) <= 1:
            return achar(j, nome, "ativo")
        return max(cands, key=lambda r: pegar(r)["dano"])  # mesmo nome, mesmos PS: o de mais dano  # max devolve o primeiro no empate (o Ativo)

    def achar_alvo_dos_contadores(dono, alvo, n_linha=None, dano=0):
        """Com dois Pokémon de mesmo nome do mesmo lado: se o ataque acabou de acertar o Ativo com esse nome,
        os contadores extras vão para o do Banco (ex.: Phantom Dive só põe contadores no Banco).
        O log não diz qual deles recebeu: a escolha fica anotada e pode ser corrigida pelo nocaute (fim de gerar)."""
        m = estado["mesa"].get(dono)
        irmaos = ([(dono, "ativo", None)] if m and m["ativo"] and m["ativo"]["nome"] == alvo else []) + \
                 ([(dono, "banco", i) for i, p in enumerate(m["banco"]) if p["nome"] == alvo] if m else [])
        if n_linha in correcoes:
            certo = next((r for r in irmaos if pegar(r)["uid"] == correcoes[n_linha]), None)
            if certo:
                return certo
        ref = None
        golpe = re.match(rf"^{P}'s .+? used .+? on {P}'s (.+?) for \d+ damage", ultima_principal or "")
        if golpe and golpe.group(2) == dono and golpe.group(3) == alvo:
            ref = next((r for r in irmaos if r[1] == "banco"), None)
        ref = ref or achar(dono, alvo)
        if ref and len(irmaos) > 1 and n_linha:
            ambiguos.append((n_linha, pegar(ref)["uid"], dano, [pegar(r)["uid"] for r in irmaos]))
        return ref

    def dono_do_anexo(j, nome, carta, sublinha):
        """De qual Pokémon saiu a carta presa em "X was discarded from j's Y.". Com dois Pokémon de mesmo nome o log
        não diz qual (ex.: dois Dreepy em jogo e só o que recuou tinha a Energia). Nesta ordem:
          1. sublinha logo depois de um recuo: o que recuou (o custo de recuo sai só dele);
          2. linha solta depois do nocaute de um Pokémon com esse nome: o nocauteado (o jogo lista o que estava preso
             nele); o irmão de mesmo nome que continua em jogo não perde nada;
          3. senão, em jogo, o que tem a carta presa (o Ativo primeiro: Crushing Hammer e ataques costumam mirar nele).
        Devolve (Pokémon, está em jogo?) ou (None, False)."""
        tem = lambda p: p["nome"] == nome and any(a["nome"] == carta for a in p["anexos"])
        if sublinha and recuou and recuou[0] == j:
            ref = achar_uid(recuou[1])
            if ref and not tem(pegar(ref)):
                mover_ambigua(j, pegar(ref), carta)  # a carta ligada "a um dos X" era deste, que recuou pagando com ela
            if ref and tem(pegar(ref)):
                return pegar(ref), True
        if not sublinha and any(dono == j and p["nome"] == nome for dono, p in caidos):
            return next((p for dono, p in reversed(caidos) if dono == j and tem(p)), None), False
        m = estado["mesa"][j]
        for p in ([m["ativo"]] if m["ativo"] else []) + m["banco"]:
            if tem(p):
                return p, True
        return None, False

    def mover_ambigua(j, destino, nome=None, energia=False):
        """Uma carta ligada de forma ambígua num irmão é, pelas provas, do `destino`: muda agora e anota a linha da ligação
        para a 2ª passada pôr a carta no lugar certo desde o começo. nome: essa carta; energia=True: qualquer Energia."""
        m_ = estado["mesa"][j]
        for x in ([m_["ativo"]] if m_["ativo"] else []) + m_["banco"]:
            if x is destino:
                continue
            k = next((k for k, a in enumerate(x["anexos"]) if a.get("ambigua")
                      and (a["nome"] == nome if nome else a["tipo"] == "energia")), None)
            if k is not None:
                a = x["anexos"].pop(k)
                destino["anexos"].append(a)
                if not correcoes and a.get("linha"):
                    novas_correcoes[a["linha"]] = destino["uid"]
                return True
        return False

    def tirar_listados(j, p, itens, completa=False):
        """"N cards were discarded from j's Y." + lista "•": tira de Y as cartas presas que a lista nomeia (as pré-evoluções
        embaixo dele também aparecem e são ignoradas). Y é o nocauteado (linha logo depois do nocaute) ou um Pokémon em jogo
        (efeito de ataque, ex.: Metallic Hammer descarta 3 Energias). Carta que Y não tem no replay veio de uma ligação
        ambígua ("to Metang on the Bench" com vários Metang, ex.: Metal Maker): sai do irmão que a recebeu, porque a lista
        prova que ela estava em Y."""
        for nome in itens:
            if not any(a["nome"] == nome for a in p["anexos"]):
                mover_ambigua(j, p, nome)
            i = next((k for k, a in enumerate(p["anexos"]) if a["nome"] == nome), None)
            if i is not None:
                p["anexos"].pop(i)
        if completa:  # lista do nocaute: é tudo o que estava preso nele; o resto ambíguo era de um irmão ainda em jogo
            for a in [a for a in p["anexos"] if a.get("ambigua")]:
                destino = next((achar_uid(u) for u in a.get("candidatos", []) if u != p["uid"] and achar_uid(u)), None)
                if destino:
                    p["anexos"].remove(a)
                    pegar(destino)["anexos"].append(a)
                    if not correcoes and a.get("linha"):
                        novas_correcoes[a["linha"]] = pegar(destino)["uid"]

    def premio_logo_adiante(n_linha, j):
        """O log às vezes escreve cartas de prêmio ANTES de "X took N Prize cards." (visto em jogadas que valem 3 prêmios):
        procura esse "took" do mesmo jogador nas próximas linhas, sem passar do fim do turno."""
        for seguinte in linhas[n_linha:n_linha + 10]:
            s = leitor.limpar_linha(seguinte)
            if re.match(rf"^(?:Turn # \d+ - )?{P}'s Turn$", s):
                return False
            pegou = re.match(rf"^{P} took (?:a|\d+) Prize cards?\.$", s)
            if pegou and pegou.group(1) == j:
                return True
        return False

    quadros = []
    premios_pegos = []     # cartas de prêmio pegas: {jogador, nome (None = "A card"), quadro (em que saiu dos prêmios), turno}
    premio_aberto = {}     # jogador -> {faltam, quadro, turno}: o "took N Prize cards" cujas cartas ainda vão aparecer
    adiantados = {}        # jogador -> nº de cartas de prêmio que o log escreveu antes do "took" (já saíram dos prêmios)
    ultima_principal = ""  # última linha que não começa com "-" (o ataque ou habilidade que gerou as sublinhas)
    recuou = None          # (jogador, uid) de quem acabou de recuar: a Energia descartada no recuo sai só dele
    caidos = []            # (jogador, Pokémon) nocauteados neste turno: as cartas presas a eles saem com eles
    descarte_lista = None  # (jogador, Pokémon) de "N cards were discarded from X's Y.": a lista "•" seguinte diz quais
    lista_pendente = None
    poder = None          # Pokémon que acabou de usar habilidade (ex.: Dudunsparce "Run Away Draw")
    embaralhou = False    # "X shuffled N cards into their deck." logo depois desse poder
    linhas = texto.splitlines()
    for n_linha, bruta in enumerate(linhas, start=1):
        l = leitor.limpar_linha(bruta)
        if not l:
            continue
        sublinha = bruta.lstrip().startswith(("-", "•"))
        if not sublinha:
            embaralhou = False
        if l.startswith("•"):
            itens = [c.strip() for c in l.lstrip("• ").split(",") if c.strip()]
            if maos.lista(itens) and quadros:  # a lista deu nome às cartas compradas/descartadas: atualiza a foto
                quadros[-1]["estado"]["maos"] = copy.deepcopy(maos.maos)
            if embaralhou and poder and poder[1] in itens:
                # O Pokémon que usou a habilidade voltou para o baralho (com a pré-evolução embaixo dele).
                ref = achar_uid(poder[2])
                if ref:
                    remover(ref)
                    quadros.append(_quadro(n_linha, f"{poder[1]} voltou para o baralho: " + ", ".join(itens), estado,
                                           {"tipo": "descarte", "jogador": poder[0], "carta": poder[1]}))
                embaralhou, poder = False, None
                continue
            if descarte_lista:
                tirar_listados(descarte_lista[0], descarte_lista[1], itens, descarte_lista[2])
                descarte_lista = None
                if quadros:
                    quadros[-1]["estado"]["mesa"] = copy.deepcopy(estado["mesa"])
                    quadros[-1].setdefault("detalhes", []).append(", ".join(itens))
                continue
            if lista_pendente:
                j, zona = lista_pendente
                for c in itens:
                    p = novo_pokemon(c, estado["turno"])
                    if zona == "Active Spot" and not estado["mesa"][j]["ativo"]:
                        estado["mesa"][j]["ativo"] = p
                    else:
                        estado["mesa"][j]["banco"].append(p)
                lista_pendente = None
                quadros.append(_quadro(n_linha, "Cartas para o Banco: " + ", ".join(itens), estado,
                                       {"tipo": "banco", "jogador": j, "cartas": itens}))
            elif quadros:
                quadros[-1].setdefault("detalhes", []).append(", ".join(itens))
            continue
        if l == "Setup":
            quadros.append(_quadro(n_linha, "Preparação da partida", estado, {"tipo": "turno"}))
            continue

        d = {"tipo": "info"}
        m = None
        descarte_lista = None
        if not sublinha:
            poder = None
            recuou = None
            ultima_principal = l
            atingidos = set()  # Pokémon que já levaram dano "took N damage" nesta mesma ação
            usou = re.match(rf"^{P}'s (.+?) used (.+?)(?: on .+)?\.$", l)
            if usou:  # para saber qual versão da carta ele é (ver _ps_minimo)
                golpes_vistos.setdefault((usou.group(1), usou.group(2)), set()).add(cartas.normalizar(usou.group(3)))
        if poder and re.match(rf"^{P} shuffled \d+ cards? into their deck\.$", l) and l.startswith(poder[0]):
            embaralhou = True
        if not re.match(r"^\d+ drawn cards\.$", l):  # "- 7 drawn cards." vem entre a compra e a lista dos nomes
            maos.fechar_pendente()
        maos.linha(l, sublinha, ultima_principal, estado["estadio"], lambda j, c: mais_recente(j, c) is not None, embaralhou)

        def casa(padrao):
            nonlocal m
            m = re.match(padrao, l)
            return m

        if casa(rf"^(?:Turn # \d+ - )?{P}'s Turn$"):
            estado["turno"] += 1
            estado["vez"] = m.group(1)
            d = {"tipo": "turno", "jogador": m.group(1)}
            premio_aberto.clear()  # as cartas de prêmio aparecem sempre no mesmo turno em que foram pegas
            adiantados.clear()
            caidos.clear()
        elif casa(rf"^{P} drew \d+ cards? and played them to the (Bench|Active Spot)\.$"):
            lista_pendente = (m.group(1), m.group(2))
            d = {"tipo": "info", "jogador": m.group(1)}
        elif casa(rf"^{P} drew (.+?) and played it to the (Bench|Active Spot)\.$") or \
                casa(rf"^{P} played (.+?) to the (Bench|Active Spot)\.$"):
            j, c, zona = m.groups()
            p = novo_pokemon(c, estado["turno"])
            mesa = estado["mesa"][j]
            if zona == "Active Spot" and not mesa["ativo"]:
                mesa["ativo"] = p
            else:
                mesa["banco"].append(p)
            d = {"tipo": "entrou", "jogador": j, "carta": c, "uid": p["uid"]}
        elif casa(rf"^{P} played (.+?) to the Stadium spot\.$"):
            estado["estadio"] = {"nome": m.group(2), "dono": m.group(1)}
            d = {"tipo": "jogada", "jogador": m.group(1), "carta": m.group(2)}
        elif casa(rf"^{P} evolved (.+?) to (.+?) (in the Active Spot|on the Bench)\.$"):
            j, de, para, onde = m.groups()
            ref = achar_evoluivel(j, de, "ativo" if "Active" in onde else "banco")
            if ref:
                p = pegar(ref)
                p["nome"] = para
                p["entrou"] = estado["turno"]
                seq[0] += 1
                p["seq"] = seq[0]
                d = {"tipo": "evolucao", "jogador": j, "carta": para, "uid": p["uid"], "de": de}
            else:
                d = {"tipo": "evolucao", "jogador": j, "carta": para}
        elif casa(rf"^{P} attached (.+?) to (.+?) (in the Active Spot|on the Bench)\.$"):
            j, c, alvo, onde = m.groups()
            ref = achar(j, alvo, "ativo" if "Active" in onde else "banco", False)
            certo = achar_uid(correcoes[n_linha]) if n_linha in correcoes else None
            if certo and pegar(certo)["nome"] == alvo:
                ref = certo  # 2ª passada: as provas mostraram de qual dos Pokémon de mesmo nome era
            tipo = _tipo_anexo(c)
            if ref:
                p = pegar(ref)
                anexo = {"nome": c, "tipo": tipo, "energia": _tipo_energia(c) if tipo == "energia" else None}
                if "Bench" in onde and sum(1 for x in estado["mesa"][j]["banco"] if x["nome"] == alvo) > 1:
                    anexo["ambigua"] = True  # vários com esse nome no Banco (ex.: Metal Maker): pode ser de um irmão
                    anexo["linha"] = n_linha
                    anexo["candidatos"] = [x["uid"] for x in estado["mesa"][j]["banco"] if x["nome"] == alvo]
                p["anexos"].append(anexo)
                d = {"tipo": "anexo", "jogador": j, "carta": c, "uid": p["uid"]}
            else:
                d = {"tipo": "anexo", "jogador": j, "carta": c}
        elif casa(rf"^{P} retreated (.+?) to the Bench\.$"):
            j, c = m.groups()
            mesa = estado["mesa"][j]
            if mesa["ativo"] and mesa["ativo"]["nome"] == c:
                mesa["banco"].append(mesa["ativo"])
                uid = mesa["ativo"]["uid"]
                mesa["ativo"] = None
                recuou = (j, uid)
                d = {"tipo": "recuo", "jogador": j, "carta": c, "uid": uid}
        elif casa(rf"^{P}'s (.+?) was switched with {P}'s (.+?) to become the Active Pokémon\.$"):
            j, a, _, b = m.groups()
            mesa = estado["mesa"][j]
            ref_b = achar(j, b, "banco", False)
            if ref_b and ref_b[1] == "banco":
                novo = remover(ref_b)
                if mesa["ativo"]:
                    mesa["banco"].append(mesa["ativo"])
                mesa["ativo"] = novo
                d = {"tipo": "troca", "jogador": j, "carta": b, "uid": novo["uid"]}
        elif casa(rf"^{P}'s (.+?) is now in the Active Spot\.$"):
            j, c = m.groups()
            mesa = estado["mesa"][j]
            if not (mesa["ativo"] and mesa["ativo"]["nome"] == c):
                ref = achar(j, c, "banco", False)
                if ref and ref[1] == "banco":
                    novo = remover(ref)
                    if mesa["ativo"]:
                        mesa["banco"].append(mesa["ativo"])
                    mesa["ativo"] = novo
                    d = {"tipo": "troca", "jogador": j, "carta": c, "uid": novo["uid"]}
            else:
                d = {"tipo": "info", "jogador": j, "carta": c, "uid": mesa["ativo"]["uid"]}
        elif casa(rf"^{P}'s (.+?) used (.+?)(?: on {P}'s (.+?))?(?: for (\d+) damage)?\."):
            j, atacante, golpe, dono_alvo, alvo, dano = m.groups()
            # ataque sai sempre do Ativo; habilidade pode vir do Banco: usa o que agiu por último
            ref_at = achar(j, atacante, "ativo", False) if dano else (mais_recente(j, atacante) or achar(j, atacante, None, False))
            if not dano and ref_at:
                poder = (j, atacante, pegar(ref_at)["uid"])
            if dano and ref_at:  # o golpe saiu: o atacante tinha as Energias do custo (as ambíguas de um irmão eram dele)
                p = pegar(ref_at)
                falta = (_custo_ataque(atacante, golpe) or 0) - sum(1 for a in p["anexos"] if a["tipo"] == "energia")
                while falta > 0 and mover_ambigua(j, p, energia=True):
                    falta -= 1
            d = {"tipo": "ataque" if dano else "habilidade", "jogador": j, "carta": atacante, "golpe": golpe,
                 "uid": pegar(ref_at)["uid"] if ref_at else None}
            if alvo and dano:
                ref = achar(dono_alvo, alvo, "ativo")
                if ref:
                    p = pegar(ref)
                    p["dano"] += int(dano)
                    d.update({"alvo_uid": p["uid"], "dano": int(dano), "alvo": alvo})
            ko = re.search(rf"\. {P}'s ([^.]+?) (?:is now|was) Knocked Out", l)
            if ko:  # ataque e nocaute na mesma linha (formato antigo do log)
                ref = achar(ko.group(1), ko.group(2), "ativo")
                if ref:
                    morto = remover(ref)
                    caidos.append((ref[0], morto))
                    estado["mesa"][ref[0]]["nocauteados"].append(morto["nome"])
                    d["nocaute_uid"] = morto["uid"]
        elif casa(rf"^{P} put (\d+|a) damage counters? on {P}'s (.+?)\.$"):  # "put a damage counter" = 1
            j, qtd, dono_alvo, alvo = m.groups()
            qtd = 1 if qtd == "a" else qtd
            dono_alvo = dono_dos_contadores(n_linha, j, dono_alvo, alvo)
            ref = achar_alvo_dos_contadores(dono_alvo, alvo, n_linha, 10 * int(qtd))
            if ref:
                p = pegar(ref)
                p["dano"] += 10 * int(qtd)
                d = {"tipo": "dano", "jogador": j, "carta": alvo, "alvo_uid": p["uid"], "dano": 10 * int(qtd)}
        elif casa(rf"^{P}'s (.+?) took (\d+) damage\.$"):
            # dano extra de um ataque em outro Pokémon (ex.: Torrential Pump do Ogerpon ex também acerta o Banco)
            dono_alvo, alvo, dano = m.group(1), m.group(2), int(m.group(3))
            ref = achar_alvo_dos_contadores(dono_alvo, alvo, n_linha, dano)
            if ref and pegar(ref)["uid"] in atingidos:  # o mesmo golpe acerta vários (ex.: Trifrost): outro de mesmo nome
                mesa = estado["mesa"][dono_alvo]
                livres = ([(dono_alvo, "ativo", None)] if mesa["ativo"] and mesa["ativo"]["nome"] == alvo else []) + \
                         [(dono_alvo, "banco", i) for i, x in enumerate(mesa["banco"]) if x["nome"] == alvo]
                ref = next((r for r in livres if pegar(r)["uid"] not in atingidos), ref)
            if ref:
                p = pegar(ref)
                atingidos.add(p["uid"])
                p["dano"] += dano
                d = {"tipo": "dano", "jogador": outro(dono_alvo), "carta": alvo, "alvo_uid": p["uid"], "dano": dano}
        elif casa(rf"^{P} moved (\d+|a) damage counters? from {P}'s (.+?) to {P}'s (.+?)\.$"):
            # ex.: Munkidori "Adrena-Brain": tira contadores de um Pokémon seu e põe num do adversário.
            # O jogo escreve o nome de quem usou também no Pokémon que recebe (mesmo defeito do "put ... on").
            j, qtd, dono_origem, origem, dono_alvo, alvo = m.groups()
            dano = 10 * (1 if qtd == "a" else int(qtd))
            ref_origem = achar(dono_origem, origem)
            if ref_origem:
                p = pegar(ref_origem)
                p["dano"] = max(0, p["dano"] - dano)
            dono_alvo = dono_dos_contadores(n_linha, j, dono_alvo, alvo)
            ref = achar_alvo_dos_contadores(dono_alvo, alvo, n_linha, dano)
            if ref:
                p = pegar(ref)
                p["dano"] += dano
                d = {"tipo": "dano", "jogador": j, "carta": alvo, "alvo_uid": p["uid"], "dano": dano}
        elif re.search(rf"{P}'s ([^.]+?) (?:is now|was) Knocked Out", l):
            m = re.search(rf"{P}'s ([^.]+?) (?:is now|was) Knocked Out", l)
            j, c = m.groups()
            ref = achar_nocauteado(j, c)
            uid = None
            if ref:
                p = remover(ref)
                caidos.append((ref[0], p))
                uid = p["uid"]
                falta = _ps_minimo(c, golpes_vistos.get((j, c), ())) - p["dano"]
                if p["dano"] and falta > 0 and not correcoes:
                    # Caiu com menos dano que os PS: um contador ambíguo de mesmo valor, posto num irmão, era dele.
                    erro = next((a for a in ambiguos if a[2] == falta and a[1] != uid and uid in a[3]
                                 and a[0] not in novas_correcoes), None)
                    if erro:
                        novas_correcoes[erro[0]] = uid
                estado["mesa"][ref[0]]["nocauteados"].append(p["nome"])
            d = {"tipo": "nocaute", "jogador": j, "carta": c, "uid": uid}
        elif casa(rf"^\d+ cards were discarded from {P}'s (.+?)\.$"):
            j, alvo = m.groups()
            caido = re.search(rf"{re.escape(j)}'s {re.escape(alvo)} (?:is now|was) Knocked Out", ultima_principal or "")
            p = next((x for dono, x in reversed(caidos) if dono == j and x["nome"] == alvo), None) if caido else None
            if not p:
                ref = achar(j, alvo, None, False)
                p = pegar(ref) if ref else None
            if p:
                descarte_lista = (j, p, bool(caido))
            d = {"tipo": "descarte", "jogador": j, "carta": alvo}
            if p and not caido:
                d["uid"] = p["uid"]
        elif casa(rf"^(.+?) was discarded from {P}'s (.+?)\.$"):
            c, j, alvo = m.groups()
            p, em_jogo = dono_do_anexo(j, alvo, c, sublinha)
            if p:
                for i, a in enumerate(p["anexos"]):
                    if a["nome"] == c:
                        p["anexos"].pop(i)
                        break
            d = {"tipo": "descarte", "jogador": j, "carta": c}
            if p and em_jogo:
                d["uid"] = p["uid"]
        elif casa(rf"^{P} took (a|\d+) Prize cards?\.$"):
            j = m.group(1)
            q = 1 if m.group(2) == "a" else int(m.group(2))
            resto = max(0, q - adiantados.pop(j, 0))  # as que o log já escreveu antes deste "took" já saíram
            estado["mesa"][j]["premios"] = max(0, estado["mesa"][j]["premios"] - resto)
            d = {"tipo": "premio", "jogador": j, "qtd": q}
            premio_aberto[j] = {"faltam": resto, "quadro": len(quadros), "turno": estado["turno"]}
        elif casa(rf"^(A card|.+?) was added to {P}'s hand\.$") and (
                (premio_aberto.get(m.group(2)) or {}).get("faltam") or premio_logo_adiante(n_linha, m.group(2))):
            # Uma linha por carta de prêmio: com o nome para quem exportou o log, "A card" para o adversário (a mão recebe
            # a carta em _Maos.linha). Em geral vem logo depois do "took"; numa jogada que vale 3 prêmios o jogo já
            # escreveu parte delas antes do "took" e o resto depois do nocaute.
            nome = None if m.group(1) == "A card" else m.group(1)
            j = m.group(2)
            aberto = premio_aberto.get(j)
            if aberto and aberto["faltam"]:
                aberto["faltam"] -= 1
                premios_pegos.append({"jogador": j, "nome": nome, "quadro": aberto["quadro"], "turno": aberto["turno"]})
            else:  # escrita antes do "took": sai dos prêmios agora
                adiantados[j] = adiantados.get(j, 0) + 1
                estado["mesa"][j]["premios"] = max(0, estado["mesa"][j]["premios"] - 1)
                premios_pegos.append({"jogador": j, "nome": nome, "quadro": len(quadros), "turno": estado["turno"]})
            d = {"tipo": "premio", "jogador": j}
            if nome:
                d["carta"] = nome
        elif casa(rf"^{P} (?:moved|shuffled|put) {P}'s (.+?) (?:and all attached cards )?(?:to their hand|into their deck)"):
            j, dono, c = m.groups()
            # Night Stretcher e companhia tiram a carta do DESCARTE (ou da mão), não da mesa:
            # o Pokémon de mesmo nome que está em jogo continua lá.
            do_descarte = re.match(rf"^{P} played ({'|'.join(map(re.escape, CARTAS_FORA_DA_MESA))})\.$", ultima_principal or "")
            ref = None if do_descarte else achar(dono, c, None, False)
            if ref:
                remover(ref)
            d = {"tipo": "info", "jogador": j, "carta": c}
        elif casa(rf"^{P} healed (\d+) damage from {P}'s (.+?)\."):
            j, qtd, dono, c = m.groups()
            ref = achar(dono, c, None, False)
            if ref:
                p = pegar(ref)
                p["dano"] = max(0, p["dano"] - int(qtd))
            d = {"tipo": "info", "jogador": j, "carta": c}
        elif casa(rf"^{P}'s (.+?) healed (\d+) damage\.$"):  # outro formato (ex.: Hydrapple ex "Ripening Charge")
            dono, c, qtd = m.groups()
            ref = achar(dono, c, None, False)
            if ref:
                p = pegar(ref)
                p["dano"] = max(0, p["dano"] - int(qtd))
            d = {"tipo": "info", "jogador": dono, "carta": c}
        elif casa(rf"^{P} played (.+?)\.$"):
            d = {"tipo": "jogada", "jogador": m.group(1), "carta": m.group(2)}
            ref = mais_recente(m.group(1), m.group(2))
            if ref:  # "played <Pokémon em jogo>." = usou a habilidade desse Pokémon
                poder = (m.group(1), m.group(2), pegar(ref)["uid"])
                d = {"tipo": "habilidade", "jogador": m.group(1), "carta": m.group(2), "uid": poder[2]}
        elif casa(rf"^{P} drew (?!a card|\d+ )(.+?)\.$"):
            d = {"tipo": "compra", "jogador": m.group(1), "carta": m.group(2)}
        elif re.search(rf"{P} wins\.?$", l):
            estado["resultado"] = re.search(rf"{P} wins\.?$", l).group(1)
            d = {"tipo": "fim", "jogador": estado["resultado"]}
        else:
            j = next((x for x in jogadores if l.startswith(x + " ") or l.startswith(x + "'s ")), None)
            d = {"tipo": "info", "jogador": j}
        quadros.append(_quadro(n_linha, l, estado, d))

    if novas_correcoes:  # contadores ou Energias ambíguos: refaz a partida com a escolha que as provas revelaram
        return gerar(texto, regras, novas_correcoes)
    maos.fechar_pendente()
    maos.revelar_no_passado(quadros)
    _premios_conhecidos(quadros, premios_pegos)
    return {"jogadores": jogadores, "primeiro": dados["resumo"]["primeiro"], "vencedor": dados["resumo"]["vencedor"],
            "turnos": estado["turno"], "quadros": quadros, "cartas": _cartas_usadas(quadros),
            "exportou": maos.exportou,
            "conferencia_maos": {"tamanho": maos.conferencia, "sem_explicacao": maos.sem_explicacao}}


def _premios_conhecidos(quadros, pegos):
    """PRÊMIOS COM A FACE CONHECIDA, em cada foto: m["premios_conhecidos"] = [{"nome", "turno"}].
    Quem exportou o log vê o nome de cada prêmio que pega ("Ana took a Prize card." e logo depois "Judge was
    added to Ana's hand."); do adversário vem "A card". Os 6 prêmios são separados na preparação e nenhuma linha
    do log os troca depois, então a carta pega estava ali desde o começo: em cada foto, os prêmios conhecidos
    são os que o jogador AINDA VAI pegar (turno = quando pegou). Os outros prêmios restantes ficam virados.
    pegos: cartas de prêmio com o quadro em que saíram dos prêmios (o do "took", ou o da própria linha quando o
    log a escreveu antes do "took"). Se o log não trouxer o nome de um prêmio, ele fica virado."""
    pegos = sorted(pegos, key=lambda c: c["quadro"])  # na ordem em que vão sair dos prêmios
    for i, q in enumerate(quadros):
        for j, m in q["estado"]["mesa"].items():
            futuros = [{"nome": c["nome"], "turno": c["turno"]} for c in pegos
                       if c["jogador"] == j and c["quadro"] > i and c["nome"]]
            m["premios_conhecidos"] = futuros[:m["premios"]]


def _quadro(n_linha, texto, estado, destaque):
    return {"linha": n_linha, "texto": texto, "turno": estado["turno"], "vez": estado["vez"],
            "destaque": destaque, "estado": copy.deepcopy({k: estado[k] for k in ("estadio", "mesa", "resultado", "maos")})}


def _cartas_usadas(quadros):
    """Nome -> dados da arte básica de todas as cartas que aparecem no replay."""
    nomes = set()
    for q in quadros:
        c = q["destaque"].get("carta")
        if c:
            nomes.add(c)
        for m in q["estado"]["mesa"].values():
            for p in ([m["ativo"]] if m["ativo"] else []) + m["banco"]:
                nomes.add(p["nome"])
                nomes.update(a["nome"] for a in p["anexos"])
        if q["estado"]["estadio"]:
            nomes.add(q["estado"]["estadio"]["nome"])
    return {n: cartas.info_publica(cartas.por_nome(n)) for n in sorted(nomes)}
