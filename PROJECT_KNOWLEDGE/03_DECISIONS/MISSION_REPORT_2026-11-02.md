# Relatório da missão de evolução do Coletor TCG Live (1º e 2/nov/2026)

Ponto de partida: versão 2026.11.01-4. Resultado: versão **2026.11.02-1**, na branch `missao-evolucao`
do histórico local (git) da pasta do programa; a versão de partida está guardada no commit `df19ef1` (branch `main`).
Nada foi publicado no GitHub e nada foi alterado na pasta real do Pedro nem nos dados dele: todos os testes
rodaram em cópias ("laboratório" com uma cópia dos dados reais + 45 torneios online reais).

Como ler as marcas usadas abaixo:
**[implementado e testado]** está no programa e passou nas medições; **[prototipado]** existe como código de teste;
**[recomendado]** foi analisado e vale fazer, mas não foi feito; **[pesquisado]** só foi estudado.

---

## 1. Diagnóstico geral

O Coletor é um programa local (Flask + SQLite + um painel em HTML/JS) com cerca de 9 mil linhas. Pontos fortes:
captura automática sem ler a memória do jogo, leitura de logs por regras editáveis, base de campeonatos grande
(grandes eventos + torneios online), troca de logs entre amigos e atualização em um clique.

O que limitava a ferramenta:
- **Segurança:** o servidor local aceitava comandos de qualquer site aberto no navegador (detalhes na seção 2).
- **Escala:** várias telas foram feitas para dezenas de partidas e um punhado de torneios. Com os torneios online
  (milhares de listas) e com um ano de partidas, algumas ficavam lentas (de 5 a 12 segundos).
- **Estatística de amostra pequena:** a tabela de matchups mostrava a taxa bruta mesmo com 3 ou 4 jogos, e
  medimos que ela previa os torneios seguintes **pior do que chutar 50%**.
- **Faltava matemática do próprio deck:** nenhuma conta de consistência (mulligan, prêmios, chance de ter a carta).

## 2. Principais problemas encontrados

| # | Problema | Gravidade | Situação |
|---|---|---|---|
| P1 | Painel aceitava pedidos de outros sites (CSRF): uma página maliciosa podia trocar o repositório de atualização e mandar "atualizar", fazendo o Coletor baixar e rodar código de outra pessoa. Demonstrado numa cópia descartável: o pedido mudou o repositório para `atacante/repo`. | Alta | **[implementado e testado]** |
| P2 | "Uso de cartas" levava 10,7 a 12 s com os torneios online (conta que percorria todas as listas para cada carta). | Alta | **[implementado e testado]** |
| P3 | Gravar uma partida relia todas as partidas: 138 ms com 13 partidas, 494 ms com 313, e cresceria sem parar (importar muitos logs de um amigo levaria dezenas de minutos). | Alta | **[implementado e testado]** |
| P4 | Com mil partidas: Início/Partidas/Desempenho 5,4 s, Decisões 6,7 a 8 s, cada deck em Meus decks 4,1 s. | Alta | **[implementado e testado]** (ver seção 8) |
| P5 | Taxa bruta de matchup com poucos jogos engana (log-loss 0,797 contra 0,693 do chute de 50%). | Média | **[implementado e testado]** como opção "taxa ajustada" |
| P6 | Identificação do deck com poucas cartas vistas era fraca (52 a 69% com 2 a 3 cartas). | Média | **[implementado e testado]** |
| P7 | Dependências sem limite de versão: uma atualização futura poderia instalar, por exemplo, o Flask 4 e quebrar o programa. | Média | **[implementado]** (limites `<próxima versão grande`) |
| P8 | Arquivos com quebras de linha misturadas (CRLF/LF) depois de edições no Windows. | Baixa | **[implementado]** (tudo em LF, como no original; `.bat` continuam CRLF) |
| P9 | Decisões ainda leva 2,7 s com mil partidas (lê o detalhe completo de cada partida). | Baixa | **[recomendado]** (seção 10) |
| P10 | O painel é um arquivo único de 2.461 linhas; difícil de manter e sem testes automáticos de tela. | Baixa | **[recomendado]** |

