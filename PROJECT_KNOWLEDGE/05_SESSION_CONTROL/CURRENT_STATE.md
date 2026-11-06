# Estado atual do projeto

> Atualizado em 06/11/2026, na sessão da Skill "Statistical Analyst" (inventário dos métodos estatísticos). **Atualize este arquivo no fim de toda sessão** (o que mudou, o que ficou pendente, o que não foi verificado).

## Versão
- **06/11/2026: publicada a 2026.11.06-2** (depois da 2026.11.06-1, `9c6519b`): deck do adversário sempre pelo NB2 (D-040), marca
  "incerto" com confiança < 0,6 (D-042) e faixas das telas de torneio com a dependência entre partidas do mesmo jogador (D-041);
  e2 corrigido. 4 testes OK; marca conferida na tela numa cópia com os dados do Pedro. Detalhes em `../04_IMPLEMENTATIONS/DONE.md`.
  A rodada de hardening da Skill (06/11) **não** está neste commit: segue sem commit na pasta do projeto.
- **Publicada na `main` do GitHub: 2026.11.05-6** (commit `2600e4c`, 05/11/2026, junto com a -4 e a -5):
  - 2026.11.05-4 — Biblioteca de cartas não para a atualização inteira por uma carta que o TCGdex não entrega (D-034);
  - 2026.11.05-5 — campo **Época** nas análises (D-036), "Ver todas" e lista de partidas mais rápida (D-037), descarte no replay (D-035);
  - 2026.11.05-6 — filtros "Deck do jogador" e "Deck do adversário" em Partidas; ícones dos decks de volta (D-038).
  Histórico técnico em `../04_IMPLEMENTATIONS/DONE.md`.
- **Publicada em 06/11: 2026.11.06-1** — o painel busca de novo nomes e ícones dos decks quando o cadastro muda no servidor
  (`versao_arquetipos` em `/api/status`). Antes, quem abria a 2026.11.05-6 só via os ícones depois de apertar F5.
- O Coletor do Pedro estava na 2026.11.05-6 desde 06/11 00:33 (cadastro de decks já refeito com os ícones).
- O repositório `PedroPauloAzevedo/pkmtracking` é **público** e não tem Releases.
- Os programas dos amigos e o do Pedro se atualizam pelo aviso "Nova versão disponível".

## Ramos
- `main` = 2026.11.06-2 (`101da5f`) + Skill "Statistical Analyst" de `55a000f` (igual ao GitHub).
- `icones-painel` (pasta do projeto): a rodada de hardening da Skill e a base estratégica, juntadas com a `main` nova; vai por PR
  para revisão. O código da 2026.11.06-1 que estava aqui sem commit é idêntico ao da `main`.
- `statistical-analyst`: publicado na `main` em 06/11 (`49664da`).
- `versoes-2026.11.05-4-e-5`: ficou no mesmo commit da `main` (já publicado). `replay-premios`, `docs-project-knowledge`,
  `corrige-modo-automatico` e `replay-maos`: ramos antigos, já publicados.

## O que está funcionando (verificado)
- Captura pela área de transferência: funcionando no computador do Pedro (várias partidas gravadas em 05/11).
- Os 4 testes (`teste_tracker`, `teste_seguranca`, `teste_replay`, `teste_telas`) terminaram com OK na 2026.11.05-6 (numa cópia de teste).
- Ícones: na cópia com os dados do Pedro, ao abrir a versão nova, as 67 partidas da lista (ele e um amigo) ficam com ícone nos dois
  decks; 32 decks antigos do cadastro continuam sem ícone até aparecerem num torneio importado.
  Os testes novos do descarte no replay e do "Ver todas" falham na versão publicada, como deviam.
- Conferido na tela com uma cópia dos dados do Pedro (porta 8799): separador de época às 15:00 de 05/11 (a partida das 14:44 fica na
  época 30th Celebration), filtro da época Delta Reign (9 partidas), Meta com a época Pitch Black (Mundial e Baltimore) e o aviso de
  que a Delta Reign vale nos torneios em 20/11, linhas tracejadas nos gráficos, "Ver todas" e o replay do recuo com dois Dreepy.
- Replay: descartes de carta presa 182/182 nas sublinhas e 0 erros depois de nocaute; prêmios 253/253; mãos 109/109 (`EVIDENCE.md`).
- Lista de partidas: ~0,1 s depois do primeiro cálculo, que é feito em segundo plano ao abrir o programa (antes: 2,2 s a cada
  2 minutos na cópia; 3 a 10 s no Coletor do Pedro).

## O que falta confirmar
- **Modo automático com o jogo real depois da 2026.11.05-1.** Ainda não houve partida com a versão corrigida. Ver
  `../04_IMPLEMENTATIONS/IN_PROGRESS.md`.
- A hora em que o TCG Live libera uma coleção (10h do Pacífico, na véspera do lançamento) veio de anúncios de coleções anteriores;
  a data de validade em torneio da 30th Celebration (25/09/2026) foi calculada pela regra, sem anúncio oficial (D-036).
