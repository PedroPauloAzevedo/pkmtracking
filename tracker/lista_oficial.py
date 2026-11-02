"""
LISTA DE DECK NO FORMATO OFICIAL (formulário Deck List da Play! Pokémon), só Standard.

A partir de uma lista de "Meus decks" o programa monta o formulário oficial:
  Pokémon      quantidade, nome, coleção, número e marca de regulamento (REG)
  Treinadores  quantidade e nome
  Energias     quantidade e nome
Você edita na tela, salva (fica guardado no deck) e usa "Salvar em PDF" (impressão do navegador).
Nome, Player ID e data de nascimento ficam só no seu computador (dados/config.json).

Também confere a lista com as regras do Standard: 60 cartas, até 4 com o mesmo nome (fora
Energia Básica; versões diferentes somam), 1 ACE SPEC, pelo menos 1 Pokémon Básico e só cartas
com marca de regulamento válida (ou reimpressas com marca válida, mesmo nome e mesmo texto).
"""
import hashlib
import json
from collections import Counter
from datetime import date, datetime

from . import banco, cartas, config, regras_jogo
from .leitor import normalizar_nome_carta

SECOES = (("pokemon", "Pokémon"), ("trainer", "Trainer"), ("energy", "Energy"))
NOME_SERIE = {"sv": "Scarlet & Violet Series", "me": "Mega Evolution Series"}
PROMOS = {"svp", "mep"}


# ------------------------------------------------------------------ dados de cada carta da lista

def _impressao(set_code, numero):
    """A impressão exata (coleção + número), se estiver na biblioteca."""
    if not set_code or not numero:
        return None
    ind = cartas.indice()
    id_ = ind["por_codigo"].get(f"{set_code.upper()}|{cartas._num(numero)}")
    return ind["cartas"].get(id_) if id_ else None


def info(nome, set_code="", numero="", carta_id=""):
    """Tudo que a lista oficial e a conferência precisam saber de uma linha."""
    ind = cartas.indice()
    exata = _impressao(set_code, numero)
    base = ind["cartas"].get(carta_id or "") or (cartas.converter(set_code, numero, nome) if set_code else cartas.por_nome(nome))
    if exata:
        a, b = normalizar_nome_carta(exata["nome"]), normalizar_nome_carta(nome)
        if a != b and a not in b and b not in a:
            exata = None  # número de outra carta (código de coleção diferente no TCG Live)
    e = exata or base
    chave = e["chave"] if e else None
    grupo = cartas.grupo(chave) if chave else []
    if not exata and grupo and numero:
        # código que a biblioteca não conhece (ex.: PR-SV 149 = SVP 149): procura pelo número no grupo
        exata = next((x for x in grupo if x["numero"] == cartas._num(numero)), None)
    marcas = regras_jogo.marcas_standard()
    alternativa = next((x for x in grupo if (x.get("marca") or "") in marcas), None)
    manual = bool(exata and exata.get("set") == "manual")  # imagem adicionada à mão: marca desconhecida
    return {
        "marca": (exata or {}).get("marca") or "",
        "conhecida": bool(e),
        "legal": None if manual else (cartas.legal_chave(chave) if chave else None),
        "ace_spec": any(x.get("ace_spec") for x in grupo),
        "basico": any((x.get("estagio") or "").lower() == "basic" for x in grupo),
        "energia_basica": cartas.eh_energia_basica(nome),
        "alternativa": f"{alternativa['codigo']} {alternativa['local']}" if alternativa else "",
    }


# ------------------------------------------------------------------ conferência com as regras do Standard

