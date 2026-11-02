"""
Banco de dados local (SQLite, um único arquivo em dados/tracker.db).

Dá para abrir esse arquivo no DB Browser for SQLite, no Power BI ou no Excel
(via conector ODBC) se você quiser fazer análises por fora.
"""
import hashlib
import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from . import config, leitor

_trava = threading.Lock()
VERSAO_LEITOR = 3  # aumente quando o leitor passar a tirar mais informação dos logs: as partidas gravadas são relidas

ESQUEMA = """
CREATE TABLE IF NOT EXISTS partidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE,
    capturada_em TEXT,
    origem TEXT,            -- area_transferencia, automatico, manual, arquivo
    arquivo TEXT,           -- cópia .txt em dados/logs
    texto TEXT,
    dados_json TEXT,        -- resultado do leitor (refeito quando as regras mudam)
    meu_deck TEXT DEFAULT '',   -- se preenchido, substitui o palpite automático
    deck_adv TEXT DEFAULT '',
    notas TEXT DEFAULT '',
    tags TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS torneios (
    id TEXT PRIMARY KEY,    -- id do Limitless Labs, ex.: 0078
    nome TEXT, data TEXT, jogadores INTEGER, rk9 TEXT, importado_em TEXT, info_json TEXT
);
CREATE TABLE IF NOT EXISTS t_jogadores (
    torneio TEXT, labs_id TEXT, nome TEXT, nome_norm TEXT, pais TEXT,
    posicao INTEGER, pontos INTEGER, v INTEGER, d INTEGER, e INTEGER, arquetipo TEXT
);
CREATE TABLE IF NOT EXISTS t_partidas (
    torneio TEXT, rodada INTEGER, mesa TEXT,
    j1 TEXT, j2 TEXT, res1 TEXT,     -- res1 = resultado do jogador 1: W, L ou T
    arq1 TEXT, arq2 TEXT
);
CREATE TABLE IF NOT EXISTS t_listas (
    torneio TEXT, labs_id TEXT, carta TEXT, set_code TEXT, numero TEXT, qtd INTEGER,
    carta_id TEXT DEFAULT '',   -- arte básica (TCGdex) depois do conversor
    carta_base TEXT DEFAULT ''  -- nome da carta na arte básica
);
CREATE TABLE IF NOT EXISTS arquetipos (
    slug TEXT PRIMARY KEY,   -- como o Limitless chama o deck (ex.: dragapult-ex)
    nome TEXT,               -- nome de exibição (ex.: Dragapult)
    icones TEXT,             -- Pokémon do ícone, em JSON (ex.: ["dragapult"])
    atualizado_em TEXT
);
CREATE TABLE IF NOT EXISTS meus_decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT, arquetipo TEXT, lista TEXT, notas TEXT DEFAULT '',
    ativo INTEGER DEFAULT 1, criado_em TEXT, versao_de INTEGER
);
CREATE TABLE IF NOT EXISTS meus_decks_cartas (
    deck_id INTEGER, qtd INTEGER, nome TEXT, set_code TEXT, numero TEXT, secao TEXT,
    carta_id TEXT DEFAULT '', carta_base TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_tj ON t_jogadores(torneio);
CREATE INDEX IF NOT EXISTS ix_tp ON t_partidas(torneio);
CREATE INDEX IF NOT EXISTS ix_tl ON t_listas(torneio, labs_id);
"""


