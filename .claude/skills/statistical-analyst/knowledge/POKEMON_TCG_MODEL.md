# O Pokémon TCG visto pela matemática (e o que os dados do Coletor mostram ou não)

> Atualizado em 06/11/2026 (seção 7: representação estratégica). Regras completas: `PROJECT_KNOWLEDGE/02_BUSINESS_RULES/STANDARD_AND_GAME_RULES.md` e
> `docs/regras-standard.md`. Formato do log: `PROJECT_KNOWLEDGE/02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md`. Só formato Standard (D-001).

## 1. Fatos do jogo que entram nas contas
- Deck de 60; até 4 cópias por nome (Energia Básica sem limite); 1 ACE SPEC por deck; mão de 7; sem Pokémon Básico = mulligan
  (o adversário pode comprar 1 carta a mais por mulligan — não modelado); 6 prêmios do topo depois da mão.
- Os dois jogadores compram no começo do próprio turno, inclusive quem começa. Quem começa não ataca nem joga Apoiador no 1º turno;
  ninguém evolui no próprio 1º turno → começar e ir em segundo são **jogos diferentes** nas aberturas e no ritmo (o programa separa).
- Vitória por prêmios (6), adversário sem Pokémon em jogo ou sem cartas para comprar.
- Torneios grandes (Labs/RK9): suíço em **partidas melhor de 3 com tempo** (empates existem, ~13%), depois corte. TCG Live Ladder:
  **jogo único**. Torneios online do Limitless: formato da partida não fica guardado no banco (lacuna G8).

## 2. Por que "probabilidade de ter a carta" não é uma conta simples
O que muda a chance real depois da mão: buscas (Pokémon, Treinador, Energia), compras extras, trocas de mão (Judge, Iono, Unfair
Stamp — a mão volta ao deck e é embaralhada), descarte do topo, cartas presas nos prêmios (que depois saem pelos nocautes) e
**decisões** (o que buscar depende do que está na mão). A hipergeométrica do programa responde "sem nada disso" (piso). Cuidado com a pergunta: Nest Ball, Ultra Ball e Buddy-Buddy
Poffin **buscam Pokémon** — uma não traz a outra; elas fazem o mesmo serviço. "Ter Poffin" e "ter alguma carta que monta o
Banco" são contas diferentes (a segunda soma as cópias do grupo: lacuna G15). Para
"montar o tabuleiro no turno 2" é preciso simular regras de cartas específicas (lacuna G1) — e cada carta modelada é uma premissa.

## 3. Cinco tipos de probabilidade (não misturar)
| Tipo | Exemplo no Coletor | Pergunta que responde |
|---|---|---|
| Exata | `probabilidades.carta` | Com sorteio puro, qual a chance? |
| Condicional ao estado | (não há na tela) | Com o que já se sabe nesta partida, qual a chance? |
| Por simulação | `e1` (conferência) | Com regras que não têm fórmula fechada, qual a chance aproximada? |
| Histórica | taxas de Meta, Desempenho | Com que frequência aconteceu? (n, período, população) |
| Preditiva de modelo | confronto ajustado, NB2 | Qual a melhor previsão para um caso novo? (validada fora da amostra?) |

## 4. Populações diferentes
- **Topo dos torneios** (listas): só os N primeiros (padrão 64; o Pedro usa 256) → taxas infladas (+4 a +6 pp, achado 1).
- **Campo dos torneios** (placar de todos): sem lista; serve para taxas do deck e matchups.
- **Ladder do TCG Live** (partidas pessoais e de amigos): jogo único, adversários de nível variado, pouco volume (dezenas).
- **Épocas:** cada coleção nova muda o meta (`tracker/colecoes.py`); juntar épocas mistura metas diferentes.

## 5. Observabilidade dos logs (o que dá e não dá para reconstruir)
Dá (conferido em `EVIDENCE.md`): mesa, dano, nocautes, prêmios pegos por quem exportou (com nome), mão de quem exportou (51/51) e do
adversário nos momentos em que o log revela o tamanho (58/58), descartes.
Não dá ou só em parte: as cartas da mão do adversário (só as jogadas/reveladas), os prêmios do adversário (sempre "A card", 0/235),
a ordem do deck, Energias ligadas por habilidade (parte não aparece: 73 de 754 ataques com Energia "de menos"), **intenção** (o que
a pessoa podia ter feito e não fez), tempo de cada decisão. Consequência: "estimar o resultado de uma jogada alternativa" exige um
modelo do estado escondido (mão e deck do adversário) — o NB2 sobre as cartas vistas é um começo — e qualquer resposta é
condicional a esse modelo.

