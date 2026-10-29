"""
ATUALIZADOR: baixa a versão mais nova do programa direto do GitHub.

Como funciona:
  1. O arquivo versao.txt no GitHub diz qual é a versão publicada.
  2. Se for mais nova que a sua, o painel mostra o aviso "Nova versão disponível".
  3. Ao clicar em Atualizar, o programa baixa o código (zip do GitHub), substitui só os
     arquivos do programa e se reinicia. NUNCA mexe em dados/ (suas partidas, decks,
     cartas), em .venv/ nem nas imagens que você colocou em modelos/.

Repositório público: não precisa de nada além do nome (ex.: seu-usuario/tcg-tracker).
Repositório privado: crie um token de leitura no GitHub e cole em Ajustes > Atualizações.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile

import requests

from . import config

ARQ_VERSAO = config.RAIZ / "versao.txt"
NUNCA_SUBSTITUIR = {"dados", ".venv", ".git"}
estado = {"atual": None, "remota": None, "disponivel": False, "verificado_em": None, "erro": "", "atualizando": False, "mensagem": ""}


def versao_local():
    try:
        return ARQ_VERSAO.read_text(encoding="utf-8").strip()
    except OSError:
        return "0"


def _como_tupla(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "0"))


def _cabecalhos(cfg):
    h = {"User-Agent": "TCGLiveTracker/1.0", "Accept": "application/vnd.github+json"}
    if cfg.get("github_token"):
        h["Authorization"] = f"Bearer {cfg['github_token']}"
    return h


def verificar():
    cfg = config.ler_config()
    repo, ramo = (cfg.get("github_repo") or "").strip(), cfg.get("github_ramo") or "main"
    estado.update({"atual": versao_local(), "erro": ""})
    if not repo:
        estado.update({"remota": None, "disponivel": False, "erro": "Informe o repositório do GitHub em Ajustes > Atualizações."})
        return estado
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/contents/versao.txt?ref={ramo}",
                         headers={**_cabecalhos(cfg), "Accept": "application/vnd.github.raw"}, timeout=20)
        if r.status_code == 404:
            raise RuntimeError("Repositório ou versao.txt não encontrado. Confira o nome (usuario/repositorio) e, se for privado, o token.")
        if r.status_code in (401, 403):
            raise RuntimeError("O GitHub recusou o acesso. Se o repositório é privado, confira o token.")
        r.raise_for_status()
        remota = r.text.strip()
        estado.update({"remota": remota, "disponivel": _como_tupla(remota) > _como_tupla(estado["atual"]),
                       "verificado_em": time.strftime("%d/%m %H:%M")})
    except (requests.RequestException, RuntimeError) as e:
        estado["erro"] = str(e)
    return estado


def atualizar():
    """Baixa, substitui os arquivos do programa, instala dependências novas e reinicia."""
    cfg = config.ler_config()
    repo, ramo = (cfg.get("github_repo") or "").strip(), cfg.get("github_ramo") or "main"
    estado.update({"atualizando": True, "mensagem": "Baixando a versão nova…", "erro": ""})
    try:
        r = requests.get(f"https://api.github.com/repos/{repo}/zipball/{ramo}", headers=_cabecalhos(cfg), timeout=120)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            raiz_zip = z.namelist()[0].split("/")[0]
            for item in z.infolist():
                partes = item.filename.split("/")[1:]
                if not partes or not partes[-1] or partes[0] in NUNCA_SUBSTITUIR:
                    continue
                destino = config.RAIZ.joinpath(*partes)
                if partes[0] == "modelos" and destino.exists():
                    continue  # mantém as imagens de botão que você já tem
                destino.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as origem, open(destino, "wb") as saida:
                    shutil.copyfileobj(origem, saida)
        estado["mensagem"] = "Instalando dependências…"
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(config.RAIZ / "requirements.txt")],
                       check=False, timeout=600)
        estado["mensagem"] = "Atualizado. Reiniciando…"
        threading.Thread(target=_reiniciar, daemon=True).start()
    except Exception as e:
        estado.update({"erro": f"Não consegui atualizar: {e}", "atualizando": False})


def _reiniciar():
    time.sleep(1.5)
    args = [sys.executable, str(config.RAIZ / "app.py"), "--sem-navegador"]
    if os.name == "nt":
        subprocess.Popen(args, cwd=str(config.RAIZ), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    else:
        subprocess.Popen(args, cwd=str(config.RAIZ))
    os._exit(0)


class Verificador:
    def iniciar(self):
        threading.Thread(target=self._loop, daemon=True, name="atualizacoes").start()

    def _loop(self):
        time.sleep(10)
        while True:
            if config.ler_config().get("github_repo"):
                verificar()
            time.sleep(6 * 3600)


verificador = Verificador()
