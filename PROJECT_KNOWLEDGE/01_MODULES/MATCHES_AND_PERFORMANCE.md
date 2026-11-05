# Minhas partidas: Partidas, Desempenho e Decisões

> Atualizado em 05/11/2026. Código: `tracker/analises.py` (`analise_pessoal`, `decisoes`, `visao`, `perspectiva`),
> `tracker/banco.py`, `tracker/decks.py` (`vincular_automatico`, identificação do deck), `web/js/partidas.js`, `web/js/decisoes.js`.
> Regras: `../02_BUSINESS_RULES/PLAYERS_AND_OWNERSHIP.md` e `../02_BUSINESS_RULES/STATISTICS.md`.

## Filtro Jogador (Início, Partidas, Desempenho e Decisões)
Caixa de opções com você e cada amigo de quem há logs (aparece só quando existe mais de um): qualquer combinação, aplicada na
hora; a caixa continua aberta enquanto se marca e fecha ao clicar fora ou com Esc; "Marcar todos" e "Só eu". Código:
`seletorJogador`/`ligarSeletorJogador` e `S.jogadorSel` em `web/js/partidas.js`; regras em
`../02_BUSINESS_RULES/PLAYERS_AND_OWNERSHIP.md` (inclusive o mesmo jogo pelos dois lados contar uma vez).

## Partidas
- Lista com filtros (período, deck, lista de Meus decks, adversário, tag, **Jogador**), resultado, decks, origem.
- Detalhe da partida: resumo do leitor, problemas ("incompleto?"), linhas não lidas, notas, tags e correção manual do deck
  (`meu_deck`, `deck_adv` substituem o palpite automático). Botão para o replay.
- Colar log à mão (quadro recolhido no Início/Partidas).
- Deck de cada jogador: palpite automático pelas cartas reveladas (NB2 + ícones; ver `STATISTICS.md`); se a partida estiver
  ligada a uma lista de Meus decks (`deck_id`, ligada sozinha por `vincular_automatico` quando as cartas reveladas batem),
  vale o arquétipo da lista. Partidas de amigos não são ligadas às suas listas.
- Exportação CSV para o Excel (`/exportar/minhas_partidas.csv`, ponto e vírgula).

## Desempenho
Taxa de vitória com faixa de confiança de 95% (Wilson), começando × indo em segundo, por adversário, por deck, por lista e por
período. "Você" em cada partida é decidido pelas regras de `PLAYERS_AND_OWNERSHIP.md`.

## Decisões
O que nas suas partidas anda junto com vencer ou perder (correlação, não causa):
aberturas (cartas jogadas nos 2 primeiros turnos) **separadas por quem começou**, corrida de prêmios (primeiro prêmio, viradas,
turno em que perdeu o controle), ritmo (turno do 1º ataque e do 1º prêmio) e cartas jogadas (taxa quando saiu × não saiu).
Filtro Todas / Começando / Indo em segundo. Mínimo de 3 partidas por item.

## Desempenho do programa
`analise_pessoal` guarda em memória a lista de partidas (`banco.marcar_mudanca` avisa quando muda). Decisões lê o detalhe
completo de cada partida: ~2,7 s com mil partidas (limite conhecido; ver `BACKLOG.md`). Medições: experimentos e4 e e8.
