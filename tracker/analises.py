"""
ANÁLISES: as contas por trás do painel.

Duas fontes:
  - Suas partidas (logs capturados)        -> desempenho pessoal
  - Campeonatos importados (Labs + RK9)    -> meta, matchups, perfil de deck, cartas

Taxa de vitória = vitórias / (vitórias + derrotas + empates), como no Limitless.
Com poucas partidas a taxa engana, então mostramos também o intervalo de confiança de
95% (método de Wilson): a faixa onde a taxa "verdadeira" provavelmente está.
"""
import math
from collections import Counter, defaultdict

from . import banco
from .leitor import slug


def nome_de_slug(s):
    """Nome do deck como o Limitless mostra (ex.: dragapult-ex -> Dragapult)."""
    from . import decks
    return decks.nome_deck(s)


def wilson(v, n, z=1.96):
    if not n:
        return None, None
    p = v / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margem = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(100 * max(0, centro - margem), 1), round(100 * min(1, centro + margem), 1)


def placar(v, d, e=0):
    n = v + d + e
    baixo, alto = wilson(v, n)
    return {"n": n, "v": v, "d": d, "e": e, "taxa": round(100 * v / n, 1) if n else None,
            "ic_baixo": baixo, "ic_alto": alto}


# ================================================================== pessoal

def descobrir_eu(partidas, nick):
    if nick:
        return nick
    contagem = Counter(j for p in partidas for j in p["jogadores"])
    if len(partidas) >= 2 and contagem:
        nome, qtd = contagem.most_common(1)[0]
        if qtd >= 2:
            return nome
    return ""


def _listas():
    return {d["id"]: d for d in banco.consultar("SELECT id, nome, arquetipo FROM meus_decks")}


def _arquetipo_lista(deck_id):
    return (_listas().get(deck_id) or {}).get("arquetipo", "") if deck_id else ""


def _nome_lista(deck_id):
    return (_listas().get(deck_id) or {}).get("nome", "") if deck_id else ""


def visao(p, eu):
    from . import decks
    """Uma partida do ponto de vista de "eu"."""
    r = p["resumo"]
    js = p["jogadores"]
    sou = eu in js
    adv = next((j for j in js if j != eu), "") if sou else (js[1] if len(js) > 1 else "")
    eu_ = eu if sou else (js[0] if js else "")
    res = ""
    if r["vencedor"] and sou:
        res = "V" if r["vencedor"] == eu else "D"
    pj = r["por_jogador"]
    return {
        "id": p["id"], "data": p["capturada_em"], "origem": p["origem"], "eu": eu_, "adversario": adv,
        "resultado": res, "comecei": (r["primeiro"] == eu_) if r["primeiro"] else None,
        "meu_deck": p["meu_deck"] or _arquetipo_lista(p.get("deck_id")) or decks.palpite_deck(r, eu_),
        "deck_adv": p["deck_adv"] or decks.palpite_deck(r, adv),
        "deck_id": p.get("deck_id"), "lista_nome": _nome_lista(p.get("deck_id")),
        "premios_eu": pj.get(eu_, {}).get("premios", 0), "premios_adv": pj.get(adv, {}).get("premios", 0),
        "turnos": r["turnos"], "motivo": r["motivo"],
        "primeiro_ko_meu": (r["primeiro_nocaute"] == eu_) if r["primeiro_nocaute"] else None,
        "mulligan_eu": pj.get(eu_, {}).get("mulligans", 0) > 0,
        "tags": p["tags"], "notas": p["notas"], "qtd_nao_lidas": p["qtd_nao_lidas"], "conhecido": sou,
    }


def _agrupar(linhas, chave):
    grupos = defaultdict(lambda: [0, 0])
    for l in linhas:
        k = chave(l)
        if k is None:
            continue
        grupos[k][0 if l["resultado"] == "V" else 1] += 1
    return [{"grupo": k, **placar(v, d)} for k, (v, d) in sorted(grupos.items(), key=lambda kv: -sum(kv[1]))]


