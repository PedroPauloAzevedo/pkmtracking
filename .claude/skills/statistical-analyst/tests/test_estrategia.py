"""
Testes das ferramentas estratégicas (`tools/estrategia.py`) e do roteiro P1–P7 (`experiments/p_estrategia.py`).
- Funções: casos montados à mão com resposta conhecida (sem dados do Pedro).
- Roteiro: uma cópia DESCARTÁVEL montada aqui, só com o log de exemplo do repositório repetido (dados sintéticos). Confere que a
  trava de amostra para tudo sem gravar nada e que, forçado com --exploratorio, os 7 experimentos rodam até o fim.
Nenhum teste lê a base real. Uso:  python -I .claude/skills/statistical-analyst/tests/test_estrategia.py
"""
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TOOLS = AQUI.parent / "tools"
EXPER = AQUI.parent / "experiments"
FONTE = Path(os.environ.get("SA_FONTE_TRACKER") or AQUI.parents[3])
sys.path.insert(0, str(TOOLS))
sys.dont_write_bytecode = True
import estrategia as E  # noqa: E402


def hg_ref(total, sucessos, amostra, k):
    """Referência independente (só para o teste): hipergeométrica pela definição."""
    return math.comb(sucessos, k) * math.comb(total - sucessos, amostra - k) / math.comb(total, amostra)


def quadro(turno, pa, pb, destaque=None):
    return {"turno": turno, "destaque": destaque or {}, "estado": {"mesa": {"A": {"premios": pa, "ativo": None, "banco": []},
                                                                          "B": {"premios": pb, "ativo": None, "banco": []}}}}


REP = {"jogadores": ["A", "B"], "quadros": [quadro(1, 6, 6), quadro(2, 6, 6), quadro(3, 4, 6), quadro(4, 4, 5), quadro(5, 2, 5),
                                            quadro(5, 2, 5), quadro(6, 2, 2), quadro(7, 0, 2)]}


class Premios(unittest.TestCase):
    def test_valor(self):
        self.assertEqual([E.valor_premio(x) for x in ("Mega Lopunny ex", "Dragapult ex", "Dreepy", "", "Mega")], [3, 2, 1, 1, 1])

    def test_tomadas_rota_corrida(self):
        tks = E.tomadas(REP)
        self.assertEqual([(x["jogador"], x["n"], x["turno"]) for x in tks], [("A", 2, 3), ("B", 1, 4), ("A", 2, 5), ("B", 3, 6), ("A", 2, 7)])
        self.assertEqual(E.rota_executada(REP), {"A": [2, 2, 2], "B": [1, 3]})
        self.assertEqual(E.mapa([2, 2, 2]), "2-2-2")
        cor = E.corrida(REP)
        self.assertEqual(cor[-1], {"turno": 7, "restantes": {"A": 0, "B": 2}})
        self.assertEqual(len(cor), 7)

    def test_rotas_possiveis(self):
        self.assertEqual(E.rotas_possiveis(6, {2: 3}), [(2, 2, 2)])
        self.assertEqual(E.rotas_possiveis(6, {2: 2}), [])                      # alvos não bastam
        self.assertEqual(set(E.rotas_possiveis(2, {1: 2, 2: 1})), {(1, 1), (1, 2), (2,)})   # 1 e depois 2 também fecha
        self.assertEqual(set(E.rotas_possiveis(3, {1: 1, 3: 1})), {(1, 3), (3,)})   # o último pode passar do necessário
        self.assertEqual(E.rotas_possiveis(0, {1: 1}), [()])
        with self.assertRaises(ValueError):
            E.rotas_possiveis(6, {1: 6, 2: 3, 3: 2}, limite=10)   # muitas rotas: a enumeração para com erro claro


