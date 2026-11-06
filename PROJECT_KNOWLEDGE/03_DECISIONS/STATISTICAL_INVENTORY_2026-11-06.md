# Inventário dos métodos matemáticos e estatísticos (Fase 2 da Skill "Statistical Analyst")

> Atualizado em 06/11/2026. Código conferido: commit `76a2005` (versão 2026.11.05-6). Este documento **não muda nenhum método**:
> registra o que existe, onde está, o que sustenta cada um e o que ainda não foi demonstrado. A auditoria (Fase 3) parte daqui.
> Medições refeitas em 06/11 numa cópia de teste com os dados do Pedro (33 torneios de 28/08 a 01/11/2026, 44.651 partidas de
> torneio, 144.060 linhas de listas, 83 partidas pessoais de 3 jogadores), código atual, `python -I`.

## 0. Como ler
**Classificação** (pedida no prompt da Skill):
- **A · Documentado:** há explicação, não necessariamente código.
- **B · Implementado:** há código funcionando; a validade matemática não foi demonstrada o bastante.
- **C · Testado:** tem teste automático ou experimento de funcionamento (o código faz o que diz).
- **D · Validado experimentalmente:** há evidência de que o método funciona nas condições testadas.
- **E · Validado em dados reais:** avaliado em dados reais, com método adequado (ex.: separação no tempo) e resultado registrado.
- **F · Conhecimento insuficiente:** falta informação para dizer se é confiável.

Um método pode ter mais de uma letra (ex.: "C + E" = tem teste e validação em dados reais). **"Validado" vale só para a pergunta que
o experimento fez**: uma validação de previsão não valida a leitura causal, nem o uso numa população diferente.

**Os 4 testes de entrega** (`teste_tracker`, `teste_seguranca`, `teste_replay`, `teste_telas`) quase não conferem matemática: só
`regressao.ajustar` (sem freio = taxas reais; freio enorme = zero) e a contagem de `analises.matchups_por_slug`. Toda a validação
dos métodos depende dos experimentos `testes/experimentos/e1..e10`, que precisam de dados reais e **não guardam o resultado**
(os números ficam só no `MISSION_REPORT_2026-11-02.md` e aqui).

**Pacotes:** o programa usa só a biblioteca padrão do Python (`math.comb`, `math.erfc`, `random`...). Não há NumPy/SciPy/Pandas.
Consequência: toda conta foi escrita à mão (Newton/IRLS, eliminação de Gauss, MM do Bradley-Terry, k-medoides), e a conferência
contra uma referência independente precisa ser feita por nós (seção 3).

## 1. Resumo
| # | Método | Onde | Classe |
|---|---|---|---|
| M1 | Hipergeométrica exata da lista (mão, mulligan, compras, prêmios, duas cartas) | `probabilidades.py` | **C + D** |
| M2 | Taxa de vitória e faixa de Wilson 95% | `analises.wilson`, `placar` | **C** (fórmula conferida); premissa de independência **F** |
| M3 | Força dos decks (Bradley-Terry, MM de Hunter) | `estrategia.forcas` | **C + D** |
| M4 | Confronto ajustado (empirical Bayes, k = 24) | `estrategia.confrontos_ajustados` | **E** (previsão); k = 24 continua bom (12–32 empatam; auditoria, achado 2) |
| M5 | Taxa esperada contra o campo | `estrategia.qual_deck` | **B** |
| M6 | Equilíbrio do meta (*fictitious play*) | `estrategia.equilibrio` | **C** (jogos com resposta conhecida); valor preditivo **F** |
| M7 | Efeito de cada carta (regressão logística L2 = 300) | `regressao.py` | **C + E** (previsão); ganho sobre o deck sozinho **não demonstrado** |
| M8 | Identificação do deck (Naive Bayes NB2 + ícones + dano) | `decks.identificar*` | NB2 **E**; a reserva pelos ícones piora com 2–5 cartas (auditoria, achado 4) |
| M9 | Versões pela ACE SPEC (M5 do exp. 9) + teste de duas proporções | `variantes.variantes`, `_valor_p` | **E** (descrição/previsão); valor-p **B** (premissa violada) |
| M10 | k-medoides + silhueta (modelo antigo de variantes) | `variantes.variantes_por_semelhanca` | **C + D** |
| M11 | Uso de cartas ("vitória com / sem") | `analises._uso_cartas` | **C** (igual à versão lenta); leitura **B** |
| M12 | Carta × matchup | `analises.cartas_matchups` | **B** |
| M13 | Meta: divisão, conversão, fator de conversão, matriz | `analises.meta` | **B** (descritivo) |
| M14 | Tendência por torneio/semana | `analises.tendencia` | **B** (descritivo) |
| M15 | Desempenho pessoal (por deck, adversário, ordem, mulligan, 1º nocaute, série) | `analises.analise_pessoal` | **B** |
| M16 | Decisões (aberturas, cartas jogadas, corrida de prêmios, ritmo) | `analises.decisoes` | **B**; uso causal **F** |
| M17 | Reconstrução do estado (replay: dano, mãos, prêmios, descartes) | `replay.py` | **E** (conferências nas partidas reais, `EVIDENCE.md`) |
| M18 | Simulação de Monte Carlo | só `testes/experimentos/e1` | **C** (serve só para conferir M1) |