def analise_pessoal(nick, de=None, ate=None, deck=None, tag=None, lista=None, adv=None):
    partidas = banco.listar_partidas()
    eu = descobrir_eu(partidas, nick)
    todas = [visao(p, eu) for p in partidas]
    linhas = [l for l in todas
              if l["resultado"]
              and (not de or l["data"][:10] >= de) and (not ate or l["data"][:10] <= ate)
              and (not deck or slug(l["meu_deck"]) == slug(deck))
              and (not tag or tag.lower() in (l["tags"] or "").lower())
              and (not lista or str(l["deck_id"]) == str(lista))
              and (not adv or slug(l["deck_adv"]) == slug(adv))]
    v = sum(1 for l in linhas if l["resultado"] == "V")

    # Matchup do seu deck nos campeonatos, para comparar com o seu resultado.
    meta_mu = matchups_por_slug()
    por_adv = _agrupar(linhas, lambda l: l["deck_adv"] or "Desconhecido")
    for g in por_adv:
        decks_meus = {slug(l["meu_deck"]) for l in linhas if (l["deck_adv"] or "Desconhecido") == g["grupo"]}
        ref = [meta_mu.get((m, slug(g["grupo"]))) for m in decks_meus]
        ref = [x for x in ref if x]
        if ref:
            n = sum(x["n"] for x in ref)
            g["meta_taxa"] = round(100 * sum(x["v"] for x in ref) / n, 1) if n else None
            g["meta_n"] = n

    dias = defaultdict(lambda: [0, 0])
    for l in linhas:
        dias[l["data"][:10]][0 if l["resultado"] == "V" else 1] += 1
    acumulado, serie = [0, 0], []
    for dia in sorted(dias):
        acumulado[0] += dias[dia][0]
        acumulado[1] += dias[dia][1]
        serie.append({"dia": dia, "v": dias[dia][0], "d": dias[dia][1],
                      "taxa_acumulada": round(100 * acumulado[0] / sum(acumulado), 1)})

    def media(campo, res):
        xs = [l[campo] for l in linhas if l["resultado"] == res]
        return round(sum(xs) / len(xs), 1) if xs else None

    return {
        "eu": eu, "total": placar(v, len(linhas) - v),
        "sem_resultado": sum(1 for l in todas if not l["resultado"]),
        "por_meu_deck": _agrupar(linhas, lambda l: l["meu_deck"] or "Desconhecido"),
        "por_lista": _agrupar(linhas, lambda l: l["lista_nome"] or None),
        "por_adversario": por_adv,
        "ordem": _agrupar(linhas, lambda l: None if l["comecei"] is None else ("Começando" if l["comecei"] else "Indo em segundo")),
        "primeiro_nocaute": _agrupar(linhas, lambda l: None if l["primeiro_ko_meu"] is None else ("Você fez o 1º nocaute" if l["primeiro_ko_meu"] else "Adversário fez o 1º nocaute")),
        "mulligan": _agrupar(linhas, lambda l: "Com mulligan" if l["mulligan_eu"] else "Sem mulligan"),
        "motivos": _agrupar(linhas, lambda l: l["motivo"]),
        "tendencia": serie,
        "turnos_medios": {"vitorias": media("turnos", "V"), "derrotas": media("turnos", "D")},
        "partidas": todas,
    }


# ================================================================== campeonatos

def _filtro_torneios(torneios):
    if not torneios:
        return "", ()
    return f" AND torneio IN ({','.join('?' * len(torneios))})", tuple(torneios)


def matchups_por_slug(torneios=None):
    """{(deck_a, deck_b): {v, d, e, n}} contando cada partida pelos dois lados."""
    f, params = _filtro_torneios(torneios)
    rows = banco.consultar(
        f"SELECT arq1, arq2, res1, COUNT(*) AS q FROM t_partidas "
        f"WHERE arq1 != '' AND arq2 != '' {f} GROUP BY arq1, arq2, res1", params)
    mu = defaultdict(lambda: {"v": 0, "d": 0, "e": 0, "n": 0})
    inverso = {"W": "L", "L": "W", "T": "T"}
    for r in rows:
        for a, b, res in ((r["arq1"], r["arq2"], r["res1"]), (r["arq2"], r["arq1"], inverso[r["res1"]])):
            c = mu[(a, b)]
            c[{"W": "v", "L": "d", "T": "e"}[res]] += r["q"]
            c["n"] += r["q"]
    return mu


def _jogadores(torneios, top=0):
    f, params = _filtro_torneios(torneios)
    sql = f"SELECT * FROM t_jogadores WHERE 1=1 {f}"
    if top:
        sql += " AND posicao <= ?"
        params = params + (top,)
    return banco.consultar(sql, params)


