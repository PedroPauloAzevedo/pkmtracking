"""
EXPERIMENTO 6: a nova versão de "Uso de cartas" dá exatamente o mesmo resultado que a anterior?

Roda as duas versões (analises._uso_cartas e analises._uso_cartas_lento) com os mesmos dados,
em três recortes, e compara item por item e o tempo.
Uso:  python testes/experimentos/e6_uso_cartas.py <pasta do programa com dados>
"""
import sys
import time

sys.path.insert(0, sys.argv[1])
from tracker import analises, banco  # noqa: E402


def dados(torneios, arq=None):
    f, params = analises._filtro_torneios(torneios)
    sql = (f"SELECT l.torneio, l.labs_id, l.carta, l.qtd, l.carta_id, l.carta_base FROM t_listas l JOIN t_jogadores j "
           f"ON j.torneio=l.torneio AND j.labs_id=l.labs_id WHERE 1=1 {f.replace('torneio', 'l.torneio')}")
    if arq:
        sql += " AND j.arquetipo=?"
        params = params + (arq,)
    return banco.consultar(sql, params), {(j["torneio"], j["labs_id"]): j for j in analises._jogadores(torneios)}


todos = analises.torneios_da_fonte("todos")
arq = analises.meta(todos)["divisao"][0]["arquetipo"]
iguais = True
for nome, (ls, js) in (("todos os torneios", dados(todos)), ("grandes eventos", dados(analises.torneios_da_fonte("grandes"))),
                       (f"só {arq}", dados(todos, arq))):
    t0 = time.perf_counter(); novo = analises._uso_cartas(ls, js); t1 = time.perf_counter()
    velho = analises._uso_cartas_lento(ls, js); t2 = time.perf_counter()
    igual = novo == velho
    iguais &= igual
    print(f"{nome:22} {len(ls):7} linhas | nova {1000 * (t1 - t0):7.0f} ms | anterior {1000 * (t2 - t1):8.0f} ms | "
          f"{(t2 - t1) / max(t1 - t0, 1e-9):5.0f}x mais rápida | resultado {'IDÊNTICO' if igual else 'DIFERENTE'}")
print("APROVADO" if iguais else "REPROVADO")
