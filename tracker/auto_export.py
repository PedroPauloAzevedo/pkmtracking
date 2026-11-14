"""
MODO AUTOMÁTICO (experimental, desligado por padrão).

Olha a tela a cada 2 segundos. Quando a tela de resultado da partida aparece, clica
em "Battle Log" e depois no botão de exportar. O log vai para a área de transferência
e o coletor grava. Ou seja: você termina a partida e ela já está registrada.

Como ele reconhece os botões: por imagens de modelo em modelos/. Você pode recortar as suas
(veja modelos/LEIA-ME.txt) ou usar as imagens prontas do projeto Full Bench
(github.com/heatfireash/FullBench, licença MIT), recortadas numa tela 2560x1440.
Por isso a busca testa vários tamanhos e guarda o que deu certo no seu monitor.

Para não perder partidas (algumas ideias do Full Bench):
  - enquanto copia, um quadrinho vermelho cobre o botão Continue (ver cobertura.py);
  - enquanto copia, os seus cliques dentro do jogo ficam segurados por até 20 s (ver trava_mouse.py); clicar no
    quadrinho vermelho solta tudo;
  - ele não segue uma sequência fixa de cliques: a cada volta olha a tela e faz só o passo que falta (desde 2026.11.13-3,
    ver _passo). Se você mesmo abriu o Battle Log, ele só clica em exportar; se você copiou o log, ele não clica mais
    nada; se você fechou o log, ele abre de novo; se você clicou em Continue, ele não clica em lugar nenhum;
  - antes de cada clique, confere numa foto nova se o botão ainda está ali;
  - cada passo tem limite de vezes e de tempo: se não der, avisa (notificação do Windows) e conta como "perdida".

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
ESPERA_COM_TELA = 0.7      # segundos entre uma olhada e outra durante um fim de partida (fora dele, 2 s)
ESPERA_DEPOIS_BATTLE_LOG = 6.0  # depois de clicar em Battle Log, espera o log abrir antes de clicar de novo
ESPERA_DEPOIS_EXPORTAR = 5.0    # depois de clicar em exportar, espera a cópia chegar antes de clicar de novo
MAX_BATTLE_LOG = 8          # cliques em Battle Log por fim de partida, no máximo (um aviso do jogo por cima engole o clique)
MAX_EXPORTAR = 3            # cliques em exportar por fim de partida, no máximo
LIMITE_TENTATIVAS = 75.0    # segundos tentando sozinho; depois pede para você copiar à mão
LIMITE_TRAVA = 20.0         # segundos, no máximo, com os seus cliques no jogo segurados (ver trava_mouse.py)
SEGURA_CONTINUE = 20.0      # depois do aviso, segundos com o Continue ainda coberto para você copiar à mão
PAUSA_MINIMIZADO = 180.0    # jogo minimizado no meio da cópia: espera você voltar por até 3 minutos


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


def retangulo_jogo():
    """(x, y, largura, altura) da área do jogo na tela, ou None (minimizada, fechada ou fora do Windows)."""
    h = _janela_do_jogo()
    if not h:
        return None
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    r, p = wintypes.RECT(), wintypes.POINT(0, 0)
    if not u.GetClientRect(h, ctypes.byref(r)) or r.bottom < 100 or not u.ClientToScreen(h, ctypes.byref(p)):
        return None
    return p.x, p.y, r.right, r.bottom


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
    def _ver(self, cv2, tela, pequena, k, conf, amplo):
        """Procura o botão k na cópia reduzida da tela; se quase achou, confere na tela inteira no mesmo tamanho."""
        if self._modelo(cv2, k) is None:
            return None
        r = self._achar(cv2, pequena, k, conf, reducao=0.5, amplo=amplo)
        if not r and self.ultima_nota >= QUASE and self.ultima_escala:
            # na cópia reduzida o botão pequeno perde detalhe: quase achou -> confere na tela inteira, no mesmo tamanho
            e = self.ultima_escala
            r = self._achar(cv2, tela, k, conf, so_escalas=[e, round(e - 0.01, 3), round(e + 0.01, 3)])
        return r

    def _confirmar(self, pyautogui, np, cv2, k, r, conf):
        """Foto nova, só em volta do botão, logo antes de clicar: o botão ainda está ali? Evita clicar "no vazio" quando
        você mudou de tela (clicou em Continue, fechou o log) entre a foto anterior e o clique."""
        e = self.escalas.get(k)
        modelo = self._modelo(cv2, k)
        if modelo is None or not e:
            return False
        tela = self._tela(pyautogui, np, cv2)
        m = cv2.resize(modelo, None, fx=e, fy=e, interpolation=cv2.INTER_AREA if e < 1 else cv2.INTER_LINEAR)
        folga = 24
        x0, y0 = max(r[0] - folga, 0), max(r[1] - folga, 0)
        recorte = tela[y0:r[1] + r[3] + folga, x0:r[0] + r[2] + folga]
        if recorte.shape[0] < m.shape[0] or recorte.shape[1] < m.shape[1]:
            return False
        return cv2.minMaxLoc(cv2.matchTemplate(recorte, m, cv2.TM_CCOEFF_NORMED))[1] >= conf

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
        ep = None        # o fim de partida em andamento (ver _passo)
        so_log = 0       # voltas seguidas vendo o log aberto sem ter visto a tela de resultado
        fim_ultimo = 0.0  # quando terminou o último fim de partida
        voltas = 0
        try:
            while not self._parar.is_set():
                voltas += 1
                cfg = config.ler_config()
                if not cfg.get("modo_automatico"):
                    self.status = "desligado"
                    return
                conf = float(cfg.get("confianca_imagem", 0.85))
                jogo = estado_do_jogo()
                if jogo != "aberto":  # sem jogo na tela não há partida para capturar: não fotografa a tela (leve)
                    if ep:
                        # Minimizado no meio da cópia: pausa (solta o mouse) e continua quando você voltar ao jogo; o relógio
                        # de "tela sumiu" (12 s) fica parado. Jogo fechado, ou minimizado por muito tempo: encerra.
                        ep.setdefault("pausado_em", time.time())
                        if jogo == "fechado" or time.time() - ep["pausado_em"] > PAUSA_MINIMIZADO:
                            ep = self._encerrar(ep, "o jogo foi fechado" if jogo == "fechado" else "o jogo ficou minimizado")
                            fim_ultimo = time.time()
                        else:
                            self._soltar(ep)
                            ep["visto"] = time.time()
                    self.status = "esperando o jogo abrir" if jogo == "fechado" else "jogo minimizado"
                    self._parar.wait(ESPERA_SEM_JOGO)
                    continue
                if self.status in ("esperando o jogo abrir", "jogo minimizado"):
                    self.status = "vigiando a tela"
                try:
                    tela = self._tela(pyautogui, np, cv2)
                    pequena = cv2.resize(tela, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                    # busca ampla: a cada 10 s enquanto não sabe o tamanho dos botões; sabendo, a cada 30 s (rede de segurança)
                    amplo = voltas % (15 if self.escalas.get("battle_log") else 5) == 1
                    bl = self._ver(cv2, tela, pequena, "battle_log", conf, amplo)
                    cont = self._achar(cv2, tela, "continuar", conf) if bl and self._modelo(cv2, "continuar") is not None else None
                    resultado = bool(bl and (cont or self._modelo(cv2, "continuar") is None))
                    # O log aberto (botão de exportar) só é procurado perto de um fim de partida: o mesmo ícone pode
                    # existir em outras telas do jogo, e clicar nele trocaria o que você copiou.
                    exp = None
                    # sem fim de partida em andamento, procura a cada 2 voltas (fica leve durante o jogo); achou uma vez,
                    # confere na volta seguinte também
                    procurou = bool(ep or resultado or so_log or (voltas % 2 == 0 and time.time() - fim_ultimo > SEM_TELA_PARA_SOLTAR))
                    if procurou:
                        exp = self._ver(cv2, tela, pequena, "exportar", conf, amplo and (ep or resultado))
                    if ep is None:
                        if resultado:
                            ep = self._comecar(cfg, cont, so_log=False)
                            so_log = 0
                        elif exp:
                            # você abriu o Battle Log antes de o modo automático ver a tela de resultado. Só conta se o log
                            # aparece em 2 voltas seguidas e, havendo a imagem do botão de fechar, com ele junto.
                            fechar_ok = self._modelo(cv2, "fechar") is None or self._ver(cv2, tela, pequena, "fechar", conf, False)
                            so_log = so_log + 1 if fechar_ok else 0
                            if so_log >= 2:
                                ep = self._comecar(cfg, None, so_log=True)
                                so_log = 0
                        elif procurou:
                            so_log = 0
                    if ep and self._passo(ep, pyautogui, np, cv2, tela, bl if resultado else None, exp, conf):
                        ep = None
                        fim_ultimo = time.time()
                except Exception as e:  # nunca deixa o vigia morrer
                    self.erro = f"Erro no modo automático: {e}"
                self._parar.wait(ESPERA_COM_TELA if ep else 2.0)
        finally:
            if ep:
                self._encerrar(ep, "o modo automático foi desligado")

    @staticmethod
    def _brilho(tela, r):
        """Brilho médio (0 a 255) da região r = (x, y, largura, altura) da tela. Só um número para o registro:
        a busca dos botões não enxerga se a tela está escurecida (por um aviso do jogo por cima, por exemplo), o brilho sim."""
        x, y, w, h = r
        recorte = tela[max(y, 0):y + h, max(x, 0):x + w]
        return float(recorte.mean()) if recorte.size else 0.0

    # -------------------------------------------------------------- um fim de partida, passo a passo
    def _comecar(self, cfg, cont, so_log):
        """Viu a tela de resultado (ou o log já aberto): começa a cuidar deste fim de partida."""
        agora = time.time()
        ep = {"inicio": agora, "visto": agora, "antes": coletor.visto_em, "so_log": so_log, "feito": False,
              "avisado": False, "trouxe": False, "cliques_bl": 0, "cliques_exp": 0, "ultimo": 0.0, "ultimo_exp": 0.0, "capa": None,
              "trava": None, "aviso_em": 0.0}
        self.status = "fim de partida detectado"
        print(f"[auto] fim de partida detectado{' (com o log já aberto por você)' if so_log else ''}")
        if cont and cfg.get("cobrir_continuar", True):
            from .cobertura import Cobertura
            ep["capa"] = Cobertura(*cont, texto="Copiando o log… (clique aqui para liberar)")
        jogo = retangulo_jogo()
        if jogo and cfg.get("travar_mouse", True):
            from .trava_mouse import TravaMouse
            livre = ep["capa"]._geo if ep["capa"] and getattr(ep["capa"], "_geo", None) else None
            ep["trava"] = TravaMouse(jogo, livre, maximo=LIMITE_TRAVA)
        return ep

    def _soltar(self, ep):
        if ep["trava"]:
            if ep["trava"].seguradas:
                print(f"[auto] trava do mouse segurou {ep['trava'].seguradas} clique(s) seu(s) no jogo")
            ep["trava"].soltar()
            ep["trava"] = None

    def _passo(self, ep, pyautogui, np, cv2, tela, bl, exp, conf):
        """Uma volta do fim de partida. Olha o que está na tela AGORA e faz só o passo seguinte:
          - o log chegou na área de transferência (por você ou por ele)  -> pronto, não clica mais nada;
          - log aberto (botão de exportar na tela)                       -> clica em exportar;
          - tela de resultado com o log fechado                          -> clica em Battle Log;
          - nenhuma das duas por 12 s (você clicou em Continue, por exemplo) -> encerra; se o log não veio, avisa.
        Antes de cada clique, confere de novo se o botão ainda está ali. Cada passo tem limite de vezes e de tempo:
        nunca fica esperando para sempre. Devolve True quando este fim de partida acabou."""
        agora = time.time()
        ep.pop("pausado_em", None)  # o jogo está aberto: a pausa (se havia) acabou
        if bl or exp:
            ep["visto"] = agora
        if not ep["feito"] and coletor.visto_em > ep["antes"]:
            ep["feito"] = True
            por_mim = ep["cliques_exp"] > 0
            print(f"[auto] log chegou ({'pelo botão de exportar' if por_mim else 'copiado por você'}) "
                  f"em {agora - ep['inicio']:.0f} s")
            if por_mim or ep["avisado"]:
                self.cliques += 1
            self.erro = ""
            coletor.origem_proxima = "area_transferencia"
            self._soltar(ep)
            if ep["capa"]:
                ep["capa"].fechar()
            if ep["cliques_bl"] and exp:  # foi ele quem abriu o log: fecha (se tiver a imagem do botão de fechar)
                fechar = self._achar(cv2, tela, "fechar", conf)
                if fechar and self._confirmar(pyautogui, np, cv2, "fechar", fechar, conf) and jogo_na_frente():
                    pyautogui.click(*self._centro(fechar))
            self.status = "vigiando a tela"
        if agora - ep["visto"] > SEM_TELA_PARA_SOLTAR:
            self._encerrar(ep, "a tela de resultado e o log sumiram antes da cópia")
            return True
        if ep["feito"]:
            return False
        if ep["trava"] and not ep["trava"].ativa():
            self._soltar(ep)
        if ep["capa"] and ep["capa"].fechada() and ep["trava"]:
            self._soltar(ep)  # você clicou no quadrinho vermelho: solta o mouse também
        # Clicar? Só com o jogo na frente. Puxa o jogo para a frente uma vez só; depois espera você voltar.
        na_frente = jogo_na_frente()
        if not na_frente and not ep["trouxe"]:
            ep["trouxe"] = True
            na_frente = trazer_jogo()
        if na_frente and not ep["avisado"]:
            if exp and agora - ep["ultimo_exp"] >= ESPERA_DEPOIS_EXPORTAR and ep["cliques_exp"] < MAX_EXPORTAR:
                if self._confirmar(pyautogui, np, cv2, "exportar", exp, conf) and jogo_na_frente():
                    coletor.origem_proxima = "automatico"
                    pyautogui.click(*self._centro(exp))
                    ep["cliques_exp"] += 1
                    ep["ultimo"] = ep["ultimo_exp"] = time.time()
                    self.status = "copiando o log"
                    print(f"[auto] clique em exportar ({ep['cliques_exp']}ª vez)")
            elif bl and not exp and not ep["so_log"] and agora - ep["ultimo"] >= ESPERA_DEPOIS_BATTLE_LOG \
                    and ep["cliques_bl"] < MAX_BATTLE_LOG:
                if self._confirmar(pyautogui, np, cv2, "battle_log", bl, conf) and jogo_na_frente():
                    pyautogui.click(*self._centro(bl))
                    ep["cliques_bl"] += 1
                    ep["ultimo"] = time.time()
                    self.status = "abrindo o Battle Log"
                    print(f"[auto] clique em Battle Log ({ep['cliques_bl']}ª vez; brilho do botão "
                          f"{self._brilho(tela, bl):.0f}; nota {self.ultima_nota:.2f})")
        # Desistir de clicar: tentou o bastante (ou passou do tempo). Pede para você copiar e segura o Continue mais um pouco.
        esgotou = (ep["cliques_bl"] >= MAX_BATTLE_LOG or ep["cliques_exp"] >= MAX_EXPORTAR) \
            and agora - ep["ultimo"] >= ESPERA_DEPOIS_EXPORTAR
        if not ep["avisado"] and (esgotou or agora - ep["inicio"] > LIMITE_TENTATIVAS):
            ep["avisado"] = True
            ep["aviso_em"] = agora
            self.status = "esperando você copiar o log"
            self.erro = "Não consegui copiar o log da última partida."
            coletor.origem_proxima = "area_transferencia"
            self._soltar(ep)
            print(f"[auto] não consegui copiar sozinho ({ep['cliques_bl']} clique(s) em Battle Log, "
                  f"{ep['cliques_exp']} em exportar); pedindo para copiar à mão")
            avisos.avisar("Não consegui copiar o Battle Log desta partida. Antes de clicar em Continue, "
                          "abra o Battle Log e clique no botão de exportar.")
            if ep["capa"]:
                ep["capa"].texto("Copie o log antes de continuar (clique aqui para liberar)")
        if ep["avisado"] and ep["capa"] and agora - ep["aviso_em"] > SEGURA_CONTINUE:
            ep["capa"].fechar()
        return False

    def _encerrar(self, ep, motivo):
        """Fim deste fim de partida: solta o mouse, tira o quadrinho e, se o log não veio, conta como perdida e avisa."""
        self._soltar(ep)
        if ep["capa"]:
            ep["capa"].fechar()
        if not ep["feito"] and coletor.visto_em > ep["antes"]:
            ep["feito"] = True  # chegou na última hora
            self.cliques += 1
        if not ep["feito"]:
            self.perdidas += 1
            self.erro = "Não consegui copiar o log da última partida."
            print(f"[auto] partida NÃO copiada: {motivo}")
            if not ep["avisado"]:
                avisos.avisar("Esta partida não foi copiada: a tela de resultado fechou antes de copiar o Battle Log.")
        coletor.origem_proxima = "area_transferencia"
        self.status = "vigiando a tela"
        return None


auto = AutoExport()
