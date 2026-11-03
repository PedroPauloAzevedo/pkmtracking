"""
TESTE DO REPLAY: logs curtos, no formato do TCG Live, com cada armadilha que o replay já errou.
Cada cenário confere o dano de cada Pokémon e quem foi nocauteado no fim (ou num ponto do log).

Uso: python -I testes/teste_replay.py <pasta do programa>   ->  termina com "OK"
Não precisa de internet nem da biblioteca de cartas (os PS vêm de um índice falso, montado aqui).
"""
import sys
from pathlib import Path

RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ))

from tracker import cartas, config, replay  # noqa: E402

# Índice de cartas falso: só nome, PS e golpes (o suficiente para o replay e para _ps_minimo).
PS = {
    "Budew": [(30, "itchy pollen")], "Dusclops": [(90, "cursed blast")], "Dunsparce": [(60, "ram"), (70, "gnaw")],
    "Dragapult ex": [(320, "phantom dive")], "Munkidori": [(110, "adrena-brain")], "Dhelmise": [(140, "vengeful anchor"), (120, "earthen power")],
    "Mega Lopunny ex": [(330, "gale thrust")], "Hydrapple ex": [(330, "ripening charge")], "Buneary": [(70, "")],
    "Slowking": [(120, "seek inspiration")], "Meowth ex": [(170, "last-ditch catch")], "Dreepy": [(70, "")],
}
_ind = {"cartas": {}, "por_codigo": {}, "basica": {}, "por_nome": {}, "grupos": {}}
for nome, versoes in PS.items():
    for i, (ps, golpe) in enumerate(versoes):
        chave = f"{nome.lower()}|{ps}||{golpe}"
        id_ = f"t-{nome}-{i}"
        _ind["cartas"][id_] = {"id": id_, "nome": nome, "chave": chave, "ps": ps, "categoria": "Pokemon", "tipos": [], "estagio": "Basic"}
        _ind["basica"][chave] = id_
        _ind["por_nome"].setdefault(cartas.normalizar(nome), []).append(chave)
cartas.indice = lambda: _ind
cartas.legal_chave = lambda chave: True

CABECALHO = """Setup
Ana chose heads for the opening coin flip.
Ana won the coin toss.
Ana decided to go first.
Ana drew 7 cards for the opening hand.
- 7 drawn cards.
Bia drew 7 cards for the opening hand.
- 7 drawn cards.
"""
# o leitor descobre os jogadores pelos cabeçalhos "Fulano's Turn": um turno vazio de cada um no fim
FIM = "\nAna's Turn\nAna ended their turn.\n\nBia's Turn\nBia ended their turn.\n"


def mesa(log, ate=None):
    """Monta o replay e devolve {jogador: {"pokemon": [(nome, dano)], "ko": [nomes]}} no fim (ou na linha `ate`)."""
    texto = CABECALHO + log.strip("\n") + "\n" + FIM
    r = replay.gerar(texto, config.ler_regras())
    q = r["quadros"][-1]
    if ate:
        q = [x for x in r["quadros"] if ate in x["texto"]][-1]
    saida = {}
    for j, m in q["estado"]["mesa"].items():
        ps = ([m["ativo"]] if m["ativo"] else []) + m["banco"]
        saida[j] = {"pokemon": [(p["nome"], p["dano"]) for p in ps], "ko": list(m["nocauteados"])}
    return saida


def confere(nome, obtido, esperado):
    if obtido != esperado:
        print(f"FALHOU: {nome}\n  esperado: {esperado}\n  obtido:   {obtido}")
        sys.exit(1)
    print(f"ok  {nome}")


# 1) Cursed Blast: o jogo escreve "Ana put ... on Ana's Budew", mas o Budew nocauteado é da Bia.
m = mesa("""
Ana played Budew to the Active Spot.
Bia played Budew to the Active Spot.

Ana's Turn
Ana played Dusclops to the Bench.
Ana's Dusclops used Cursed Blast.
- Ana put 5 damage counters on Ana's Budew.
Bia's Budew was Knocked Out!
Ana's Dusclops was Knocked Out!
""")
confere("Cursed Blast: dano no Budew do adversário", (m["Ana"]["pokemon"], m["Bia"]["ko"]), ([("Budew", 0)], ["Budew"]))