## 6. Causalidade
Tudo no Coletor é observacional. Uma carta jogada **por causa** do estado (ex.: buscar para virar uma partida perdida) aparece
associada a derrota sem causá-la; partidas longas mostram mais cartas (viés de duração); jogadores melhores escolhem listas
diferentes (confundimento). Para dizer "essa decisão ajuda", seria preciso comparar situações iguais em que a decisão variou
(pareamento por estado, experimento do próprio jogador), e mesmo assim com cautela.

## 7. Representação estratégica (06/11/2026)
O jogo como **corrida de prêmios com informação escondida**: estado = (prêmios restantes dos dois lados, mesa com PS/dano/Energia/
valor de prêmio de cada Pokémon, mão e baralho de cada um, Estádio, vez). Valor de prêmio: ex 2, Mega ex 3, demais 1 (cartas podem
alterar). Para quem exportou o log, conhecidos: mesa, a própria mão e os próprios prêmios **depois** de pegos; do adversário, só o
revelado. Conceitos (prize mapping, racing, checking, trade, stall, lock, disrupção, mill, sequência) e o que dá para medir:
`STRATEGIC_CONCEPTS.md` (matriz de observabilidade); matemática: `PRIZE_ANALYSIS.md`, `CONTROL_AND_DISRUPTION.md`,
`DECISION_ANALYSIS.md`. Fatos medidos (p0, 83 partidas): 55% terminam por desistência, 0 por deck acabado; a rota de prêmios
executada é observável; a contagem de prêmios no turno 3–6 quase não diz quem vence.

## 8. Sequência completa de um ataque (roteiro dos juízes) e o que o log mostra
Fonte: "Roadmap to Pokémon TCG attacks", Karin Siehs, rev. nov/2024, em Judge Ball (registro em `RESEARCH_REGISTER.md`). Resume o
Rulebook (SV8) e as decisões do Compendium; o resumo do Rulebook de 2026 já está em `docs/regras-standard.md` (ordem do ataque e do
dano, Checkup). O que o roteiro **acrescenta** é o que vem depois do dano:
0 escolher o ataque → A anunciar → B efeitos que cancelam → C Confuso → D escolhas (sem executar) → E requisitos → F efeitos antes do
dano → G calcular o dano (base → efeitos no atacante → Fraqueza → Resistência → efeitos no defensor; base ≤ 0 pula para H) →
**colocar o dano** → H efeitos do ataque (inclusive os pendentes de D) → I efeitos disparados pelo ataque → J checar nocautes →
K efeitos disparados pelo nocaute → **L executar os nocautes: 1 descartar os nocauteados; 2 o adversário pega os prêmios dele
primeiro; 3 você pega os seus; 4 o adversário troca o Ativo; 5 você troca o seu** → M efeitos disparados por executar nocautes
(volta a J) → N checar vitória → fim do ataque → efeitos de "fim do turno" → turno acaba → Checkup.
Notas do roteiro: a checagem de nocautes vale para **todos os Pokémon ao mesmo tempo**; as condições de vitória também, para os dois
jogadores, depois que a sequência de efeitos disparados termina.
**Conferido nos logs (a12, 83 partidas):** a ordem do dano aparece no `Damage breakdown` (Fraqueza = dobro do subtotal com os efeitos
do atacante, 36/36; Resistência depois deles, 7/7); nos nocautes ao mesmo tempo, o adversário de quem joga pega primeiro (8/8);
vários nocautes do mesmo dono viram um só "took N" (10/12). **Uso:** (a) o replay e o leitor podem confiar nessa ordem das linhas;
(b) o "dano necessário" de uma rota de prêmios (`PRIZE_ANALYSIS.md`) deve aplicar a Fraqueza **depois** dos bônus do atacante — um
bônus de +30 vale +60 contra um Pokémon com Fraqueza; (c) o `Damage breakdown` mostra a Fraqueza/Resistência real do defensor e os
bônus de dano usados (Black Belt's Training, Premium Power Pro, Brave Bangle) — dado observável que o Coletor ainda não lê (G24).
