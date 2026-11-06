"""
Testes das ferramentas novas da Skill (valores conhecidos, casos extremos, consistência matemática).
Uso:  python -I .claude/skills/statistical-analyst/tests/test_sa_tools.py
(só biblioteca padrão; não precisa do programa nem de dados)
"""
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import sa_tools as T  # noqa: E402


class Previsoes(unittest.TestCase):
    def test_chute_50(self):
        pares = [(0.5, 1), (0.5, 0)] * 10
        self.assertAlmostEqual(T.logloss(pares), math.log(2), places=12)
        self.assertAlmostEqual(T.brier(pares), 0.25, places=12)

    def test_previsao_perfeita_e_limites(self):
        self.assertAlmostEqual(T.logloss([(1.0, 1), (0.0, 0)]), 0.0, places=6)
        self.assertGreater(T.logloss([(0.0, 1)]), 20)  # errou com certeza: perda grande, mas finita (eps)

    def test_entradas_invalidas(self):
        for ruim in ([], [(1.2, 1)], [(0.5, 2)]):
            with self.assertRaises(ValueError):
                T.logloss(ruim)

    def test_calibracao(self):
        rng = random.Random(1)
        pares = [(p, 1 if rng.random() < p else 0) for p in (rng.random() for _ in range(40000))]
        self.assertLess(T.calibracao(pares)["ece"], 0.015)      # calibrado de propósito
        exagerado = [(min(1, p * 1.6), y) for p, y in pares]
        self.assertGreater(T.calibracao(exagerado)["ece"], 0.1)  # confiança exagerada aparece


