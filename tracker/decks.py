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

# Muda a cada gravação do cadastro de decks. O painel recebe esse número em /api/status e, quando ele muda, busca de novo
# os nomes e ícones (sem isso, a janela aberta antes de o cadastro ser refeito ficava sem ícones até apertar F5).
versao_arquetipos = [0]


def salvar_arquetipos(lista):
    """Grava nomes e ícones dos decks. Lista de ícones vazia não apaga a que já existia (uma página do Labs com layout novo
    chegou a zerar os ícones de quase todos os decks em 05/11/2026)."""
    agora = datetime.now().isoformat(timespec="seconds")
    with banco.conectar() as con:
        for a in lista:
            con.execute("INSERT INTO arquetipos (slug, nome, icones, atualizado_em) VALUES (?,?,?,?) "
                        "ON CONFLICT(slug) DO UPDATE SET nome=excluded.nome, atualizado_em=excluded.atualizado_em, "
                        "icones=CASE WHEN excluded.icones = '[]' THEN arquetipos.icones ELSE excluded.icones END",
                        (a["slug"], a["nome"], json.dumps(a["icones"]), agora))
    _cache.clear()
    versao_arquetipos[0] += 1


def icones_sem_cadastro():
    """Quantos decks do cadastro estão sem ícone (para refazer o cadastro quando a maioria está vazia)."""
    r = banco.consultar("SELECT COUNT(*) AS n, SUM(icones = '[]') AS vazios FROM arquetipos")[0]
    return r["n"] or 0, r["vazios"] or 0


def ler_pagina_decks(sopa, tid):
    """Lê /<torneio>/decks do Labs: [{slug, nome, icones}].
    Os ícones ficavam dentro do link do deck; desde 11/2026 ficam numa coluna à parte da mesma linha da tabela
    (<img class="pokemon" src=".../pokemon/gen9/dragapult.png">): procura nos dois lugares."""
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
        linha = a.find_parent("tr")
        for img in a.find_all("img") or (linha.find_all("img") if linha else []):
            arq = re.search(r"/([a-z0-9-]+)\.png", img.get("src", ""))
            if arq and arq.group(1) not in d["icones"]:
                d["icones"].append(arq.group(1))
    for d in achados.values():
        d["nome"] = d["nome"] or nome_de_slug(d["slug"])
    return list(achados.values())


_cache = {}


def _em_dia(chave, segundos=3600):
    """A conta guardada em _cache[chave] ainda vale? Vale enquanto os torneios não mudarem (banco.versao_torneios)
    e por no máximo `segundos`. Guardada sem versão (ex.: pelos experimentos), vale só pelo tempo."""
    x = _cache.get(chave)
    if not x or time.time() - x[0] >= segundos:
        return False
    return len(x) < 3 or x[2] == banco.versao_torneios()


def arquetipos():
    """slug -> {nome, icones, jogadores} (do cadastro + dos torneios importados)."""
    if _em_dia("arq"):
        return _cache["arq"][1]
    versao = banco.versao_torneios()
    saida = {}
    for r in banco.consultar("SELECT * FROM arquetipos"):
        saida[r["slug"]] = {"slug": r["slug"], "nome": r["nome"], "icones": json.loads(r["icones"] or "[]"), "jogadores": 0}
    for r in banco.consultar("SELECT arquetipo, COUNT(*) AS q FROM t_jogadores WHERE arquetipo != '' GROUP BY arquetipo"):
        a = saida.setdefault(r["arquetipo"], {"slug": r["arquetipo"], "nome": nome_de_slug(r["arquetipo"]),
                                              "icones": [pokemon_id(nome_de_slug(r["arquetipo"]))], "jogadores": 0})
        a["jogadores"] = r["q"]
    _cache["arq"] = (time.time(), saida, versao)
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
    if _em_dia("ass"):
        return _cache["ass"][1]
    versao = banco.versao_torneios()
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
    _cache["ass"] = (time.time(), dados, versao)
    return dados