@contextmanager
def conectar():
    con = sqlite3.connect(config.ARQ_BANCO, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def iniciar():
    regras_novas = config.preparar_pastas()
    with conectar() as con:
        con.executescript(ESQUEMA)
        colunas = {r["name"] for r in con.execute("PRAGMA table_info(t_listas)")}
        for col in ("carta_id", "carta_base"):  # bancos criados pela versão anterior
            if col not in colunas:
                con.execute(f"ALTER TABLE t_listas ADD COLUMN {col} TEXT DEFAULT ''")
        if "deck_id" not in {r["name"] for r in con.execute("PRAGMA table_info(partidas)")}:
            con.execute("ALTER TABLE partidas ADD COLUMN deck_id INTEGER")  # lista de "Meus decks" usada
        if "favorito" not in {r["name"] for r in con.execute("PRAGMA table_info(meus_decks)")}:
            con.execute("ALTER TABLE meus_decks ADD COLUMN favorito INTEGER DEFAULT 0")
        if "icones_manual" not in {r["name"] for r in con.execute("PRAGMA table_info(meus_decks)")}:
            con.execute("ALTER TABLE meus_decks ADD COLUMN icones_manual TEXT DEFAULT ''")  # ícones que você corrigiu
        if "lista_oficial" not in {r["name"] for r in con.execute("PRAGMA table_info(meus_decks)")}:
            con.execute("ALTER TABLE meus_decks ADD COLUMN lista_oficial TEXT DEFAULT ''")  # lista oficial editada por você
        if "dono" not in {r["name"] for r in con.execute("PRAGMA table_info(partidas)")}:
            con.execute("ALTER TABLE partidas ADD COLUMN dono TEXT DEFAULT ''")  # vazio = sua; senão, o nick do amigo
        colunas_t = {r["name"] for r in con.execute("PRAGMA table_info(torneios)")}
        if "fonte" not in colunas_t:  # 'labs' (grandes eventos) ou 'online' (play.limitlesstcg.com)
            con.execute("ALTER TABLE torneios ADD COLUMN fonte TEXT DEFAULT 'labs'")
        if "formato" not in colunas_t:  # 'standard' confirmado, '' não confirmado, outro = fora das contas
            con.execute("ALTER TABLE torneios ADD COLUMN formato TEXT DEFAULT ''")
        ace_nova = "ace_spec" not in {r["name"] for r in con.execute("PRAGMA table_info(t_jogadores)")}
        if ace_nova:  # ACE SPEC da lista do jogador: NULL = sem lista (ou ainda não calculada), '' = lista sem ACE SPEC
            con.execute("ALTER TABLE t_jogadores ADD COLUMN ace_spec TEXT")
    if ace_nova:
        atualizar_ace_spec()  # listas já importadas: calcula uma vez
    cfg = config.ler_config()
    if regras_novas or cfg.get("versao_leitor") != VERSAO_LEITOR:  # leitor ou regras novas: relê as partidas já gravadas
        reprocessar_partidas(config.ler_regras())
        cfg["versao_leitor"] = VERSAO_LEITOR
        config.salvar_config(cfg)
    separar_partidas_de_outros()


# ---------------------------------------------------------------- partidas

def hash_log(texto):
    normal = "\n".join(l.strip() for l in texto.strip().splitlines() if l.strip())
    return hashlib.sha1(normal.encode("utf-8")).hexdigest()


def dono_provavel(dados, nick, amigos=()):
    """Partida capturada ou colada sem dono: se o seu nick não joga nela, ela é de outra pessoa
    (um amigo copiou o log dele no seu computador, ou você colou o log de um amigo).
    Devolve de quem ela é: o amigo que já está no programa; senão, quem exportou o log;
    senão, o primeiro jogador. Devolve "" se a partida é sua (ou se não há nick para comparar)."""
    jogadores = dados.get("jogadores") or []
    if not nick or not jogadores or nick.lower() in {j.lower() for j in jogadores}:
        return ""
    conhecidos = {a.lower() for a in amigos}
    amigo = next((j for j in jogadores if j.lower() in conhecidos), None)
    exportou = (dados.get("resumo") or {}).get("exportou")
    return amigo or (exportou if exportou in jogadores else jogadores[0])


def _amigos(con):
    return [r[0] for r in con.execute("SELECT DISTINCT dono FROM partidas WHERE COALESCE(dono,'')!=''")]


def separar_partidas_de_outros():
    """Partidas gravadas como suas em que o seu nick não joga passam para o amigo (ver dono_provavel).
    Roda ao abrir o programa e quando o nick muda; não apaga nada, só troca o dono."""
    nick = (config.ler_config().get("nick") or "").strip()
    if not nick:
        return 0
    movidas = 0
    with _trava, conectar() as con:
        amigos = _amigos(con)
        for r in con.execute("SELECT id, dados_json FROM partidas WHERE COALESCE(dono,'')=''").fetchall():
            dono = dono_provavel(json.loads(r["dados_json"]), nick, amigos)
            if dono:
                con.execute("UPDATE partidas SET dono=? WHERE id=?", (dono, r["id"]))
                amigos.append(dono)
                movidas += 1
    if movidas:
        marcar_mudanca()
        print(f"[banco] {movidas} partida(s) de outro jogador passaram para Amigos.")
    return movidas


def inserir_partida(texto, origem, regras, dono="", capturada_em=None, extras=None):
    """Grava uma partida. Devolve (id, nova?). Logs repetidos são ignorados.
    dono: vazio para as suas partidas; o nick do amigo para logs importados dele.
    Sem dono, se o seu nick não joga a partida, ela vai para o amigo (ver dono_provavel)."""
    h = hash_log(texto)
    with _trava, conectar() as con:
        existente = con.execute("SELECT id FROM partidas WHERE hash=?", (h,)).fetchone()
        if existente:
            return existente["id"], False
        dados = leitor.ler_partida(texto, regras)
        if not dono:
            dono = dono_provavel(dados, (config.ler_config().get("nick") or "").strip(), _amigos(con))
        quando = capturada_em or datetime.now().isoformat(timespec="seconds")
        nome = quando.replace("T", "_").replace(":", "")[:17] + f"_{h[:6]}.txt"
        pasta = config.PASTA_LOGS
        if dono:  # logs de amigos ficam separados, e nunca são reenviados quando você exporta os seus
            pasta = config.PASTA_DADOS / "logs_amigos" / (re.sub(r"[^A-Za-z0-9_.-]", "_", dono) or "amigo")
            pasta.mkdir(parents=True, exist_ok=True)
            nome = str(Path("..") / "logs_amigos" / pasta.name / nome)
        (config.PASTA_LOGS / nome).write_text(texto, encoding="utf-8")
        ex = extras or {}
        cur = con.execute(
            "INSERT INTO partidas (hash, capturada_em, origem, arquivo, texto, dados_json, dono, meu_deck, deck_adv, tags, notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (h, quando, origem, nome, texto, json.dumps(dados, ensure_ascii=False), dono,
             ex.get("meu_deck", ""), ex.get("deck_adv", ""), ex.get("tags", ""), ex.get("notas", "")),
        )
        pid = cur.lastrowid
    marcar_mudanca()
    if dono:
        return pid, True
    try:  # liga a partida a uma lista de "Meus decks", se as cartas reveladas baterem
        from . import decks
        decks.vincular_automatico(pid)
    except Exception as e:
        print("[decks] não consegui vincular a partida:", e)
    return pid, True


