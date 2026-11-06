# Sequência, gestão de recursos e análise de decisões

> Atualizado em 06/11/2026. Conceitos e observabilidade: `STRATEGIC_CONCEPTS.md`. Ligado à lacuna G12/G13 (`GAPS_AND_ROADMAP.md`) e
> à tela Decisões do Coletor (`analises.decisoes`, classe B; F para causa). Nada aqui está implementado no Coletor.

> **Ferramentas prontas, não aplicadas (decisão do Pedro em 06/11/2026: poucos jogos):** funções em `tools/estrategia.py`,
> roteiro `experiments/p_estrategia.py <cópia> <p1..p7|todos>`, com trava de amostra mínima (MINIMOS no roteiro); testes em
> `tests/test_estrategia.py` (dados sintéticos).

## 1. O que é "decisão" nos dados
O log é a **trajetória executada**: estado → ação → estado. Para avaliar uma decisão seria preciso (a) o conjunto de ações
possíveis naquele estado, (b) o valor de cada uma. Nenhum dos dois está no log:
- (a) as ações possíveis dependem da mão (conhecida só para quem exportou), do baralho (ordem desconhecida) e das regras de cada carta;
- (b) o valor depende do que o adversário faria (mão e baralho escondidos) → só sob um **modelo**.
Por isso, sem modelo: descrever padrões e associá-los a resultados. Com modelo: estimativas **condicionais ao modelo** (dizer qual).

## 2. Sequencing (ordem das ações no turno)
**Definição (comunidade):** a ordem em que se joga muda o resultado (ex.: comprar antes de buscar, ligar Energia por último, jogar
Apoiador depois de ver as buscas). Guias citados em `RESEARCH_REGISTER.md` tratam isso como otimizável dentro do turno.
**O que dá para medir (O):** ordem das linhas no turno de quem exportou (mediana 8 ações por turno, p90 19 — p0); posição relativa de
compra × busca × Energia × Apoiador; cartas buscadas e descartadas. **Padrões** (ex.: "Energia antes da compra") são contáveis.
**O que não dá (N):** se a outra ordem era possível e melhor — a mão no momento é conhecida (quem exportou), mas o que as buscas
encontrariam depende do baralho.
**Métodos:** contagem de padrões de sequência (n-gramas de tipos de ação por turno); associação com o resultado do turno (ataque
feito, nocaute) ou da partida, controlando turno, ordem (começou ou não), deck e D(t); comparação pareada por estado.

## 3. Gestão de recursos e thinning
- **Recursos:** Energias ligadas/descartadas, cartas de busca usadas, Apoiadores por turno, cartas recuperáveis (Night Stretcher etc.).
  Contagem **O** (quem exportou); do adversário, só o que ele jogou.
- **Thinning:** tirar cartas do baralho aumenta a chance das restantes. Efeito exato pela hipergeométrica: ao tirar j cartas
  irrelevantes de um baralho de N com m cópias da carta X, P(comprar ≥1 X em k compras) passa de 1 − C(N−m,k)/C(N,k) para
  1 − C(N−j−m,k)/C(N−j,k). Ganho pequeno por carta (guias citam ~1–2 pp no 1º turno); calculável com `probabilidades.hipergeometrica`.
  Prêmios entram no N enquanto não forem conhecidos (ver `PRIZE_ANALYSIS.md` §3).
- **Preservação de opções:** quantas saídas (cartas-chave) ainda existem no baralho+prêmios — hipergeométrica condicional; **I**.

## 4. As quatro rotas/decisões (vale para qualquer decisão, não só prêmios)
| Nível | Pergunta | Dados | Classe máxima com o Coletor hoje |
|---|---|---|---|
| Matematicamente possível | Existia uma sequência de ações que vencia? | regras + estado completo | N (estado do adversário escondido) |
| Executável com recursos conhecidos | Com a mão e a mesa de quem exportou, o que dava para fazer? | mão (quem exportou), mesa, regras das cartas | I (exige motor de regras de cada carta) |
| Robusta ao adversário | Considerando respostas plausíveis, qual era melhor? | + modelo do adversário (NB2 + listas típicas, determinização/ISMCTS) | I sob modelo, nunca observado |
| Executada | O que foi feito? | log | **O** |
Nunca descrever a executada como "erro" sem mostrar, sob um modelo declarado, que outra opção executável era melhor.

## 5. Métodos (escolher pelo tipo de pergunta)
| Pergunta | Método | Ferramenta existente | Premissas |
|---|---|---|---|
| Chance de ter X agora / depois de thinning | probabilidade exata condicional | `probabilidades.hipergeometrica` | sorteio sem reposição; zonas bem definidas |
| Chance com regras de carta (buscas, compras) | Monte Carlo | (nenhuma no programa; e1 só confere a exata) | cada carta modelada é uma premissa (G9) |
| Melhor ação dado o estado | busca/otimização sobre conjuntos de informação | não existe | modelo do adversário; custo alto |
| Padrão associado a vitória | comparação pareada por estado; logística com controles | `sa_tools.diferenca_pareada`, `bootstrap_agrupado`, `regressao.ajustar` | observacional: associação |
| "O padrão causa vitória?" | só com desenho: experimento do próprio jogador (alternar a ordem por sorteio) ou pareamento rigoroso | — | sem isso, **não afirmar** |

## 6. Experimento proposto (P7)
| Pergunta | Hipótese | Dados e inclusão | Método | Métricas | Separação / vazamento | Limitações |
|---|---|---|---|---|---|---|
| Padrões observáveis de sequência estão associados a melhores resultados? | Alguns padrões (ex.: compra antes de busca) aparecem mais em turnos com ataque/nocaute | turnos de quem exportou (mão conhecida), sem desistência no turno | n-gramas de tipos de ação; pareamento por estado (turno, D(t), deck, tamanho da mão); bootstrap agrupado por partida; Holm/BH para muitos padrões | diferença de taxa de ataque/nocaute; faixa 95%; q-valor | se virar previsão, separação no tempo | associação; o padrão pode refletir a mão (quem tem a carta X joga em outra ordem); poucos jogadores; **sem afirmação causal** |
**Desenho causal possível no futuro:** o próprio Pedro sorteia, em partidas de treino, entre duas ordens equivalentes e registra numa
tag — único jeito de chegar a "causa" com estes dados (D-021: hoje tudo é observacional).
