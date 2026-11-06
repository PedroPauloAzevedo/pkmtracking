# Estado atual do projeto

> Atualizado em 06/11/2026, na sessão da Skill "Statistical Analyst" (inventário dos métodos estatísticos). **Atualize este arquivo no fim de toda sessão** (o que mudou, o que ficou pendente, o que não foi verificado).

## Versão
- **Publicada na `main` do GitHub: 2026.11.05-6** (commit `2600e4c`, 05/11/2026, junto com a -4 e a -5):
  - 2026.11.05-4 — Biblioteca de cartas não para a atualização inteira por uma carta que o TCGdex não entrega (D-034);
  - 2026.11.05-5 — campo **Época** nas análises (D-036), "Ver todas" e lista de partidas mais rápida (D-037), descarte no replay (D-035);
  - 2026.11.05-6 — filtros "Deck do jogador" e "Deck do adversário" em Partidas; ícones dos decks de volta (D-038).
  Histórico técnico em `../04_IMPLEMENTATIONS/DONE.md`.
- O Coletor do Pedro estava na 2026.11.05-3 às 19:55 de 05/11; o aviso de versão nova deve aparecer para ele e para os amigos.
- O repositório `PedroPauloAzevedo/pkmtracking` é **público** e não tem Releases.
- Os programas dos amigos e o do Pedro se atualizam pelo aviso "Nova versão disponível".

## Ramos
- `main` = 2026.11.05-6 + documentação (`76a2005`, igual ao GitHub).
- `statistical-analyst` (06/11, a partir da `main`, commit `Skill Statistical Analyst`): a Skill em `.claude/skills/statistical-analyst/`, o inventário e a auditoria em `../03_DECISIONS/` e trechos de
  `INDEX.md`, `DECISIONS.md`, `EVIDENCE.md`, `IN_PROGRESS.md`, `NEXT_STEPS.md` e aqui. Não muda código do programa.
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

## Ambiente
Pastas, instalações, cópias de teste e recursos privados do computador do Pedro: `CLAUDE.local.md` (fora do GitHub).
