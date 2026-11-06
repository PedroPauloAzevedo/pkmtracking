# Em andamento

> Atualizado em 05/11/2026. Itens começados que faltam terminar ou confirmar. Ao concluir, registre em `DONE.md` e tire daqui.

## Confirmar o modo automático com o jogo real (versão 2026.11.05-1)
- **Situação:** publicado em 05/11/2026; testado em simulação (`../03_DECISIONS/EVIDENCE.md`). O modo tinha parado de reconhecer a tela
  de resultado em 03/11 porque o tamanho dos botões ficou preso ao da primeira partida. Em 05/11 o Coletor do Pedro só passou para a
  2026.11.05-3 às 19:55; as 7 partidas dele daquele dia foram antes, ainda na 2026.11.03-1 (pela área de transferência). Ainda não há
  partida com a versão corrigida.
- **Falta:** o Pedro jogar uma partida com o Coletor atualizado e deixar o jogo na frente na tela de resultado por alguns segundos.
- **Como conferir:** `dados/programa.log` do Coletor dele deve ter `[auto] tentativa 1: jogo na frente=True, botão de exportar
  achado=True ..., log chegou=True` e a partida deve aparecer com origem `automatico`. Se o jogo mudou de tamanho, aparece também
  `[auto] tela/janela do jogo mudou ...`.
- **Visto em 05/11 no registro:** essa linha alterna entre `[1080, 1920]` e `[1080, 1920, 1080, 1920]` quando a janela do jogo some e
  volta (jogo minimizado ou fechado): o modo automático esquece o tamanho dos botões e procura de novo. É o esperado; só vira problema
  se ele demorar a achar os botões depois.
- **Se falhar:** seguir "Como investigar" em `../01_MODULES/CAPTURE.md` (imagens só da janela do jogo, D-016).

## Publicar a 2026.11.05-4, a -5 e a -6
- **Situação:** prontas e testadas (4 testes OK) no ramo `versoes-2026.11.05-4-e-5`, sem commit.
  - 2026.11.05-6: filtros Deck do jogador / Deck do adversário em Partidas e ícones dos decks de volta (D-038). Pedidas em 05/11.
  - 2026.11.05-4: Biblioteca de cartas não para por uma carta (D-034). O Pedro pediu em 05/11 para não publicar ainda.
  - 2026.11.05-5: épocas de coleção nas análises (D-036), "Ver todas" consertado e lista de partidas mais rápida (D-037), replay com
    o descarte certo (D-035). Pedidas pelo Pedro em 05/11; ele ainda não pediu a publicação.
- **Falta:** o Pedro pedir a publicação (passos em `../05_SESSION_CONTROL/NEXT_STEPS.md`, item 1).
