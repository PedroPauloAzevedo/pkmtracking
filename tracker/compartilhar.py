"""
COMPARTILHAR LOGS ENTRE AMIGOS

Exportar (quem manda): junta as SUAS partidas num arquivo .zip
  - logs/<data>_<hash>.txt  -> o log exatamente como o jogo exportou
  - coletor-logs.json       -> quem é o dono (nick), versão e, para cada log, a data e as
                               correções que você fez (seu deck, deck do adversário, tags, notas)
  Logs que você recebeu de outros amigos nunca entram no seu arquivo.

Importar (quem recebe): lê o .zip (ou arquivos .txt soltos) e grava cada partida marcada com o
nick do dono. Logs repetidos são ignorados, então pode importar o mesmo arquivo de novo sem
contar nada duas vezes. Nas telas, o filtro "Jogador" escolhe de quem ver as partidas.
"""
import io
import json
import os
import platform
import re
import subprocess
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import banco, config, leitor

FORMATO = "coletor-tcg-live-logs"
MANIFESTO = "coletor-logs.json"
_DATA_NOME = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})")


def _minhas(desde=None):
    sql = "SELECT id, hash, capturada_em, origem, texto, meu_deck, deck_adv, tags, notas FROM partidas WHERE COALESCE(dono,'')=''"
    params = ()
    if desde:
        sql += " AND capturada_em > ?"
        params = (desde,)
    return banco.consultar(sql + " ORDER BY capturada_em", params)


def resumo_exportacao():
    cfg = config.ler_config()
    ultima = cfg.get("ultima_exportacao") or ""
    return {"nick": _meu_nick(), "total": len(_minhas()), "novas": len(_minhas(ultima)) if ultima else None,
            "ultima_exportacao": ultima}


def _meu_nick():
    from . import analises
    return analises.descobrir_eu(banco.listar_partidas(), config.ler_config()["nick"])


def montar_zip(so_novas=False, marcar=True):
    """Devolve (nome_do_arquivo, bytes do zip, quantidade de partidas)."""
    cfg = config.ler_config()
    nick = _meu_nick()
    if not nick:
        raise ValueError("Informe seu nick do TCG Live no Painel (ou em Ajustes) antes de exportar.")
    desde = cfg.get("ultima_exportacao") if so_novas else None
    linhas = _minhas(desde)
    if not linhas:
        raise ValueError("Nenhuma partida nova desde o último envio." if so_novas else "Você ainda não tem partidas para exportar.")
    agora = datetime.now()
    arquivos = {}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in linhas:
            nome = f"logs/{p['capturada_em'].replace('T', '_').replace(':', '')[:17]}_{p['hash'][:6]}.txt"
            z.writestr(nome, p["texto"])
            arquivos[nome] = {"capturada_em": p["capturada_em"], "origem": p["origem"],
                              **{k: p[k] for k in ("meu_deck", "deck_adv", "tags", "notas") if p[k]}}
        z.writestr(MANIFESTO, json.dumps({
            "formato": FORMATO, "versao": 1, "nick": nick, "programa": _versao(),
            "exportado_em": agora.isoformat(timespec="seconds"), "partidas": len(linhas), "arquivos": arquivos,
        }, ensure_ascii=False, indent=1))
    if marcar:  # o envio automático pela pasta não mexe na data do último envio manual
        cfg["ultima_exportacao"] = max(p["capturada_em"] for p in linhas)
        config.salvar_config(cfg)
    seguro = re.sub(r"[^A-Za-z0-9_-]", "_", nick)
    return f"logs-tcg_{seguro}_{agora.strftime('%Y-%m-%d_%H%M')}.zip", buf.getvalue(), len(linhas)