- A 2026.11.05-4 não foi testada contra o TCGdex de verdade com falha real (só com o TCGdex falso do teste).
- A Delta Reign ainda não estava no TCGdex nem no Limitless em 05/11 à noite (pedido aberto no GitHub do TCGdex). Quando entrar, a
  biblioteca baixa sozinha; até lá, as cartas dela aparecem como retângulo com o nome.

## Alertas
- **Inventário estatístico (06/11):** várias análises usam só as listas do topo dos torneios (viés de seleção), o k = 24 do
  confronto ajustado foi reconferido e a identificação do deck pelo NB2 foi medida sem vazamento.
  A auditoria (`../03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md`) confirmou o viés das listas do topo e a mistura de 1 jogo com
  melhor de 3 em "seu resultado × meta"; mostrou que o k = 24 continua bom, que a reserva pelos ícones **piora** a identificação do
  deck e que o experimento e2 passou a vazar o teste. **Nada foi mudado no programa**; as recomendações esperam o Pedro.
- O instalador .exe que existe (fora do GitHub, no computador do Pedro) é da versão **2026.11.02-2**; quem instala por ele se
  atualiza sozinho depois. Não há Release no GitHub.
- O estudo de um **servidor central para análises coletivas** foi feito numa sessão que foi apagada; só sobrou um resumo
  (ver `BACKLOG.md`).
- Os scripts de medição do replay, das mãos, dos prêmios e dos descartes ainda estão **fora do repositório** (só no computador do
  Pedro; ver `EVIDENCE.md`).
- Antes de cada commit de documentação, conferir `git diff --stat`: o `7a9850f` apagou este arquivo sem ninguém perceber.
- Coleção nova que ainda não está no TCGdex precisa entrar à mão em `tracker/colecoes.py` (`NEXT_STEPS.md`, item 2).

## Rodada de hardening da Skill (acréscimo de 06/11/2026, sem commit)
- Ponte da Skill agora é **só leitura com trava na execução** (banco `mode=ro` + autorizador do SQLite, funções de escrita bloqueadas,
  vigia contra gravação de arquivos, rede e programas); exige `config.json` na porta 8799 e a marca `dados/COPIA_DE_TESTE.json`.
  `test_ponte.py` (22), `test_sa_tools.py` (31) e `test_referencias.py` OK; os 4 testes de entrega do Coletor OK numa cópia.
- Revisões de conclusão: independência entre partidas só vale para quem tem lista (todos: ICC +0,063); identificação — NB2 melhor na
  acurácia, regra atual melhor para decks raros; NB2 confiante demais (inclinação 0,56); confronto ajustado pior que 50% em 4 de 10
  torneios de teste online pequenos. Nada mudou no programa. `../03_DECISIONS/STATISTICAL_HARDENING_2026-11-06.md`.
- Não verificado: identificação com o deck do adversário de verdade (não há gabarito nos logs); Ladder sem amostra para independência.

## Ambiente
Pastas, instalações, cópias de teste e recursos privados do computador do Pedro: `CLAUDE.local.md` (fora do GitHub).

## Preparação para dois desenvolvedores (acréscimo de 06/11/2026, ramo `docs/preparar-dois-devs`, por Pull Request)
- Decidido pelo Pedro: segundo desenvolvedor no **Mac**, com prioridade de paridade no Mac (D-044); **só o Pedro junta PR na `main`**
  (D-043); repositório continua **público**; e-mail e nick antigos no histórico ficam como estão.
- Criados: `.gitattributes`, `.github/pull_request_template.md`, `.github/CODEOWNERS`, `CLAUDE.local.example.md`,
  `00_CENTRAL/COLLABORATION.md`, `00_CENTRAL/API_CONTRACTS.md`, `00_CENTRAL/DATA_MODEL.md` (a seção do banco saiu do ARCHITECTURE).
  Atualizados: `.gitignore`, `CLAUDE.md`, INDEX, ARCHITECTURE (tabela Windows × Mac), WORKFLOW (seções 6 e 9), OVERVIEW, DECISIONS
  (D-043, D-044), BACKLOG ("Paridade no Mac" M1–M7 e arrumação para dois).
- **Nenhum arquivo do programa mudou** (conferido por `git diff --stat main`); os 4 testes rodaram numa cópia deste ramo.
- Auditoria de segurança (29 commits): nenhum token, senha ou arquivo de `dados/` no histórico; nada a revogar.
- **Pendente no GitHub (só o Pedro faz):** proteger a `main`, convidar o segundo dev como Write, 2FA, apagar ramos ao juntar,
  esconder o e-mail. Lista em `00_CENTRAL/COLLABORATION.md`, seção 9.
- Nada disto foi testado num Mac (não há Mac aqui); o levantamento Windows × Mac é pela leitura do código.
