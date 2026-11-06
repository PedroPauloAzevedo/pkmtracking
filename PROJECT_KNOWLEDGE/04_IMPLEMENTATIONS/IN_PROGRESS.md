# Em andamento

> Atualizado em 06/11/2026. Itens começados que faltam terminar ou confirmar. Ao concluir, registre em `DONE.md` e tire daqui.

## Confirmar o modo automático com o jogo real (versão 2026.11.05-1 ou mais nova)
- **Situação:** publicado em 05/11/2026; testado em simulação (`../03_DECISIONS/EVIDENCE.md`). O modo tinha parado de reconhecer a tela
  de resultado em 03/11 porque o tamanho dos botões ficou preso ao da primeira partida.
- **Visto em 06/11 00:04 (na 2026.11.05-3):** o modo automático achou a tela de resultado e tentou duas vezes, mas com
  `jogo na frente=False` (o Pedro estava no painel) e não achou o botão de exportar: avisou para exportar à mão. O reconhecimento
  funcionou; falhou trazer o jogo para a frente.
- **Visto em 05/11 no registro:** a linha `[auto] tela/janela do jogo mudou` alterna entre `[1080, 1920]` e `[1080, 1920, 1080, 1920]`
  quando a janela do jogo some e volta (minimizada ou fechada): o modo automático esquece o tamanho dos botões e procura de novo.
  É o esperado; só vira problema se ele demorar a achar os botões depois.
- **Falta:** uma partida com o jogo na frente na tela de resultado por alguns segundos.
- **Como conferir:** `dados/programa.log` do Coletor do Pedro deve ter `[auto] tentativa 1: jogo na frente=True, botão de exportar
  achado=True ..., log chegou=True` e a partida deve aparecer com origem `automatico`.
- **Se falhar:** seguir "Como investigar" em `../01_MODULES/CAPTURE.md` (imagens só da janela do jogo, D-016).

## Configuração do GitHub para dois desenvolvedores
- **Situação:** documentação, `.gitattributes`, `.gitignore` e `.github/` na `main` (PR #2, 06/11/2026).
- **Falta (só o Pedro):** os passos de `../00_CENTRAL/COLLABORATION.md`, seção 9.

## Erros de replay (ramo `fix/erros-replay`)
- **Situação:** primeiro caso (Risky Ruins, D-045) publicado como 2026.11.06-3. O ramo continua aberto para os próximos erros que o
  Pedro mandar.