## 2. Fichas

### M1 · Consistência da lista (hipergeométrica exata) — `tracker/probabilidades.py`
- **Problema:** chance de mulligan, de ter a carta na mão/até o turno t, de ficar presa nos prêmios, de ter A e B juntas.
- **Fundamento:** sorteio sem reposição. P(k de K em n de N) = C(K,k)·C(N−K,n−k)/C(N,n). Mão dividida em categorias
  (carta, outros Básicos, resto) → hipergeométrica multivariada (`_maos`). Mulligan como **condição**: só mãos com ≥ 1 Básico, renormalizadas
  (equivale às regras: cada nova mão é um sorteio novo do deck inteiro). Mulligans esperados = p/(1−p) (geométrica).
  Prêmios e compras saem das 53 restantes e, por simetria, as t compras são um subconjunto aleatório das 53 (os prêmios não precisam
  ser sorteados antes). Duas cartas: inclusão-exclusão nas compras.
- **Funções:** `hipergeometrica`, `ao_menos_um`, `_maos`, `mulligan`, `mulligans_esperados`, `carta` (com `lru_cache`), `combo`,
  `resumo_lista`. Constantes `DECK, MAO, PREMIOS = 60, 7, 6`. `compras_turno = (1, 2, 3)` (os dois jogadores compram no próprio turno,
  inclusive quem começa: regra atual).
- **Entrada:** lista `[{nome, qtd, basico}]`. **Saída:** mulligan, mulligans esperados, por carta `na_mao`, `ate_turno[3]`, `alguma_premio`, `todas_premio`.
- **Premissas:** deck embaralhado de verdade; nenhuma carta compra, procura ou embaralha; ninguém joga Judge/Iono etc.; não conta as cartas
  extras que o adversário compra pelos seus mulligans. **Resultado = piso** (documentado em D-031).
- **Testes:** nenhum nos 4 testes de entrega. **Experimento e1** (200 mil partidas simuladas, semente 42): 9 medidas, todas ≤ 0,10 pp do
  exato (refeito em 06/11: APROVADO).
- **Conferido em 06/11:** soma da distribuição = 1; 0 Básicos → mulligan 100% e esperados ∞ (vai como `None` no JSON).
- **Pontos de atenção:** entrada impossível (ex.: carta Básica com mais cópias que o total de Básicos) devolve zeros em silêncio, sem erro;
  `combo` supõe A ≠ B. A simulação do e1 usa as mesmas premissas do código, então confere a **conta**, não as **premissas** (não diz
  quanto as buscas mudam o resultado).

### M2 · Taxa de vitória e faixa de Wilson — `analises.wilson`, `analises.placar`
- **Fórmula:** taxa = V/(V+D+E) (empate conta como não-vitória, como no Limitless). Wilson com z = 1,96:
  centro = (p + z²/2n)/(1 + z²/n), margem = z·√(p(1−p)/n + z²/4n²)/(1 + z²/n).
