# Mapa da documentação técnica

> Atualizado em 13/11/2026. Este arquivo só aponta para onde cada assunto está. A documentação técnica do projeto
> fica em [`PROJECT_KNOWLEDGE/`](../PROJECT_KNOWLEDGE/00_CENTRAL/INDEX.md); não crie cópias dela aqui.

A pasta `docs/` guarda só a base de regras do Standard ([`regras-standard.md`](regras-standard.md)), que **é lida pelo
programa** (`tracker/regras_jogo.py`): não mude esse arquivo de lugar nem o formato da tabela de marcas.

## Onde está cada assunto

| Assunto | Documento |
|---|---|
| Visão geral, funcionalidades e limites | [`00_CENTRAL/OVERVIEW.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/OVERVIEW.md) |
| Arquitetura, módulos e fluxo de dados | [`00_CENTRAL/ARCHITECTURE.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/ARCHITECTURE.md) |
| Rotas `/api` e camadas | [`00_CENTRAL/API_CONTRACTS.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/API_CONTRACTS.md) |
| Banco de dados e migrações | [`00_CENTRAL/DATA_MODEL.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/DATA_MODEL.md) |
| Captura dos logs | [`01_MODULES/CAPTURE.md`](../PROJECT_KNOWLEDGE/01_MODULES/CAPTURE.md) |
| Leitura e processamento das partidas | [`01_MODULES/LOG_READER.md`](../PROJECT_KNOWLEDGE/01_MODULES/LOG_READER.md), [`01_MODULES/REPLAY.md`](../PROJECT_KNOWLEDGE/01_MODULES/REPLAY.md) |
| Regras de negócio | [`02_BUSINESS_RULES/`](../PROJECT_KNOWLEDGE/02_BUSINESS_RULES/) (formato do log, dono das partidas, regras do Standard) |
| Cálculos estatísticos | [`02_BUSINESS_RULES/STATISTICS.md`](../PROJECT_KNOWLEDGE/02_BUSINESS_RULES/STATISTICS.md) e a Skill [`statistical-analyst`](../.claude/skills/statistical-analyst/SKILL.md) |
| Integrações externas (TCGdex, Limitless, malie.io, Google Drive) | [`ARCHITECTURE.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/ARCHITECTURE.md), [`01_MODULES/CARD_LIBRARY.md`](../PROJECT_KNOWLEDGE/01_MODULES/CARD_LIBRARY.md), [`01_MODULES/TOURNAMENTS.md`](../PROJECT_KNOWLEDGE/01_MODULES/TOURNAMENTS.md) |
| Instalação e atualização | [`README.md`](../README.md) (quem usa) e [`01_MODULES/UPDATE_AND_INSTALL.md`](../PROJECT_KNOWLEDGE/01_MODULES/UPDATE_AND_INSTALL.md) (quem desenvolve) |
| Testes e medições | [`00_CENTRAL/WORKFLOW.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/WORKFLOW.md), [`03_DECISIONS/EVIDENCE.md`](../PROJECT_KNOWLEDGE/03_DECISIONS/EVIDENCE.md) e a CI em [`.github/workflows/testes-python.yml`](../.github/workflows/testes-python.yml) |
| Decisões técnicas (D-001 em diante) | [`03_DECISIONS/DECISIONS.md`](../PROJECT_KNOWLEDGE/03_DECISIONS/DECISIONS.md) |
| Problemas conhecidos e pendências | [`05_SESSION_CONTROL/CURRENT_STATE.md`](../PROJECT_KNOWLEDGE/05_SESSION_CONTROL/CURRENT_STATE.md) (alertas) e [`04_IMPLEMENTATIONS/IN_PROGRESS.md`](../PROJECT_KNOWLEDGE/04_IMPLEMENTATIONS/IN_PROGRESS.md) |
| Próximos passos | [`05_SESSION_CONTROL/NEXT_STEPS.md`](../PROJECT_KNOWLEDGE/05_SESSION_CONTROL/NEXT_STEPS.md) e [`04_IMPLEMENTATIONS/BACKLOG.md`](../PROJECT_KNOWLEDGE/04_IMPLEMENTATIONS/BACKLOG.md) |
| Histórico por versão | [`04_IMPLEMENTATIONS/DONE.md`](../PROJECT_KNOWLEDGE/04_IMPLEMENTATIONS/DONE.md) (técnico) e [`novidades.json`](../novidades.json) (quem usa) |
| Trabalho a dois, ramos e Pull Requests | [`00_CENTRAL/COLLABORATION.md`](../PROJECT_KNOWLEDGE/00_CENTRAL/COLLABORATION.md) |
