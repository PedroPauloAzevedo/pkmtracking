# Concluído: histórico técnico por versão

> Atualizado em 05/11/2026. O lado de quem usa (o que mudou na tela e o passo a passo) está em `novidades.json`; os commits estão no
> `git log`. Aqui fica o que **não** está em nenhum dos dois: o porquê técnico, nomes no código e o que foi testado.
> Mais recente primeiro. Versões publicadas na `main` de `PedroPauloAzevedo/pkmtracking`.

| Versão | Data | Commit | Título |
|---|---|---|---|
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