MINIMO_LISTAS_NB = 200   # com menos listas de torneio que isso, o modelo de probabilidade não tem base
CONFIANCA_NB = 0.5       # abaixo disso, vale o método por ícones (e depois o palpite pelo dano, no leitor)


def _modelo_nb():
    """Para cada deck: quantas listas e em quantas delas cada carta aparece (listas dos torneios importados)."""
    if _em_dia("nb"):
        return _cache["nb"][1]
    versao = banco.versao_torneios()
    rows = banco.consultar(
        "SELECT j.arquetipo AS arq, l.torneio || '/' || l.labs_id AS lista, COALESCE(NULLIF(l.carta_base,''), l.carta) AS carta "
        "FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE j.arquetipo != ''")
    cartas_lista = defaultdict(set)
    arq_lista = {}
    for r in rows:
        cartas_lista[r["lista"]].add(normalizar_nome_carta(r["carta"]))
        arq_lista[r["lista"]] = r["arq"]
    n = Counter(arq_lista.values())
    cont = defaultdict(Counter)
    geral = Counter()
    for lista, cs in cartas_lista.items():
        cont[arq_lista[lista]].update(cs)
        geral.update(cs)
    total = len(arq_lista)
    # Índice para calcular rápido (mesmas contas de _identificar_nb_direto, reorganizadas):
    #   nota(deck) = log(fração de listas do deck) - (cartas vistas) * log(listas do deck + BETA)
    #              + soma, para cada carta vista que o deck usa, de log(1 + vezes / (BETA * freq. geral))
    # (a parte igual para todos os decks foi tirada: não muda o vencedor nem a confiança)
    validos = {a: q for a, q in n.items() if q >= MIN_LISTAS_DECK}
    base = {a: math.log(q / total) for a, q in validos.items()} if total else {}
    log_n = {a: math.log(q + BETA_NB) for a, q in validos.items()}
    indice = defaultdict(dict)
    for a in validos:
        for carta, vezes in cont[a].items():
            g = BETA_NB * (geral[carta] + 1) / (total + 2)
            indice[carta][a] = math.log(1 + vezes / g)
    dados = {"n": n, "cont": cont, "geral": geral, "total": total, "base": base, "log_n": log_n, "indice": indice}
    _cache["nb"] = (time.time(), dados, versao)
    _cache.pop("ident", None)  # modelo novo: esquece as identificações já feitas
    return dados


BETA_NB = 2.0          # força da suavização pela frequência geral da carta
MIN_LISTAS_DECK = 3    # deck com 1 ou 2 listas "aceita" qualquer carta e ganharia por acaso


def identificar_nb(reveladas):
    """Naive Bayes: o deck em que as cartas vistas são mais prováveis. Devolve (slug, confiança 0-1).
    Só as cartas vistas contam (não ver uma carta não prova que ela não está no deck).
    Testado em testes/experimentos/e2_identificar_deck.py: acerta mais que o método por ícones com poucas cartas.
    Usa o índice do modelo: só os decks que têm as cartas vistas recebem pontos extras."""
    m = _modelo_nb()
    if m["total"] < MINIMO_LISTAS_NB or not reveladas or not m["base"]:
        return "", 0.0
    k = len(reveladas)
    notas = {a: b - k * m["log_n"][a] for a, b in m["base"].items()}
    for carta in reveladas:
        for a, extra in m["indice"].get(carta, {}).items():
            notas[a] += extra
    melhor = max(notas, key=notas.get)
    topo = notas[melhor]
    return melhor, 1 / sum(math.exp(v - topo) for v in notas.values())


