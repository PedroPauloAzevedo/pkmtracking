"""
EXPERIMENTO 4: quanto tempo cada análise leva com muitos dados.

Mede as funções por trás das telas mais usadas. Para simular um ano de uso, pode multiplicar as
suas partidas (cópias com textos levemente diferentes) num banco de teste: NUNCA rode no banco real.
Uso:  python testes/experimentos/e4_desempenho.py <pasta do programa com dados de TESTE> [partidas_extras]
"""
import sys
import time

sys.path.insert(0, sys.argv[1])
from tracker import analises, banco, config, decks  # noqa: E402

extras = int(sys.argv[2]) if len(sys.argv) > 2 else 0
if extras:
    base = banco.consultar("SELECT texto FROM partidas WHERE COALESCE(dono,'')='' LIMIT 20")
    regras = config.ler_regras()
    for i in range(extras):
        t = base[i % len(base)]["texto"] + f"\n\n{'' if i % 2 else ' '}{i}"  # muda o texto: não é repetida
        banco.inserir_partida(t, "teste", regras)
total = banco.consultar("SELECT COUNT(*) AS n FROM partidas")[0]["n"]
tor = banco.consultar("SELECT COUNT(*) AS n, SUM(fonte='online') AS on_ FROM torneios")[0]
print(f"Banco: {total} partidas suas/amigos; {tor['n']} torneios ({tor['on_']} online); "
      f"{banco.consultar('SELECT COUNT(*) AS n FROM t_partidas')[0]['n']} mesas; "
      f"{banco.consultar('SELECT COUNT(*) AS n FROM t_listas')[0]['n']} linhas de listas\n")

nick = config.ler_config()["nick"]
todos = analises.torneios_da_fonte("todos")
arq = (analises.meta(todos)["divisao"] or [{"arquetipo": ""}])[0]["arquetipo"]


def medir(nome, f, vezes=3):
    tempos = []
    for _ in range(vezes):
        t0 = time.perf_counter()
        f()
        tempos.append(time.perf_counter() - t0)
    print(f"{nome:46} {1000 * min(tempos):9.0f} ms")
    return min(tempos)


medir("listar_partidas (lê e decodifica todas)", banco.listar_partidas)
medir("analise_pessoal (Início/Partidas/Desempenho)", lambda: analises.analise_pessoal(nick))
medir("decisoes (tela Decisões)", lambda: analises.decisoes(nick), 1)
medir("meta - grandes eventos", lambda: analises.meta(analises.torneios_da_fonte("grandes")))
medir("meta - todos (com online)", lambda: analises.meta(todos))
medir("perfil de deck (todos)", lambda: analises.perfil(arq, todos))
medir("uso de cartas (todos)", lambda: analises.cartas(todos))
medir("tendência (todos)", lambda: analises.tendencia(8, todos))
medir("identificar deck de 1 partida", lambda: decks.identificar({"Dreepy": 1, "Drakloak": 1, "Dragapult ex": 1}))
qtd_decks = len(decks.listar_decks())
medir(f"/api/decks ({qtd_decks} decks: 1 análise por deck)",
      lambda: [analises.analise_pessoal(nick, lista=d["id"]) for d in decks.listar_decks()], 1)