class Agrupado(unittest.TestCase):
    def test_bootstrap_reprodutivel_e_contem_media(self):
        rng = random.Random(2)
        g = {i: [rng.random() for _ in range(5)] for i in range(40)}
        a = T.bootstrap_agrupado(g, lambda xs: sum(xs) / len(xs), 500, semente=7)
        b = T.bootstrap_agrupado(g, lambda xs: sum(xs) / len(xs), 500, semente=7)
        self.assertEqual(a, b)
        self.assertTrue(a["baixo"] <= a["estimativa"] <= a["alto"])

    def test_bootstrap_agrupado_mais_largo_com_dependencia(self):
        # grupos em que todas as linhas são iguais: a faixa por grupo deve ser bem mais larga que tratando linhas soltas
        rng = random.Random(3)
        g = {i: [rng.random()] * 10 for i in range(50)}
        agr = T.bootstrap_agrupado(g, lambda xs: sum(xs) / len(xs), 800, semente=1)
        solto = T.bootstrap_agrupado({j: [x] for j, x in enumerate(x for v in g.values() for x in v)},
                                     lambda xs: sum(xs) / len(xs), 800, semente=1)
        self.assertGreater(agr["alto"] - agr["baixo"], 2 * (solto["alto"] - solto["baixo"]))

    def test_diferenca_pareada(self):
        rng = random.Random(4)
        linhas = [(i // 10, 0.60 + rng.gauss(0, 0.05), 0.70 + rng.gauss(0, 0.05)) for i in range(400)]
        r = T.diferenca_pareada(linhas, 500)
        self.assertTrue(r["provavel"] and r["alto"] < 0)
        iguais = [(i // 10, x, x) for i, x in enumerate(rng.random() for _ in range(200))]
        self.assertFalse(T.diferenca_pareada(iguais, 200)["provavel"])

    def test_icc(self):
        rng = random.Random(5)
        indep = [[1 if rng.random() < 0.5 else 0 for _ in range(8)] for _ in range(3000)]
        self.assertLess(abs(T.icc_binario(indep)), 0.03)
        juntos = [[1] * 8 if rng.random() < 0.5 else [0] * 8 for _ in range(500)]
        self.assertGreater(T.icc_binario(juntos), 0.95)
        # habilidade diferente por jogador (p ~ Beta): ICC teórico = 1/(a+b+1) = 1/11 com a=b=5
        hab = []
        for _ in range(6000):
            p = rng.betavariate(5, 5)
            hab.append([1 if rng.random() < p else 0 for _ in range(8)])
        self.assertAlmostEqual(T.icc_binario(hab), 1 / 11, delta=0.02)
        with self.assertRaises(ValueError):
            T.icc_binario([[1]])

    def test_efeito_desenho_e_z(self):
        self.assertAlmostEqual(T.efeito_desenho(9, 0.1), 1.8)
        self.assertEqual(T.efeito_desenho(1, 0.5), 1.0)
        p1 = T.z_duas_proporcoes_efetivo(60, 100, 50, 100)
        self.assertAlmostEqual(p1, 0.1552, places=3)          # igual a variantes._valor_p
        self.assertGreater(T.z_duas_proporcoes_efetivo(60, 100, 50, 100, 2.0), p1)
        self.assertIsNone(T.z_duas_proporcoes_efetivo(0, 0, 1, 2))


class Multiplos(unittest.TestCase):
    def test_holm_bh_exemplo_conhecido(self):
        p = [0.01, 0.04, 0.03, 0.005]
        self.assertEqual([round(x, 4) for x in T.holm(p)], [0.03, 0.06, 0.06, 0.02])
        self.assertEqual([round(x, 4) for x in T.benjamini_hochberg(p)], [0.02, 0.04, 0.04, 0.02])
        with self.assertRaises(ValueError):
            T.holm([1.5])

    def test_ajuste_nunca_diminui(self):
        rng = random.Random(6)
        p = [rng.random() for _ in range(50)]
        self.assertTrue(all(a >= b - 1e-15 for a, b in zip(T.holm(p), p)))
        self.assertTrue(all(a >= b - 1e-15 for a, b in zip(T.benjamini_hochberg(p), p)))


class MelhorDe3(unittest.TestCase):
    def test_valores(self):
        self.assertAlmostEqual(T.bo3_de_jogo(0.6), 0.648)
        self.assertEqual(T.bo3_de_jogo(0.5), 0.5)
        self.assertEqual((T.bo3_de_jogo(0), T.bo3_de_jogo(1)), (0, 1))

    def test_simetria_e_inversa(self):
        for q in (0.1, 0.33, 0.5, 0.71, 0.9):
            self.assertAlmostEqual(T.bo3_de_jogo(q) + T.bo3_de_jogo(1 - q), 1.0, places=12)
            self.assertAlmostEqual(T.jogo_de_bo3(T.bo3_de_jogo(q)), q, places=9)

    def test_simulacao(self):
        rng = random.Random(8)
        n = 100000
        v = sum(1 for _ in range(n) if sum(rng.random() < 0.6 for _ in range(3)) >= 2)  # melhor de 3 = maioria de 3
        self.assertAlmostEqual(v / n, T.bo3_de_jogo(0.6), delta=0.006)


class Registro(unittest.TestCase):
    def test_nao_sobrescreve(self):
        with tempfile.TemporaryDirectory() as d:
            a = T.registrar("x", {"v": 1}, Path(d), Path(d) / "res", semente=1)
            b = T.registrar("x", {"v": 2}, Path(d), Path(d) / "res", semente=1)
            self.assertNotEqual(a, b)
            self.assertTrue(a.exists() and b.exists())

    def test_sa_saida_desvia(self):
        import os
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outro:
            os.environ["SA_SAIDA"] = outro
            try:
                a = T.registrar("y", {}, Path(d), Path(d) / "res")
            finally:
                del os.environ["SA_SAIDA"]
            self.assertEqual(a.parent, Path(outro))
            self.assertFalse((Path(d) / "res").exists())


class Reprodutibilidade(unittest.TestCase):
    """Registro completo dos experimentos (formato 2, revisto em 06/11/2026)."""

    def _programa(self, raiz: Path, linhas=(("0001", "Teste", "2026-10-01"), ("0002", "Nick Secreto Xyz", "2026-10-08")),
                  versao=True) -> Path:
        import sqlite3
        p = raiz / "prog"
        (p / "tracker").mkdir(parents=True)
        (p / "tracker" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (p / "dados").mkdir()
        if versao:
            (p / "versao.txt").write_text("2026.01.01-1\n", encoding="utf-8")
        con = sqlite3.connect(p / "dados" / "tracker.db")
        con.execute("CREATE TABLE torneios (id TEXT, nome TEXT, data TEXT)")
        con.execute("CREATE TABLE partidas (id INTEGER, capturada_em TEXT)")
        con.executemany("INSERT INTO torneios VALUES (?,?,?)", linhas)
        con.commit()
        con.close()
        return p

    def _reg(self, prog, saida, script, **kw):
        import json
        arq = T.registrar("exp", kw.pop("resultado", {"acerto": 0.5}), prog, saida, script=script, **kw)
        return json.loads(arq.read_text(encoding="utf-8")), arq

    def _script(self, raiz, texto="print(1)\n", nome="exp.py"):
        s = raiz / nome
        s.write_text(texto, encoding="utf-8")
        return s

    def test_mesmos_dados_e_parametros_reproduzem(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog, s = self._programa(d), self._script(d)
            a, fa = self._reg(prog, d / "r", s, semente=7, parametros={"k": 3})
            b, fb = self._reg(prog, d / "r", s, semente=7, parametros={"k": 3})
            self.assertNotEqual(fa, fb)                                   # dois arquivos, nenhum sobrescrito
            self.assertNotEqual(a["id"], b["id"])
            for chave in ("semente", "parametros", "resultado_sha256"):
                self.assertEqual(a[chave], b[chave])
            self.assertEqual(a["dados"]["impressao"], b["dados"]["impressao"])
            self.assertEqual(a["codigo"]["script"]["sha256"], b["codigo"]["script"]["sha256"])
            self.assertEqual(a["formato_registro"], 2)

    def test_impressao_independe_da_ordem_de_insercao(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            l = (("0001", "A", "2026-10-01"), ("0002", "B", "2026-10-08"), ("0003", "C", "2026-10-09"))
            i1 = T.impressao_banco(self._programa(Path(d1), l) / "dados" / "tracker.db")
            i2 = T.impressao_banco(self._programa(Path(d2), tuple(reversed(l))) / "dados" / "tracker.db")
            self.assertEqual(i1["impressao"], i2["impressao"])

    def test_dados_diferentes_mudam_a_impressao(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            i1 = T.impressao_banco(self._programa(Path(d1)) / "dados" / "tracker.db")
            # mesma contagem e mesmas datas, só um nome diferente: a impressão antiga (contagens) não via; a nova vê
            i2 = T.impressao_banco(self._programa(Path(d2), (("0001", "Teste", "2026-10-01"),
                                                             ("0002", "Outro", "2026-10-08"))) / "dados" / "tracker.db")
            self.assertNotEqual(i1["impressao"], i2["impressao"])
            self.assertEqual(i1["impressao_contagens"], i2["impressao_contagens"])   # a limitação da versão anterior

    def test_mudanca_de_parametro_registrada(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog, s = self._programa(d), self._script(d)
            a, _ = self._reg(prog, d / "r", s, semente=7, parametros={"k": 3})
            b, _ = self._reg(prog, d / "r", s, semente=8, parametros={"k": 5}, filtros={"so_standard": True})
            self.assertEqual((a["semente"], a["parametros"]["k"]), (7, 3))
            self.assertEqual((b["semente"], b["parametros"]["k"], b["filtros"]["so_standard"]), (8, 5, True))

    def test_mudanca_no_script_muda_o_hash(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog = self._programa(d)
            a, _ = self._reg(prog, d / "r", self._script(d, "print(1)\n", "e1.py"))
            b, _ = self._reg(prog, d / "r", self._script(d, "print(2)\n", "e2.py"))
            self.assertNotEqual(a["codigo"]["script"]["sha256"], b["codigo"]["script"]["sha256"])

    def test_versao_ausente_registrada(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog = self._programa(d, versao=False)
            a, _ = self._reg(prog, d / "r", d / "nao_existe.py", pacotes=("pacote_que_nao_existe_xyz",))
            self.assertIsNone(a["codigo"]["coletor"]["versao"])
            texto = " | ".join(a["limitacoes"])
            for trecho in ("versao.txt do Coletor ausente", "script do experimento não identificado",
                           "pacote pacote_que_nao_existe_xyz ausente", "sem git", "tabela t_listas ausente"):
                self.assertIn(trecho, texto)
            self.assertEqual(a["ambiente"]["pacotes"]["pacote_que_nao_existe_xyz"], "ausente")
            self.assertTrue(a["ambiente"]["python"])

    def test_sem_dado_pessoal_no_registro(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog = self._programa(d)
            _, arq = self._reg(prog, d / "r", self._script(d))
            self.assertNotIn("Nick Secreto Xyz", arq.read_text(encoding="utf-8"))
            self.assertNotIn(str(d), arq.read_text(encoding="utf-8"))

    def test_arquivos_de_saida_e_resultado(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            prog = self._programa(d)
            extra = d / "tabela.csv"
            extra.write_text("a,b\n1,2\n", encoding="utf-8")
            a, _ = self._reg(prog, d / "r", self._script(d), arquivos_saida=[extra, d / "sumiu.csv"],
                             dados_usados={"n_registros": 2, "impressao": T.impressao_objeto([{"x": 1}, {"x": 2}])})
            self.assertEqual(a["arquivos_saida"][0]["arquivo"], "tabela.csv")
            self.assertEqual(len(a["arquivos_saida"][0]["sha256"]), 64)
            self.assertIn("arquivo de saída não encontrado: sumiu.csv", a["limitacoes"])
            self.assertEqual(a["dados_usados"]["n_registros"], 2)

    def test_impressao_objeto_canonica(self):
        self.assertEqual(T.impressao_objeto({"b": {3, 1, 2}, "a": [0.1, 2]}), T.impressao_objeto({"a": [0.1, 2], "b": {2, 1, 3}}))
        self.assertNotEqual(T.impressao_objeto([1, 2]), T.impressao_objeto([2, 1]))   # lista: a ordem importa
        # diferença só na última casa (ordem de soma): igual com 12 algarismos, diferente no hash exato
        self.assertNotEqual(T.impressao_objeto([0.16518185934130128]), T.impressao_objeto([0.1651818593413013]))
        self.assertEqual(T.impressao_objeto([0.16518185934130128], 12), T.impressao_objeto([0.1651818593413013], 12))
        self.assertNotEqual(T.impressao_objeto([0.1651], 12), T.impressao_objeto([0.1652], 12))


class Classes(unittest.TestCase):
    def test_leitura_nao_grava(self):
        """Toda ferramenta 'leitura' roda sem abrir arquivo para gravar (vigia de auditoria só observa neste processo)."""
        import sys as _s
        gravou = []

        def obs(ev, args):
            if ev == "open" and len(args) > 1 and isinstance(args[1], str) and any(c in args[1] for c in "wax+"):
                gravou.append(args[0])
        _s.addaudithook(obs)
        pares = [(0.3, 0), (0.7, 1), (0.6, 1), (0.2, 0)]
        T.logloss(pares), T.brier(pares), T.calibracao(pares), T.holm([0.01, 0.2]), T.benjamini_hochberg([0.01, 0.2])
        T.bootstrap_agrupado({"a": [1, 0], "b": [1, 1]}, lambda x: sum(x) / len(x), 20)
        T.diferenca_pareada([("a", 0.1, 0.2), ("b", 0.3, 0.2)], 20), T.icc_binario([[1, 0, 1], [0, 0, 1]])
        T.efeito_desenho(3, 0.1), T.z_duas_proporcoes_efetivo(6, 10, 5, 10), T.bo3_de_jogo(0.6), T.jogo_de_bo3(0.6)
        T.impressao_objeto([1]), T.ambiente()
        T.ece(pares, 2, "massa"), T.recalibracao_logistica(pares), T.calibracao_detalhada(pares, repeticoes=30)
        T.calibracao_por_grupo([("a", 0.3, 0), ("a", 0.6, 1), ("b", 0.5, 1)], minimo=1)
        self.assertEqual(gravou, [])


class CalibracaoAFundo(unittest.TestCase):
    def setUp(self):
        rng = random.Random(3)
        self.ps = [rng.uniform(0.05, 0.95) for _ in range(20000)]
        self.cal = [(p, 1 if rng.random() < p else 0) for p in self.ps]
        self.rng = rng

    def test_recalibracao_recupera_parametros(self):
        r = T.recalibracao_logistica(self.cal)
        self.assertAlmostEqual(r["inclinacao"], 1.0, delta=4 * r["ep_inclinacao"])
        self.assertAlmostEqual(r["intercepto"], 0.0, delta=4 * r["ep_intercepto"])
        # confiança exagerada: p' = logística(2·logit p) -> inclinação ≈ 0,5
        exag = [(1 / (1 + math.exp(-2 * math.log(p / (1 - p)))), y) for p, y in self.cal]
        self.assertAlmostEqual(T.recalibracao_logistica(exag)["inclinacao"], 0.5, delta=0.05)

    def test_recalibracao_com_separacao_perfeita(self):
        # antes de 06/11 (tarde) estourava com OverflowError; agora termina e avisa que não convergiu
        r = T.recalibracao_logistica([(0.9, 1), (0.8, 1), (0.2, 0), (0.1, 0)])
        self.assertFalse(r["convergiu"])
        self.assertTrue(math.isfinite(r["inclinacao"]))
        self.assertTrue(T.recalibracao_logistica(self.cal)["convergiu"])

    def test_ece_massa_e_largura(self):
        for esquema in ("largura", "massa"):
            e = T.ece(self.cal, 10, esquema)
            self.assertLess(e["ece"], 0.03)
            self.assertEqual(sum(f["n"] for f in e["faixas"]), len(self.cal))
        m = T.ece(self.cal, 10, "massa")
        self.assertLessEqual(max(f["n"] for f in m["faixas"]) - m["n_min"], 1)   # mesma massa
        with self.assertRaises(ValueError):
            T.ece(self.cal, 10, "outro")

    def test_ece_baixo_nao_prova_calibracao(self):
        # o modelo diz 50% para todos: no total acerta (ECE ~ 0), mas o grupo A vence 70% e o B, 30% -> descalibrado por grupo
        linhas = []
        for i in range(20000):
            g = "A" if i % 2 else "B"
            y = 1 if self.rng.random() < (0.7 if g == "A" else 0.3) else 0
            linhas.append((g, 0.5, y))
        self.assertLess(T.ece([(p, y) for _, p, y in linhas], 10)["ece"], 0.02)
        por = T.calibracao_por_grupo(linhas)
        self.assertFalse(por["A"]["previsto_dentro_da_faixa"])
        self.assertFalse(por["B"]["previsto_dentro_da_faixa"])

    def test_piso_de_ruido_e_ic(self):
        pequeno = self.cal[:300]
        r = T.calibracao_detalhada(pequeno, grupos=[i % 15 for i in range(300)], faixas=(5, 20), repeticoes=150)
        self.assertGreater(r["por_faixas"][20]["piso_ruido_medio"], r["por_faixas"][5]["piso_ruido_medio"])  # mais faixas, mais ruído
        self.assertLessEqual(r["ece10_ic95"]["baixo"], r["ece10_ic95"]["alto"])
        self.assertEqual(r["ece10_ic95"]["agrupado_por"], "grupo")

    def test_por_grupo(self):
        linhas = [("bom", p, y) for p, y in self.cal[:3000]] + [("ruim", min(0.99, p + 0.2), y) for p, y in self.cal[3000:6000]]
        g = T.calibracao_por_grupo(linhas)
        self.assertTrue(g["bom"]["previsto_dentro_da_faixa"])
        self.assertFalse(g["ruim"]["previsto_dentro_da_faixa"])
        self.assertLess(g["ruim"]["diferenca"], -0.1)


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=1).result
    print("OK" if r.wasSuccessful() else "FALHOU")
    sys.exit(0 if r.wasSuccessful() else 1)
