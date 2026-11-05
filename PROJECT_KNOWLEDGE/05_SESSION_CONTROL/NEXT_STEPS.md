# Próximos passos

> Atualizado em 05/11/2026. As próximas ações concretas, em ordem. A lista completa de ideias está em `../04_IMPLEMENTATIONS/BACKLOG.md`.
> **Atualize este arquivo no fim de toda sessão.** Sempre pergunte ao Pedro antes de começar algo grande.

1. **Publicar juntas a reorganização da documentação e as versões 2026.11.05-2 e -3**, quando o Pedro pedir (ramo
   `replay-premios`): conferir que nenhum dado pessoal entrou (`WORKFLOW.md`, seção 7); um commit para a documentação e um para
   cada versão, se der para separar os arquivos (`git commit -- <arquivos>`; o `git mv` do relatório já está preparado no índice;
   `estilo.css`, `README.md`, `versao.txt` e `novidades.json` têm mudanças das duas versões e podem ir no commit da -3);
   `merge --ff-only` na `main` e push; depois, o passo a passo para os amigos no chat (D-024) e os hashes em `DONE.md` e aqui.
2. **Confirmar o modo automático numa partida real** (versão 2026.11.05-1 ou mais nova) lendo o `dados/programa.log` do Coletor
   do Pedro. Se falhar, o registro diz em qual passo parou (`../01_MODULES/CAPTURE.md`).
3. **Perguntar ao Pedro se ele guardou o texto completo do estudo do servidor central** e, se sim, registrar em `BACKLOG.md`.
4. **Trazer para `testes/experimentos/` os scripts de medição do replay, das mãos e dos prêmios** (hoje fora do repositório), para
   que qualquer sessão consiga repetir as medições de `EVIDENCE.md`. É código de teste: pedir autorização antes.