def _versao():
    try:
        return (config.RAIZ / "versao.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def pasta_downloads():
    p = Path.home() / "Downloads"
    return p if p.is_dir() else Path.home()


def exportar_para_downloads(so_novas=False):
    """Salva o .zip na pasta Downloads e abre o Explorer com o arquivo selecionado (pronto para arrastar no WhatsApp/e-mail)."""
    nome, conteudo, n = montar_zip(so_novas)
    destino = pasta_downloads() / nome
    destino.write_bytes(conteudo)
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["explorer", "/select,", str(destino)])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-R", str(destino)])
    except Exception:
        pass
    return {"arquivo": str(destino), "nome": nome, "partidas": n}


# ------------------------------------------------------------------ importar

def _data_do_nome(nome):
    m = _DATA_NOME.search(nome)
    return f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}" if m else None


def ler_envio(arquivos):
    """arquivos: lista de (nome, bytes). Aceita o .zip exportado, um .zip da pasta dados/logs ou .txt soltos.
    Devolve {nick, logs: [(nome, texto, info)]}."""
    nick, logs = "", []
    for nome, conteudo in arquivos:
        if nome.lower().endswith(".zip") or conteudo[:2] == b"PK":
            try:
                z = zipfile.ZipFile(io.BytesIO(conteudo))
            except zipfile.BadZipFile:
                continue
            info = {}
            if MANIFESTO in z.namelist():
                try:
                    m = json.loads(z.read(MANIFESTO).decode("utf-8"))
                    if m.get("formato") == FORMATO:
                        nick = nick or m.get("nick", "")
                        info = m.get("arquivos") or {}
                except ValueError:
                    pass
            for n in z.namelist():
                if n.lower().endswith(".txt") and not n.endswith("/"):
                    logs.append((n, z.read(n).decode("utf-8", "replace"), info.get(n, {})))
        elif nome.lower().endswith(".txt"):
            logs.append((nome, conteudo.decode("utf-8", "replace"), {}))
    return {"nick": nick, "logs": logs}


def importar(arquivos, nome=""):
    """Grava os logs de um amigo. nome: o nick dele (se vazio, usa o do arquivo exportado)."""
    envio = ler_envio(arquivos)
    regras = config.ler_regras()
    validos = [(n, t, i) for n, t, i in envio["logs"] if leitor.parece_log(t)]
    if not validos:
        raise ValueError("Não encontrei logs do TCG Live nesse arquivo. Peça para o seu amigo usar o botão "
                         "\"Exportar meus logs\" em Programa > Amigos, ou mandar os .txt da pasta dados\\logs.")
    # O dono precisa ser o nick que aparece nos logs: é por ele que o programa sabe quem venceu.
    cont = Counter(j for _, t, _ in validos for j in set(leitor.ler_partida(t, regras)["jogadores"]))
    provavel = cont.most_common(1)[0][0] if cont else ""
    dono = (nome or envio["nick"] or "").strip()
    if dono:
        certo = next((j for j in cont if j.lower() == dono.lower()), None)
        if not certo or cont[certo] < 0.5 * len(validos):
            raise ValueError(f"O nick \"{dono}\" não aparece na maioria desses logs."
                             + (f" O jogador que mais aparece é \"{provavel}\"." if provavel else "")
                             + " Use o nick exatamente como está no jogo.")
        dono = certo
    elif provavel and cont[provavel] >= max(2, int(0.8 * len(validos))):
        dono = provavel
    else:
        raise ValueError("Não consegui descobrir de quem são esses logs. Digite o nick do seu amigo e importe de novo.")
    meu = _meu_nick()
    if meu and dono.lower() == meu.lower():
        raise ValueError(f"Esses logs são seus ({meu}). Logs de amigos precisam ser de outro jogador.")
    novas = repetidas = 0
    for n, texto, info in validos:
        quando = info.get("capturada_em") or _data_do_nome(os.path.basename(n))
        _, nova = banco.inserir_partida(texto, "amigo", regras, dono=dono, capturada_em=quando,
                                        extras={k: info.get(k, "") for k in ("meu_deck", "deck_adv", "tags", "notas")})
        novas += nova
        repetidas += not nova
    return {"nome": dono, "novas": novas, "repetidas": repetidas, "invalidos": len(envio["logs"]) - len(validos)}


