"""
EXPERIMENTO 8: as análises pessoais ficaram mais rápidas sem mudar o resultado?

Compara a versão do programa em <pasta antiga> com a de <pasta nova>, usando o MESMO banco:
roda analise_pessoal e decisoes nas duas, mede o tempo e confere se os resultados são idênticos.
Também confere identificar_nb (com índice) contra _identificar_nb_direto (sem índice) em todas as partidas.
Uso:  python testes/experimentos/e8_analise_rapida.py <pasta antiga> <pasta nova>
"""
import json
import subprocess
import sys

CODIGO = r'''
import json, sys, time
sys.path.insert(0, sys.argv[1])
from tracker import analises, config
nick = config.ler_config()["nick"]
saida = {}
for nome, f in (("analise_pessoal", lambda: analises.analise_pessoal(nick)), ("decisoes", lambda: analises.decisoes(nick)),
                ("todos os jogadores", lambda: analises.analise_pessoal(nick, jogador="*"))):
    t0 = time.perf_counter(); r1 = f(); t1 = time.perf_counter(); r2 = f(); t2 = time.perf_counter()
    saida[nome] = {"primeira": t1 - t0, "segunda": t2 - t1, "resultado": json.dumps(r1, sort_keys=True, default=str)}
print(json.dumps(saida))
'''
res = {}
for rotulo, pasta in (("antes", sys.argv[1]), ("agora", sys.argv[2])):
    out = subprocess.run([sys.executable, "-c", CODIGO, pasta], capture_output=True, text=True, encoding="utf-8", cwd=pasta).stdout
    res[rotulo] = json.loads(out.strip().splitlines()[-1])
print(f"{'análise':22} | {'antes (1ª / 2ª vez)':>22} | {'agora (1ª / 2ª vez)':>22} | resultado")
for nome in res["antes"]:
    a, b = res["antes"][nome], res["agora"][nome]
    print(f"{nome:22} | {a['primeira']:9.2f} s / {a['segunda']:5.2f} s | {b['primeira']:9.2f} s / {b['segunda']:5.2f} s | "
          f"{'IDÊNTICO' if a['resultado'] == b['resultado'] else 'DIFERENTE'}")

sys.path.insert(0, sys.argv[2])
from tracker import banco, cartas, decks  # noqa: E402
from tracker.leitor import normalizar_nome_carta  # noqa: E402
dif = n = 0
for p in banco.listar_partidas():
    for j in p["jogadores"]:
        r = {normalizar_nome_carta(c) for c in (p["resumo"].get("vistas") or {}).get(j, {}) if not cartas.eh_energia_basica(c)}
        if not r:
            continue
        a, b = decks.identificar_nb(r), decks._identificar_nb_direto(r)
        n += 1
        dif += a[0] != b[0] or abs(a[1] - b[1]) > 1e-9
print(f"identificar_nb com índice x direto: {n - dif} de {n} iguais")