- **Usada em:** quase todas as telas (pessoal, meta, matriz, variantes, uso de cartas, decisões).
- **Conferido em 06/11:** 7/10 → 39,7–89,2% (referência 39,68–89,22%); 0/10 → 0–27,8%; 10/10 → 72,2–100%; n = 0 → vazio. **Fórmula correta.**
- **Premissa:** jogos independentes com a mesma chance. Nos torneios, um mesmo jogador com a mesma lista faz ~8,2 partidas em média
  (medido em 06/11): as partidas não são independentes, e a faixa fica **estreita demais** quando a conta junta partidas de poucos jogadores
  (variantes, uso de cartas, carta × matchup). Nas partidas pessoais (Ladder) a independência é mais razoável. Não há correção de
  comparações múltiplas em telas com dezenas de faixas. *Auditoria (achado 6): nos torneios o ICC medido é ≈ 0 (efeito de
  desenho 1,00), então a premissa de independência se sustenta ali; a correção de comparações múltiplas continua faltando (achado 5).*
  *Revisão 06/11 (a7): o ICC ≈ 0 é dos jogadores com lista; com todos os jogadores de torneio é +0,063 (Labs +0,096), e as faixas
  das telas que juntam todas as partidas (Meta, Matchups) ficam até ~25% estreitas demais. `STATISTICAL_HARDENING_2026-11-06.md`, D.1.*
  *(Corrigido em 06/11 pelo a11: nas telas de Meta/Matchups — decks dos dois lados conhecidos, empate = não-vitória — o ICC é
  0,015 (Labs 0,032) e as faixas antigas cobriam 93–96% em vez de 95%; o "até ~25%" valia só para o recorte do a7.)*

### M3 · Força dos decks (Bradley-Terry) — `estrategia.forcas`
- **Modelo:** P(A vence B) = sA/(sA+sB). Algoritmo MM de Hunter (2004), 200 iterações, normalizado pela média geométrica.
- **Prior = 2:** cada deck ganha 2 jogos imaginários (1 vitória, 1 derrota) contra um deck de força 1 — puxa decks raros para a média.
- **Entrada:** partidas W/L (sem empates, sem espelhos, sem deck vazio). Partidas são **partidas de torneio (melhor de 3)**.
- **Conferido em 06/11:** dados sintéticos com forças conhecidas (20 mil partidas) → forças recuperadas com erro < 2%.
- **Validação:** usado dentro de M4 (exp. 3). Sozinho, prevê pouco: log-loss 0,6921 contra 0,6931 do chute de 50% (06/11).
- **Atenção:** não há critério de parada por convergência (200 iterações fixas); nenhum controle de jogador nem de tempo.

### M4 · Confronto ajustado (empirical Bayes) — `estrategia.confrontos_ajustados`, `K_PADRAO = 24`
- **Fórmula:** p(A,B) = (V_AB + k·(1−t)·sA/(sA+sB)) / (n_AB + k), t = fração geral de empates (com empates na conta, a previsão pela força
  é reduzida para manter a convenção do Limitless).
- **Validação — exp. 3** (separação no tempo: 70% dos torneios mais antigos treinam; k escolhido numa segunda separação dentro do treino).
  - 02/11 (dados da época): k = 24; log-loss da ajustada 0,6856 contra 1,0146 da taxa bruta nos confrontos com poucos jogos.
  - **06/11 (refeito, 33 torneios, 23.308 partidas):** k escolhido = **16**.
    | Teste (5.106 partidas) | log-loss | Brier | acerto |
    |---|---|---|---|
    | taxa bruta | 0,7661 | 0,2557 | 58,1% |
    | Laplace (+1/+1) | 0,6836 | 0,2445 | 58,1% |
    | só a força | 0,6921 | 0,2489 | 53,9% |
    | **ajustada** | **0,6776** | **0,2417** | **58,8%** |
    | chute 50% | 0,6931 | 0,2500 | — |
    Só confrontos com < 10 jogos no treino (1.304 partidas): ajustada **0,6976**, pior que o chute de 50% (0,6931); bruta 1,0235.
- **Classe E** para "prevê melhor que a taxa bruta". **Auditoria (achado 2):** k = 16 e 24 empatam (o k escolhido pelo e3 muda com o corte no tempo); ainda não demonstrado que,
  com poucos jogos, a ajustada é melhor que dizer 50%.
- **Uso na tela:** a taxa real é o padrão em Matchups; a ajustada é opção (D-018). Também é o ponto de partida de M5, M6 e M7.

### M5 · Taxa esperada contra o campo — `estrategia.qual_deck`
- Σ_B campo(B)·p(A,B), com os 12 decks mais presentes. **Campo = presença em partidas**, não em inscrições: decks que vão longe no
  torneio jogam mais partidas e pesam mais. Sem faixa de incerteza; sem validação própria. **Classe B.**

