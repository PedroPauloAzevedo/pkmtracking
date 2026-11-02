"""
TESTE DAS TELAS: abre o painel num navegador de verdade (Edge ou Chrome, escondido) e passa por todas as telas.

Em cada tela confere:
  - que ela desenhou (tem um título);
  - que não houve erro de JavaScript nem pedido ao servidor com erro (5xx);
  - que, na largura de celular, a página não rola para o lado.

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
                for largura in (1366, 375):
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
                    if largura == 375 and pagina.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1"):
                        erros.append("no celular, a página rola para o lado")
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
            # busca rápida (Ctrl+K)
            pagina.keyboard.press("Control+K")
            if not pagina.wait_for_selector("input", timeout=5000):
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
