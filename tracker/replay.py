"""
REPLAY: reconstrói a mesa linha a linha a partir do log.

Para cada linha do log guardamos uma "foto" da mesa: Pokémon Ativo e Banco de cada
jogador (com dano, energias e ferramentas), prêmios restantes, Estádio, descarte de
Pokémon nocauteados e o que aconteceu naquela linha (o "destaque").
O painel só desenha essas fotos, uma depois da outra.

O log não mostra tudo (por exemplo, a mão do adversário), então o replay mostra o que
está em jogo na mesa, que é o que o log descreve com segurança.
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

    estado = {
        "turno": 0, "vez": None, "estadio": None, "resultado": None,
        "mesa": {j: {"ativo": None, "banco": [], "premios": regras_jogo.PREMIOS_PARTIDA, "nocauteados": []} for j in jogadores},
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
          3. senão, vale o que está escrito (ex.: Estádio Risky Ruins pondo contadores no Básico que X acabou de jogar)."""
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

    quadros = []
    ultima_principal = ""  # última linha que não começa com "-" (o ataque ou habilidade que gerou as sublinhas)
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
            if embaralhou and poder and poder[1] in itens:
                # O Pokémon que usou a habilidade voltou para o baralho (com a pré-evolução embaixo dele).
                ref = achar_uid(poder[2])
                if ref:
                    remover(ref)
                    quadros.append(_quadro(n_linha, f"{poder[1]} voltou para o baralho: " + ", ".join(itens), estado,
                                           {"tipo": "descarte", "jogador": poder[0], "carta": poder[1]}))
                embaralhou, poder = False, None
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
        if not sublinha:
            poder = None
            ultima_principal = l
            atingidos = set()  # Pokémon que já levaram dano "took N damage" nesta mesma ação
            usou = re.match(rf"^{P}'s (.+?) used (.+?)(?: on .+)?\.$", l)
            if usou:  # para saber qual versão da carta ele é (ver _ps_minimo)
                golpes_vistos.setdefault((usou.group(1), usou.group(2)), set()).add(cartas.normalizar(usou.group(3)))
        if poder and re.match(rf"^{P} shuffled \d+ cards? into their deck\.$", l) and l.startswith(poder[0]):
            embaralhou = True

        def casa(padrao):
            nonlocal m
            m = re.match(padrao, l)
            return m

        if casa(rf"^(?:Turn # \d+ - )?{P}'s Turn$"):
            estado["turno"] += 1
            estado["vez"] = m.group(1)
            d = {"tipo": "turno", "jogador": m.group(1)}
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
            tipo = _tipo_anexo(c)
            if ref:
                p = pegar(ref)
                p["anexos"].append({"nome": c, "tipo": tipo, "energia": _tipo_energia(c) if tipo == "energia" else None})
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
        elif casa(rf"^(.+?) was discarded from {P}'s (.+?)\.$"):
            c, j, alvo = m.groups()
            ref = achar(j, alvo, None, False)
            if ref:
                p = pegar(ref)
                for i, a in enumerate(p["anexos"]):
                    if a["nome"] == c:
                        p["anexos"].pop(i)
                        break
            d = {"tipo": "descarte", "jogador": j, "carta": c}
        elif casa(rf"^{P} took (a|\d+) Prize cards?\.$"):
            j = m.group(1)
            q = 1 if m.group(2) == "a" else int(m.group(2))
            estado["mesa"][j]["premios"] = max(0, estado["mesa"][j]["premios"] - q)
            d = {"tipo": "premio", "jogador": j, "qtd": q}
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

    if novas_correcoes:  # contadores ambíguos: refaz a partida com a escolha que o nocaute revelou
        return gerar(texto, regras, novas_correcoes)
    return {"jogadores": jogadores, "primeiro": dados["resumo"]["primeiro"], "vencedor": dados["resumo"]["vencedor"],
            "turnos": estado["turno"], "quadros": quadros, "cartas": _cartas_usadas(quadros)}


def _quadro(n_linha, texto, estado, destaque):
    return {"linha": n_linha, "texto": texto, "turno": estado["turno"], "vez": estado["vez"],
            "destaque": destaque, "estado": copy.deepcopy({k: estado[k] for k in ("estadio", "mesa", "resultado")})}


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
