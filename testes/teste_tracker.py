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
print("OK")
