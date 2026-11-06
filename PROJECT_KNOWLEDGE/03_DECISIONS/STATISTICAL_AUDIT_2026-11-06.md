# Auditoria matemática e estatística (Fase 3 da Skill "Statistical Analyst")

> Atualizado em 06/11/2026. Código auditado: commit `76a2005` (versão 2026.11.05-6). Parte do inventário
> (`STATISTICAL_INVENTORY_2026-11-06.md`). **Nenhum método do programa foi mudado**: cada achado termina numa recomendação, que só
> vira mudança com medição contra o atual (D-017) e decisão do Pedro.
> Dados: cópia de teste com os dados do Pedro (33 torneios de 28/08 a 01/11/2026; 44.651 partidas de torneio; 144.060 linhas de listas).
> Scripts: `.claude/skills/statistical-analyst/experiments/a1..a6` (só leem; resultado gravado em `experiments/resultados/*.json` com
> versão, semente e impressão dos dados). Ferramentas novas: `.claude/skills/statistical-analyst/tools/sa_tools.py` (testadas).

## Placar
| # | Hipótese levada à auditoria | Veredito | Gravidade |
|---|---|---|---|
| 1 | Análises com listas usam só quem foi bem (viés de seleção) | **Comprovado** | Alta (leitura das telas) |
| 2 | k = 24 do confronto ajustado ficou ruim | **Descartado** (k = 16 e 24 empatam) | — |
| 3 | Confronto ajustado com poucos jogos é pior que 50% | **Sem diferença clara** (nem melhor nem pior) | Baixa |
| 4 | A regra de identificação do deck do programa é a melhor | **Refutado**: a reserva pelos ícones piora o acerto; e o e2 vaza o teste | Média |
| 5 | Muitos testes sem correção dão falsos achados | **Em parte**: variantes sim (7 marcados, 2 sobrevivem a Holm); cartas não (o freio já zera tudo) | Média |
| 6 | Partidas do mesmo jogador não são independentes | **Descartado** nos torneios (ICC ≈ 0) | — |
| 7 | "Seu resultado × meta" mistura 1 jogo com melhor de 3 | **Comprovado** (4,35 pp em média; até 15 pp) | Média |
| 8 | Efeito das cartas acrescenta previsão ao deck sozinho | **Não demonstrado** (−0,0007, faixa contém 0) | Média (expectativa da tela) |
| 9 | O e2 ainda mede o que diz medir | **Refutado** (coluna "atual" mudou de significado e usa dados do teste) | Média (evidência) |
| 10 | Empates e o lado do jogador 1 | **Descrito**: 13,3% de empates no Labs (1,0% online); no Labs o jogador 1 vence 72% das decididas | Baixa (modelos simétricos) |

> **Revisão de 06/11/2026 (rodada de hardening, `STATISTICAL_HARDENING_2026-11-06.md`):** o achado 6 vale **só para jogadores com
> lista**; com todos os jogadores o ICC é +0,063 [+0,059; +0,068] (a7). O achado 4 foi confirmado com cartas vistas de forma realista
> (a8), com a ressalva de que a regra do programa é melhor para os decks raros. O texto abaixo fica como estava (histórico).

---

## Achado 1 — Listas só do topo: as análises por carta e por versão olham só para quem foi bem
1. **Problema:** "Uso de cartas", "Efeito de cada carta", "Versões do deck", "Carta × matchup" e o prior do NB2 usam só jogadores com
   lista importada. As listas vêm só do topo (`listas_top`, padrão 64; o Pedro usa 256).
2. **Contexto:** `limitless.importar(..., listas_top)`, `importar_online`; leitura em `regressao.dados`, `variantes.variantes`,
   `analises._uso_cartas`, `cartas_matchups`, `decks._modelo_nb`.
3. **Método:** placar final (V/(V+D+E)) de quem tem e de quem não tem lista, por fonte e por deck (a1); taxa real × esperada pelos
   confrontos no teste do exp. 10 (a3).
4. **Fundamento:** se a amostra é escolhida pelo resultado (ficar no topo), qualquer taxa dentro dela fica inflada, e diferenças entre
   escolhas de cartas podem encolher ou mudar de sinal (seleção pelo resultado = "viés de colisor").
