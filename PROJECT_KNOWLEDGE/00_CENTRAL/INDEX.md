# Índice da documentação do projeto

> Atualizado em 06/11/2026. Este repositório é a **fonte de verdade** do projeto: tudo o que uma sessão nova precisa saber
> está aqui ou no código. Conversas antigas do Claude Code e a memória automática do Claude **não** são fonte oficial.

## Como usar este índice
1. Comece sempre por [`../05_SESSION_CONTROL/CURRENT_STATE.md`](../05_SESSION_CONTROL/CURRENT_STATE.md) e
   [`../05_SESSION_CONTROL/NEXT_STEPS.md`](../05_SESSION_CONTROL/NEXT_STEPS.md).
2. Pela tabela abaixo, abra **só** os documentos que a tarefa pede (coluna "Ler quando").
3. O detalhe de cada função está na explicação no topo de cada arquivo do código (`tracker/*.py`, `app.py`):
   os documentos de módulo dizem o que é cada coisa e onde está, sem repetir o código.
4. Ao terminar, siga o protocolo de encerramento do [`CLAUDE.md`](../../CLAUDE.md).

## 00_CENTRAL — visão geral
| Documento | O que tem | Ler quando |
|---|---|---|
| [`OVERVIEW.md`](OVERVIEW.md) | O que é o programa, para quem, limites de escopo, funcionalidades, glossário | Primeira sessão; dúvida sobre o que o programa faz |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Camadas, mapa das pastas e módulos, threads, painel, banco de dados, configurações, integrações | Antes de mexer em código; para achar onde algo está |
| [`WORKFLOW.md`](WORKFLOW.md) | Como testar, medir, versionar, publicar, cuidados de privacidade e no Windows, manutenção destes documentos | Antes de testar, publicar ou criar versão |

## 01_MODULES — uma funcionalidade por documento
| Documento | Assunto | Ler quando |
|---|---|---|
| [`CAPTURE.md`](../01_MODULES/CAPTURE.md) | Captura pela área de transferência e modo automático (reconhecer botões e clicar) | Partida não gravada; modo automático |
| [`LOG_READER.md`](../01_MODULES/LOG_READER.md) | Leitor do log, regras de leitura, linhas não lidas | Mudança no leitor ou nas regras de leitura |
| [`REPLAY.md`](../01_MODULES/REPLAY.md) | Replay: mesa, dano, nocautes, mãos dos jogadores, prêmios, versão das cartas | Qualquer erro ou melhoria no replay |
| [`MATCHES_AND_PERFORMANCE.md`](../01_MODULES/MATCHES_AND_PERFORMANCE.md) | Partidas, Desempenho, Decisões | Telas de "Minhas partidas" |
| [`MY_DECKS.md`](../01_MODULES/MY_DECKS.md) | Meus decks, conferência do Standard, Consistência, Lista oficial | Listas e probabilidades |
| [`TOURNAMENTS.md`](../01_MODULES/TOURNAMENTS.md) | Importação de campeonatos e análises de meta | Meta, matchups, perfil de deck, uso de cartas |
| [`CARD_LIBRARY.md`](../01_MODULES/CARD_LIBRARY.md) | Biblioteca de cartas (TCGdex), arte básica, conversor | Cartas, imagens, marcas de regulamento |
| [`FRIENDS.md`](../01_MODULES/FRIENDS.md) | Logs de amigos (.zip e pasta do Google Drive) | Troca de logs entre amigos |
| [`RULES_BASE.md`](../01_MODULES/RULES_BASE.md) | Base de regras do Standard dentro do programa e a rotina mensal | Atualizar a base de regras |
| [`PANEL.md`](../01_MODULES/PANEL.md) | Painel (web), ícone na bandeja, atalhos, janela própria, primeiro uso | Telas e visual |
| [`UPDATE_AND_INSTALL.md`](../01_MODULES/UPDATE_AND_INSTALL.md) | Atualizador, instalador .exe, novidades, entrega para amigos | Publicar versão; instalar para alguém |

## 02_BUSINESS_RULES — regras de negócio
| Documento | O que tem | Ler quando |
|---|---|---|
| [`STANDARD_AND_GAME_RULES.md`](../02_BUSINESS_RULES/STANDARD_AND_GAME_RULES.md) | O que o programa usa das regras do Standard e do jogo | Conferência de listas, probabilidades, replay |
| [`BATTLE_LOG_FORMAT.md`](../02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md) | Cada tipo de linha do Battle Log, suas "manias" e como o programa interpreta | Qualquer coisa que leia logs (leitor, replay, mãos) |
| [`PLAYERS_AND_OWNERSHIP.md`](../02_BUSINESS_RULES/PLAYERS_AND_OWNERSHIP.md) | Quem é "você", de quem é cada partida, amigos, repetidas | Partidas, amigos, filtro Jogador |
| [`STATISTICS.md`](../02_BUSINESS_RULES/STATISTICS.md) | Fórmulas, limites e números das análises | Mexer em qualquer análise ou estatística |