# 2) Phantom Dive sem nocaute: contadores no Banco do ADVERSÁRIO (os dois têm Dunsparce).
#    E o Risky Ruins: contadores no Básico do próprio jogador (o que está escrito vale).
m = mesa("""
Ana played Dragapult ex to the Active Spot.
Bia played Budew to the Active Spot.

Ana's Turn
Ana played Dunsparce to the Bench.
Risky Ruins was activated.
- Ana put 2 damage counters on Ana's Dunsparce.
Bia played Dunsparce to the Bench.
Ana's Dragapult ex used Phantom Dive on Bia's Budew for 10 damage.
- Ana put 3 damage counters on Ana's Dunsparce.
""")
confere("Phantom Dive no Banco do adversário + Risky Ruins no próprio",
        (m["Ana"]["pokemon"], m["Bia"]["pokemon"]), ([("Dragapult ex", 0), ("Dunsparce", 20)], [("Budew", 10), ("Dunsparce", 30)]))

# 3) "put a damage counter" = 1 contador.
m = mesa("""
Ana played Dragapult ex to the Active Spot.
Bia played Budew to the Active Spot.
Bia played Meowth ex to the Bench.

Ana's Turn
Ana's Dragapult ex used Phantom Dive on Bia's Budew for 10 damage.
- Ana put a damage counter on Ana's Meowth ex.
""")
confere("um contador só ('a damage counter')", m["Bia"]["pokemon"], [("Budew", 10), ("Meowth ex", 10)])

# 4) Munkidori (Adrena-Brain): tira do próprio e põe no do adversário (o jogo escreve o dono errado no alvo).
m = mesa("""
Ana played Munkidori to the Active Spot.
Bia played Budew to the Active Spot.

Ana's Turn
Ana played Budew to the Bench.
Bia's Budew used Itchy Pollen on Ana's Munkidori for 30 damage.
Ana's Munkidori used Adrena-Brain.
- Ana moved 3 damage counters from Ana's Munkidori to Ana's Budew.
""", ate="moved 3 damage counters")
confere("Adrena-Brain move contadores para o adversário", (m["Ana"]["pokemon"], m["Bia"]["pokemon"]),
        ([("Munkidori", 0), ("Budew", 0)], [("Budew", 30)]))

# 5) Cura no formato "Bia's Hydrapple ex healed 30 damage."
m = mesa("""
Ana played Dragapult ex to the Active Spot.
Bia played Hydrapple ex to the Active Spot.

Ana's Turn
Ana's Dragapult ex used Phantom Dive on Bia's Hydrapple ex for 200 damage.

Bia's Turn
Bia's Hydrapple ex used Ripening Charge.
- Bia's Hydrapple ex healed 30 damage.
""")
confere("cura 'healed N damage' sem 'from'", m["Bia"]["pokemon"], [("Hydrapple ex", 170)])

# 6) Dois Pokémon de mesmo nome: Phantom Dive acerta o Ativo e os contadores extras vão para o do Banco;
#    no nocaute, cai o que tem mais dano (o do Banco), não o Ativo.
golpe = """
Ana's Turn
Ana's Dragapult ex used Phantom Dive on Bia's Mega Lopunny ex for 10 damage.
- Ana put 6 damage counters on Ana's Mega Lopunny ex.
"""
m = mesa("""
Ana played Dragapult ex to the Active Spot.
Bia played Mega Lopunny ex to the Active Spot.
Bia played Mega Lopunny ex to the Bench.
""" + golpe * 6 + """Bia's Mega Lopunny ex was Knocked Out!
""")  # Ativo com 60 de dano, Banco com 360 (>= 330 PS): cai o do Banco
confere("mesmo nome: contadores no Banco e nocaute do mais danificado", (m["Bia"]["pokemon"], m["Bia"]["ko"]),
        ([("Mega Lopunny ex", 60)], ["Mega Lopunny ex"]))

# 7) Contador ambíguo corrigido pelo nocaute: Munkidori move 30 "para Dhelmise" (são dois); depois o do Banco
#    cai com 110 de dano num Dhelmise de 140 PS (Vengeful Anchor) -> os 30 eram dele.
m = mesa("""
Ana played Munkidori to the Active Spot.
Bia played Dhelmise to the Active Spot.
Bia played Dhelmise to the Bench.

Bia's Turn
Bia's Dhelmise used Vengeful Anchor on Ana's Munkidori for 30 damage.

Ana's Turn
Ana's Munkidori used Adrena-Brain.
- Ana moved 3 damage counters from Ana's Munkidori to Ana's Dhelmise.
Ana played Dragapult ex to the Bench.
Ana's Dragapult ex used Phantom Dive on Bia's Dhelmise for 200 damage.
- Ana put 6 damage counters on Ana's Dhelmise.
- Ana put 5 damage counters on Ana's Dhelmise.
Bia's Dhelmise was Knocked Out!
Bia's Dhelmise was Knocked Out!
""", ate="put 5 damage counters")
confere("contador ambíguo corrigido pelo nocaute (Dhelmise)", m["Bia"]["pokemon"], [("Dhelmise", 200), ("Dhelmise", 140)])

