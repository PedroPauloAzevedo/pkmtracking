import json, random, re, sys, shutil
from pathlib import Path
from bs4 import BeautifulSoup

RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ))
shutil.rmtree(RAIZ / "dados", ignore_errors=True)

from tracker import banco, config, leitor, limitless, analises

banco.iniciar()
html = Path(sys.argv[2]).read_text(encoding="utf-8")
exemplo = re.search(r"const EXEMPLO = `([\s\S]*?)`;", html).group(1)

# 1) leitor
d = leitor.ler_partida(exemplo, config.ler_regras())
r = d["resumo"]
print("jogadores", d["jogadores"], "| venc", r["vencedor"], "| motivo", r["motivo"], "| turnos", r["turnos"])
print("premios", {k: v["premios"] for k, v in r["por_jogador"].items()}, "| palpite", r["deck_palpite"], "| 1o KO", r["primeiro_nocaute"])
print("nao lidas", [x["texto"] for x in d["nao_lidas"]])
assert leitor.parece_log(exemplo)
assert leitor.testar_linha("Ana_TCG took 2 Prize cards.", config.ler_regras())[0]["grupos"]["qtd"] == "2"
# sintaxe JS também aceita
assert leitor.compilar_regras([{"id": "x", "tipo": "outro", "ativa": True, "re": "^(?<player>.+) wins"}])[1] == {}

# 2) várias partidas pessoais (variações do exemplo)
random.seed(1)
ids = []
for i in range(14):
    adv = random.choice(["MistyPsy", "BrockRock", "GaryOak"])
    txt = exemplo.replace("MistyPsy", adv)
    if i % 3 == 0:  # derrota: troca a última linha
        txt = txt.replace("Ana_TCG took all of their Prize cards. Ana_TCG wins.", f"Ana_TCG conceded. {adv} wins.")
    txt += f"\n\n(partida {i})"
    pid, nova = banco.inserir_partida(txt, "teste", config.ler_regras())
    ids.append(pid)
pid, nova = banco.inserir_partida(txt, "teste", config.ler_regras())
assert not nova, "duplicado deveria ser ignorado"
banco.atualizar_partida(ids[0], {"meu_deck": "Charizard ex", "deck_adv": "Dragapult ex", "tags": "liga"})
p = analises.analise_pessoal("")
print("eu", p["eu"], "| total", p["total"], "| ordem", [(g["grupo"], g["n"]) for g in p["ordem"]])
print("por adv", [(g["grupo"], g["n"], g["taxa"]) for g in p["por_adversario"]])

# 2b) partida de outra pessoa copiada no seu computador: seu nick não joga nela -> vai para Amigos
outro = exemplo.replace("Ana_TCG", "Bia_Amiga") + "\n\n(partida de outra pessoa)"
cfg = config.ler_config(); cfg["nick"] = "Ana_TCG"; config.salvar_config(cfg)
pid_outro, _ = banco.inserir_partida(outro, "teste", config.ler_regras())
assert banco.obter_partida(pid_outro)["dono"] == "Bia_Amiga", banco.obter_partida(pid_outro)["dono"]
assert banco.obter_partida(ids[0])["dono"] == "", "partida sua não pode mudar de dono"
with banco.conectar() as con:  # gravada como sua por uma versão antiga: separada ao abrir o programa
    con.execute("UPDATE partidas SET dono='' WHERE id=?", (pid_outro,))
assert banco.separar_partidas_de_outros() == 1 and banco.obter_partida(pid_outro)["dono"] == "Bia_Amiga"
assert analises.analise_pessoal("Ana_TCG")["total"] == p["total"], "partida do amigo entrou nas suas"
cfg["nick"] = ""; config.salvar_config(cfg)
print("partida de outra pessoa -> dono", banco.obter_partida(pid_outro)["dono"])