## 03_DECISIONS — decisões e evidências
| Documento | O que tem | Ler quando |
|---|---|---|
| [`DECISIONS.md`](../03_DECISIONS/DECISIONS.md) | Registro numerado das decisões (e do que foi pesquisado e descartado) | Antes de propor mudança de rumo; ao registrar decisão nova |
| [`EVIDENCE.md`](../03_DECISIONS/EVIDENCE.md) | Medições que sustentam as decisões (experimentos e1–e10, replay, mãos, modo automático) | Antes de trocar um algoritmo; para repetir uma medição |
| [`MISSION_REPORT_2026-11-02.md`](../03_DECISIONS/MISSION_REPORT_2026-11-02.md) | Relatório completo da missão de 2/nov (pesquisas, matemática, medições, riscos) | Só ao mexer em análises/estatística a fundo |
| [`STATISTICAL_INVENTORY_2026-11-06.md`](../03_DECISIONS/STATISTICAL_INVENTORY_2026-11-06.md) | Inventário de cada método matemático/estatístico: fórmula, parâmetros, testes, experimentos refeitos em 06/11 e classificação (documentado → validado) | Antes de mexer, confiar ou propor troca de qualquer análise |
| [`STATISTICAL_AUDIT_2026-11-06.md`](../03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md) | Auditoria do motor estatístico: 10 achados (comprovados, descartados, recomendações) | Antes de confiar numa tela de análise ou propor mudança nela |
| [`STATISTICAL_HARDENING_2026-11-06.md`](../03_DECISIONS/STATISTICAL_HARDENING_2026-11-06.md) | Rodada de hardening da Skill: ponte só leitura, registro dos experimentos, revisão da independência e da identificação, calibração a fundo, avaliação A–H | Junto com a auditoria; antes de usar a ponte ou citar independência, identificação ou calibração |

## 04_IMPLEMENTATIONS — o que fazer, o que está em curso, o que foi feito
| Documento | O que tem | Ler quando |
|---|---|---|
| [`BACKLOG.md`](../04_IMPLEMENTATIONS/BACKLOG.md) | Ideias e pendências, por prioridade | Planejar trabalho novo |
| [`IN_PROGRESS.md`](../04_IMPLEMENTATIONS/IN_PROGRESS.md) | O que está começado e falta terminar ou confirmar | Início de sessão |
| [`DONE.md`](../04_IMPLEMENTATIONS/DONE.md) | Histórico técnico por versão | Entender por que algo é como é |

## 05_SESSION_CONTROL — controle de sessão
| Documento | O que tem | Ler quando |
|---|---|---|
| [`CURRENT_STATE.md`](../05_SESSION_CONTROL/CURRENT_STATE.md) | Versão publicada, ramos, testes, alertas, o que falta confirmar | **Toda sessão, no início**; atualizar no fim |
| [`NEXT_STEPS.md`](../05_SESSION_CONTROL/NEXT_STEPS.md) | As próximas 3 a 5 ações concretas | **Toda sessão, no início**; atualizar no fim |

## Outras fontes no repositório (não repetidas aqui)
| Arquivo | O que é |
|---|---|
| `README.md`, `COMECE_AQUI.txt` | Manual de quem usa o programa (os amigos). `COMECE_AQUI.txt` fica em CRLF |
| `web/LEIA-ME.md` | Como o painel está dividido em arquivos (`web/js/*.js`) |
| `modelos/LEIA-ME.txt` | Imagens dos botões do modo automático |
| `docs/regras-standard.md` | Base de regras do Standard. **É lida pelo programa**: não mudar de lugar nem o formato da tabela de marcas |
| `novidades.json` | O que mudou em cada versão, do ponto de vista de quem usa (o programa mostra na tela) |
| `testes/`, `testes/experimentos/` | Testes de regressão, segurança, replay e telas; experimentos de medição |
| `.claude/skills/statistical-analyst/` | Skill de matemática e estatística: matriz dos métodos (`knowledge/KNOWN_METHODS.md`), fórmulas, lacunas, ferramentas (`tools/`), experimentos de auditoria e testes. O Claude Code a carrega sozinho quando a tarefa é de análise |

## Fora do GitHub (só no computador do Pedro)
| Arquivo | O que é |
|---|---|
| `CLAUDE.local.md` | Dados da máquina: pastas reais, instalações, nick, pasta do Drive, cópias de teste, links e códigos privados. Ler quando a tarefa envolver o computador do Pedro |
| `_arquivo_docs_antigos/` | Documentos antigos (antes de 05/11/2026), guardados só como cópia. Tudo o que tinham foi migrado para cá |
| `ferramentas/video/` | Como refazer o vídeo tutorial (excluída do GitHub; ver `DONE.md`, versão 2026.11.02-3) |