def amigos():
    return banco.consultar("SELECT dono AS nome, COUNT(*) AS partidas, MIN(capturada_em) AS primeira, MAX(capturada_em) AS ultima "
                           "FROM partidas WHERE COALESCE(dono,'')!='' GROUP BY dono ORDER BY dono COLLATE NOCASE")


def apagar_amigo(nome):
    with banco.conectar() as con:
        n = con.execute("DELETE FROM partidas WHERE dono=?", (nome,)).rowcount
    return n


# ------------------------------------------------------------------ automático: pasta compartilhada (Google Drive)
#
# Todos apontam o programa para a MESMA pasta compartilhada no Google Drive para computador.
#   - Enviar: de tempos em tempos, se houver partidas suas novas, o programa grava (substituindo)
#     o arquivo  <pasta>/logs-tcg_<seu nick>.zip  com todas as suas partidas.
#   - Receber: lê os .zip dos outros nessa pasta e importa o que mudou desde a última vez.
# O Google Drive cuida de levar o arquivo de um computador para o outro. Nenhuma senha no programa.

import threading
import time

ARQ_VISTOS = config.PASTA_DADOS / "pasta_compartilhada.json"
estado_pasta = {"rodando": False, "ultima": None, "mensagem": "", "erro": "", "enviadas": 0, "importadas": []}