5. **Dados:** 10.127 jogadores; 5.695 listas.
6. **Resultado:** grandes eventos: com lista 61,9% × sem lista 50,3%; online: 52,1% × 27,9%. Nos 12 decks mais jogados, a taxa só com
   lista é **4,0 a 6,1 pp maior** que a taxa de todos. No teste do exp. 10, quem tem lista venceu 57,7% contra 51,4% esperados pelos
   confrontos (já sem empates) — 6,3 pp acima; outros 4,7 pp vêm só da convenção "empate = não-vitória" do confronto.
7. **Confiabilidade:** contagem direta, sem modelo; alta. O tamanho do efeito sobre **cada** carta não foi medido (precisaria das listas
   de todos, que não existem nos torneios importados).
8. **Interpretação:** "Vitória com / sem" e as taxas das versões descrevem o topo, não o deck. Uma carta usada por quem foi bem não
   fica provada boa; e as taxas do topo são mais altas que a do deck no campo.
9. **Recomendação:** (a) aviso nas telas: "listas só dos N primeiros de cada torneio"; (b) mostrar ao lado a taxa do deck no campo
   inteiro (já existe em Meta); (c) para estudo, importar todas as listas de alguns torneios online (a API entrega) e medir o viés por
   carta. Nenhuma mudança feita.
10. **Referências:** a1, a3; inventário M7, M9, M11, M12, M8.

## Achado 2 — k = 24 do confronto ajustado continua bom
- **Método:** a2 — mesmo desenho do exp. 3 (70/30 no tempo), todos os k no teste, diferença pareada com bootstrap por torneio
  (10 torneios de teste, 2.000 repetições, semente 11), usando `estrategia.confrontos_ajustados` do programa.
- **Resultado:** log-loss no teste: k = 12: 0,6778; 16: 0,6776; **24: 0,6778**; 32: 0,6782 (chute 0,6931). k16 − k24 = −0,0002
  [−0,0010; +0,0010]. A curva é plana entre 12 e 32. **Calibração** (as duas pontas de cada partida): erro médio 1,5 pp; só as
  previsões abaixo de 20% ou acima de 80% (30 de 10.212) erram, com poucos casos.
- **Também visto num teste da Skill (script de rascunho, não guardado):** o k que o e3 escolhe muda com o ponto de corte no tempo
  (64, 32, 16 e 16 com 50, 60, 70 e 80% dos torneios no treino).
- **Interpretação:** o e3 escolher 16 é ruído da escolha; não há motivo para trocar o k. Confronto ajustado: **E** confirmado.
- **Recomendação:** manter k = 24; registrar em `EVIDENCE.md` que 12–32 empatam.

## Achado 3 — Com poucos jogos, o confronto ajustado empata com o chute de 50%
- **Resultado (a2):** confrontos com < 10 jogos no treino (1.304 partidas de teste): ajustada − 50% = +0,0053 [−0,0083; +0,0214]
  (sem diferença clara); com ≥ 30 jogos: −0,0188 [−0,0265; −0,0050] (melhor, provável).
- **Confiabilidade:** só 10 torneios no teste; o bootstrap por torneio com 10 grupos é aproximado.
- **Interpretação:** com poucos jogos a ajustada não piora, mas também não acrescenta informação (a força geral do deck sozinha
  quase não prevê: 0,6921). Na tela, a célula com poucos jogos já vem marcada.
- **Recomendação:** no texto da opção "taxa ajustada", dizer que abaixo de ~10 jogos ela vale como "perto de 50%". Sem mudança de conta.

## Achado 4 — Identificação do deck: a reserva pelos ícones atrapalha
1. **Problema:** o programa usa o NB2 quando a confiança é ≥ 0,5 e, abaixo disso, os ícones (`decks.identificar`). Essa regra nunca foi
   medida sem vazamento.
2. **Método:** a4 — funções do programa (`identificar`, `identificar_nb`, `_identificar_por_icones`) com os modelos montados **só com os
   torneios de treino** (o `banco.consultar` de `decks` é filtrado); 1.500 listas de teste por linha; cartas sorteadas; semente 7.
3. **Resultado:**
   | Cartas vistas | Ícones | NB2 | Programa | NB2 decide em | Acerto quando decide |
   |---|---|---|---|---|---|
   | 2 | 19,0% | **63,6%** | 51,2% | 62,8% | 79,5% |
   | 3 | 35,3% | **74,9%** | 69,7% | 83,2% | 82,8% |
   | 5 | 52,3% | **84,4%** | 83,3% | 94,7% | 87,5% |
   | 8 | 69,4% | **89,8%** | **89,8%** | 98,4% | 90,9% |
   | 12 | 74,4% | 91,8% | **92,0%** | 99,4% | 92,3% |
   **Calibração do NB2:** erro médio 3,1 pp; levemente otimista no topo (diz 98,2%, acerta 95,5%; diz 85%, acerta 80%).
