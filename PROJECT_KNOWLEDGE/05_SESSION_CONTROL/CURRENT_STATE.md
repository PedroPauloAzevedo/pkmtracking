# Estado atual do projeto

> Atualizado em 05/11/2026, no fim da sessão que pôs os prêmios no replay (2026.11.05-2) e o filtro Jogador com qualquer
> combinação (2026.11.05-3); nenhuma das duas publicada.
> **Atualize este arquivo no fim de toda sessão** (o que mudou, o que ficou pendente, o que não foi verificado).

## Versão
- **Publicada na `main` do GitHub: 2026.11.05-1** (commit `c0b0943`, 05/11/2026): o modo automático reaprende o tamanho dos
  botões quando a janela do jogo muda de tamanho. Histórico técnico em `../04_IMPLEMENTATIONS/DONE.md`.
- **Prontas, sem commit e não publicadas:**
  - **2026.11.05-2** — o replay mostra com a face os prêmios que quem exportou o log pegou, desde o começo da partida (D-032);
  - **2026.11.05-3** — o filtro Jogador virou caixa de opções (qualquer combinação de você e amigos) e o mesmo jogo pelos dois
    lados só junta logs de donos diferentes (D-033).
  Aguardam o Pedro pedir a publicação (o `versao.txt` já está em 2026.11.05-3).
- O repositório `PedroPauloAzevedo/pkmtracking` é **público** e não tem Releases.
- Os programas dos amigos e o do Pedro se atualizam pelo aviso "Nova versão disponível".

## Ramos
- `main` = 2026.11.05-1 (igual ao GitHub).
- `replay-premios` (ramo atual, criado a partir da `main`): **sem commit**. Tem duas coisas juntas no diretório de trabalho:
  1. a reorganização da documentação (pasta `PROJECT_KNOWLEDGE/`, novo `CLAUDE.md`, correções no `README.md`, relatório da missão
     movido para `03_DECISIONS/` — já preparado com `git mv`);
  2. a versão 2026.11.05-2 (`tracker/replay.py`, `web/js/replay.js`, `web/estilo.css`, `testes/teste_replay.py`, `versao.txt`,
     `novidades.json`, README seção 6) e a troca de dois nicks reais por nomes fictícios em comentários (`replay.py`, `revisao.py`);
  3. a versão 2026.11.05-3 (`web/js/partidas.js`, `decisoes.js`, `amigos.js`, `web/estilo.css`, `tracker/analises.py`, `app.py`,
     `testes/teste_tracker.py`, `testes/teste_telas.py`, README seção 3, `versao.txt`, `novidades.json`).
  Os documentos novos já descrevem as duas versões: publicar tudo junto (`NEXT_STEPS.md`, item 1).
- `docs-project-knowledge`: ficou no mesmo commit da `main` (o trabalho da documentação seguiu para `replay-premios`).
  `corrige-modo-automatico` e `replay-maos`: ramos antigos, já publicados.

## O que está funcionando (verificado)
- Captura pela área de transferência: funcionando no computador do Pedro (várias partidas gravadas em 05/11).
- Os 4 testes (`teste_tracker`, `teste_seguranca`, `teste_replay`, `teste_telas`) terminaram com OK na 2026.11.05-3 (numa cópia de teste).
- Filtro Jogador com vários jogadores conferido na tela, numa cópia com os dados do Pedro (porta 8799): você + amigo = 60 partidas.
- Replay: nas partidas reais, 0 momentos com Pokémon em jogo com dano ≥ PS; mãos conferidas 109/109; prêmios de quem exportou
  253/253 com a face desde o começo, e mesa e mãos iguais às da versão publicada (ver `EVIDENCE.md`).
- Tela do replay com os prêmios conferida no navegador, numa cópia com os dados do Pedro (porta 8799).

## O que falta confirmar
- **Modo automático com o jogo real depois da 2026.11.05-1.** Ele parou em 03/11 (tamanho dos botões preso); a correção foi
  testada só em simulação. Confirmar numa partida real: o `dados/programa.log` mostra `[auto] tentativa ...` e, se o jogo
  mudou de tamanho, `[auto] tela/janela do jogo mudou ...`. Ver `../04_IMPLEMENTATIONS/IN_PROGRESS.md`.
- Às 09:22 de 05/11 o Coletor do Pedro ainda estava na 2026.11.03-1; não foi visto se ele atualizou para a 2026.11.05-1.

## Alertas
- O instalador .exe que existe (fora do GitHub, no computador do Pedro) é da versão **2026.11.02-2**; quem instala por ele se
  atualiza sozinho depois. Não há Release no GitHub.
- O estudo de um **servidor central para análises coletivas** foi feito numa sessão que foi apagada; só sobrou um resumo
  (ver `BACKLOG.md`).
- Os scripts de medição do replay, das mãos e dos prêmios ainda estão **fora do repositório** (só no computador do Pedro; ver
  `EVIDENCE.md`).

## Ambiente
Pastas, instalações, cópias de teste e recursos privados do computador do Pedro: `CLAUDE.local.md` (fora do GitHub).
