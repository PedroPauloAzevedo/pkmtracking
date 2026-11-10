# Concluído: histórico técnico por versão

> Atualizado em 10/11/2026. O lado de quem usa (o que mudou na tela e o passo a passo) está em `novidades.json`; os commits estão no
> `git log`. Aqui fica o que **não** está em nenhum dos dois: o porquê técnico, nomes no código e o que foi testado.
> Mais recente primeiro. Versões publicadas na `main` de `PedroPauloAzevedo/pkmtracking`.

| Versão | Data | Commit | Título |
|---|---|---|---|
| (Skill) | 06/11/2026 | `d0d0a58` (PR #1) | Skill: hardening, revisão das conclusões, experimentos a7–a11 e p0, base estratégica e ferramentas P1–P7 |
| (Skill) | 06/11/2026 | `49664da` | Skill "Statistical Analyst": inventário, auditoria e ferramentas estatísticas (sem versão nova do programa) |
| 2026.11.10-4 | 10/11/2026 | (ver `git log`: "v2026.11.10-4") | Modo automático mais leve |
| 2026.11.10-3 | 10/11/2026 | (ver `git log`: "v2026.11.10-3") | Coleção nova na biblioteca no mesmo dia |
| 2026.11.10-2 | 10/11/2026 | (ver `git log`: "v2026.11.10-2") | Deck novo ganha nome provisório |
| 2026.11.10-1 | 10/11/2026 | (ver `git log`: "v2026.11.10-1") | Logs com o código das cartas |
| 2026.11.09-4 | 09/11/2026 | (ver `git log`: "v2026.11.09-4") | Início novo: Hoje, tema e dados coletados |
| 2026.11.09-3 | 09/11/2026 | (ver `git log`: "v2026.11.09-3") | Tema claro ou escuro à sua escolha |
| 2026.11.09-2 | 09/11/2026 | (ver `git log`: "v2026.11.09-2") | Cartas x matchups com colunas do mesmo tamanho |
| 2026.11.09-1 | 09/11/2026 | (ver `git log`: "v2026.11.09-1") | Época da coleção nova nos torneios online |
| 2026.11.07-1 | 07/11/2026 | (ver `git log`: "v2026.11.07-1") | Decisões mostra o placar sem a carta |
| 2026.11.06-6 | 06/11/2026 | (ver `git log`: "v2026.11.06-6") | Telas ocupam a janela inteira |
| 2026.11.06-5 | 06/11/2026 | (ver `git log`: "v2026.11.06-5") | Replay: Energias no Pokémon certo (listas de descarte e ligações ambíguas) |
| 2026.11.06-4 | 06/11/2026 | (ver `git log`: "v2026.11.06-4") | Log original de cada partida (copiar / baixar .txt) |
| 2026.11.06-3 | 06/11/2026 | (ver `git log`: "v2026.11.06-3") | Replay: dano do Risky Ruins no Pokémon certo |
| 2026.11.06-2 | 06/11/2026 | (ver `git log`: "v2026.11.06-2") | Deck do adversário pelo NB2, marca "incerto" e faixas do meta com a dependência entre partidas |
| 2026.11.06-1 | 06/11/2026 | (ver `git log`: "v2026.11.06-1") | Ícones dos decks aparecem sem recarregar o painel |
| 2026.11.05-6 | 05/11/2026 | `2600e4c` | Partidas: filtro do deck do adversário; ícones dos decks de volta |
| 2026.11.05-5 | 05/11/2026 | `2600e4c` | Épocas de coleção nas análises, "Ver todas" consertado e replay com o descarte certo |
| 2026.11.05-4 | 05/11/2026 | `2600e4c` | Biblioteca de cartas: carta que o TCGdex não entrega não para a atualização |
| 2026.11.05-3 | 05/11/2026 | `c53abc5` | Filtro Jogador com qualquer combinação (publicada junto com a -2) |
| 2026.11.05-2 | 05/11/2026 | `c53abc5` | Replay mostra os prêmios que o log revela (não saiu sozinha: foi junto com a -3) |
| (documentação) | 05/11/2026 | `c100596` | Reorganização da documentação em `PROJECT_KNOWLEDGE/` |
| 2026.11.05-1 | 05/11/2026 | `c0b0943` | Modo automático se ajusta quando o jogo muda de tamanho |
| 2026.11.03-1 | 03/11/2026 | `4484f2c` | Replay mostra a mão dos dois jogadores; painel só para computador |
| 2026.11.02-7 | 02/11/2026 | `c5196bd` | Efeito de cada carta, replay mais fiel, painel dividido e testes de tela |
| 2026.11.02-6 | 02/11/2026 | `d9f5de3` | Replay põe o dano de habilidades e do Phantom Dive no Pokémon certo |
| 2026.11.02-5 | 02/11/2026 | `d75a60d` | Modo automático põe o jogo na frente antes de clicar |
| 2026.11.02-4 | 02/11/2026 | `78edbea` | Partidas de outro jogador vão para Amigos; modo automático instalável pelo painel |
| 2026.11.02-3 | 02/11/2026 | `701b31b` | Consistência não quebra com 7 ou mais cópias de uma carta |
| (instalador) | 02/11/2026 | `9a23c1a` | Desinstalar fecha só o Coletor da própria pasta |
| 2026.11.02-2 | 02/11/2026 | `36a1d67` | Reúne 2026.11.01-1 a 2026.11.02-2 (ícone, menu, torneios online, só Standard, segurança, consistência, qual deck jogar, ACE SPEC) |
| 2026.10.29-4 a -9 | 29/10/2026 | `05780c6` … `f18f808` | Biblioteca rebusca coleções; Decisões; boas-vindas; vários jogadores; pasta do Drive; Amigos sem travar |

## 2026.11.10-4 — 10/11/2026 (R4 da pesquisa de outros apps)
- `tracker/auto_export.py`: `estado_do_jogo`, `ESPERA_SEM_JOGO`; o laço não fotografa a tela com o jogo fechado ou minimizado; a
  espera de 20 s com o Continue coberto termina quando o log chega. `tracker/cobertura.py`: `fechada()`.
- `teste_tracker.py`: `estado_do_jogo` responde um dos três estados.
## 2026.11.10-3 — 10/11/2026 (R3 da pesquisa de outros apps; D-051)
- `tracker/cartas.py`: `MALIE`, `id_malie`, `set_do_malie`, `_completar_pelo_malie`; `atualizar` troca o arquivo do malie.io pelo do
  TCGdex quando ele tiver a coleção com cartas.
- `teste_tracker.py`: conversão e chave da coleção. Medição (Delta Reign pelas duas fontes) em `EVIDENCE.md`.
## 2026.11.10-2 — 10/11/2026 (R2 da pesquisa de outros apps; D-050)
- `tracker/decks.py`: `carta_sem_listas`; `palpite_deck_detalhe` com o método `provisorio`; `incerto` marca o provisório.
- `teste_tracker.py`: caso do atacante sem listas. Medição de três critérios em `EVIDENCE.md`.
## 2026.11.10-1 — 10/11/2026 (R1 da pesquisa de outros apps; D-049)
- `tracker/leitor.py`: `CODIGO_CARTA`, `limpar_linha` tira o código, `_codigos_da_linha`, `resumo.codigos`. `banco.VERSAO_LEITOR` = 4.
- `tracker/cartas.py`: `id_do_codigo`. `tracker/decks.py`: `resolver_versoes` usa os códigos antes das pistas.
- `teste_tracker.py` seção 9. Medição em `EVIDENCE.md`.

## 2026.11.09-4 — 09/11/2026 (pedido do Pedro: reformular o Início com a sugestão 5, o tema e dados gerais)
- `web/js/partidas.js`: `contasHoje`, `painelHoje`, `painelDados`; `renderPainel` com tema no topo, Hoje, Geral, últimas partidas
  e Dados coletados. `app.py`: rota `/api/resumo-geral` (só contagens). Tema saiu da barra da esquerda (`index.html`) para o Início.
- Testes: `teste_tracker` confere `/api/resumo-geral`; `teste_telas.tema_manual` abre o Início e confere `#in-hoje` e `#in-dados`.

## 2026.11.09-3 — 09/11/2026 (sugestão 9 da comparação com o Pokemon Champions Battle Logger; pedido do Pedro)
- `web/estilo.css`: cores escuras também em `:root[data-tema="escuro"]`; a media query do Windows escuro não vale com
  `data-tema="claro"`; botões `nav .tema`. `web/index.html`: botões e o script do `<head>`. `web/js/base.js`: `aplicarTema`.
- `teste_telas.py`: `tema_manual` (Escuro, recarregar, Claro com o Windows escuro, Automático nos dois temas). Os 4 testes OK.
- `nav` com `overflow-y: auto`: com a janela baixa, os botões do tema (no fim da barra) ficavam fora da tela.
## 2026.11.09-2 — 09/11/2026 (pedido do Pedro: caixas do mesmo tamanho em Cartas x matchups)
- `web/js/campeonatos.js` (`renderCartasMatchups`): tabela `matriz iguais` com `<colgroup>` e `min-width` pelo número de decks;
  `web/estilo.css`: `.matriz.iguais` (`table-layout: fixed`, 80px nas 3 primeiras, cabeçalho alinhado embaixo).
- Conferido numa cópia com os dados do Pedro (Basic Box × Meowth ex, 8 decks): colunas de deck todas com 115px a 1600px de janela.
## 2026.11.09-1 — 09/11/2026 (pedido do Pedro: decks novos antes dos grandes eventos; D-048)
- `tracker/colecoes.py`: tipo de época `online` (`inicio_online` = dia do lançamento) e `INICIO` com os três tipos.
- `analises.torneios_da_fonte(..., epoca=)` e `app._lista_torneios` (`?epoca=`): cada fonte com o seu começo; `/api/epocas` com `online`.
- `web/js/base.js`: `tipoMeta()`, `qsTorneios` manda `?epoca=`, seletor e aviso por fonte; `campeonatos.js`: linha da época nos
  gráficos pela fonte.
- `teste_tracker.py` (seção 6): épocas online e `?epoca=` com o torneio sintético como grande evento e como online. Os 4 testes OK;
  conferido na tela numa cópia com os dados do Pedro e 7 torneios online de 05–08/11 (`EVIDENCE.md`).
## 2026.11.07-1 — 07/11/2026 (dúvida do Pedro: Dreepy com −27 p.p.)
- `analises.decisoes`: cada carta das tabelas de abertura e de cartas jogadas ganha `sem_v` (vitórias sem a carta).
- `web/js/decisoes.js`: "sem ela: V–D" ao lado da Diferença (tabela compacta por ordem) e no lugar de "N partidas" em "Quando não
  jogou". O caso: Dreepy 27–10 com ele e 2–0 sem ele dava −27 p.p., que parecia "jogar Dreepy atrapalha".

## 2026.11.06-6 — 06/11/2026 (pedido do Pedro: espaço vazio na lateral)
- `web/estilo.css`: `main` com `max-width: 2000px`; `.tabela.alta`, `.rp-log` e a coluna do replay acompanham a janela.
- Conferido numa cópia com os dados do Pedro, em 17 telas: a 1696×962 a área principal vai até a borda (antes parava em 1460px) e
  as listas têm 662px (antes 520px); a 1280×720 nenhuma tela ganha rolagem lateral e as listas ficam em 520px. Os 4 testes OK.

## 2026.11.06-5 — 06/11/2026 (erro de replay visto pelo Pedro)
- `tracker/replay.py`: `N cards were discarded` + lista (`tirar_listados`), Energias ambíguas (`mover_ambigua`, `_custo_ataque`,
  2ª passada) (D-046). Teste: `teste_replay.py` seção 14 (dois Metang com Metal Maker e lista do nocaute; Metallic Hammer).
  4 testes OK numa cópia de teste só desta tarefa (a cópia compartilhada foi sobrescrita por outra sessão no meio da medição).

## 2026.11.06-4 — 06/11/2026 (pedido do Pedro)
- `web/js/partidas.js`: botão "Log original" no detalhe da partida e `mostrarLogOriginal` (janela com o texto gravado, Copiar tudo,
  Baixar .txt, Fechar/Esc). Nenhuma rota nova: `/api/partidas/<id>` já devolvia `texto`.
- Teste: `teste_telas.py` (o texto da janela é igual ao gravado; a janela fecha). Os 4 testes OK.

## 2026.11.06-3 — 06/11/2026 (erro de replay visto pelo Pedro)
- `tracker/replay.py`, `dono_dos_contadores`: depois de `Risky Ruins was activated.`, o dono é quem escreveu a linha (D-045).
- Teste: `teste_replay.py` cenário 2b (Risky Ruins da Ana, Budew da Bia; falha na versão anterior). Medição em `EVIDENCE.md`.

## 2026.11.06-2 — 06/11/2026 (decisões do Pedro D-040, D-041, D-042)
- **D-040** `decks.identificar_detalhe` (novo; `identificar` passa a usá-lo): o NB2 decide sempre que há modelo (≥ 200 listas); ícones
  só sem modelo. A regra antiga fica em `decks._identificar_regra_antiga` (e `CONFIANCA_NB`, usado só por ela e pelos experimentos).
  Medição antes/depois (a8 da Skill, mesmos dados e semente): a coluna "programa" passou de 57,5 / 79,3 / 91,3% (turnos 1 / 2 / 6) para
  63,4 / 81,0 / 91,0%, idêntica ao NB2 em todos os turnos.
- **D-042** `decks.incerto` + `LIMIAR_INCERTO = 0,6` (experimento a10, critério fixado antes de olhar: menor limiar com acerto ≥ 90% nas
  não marcadas → marca ~10%, que acertam ~37%). `analises.visao` devolve `deck_adv_incerto` (nunca para deck escolhido à mão);
  painel: `incertoHtml` (`base.js`) na lista de partidas e na partida; CSV `minhas_partidas.csv` ganhou a coluna no fim.
  Nos dados do Pedro (80 partidas): 3 mudam de deck do adversário e 4 ficam "incertas" (todas de amigos).
- **D-041** `analises.wilson(..., efeito)`, `placar(..., efeito)`, `icc_binario`, `dependencia_torneios`, `efeito_desenho`: no Meta
  (taxa dos decks, matriz) e no perfil do deck, faixa com efeito de desenho 1 + (m − 1)·ICC, ICC calculado nas partidas da seleção.
  Escolha pelo experimento a11 (metades independentes por jogador): cobertura 93,1% → 95,3% (decks, Labs); fator fixo ×1,25 exagerava
  (98%). Nos dados do Pedro: ICC 0,015; faixas dos decks 2,3% mais largas em média (máx. 6%), 61 de 119 mudam 1 ponto, nenhuma cruza
  50%; matriz quase igual; taxas idênticas; `meta()` de 0,31 s para 0,49 s. Telas pessoais (Ladder) não mudam.
- `testes/experimentos/e2_identificar_deck.py`: coluna "atual" volta a medir os ícones (achado 9: chamava a regra de produção com o
  banco inteiro). Agora ícones 19–76% (antes, 95,7% com vazamento).
- Testes: `teste_tracker.py` seção 9 (regra nova, limiar, Wilson com efeito, ICC, faixas nunca mais estreitas); os 4 testes OK.
  Conferido na tela: marca "incerto" na partida. Evidências: `.claude/skills/statistical-analyst/experiments/resultados/` (a8 de
  06/11 09:24 com o código novo, a10, a11).

## (Skill) Statistical Analyst — 06/11/2026, `49664da`
- `.claude/skills/statistical-analyst/` (D-039): `SKILL.md`; `knowledge/` (matriz dos métodos com classe A–F e evidência, fórmulas,
  modelo do jogo, lacunas G0–G15, registro de pesquisas); `tools/ponte.py` (usa o `tracker` de uma cópia) e `tools/sa_tools.py`
  (log-loss, calibração, bootstrap agrupado, ICC, Holm/BH, melhor de 3, `registrar`); `experiments/a1..a6` com resultados;
  `tests/` (20 testes) e `evals/` (4 cenários: 16/16 com a Skill, 12/16 sem).
- `03_DECISIONS/STATISTICAL_INVENTORY_2026-11-06.md` e `STATISTICAL_AUDIT_2026-11-06.md` (10 achados). Nenhum código do programa mudou;
  as recomendações esperam o Pedro (`GAPS_AND_ROADMAP.md`).

## 2026.11.06-1 — Ícones sem recarregar (erro visto pelo Pedro)
- `decks.versao_arquetipos` (aumenta em `salvar_arquetipos`), em `/api/status`; `atualizarStatus` (base.js) busca de novo os decks
  e redesenha quando muda. Teste: `teste_tracker.py` seção 8. Conferido numa cópia com o cadastro zerado: 0 ícones ao abrir, 214
  sem recarregar uns segundos depois. Os 4 testes OK. Publicada a partir de um worktree separado, porque a pasta do projeto tinha
  trabalho sem commit da rodada de hardening da Skill.

## 2026.11.05-6 — Filtros de deck em Partidas e ícones dos decks (pedidos do Pedro)
- `web/js/partidas.js`: `S.filtroPartidas.adv`, campos "Deck do jogador" e "Deck do adversário" (opções em ordem de `nomeDeck`).
- `tracker/decks.py`: `ler_pagina_decks` procura os ícones na linha da tabela (`find_parent("tr")`) quando não há imagem no link;
  `salvar_arquetipos` não troca ícones por lista vazia; `icones_sem_cadastro`. `app.main` refaz a lista quando a maioria está vazia.
- Testes: `teste_tracker.py` seção 8 (os dois formatos do Labs e o "não apagar"); `teste_telas.py` (filtro Deck do adversário). Os
  4 testes OK; conferido numa cópia com os dados do Pedro (ícones nas 67 partidas). D-038.

## 2026.11.05-5 — Épocas de coleção, "Ver todas" e descarte no replay (pedidos do Pedro)
- **Épocas** (D-036): `tracker/colecoes.py` (tabela `COLECOES` + biblioteca para as futuras; `chegada_live` com hora, convertida
  do Pacífico para o relógio local sem tzdata; `validade_torneio`; `epocas`, `proxima`, `epoca_de`); rota `/api/epocas`;
  `analises.analise_pessoal`/`decisoes` aceitam `antes` e comparam `de` com dia e hora; `analises.torneios_da_fonte(de, ate, ids)` e
  `app._lista_torneios` com `?de=&ate=`. Painel: `seletorEpoca`, `comEpoca`, `noPeriodo`, `epocaDe`, `marcasEpoca`,
  `quandoEpoca` (base.js), separador na lista (`separadorEpoca`, partidas.js), linha tracejada em `graficoLinhas`.
- **"Ver todas"** (D-037): `novaTela`/`telaVelha` em todas as funções `render...()`, `setTimeout` com `aba()`, "Carregando…" em
  `render()`; contas dos decks guardadas por versão dos torneios (`banco.versao_torneios`, `decks._em_dia`) e feitas em segundo plano
  ao abrir (`app.main`).
- **Replay** (D-035): `dono_do_anexo`, `recuou`, `caidos` em `tracker/replay.py`; o destaque do descarte traz o `uid`.
- Testes: `teste_replay.py` (recuo com dois Dreepy, nocaute com dois Munkidori, Crushing Hammer; falha na versão publicada),
  `teste_tracker.py` seções 6 (épocas, coleção nova pela biblioteca, `/api/epocas`, `de`/`antes`, torneios por data) e 7 (contas dos
  decks por versão), `teste_telas.py` (`ver_todas_e_epocas`: falha na versão publicada; a busca Ctrl+K agora espera `#busca-q`).
  Os 4 testes OK. Conferido na tela com uma cópia dos dados do Pedro (porta 8799): separador às 15:00 de 05/11, filtro da época
  Delta Reign (9 partidas), Meta com a época Pitch Black (Mundial e Baltimore) e o aviso de 20/11, "Ver todas" e o replay do
  recuo com dois Dreepy.

## 2026.11.05-4 — Biblioteca de cartas não para por uma carta (erro visto pelo Pedro)
- `tracker/cartas.py`: o download de uma coleção foi para `_baixar_cartas` (6 por vez; se uma carta falhar, cancela as que faltam
  e repassa o `RuntimeError`). Em `atualizar`, a falha numa coleção vai para a lista `falhas` e o laço segue; no fim,
  `progresso["aviso"]` diz quais não foram atualizadas e `estado.json` guarda `falhas` sem avançar `ultima_verificacao` (D-034).
  `web/js/biblioteca.js` mostra o aviso em amarelo (o erro continua em vermelho).
- Teste: `teste_tracker.py` seção 5 (TCGdex falso com uma carta que nunca responde: a outra coleção é baixada, a com falha fica
  igual, 3 tentativas, data não avança; sem falha, a data avança). Com o `cartas.py` antigo, o teste falha com a mesma mensagem que
  o Pedro viu. Os 4 testes OK numa cópia.

## 2026.11.05-3 — Filtro Jogador com qualquer combinação (pedido do Pedro)
- Painel (`web/js/partidas.js`): `S.jogadorSel` (lista; `''` = você) no lugar de `S.jogador`; `seletorJogador` virou caixa de
  opções (`details.multi`, estilo em `estilo.css`) com "Marcar todos"/"Só eu"; aplica na hora, mantém a caixa aberta
  (`S.jogadorAberto`) e devolve o foco à marca; fecha ao clicar fora ou com Esc; não deixa desmarcar todos. Guardado em
  `localStorage` "jogadores" (a escolha antiga "jogador" é convertida, inclusive "*"). Ajustados `decisoes.js` e `amigos.js`
  ("Ver partidas dele" e apagar amigo). O resumo da caixa não mostra total (a soma contaria duas vezes o mesmo jogo).
- Servidor: `analises.do_jogador` aceita lista, `varios_jogadores`, `sem_repetidas` só junta donos diferentes (D-033);
  `app._jogador_pedido` lê `?jogadores=` (vários) ou `?jogador=` (antigo) em `/api/partidas`, `/api/decisoes` e no CSV.
- Testes: `teste_tracker.py` seção 2c (combinações, mesmo jogo pelos dois lados, formato antigo, API e CSV) e
  `teste_telas.py` (`jogadores_combinados`: marcar, não desmarcar todos, "Marcar todos", clicar fora, outra aba, recarregar).
  Os 4 testes OK. Conferido na tela com uma cópia dos dados do Pedro (você + amigo = 60 partidas: 21 + 40 − 1 jogo dos dois lados).

## 2026.11.05-2 — Prêmios no replay (pedido do Pedro)
- `replay.gerar`: cada linha "<carta> was added to X's hand." ligada a um "took" vira carta de prêmio (`premios_pegos`, com o quadro
  em que saiu dos prêmios); `premio_aberto` por jogador (aberto até completar ou até o turno acabar) e `adiantados` +
  `premio_logo_adiante` para as cartas que o log escreve antes do "took" (jogada de 3 prêmios). Destaque `premio` com a carta.
- `_premios_conhecidos`: em cada quadro, `mesa[j]["premios_conhecidos"]` = prêmios com nome que o jogador ainda vai pegar (D-032).
- Painel: `premiosHtml` em `web/js/replay.js` (grade 3 × 2 com face, verso ou vazio; dica com o turno em que foi pego) e classes
  `premio-carta` em `estilo.css` (não `premio`, que já é usada na tabela de eventos). README (seção 6) atualizado, inclusive a frase
  antiga "a mão do adversário não aparece".
- Explicação no topo de `replay.py` atualizada (mão e prêmios). 12 conferências de prêmios em `teste_replay.py`. Medição nas
  partidas reais em `EVIDENCE.md` (253 de 253 prêmios de quem exportou; mesa e mãos iguais à versão publicada). Os 4 testes OK.
- Privacidade: os exemplos nos comentários de `replay._Maos` (desde a 2026.11.03-1) e do topo de `revisao.py` (desde o primeiro
  envio) traziam nicks reais; trocados por Ana/Bia. Eles continuam no histórico antigo do git (não foi reescrito).

## 05/11/2026 — Reorganização da documentação
`PROJECT_KNOWLEDGE/` criada (00 a 05), `CLAUDE.md` virou guia de navegação e passou a ser publicado, dados da máquina em
`CLAUDE.local.md` (fora do GitHub), relatório da missão movido de `docs/` para `03_DECISIONS/`, README corrigido (não havia Releases;
lista antiga de arquivos trocada por link). `CONTEXTO_MESTRE.md`, `INSTRUCOES_NOVA_SESSAO.md`, `PASSAGEM.md` e a memória do Claude
foram migrados e guardados em `_arquivo_docs_antigos/` (local). Decisão D-026.

## 2026.11.05-1 — Modo automático e o tamanho do jogo
- Causa: `escala_modelos` guardava o tamanho dos botões da 1ª partida; `_candidatas` só testava esse tamanho e os vizinhos, e o
  "esquecer" só acontecia se a resolução do monitor mudasse. Com o jogo em outro tamanho, nunca mais reconhecia a tela (03/11 a 05/11).
- `auto_export.tamanho_jogo()` (área da janela "Pokemon TCG Live"); `_candidatas` usa a altura da janela/1440 e, na busca ampla,
  sempre testa ao redor do esperado; o tamanho da janela entra em `escalas["_tela"]` (mudou → esquece e anota no log);
  busca ampla a cada 5 voltas sem tamanho conhecido e a cada 15 com; `QUASE = 0.70` + `so_escalas` para confirmar em tela inteira;
  `ultima_escala`. Medição em `EVIDENCE.md`. Os 4 testes OK. Falta confirmar com o jogo real.

## 2026.11.03-1 — Mão dos jogadores; nada de celular
- `replay._Maos` (constantes `DESCARTA_DO_BARALHO`, `LIGA_DA_MAO`, `MAO_INTEIRA`), mão em cada quadro (`estado.maos`),
  `revelar_no_passado` para o mulligan de quem exportou, `conferencia_maos` na resposta do replay; desenho em `web/js/replay.js`
  (`maoHtml`) e `estilo.css`. 7 cenários de mão em `teste_replay.py`. Conferido 109/109 (EVIDENCE).
- D-002: removidas as regras CSS ≤ 600px, a tag `viewport` e a passagem a 375px do `teste_telas.py`.

## 2026.11.02-7 — Efeito de cada carta, replay e painel
- `tracker/regressao.py` + `e10_regressao_cartas.py` (D-021).
- Replay (D-011, D-012): `decks._limites_ps`/`_ps_compativel` na escolha de versão; "moved damage counters"; cura no formato
  "X's Y healed N damage"; "took N damage" com `atingidos`; Phantom Dive no Banco quando o Ativo tem o mesmo nome; `achar_nocauteado`
  (o de mais dano); contadores ambíguos com segunda passada (`_correcoes`) usando `_ps_minimo` com os golpes vistos;
  `CARTAS_FORA_DA_MESA` (Night Stretcher). Estados impossíveis 96 → 0 (EVIDENCE).
- Painel dividido em `web/estilo.css` + `web/js/*.js` (servidos por `/web/`); testes novos `teste_replay.py`, `teste_telas.py`
  (Playwright + Edge) e `/web/` no teste de segurança. Correções achadas pelos testes de tela: Ajustes (atalhos), Consistência sem
  Básico (Infinity no JSON), larguras de Perfil de deck e detalhe da partida.

## 2026.11.02-6 — Dono dos contadores
`replay.dono_dos_contadores` (nocaute seguinte ou ataque/habilidade que causou; D-010) e "put a damage counter" (= 1).

## 2026.11.02-5 — Jogo na frente antes de clicar
`_janela_do_jogo`, `jogo_na_frente`, `trazer_jogo` (Alt + `SetForegroundWindow`); espera do botão de exportar até ~10 s;
`[auto] tentativa ...` no `programa.log`; `ultima_nota`. Diagnóstico com o jogo real em 02/11 (EVIDENCE, D-014, D-016).

## 2026.11.02-4 — Partidas de outros e instalar o modo automático
`banco.dono_provavel` e `separar_partidas_de_outros` (na abertura e quando o nick muda; D-008); teste 2b no `teste_tracker.py`.
`AutoExport.instalar` (pip do Python do programa: `python_do_programa`, sem janela) + `importlib.invalidate_caches` para ligar sem
reiniciar; mensagem de erro com o comando exato. Causa do problema: as bibliotecas tinham sido instaladas em outro Python.

## 2026.11.02-3 — Consistência com 7+ cópias; instalador; vídeo
- `probabilidades.hipergeometrica` devolvia erro com k maior que a amostra; o exp. 1 passou a cobrir uma carta com 9 cópias.
- Instalador: Inno Setup 6.7.3 instalado por usuário (winget) no PC de desenvolvimento; `ColetorTCG-Instalador-2026.11.02-2.exe`
  (58,5 MB) gerado da versão publicada e testado (instala em pasta à parte, abre, desinstala fechando só o Coletor daquela pasta e
  mantém `dados/`). Correções no `coletor.iss` (commit `9a23c1a`): o desinstalador fechava qualquer Coletor na porta 8765; agora
  só o da própria pasta, pela lista de processos via CIM (o desinstalador é 32 bits e o `Get-Process` 32 bits não vê o caminho de
  programas 64 bits). No Inno só `{{` é dobrada.
- Vídeo tutorial (1:57, Full HD) com uma cópia de demonstração (jogadora fictícia "Ana_TCG" + torneios públicos). Scripts em
  `ferramentas/video/` (fora do GitHub): `capturar.py`, `narrar.ps1`, `montar_video.py`, `roteiro.json` e o `LEIA-ME.md` com o passo a passo.

## 02/11/2026 — Histórico git
A pasta do projeto voltou a ter `.git` com o histórico do GitHub (o histórico local antigo e o ramo `missao-evolucao`, onde a missão
de 02/11 tinha um commit por etapa, se perderam). Documentos privados em `.git/info/exclude`.

## 2026.11.02-2 (publicada em 02/11, reúne 2026.11.01-1 a -4 e 2026.11.02-1/-2)
- **ACE SPEC:** `t_jogadores.ace_spec` (NULL = sem lista, '' = sem ACE SPEC) gravada por `banco.atualizar_ace_spec()` na importação,
  na migração e quando a biblioteca muda. O INSERT de `t_jogadores` passou a nomear as colunas (o teste pegou 11 × 12 colunas).
  `variantes.variantes()` = versões pela ACE SPEC (M5, exp. 9); o anterior virou `variantes_por_semelhanca()`.
- **2026.11.02-1 (missão de evolução, relatório em `03_DECISIONS/MISSION_REPORT_2026-11-02.md`):** proteção de origem, Consistência,
  Qual deck jogar?, variantes, taxa ajustada, NB2, telas rápidas (memória da lista de partidas, índices), tetos de versão; e1–e8 e
  `teste_seguranca.py`.
- **2026.11.01-4 (torneios online, só Standard confirmado):** `limitless.formatos_labs()` (índice `tr[data-format]` + página do evento
  para o id do Labs), `escolher_para_importar(..., formatos)` pula o que não é Standard, `importar()` grava `formato`; online:
  `listar_online`, `importar_online`, `sincronizar_online` (no fim de `Sincronizador.rodar_uma_vez`); colunas `torneios.fonte` e
  `formato`; `analises.torneios_da_fonte`, `_filtro_torneios(None)` = todos os Standard, `[]` = nenhum; `tendencia` por semana com
  mais de 20 torneios; painel `S.fonte` (localStorage) e `seletorTorneios()`. Testado: 8 eventos do Labs confirmados Standard em
  11 s; 3 torneios online (379, 157 e 128 jogadores, ~14 s cada pelo limite da API).
- **2026.11.01-3:** leitor com `exportou`, `problemas`, `digital` (`VERSAO_LEITOR` 3; conferido em 13 logs reais, sem falso alarme);
  `descobrir_eu`/`perspectiva` por quem exportou, `sem_repetidas`; modo automático com busca multiescala, escala por botão,
  esperado = altura/1440, busca ampla a cada 5 olhadas, testado em telas simuladas 1920/2560/1366 (custo 0,07–0,14 s a cada 2 s);
  imagens do Full Bench em commit fixo; cobertura Win32 (testada lendo os pixels da tela); nova tentativa e aviso; janela própria
  (`janela.py`), primeiro uso guiado, busca Ctrl+K; instalador (`montar.py` + `coletor.iss`, Python do NuGet 3.15.2 sem tkinter;
  pasta de 235 MB, cv2 = 112 MB).
- **2026.11.01-2:** ícone na bandeja (`bandeja.py`; aberto pelo `python.exe`, o `app.py` se reabre pelo `pythonw.exe` —
  `_reabrir_sem_janela`); atalhos (`atalhos.py`; pasta pela API do Windows porque o PowerShell quebrava o acento de "Área de
  Trabalho"); menu de 4 seções com abas (`SECAO`, `ABAS`, `trilha()`). Lição: testar na porta 8799.
- **2026.11.01-1:** base de regras reduzida ao Standard e dentro do programa (tela, download diário); leitura com as regras (marcas
  H/I/J, promos liberados; `por_nome` e `resolver_versoes` preferem a versão Standard; quem começou = quem joga o 1º turno;
  vencedor = quem completou 6 prêmios; replay não evolui Pokémon que entrou no mesmo turno; `VERSAO_LEITOR` 2 e `VERSAO_INDICE` 2);
  aberturas por quem começou; Lista oficial; conferência do Standard; `novidades.json` + janela de novidades; correção de códigos de
  coleção começando por número (`30C 152`, relidas via `versao_listas`).

## Antes de 2026.11.01 (29/10/2026)
2026.10.29-4 (biblioteca rebusca coleções novas, ex.: 30th Celebration), -5 (tela Decisões, ícones corrigíveis), -6 (boas-vindas com
nick e `COMECE_AQUI.txt`), -7 (vários jogadores, exportar/importar logs), -8 (pasta compartilhada do Google Drive), -9 (Amigos não
trava procurando o Drive). Primeiros arquivos enviados ao GitHub em 29/10/2026.