def _vistos():
    try:
        return json.loads(ARQ_VISTOS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sugestoes_pasta():
    """Lugares onde o Google Drive para computador costuma aparecer."""
    casa = Path.home()
    candidatos = [casa / "Google Drive", casa / "Meu Drive", casa / "My Drive"]
    if platform.system() == "Windows":
        for letra in "GHIJKLMNOPQRSTUVWXYZ":
            for nome in ("Meu Drive", "My Drive"):
                candidatos.append(Path(f"{letra}:\\") / nome)
    else:
        nuvem = casa / "Library" / "CloudStorage"
        if nuvem.is_dir():
            for d in nuvem.glob("GoogleDrive-*"):
                candidatos += [d / "Meu Drive", d / "My Drive"]
    saida = []
    for c in candidatos:
        try:
            if c.is_dir():
                saida.append(str(c))
        except OSError:
            pass
    return saida


def escolher_pasta_dialogo():
    """Abre a janela do Windows/macOS para escolher a pasta (roda no seu computador)."""
    resultado = {}

    def abrir():
        try:
            import tkinter
            from tkinter import filedialog
            raiz = tkinter.Tk()
            raiz.withdraw()
            raiz.attributes("-topmost", True)
            resultado["pasta"] = filedialog.askdirectory(title="Escolha a pasta compartilhada do Google Drive") or ""
            raiz.destroy()
        except Exception as e:
            resultado["erro"] = str(e)

    t = threading.Thread(target=abrir)
    t.start()
    t.join(300)
    return resultado


def _nome_arquivo(nick):
    return "logs-tcg_" + (re.sub(r"[^A-Za-z0-9_-]", "_", nick) or "jogador") + ".zip"


def sincronizar_pasta():
    """Uma rodada: envia as suas partidas (se tiver novas) e importa as dos outros."""
    cfg = config.ler_config()
    pasta = Path(cfg.get("pasta_compartilhada") or "")
    if not cfg.get("pasta_compartilhada"):
        raise ValueError("Escolha a pasta compartilhada primeiro.")
    if not pasta.is_dir():
        raise ValueError(f"Não encontrei a pasta {pasta}. O Google Drive para computador está aberto?")
    nick = _meu_nick()
    if not nick:
        raise ValueError("Informe seu nick do TCG Live no Painel antes de ligar o envio automático.")
    meu_arquivo = pasta / _nome_arquivo(nick)
    vistos = _vistos()
    enviadas = 0
    # 1) enviar: regrava o seu arquivo quando há partida nova
    minhas = _minhas()
    marca = f"{len(minhas)}|{minhas[-1]['capturada_em'] if minhas else ''}"
    if minhas and (vistos.get("_enviado") != marca or not meu_arquivo.exists()):
        _, conteudo, enviadas = montar_zip(False, marcar=False)
        temporario = pasta / (meu_arquivo.name + ".tmp")
        temporario.write_bytes(conteudo)
        os.replace(temporario, meu_arquivo)
        vistos["_enviado"] = marca
    # 2) receber: os .zip dos outros que mudaram
    importadas = []
    for arq in sorted(pasta.glob("*.zip")):
        if arq.name == meu_arquivo.name:
            continue
        try:
            st = arq.stat()
        except OSError:
            continue
        assinatura = f"{st.st_size}|{int(st.st_mtime)}"
        if vistos.get(arq.name) == assinatura:
            continue
        if time.time() - st.st_mtime < 20:  # o Drive ainda pode estar baixando
            continue
        try:
            r = importar([(arq.name, arq.read_bytes())])
            importadas.append({"arquivo": arq.name, **r})
            vistos[arq.name] = assinatura
        except ValueError as e:
            if "são seus" in str(e):  # um arquivo seu com outro nome: não reler
                vistos[arq.name] = assinatura
            else:
                importadas.append({"arquivo": arq.name, "erro": str(e)})
        except (OSError, zipfile.BadZipFile) as e:
            importadas.append({"arquivo": arq.name, "erro": f"não consegui ler ({e})"})
    ARQ_VISTOS.write_text(json.dumps(vistos, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"enviadas": enviadas, "importadas": importadas, "meu_arquivo": str(meu_arquivo)}


class SincronizadorPasta:
    """Roda sincronizar_pasta de tempos em tempos enquanto o programa está aberto."""

    def __init__(self):
        self._parar = threading.Event()
        self._agora = threading.Event()
        self._thread = None

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="pasta-compartilhada", daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()
        self._agora.set()

    def agora(self):
        if self._thread and self._thread.is_alive():
            self._agora.set()
        else:
            threading.Thread(target=self.rodar_uma_vez, daemon=True).start()

    def rodar_uma_vez(self):
        if estado_pasta["rodando"]:
            return
        estado_pasta.update(rodando=True, erro="", mensagem="Sincronizando com a pasta compartilhada…")
        try:
            r = sincronizar_pasta()
            novas = sum(x.get("novas", 0) for x in r["importadas"])
            erros = [f"{x['arquivo']}: {x['erro']}" for x in r["importadas"] if x.get("erro")]
            estado_pasta.update(enviadas=r["enviadas"], importadas=r["importadas"], erro="; ".join(erros),
                                mensagem=(f"Enviei {r['enviadas']} partida(s). " if r["enviadas"] else "Nada novo para enviar. ")
                                + (f"Recebi {novas} partida(s) nova(s)." if novas else "Nada novo para receber."))
        except ValueError as e:
            estado_pasta.update(erro=str(e), mensagem="")
        except Exception as e:
            estado_pasta.update(erro=f"Erro inesperado: {e}", mensagem="")
        finally:
            estado_pasta.update(rodando=False, ultima=datetime.now().isoformat(timespec="seconds"))

    def _loop(self):
        self._agora.wait(15)  # deixa o programa abrir primeiro
        self._agora.clear()
        while not self._parar.is_set():
            cfg = config.ler_config()
            if cfg.get("pasta_auto") and cfg.get("pasta_compartilhada"):
                self.rodar_uma_vez()
            minutos = max(5, int(cfg.get("pasta_minutos") or 30))
            self._agora.wait(minutos * 60)
            self._agora.clear()


sincronizador_pasta = SincronizadorPasta()
