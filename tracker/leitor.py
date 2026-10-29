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


def limpar_linha(bruta):
    # Troca o apóstrofo "curvo" (’), que o jogo às vezes usa, pelo reto (').
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
    ultimo = None  # último jogador citado no começo de uma linha (dono das listas "•")
    for i, bruta in enumerate(linhas, start=1):
        linha = limpar_linha(bruta)
        if linha.startswith("•"):
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
    return {"jogadores": jogadores, "eventos": eventos, "nao_lidas": nao_lidas, "resumo": resumo}


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

    baixo = texto.lower()
    if vencedor and por.get(vencedor, {}).get("premios", 0) >= 6:
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
