"""
MODO AUTOMÁTICO (experimental, desligado por padrão).

Olha a tela a cada 2 segundos. Quando a tela de resultado da partida aparece, clica
em "Battle Log" e depois no botão de exportar. O log vai para a área de transferência
e o coletor grava. Ou seja: você termina a partida e ela já está registrada.

Como ele reconhece os botões: por imagens de modelo em modelos/. Você pode recortar as suas
(veja modelos/LEIA-ME.txt) ou usar as imagens prontas do projeto Full Bench
(github.com/heatfireash/FullBench, licença MIT), recortadas numa tela 2560x1440.
Por isso a busca testa vários tamanhos e guarda o que deu certo no seu monitor.

Para não perder partidas (ideias do Full Bench):
  - enquanto copia, um quadrinho vermelho cobre o botão Continue (ver cobertura.py);
  - se o log não chegar, tenta mais uma vez (e, se o log já estiver aberto, só clica em exportar);
  - se ainda assim não chegar, avisa (notificação do Windows) e conta como "perdida";
  - enquanto a tela de resultado continuar aberta, tenta de novo a cada 5 s, em silêncio (desde 2026.11.13: um aviso
    do jogo por cima da tela de resultado engolia o clique em Battle Log, e a busca dos botões não percebe isso).

Para ficar leve (ideia do Full Bench, desde 2026.11.10-4): no Windows, com o jogo fechado ou minimizado, ele não
fotografa a tela, só confere a cada 5 segundos se o jogo abriu (estado_do_jogo). E, quando pede para você copiar o log
à mão, libera o Continue assim que o log chega, sem esperar os 20 segundos.

Ele NÃO lê a memória do jogo, não mexe nos arquivos do jogo e não joga por você:
só reconhece dois botões e clica neles depois que a partida acabou. Mesmo assim,
é automação de cliques no cliente do jogo; use por sua conta e risco.

Precisa de: pip install -r requirements-auto.txt  (pyautogui, opencv-python, pillow)
O "pip" precisa ser o do Python que roda o programa (o da pasta .venv): um "pip install" num
terminal qualquer instala no Python do Windows, e o programa continua sem as bibliotecas.
Por isso o painel tem o botão "Instalar o modo automático" (ver instalar()).
"""
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import avisos, config
from .coletor import coletor

MODELOS = {
    "battle_log": "botao_battle_log.png",   # obrigatório: botão "Battle Log" na tela de resultado
    "exportar": "botao_exportar.png",       # obrigatório: botão de exportar/copiar dentro do log
    "continuar": "botao_continuar.png",     # opcional: confirma a tela de resultado e é coberto enquanto copia
    "fechar": "botao_fechar.png",           # opcional: botão para fechar o log depois
}
OPCIONAIS = ("continuar", "fechar")

# Imagens prontas do Full Bench (licença MIT), num commit fixo para não mudarem sem aviso.
FULLBENCH = "https://raw.githubusercontent.com/heatfireash/FullBench/393eec46257fc5f3fa010593b75b7f1e50a46cdf/"
PRONTAS = {"battle_log": "battlelog_button.png", "exportar": "copy_button.png", "continuar": "continue_button.png"}

ESCALAS = [round(0.36 + 0.02 * i, 2) for i in range(63)]   # 0,36 a 1,60 do tamanho da imagem
TESTADAS = 16               # busca ampla: as 16 escalas mais perto do esperado (jogo em janela, por exemplo)
ALTURA_PRONTAS = 1440       # as imagens do Full Bench foram recortadas numa tela de 1440 de altura
SEM_TELA_PARA_SOLTAR = 12   # segundos sem a tela de resultado até poder capturar a próxima partida
QUASE = 0.70                # nota na tela reduzida a partir da qual vale conferir na tela inteira
ESPERA_REPETIR = 5.0        # depois de uma falha, com a tela de resultado ainda aberta: segundos até a nova tentativa
MAX_REPETIR = 12            # novas tentativas, no máximo (uns 2 minutos), enquanto a tela de resultado continuar aberta


