# PLAYBPO_DATA_MAP — Mapa de dados do PlayBPO

> Missão 01 (diagnóstico, só leitura) · Atualizado em 06/11/2026
> Documento investigativo: **nada aqui foi implementado**. Onde não há confirmação, está escrito "a confirmar" — nada foi presumido.

## 1. O que foi verificado de fato (evidências)

Todas as consultas abaixo foram feitas **sem login, sem credenciais, só com GET**, em 06/11/2026.

| # | Consulta | Resultado | O que isso prova |
|---|----------|-----------|------------------|
| E1 | `GET https://v2.sistemaplaybpo.com.br/public` | `200`, página HTML "Swagger UI" (swagger-ui-dist 5.17.14), que carrega `/assets/js/swagger-init.js` | **Existe documentação oficial da API pública** no formato Swagger/OpenAPI. |
| E2 | `GET .../assets/js/swagger-init.js` (o arquivo que aponta para a especificação) | `403`, página de desafio da Cloudflare ("Just a moment...") | A especificação **não pode ser lida por robô**; só por uma pessoa num navegador. Não foi feita nenhuma tentativa de contornar. |
| E3 | Página `/public` aberta uma vez num navegador automatizado | Título "Swagger UI", corpo vazio (a especificação não carregou) | Confirma E2. |
| E4 | `GET https://v2.sistemaplaybpo.com.br/public/empresas` sem credencial | `401`, JSON `{"messages":{"error":"Sem autorização!","statusCode":401}}` | O endpoint **existe e exige autenticação**. Formato de erro: `messages.error` + `messages.statusCode`. O tipo de autenticação (token, chave, cabeçalho) **não foi descoberto** — está na especificação. |
| E5 | `GET https://sistemaplaybpo.com.br` | `403`, desafio da Cloudflare | O site principal também barra acesso automatizado. |
| E6 | Busca pública na web | Só páginas de terceiros (comparadores B2BStack, notícia de aporte da Bossa Invest) | Nenhuma documentação técnica pública fora do Swagger. Produto descrito como "plataforma de gestão de tarefas para BPO financeiro". |

Os demais endpoints citados na missão (`/public/resumo-empresas`, `/public/comunicacoes-pendentes`, `/public/comunicacoes-esperando-resposta`) **não foram chamados**: sem credencial, o resultado seria o mesmo `401` de E4, e com credencial a missão proíbe consultas sem autorização.

Também foi verificado: **não há credencial do PlayBPO configurada** neste ambiente nem no repositório.

## 2. Legenda de classificação

| Sigla | Significado |
|-------|-------------|
| **API** | Disponível via API oficial (endpoint documentado conhecido) |
| **API?** | Endpoint conhecido, mas campos/abrangência **a confirmar** na especificação |
| **EXP** | Disponível via exportação (CSV/XLSX/PDF) — **a confirmar** quais telas exportam |
| **INT** | Disponível via integração autorizada (ERP/banco) — **a confirmar** |
| **ESC** | Depende de esclarecimento da PlayBPO |
| **IND** | Indisponível no momento |

## 3. Endpoints conhecidos (fonte: enunciado da missão + E1/E4)

| Método | Caminho | Status confirmado | Autenticação | Campos | Paginação/filtros |
|--------|---------|-------------------|--------------|--------|-------------------|
| GET | `/public` | 200 — documentação Swagger | Não | — | — |
| GET | `/public/empresas` | Existe; 401 sem credencial | Sim (tipo a confirmar) | a confirmar | a confirmar |
| GET | `/public/resumo-empresas` | Não chamado | Provável (a confirmar) | a confirmar | a confirmar |
| GET | `/public/comunicacoes-pendentes` | Não chamado | Provável (a confirmar) | a confirmar | a confirmar |
| GET | `/public/comunicacoes-esperando-resposta` | Não chamado | Provável (a confirmar) | a confirmar | a confirmar |

Formato de erro conhecido: `{"messages": {"error": "<texto>", "statusCode": <número>}}`.

## 4. Mapa por módulo

Colunas pedidas: fonte · método autorizado · campos · identificador único · relação com empresa · atualização · limites · histórico · intervenção manual · classificação.

### 4.1 Empresas
- **Fonte:** API pública, `GET /public/empresas` (+ `GET /public/resumo-empresas`).
- **Método autorizado:** API oficial com a credencial do próprio escritório (depois da autorização do Pedro).
- **Campos:** a confirmar na especificação. Esperados (hipótese, **não confirmados**): id, razão social/nome, CNPJ, situação.
- **Identificador único:** a confirmar (provável id interno do PlayBPO; CNPJ como chave secundária).
- **Relação com empresas:** é a entidade-raiz; todos os outros módulos se ligam a ela.
- **Atualização:** leitura periódica (pull). Não há webhook conhecido.
- **Limites:** paginação e limite de requisições a confirmar.
- **Histórico:** a API provavelmente devolve só o estado atual → histórico só se o nosso sistema guardar fotos (snapshots).
- **Intervenção manual:** gerar/guardar a credencial.
- **Classificação:** **API?** (endpoint confirmado, campos a confirmar).

