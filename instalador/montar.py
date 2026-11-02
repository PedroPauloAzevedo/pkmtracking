"""
MONTAR O INSTALADOR (.exe) DO COLETOR, que não precisa de Python instalado.

Como usar (no Windows, com qualquer Python 3 e o Inno Setup 6 instalados):
    python instalador/montar.py

O que ele faz:
  1. Baixa o Python oficial "portátil" (pacote do NuGet, publicado pela equipe do Python) e guarda
     em instalador/cache/ para não baixar de novo.
  2. Monta a pasta build/ColetorTCG/ com o programa (sem dados/) e esse Python em python/.
  3. Instala ali dentro as bibliotecas de requirements.txt e requirements-auto.txt.
  4. Se o Inno Setup estiver instalado, gera dist/ColetorTCG-Instalador-<versão>.exe.

O instalador põe o programa em %LOCALAPPDATA%\\Programs\\ColetorTCG (sem pedir senha de
administrador), cria os atalhos e abre o Coletor. As atualizações continuam pelo próprio programa:
o atualizador troca os arquivos .py e usa o pip desse Python para instalar o que faltar.
"""
import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PY_VERSAO = "3.15.2"
PY_URL = f"https://api.nuget.org/v3-flatcontainer/python/{PY_VERSAO}/python.{PY_VERSAO}.nupkg"
PY_SHA256 = "294f5ed7ab97148fcbb57b8c06ba428f6d282c2bbaa266dbe3137284497998f0"  # confere o download (ver _conferir)

RAIZ = Path(__file__).resolve().parent.parent
AQUI = RAIZ / "instalador"
CACHE = AQUI / "cache"
SAIDA = RAIZ / "build" / "ColetorTCG"
DIST = RAIZ / "dist"
FORA = {"dados", ".venv", ".git", "build", "dist", "__pycache__", "cache", "testes", "minhas", "instalador"}
ISCC = [Path(p) / "Inno Setup 6" / "ISCC.exe" for p in
        (r"C:\Program Files (x86)", r"C:\Program Files", str(Path.home() / "AppData/Local/Programs"))]


def baixar_python():
    CACHE.mkdir(parents=True, exist_ok=True)
    arq = CACHE / f"python.{PY_VERSAO}.nupkg"
    if not arq.exists():
        print("Baixando o Python", PY_VERSAO, "…")
        urllib.request.urlretrieve(PY_URL, arq)
    _conferir(arq)
    return arq


def _conferir(arq):
    soma = hashlib.sha256(arq.read_bytes()).hexdigest()
    if PY_SHA256 and soma != PY_SHA256:
        arq.unlink()
        sys.exit(f"O arquivo do Python baixado não confere (sha256 {soma}). Rode de novo.")
    if not PY_SHA256:
        print(f"sha256 do Python {PY_VERSAO}: {soma}  (cole em PY_SHA256 para conferir nas próximas vezes)")


def copiar_programa():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)
    for item in RAIZ.iterdir():
        if item.name in FORA or item.name.startswith("."):
            continue
        destino = SAIDA / item.name
        if item.is_dir():
            shutil.copytree(item, destino, ignore=shutil.ignore_patterns(*FORA, "*.pyc"))
        else:
            shutil.copy2(item, destino)


def montar_python(arq):
    pasta = SAIDA / "python"
    with zipfile.ZipFile(arq) as z:
        for info in z.infolist():
            if info.filename.startswith("tools/") and not info.is_dir():
                destino = pasta / info.filename[len("tools/"):]
                destino.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as o, open(destino, "wb") as d:
                    shutil.copyfileobj(o, d)
    py = pasta / "python.exe"
    subprocess.run([str(py), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "--no-warn-script-location", "-q",
                    "-r", str(SAIDA / "requirements.txt"), "-r", str(SAIDA / "requirements-auto.txt")], check=True)
    subprocess.run([str(py), "-c", "import flask, requests, bs4, pystray, PIL, cv2, numpy, pyautogui; print('bibliotecas ok')"],
                   check=True)


def gerar_exe():
    iscc = next((p for p in ISCC if p.exists()), None)
    versao = (RAIZ / "versao.txt").read_text(encoding="utf-8").strip()
    if not iscc:
        print("\nPasta pronta em", SAIDA)
        print("Para gerar o .exe, instale o Inno Setup 6 (https://jrsoftware.org/isinfo.php ou "
              "'winget install JRSoftware.InnoSetup') e rode este script de novo.")
        return None
    DIST.mkdir(exist_ok=True)
    subprocess.run([str(iscc), f"/DVersao={versao}", f"/DOrigem={SAIDA}", f"/O{DIST}", str(AQUI / "coletor.iss")], check=True)
    exe = DIST / f"ColetorTCG-Instalador-{versao}.exe"
    print("\nInstalador pronto:", exe, f"({exe.stat().st_size / 1e6:.0f} MB)")
    return exe


if __name__ == "__main__":
    arq = baixar_python()
    copiar_programa()
    montar_python(arq)
    gerar_exe()