def meta(torneios=None, top=0, corte=32, k=12, min_partidas=10):
    """Divisão do meta, taxa de vitória, conversão e matriz de matchups."""
    jogadores = _jogadores(torneios, top)
    todos = _jogadores(torneios)
    conhecidos = [j for j in jogadores if j["arquetipo"]]
    total = len(conhecidos) or 1
    cont = Counter(j["arquetipo"] for j in conhecidos)
    no_corte = Counter(j["arquetipo"] for j in todos if j["arquetipo"] and j["posicao"] and j["posicao"] <= corte)
    total_corte = sum(no_corte.values()) or 1
    total_campo = sum(1 for j in todos if j["arquetipo"]) or 1
    campo = Counter(j["arquetipo"] for j in todos if j["arquetipo"])
    mu = matchups_por_slug(torneios)

    divisao = []
    for arq, qtd in cont.most_common():
        geral = {"v": 0, "d": 0, "e": 0}
        for (a, b), c in mu.items():
            if a == arq and b != arq:  # espelho fora da conta
                for x in ("v", "d", "e"):
                    geral[x] += c[x]
        pct_campo = campo[arq] / total_campo
        divisao.append({
            "arquetipo": arq, "nome": nome_de_slug(arq), "jogadores": qtd,
            "pct": round(100 * qtd / total, 1),
            "no_corte": no_corte.get(arq, 0),
            "conversao": round(100 * no_corte.get(arq, 0) / campo[arq], 1) if campo[arq] else None,
            "fator_conversao": round((no_corte.get(arq, 0) / total_corte) / pct_campo, 2) if pct_campo else None,
            **placar(geral["v"], geral["d"], geral["e"]),
        })

    principais = [d["arquetipo"] for d in divisao[:k]]
    matriz = []
    for a in principais:
        linha = []
        for b in principais:
            c = mu.get((a, b), {"v": 0, "d": 0, "e": 0, "n": 0})
            cel = placar(c["v"], c["d"], c["e"])
            cel["espelho"] = a == b
            cel["pouco"] = cel["n"] < min_partidas
            linha.append(cel)
        matriz.append({"arquetipo": a, "nome": nome_de_slug(a), "celulas": linha})

    return {"divisao": divisao, "matriz": matriz, "colunas": [{"arquetipo": a, "nome": nome_de_slug(a)} for a in principais],
            "jogadores_considerados": len(conhecidos), "sem_deck": len(jogadores) - len(conhecidos), "corte": corte}


def tendencia(k=8):
    """Participação dos principais decks em cada torneio, em ordem de data."""
    torneios = banco.listar_torneios()[::-1]
    geral = Counter(j["arquetipo"] for j in _jogadores(None) if j["arquetipo"])
    principais = [a for a, _ in geral.most_common(k)]
    pontos = []
    for t in torneios:
        js = [j for j in _jogadores([t["id"]]) if j["arquetipo"]]
        c = Counter(j["arquetipo"] for j in js)
        tot = len(js) or 1
        pontos.append({"torneio": t["id"], "nome": t["nome"], "data": t["data"],
                       "pct": {a: round(100 * c.get(a, 0) / tot, 1) for a in principais}})
    return {"series": [{"arquetipo": a, "nome": nome_de_slug(a)} for a in principais], "torneios": pontos}