def _identificar_nb_direto(reveladas, beta=BETA_NB, minimo=MIN_LISTAS_DECK):
    """A mesma conta de identificar_nb, sem o índice (mais lenta). Fica para conferir que as duas batem."""
    m = _modelo_nb()
    if m["total"] < MINIMO_LISTAS_NB or not reveladas:
        return "", 0.0
    notas = {}
    for a, n in m["n"].items():
        if n < minimo:
            continue  # deck com 1 ou 2 listas "aceita" qualquer carta e ganharia por acaso
        c = m["cont"][a]
        # suavização pela frequência geral da carta: carta comum em todo deck pesa pouco; rara, pesa muito
        notas[a] = math.log(n / m["total"]) + sum(
            math.log((c.get(x, 0) + beta * (m["geral"].get(x, 0) + 1) / (m["total"] + 2)) / (n + beta)) for x in reveladas)
    if not notas:
        return "", 0.0
    melhor = max(notas, key=notas.get)
    topo = notas[melhor]
    return melhor, 1 / sum(math.exp(v - topo) for v in notas.values())


def identificar(vistas):
    """Melhor arquétipo para um conjunto de cartas reveladas. Devolve slug ou ''.
    Primeiro o modelo de probabilidade (se houver listas de torneio suficientes e ele estiver confiante);
    senão, o método por ícones e assinatura de cartas."""
    if not vistas:
        return ""
    _modelo_nb()  # garante o modelo em dia antes de olhar a memória de identificações
    memoria = _cache.setdefault("ident", {})
    chave = frozenset(vistas)
    if chave not in memoria:
        s, confianca = identificar_nb({normalizar_nome_carta(c) for c in vistas if not cartas.eh_energia_basica(c)})
        memoria[chave] = s if s and confianca >= CONFIANCA_NB else _identificar_por_icones(vistas)
    return memoria[chave]


def _identificar_por_icones(vistas):
    """Método anterior: ícone do deck entre os Pokémon vistos + assinatura de cartas comuns no deck."""
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
        # código da coleção: 2 a 5 letras/dígitos com pelo menos uma letra (SFA, PR-SV, 30C...)
        m = re.match(r"^(\d+)\s+(.+?)\s+((?=[A-Z0-9]*[A-Z])[A-Z0-9]{2,5}(?:-[A-Z0-9]+)?)\s+(\d+[a-zA-Z]?)$", l)
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
    # Confere com as regras do Standard (60 cartas, 4 cópias, ACE SPEC, Básico, marcas de regulamento)
    from . import lista_oficial
    v = lista_oficial.validar(lista_oficial.gerar(obter_deck(deck_id)))
    avisos = [a for a in avisos if not a.startswith("A lista tem")] + [f"Standard: {x}" for x in v["problemas"]]
    return deck_id, avisos


def reler_listas():
    """Relê as listas salvas com o leitor atual (ex.: códigos que começam com número, como 30C)."""
    n = 0
    for d in banco.consultar("SELECT id, lista FROM meus_decks"):
        novas, _ = ler_lista(d["lista"])
        atuais = banco.consultar("SELECT nome, set_code, numero FROM meus_decks_cartas WHERE deck_id=? ORDER BY rowid", (d["id"],))
        if not novas or [(c["nome"], c["set"], c["numero"]) for c in novas] == [(c["nome"], c["set_code"], c["numero"]) for c in atuais]:
            continue
        with banco.conectar() as con:
            con.execute("DELETE FROM meus_decks_cartas WHERE deck_id=?", (d["id"],))
            for c in novas:
                e = cartas.converter(c["set"], c["numero"], c["nome"]) if c["set"] else cartas.por_nome(c["nome"])
                con.execute("INSERT INTO meus_decks_cartas VALUES (?,?,?,?,?,?,?,?)",
                            (d["id"], c["qtd"], c["nome"], c["set"], c["numero"], c["secao"], e["id"] if e else "", e["nome"] if e else ""))
        n += 1
    return n


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
    exportou = p["resumo"].get("exportou")
    # o próprio log diz quem exportou; só sem isso é preciso ler todas as partidas para descobrir "você"
    # (ler todas a cada partida nova deixava a importação de muitos logs cada vez mais lenta)
    eu = exportou if exportou in p["jogadores"] else analises.perspectiva(
        p, analises.descobrir_eu(banco.listar_partidas(), config.ler_config()["nick"]))
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