class PremiosChecados(unittest.TestCase):
    def test_formula(self):
        self.assertAlmostEqual(E.premio_checado(53, 1, 6, hg_ref), 6 / 53, places=12)      # 1 cópia fora da mão
        self.assertAlmostEqual(E.premio_checado(60, 4, 7, hg_ref), 1 - math.comb(56, 7) / math.comb(60, 7), places=12)  # 39,95%
        self.assertEqual(E.premio_checado(53, 0, 6, hg_ref), 0.0)
        self.assertAlmostEqual(E.alguma_premiada(53, [1, 1, 2], 6, hg_ref), E.premio_checado(53, 4, 6, hg_ref))
        with self.assertRaises(ValueError):
            E.premio_checado(10, 11, 6, hg_ref)

    def test_igual_a_funcao_do_programa(self):
        sys.path.insert(0, str(FONTE))
        try:
            from tracker import probabilidades   # módulo puro do Coletor (só matemática)
        finally:
            sys.path.remove(str(FONTE))
        for N, m, k in ((53, 1, 6), (53, 4, 6), (40, 3, 2)):
            self.assertAlmostEqual(E.premio_checado(N, m, k, probabilidades.hipergeometrica), E.premio_checado(N, m, k, hg_ref), places=12)

    def test_simulacao(self):
        import random
        rng = random.Random(5)
        baralho = ["X"] * 3 + ["o"] * 50
        n = 40000
        hits = sum("X" in rng.sample(baralho, 6) for _ in range(n))
        self.assertAlmostEqual(hits / n, E.premio_checado(53, 3, 6, hg_ref), delta=0.01)

    def test_mao_inicial_e_zonas(self):
        texto = (FONTE / "exemplos" / "log_de_exemplo.txt").read_text(encoding="utf-8")
        mao = E.mao_inicial(texto, "Ana_TCG")
        self.assertEqual(sum(mao.values()), 7)
        self.assertEqual(mao["Rare Candy"], 1)
        self.assertIsNone(E.mao_inicial(texto, "MistyPsy"))           # mulligan: a mão nova não está no log
        deck = Counter({"Rare Candy": 4, "Iono": 2, "Fire Energy": 54})
        z = E.zonas_desconhecidas(deck, {"Rare Candy": 1, "Fire Energy": 6})
        self.assertEqual(z["N"], 53)
        self.assertEqual(z["m"], {"Rare Candy": 3, "Iono": 2, "Fire Energy": 48})
        with self.assertRaises(ValueError):
            E.zonas_desconhecidas(deck, {"Pikachu": 1})                # carta fora da lista
        with self.assertRaises(ValueError):
            E.zonas_desconhecidas(Counter({"X": 59}), {})


class Trocas(unittest.TestCase):
    def test_trocas_e_eficiencia(self):
        tks = E.tomadas(REP)
        tr = E.trocas(tks, "A")
        self.assertEqual([(x["ganhei"], x["cedi"], x["saldo"], x["aberta"]) for x in tr], [(2, 1, 1, False), (2, 3, -1, False), (2, 0, 2, True)])
        ef = E.eficiencia(tks, "A")
        self.assertIsNone(ef[0]["eficiencia"])
        self.assertAlmostEqual(ef[-1]["eficiencia"], 6 / 4)
        junta = [{"jogador": "A", "n": 1, "turno": 1}, {"jogador": "A", "n": 1, "turno": 3}, {"jogador": "B", "n": 2, "turno": 4}]
        self.assertEqual(E.trocas(junta, "B")[0]["saldo"], 0)      # tomadas seguidas do mesmo lado somam


