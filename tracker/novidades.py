"""
NOVIDADES de cada versão: o que mudou e o passo a passo para quem atualiza.

novidades.json (na raiz do programa) tem uma entrada por versão, da mais nova para a mais antiga:
  {"versao": "2026.10.30-1", "data": "2026-10-30", "titulo": "...",
   "mudancas": [...],        o que mudou
   "como_atualizar": [...],  passo a passo para atualizar (aparece ANTES, em Ajustes > Atualizações)
   "passos": [...]}          o que fazer depois de atualizar (aparece DEPOIS, numa janela no painel)

Depois de atualizar, o painel abre a janela com as novidades das versões que a pessoa ainda não
viu. Ela some quando a pessoa clica em "Entendi" (fica guardado em dados/config.json).
"""
import json

from . import banco, config
from .atualizador import _como_tupla, versao_local

ARQ = config.RAIZ / "novidades.json"


def ler(texto=None):
    try:
        dados = json.loads(texto if texto is not None else ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    return [x for x in dados if isinstance(x, dict) and x.get("versao")] if isinstance(dados, list) else []


def entre(lista, de, ate):
    """Entradas com versão maior que 'de' e até 'ate' (inclusive), da mais nova para a mais antiga."""
    a, b = _como_tupla(de), _como_tupla(ate)
    return sorted((x for x in lista if a < _como_tupla(x["versao"]) <= b), key=lambda x: _como_tupla(x["versao"]), reverse=True)


def para_mostrar():
    cfg = config.ler_config()
    atual = versao_local()
    todas = ler()
    vista = cfg.get("versao_vista")
    if vista is None:
        # Primeira versão com este aviso: quem já usava o programa vê as novidades desta versão;
        # quem acabou de instalar não precisa (não há nada para "atualizar").
        ja_usava = bool(cfg.get("nick")) or bool(banco.consultar("SELECT 1 FROM partidas LIMIT 1"))
        if not ja_usava:
            marcar_vista()
            return {"versao": atual, "pendentes": [], "todas": todas}
        pendentes = [x for x in todas if x["versao"] == atual]
    else:
        pendentes = entre(todas, vista, atual)
    return {"versao": atual, "pendentes": pendentes, "todas": todas}


def marcar_vista():
    cfg = config.ler_config()
    cfg["versao_vista"] = versao_local()
    config.salvar_config(cfg)