# 2c) filtro Jogador com qualquer combinação (caixa de opções do painel): '' = você, nick = amigo.
#     O mesmo jogo exportado pelos dois lados conta uma vez; jogos do MESMO dono com o mesmo resumo são jogos diferentes.
p1 = banco.obter_partida(ids[1])
adv1 = next(j for j in p1["jogadores"] if j != "Ana_TCG")
pid_dele, _ = banco.inserir_partida(p1["texto"] + "\n(o mesmo jogo, exportado pelo adversário)", "teste", config.ler_regras(), dono=adv1)
assert banco.obter_partida(pid_dele)["dono"] == adv1 and banco.obter_partida(pid_dele)["resumo"]["digital"] == p1["resumo"]["digital"]
n = lambda jog: len(analises.analise_pessoal("Ana_TCG", jogador=jog)["partidas"])
assert n("") == n([""]) == 14 and n("Bia_Amiga") == n(["Bia_Amiga"]) == 1 and n(adv1) == 1
assert n(["", "Bia_Amiga"]) == 15, n(["", "Bia_Amiga"])
assert n(["", adv1]) == 14, "o mesmo jogo pelos dois lados deveria contar uma vez"
assert n(["Bia_Amiga", adv1]) == 2
assert n("*") == n(["", "Bia_Amiga", adv1]) == 15, ("partidas suas com o mesmo resumo não podem sumir", n("*"))
print("filtro jogador: você", n(""), "| você + amiga", n(["", "Bia_Amiga"]), "| você + o outro lado do mesmo jogo", n(["", adv1]),
      "| todos", n("*"))

