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
  - se o log não chegar, tenta mais uma vez;
  - se ainda assim não chegar, avisa (notificação do Windows) e conta como "perdida".

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
        """Tamanhos a testar. Já achou antes: só esse e os vizinhos (vigiar fica leve).
        Ainda não: o esperado para a sua tela (imagens prontas: altura da tela / 1440; as suas: 1,0)
        e, na busca ampla, os tamanhos ao redor dele."""
        conhecida = self.escalas.get(k)
        if conhecida:
            return [conhecida, round(conhecida - 0.01, 3), round(conhecida + 0.01, 3)]
        prontas = k in (config.ler_config().get("modelos_prontos") or [])
        esperado = round(altura_tela / ALTURA_PRONTAS, 3) if prontas else 1.0
        perto = [esperado, round(esperado - 0.01, 3), round(esperado + 0.01, 3)]
        return perto + (sorted(ESCALAS, key=lambda s: abs(s - esperado))[:TESTADAS] if amplo else [])

    def _achar(self, cv2, tela, k, conf, reducao=1.0, amplo=True):
        """Procura o botão na tela em vários tamanhos. Devolve (x, y, largura, altura) na tela real, ou None.
        reducao < 1: `tela` é uma cópia reduzida (vigiar a tela o tempo todo fica mais leve)."""
        modelo = self._modelo(cv2, k)
        if modelo is None:
            return None
        real = [round(tela.shape[0] / reducao), round(tela.shape[1] / reducao)]
        antes = self.escalas.get("_tela") or [0, 0]
        if abs(antes[0] - real[0]) > 4 or abs(antes[1] - real[1]) > 4:  # monitor ou resolução mudou: descobre de novo
            self.escalas = {"_tela": real}
        melhor = None
        for s in self._candidatas(k, tela.shape[0] / reducao, amplo):
            f = s * reducao
            m = modelo if f == 1.0 else cv2.resize(modelo, None, fx=f, fy=f,
                                                     interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_LINEAR)
            h, w = m.shape[:2]
            if h < 8 or w < 8 or h > tela.shape[0] or w > tela.shape[1]:
                continue
            _, valor, _, pos = cv2.minMaxLoc(cv2.matchTemplate(tela, m, cv2.TM_CCOEFF_NORMED))
            if not melhor or valor > melhor[0]:
                melhor = (valor, pos, w, h, s)
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
        voltas = 0
        while not self._parar.is_set():
            voltas += 1
            cfg = config.ler_config()
            if not cfg.get("modo_automatico"):
                self.status = "desligado"
                return
            conf = float(cfg.get("confianca_imagem", 0.85))
            try:
                tela = self._tela(pyautogui, np, cv2)
                pequena = cv2.resize(tela, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                bl = self._achar(cv2, pequena, "battle_log", conf, reducao=0.5, amplo=voltas % 5 == 1)
                cont = self._achar(cv2, tela, "continuar", conf) if bl and self._modelo(cv2, "continuar") is not None else None
                resultado = bl and (cont or self._modelo(cv2, "continuar") is None)
                if resultado:
                    visto = time.time()
                    if not tratada:
                        tratada = True
                        self._capturar(pyautogui, np, cv2, bl, cont, conf, cfg)
                elif tratada and time.time() - visto > SEM_TELA_PARA_SOLTAR:
                    tratada = False  # saiu da tela de resultado: pronto para a próxima partida
            except Exception as e:  # nunca deixa o vigia morrer
                self.erro = f"Erro no modo automático: {e}"
            self._parar.wait(2.0)

    def _capturar(self, pyautogui, np, cv2, bl, cont, conf, cfg):
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
                if tentativa == 2:  # o log pode ter fechado: procura o botão Battle Log de novo
                    bl = self._achar(cv2, self._tela(pyautogui, np, cv2), "battle_log", conf) or bl
                pyautogui.click(*self._centro(bl))
                exp = None
                for _ in range(6):
                    time.sleep(0.8)
                    exp = self._achar(cv2, self._tela(pyautogui, np, cv2), "exportar", conf)
                    if exp:
                        break
                if exp:
                    pyautogui.click(*self._centro(exp))
                    for _ in range(8):  # o coletor olha a área de transferência a cada segundo
                        time.sleep(0.5)
                        if coletor.visto_em > antes:
                            chegou = True
                            break
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
                    capa.esperar_fechar(20)
        finally:
            if capa:
                capa.fechar()
            self.status = "vigiando a tela"


auto = AutoExport()