def validar(linhas):
    """linhas = {"pokemon": [{qtd, nome, set, numero}], "trainer": [...], "energy": [...]}.
    Devolve {total, por_secao, problemas, avisos}. Problema = a lista não vale; aviso = vale, mas confira."""
    marcas = regras_jogo.marcas_standard()
    problemas, avisos = [], []
    por_secao, por_nome, nome_exib, ace, n_ace, basicos = {}, Counter(), {}, [], 0, 0
    for chave_secao, secao in SECOES:
        soma = 0
        for c in linhas.get(chave_secao) or []:
            nome = (c.get("nome") or "").strip()
            try:
                qtd = int(c.get("qtd") or 0)
            except (TypeError, ValueError):
                qtd = 0
            if not nome or qtd <= 0:
                continue
            soma += qtd
            i = info(nome, c.get("set") or "", c.get("numero") or "")
            n = normalizar_nome_carta(nome)
            if not i["energia_basica"]:
                por_nome[n] += qtd
                nome_exib.setdefault(n, nome)
            if i["ace_spec"]:
                ace.append(f"{qtd}× {nome}")
                n_ace += qtd
            if secao == "Pokémon" and i["basico"]:
                basicos += qtd
            onde = f" ({c.get('set')} {c.get('numero')})" if c.get("set") else ""
            if i["energia_basica"]:
                continue
            if i["legal"] is False:
                problemas.append(f"{nome}{onde} não vale no Standard: marca {i['marca'] or 'antiga'} e nenhuma reimpressão com marca {', '.join(marcas)}.")
            elif not i["conhecida"]:
                avisos.append(f"{nome}: não está na biblioteca de cartas, então não deu para conferir a marca de regulamento.")
            elif i["legal"] is None:
                avisos.append(f"{nome}{onde}: a biblioteca ainda não informa a marca de regulamento; confira na carta.")
            elif secao == "Pokémon" and i["marca"] and i["marca"] not in marcas:
                avisos.append(f"{nome}{onde} tem marca {i['marca']}: vale pela regra de reimpressão (mesmo nome e texto de {i['alternativa']}).")
        por_secao[chave_secao] = soma
    total = sum(por_secao.values())
    if total != regras_jogo.TAMANHO_DECK:
        problemas.insert(0, f"A lista tem {total} cartas: no Standard são exatamente {regras_jogo.TAMANHO_DECK}.")
    for n, q in por_nome.items():
        if q > regras_jogo.MAX_COPIAS:
            problemas.append(f"{nome_exib[n]}: {q} cópias. O máximo é {regras_jogo.MAX_COPIAS} com o mesmo nome (versões diferentes somam).")
    if n_ace > regras_jogo.MAX_ACE_SPEC:
        problemas.append(f"Mais de 1 ACE SPEC ({', '.join(ace)}): só pode 1 no deck inteiro.")
    if total and not basicos:
        problemas.append("Nenhum Pokémon Básico na lista: o deck precisa de pelo menos 1.")
    return {"total": total, "por_secao": por_secao, "problemas": problemas, "avisos": avisos,
            "valida": not problemas, "marcas": list(marcas)}


# ------------------------------------------------------------------ montar e guardar

def _assinatura(lista_texto):
    return hashlib.sha1((lista_texto or "").encode("utf-8")).hexdigest()[:12]


def gerar(deck):
    """Lista oficial a partir das cartas do deck (sem as suas edições)."""
    saida = {"pokemon": [], "trainer": [], "energy": []}
    for c in deck["cartas"]:
        if c["secao"] == "Pokémon":
            i = info(c["nome"], c["set_code"], c["numero"], c.get("carta_id") or "")
            saida["pokemon"].append({"qtd": c["qtd"], "nome": c["nome"], "set": c["set_code"] or "", "numero": c["numero"] or "", "reg": i["marca"]})
        else:
            saida["trainer" if c["secao"] == "Trainer" else "energy"].append({"qtd": c["qtd"], "nome": c["nome"]})
    return saida