# 3) torneio sintético com HTML no formato do Labs e do RK9
arqs = ["dragapult-ex", "charizard-ex", "gardevoir-ex", "raging-bolt-ex", "n-zoroark"]
forca = {"dragapult-ex": 0.58, "charizard-ex": 0.55, "gardevoir-ex": 0.5, "raging-bolt-ex": 0.47, "n-zoroark": 0.45}
jog = [{"id": f"{i:04d}", "nome": f"Jogador {i}" + (" José" if i == 3 else ""), "arq": random.choice(arqs)} for i in range(1, 65)]
rec = {j["id"]: [0, 0, 0] for j in jog}
rodadas = []
for rd in range(1, 7):
    random.shuffle(jog)
    mesas = []
    for k in range(0, len(jog), 2):
        a, b = jog[k], jog[k + 1]
        pa = 0.5 + forca[a["arq"]] - forca[b["arq"]]
        x = random.random()
        res = "T" if x > 0.95 else ("W" if x < pa * 0.95 else "L")
        if res == "W": rec[a["id"]][0] += 1; rec[b["id"]][1] += 1
        elif res == "L": rec[a["id"]][1] += 1; rec[b["id"]][0] += 1
        else: rec[a["id"]][2] += 1; rec[b["id"]][2] += 1
        mesas.append((k // 2 + 1, a, b, res))
    rodadas.append(mesas)
ordem = sorted(jog, key=lambda j: (-(rec[j["id"]][0] * 3 + rec[j["id"]][2]), j["id"]))
linhas = "".join(
    f'<tr><td>{pos}</td><td><a href="/0999/player/{j["id"]}">{j["nome"]}</a> <img src="x.png" title="BR"></td>'
    f'<td>{rec[j["id"]][0]*3+rec[j["id"]][2]}</td><td>{rec[j["id"]][0]} - {rec[j["id"]][1]} - {rec[j["id"]][2]}</td><td>55.00%</td><td>52.00%</td>'
    f'<td><a href="/0999/decks/{j["arq"]}"><img src="a.png"></a></td><td><a href="/0999/player/{j["id"]}/decklist">lista</a></td></tr>'
    for pos, j in enumerate(ordem, 1))
STANDINGS = f"""<html><head><title>Teste</title></head><body><h1>Regional Championship Teste</h1>
<p>October 24–25, 2026 • 64 players • 5% ties</p><a href="https://rk9.gg/pairings/TESTE123">Pairings</a>
<table><tr><th>#</th><th>Name</th><th>Points</th><th>Record</th></tr>{linhas}</table></body></html>"""
NAV = '<ul class="nav nav-pills"><li><a aria-controls="P0">Juniors Round 3</a></li><li><a aria-controls="P2">Masters Round 6</a></li></ul>'

def pagina_rodada(rd):
    def lado(cls, j, st):
        return f'<div class="{cls} {st}"><span class="name">{j["nome"]} [BR]</span> (1-0-0)</div>'
    mapa = {"W": ("winner", "loser"), "L": ("loser", "winner"), "T": ("tie", "tie")}
    corpo = "".join(f'<div class="match"><div class="col-2"><span class="tablenumber">{m}</span></div>{lado("player1", a, mapa[res][0])}{lado("player2", b, mapa[res][1])}</div>'
                    for m, a, b, res in rodadas[rd - 1])
    corpo += '<div class="match"><div class="player1 winner"><span class="name">Folga Fulano</span></div><div class="player2"><span class="name"></span></div></div>'
    return f"<html><body>{NAV}{corpo}</body></html>"

CARTAS = {"dragapult-ex": [("Dreepy", "TWM", "128", 4), ("Dragapult ex", "TWM", "130", 3)],
          "charizard-ex": [("Charmander", "OBF", "26", 3), ("Charizard ex", "OBF", "125", 2)]}
def pagina_lista(pid):
    j = next(x for x in jog if x["id"] == pid)
    base = CARTAS.get(j["arq"], [("Ralts", "SVI", "84", 4)]) + [("Arven", "SVI", "166", 4 if int(pid) % 2 else 3), ("Iono", "PAL", "185", 2)]
    return "<html><body>" + "".join(
        f'<a href="https://limitlesstcg.com/cards/{s}/{n}"><img alt="{nome}" src="c.png"><img alt="{q}" src="q.png"></a>' for nome, s, n, q in base) + "</body></html>"

def falsa(self, url):
    if "/standings" in url: h = STANDINGS
    elif "rnd=" in url: h = pagina_rodada(int(re.search(r"rnd=(\d+)", url).group(1)))
    elif "rk9.gg/pairings" in url: h = f"<html><body>{NAV}</body></html>"
    elif url.endswith("/decklist"): h = pagina_lista(re.search(r"player/(\d+)/decklist", url).group(1))
    else: raise limitless.ErroImportacao("url inesperada " + url)
    return BeautifulSoup(h, "html.parser")

limitless.Navegador.sopa = falsa
limitless.PAUSA = 0
limitless.importar("999", listas_top=16)
print("progresso", limitless.progresso)
assert not limitless.progresso["erro"], limitless.progresso["erro"]
m = analises.meta()
print("divisao", [(d["nome"], d["jogadores"], d["taxa"], d["n"], d["conversao"]) for d in m["divisao"]])
print("matriz linha 1", m["matriz"][0]["nome"], [(c["taxa"], c["n"], c["espelho"]) for c in m["matriz"][0]["celulas"]])
pf = analises.perfil("dragapult-ex")
print("perfil", pf["jogadores"], pf["taxa_esperada"], pf["colocacoes"], "listas", pf["listas"], [(c["carta"], c["pct"], c["media_copias"]) for c in pf["esqueleto"]][:4])
c = analises.cartas()
print("cartas", c["listas"], [(x["carta"], x["pct"], x["taxa_com"], x["taxa_sem"]) for x in c["cartas"]][:4])
print("tendencia", analises.tendencia())
tot = sum(len(r) for r in rodadas)
assert len(banco.consultar("SELECT * FROM t_partidas")) == tot, "todas as mesas (sem a folga) devem entrar"
# conferência: total de vitórias da matriz = total de derrotas
mu = analises.matchups_por_slug()
assert sum(v["v"] for v in mu.values()) == sum(v["d"] for v in mu.values())
# acento: "Jogador 3 José" casado entre RK9 e Labs
assert all(p["arq1"] and p["arq2"] for p in banco.consultar("SELECT * FROM t_partidas")), "todo jogador deveria ter deck"
print("dif", analises.comparar_listas("0999", ordem[0]["id"], "0999", ordem[1]["id"]))

# 4) API Flask
import app as aplicativo
cli = aplicativo.app.test_client()
for url in ["/", "/api/status", "/api/partidas", f"/api/partidas/{ids[1]}", "/api/regras", "/api/torneios", "/api/meta?top=32",
            "/api/tendencia", "/api/deck/charizard-ex", "/api/cartas?arq=dragapult-ex", "/api/efeito-cartas?arq=dragapult-ex",
            "/api/jogadores?torneio=0999",
            "/exportar/minhas_partidas.csv", "/exportar/eventos.csv", "/exportar/torneios.csv", "/exportar/meta.csv"]:
    r = cli.get(url)
    assert r.status_code == 200, (url, r.status_code, r.data[:200])
# filtro Jogador pela API: vários (?jogadores=, vazio = você) e o formato das versões antigas (?jogador=)
qtd = lambda url: len(cli.get(url).get_json()["partidas"])
assert {j["id"] for j in cli.get("/api/jogadores-locais").get_json()} == {"", "Bia_Amiga", adv1}
assert qtd("/api/partidas?jogadores=&jogadores=Bia_Amiga") == 15
assert qtd("/api/partidas?jogadores=Bia_Amiga") == qtd("/api/partidas?jogador=Bia_Amiga") == 1
assert qtd("/api/partidas") == 14 and qtd("/api/partidas?jogador=*") == 15
assert cli.get("/api/decisoes?jogadores=&jogadores=Bia_Amiga").status_code == 200
assert len(cli.get("/exportar/minhas_partidas.csv?jogadores=&jogadores=Bia_Amiga").data.decode("utf-8-sig").strip().splitlines()) == 16
# efeito de cada carta (regressão): com o freio no máximo, todo efeito vai a zero; sem freio, a conta converge
from tracker import regressao  # noqa: E402
ef = cli.get("/api/efeito-cartas?arq=dragapult-ex").get_json()
print("efeito cartas:", {k: ef[k] for k in ("listas", "partidas")}, [(c["carta"], c["efeito_pp"]) for c in ef["cartas"][:3]])
linhas = [(0.0, {0: 1.0, 1: 1.0}, 1), (0.0, {0: 1.0, 1: 1.0}, 1), (0.0, {0: 1.0, 1: 1.0}, 0), (0.0, {0: 1.0}, 0), (0.0, {0: 1.0}, 0), (0.0, {0: 1.0}, 1)]
b, _ = regressao.ajustar(linhas, 2, peso=1e9)
assert abs(b[1]) < 1e-6, b
b, _ = regressao.ajustar(linhas, 2, peso=1e-6, peso_deck=1e-6)
assert abs(regressao._sig(b[0] + b[1]) - 2 / 3) < 1e-3 and abs(regressao._sig(b[0]) - 1 / 3) < 1e-3, b  # sem freio = taxas reais
print("POST manual ruim:", cli.post("/api/partidas", json={"texto": "oi"}).status_code)
print("testar:", cli.post("/api/regras/testar", json={"linha": "Ana_TCG's Pidgey was Knocked Out!"}).get_json())
print("regra inválida:", cli.post("/api/regras", json={"regras": [{"id": "x", "tipo": "outro", "ativa": True, "re": "("}]}).status_code)
print("salvar regras:", cli.post("/api/regras", json={"restaurar": True}).get_json())
print("csv:", cli.get("/exportar/meta.csv").data.decode("utf-8-sig").splitlines()[:3])

# 5) biblioteca de cartas com um TCGdex falso: uma carta que nunca responde não pode parar a atualização inteira.
#    A coleção com falha fica como estava, as outras são atualizadas, e a data da última verificação não avança.
import requests, time as _time
from tracker import cartas
SETS_FALSOS = {"/series/sv": {"sets": [{"id": "tA", "name": "Set A", "cardCount": {"total": 2}},
                                       {"id": "tB", "name": "Set B", "cardCount": {"total": 2}}]},
               "/sets/tA": {"id": "tA", "name": "Set A", "releaseDate": "2024-01-01", "cards": [{"id": "tA-001"}, {"id": "tA-002"}]},
               "/sets/tB": {"id": "tB", "name": "Set B", "releaseDate": "2024-01-01", "cards": [{"id": "tB-001"}, {"id": "tB-002"}]}}
class _Resp:
    def __init__(self, dados): self.status_code, self._d = (200, dados) if dados is not None else (404, None)
    def json(self): return self._d
class _SessaoFalsa:
    pedidos = []
    def __init__(self): self.headers = {}
    def get(self, url, timeout=None):
        caminho = url.replace(cartas.API, "")
        _SessaoFalsa.pedidos.append(caminho)
        if caminho == "/cards/tB-002": raise requests.ConnectionError("sem resposta")
        if caminho.startswith("/cards/"):
            i = caminho.split("/")[-1]
            return _Resp({"id": i, "name": "Carta " + i, "localId": i.split("-")[1], "category": "Trainer", "image": "x"})
        return _Resp(SETS_FALSOS.get(caminho))
sessao_real, dormir_real = cartas.requests.Session, _time.sleep
cartas.requests.Session, _time.sleep = _SessaoFalsa, (lambda s: None)
try:
    cartas.PASTA_SETS.mkdir(parents=True, exist_ok=True)
    antigo_b = {"set": {"id": "tB", "name": "Set B"}, "cards": [{"id": "tB-001", "name": "Velha", "image": "x"}]}
    cartas._gravar_json(cartas.PASTA_SETS / "tB.json", antigo_b)
    cartas._gravar_json(cartas.ARQ_ESTADO, {"ultima_verificacao": "2026-01-01T10:00:00", "versao_busca": cartas.VERSAO_BUSCA})
    cartas.atualizar(forcar=True)
    pr = cartas.progresso
    assert not pr["erro"], pr["erro"]
    assert "Set B" in pr["aviso"] and "Set A" not in pr["aviso"], pr["aviso"]
    assert len(cartas._ler_json(cartas.PASTA_SETS / "tA.json", {}).get("cards", [])) == 2, "Set A deveria ter sido baixado"
    assert cartas._ler_json(cartas.PASTA_SETS / "tB.json", None) == antigo_b, "Set B com falha deveria ficar como estava"
    est = cartas._ler_json(cartas.ARQ_ESTADO, {})
    assert est["ultima_verificacao"] == "2026-01-01T10:00:00" and est["falhas"] == ["Set B"], est
    assert _SessaoFalsa.pedidos.count("/cards/tB-002") == 3, "deveria tentar 3 vezes a carta que falha"
    print("biblioteca com falha:", pr["etapa"], "|", pr["aviso"])
    # sem falha, a data avança e o aviso some
    SETS_FALSOS["/sets/tB"]["cards"] = [{"id": "tB-001"}]
    cartas.atualizar(forcar=True)
    est = cartas._ler_json(cartas.ARQ_ESTADO, {})
    assert not cartas.progresso["aviso"] and not cartas.progresso["erro"] and est["falhas"] == [] and est["ultima_verificacao"] > "2026-01-01T10:00:00"
    print("biblioteca sem falha:", cartas.progresso["etapa"])
finally:
    cartas.requests.Session, _time.sleep = sessao_real, dormir_real

# 6) épocas do meta (uma por coleção): no TCG Live a coleção chega na véspera do lançamento nas lojas dos EUA, às 10h
#    do Pacífico (a hora conta); nos torneios ela vale na segunda sexta-feira depois do lançamento (docs/regras-standard.md).
from datetime import datetime as _dt, timezone as _tz
from tracker import colecoes
local = lambda *a: _dt.fromtimestamp(_dt(*a, tzinfo=_tz.utc).timestamp()).isoformat(timespec="seconds")  # UTC -> relógio local
assert colecoes.chegada_live("2026-11-06") == local(2026, 11, 5, 18)  # 10h do Pacífico fora do horário de verão (-8)
assert colecoes.chegada_live("2026-09-16") == local(2026, 9, 15, 17)  # 10h do Pacífico no horário de verão dos EUA (-7)
assert colecoes.validade_torneio("2026-11-06") == "2026-11-20"  # Delta Reign: a mesma data da base de regras
assert colecoes.validade_torneio("2026-09-16") == "2026-09-25"  # lançada numa quarta: 1ª sexta 18/09, 2ª 25/09
agora = "2026-11-05T23:00:00"
ep = colecoes.epocas("live", agora=agora)
assert (ep[0]["nome"], ep[0]["de"], ep[0]["fim"], ep[0]["ate"]) == ("Delta Reign", local(2026, 11, 5, 18), None, None), ep[0]
assert (ep[1]["nome"], ep[1]["de"], ep[1]["fim"]) == ("30th Celebration", local(2026, 9, 15, 17), local(2026, 11, 5, 18)), ep[1]
assert any(e["nome"] == "Black Bolt e White Flare" for e in ep), "coleções do mesmo dia viram uma época só"
# a manhã do dia da chegada ainda é da época anterior
assert colecoes.epocas("live", agora=local(2026, 11, 5, 17))[0]["nome"] == "30th Celebration"
assert colecoes.epoca_de(local(2026, 11, 5, 17), "live", agora=agora)["nome"] == "30th Celebration"
assert colecoes.epoca_de(local(2026, 11, 5, 19), "live", agora=agora)["nome"] == "Delta Reign"
et = colecoes.epocas("torneios", agora=agora)
assert (et[0]["nome"], et[0]["de"], et[0]["fim"], et[0]["ate"]) == ("30th Celebration", "2026-09-25", None, None), et[0]
assert (et[1]["nome"], et[1]["fim"], et[1]["ate"]) == ("Pitch Black", "2026-09-25", "2026-09-24"), et[1]
assert colecoes.proxima("torneios", agora=agora) == {"nome": "Delta Reign", "de": "2026-11-20"}
assert colecoes.proxima("live", agora=agora) is None
# coleção nova que aparece na biblioteca de cartas (depois da última da tabela) entra sozinha; promo e coleção pequena, não
novas = {"tC": ("Futura", "2027-01-29", 120), "tD": ("MEP Black Star Promos", "2027-02-05", 100), "tE": ("Mini", "2027-02-12", 20)}
for sid, (nome, data, total) in novas.items():
    cartas._gravar_json(cartas.PASTA_SETS / f"{sid}.json", {"set": {"id": sid, "name": nome, "releaseDate": data, "cardCount": {"total": total}}, "cards": []})
ep = colecoes.epocas("live", agora="2027-03-01T12:00:00")
assert (ep[0]["nome"], ep[0]["de"]) == ("Futura", local(2027, 1, 28, 18)) and ep[1]["nome"] == "Delta Reign", [e["nome"] for e in ep[:3]]
for sid in novas:
    (cartas.PASTA_SETS / f"{sid}.json").unlink()
r = cli.get("/api/epocas").get_json()
assert r["live"] and r["torneios"] and r["primeira_partida"] and r["primeiro_torneio"] and set(r["proxima"]) == {"live", "torneios"}, r
# filtro de época nas suas partidas: de (com hora) e antes (fim da época, com hora, não incluído)
n_total = lambda q: cli.get("/api/partidas" + q).get_json()["total"]["n"]
assert n_total("?antes=2000-01-01T00:00:00") == 0 and n_total("?de=2000-01-01T10:00:00") == n_total("") > 0
assert n_total("?de=2999-01-01T00:00:00") == 0 and cli.get("/api/decisoes?antes=2000-01-01T00:00:00").get_json()["partidas"] == 0
# filtro de época nas telas de Meta: ?de=&ate= deixa só os torneios dessas datas
tid, dt = (lambda r: (r["id"], r["data"][:10]))(banco.consultar("SELECT id, data FROM torneios")[0])  # o torneio sintético (0999)
dia = lambda d, n: (__import__("datetime").date.fromisoformat(d) + __import__("datetime").timedelta(days=n)).isoformat()
jog = lambda q: cli.get("/api/meta?fonte=todos" + q).get_json()["jogadores_considerados"]
assert jog("") > 0 and jog(f"&de={dt}") == jog("") and jog(f"&de={dia(dt, 1)}") == 0 and jog(f"&ate={dia(dt, -1)}") == 0
assert jog(f"&torneios={tid}&de={dt}&ate={dt}") == jog("") and jog(f"&torneios={tid}&de={dia(dt, 1)}") == 0
print("épocas:", [(e["nome"], e["de"]) for e in colecoes.epocas("live", agora=agora)[:3]], f"| torneio {tid} em", dt)

# 7) identificação do deck: a conta das listas dos torneios fica guardada até os torneios mudarem (antes: 2 minutos)
from tracker import decks
decks._modelo_nb()
assert decks._em_dia("nb")
v = banco.versao_torneios()
banco.apagar_torneio("nao-existe")
assert banco.versao_torneios() == v + 1 and not decks._em_dia("nb"), "torneio apagado deveria refazer a conta"
decks._modelo_nb()
assert decks._em_dia("nb")

# 8) ícones dos decks na página /<torneio>/decks do Labs: no formato antigo dentro do link; no novo (11/2026), numa coluna
#    à parte da mesma linha. E uma lista de ícones vazia não apaga a que já estava gravada.
IMG = '<img src="https://r2.limitlesstcg.net/pokemon/gen9/{}.png" class="pokemon" alt="{}">'
novo = ('<table><tr><td><div><span>' + IMG.format("dragapult", "dragapult") + '</span></div></td><td>142</td>'
        '<td><a href="/0999/decks/dragapult-ex">Dragapult</a></td></tr>'
        '<tr><td><div><span>' + IMG.format("ogerpon", "ogerpon") + IMG.format("clefairy", "clefairy") + '</span></div></td><td>90</td>'
        '<td><a href="/0999/decks/basic-box-m">Basic Box</a></td></tr></table>')
antigo = '<a href="/0999/decks/n-zoroark">' + IMG.format("zoroark", "zoroark") + "N's Zoroark</a>"
lidos = {d["slug"]: d["icones"] for d in decks.ler_pagina_decks(BeautifulSoup(novo + antigo, "html.parser"), "0999")}
assert lidos == {"dragapult-ex": ["dragapult"], "basic-box-m": ["ogerpon", "clefairy"], "n-zoroark": ["zoroark"]}, lidos
v_arq = cli.get("/api/status").get_json()["versao_arquetipos"]
decks.salvar_arquetipos([{"slug": "teste-icone", "nome": "Teste", "icones": ["dragapult"]}])
assert cli.get("/api/status").get_json()["versao_arquetipos"] == v_arq + 1, "o painel precisa saber que o cadastro de decks mudou"
decks.salvar_arquetipos([{"slug": "teste-icone", "nome": "Teste novo", "icones": []}])
assert decks.arquetipos()["teste-icone"]["icones"] == ["dragapult"] and decks.arquetipos()["teste-icone"]["nome"] == "Teste novo"
print("ícones dos decks:", lidos)
print("OK")