class Eventos(unittest.TestCase):
    EV = [{"linha": 1, "turno": 1, "jogador": "A", "tipo": "compra"}, {"linha": 2, "turno": 1, "jogador": "A", "tipo": "jogada", "carta": "Iono"},
          {"linha": 3, "turno": 1, "jogador": "A", "tipo": "energia"}, {"linha": 4, "turno": 1, "jogador": "A", "tipo": "ataque"},
          {"linha": 5, "turno": 2, "jogador": "B", "tipo": "compra"}, {"linha": 6, "turno": 2, "jogador": "B", "tipo": "jogada", "carta": "Boss's Orders"},
          {"linha": 7, "turno": 2, "jogador": "B", "tipo": "nocaute"}]

    def test_disrupcao_desenvolvimento_sequencia(self):
        d = E.categorias_disrupcao(self.EV)
        self.assertEqual([(x["jogador"], x["categoria"]) for x in d], [("A", "mão"), ("B", "puxar alvo")])
        self.assertEqual(E.categorias_disrupcao(self.EV, {"Iono": "x"})[0]["categoria"], "x")
        dv = E.desenvolvimento(self.EV, "B", [2])
        self.assertEqual((dv["acoes"], dv["atacou"]), (2, False))
        self.assertEqual(E.turnos_do_jogador(self.EV, "A"), [1])
        seq = E.acoes_do_turno(self.EV, "A", 1)
        self.assertEqual(seq, ["compra", "jogada", "energia", "ataque"])
        self.assertEqual(E.ngramas(seq, 2)[("jogada", "energia")], 1)
        self.assertTrue(E.antes_de(seq, "jogada", "energia"))
        self.assertIsNone(E.antes_de(seq, "recuo", "energia"))
        self.assertEqual(E.fins([{"motivo": "Desistência"}, {"motivo": "Desistência"}, None]), Counter({"Desistência": 2, "?": 1}))


class Estatistica(unittest.TestCase):
    def test_kaplan_meier(self):
        km = E.kaplan_meier([1, 2, 2, 3], [1, 1, 0, 1])
        self.assertEqual([round(x["S"], 6) for x in km], [0.75, 0.5, 0.0])
        self.assertEqual([x["em_risco"] for x in km], [4, 3, 1])
        self.assertEqual(E.kaplan_meier([5, 5], [0, 0])[-1]["S"], 1.0)     # só censura: S fica 1
        with self.assertRaises(ValueError):
            E.kaplan_meier([1], [])

    def test_diferenca_por_estrato(self):
        linhas = [("a", True, 3), ("a", False, 1), ("a", True, 5), ("b", True, 10), ("c", False, 7)]
        r = E.diferenca_por_estrato(linhas)
        self.assertAlmostEqual(r["diferenca"], 3.0)    # estrato a: (3+5)/2 − 1 = 3, peso 2; b e c sem par
        self.assertEqual((r["estratos_usados"], r["estratos_fora"], r["tratados"]), (1, 2, 2))
        self.assertIsNone(E.diferenca_por_estrato([("a", True, 1)])["diferenca"])

    def test_classes(self):
        publicas = {n for n, f in vars(E).items() if callable(f) and not n.startswith("_") and getattr(f, "__module__", "") == "estrategia"}
        self.assertEqual(publicas, set(E.CLASSE))
        self.assertEqual(set(E.CLASSE.values()), {"leitura"})


