"""
MODO AUTOMÁTICO (experimental, desligado por padrão).

Olha a tela a cada 2 segundos. Quando a tela de resultado da partida aparece, clica
em "Battle Log" e depois no botão de exportar. O log vai para a área de transferência
e o coletor grava. Ou seja: você termina a partida e ela já está registrada.

Como ele reconhece os botões: por imagens de modelo que VOCÊ recorta da sua tela
(cada computador tem resolução e idioma diferentes). Veja modelos/LEIA-ME.txt.

Ele NÃO lê a memória do jogo, não mexe nos arquivos do jogo e não joga por você:
só reconhece dois botões e clica neles depois que a partida acabou. Mesmo assim,
é automação de cliques no cliente do jogo; use por sua conta e risco.

Precisa de: pip install -r requirements-auto.txt  (pyautogui, opencv-python, pillow)
"""
import threading
import time

from . import config
from .coletor import coletor

MODELOS = {
    "battle_log": "botao_battle_log.png",   # obrigatório: botão "Battle Log" na tela de resultado
    "exportar": "botao_exportar.png",       # obrigatório: botão de exportar/copiar dentro do log
    "fechar": "botao_fechar.png",           # opcional: botão para fechar o log depois
}


class AutoExport:
    def __init__(self):
        self.status = "desligado"
        self.erro = ""
        self.cliques = 0
        self._thread = None
        self._parar = threading.Event()

    def faltando(self):
        return [n for k, n in MODELOS.items() if k != "fechar" and not (config.PASTA_MODELOS / n).exists()]

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="auto_export", daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()
        self.status = "desligado"

    def _achar(self, pyautogui, nome, confianca):
        caminho = str(config.PASTA_MODELOS / nome)
        try:
            return pyautogui.locateCenterOnScreen(caminho, confidence=confianca, grayscale=True)
        except Exception:  # versões novas lançam exceção quando não encontram
            return None

    def _loop(self):
        try:
            import pyautogui  # noqa: importado aqui para o resto do programa funcionar sem ele
            import cv2  # noqa: necessário para o parâmetro "confidence"
        except ImportError:
            self.status = "indisponível"
            self.erro = "Instale as dependências: pip install -r requirements-auto.txt"
            return
        if self.faltando():
            self.status = "sem modelos"
            self.erro = "Faltam imagens em modelos/: " + ", ".join(self.faltando())
            return
        pyautogui.FAILSAFE = True  # leve o mouse ao canto da tela para abortar um clique
        self.status = "vigiando a tela"
        self.erro = ""
        espera_ate = 0
        while not self._parar.is_set():
            cfg = config.ler_config()
            if not cfg.get("modo_automatico"):
                self.status = "desligado"
                return
            conf = float(cfg.get("confianca_imagem", 0.85))
            if time.time() >= espera_ate:
                pos = self._achar(pyautogui, MODELOS["battle_log"], conf)
                if pos:
                    self.status = "fim de partida detectado"
                    pyautogui.click(pos)
                    time.sleep(2.5)
                    exp = None
                    for _ in range(5):
                        exp = self._achar(pyautogui, MODELOS["exportar"], conf)
                        if exp:
                            break
                        time.sleep(1)
                    if exp:
                        coletor.origem_proxima = "automatico"
                        pyautogui.click(exp)
                        self.cliques += 1
                        time.sleep(1.5)
                        if (config.PASTA_MODELOS / MODELOS["fechar"]).exists():
                            fechar = self._achar(pyautogui, MODELOS["fechar"], conf)
                            if fechar:
                                pyautogui.click(fechar)
                    else:
                        self.erro = "Abri o Battle Log mas não achei o botão de exportar. Refaça a imagem botao_exportar.png."
                    espera_ate = time.time() + 45  # não clicar de novo na mesma tela de resultado
                    self.status = "vigiando a tela"
            self._parar.wait(2.0)


auto = AutoExport()
