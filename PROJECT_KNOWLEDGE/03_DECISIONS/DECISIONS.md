# Registro de decisões

> Atualizado em 10/11/2026. Decisões técnicas e de produto, numeradas. **Não reaproveite números**; para mudar uma decisão,
> crie outra que diga qual substitui e por quê. Rever uma decisão firme exige justificativa (e, se for algoritmo, medição).
> Datas "até 02/11" = decisões tomadas nas primeiras versões (out–nov/2026), registradas na consolidação de 02/11/2026.

## Escopo e produto
- **D-001 · Só formato Standard** (até 02/11; firme). Nada de Expanded/Unlimited/limitados; torneio de outro formato fica fora das
  contas. *Por quê:* é o formato que o Pedro joga; misturar formatos distorce meta e listas. Ver `STANDARD_AND_GAME_RULES.md`.
- **D-002 · Só computador, nada para celular** (03/11/2026; firme). Sem CSS de largura de celular, sem teste a 375px, sem `viewport`,
  sem recursos para celular. As regras de janela estreita (≤ 900/1100px) ficam porque servem ao PC. *Por quê:* pedido do Pedro, para
  economizar espaço e desenvolvimento; ninguém usa o Coletor no celular. Complementa D-003.
- **D-003 · Servidor só local + proteção de origem** (02/11; firme). Host local; `Origin`/`Sec-Fetch-Site` de outro site = 403.
  Acesso pela rede/celular foi descartado pelo Pedro. *Por quê:* antes, uma página maliciosa aberta no navegador conseguiria mudar o
  repositório de atualização e instalar código de outra pessoa.
- **D-004 · Os dados de cada pessoa ficam só com ela** (até 02/11; firme). `dados/` nunca vai para o GitHub e o atualizador nunca
  toca em `dados/`, `.venv/`, `.git/` nem nas imagens existentes de `modelos/`.

## Captura
- **D-005 · Capturar o log pronto do jogo (área de transferência) em vez de ler a tela** (até 01/11). Reconhecer cartas e dano por
  imagem exigiria visão computacional treinada, erraria com animações e geraria um log pior que o do jogo. O jogo não grava o log em
  arquivo (o diagnóstico procura e não acha).