### M6 · Equilíbrio do meta — `estrategia.equilibrio`
- Jogo simétrico de soma zero com ganho p(A,B) − 0,5 (em `qual_deck` só entram W/L, então a matriz é antissimétrica de verdade).
  *Fictitious play* (Robinson, 1951), 20.000 rodadas, começa pelo deck 0; devolve a mistura e a **folga** (quanto a melhor resposta ainda
  ganha; 0 = equilíbrio exato).
- **Conferido em 06/11:** pedra-papel-tesoura → 33,3/33,1/33,6% com folga 0,24 pp; deck dominante → 100% nele, folga 0. **Classe C.**
- **Não demonstrado:** que a mistura de equilíbrio diga algo útil sobre os torneios seguintes (nenhum experimento). A incerteza da
  matriz (M4) não é propagada para a mistura. Programação linear daria o valor exato, mas exigiria SciPy (descartado em `DECISIONS.md`).

### M7 · Efeito de cada carta (regressão logística com freio) — `tracker/regressao.py`
- **Modelo:** logit P(vitória) = logit(confronto ajustado) [offset fixo] + b₀ (deck) + Σ b_c·(cópias_c − cópias mais comuns_c).
  Newton/IRLS, 25 iterações, freio L2: `PESO = 300` nas cartas, `PESO_DECK = 1`. Só cartas com ≥ `MIN_LISTAS = 12` listas fora do comum.
  Exige ≥ 24 listas e 50 partidas. Incerteza = raiz da diagonal da inversa da Hessiana com freio (leitura bayesiana com prior normal).
  "Efeito provável" se |b| > 1,96·erro.
- **Testes:** `teste_tracker.py` confere os dois extremos do freio.
- **Validação — exp. 10** (separação no tempo; o confronto ajustado é recalculado só com o treino):
  | Modelo (6.372 partidas de teste, 06/11) | log-loss | Brier |
  |---|---|---|
  | M0 só o confronto ajustado | 0,6919 | 0,2487 |
  | M1 + ajuste do deck | **0,6667** | 0,2368 |
  | M2 regressão, peso 100 / **300** / 1000 | 0,6665 / **0,6660** / 0,6661 | 0,2366 / 0,2364 / 0,2365 |
  | M3 bruto com/sem | 1,0569 | 0,2708 |
  O peso 300 continua o melhor. **Mas o ganho das cartas sobre o deck sozinho é de 0,0007 em log-loss** (02/11: 0,0009). Não há
  intervalo nem teste para essa diferença: **não está demonstrado que os efeitos das cartas acrescentam previsão.** O que está
  demonstrado (E) é que a regressão é muito melhor que o "com/sem" bruto.
- **Premissas e riscos (para a Fase 3):** (1) **viés de seleção** — só jogadores com lista entram, e as listas são só do topo
  (`listas_top`, padrão 64). Medido em 06/11: nos grandes eventos, quem tem lista venceu 61,4% das partidas, quem não tem 50,0%; nos
  online, 46,4% × 20,5%. O ajuste do deck (M1) pode estar medindo isso, e o efeito de uma carta é estimado só entre quem já foi bem;
  (2) partidas do mesmo jogador não independentes — *descartado pela auditoria (ICC ≈ 0)*; (3) dezenas de cartas testadas sem correção de
  comparações múltiplas; (4) em produção o offset usa os mesmos torneios (circular, só para descrição); (5) o offset conta empate como
  não-vitória, mas a regressão só usa W/L. Leitura oficial: associação, não causa (D-021).

### M8 · Identificação do deck pelas cartas reveladas — `tracker/decks.py`
- **NB2:** Naive Bayes só com as cartas vistas (presença/ausência por lista). nota(deck) = log(fração de listas do deck) +
  Σ log((vezes + β·(freq. geral + 1)/(total + 2)) / (n_deck + β)), `BETA_NB = 2`, `MIN_LISTAS_DECK = 3`. Decide se houver
  `MINIMO_LISTAS_NB = 200` listas e confiança (posterior normalizada) ≥ `CONFIANCA_NB = 0,5`; senão, ícones (`_identificar_por_icones`,
  nota ≥ 2,5); senão, palpite do leitor pelo dano. Energias Básicas ficam de fora. Duas implementações iguais (`identificar_nb` com
  índice, `_identificar_nb_direto` sem), conferidas no e8.