# 8) Night Stretcher pega do descarte: o Meowth ex em jogo continua na mesa.
m = mesa("""
Ana played Budew to the Active Spot.
Bia played Budew to the Active Spot.
Bia played Meowth ex to the Bench.

Bia's Turn
Bia played Night Stretcher.
- Bia moved Bia's Meowth ex to their hand.
""")
confere("Night Stretcher não tira o Pokémon da mesa", m["Bia"]["pokemon"], [("Budew", 0), ("Meowth ex", 0)])

# 9) "took N damage" e o mesmo golpe acertando dois de mesmo nome (Trifrost copiado pelo Slowking).
m = mesa("""
Ana played Slowking to the Active Spot.
Bia played Budew to the Active Spot.
Bia played Buneary to the Bench.
Bia played Buneary to the Bench.

Ana's Turn
Ana's Slowking used Seek Inspiration.
- Bia's Buneary took 30 damage.
- Bia's Buneary took 30 damage.
""")
confere("'took N damage' em dois Pokémon de mesmo nome", m["Bia"]["pokemon"], [("Budew", 0), ("Buneary", 30), ("Buneary", 30)])

# 10) Versão da carta pelos PS: Dunsparce nocauteado com 60 de dano é o de 60 PS (não o de 70).
from tracker import decks  # noqa: E402
texto = CABECALHO + """Ana played Dragapult ex to the Active Spot.
Bia played Budew to the Active Spot.
Bia played Dunsparce to the Bench.

Ana's Turn
Ana's Dragapult ex used Phantom Dive on Bia's Budew for 10 damage.
- Ana put 6 damage counters on Ana's Dunsparce.
Bia's Dunsparce was Knocked Out!
""" + FIM
lim =decks._limites_ps(replay.gerar(texto, config.ler_regras())["quadros"])
ok = [k for k in _ind["por_nome"]["dunsparce"] if decks._ps_compativel(k, *lim[("Bia", "Dunsparce")])]
confere("versão pelo nocaute: Dunsparce de 60 PS", ok, ["dunsparce|60||ram"])


# 11) MÃOS. Ana exportou o log (vê o nome do que compra); da Bia só aparece o que ela busca no baralho.
def maos(log, ate=None, cabecalho=None):
    """{jogador: [nome ou "?"]} no fim do log (ou na última linha que contém `ate`)."""
    texto = (cabecalho or CABECALHO_ANA) + log.strip("\n") + "\n" + FIM
    r = replay.gerar(texto, config.ler_regras())
    q = [x for x in r["quadros"] if ate in x["texto"]][-1] if ate else r["quadros"][-1]
    return {j: sorted(c["nome"] or "?" for c in m) for j, m in q["estado"]["maos"].items()}, r


CABECALHO_ANA = """Setup
Ana chose heads for the opening coin flip.
Ana won the coin toss.
Ana decided to go first.
Ana drew 7 cards for the opening hand.
- 7 drawn cards.
   • Budew, Dunsparce, Judge, Poké Pad, Basic Psychic Energy, Ultra Ball, Buneary
Bia drew 7 cards for the opening hand.
- 7 drawn cards.
Ana played Budew to the Active Spot.
Bia played Dreepy to the Active Spot.
"""
m, _ = maos("""
Ana's Turn
Ana drew Munkidori.
Ana played Poké Pad.
- Ana drew Dreepy.
- Ana shuffled their deck.
Ana attached Basic Psychic Energy to Budew in the Active Spot.
Ana ended their turn.

Bia's Turn
Bia drew a card.
Bia played Buddy-Buddy Poffin.
- Bia drew Dreepy and played it to the Bench.
Bia played Ultra Ball.
- Bia discarded 2 cards.
   • Basic Fire Energy, Night Stretcher
- Bia drew Dragapult ex.
- Bia shuffled their deck.
""", ate="Bia drew Dragapult ex")
confere("mão: compras com nome (Ana) e busca à vista (Bia)", m,
        {"Ana": ["Buneary", "Dreepy", "Dunsparce", "Judge", "Munkidori", "Ultra Ball"], "Bia": ["?", "?", "?", "Dragapult ex"]})

