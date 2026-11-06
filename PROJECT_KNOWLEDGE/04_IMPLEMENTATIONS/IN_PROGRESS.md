# Em andamento

> Atualizado em 06/11/2026. Itens começados que faltam terminar ou confirmar. Ao concluir, registre em `DONE.md` e tire daqui.

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

## Preparar o projeto para dois desenvolvedores — ramo `docs/preparar-dois-devs`, Pedro (06/11/2026)
- **Situação:** documentação, `.gitattributes`, `.gitignore` e `.github/` prontos, em Pull Request. Nenhum código do programa mudou.
- **Falta:** o Pedro revisar e juntar o PR; configurar o GitHub (`../00_CENTRAL/COLLABORATION.md`, seção 9).