### 4.2 Tarefas
- **Fonte:** nenhum endpoint conhecido. É o centro do produto ("gestão de tarefas de BPO"), então a ausência na API pública é uma lacuna relevante.
- **Método autorizado:** a confirmar — exportação da tela de tarefas, se existir; ou endpoint a ser liberado pela PlayBPO.
- **Campos / id / limites:** a confirmar.
- **Relação com empresas:** esperada (cada tarefa pertence a uma empresa-cliente) — a confirmar.
- **Histórico:** a confirmar (concluídas/atrasadas por período).
- **Intervenção manual:** alta (exportar e importar arquivo), até haver endpoint.
- **Classificação:** **ESC** (e **EXP** se a tela exportar).
- **Observação:** `resumo-empresas` pode trazer contagens de tarefas por empresa — a confirmar.

### 4.3 Lançamentos financeiros
- **Fonte:** nenhum endpoint conhecido.
- **Método autorizado:** exportação (a confirmar) ou integração com ERP/banco do cliente (a confirmar).
- **Campos esperados (hipótese):** data, valor, conta, categoria/plano de contas, histórico, empresa, conciliado sim/não.
- **Identificador único:** a confirmar; em arquivo exportado pode não existir → chave composta (empresa + data + valor + descrição + conta) com risco de duplicidade.
- **Histórico:** sim, se a exportação permitir escolher período.
- **Classificação:** **ESC** / **EXP** / **INT** — nenhum confirmado.

### 4.4 Indicadores e relatórios
- **Fonte:** possivelmente `GET /public/resumo-empresas` (nome sugere resumo por empresa) — a confirmar o conteúdo.
- **Relatórios em PDF:** a confirmar se existem e se são exportáveis.
- **Estratégia recomendada:** calcular os indicadores **no nosso sistema** a partir dos dados brutos (empresas, comunicações, e depois tarefas/financeiro), em vez de depender de relatórios prontos.
- **Histórico:** só se guardarmos fotos diárias do resumo.
- **Classificação:** **API?** (resumo) + **ESC** (relatórios).

### 4.5 Comunicações
- **Fonte:** `GET /public/comunicacoes-pendentes` e `GET /public/comunicacoes-esperando-resposta`.
- **Abrangência:** os nomes indicam **só comunicações em aberto**. Comunicações já respondidas/encerradas **não** parecem disponíveis → sem histórico completo pela API.
- **Campos esperados (hipótese):** id, empresa, assunto, data de envio, prazo, responsável, situação.
- **Histórico:** reconstruível parcialmente: se uma comunicação some da lista "pendentes" entre duas sincronizações, registramos a data em que saiu (sem saber o motivo).
- **Anexos:** a confirmar; tratar como dado sensível (ver arquitetura).
- **Classificação:** **API?** (parcial: só em aberto).

### 4.6 Contas a pagar e a receber
- **Fonte:** nenhum endpoint conhecido.
- **Método autorizado:** exportação (a confirmar) ou integração ERP (a confirmar).
- **Campos esperados (hipótese):** empresa, fornecedor/cliente, documento, vencimento, valor, situação (aberto/pago/vencido), data de pagamento.
- **Identificador único:** a confirmar.
- **Classificação:** **ESC** / **EXP**.

### 4.7 Documentos e arquivos
- **Fonte:** nenhum endpoint conhecido.
- **Risco:** é o módulo mais sensível (notas, boletos, extratos, documentos pessoais — LGPD).
- **Recomendação:** na primeira fase, **não copiar arquivos**; no máximo guardar metadados (nome, tipo, data, empresa) se a PlayBPO fornecer, e abrir o documento no próprio PlayBPO.
- **Classificação:** **IND** (no momento) / **ESC**.

## 5. Quadro-resumo

| Módulo | Classificação | Fonte principal | Histórico | Intervenção manual |
|--------|---------------|-----------------|-----------|--------------------|
| Empresas | API? | `/public/empresas`, `/public/resumo-empresas` | Por fotos nossas | Baixa |
| Tarefas | ESC (EXP?) | — | A confirmar | Alta |
| Lançamentos financeiros | ESC / EXP? / INT? | — | Se exportação por período | Alta |
| Indicadores e relatórios | API? (resumo) + ESC | `/public/resumo-empresas` | Por fotos nossas | Baixa/Média |
| Comunicações | API? (só em aberto) | `/public/comunicacoes-*` | Parcial | Baixa |
| Contas a pagar/receber | ESC / EXP? | — | Se exportação por período | Alta |
| Documentos e arquivos | IND / ESC | — | — | — |

## 6. Como fechar as lacunas deste mapa (passo do Pedro, sem robô)

1. Abrir `https://v2.sistemaplaybpo.com.br/public` **no seu navegador** (a checagem da Cloudflare passa normalmente para uma pessoa).
2. Na página do Swagger, clicar no link da especificação (geralmente no topo, algo como `openapi.json` ou `swagger.json`) e **salvar o arquivo**.
3. Entregar esse arquivo para a próxima sessão (ele não tem senha; é documentação pública). Com ele, as colunas "a confirmar" das seções 3 e 4 são preenchidas sem nenhuma chamada autenticada.
4. Dentro do PlayBPO, anotar **quais telas têm botão de exportar** (Tarefas, Financeiro, Contas a pagar/receber, Relatórios) e em qual formato.
