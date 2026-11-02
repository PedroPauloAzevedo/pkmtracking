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

print("OK")
