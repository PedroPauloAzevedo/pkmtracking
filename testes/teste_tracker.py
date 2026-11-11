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
# segunda fonte (malie.io, D-051): chave da coleção e conversão para o formato do TCGdex (só a impressão normal entra)
assert [cartas.id_malie(x) for x in ("me06", "me02.5", "sv08.5", "sv10.5b", "30th")] == ["me6", "me2-5", "sv8-5", "sv10-5b", None]
m_cartas = [{"name": "Bubbly {W} Energy", "card_type": "ENERGY", "subtype": "SPECIAL", "collector_number": {"numeric": 132},
             "rarity": {"designation": "UNCOMMON"}, "ext": {"tcgl": {"longFormID": "Bubbly_me6_132_std_Uncommon"}}},
            {"name": "Bubbly {W} Energy", "card_type": "ENERGY", "subtype": "SPECIAL", "collector_number": {"numeric": 132},
             "ext": {"tcgl": {"longFormID": "Bubbly_me6_132_ph_Uncommon_Reverse"}}},
            {"name": "Heracross", "card_type": "POKEMON", "hp": 130, "stage": "BASIC", "regulation_mark": "J",
             "collector_number": {"numeric": 1}, "rarity": {"designation": "COMMON"}, "ext": {"tcgl": {"longFormID": "H_me6_1_std_C"}},
             "text": [{"kind": "ATTACK", "name": "Spike Draw"}, {"kind": "ABILITY", "name": "Horn"}]}]
conv = cartas.set_do_malie(m_cartas, "me06", "Delta Reign", "2026-11-06", "DLR")
assert [c["id"] for c in conv["cards"]] == ["me06-132", "me06-001"] and conv["set"]["fonte"] == "malie", conv
assert conv["cards"][0]["name"] == "Bubbly Water Energy" and conv["cards"][0]["energyType"] == "Special"
assert cartas.chave_funcional(conv["cards"][1]) == "heracross|130|horn|spike draw" and conv["cards"][1]["regulationMark"] == "J"

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
# torneios online usam a coleção desde o lançamento (D-048): Delta Reign já é a época atual deles em 05/11 à noite
eo = colecoes.epocas("online", agora="2026-11-06T12:00:00")
assert (eo[0]["nome"], eo[0]["de"], eo[0]["fim"]) == ("Delta Reign", "2026-11-06", None) and eo[1]["ate"] == "2026-11-05", eo[:2]
assert colecoes.proxima("online", agora="2026-11-06T12:00:00") is None
# coleção nova que aparece na biblioteca de cartas (depois da última da tabela) entra sozinha; promo e coleção pequena, não
novas = {"tC": ("Futura", "2027-01-29", 120), "tD": ("MEP Black Star Promos", "2027-02-05", 100), "tE": ("Mini", "2027-02-12", 20)}
for sid, (nome, data, total) in novas.items():
    cartas._gravar_json(cartas.PASTA_SETS / f"{sid}.json", {"set": {"id": sid, "name": nome, "releaseDate": data, "cardCount": {"total": total}}, "cards": []})
ep = colecoes.epocas("live", agora="2027-03-01T12:00:00")
assert (ep[0]["nome"], ep[0]["de"]) == ("Futura", local(2027, 1, 28, 18)) and ep[1]["nome"] == "Delta Reign", [e["nome"] for e in ep[:3]]
for sid in novas:
    (cartas.PASTA_SETS / f"{sid}.json").unlink()