def perfil(arq, torneios=None):
    """Tudo sobre um deck: participação, matchups, colocações, esqueleto e taxa esperada."""
    todos = _jogadores(torneios)
    com_deck = [j for j in todos if j["arquetipo"]]
    deles = sorted([j for j in com_deck if j["arquetipo"] == arq], key=lambda j: (j["torneio"], j["posicao"] or 99999))
    if not deles:
        return None
    mu = matchups_por_slug(torneios)
    share = Counter(j["arquetipo"] for j in com_deck)
    tot = len(com_deck)

    spread, esperado_num, esperado_den = [], 0.0, 0.0
    for (a, b), c in mu.items():
        if a != arq:
            continue
        cel = placar(c["v"], c["d"], c["e"])
        peso = share.get(b, 0) / tot
        spread.append({"arquetipo": b, "nome": nome_de_slug(b), "pct_campo": round(100 * peso, 1), **cel})
        if b != arq and cel["n"] >= 5:
            esperado_num += peso * cel["taxa"]
            esperado_den += peso
    spread.sort(key=lambda x: -x["pct_campo"])

    faixas = [("Top 8", 8), ("Top 16", 16), ("Top 32", 32), ("Top 64", 64), ("Top 128", 128), ("Top 256", 256)]
    colocacoes = {nome: sum(1 for j in deles if j["posicao"] and j["posicao"] <= lim) for nome, lim in faixas}

    f, params = _filtro_torneios(torneios)
    listas = banco.consultar(
        f"SELECT l.torneio, l.labs_id, l.carta, l.qtd, l.carta_id, l.carta_base FROM t_listas l JOIN t_jogadores j "
        f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo=? {f.replace('torneio', 'l.torneio')}",
        (arq,) + params)
    esqueleto = _uso_cartas(listas, {(j["torneio"], j["labs_id"]): j for j in deles})

    return {
        "arquetipo": arq, "nome": nome_de_slug(arq), "jogadores": len(deles),
        "pct": round(100 * len(deles) / tot, 1) if tot else 0,
        "colocacoes": colocacoes, "melhores": sorted(deles, key=lambda j: j["posicao"] or 99999)[:15],
        "spread": spread,
        "taxa_esperada": round(esperado_num / esperado_den, 1) if esperado_den else None,
        "listas": len({(l["torneio"], l["labs_id"]) for l in listas}), "esqueleto": esqueleto[:60],
        "por_torneio": _participacao_por_torneio(arq),
    }


def _participacao_por_torneio(arq):
    saida = []
    for t in banco.listar_torneios()[::-1]:
        js = [j for j in _jogadores([t["id"]]) if j["arquetipo"]]
        if js:
            q = sum(1 for j in js if j["arquetipo"] == arq)
            saida.append({"torneio": t["id"], "nome": t["nome"], "data": t["data"], "pct": round(100 * q / len(js), 1), "jogadores": q})
    return saida


def _uso_cartas(listas, jogadores_por_chave):
    """Por carta: % das listas que usam, média de cópias, distribuição e taxa de vitória com/sem."""
    # Agrupa pela arte básica (conversor): artes alternativas da mesma carta contam juntas.
    por_lista = defaultdict(dict)
    nomes = {}
    for l in listas:
        chave = l.get("carta_id") or l["carta"]
        nomes.setdefault(chave, (l.get("carta_base") or l["carta"], l.get("carta_id") or ""))
        por_lista[(l["torneio"], l["labs_id"])][chave] = por_lista[(l["torneio"], l["labs_id"])].get(chave, 0) + l["qtd"]
    n_listas = len(por_lista)
    if not n_listas:
        return []

    def taxa(chaves):
        v = d = e = 0
        for ch in chaves:
            j = jogadores_por_chave.get(ch)
            if j and j["v"] is not None:
                v, d, e = v + j["v"], d + j["d"], e + j["e"]
        return round(100 * v / (v + d + e), 1) if (v + d + e) else None

    cartas = Counter(c for lista in por_lista.values() for c in lista)
    saida = []
    for carta, qtd in cartas.most_common():
        com = [ch for ch, lista in por_lista.items() if carta in lista]
        sem = [ch for ch in por_lista if carta not in por_lista[ch]]
        copias = [por_lista[ch][carta] for ch in com]
        # Desempenho por número de cópias (0 = listas do mesmo recorte sem a carta)
        por_copias = {}
        for q in sorted(set(copias)):
            chs = [ch for ch in com if por_lista[ch][carta] == q]
            por_copias[q] = {"listas": len(chs), "taxa": taxa(chs)}
        if sem:
            por_copias = {0: {"listas": len(sem), "taxa": taxa(sem)}, **por_copias}
        saida.append({
            "chave": carta, "por_copias": por_copias,
            "carta": nomes[carta][0], "carta_id": nomes[carta][1], "listas": qtd, "pct": round(100 * qtd / n_listas, 1),
            "media_copias": round(sum(copias) / len(copias), 2),
            "distribuicao": dict(sorted(Counter(copias).items())),
            "taxa_com": taxa(com), "taxa_sem": taxa(sem) if sem else None,
        })
    return saida