- **Validação — exp. 2** (listas reais; torneios antigos treinam, novos testam; k cartas sorteadas, semente 7): NB2 acerta mais que os
  ícones com poucas cartas (02/11: 61,3% / 75,5% com 2 / 3 cartas, contra 51,8% / 68,7%).
- **Refeito em 06/11 — e o e2 ficou inválido em parte.** A coluna "atual" do e2 chama `decks.identificar`, que **desde a 2026.11.02-1
  é a regra combinada com o NB2** (não mais os ícones) e monta o NB2 com **todas** as listas do banco, inclusive as do teste. Por isso
  ela "ganhava" do NB2 com 5+ cartas (95,7% × 92,0% com 12). Uma primeira versão deste inventário concluiu, errado, que os ícones
  acertavam mais; a medição correta (auditoria A4, modelos só com o treino) está em `STATISTICAL_AUDIT_2026-11-06.md`, achado 4:
  ícones sozinhos 19–74%, NB2 64–92%, regra do programa 51–92% (pior que o NB2 sozinho com 2–3 cartas).
- **Limitações:** no teste as cartas vistas são **sorteadas ao acaso** da lista; numa partida real as primeiras cartas vistas não são
  aleatórias (Pokémon de abertura, buscas). O prior é a fração de listas **dos torneios (topo)**, de todas as épocas, não do Ladder do
  TCG Live. Classe após a auditoria: **E** para o NB2 (separação no tempo, calibração com erro médio de 3 pontos); a reserva pelos ícones
  com confiança < 0,5 **piora** o acerto (achado 4).

### M9 · Versões pela ACE SPEC + "diferença provável" — `variantes.variantes`
- **Regra:** separa por ACE SPEC; as raras (< 8% ou < 8 listas) vão para a versão de medoide mais parecido; junta versões com
  distância < `DISTANCIA_JUNTAR = 0,12` sem a ACE SPEC. Distância = Jaccard ponderado pelas cópias. Medoide numa amostra de até 120
  listas, semente 42.
- **"Diferença provável":** teste z de duas proporções (`_valor_p`, conferido em 06/11: 60/100 × 50/100 → p = 0,155), p < 0,05 e
  ≥ 30 jogos (`MIN_JOGOS_DIFERENCA`).
- **Validação — exp. 9:** M5 é o melhor modelo **entre os que usam a ACE SPEC**; nenhuma divisão prevê melhor que o deck inteiro
  (D-020: versões servem para descrever).
- **Refeito em 06/11** (parte 3, ganho sobre o deck inteiro em milésimos de log-loss por jogo; log-loss do deck inteiro 0,6872):
  k-medoides −0,08; só ACE **+0,22**; ACE + aglutina −0,01; + sub-versões −0,09; **M5 (o do programa) +0,06**; ACE só se significativa
  (+0,3). Com os dados de hoje o M5 **não é mais o melhor** entre os que usam a ACE SPEC, mas todas as diferenças são de décimos de
  milésimo, pequenas demais para escolher entre eles. A conclusão de D-020 (versões descrevem, não preveem) continua de pé.
- **Riscos:** o teste trata cada partida como independente, mas a unidade real é a lista/jogador (~8 partidas cada) → p-valores
  pequenos demais *(revisão 06/11: entre jogadores com lista o ICC medido é ≈ 0, então este risco é pequeno aqui — a7)*; vários testes por deck sem correção; usa o placar final do jogador (V/D/E do torneio), com o mesmo viés de seleção do M7.

### M10 · k-medoides + silhueta — `variantes.variantes_por_semelhanca`
- k de 2 a 4, 5 tentativas, até 300 listas (sorteio com semente 42), silhueta ≥ 0,25, grupo ≥ 8% e ≥ 8 listas. Mantido como
  alternativa (D-017). Exp. 5: grupos nítidos nos decks mais jogados (silhueta 0,27–0,44 em 02/11). **C + D** (descreve; não prevê, exp. 9).

### M11 · Uso de cartas — `analises._uso_cartas`
- % de listas, média de cópias, distribuição e "taxa com / taxa sem" pelo placar final de cada jogador. Exp. 6 refeito em 06/11:
  resultado **idêntico** à versão lenta, 47× mais rápida. A conta está certa (C); a **leitura** com/sem mistura adversários, jogador e
  outras cartas (M3 do exp. 10 mostra que prevê muito mal: log-loss 1,06) e tem o viés de seleção das listas do topo. **B.**

