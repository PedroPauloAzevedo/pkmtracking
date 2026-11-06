# Próximos passos

> Atualizado em 06/11/2026. As próximas ações concretas, em ordem. A lista completa de ideias está em `../04_IMPLEMENTATIONS/BACKLOG.md`.
> **Atualize este arquivo no fim de toda sessão.** Sempre pergunte ao Pedro antes de começar algo grande.

0. **2026.11.06-1 publicada em 06/11 (`9c6519b`)**, a partir de um worktree separado. Nesta pasta o ramo `icones-painel` (base
   `76a2005`) ainda tem o mesmo código sem commit, misturado com o trabalho do hardening da Skill: antes do próximo commit daqui,
   trazer a `main` (`9c6519b`) e descartar o que já está nela (o código da 2026.11.06-1 é idêntico).
1. **Skill "Statistical Analyst" (publicada em 06/11, `49664da`):** o Pedro escolhe quais recomendações da auditoria viram trabalho — sugestão de ordem em
   `.claude/skills/statistical-analyst/knowledge/GAPS_AND_ROADMAP.md` (corrigir o e2; identificação só pelo NB2; aviso de "listas do
   topo"; converter o meta para jogo único).
2. **Confirmar o modo automático numa partida real** (versão 2026.11.05-1 ou mais nova) lendo o `dados/programa.log` do Coletor
   do Pedro. Se falhar, o registro diz em qual passo parou (`../01_MODULES/CAPTURE.md`).
3. **Quando sair a próxima coleção:** acrescentar a linha dela em `tracker/colecoes.py` (`COLECOES`, com a data de lançamento nos
   EUA) numa versão nova, se ela ainda não estiver no TCGdex. Já estando na biblioteca, ela entra sozinha. Conferir se o TCG Live
   continuou liberando na véspera, às 10h do Pacífico (D-036).
4. **Perguntar ao Pedro se ele guardou o texto completo do estudo do servidor central** e, se sim, registrar em `BACKLOG.md`.
5. **Trazer para `testes/experimentos/` os scripts de medição do replay, das mãos, dos prêmios e dos descartes** (hoje fora do
   repositório), para que qualquer sessão consiga repetir as medições de `EVIDENCE.md`. É código de teste: pedir autorização antes.

**Acréscimo de 06/11/2026 (rodada de hardening da Skill; sem commit):**
- Commit da rodada quando o Pedro pedir — arquivos listados em `../03_DECISIONS/STATISTICAL_HARDENING_2026-11-06.md`, seção H, num
  ramo a partir da `main`, sem misturar com a 2026.11.06-1.
- Decisões que esperam o Pedro (seção G do relatório): métrica da identificação antes de mudar a regra (G18); faixas do meta com
  efeito de desenho (G16); confiança do deck do adversário como "incerta" (G17); definir `SA_PASTAS_PROTEGIDAS` com a pasta da
  instalação dele (fica em `CLAUDE.local.md`, nunca no GitHub).
- Para usar a ponte numa cópia nova: `python -I .claude/skills/statistical-analyst/tools/marcar_copia.py <cópia>` antes.
- **Decidido pelo Pedro em 06/11 (D-040, D-041, D-042), a implementar numa versão nova do Coletor:** identificação só pelo NB2
  quando houver modelo; faixas de Meta/Matchups com a dependência entre partidas; deck do adversário "incerto" com confiança baixa.
  Mexe em `tracker/decks.py` — o mesmo arquivo da 2026.11.06-1 ainda sem commit —, então vem **depois** de a 2026.11.06-1 ir para a
  `main`, num ramo próprio, com medição antes/depois (D-017) e os 4 testes. Proteção da instalação real na ponte: feita.
- **Atualização (06/11, depois da publicação da 2026.11.06-1):** D-040, D-041 e D-042 implementadas como **2026.11.06-2** no ramo
  `nb2-faixas-incerto` (worktree fora desta pasta; caminho em `CLAUDE.local.md`), a partir da `main` 9c6519b, **sem commit**.
  4 testes OK; medições a8 (depois), a10 e a11 na Skill. Falta: o Pedro pedir commit e publicação. A Skill (rodada de hardening) segue
  sem commit nesta pasta; os dois vão em commits separados.
- **Publicada em 06/11 a pedido do Pedro: 2026.11.06-2 (`101da5f`, `main` e GitHub).** Esta pasta (ramo `icones-painel`, base
  `76a2005`) ainda não tem as -1 e -2: antes de commitar a rodada de hardening da Skill, criar um ramo a partir da `main` nova e levar
  só os arquivos da Skill e os acréscimos de documentação (conferir `DECISIONS.md`, `CURRENT_STATE.md` e `NEXT_STEPS.md`, que a `main`
  também mudou).
- **Skill — estratégia (06/11, sem commit):** próximos passos sugeridos em `GAPS_AND_ROADMAP.md`: P3 (prêmios checados) e P1 (rotas
  possíveis × executada) primeiro, porque já têm dado; G20 (atribuição de prêmios por nocaute no resumo) é mudança no Coletor e precisa
  do Pedro; P2/P4–P7 ficam exploratórios até haver centenas de partidas.
- **Skill — ferramentas estratégicas prontas (06/11, sem commit, NÃO aplicadas por decisão do Pedro):** `tools/estrategia.py` e
  `experiments/p_estrategia.py` (P1–P7, com trava: P1 50, P3 100, demais 300 partidas). Rodar quando houver amostra suficiente.
