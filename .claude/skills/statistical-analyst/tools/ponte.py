"""
PONTE ENTRE A SKILL E O MOTOR ESTATÍSTICO DO COLETOR — SÓ LEITURA, COM TRAVA NA EXECUÇÃO (reutiliza; não copia).

    from ponte import carregar
    t = carregar(r"C:\\caminho\\da\\COPIA")      # pasta de uma CÓPIA de teste (ver "Identificação" abaixo)
    t.analises.wilson(7, 10)                     # -> (39.7, 89.2)
    t.estrategia.confrontos_ajustados(partidas, decks)
    t.banco.consultar("SELECT COUNT(*) AS n FROM torneios")   # só leitura

Por que existe (revisão de 06/11/2026): a versão anterior só "pedia" que ninguém escrevesse. Agora a escrita é IMPEDIDA na execução,
em camadas independentes (se uma falhar, as outras seguram):
  1. Validação ANTES de importar qualquer módulo do Coletor (`validar_copia`): pasta com `tracker/`; `dados/config.json` presente,
     legível e com porta 8799 (faltou = falha, não aviso); marca de cópia `dados/COPIA_DE_TESTE.json` (`marcar_copia.py`); sem `.venv`
     nem `.git` (instalação em uso ou o próprio repositório); fora das pastas de `SA_PASTAS_PROTEGIDAS`; `dados/tracker.db` arquivo
     SQLite de verdade, dentro da cópia, que abre em modo leitura.
  2. Banco: `banco.conectar` do Coletor é trocado por uma conexão `file:...?mode=ro` (o SQLite recusa gravar), com
     `PRAGMA query_only=ON` e um autorizador (`set_authorizer`) que só deixa passar leitura. Não é filtro de texto do SQL: quem decide
     é o compilador do SQLite, comando por comando.
  3. Funções que gravam (lista `FUNCOES_ESCRITA`) são trocadas por um bloqueio com erro claro.
  4. Vigia do Python (`sys.addaudithook`), ligado antes do import: bloqueia abrir arquivo para gravar, criar/apagar/renomear arquivo
     ou pasta dentro da cópia e das pastas protegidas; qualquer conexão SQLite que não seja `mode=ro` (em qualquer lugar); conexões
     de rede; e programas externos (menos `git` de consulta, usado pelo registro dos experimentos). O vigia não pode ser desligado
     no mesmo processo: depois de `carregar`, o processo inteiro fica em modo análise.
Limite conhecido: código que chame o sistema operacional direto (ctypes) passa por fora do vigia; o banco continua protegido pelo
`mode=ro`. Não há "modo escrita" aqui de propósito: experimento que grava (e4, e7) roda à parte, num banco descartável.

Regras:
  - Um processo por cópia (o tracker usa a pasta `dados/` ao lado do código importado).
  - As funções do Coletor são usadas como estão; se uma precisar mudar, a mudança é no Coletor (com medição, D-017), não aqui.
Testes: ../tests/test_ponte.py (pede escrita de propósito e confere que é bloqueada).
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sqlite3
import sys
import threading
import urllib.parse
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

PORTA_TESTE = 8799
MARCA_COPIA = "COPIA_DE_TESTE.json"   # dentro de dados/; criada por marcar_copia.py
MODULOS = ("analises", "banco", "decks", "estrategia", "probabilidades", "regressao", "variantes", "leitor", "replay", "cartas")

# Classificação das funções do Coletor que a ponte expõe. Toda função pública de `banco` precisa estar num dos dois grupos
# (tests/test_ponte.py falha se aparecer uma nova sem classificação). Nos outros módulos, as de escrita conhecidas são bloqueadas
# por nome e o vigia pega o resto.
FUNCOES_LEITURA_BANCO = {"hash_log", "dono_provavel", "listar_partidas", "obter_partida", "versao_torneios", "listar_torneios",
                         "consultar", "marcar_mudanca", "marcar_mudanca_torneios", "conectar"}   # marcar_* = contador na memória
FUNCOES_ESCRITA = {
    "banco": {"iniciar", "separar_partidas_de_outros", "inserir_partida", "atualizar_partida", "apagar_partida",
              "reprocessar_partidas", "salvar_torneio", "atualizar_ace_spec", "reconverter_listas", "marcar_formatos",
              "apagar_torneio"},
    "config": {"preparar_pastas", "atualizar_regras_antigas", "salvar_config", "salvar_regras"},
    "decks": {"salvar_arquetipos", "aprender_icones", "salvar_icones", "salvar_deck", "reler_listas", "vincular_automatico",
              "caminho_icone"},
    "cartas": {"montar_indice", "atualizar", "baixar_todas_imagens", "adicionar_manual", "remover_manual", "caminho_imagem",
               "_gravar_json", "_baixar_cartas"},
}


class CopiaInvalida(RuntimeError):
    """A pasta não é uma cópia de teste válida: nada foi importado."""


class EscritaBloqueada(PermissionError):
    """Tentativa de gravar durante uma análise (banco, arquivo, rede ou programa externo)."""


# ------------------------------------------------------------------ 1. validação (antes de importar)

ARQ_PROTEGIDAS_LOCAL = ".sa_pastas_protegidas"   # na pasta do usuário (fora do repositório): uma pasta por linha; '#' = comentário


def _pastas_protegidas_env() -> list[Path]:
    """Pastas que a ponte nunca carrega nem deixa gravar (instalações reais): variável SA_PASTAS_PROTEGIDAS (separadas por ';' no
    Windows) + arquivo ~/.sa_pastas_protegidas. O arquivo fica no computador de cada pessoa: caminhos pessoais não vão para o GitHub."""
    brutos = [p for p in os.environ.get("SA_PASTAS_PROTEGIDAS", "").split(os.pathsep) if p.strip()]
    try:
        arq = Path.home() / ARQ_PROTEGIDAS_LOCAL
        if arq.is_file():
            brutos += [l.strip() for l in arq.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
    except (OSError, RuntimeError, UnicodeDecodeError):
        pass
    return [Path(p).expanduser().resolve() for p in brutos]


def _dentro(caminho: Path, raiz: Path) -> bool:
    a, b = os.path.normcase(str(caminho)), os.path.normcase(str(raiz))
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:   # discos diferentes no Windows
        return False


def _hash_arquivos(pasta: Path, padrao: str) -> str:
    h = hashlib.sha256()
    for arq in sorted(pasta.glob(padrao)):
        h.update(arq.name.encode())
        h.update(arq.read_bytes())
    return h.hexdigest()[:16]


def validar_copia(pasta_programa: str | Path) -> dict:
    """Confere tudo o que dá para conferir SEM importar o Coletor. Devolve a identificação da cópia (sem caminho nem dado pessoal)
    ou levanta CopiaInvalida com o motivo. Falha segura: qualquer dúvida = recusa."""
    pasta = Path(pasta_programa).expanduser().resolve()
    if not pasta.is_dir():
        raise CopiaInvalida(f"pasta não existe: {pasta}")
    if not (pasta / "tracker" / "__init__.py").exists():
        raise CopiaInvalida(f"{pasta} não tem tracker/: não é uma pasta do Coletor")
    for nome, motivo in ((".venv", "tem .venv: parece uma instalação em uso, não uma cópia de teste"),
                         (".git", "tem .git: é o repositório, não uma cópia de teste")):
        if (pasta / nome).exists():
            raise CopiaInvalida(f"{pasta} {motivo}")
    for prot in _pastas_protegidas_env():
        if _dentro(pasta, prot) or _dentro(prot, pasta):
            raise CopiaInvalida(f"{pasta} está numa pasta protegida (SA_PASTAS_PROTEGIDAS): banco de produção recusado")
    cfg_arq = pasta / "dados" / "config.json"
    if not cfg_arq.is_file():
        raise CopiaInvalida(f"falta {cfg_arq}: sem configuração não dá para provar que é uma cópia de teste (porta {PORTA_TESTE})")
    try:
        cfg = json.loads(cfg_arq.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CopiaInvalida(f"{cfg_arq} ilegível ({e})") from e
    if not isinstance(cfg, dict) or cfg.get("porta") != PORTA_TESTE:
        raise CopiaInvalida(f"{cfg_arq} tem porta {cfg.get('porta') if isinstance(cfg, dict) else '?'}: "
                            f"use uma CÓPIA de teste com porta {PORTA_TESTE} (CLAUDE.md)")
    marca = pasta / "dados" / MARCA_COPIA
    try:
        m = json.loads(marca.read_text(encoding="utf-8"))
        assert isinstance(m, dict) and m.get("copia_de_teste") is True
    except Exception:
        raise CopiaInvalida(f"falta a marca de cópia {marca} (crie com tools/marcar_copia.py, que confere a pasta antes)") from None
    db = pasta / "dados" / "tracker.db"
    if db.is_symlink() or not db.is_file():
        raise CopiaInvalida(f"caminho de banco inválido: {db} não é um arquivo comum")
    if not _dentro(db.resolve(), pasta):
        raise CopiaInvalida(f"caminho de banco inválido: {db} aponta para fora da cópia")
    for prot in _pastas_protegidas_env():
        alvo = prot / "dados" / "tracker.db"
        if alvo.exists() and os.path.samefile(alvo, db):
            raise CopiaInvalida("o banco é o mesmo arquivo de uma pasta protegida: banco de produção recusado")
    with open(db, "rb") as f:
        if f.read(16) != b"SQLite format 3\x00":
            raise CopiaInvalida(f"caminho de banco inválido: {db} não é um banco SQLite")
    try:
        con = sqlite3.connect(_uri_leitura(db), uri=True)
        try:
            tabelas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            con.close()
    except sqlite3.Error as e:
        raise CopiaInvalida(f"caminho de banco inválido: {db} não abre em modo leitura ({e})") from e
    if "partidas" not in tabelas or "torneios" not in tabelas:
        raise CopiaInvalida(f"caminho de banco inválido: {db} não tem as tabelas do Coletor")
    versao = (pasta / "versao.txt").read_text(encoding="utf-8").strip() if (pasta / "versao.txt").exists() else None
    return {"copia": hashlib.sha256(os.path.normcase(str(pasta)).encode()).hexdigest()[:12],   # só a impressão do caminho
            "versao_coletor": versao, "codigo_tracker": _hash_arquivos(pasta / "tracker", "*.py"), "porta": PORTA_TESTE,
            "marca_criada_em": m.get("criada_em")}


# ------------------------------------------------------------------ 2. banco só leitura

def _uri_leitura(db: Path) -> str:
    return "file:" + urllib.parse.quote(Path(db).resolve().as_posix(), safe="/:") + "?mode=ro"


# PRAGMAs que só consultam, mesmo com argumento (o argumento é o nome de uma tabela ou índice)
_PRAGMAS_CONSULTA = {"table_info", "table_xinfo", "index_list", "index_info", "index_xinfo", "foreign_key_list",
                     "table_list", "database_list", "compile_options", "collation_list", "function_list"}
# PRAGMAs que podem ser LIDOS sem argumento, mas gravam quando recebem valor (PRAGMA user_version = 7): só sem argumento
_PRAGMAS_SO_LEITURA = {"query_only", "user_version", "schema_version", "page_count", "page_size", "journal_mode",
                       "encoding", "freelist_count", "application_id"}
_ACOES_PERMITIDAS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}


def _autorizador(acao, arg1, arg2, _db, _gatilho):
    if acao in _ACOES_PERMITIDAS:
        return sqlite3.SQLITE_OK
    if acao == sqlite3.SQLITE_PRAGMA:
        nome = (arg1 or "").lower()
        if nome in _PRAGMAS_CONSULTA or (nome in _PRAGMAS_SO_LEITURA and arg2 is None):
            return sqlite3.SQLITE_OK   # PRAGMA de consulta, sem atribuição
    return sqlite3.SQLITE_DENY       # INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, ATTACH, PRAGMA x=y, ...


def conexao_leitura(db: Path) -> sqlite3.Connection:
    """Conexão que não grava: mode=ro + query_only + autorizador."""
    con = sqlite3.connect(_uri_leitura(db), uri=True, timeout=30)
    con.execute("PRAGMA query_only = ON")
    con.set_authorizer(_autorizador)
    con.row_factory = sqlite3.Row
    return con


def _fabricar_conectar(db: Path):
    @contextmanager
    def conectar():
        con = conexao_leitura(db)
        try:
            yield con          # sem commit: não há o que gravar
        except sqlite3.DatabaseError as e:
            txt = str(e).lower()
            if "not authorized" in txt or "readonly" in txt or "read-only" in txt or "query_only" in txt:
                raise EscritaBloqueada(f"escrita no banco bloqueada (análise é só leitura): {e}") from e
            raise
        finally:
            con.close()
    return conectar


def _bloqueio(modulo: str, nome: str):
    def bloqueada(*_a, **_k):
        raise EscritaBloqueada(f"{modulo}.{nome} grava dados e está bloqueada na análise (ponte só leitura)")
    bloqueada.__name__ = nome
    bloqueada.escrita_bloqueada = True
    return bloqueada


# ------------------------------------------------------------------ 4. vigia do Python

_estado = {"ligado": False, "raizes": [], "guarda": threading.local()}
_FLAGS_ESCRITA = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_EVENTOS_CAMINHO = {"os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "os.rename": (0, 1), "os.truncate": (0,),
                    "os.chmod": (0,), "os.link": (0, 1), "os.symlink": (0, 1), "os.utime": (0,), "shutil.copyfile": (1,),
                    "shutil.copytree": (1,), "shutil.rmtree": (0,), "shutil.move": (0, 1), "shutil.make_archive": (0,)}
_GIT_CONSULTA = {"rev-parse", "status", "log", "ls-files", "diff", "hash-object"}


def _protegido(caminho) -> bool:
    if isinstance(caminho, int) or caminho is None:
        return False
    try:
        p = Path(os.fsdecode(os.fspath(caminho)))
        p = Path(os.path.realpath(p if p.is_absolute() else Path.cwd() / p))
    except (TypeError, ValueError, OSError):
        return True   # na dúvida, protegido
    return any(_dentro(p, r) for r in _estado["raizes"])


def _vigia(evento: str, args: tuple) -> None:
    if not _estado["ligado"]:
        return
    g = _estado["guarda"]
    if getattr(g, "dentro", False):
        return
    g.dentro = True
    try:
        if evento == "open":
            caminho, modo, flags = (list(args) + [None, None, 0])[:3]
            grava = (isinstance(modo, str) and any(c in modo for c in "wax+")) or (modo is None and (flags or 0) & _FLAGS_ESCRITA)
            if grava and _protegido(caminho):
                raise EscritaBloqueada(f"gravar arquivo bloqueado na análise: {caminho}")
        elif evento in _EVENTOS_CAMINHO:
            for i in _EVENTOS_CAMINHO[evento]:
                if i < len(args) and _protegido(args[i]):
                    raise EscritaBloqueada(f"{evento} bloqueado na análise: {args[i]}")
        elif evento == "sqlite3.connect":
            alvo = os.fsdecode(os.fspath(args[0])) if args and not isinstance(args[0], int) else ""
            if alvo not in ("", ":memory:") and "mode=ro" not in alvo and "mode=memory" not in alvo:
                raise EscritaBloqueada(f"conexão SQLite que pode gravar bloqueada na análise (use mode=ro): {alvo}")
        elif evento in ("socket.connect", "socket.getaddrinfo"):
            raise EscritaBloqueada("acesso à rede bloqueado na análise (nada de baixar ou enviar)")
        elif evento in ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.startfile", "os.posix_spawn",
                        "ctypes.dlopen"):
            prog = args[1] if evento == "subprocess.Popen" and len(args) > 1 else args
            if isinstance(prog, (str, bytes)):          # no Windows o comando chega como texto único
                prog = os.fsdecode(prog).replace('"', " ").split()
            partes = [os.fsdecode(x) if isinstance(x, (str, bytes, os.PathLike)) else str(x) for x in
                      (prog if isinstance(prog, (list, tuple)) else [prog])]
            nome = Path(partes[0]).stem.lower() if partes else ""
            if not (evento == "subprocess.Popen" and nome == "git" and _GIT_CONSULTA & set(partes)):
                raise EscritaBloqueada(f"programa externo bloqueado na análise: {' '.join(partes)[:120]}")
    finally:
        g.dentro = False


def ligar_vigia(raizes: list[Path]) -> None:
    """Liga o vigia (uma vez por processo) e acrescenta pastas protegidas. Não há como desligar."""
    for r in raizes:
        r = Path(os.path.realpath(r))
        if r not in _estado["raizes"]:
            _estado["raizes"].append(r)
    if not _estado["ligado"]:
        sys.addaudithook(_vigia)
        _estado["ligado"] = True


def vigia_ligado() -> bool:
    return _estado["ligado"]


# ------------------------------------------------------------------ carregar

def carregar(pasta_programa: str | Path) -> SimpleNamespace:
    """Valida a cópia, liga as travas e devolve os módulos do Coletor em modo só leitura."""
    ident = validar_copia(pasta_programa)                    # 1. nada é importado antes disso
    pasta = Path(pasta_programa).expanduser().resolve()
    if "tracker" in sys.modules and Path(sys.modules["tracker"].__file__).resolve().parent.parent != pasta:
        raise CopiaInvalida("outro tracker já foi importado neste processo; rode um processo por pasta")
    ligar_vigia([pasta] + _pastas_protegidas_env())           # 4. antes do import: pega gravação feita ao importar
    sys.dont_write_bytecode = True                           # sem __pycache__ dentro da cópia
    sys.path.insert(0, str(pasta))
    config = importlib.import_module("tracker.config")
    banco = importlib.import_module("tracker.banco")
    db = (pasta / "dados" / "tracker.db").resolve()
    if Path(config.ARQ_BANCO).resolve() != db:
        raise CopiaInvalida("o tracker importado aponta para outro banco; recusado")
    banco.conectar = _fabricar_conectar(db)                  # 2.
    mods = {m: importlib.import_module(f"tracker.{m}") for m in MODULOS}
    mods["config"] = config
    for modulo, nomes in FUNCOES_ESCRITA.items():            # 3.
        for nome in nomes:
            if hasattr(mods[modulo], nome):
                setattr(mods[modulo], nome, _bloqueio(modulo, nome))
    return SimpleNamespace(**mods, pasta=pasta, identificacao=ident, modo="leitura",
                           conexao_leitura=lambda: conexao_leitura(db))