- **D-006 · Modo automático = reconhecer só dois botões e clicar; experimental e desligado por padrão** (01/11). Imagens prontas do
  Full Bench (MIT) num commit fixo; busca em vários tamanhos. *Riscos assumidos:* automação de cliques no cliente oficial ("por sua
  conta e risco", dito ao usuário).
- **D-007 · Cobertura do Continue em Win32 puro** (01/11). O Python embutido no instalador não tem tkinter.
- **D-014 · Pôr o jogo na frente antes de clicar e registrar cada tentativa** (02/11/2026, v2026.11.02-5). Com outra janela ativa o
  clique caía no lugar errado. O registro em `programa.log` permite diagnosticar sem imagens.
- **D-015 · Tamanho dos botões pela janela do jogo, reaprendido quando ela muda; busca ampla de segurança a cada 30 s; confirmação em
  tela inteira quando a busca reduzida chega a 0,70** (05/11/2026, v2026.11.05-1). *Por quê:* o tamanho ficava preso ao da 1ª
  partida e o modo parou de reconhecer a tela em 03/11. Medição em `EVIDENCE.md`. A busca ampla com tamanho conhecido foi limitada a
  30 s para não pesar durante o jogo (~0,5 s de processamento).
- **D-016 · Diagnóstico na máquina do Pedro: imagens só da janela do jogo, só com o jogo na frente; banco real só para leitura**
  (02/11/2026; firme). *Por quê:* um gravador de diagnóstico que fotografava a tela inteira chegou a salvar janelas pessoais
  (apagadas na hora). Imagens de diagnóstico são apagadas ao fim.

## Leitura, dono e replay
- **D-008 · "Você" = quem exportou o log; partida em que o seu nick não joga vai para o amigo** (02/11/2026, v2026.11.02-4).
  Ver `PLAYERS_AND_OWNERSHIP.md`. *Por quê:* uma partida de um amigo, copiada no computador do Pedro, entrou no histórico dele.
- **D-009 · Repetidas: mesmo texto é ignorado; mesmo jogo pelos dois lados conta uma vez (impressão digital)** (01/11, ideia do Full Bench).
- **D-010 · Replay: o dono dos contadores vem do nocaute seguinte ou do ataque que os causou, não do texto** (02/11/2026, v2026.11.02-6).
  O jogo escreve o nome de quem usou no Pokémon atingido. Ver `BATTLE_LOG_FORMAT.md` §6.
- **D-011 · Replay: a versão da carta sai dos PS que a partida revela, e isso vale mais que a lista de Meus decks** (02/11/2026,
  v2026.11.02-7). Nocauteado com D de dano tem no máximo D PS; quem aguentou D tem mais.
- **D-012 · Replay: contadores ambíguos (dois Pokémon de mesmo nome) são corrigidos pelo nocaute, montando a partida de novo**
  (02/11/2026, v2026.11.02-7). Usa o menor PS das versões válidas que têm os golpes usados.
- **D-013 · Mão no replay: quem exportou vê tudo; o adversário mostra só o que buscou; revelação "desde o começo" só para quem
  exportou** (03/11/2026, v2026.11.03-1). Para o adversário não dá para saber em que compra a carta entrou.
- **D-032 · Prêmios no replay: os que quem exportou pegou aparecem com a face desde o começo; os outros ficam virados**
  (05/11/2026, v2026.11.05-2; pedido do Pedro). *Por quê:* o jogo escreve o nome de cada prêmio pego por quem exportou, e os prêmios
  são separados na preparação sem nenhuma linha que os troque depois; do adversário vem sempre "A card". Não se adivinham os prêmios
  restantes pela lista do deck (a carta não vista pode estar no baralho). Medição em `EVIDENCE.md`.
- **D-033 · Filtro Jogador com qualquer combinação (caixa de opções); o mesmo jogo pelos dois lados só junta logs de donos
  diferentes** (05/11/2026, v2026.11.05-3; pedido do Pedro). *Por quê:* o seletor só permitia um jogador ou todos. Com vários
  marcados, a impressão digital evita contar duas vezes o jogo que chegou pelo seu log e pelo do amigo; mas ela é só um resumo
  (vencedor, perdedor, turnos, motivo, prêmios) e dois jogos diferentes do mesmo dono podem ter o mesmo — esses não se juntam
  mais. O formato antigo `?jogador=` continua aceito. Medição em `EVIDENCE.md`.
- **D-034 · Biblioteca de cartas: falha do TCGdex numa carta pula só aquela coleção, e a verificação é repetida em 1 hora**
  (05/11/2026, v2026.11.05-4; erro visto pelo Pedro). *Por quê:* no "Baixar tudo de novo" uma carta (`sv08-236`) não respondeu
  em 3 tentativas e a atualização inteira parou na coleção 14 de 29; a carta respondia normalmente minutos depois. Manter o arquivo
  antigo da coleção é seguro (já era o que se fazia com resposta incompleta). As tentativas e a espera entre elas não mudaram.
- **D-035 · Replay: a carta presa descartada sai do Pokémon que recuou, do nocauteado ou do que tem a carta** (05/11/2026,
  v2026.11.05-5; erro visto pelo Pedro num replay com dois Dreepy). *Por quê:* o replay tirava a carta do primeiro Pokémon com
  aquele nome; com dois de mesmo nome, a Energia do recuo ficava presa no que recuou, e a Energia listada depois de um nocaute saía
  do irmão que continuava em jogo. O contexto resolve: no recuo a frase vem em sublinha; depois do nocaute, em linha solta.
  Medição em `EVIDENCE.md` (descartes que não tiravam nada: 41 → 0; tirados do irmão em jogo: 2 → 0; ataques com Energia de
  menos: 78 → 73, nenhum caso novo).
- **D-045 · Replay: os contadores do Risky Ruins vão para o Básico de quem o jogou, não para o do dono do Estádio** (06/11/2026,
  v2026.11.06-3; erro visto pelo Pedro num replay com dois Budew). *Por quê:* depois de `Risky Ruins was activated.` o jogo escreve
  `X put 2 damage counters on <dono do Estádio>'s Y`; o Y é sempre o Básico que X acabou de pôr no Banco. O replay confiava no dono
  escrito quando ele era outro jogador. Medição em `EVIDENCE.md` (55 de 145 linhas com o dono trocado; estados impossíveis 1742 → 1660).
- **D-046 · Replay: listas de descarte tiram as cartas presas, e Energia ligada "a um dos X" vai para o X que as provas apontam**
  (06/11/2026, v2026.11.06-5; erro visto pelo Pedro num replay com quatro Metang). *Por quê:* `N cards were discarded from P's Y.` +
  lista `•` (efeito de ataque, ex.: Metallic Hammer, ou nocaute) não era lido, e as Energias descartadas ficavam na mesa; habilidades
  como Metal Maker ligam "to Metang on the Bench" sem dizer qual, e tudo caía no primeiro. As provas: a lista completa do nocaute (o
  que sobra de ambíguo no nocauteado era de outro candidato), a lista do descarte, o custo do ataque (pela biblioteca de cartas) e o
  descarte no recuo. A ligação ambígua guarda a linha e os candidatos; a 2ª passada (a mesma dos contadores, D-012) liga no Pokémon
  certo desde o começo. Sem prova, continua no primeiro. Medição em `EVIDENCE.md` (ataques com Energia de menos 82 → 42 de 840, sem
  caso novo; nocautes com as cartas presas iguais à lista 178 → 204 de 221).
- **D-036 · Análises por época de coleção: no TCG Live a época começa na véspera do lançamento, às 10h do Pacífico; nos torneios,
  na segunda sexta-feira depois do lançamento** (05/11/2026, v2026.11.05-5; pedido do Pedro). *Por quê:* cada coleção nova pode
  mudar o meta. O jogo libera a coleção um dia antes das lojas, às 10h do horário do Pacífico (visto nas coleções recentes); a
  Play! Pokémon só aceita a coleção em torneio na segunda sexta-feira depois do lançamento (`docs/regras-standard.md`). A hora conta
  nas suas partidas porque as da manhã do dia da chegada ainda são do meta anterior (no dia da Delta Reign, todas as 7 partidas do
  Pedro foram antes das 15h). As datas vêm de uma tabela no código (inclui coleção que ainda não está no TCGdex) e, para coleções
  futuras, da biblioteca de cartas. O padrão continua "Todas as épocas", para nada sumir da tela sem a pessoa escolher.
- **D-037 · Painel: uma tela lenta não cobre a nova; contas dos decks guardadas até os torneios mudarem** (05/11/2026,
  v2026.11.05-5; "Ver todas" que não fazia nada). *Por quê:* duas telas podiam estar sendo desenhadas ao mesmo tempo, e a que
  terminava por último (o Início, mais lento) cobria a outra; como o endereço já era o de Partidas, clicar de novo não fazia nada.
  A lentidão vinha da identificação do deck, refeita a cada 2 minutos sobre todas as listas dos torneios. Agora cada tela confere se
  ainda é a vez dela antes de desenhar, a tela lenta mostra "Carregando…", e as contas só são refeitas quando um torneio é gravado,
  apagado ou reconvertido (no máximo a cada 1 hora), com a primeira feita em segundo plano ao abrir. Os decks identificados não
  mudaram (medição em `EVIDENCE.md`).
- **D-038 · Ícones dos decks: ler a coluna nova do Labs e nunca apagar um ícone gravado** (05/11/2026, v2026.11.05-6; ícones
  sumidos em Partidas). *Por quê:* a página de decks do Labs passou a pôr o ícone fora do link do deck; o programa lia vazio e
  regravava o cadastro, apagando 122 dos 134 ícones. Ler os dois formatos e não aceitar lista vazia por cima evita que a próxima
  mudança de layout apague tudo de novo; refazer a lista ao abrir conserta quem já perdeu os ícones. Em 2026.11.06-1 o painel
  passou a buscar a lista de novo quando ela muda no servidor (`versao_arquetipos` em `/api/status`): no Coletor do Pedro o cadastro
  foi refeito 19 s depois de abrir, mas a janela já tinha carregado a lista sem ícones.

## Análises e algoritmos
- **D-017 · Melhoria de algoritmo só com medição contra o atual, nos mesmos dados** (até 02/11; firme). Manter a versão antiga quando
  útil (`_uso_cartas_lento`, `_identificar_nb_direto`, `variantes_por_semelhanca`).
- **D-018 · Matchups: taxa real é o padrão; confronto ajustado (k = 24) é opção** (02/11, exp. 3).
- **D-019 · Identificação do deck: NB2 com reserva pelos ícones e pelo palpite do dano** (02/11, exp. 2). *Substituída por D-040
  em 06/11/2026: a reserva pelos ícones só vale sem modelo.*
- **D-020 · Versões do deck pela ACE SPEC (modelo M5)** (02/11, exp. 9). Sub-versões dentro de cada ACE SPEC pioraram a previsão;
  nenhuma divisão prevê o resultado individual melhor que o deck inteiro: versões servem para descrever.
- **D-021 · Efeito de cada carta por regressão logística com o confronto ajustado como ponto de partida e freio L2 = 300** (02/11/2026,
  v2026.11.02-7, exp. 10). Ganho de previsão pequeno, mas bem melhor que o método bruto com/sem.
- **D-031 · Consistência com contas exatas (hipergeométrica), mulligan como condição** (02/11, exp. 1). Não simula; não considera
  efeitos de cartas (piso).
- **D-039 · Skill "Statistical Analyst" dentro do repositório, em `.claude/skills/statistical-analyst/`** (06/11/2026, pedido do
  Pedro com autorização para todas as fases). *Por quê:* o repositório é a fonte de verdade (D-026) e a Skill só tem conhecimento,
  ferramentas e experimentos sem dado pessoal (um teste da própria Skill confere isso). Ela usa as funções do Coletor pela
  `tools/ponte.py` em vez de copiá-las e traz só contas que o programa não tem. Vai junto para quem atualiza (o atualizador copia o
  zip inteiro; não faz mal: o programa não lê essa pasta). Achados que pedem mudança no programa ficam como recomendação
  (`STATISTICAL_AUDIT_2026-11-06.md`, `GAPS_AND_ROADMAP.md`) até o Pedro decidir.
- **D-040 · Identificação do deck: NB2 sempre que houver modelo; ícones só sem modelo** (06/11/2026, decisão do Pedro; v2026.11.06-2;
  substitui D-019). *Por quê:* a8 — com cartas vistas realistas e sem vazamento, +5,9 e +1,7 pp de acerto nos turnos 1 e 2. *Custo
  aceito:* decks raros pioram (F1 macro 0,53 × 0,58 no turno 2). Regra antiga mantida em `_identificar_regra_antiga` (D-017).
- **D-041 · Faixas das telas de torneio com a dependência entre partidas do mesmo jogador** (06/11/2026, decisão do Pedro;
  v2026.11.06-2). Efeito de desenho 1 + (m − 1)·ICC com o ICC das partidas da seleção (a11: cobertura 93,1% → 95,3%; fator fixo
  exagerava). Não muda nenhuma taxa. Telas pessoais (Ladder) sem correção: lá a dependência não foi medida com poder (a7).
- **D-042 · Deck do adversário "incerto" com confiança do NB2 abaixo de 0,6** (06/11/2026, decisão do Pedro; v2026.11.06-2).
  Limiar pelo a10 (critério fixado antes: menor limiar com acerto ≥ 90% nas não marcadas). Ícones e palpite pelo dano não têm
  medida de confiança e não são marcados. Alternativa registrada: 0,9 (marcaria ~28%, que acertam ~60%).
- **Proteção da instalação real na ponte da Skill** (06/11/2026, decisão do Pedro; feito): a ponte também lê
  `~/.sa_pastas_protegidas`, arquivo pessoal fora do repositório (`tools/ponte.py`; teste em `tests/test_ponte.py`).

## Engenharia, distribuição e processo
- **D-022 · Dependências com teto de versão grande** (`flask<4`, `pillow<14`, `opencv-python<6`...) (02/11). Uma atualização nunca
  puxa uma versão nova grande que quebre o programa.
- **D-023 · Instalador por usuário em `%LOCALAPPDATA%\Programs\ColetorTCG`, sem administrador; desinstalar fecha só o Coletor da
  própria pasta e mantém `dados/`** (02/11). Sem administrador o atualizador consegue trocar arquivos.
- **D-024 · Versão `AAAA.MM.DD-N` + entrada em `novidades.json` + passo a passo para os amigos** (até 02/11; firme). Leitor mudou →
  `banco.VERSAO_LEITOR`; índice de cartas → `cartas.VERSAO_INDICE`.
- **D-025 · Publicar = commit + push na `main`, só quando o Pedro pedir; autor `Claude <noreply@anthropic.com>`; `.bat` e
  `COMECE_AQUI.txt` em CRLF** (até 02/11; firme). Um ramo por tarefa; `merge --ff-only` na `main` ao publicar (desde 02/11, quando a
  pasta do projeto voltou a ter o histórico do GitHub).
- **D-026 · A documentação do projeto mora no repositório (`PROJECT_KNOWLEDGE/` + `CLAUDE.md`), pública e sem dados pessoais;
  dados da máquina em `CLAUDE.local.md` (fora do GitHub); conversas antigas e a memória automática do Claude não são fonte**
  (05/11/2026). Substitui a regra antiga "nunca publicar o CLAUDE.md e os documentos de contexto". *Por quê:* não depender do histórico
  das conversas (uma sessão apagada levou junto um estudo inteiro) e o repositório não pode ser privado (os programas dos amigos
  baixam as atualizações dele sem senha). Os documentos antigos ficaram em `_arquivo_docs_antigos/` (local).
- **D-027 · Dados reais do Pedro nunca em vídeos, demonstrações ou no GitHub** (02/11; firme). Demonstrações usam a jogadora fictícia
  "Ana_TCG" e torneios públicos.
- **D-028 · Base de regras como texto (`docs/regras-standard.md`), baixada do GitHub uma vez por dia, revisada todo mês** (01/11).
  Uma rotação de marcas chega sem versão nova do programa.
- **D-029 · Nome, Player ID e nascimento (Lista oficial) só em `dados/config.json`** (01/11).
- **D-030 · Painel sem frameworks, dividido em arquivos por área, com testes de tela automáticos** (02/11/2026, v2026.11.02-7).

- **D-043 · Dois desenvolvedores: tudo entra na `main` por Pull Request e só o Pedro junta** (06/11/2026, decisão do Pedro).
  Complementa D-025 (o "publicar" passa a ser o Pedro juntar o PR na `main`). Ramos `feature/`, `fix/`, `refactor/`, `docs/`,
  `chore/`; modelo de PR em `.github/`; `CODEOWNERS` com o Pedro; PR que muda o programa traz a própria versão (D-024); mudança de
  banco ou de contrato registrada em `DATA_MODEL.md`/`API_CONTRACTS.md`; cada um com dados, credenciais e `CLAUDE.local.md` próprios.
  Repositório continua **público** (confirmado pelo Pedro; D-026); o e-mail e o nick antigos que já estão no histórico ficam como
  estão (aceito pelo Pedro: tirar exigiria reescrever o histórico). *Por quê:* a `main` é baixada pelo atualizador dos amigos sem
  conferência de assinatura, então só código revisado pode chegar lá. Regras em `../00_CENTRAL/COLLABORATION.md`; a proteção da
  `main` no GitHub é configurada pelo Pedro (seção 9 de lá).
- **D-047 · No computador do Pedro, "publicar" = o Claude abre o PR e junta** (06/11/2026, decisão do Pedro; ajusta D-043).
  *Por quê:* o Pedro não quer clicar para aprovar as próprias mudanças. O pedido "publicar" dele já é a aprovação: o Claude roda os
  testes de entrega, faz o commit, envia o ramo, abre o PR com o modelo e junta (`gh pr merge --merge`). O PR continua no histórico.
  Não vale para o segundo desenvolvedor: o PR dele espera o Pedro. No GitHub, a regra "Main" (hoje desligada) já deixa o
  administrador passar; se ela for ligada, o Pedro continua juntando sem aprovação, e o segundo dev precisa da aprovação dele.
- **D-044 · Mac como plataforma de uso completo, prioridade do segundo desenvolvedor** (06/11/2026, decisão do Pedro). O segundo
  desenvolvedor usa Mac e vai priorizar fazer o programa funcionar por inteiro nele. Código de uma plataforma fica dentro de
  `if sys.platform == ...`, sem mudar o comportamento no Windows (os amigos usam Windows); PR de plataforma diz em qual sistema foi
  testado. Não muda D-002 (continua nada para celular). Levantamento em `../00_CENTRAL/ARCHITECTURE.md` ("Windows × Mac") e lista em
  `../04_IMPLEMENTATIONS/BACKLOG.md` ("Paridade no Mac").
- **D-048 · Torneios online: a época de uma coleção começa no dia do lançamento, não na validade dos grandes eventos**
  (09/11/2026, v2026.11.09-1; pedido do Pedro; ajusta D-036). *Por quê:* os torneios online do Limitless são jogados no TCG Live e os
  organizadores liberam a coleção assim que ela chega ao jogo. Em 06–08/11/2026 vários se chamavam "DELTA REIGN LEGAL" e, no maior
  deles (494 jogadores, 07/11), o deck mais jogado foi o Mega Rayquaza (70), da coleção nova. Com a regra de D-036 esses torneios
  ficavam na época anterior até 20/11, misturados com o meta antigo. O começo é o dia do lançamento nos EUA porque o Limitless dá a
  data em UTC e a coleção chega ao jogo às 17h ou 18h UTC da véspera (D-036): os torneios da véspera, quase todos antes da chegada,
  ficam na época anterior; os poucos do dia do lançamento que começaram antes da chegada (nenhum na Delta Reign) ficariam na nova.
  Os grandes eventos continuam com a validade em torneio. Código: `colecoes.inicio_online`, `analises.torneios_da_fonte(epoca=)`.
- **D-050 · Deck sem listas de torneio: nome provisório pelo Pokémon que mais causou dano** (10/11/2026, v2026.11.10-2; R2 da
  pesquisa de outros apps, ideia do Full Bench). *Por quê:* o NB2 só escolhe entre decks com listas importadas; no começo de uma
  coleção ele chama um deck novo de outro conhecido (Talonflame Dusknoir virou "Tera Box" em 09/11). Regra escolhida pela medição
  (`EVIDENCE.md`): só quando o atacante principal não está em nenhuma lista (5% ou mais); critérios mais largos (atacante fora da
  lista do deck escolhido; vários Pokémon vistos fora dela) disparavam em 10 a 22 partidas do Pedro, quase sempre por engano (cartas
  de suporte como Fan Rotom e cartas do adversário nas "vistas"). Sempre marcado "incerto" (D-042).
## Pesquisado e descartado (não refazer sem motivo novo)
- **Logs de outros jogadores como fonte:** o Full Bench guarda logs privados (só estatísticas somadas públicas, sem API) e o Dead Draw
  tem poucas dezenas de replays públicos, muitos fora do Standard. Aproveitado do Full Bench: impressão digital, validação do log,
  "quem exportou", ideias do modo automático.
- **Fontes japonesas** (City League, CardRush, Players Club) = "Standard JP", outro conjunto de cartas e nomes em japonês: não misturar.
  PokeData só como plano B do RK9.
- **Acesso pelo celular / painel na rede:** descartado pelo Pedro (D-002, D-003).
- **Algoritmos para montar listas** (genético, branch and bound): sem modelo causal do valor de cada carta, otimizariam correlação.
  Programação linear para o equilíbrio exigiria scipy (o *fictitious play* basta).
- **Ler a tela para montar o próprio log:** ver D-005.
