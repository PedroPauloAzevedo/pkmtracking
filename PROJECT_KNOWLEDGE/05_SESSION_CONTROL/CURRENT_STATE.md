# Estado atual do projeto

> Atualizado em 13/11/2026 (versão e CI conferidas no GitHub; modo automático confirmado no jogo real). Antes: 11/11/2026 (2026.11.11-3 publicada no PR #26; 2026.11.11-4: vermelho do mapa, "Meganium Hydrapple" e
> Lopunny Froslass, D-055). **Atualize este arquivo no
> fim de toda sessão** (o que mudou, o que ficou pendente, o que não foi verificado).

## Versão
- **13/11/2026 (conferido no GitHub): a `main` está na 2026.11.13-1** (Meus decks junta as reimpressões da mesma carta; PR #30).
  Antes dela entraram a 2026.11.11-2 (PR #25), -3 (PR #26) e -4 (PR #27). Os itens abaixo de 11/11 e 10/11 ficam como histórico:
  "pronta no ramo" e "No GitHub: 2026.11.09-4" já não valem.
- **CI (PRs #28 e #29, juntados em 12/11):** `.github/workflows/testes-python.yml` roda `teste_replay.py` e `teste_tracker.py`
  (jobs "Replay" e "Coletor") em todo PR para a `main`. Última execução: PR #30, as duas OK. `teste_seguranca.py` e
  `teste_telas.py` continuam só locais.
- **Mapa da documentação por assunto:** `docs/README.md` (só aponta para estes documentos).
- **11/11/2026:** a **2026.11.11-2** (D-053: aproveitamento no suíço, lista base pesada pelos pontos, mudanças nas listas,
  estabilidade e tela Metodologia) está pronta no ramo `feature/metodos-indigo`. Na `main`: a **2026.11.11-1** (visual novo em Meta e Matchups, inspirado no painel Indigo
  Plateau: gráfico "Quem vale a pena jogar", cartões por deck com a cor do tipo, mapa de calor, pílulas, mais espaço) (PR #24).
- **No GitHub (`main`): 2026.11.09-4** (09/11/2026), publicada junto com as anteriores que esperavam: 2026.11.07-1 (Decisões mostra
  "sem ela: V–D"), 2026.11.09-1 (época dos torneios online começa no lançamento da coleção; D-048), 2026.11.09-2 (Cartas x matchups
  com colunas iguais), 2026.11.09-3 (tema claro/escuro/automático) e 2026.11.09-4 (Início novo: Hoje, tema, Dados coletados;
  `/api/resumo-geral`; `index.html` sem cache). Antes: 2026.11.06-6 (telas na largura da janela) e 2026.11.06-4/-5 (Log original,
  replay). Histórico técnico em `../04_IMPLEMENTATIONS/DONE.md`.
- Também na `main`: Skill "Statistical Analyst" (PR #1) e a preparação para dois desenvolvedores (PR #2; D-043, D-044, D-047).
- O repositório `PedroPauloAzevedo/pkmtracking` é **público** e não tem Releases. Os programas se atualizam pelo aviso
  "Nova versão disponível".
- **Achado de 09/11:** o Coletor do Pedro importa torneios online só com 256 jogadores ou mais; desde a Delta Reign só um passou.
  Sem listas dos decks novos, o NB2 chamou um Talonflame Dusknoir de "Tera Box" (partida de 09/11 às 20:12). Recomendado ao Pedro:
  Torneios > "com pelo menos 64 jogadores" > Verificar agora.

- **Publicadas em 10/11/2026 (PRs #15–#20): 2026.11.10-1 a -5**, da pesquisa de outros apps (`../03_DECISIONS/REFERENCE_TOOLS.md`):
  códigos das cartas no log (D-049), nome provisório para deck sem listas (D-050), coleção nova pelo malie.io (D-051), modo
  automático leve e replay com melhores momentos. A versão no GitHub é a 2026.11.10-5.
- Rotina mensal de verificação dos outros apps: tarefa agendada no computador do Pedro (dia 10, 19h; detalhes em `CLAUDE.local.md`).

## Ramos e pastas
- `main` = o que está no GitHub. Tudo entra por Pull Request e só o Pedro junta (D-043); no computador dele, o "publicar" autoriza o
  Claude a abrir e juntar o PR (D-047).
- `fix/erros-replay`: ramo dos erros de replay (worktree próprio; caminho em `CLAUDE.local.md`). Continua aberto para os próximos.
- `docs/etapas-de-ataque` (06/11, sem commit): pesquisa no Judge Ball (roteiro do ataque dos juízes) conferida nos logs (experimento a12
  da Skill): registros em `BATTLE_LOG_FORMAT.md`, `EVIDENCE.md` e na Skill (`POKEMON_TCG_MODEL.md` seção 8, `RESEARCH_REGISTER.md`, G24). Só documentação.
- Ramos já juntados ou publicados (podem ser apagados): `icones-painel`, `nb2-faixas-incerto`, `publica-2026.11.06-1`,
  `versoes-2026.11.05-4-e-5`, `statistical-analyst`, `replay-premios`, `docs-project-knowledge`, `corrige-modo-automatico`, `replay-maos`.
- Outros ramos no GitHub que não são deste projeto de trabalho (ex.: diagnósticos de outro trabalho do Pedro): não mexer.

## O que está funcionando (verificado)
- Captura pela área de transferência no computador do Pedro.
- **Modo automático no jogo real (13/11/2026, versão 2026.11.11-4):** exportou sozinho na primeira tentativa; partida #207
  gravada com origem `automatico` (`../03_DECISIONS/EVIDENCE.md`).
- Os 4 testes de entrega OK na 2026.11.06-3 (numa cópia de teste).
- Replay: Risky Ruins com o dono certo (55 de 145 linhas tinham o dono trocado no log; estados impossíveis 1742 → 1660); descartes de
  carta presa 182/182; prêmios 253/253; mãos 109/109 (`../03_DECISIONS/EVIDENCE.md`).
- Épocas de coleção, "Ver todas", lista de partidas rápida (~0,1 s depois do primeiro cálculo) e ícones dos decks conferidos na tela
  numa cópia com os dados do Pedro em 05–06/11.
- Skill: ponte só leitura com trava na execução (`test_ponte.py`, `test_sa_tools.py`, `test_referencias.py` OK).

## O que falta confirmar
- A hora em que o TCG Live libera uma coleção (10h do Pacífico, na véspera do lançamento) veio de anúncios de coleções anteriores;
  a validade em torneio da 30th Celebration (25/09/2026) foi calculada pela regra, sem anúncio oficial (D-036).
- A 2026.11.05-4 não foi testada contra uma falha real do TCGdex (só com o TCGdex falso do teste).
- Delta Reign: em 05/11 ainda não estava no TCGdex nem no Limitless; quando entrar, a biblioteca baixa sozinha.
- Nada do Mac foi testado num Mac de verdade (D-044; BACKLOG M1–M7).

## Alertas
- Auditoria estatística (`../03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md`, `STATISTICAL_HARDENING_2026-11-06.md`): análises que usam
  só as listas do topo dos torneios têm viés de seleção; "seu resultado × meta" mistura jogo único com melhor de 3. As recomendações
  ainda não aplicadas esperam o Pedro (`NEXT_STEPS.md`).
- O instalador .exe (fora do GitHub, no computador do Pedro) é da versão 2026.11.02-2; quem instala por ele se atualiza depois.
- O estudo do servidor central para análises coletivas só existe como resumo (`BACKLOG.md`).
- Os scripts de medição do replay, das mãos, dos prêmios, dos descartes e do Risky Ruins estão fora do repositório (`EVIDENCE.md`).
- Antes de cada commit de documentação, conferir `git diff --stat` (um commit de 05/11 esvaziou este arquivo sem ninguém ver).
- Coleção nova que ainda não está no TCGdex precisa entrar à mão em `tracker/colecoes.py` (`NEXT_STEPS.md`).

## Ambiente
Pastas, instalações, cópias de teste e recursos privados de cada computador: `CLAUDE.local.md` (fora do GitHub; modelo em
`CLAUDE.local.example.md`). Trabalho a dois: `../00_CENTRAL/COLLABORATION.md`.
