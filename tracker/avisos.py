"""
AVISOS: recados curtos para a pessoa, mostrados fora do painel.

Quem quer mostrar (o ícone perto do relógio, como notificação do Windows) se inscreve em
`ouvintes`. O painel também mostra o último aviso (ver /api/status).
"""
import itertools
import time

ouvintes = []   # funções que recebem o texto do aviso
ultimos = []    # os últimos avisos, para o painel: {"id", "quando", "texto"}
_ids = itertools.count(1)


def avisar(texto):
    ultimos.append({"id": next(_ids), "quando": time.strftime("%H:%M:%S"), "texto": texto})
    del ultimos[:-10]
    print("[aviso]", texto)
    for f in list(ouvintes):
        try:
            f(texto)
        except Exception:
            pass


def ultimo():
    return ultimos[-1] if ultimos else None
