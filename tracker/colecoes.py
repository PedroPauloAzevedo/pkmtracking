"""
COLEÇÕES E ÉPOCAS DO META: quando cada coleção do Standard chegou, para separar as análises por época.

Cada coleção nova pode mudar o meta. Uma "época" vai da chegada de uma coleção até a chegada da seguinte; a mais
recente é a época atual. A chegada depende do que se analisa:
  - TCG Live (as suas partidas e as dos amigos): o jogo libera a coleção UM DIA ANTES do lançamento nas lojas dos
    EUA, às 10h do horário do Pacífico (visto nas coleções recentes: Chaos Rising em 21/05/2026, Pitch Black em
    16/07/2026, 30th Celebration em 15/09/2026, Delta Reign em 05/11/2026). A hora conta: em 05/11/2026 a Delta Reign
    saiu às 15h de Brasília, e as partidas daquela manhã ainda são da época anterior. A hora é convertida para o
    relógio deste computador (as partidas são gravadas com ele);
  - torneios (grandes eventos): a coleção passa a valer na SEGUNDA SEXTA-FEIRA depois do lançamento nos EUA (regra da
    Play! Pokémon, em docs/regras-standard.md; ex.: Delta Reign lança em 06/11/2026 e vale em 20/11/2026). Aqui conta o dia;
  - online (torneios do play.limitlesstcg.com, jogados no TCG Live): os organizadores liberam a coleção assim que ela chega
    ao jogo (em 11/2026 vários torneios de 06/11 já se chamavam "DELTA REIGN LEGAL", e o deck mais jogado era da coleção
    nova). A época começa no dia do lançamento nos EUA: é o dia, em UTC (a data que o Limitless dá aos torneios), em que a
    coleção chegou ao TCG Live (17h ou 18h UTC). Torneios desse dia que começaram antes da chegada são raros e ficam na
    época nova (D-048).
Coleções lançadas no mesmo dia (Black Bolt e White Flare) formam uma época só.

De onde vêm as coleções:
  1. COLECOES, a tabela abaixo, revisada a cada versão do programa (inclui coleção que ainda não chegou à biblioteca
     de cartas, como a Delta Reign no dia em que saiu no TCG Live);
  2. a biblioteca de cartas (TCGdex): coleção das séries do Standard lançada depois da última da tabela entra
     sozinha, com a data de lançamento que o TCGdex informa. Promos, Energias e coleções com menos de 60 cartas
     ficam de fora (não mudam o meta).
"""
import json
import re
from datetime import date, datetime, timedelta, timezone

# (id no TCGdex, nome, lançamento nas lojas dos EUA). Coleções do Standard atual, da mais antiga para a mais nova.
COLECOES = [
    ("sv01", "Scarlet & Violet", "2023-03-31"),
    ("sv02", "Paldea Evolved", "2023-06-09"),
    ("sv03", "Obsidian Flames", "2023-08-11"),
    ("sv03.5", "151", "2023-09-22"),
    ("sv04", "Paradox Rift", "2023-11-03"),
    ("sv04.5", "Paldean Fates", "2024-01-26"),
    ("sv05", "Temporal Forces", "2024-03-22"),
    ("sv06", "Twilight Masquerade", "2024-05-24"),
    ("sv06.5", "Shrouded Fable", "2024-08-02"),
    ("sv07", "Stellar Crown", "2024-09-13"),
    ("sv08", "Surging Sparks", "2024-11-08"),
    ("sv08.5", "Prismatic Evolutions", "2025-01-17"),
    ("sv09", "Journey Together", "2025-03-28"),
    ("sv10", "Destined Rivals", "2025-05-30"),
    ("sv10.5b", "Black Bolt", "2025-07-17"),
    ("sv10.5w", "White Flare", "2025-07-17"),
    ("me01", "Mega Evolution", "2025-09-26"),
    ("me02", "Phantasmal Flames", "2025-11-14"),
    ("me02.5", "Ascended Heroes", "2026-01-30"),
    ("me03", "Perfect Order", "2026-03-27"),
    ("me04", "Chaos Rising", "2026-05-22"),
    ("me05", "Pitch Black", "2026-07-17"),
    ("30th", "30th Celebration", "2026-09-16"),
    ("me06", "Delta Reign", "2026-11-06"),
]
MINIMO_CARTAS = 60
FORA = re.compile(r"promo|energy|classic|my first battle", re.I)
HORA_LIVE = 10  # o TCG Live libera a coleção às 10h da manhã no horário do Pacífico (EUA)


def _fuso_pacifico(d):
    """Horas do horário do Pacífico em relação ao UTC naquele dia: -7 no horário de verão dos EUA (do 2º domingo de
    março ao 1º domingo de novembro) e -8 no resto do ano."""
    def domingo(mes, n):  # n-ésimo domingo do mês
        d1 = date(d.year, mes, 1)
        return d1 + timedelta(days=(6 - d1.weekday()) % 7 + 7 * (n - 1))
    return -7 if domingo(3, 2) <= d < domingo(11, 1) else -8


