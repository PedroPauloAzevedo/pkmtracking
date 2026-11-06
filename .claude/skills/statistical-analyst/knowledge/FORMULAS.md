# Fórmulas, derivações e premissas

> Atualizado em 06/11/2026. Complementa `PROJECT_KNOWLEDGE/02_BUSINESS_RULES/STATISTICS.md` (que diz os números das telas) com o
> **porquê** de cada conta e as premissas que a sustentam. Não repete o código: aponta para ele.

## 1. Sorteio sem reposição (Consistência — `tracker/probabilidades.py`)
- P(X = k) = C(K, k)·C(N − K, n − k) / C(N, n). Várias categorias (carta, outros Básicos, resto): hipergeométrica multivariada,
  enumerando as divisões da mão (`_maos`).
- **Mulligan como condição:** cada nova mão é um sorteio novo do deck inteiro, então a mão que vale tem a distribuição da mão de 7
  *condicionada* a ter ≥ 1 Básico: P(mão | válida) = P(mão)·1[válida] / P(válida). Mulligans até a primeira válida: geométrica,
  média p/(1 − p) com p = C(60 − B, 7)/C(60, 7).
- **Prêmios e compras pela simetria:** depois da mão, as 53 cartas estão em ordem aleatória; os 6 prêmios e as t compras são dois
  subconjuntos disjuntos aleatórios das 53. Para "achar a carta nas t compras" importa só o subconjunto das compras, que é uniforme
  entre os de tamanho t: P(≥ 1 nas compras) = 1 − C(53 − f, t)/C(53, t) (f = cópias fora da mão), sem precisar sortear os prêmios.
- **Duas cartas (A e B) até o turno:** 1 − P(sem A) − P(sem B) + P(sem A e sem B), cada uma hipergeométrica nas compras.
- **Premissas:** embaralhado de verdade; nenhuma carta compra, busca, embaralha ou troca a mão; a ordem de turno não muda a contagem
  de compras (os dois compram no próprio turno). **Resultado é piso** quando há buscas. Para efeitos de cartas: simulação (lacuna G1).

## 2. Taxas e incerteza
- Taxa = V/(V + D + E). **Wilson** (z = 1,96): centro (p + z²/2n)/(1 + z²/n), margem z√(p(1−p)/n + z²/4n²)/(1 + z²/n). Melhor que
  "p ± 1,96√(p(1−p)/n)" com n pequeno ou p perto de 0/1 (não sai de [0, 1]).
- **Premissa:** partidas independentes com a mesma chance. Nos torneios o ICC medido é ≈ 0 (a1), então vale ali.
- **Efeito de desenho (Kish):** n_ef = n / (1 + (m − 1)·ICC), m = partidas por grupo. Use quando o ICC medido for > 0.
- **Muitos testes:** Holm (multiplica o i-ésimo menor p por m − i + 1, monotônico) controla "algum falso positivo";
  Benjamini-Hochberg (p_(i)·m/i, monotônico de cima para baixo) controla a fração de falsos entre os achados.
- **Significância ≠ relevância:** com milhares de partidas, 0,5 pp pode ser "provável" e não importar; com 30, 15 pp pode ser ruído.
  Sempre mostre o tamanho do efeito com a faixa.

## 3. Força, confronto e equilíbrio (`tracker/estrategia.py`)
- **Bradley-Terry:** P(A vence B) = sA/(sA + sB). Atualização MM (Hunter, 2004): s_d ← (W_d + prior/2) / (Σ_o n_do/(s_d + s_o) +
  prior/(s_d + 1)). O prior equivale a 2 jogos (1 V, 1 D) contra um deck de força 1. Normaliza pela média geométrica.
- **Confronto ajustado (encolhimento empírico-bayesiano):** p = (V + k·(1 − t)·BT) / (n + k). É a média a posteriori de uma Beta com
  "k jogos imaginários" centrada na previsão pela força. k escolhido por validação no tempo (e3); 12–32 empatam (a2).
- **Equilíbrio:** jogo simétrico de soma zero com ganho p(A,B) − ½ (antissimétrico só com W/L). *Fictitious play* (Robinson, 1951)
  converge para o valor do jogo; a **folga** = max_A Σ_B m(A,B)·x(B) mede a distância do equilíbrio (0 = exato).

## 4. Regressão logística com freio (`tracker/regressao.py`)
- logit P(V) = offset + b₀ + Σ b_c·Δcópias_c, offset = logit(confronto ajustado). Freio L2 λ: maximiza log-verossimilhança − ½λ‖b‖²
  (= posterior com prior normal de variância 1/λ). Newton/IRLS; erro padrão = √diag((XᵀWX + Λ)⁻¹) (aproximação de Laplace).
- **Premissas:** observações independentes (ok, a1); efeito linear por cópia em logit; amostra representativa — **falha**: só listas do
  topo (achado 1). "Provável" = |b| > 1,96·erro, sem correção de comparações múltiplas (com λ = 300, nenhuma carta passa: a5).

## 5. Naive Bayes da identificação (`tracker/decks.py`)
- nota(d) = log π_d + Σ_{c vista} log((n_dc + β·(g_c + 1)/(N + 2)) / (n_d + β)), π_d = fração de listas do deck, g_c = listas com a
  carta, N = listas. Confiança = softmax das notas. Só cartas vistas entram (não ver ≠ não ter).
- **Premissas:** cartas independentes dado o deck (falsa, mas a calibração medida ficou com erro de ±3 pp, a4); prior = meta do topo
  de todos os torneios importados (pode diferir do Ladder e da época atual).

## 6. Previsões: como medir
- **log-loss** = −média(y·ln q + (1 − y)·ln(1 − q)); chute 50% = ln 2 = 0,6931. **Brier** = média((q − y)²); chute = 0,25.
- **Calibração:** em cada faixa de q, compare a média prevista com a frequência real (erro médio ponderado = ECE). Em dados de
  pareamento, conte as **duas pontas** de cada partida (o lado do jogador 1 é viciado no Labs).
- **Comparar dois modelos:** diferença de perda *por linha* nas mesmas linhas, com bootstrap **agrupado por torneio** (as partidas de
  um torneio dividem meta e condições). Diferença cuja faixa de 95% contém 0 = "sem diferença clara".
- **Separação no tempo:** treino = torneios mais antigos, teste = mais novos; tudo que o modelo usa (inclusive o offset e os
  hiperparâmetros) calculado só com o treino. Cuidado com funções de produção que leem o banco inteiro (achado 9).

## 7. Jogo único × melhor de 3
- P(vencer melhor de 3) = q² + 2q²(1 − q) = q²(3 − 2q), q = chance por jogo, jogos independentes, sem empate. Crescente e simétrica
  (f(q) + f(1 − q) = 1); inversa por bisseção (`sa_tools.jogo_de_bo3`). A partida exagera a distância de 50%: 60% → 64,8%.
- Premissa frágil: jogos de uma mesma partida dividem os mesmos decks e o mesmo par de jogadores; quem começa alterna. Use como
  ordem de grandeza.
