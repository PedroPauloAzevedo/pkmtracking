# Ferramentas da Skill

> Atualizado em 06/11/2026. Só biblioteca padrão do Python (como o programa). Rodar com `python -I`.

- **`ponte.py`** — carrega o `tracker` de uma **cópia** do programa (recusa pasta sem `tracker/` e `config.json` com porta ≠ 8799) e
  devolve os módulos para usar as funções do Coletor como estão. Um processo por cópia.
- **`sa_tools.py`** — contas que o Coletor não tem: `logloss`, `brier`, `calibracao`, `bootstrap_agrupado`, `diferenca_pareada`,
  `icc_binario`, `efeito_desenho`, `z_duas_proporcoes_efetivo`, `holm`, `benjamini_hochberg`, `bo3_de_jogo`, `jogo_de_bo3`,
  `impressao_banco`, `registrar`. Premissas no texto de cada função; fórmulas em `../knowledge/FORMULAS.md`.

Exemplo:
```python
import sys; sys.path.insert(0, r".claude/skills/statistical-analyst/tools")
from ponte import carregar
import sa_tools as T
t = carregar(r"<pasta da CÓPIA>")
print(t.analises.wilson(30, 50))             # faixa de Wilson do programa
print(T.jogo_de_bo3(0.648))                  # 0,60 por jogo
```

Antes de criar uma função nova aqui: confira `../knowledge/KNOWN_METHODS.md` (se o programa já tem, use pela ponte). Toda função nova:
tipos, texto com premissas, erro claro para entrada inválida e testes em `../tests/test_sa_tools.py` (valor conhecido, extremos,
consistência, e simulação quando houver aproximação).
