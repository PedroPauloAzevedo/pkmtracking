"""
Caminhos e configurações do programa.

Tudo o que o programa grava fica na pasta "dados", ao lado do app.py:
  dados/tracker.db   -> banco SQLite com partidas e campeonatos
  dados/logs/        -> cópia em .txt de cada log capturado (backup)
  dados/config.json  -> suas configurações (nick, modo automático...)
  dados/regras.json  -> regras de leitura editadas por você
"""
import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"
PASTA_LOGS = PASTA_DADOS / "logs"
PASTA_MODELOS = RAIZ / "modelos"
ARQ_BANCO = PASTA_DADOS / "tracker.db"
ARQ_CONFIG = PASTA_DADOS / "config.json"
ARQ_REGRAS = PASTA_DADOS / "regras.json"
ARQ_REGRAS_PADRAO = Path(__file__).resolve().parent / "regras_padrao.json"

CONFIG_PADRAO = {
    "nick": "",                    # seu nome no TCG Live (para saber quem é "você" nos logs)
    "coletor_ativo": True,         # vigiar a área de transferência
    "intervalo_coletor": 1.0,      # segundos entre cada checagem
    "modo_automatico": False,      # clicar sozinho em "Battle Log" e "Exportar" (experimental)
    "confianca_imagem": 0.85,      # quão parecida a tela precisa estar com as imagens de modelo
    "porta": 8765,                 # endereço do painel: http://127.0.0.1:8765
    "sincronizar_auto": True,      # procurar e importar torneios novos do Limitless sozinho
    "sincronizar_horas": 6,        # de quantas em quantas horas verificar
    "sincronizar_dias": 45,        # importar torneios que começaram nos últimos N dias
    "listas_top": 64,              # quantas listas do topo baixar em cada torneio
    "github_repo": "",             # de onde baixar atualizações (usuario/repositorio); vazio = repositorio.txt
    "github_ramo": "main",
    "github_token": "",            # só para repositório privado (token de leitura)
}


def repositorio_padrao():
    """Quem baixa o programa do GitHub já vem com o endereço certo em repositorio.txt."""
    try:
        r = (RAIZ / "repositorio.txt").read_text(encoding="utf-8").strip()
        return "" if r.startswith("SEU-USUARIO") else r
    except OSError:
        return ""


def preparar_pastas():
    for p in (PASTA_DADOS, PASTA_LOGS, PASTA_MODELOS):
        p.mkdir(parents=True, exist_ok=True)
    if not ARQ_REGRAS.exists():
        shutil.copy(ARQ_REGRAS_PADRAO, ARQ_REGRAS)
        return False
    return atualizar_regras_antigas()


# Impressões digitais das versões anteriores das regras padrão. Se dados/regras.json for
# exatamente uma delas (você não editou nada), ele é trocado pela versão nova.
VERSOES_ANTIGAS = {"1a40b87f1f75eb0da144e63a94ca8d8e7fc826f4", "19570e5b097427556693503be371fb25ae220f2d"}


def _impressao(regras):
    import hashlib
    return hashlib.sha1(json.dumps(regras, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def atualizar_regras_antigas():
    try:
        atuais = json.loads(ARQ_REGRAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        atuais = None
    if atuais is None or _impressao(atuais) in VERSOES_ANTIGAS:
        shutil.copy(ARQ_REGRAS_PADRAO, ARQ_REGRAS)
        return True
    return False


def ler_config():
    cfg = dict(CONFIG_PADRAO)
    if ARQ_CONFIG.exists():
        try:
            cfg.update(json.loads(ARQ_CONFIG.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    if not cfg.get("github_repo"):
        cfg["github_repo"] = repositorio_padrao()
    return cfg


def salvar_config(cfg):
    ARQ_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def ler_regras():
    try:
        return json.loads(ARQ_REGRAS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return json.loads(ARQ_REGRAS_PADRAO.read_text(encoding="utf-8"))


def salvar_regras(regras):
    ARQ_REGRAS.write_text(json.dumps(regras, ensure_ascii=False, indent=2), encoding="utf-8")


def regras_padrao():
    return json.loads(ARQ_REGRAS_PADRAO.read_text(encoding="utf-8"))
