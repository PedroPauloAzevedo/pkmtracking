# TECHNICAL_ARCHITECTURE — Proposta de arquitetura (visualizador PlayBPO)

> Missão 01 (diagnóstico, só leitura) · Atualizado em 06/11/2026
> Proposta para aprovação. **Nada foi implementado nem instalado.**

## 1. Princípios

1. **PlayBPO é a fonte oficial.** Nosso sistema é uma cópia de leitura; nunca escreve no PlayBPO (na fase 1 nem existe código de escrita).
2. **Só o Núcleo de Integração fala com o PlayBPO.** Os módulos (telas) leem só o nosso banco.
3. **Toda linha sabe de onde veio:** origem (API/arquivo), data da sincronização, id da execução.
4. **Separação por empresa** desde o banco (não só na tela).
5. **Duas portas de entrada iguais:** API oficial e arquivo exportado passam pela mesma normalização.
6. **Histórico por fotos:** como a API parece só dar o estado atual, guardamos versões.

## 2. Avaliação da pilha pedida

| Camada | Escolha | Avaliação |
|--------|---------|-----------|
| Frontend | React + TypeScript + Tailwind + shadcn/ui | Adequada. shadcn dá tabelas, filtros e cards prontos; somar TanStack Query (cache de chamadas) e TanStack Table, e Recharts para gráficos. |
| Backend | Python + FastAPI | Adequada. Tipagem com Pydantic encaixa na "camada de normalização"; `httpx` para chamar a API; agendador simples (APScheduler) na fase 1. |
| Banco | PostgreSQL | Adequado. JSONB para guardar a resposta bruta; Row-Level Security para separar empresas; Alembic para migrações. |
| Ponto de atenção | — | Para quem está aprendendo, são 2 linguagens e ~6 ferramentas. Sugestão: começar só com backend + banco + 1 tela; o resto entra quando precisar. |

## 3. Visão geral

```
            ┌──────────────────────────── nosso sistema ────────────────────────────┐
 PlayBPO    │  NÚCLEO DE INTEGRAÇÃO                                                 │
 API ──────►│  conectores/ ─► raw (bruto) ─► normalização ─► persistência ─► banco  │
 (só GET)   │      ▲                                                       │        │
 Arquivos ─►│  importador de arquivos (CSV/XLSX) ──────────────────────────┘        │
 exportados │                                                                       │
            │  MÓDULOS (empresas, comunicações, tarefas, financeiro, ...)           │
            │      só leem o banco ─► API interna (FastAPI) ─► Frontend React       │
            │  PERMISSÕES: usuário ↔ empresas que pode ver (aplicado no banco)      │
            └───────────────────────────────────────────────────────────────────────┘
```

## 4. Estrutura de diretórios (repositório próprio, privado)

```
playbpo-viewer/
├── .env.example            # só nomes das variáveis, sem valores
├── .gitignore              # inclui .env, data/, uploads/
├── docker-compose.yml      # postgres local (fase 1)
├── backend/
│   ├── pyproject.toml
│   ├── alembic/            # migrações do banco
│   └── app/
│       ├── main.py
│       ├── config.py       # lê .env (pydantic-settings); nunca imprime segredos
│       ├── core/
│       │   ├── integration/
│       │   │   ├── client.py        # ÚNICO lugar que chama o PlayBPO (só GET)
│       │   │   ├── connectors/      # um arquivo por endpoint
│       │   │   ├── importers/       # CSV/XLSX exportados manualmente
│       │   │   ├── normalize/       # bruto -> modelo canônico (Pydantic)
│       │   │   └── sync.py          # orquestra execução, registra sync_runs
│       │   ├── db/                  # sessão, modelos, RLS
│       │   ├── security/            # autenticação do nosso app, permissões
│       │   └── logging.py           # logs estruturados, com máscara de dados
│       ├── modules/
│       │   ├── empresas/            # router + queries (lê só o banco)
│       │   ├── comunicacoes/
│       │   ├── indicadores/
│       │   ├── tarefas/             # entra quando houver fonte
│       │   ├── financeiro/          # idem
│       │   └── documentos/          # idem (só metadados)
│       └── tests/
└── frontend/
    ├── package.json
    └── src/
        ├── components/ui/           # shadcn
        ├── lib/api.ts               # chama SÓ o nosso backend
        └── modules/                 # uma pasta por módulo, espelhando o backend
```

## 5. Banco de dados (esquema proposto)

Três esquemas no Postgres:

- **`raw`** — resposta exatamente como chegou (JSONB), para auditoria e reprocessar sem chamar a API de novo.
- **`core`** — dados normalizados que as telas usam.
- **`ops`** — controle (execuções, arquivos importados, usuários, permissões, auditoria).

