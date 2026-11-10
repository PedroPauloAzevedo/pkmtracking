"""
TESTE DAS TELAS: abre o painel num navegador de verdade (Edge ou Chrome, escondido) e passa por todas as telas.

Em cada tela confere:
  - que ela desenhou (tem um título);
  - que não houve erro de JavaScript nem pedido ao servidor com erro (5xx).
Depois confere o filtro Jogador com vários jogadores marcados (caixa de opções), a seção Efeito de cada carta,
o "Ver todas" com o Início demorando (a tela velha não pode cobrir a nova) e o separador de época (coleção nova).
Só na largura de computador: o programa não é usado no celular.

Uso (numa CÓPIA do programa, nunca na pasta de quem usa):
    python -I testes/teste_tracker.py <cópia> testes/leitor-tcg-live.html     (cria partidas e um torneio de teste)
    python -I testes/teste_telas.py <cópia>                                    -> termina com "OK"

Precisa do Playwright só aqui (não faz parte do programa): pip install -r requirements-dev.txt
Usa o Edge ou o Chrome já instalados (não baixa navegador). Abre o programa na porta 8799.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(sys.argv[1]).resolve()
PORTA = 8799
URL = f"http://127.0.0.1:{PORTA}"
TESTE_ID = f"{time.time():.6f}"
LISTA = """Pokémon: 8
4 Charmander PAF 7
3 Charmeleon PAF 8
1 Charizard ex OBF 125

Trainer: 4
4 Rare Candy SVI 191

