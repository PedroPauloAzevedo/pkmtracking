# Stall, controle (lock), disrupção e mill

> Atualizado em 06/11/2026. Conceitos e observabilidade: `STRATEGIC_CONCEPTS.md`. Evidência: `experiments/p0_viabilidade_estrategica.py`.
> Nada aqui está implementado no Coletor. Lista de cartas por categoria = **lista de trabalho** (muda a cada coleção; conferir na
> biblioteca de cartas e em `docs/regras-standard.md`).

> **Ferramentas prontas, não aplicadas (decisão do Pedro em 06/11/2026: poucos jogos):** funções em `tools/estrategia.py`,
> roteiro `experiments/p_estrategia.py <cópia> <p1..p7|todos>`, com trava de amostra mínima (MINIMOS no roteiro); testes em
> `tests/test_estrategia.py` (dados sintéticos).

## 1. Definições (comunidade) e o que o log mostra
| Estratégia | Definição | O que fica no log | O que **não** fica |
|---|---|---|---|
| **Stall** | Atrasar a corrida: impedir nocautes, tirar alvos, curar, sobreviver; vencer por deck acabado ou pelo tempo | nocautes (e a falta deles), cura (`healed`), dano prevenido (`was prevented`, `did not affect`), recuos | se o adversário **podia** ter nocauteado |
| **Control / lock** | Restringir opções do adversário por vários turnos (habilidades, itens, recuo, recursos) | a carta/estádio de bloqueio sendo jogado e ficando em jogo; o que o adversário jogou depois | o que o adversário **deixou** de jogar por causa do bloqueio (a mão dele é escondida) |
| **Disruption** | Interferência pontual (ver §2) | a jogada e o efeito visível (cartas embaralhadas, Energia descartada, Pokémon puxado) | o conteúdo da mão perdida do adversário (só o número) |
| **Mill** | Tirar cartas do baralho do adversário até ele não poder comprar | descarte do topo do baralho do adversário; fim "não pôde comprar" | — |

## 2. Classificação da disrupção (categoria → exemplos de cartas → sinal no log)
| Categoria | Exemplos (Standard recente; conferir) | Sinal no log | Medido no p0 (83 partidas) |
|---|---|---|---|
| Mão | Iono, Judge, Unfair Stamp, Xerosic's Machinations, Eri | `played X` + `shuffled N cards into their deck` / `discarded N cards` do adversário | 68 jogadas, em 47 partidas |
| Energia | Crushing Hammer, Enhanced Hammer | `- Basic X Energy was discarded from Y` em sublinha | 45 jogadas, em 18 partidas |
| Banco (puxar alvo) | Boss's Orders, Prime Catcher, Counter Catcher | troca de Ativo do adversário | 103 jogadas, em 54 partidas |
| Habilidade (bloqueio) | Team Rocket's Watchtower, Path to the Peak (Estádios) | Estádio jogado/em jogo | 33 jogadas, em 28 partidas |
| Ferramenta / Estádio | Lost Vacuum, Tool Scrapper | ferramenta/estádio removido | 0 nos dados |
| Item lock, recuo | cartas com efeito contínuo (ex.: aumento de custo de recuo) | a carta em jogo; efeito pela regra da carta | não medido |
| Ordem/composição de recursos | colocar cartas no fundo/topo do baralho | `put N cards on the bottom/top` | não medido |
A lista do p0 é **incompleta** (subcontagem). "Banco (puxar)" é seleção de alvo, não só disrupção — separar nas análises.

## 3. Indicadores e métodos
- **Frequência e momento** de cada categoria (por turno, por lado). Contagem — **O**.
- **Duração de um bloqueio**: turnos em que a carta/estádio de bloqueio ficou em jogo. **I** (efeito = regra da carta; o log mostra
  presença, não o que foi impedido).
- **Desenvolvimento do adversário depois da disrupção** (P5): nos k turnos seguintes, nº de jogadas, evoluções, Energias ligadas,
  ataque feito (sim/não), prêmios pegos. **O** para os fatos, **I** para "travou".
- **Tamanho da mão do adversário** antes/depois (Iono, Judge revelam o número): **O** nos momentos em que o log diz.
- **Stall:** sequência de turnos do adversário sem nocaute com ataque feito; dano prevenido/curado por turno. **O/I**.
- **Mill:** cartas do baralho do adversário descartadas por turno; tempo até o baralho acabar = (cartas no baralho) / (ritmo de
  compra + mill) — **I** (o tamanho do baralho do adversário é inferível: 60 − cartas vistas − prêmios − mão conhecida em tamanho).
  P(vitória por deck acabado) só com modelo de ritmo; **sem nenhum caso nos dados** (0 de 83).
- **Recursos para manter a estratégia** (stall/lock/mill): cópias das cartas-chave restantes (hipergeométrica condicional, como em
  `PRIZE_ANALYSIS.md` §3) — só para quem exportou.

## 4. Experimentos propostos (P5, P6)
| | Pergunta | Hipótese | Dados e inclusão | Método | Métricas | Separação / vazamento | Limitações |
|---|---|---|---|---|---|---|---|
| **P5** | A disrupção está associada a interrupção no desenvolvimento do adversário? | Depois de disrupção de mão, menos jogadas/ataques nos 1–2 turnos seguintes do adversário | turnos do adversário com/sem disrupção no turno anterior; mesmos decks e mesma faixa de turno | comparação **pareada por estado** (turno, D(t), deck dos dois lados, tamanho da mão quando conhecido); diferença com bootstrap agrupado por partida | diferença média de jogadas/ataques; faixa de 95% | descritivo; se prever, separação no tempo | **causalidade reversa** (quem joga Iono está atrás), seleção (só joga quando o adversário tem mão boa), regressão à média da mão; associação, nunca "a carta causa" |
| **P6** | Há partidas de stall/mill e como terminam? | Raras nos dados atuais | todas; marcar: deck acabado, turnos longos sem nocaute, mill do adversário | contagem; tempo até o fim com censura pela desistência | nº de casos, turnos, motivo do fim | — | **0 deck-out em 83**; precisa de mais dados ou de partidas de decks de controle |

## 5. Associação temporal não é causa (checklist antes de qualquer frase sobre "efeito" da disrupção)
1. Quem decide jogar a carta escolhe o momento (seleção): compare com momentos **parecidos** em que ela não foi jogada.
2. A disrupção é mais jogada por quem está atrás → partidas perdidas concentram disrupção (causalidade reversa).
3. A mão do adversário depois de Iono/Judge depende do tamanho antes — controle pelo tamanho (quando revelado).
4. Turnos seguintes "piores" podem ser regressão à média (um turno ótimo seguido de um comum).
5. Muitos indicadores × muitas categorias → correção de múltiplos testes (`sa_tools.holm`/`benjamini_hochberg`).
6. Diga sempre: descrição × associação × previsão × causa (SKILL.md §3). Com os dados do Coletor, no máximo **associação**.
