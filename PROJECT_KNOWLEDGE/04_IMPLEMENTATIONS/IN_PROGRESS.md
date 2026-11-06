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
- **Visto em 06/11 00:04 (ainda na 2026.11.05-3):** o modo automático achou a tela de resultado e tentou duas vezes, mas com
  `jogo na frente=False` (o Pedro estava no painel, na tela de Meta) e não achou o botão de exportar: avisou para exportar à mão.
  O reconhecimento funcionou; falhou trazer o jogo para a frente.
- **Se falhar:** seguir "Como investigar" em `../01_MODULES/CAPTURE.md` (imagens só da janela do jogo, D-016).

## Skill "Statistical Analyst": rodada de hardening (06/11/2026, sem commit)
- Feito e testado, **aguardando o Pedro pedir o commit**: ponte só leitura com trava na execução, registro completo dos experimentos,
  a7–a9, 8 cenários de avaliação (A–H) e consolidação dos documentos. Relatório: `../03_DECISIONS/STATISTICAL_HARDENING_2026-11-06.md`.
- Arquivos só em `.claude/skills/statistical-analyst/` e em `PROJECT_KNOWLEDGE/` (acréscimos). Nenhum código do Coletor mudou.
- Ao commitar: num ramo a partir da `main` (a Skill já está lá), separado da 2026.11.06-1.

## Skill "Statistical Analyst": modelagem estratégica (06/11/2026, sem commit)
- Feito: `knowledge/STRATEGIC_CONCEPTS.md` (conceitos, níveis de afirmação, matriz de observabilidade), `PRIZE_ANALYSIS.md`,
  `CONTROL_AND_DISRUPTION.md`, `DECISION_ANALYSIS.md`; `experiments/p0_viabilidade_estrategica.py` (+ resultado); pesquisa registrada em
  `RESEARCH_REGISTER.md`; `SKILL.md`, `POKEMON_TCG_MODEL.md`, `GAPS_AND_ROADMAP.md` (G20–G24) e `KNOWN_METHODS.md` atualizados.
- Não feito (propostos): experimentos P1–P7. Nada no Coletor mudou. Vai junto com a rodada de hardening quando o Pedro pedir o commit.

## Preparar o projeto para dois desenvolvedores — ramo `docs/preparar-dois-devs`, Pedro (06/11/2026)
- **Situação:** documentação, `.gitattributes`, `.gitignore` e `.github/` prontos, em Pull Request. Nenhum código do programa mudou.
- **Juntado na `main` em 06/11 (PR #2, `66440fe`).** **Falta:** configurar o GitHub (`../00_CENTRAL/COLLABORATION.md`, seção 9).