Energy: 1
48 Basic Fire Energy SVE 2
"""
IGNORAR = ("/icone/", "/cartas/imagem", "/modelos/", "fonts.googleapis", "fonts.gstatic", "pokemondb", "tcgdex")


def _onde(pilha):
    """Arquivo e linha do erro, ex.: (programa.js:120)."""
    import re
    m = re.search(r"/web/js/([\w.]+:\d+)", pilha or "")
    return f"({m.group(1)})" if m else ""


def preparar():
    """Config da cópia: porta de teste, nada de capturar a área de transferência nem buscar coisas sozinho."""
    if not (RAIZ / "dados" / "tracker.db").exists():
        sys.exit("Rode antes o testes/teste_tracker.py nesta cópia (ele cria os dados de teste).")
    arq = RAIZ / "dados" / "config.json"
    cfg = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
    versao = (RAIZ / "versao.txt").read_text(encoding="utf-8").strip()
    cfg.update({"porta": PORTA, "coletor_ativo": False, "modo_automatico": False, "sincronizar_auto": False,
                "online_ativo": False, "pasta_auto": False, "guia_visto": True, "nick": "Ana_TCG", "versao_vista": versao,
                "teste_id": TESTE_ID})  # para conferir que quem responde na 8799 é esta cópia
    arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def pedir(caminho, dados=None):
    req = urllib.request.Request(URL + caminho, data=json.dumps(dados).encode() if dados else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if dados else "GET")
    return json.load(urllib.request.urlopen(req, timeout=30))


def encerrar_servidor():
    """Fecha o programa que estiver na porta de TESTE (8799), pelo mesmo pedido que o programa usa para fechar
    uma versão antiga. Nunca mexe na 8765, onde fica o Coletor de quem usa."""
    try:
        urllib.request.urlopen(urllib.request.Request(URL + "/api/encerrar", method="POST"), timeout=5)
    except Exception:
        return
    for _ in range(20):
        try:
            pedir("/api/status")
            time.sleep(0.5)
        except Exception:
            return


def abrir_servidor():
    encerrar_servidor()  # um teste anterior (ou outra cópia) ainda aberto na 8799 responderia no lugar desta cópia
    proc = subprocess.Popen([sys.executable, "app.py", "--sem-navegador", "--janela"], cwd=RAIZ,  # sem -I: o app importa tracker/ da pasta dele
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(60):
        try:
            if pedir("/api/status").get("config", {}).get("teste_id") != TESTE_ID:
                sys.exit("Outro programa respondeu na porta 8799 (não é esta cópia).")
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    sys.exit("O programa não abriu na porta 8799.")


def telas():
    """Todas as rotas do painel (tiradas do próprio ROTAS) com os ids de teste nas que precisam de um."""
    deck = pedir("/api/decks", {"nome": "Deck de teste", "lista": LISTA})["id"]
    partida = pedir("/api/partidas")["partidas"][0]["id"]
    com_id = {"partida": f"partida-{partida}", "replay": f"replay-{partida}", "meudeck": f"meudeck-{deck}", "lista": f"lista-{deck}"}
    return com_id


def jogadores_combinados(pagina):
    """Marca e desmarca jogadores na caixa de opções da tela Partidas e confere a lista. Devolve os problemas achados."""
    problemas = []
    contagem = "() => (document.querySelector('#main p.muted.num') || {}).innerText || ''"
    resumo = "() => (document.querySelector('#sel-jogador summary b') || {}).innerText || ''"

    def esperar(texto, onde=contagem):
        try:
            pagina.wait_for_function(f"t => ({onde})().trim() === t", arg=texto, timeout=15000)
        except Exception:
            problemas.append(f"esperava '{texto}', apareceu '{pagina.evaluate(onde)}'")

    pagina.evaluate("try { localStorage.removeItem('jogadores'); localStorage.removeItem('jogador'); } catch (e) {} "
                    "S.jogadorSel = ['']; S.jogadorAberto = false; location.hash = '#x'; location.hash = '#partidas'")
    pagina.wait_for_selector("#sel-jogador summary", timeout=20000)
    esperar("14 partidas")
    pagina.click("#sel-jogador summary")
    pagina.click("#sel-jogador input[value='Bia_Amiga']")      # você + Bia_Amiga
    esperar("15 partidas")
    esperar("Eu + Bia_Amiga", resumo)
    if not pagina.evaluate("document.querySelector('#sel-jogador').open"):
        problemas.append("a caixa fechou depois de marcar (deveria continuar aberta)")
    if "Jogador" not in pagina.evaluate("[...document.querySelectorAll('#main th')].map(t => t.textContent).join('|')"):  # innerText viria em maiúsculas (CSS)
        problemas.append("faltou a coluna Jogador com mais de um jogador marcado")
    pagina.click("#sel-jogador input[value='']")               # só Bia_Amiga
    esperar("1 partidas")
    pagina.click("#sel-jogador input[value='Bia_Amiga']")      # desmarcar o último: não pode
    pagina.wait_for_timeout(500)
    if not pagina.evaluate("document.querySelector(\"#sel-jogador input[value='Bia_Amiga']\").checked"):
        problemas.append("deixou desmarcar todos os jogadores")
    pagina.click("#sel-jogador [data-jog='todos']")            # todos: o mesmo jogo pelos dois lados conta uma vez
    esperar("15 partidas")
    esperar("Todos os jogadores", resumo)
    pagina.click("#main h1")                                    # clicar fora fecha a caixa
    if pagina.evaluate("document.querySelector('#sel-jogador').open"):
        problemas.append("a caixa não fechou ao clicar fora")
    pagina.evaluate("location.hash = '#desempenho'")            # a escolha vale nas outras telas
    pagina.wait_for_selector("#sel-jogador summary", timeout=20000)
    esperar("Todos os jogadores", resumo)
    pagina.reload()                                             # e fica guardada no navegador
    pagina.wait_for_selector("#sel-jogador summary", timeout=20000)
    esperar("Todos os jogadores", resumo)
    pagina.evaluate("location.hash = '#partidas'")
    pagina.wait_for_selector("#sel-jogador summary", timeout=20000)
    pagina.click("#sel-jogador summary")
    pagina.click("#sel-jogador [data-jog='eu']")               # volta para "só eu"
    esperar("14 partidas")
    return problemas


def ver_todas_e_epocas(pagina):
    """"Ver todas" com o Início demorando (a tela velha não pode cobrir a nova) e o separador de época. Devolve os problemas."""
    problemas = []
    pagina.evaluate("location.hash = '#x'; location.hash = '#painel'")
    pagina.wait_for_selector("a.btn[href='#partidas']", timeout=20000)
    # o Início é desenhado de novo e demora 1,5 s; enquanto isso a pessoa clica em "Ver todas"
    pagina.evaluate("""() => {
        const original = window.fetch; window._fetchOriginal = original;
        window.fetch = (url, o) => String(url).endsWith('/api/partidas')
            ? new Promise(ok => setTimeout(() => ok(original(url, o)), 1500)) : original(url, o);
        render(); document.querySelector("a.btn[href='#partidas']").click();
    }""")
    pagina.wait_for_timeout(2500)
    titulo = pagina.evaluate("document.querySelector('#main h1')?.textContent")
    if titulo != "Partidas":
        problemas.append(f"depois de 'Ver todas' a tela é '{titulo}' (o Início, mais lento, cobriu a tela de Partidas)")
    pagina.evaluate("window.fetch = window._fetchOriginal")
    # seletor de época na tela Partidas: escolher a época atual mostra só as partidas dela
    pagina.evaluate("try { localStorage.removeItem('epoca'); } catch (e) {} S.epoca = ''; location.hash = '#x'; location.hash = '#partidas'")
    try:
        pagina.wait_for_selector("#sel-epoca", timeout=20000)
        atual = pagina.evaluate("[...document.querySelectorAll('#sel-epoca option')].find(o => /atual/.test(o.textContent))?.value")
        pagina.select_option("#sel-epoca", atual)
        pagina.wait_for_function("() => /na época/.test(document.querySelector('#main p.muted.num')?.innerText || '')", timeout=15000)
    except Exception as e:
        problemas.append(f"seletor de época na tela Partidas: {str(e).splitlines()[0]}")
    pagina.evaluate("try { localStorage.removeItem('epoca'); } catch (e) {} S.epoca = ''; location.hash = '#x'; location.hash = '#partidas'")
    # filtros Deck do jogador e Deck do adversário: escolher um deck do adversário deixa só as partidas contra ele
    try:
        pagina.wait_for_selector("#f-adv", timeout=20000)
        adv = pagina.evaluate("document.querySelectorAll('#f-adv option')[1]?.value")
        pagina.select_option("#f-adv", adv)
        pagina.wait_for_function("v => document.querySelector('#f-adv')?.value === v", arg=adv, timeout=15000)
        nomes = pagina.evaluate("[...document.querySelectorAll('tr.clicavel td:nth-child(5)')].map(td => td.innerText.trim())")
        alvo = pagina.evaluate("v => nomeDeck(v)", adv)
        if not nomes or any(n != alvo for n in nomes):
            problemas.append(f"filtro Deck do adversário: esperava só '{alvo}', veio {sorted(set(nomes))[:4]}")
        pagina.select_option("#f-adv", "")
    except Exception as e:
        problemas.append(f"filtro Deck do adversário: {str(e).splitlines()[0]}")
    # separador na lista (partidas de duas épocas) e linha tracejada no gráfico
    sep = pagina.evaluate("""() => { const e = S.epocas.live; if (e.length < 2) return 'sem épocas';
        const l = d => ({ id: 1, data: d, resultado: 'V', adversario: 'X', meu_deck: '', deck_adv: '', premios_eu: 6, premios_adv: 0, turnos: 9, comecei: true, motivo: '' });
        const h = tabelaPartidas([l(e[0].de), l(e[1].de)]);  // o começo de cada época (dia e hora) já é dela
        return (h.match(/sep-epoca/g) || []).length + '|' + /marca-epoca/.test(graficoLinhas([{ nome: 'x', valores: [1, 2] }], ['a', 'b'], { marcas: [{ i: 1, rotulo: e[0].nome }] })); }""")
    if sep != "2|true":
        problemas.append(f"separador de época na lista/gráfico: {sep}")
    # "Log original" no detalhe da partida: a janela mostra o texto exatamente como foi gravado
    try:
        pid = pagina.evaluate("api('/api/partidas').then(d => d.partidas[0].id)")
        pagina.evaluate("id => { location.hash = '#x'; location.hash = '#partida-' + id; }", pid)
        pagina.wait_for_selector("#ver-log", timeout=20000)
        pagina.click("#ver-log")
        pagina.wait_for_selector("#log-texto", timeout=5000)
        igual = pagina.evaluate("id => api('/api/partidas/' + id).then(p => document.querySelector('#log-texto').value === p.texto && p.texto.length > 100)", pid)
        if not igual:
            problemas.append("Log original: o texto da janela é diferente do log gravado")
        pagina.click("#log-fechar")
        if pagina.evaluate("!!document.querySelector('#log-texto')"):
            problemas.append("Log original: a janela não fechou")
    except Exception as e:
        problemas.append(f"Log original: {str(e).splitlines()[0]}")
    return problemas


def tema_manual(pagina):
    """Tema escolhido à mão: Escuro e Claro valem por cima do Windows, continuam depois de recarregar e Automático volta a
    seguir o Windows. O navegador do teste está em tema claro, então "Automático" = fundo claro. Devolve os problemas."""
    problemas = []
    fundo = lambda: pagina.evaluate("getComputedStyle(document.body).backgroundColor")
    claro, escuro = "rgb(238, 241, 245)", "rgb(15, 20, 32)"
    try:
        # os botões ficam no Início, junto com "Hoje" e "Dados coletados" (2026.11.09-4)
        pagina.evaluate("location.hash = '#x'; location.hash = '#painel'")
        pagina.wait_for_selector("#tema [data-tema='escuro']", timeout=20000)
        for parte in ("#in-hoje", "#in-dados"):
            if not pagina.query_selector(parte):
                problemas.append(f"Início sem {parte}")
        pagina.click("#tema [data-tema='escuro']")
        if fundo() != escuro:
            problemas.append(f"Escuro: fundo {fundo()}")
        pagina.reload()
        pagina.wait_for_selector("#tema [aria-pressed='true']", timeout=20000)
        if fundo() != escuro or pagina.evaluate("document.querySelector('#tema [aria-pressed=\"true\"]').dataset.tema") != "escuro":
            problemas.append("Escuro não continuou depois de recarregar")
        pagina.click("#tema [data-tema='claro']")
        if fundo() != claro:
            problemas.append(f"Claro: fundo {fundo()}")
        pagina.emulate_media(color_scheme="dark")
        if fundo() != claro:
            problemas.append("Claro escolhido não vale por cima do Windows escuro")
        pagina.click("#tema [data-tema='']")
        if fundo() != escuro or pagina.evaluate("'tema' in document.documentElement.dataset"):
            problemas.append("Automático não voltou a seguir o Windows (escuro)")
        pagina.emulate_media(color_scheme="light")
        if fundo() != claro:
            problemas.append("Automático não voltou a seguir o Windows (claro)")
    except Exception as e:
        problemas.append(str(e).splitlines()[0])
    finally:
        pagina.emulate_media(color_scheme="light")
        pagina.evaluate("try { localStorage.removeItem('tema'); } catch (e) {} aplicarTema('')")
    return problemas


def main():
    from playwright.sync_api import sync_playwright
    preparar()
    proc = abrir_servidor()
    falhas = []
    try:
        com_id = telas()
        with sync_playwright() as pw:
            nav = None
            for canal in ("msedge", "chrome"):
                try:
                    nav = pw.chromium.launch(channel=canal, headless=True)
                    break
                except Exception:
                    continue
            if not nav:
                sys.exit("Não achei o Edge nem o Chrome instalados.")
            pagina = nav.new_page(viewport={"width": 1366, "height": 900})
            erros = []
            pagina.on("pageerror", lambda e: erros.append(f"erro de JavaScript: {e.message} " + _onde(e.stack)))
            pagina.on("console", lambda m: m.type == "error" and not any(x in m.text for x in IGNORAR)
                      and "Failed to load resource" not in m.text and erros.append(f"console: {m.text}"))
            pagina.on("response", lambda r: r.status >= 500 and erros.append(f"servidor {r.status}: {r.url}"))
            pagina.on("requestfailed", lambda r: not any(x in r.url for x in IGNORAR) and "ABORTED" not in (r.failure or "")
                      and erros.append(f"pedido falhou: {r.url}"))  # ABORTED: o navegador cancela ao trocar de tela
            pagina.goto(URL + "/")
            pagina.wait_for_function("() => document.querySelector('#main h1')", timeout=20000)
            rotas = pagina.evaluate("Object.keys(ROTAS)")
            for nome in rotas:
                destino = com_id.get(nome, nome)
                for largura in (1366,):
                    erros.clear()
                    pagina.set_viewport_size({"width": largura, "height": 900})
                    pagina.evaluate("h => { location.hash = '#x'; location.hash = '#' + h; }", destino)
                    try:
                        pagina.wait_for_function(
                            "() => { const m = document.querySelector('#main'); return m && m.querySelector('h1, h2, .panel') && !/Carregando|Montando/.test(m.innerText); }",
                            timeout=20000)
                    except Exception:
                        erros.append("a tela não terminou de desenhar (nada em 20 s)")
                    pagina.wait_for_timeout(400)  # pedidos que a tela faz depois de desenhar
                    situacao = "ok" if not erros else "FALHOU"
                    print(f"{situacao:6} #{destino:24} {largura}px" + ("" if not erros else "\n         " + "\n         ".join(erros[:5])))
                    if erros:
                        falhas.append(destino)
            # Uso de cartas com um deck escolhido: aparece a seção "Efeito de cada carta" (regressão)
            pagina.set_viewport_size({"width": 1366, "height": 900})
            erros.clear()
            pagina.evaluate("location.hash = '#cartas'")
            pagina.wait_for_timeout(1500)
            pagina.evaluate("S.deckCartas = 'dragapult-ex'; render()")
            try:
                pagina.wait_for_function("() => { const e = document.querySelector('#efeito-cartas'); return e && !/Calculando/.test(e.innerText); }", timeout=30000)
            except Exception:
                erros.append("a seção Efeito de cada carta não terminou")
            print(("ok    " if not erros else "FALHOU") + " #cartas com deck (Efeito de cada carta)" + ("" if not erros else "\n         " + "\n         ".join(erros[:5])))
            if erros:
                falhas.append("efeito-cartas")
            # Filtro Jogador: caixa de opções com qualquer combinação (dados do teste_tracker: você com 14 partidas,
            # Bia_Amiga com 1 e o adversário de uma das suas com o outro lado do mesmo jogo)
            erros.clear()
            problemas = jogadores_combinados(pagina)
            print(("ok    " if not (erros or problemas) else "FALHOU") + " #partidas com vários jogadores marcados"
                  + ("" if not (erros or problemas) else "\n         " + "\n         ".join((problemas + erros)[:6])))
            if erros or problemas:
                falhas.append("filtro jogador")
            # "Ver todas" com uma tela lenta e o separador de época (coleção nova)
            erros.clear()
            problemas = ver_todas_e_epocas(pagina)
            print(("ok    " if not (erros or problemas) else "FALHOU") + " Ver todas com o Início lento + época"
                  + ("" if not (erros or problemas) else "\n         " + "\n         ".join((problemas + erros)[:6])))
            if erros or problemas:
                falhas.append("ver todas / época")
            # tema claro / escuro / automático escolhido à mão
            erros.clear()
            problemas = tema_manual(pagina)
            print(("ok    " if not (erros or problemas) else "FALHOU") + " tema claro / escuro / automático"
                  + ("" if not (erros or problemas) else "\n         " + "\n         ".join((problemas + erros)[:6])))
            if erros or problemas:
                falhas.append("tema")
            # busca rápida (Ctrl+K)
            pagina.keyboard.press("Control+K")
            if not pagina.wait_for_selector("#busca-q", timeout=5000):  # o campo da busca (não outro campo da tela)
                falhas.append("busca Ctrl+K")
            nav.close()
    finally:
        encerrar_servidor()
        proc.kill()
    if falhas:
        sys.exit(f"Telas com problema: {sorted(set(falhas))}")
    print("OK")


if __name__ == "__main__":
    main()
