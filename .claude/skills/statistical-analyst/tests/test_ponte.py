"""
Testes de SEGURANÇA da ponte (tools/ponte.py): pedem escrita de propósito e conferem que ela é bloqueada.

Cada teste monta uma cópia descartável numa pasta temporária (tracker/ do repositório + banco SQLite pequeno com o esquema do
Coletor) e roda a ponte num processo separado (o vigia vale para o processo inteiro). Ao final de cada caso, confere que nenhum
arquivo da cópia mudou (impressão de todos os arquivos antes × depois).

Uso:  python -I .claude/skills/statistical-analyst/tests/test_ponte.py
(usa o tracker/ do repositório onde a Skill está; outra fonte: variável SA_FONTE_TRACKER=<pasta com tracker/>)
"""
import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TOOLS = AQUI.parent / "tools"
FONTE = Path(os.environ.get("SA_FONTE_TRACKER") or AQUI.parents[3])
sys.path.insert(0, str(TOOLS))
import ponte  # noqa: E402  (só funções puras aqui; o vigia NÃO é ligado neste processo)

ESQUEMA_MIN = """
CREATE TABLE partidas (id INTEGER PRIMARY KEY, hash TEXT, capturada_em TEXT, origem TEXT, arquivo TEXT, texto TEXT,
                       dados_json TEXT, meu_deck TEXT DEFAULT '', deck_adv TEXT DEFAULT '', notas TEXT DEFAULT '', tags TEXT DEFAULT '');
CREATE TABLE torneios (id TEXT PRIMARY KEY, nome TEXT, data TEXT, jogadores INTEGER, rk9 TEXT, importado_em TEXT, info_json TEXT);
CREATE TABLE t_jogadores (torneio TEXT, labs_id TEXT, nome TEXT, nome_norm TEXT, pais TEXT, posicao INTEGER, pontos INTEGER,
                          v INTEGER, d INTEGER, e INTEGER, arquetipo TEXT);
CREATE TABLE t_partidas (torneio TEXT, rodada INTEGER, mesa TEXT, j1 TEXT, j2 TEXT, res1 TEXT, arq1 TEXT, arq2 TEXT);
CREATE TABLE t_listas (torneio TEXT, labs_id TEXT, carta TEXT, set_code TEXT, numero TEXT, qtd INTEGER, carta_id TEXT DEFAULT '',
                       carta_base TEXT DEFAULT '');
CREATE TABLE arquetipos (slug TEXT PRIMARY KEY, nome TEXT, icones TEXT, atualizado_em TEXT);
INSERT INTO torneios(id, nome, data) VALUES ('0001', 'Teste', '2026-10-01'), ('0002', 'Teste 2', '2026-10-08');
"""


def montar_copia(raiz: Path, porta=8799, config=True, marca=True, banco="ok") -> Path:
    pasta = raiz / "copia"
    shutil.copytree(FONTE / "tracker", pasta / "tracker", ignore=shutil.ignore_patterns("__pycache__"))
    (pasta / "versao.txt").write_text("teste\n", encoding="utf-8")
    (pasta / "dados").mkdir()
    if config:
        (pasta / "dados" / "config.json").write_text(json.dumps({"porta": porta}), encoding="utf-8")
    if marca:
        (pasta / "dados" / ponte.MARCA_COPIA).write_text(json.dumps({"copia_de_teste": True}), encoding="utf-8")
    db = pasta / "dados" / "tracker.db"
    if banco == "ok":
        con = sqlite3.connect(db)
        con.executescript(ESQUEMA_MIN)
        con.commit()
        con.close()
    elif banco == "pasta":
        db.mkdir()
    elif banco == "texto":
        db.write_text("isto não é um banco", encoding="utf-8")
    return pasta


def impressao(pasta: Path) -> dict:
    return {str(p.relative_to(pasta)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.rglob("*")) if p.is_file()}