g = cli.get("/api/resumo-geral").get_json()  # números gerais do Início ("Dados coletados")
assert g["partidas"]["n"] > 0 and g["partidas"]["n"] == g["partidas"]["suas"] + g["partidas"]["amigos"] and g["torneios"]["n"] > 0, g
r = cli.get("/api/epocas").get_json()
assert r["live"] and r["torneios"] and r["online"] and r["primeira_partida"] and r["primeiro_torneio"] and set(r["proxima"]) == {"live", "torneios", "online"}, r
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
# ?epoca=<coleção>: cada fonte com o seu começo (D-048). O torneio sintético é um grande evento; marcado como online, passa a
# seguir a época dos online (que começa no lançamento, antes da validade nos grandes eventos)
e_t, e_o = colecoes.epoca_de(dt, "torneios"), colecoes.epoca_de(dt, "online")
outra = next(e for e in colecoes.epocas("online") if e["id"] not in (e_t["id"], e_o["id"]))
assert jog(f"&epoca={e_t['id']}") == jog("") and jog(f"&epoca={outra['id']}") == 0 and jog(f"&epoca={e_t['id']}&torneios={tid}") == jog("")
assert cli.get(f"/api/meta?fonte=online&epoca={e_t['id']}").get_json()["jogadores_considerados"] == 0
with banco.conectar() as con:
    con.execute("UPDATE torneios SET fonte = 'online' WHERE id = ?", (tid,))
banco.marcar_mudanca_torneios()
try:
    assert jog(f"&epoca={e_o['id']}") == jog("") > 0 and jog(f"&epoca={outra['id']}") == 0
    assert cli.get(f"/api/meta?fonte=grandes&epoca={e_o['id']}").get_json()["jogadores_considerados"] == 0
finally:
    with banco.conectar() as con:
        con.execute("UPDATE torneios SET fonte = 'labs' WHERE id = ?", (tid,))
    banco.marcar_mudanca_torneios()
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

# 9) D-040 (NB2 decide sempre que há modelo), D-042 (deck "incerto") e D-041 (faixas com a dependência entre partidas)
guardado = decks.identificar_nb
try:
    for conf, esperado_incerto in ((0.3, True), (0.59, True), (0.6, False), (0.95, False)):
        decks.identificar_nb = lambda r, c=conf: ("deck-do-modelo", c)
        decks._cache.pop("ident", None)
        d = decks.identificar_detalhe({"Dusknoir": 1, "Rare Candy": 1})
        assert d["deck"] == "deck-do-modelo" and d["metodo"] == "nb2", d   # antes: com confiança < 0,5 valiam os ícones
        assert decks.incerto(d) is esperado_incerto, (conf, d)
    decks.identificar_nb = lambda r: ("", 0.0)                             # sem modelo: ícones, nunca "incerto"
    decks._cache.pop("ident", None)
    d = decks.identificar_detalhe({"Dragapult ex": 1})
    assert d["metodo"] in ("icones", "") and not decks.incerto(d), d
finally:
    decks.identificar_nb = guardado
    decks._cache.pop("ident", None)
assert all("deck_adv_incerto" in l for l in cli.get("/api/partidas").get_json()["partidas"])
assert analises.wilson(50, 100) == analises.wilson(50, 100, efeito=1.0)
assert analises.wilson(50, 100, efeito=4) == analises.wilson(12.5, 25), "efeito 4: 100 partidas valem como 25"
largura = lambda f: f[1] - f[0]
assert largura(analises.wilson(55, 100, efeito=1.5)) > largura(analises.wilson(55, 100))
assert abs(analises.icc_binario([[1, 1, 1], [0, 0, 0], [1, 1, 1], [0, 0, 0]]) - 1) < 1e-9
assert analises.efeito_desenho(100, 20, 0.1) == 1.4 and analises.efeito_desenho(100, 20, -0.2) == 1.0 and analises.efeito_desenho(0, 0, 0.1) == 1.0
m = analises.meta()
assert m["icc"] >= 0
for d in m["divisao"]:
    ingenua = analises.wilson(d["v"], d["n"])
    assert d["taxa"] == round(100 * d["v"] / d["n"], 1), "a taxa não muda com a correção"
    assert d["ic_baixo"] <= ingenua[0] and d["ic_alto"] >= ingenua[1], (d, ingenua)   # faixa nunca mais estreita