def _linha_para_partida(r, completo=False):
    d = json.loads(r["dados_json"])
    p = {k: r[k] for k in ("id", "capturada_em", "origem", "arquivo", "meu_deck", "deck_adv", "notas", "tags", "deck_id", "dono")}
    p["dono"] = p["dono"] or ""
    p["jogadores"] = d["jogadores"]
    p["resumo"] = d["resumo"]
    p["qtd_nao_lidas"] = len(d["nao_lidas"])
    if completo:
        p["eventos"] = d["eventos"]
        p["nao_lidas"] = d["nao_lidas"]
        p["texto"] = r["texto"]
    return p


# Memória da lista de partidas: ler e decodificar todas leva ~1 s com mil partidas, e cada tela pede
# isso várias vezes. Qualquer gravação em `partidas` chama marcar_mudanca(); por segurança, vale 60 s.
_memoria = {"versao": 0, "lida": -1, "t": 0.0, "lista": []}


def marcar_mudanca():
    _memoria["versao"] += 1


def listar_partidas():
    import time
    if _memoria["lida"] != _memoria["versao"] or time.time() - _memoria["t"] > 60:
        versao = _memoria["versao"]
        with conectar() as con:
            rows = con.execute("SELECT * FROM partidas ORDER BY capturada_em DESC").fetchall()
        _memoria.update(lista=[_linha_para_partida(r) for r in rows], lida=versao, t=time.time())
    return [dict(p) for p in _memoria["lista"]]  # cópias: quem usa pode mexer sem estragar a memória


