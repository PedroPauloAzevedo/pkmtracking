"""
MARCAR UMA CÓPIA DE TESTE (ferramenta de ESCRITA: grava um único arquivo, dados/COPIA_DE_TESTE.json, na cópia).

A ponte (ponte.py) só carrega pastas com essa marca. Ela é a "identificação positiva" da cópia: uma instalação em uso nunca tem.
Antes de gravar, confere o mesmo que a ponte confere (porta 8799, sem .venv/.git, fora de SA_PASTAS_PROTEGIDAS, banco SQLite válido
dentro da pasta), menos a própria marca. Não mexe no banco nem no config.json.

Uso:  python -I marcar_copia.py <pasta da CÓPIA> [origem em poucas palavras, sem caminho nem nick]
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ponte  # noqa: E402

CLASSE = "escrita"


def marcar(pasta_programa: str | Path, origem: str = "") -> Path:
    if ponte.vigia_ligado():
        raise ponte.EscritaBloqueada("este processo está em modo análise (ponte carregada): marque a cópia em outro processo")
    pasta = Path(pasta_programa).expanduser().resolve()
    marca = pasta / "dados" / ponte.MARCA_COPIA
    try:
        ponte.validar_copia(pasta)
    except ponte.CopiaInvalida as e:
        if "falta a marca de cópia" not in str(e):
            raise
    if marca.exists():
        return marca
    with open(marca, "x", encoding="utf-8", newline="\n") as f:     # "x": nunca sobrescreve
        json.dump({"copia_de_teste": True, "criada_em": _dt.datetime.now().isoformat(timespec="seconds"),
                   "origem": origem[:80]}, f, ensure_ascii=False, indent=1)
    return marca


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(marcar(sys.argv[1], " ".join(sys.argv[2:])))