def baixar_prontas():
    """Troca as imagens dos botões pelas do Full Bench. As suas vão para modelos/minhas/."""
    import requests
    novas = {}
    for k, arquivo in PRONTAS.items():
        r = requests.get(FULLBENCH + arquivo, timeout=30)
        r.raise_for_status()
        if r.content[:4] != b"\x89PNG":
            raise RuntimeError(f"O arquivo {arquivo} do Full Bench não veio como PNG.")
        novas[k] = r.content
    licenca = requests.get(FULLBENCH + "LICENSE", timeout=30).text
    pasta = config.PASTA_MODELOS
    guarda = pasta / "minhas"
    for k, conteudo in novas.items():
        destino = pasta / MODELOS[k]
        if destino.exists():
            guarda.mkdir(exist_ok=True)
            shutil.copy(destino, guarda / MODELOS[k])
        destino.write_bytes(conteudo)
    cfg = config.ler_config()
    cfg["modelos_prontos"] = sorted(novas)
    config.salvar_config(cfg)
    (pasta / "CREDITOS-FullBench.txt").write_text(
        "As imagens botao_battle_log.png, botao_exportar.png e botao_continuar.png vieram do projeto\n"
        "Full Bench (https://github.com/heatfireash/FullBench), sob esta licença:\n\n" + licenca, encoding="utf-8")
    esquecer_escala()
    return sorted(MODELOS[k] for k in novas)


TITULO_JOGO = "Pokemon TCG Live"


def _janela_do_jogo():
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    u, achadas = ctypes.windll.user32, []

    def olhar(h, _):
        n = u.GetWindowTextLengthW(h)
        if n and u.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, b, n + 1)
            if b.value == TITULO_JOGO:
                achadas.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(olhar), 0)
    return achadas[0] if achadas else None


def tamanho_jogo():
    """(largura, altura) da área do jogo (sem a borda da janela), ou None se não achar a janela (ou fora do Windows).
    Os botões crescem e diminuem com a janela do jogo, não com o monitor."""
    h = _janela_do_jogo()
    if not h:
        return None
    import ctypes
    from ctypes import wintypes
    r = wintypes.RECT()
    if not ctypes.windll.user32.GetClientRect(h, ctypes.byref(r)) or r.bottom < 100:
        return None  # minimizada
    return r.right, r.bottom


def estado_do_jogo():
    """"fechado", "minimizado" ou "aberto". Fora do Windows não dá para saber: "aberto" (olha a tela como antes)."""
    if sys.platform != "win32":
        return "aberto"
    h = _janela_do_jogo()
    if not h:
        return "fechado"
    import ctypes
    return "minimizado" if ctypes.windll.user32.IsIconic(h) else "aberto"


ESPERA_SEM_JOGO = 5.0  # segundos entre uma conferência e outra com o jogo fechado ou minimizado (sem foto da tela)


def jogo_na_frente():
    """O jogo é a janela ativa? (Fora do Windows não dá para saber: considera que sim.)"""
    if sys.platform != "win32":
        return True
    import ctypes
    h = _janela_do_jogo()
    return bool(h) and ctypes.windll.user32.GetForegroundWindow() == h


def trazer_jogo():
    """Põe o jogo na frente antes de clicar. O toque na tecla Alt é o jeito aceito pelo Windows
    de deixar um programa em segundo plano trocar a janela ativa."""
    h = _janela_do_jogo()
    if not h:
        return False
    import ctypes
    u = ctypes.windll.user32
    u.keybd_event(0x12, 0, 0, 0)
    u.keybd_event(0x12, 0, 2, 0)
    u.SetForegroundWindow(h)
    time.sleep(0.4)
    return jogo_na_frente()


def python_do_programa():
    """O python.exe que roda o programa (com o ícone na bandeja ele roda como pythonw.exe, que não mostra o pip)."""
    exe = Path(sys.executable)
    console = exe.with_name("python.exe")
    return console if exe.name.lower() == "pythonw.exe" and console.exists() else exe


def comando_instalar():
    return f'"{python_do_programa()}" -m pip install -r "{config.RAIZ / "requirements-auto.txt"}"'