4. **Confiabilidade:** cartas sorteadas, não as vistas de verdade; o cadastro de arquétipos (ícones) usa todos os torneios (pequeno
   vazamento a favor dos ícones); quando os ícones não decidem, o programa ainda tenta o palpite pelo dano, que este teste não mede.
5. **Interpretação:** quando o NB2 está inseguro (< 0,5), ele ainda acerta mais que os ícones; trocar pelos ícones custa até
   12 pp com 2 cartas.
6. **Recomendação (precisa de decisão e versão nova):** testar "NB2 sempre que houver modelo; ícones só sem modelo" contra a regra
   atual também com cartas vistas de verdade (partidas em que o deck do adversário é conhecido: o mesmo jogo pelos dois lados, ou
   listas de Meus decks ligadas). Corrigir o e2 (ver achado 9).
7. **Revisão (06/11, a8):** com cartas vistas de forma realista e sem nenhuma informação do teste no treino (nem o cadastro de
   ícones, que aqui vinha de todos os torneios — efeito medido ≤ 0,3 pp), o NB2 ganha da regra do programa na acurácia nos turnos 1–2
   (+5,9 e +1,7 pp), mas perde no F1 macro (0,53 × 0,58 no turno 2): a reserva pelos ícones ajuda os decks raros. A confiança do NB2
   é exagerada (inclinação 0,56), apesar do ECE de 3 pp. Ver `STATISTICAL_HARDENING_2026-11-06.md`, D.2 e D.3.

## Achado 5 — Muitos testes ao mesmo tempo
- **Método:** a5 — `variantes.variantes` e `regressao.efeito_cartas` como estão, 12 decks mais jogados; Holm e Benjamini-Hochberg.
- **Resultado:** variantes: 87 testes, a tela marca 7 "diferenças prováveis"; 12 têm p < 0,05 (o acaso daria ~4,4); sobrevivem a
  Holm **2**, a Benjamini-Hochberg (q < 0,10) **7**. Efeito das cartas: 392 cartas, **0** "efeito provável" (o freio L2 = 300 deixa
  todas as faixas largas).
- **Interpretação:** nas variantes, a maioria das marcas resiste a uma taxa de falsos achados de 10%, mas só 2 resistem ao critério
  rígido; as marcas devem ser lidas como "vale olhar". Na tela de cartas não há falso positivo — mas também nunca há achado.
- **Recomendação:** nas variantes, marcar com Benjamini-Hochberg (q < 0,10) por deck; no efeito das cartas, rever o texto da tela
  (achado 8).

## Achado 6 — Partidas do mesmo jogador: independência se sustenta nos torneios
- **Método:** a1 — ICC (estimador de ANOVA) dos resultados W/L dentro de cada jogador com lista (5.513 jogadores, 7,6 partidas cada).
- **Resultado:** ICC = −0,015 → efeito de desenho 1,00.
- **Interpretação:** o sistema suíço junta quem está com o mesmo placar, e isso anula a "mão quente" de cada jogador. As faixas de
  Wilson e os valores-p por partida **não** estão estreitos demais por esse motivo. Hipótese descartada; vale só para os torneios (no
  Ladder não foi medido).
- **Revisão (06/11, a7 — `STATISTICAL_HARDENING_2026-11-06.md`, D.1):** a conclusão acima foi tirada de uma amostra escolhida pelo
  resultado (só quem tem lista = o topo). Com faixa por bootstrap de jogadores: com lista −0,015 [−0,020; −0,011]; sem lista +0,034;
  **todos +0,063 [+0,059; +0,068]; Labs +0,096** (efeito de desenho até ~1,6); online ≈ 0. Ou seja: independência razoável nas
  análises que usam só listas (cartas, versões, regressão); **não** nas que juntam todas as partidas de torneio (meta, matchups,
  confronto ajustado). Ladder: sem poder para concluir; jogos dentro da melhor de 3: não mensurável. Ausência de evidência não prova
  independência.

