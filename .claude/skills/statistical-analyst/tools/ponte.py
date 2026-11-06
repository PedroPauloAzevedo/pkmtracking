"""
PONTE ENTRE A SKILL E O MOTOR ESTATÍSTICO DO COLETOR (reutiliza; não copia).

    from ponte import carregar
    t = carregar(r"C:\\caminho\\da\\COPIA")      # pasta de uma CÓPIA do programa (com dados/ próprio, porta 8799)
    t.analises.wilson(7, 10)                     # -> (39.7, 89.2)
    t.probabilidades.carta(4, 12, False, 2)
    t.estrategia.confrontos_ajustados(partidas, decks)

Regras:
  - Sempre uma CÓPIA do programa: o tracker usa a pasta `dados/` que fica ao lado do código importado. Nunca a instalação real.
  - As funções do Coletor são usadas como estão; se uma precisar mudar, a mudança é no Coletor (com medição, D-017), não aqui.
  - `carregar` recusa uma pasta sem `tracker/` e avisa se `dados/config.json` não tiver a porta de teste 8799.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

MODULOS = ("analises", "banco", "decks", "estrategia", "probabilidades", "regressao", "variantes", "leitor", "replay", "cartas")


def carregar(pasta_programa: str | Path, exigir_porta_teste: bool = True) -> SimpleNamespace:
    pasta = Path(pasta_programa).resolve()
    if not (pasta / "tracker" / "__init__.py").exists():
        raise FileNotFoundError(f"{pasta} não tem tracker/: não é uma pasta do Coletor")
    cfg = pasta / "dados" / "config.json"
    if exigir_porta_teste and cfg.exists():
        porta = json.loads(cfg.read_text(encoding="utf-8")).get("porta")
        if porta != 8799:
            raise RuntimeError(f"{cfg} tem porta {porta}: use uma CÓPIA de teste com porta 8799 (CLAUDE.md)")
    if "tracker" in sys.modules and Path(sys.modules["tracker"].__file__).resolve().parent.parent != pasta:
        raise RuntimeError("outro tracker já foi importado neste processo; rode um processo por pasta")
    sys.path.insert(0, str(pasta))
    return SimpleNamespace(**{m: importlib.import_module(f"tracker.{m}") for m in MODULOS}, pasta=pasta)