def obter_partida(pid):
    with conectar() as con:
        r = con.execute("SELECT * FROM partidas WHERE id=?", (pid,)).fetchone()
    return _linha_para_partida(r, completo=True) if r else None


def atualizar_partida(pid, campos):
    permitidos = {k: v for k, v in campos.items() if k in ("meu_deck", "deck_adv", "notas", "tags", "deck_id")}
    if not permitidos:
        return
    sets = ", ".join(f"{k}=?" for k in permitidos)
    with _trava, conectar() as con:
        con.execute(f"UPDATE partidas SET {sets} WHERE id=?", (*permitidos.values(), pid))
    marcar_mudanca()


def apagar_partida(pid):
    with _trava, conectar() as con:
        con.execute("DELETE FROM partidas WHERE id=?", (pid,))
    marcar_mudanca()


def reprocessar_partidas(regras):
    with _trava, conectar() as con:
        rows = con.execute("SELECT id, texto FROM partidas").fetchall()
        for r in rows:
            dados = leitor.ler_partida(r["texto"], regras)
            con.execute("UPDATE partidas SET dados_json=? WHERE id=?", (json.dumps(dados, ensure_ascii=False), r["id"]))
    marcar_mudanca()
    return len(rows)


# ---------------------------------------------------------------- torneios

def salvar_torneio(t, jogadores, partidas, listas=None):
    """Substitui todos os dados de um torneio pelos novos."""
    with _trava, conectar() as con:
        for tabela in ("t_jogadores", "t_partidas") + (("t_listas",) if listas is not None else ()):
            con.execute(f"DELETE FROM {tabela} WHERE torneio=?", (t["id"],))
        con.execute(
            "INSERT OR REPLACE INTO torneios (id, nome, data, jogadores, rk9, importado_em, info_json, fonte, formato) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (t["id"], t.get("nome"), t.get("data"), t.get("jogadores"), t.get("rk9"),
             datetime.now().isoformat(timespec="seconds"), json.dumps(t.get("info", {}), ensure_ascii=False),
             t.get("fonte", "labs"), t.get("formato", "")),
        )
        con.executemany(
            "INSERT INTO t_jogadores (torneio, labs_id, nome, nome_norm, pais, posicao, pontos, v, d, e, arquetipo) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(t["id"], j.get("labs_id"), j["nome"], j["nome_norm"], j.get("pais", ""), j.get("posicao"),
              j.get("pontos"), j.get("v"), j.get("d"), j.get("e"), j.get("arquetipo", "")) for j in jogadores],
        )
        con.executemany(
            "INSERT INTO t_partidas VALUES (?,?,?,?,?,?,?,?)",
            [(t["id"], p["rodada"], p.get("mesa", ""), p["j1"], p["j2"], p["res1"], p.get("arq1", ""), p.get("arq2", ""))
             for p in partidas],
        )
        if listas:
            con.executemany(
                "INSERT INTO t_listas (torneio, labs_id, carta, set_code, numero, qtd, carta_id, carta_base) VALUES (?,?,?,?,?,?,?,?)",
                [(t["id"], c["labs_id"], c["carta"], c.get("set", ""), c.get("numero", ""), c["qtd"],
                  *_converter(c)) for c in listas],
            )
    if listas:
        atualizar_ace_spec(t["id"])


