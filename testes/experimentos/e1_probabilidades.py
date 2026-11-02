"""
EXPERIMENTO 1: as contas exatas de tracker/probabilidades.py batem com uma simulação?

Embaralha um deck de 60 cartas muitas vezes, seguindo as regras (mulligan até ter Básico,
6 prêmios, compras), e compara a frequência observada com a conta exata.
Uso:  python testes/experimentos/e1_probabilidades.py <pasta do programa> [simulações]
"""
import random
import sys
import time

sys.path.insert(0, sys.argv[1])
from tracker import probabilidades as pr  # noqa: E402

N = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
random.seed(42)

# deck de teste: 12 Básicos (4 A, 4 B, 4 C), um treinador X com 4 cópias, uma carta Y com 1 cópia, resto
deck = ["A"] * 4 + ["B"] * 4 + ["C"] * 4 + ["X"] * 4 + ["Y"] + ["E"] * 9 + ["-"] * 34  # E: Energia com 9 cópias (mais que os 6 prêmios)
basicos = {"A", "B", "C"}
assert len(deck) == 60


def simular():
    cont = {"mull": 0, "maos": 0, "X_mao": 0, "X_t2": 0, "Y_todas_premio": 0, "X_alguma_premio": 0, "A_mao": 0, "combo": 0,
            "E_mao": 0, "E_alguma_premio": 0}
    for _ in range(N):
        while True:
            random.shuffle(deck)
            cont["maos"] += 1
            if any(c in basicos for c in deck[:7]):
                break
            cont["mull"] += 1
        mao, premios, compras = deck[:7], deck[7:13], deck[13:15]  # 2 compras = até o seu 2º turno
        vistas = mao + compras
        cont["X_mao"] += "X" in mao
        cont["A_mao"] += "A" in mao
        cont["X_t2"] += "X" in vistas
        cont["Y_todas_premio"] += "Y" in premios
        cont["X_alguma_premio"] += "X" in premios
        cont["combo"] += ("X" in vistas) and ("Y" in vistas)
        cont["E_mao"] += "E" in mao
        cont["E_alguma_premio"] += "E" in premios
    return cont


t0 = time.time()
c = simular()
t_sim = time.time() - t0
t0 = time.time()
x = pr.carta(4, 12, False, 2)
a = pr.carta(4, 12, True, 0)
y = pr.carta(1, 12, False, 0)
comb_ = pr.combo(4, 1, 12, compras=2)
mull = pr.mulligan(12)
e = pr.carta(9, 12, False, 0)  # antes dava erro: mais cópias do que prêmios
t_exato = time.time() - t0

linhas = [
    ("Mulligan (12 Básicos)", mull, c["mull"] / c["maos"]),
    ("X (4 cópias) na mão inicial", x["na_mao"], c["X_mao"] / N),
    ("Básico A (4 cópias) na mão", a["na_mao"], c["A_mao"] / N),
    ("X até o 2º turno (mão + 2 compras)", x["ate_compras"], c["X_t2"] / N),
    ("Y (1 cópia) presa nos prêmios", y["todas_premio"], c["Y_todas_premio"] / N),
    ("X: alguma cópia nos prêmios", x["alguma_premio"], c["X_alguma_premio"] / N),
    ("Combo X e Y até o 2º turno", comb_, c["combo"] / N),
    ("Energia (9 cópias) na mão inicial", e["na_mao"], c["E_mao"] / N),
    ("Energia: alguma cópia nos prêmios", e["alguma_premio"], c["E_alguma_premio"] / N),
]
pior = 0.0
print(f"{N} partidas simuladas em {t_sim:.1f} s; contas exatas em {1000 * t_exato:.1f} ms\n")
print(f"{'Medida':40} {'exato':>8} {'simulado':>9} {'diferença':>10}")
for nome, ex, sim in linhas:
    erro = sim - ex
    margem = 4 * (ex * (1 - ex) / N) ** 0.5 + 1e-9  # 4 desvios-padrão da simulação
    pior = max(pior, abs(erro) / margem)
    print(f"{nome:40} {100 * ex:7.2f}% {100 * sim:8.2f}% {100 * erro:+9.2f} pp")
print("\nResultado:", "APROVADO (todas as diferenças dentro do ruído da simulação)" if pior < 1 else "REPROVADO")
