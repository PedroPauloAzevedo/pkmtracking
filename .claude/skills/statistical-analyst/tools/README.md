# Ferramentas da Skill

> Atualizado em 06/11/2026 (rodada de hardening: ponte só leitura, registro completo, calibração). Só biblioteca padrão do Python (como o programa). Rodar com `python -I`.

- **`ponte.py`** — carrega o `tracker` de uma **cópia** do programa em **modo só leitura com trava na execução** e devolve os módulos
  para usar as funções do Coletor como estão. Antes de importar, confere a cópia (`validar_copia`: `config.json` com porta 8799 —
  faltou = falha —, marca `dados/COPIA_DE_TESTE.json`, sem `.venv`/`.git`, fora das pastas protegidas — variável `SA_PASTAS_PROTEGIDAS` ou arquivo pessoal
  `~/.sa_pastas_protegidas`, uma pasta por linha, fora do repositório —, banco SQLite válido dentro da pasta). Depois: banco `mode=ro` + `query_only` + autorizador do SQLite; funções de escrita (`FUNCOES_ESCRITA`) bloqueadas; vigia do
  Python que barra gravar/apagar arquivos da cópia, SQLite de escrita, rede e programas externos. Um processo por cópia; o processo
  fica em modo análise até o fim. Erros: `CopiaInvalida` (nada foi importado) e `EscritaBloqueada`.
- **`marcar_copia.py`** (ESCRITA) — cria a marca de cópia de teste depois de conferir a pasta; nunca sobrescreve. Rodar à parte:
  `python -I marcar_copia.py <pasta da CÓPIA> "origem em poucas palavras"`.
- **`estrategia.py`** — análise estratégica (06/11/2026), funções puras sobre o replay e os eventos que o Coletor já produz: rota
  executada e rotas possíveis, corrida, prêmios checados (N, m, k por estado; recebe a hipergeométrica do programa como `hg`), trocas,
  disrupção por categoria, desenvolvimento do adversário, sequência de ações e n-gramas, Kaplan-Meier com censura, comparação pareada
  por estado. Todas `leitura` (`CLASSE`). Usadas por `../experiments/p_estrategia.py`.
- **`sa_tools.py`** — contas que o Coletor não tem: `logloss`, `brier`, `calibracao`, `bootstrap_agrupado`, `diferenca_pareada`,
  `icc_binario`, `efeito_desenho`, `z_duas_proporcoes_efetivo`, `holm`, `benjamini_hochberg`, `bo3_de_jogo`, `jogo_de_bo3`,
  `ece`, `recalibracao_logistica`, `calibracao_detalhada`, `calibracao_por_grupo`, `impressao_banco`, `impressao_objeto`, `ambiente`,
  `registrar`. Cada uma marcada em `CLASSE` como `leitura` ou `escrita` (só `registrar` grava). Premissas no texto de cada função;
  fórmulas em `../knowledge/FORMULAS.md`.
- **Registro dos experimentos (`registrar`, formato 2, 06/11):** id, data/hora, commit e hash do código do Coletor e da Skill, hash do
  script, Python/SQLite/pacotes, semente, parâmetros, filtros, impressão dos dados (SHA-256 das linhas ordenadas de cada tabela, sem
  copiar dados), conjunto usado, resultado e seus hashes (exato e com 12 algarismos), arquivos de saída e **limitações**. Nunca
  sobrescreve (abertura exclusiva). Com `-I` a ordem dos conjuntos de texto muda por processo: compare reproduções pelo hash de 12
  algarismos.

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
