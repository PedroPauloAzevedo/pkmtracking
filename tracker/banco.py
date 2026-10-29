"""
Banco de dados local (SQLite, um único arquivo em dados/tracker.db).

Dá para abrir esse arquivo no DB Browser for SQLite, no Power BI ou no Excel
(via conector ODBC) se você quiser fazer análises por fora.
"""
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from . import config, leitor

_trava = threading.Lock()

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
    if regras_novas:  # regras atualizadas: relê as partidas já gravadas
        reprocessar_partidas(config.ler_regras())


# ---------------------------------------------------------------- partidas

def hash_log(texto):
    normal = "\n".join(l.strip() for l in texto.strip().splitlines() if l.strip())
    return hashlib.sha1(normal.encode("utf-8")).hexdigest()


def inserir_partida(texto, origem, regras):
    """Grava uma partida. Devolve (id, nova?). Logs repetidos são ignorados."""
    h = hash_log(texto)
    with _trava, conectar() as con:
        existente = con.execute("SELECT id FROM partidas WHERE hash=?", (h,)).fetchone()
        if existente:
            return existente["id"], False
        dados = leitor.ler_partida(texto, regras)
        agora = datetime.now()
        nome = agora.strftime("%Y-%m-%d_%H%M%S") + f"_{h[:6]}.txt"
        (config.PASTA_LOGS / nome).write_text(texto, encoding="utf-8")
        cur = con.execute(
            "INSERT INTO partidas (hash, capturada_em, origem, arquivo, texto, dados_json) VALUES (?,?,?,?,?,?)",
            (h, agora.isoformat(timespec="seconds"), origem, nome, texto, json.dumps(dados, ensure_ascii=False)),
        )
        pid = cur.lastrowid
    try:  # liga a partida a uma lista de "Meus decks", se as cartas reveladas baterem
        from . import decks
        decks.vincular_automatico(pid)
    except Exception as e:
        print("[decks] não consegui vincular a partida:", e)
    return pid, True


def _linha_para_partida(r, completo=False):
    d = json.loads(r["dados_json"])
    p = {k: r[k] for k in ("id", "capturada_em", "origem", "arquivo", "meu_deck", "deck_adv", "notas", "tags", "deck_id")}
    p["jogadores"] = d["jogadores"]
    p["resumo"] = d["resumo"]
    p["qtd_nao_lidas"] = len(d["nao_lidas"])
    if completo:
        p["eventos"] = d["eventos"]
        p["nao_lidas"] = d["nao_lidas"]
        p["texto"] = r["texto"]
    return p


def listar_partidas():
    with conectar() as con:
        rows = con.execute("SELECT * FROM partidas ORDER BY capturada_em DESC").fetchall()
    return [_linha_para_partida(r) for r in rows]


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


def apagar_partida(pid):
    with _trava, conectar() as con:
        con.execute("DELETE FROM partidas WHERE id=?", (pid,))


def reprocessar_partidas(regras):
    with _trava, conectar() as con:
        rows = con.execute("SELECT id, texto FROM partidas").fetchall()
        for r in rows:
            dados = leitor.ler_partida(r["texto"], regras)
            con.execute("UPDATE partidas SET dados_json=? WHERE id=?", (json.dumps(dados, ensure_ascii=False), r["id"]))
    return len(rows)


# ---------------------------------------------------------------- torneios

def salvar_torneio(t, jogadores, partidas, listas=None):
    """Substitui todos os dados de um torneio pelos novos."""
    with _trava, conectar() as con:
        for tabela in ("t_jogadores", "t_partidas") + (("t_listas",) if listas is not None else ()):
            con.execute(f"DELETE FROM {tabela} WHERE torneio=?", (t["id"],))
        con.execute(
            "INSERT OR REPLACE INTO torneios (id, nome, data, jogadores, rk9, importado_em, info_json) VALUES (?,?,?,?,?,?,?)",
            (t["id"], t.get("nome"), t.get("data"), t.get("jogadores"), t.get("rk9"),
             datetime.now().isoformat(timespec="seconds"), json.dumps(t.get("info", {}), ensure_ascii=False)),
        )
        con.executemany(
            "INSERT INTO t_jogadores VALUES (?,?,?,?,?,?,?,?,?,?,?)",
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


def _converter(c):
    """Arte alternativa -> arte básica (id e nome). Sem biblioteca, fica em branco."""
    from . import cartas
    e = cartas.converter(c.get("set"), c.get("numero"), c.get("carta"))
    return (e["id"], e["nome"]) if e else ("", "")


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
    return len(linhas)


def listar_torneios():
    with conectar() as con:
        rows = con.execute("""
            SELECT t.*, (SELECT COUNT(*) FROM t_partidas p WHERE p.torneio=t.id) AS qtd_partidas,
                        (SELECT COUNT(DISTINCT labs_id) FROM t_listas l WHERE l.torneio=t.id) AS qtd_listas
            FROM torneios t ORDER BY data DESC""").fetchall()
    return [dict(r) for r in rows]


def apagar_torneio(tid):
    with _trava, conectar() as con:
        for tabela in ("t_jogadores", "t_partidas", "t_listas"):
            con.execute(f"DELETE FROM {tabela} WHERE torneio=?", (tid,))
        con.execute("DELETE FROM torneios WHERE id=?", (tid,))


def consultar(sql, params=()):
    with conectar() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