print("D-040/D-041/D-042: ok; ICC do meta de teste", m["icc"])
# D-052: Dragapult com Dunsparce na lista vira Dragapult Dudunsparce (e sem nenhum, Dragapult), também nos confrontos
with banco.conectar() as con:
    con.execute("INSERT INTO t_jogadores (torneio, labs_id, nome, nome_norm, arquetipo) VALUES ('0999','dragteste','Ana Teste','ana teste','dragapult-ex')")
    con.execute("INSERT INTO t_listas (torneio, labs_id, carta, qtd) VALUES ('0999','dragteste','Dunsparce',1), ('0999','dragteste','Dreepy',4)")
    con.execute("INSERT INTO t_partidas VALUES ('0999', 99, '1', 'ana teste', 'outro', 'W', 'dragapult-ex', 'x')")
try:
    assert banco.separar_arquetipos("0999") >= 1
    assert banco.consultar("SELECT arquetipo FROM t_jogadores WHERE labs_id='dragteste'")[0]["arquetipo"] == "dragapult-dudunsparce"
    assert banco.consultar("SELECT arq1 FROM t_partidas WHERE rodada=99 AND torneio='0999'")[0]["arq1"] == "dragapult-dudunsparce"
    with banco.conectar() as con:
        con.execute("DELETE FROM t_listas WHERE labs_id='dragteste' AND carta='Dunsparce'")
    banco.separar_arquetipos("0999")
    assert banco.consultar("SELECT arquetipo FROM t_jogadores WHERE labs_id='dragteste'")[0]["arquetipo"] == "dragapult-ex"
finally:
    with banco.conectar() as con:
        for tab, col in (("t_jogadores", "labs_id"), ("t_listas", "labs_id")):
            con.execute(f"DELETE FROM {tab} WHERE {col}='dragteste'")
        con.execute("DELETE FROM t_partidas WHERE rodada=99 AND torneio='0999'")
    banco.marcar_mudanca_torneios()
assert decks.regra_dragapult("dragapult-ex", {"Dudunsparce": 1}) == "dragapult-dudunsparce"
assert decks.regra_dragapult("dragapult-dudunsparce", {"Dreepy": 2}) == "dragapult-ex"
assert decks.regra_dragapult("dragapult-dusknoir", {"Dunsparce": 1}) == "dragapult-dusknoir"
# Perfil de deck > Listas: listas completas do deck, com link do Limitless e busca por cartas (todas ao mesmo tempo)
arq_l = banco.consultar("SELECT j.arquetipo AS a FROM t_listas l JOIN t_jogadores j ON j.torneio=l.torneio AND j.labs_id=l.labs_id "
                        "WHERE j.arquetipo != '' GROUP BY j.arquetipo ORDER BY COUNT(*) DESC LIMIT 1")[0]["a"]
rl = cli.get(f"/api/deck/{arq_l}/listas?fonte=todos").get_json()
assert rl["total"] > 0 and rl["listas"] and rl["listas"][0]["cartas"] and rl["listas"][0]["link"].startswith("https://labs.limitlesstcg.com/"), rl
c1 = rl["listas"][0]["cartas"][0]["carta"]
com1 = cli.get(f"/api/deck/{arq_l}/listas?fonte=todos&com={c1}").get_json()
assert 1 <= com1["achadas"] <= rl["total"] and all(any(c1 == x["carta"] for x in l["cartas"]) for l in com1["listas"])
assert cli.get(f"/api/deck/{arq_l}/listas?fonte=todos&com={c1}&com=Carta Que Nao Existe").get_json()["achadas"] == 0
from tracker import auto_export  # modo automático leve: sem o jogo aberto, não fotografa a tela (2026.11.10-4)
assert auto_export.estado_do_jogo() in ("fechado", "minimizado", "aberto")
# D-050: deck cujo atacante principal não está em nenhuma lista de torneio ganha nome provisório (esse Pokémon) e fica "incerto"
r_nova = {"deck_palpite": {"Bia": "Pokémon Inventado ex"}, "vistas": {"Bia": {"Pokémon Inventado ex": 3, "Rare Candy": 1}}}
d = decks.palpite_deck_detalhe(r_nova, "Bia")
assert d == {"deck": "Pokémon Inventado ex", "confianca": None, "metodo": "provisorio"} and decks.incerto(d), d
carta_comum = max(next(iter(decks._assinaturas()[0].values())).items(), key=lambda kv: kv[1])[0]  # carta comum nas listas
assert not decks.carta_sem_listas(carta_comum) and decks.palpite_deck_detalhe({"deck_palpite": {"Bia": carta_comum}, "vistas": {}}, "Bia")["metodo"] != "provisorio"