### M12 · Carta × matchup — `analises.cartas_matchups`
- Taxa contra cada adversário por número de cópias, com Wilson e aviso de poucos jogos (< 5). Mesmas limitações do M11. **B.**

### M13 · Meta — `analises.meta`
- Divisão (% de jogadores), conversão = no corte / no campo, fator de conversão = (fração no corte)/(fração no campo), taxa sem espelho
  com Wilson, matriz 12 × 12 com aviso abaixo de 10 partidas. Descritivo; conta empates como não-vitória. **B.**

### M14 · Tendência — `analises.tendencia`
- Participação por torneio; acima de 20 torneios, agrupa por semana (segunda-feira). Sem incerteza nem suavização. **B.**

### M15 · Desempenho pessoal — `analises.analise_pessoal`
- Placar com Wilson por deck, lista, adversário, ordem, mulligan, primeiro nocaute, motivo, série acumulada e turnos médios.
  Partidas repetidas (mesmo jogo pelos dois lados) contam uma vez (D-033).
- **Ponto de atenção comprovável:** a comparação "seu resultado × meta" (`meta_taxa`) usa a taxa de **partidas de torneio (melhor de 3)**
  para comparar com **jogos do Ladder (1 jogo)**. Se a chance de vencer um jogo é q, a de vencer uma melhor de 3 é q²(3 − 2q): q = 55% →
  57,5%; q = 60% → 64,8%; q = 65% → 71,8%. A referência do meta fica mais longe de 50% do que deveria. Também usa todos os torneios,
  sem a época escolhida.
- **Amostra:** 83 partidas pessoais na cópia (3 jogadores; o maior com 47). Com 47 jogos, a faixa de Wilson de uma taxa de 50% vai de
  ~36% a ~64%: quase toda divisão por deck/adversário fica sem conclusão.

### M16 · Decisões — `analises.decisoes`
- Aberturas (cartas dos 2 primeiros turnos), cartas jogadas, primeiro prêmio, viradas, turno em que perdeu o controle, ritmo; separadas
  por quem começou; mínimo 3 partidas por linha; Wilson nas taxas.
- **Riscos:** associação pura, com causalidade reversa forte (uma carta é jogada **por causa** do estado da partida) e viés de duração
  (partidas longas mostram mais cartas). Dezenas de linhas sem correção de comparações múltiplas. O documento e a tela já dizem
  "correlação, não causa". **B**; para decisões de jogo, **F**.

### M17 · Reconstrução do estado (replay) — `tracker/replay.py`
- Não é estatística, mas é a base de qualquer análise de decisão futura. Conferências em partidas reais registradas em `EVIDENCE.md`:
  0 estados impossíveis de dano, mãos 109/109, prêmios de quem exportou 253/253, descartes 182/182. **Observabilidade:** a mão do
  adversário só é conhecida quando o log revela; prêmios do adversário nunca têm nome (0/235); Energias ligadas por habilidade nem sempre
  aparecem (73 de 754 ataques com Energia "de menos"). Os scripts dessas medições estão fora do repositório (`NEXT_STEPS.md`, item 4).

### M18 · Monte Carlo
- Só no e1, para conferir M1 (semente 42, 200 mil partidas, ~5 s). A simulação de abertura **com efeitos de cartas** está recomendada
  (relatório da missão, seção 5; `BACKLOG.md`, item 8) e não existe.

## 3. Conferências independentes feitas em 06/11 (rascunho fora do repositório)
| Conferência | Esperado | Obtido |
|---|---|---|
| Wilson 7/10, 0/10, 10/10 | 39,68–89,22; 0–27,75; 72,25–100 | 39,7–89,2; 0–27,8; 72,2–100 |
| Hipergeométrica: soma das probabilidades | 1 | 1,0 |
| Mulligan com 0 / 60 Básicos | 100% / 0% | 100% / 0% |
| Equilíbrio em pedra-papel-tesoura | 1/3 cada | 33,3 / 33,1 / 33,6% (folga 0,24 pp) |
| Equilíbrio com deck dominante | 100% nele | 100%, folga 0 |
| Bradley-Terry com forças conhecidas (20 mil partidas) | 2,449 / 1,225 / 0,816 / 0,408 | 2,422 / 1,242 / 0,819 / 0,406 |
| Teste de duas proporções 60/100 × 50/100 | p = 0,155 | 0,1552 |
| Melhor de 3 a partir da chance por jogo | q²(3 − 2q) | — (usado na ficha M15) |

