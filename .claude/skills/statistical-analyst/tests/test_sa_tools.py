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


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=1).result
    print("OK" if r.wasSuccessful() else "FALHOU")
    sys.exit(0 if r.wasSuccessful() else 1)
