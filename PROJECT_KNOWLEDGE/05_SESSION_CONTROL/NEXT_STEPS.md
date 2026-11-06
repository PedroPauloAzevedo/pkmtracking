# Próximos passos

> Atualizado em 05/11/2026. As próximas ações concretas, em ordem. A lista completa de ideias está em `../04_IMPLEMENTATIONS/BACKLOG.md`.
> **Atualize este arquivo no fim de toda sessão.** Sempre pergunte ao Pedro antes de começar algo grande.

1. **Publicar a 2026.11.05-4, a -5 e a -6 quando o Pedro pedir** (ramo `versoes-2026.11.05-4-e-5`): conferir `git diff --stat`
   (em 05/11 um commit de documentação esvaziou o `CURRENT_STATE.md` sem ninguém ver) e que nenhum dado pessoal entrou
   (`WORKFLOW.md`, seção 7); um commit por versão quando der para separar os arquivos (`git commit -- <arquivos>`; `versao.txt`,
   `novidades.json`, `CURRENT_STATE.md`, `DONE.md` e `IN_PROGRESS.md` têm todas e podem ir no commit da última); `merge --ff-only` na
   `main` e push; passo a passo para os amigos no chat (D-024) e os hashes em `DONE.md` e em `CURRENT_STATE.md`.
2. **Confirmar o modo automático numa partida real** (versão 2026.11.05-1 ou mais nova) lendo o `dados/programa.log` do Coletor
   do Pedro. Se falhar, o registro diz em qual passo parou (`../01_MODULES/CAPTURE.md`).
3. **Quando sair a próxima coleção:** acrescentar a linha dela em `tracker/colecoes.py` (`COLECOES`, com a data de lançamento nos
   EUA) numa versão nova, se ela ainda não estiver no TCGdex. Já estando na biblioteca, ela entra sozinha. Conferir se o TCG Live
   continuou liberando na véspera, às 10h do Pacífico (D-036).
4. **Perguntar ao Pedro se ele guardou o texto completo do estudo do servidor central** e, se sim, registrar em `BACKLOG.md`.
5. **Trazer para `testes/experimentos/` os scripts de medição do replay, das mãos, dos prêmios e dos descartes** (hoje fora do
   repositório), para que qualquer sessão consiga repetir as medições de `EVIDENCE.md`. É código de teste: pedir autorização antes.
