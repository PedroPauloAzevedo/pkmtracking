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
  registrar                         - grava o resultado de um experimento com semente, versão do código e impressão dos dados

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


# ------------------------------------------------------------------ reprodutibilidade

def _commit(pasta: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(pasta), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or "(sem git)"
    except Exception:
        return "(sem git)"


def impressao_banco(caminho_db: Path) -> dict:
    """Impressão dos dados usados (contagens por tabela + resumo), sem copiar nenhum dado pessoal. Abre só para leitura."""
    import sqlite3
    con = sqlite3.connect(f"file:{Path(caminho_db).as_posix()}?mode=ro", uri=True)
    try:
        cont = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("partidas", "torneios", "t_jogadores", "t_partidas", "t_listas")}
        datas = con.execute("SELECT MIN(data), MAX(data) FROM torneios").fetchone()
        h = hashlib.sha256(json.dumps([cont, datas]).encode()).hexdigest()[:12]
    finally:
        con.close()
    return {"tabelas": cont, "torneios_de": datas[0], "torneios_ate": datas[1], "impressao": h}


def registrar(nome: str, resultado: dict, pasta_programa: Path, pasta_saida: Path, semente: int | None = None,
              parametros: dict | None = None) -> Path:
    """Grava resultados/<nome>_<AAAAMMDD-HHMMSS>.json com data, semente, parâmetros, commit do código e impressão dos dados.
    Nunca sobrescreve: cada execução gera um arquivo novo. Com a variável de ambiente SA_SAIDA definida, grava nela em vez de
    `pasta_saida` (para explorações e testes que não devem deixar arquivo no repositório)."""
    import os
    pasta_saida = Path(os.environ.get("SA_SAIDA") or pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    agora = _dt.datetime.now()
    arq = pasta_saida / f"{nome}_{agora.strftime('%Y%m%d-%H%M%S')}.json"
    n = 1
    while arq.exists():
        arq = pasta_saida / f"{nome}_{agora.strftime('%Y%m%d-%H%M%S')}_{n}.json"
        n += 1
    pasta_programa = Path(pasta_programa)
    reg = {"experimento": nome, "quando": agora.isoformat(timespec="seconds"), "semente": semente,
           "parametros": parametros or {}, "codigo": {"commit": _commit(pasta_programa),
                                                      "versao": (pasta_programa / "versao.txt").read_text().strip()
                                                      if (pasta_programa / "versao.txt").exists() else None},
           "dados": impressao_banco(pasta_programa / "dados" / "tracker.db")
           if (pasta_programa / "dados" / "tracker.db").exists() else None,
           "resultado": resultado}
    arq.write_text(json.dumps(reg, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    return arq