def _limites_ps(quadros):
    """O que o replay revela dos PS de cada Pokémon: {(jogador, nome): (mínimo exclusivo, máximo ou None)}.
    Ficou em jogo com D de dano -> PS > D. Nocauteado com D de dano (D > 0) -> PS <= D.
    Nocaute sem dano (ex.: Dusclops que se nocauteia com Cursed Blast) não diz nada."""
    def pokemons(q):
        for j, m in q["estado"]["mesa"].items():
            for p in ([m["ativo"]] if m["ativo"] else []) + m["banco"]:
                yield j, p
    # 1º: com quanto dano cada Pokémon caiu (o dano do quadro anterior ao nocaute)
    caiu_com = {}
    for i, q in enumerate(quadros):
        if i and q["destaque"].get("tipo") == "nocaute" and q["destaque"].get("uid"):
            for j, p in pokemons(quadros[i - 1]):
                if p["uid"] == q["destaque"]["uid"] and p["dano"]:
                    caiu_com[p["uid"]] = (j, p["nome"], p["dano"])
    # 2º: o dano que ele aguentou (o dano fatal, mostrado antes do nocaute, não conta)
    limites = {}
    for q in quadros:
        for j, p in pokemons(q):
            fatal = caiu_com.get(p["uid"])
            if fatal and fatal[1] == p["nome"] and p["dano"] >= fatal[2]:
                continue
            mi, ma = limites.get((j, p["nome"]), (0, None))
            limites[(j, p["nome"])] = (max(mi, p["dano"]), ma)
    for j, nome, dano in caiu_com.values():
        mi, ma = limites.get((j, nome), (0, None))
        limites[(j, nome)] = (mi, dano if ma is None else min(ma, dano))
    return limites


def _ps_compativel(chave, minimo, maximo):
    try:
        ps = int(chave.split("|")[1])
    except (IndexError, ValueError):
        return True  # PS desconhecido: não dá para descartar
    return ps > minimo and (maximo is None or ps <= maximo)


def resolver_versoes(rep, partida, eu):
    """
    Cartas diferentes podem ter o mesmo nome (ex.: Dunsparce TEF 128 e JTG 120). O log só traz o
    nome, então escolhemos a versão nesta ordem:
      0. só as versões que valem no Standard (marca de regulamento válida), se houver alguma;
      0b. só as versões com PS compatíveis com o replay: nocauteado com 60 de dano tem no máximo 60 PS,
          e quem ficou em jogo com 60 de dano tem mais de 60 (ver _limites_ps);
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
    limites = _limites_ps(rep["quadros"])
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
            chaves = cartas._preferir_standard(chaves)
            validas = [k for k in chaves if cartas.legal_chave(k) is not False] or chaves
            minimo, maximo = limites.get((j, nome), (0, None))
            pelos_ps = [k for k in validas if _ps_compativel(k, minimo, maximo)]
            validas = pelos_ps or validas  # nenhuma versão bate (ex.: ferramenta que dá PS): ignora a pista
            ids = [ind["basica"][k] for k in validas]
            usados = golpes.get((j, nome))
            escolha = None
            if usados:
                def compativeis(ks):
                    return [ind["basica"][k] for k in ks if usados & set(k.split("|")[-1].split(",") + k.split("|")[-2].split(","))]
                compat = compativeis(validas) or compativeis(chaves)
                if len(compat) == 1:
                    escolha = compat[0]
            if not escolha and j == eu and cartas.normalizar(nome) in lista_deck:
                da_lista = lista_deck[cartas.normalizar(nome)]
                if not pelos_ps:
                    escolha = da_lista[0]
                else:  # a lista só vale se a versão dela tem os PS que o replay mostrou
                    escolha = next((i for i in da_lista if cartas._basica_de(i) and cartas._basica_de(i)["id"] in ids), None)
            if not escolha:
                melhor = max(ids, key=lambda i: uso.get(i, 0))
                if uso.get(melhor, 0):
                    escolha = melhor
            saida[j][nome] = escolha or ids[0]
    return saida