def rodar(pasta: Path, corpo: str, env_extra: dict | None = None) -> dict:
    """Roda `corpo` num processo novo depois de `t = carregar(pasta)` (ou captura o erro do carregar). Devolve o JSON impresso."""
    codigo = textwrap.dedent(f"""
        import json, os, sys
        sys.path.insert(0, {str(TOOLS)!r})
        import ponte
        saida = {{}}
        try:
            t = ponte.carregar({str(pasta)!r})
        except Exception as e:
            print(json.dumps({{"carregar": type(e).__name__, "msg": str(e)}})); sys.exit(0)
        def tenta(nome, f):
            try:
                f(); saida[nome] = "PASSOU"
            except Exception as e:
                saida[nome] = type(e).__name__ + ": " + str(e)[:200]
    """) + textwrap.dedent(corpo) + "\nprint(json.dumps(saida))\n"
    env = dict(os.environ, **(env_extra or {}))
    env.pop("SA_PASTAS_PROTEGIDAS", None) if not env_extra or "SA_PASTAS_PROTEGIDAS" not in env_extra else None
    r = subprocess.run([sys.executable, "-I", "-c", codigo], capture_output=True, text=True, env=env, timeout=120, cwd=str(pasta.parent))
    if r.returncode != 0:
        raise AssertionError(f"processo falhou: {r.stderr[-1500:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class Leitura(Base):
    def test_select_permitido(self):
        pasta = montar_copia(self.raiz)
        r = rodar(pasta, """
            saida["n"] = t.banco.consultar("SELECT COUNT(*) AS n FROM torneios")[0]["n"]
            saida["pragma"] = len(t.banco.consultar("PRAGMA table_info(torneios)"))
            saida["modo"] = t.modo
            saida["wilson"] = t.analises.wilson(7, 10)
        """)
        self.assertEqual(r["n"], 2)
        self.assertGreater(r["pragma"], 3)
        self.assertEqual(r["modo"], "leitura")
        self.assertEqual(r["wilson"], [39.7, 89.2])


class EscritaNoBanco(Base):
    COMANDOS = {"insert": "INSERT INTO torneios(id) VALUES ('x')", "update": "UPDATE torneios SET nome='y'",
                "delete": "DELETE FROM torneios", "create": "CREATE TABLE z(a)", "drop": "DROP TABLE torneios",
                "alter": "ALTER TABLE torneios ADD COLUMN q TEXT", "create_index": "CREATE INDEX ix_z ON torneios(nome)",
                "pragma_escrita": "PRAGMA user_version = 7", "attach": "ATTACH DATABASE 'outro.db' AS o",
                "replace": "REPLACE INTO torneios(id) VALUES ('0001')", "vacuum": "VACUUM", "temp": "CREATE TEMP TABLE w(a)"}

    def test_escrita_bloqueada_por_sql(self):
        pasta = montar_copia(self.raiz)
        antes = impressao(pasta)
        corpo = "".join(f"tenta({k!r}, lambda: t.banco.consultar({v!r}))\n" for k, v in self.COMANDOS.items())
        corpo += "tenta('executescript', lambda: t.conexao_leitura().executescript('DELETE FROM torneios;'))\n"
        r = rodar(pasta, corpo)
        for k in list(self.COMANDOS) + ["executescript"]:
            self.assertNotEqual(r[k], "PASSOU", f"{k} deveria ser bloqueado")
            self.assertTrue(r[k].startswith(("EscritaBloqueada", "OperationalError", "DatabaseError")), r[k])
        self.assertEqual(impressao(pasta), antes, "o banco mudou")
        self.assertFalse((pasta.parent / "outro.db").exists())

    def test_funcoes_de_escrita_bloqueadas(self):
        pasta = montar_copia(self.raiz)
        antes = impressao(pasta)
        r = rodar(pasta, """
            tenta("apagar_torneio", lambda: t.banco.apagar_torneio("0001"))
            tenta("salvar_torneio", lambda: t.banco.salvar_torneio({"id": "9"}, [], []))
            tenta("iniciar", lambda: t.banco.iniciar())
            tenta("salvar_config", lambda: t.config.salvar_config({"porta": 8765}))
            tenta("salvar_deck", lambda: t.decks.salvar_deck({"nome": "x", "lista": ""}))
            tenta("aprender_icones", lambda: t.decks.aprender_icones("x", ["y"]))
            tenta("montar_indice", lambda: t.cartas.montar_indice())
            def via_conectar():
                with t.banco.conectar() as con:      # o mesmo caminho que decks/analises usam por dentro
                    con.execute("INSERT INTO torneios(id) VALUES ('z')")
            tenta("conectar_insert", via_conectar)
        """)
        for k, v in r.items():
            self.assertTrue(v.startswith("EscritaBloqueada"), f"{k}: {v}")
        self.assertEqual(impressao(pasta), antes)

    def test_cada_trava_sozinha(self):
        """As três travas do SQLite seguram a escrita mesmo uma de cada vez (defesa em camadas)."""
        db = self.raiz / "x.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE a(x)")
        con.commit()
        con.close()
        so_ro = sqlite3.connect(ponte._uri_leitura(db), uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            so_ro.execute("INSERT INTO a VALUES (1)")
        so_ro.close()
        so_qo = sqlite3.connect(db)
        so_qo.execute("PRAGMA query_only = ON")
        with self.assertRaises(sqlite3.OperationalError):
            so_qo.execute("INSERT INTO a VALUES (1)")
        so_qo.close()
        so_aut = sqlite3.connect(db)
        so_aut.set_authorizer(ponte._autorizador)
        for sql in ("INSERT INTO a VALUES (1)", "DROP TABLE a", "PRAGMA user_version = 3", "CREATE TABLE b(y)"):
            with self.assertRaises(sqlite3.DatabaseError, msg=sql):
                so_aut.execute(sql)
        self.assertEqual(so_aut.execute("SELECT COUNT(*) FROM a").fetchone()[0], 0)   # leitura passa
        so_aut.close()


class FalhaSegura(Base):
    def _recusa(self, pasta, trecho, env=None):
        r = rodar(pasta, "", env)
        self.assertEqual(r.get("carregar"), "CopiaInvalida", r)
        self.assertIn(trecho, r["msg"])

    def test_sem_config(self):
        self._recusa(montar_copia(self.raiz, config=False), "falta")

    def test_config_ilegivel(self):
        pasta = montar_copia(self.raiz)
        (pasta / "dados" / "config.json").write_text("{porta: ", encoding="utf-8")
        self._recusa(pasta, "ilegível")

    def test_porta_de_producao(self):
        self._recusa(montar_copia(self.raiz, porta=8765), "porta 8765")

    def test_sem_marca(self):
        self._recusa(montar_copia(self.raiz, marca=False), "marca de cópia")

    def test_banco_ausente(self):
        self._recusa(montar_copia(self.raiz, banco="nenhum"), "caminho de banco inválido")

    def test_banco_e_pasta(self):
        self._recusa(montar_copia(self.raiz, banco="pasta"), "caminho de banco inválido")

    def test_banco_nao_sqlite(self):
        self._recusa(montar_copia(self.raiz, banco="texto"), "não é um banco SQLite")

    def test_banco_fora_da_copia(self):
        pasta = montar_copia(self.raiz, banco="nenhum")
        fora = self.raiz / "fora.db"
        sqlite3.connect(fora).close()
        try:
            os.symlink(fora, pasta / "dados" / "tracker.db")
        except (OSError, NotImplementedError):
            self.skipTest("este sistema não deixa criar link simbólico sem permissão")
        self._recusa(pasta, "caminho de banco inválido")

    def test_dados_fora_da_copia_por_juncao(self):
        """No Windows, uma junção de pasta (não precisa de permissão especial) leva dados/ para fora da cópia: recusado."""
        if os.name != "nt":
            self.skipTest("junção de pasta é do Windows")
        pasta = montar_copia(self.raiz)
        fora = self.raiz / "dados_de_fora"
        shutil.move(str(pasta / "dados"), str(fora))
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(pasta / "dados"), str(fora)], capture_output=True)
        if r.returncode != 0:
            self.skipTest("não deu para criar a junção")
        self._recusa(pasta, "aponta para fora da cópia")

    def test_pasta_inexistente_e_sem_tracker(self):
        with self.assertRaises(ponte.CopiaInvalida):
            ponte.validar_copia(self.raiz / "nao_existe")
        (self.raiz / "vazia").mkdir()
        with self.assertRaises(ponte.CopiaInvalida):
            ponte.validar_copia(self.raiz / "vazia")


