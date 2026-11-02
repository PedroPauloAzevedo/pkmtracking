"""
EXPERIMENTO 3: estimar "deck A vence deck B" com poucos jogos.

Compara, prevendo as partidas dos torneios MAIS NOVOS só com os dados dos mais antigos:
  1. atual      - taxa bruta do confronto (vitórias / jogos); sem jogos, 50%;
  2. laplace    - taxa bruta com 1 vitória e 1 derrota "imaginárias";
  3. forca      - só a força geral de cada deck (modelo de Bradley-Terry), ignorando o confronto;
  4. ajustada   - confronto puxado para a previsão da força geral, com peso k (empirical Bayes):
                  p = (vitórias + k * força) / (jogos + k); k escolhido nos próprios dados de treino.
Métricas: log-loss e Brier (menor é melhor; medem se a probabilidade prevista estava certa) e acerto.
Uso:  python testes/experimentos/e3_matchups.py <pasta do programa com dados>
"""
import math
import sys
from collections import defaultdict

sys.path.insert(0, sys.argv[1])
from tracker import banco  # noqa: E402

partidas = banco.consultar(
    "SELECT p.arq1, p.arq2, p.res1, t.data, t.id FROM t_partidas p JOIN torneios t ON t.id = p.torneio "
    "WHERE p.arq1 != '' AND p.arq2 != '' AND p.arq1 != p.arq2 AND p.res1 IN ('W', 'L') "
    "AND COALESCE(t.formato, '') IN ('', 'standard')")
torneios = sorted({p["id"]: p["data"] or "" for p in partidas}.items(), key=lambda x: x[1])
ids = [t for t, _ in torneios]
corte = int(len(ids) * 0.7)
treino_ids, teste_ids = set(ids[:corte]), set(ids[corte:])
treino = [p for p in partidas if p["id"] in treino_ids]
teste = [p for p in partidas if p["id"] in teste_ids]
print(f"{len(partidas)} partidas (sem espelho, sem empate) em {len(ids)} torneios; treino {len(treino)}, teste {len(teste)}")


def confrontos(ps):
    c = defaultdict(lambda: [0, 0])  # (a, b) -> [vitórias de a, jogos]
    for p in ps:
        a, b, venceu = p["arq1"], p["arq2"], p["res1"] == "W"
        c[(a, b)][0] += venceu
        c[(a, b)][1] += 1
        c[(b, a)][0] += not venceu
        c[(b, a)][1] += 1
    return c


def bradley_terry(ps, iteracoes=200, prior=2.0):
    """Força de cada deck (algoritmo MM de Hunter), com um pouco de puxão para a média (prior) para decks raros."""
    vit, jogos = defaultdict(float), defaultdict(lambda: defaultdict(float))
    for p in ps:
        a, b = p["arq1"], p["arq2"]
        vit[a if p["res1"] == "W" else b] += 1
        jogos[a][b] += 1
        jogos[b][a] += 1
    decks = list(jogos)
    s = {d: 1.0 for d in decks}
    for _ in range(iteracoes):
        novo = {}
        for d in decks:
            den = sum(n / (s[d] + s[o]) for o, n in jogos[d].items()) + prior / (s[d] + 1.0)
            novo[d] = (vit[d] + prior / 2) / den
        media = math.exp(sum(math.log(v) for v in novo.values()) / len(novo))
        s = {d: v / media for d, v in novo.items()}
    return s


def modelo(ps, k):
    c, s = confrontos(ps), bradley_terry(ps)

    def prever(a, b, tipo):
        v, n = c.get((a, b), (0, 0))
        sa, sb = s.get(a, 1.0), s.get(b, 1.0)
        forca = sa / (sa + sb)
        if tipo == "atual":
            return v / n if n else 0.5
        if tipo == "laplace":
            return (v + 1) / (n + 2)
        if tipo == "forca":
            return forca
        return (v + k * forca) / (n + k)
    return prever


def avaliar(prever, ps, tipo, filtro=None):
    ll = br = ac = n = 0
    for p in ps:
        if filtro and not filtro(p):
            continue
        q = min(max(prever(p["arq1"], p["arq2"], tipo), 0.01), 0.99)
        y = 1.0 if p["res1"] == "W" else 0.0
        ll -= y * math.log(q) + (1 - y) * math.log(1 - q)
        br += (q - y) ** 2
        ac += (q > 0.5) == (y == 1.0) if q != 0.5 else 0.5
        n += 1
    return ll / max(n, 1), br / max(n, 1), ac / max(n, 1), n


# escolhe k só com o treino: treina na parte antiga do treino, valida na parte nova do treino
ids_t = ids[:corte]
sub_corte = int(len(ids_t) * 0.7)
sub_tr = [p for p in treino if p["id"] in set(ids_t[:sub_corte])]
sub_va = [p for p in treino if p["id"] in set(ids_t[sub_corte:])]
melhor_k = min((avaliar(modelo(sub_tr, k), sub_va, "ajustada")[0], k) for k in (1, 2, 4, 6, 8, 12, 16, 24, 32, 48))[1]
print(f"k escolhido no treino: {melhor_k}")

prever = modelo(treino, melhor_k)
c_treino = confrontos(treino)
poucos = lambda p: c_treino.get((p["arq1"], p["arq2"]), (0, 0))[1] < 10
for titulo, filtro in (("Todas as partidas de teste", None), ("Só confrontos com menos de 10 jogos no treino", poucos)):
    print(f"\n{titulo}")
    print(f"{'método':>10} | {'log-loss':>8} | {'Brier':>6} | {'acerto':>6} | partidas")
    for tipo in ("atual", "laplace", "forca", "ajustada"):
        ll, br, ac, n = avaliar(prever, teste, tipo, filtro)
        print(f"{tipo:>10} | {ll:8.4f} | {br:.4f} | {100 * ac:5.1f}% | {n}")
print("\nReferência: prever sempre 50% dá log-loss 0,6931 e Brier 0,2500.")
