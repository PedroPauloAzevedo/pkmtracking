"""
ATALHOS DO WINDOWS: "Coletor TCG Live" na Área de Trabalho e na pasta Inicializar.

  - Área de Trabalho: dois cliques abrem o programa (ou só o painel, se ele já estiver aberto).
  - Inicializar: o programa abre sozinho, sem janela, quando o computador liga.

Os atalhos apontam para o pythonw.exe da pasta .venv (abre sem janela preta) e usam o
ícone web/icone.ico. Só existem no Windows.
"""
import subprocess
import sys
from pathlib import Path

from . import config

NOME = "Coletor TCG Live.lnk"
PASTAS = {"area": 0x10, "inicializar": 0x07}  # códigos do Windows: Área de Trabalho e Inicializar


def disponivel():
    return sys.platform == "win32"


def _python_sem_janela():
    exe = Path(sys.executable)
    w = exe.with_name("pythonw.exe")
    return w if w.exists() else exe


def _pasta(onde):
    """Pergunta ao Windows onde fica a pasta (a Área de Trabalho pode estar dentro do OneDrive e ter acento)."""
    import ctypes
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.shell32.SHGetFolderPathW(None, PASTAS[onde], None, 0, buf) != 0:
        raise RuntimeError("Não encontrei a pasta da Área de Trabalho do Windows.")
    return Path(buf.value)


def existe(onde):
    if not disponivel():
        return False
    try:
        return (_pasta(onde) / NOME).exists()
    except Exception:
        return False


def criar(onde):
    """Cria (ou refaz) o atalho. onde = 'area' ou 'inicializar'. Devolve o caminho do atalho."""
    if not disponivel():
        raise RuntimeError("Atalhos só existem no Windows.")
    destino = _pasta(onde) / NOME
    args = "app.py" + (" --sem-navegador" if onde == "inicializar" else "")
    def aspas(x):
        return "'" + str(x).replace("'", "''") + "'"  # texto entre aspas simples no PowerShell
    comando = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut({aspas(destino)});"
               f"$s.TargetPath={aspas(_python_sem_janela())};$s.Arguments={aspas(args)};"
               f"$s.WorkingDirectory={aspas(config.RAIZ)};$s.IconLocation={aspas(config.RAIZ / 'web' / 'icone.ico')};"
               f"$s.Description='Coletor de partidas do Pokémon TCG Live';$s.Save()")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0 or not destino.exists():
        raise RuntimeError(f"Não consegui criar o atalho. {r.stderr.strip()[:300]}")
    return destino


def remover(onde):
    if disponivel():
        (_pasta(onde) / NOME).unlink(missing_ok=True)