## 3. Pesquisas realizadas

- **Ferramentas parecidas:** Full Bench (captura e estatísticas globais; já aproveitado na versão -3),
  Dead Draw e PTCGL Replay (replays), Trainer Hill, dittobase (que separa decks em "variantes"),
  calculadoras hipergeométricas de Magic/Yu-Gi-Oh/Pokémon (nenhuma trata os prêmios do Pokémon com o mulligan junto),
  HSReplay (artigo de teoria dos jogos e escolha de deck) e um artigo acadêmico de 2026 que calcula o equilíbrio
  de Nash do meta do Pokémon TCG por programação linear sobre a matriz de matchups.
- **Técnicas:** distribuição hipergeométrica multivariada; Bradley-Terry (força de cada deck); empirical Bayes
  (puxar estimativas de amostra pequena para uma média confiável); Naive Bayes (classificação por probabilidade);
  k-medoides com silhueta (agrupar listas); fictitious play (equilíbrio de jogos de soma zero); índices invertidos
  e memorização (desempenho).

Fontes: [arXiv 2607.08692](https://arxiv.org/abs/2607.08692) (equilíbrio do meta no Pokémon TCG),
[HSReplay: Game Theory and Deck Choice](https://articles.hsreplay.net/2020/05/22/game-theory-and-deck-choice/),
[Six Prizes: TheMathTCG](https://sixprizes.com/2013/01/13/themathtcg-the-probabilities-behind/),
[Counterwatch: shrinkage bayesiano em taxas de vitória](https://www.counterwatch.gg/blog/why-we-use-bayesian-shrinkage-and-blizzard-s-rates-page-does-15e2fb82).

## 4. Descobertas em análise combinatória e matemática aplicada

Para cada técnica: o que é, como foi aplicada, o ganho medido e os limites.

**4.1 Hipergeométrica multivariada com condição de mulligan** **[implementado e testado]**
- *O que é:* a chance de tirar k cartas de um tipo ao sortear sem reposição; "multivariada" = vários tipos ao mesmo tempo.
- *Como funciona aqui:* a mão inicial é dividida em categorias (a carta X, outros Básicos, o resto). O programa
  percorre todas as composições possíveis (são poucas) e descarta as que dariam mulligan. Depois da mão, prêmios
  e compras saem das 53 cartas restantes; por simetria, a ordem não importa.
- *Problema que resolve:* "com 11 Básicos, qual a chance de mulligan?", "qual a chance de ter Rare Candy até o 2º turno?",
  "qual o risco de as 2 cópias de uma carta ficarem nos prêmios?", "qual a chance de ter Buddy-Buddy Poffin e Mist Energy juntos?".
- *Ganho:* contas exatas em 0,4 ms (a simulação equivalente de 200 mil partidas leva 4,9 s).
  Descoberta: a fórmula de livro, que ignora o mulligan, superestima. Um Treinador com 4 cópias aparece na mão em 38,1%
  dos jogos (a fórmula simples diz 39,9%), enquanto um Básico com 4 cópias aparece em 49,4%.
- *Limites:* não modela efeitos de cartas (buscas, compras extras). Precisa do estágio das cartas na biblioteca.
- *Combinação:* a chance de mulligan esperada é comparada com o mulligan real das partidas do deck, o que
  separa azar de lista mal montada.

**4.2 Bradley-Terry + empirical Bayes (confronto ajustado)** **[implementado e testado]**
- *O que é:* Bradley-Terry dá uma "força" a cada deck a partir de todas as partidas. Empirical Bayes completa um
  confronto de poucos jogos com essa previsão: `p = (vitórias + k × previsão) / (jogos + k)`.
- *Ganho medido (prevendo os 30% de torneios mais novos com os 70% mais antigos, 19.626 partidas):*

| Método | Log-loss (todas) | Log-loss (confrontos com <10 jogos) | Acerto |
|---|---|---|---|
| Taxa bruta (atual) | 0,7965 | 1,0146 | 56,9% |
| Taxa com 1+1 imaginários | 0,6894 | 0,7013 | 56,9% |
| Só força geral | 0,6886 | 0,6906 | 54,2% |
| **Ajustada (k = 24)** | **0,6779** | **0,6856** | **57,6%** |

  (log-loss menor é melhor; o chute de 50% dá 0,6931). O k = 24 foi escolhido só com dados de treino.
- *Limites:* o meta muda com coleções novas; o modelo assume que a força de um deck é estável dentro do período escolhido.

**4.3 Equilíbrio do meta (teoria dos jogos, soma zero)** **[implementado e testado]**
- *O que é:* a mistura de decks que nenhum outro deck consegue explorar (o "pedra-papel-tesoura" do meta).
- *Como:* fictitious play, sem biblioteca extra. Conferido em jogos com resposta conhecida: pedra-papel-tesoura dá
  33/33/33%, um jogo com deck dominado dá 0% para ele, e um ciclo assimétrico dá exatamente 22,2/33,3/44,4%.
- *Resultado nos dados reais (todas as fontes):* N's Zoroark tem a melhor taxa esperada contra o campo atual (52,7%),
  mas 0% no equilíbrio, porque perde muito para Festival Lead (34%). O equilíbrio fica em Dragapult 47%, Basic Box 33%
  e Alakazam Dudunsparce 17%.
- *Limites:* modelo de partida única; não considera o formato suíço nem o top cut. Usa só os 12 decks mais jogados.

**4.4 Naive Bayes suavizado para identificar o deck** **[implementado e testado]**
- *O que é:* a chance de cada deck dadas as cartas vistas, usando a frequência de cada carta nas listas reais.
- *Lição importante:* a primeira versão ganhou na simulação, mas **errou nos logs reais** (o seu Lopunny/Dusknoir
  virou "Milotic ex"). A causa: decks com 1 lista "aceitavam" qualquer carta. A versão final (NB2) suaviza pela
  frequência geral da carta e ignora decks com menos de 3 listas.
- *Ganho medido (simulação com 6.108 listas; acerto):*

| Cartas vistas | Método atual | NB2 |
|---|---|---|
| 2 | 51,8% | 61,3% |
| 3 | 68,7% | 75,5% |
| 5 | 81,3% | 83,3% |
| 8 | 89,1% | 89,1% |
| 12 | 91,8% | 91,6% |

  Nos 26 lados dos seus 13 logs reais, NB2 muda 7 resultados. Todos pareceram iguais ou melhores olhando as cartas
  (exemplo: quem revelou "Team Rocket's Mewtwo ex" agora é Rocket Mewtwo, não Spidops). O NB2 decide quando tem
  ≥ 50% de confiança; abaixo disso, vale o método antigo.

**4.5 k-medoides com silhueta (variantes de um deck)** **[implementado e testado]**
- *O que é:* agrupar listas parecidas (distância de Jaccard ponderada pelas cópias), escolhendo quantos grupos pela silhueta.
- *Resultado:* grupos nítidos nos decks mais jogados. Em N's Zoroark, a versão principal vence **56,5%**
  (provável 53 a 59%) e a com Transformation Tome vence **47,1%** (provável 41 a 54%).
- *Lição:* sem tamanho mínimo, a silhueta "achava" uma variante de uma lista só. Agora cada variante precisa de
  8% das listas e o agrupamento roda 5 vezes.

**4.6 Técnicas pesquisadas e não usadas**
- *Programação linear exata para o equilíbrio:* daria o equilíbrio exato, mas exigiria uma biblioteca nova (scipy).
  O fictitious play acertou os jogos de resposta conhecida e informa a própria "folga" (quanto falta para o equilíbrio
  exato). A comparação com programação linear nos dados reais **não foi feita**.
- *Algoritmo genético / branch and bound para montar listas:* exigiria um modelo confiável de "quanto cada carta vale".
  Os dados atuais só mostram correlação (quem usa a carta venceu mais), não causa; otimizar em cima disso
  recomendaria listas erradas. **[recomendado só para o futuro, com cautela]**
- *Subset sum / mochila:* não há problema do Coletor com essa forma. O mais próximo, "60 cartas com limites",
  cai no item anterior. **[pesquisado]**

## 5. Novos algoritmos que poderiam ser usados (além dos implementados)

- **Regressão logística regularizada por carta, controlando o adversário:** separa "a carta ajuda" de "quem joga
  aquele deck já é bom". Melhoraria "Cartas x matchups". **[recomendado]**
- **Ordem do tempo (decaimento exponencial):** pesar mais os torneios recentes no confronto ajustado, para o meta
  atual pesar mais que o de 3 semanas atrás. Fácil de testar com o experimento 3. **[recomendado]**
- **Simulação de abertura por efeitos de carta (Monte Carlo):** chance real de montar o tabuleiro no turno 2 usando
  buscas (Nest Ball, Poffin). Complementa a hipergeométrica, que não vê efeitos. **[recomendado]**

## 6. Funcionalidades que poderiam ser adicionadas

- **Sugerir o deck da partida pela lista de Meus decks**, já usando o NB2 (hoje é pela cobertura de cartas). **[recomendado]**
- **"Por que perdi?"**: juntar Decisões, mulligan observado e confronto ajustado num resumo por deck. **[recomendado]**
- **Alerta de meta:** avisar quando um deck sobe mais de X pontos na semana nos torneios online. **[recomendado]**
- **Comparar minha lista com as variantes:** dizer de qual variante a sua lista está mais perto e quanto ela vence. **[recomendado]**

## 7. Melhorias efetivamente implementadas (versão 2026.11.02-1)

1. **Proteção do painel** contra pedidos de outros sites (`app.py`, `so_pedidos_do_painel`) + `testes/teste_seguranca.py`.
2. **Consistência** em Meus decks (`tracker/probabilidades.py`, rotas `/api/decks/<id>/consistencia` e `/combo`).
3. **Qual deck jogar?** na tela Meta (`tracker/estrategia.py`, rota `/api/qual-deck`).
4. **Variantes** no Perfil de deck (`tracker/variantes.py`, rota `/api/variantes/<deck>`).
5. **Taxa ajustada** opcional em Matchups (empates contados como na taxa real).
6. **Identificação do deck com NB2** (`decks.identificar_nb`, reserva no método antigo).
7. **Uso de cartas em uma passada só** (`analises._uso_cartas`; a versão antiga ficou como `_uso_cartas_lento` para conferência).
8. **Gravar partida em tempo constante** (`decks.vincular_automatico` usa quem exportou o log).
9. **Análises rápidas:** identificador com índice e memória, lista de partidas em memória (invalidada a cada gravação),
   nomes de carta normalizados em memória, lista de Meus decks reaproveitada por 5 s.
10. **Limites de versão nas dependências**, quebras de linha normalizadas, `CLAUDE.md` e `novidades.json` atualizados.

## 8. Testes realizados e resultados

| Teste | Resultado |
|---|---|
| Teste de regressão (`testes/teste_tracker.py`) depois de cada etapa | `OK` em todas |
| Teste de segurança (7 casos: painel, script local, outro site, outra porta, DNS rebinding) | `OK`; a versão anterior aceitava o pedido de outro site |
| Experimento 1: contas exatas x 200 mil partidas simuladas (7 medidas) | Todas dentro do ruído (≤ 0,07 ponto) |
| Experimento 2: identificação do deck (6.108 listas reais, treino/teste separados por data) | Tabela da seção 4.4 + conferência nos logs reais |
| Experimento 3: matchups (19.626 partidas, previsão dos torneios mais novos) | Tabela da seção 4.2 |
| Experimento 5: variantes (listas reais) | Grupos nítidos (silhueta 0,27 a 0,44) |
| Experimento 6: Uso de cartas nova x antiga, 3 recortes | Resultado **idêntico**, de 7 a 44 vezes mais rápida |
| Experimento 7: tempo de gravar partida conforme o banco cresce | Antes 138 → 494 ms (13 → 313 partidas); agora ~43 ms constante |
| Experimento 8: análises com 1.013 partidas, versão anterior x nova | Resultado **idêntico**; tempos abaixo |
| Equilíbrio em jogos com resposta conhecida | Corretos |
| Telas no navegador (Meta/Qual deck, Matchups ajustada, Variantes, Consistência) com os dados do laboratório | Funcionando |

## 9. Antes e depois

| Medida | Antes | Depois |
|---|---|---|
| Uso de cartas, todos os torneios (153 mil linhas de listas) | 10,7 s | 0,24 s |
| Início/Partidas/Desempenho com 1.013 partidas (2ª abertura) | 5,3 s | 0,11 s |
| "Todos os jogadores" com 1.013 partidas | 1,5 s | 0,08 s |
| Decisões com 1.013 partidas | 8,0 s | 2,7 s |
| Gravar 1 partida com 313 já gravadas | 494 ms | 43 ms |
| Identificação com 2 / 3 cartas vistas (simulação) | 51,8% / 68,7% | 61,3% / 75,5% |
| Matchup com poucos jogos: log-loss | 1,0146 | 0,6856 (opção ajustada) |
| Pedido de outro site mudando a configuração | aceito | recusado (403) |

## 10. Não implementado, e por quê

- **Decisões ainda leva 2,7 s com mil partidas:** precisaria guardar os eventos de cada partida de outro jeito no banco
  (uma migração). O ganho não justifica o risco agora; com o uso atual (dezenas de partidas), leva décimos de segundo.
- **Trocar a taxa real pela ajustada como padrão em Matchups:** a ajustada prevê melhor, mas a real é o dado "como
  aconteceu", que as pessoas conferem no Limitless. Ficou como opção.
- **Algoritmos de montar lista (genético, branch and bound):** sem um modelo causal do valor de cada carta, otimizariam correlações. Ver 4.6.
- **Dividir o painel em vários arquivos:** é uma reorganização grande e sem ganho para quem usa; risco de regressão nas telas.
- **Gerar o instalador .exe:** continua dependendo do Inno Setup no PC (pedido de permissão pendente).

## 11. Riscos técnicos

- **Dependência de páginas de terceiros:** a importação do Labs e do índice do Limitless lê HTML; se o layout mudar,
  a importação de grandes eventos para. A API dos torneios online é documentada e mais estável.
- **Atualizador sem verificação de assinatura:** baixa o código da `main` do GitHub do Pedro. Com a proteção nova,
  um site não consegue mais trocar o repositório, mas uma conta do GitHub comprometida ainda poderia publicar código.
  Recomendado: publicar versões com tag e conferir o resumo (hash) do zip antes de instalar.
- **Tamanho do banco:** cada torneio online acrescenta milhares de linhas de listas. Com 45 torneios, cerca de
  150 mil linhas. As telas seguem rápidas (seção 9), mas vale apagar torneios com mais de 90 dias no futuro.
- **Modelos estatísticos:** "Qual deck jogar?" e a taxa ajustada são estimativas. O meta muda com coleções novas;
  as telas dizem isso.

## 12. Plano de evolução recomendado

**Prioridade alta**
1. Publicar a 2026.11.02-1, principalmente pela correção de segurança.
2. Publicar versões com tag e conferência do zip no atualizador (fecha o risco restante da seção 11).
3. Peso maior para torneios recentes no confronto ajustado (testar com o experimento 3; é baixo risco).

**Prioridade média**
4. Ligar a partida à lista de Meus decks usando o NB2.
5. "Minha lista x variantes": de qual variante a sua lista está mais perto.
6. Alerta semanal de meta (deck subindo nos torneios online).
7. Decisões mais rápida (eventos guardados à parte), se o número de partidas passar de algumas centenas.

**Prioridade baixa**
8. Regressão logística por carta controlando o adversário.
9. Simulação de abertura com efeitos de busca.
10. Dividir o painel em arquivos menores e criar testes automáticos de tela.

---

## Adendo (2/nov): ACE SPEC das listas e versões dos decks

**O que mudou** **[implementado e testado]**
- A ACE SPEC de cada lista é identificada pela biblioteca (raridade "ACE SPEC" no TCGdex, com o nome como reserva) e gravada em
  `t_jogadores.ace_spec` na importação, na primeira abertura (listas antigas, 1,9 s para 6.108 listas) e quando a biblioteca muda.
- Cobertura nas 6.108 listas do laboratório: 5.937 com exatamente 1 ACE SPEC, 171 sem nenhuma (conferidas: todas as cartas dessas
  listas existem na biblioteca, então não há ACE SPEC escondida) e **nenhuma com 2** (nenhum falso positivo).

**Análise por ACE SPEC** (experimento 9, `testes/experimentos/e9_ace_spec.py`; taxa de vitória e teste contra o resto do deck)
- Dragapult: Unfair Stamp 56,8% (95,6% das listas) × Hero's Cape **44,0%** (p = 0,016).
- N's Zoroark: Secret Box **57,0%** (p = 0,002) × Unfair Stamp 52,8% × Hero's Cape 45,1% × Survival Brace 29,3%.
- Ogerpon Meganium Hydrapple: Unfair Stamp 56,0% × Max Rod **43,5%** (p = 0,033) × Scoop Up Cyclone 31,0%.
- Dragapult Blaziken: Unfair Stamp 54,4% × Hero's Cape 20,5% (7 listas).
- Basic Box: Unfair Stamp 54,8%, Hero's Cape 52,3%, Prime Catcher 52,8% (sem diferença).
- **Padrão:** a ACE SPEC "padrão" do deck quase sempre vence mais do que as escolhas alternativas.
  Cuidado: com várias ACE SPEC comparadas ao mesmo tempo, alguma diferença pode aparecer por acaso.

**Qual modelo de versões** (previsão da taxa de vitória de listas dos torneios mais novos; log-loss por jogo, menor é melhor;
divisão de treino e teste fixa, conferida com duas execuções iguais)

| Modelo | Log-loss | Diferença para o deck inteiro |
|---|---|---|
| M0 deck inteiro (sem versões) | 0,6953 | — |
| M1 semelhança de listas (modelo anterior) | 0,6961 | −0,79 milésimo |
| M2 só ACE SPEC | 0,6963 | −1,05 |
| M3 ACE SPEC + raras aglutinadas | 0,6960 | −0,76 |
| M4 M3 + sub-versões | 0,6963 | −1,01 |
| **M5 M3 + junta ACE SPEC com listas quase iguais (adotado)** | **0,6958** | **−0,48** |
| M6 separa só ACE SPEC com diferença significativa | 0,6958 | −0,54 |

Conclusão honesta: **nenhuma divisão prevê o resultado de um jogador melhor do que o deck inteiro.** O resultado individual depende
mais do jogador e da sorte do que da versão da lista. Por isso as versões servem para **descrever e comparar**, não para prever.
Entre os modelos pela ACE SPEC, o M5 (separar por ACE SPEC, aglutinar as raras, juntar as quase iguais) foi o de melhor previsão e é o
pedido; ele foi adotado. Como aglutinar as raras esconderia diferenças reais (ex.: Hero's Cape no Dragapult), a tela mostra também a
tabela completa de cada ACE SPEC, e a marca "diferença provável" exige p < 0,05 e pelo menos 30 jogos.

---
*Como reproduzir as medições:* os scripts estão em `testes/experimentos/` (e1 a e8), cada um com o modo de uso no
começo. Rode sempre numa cópia do programa com uma cópia dos dados: alguns acrescentam partidas de teste ao banco.
