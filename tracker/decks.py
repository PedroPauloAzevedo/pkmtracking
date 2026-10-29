"""
DECKS: arquétipos do Limitless, ícones, identificação do deck de cada jogador,
"Meus decks" (suas listas) e escolha da versão certa de cartas com o mesmo nome.

ARQUÉTIPOS
  A lista de decks e os Pokémon do ícone de cada um vêm da página de metagame de cada
  torneio no Limitless Labs (/<torneio>/decks). Ex.: "Dragapult" = dragapult-ex, ícone dragapult.

ÍCONES
  Imagem pequena do Pokémon (PokémonDB). Formas Mega vêm de outra pasta do PokémonDB e,
  se faltar, do próprio Limitless. Ficam guardadas em dados/icones/.

IDENTIFICAÇÃO DO DECK
  Para cada jogador juntamos todas as cartas reveladas no log (jogadas, evoluções, ataques e
  as listas "•" de compra/descarte que o jogo mostra) e damos nota a cada arquétipo:
    + Pokémon do ícone do arquétipo que apareceu (o primeiro ícone vale mais)
    - Pokémon do ícone que não apareceu
    + cartas típicas do arquétipo nas listas dos torneios importados (pesando as que são
      exclusivas daquele deck mais do que as que todo deck usa, como Ultra Ball)
  Ganha a maior nota. Se a partida estiver ligada a uma lista de "Meus decks", vale o
  arquétipo da lista.
"""
import json
import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import requests

from . import banco, cartas, config
from .leitor import nome_de_slug, normalizar_nome_carta, slug

PASTA_ICONES = config.PASTA_DADOS / "icones"
FONTES_ICONE = [
    "https://img.pokemondb.net/sprites/scarlet-violet/icon/{p}.png",
    "https://img.pokemondb.net/sprites/home/normal/{p}.png",
    "https://r2.limitlesstcg.net/pokemon/gen9/{p}.png",
]
PREFIXOS_DONO = r"^(team-rocket-s|[a-z]+-s|n)-"   # N's, Ethan's, Team Rocket's...
REGIOES = {"alolan": "alola", "galarian": "galar", "hisuian": "hisui", "paldean": "paldea"}


# ------------------------------------------------------------------ arquétipos

def salvar_arquetipos(lista):
    agora = datetime.now().isoformat(timespec="seconds")
    with banco.conectar() as con:
        for a in lista:
            con.execute("INSERT INTO arquetipos (slug, nome, icones, atualizado_em) VALUES (?,?,?,?) "
                        "ON CONFLICT(slug) DO UPDATE SET nome=excluded.nome, icones=excluded.icones, atualizado_em=excluded.atualizado_em",
                        (a["slug"], a["nome"], json.dumps(a["icones"]), agora))
    _cache.clear()


def ler_pagina_decks(sopa, tid):
    """Lê /<torneio>/decks do Labs: [{slug, nome, icones}]."""
    padrao = re.compile(rf"/{tid}/decks/([^/?#]+)/?$")
    achados = {}
    for a in sopa.find_all("a", href=True):
        m = padrao.search(a["href"])
        if not m:
            continue
        s = m.group(1)
        d = achados.setdefault(s, {"slug": s, "nome": "", "icones": []})
        texto = a.get_text(" ", strip=True)
        if texto and not d["nome"] and not texto.isdigit():
            d["nome"] = texto
        for img in a.find_all("img"):
            arq = re.search(r"/([a-z0-9-]+)\.png", img.get("src", ""))
            if arq and arq.group(1) not in d["icones"]:
                d["icones"].append(arq.group(1))
    for d in achados.values():
        d["nome"] = d["nome"] or nome_de_slug(d["slug"])
    return list(achados.values())


_cache = {}


def arquetipos():
    """slug -> {nome, icones, jogadores} (do cadastro + dos torneios importados)."""
    if "arq" in _cache and time.time() - _cache["arq"][0] < 30:
        return _cache["arq"][1]
    saida = {}
    for r in banco.consultar("SELECT * FROM arquetipos"):
        saida[r["slug"]] = {"slug": r["slug"], "nome": r["nome"], "icones": json.loads(r["icones"] or "[]"), "jogadores": 0}
    for r in banco.consultar("SELECT arquetipo, COUNT(*) AS q FROM t_jogadores WHERE arquetipo != '' GROUP BY arquetipo"):
        a = saida.setdefault(r["arquetipo"], {"slug": r["arquetipo"], "nome": nome_de_slug(r["arquetipo"]),
                                              "icones": [pokemon_id(nome_de_slug(r["arquetipo"]))], "jogadores": 0})
        a["jogadores"] = r["q"]
    _cache["arq"] = (time.time(), saida)
    return saida


