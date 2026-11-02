"""
JANELA: abre o painel numa janela própria, sem abas nem barra de endereço.

Usa o modo "aplicativo" do Microsoft Edge (que já vem no Windows) ou do Google Chrome, com
uma pasta de perfil só do Coletor (dados/janela). Nada para instalar.
Sem Edge/Chrome, ou com "abrir_em" = "navegador" em Ajustes, abre uma aba no navegador padrão.
"""
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from . import config


def _navegador_app():
    if sys.platform != "win32":
        return None
    bases = [os.environ.get(v) for v in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    for base in filter(None, bases):
        for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
            exe = Path(base) / rel
            if exe.exists():
                return exe
    return None


def disponivel():
    return _navegador_app() is not None


def abrir(url):
    exe = _navegador_app() if config.ler_config().get("abrir_em", "janela") == "janela" else None
    if exe:
        try:
            subprocess.Popen([str(exe), f"--app={url}", f"--user-data-dir={config.PASTA_DADOS / 'janela'}",
                              "--window-size=1320,880", "--no-first-run", "--no-default-browser-check"])
            return
        except OSError as e:
            print("[janela] não consegui abrir a janela própria:", e)
    webbrowser.open(url)
