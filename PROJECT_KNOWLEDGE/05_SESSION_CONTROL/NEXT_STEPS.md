# Próximos passos

> Atualizado em 13/11/2026. As próximas ações concretas, em ordem. A lista completa de ideias está em `../04_IMPLEMENTATIONS/BACKLOG.md`.
> **Atualize este arquivo no fim de toda sessão.** Sempre pergunte ao Pedro antes de começar algo grande.

1. **Pedro, no GitHub:** proteger a `main`, convidar o segundo desenvolvedor (Write), 2FA, apagar ramos ao juntar, esconder o
   e-mail — lista em `../00_CENTRAL/COLLABORATION.md`, seção 9. Depois, o segundo dev faz o primeiro dia (`COLLABORATION.md`,
   seção 2) e o item **M1** do BACKLOG (conferir o básico no Mac), que diz quais dos itens M2–M7 são reais.
2. **Erros de replay:** o ramo `fix/erros-replay` continua aberto; cada erro que o Pedro mandar vira um caso em `testes/teste_replay.py`
   e uma medição antes × depois em todas as partidas (D-017).
3. **Skill "Statistical Analyst":** o Pedro escolhe quais recomendações ainda não aplicadas viram trabalho — ordem sugerida em
   `.claude/skills/statistical-analyst/knowledge/GAPS_AND_ROADMAP.md` (aviso de "listas do topo"; converter o meta para jogo único;
   G20, atribuição de prêmios por nocaute no resumo, que muda o Coletor). Os experimentos estratégicos P1–P7
   (`tools/estrategia.py`, `experiments/p_estrategia.py`) ficam desligados até haver amostra (P1 50, P3 100, demais 300 partidas).
   Para usar a ponte numa cópia nova: `python -I .claude/skills/statistical-analyst/tools/marcar_copia.py <cópia>` antes.
   Novo em 06/11: G24 (ler o `Damage breakdown` dos logs) e a causa de parte do G20 (um "took N" para vários nocautes), do
   experimento a12 (ramo `docs/etapas-de-ataque`, sem commit).
4. **Quando sair a próxima coleção:** acrescentar a linha dela em `tracker/colecoes.py` (`COLECOES`, com a data de lançamento nos
   EUA) numa versão nova, se ela ainda não estiver no TCGdex. Conferir se o TCG Live continuou liberando na véspera, às 10h do
   Pacífico (D-036). Nos torneios online a época começa no lançamento (D-048): conferir no Limitless se os torneios do dia do
   lançamento já usam a coleção.
5. **Sugestões da comparação com o Pokemon Champions Battle Logger (09/11/2026)** esperam a escolha do Pedro: ficha do adversário
   (sugestão 1) e sequências/horário (6) já têm maquete (mostrada ao Pedro em 09/11); lista em `../04_IMPLEMENTATIONS/BACKLOG.md`.
6. **Perguntar ao Pedro se ele guardou o texto completo do estudo do servidor central** e, se sim, registrar em `BACKLOG.md`.
7. **Trazer para `testes/experimentos/` os scripts de medição do replay, das mãos, dos prêmios, dos descartes e do Risky Ruins**
   (hoje fora do repositório), para que qualquer sessão consiga repetir as medições de `EVIDENCE.md`. É código de teste: pedir
   autorização antes.