def nome_deck(valor):
    """Nome de exibição: slug conhecido -> nome do Limitless; texto livre -> como está."""
    a = arquetipos().get(valor or "")
    return a["nome"] if a else (valor or "")


ARQ_APRENDIDOS = config.PASTA_DADOS / "icones_aprendidos.json"


def icones_aprendidos():
    """Correções de ícone que você fez (arquétipo -> Pokémon do ícone). Valem para todo o programa."""
    try:
        return json.loads(ARQ_APRENDIDOS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def aprender_icones(arquetipo, icones):
    if not arquetipo:
        return
    d = icones_aprendidos()
    if icones:
        d[arquetipo] = icones
    else:
        d.pop(arquetipo, None)
    ARQ_APRENDIDOS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def limpar_icones(lista):
    saida = []
    for i in lista or []:
        p = pokemon_id(i) if i else ""
        p = re.sub(r"[^a-z0-9-]", "", p)
        if p and p not in saida:
            saida.append(p)
    return saida[:2]


def icones_deck(valor):
    aprendido = icones_aprendidos().get(valor or "")
    if aprendido:
        return aprendido
    a = arquetipos().get(valor or "")
    if a and a["icones"]:
        return a["icones"]
    return [pokemon_id(valor)] if valor else []


def sugerir_icones(deck_id, arquetipo):
    """Dois Pokémon principais do deck: primeiro o que você ensinou, depois o ícone do arquétipo
    no Limitless, completando com os Pokémon de maior peso da lista (ex/Mega, Estágio 2, cópias)."""
    a = arquetipos().get(arquetipo or "")
    base = list(icones_aprendidos().get(arquetipo or "") or (a["icones"] if a else []))[:2]
    if len(base) >= 2 or icones_aprendidos().get(arquetipo or ""):
        return base
    pontos = Counter()
    for c in banco.consultar("SELECT nome, qtd FROM meus_decks_cartas WHERE deck_id=? AND secao='Pokémon'", (deck_id,)):
        e = cartas.por_nome(c["nome"]) or {}
        estagio = (e.get("estagio") or "").lower().replace(" ", "")
        peso = 3 if (" ex" in c["nome"] or c["nome"].startswith("Mega ")) else 0
        peso += 2 if estagio == "stage2" else 1 if estagio == "stage1" else 0
        pontos[pokemon_id(c["nome"])] += peso + 0.3 * c["qtd"]
    for p, _ in pontos.most_common():
        if len(base) >= 2:
            break
        if p not in base and _sem_forma(p) not in [_sem_forma(b) for b in base]:
            base.append(p)
    return base


def _icones_do_deck(d):
    try:
        manual = json.loads(d.get("icones_manual") or "[]")
    except Exception:
        manual = []
    d["icones_corrigidos"] = bool(manual)
    return manual or sugerir_icones(d["id"], d["arquetipo"])


def salvar_icones(deck_id, icones):
    """Grava a sua correção no deck e aprende para o arquétipo (próximos decks e telas usam)."""
    icones = limpar_icones(icones)
    r = banco.consultar("SELECT arquetipo FROM meus_decks WHERE id=?", (deck_id,))
    if not r:
        return None
    with banco.conectar() as con:
        con.execute("UPDATE meus_decks SET icones_manual=? WHERE id=?", (json.dumps(icones) if icones else "", deck_id))
    aprender_icones(r[0]["arquetipo"], icones)
    return icones


# ------------------------------------------------------------------ ícones

def pokemon_id(nome_carta):
    """'Mega Lopunny ex' -> 'lopunny-mega'; "N's Zoroark ex" -> 'zoroark'; 'dragapult-ex' -> 'dragapult'."""
    s = slug(nome_carta)
    s = re.sub(r"-(ex|v|vstar|vmax|gx|v-union|break|lv-x|prime|star)$", "", s)
    s = re.sub(PREFIXOS_DONO, "", s)
    mega = s.startswith("mega-")
    s = s[5:] if mega else s
    for regiao, sufixo in REGIOES.items():
        if s.startswith(regiao + "-"):
            s = s[len(regiao) + 1:] + "-" + sufixo
    return s + ("-mega" if mega else "")


def _sem_forma(p):
    return re.sub(r"-(mega|galar|alola|hisui|paldea)$", "", p)


_falhas_icone = {}


def caminho_icone(p):
    p = re.sub(r"[^a-z0-9-]", "", (p or "").lower())
    if not p:
        return None
    destino = PASTA_ICONES / f"{p}.png"
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    if time.time() - _falhas_icone.get(p, 0) < 600:
        return None
    candidatos = [p]
    if _sem_forma(p) != p:
        candidatos.append(_sem_forma(p))  # sem ícone da forma (Mega, regional): usa o Pokémon normal
    for nome in candidatos:
        for fonte in FONTES_ICONE:
            try:
                r = requests.get(fonte.format(p=nome), timeout=15, headers={"User-Agent": "TCGLiveTracker/1.0"})
                if r.status_code == 200 and r.content[:4] == b"\x89PNG":
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(r.content)
                    return destino
            except requests.RequestException:
                continue
    _falhas_icone[p] = time.time()
    return None


# ------------------------------------------------------------------ conhecimento das listas dos torneios

def _assinaturas():
    """arquétipo -> {carta: % das listas}, e carta -> em quantos arquétipos é comum (>=30%)."""
    if "ass" in _cache and time.time() - _cache["ass"][0] < 120:
        return _cache["ass"][1]
    rows = banco.consultar(
        "SELECT j.arquetipo AS arq, l.torneio || '/' || l.labs_id AS lista, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta "
        "FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo != ''")
    listas = defaultdict(set)
    cartas_por_lista = defaultdict(set)
    for r in rows:
        listas[r["arq"]].add(r["lista"])
        cartas_por_lista[(r["arq"], r["lista"])].add(normalizar_nome_carta(r["carta"]))
    perfil = {}
    for arq, ls in listas.items():
        c = Counter(x for l in ls for x in cartas_por_lista[(arq, l)])
        perfil[arq] = {carta: q / len(ls) for carta, q in c.items()}
    comum_em = Counter(carta for p in perfil.values() for carta, f in p.items() if f >= 0.3)
    dados = (perfil, comum_em, len(perfil))
    _cache["ass"] = (time.time(), dados)
    return dados


def identificar(vistas):
    """Melhor arquétipo para um conjunto de cartas reveladas. Devolve slug ou ''."""
    if not vistas:
        return ""
    reveladas = {normalizar_nome_carta(c) for c in vistas}
    pokes = {pokemon_id(c) for c in vistas}
    pokes |= {_sem_forma(p) for p in pokes}  # Mega Lopunny ex também conta como Lopunny
    arqs = arquetipos()
    perfil, comum_em, n_arq = _assinaturas()
    melhor, nota_melhor = "", 0.0
    for s, a in arqs.items():
        nota = 0.0
        for i, ic in enumerate(a["icones"]):
            if ic in pokes:
                nota += 4 if i == 0 else 3
            else:
                nota -= 1.5
        p = perfil.get(s)
        if p:
            for c in reveladas:
                f = p.get(c, 0)
                if f >= 0.3:
                    nota += f * math.log(1 + n_arq / max(comum_em.get(c, 1), 1))
        nota += min(a.get("jogadores", 0), 500) / 10000  # desempate: o deck mais jogado
        if nota > nota_melhor:
            melhor, nota_melhor = s, nota
    return melhor if nota_melhor >= 2.5 else ""


def palpite_deck(resumo, jogador):
    """Arquétipo do Limitless se der para identificar; senão, o palpite do leitor (nome de carta)."""
    s = identificar((resumo.get("vistas") or {}).get(jogador) or {})
    if s:
        return s
    return (resumo.get("deck_palpite") or {}).get(jogador, "")


# ------------------------------------------------------------------ Meus decks

ENERGIA_SIMBOLO = {"G": "Grass", "R": "Fire", "W": "Water", "L": "Lightning", "P": "Psychic",
                   "F": "Fighting", "D": "Darkness", "M": "Metal", "Y": "Fairy", "N": "Dragon", "C": "Colorless"}


def ler_lista(texto):
    """Lê a lista exportada do TCG Live (ou do Limitless). Devolve (cartas, avisos)."""
    cartas_l, avisos, secao = [], [], "Pokémon"
    for bruta in (texto or "").splitlines():
        l = bruta.strip().lstrip("*").strip()
        if not l:
            continue
        cab = re.match(r"^(Pok[eé]mon|Trainer|Energy)\s*(?:\(\d+\))?\s*:?\s*\d*\s*$", l, re.I)
        if cab:
            secao = {"p": "Pokémon", "t": "Trainer", "e": "Energy"}[cab.group(1)[0].lower()]
            continue
        if re.match(r"^total cards", l, re.I):
            continue
        m = re.match(r"^(\d+)\s+(.+?)\s+([A-Z][A-Z0-9]{1,4}(?:-[A-Z0-9]+)?)\s+(\d+[a-zA-Z]?)$", l)
        if m:
            qtd, nome, set_code, numero = m.groups()
        else:
            m = re.match(r"^(\d+)\s+(.+)$", l)
            if not m:
                avisos.append(f"Linha ignorada: {l}")
                continue
            qtd, nome = m.groups()
            set_code = numero = ""
        nome = re.sub(r"\{([A-Z])\}", lambda x: ENERGIA_SIMBOLO.get(x.group(1), x.group(1)), nome)
        nome = re.sub(r"\s+Energy\s+Energy$", " Energy", nome)
        cartas_l.append({"qtd": int(qtd), "nome": nome.strip(), "set": set_code, "numero": numero, "secao": secao})
    total = sum(c["qtd"] for c in cartas_l)
    if cartas_l and total != 60:
        avisos.append(f"A lista tem {total} cartas (o normal são 60).")
    return cartas_l, avisos


def salvar_deck(dados, deck_id=None):
    cartas_l, avisos = ler_lista(dados.get("lista", ""))
    if not cartas_l:
        raise ValueError("Não encontrei cartas na lista. Cole a lista exportada do TCG Live (Pokémon: ..., Trainer: ..., Energy: ...).")
    nome = (dados.get("nome") or "").strip() or "Meu deck"
    arq = (dados.get("arquetipo") or "").strip()
    if not arq:
        arq = identificar({c["nome"]: c["qtd"] for c in cartas_l})
    with banco.conectar() as con:
        if deck_id:
            con.execute("UPDATE meus_decks SET nome=?, arquetipo=?, lista=?, notas=? WHERE id=?",
                        (nome, arq, dados.get("lista", ""), dados.get("notas", ""), deck_id))
            con.execute("DELETE FROM meus_decks_cartas WHERE deck_id=?", (deck_id,))
        else:
            cur = con.execute("INSERT INTO meus_decks (nome, arquetipo, lista, notas, ativo, criado_em, versao_de) VALUES (?,?,?,?,1,?,?)",
                              (nome, arq, dados.get("lista", ""), dados.get("notas", ""),
                               datetime.now().isoformat(timespec="seconds"), dados.get("versao_de")))
            deck_id = cur.lastrowid
        for c in cartas_l:
            e = cartas.converter(c["set"], c["numero"], c["nome"]) if c["set"] else cartas.por_nome(c["nome"])
            con.execute("INSERT INTO meus_decks_cartas VALUES (?,?,?,?,?,?,?,?)",
                        (deck_id, c["qtd"], c["nome"], c["set"], c["numero"], c["secao"], e["id"] if e else "", e["nome"] if e else ""))
    return deck_id, avisos


def listar_decks():
    decks = banco.consultar("SELECT * FROM meus_decks ORDER BY favorito DESC, ativo DESC, criado_em DESC")
    for d in decks:
        d["nome_arquetipo"] = nome_deck(d["arquetipo"])
        d["icones"] = _icones_do_deck(d)
        # capa: o Pokémon "ex" mais numeroso da lista (ou o primeiro Pokémon)
        pokes = banco.consultar("SELECT nome, carta_id, qtd FROM meus_decks_cartas WHERE deck_id=? AND secao='Pokémon' ORDER BY rowid", (d["id"],))
        capa = sorted(pokes, key=lambda c: (" ex" not in c["nome"] and "Mega" not in c["nome"], -c["qtd"]))
        d["capa"] = {"id": capa[0]["carta_id"], "nome": capa[0]["nome"]} if capa else None
    return decks


def obter_deck(deck_id):
    r = banco.consultar("SELECT * FROM meus_decks WHERE id=?", (deck_id,))
    if not r:
        return None
    d = r[0]
    d["cartas"] = banco.consultar("SELECT * FROM meus_decks_cartas WHERE deck_id=? ORDER BY rowid", (deck_id,))
    d["nome_arquetipo"] = nome_deck(d["arquetipo"])
    d["icones"] = _icones_do_deck(d)
    return d


def _nomes_deck(deck_id):
    return {normalizar_nome_carta(c["nome"]) for c in banco.consultar("SELECT nome FROM meus_decks_cartas WHERE deck_id=?", (deck_id,))} | \
           {normalizar_nome_carta(c["carta_base"]) for c in banco.consultar("SELECT carta_base FROM meus_decks_cartas WHERE deck_id=? AND carta_base != ''", (deck_id,))}


def cobertura(vistas, deck_id):
    """Fração das cartas reveladas que existem na lista (1.0 = todas estão na lista)."""
    reveladas = {normalizar_nome_carta(c) for c in vistas}
    if not reveladas:
        return 0.0
    nomes = _nomes_deck(deck_id)
    return len(reveladas & nomes) / len(reveladas)


def vincular_automatico(pid, sobrescrever=False):
    """Liga a partida à lista de "Meus decks" que contém as cartas que você revelou."""
    from . import analises
    p = banco.obter_partida(pid)
    if not p or (p.get("deck_id") and not sobrescrever) or p.get("dono"):
        return None  # partidas de amigos não usam as suas listas
    eu = analises.descobrir_eu(banco.listar_partidas(), config.ler_config()["nick"])
    vistas = (p["resumo"].get("vistas") or {}).get(eu)
    if not vistas:
        return None
    notas = sorted(((cobertura(vistas, d["id"]), d["criado_em"], d["id"]) for d in banco.consultar("SELECT id, criado_em FROM meus_decks WHERE ativo=1")),
                   reverse=True)
    if notas and notas[0][0] >= 0.9:
        banco.atualizar_partida(pid, {"deck_id": notas[0][2]})
        return notas[0][2]
    return None


# ------------------------------------------------------------------ versão certa de cartas com o mesmo nome

def resolver_versoes(rep, partida, eu):
    """
    Cartas diferentes podem ter o mesmo nome (ex.: Dunsparce TEF 128 e JTG 120). O log só traz o
    nome, então escolhemos a versão nesta ordem:
      1. ataque/habilidade usado no log que só uma das versões tem;
      2. a versão que está na sua lista de "Meus decks" ligada à partida;
      3. a versão mais usada nas listas dos torneios para o deck do adversário (ou no geral);
      4. a versão mais recente.
    Devolve {jogador: {nome: id da arte básica}}.
    """
    ind = cartas.indice()
    golpes = defaultdict(set)  # (jogador, nome) -> golpes usados
    for q in rep["quadros"]:
        d = q["destaque"]
        if d.get("tipo") in ("ataque", "habilidade") and d.get("carta") and d.get("golpe"):
            golpes[(d["jogador"], d["carta"])].add(cartas.normalizar(d["golpe"]))
    nomes = defaultdict(set)
    for q in rep["quadros"]:
        for j, m in q["estado"]["mesa"].items():
            for p in ([m["ativo"]] if m["ativo"] else []) + m["banco"]:
                nomes[j].add(p["nome"])
    lista_deck = {}
    if partida.get("deck_id"):
        for c in banco.consultar("SELECT nome, carta_base, carta_id, qtd FROM meus_decks_cartas WHERE deck_id=? AND carta_id != ''", (partida["deck_id"],)):
            lista_deck.setdefault(cartas.normalizar(c["carta_base"] or c["nome"]), []).append(c["carta_id"])
    uso = Counter()
    for r in banco.consultar("SELECT carta_id, COUNT(*) AS q FROM t_listas WHERE carta_id != '' GROUP BY carta_id"):
        uso[r["carta_id"]] = r["q"]

    saida = {}
    for j, ns in nomes.items():
        saida[j] = {}
        for nome in ns:
            chaves = ind["por_nome"].get(cartas.normalizar(nome)) or []
            if len(chaves) <= 1:
                continue  # só existe uma versão: o padrão já resolve
            ids = [ind["basica"][k] for k in chaves]
            usados = golpes.get((j, nome))
            escolha = None
            if usados:
                compat = [ind["basica"][k] for k in chaves if usados & set(k.split("|")[-1].split(",") + k.split("|")[-2].split(","))]
                if len(compat) == 1:
                    escolha = compat[0]
            if not escolha and j == eu and cartas.normalizar(nome) in lista_deck:
                escolha = lista_deck[cartas.normalizar(nome)][0]
            if not escolha:
                melhor = max(ids, key=lambda i: uso.get(i, 0))
                if uso.get(melhor, 0):
                    escolha = melhor
            saida[j][nome] = escolha or ids[0]
    return saida
