"""
EXPERIMENTO 7: quanto tempo leva gravar uma partida conforme o banco cresce.

Grava lotes de partidas (cópias levemente alteradas das suas) e mede o tempo médio de cada
gravação em cada tamanho de banco. Rode só numa cópia de teste: ele acrescenta partidas ao banco.
Uso:  python testes/experimentos/e7_inserir.py <pasta do programa com dados de TESTE> [lotes]
"""
import sys
import time

sys.path.insert(0, sys.argv[1])
from tracker import banco, config  # noqa: E402

lotes = int(sys.argv[2]) if len(sys.argv) > 2 else 4
base = [r["texto"] for r in banco.consultar("SELECT texto FROM partidas WHERE COALESCE(dono,'')='' LIMIT 20")]
regras = config.ler_regras()
n = 0
for lote in range(lotes):
    tamanho = banco.consultar("SELECT COUNT(*) AS q FROM partidas")[0]["q"]
    t0 = time.perf_counter()
    for i in range(100):
        banco.inserir_partida(base[n % len(base)] + f"\n\n{n}-{time.time()}", "teste", regras)
        n += 1
    print(f"banco com {tamanho:5} partidas: {1000 * (time.perf_counter() - t0) / 100:7.1f} ms por partida gravada", flush=True)
