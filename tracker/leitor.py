"""
O LEITOR: transforma o texto do log do TCG Live em dados.

Cada regra (em dados/regras.json) é uma expressão regular com grupos nomeados:
  (?P<player>...)  nome do jogador
  (?P<card>...)    carta
  (?P<target>...)  alvo
  (?P<dano>\\d+) ou (?P<qtd>...)   valor numérico
  (?P<n>\\d+)      número do turno (só na regra de turno)
Também aceitamos a sintaxe de JavaScript (?<nome>...), convertida automaticamente.
"""
import re
import unicodedata
from functools import lru_cache

PREMIOS_PARTIDA = 6  # Standard: partidas de 6 prêmios (ver regras_jogo)

TIPOS = {
    "turno": "Início de turno", "moeda": "Cara ou coroa", "ordem": "Quem começa",
    "mulligan": "Mulligan", "compra": "Compra de cartas", "jogada": "Carta jogada",
    "evolucao": "Evolução", "energia": "Energia ligada", "ataque": "Ataque",
    "nocaute": "Nocaute", "premio": "Prêmio pego", "recuo": "Recuo",
    "fim_turno": "Fim de turno", "vitoria": "Vitória", "outro": "Outro",
    "ignorar": "Ignorar (não impacta)",
}


def slug(texto):
    """'Dragapult ex' -> 'dragapult-ex'. Usado para comparar nomes de decks entre fontes."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


@lru_cache(maxsize=65536)  # chamada centenas de milhares de vezes nas análises; o resultado nunca muda
def normalizar_nome_carta(nome):
    """Para comparar nomes de cartas: sem acento, minúsculo, e 'Basic Psychic Energy' = 'Psychic Energy'."""
    t = unicodedata.normalize("NFKD", (nome or "").replace("\u2019", "'")).encode("ascii", "ignore").decode()
    t = re.sub(r"\s+", " ", t).strip().lower()
    return re.sub(r"^basic ", "", t)


def nome_de_slug(s):
    """'dragapult-ex' -> 'Dragapult ex' (para exibir)."""
    partes = [p if p in ("ex", "v", "vstar", "vmax", "gx") else p.capitalize() for p in (s or "").split("-")]
    texto = " ".join(partes)
    return texto.replace(" Vstar", " VSTAR").replace(" Vmax", " VMAX")


def parece_log(texto):
    """Diz se um texto parece um log exportado do TCG Live."""
    if not texto or len(texto) < 80:
        return False
    texto = texto.replace("\u2019", "'")
    # O cabeçalho do turno é "Fulano's Turn" (versões antigas: "Turn # 1 - Fulano's Turn").
    tem_turno = re.search(r"^\s*(?:Turn # \d+ - )?.+'s Turn\s*$", texto, re.M) is not None
    tem_setup = ("opening hand" in texto) or ("coin toss" in texto) or texto.lstrip().startswith("Setup")
    return tem_turno and tem_setup


def _python_regex(padrao):
    return re.sub(r"\(\?<(?![=!])", "(?P<", padrao)


def compilar_regras(regras):
    ok, erros = [], {}
    for r in regras:
        if not r.get("ativa", True):
            continue
        try:
            ok.append({**r, "rx": re.compile(_python_regex(r["re"]))})
        except re.error as e:
            erros[r["id"]] = str(e)
    return ok, erros


# Código da carta antes do nome, quando a opção "Hide card IDs from export" (Battle Log Settings do jogo) está desmarcada:
# "(sv6_200) Dragapult ex", "(sv8-5_72_ph) Drakloak", "(me2-5_288) Fezandipiti ex". Os apps de replay pedem para desmarcar
# (PTCG Tools, Dead Draw, TrainerLog; REFERENCE_TOOLS.md). O leitor tira o código do nome (senão "(sv6_200) Dragapult ex" vira
# outra carta) e guarda os códigos de cada jogador em resumo["codigos"]: dizem a versão exata (decks.resolver_versoes).
CODIGO_CARTA = re.compile(r"\(([a-z]+\d*(?:-\d+[a-z]?)?_\d+[a-z]?(?:_[a-z]+)*)\) ", re.I)


def _codigos_da_linha(bruta, jogadores, dono):
    """[(jogador, código)] dos códigos de carta de uma linha. O dono é quem aparece logo antes ("Ana's (sv6_200) ...");
    sem isso, quem começa a linha (ou o dono das listas "•")."""
    texto = bruta.replace("’", "'")
    saida = []
    for m in CODIGO_CARTA.finditer(texto):
        antes = texto[:m.start()]
        de = next((j for j in sorted(jogadores, key=len, reverse=True) if antes.endswith(j + "'s ")), None) or dono
        if de:
            saida.append((de, m.group(1).lower()))
    return saida


def limpar_linha(bruta):
    # Troca o apóstrofo "curvo" (’), que o jogo às vezes usa, pelo reto ('), e tira o código das cartas (CODIGO_CARTA).
    bruta = CODIGO_CARTA.sub("", bruta)
    linha = re.sub(r"\s+", " ", bruta.replace("\u2019", "'").replace("\u00a0", " ")).strip()
    return re.sub(r"^- ", "", linha)


def _numero(v):
    if v in (None, ""):
        return None
    if v in ("a", "an"):
        return 1
    try:
        return int(v)
    except ValueError:
        return None


def testar_linha(linha, regras):
    """Mostra quais regras leem uma linha e o que cada grupo capturou."""
    rs, _ = compilar_regras(regras)
    linha = limpar_linha(linha)
    saida = []
    for r in rs:
        m = r["rx"].search(linha)
        if m:
            grupos = {k: v for k, v in m.groupdict().items() if v is not None}
            saida.append({"id": r["id"], "tipo": r["tipo"], "grupos": grupos})
    return saida


def ler_partida(texto, regras):
    """Lê o log inteiro. Devolve {jogadores, eventos, nao_lidas, resumo}."""
    rs, _ = compilar_regras(regras)
    linhas = texto.splitlines()

    # Passo 1: nomes dos jogadores (pelos cabeçalhos de turno e cara/coroa).
    jogadores = []
    for bruta in linhas:
        linha = limpar_linha(bruta)
        for r in rs:
            if r["tipo"] not in ("turno", "moeda", "ordem"):
                continue
            m = r["rx"].search(linha)
            if m and m.groupdict().get("player"):
                p = m.group("player").strip()
                if p not in jogadores:
                    jogadores.append(p)

    # Passo 2: linha a linha, vira evento.
    eventos, nao_lidas = [], []
    turno, dono = 0, None
    expandir = None  # jogador que "played them to the Bench": as cartas vêm na linha "•" seguinte
    vistas = {j: {} for j in jogadores}  # cartas reveladas de cada jogador (inclui listas "•" de compra/descarte)
    codigos = {j: {} for j in jogadores}  # códigos das cartas de cada jogador, quando o log os traz (CODIGO_CARTA)
    ultimo = None  # último jogador citado no começo de uma linha (dono das listas "•")
    for i, bruta in enumerate(linhas, start=1):
        linha = limpar_linha(bruta)
        if linha.startswith("•"):
            for de, cod in _codigos_da_linha(bruta, jogadores, ultimo):
                if de in codigos:
                    codigos[de][cod] = codigos[de].get(cod, 0) + 1
            if ultimo in vistas and ":" not in linha:
                for carta in (c.strip() for c in linha.lstrip("• ").split(",")):
                    if carta:
                        vistas[ultimo][carta] = vistas[ultimo].get(carta, 0) + 1
            if expandir:
                for carta in (c.strip() for c in linha.lstrip("• ").split(",")):
                    if carta:
                        eventos.append({"linha": i, "turno": turno, "dono": dono, "tipo": "jogada", "regra": "lista",
                                        "jogador": expandir, "carta": carta, "alvo": "", "golpe": "", "valor": None,
                                        "extra": "Bench", "texto": linha})
                expandir = None
            continue
        expandir = None
        dono_linha = next((j for j in sorted(jogadores, key=len, reverse=True)
                           if linha.startswith(j + " ") or linha.startswith(j + "'s ")), None)
        if dono_linha:
            ultimo = dono_linha
        for de, cod in _codigos_da_linha(bruta, jogadores, dono_linha or ultimo):
            if de in codigos:
                codigos[de][cod] = codigos[de].get(cod, 0) + 1
        if (not linha or linha == "Setup" or re.match(r"^\d+ drawn cards?\.?$", linha)
                or re.match(r"^(Damage breakdown:|Cards revealed from Mulligan \d+)$", linha)):
            continue
        m_lista = re.match(r"^(.+?) drew \d+ cards? and played them to the (?:Bench|Active Spot)\.$", linha)
        if m_lista and (not jogadores or m_lista.group(1) in jogadores):
            expandir = m_lista.group(1)
        leu = False
        for r in rs:
            m = r["rx"].search(linha)
            if not m:
                continue
            g = m.groupdict()
            jogador = (g.get("player") or "").strip()
            if "player" in g and jogadores and jogador not in jogadores:
                continue  # evita confundir "X drew Y and played..." com um nome
            if r["tipo"] == "ignorar":  # linha conhecida que não muda nenhuma estatística
                leu = True
                break
            if r["tipo"] == "turno":
                turno = int(g.get("n") or turno + 1)
                dono = jogador
            valor = g.get("dano") if g.get("dano") is not None else g.get("qtd")
            eventos.append({
                "linha": i, "turno": turno, "dono": dono, "tipo": r["tipo"], "regra": r["id"],
                "jogador": jogador, "carta": (g.get("card") or "").strip(),
                "alvo": (g.get("target") or "").strip(), "golpe": (g.get("golpe") or "").strip(),
                "valor": _numero(valor), "extra": g.get("ordem") or g.get("lugar") or g.get("from") or "",
                "texto": linha,
            })
            leu = True
        if not leu:
            nao_lidas.append({"linha": i, "texto": linha})

    for e in eventos:  # cartas que apareceram nos eventos também foram reveladas
        if e["jogador"] in vistas and e["carta"] and e["tipo"] != "nocaute":
            vistas[e["jogador"]][e["carta"]] = vistas[e["jogador"]].get(e["carta"], 0) + 1
    resumo = resumir(jogadores, eventos, texto)
    resumo["vistas"] = vistas
    resumo["codigos"] = codigos
    resumo["exportou"] = quem_exportou(linhas, jogadores)
    resumo["problemas"] = conferir(jogadores, eventos, resumo, linhas)
    resumo["digital"] = impressao_digital(jogadores, resumo)
    return {"jogadores": jogadores, "eventos": eventos, "nao_lidas": nao_lidas, "resumo": resumo}


def quem_exportou(linhas, jogadores):
    """De quem é o log, sem precisar do nick.

    O jogo só mostra o nome das cartas compradas por quem exportou ("Fulano drew Rare Candy.")
    e só lista a mão inicial dele; as compras do adversário aparecem como "drew a card".
    (Ideia do Full Bench, github.com/heatfireash/FullBench, licença MIT.)
    """
    if len(jogadores) != 2:
        return None
    pontos = {j: 0 for j in jogadores}
    abriu = None  # jogador cuja mão inicial acabou de ser anunciada
    for bruta in linhas:
        efeito = bruta.strip().startswith("- ")  # linha de efeito: cartas buscadas aparecem para os dois
        linha = limpar_linha(bruta)
        if linha.startswith("•"):
            if abriu:
                pontos[abriu] += 3  # mão inicial com as cartas listadas: só a de quem exportou
            abriu = None
            continue
        if re.match(r"^\d+ drawn cards?\.?$", linha):
            continue  # "- 7 drawn cards." fica entre o anúncio da mão e a lista
        abriu = None
        m = re.match(r"^(.+?) drew (.+?)\.$", linha)
        if not m or m.group(1) not in pontos:
            continue
        o_que = m.group(2)
        if o_que.endswith("for the opening hand"):
            abriu = m.group(1)
        elif not efeito and not re.match(r"^(a card|\d+ (more )?cards?)\b", o_que) and " and played " not in o_que:
            pontos[m.group(1)] += 1  # compra do turno com o nome da carta
    a, b = sorted(pontos.items(), key=lambda kv: -kv[1])
    return a[0] if a[1] > 0 and a[1] >= 3 * b[1] else None


def conferir(jogadores, eventos, resumo, linhas):
    """Sinais de log cortado ou estranho. A partida é gravada mesmo assim, com um aviso."""
    problemas = []
    if len(jogadores) != 2:
        problemas.append("não achei os dois jogadores")
    vitorias = [e for e in eventos if e["tipo"] == "vitoria"]
    if not vitorias and not resumo["vencedor"]:
        problemas.append("falta a linha final com o resultado (o log foi copiado inteiro?)")
    maos = sum(1 for l in linhas if "drew 7 cards for the opening hand" in l)
    if jogadores and maos < 2:
        problemas.append("falta a mão inicial de um dos jogadores")
    if any(p["premios"] > PREMIOS_PARTIDA for p in resumo["por_jogador"].values()):
        problemas.append("mais de 6 prêmios para um jogador")
    if resumo["turnos"] > 80:
        problemas.append("número de turnos fora do normal")
    return problemas


def impressao_digital(jogadores, resumo):
    """A mesma partida vista pelos dois lados gera logs diferentes (cada um vê as próprias compras).

    Esta "impressão digital" usa só o que os dois logs têm em comum: vencedor, perdedor, turnos,
    motivo e prêmios. Serve para não contar duas vezes um jogo entre você e um amigo.
    """
    import hashlib
    v = resumo["vencedor"]
    if len(jogadores) != 2 or v not in jogadores:
        return None
    perdedor = next(j for j in jogadores if j != v)
    pj = resumo["por_jogador"]
    chave = "|".join(str(x) for x in (v.lower(), perdedor.lower(), resumo["turnos"], resumo["motivo"],
                                      pj[v]["premios"], pj[perdedor]["premios"]))
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()[:20]


def resumir(jogadores, eventos, texto):
    def outro(p):
        return next((j for j in jogadores if j != p), "")

    base = lambda: {"premios": 0, "nocautes": 0, "dano": 0, "ataques": 0, "mulligans": 0,
                    "jogadas": 0, "energias": 0, "evolucoes": 0}
    por = {j: base() for j in jogadores}
    cartas = {j: {} for j in jogadores}
    atacantes = {j: {} for j in jogadores}   # usou golpe ou habilidade
    dano_por = {j: {} for j in jogadores}     # ataques que causaram dano

    def contar(dic, j, c):
        if j in dic and c:
            dic[j][c] = dic[j].get(c, 0) + 1

    primeiro = vencedor = None
    max_turno = 0
    nocautes = []
    for e in eventos:
        s = por.get(e["jogador"])
        max_turno = max(max_turno, e["turno"])
        t = e["tipo"]
        if t == "ordem":
            primeiro = e["jogador"] if e["extra"] == "first" else outro(e["jogador"])
        elif t == "mulligan" and s:
            # o jogo escreve "took a mulligan", "took 2 mulligans"...: vale o maior número
            s["mulligans"] = max(s["mulligans"], e["valor"] or 1)
        elif t in ("jogada", "evolucao", "energia") and s:
            s[{"jogada": "jogadas", "evolucao": "evolucoes", "energia": "energias"}[t]] += 1
            contar(cartas, e["jogador"], e["carta"])
        elif t == "ataque" and s:
            s["ataques"] += 1
            s["dano"] += e["valor"] or 0
            contar(atacantes, e["jogador"], e["carta"])
            if e["valor"]:
                contar(dano_por, e["jogador"], e["carta"])
        elif t == "premio" and s:
            s["premios"] += e["valor"] or 0
        elif t == "nocaute":
            autor = outro(e["jogador"])  # o Pokémon nocauteado é de "jogador"
            if autor in por:
                por[autor]["nocautes"] += 1
            nocautes.append({"turno": e["turno"], "autor": autor, "vitima": e["jogador"],
                             "carta": e["carta"], "premios": 0})
        elif t == "vitoria":
            vencedor = e["jogador"]

    for e in (x for x in eventos if x["tipo"] == "premio"):
        for k in reversed(nocautes):
            if k["turno"] == e["turno"] and k["autor"] == e["jogador"] and not k["premios"]:
                k["premios"] = e["valor"] or 0
                break

    serie = {}
    for j in jogadores:
        acc, s = 0, []
        for t in range(max_turno + 1):
            acc += sum(e["valor"] or 0 for e in eventos
                       if e["tipo"] == "premio" and e["jogador"] == j and e["turno"] == t)
            s.append(acc)
        serie[j] = s

    # Regras do Standard (base de regras): quem joga o turno 1 é quem começou, e quem pega o
    # último dos 6 prêmios vence na hora. Valem quando o log não traz a linha de cara/coroa
    # ou a linha final com o vencedor.
    if not primeiro:
        primeiro = next((e["jogador"] for e in eventos if e["tipo"] == "turno" and e["jogador"]), None)
    if not vencedor:
        completos = [j for j in jogadores if por[j]["premios"] >= PREMIOS_PARTIDA]
        if len(completos) == 1:
            vencedor = completos[0]

    baixo = texto.lower()
    if vencedor and por.get(vencedor, {}).get("premios", 0) >= PREMIOS_PARTIDA:
        motivo = "Pegou todos os prêmios"
    elif "conceded" in baixo:
        motivo = "Desistência"
    elif re.search(r"(no more cards|could not draw|deck out|ran out of cards)", baixo):
        motivo = "Deck acabou"
    elif re.search(r"(no (more |benched |other |remaining )?pok[eé]mon|without (any )?pok[eé]mon|pok[eé]mon left in play)", baixo):
        motivo = "Sem Pokémon em jogo"
    elif "didn't take an action in time" in baixo or "ran out of time" in baixo:
        motivo = "Tempo esgotado"
    else:
        motivo = "Não identificado"
    if vencedor and motivo in ("Não identificado", "Tempo esgotado"):
        # Confere a mesa: se o perdedor ficou sem nenhum Pokémon em jogo, foi esse o motivo.
        em_jogo = {j: 0 for j in jogadores}
        for e in eventos:
            if e["jogador"] in em_jogo and e["tipo"] == "jogada" and e["extra"] in ("Bench", "Active Spot"):
                em_jogo[e["jogador"]] += 1
            elif e["jogador"] in em_jogo and e["tipo"] == "nocaute":
                em_jogo[e["jogador"]] -= 1
        perdedor = outro(vencedor)
        if perdedor in em_jogo and em_jogo[perdedor] <= 0 and any(e["tipo"] == "nocaute" for e in eventos):
            motivo = "Sem Pokémon em jogo"
    linhas_texto = [l.strip() for l in texto.strip().splitlines() if l.strip()]

    # Palpite do deck, em ordem de preferência:
    #   1. o Pokémon que mais causou dano (habilidades como "Run Errand" não contam);
    #   2. sem dano (partida curta, desistência): o Pokémon "ex"/"V" que mais foi para a mesa;
    #   3. o que mais usou golpes/habilidades.  Desempate: nome com "ex"/"V".
    na_mesa = {j: {} for j in jogadores}
    for e in eventos:
        if e["jogador"] in na_mesa and e["carta"] and (e["tipo"] == "evolucao" or (e["tipo"] == "jogada" and e["extra"] in ("Bench", "Active Spot"))):
            na_mesa[e["jogador"]][e["carta"]] = na_mesa[e["jogador"]].get(e["carta"], 0) + 1
    decks = {}
    for j in jogadores:
        grandes = {c: q for c, q in na_mesa[j].items() if re.search(r" (ex|V|VSTAR|VMAX)$", c)}
        base_contagem = dano_por[j] or grandes or atacantes[j]
        ranking = sorted(base_contagem.items(), key=lambda kv: (kv[1], " ex" in kv[0] or " V" in kv[0]), reverse=True)
        decks[j] = ranking[0][0] if ranking else ""

    return {
        "primeiro": primeiro, "vencedor": vencedor, "motivo": motivo, "turnos": max_turno,
        "por_jogador": por, "cartas": cartas, "nocautes": nocautes, "serie": serie,
        "deck_palpite": decks,
        "primeiro_nocaute": nocautes[0]["autor"] if nocautes else None,
        "linha_final": linhas_texto[-1] if linhas_texto else "",
    }
