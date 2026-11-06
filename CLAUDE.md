# Coletor TCG Live — guia do Claude Code

Programa local (Python + Flask + SQLite + painel HTML) que grava e analisa as partidas de **Pokémon TCG Live** (jogo em inglês,
**só formato Standard**) e importa campeonatos. Dono: Pedro (GitHub `PedroPauloAzevedo`), trabalha com finanças, usa Excel e está
aprendendo a programar: **fale com ele em português do Brasil, simples, sem jargão**, dizendo o que foi feito e por quê.

**Este repositório é a fonte de verdade.** Tudo o que importa está em `PROJECT_KNOWLEDGE/` ou no código. Conversas antigas e a
memória automática do Claude **não** são fonte: se algo importante só existir numa conversa, registre aqui.

## Protocolo de toda sessão
**Início**
1. Ler `PROJECT_KNOWLEDGE/05_SESSION_CONTROL/CURRENT_STATE.md` e `NEXT_STEPS.md`.
2. Abrir `PROJECT_KNOWLEDGE/00_CENTRAL/INDEX.md` e ler **só** os documentos que a tarefa pede (coluna "Ler quando").
3. Se a tarefa envolver o computador do Pedro (pastas, instalação dele, pasta do Drive, recursos privados), ler `CLAUDE.local.md`
   (existe só no computador dele; fica fora do GitHub).
4. Antes de mexer num arquivo de código, ler a explicação no topo dele.

**Durante** — decisão técnica → `03_DECISIONS/DECISIONS.md`; regra nova ou "mania" nova do log → `02_BUSINESS_RULES/`;
módulo alterado → seu documento em `01_MODULES/`; medição → `03_DECISIONS/EVIDENCE.md`.

**Fim** — atualizar `CURRENT_STATE.md` e `NEXT_STEPS.md`; mover itens entre `04_IMPLEMENTATIONS/BACKLOG.md`, `IN_PROGRESS.md` e
`DONE.md`; trocar a data "Atualizado em" dos documentos editados. Detalhes em `00_CENTRAL/WORKFLOW.md`, seção 9.

## Regras de ouro (detalhes e motivos em `00_CENTRAL/WORKFLOW.md` e `03_DECISIONS/DECISIONS.md`)
- **Escopo:** só Standard (D-001); só computador, nada para celular (D-002); servidor só local com proteção de origem (D-003);
  `dados/` de cada pessoa nunca vai para o GitHub nem é tocado pelo atualizador (D-004).
- **Testar sempre numa cópia** em pasta curta com `"porta": 8799` em `dados/config.json` (na 8765 o programa novo fecha o Coletor do
  Pedro). Nunca mexer na instalação do Pedro; banco real só para leitura; não copiar logs para a área de transferência com o Coletor
  dele aberto; rodar scripts a partir da pasta da cópia. Diagnóstico com imagens: **só a janela do jogo** (D-016).
- **Antes de entregar:** `python -I testes/teste_tracker.py <cópia> testes/leitor-tcg-live.html`, `python testes/teste_seguranca.py <cópia>`,
  `python -I testes/teste_replay.py <cópia>` e `python -I testes/teste_telas.py <cópia>` → todos `OK`.
- **Algoritmo só muda com medição** contra o atual, nos mesmos dados (D-017).
- **Banco e leitor:** coluna nova → migração em `banco.iniciar()` e INSERT com nomes de colunas; leitor mudou → `banco.VERSAO_LEITOR`;
  índice de cartas mudou → `cartas.VERSAO_INDICE`.
- **Versão nova:** `versao.txt` (`AAAA.MM.DD-N`) + topo de `novidades.json` + `DONE.md` + passo a passo para os amigos no chat (D-024).
- **Git:** um ramo por tarefa; **commit e push só quando o Pedro pedir**; publicar = `merge --ff-only` na `main` + push; autor
  `Claude <noreply@anthropic.com>`; `.bat` e `COMECE_AQUI.txt` em CRLF, o resto em LF (D-025).
- **O repositório é público:** nada de caminhos do computador do Pedro, nicks reais, e-mail, pasta do Drive, links ou códigos
  privados, tokens ou senhas em arquivos publicados — isso vai em `CLAUDE.local.md` (D-026, D-027). Senhas e tokens nunca no chat.
- `docs/regras-standard.md` é lido pelo programa: não mudar de lugar nem o formato da tabela de marcas e do item de promos.
- Painel (`web/`): o que roda ao carregar só usa o que veio antes no `index.html` (`ROTAS` fica no `inicio.js`); depois de um
  `await`, procurar elementos dentro do próprio quadro (`el.querySelector`); toda tela começa com `const vez = novaTela()` e,
  depois de esperar os dados, só desenha se `!telaVelha(vez)` (uma tela lenta não pode cobrir a nova; D-037).
- Não remover funcionalidades nem apagar arquivos ou dados sem listar e pedir autorização ao Pedro.
