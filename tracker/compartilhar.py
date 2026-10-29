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


def montar_zip(so_novas=False):
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