## 4. Experimentos refeitos em 06/11 (mesmos dados, código atual)
| Exp. | O que valida | Separação no tempo | Semente | Resultado 06/11 |
|---|---|---|---|---|
| e1 | conta exata de M1 × simulação | não se aplica | 42 | APROVADO (≤ 0,10 pp) |
| e2 | M8 | sim (70/30 por torneio), **mas a coluna "atual" vaza o teste** | 7 | NB2 63,6–92,0%; coluna "atual" inválida (ver M8) |
| e3 | M4 | sim (70/30 + validação interna para k) | — (determinístico) | ajustada 0,6776; k = 16 |
| e5 | M10 | não (descritivo) | sim | grupos nítidos em 3 de 4 decks (silhueta 0,33–0,53); Slowking 0,17 |
| e6 | M11 rápido = lento | não se aplica | — | idêntico, 47× mais rápido |
| e9 | M9 | sim (parte 3) | sim | todas as divisões a ±0,3 milésimo do deck inteiro; M5 +0,06 |
| e10 | M7 | sim (70/30; confronto só com o treino) | — | peso 300: 0,6660 × deck sozinho 0,6667 |
| e4, e7 | tempo (gravam no banco) | — | — | não refeitos (só em banco descartável) |
| e8 | análises pessoais iguais entre versões | — | — | não refeito (precisa de duas versões) |

**Reprodutibilidade:** os experimentos imprimem o resultado, mas não o guardam e não registram a versão do código nem dos dados. Os
números de 02/11 e de 06/11 são diferentes porque os dados cresceram (19.626 → 23.308 partidas no e3). Não há como refazer exatamente
a medição de 02/11.

## 5. Conhecimento já pesquisado (não repetir)
- Fontes em `MISSION_REPORT_2026-11-02.md`, seção 3: arXiv 2607.08692 (equilíbrio de Nash do meta do Pokémon TCG por programação linear),
  HSReplay (teoria dos jogos e escolha de deck), Six Prizes (TheMathTCG), Counterwatch (encolhimento bayesiano de taxas).
- Descartados com motivo (`DECISIONS.md`): algoritmos de montar lista; programação linear (exigiria SciPy); fontes japonesas; logs de
  terceiros (Full Bench, Dead Draw).
- Recomendados e não feitos (missão, seção 5 e 12): peso maior para torneios recentes; simulação de abertura com efeitos; regressão
  controlando o adversário (feita como M7); "minha lista × variantes"; alerta de meta.

## 6. Pontos para a Fase 3 (hipóteses levadas à auditoria)
> Resultado de cada um em `STATISTICAL_AUDIT_2026-11-06.md` (alguns se confirmaram, um foi descartado: a dependência entre partidas).
1. **Viés de seleção das listas do topo** em M7, M9, M11, M12 e no prior do M8 (números da ficha M7).
2. **Partidas não independentes** (~8 por jogador) nas faixas e valores-p de M2, M9, M11, M12.
3. **Melhor de 3 × 1 jogo** na comparação pessoal × meta (M15) — a diferença matemática está demonstrada; falta medir o tamanho na tela.
4. **k do confronto ajustado** (24 no código, 16 nos dados de hoje) e confrontos com poucos jogos piores que 50%.
5. **M7 sem ganho demonstrado** sobre o deck sozinho; falta um intervalo (bootstrap por torneio) para a diferença de log-loss.
6. **Identificação do deck:** a regra combinada de produção (NB2 ≥ 0,5, senão ícones) nunca foi medida sem vazamento, e o teste
   sorteia as cartas em vez de usar as vistas de verdade.
7. **Empates** (~10% das partidas de torneio, 4.354 de 44.651; muitos são empates combinados) contados como não-vitória em todas as taxas.
8. Em `t_partidas`, `res1` tem 26.275 W × 14.022 L: o jogador 1 vence quase o dobro. Os modelos atuais são simétricos e não são afetados,
   mas qualquer modelo novo com "lado" precisa saber disso (provável ordem da página de pareamentos; não investigado).
9. Nenhum método usa a **época** (coleção) nem pesa o tempo, exceto pelos filtros da tela.