def _converter(c):
    """Arte alternativa -> arte básica (id e nome). Sem biblioteca, fica em branco."""
    from . import cartas
    e = cartas.converter(c.get("set"), c.get("numero"), c.get("carta"))
    return (e["id"], e["nome"]) if e else ("", "")


def atualizar_ace_spec(torneio=None):
    """Grava em t_jogadores.ace_spec a ACE SPEC da lista de cada jogador ('' = a lista não tem ACE SPEC).
    Jogador sem lista importada fica NULL. Sem a biblioteca de cartas, não mexe em nada (não daria para saber).
    torneio: só um torneio; None = todos."""
    from . import cartas
    from .leitor import normalizar_nome_carta
    ids, nomes = cartas.ace_spec()
    if not ids:
        return 0
    filtro, params = (" WHERE torneio=?", (torneio,)) if torneio else ("", ())
    achado = {}
    for r in consultar(f"SELECT torneio, labs_id, carta, carta_id, carta_base FROM t_listas{filtro}", params):
        chave = (r["torneio"], r["labs_id"])
        achado.setdefault(chave, "")
        nome = r["carta_base"] or r["carta"]
        if r["carta_id"] in ids or normalizar_nome_carta(nome) in nomes:
            achado[chave] = nome
    with _trava, conectar() as con:
        con.executemany("UPDATE t_jogadores SET ace_spec=? WHERE torneio=? AND labs_id=?",
                        [(ace, t, l) for (t, l), ace in achado.items()])
    return len(achado)


def reconverter_listas():
    """Refaz a conversão de todas as listas (chamado quando a biblioteca de cartas muda)."""
    with _trava, conectar() as con:
        linhas = con.execute("SELECT rowid, carta, set_code, numero FROM t_listas").fetchall()
        for r in linhas:
            cid, base = _converter({"carta": r["carta"], "set": r["set_code"], "numero": r["numero"]})
            con.execute("UPDATE t_listas SET carta_id=?, carta_base=? WHERE rowid=?", (cid, base, r["rowid"]))
        for r in con.execute("SELECT rowid, nome, set_code, numero FROM meus_decks_cartas").fetchall():
            cid, base = _converter({"carta": r["nome"], "set": r["set_code"], "numero": r["numero"]})
            con.execute("UPDATE meus_decks_cartas SET carta_id=?, carta_base=? WHERE rowid=?", (cid, base, r["rowid"]))
    atualizar_ace_spec()  # a biblioteca mudou: a marcação de ACE SPEC pode ter mudado também
    return len(linhas)


def listar_torneios():
    with conectar() as con:
        rows = con.execute("""
            SELECT t.*, (SELECT COUNT(*) FROM t_partidas p WHERE p.torneio=t.id) AS qtd_partidas,
                        (SELECT COUNT(DISTINCT labs_id) FROM t_listas l WHERE l.torneio=t.id) AS qtd_listas
            FROM torneios t ORDER BY data DESC""").fetchall()
    return [dict(r) for r in rows]


def marcar_formatos(formatos):
    """Grava o formato confirmado dos torneios do Labs: {labs_id: 'standard' | 'standard-jp' | ...}."""
    with _trava, conectar() as con:
        for tid, formato in formatos.items():
            con.execute("UPDATE torneios SET formato=? WHERE id=? AND COALESCE(fonte,'labs')='labs'", (formato, tid))


def apagar_torneio(tid):
    with _trava, conectar() as con:
        for tabela in ("t_jogadores", "t_partidas", "t_listas"):
            con.execute(f"DELETE FROM {tabela} WHERE torneio=?", (tid,))
        con.execute("DELETE FROM torneios WHERE id=?", (tid,))


def consultar(sql, params=()):
    with conectar() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
