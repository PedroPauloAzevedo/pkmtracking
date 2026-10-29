"""
REVISÃO DE LINHAS NÃO LIDAS

Quando o log traz uma frase que nenhuma regra conhece, ela vira "linha não lida".
Aqui juntamos essas linhas em MODELOS, trocando o que muda de partida para partida:
    {J} = nome de jogador      {C} = nome de carta      {N} = número
Ex.: "PEPONILDO put 5 damage counters on Gokuzera's Mega Kangaskhan ex."
  -> "{J} put {N} damage counters on {J}'s {C}."

Para cada modelo você decide:
  - Ignorar: a frase não muda nenhuma estatística (vira uma regra do tipo "ignorar");
  - Criar regra: escolhe o tipo de evento; a expressão regular é montada a partir do modelo.
Depois de salvar, todas as partidas são relidas.
"""
import re

from . import banco, config, leitor

# Palavras que costumam indicar que a frase mexe no resultado ou nas estatísticas.
SINAIS_IMPORTANTES = [
    (r"damage", "Fala de dano: pode mudar o dano total e o replay."),
    (r"prize", "Fala de prêmios: pode mudar o placar."),
    (r"knocked out", "Fala de nocaute."),
    (r"\bwins?\b|conceded|lost", "Fala do fim da partida."),
    (r"evolved|devolved", "Fala de evolução."),
    (r"attached", "Fala de energia ou ferramenta ligada."),
    (r"\bused\b", "Fala de ataque ou habilidade."),
    (r"played", "Fala de carta jogada."),
    (r"heal", "Fala de cura (dano removido)."),
]


def modelo_da_linha(linha, jogadores, cartas_conhecidas):
    m = linha
    for j in sorted(jogadores, key=len, reverse=True):
        m = m.replace(j, "\x01")
    for c in sorted(cartas_conhecidas, key=len, reverse=True):
        if len(c) >= 3:
            m = re.sub(rf"(?<![\w']){re.escape(c)}(?![\w])", "\x02", m)
    m = re.sub(r"\b\d+\b", "\x03", m)
    return m.replace("\x01", "{J}").replace("\x02", "{C}").replace("\x03", "{N}")


def regex_do_modelo(modelo):
    """Monta a expressão regular: 1º jogador = player, 1ª carta = card, 2ª carta = target, 1º número = qtd."""
    partes = re.split(r"(\{[JCN]\})", modelo)
    saida, cont = [], {"J": 0, "C": 0, "N": 0}
    nomes = {"J": ["player"], "C": ["card", "target"], "N": ["qtd"]}
    for p in partes:
        mm = re.fullmatch(r"\{([JCN])\}", p)
        if not mm:
            saida.append(re.escape(p))
            continue
        k = mm.group(1)
        disponiveis = nomes[k]
        nome = disponiveis[cont[k]] if cont[k] < len(disponiveis) else None
        cont[k] += 1
        corpo = r"\d+" if k == "N" else ".+?"
        saida.append(f"(?P<{nome}>{corpo})" if nome else f"(?:{corpo})")
    return "^" + "".join(saida) + "$"


def sugestao(modelo):
    baixo = modelo.lower()
    for padrao, motivo in SINAIS_IMPORTANTES:
        if re.search(padrao, baixo):
            return {"acao": "regra", "motivo": motivo}
    return {"acao": "ignorar", "motivo": "Não parece mudar placar, dano, cartas jogadas nem o fim da partida."}


def pendentes():
    """Modelos de linhas não lidas em todas as partidas, do mais frequente para o menos."""
    grupos = {}
    for p in banco.listar_partidas():
        completa = banco.obter_partida(p["id"])
        if not completa["nao_lidas"]:
            continue
        conhecidas = {e["carta"] for e in completa["eventos"] if e["carta"]} | \
                     {e["alvo"] for e in completa["eventos"] if e["alvo"]}
        for cs in (completa["resumo"].get("vistas") or {}).values():
            conhecidas |= set(cs)
        for l in completa["nao_lidas"]:
            mod = modelo_da_linha(l["texto"], completa["jogadores"], conhecidas)
            g = grupos.setdefault(mod, {"modelo": mod, "vezes": 0, "partidas": set(), "exemplos": []})
            g["vezes"] += 1
            g["partidas"].add(p["id"])
            if len(g["exemplos"]) < 3:
                g["exemplos"].append({"partida": p["id"], "linha": l["linha"], "texto": l["texto"]})
    saida = []
    for g in sorted(grupos.values(), key=lambda x: -x["vezes"]):
        g["partidas"] = sorted(g["partidas"])
        g["regex"] = regex_do_modelo(g["modelo"])
        g["sugestao"] = sugestao(g["modelo"])
        saida.append(g)
    return saida


def adicionar_regra(id_, tipo, padrao, exemplos=()):
    """Valida e grava uma regra nova em dados/regras.json; relê todas as partidas."""
    if tipo not in leitor.TIPOS:
        raise ValueError("Tipo de regra desconhecido.")
    try:
        rx = re.compile(leitor._python_regex(padrao))
    except re.error as e:
        raise ValueError(f"A expressão regular tem um erro: {e}")
    falham = [x for x in exemplos if not rx.search(leitor.limpar_linha(x))]
    if falham:
        raise ValueError("A regra não lê esta linha de exemplo: " + falham[0])
    regras = config.ler_regras()
    base = re.sub(r"[^a-z0-9_]", "_", (id_ or tipo).lower()) or tipo
    novo_id, n = base, 2
    while any(r["id"] == novo_id for r in regras):
        novo_id, n = f"{base}_{n}", n + 1
    nova = {"id": novo_id, "tipo": tipo, "ativa": True, "re": padrao}
    # Regras de ignorar ficam no fim; regras de leitura entram antes delas.
    if tipo == "ignorar":
        regras.append(nova)
    else:
        pos = next((i for i, r in enumerate(regras) if r["tipo"] == "ignorar"), len(regras))
        regras.insert(pos, nova)
    config.salvar_regras(regras)
    relidas = banco.reprocessar_partidas(regras)
    return {"id": novo_id, "relidas": relidas}