# 9) códigos das cartas no log ("Hide card IDs from export" desmarcado no jogo): "(sv6_200) Dragapult ex". A leitura tem que ser
#    a mesma do log sem códigos, e os códigos ficam guardados por jogador (versão exata da carta)
base = leitor.ler_partida(exemplo, config.ler_regras())
jog_a = base["jogadores"][0]
carta_a = sorted(base["resumo"]["vistas"][jog_a], key=len, reverse=True)[0]
com_cod = exemplo.replace(carta_a, "(sv6_200) " + carta_a)
assert "(sv6_200) " + carta_a in com_cod
lido = leitor.ler_partida(com_cod, config.ler_regras())
codigos = lido["resumo"].pop("codigos")
base["resumo"].pop("codigos")
assert json.dumps(lido, sort_keys=True, default=str) == json.dumps(base, sort_keys=True, default=str), "código mudou a leitura"
assert "sv6_200" in codigos[jog_a], codigos
assert leitor.limpar_linha("Ana's (sv8-5_72_ph) Drakloak was Knocked Out!") == "Ana's Drakloak was Knocked Out!"
ind_f = {"cartas": {"sv06-200": {}, "me02.5-158": {}, "sv08.5-072": {}}}
assert [cartas.id_do_codigo(c, ind_f) for c in ("sv6_200", "me2-5_158", "sv8-5_72_ph", "swsh9_186")] == ["sv06-200", "me02.5-158", "sv08.5-072", None]
print("códigos das cartas no log: ok,", carta_a)

# 10) D-053 (métodos do painel Indigo Plateau): rodadas suíças, binomial, estabilidade e lista base com respostas conhecidas
from tracker import evolucao_listas as ev
assert ev.rodadas_suicas({1: 922, 2: 900, 8: 850, 9: 279, 10: 270, 11: 4, 12: 2, 13: 1}) == {1, 2, 8}       # Dia 1 sem o Dia 2 e o corte
assert ev.rodadas_suicas({1: 66, 5: 39, 8: 18, 9: 10, 10: 9}, grande_evento=False) == {1, 5, 8, 9, 10}    # online: desistência não corta
assert ev.rodadas_suicas({1: 61, 2: 57, 3: 4, 4: 2, 5: 1}, grande_evento=False) == {1, 2}                 # top 8 fora
assert abs(ev.binomial_cauda_superior(8, 10, 0.5) - 56 / 1024) < 1e-12                                    # (45 + 10 + 1) / 2^10
assert ev.binomial_cauda_superior(0, 5, 0.3) == 1.0
lst = lambda cs: {"cartas": cs, "pontos": 9, "partidas": 4, "data": "2026-11-01", "chave": id(cs)}
iguais = [lst({"A": 4, "B": 2}) for _ in range(20)]
e0 = ev.estabilidade(iguais, [lst({"A": 4, "B": 2}) for _ in range(20)])
assert e0["mudou"] == 0 and e0["estavel"], e0
e1 = ev.estabilidade(iguais, [lst({"A": 4, "C": 2}) for _ in range(20)])                                  # trocou 2 B por 2 C
assert e1["mudou"] == 2 and not e1["estavel"] and e1 == ev.estabilidade(iguais, [lst({"A": 4, "C": 2}) for _ in range(20)]), e1
assert ev._nome_carta("Basic Fire Energy") == "Fire Energy" and ev._nome_carta("Fire Energy") == "Fire Energy"
print("métodos D-053: ok")
print("OK")