def chegada_live(lancamento):
    """Quando a coleção chega ao TCG Live, no relógio deste computador (AAAA-MM-DDTHH:MM:SS): a véspera do lançamento
    nas lojas dos EUA, às 10h do Pacífico (ex.: Delta Reign, lançada em 06/11/2026: 05/11/2026 às 15h em Brasília)."""
    d = date.fromisoformat(lancamento) - timedelta(days=1)
    utc = datetime(d.year, d.month, d.day, HORA_LIVE, tzinfo=timezone.utc) - timedelta(hours=_fuso_pacifico(d))
    return datetime.fromtimestamp(utc.timestamp()).isoformat(timespec="seconds")


def validade_torneio(lancamento):
    """Dia em que a coleção passa a valer em torneio: a segunda sexta-feira depois do lançamento nos EUA."""
    d = date.fromisoformat(lancamento)
    ate_sexta = (4 - d.weekday()) % 7 or 7  # sexta-feira = 4; lançada numa sexta, a primeira "depois" é a seguinte
    return (d + timedelta(days=ate_sexta + 7)).isoformat()


def inicio_online(lancamento):
    """Dia em que a coleção passa a contar nos torneios online: o próprio dia do lançamento (ver o topo do arquivo)."""
    return date.fromisoformat(lancamento).isoformat()


INICIO = {"live": chegada_live, "torneios": validade_torneio, "online": inicio_online}


def _da_biblioteca():
    """Coleções da biblioteca de cartas (TCGdex) que podem mudar o meta: [(id, nome, lançamento)]."""
    from . import cartas
    saida = []
    for arq in sorted(cartas.PASTA_SETS.glob("*.json")) if cartas.PASTA_SETS.exists() else []:
        try:
            s = json.loads(arq.read_text(encoding="utf-8"))["set"]
        except (OSError, ValueError, KeyError):
            continue
        total = (s.get("cardCount") or {}).get("total") or (s.get("cardCount") or {}).get("official") or 0
        if s.get("releaseDate") and total >= MINIMO_CARTAS and not FORA.search(s.get("name") or ""):
            saida.append((s["id"], s.get("name") or s["id"], s["releaseDate"][:10]))
    return saida


def colecoes():
    """Coleções que abrem uma época: as da tabela e as da biblioteca lançadas depois da última da tabela.
    [{"ids", "nome", "lancamento"}], da mais antiga para a mais nova; as lançadas no mesmo dia viram uma só."""
    lista = list(COLECOES)
    conhecidas = {c[0] for c in lista}
    ultima = max(c[2] for c in lista)
    lista += [c for c in _da_biblioteca() if c[0] not in conhecidas and c[2] > ultima]
    por_dia = {}
    for id_, nome, lanc in sorted(lista, key=lambda c: (c[2], c[0])):
        g = por_dia.setdefault(lanc, {"ids": [], "nomes": [], "lancamento": lanc})
        g["ids"].append(id_)
        g["nomes"].append(nome)
    return [{"ids": g["ids"], "nome": " e ".join(g["nomes"]), "lancamento": g["lancamento"]} for g in por_dia.values()]


def epocas(tipo="live", agora=None):
    """Épocas do meta, da mais recente para a mais antiga, só as que já começaram.
    tipo: "live" (chegada ao TCG Live, para as suas partidas; com hora), "torneios" (validade nos grandes eventos; dia) ou
    "online" (torneios online: o dia do lançamento).
    Cada uma: {"id", "nome", "lancamento", "de", "fim", "ate"}:
      de  = começo (incluído);  fim = começo da época seguinte (não incluído); None na época atual;
      ate = último dia da época, para mostrar (no TCG Live é o dia em que a seguinte chegou, que fica dividido).
    agora: AAAA-MM-DD[THH:MM:SS] (para testes); sem ele, o relógio do computador."""
    agora = agora or datetime.now().isoformat(timespec="seconds")
    inicio = INICIO[tipo]
    todas = sorted(({"id": c["ids"][0], "nome": c["nome"], "lancamento": c["lancamento"], "de": inicio(c["lancamento"])}
                    for c in colecoes()), key=lambda e: e["de"])
    comecadas = [e for e in todas if e["de"] <= agora]
    for e, seguinte in zip(comecadas, comecadas[1:] + [None]):
        e["fim"] = seguinte["de"] if seguinte else None  # a época atual vai até agora (a próxima ainda não começou)
        if not seguinte:
            e["ate"] = None
        elif tipo == "live":
            e["ate"] = seguinte["de"][:10]
        else:
            e["ate"] = (date.fromisoformat(seguinte["de"]) - timedelta(days=1)).isoformat()
    return list(reversed(comecadas))


def proxima(tipo="live", agora=None):
    """A próxima época, se já se sabe a data e ela ainda não começou (ex.: Delta Reign nos torneios até 20/11/2026)."""
    agora = agora or datetime.now().isoformat(timespec="seconds")
    inicio = INICIO[tipo]
    futuras = sorted((inicio(c["lancamento"]), c["nome"]) for c in colecoes() if inicio(c["lancamento"]) > agora)
    return {"nome": futuras[0][1], "de": futuras[0][0]} if futuras else None


def epoca_de(data, tipo="live", agora=None):
    """Época de um momento (AAAA-MM-DD ou AAAA-MM-DDTHH:MM:SS, como capturada_em): a da coleção em vigor, ou None
    se for antes de todas. No TCG Live a hora conta (a coleção sai às 10h do Pacífico)."""
    d = data or ""
    return next((e for e in epocas(tipo, agora) if e["de"] <= d), None)
