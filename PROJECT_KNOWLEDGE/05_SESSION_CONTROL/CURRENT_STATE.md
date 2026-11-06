# Estado atual do projeto

> Atualizado em 05/11/2026, no fim da sessão das épocas de coleção, do "Ver todas" e do descarte no replay (2026.11.05-5, não
> publicada). **Atualize este arquivo no fim de toda sessão** (o que mudou, o que ficou pendente, o que não foi verificado).

## Versão
- **Publicada na `main` do GitHub: 2026.11.05-3** (commits `c100596` documentação, `c53abc5` versões -2/-3, `7a9850f` registro):
  prêmios no replay (D-032) e filtro Jogador com qualquer combinação (D-033). Histórico técnico em `../04_IMPLEMENTATIONS/DONE.md`.
- **Prontas, sem commit e não publicadas:**
  - **2026.11.05-4** — na Biblioteca de cartas, uma carta que o TCGdex não entrega deixa só aquela coleção como estava, em vez de
    parar a atualização inteira (D-034). O Pedro pediu para **não publicar ainda**.
  - **2026.11.05-5** — campo **Época** nas análises (uma época por coleção; no TCG Live com hora, nos torneios pela validade; D-036),
    "Ver todas" que não fazia nada e lista de partidas lenta (D-037), replay que deixava a Energia do recuo no Pokémon errado (D-035).
  - **2026.11.05-6** — filtros "Deck do jogador" e "Deck do adversário" em Partidas; ícones dos decks de volta (o Labs mudou a
    página de decks e o programa tinha apagado 122 de 134 ícones; D-038).
  O `versao.txt` já está em 2026.11.05-6. Aguardam o Pedro pedir a publicação (em 05/11 ele disse "ainda não").
- O Coletor do Pedro estava na 2026.11.05-3 às 19:55 de 05/11.
- O repositório `PedroPauloAzevedo/pkmtracking` é **público** e não tem Releases.
- Os programas dos amigos e o do Pedro se atualizam pelo aviso "Nova versão disponível".

## Ramos
- `main` = 2026.11.05-3 (igual ao GitHub).
- `versoes-2026.11.05-4-e-5` (ramo atual, criado a partir da `main`; antes se chamava `biblioteca-falha-carta`): **sem commit**.
  Tem as duas versões juntas no diretório de trabalho:
  1. 2026.11.05-4: `tracker/cartas.py`, `web/js/biblioteca.js`, seção 5 de `testes/teste_tracker.py`, `CARD_LIBRARY.md`;
  2. 2026.11.05-5: `tracker/colecoes.py` (novo), `tracker/replay.py`, `tracker/analises.py`, `tracker/banco.py`, `tracker/decks.py`,
     `app.py`, `web/js/*.js` (quase todos, pela conferência de tela velha), `web/estilo.css`, `web/LEIA-ME.md`, `README.md`,
     `CLAUDE.md`, seções 6 e 7 de `teste_tracker.py`, `teste_replay.py`, `teste_telas.py` e os documentos;
  3. 2026.11.05-6: `tracker/decks.py`, `app.py` (refazer a lista de decks), `web/js/partidas.js`, seção 8 de `teste_tracker.py`,
     `teste_telas.py`, `TOURNAMENTS.md`, `MATCHES_AND_PERFORMANCE.md`;
  4. `versao.txt`, `novidades.json`, `DONE.md`, `IN_PROGRESS.md`, `NEXT_STEPS.md` e este arquivo têm todas. Este arquivo tinha ido
     vazio por engano no commit `7a9850f` e foi recuperado de `c53abc5`.
- `replay-premios`, `docs-project-knowledge`, `corrige-modo-automatico` e `replay-maos`: ramos antigos, já publicados.

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
- O instalador .exe que existe (fora do GitHub, no computador do Pedro) é da versão **2026.11.02-2**; quem instala por ele se
  atualiza sozinho depois. Não há Release no GitHub.
- O estudo de um **servidor central para análises coletivas** foi feito numa sessão que foi apagada; só sobrou um resumo
  (ver `BACKLOG.md`).
- Os scripts de medição do replay, das mãos, dos prêmios e dos descartes ainda estão **fora do repositório** (só no computador do
  Pedro; ver `EVIDENCE.md`).
- Antes de cada commit de documentação, conferir `git diff --stat`: o `7a9850f` apagou este arquivo sem ninguém perceber.
- Coleção nova que ainda não está no TCGdex precisa entrar à mão em `tracker/colecoes.py` (`NEXT_STEPS.md`, item 3).

## Ambiente
Pastas, instalações, cópias de teste e recursos privados do computador do Pedro: `CLAUDE.local.md` (fora do GitHub).