def esquecer_escala():
    """Imagens novas: o tamanho certo no seu monitor precisa ser descoberto de novo."""
    cfg = config.ler_config()
    cfg["escala_modelos"] = {}
    config.salvar_config(cfg)
    auto.escalas = {}
    auto._cache.clear()


class AutoExport:
    def __init__(self):
        self.status = "desligado"
        self.erro = ""
        self.cliques = 0
        self.perdidas = 0
        self.escalas = {}   # tamanho que funcionou no seu monitor, por botão
        self.ultima_nota = 0.0  # parecença da última busca (0 a 1), para o registro de diagnóstico
        self.ultima_escala = None  # tamanho em que a última busca chegou mais perto
        self._cache = {}
        self._thread = None
        self._parar = threading.Event()

    def faltando(self):
        return [n for k, n in MODELOS.items() if k not in OPCIONAIS and not (config.PASTA_MODELOS / n).exists()]

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="auto_export", daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()
        self.status = "desligado"

    def instalar(self):
        """Instala pyautogui/opencv/pillow no Python do programa e, se o modo estiver ligado, já começa a vigiar."""
        if self.status == "instalando":
            return
        self.status, self.erro = "instalando", ""
        threading.Thread(target=self._instalar, name="instalar_auto", daemon=True).start()

    def _instalar(self):
        try:
            r = subprocess.run([str(python_do_programa()), "-m", "pip", "install", "-r", str(config.RAIZ / "requirements-auto.txt")],
                               capture_output=True, text=True, timeout=900, cwd=str(config.RAIZ),
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if r.returncode != 0:
                fim = (r.stderr or r.stdout or "").strip().splitlines()[-1:] or ["sem detalhes"]
                raise RuntimeError(fim[0])
        except Exception as e:
            self.status = "indisponível"
            self.erro = f"Não consegui instalar: {e}. Tente num terminal: {comando_instalar()}"
            return
        import importlib
        importlib.invalidate_caches()  # o import seguinte já enxerga as bibliotecas novas, sem reabrir o programa
        self.status = "desligado"
        if config.ler_config().get("modo_automatico"):
            self.iniciar()

    # -------------------------------------------------------------- reconhecer os botões
    def _modelo(self, cv2, k):
        caminho = config.PASTA_MODELOS / MODELOS[k]
        if not caminho.exists():
            return None
        marca = caminho.stat().st_mtime
        if k not in self._cache or self._cache[k][0] != marca:
            img = cv2.imread(str(caminho), cv2.IMREAD_GRAYSCALE)
            self._cache[k] = (marca, img)
        return self._cache[k][1]

    def _tela(self, pyautogui, np, cv2):
        return cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2GRAY)

    def _candidatas(self, k, altura_tela, amplo):
        """Tamanhos a testar. Já achou antes: esse e os vizinhos (vigiar fica leve).
        Ainda não: o esperado (imagens prontas: altura da JANELA DO JOGO / 1440 — ou da tela, se não achar a janela;
        as suas: 1,0) e os vizinhos.
        Na busca ampla (a cada 10 s), sempre testa também os tamanhos ao redor do esperado, mesmo com um tamanho
        já conhecido: se o jogo mudou de tamanho (tela cheia, janela maior ou menor), o modo automático se acerta
        sozinho em vez de ficar procurando para sempre no tamanho antigo (problema de 3/nov/2026)."""
        jogo = tamanho_jogo()
        guardada = self.escalas.get("_tela") or []
        altura = jogo[1] if jogo else (guardada[2] if len(guardada) == 4 else altura_tela)
        prontas = k in (config.ler_config().get("modelos_prontos") or [])
        esperado = round(altura / ALTURA_PRONTAS, 3) if prontas else 1.0
        conhecida = self.escalas.get(k)
        base = conhecida or esperado
        perto = [base, round(base - 0.01, 3), round(base + 0.01, 3)]
        if not conhecida and esperado not in perto:
            perto.append(esperado)
        return perto + ([s for s in sorted(ESCALAS, key=lambda s: abs(s - esperado))[:TESTADAS] if s not in perto] if amplo else [])

    def _achar(self, cv2, tela, k, conf, reducao=1.0, amplo=True, so_escalas=None):
        """Procura o botão na tela em vários tamanhos. Devolve (x, y, largura, altura) na tela real, ou None.
        reducao < 1: `tela` é uma cópia reduzida (vigiar a tela o tempo todo fica mais leve)."""
        modelo = self._modelo(cv2, k)
        if modelo is None:
            return None
        jogo = tamanho_jogo()
        real = [round(tela.shape[0] / reducao), round(tela.shape[1] / reducao)] + ([jogo[1], jogo[0]] if jogo else [])
        antes = self.escalas.get("_tela") or [0, 0]
        if not jogo and len(antes) == 4 and real == antes[:2]:
            # a janela do jogo "sumiu" só nesta conferência (aconteceu dezenas de vezes no registro do Pedro, com o jogo
            # aberto): mesma tela, fica com o tamanho de janela já conhecido em vez de esquecer os tamanhos dos botões
            real = antes
        if len(antes) != len(real) or any(abs(x - y) > 4 for x, y in zip(antes, real)):
            # monitor, resolução ou tamanho da janela do jogo mudou: descobre o tamanho dos botões de novo
            print(f"[auto] tela/janela do jogo mudou ({antes} -> {real}): procurando o tamanho dos botões de novo")
            self.escalas = {"_tela": real}
        melhor = None
        for s in so_escalas or self._candidatas(k, tela.shape[0] / reducao, amplo):
            f = s * reducao
            m = modelo if f == 1.0 else cv2.resize(modelo, None, fx=f, fy=f,
                                                     interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_LINEAR)
            h, w = m.shape[:2]
            if h < 8 or w < 8 or h > tela.shape[0] or w > tela.shape[1]:
                continue
            _, valor, _, pos = cv2.minMaxLoc(cv2.matchTemplate(tela, m, cv2.TM_CCOEFF_NORMED))
            if not melhor or valor > melhor[0]:
                melhor = (valor, pos, w, h, s)
        self.ultima_nota = melhor[0] if melhor else 0.0
        self.ultima_escala = melhor[4] if melhor else None
        if not melhor or melhor[0] < conf:
            return None
        valor, (x, y), w, h, s = melhor
        if self.escalas.get(k) != s:
            self.escalas[k] = s  # guarda o tamanho que funcionou no seu monitor
            cfg = config.ler_config()
            cfg["escala_modelos"] = dict(self.escalas)
            config.salvar_config(cfg)
        return (int(x / reducao), int(y / reducao), int(w / reducao), int(h / reducao))

    @staticmethod
    def _centro(r):
        return (r[0] + r[2] // 2, r[1] + r[3] // 2)

    # -------------------------------------------------------------- o vigia
    def _loop(self):
        try:
            import cv2
            import numpy as np
            import pyautogui  # noqa: importado aqui para o resto do programa funcionar sem ele
        except ImportError:
            self.status = "indisponível"
            self.erro = ("Faltam as bibliotecas do modo automático no Python do programa. Clique em \"Instalar o modo automático\" "
                         f"ou rode num terminal: {comando_instalar()}")
            return
        if self.faltando():
            self.status = "sem modelos"
            self.erro = "Faltam imagens em modelos/: " + ", ".join(self.faltando()) + ". Use \"Usar imagens prontas\" em Ajustes."
            return
        pyautogui.FAILSAFE = True  # leve o mouse ao canto da tela para abortar um clique
        try:  # coordenadas em pixels reais (tela com zoom de 125%, 150%...): a captura, o clique e a cobertura batem
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        guardadas = config.ler_config().get("escala_modelos")
        self.escalas = dict(guardadas) if isinstance(guardadas, dict) else {}
        self.status = "vigiando a tela"
        self.erro = ""
        tratada, visto = False, 0.0  # a tela de resultado atual já foi tratada?
        repetir = None  # depois de uma falha, com a tela de resultado ainda aberta: quando tentar de novo
        voltas = 0
        while not self._parar.is_set():
            voltas += 1
            cfg = config.ler_config()
            if not cfg.get("modo_automatico"):
                self.status = "desligado"
                return
            conf = float(cfg.get("confianca_imagem", 0.85))
            jogo = estado_do_jogo()
            if jogo != "aberto":  # sem jogo na tela não há partida para capturar: não fotografa a tela (leve)
                self.status = "esperando o jogo abrir" if jogo == "fechado" else "jogo minimizado"
                tratada = False
                self._parar.wait(ESPERA_SEM_JOGO)
                continue
            if self.status in ("esperando o jogo abrir", "jogo minimizado"):
                self.status = "vigiando a tela"
            try:
                tela = self._tela(pyautogui, np, cv2)
                pequena = cv2.resize(tela, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                # busca ampla: a cada 10 s enquanto não sabe o tamanho dos botões; sabendo, a cada 30 s (rede de segurança)
                amplo = voltas % (15 if self.escalas.get("battle_log") else 5) == 1
                bl = self._achar(cv2, pequena, "battle_log", conf, reducao=0.5, amplo=amplo)
                if not bl and self.ultima_nota >= QUASE and self.ultima_escala:
                    # na cópia reduzida o botão pequeno perde detalhe: quase achou -> confere na tela inteira, no mesmo tamanho
                    e = self.ultima_escala
                    bl = self._achar(cv2, tela, "battle_log", conf, so_escalas=[e, round(e - 0.01, 3), round(e + 0.01, 3)])
                cont = self._achar(cv2, tela, "continuar", conf) if bl and self._modelo(cv2, "continuar") is not None else None
                resultado = bl and (cont or self._modelo(cv2, "continuar") is None)
                if resultado:
                    visto = time.time()
                    if not tratada:
                        tratada = True
                        antes = coletor.visto_em
                        ok = self._capturar(pyautogui, np, cv2, bl, cont, conf, cfg)
                        repetir = None if ok else {"antes": antes, "n": 0, "em": time.time() + ESPERA_REPETIR}
                    elif repetir and coletor.visto_em > repetir["antes"]:
                        repetir = None  # o log chegou (copiado à mão): nada mais a fazer
                    elif repetir and time.time() >= repetir["em"]:
                        repetir["n"] += 1
                        if self._repetir(pyautogui, np, cv2, bl, conf, repetir["antes"], repetir["n"]) \
                                or repetir["n"] >= MAX_REPETIR:
                            repetir = None
                        else:
                            repetir["em"] = time.time() + ESPERA_REPETIR
                elif tratada and time.time() - visto > SEM_TELA_PARA_SOLTAR:
                    tratada, repetir = False, None  # saiu da tela de resultado: pronto para a próxima partida
            except Exception as e:  # nunca deixa o vigia morrer
                self.erro = f"Erro no modo automático: {e}"
            self._parar.wait(2.0)

    @staticmethod
    def _brilho(tela, r):
        """Brilho médio (0 a 255) da região r = (x, y, largura, altura) da tela. Só um número para o registro:
        a busca dos botões não enxerga se a tela está escurecida (por um aviso do jogo por cima, por exemplo), o brilho sim."""
        x, y, w, h = r
        recorte = tela[max(y, 0):y + h, max(x, 0):x + w]
        return float(recorte.mean()) if recorte.size else 0.0

    def _tentar_copiar(self, pyautogui, np, cv2, bl, conf, antes, rotulo, trazer=True):
        """Uma tentativa: se o log já estiver aberto, só clica em exportar; se não, clica em Battle Log e espera o
        botão de exportar. Devolve (chegou, bl). trazer=False: não rouba a janela ativa (novas tentativas)."""
        tela = self._tela(pyautogui, np, cv2)
        # O log pode já estar aberto (a cópia anterior demorou): clicar em Battle Log de novo fecharia o log
        # (aconteceu 3 vezes no registro do Pedro até 13/11/2026). Então primeiro procura o botão de exportar.
        exp = self._achar(cv2, tela, "exportar", conf)
        ja_aberto = bool(exp)
        brilho = None
        na_frente = jogo_na_frente() or (trazer and trazer_jogo())
        if not na_frente and not trazer:
            return False, bl
        if not exp:
            bl = self._achar(cv2, tela, "battle_log", conf) or bl
            brilho = self._brilho(tela, bl)
            # Com outra janela ativa (o painel, o navegador...), o clique só "acorda" o jogo ou cai na janela errada.
            pyautogui.click(*self._centro(bl))
            for _ in range(12):  # o log pode demorar a abrir (partidas longas)
                time.sleep(0.8)
                exp = self._achar(cv2, self._tela(pyautogui, np, cv2), "exportar", conf)
                if exp:
                    break
        nota = self.ultima_nota
        chegou = False
        if exp:
            pyautogui.click(*self._centro(exp))
            for _ in range(12):  # o coletor olha a área de transferência a cada segundo; log longo demora mais
                time.sleep(0.5)
                if coletor.visto_em > antes:
                    chegou = True
                    break
        # fica em dados/programa.log: se falhar, dá para saber em qual passo (sem guardar imagem da tela)
        extra = " (log já estava aberto)" if ja_aberto else (f", brilho do Battle Log {brilho:.0f}" if brilho is not None else "")
        print(f"[auto] {rotulo}: jogo na frente={na_frente}, botão de exportar achado={bool(exp)} "
              f"(nota {nota:.2f}){extra}, log chegou={chegou}")
        return chegou, bl

    def _capturar(self, pyautogui, np, cv2, bl, cont, conf, cfg):
        """Devolve True se o log chegou (pelo clique ou copiado à mão enquanto o Continue estava coberto)."""
        self.status = "fim de partida detectado"
        antes = coletor.visto_em
        capa = None
        if cont and cfg.get("cobrir_continuar", True):
            from .cobertura import Cobertura
            capa = Cobertura(*cont, texto="Copiando o log… (clique para liberar)")
        try:
            coletor.origem_proxima = "automatico"
            chegou = False
            for tentativa in (1, 2):
                chegou, bl = self._tentar_copiar(pyautogui, np, cv2, bl, conf, antes, f"tentativa {tentativa}")
                if chegou:
                    break
            if chegou:
                self.cliques += 1
                self.erro = ""
                fechar = self._achar(cv2, self._tela(pyautogui, np, cv2), "fechar", conf)
                if fechar:
                    pyautogui.click(*self._centro(fechar))
            else:
                self.perdidas += 1
                coletor.origem_proxima = "area_transferencia"
                self.erro = "Não consegui copiar o log da última partida."
                avisos.avisar("Não consegui copiar o Battle Log desta partida. Antes de clicar em Continue, "
                              "abra o Battle Log e clique no botão de exportar.")
                if capa:  # segura o Continue mais um pouco para dar tempo de copiar à mão
                    capa.texto("Copie o log antes de continuar (clique aqui para liberar)")
                    fim = time.time() + 20
                    while time.time() < fim and not capa.fechada():
                        if coletor.visto_em > antes:  # você copiou à mão: o log chegou, libera o Continue na hora
                            self.cliques += 1
                            self.perdidas -= 1
                            self.erro = ""
                            chegou = True
                            break
                        time.sleep(0.5)
            return chegou
        finally:
            if capa:
                capa.fechar()
            self.status = "vigiando a tela"

    def _repetir(self, pyautogui, np, cv2, bl, conf, antes, n):
        """Nova tentativa, em silêncio, com a tela de resultado ainda aberta depois de uma falha.
        Motivo (registro do Pedro, 02 a 13/11/2026): em 43 de 76 partidas o clique em Battle Log não abriu o log e a
        segunda tentativa, logo em seguida, deu a mesma nota. A busca dos botões não percebe um aviso do jogo escurecendo
        a tela por cima (ela ignora o brilho), então o clique cai no aviso. Quando o aviso some, a nova tentativa acerta.
        Não puxa o jogo para a frente: se você estiver em outra janela, espera você voltar."""
        coletor.origem_proxima = "automatico"
        chegou, _ = self._tentar_copiar(pyautogui, np, cv2, bl, conf, antes, f"nova tentativa {n}", trazer=False)
        if chegou:
            self.cliques += 1
            self.perdidas -= 1
            self.erro = ""
            fechar = self._achar(cv2, self._tela(pyautogui, np, cv2), "fechar", conf)
            if fechar:
                pyautogui.click(*self._centro(fechar))
        else:
            coletor.origem_proxima = "area_transferencia"
        return chegou


auto = AutoExport()
