"""
FERRAMENTAS DA SKILL STATISTICAL ANALYST (só biblioteca padrão do Python, como o programa).

Aqui ficam APENAS as contas que o Coletor ainda não tem. O que já existe no programa é usado de lá (ver `ponte.py` e
`knowledge/KNOWN_METHODS.md`): Wilson (`analises.wilson`), hipergeométrica (`probabilidades`), Bradley-Terry e confronto
ajustado (`estrategia`), regressão (`regressao.ajustar`), teste de duas proporções (`variantes._valor_p`).

Conteúdo:
  logloss, brier, calibracao        - qualidade de previsões de probabilidade (menor = melhor; calibração = "70% acontece 70%?")
  bootstrap_agrupado                - faixa de incerteza reamostrando GRUPOS (torneios, jogadores), não linhas soltas
  diferenca_pareada                 - A melhor que B? diferença média de perda por linha com bootstrap agrupado
  icc_binario, efeito_desenho       - quanto as partidas de um mesmo jogador "andam juntas" e quantos jogos independentes valem
  holm, benjamini_hochberg          - correção para muitos testes ao mesmo tempo
  bo3_de_jogo, jogo_de_bo3          - converte chance por jogo em chance de vencer uma melhor de 3 (e o contrário)
  z_duas_proporcoes_efetivo         - teste de duas proporções com o tamanho de amostra efetivo
  ece, calibracao_detalhada         - calibração a fundo: faixas por largura e por massa, piso de ruído, intervalo, recalibração
  recalibracao_logistica            - inclinação/intercepto de calibração (1 e 0 = calibrado)
  calibracao_por_grupo              - calibração por arquétipo, período ou grupo de jogadores, com faixa de Wilson
  impressao_banco, impressao_objeto - impressão digital dos dados (hash das linhas ordenadas), sem copiar dados
  ambiente                          - versões do Python, SQLite e pacotes
  registrar                         - grava o registro completo de um experimento (ESCRITA; nunca sobrescreve)
  CLASSE                            - cada função pública marcada como "leitura" ou "escrita"

Premissas estão no texto de cada função. Testes em ../tests/test_sa_tools.py.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import random
import subprocess
from pathlib import Path
from typing import Callable, Hashable, Iterable, Sequence

_EPS = 1e-9


# ------------------------------------------------------------------ qualidade de previsões

def _checar_pares(pares: Sequence[tuple[float, float]]) -> None:
    if not pares:
        raise ValueError("lista de previsões vazia")
    for p, y in pares:
        if not (0.0 <= p <= 1.0) or y not in (0, 1, 0.0, 1.0, True, False):
            raise ValueError(f"par inválido (p={p}, y={y}): p deve estar em [0, 1] e y ser 0 ou 1")


def logloss(pares: Sequence[tuple[float, float]], eps: float = _EPS) -> float:
    """Perda logarítmica média de [(probabilidade prevista, resultado 0/1)]. Chute de 50% = ln 2 = 0,6931."""
    _checar_pares(pares)
    return -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y in pares) / len(pares)


def brier(pares: Sequence[tuple[float, float]]) -> float:
    """Erro quadrático médio da probabilidade. Chute de 50% = 0,25."""
    _checar_pares(pares)
    return sum((p - y) ** 2 for p, y in pares) / len(pares)


def calibracao(pares: Sequence[tuple[float, float]], faixas: int = 10) -> dict:
    """Tabela de calibração: em cada faixa de probabilidade prevista, a média prevista e a frequência real.
    Devolve {"faixas": [{de, ate, n, previsto, real}], "ece": erro de calibração esperado (média |previsto-real| pesada por n)}."""
    _checar_pares(pares)
    if faixas < 1:
        raise ValueError("faixas deve ser >= 1")
    caixas: list[list[tuple[float, float]]] = [[] for _ in range(faixas)]
    for p, y in pares:
        caixas[min(int(p * faixas), faixas - 1)].append((p, y))
    saida, ece = [], 0.0
    for i, c in enumerate(caixas):
        if not c:
            continue
        prev = sum(p for p, _ in c) / len(c)
        real = sum(y for _, y in c) / len(c)
        ece += len(c) * abs(prev - real)
        saida.append({"de": i / faixas, "ate": (i + 1) / faixas, "n": len(c), "previsto": prev, "real": real})
    return {"faixas": saida, "ece": ece / len(pares)}


# ------------------------------------------------------------------ incerteza com observações agrupadas

def bootstrap_agrupado(grupos: dict[Hashable, Sequence], estatistica: Callable[[list], float], repeticoes: int = 1000,
                       semente: int = 12345, nivel: float = 0.95) -> dict:
    """Bootstrap por grupos: sorteia GRUPOS inteiros com reposição (ex.: torneios ou jogadores) e recalcula a estatística
    sobre a junção das linhas dos grupos sorteados. Respeita a dependência dentro do grupo (premissa: grupos independentes
    entre si). Devolve {"estimativa", "baixo", "alto", "repeticoes", "grupos"} (faixa por percentis)."""
    chaves = [k for k, v in grupos.items() if len(v)]
    if len(chaves) < 2:
        raise ValueError("precisa de pelo menos 2 grupos com linhas")
    if not 0 < nivel < 1 or repeticoes < 10:
        raise ValueError("nivel deve estar em (0, 1) e repeticoes >= 10")
    rng = random.Random(semente)
    todas = [x for k in chaves for x in grupos[k]]
    est = estatistica(todas)
    valores = []
    for _ in range(repeticoes):
        linhas = []
        for k in (rng.choice(chaves) for _ in chaves):
            linhas.extend(grupos[k])
        valores.append(estatistica(linhas))
    valores.sort()
    a = (1 - nivel) / 2
    return {"estimativa": est, "baixo": valores[int(a * (repeticoes - 1))], "alto": valores[int((1 - a) * (repeticoes - 1))],
            "repeticoes": repeticoes, "grupos": len(chaves), "semente": semente}


def diferenca_pareada(linhas: Sequence[tuple[Hashable, float, float]], repeticoes: int = 1000, semente: int = 12345) -> dict:
    """Compara dois modelos nas MESMAS linhas: [(grupo, perda_A, perda_B)]. Diferença = média(A - B)
    (negativa = A melhor). Faixa por bootstrap agrupado. "Provável" se a faixa de 95% não contém 0."""
    grupos: dict = {}
    for g, a, b in linhas:
        grupos.setdefault(g, []).append(a - b)
    r = bootstrap_agrupado(grupos, lambda xs: sum(xs) / len(xs), repeticoes, semente)
    r["provavel"] = r["alto"] < 0 or r["baixo"] > 0
    r["linhas"] = len(linhas)
    return r


def icc_binario(grupos: Iterable[Sequence[int]]) -> float:
    """Correlação intraclasse (estimador de ANOVA) para resultados 0/1 agrupados (ex.: partidas de cada jogador).
    0 = partidas independentes; 1 = todas as partidas do grupo dão o mesmo resultado. Pode sair negativo por acaso
    (é devolvido como está). Premissa: dentro de cada grupo, a mesma chance para todas as linhas."""
    gs = [list(g) for g in grupos if len(g) > 0]
    k = len(gs)
    n = sum(len(g) for g in gs)
    if k < 2 or n <= k:
        raise ValueError("precisa de pelo menos 2 grupos e mais linhas que grupos")
    media = sum(sum(g) for g in gs) / n
    ssb = sum(len(g) * (sum(g) / len(g) - media) ** 2 for g in gs)
    ssw = sum(sum((y - sum(g) / len(g)) ** 2 for y in g) for g in gs)
    msb, msw = ssb / (k - 1), ssw / (n - k)
    n0 = (n - sum(len(g) ** 2 for g in gs) / n) / (k - 1)
    den = msb + (n0 - 1) * msw
    return (msb - msw) / den if den else 0.0


def efeito_desenho(tamanho_medio: float, icc: float) -> float:
    """Efeito de desenho de Kish: 1 + (m - 1)·ICC. Amostra efetiva = n / efeito."""
    if tamanho_medio < 1:
        raise ValueError("tamanho_medio deve ser >= 1")
    return max(1.0, 1 + (tamanho_medio - 1) * icc)


def z_duas_proporcoes_efetivo(v1: float, n1: float, v2: float, n2: float, efeito: float = 1.0) -> float | None:
    """Valor-p bilateral do teste z de duas proporções com n dividido pelo efeito de desenho
    (efeito = 1 reproduz `variantes._valor_p`). Devolve None se não houver dados ou variância."""
    if efeito < 1:
        raise ValueError("efeito de desenho deve ser >= 1")
    if not n1 or not n2:
        return None
    p = (v1 + v2) / (n1 + n2)
    ep = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2) * efeito)
    return math.erfc(abs((v1 / n1 - v2 / n2) / ep) / math.sqrt(2)) if ep else None


# ------------------------------------------------------------------ muitos testes ao mesmo tempo

def holm(pvalores: Sequence[float]) -> list[float]:
    """Valores-p ajustados por Holm-Bonferroni (controla a chance de QUALQUER falso positivo). Mesma ordem da entrada."""
    if any(not 0 <= p <= 1 for p in pvalores):
        raise ValueError("valores-p devem estar em [0, 1]")
    m = len(pvalores)
    ordem = sorted(range(m), key=lambda i: pvalores[i])
    ajust, maior = [0.0] * m, 0.0
    for pos, i in enumerate(ordem):
        maior = max(maior, min(1.0, (m - pos) * pvalores[i]))
        ajust[i] = maior
    return ajust


def benjamini_hochberg(pvalores: Sequence[float]) -> list[float]:
    """Valores-q de Benjamini-Hochberg (controla a FRAÇÃO esperada de falsos positivos entre os achados)."""
    if any(not 0 <= p <= 1 for p in pvalores):
        raise ValueError("valores-p devem estar em [0, 1]")
    m = len(pvalores)
    ordem = sorted(range(m), key=lambda i: pvalores[i], reverse=True)
    ajust, menor = [0.0] * m, 1.0
    for pos, i in enumerate(ordem):
        menor = min(menor, pvalores[i] * m / (m - pos))
        ajust[i] = menor
    return ajust


# ------------------------------------------------------------------ jogo único × melhor de 3

def bo3_de_jogo(q: float) -> float:
    """Chance de vencer uma melhor de 3 se cada jogo é vencido com chance q, jogos independentes, sem empates:
    q² + 2q²(1 - q) = q²(3 - 2q)."""
    if not 0 <= q <= 1:
        raise ValueError("q deve estar em [0, 1]")
    return q * q * (3 - 2 * q)


def jogo_de_bo3(p: float, tol: float = 1e-12) -> float:
    """Inversa de bo3_de_jogo (a função é crescente em [0, 1]): chance por jogo que dá a chance p de vencer a melhor de 3."""
    if not 0 <= p <= 1:
        raise ValueError("p deve estar em [0, 1]")
    lo, hi = 0.0, 1.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if bo3_de_jogo(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ------------------------------------------------------------------ calibração a fundo (06/11/2026)
# Por que: um ECE baixo sozinho NÃO prova calibração. Ele depende do nº de faixas, some quando quase todas as previsões caem perto
# de 50% e tem um "piso" de ruído mesmo para um modelo perfeito. Por isso: várias quantidades de faixas, faixas de mesmo tamanho
# (massa), observações por faixa, piso de ruído simulado, faixa de incerteza por bootstrap (agrupado, quando houver grupos) e o
# ajuste logístico de recalibração (inclinação 1 e intercepto 0 = calibrado; inclinação < 1 = confiança exagerada).

def ece(pares: Sequence[tuple[float, float]], faixas: int = 10, esquema: str = "largura") -> dict:
    """ECE com faixas de mesma LARGURA (como `calibracao`) ou de mesma MASSA (mesmo nº de previsões por faixa).
    Devolve {"ece", "faixas": [{n, previsto, real}], "n_min", "n_mediana"}."""
    _checar_pares(pares)
    if faixas < 1 or esquema not in ("largura", "massa"):
        raise ValueError("faixas >= 1 e esquema 'largura' ou 'massa'")
    if esquema == "largura":
        caixas: list[list] = [[] for _ in range(faixas)]
        for p, y in pares:
            caixas[min(int(p * faixas), faixas - 1)].append((p, y))
    else:
        ordem = sorted(pares)
        n = len(ordem)
        caixas = [ordem[i * n // faixas:(i + 1) * n // faixas] for i in range(faixas)]
    caixas = [c for c in caixas if c]
    tab = [{"n": len(c), "previsto": sum(p for p, _ in c) / len(c), "real": sum(y for _, y in c) / len(c)} for c in caixas]
    tamanhos = sorted(f["n"] for f in tab)
    return {"ece": sum(f["n"] * abs(f["previsto"] - f["real"]) for f in tab) / len(pares), "faixas": tab,
            "n_min": tamanhos[0], "n_mediana": tamanhos[len(tamanhos) // 2], "esquema": esquema, "k": faixas}


def recalibracao_logistica(pares: Sequence[tuple[float, float]], eps: float = 1e-6, iteracoes: int = 50) -> dict:
    """Ajusta y ~ logística(a + b·logit(p)) por Newton-Raphson. Calibrado: a ≈ 0 e b ≈ 1. b < 1: previsões extremas demais
    (confiança exagerada); b > 1: tímidas demais. Devolve {"intercepto", "inclinacao", "ep_intercepto", "ep_inclinacao"}."""
    _checar_pares(pares)
    xs = [math.log(min(max(p, eps), 1 - eps) / (1 - min(max(p, eps), 1 - eps))) for p, _ in pares]
    ys = [float(y) for _, y in pares]
    a, b = 0.0, 1.0
    h00 = h01 = h11 = 0.0
    convergiu = False
    for _ in range(iteracoes):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            eta = max(-35.0, min(35.0, a + b * x))     # conta estável (separação perfeita levava a math.exp estourar; 06/11)
            q = 1 / (1 + math.exp(-eta))
            w = q * (1 - q)
            g0 += y - q
            g1 += (y - q) * x
            h00 += w
            h01 += w * x
            h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if det <= 1e-12:
            break
        da, db = (h11 * g0 - h01 * g1) / det, (h00 * g1 - h01 * g0) / det
        passo = max(abs(da), abs(db))
        if passo > 5:                                   # passo grande demais: amortece (Newton diverge com separação)
            da, db = 5 * da / passo, 5 * db / passo
        a, b = a + da, b + db
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            convergiu = True
            break
    det = h00 * h11 - h01 * h01
    ep_a = math.sqrt(h11 / det) if det > 1e-12 else float("nan")
    ep_b = math.sqrt(h00 / det) if det > 1e-12 else float("nan")
    return {"intercepto": a, "inclinacao": b, "ep_intercepto": ep_a, "ep_inclinacao": ep_b, "convergiu": convergiu}


def calibracao_detalhada(pares: Sequence[tuple[float, float]], grupos: Sequence[Hashable] | None = None,
                         faixas: Sequence[int] = (5, 10, 15, 20), repeticoes: int = 300, semente: int = 12345) -> dict:
    """Relatório de calibração para não concluir só pelo ECE:
      - log-loss e Brier;
      - ECE por largura e por massa, para cada nº de faixas, com observações mínima/mediana por faixa;
      - piso de ruído: ECE médio (e percentil 95) de um modelo PERFEITAMENTE calibrado com as mesmas previsões (y sorteado de p);
        ECE observado dentro do piso = "compatível com calibrado", não "provado calibrado";
      - faixa de 95% do ECE (10 faixas, largura) por bootstrap — por GRUPO se `grupos` vier (ex.: torneio de cada linha);
      - recalibração logística (intercepto e inclinação)."""
    _checar_pares(pares)
    if grupos is not None and len(grupos) != len(pares):
        raise ValueError("grupos deve ter um rótulo por par")
    rng = random.Random(semente)
    saida = {"n": len(pares), "logloss": logloss(pares), "brier": brier(pares), "media_prevista": sum(p for p, _ in pares) / len(pares),
             "frequencia_real": sum(y for _, y in pares) / len(pares), "por_faixas": {}}
    for k in faixas:
        lar, mas = ece(pares, k, "largura"), ece(pares, k, "massa")
        piso = []
        for _ in range(max(repeticoes // 3, 50)):
            sim = [(p, 1 if rng.random() < p else 0) for p, _ in pares]
            piso.append(ece(sim, k, "largura")["ece"])
        piso.sort()
        saida["por_faixas"][k] = {"ece_largura": lar["ece"], "ece_massa": mas["ece"], "n_min_largura": lar["n_min"],
                                  "n_mediana_largura": lar["n_mediana"], "n_por_faixa_massa": mas["n_min"],
                                  "piso_ruido_medio": sum(piso) / len(piso), "piso_ruido_p95": piso[int(0.95 * (len(piso) - 1))]}
    if grupos is None:
        blocos = {i: [par] for i, par in enumerate(pares)}
    else:
        blocos = {}
        for g, par in zip(grupos, pares):
            blocos.setdefault(g, []).append(par)
    if len(blocos) >= 2:
        saida["ece10_ic95"] = bootstrap_agrupado(blocos, lambda xs: ece(xs, 10)["ece"], repeticoes, semente)
        saida["ece10_ic95"]["agrupado_por"] = "grupo" if grupos is not None else "linha"
    saida["recalibracao"] = recalibracao_logistica(pares)
    return saida


def calibracao_por_grupo(linhas: Sequence[tuple[Hashable, float, float]], minimo: int = 30) -> dict:
    """Calibração "no atacado" por grupo (arquétipo, período, jogador...): [(grupo, p, y)] → por grupo: n, previsto médio,
    frequência real, diferença, faixa de Wilson 95% da frequência real e log-loss. Grupos com menos de `minimo` linhas são
    juntados em "(outros)" (marcar, não esconder)."""
    por: dict = {}
    for g, p, y in linhas:
        por.setdefault(g, []).append((p, y))
    pequenos = [g for g, v in por.items() if len(v) < minimo]
    if len(pequenos) > 1:
        por.setdefault("(outros)", [])
        for g in pequenos:
            por["(outros)"].extend(por.pop(g))
    saida = {}
    z = 1.959963984540054
    for g, v in sorted(por.items(), key=lambda kv: -len(kv[1])):
        n = len(v)
        f = sum(y for _, y in v) / n
        prev = sum(p for p, _ in v) / n
        den = 1 + z * z / n
        centro = (f + z * z / (2 * n)) / den
        meia = z * math.sqrt(f * (1 - f) / n + z * z / (4 * n * n)) / den
        saida[str(g)] = {"n": n, "previsto": prev, "real": f, "diferenca": f - prev, "real_baixo": centro - meia,
                         "real_alto": centro + meia, "previsto_dentro_da_faixa": centro - meia <= prev <= centro + meia,
                         "logloss": logloss(v)}
    return saida


# ------------------------------------------------------------------ reprodutibilidade (revisto em 06/11/2026)
#
# Cada experimento grava um registro com: id, data e hora; commit e impressão do código do Coletor e da Skill; hash do script;
# Python e dependências; semente e parâmetros; impressão COMPLETA dos dados (hash determinístico das linhas ordenadas de cada
# tabela, sem copiar nenhum dado), nº de registros, período e filtros; resultado, hash do resultado e arquivos de saída.
# O que não puder ser registrado vira uma linha em "limitacoes" (nunca some em silêncio). Nada é sobrescrito.

TABELAS_DADOS = ("partidas", "torneios", "t_jogadores", "t_partidas", "t_listas", "arquetipos", "meus_decks")


def _git(pasta: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(pasta), *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _commit(pasta: Path) -> str:
    """Compatibilidade com a versão anterior: commit curto ou '(sem git)'."""
    return _git(Path(pasta), "rev-parse", "--short", "HEAD") or "(sem git)"


def _sha_arquivo(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _sha_pasta(pasta: Path, padrao: str = "*.py") -> str | None:
    arqs = sorted(Path(pasta).glob(padrao))
    if not arqs:
        return None
    h = hashlib.sha256()
    for a in arqs:
        h.update(a.name.encode())
        h.update(a.read_bytes())
    return h.hexdigest()[:16]


def impressao_objeto(obj, algarismos: int | None = None) -> str:
    """Hash determinístico de dados já carregados (listas, dicionários, conjuntos): JSON canônico (chaves e conjuntos ordenados).
    Com `algarismos`, cada número real é arredondado a esse nº de algarismos significativos antes do hash: serve para comparar
    reproduções sem o ruído da última casa (a ordem de soma pode mudar entre processos; ver `ambiente()["hash_aleatorio"]`)."""
    def canon(x):
        if isinstance(x, dict):
            return {str(k): canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
        if isinstance(x, (set, frozenset)):
            return sorted((canon(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True, default=str))
        if isinstance(x, (list, tuple)):
            return [canon(v) for v in x]
        if isinstance(x, float):
            return format(x, f".{algarismos}g") if algarismos else repr(x)
        return x
    return hashlib.sha256(json.dumps(canon(obj), sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def impressao_banco(caminho_db: Path, tabelas: Sequence[str] = TABELAS_DADOS) -> dict:
    """Impressão dos dados SEM copiar nenhum dado: para cada tabela, nº de linhas e SHA-256 de todas as linhas ordenadas por todas
    as colunas (o mesmo conteúdo dá o mesmo hash em qualquer máquina; qualquer linha mudada muda o hash). Abre só para leitura.
    Mantém os campos da versão anterior ("tabelas", "torneios_de/ate") e a impressão antiga (só contagens e datas) como
    "impressao_contagens", para comparar com os registros de 06/11. Tabela ausente fica em "limitacoes"."""
    import sqlite3
    import urllib.parse
    uri = "file:" + urllib.parse.quote(Path(caminho_db).resolve().as_posix(), safe="/:") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    limitacoes, por_tabela = [], {}
    try:
        existentes = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in tabelas:
            if t not in existentes:
                limitacoes.append(f"tabela {t} ausente no banco")
                continue
            ncols = len(con.execute(f"PRAGMA table_info({t})").fetchall())
            h, n = hashlib.sha256(), 0
            for linha in con.execute(f"SELECT * FROM {t} ORDER BY " + ", ".join(str(i) for i in range(1, ncols + 1))):
                h.update(json.dumps([x.hex() if isinstance(x, bytes) else (repr(x) if isinstance(x, float) else x)
                                     for x in linha], ensure_ascii=False).encode())
                h.update(b"\n")
                n += 1
            por_tabela[t] = {"linhas": n, "sha256": h.hexdigest()}
        datas = con.execute("SELECT MIN(data), MAX(data) FROM torneios").fetchone() if "torneios" in existentes else (None, None)
        capt = (con.execute("SELECT MIN(capturada_em), MAX(capturada_em) FROM partidas").fetchone()
                if "partidas" in existentes else (None, None))
    finally:
        con.close()
    cont = {t: por_tabela[t]["linhas"] for t in ("partidas", "torneios", "t_jogadores", "t_partidas", "t_listas") if t in por_tabela}
    return {"tabelas": cont, "torneios_de": datas[0], "torneios_ate": datas[1],
            "partidas_de": capt[0], "partidas_ate": capt[1],
            "por_tabela": por_tabela,
            "impressao": hashlib.sha256(json.dumps(por_tabela, sort_keys=True).encode()).hexdigest(),
            "impressao_contagens": hashlib.sha256(json.dumps([cont, list(datas)]).encode()).hexdigest()[:12],
            "metodo": "sha256 das linhas ordenadas por todas as colunas, por tabela; impressao = sha256 do manifesto",
            "limitacoes": limitacoes}


def ambiente(pacotes: Sequence[str] = ("numpy", "requests")) -> dict:
    """Python, SQLite e versões das dependências relevantes (ausente = 'ausente'). Sem nome de máquina nem usuário."""
    import platform
    import sqlite3
    from importlib import metadata
    vers = {}
    for p in pacotes:
        try:
            vers[p] = metadata.version(p)
        except Exception:
            vers[p] = "ausente"
    import sys
    return {"python": platform.python_version(), "implementacao": platform.python_implementation(),
            "sistema": platform.system(), "sqlite": sqlite3.sqlite_version, "pacotes": vers,
            # 1 = a ordem de conjuntos/dicionários de texto muda a cada processo (com -I, PYTHONHASHSEED é ignorado):
            # somas feitas nessa ordem podem diferir na última casa; compare reproduções por resultado_sha256_12alg
            "hash_aleatorio": sys.flags.hash_randomization}


def registrar(nome: str, resultado: dict, pasta_programa: Path, pasta_saida: Path, semente: int | None = None,
              parametros: dict | None = None, *, script: Path | str | None = None, filtros: dict | None = None,
              dados_usados: dict | None = None, arquivos_saida: Sequence[Path] = (), copia: dict | None = None,
              pacotes: Sequence[str] = ("numpy", "requests")) -> Path:
    """Grava resultados/<nome>_<AAAAMMDD-HHMMSS>[_n].json (abertura exclusiva: nunca sobrescreve) com o registro completo descrito
    acima. Com a variável de ambiente SA_SAIDA, grava nela (explorações e testes que não devem deixar arquivo no repositório).
      script         arquivo do experimento (padrão: o __main__); entra o SHA-256
      filtros        filtros e recortes aplicados (ex.: {"corte": 0.7, "so_standard": True})
      dados_usados   descrição do conjunto efetivamente usado: {"n_registros": ..., "periodo": [...], "impressao": impressao_objeto(...)}
      arquivos_saida outros arquivos gerados (nome, tamanho e SHA-256)
      copia          a identificação devolvida pela ponte (t.identificacao)"""
    import os
    import sys
    import uuid
    pasta_saida = Path(os.environ.get("SA_SAIDA") or pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    agora = _dt.datetime.now().astimezone()
    pasta_programa = Path(pasta_programa)
    skill = Path(__file__).resolve().parent.parent
    limitacoes: list[str] = []

    if script is None:
        script = getattr(sys.modules.get("__main__"), "__file__", None)
    if script and Path(script).is_file():
        info_script = {"arquivo": Path(script).name, "sha256": _sha_arquivo(Path(script))}
    else:
        info_script = {"arquivo": None, "sha256": None}
        limitacoes.append("script do experimento não identificado: hash ausente")

    versao_txt = pasta_programa / "versao.txt"
    versao = versao_txt.read_text(encoding="utf-8").strip() if versao_txt.exists() else None
    if versao is None:
        limitacoes.append("versao.txt do Coletor ausente")
    commit_col = _git(pasta_programa, "rev-parse", "HEAD")
    if commit_col is None:
        limitacoes.append("cópia do Coletor sem git: identidade do código = versao.txt + hash de tracker/*.py")
    hash_tracker = _sha_pasta(pasta_programa / "tracker")
    if hash_tracker is None:
        limitacoes.append("tracker/ não encontrado: código do Coletor sem impressão")
    commit_skill = _git(skill, "rev-parse", "HEAD")
    status_skill = _git(skill, "status", "--porcelain", "--", ".")
    if commit_skill is None:
        limitacoes.append("Skill fora do git: commit ausente")
    elif status_skill:
        limitacoes.append("Skill com mudanças sem commit: vale o hash das ferramentas, não só o commit")
    amb = ambiente(pacotes)
    if amb["hash_aleatorio"]:
        limitacoes.append("ordem de conjuntos de texto aleatória por processo: reprodução exata até ~12 algarismos")
    for p, v in amb["pacotes"].items():
        if v == "ausente":
            limitacoes.append(f"pacote {p} ausente no ambiente")

    db = pasta_programa / "dados" / "tracker.db"
    if db.exists():
        dados = impressao_banco(db)
        limitacoes.extend(dados["limitacoes"])
    else:
        dados = None
        limitacoes.append("banco ausente: dados sem impressão")
    if not dados_usados:
        limitacoes.append("conjunto efetivamente usado não descrito (só a impressão do banco inteiro)")

    saidas = []
    for a in arquivos_saida:
        a = Path(a)
        if a.is_file():
            saidas.append({"arquivo": a.name, "bytes": a.stat().st_size, "sha256": _sha_arquivo(a)})
        else:
            limitacoes.append(f"arquivo de saída não encontrado: {a.name}")

    reg = {"id": f"{nome}-{agora.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}", "experimento": nome,
           "quando": agora.isoformat(timespec="seconds"), "semente": semente, "parametros": parametros or {},
           "codigo": {"commit": commit_col[:7] if commit_col else "(sem git)", "versao": versao,
                      "coletor": {"commit": commit_col, "versao": versao, "tracker_sha": hash_tracker},
                      "skill": {"commit": commit_skill, "mudancas_sem_commit": bool(status_skill) if commit_skill else None,
                                "ferramentas_sha": _sha_pasta(skill / "tools")},
                      "script": info_script, "copia": copia},
           "ambiente": amb,
           "dados": dados, "filtros": filtros or {}, "dados_usados": dados_usados or {},
           "resultado": resultado, "resultado_sha256": impressao_objeto(resultado),
           "resultado_sha256_12alg": impressao_objeto(json.loads(json.dumps(resultado, default=str)), 12),
           "arquivos_saida": saidas, "limitacoes": limitacoes,
           "formato_registro": 2}
    texto = json.dumps(reg, ensure_ascii=False, indent=1, default=str)
    base = f"{nome}_{agora.strftime('%Y%m%d-%H%M%S')}"
    n = 0
    while True:
        arq = pasta_saida / (f"{base}.json" if n == 0 else f"{base}_{n}.json")
        try:
            with open(arq, "x", encoding="utf-8", newline="\n") as f:     # "x": falha se já existe (nunca sobrescreve)
                f.write(texto)
            return arq
        except FileExistsError:
            n += 1


# ------------------------------------------------------------------ classificação (leitura × escrita)
# leitura = só calcula ou só lê; escrita = grava arquivo. Conferido por tests/test_ponte.py e tests/test_sa_tools.py.
CLASSE = {n: "leitura" for n in ("logloss", "brier", "calibracao", "bootstrap_agrupado", "diferenca_pareada", "icc_binario",
                                 "efeito_desenho", "z_duas_proporcoes_efetivo", "holm", "benjamini_hochberg", "bo3_de_jogo",
                                 "jogo_de_bo3", "impressao_banco", "impressao_objeto", "ambiente", "ece",
                                 "recalibracao_logistica", "calibracao_detalhada", "calibracao_por_grupo")}
CLASSE["registrar"] = "escrita"
