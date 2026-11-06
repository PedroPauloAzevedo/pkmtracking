# INTEGRATION_GAP_ANALYSIS — Lacunas de integração do PlayBPO

> Missão 01 (diagnóstico, só leitura) · Atualizado em 06/11/2026
> Base: evidências E1–E6 de `PLAYBPO_DATA_MAP.md`.

## 1. Lacunas gerais (valem para todos os módulos)

| # | Lacuna | Impacto | Alternativa | Quem resolve |
|---|--------|---------|-------------|--------------|
| G1 | ~~Especificação da API não lida~~ **Resolvido em 06/11/2026** (`/public?json=true`). **Porém a especificação não descreve as respostas** (nenhum campo) | Não sabemos os campos que cada rota devolve | Uma chamada de teste autorizada pelo Pedro, registrando só os nomes dos campos; ou pedir um exemplo de resposta à PlayBPO | Pedro / PlayBPO |
| G2 | Autenticação **confirmada: HTTP Basic** ("Token de autenticação"). Falta saber o que vai dentro (usuário e senha, ou token) e como gerar | Basic manda a credencial em toda chamada: exige HTTPS sempre e cuidado com logs | Perguntar à PlayBPO como gerar e se dá para criar uma credencial só de leitura, separada da senha pessoal | Pedro / PlayBPO |
| G3 | **Termos de uso da API desconhecidos** | Risco contratual/LGPD ao guardar cópia dos dados | Pedir à PlayBPO os termos da API e confirmar que guardar cópia local é permitido | PlayBPO |
| G4 | **API cobre só 2 dos 7 módulos** (Empresas e Comunicações; Indicadores em parte) | Tarefas, financeiro, contas e documentos ficam sem fonte automática | Importação de arquivos exportados; pedir endpoints novos | PlayBPO / Pedro |
| G5 | **Sem histórico nativo aparente** (endpoints parecem devolver o estado atual) | Gráficos de evolução impossíveis só com a API | Guardar "fotos" a cada sincronização a partir do primeiro dia | Nosso sistema |
| G6 | **Sem webhook conhecido** | Dados só tão atuais quanto a última leitura | Sincronização agendada (ex.: a cada 30–60 min em horário comercial) | Nosso sistema |
| G7 | **Limite de requisições desconhecido**, **sem paginação** e **comunicações exigem `empresaId`** (1 chamada por empresa em cada rota) | Sincronização completa = 2 + 2×N chamadas; risco de bloqueio da chave | 1 requisição por vez com intervalo, respeitar `429`/`Retry-After`, horário comercial | Nosso sistema |
| G8 | **Cloudflare na frente de tudo** | Uma sincronização automatizada pode ser barrada pela Cloudflare mesmo com credencial válida | Confirmar com a PlayBPO que chamadas de servidor com chave são permitidas (e de qual IP) | PlayBPO |

## 2. Lacunas por módulo

### Empresas — viabilidade: **alta**
- Falta: lista de campos, id único, paginação.
- Alternativa se faltar campo: completar com cadastro manual (ex.: apelido, carteira, responsável interno) em tabela própria, **sem** gravar nada no PlayBPO.

### Comunicações — viabilidade: **média/alta (parcial)**
- Falta: comunicações encerradas/respondidas (histórico), conteúdo completo, anexos.
- Alternativa: fotos a cada sincronização → sabemos quando uma comunicação entrou e saiu das listas, e quanto tempo ficou pendente (bom indicador de SLA).
- Limite que não se resolve sozinho: não sabemos se "saiu da lista" = respondida ou cancelada.

### Indicadores e relatórios — viabilidade: **média**
- Falta: conteúdo de `resumo-empresas`; relatórios prontos.
- Alternativa: indicadores calculados por nós a partir dos dados brutos (mais controle, mesma fórmula para todas as empresas).

### Tarefas — viabilidade: **baixa até haver fonte**
- Falta: qualquer endpoint.
- Alternativas, em ordem: (1) pedir endpoint de tarefas à PlayBPO; (2) exportação da tela de tarefas + importação no nosso sistema; (3) contagens que vierem em `resumo-empresas`.
- Risco da importação manual: dados envelhecem rápido; sem id estável pode duplicar.

### Lançamentos financeiros — viabilidade: **baixa até haver fonte**
- Falta: endpoint; não sabemos se há exportação nem integração ERP ativa.
- Alternativas: exportação por período (CSV/XLSX); ou ler direto do ERP/banco do cliente **se** houver integração oficial e autorização do cliente (fora do PlayBPO, exige contrato próprio).
- Risco: dado financeiro de terceiros (clientes do escritório) → LGPD e sigilo.

### Contas a pagar e a receber — viabilidade: **baixa até haver fonte**
- Mesmo caso de Lançamentos. Importação de planilha é o caminho mais provável no curto prazo.

### Documentos e arquivos — viabilidade: **indisponível**
- Falta: endpoint, regras de acesso, termos.
- Recomendação: **fora do escopo da 1ª fase**. Quando entrar: só metadados + link que abre no PlayBPO; nunca copiar o arquivo sem autorização explícita.

## 3. Perguntas para a PlayBPO (enviar por escrito, guardar a resposta)

1. ~~Onde está a especificação?~~ (achada). Vocês podem mandar **exemplos de resposta** de cada rota, com os campos? Há changelog da versão 1.0?
2. A autenticação é HTTP Basic: o que vai em usuário e senha? A credencial é por escritório ou por usuário? Ela expira? Pode ser **somente leitura** e separada da senha de login?
3. Quais os limites de requisições e regras de paginação?
4. Chamadas de servidor (sem navegador) são permitidas apesar da Cloudflare? Precisa liberar IP?
5. Existem ou estão previstos endpoints para **tarefas, lançamentos, contas a pagar/receber, relatórios e documentos**?
6. Há webhooks (avisar quando algo muda)?
7. `comunicacoes-*` traz histórico (encerradas) ou só itens em aberto? Traz anexos?
8. Quais telas exportam CSV/XLSX/PDF e com quais colunas? A exportação traz o id interno?
9. Os termos de uso permitem guardar cópia dos dados num sistema próprio do escritório? Por quanto tempo?
10. Quais integrações com ERPs/bancos existem oficialmente e o que elas trazem para dentro do PlayBPO?

## 4. Dúvidas registradas (não inventadas)

- D1: O ano de fundação diverge entre fontes públicas (2020 × 2022) — irrelevante para a integração, apenas registrado.
- D2: `resumo-empresas` aceita `empresaId` opcional (resolvido em parte). Ainda não se sabe o que o resumo contém.
- D3: A especificação é a versão "1.0" (OpenAPI 3.0.0). A documentação fica em `v2.sistemaplaybpo.com.br`, mas o servidor das chamadas é `api.sistemaplaybpo.com.br`. Confirmar com a PlayBPO qual endereço usar.
- D4: Onde este projeto vai morar: hoje os documentos estão neste repositório (que é público e de outro assunto). Recomendo um repositório **privado** próprio antes de qualquer código.