class Producao(Base):
    def test_instalacao_com_venv(self):
        pasta = montar_copia(self.raiz)
        (pasta / ".venv").mkdir()
        r = rodar(pasta, "")
        self.assertEqual(r.get("carregar"), "CopiaInvalida")
        self.assertIn(".venv", r["msg"])

    def test_pasta_protegida(self):
        pasta = montar_copia(self.raiz)
        r = rodar(pasta, "", {"SA_PASTAS_PROTEGIDAS": str(pasta)})
        self.assertEqual(r.get("carregar"), "CopiaInvalida")
        self.assertIn("produção recusado", r["msg"])

    def test_pasta_protegida_por_arquivo_local(self):
        """~/.sa_pastas_protegidas (fora do repositório) protege igual à variável de ambiente."""
        pasta = montar_copia(self.raiz)
        casa = self.raiz / "casa"
        casa.mkdir()
        (casa / ponte.ARQ_PROTEGIDAS_LOCAL).write_text(f"# instalação real\n{pasta}\n", encoding="utf-8")
        r = rodar(pasta, "", {"USERPROFILE": str(casa), "HOME": str(casa)})
        self.assertEqual(r.get("carregar"), "CopiaInvalida")
        self.assertIn("produção recusado", r["msg"])

    def test_repositorio_recusado(self):
        pasta = montar_copia(self.raiz)
        (pasta / ".git").mkdir()
        with self.assertRaises(ponte.CopiaInvalida):
            ponte.validar_copia(pasta)