m, _ = maos("""
Ana's Turn
Ana drew Munkidori.
Ana played Judge.
- Ana shuffled 6 cards into their deck.
   • Dunsparce, Poké Pad, Basic Psychic Energy, Ultra Ball, Buneary, Munkidori
- Bia shuffled 7 cards into their deck.
- Ana drew 4 cards.
   • Crispin, Dreepy, Dreepy, Boss's Orders
- Bia drew 4 cards.
""")
confere("mão: Judge embaralha as duas mãos e cada um compra 4", m,
        {"Ana": ["Boss's Orders", "Crispin", "Dreepy", "Dreepy"], "Bia": ["?", "?", "?", "?"]})

# Mulligan de quem exportou: a nova mão não aparece no log; a carta jogada depois é revelada desde o começo.
m, r = maos("""
Ana's Turn
Ana drew Crispin.
Ana played Ultra Ball.
- Ana discarded 2 cards.
   • Crispin, Judge
- Ana drew Munkidori.
""", cabecalho="""Setup
Ana chose heads for the opening coin flip.
Ana won the coin toss.
Ana decided to go first.
Ana drew 7 cards for the opening hand.
- 7 drawn cards.
   • Judge, Poké Pad, Ultra Ball, Crispin, Boss's Orders, Night Stretcher, Rare Candy
Bia drew 7 cards for the opening hand.
- 7 drawn cards.
Ana took a mulligan.
- Cards revealed from Mulligan 1
   • Judge, Poké Pad, Ultra Ball, Crispin, Boss's Orders, Night Stretcher, Rare Candy
Ana played Budew to the Active Spot.
Bia played Dreepy to the Active Spot.
""")
inicio = [q for q in r["quadros"] if q["texto"] == "Ana played Budew to the Active Spot."][0]["estado"]["maos"]["Ana"]
confere("mão: depois do mulligan, Ultra Ball e Judge aparecem desde o começo (descobertas)",
        sorted((c["nome"] or "?", bool(c.get("inferida"))) for c in inicio),
        [("?", False), ("?", False), ("?", False), ("?", False), ("Judge", True), ("Ultra Ball", True)])
confere("mão: no fim, só a compra e a carta buscada", m["Ana"], ["?", "?", "?", "?", "Munkidori"])

m, _ = maos("""
Ana's Turn
Ana drew Munkidori.
Ana played Lillie's Determination.
- Ana shuffled Munkidori into their deck.
- Ana drew 6 cards.
   • Crispin, Dreepy, Dreepy, Boss's Orders, Rare Candy, Judge
""", cabecalho=CABECALHO_ANA.replace("Budew, Dunsparce, Judge, Poké Pad, Basic Psychic Energy, Ultra Ball, Buneary",
                                      "Budew, Lillie's Determination, Ultra Ball, Ultra Ball, Ultra Ball, Ultra Ball, Ultra Ball")
                            .replace("Ana played Budew to the Active Spot.", "Ana played Budew to the Active Spot.\nAna played Ultra Ball.\n"
                                     "Ana played Ultra Ball.\nAna played Ultra Ball.\nAna played Ultra Ball.\nAna played Ultra Ball."))
confere("mão: 'shuffled <carta> into their deck' (uma carta, com nome)", m["Ana"],
        ["Boss's Orders", "Crispin", "Dreepy", "Dreepy", "Judge", "Rare Candy"])

m, _ = maos("""
Ana's Turn
Ana drew Munkidori.
Ana played Academy at Night to the Stadium spot.
Ana played Academy at Night.
- Ana put a card on top of their deck.
Ana played Slowking to the Bench.
Ana's Slowking used Seek Inspiration.
- Ana discarded Munkidori.
""", cabecalho=CABECALHO_ANA.replace("Judge, Poké Pad", "Academy at Night, Slowking"))
# 7 - Budew + Munkidori - Academy (jogada) - carta no topo - Slowking = 4; usar o Estádio e o Seek Inspiration não tiram nada
confere("mão: usar o Estádio e o Seek Inspiration (descarta do baralho) não tiram carta a mais", len(m["Ana"]), 4)

print("OK")