```sql
-- ops: cada sincronização ou importação
ops.sync_runs (id, source text /*'api'|'file'*/, endpoint text, started_at, finished_at,
               status text /*'ok'|'erro'|'parcial'*/, records_read int, records_changed int,
               error_message text /*sem dados sensíveis*/)

ops.file_imports (id, sync_run_id, file_name, file_sha256, module, uploaded_by, uploaded_at)

-- raw: bruto
raw.payloads (id, sync_run_id, endpoint, empresa_ext_id, payload jsonb, payload_hash, fetched_at)

-- core: entidade-raiz
core.empresas (id uuid, ext_id text UNIQUE /*id do PlayBPO, a confirmar*/, cnpj, nome, ativo,
               source, first_seen_at, last_seen_at, last_sync_run_id)

-- core: histórico por versões (fotos). Mesmo padrão para os outros módulos.
core.comunicacoes_versoes (id, empresa_id, ext_id, situacao /*'pendente'|'esperando_resposta'*/,
               dados jsonb, valid_from, valid_to /*null = atual*/, sync_run_id)

core.resumo_empresas_fotos (id, empresa_id, data_foto date, dados jsonb, sync_run_id)

-- módulos sem API: mesma forma, origem 'file'
core.tarefas, core.lancamentos, core.titulos (pagar/receber), core.documentos_meta
   -> todos com empresa_id, ext_id (ou chave composta), source, sync_run_id

-- ops: permissões
ops.usuarios (id, email, nome, papel)
ops.usuario_empresas (usuario_id, empresa_id)   -- quem vê o quê
```

**Regras:**
- Toda tabela de `core` tem `empresa_id` + **Row-Level Security** filtrando por `ops.usuario_empresas`.
- Gravação idempotente: `INSERT ... ON CONFLICT (ext_id) DO UPDATE` só se o `payload_hash` mudou.
- Quando o id oficial não existir (arquivos), chave composta + `file_sha256` para não importar o mesmo arquivo duas vezes.
- Nunca apagar: item que sumiu da API ganha `valid_to`/`last_seen_at` — vira histórico.

## 6. Estratégia de sincronização

| Item | Proposta |
|------|----------|
| Gatilho | Agendado (ex.: a cada 60 min, só horário comercial) + botão "atualizar agora" para admin |
| Ordem | 1) empresas → 2) resumo-empresas → 3) comunicações (dependem de empresa) |
| Tipo | Leitura completa (a API não parece ter filtro "alterados desde") — rever quando a especificação for lida |
| Ritmo | Uma requisição por vez, pausa entre páginas, respeitar `429`/`Retry-After`, tentativas com espera crescente (máx. 3) |
| Falha | Execução marcada `erro`/`parcial`; dados anteriores continuam valendo; tela mostra "atualizado em ..." |
| Arquivos | Upload na tela de admin → validação de colunas → prévia → confirmar → mesma normalização da API |
| Somente GET | O `client.py` só tem método GET; teste automatizado falha se alguém adicionar POST/PUT/PATCH/DELETE |

## 7. Segurança, integridade e LGPD

| Tema | Medida |
|------|--------|
| Credenciais | Só em `.env` (fora do Git) ou cofre do servidor; `.env.example` com nomes vazios; nunca em log, erro ou tela; troca periódica |
| Versionamento | `.gitignore` com `.env`, `data/`, `uploads/`; varredura de segredos antes de cada commit; repositório **privado** |
| Separação por empresa | RLS no Postgres + filtro na API interna + testes que tentam ler empresa alheia |
| Origem e data | `source`, `sync_run_id`, `fetched_at` em toda linha |
| Logs | Estruturados (JSON); mascaram CNPJ/CPF/e-mail; guardam id da execução, endpoint, código HTTP, tempo |
| Erros | Mensagem amigável na tela; detalhe técnico só no log; nunca devolver o payload bruto ao usuário |
| Documentos | Fase 1 não copia arquivos; depois, só metadados + link. Se um dia copiar: storage privado, links temporários, antivírus |
| Permissões do PlayBPO | Usar só endpoints documentados, com a chave do escritório, dentro dos termos; nada de raspagem de tela |
| LGPD | Base legal: execução de contrato do escritório com o cliente (confirmar com jurídico); mínimo de dados necessário; prazo de retenção definido; registro de quem acessou o quê (`ops.auditoria`); procedimento para apagar dados de um cliente que sair |
| Sistema original | Nenhuma alteração: só GET; nenhum dado digitado no nosso app volta para o PlayBPO na fase 1 |

## 8. Preparado para escrever no futuro (sem fazer agora)

- Escrita só existiria num módulo separado `core/integration/writers/`, desligado por padrão (variável `PLAYBPO_WRITE_ENABLED=false`), com aprovação por usuário, registro em auditoria e endpoint documentado pela PlayBPO.
- Os módulos continuam sem falar com o PlayBPO: pedem ao núcleo, que decide.

## 9. Fases sugeridas

| Fase | Entrega | Depende de |
|------|---------|------------|
| 0 | Ler a especificação (arquivo salvo pelo Pedro) e respostas da PlayBPO; atualizar `PLAYBPO_DATA_MAP.md` | Pedro / PlayBPO |
| 1 | Núcleo + banco + **Empresas** (lista e ficha) + registro de sincronização | Credencial somente leitura, autorizada pelo Pedro |
| 2 | **Comunicações** (pendentes / esperando resposta, tempo em aberto) + resumo por empresa | Fase 1 |
| 3 | Importador de arquivos + primeiro módulo sem API (Tarefas ou Contas a pagar/receber) | Saber quais telas exportam |
| 4 | Indicadores calculados e painel geral | Fases 2–3 com algumas semanas de fotos |
| 5 | Documentos (metadados) e, se autorizado, operações de escrita | PlayBPO + jurídico |