class SemEscritaIndireta(Base):
    def test_arquivos_rede_programas(self):
        pasta = montar_copia(self.raiz)
        outro_db = self.raiz / "qualquer.db"
        sqlite3.connect(outro_db).close()
        antes = impressao(pasta)
        r = rodar(pasta, f"""
            import os, sqlite3, socket, subprocess, shutil
            from pathlib import Path
            p = Path({str(pasta)!r})
            tenta("open_w", lambda: open(p / "dados" / "novo.txt", "w"))
            tenta("open_a", lambda: open(p / "dados" / "config.json", "a"))
            tenta("open_rplus", lambda: open(p / "dados" / "tracker.db", "r+b"))
            tenta("os_open", lambda: os.open(str(p / "dados" / "y.txt"), os.O_CREAT | os.O_WRONLY))
            tenta("write_text", lambda: (p / "tracker" / "x.py").write_text("x"))
            tenta("remove", lambda: os.remove(p / "dados" / "config.json"))
            tenta("rename", lambda: os.rename(p / "dados" / "config.json", p / "dados" / "c2.json"))
            tenta("mkdir", lambda: os.mkdir(p / "dados" / "nova"))
            tenta("rmtree", lambda: shutil.rmtree(p / "tracker"))
            tenta("copyfile", lambda: shutil.copyfile(p / "versao.txt", p / "v2.txt"))
            tenta("sqlite_rw_copia", lambda: sqlite3.connect(str(p / "dados" / "tracker.db")))
            tenta("sqlite_rw_outro", lambda: sqlite3.connect({str(outro_db)!r}))
            tenta("rede", lambda: socket.create_connection(("127.0.0.1", 9), timeout=1))
            tenta("programa", lambda: subprocess.run(["cmd", "/c", "echo", "oi"] if os.name == "nt" else ["echo", "oi"]))
            tenta("os_system", lambda: os.system("echo oi"))
            # o que pode: ler arquivo da cópia, SQLite em memória, git de consulta
            tenta("ler_ok", lambda: (p / "versao.txt").read_text())
            tenta("memoria_ok", lambda: sqlite3.connect(":memory:").execute("CREATE TABLE a(x)"))
            tenta("git_ok", lambda: subprocess.run(["git", "--version", "rev-parse"], capture_output=True))
            # funções de análise de verdade não gravam nada
            tenta("analise_ok", lambda: (t.decks.identificar(["Pikachu ex"]), t.analises.wilson(3, 9),
                                         t.probabilidades.carta(4, 12, False, 2)))
        """)
        bloqueados = ["open_w", "open_a", "open_rplus", "os_open", "write_text", "remove", "rename", "mkdir", "rmtree",
                      "copyfile", "sqlite_rw_copia", "sqlite_rw_outro", "rede", "programa", "os_system"]
        for k in bloqueados:
            self.assertTrue(r[k].startswith("EscritaBloqueada"), f"{k}: {r[k]}")
        for k in ("ler_ok", "memoria_ok", "git_ok", "analise_ok"):
            self.assertEqual(r[k], "PASSOU", f"{k}: {r[k]}")
        self.assertEqual(impressao(pasta), antes, "algum arquivo da cópia mudou")
        self.assertFalse((pasta / "tracker" / "__pycache__").exists(), "o import gravou __pycache__ na cópia")