## Achado 7 — "Seu resultado × meta": 1 jogo contra melhor de 3
- **Problema:** `analise_pessoal` põe ao lado da sua taxa (jogos únicos do Ladder) a taxa do confronto nos torneios (partidas melhor de 3).
- **Fundamento:** com chance q por jogo, a melhor de 3 vale q²(3 − 2q): 55% → 57,5%; 60% → 64,8%; 65% → 71,8% (conferido por
  simulação nos testes da Skill).
- **Resultado (a6):** 128 confrontos do Labs com ≥ 30 partidas: a taxa da partida fica em média **4,35 pp** mais longe de 50% que a taxa
  por jogo equivalente; nos confrontos extremos, ~10 pp (Dhelmise × N's Zoroark: 12,3% por partida ≈ 21,9% por jogo).
- **Confiabilidade:** a fórmula supõe jogos independentes e ignora empates (partidas por tempo). Os torneios online **não guardam** se
  foram melhor de 1 ou de 3 — lacuna.
- **Recomendação:** converter a referência do meta para "por jogo" antes de comparar (ou dizer na tela que é por partida melhor de 3).
  Mudança de tela: precisa de decisão.

## Achado 8 — Efeito das cartas não acrescenta previsão
- **Método:** a3 — exp. 10 com as funções do programa + diferença pareada M2 (peso 300) − M1 (deck sozinho), bootstrap por torneio e
  por jogador (2.000 repetições, semente 21).
- **Resultado:** −0,0007 [−0,0020; +0,0003] por torneio; −0,0007 [−0,0018; +0,0004] por jogador (1.044 jogadores). O M1 ganha do M0
  com folga (−0,0252 [−0,0362; −0,0065]), mas esse ganho é em boa parte o achado 1 (quem tem lista vence mais).
- **Interpretação:** a regressão é muito melhor que o "com/sem" bruto (D-021 continua certo nisso), mas com os dados de hoje não há
  sinal de que o número de cópias de uma carta mude a chance de vencer — ou o sinal é pequeno demais para os ~6 mil jogos, ou o viés
  de seleção o apaga.
- **Recomendação:** dizer na tela que, com os dados atuais, nenhuma carta mostra efeito claro; reavaliar quando houver listas de
  todos os jogadores (achado 1, item c).

## Achado 9 — O experimento 2 mudou de significado
- **Problema:** `e2_identificar_deck.atual()` chama `decks.identificar`, que deixou de ser "só ícones" na 2026.11.02-1 e passou a usar
  o NB2 montado com **todo** o banco (inclui as listas de teste). O e2 continua dizendo no cabeçalho que compara com os ícones.
- **Evidência:** e2 de 06/11, coluna "atual" com 12 cartas 95,7% contra NB2 92,0% e ícones sozinhos 74,4% (a4).
- **Recomendação:** corrigir o e2 (filtrar o banco como o a4 ou chamar `_identificar_por_icones`). É código de teste: pedir ao Pedro.
  Lição geral para a Skill: **um experimento que chama a função de produção precisa ser revalidado quando a função muda**.

## Achado 10 — Empates e o lado do jogador 1 (descrição)
- Empates: Labs 4.232 de 31.893 partidas (13,3%; muitos são empates combinados no fim do suíço); online 122 de 12.758 (1,0%).
  As taxas contam empate como não-vitória (convenção do Limitless): um deck que nunca perde e empata muito aparece abaixo de 100%.
- No Labs o jogador 1 venceu 19.942 e perdeu 7.719 (72% das decididas), em todas as rodadas; no online, 50%. Provavelmente a ordem da
  página de pareamentos. Os modelos atuais são simétricos e não são afetados, mas **qualquer tabela vista por um lado só** (ex.: uma
  calibração) sai torta — a primeira versão da calibração no a2 saiu assim e foi corrigida contando as duas pontas.

## Conferido e sem problema
Hipergeométrica, mulligan e "duas cartas" (e1 refeito; soma 1; extremos); Wilson (valores de referência); Bradley-Terry (forças
conhecidas recuperadas); equilíbrio (pedra-papel-tesoura, deck dominante; folga informada); teste de duas proporções; "Uso de cartas"
rápido = lento (e6); replay (`EVIDENCE.md`). Observação menor: `probabilidades.carta` devolve zeros em silêncio para uma entrada
impossível (carta Básica com mais cópias que o total de Básicos).