def cartas(torneios=None, arq=None):
    f, params = _filtro_torneios(torneios)
    sql = (f"SELECT l.torneio, l.labs_id, l.carta, l.qtd, l.carta_id, l.carta_base FROM t_listas l JOIN t_jogadores j "
           f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE 1=1 {f.replace('torneio', 'l.torneio')}")
    if arq:
        sql += " AND j.arquetipo=?"
        params = params + (arq,)
    listas = banco.consultar(sql, params)
    js = {(j["torneio"], j["labs_id"]): j for j in _jogadores(torneios)}
    return {"listas": len({(l["torneio"], l["labs_id"]) for l in listas}), "cartas": _uso_cartas(listas, js)}


def comparar_listas(torneio_a, id_a, torneio_b, id_b):
    """Diferença carta a carta entre duas listas (como o Deck Diff)."""
    def lista(t, i):
        return {r["carta"]: r["qtd"] for r in banco.consultar(
            "SELECT COALESCE(NULLIF(carta_base, ''), carta) AS carta, SUM(qtd) AS qtd FROM t_listas "
            "WHERE torneio=? AND labs_id=? GROUP BY COALESCE(NULLIF(carta_id, ''), carta)", (t, i))}
    a, b = lista(torneio_a, id_a), lista(torneio_b, id_b)
    linhas = [{"carta": c, "a": a.get(c, 0), "b": b.get(c, 0), "dif": b.get(c, 0) - a.get(c, 0)} for c in sorted(set(a) | set(b))]
    return sorted(linhas, key=lambda x: (x["dif"] == 0, -abs(x["dif"]), x["carta"]))


def cartas_matchups(arq, chave_carta, torneios=None, k=8, min_partidas=5):
    """
    CARTA x MATCHUP (como o "Card Matchups" do Trainer Hill): para um deck, compara a taxa de
    vitória contra cada adversário conforme o número de cópias de uma carta na lista.
    Só entram jogadores com lista importada (veja "Listas do topo" ao importar torneios).
    """
    f, params = _filtro_torneios(torneios)
    jogadores = [j for j in _jogadores(torneios) if j["arquetipo"] == arq]
    if not jogadores:
        return None
    listas = banco.consultar(
        f"SELECT l.torneio, l.labs_id, l.carta, l.carta_id, l.qtd FROM t_listas l JOIN t_jogadores j "
        f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo=? {f.replace('torneio', 'l.torneio')}",
        (arq,) + params)
    com_lista = {(l["torneio"], l["labs_id"]) for l in listas}
    copias = defaultdict(int)
    for l in listas:
        if (l["carta_id"] or l["carta"]) == chave_carta:
            copias[(l["torneio"], l["labs_id"])] += l["qtd"]
    por_nome = {}
    for j in jogadores:
        if (j["torneio"], j["labs_id"]) in com_lista:
            por_nome[(j["torneio"], j["nome_norm"])] = copias.get((j["torneio"], j["labs_id"]), 0)

    partidas = banco.consultar(f"SELECT * FROM t_partidas WHERE (arq1=? OR arq2=?) {f}", (arq, arq) + params)
    inverso = {"W": "L", "L": "W", "T": "T"}
    grupos = defaultdict(lambda: defaultdict(lambda: {"v": 0, "d": 0, "e": 0}))
    adversarios = Counter()
    for p in partidas:
        for meu, outro, arq_meu, arq_outro, res in ((p["j1"], p["j2"], p["arq1"], p["arq2"], p["res1"]),
                                                    (p["j2"], p["j1"], p["arq2"], p["arq1"], inverso[p["res1"]])):
            q = por_nome.get((p["torneio"], meu))
            if arq_meu != arq or q is None or not arq_outro or arq_outro == arq:
                continue  # sem lista, deck desconhecido ou mirror
            campo = {"W": "v", "L": "d", "T": "e"}[res]
            grupos[q][arq_outro][campo] += 1
            grupos[q]["__geral"][campo] += 1
            adversarios[arq_outro] += 1
    colunas = [a for a, _ in adversarios.most_common(k)]
    linhas = []
    for q in sorted(grupos):
        listas_q = sum(1 for v in por_nome.values() if v == q)
        celulas = []
        for a in colunas:
            c = grupos[q][a]
            cel = placar(c["v"], c["d"], c["e"])
            cel["pouco"] = cel["n"] < min_partidas
            celulas.append(cel)
        g = grupos[q]["__geral"]
        linhas.append({"copias": q, "listas": listas_q, "geral": placar(g["v"], g["d"], g["e"]), "celulas": celulas})
    return {"arquetipo": arq, "nome": nome_de_slug(arq), "listas": len(por_nome),
            "colunas": [{"arquetipo": a, "nome": nome_de_slug(a)} for a in colunas], "linhas": linhas}