def colecoes_standard(hoje=None):
    """Legenda do formulário: coleções que têm cartas válidas no Standard, por série."""
    hoje = (hoje or date.today()).isoformat()
    marcas = regras_jogo.marcas_standard()
    por_set = {}
    for e in cartas.indice()["cartas"].values():
        if e["set"] == "manual" or not e.get("codigo"):
            continue
        s = por_set.setdefault(e["set"], {"codigo": e["codigo"], "nome": e["set_nome"], "serie": e.get("serie") or "",
                                          "data": e.get("data") or "", "validas": 0, "sem_marca": 0, "nao_energia": 0})
        if (e.get("categoria") or "").lower() == "energy":
            continue
        s["nao_energia"] += 1
        if e.get("marca") in marcas:
            s["validas"] += 1
        elif not e.get("marca"):
            s["sem_marca"] += 1
    com_marca = [s["data"] for sid, s in por_set.items() if s["validas"] and sid not in PROMOS]
    inicio = min(com_marca) if com_marca else ""
    lista = []
    for sid, s in por_set.items():
        if not s["nao_energia"] or s["data"] > hoje or "classic collection" in s["nome"].lower():
            continue  # (as "Classic Collection" são reimpressões de cartas antigas, fora do Standard)
        # coleção nova que o TCGdex ainda não marcou (ex.: 30th Celebration): entra se for desta época
        if s["validas"] or (s["sem_marca"] == s["nao_energia"] and inicio and s["data"] >= inicio):
            grupo = "Promotional Cards" if sid in PROMOS else NOME_SERIE.get(s["serie"], "Other")
            lista.append({"codigo": s["codigo"], "nome": s["nome"], "data": s["data"], "grupo": grupo, "sem_marca": not s["validas"]})
    lista.sort(key=lambda x: x["data"])
    return lista


def obter(deck_id):
    from . import decks
    d = decks.obter_deck(deck_id)
    if not d:
        return None
    try:
        salva = json.loads(d.get("lista_oficial") or "null")
    except ValueError:
        salva = None
    gerada = gerar(d)
    linhas = (salva or {}).get("linhas") or gerada
    cfg = config.ler_config()
    sets = colecoes_standard()
    ultima = next((s["nome"] for s in reversed(sets) if s["grupo"] != "Promotional Cards"), "")
    return {
        "deck": {"id": d["id"], "nome": d["nome"], "arquetipo": d.get("nome_arquetipo") or ""},
        "linhas": linhas, "gerada": gerada,
        "editada": bool(salva), "salvo_em": (salva or {}).get("salvo_em"),
        "deck_mudou": bool(salva) and salva.get("origem") != _assinatura(d.get("lista")),
        "jogador": {"nome": cfg.get("jogador_nome", ""), "id": cfg.get("jogador_id", ""), "nascimento": cfg.get("jogador_nascimento", "")},
        "divisoes": regras_jogo.divisoes_idade(), "colecoes": sets, "ultima_colecao": ultima,
        "validacao": validar(linhas),
    }


def _limpar_linhas(linhas):
    saida = {}
    for chave_secao, _ in SECOES:
        lista = []
        for c in (linhas or {}).get(chave_secao) or []:
            nome = str(c.get("nome") or "").strip()[:80]
            if not nome:
                continue
            try:
                qtd = max(0, min(60, int(c.get("qtd") or 0)))
            except (TypeError, ValueError):
                qtd = 0
            item = {"qtd": qtd, "nome": nome}
            if chave_secao == "pokemon":
                item.update({k: str(c.get(k) or "").strip()[:12] for k in ("set", "numero", "reg")})
            lista.append(item)
        saida[chave_secao] = lista
    return saida


def salvar(deck_id, linhas, jogador=None):
    from . import decks
    d = decks.obter_deck(deck_id)
    if not d:
        return None
    dados = {"linhas": _limpar_linhas(linhas), "origem": _assinatura(d.get("lista")),
             "salvo_em": datetime.now().isoformat(timespec="seconds")}
    with banco.conectar() as con:
        con.execute("UPDATE meus_decks SET lista_oficial=? WHERE id=?", (json.dumps(dados, ensure_ascii=False), deck_id))
    if jogador is not None:
        cfg = config.ler_config()
        for k_cfg, k in (("jogador_nome", "nome"), ("jogador_id", "id"), ("jogador_nascimento", "nascimento")):
            cfg[k_cfg] = str(jogador.get(k) or "").strip()[:60]
        config.salvar_config(cfg)
    return obter(deck_id)


def descartar(deck_id):
    """Volta a lista oficial para a do deck (apaga as suas edições)."""
    with banco.conectar() as con:
        con.execute("UPDATE meus_decks SET lista_oficial='' WHERE id=?", (deck_id,))
    return obter(deck_id)