class Classificacao(unittest.TestCase):
    def test_toda_funcao_publica_do_banco_classificada(self):
        arvore = ast.parse((FONTE / "tracker" / "banco.py").read_text(encoding="utf-8"))
        publicas = {n.name for n in arvore.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")}
        sem = publicas - ponte.FUNCOES_LEITURA_BANCO - ponte.FUNCOES_ESCRITA["banco"]
        self.assertFalse(sem, f"funções novas em banco.py sem classificação leitura/escrita na ponte: {sorted(sem)}")
        self.assertFalse(ponte.FUNCOES_LEITURA_BANCO & ponte.FUNCOES_ESCRITA["banco"])

    def test_escrita_listada_existe(self):
        for modulo, nomes in ponte.FUNCOES_ESCRITA.items():
            codigo = (FONTE / "tracker" / f"{modulo}.py").read_text(encoding="utf-8")
            for n in nomes:
                self.assertRegex(codigo, rf"(?m)^def {n}\(", f"{modulo}.{n} sumiu: revisar a lista de escrita")

    def test_ferramentas_da_skill_classificadas(self):
        import sa_tools
        publicas = {n for n, f in vars(sa_tools).items() if callable(f) and not n.startswith("_")
                    and getattr(f, "__module__", "") == "sa_tools"}
        self.assertEqual(publicas, set(sa_tools.CLASSE), "toda função pública do sa_tools precisa de classe leitura/escrita")
        self.assertTrue(set(sa_tools.CLASSE.values()) <= {"leitura", "escrita"})


class MarcarCopia(Base):
    def test_recusa_porta_errada_e_nao_sobrescreve(self):
        import marcar_copia
        pasta = montar_copia(self.raiz, porta=8765, marca=False)
        with self.assertRaises(ponte.CopiaInvalida):
            marcar_copia.marcar(pasta)
        self.assertFalse((pasta / "dados" / ponte.MARCA_COPIA).exists())
        pasta2 = montar_copia(self.raiz / "b" if (self.raiz / "b").mkdir() is None else self.raiz, marca=False)
        m = marcar_copia.marcar(pasta2, "teste")
        conteudo = m.read_text(encoding="utf-8")
        self.assertEqual(marcar_copia.marcar(pasta2, "outra"), m)
        self.assertEqual(m.read_text(encoding="utf-8"), conteudo)
        ponte.validar_copia(pasta2)   # agora é válida


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=1).result
    print("OK" if r.wasSuccessful() else "FALHOU")
    sys.exit(0 if r.wasSuccessful() else 1)
