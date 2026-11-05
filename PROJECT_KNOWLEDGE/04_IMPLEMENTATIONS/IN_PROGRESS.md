# Em andamento

> Atualizado em 05/11/2026. Itens começados que faltam terminar ou confirmar. Ao concluir, registre em `DONE.md` e tire daqui.

## Confirmar o modo automático com o jogo real (versão 2026.11.05-1)
- **Situação:** publicado em 05/11/2026; testado em simulação (`../03_DECISIONS/EVIDENCE.md`). O modo tinha parado de reconhecer a tela
  de resultado em 03/11 porque o tamanho dos botões ficou preso ao da primeira partida.
- **Falta:** o Pedro jogar uma partida com o Coletor atualizado e deixar o jogo na frente na tela de resultado por alguns segundos.
- **Como conferir:** `dados/programa.log` do Coletor dele deve ter `[auto] tentativa 1: jogo na frente=True, botão de exportar
  achado=True ..., log chegou=True` e a partida deve aparecer com origem `automatico`. Se o jogo mudou de tamanho, aparece também
  `[auto] tela/janela do jogo mudou ...`.
- **Se falhar:** seguir "Como investigar" em `../01_MODULES/CAPTURE.md` (imagens só da janela do jogo, D-016).

## Reorganização da documentação + versões 2026.11.05-2 e -3 (05/11/2026)
- **Situação:** prontas no ramo `replay-premios`, sem commit. Documentação: pasta `PROJECT_KNOWLEDGE/`, novo `CLAUDE.md`,
  `CLAUDE.local.md` local, documentos antigos em `_arquivo_docs_antigos/`. Versão 2026.11.05-2: prêmios no replay. Versão
  2026.11.05-3: filtro Jogador com qualquer combinação. Detalhes em `DONE.md`; os 4 testes OK; medições em `EVIDENCE.md`.
- **Falta:** o Pedro pedir a publicação. Passos em `../05_SESSION_CONTROL/NEXT_STEPS.md`, item 1.