def montar_copia_sintetica(raiz: Path, n_partidas: int) -> Path:
    """Cópia descartável com o tracker do repositório e n cópias do log de exemplo (prêmios de quem exportou com nome)."""
    pasta = raiz / "copia"
    shutil.copytree(FONTE / "tracker", pasta / "tracker", ignore=shutil.ignore_patterns("__pycache__"))
    (pasta / "versao.txt").write_text("teste\n", encoding="utf-8")
    texto = (FONTE / "exemplos" / "log_de_exemplo.txt").read_text(encoding="utf-8")

    def nomes(m):
        n = 1 if m.group(2) == "a Prize card" else int(m.group(2).split()[0])
        return m.group(0) + "".join(f"\nArven was added to {m.group(1)}'s hand." for _ in range(n))
    texto = re.sub(r"^(Ana_TCG) took (a Prize card|\d+ Prize cards)\.", nomes, texto, flags=re.M)
    (raiz / "log.txt").write_text(texto, encoding="utf-8")
    codigo = textwrap.dedent(f"""
        import json, sys
        sys.path.insert(0, {str(pasta)!r})
        from tracker import banco, config, leitor
        banco.iniciar()
        regras = config.ler_regras()
        texto = open({str(raiz / 'log.txt')!r}, encoding='utf-8').read()
        dados = leitor.ler_partida(texto, regras)
        lista = "Pokémon: 8\\n4 Charmander OBF 26\\n4 Pidgey OBF 162\\nTrainer: 16\\n4 Nest Ball SVI 181\\n4 Rare Candy SVI 191\\n4 Arven SVI 166\\n4 Iono PAL 185\\nEnergy: 36\\n36 Fire Energy SVE 2\\n"
        with banco.conectar() as con:
            con.execute("INSERT INTO meus_decks(nome, arquetipo, lista, ativo) VALUES ('teste', 'charizard-ex', ?, 1)", (lista,))
            for i in range({n_partidas}):
                con.execute("INSERT INTO partidas(hash, capturada_em, origem, texto, dados_json, deck_id) VALUES (?, ?, 'manual', ?, ?, 1)",
                            (f"h{{i}}", f"2026-10-{{1 + i % 28:02d}}T10:{{i % 60:02d}}:00", texto, json.dumps(dados)))
        print("ok")
    """)
    r = subprocess.run([sys.executable, "-I", "-c", codigo], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError(r.stderr[-1500:])
    cfg = pasta / "dados" / "config.json"
    c = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
    c["porta"] = 8799
    cfg.write_text(json.dumps(c), encoding="utf-8")
    (pasta / "dados" / "COPIA_DE_TESTE.json").write_text(json.dumps({"copia_de_teste": True}), encoding="utf-8")
    return pasta


class Roteiro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.raiz = Path(cls._tmp.name)
        cls.pasta = montar_copia_sintetica(cls.raiz, 12)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def rodar(self, *args):
        saida = self.raiz / f"res_{len(list(self.raiz.glob('res_*')))}"
        saida.mkdir()
        env = dict(os.environ, SA_SAIDA=str(saida))
        env.pop("SA_PASTAS_PROTEGIDAS", None)
        r = subprocess.run([sys.executable, "-I", str(EXPER / "p_estrategia.py"), str(self.pasta), *args], capture_output=True,
                           text=True, timeout=600, env=env, cwd=str(self.raiz))
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return r.stdout, sorted(saida.glob("*.json"))

    def test_trava_de_amostra(self):
        out, arqs = self.rodar("todos")
        self.assertEqual(out.count("NÃO foi rodado"), 7, out)
        self.assertEqual(arqs, [], "abaixo do mínimo nada pode ser gravado")

    def test_exploratorio_roda_tudo(self):
        out, arqs = self.rodar("todos", "--exploratorio")
        self.assertEqual(len(arqs), 7, out)
        for a in arqs:
            reg = json.loads(a.read_text(encoding="utf-8"))
            self.assertTrue(reg["resultado"]["exploratorio"], a.name)
            self.assertNotIn("erro", reg["resultado"], (a.name, reg["resultado"]))
        p1 = json.loads(next(a for a in arqs if a.name.startswith("p1_")).read_text(encoding="utf-8"))["resultado"]
        self.assertEqual(p1["rotas_executadas_vitorias_por_premios"], {"1-1-2-2": 12})
        p3 = json.loads(next(a for a in arqs if a.name.startswith("p3_")).read_text(encoding="utf-8"))["resultado"]
        self.assertEqual(p3["partidas_usadas"], 12)

    def test_minimo_manual(self):
        out, arqs = self.rodar("p1", "--minimo", "5")
        self.assertIn("p1: 12", out)
        self.assertEqual(len(arqs), 1)


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=1).result
    print("OK" if r.wasSuccessful() else "FALHOU")
    sys.exit(0 if r.wasSuccessful() else 1)
