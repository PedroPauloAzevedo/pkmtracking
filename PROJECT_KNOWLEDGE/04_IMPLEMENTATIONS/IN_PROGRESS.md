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

## Skill "Statistical Analyst" (pedida pelo Pedro em 06/11/2026)
- **Situação:** as 6 fases feitas em 06/11; **commit no ramo `statistical-analyst`, não publicado** (arquivos: `.claude/skills/statistical-analyst/`,
  `../03_DECISIONS/STATISTICAL_INVENTORY_2026-11-06.md`, `../03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md` e trechos de `INDEX.md`,
  `DECISIONS.md` (D-039), `EVIDENCE.md`, `CURRENT_STATE.md`, `NEXT_STEPS.md` e aqui). Nenhum método do programa foi alterado.
  Testes da Skill: `tests/test_sa_tools.py` e `tests/test_referencias.py` OK; 4 cenários em `evals/` rodados com e sem a Skill:
  16/16 critérios com a Skill, 12/16 sem (`.claude/skills/statistical-analyst/tests/RELATORIO_TESTES_2026-11-06.md`).
- **Falta:** publicar quando o Pedro pedir (`merge --ff-only` na `main` + push; se a 2026.11.06-1 for publicada antes, refazer o
  ramo sobre a `main` nova, porque os dois saíram do `76a2005`) e o Pedro decidir as recomendações da auditoria (`.claude/skills/statistical-analyst/knowledge/GAPS_AND_ROADMAP.md`).
- **Regra:** qualquer troca de método, número ou tela passa pelo Pedro (D-017).
