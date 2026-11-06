# Registro de decisões

> Atualizado em 06/11/2026. Decisões técnicas e de produto, numeradas. **Não reaproveite números**; para mudar uma decisão,
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
- **D-019 · Identificação do deck: NB2 com reserva pelos ícones e pelo palpite do dano** (02/11, exp. 2).
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
