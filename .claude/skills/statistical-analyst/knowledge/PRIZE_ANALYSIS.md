# Análise de prêmios: rota, corrida, prêmios checados e troca

> Atualizado em 06/11/2026. Conceitos e observabilidade: `STRATEGIC_CONCEPTS.md`. Hipergeométrica do programa:
> `tracker/probabilidades.py::hipergeometrica` (reutilizar; não reimplementar). Evidência: `experiments/p0_viabilidade_estrategica.py`.
> Nada aqui está implementado no Coletor; o que está marcado "medido" foi medido no p0 (83 partidas, exploratório).

> **Ferramentas prontas, não aplicadas (decisão do Pedro em 06/11/2026: poucos jogos):** funções em `tools/estrategia.py`,
> roteiro `experiments/p_estrategia.py <cópia> <p1..p7|todos>`, com trava de amostra mínima (MINIMOS no roteiro); testes em
> `tests/test_estrategia.py` (dados sintéticos).

## 0. Notação do estado
Turno t; jogador i ∈ {A, B}; **R_i(t)** prêmios restantes de i (6 no começo); **V(P)** valor de prêmio do Pokémon P (regra: Pokémon
ex = 2, Mega Evolução ex = 3, demais = 1; cartas podem alterar — o log não diz quando); **H(P)** PS restantes de P; **E_i** em jogo,
mão, descarte, baralho, prêmios de i. Conhecido por quem exportou (X): própria mão, próprias compras, os próprios prêmios **depois
de pegos**. Do adversário (Y): só o que foi jogado/revelado e o tamanho da mão.

## 1. Prize mapping (rota de prêmios)
**Definição (comunidade):** sequência planejada de nocautes cuja soma de valores chega a 6 (ex.: 2-2-2, 1-1-2-2, 3-3).
**Formalização.** Uma rota é uma sequência (v_1, …, v_n) com Σ v_k ≥ R_i e v_k ∈ {1, 2, 3}, em que cada v_k é o valor de um alvo que
existe (ou pode existir) no lado do adversário. As rotas possíveis a partir de R_i são **composições** de R_i com partes 1–3 (para
R = 6 há 24, se toda parte for permitida). Restrições reais: (a) o alvo precisa estar em jogo (Ativo, ou Banco com "puxar" — Boss's
Orders, Prime Catcher); (b) o dano precisa alcançar H(P) no turno; (c) recursos (Energia, cartas de puxar) são finitos.
**Como problema de busca:** estado s = (R_A, R_B, mesa, recursos conhecidos, vez); ação = (alvo, ataque, cartas usadas); transição =
dano/nocaute/prêmios + resposta do adversário. Objetivo **não** é "menos nocautes": é maximizar P(vencer) — uma rota 2-2-2 com alvos
que o adversário pode esconder vale menos que 1-1-2-2 garantida. Com informação escondida (mão/baralho do adversário), a busca deve
ser sobre **conjuntos de informação**: amostrar mãos plausíveis do adversário (determinização) ou ISMCTS (Cowling, Powley e
Whitehouse, 2012). Determinização tem vieses conhecidos (fusão de estratégias) — registrar.
**Quatro rotas diferentes (nunca chamar uma pela outra):**
1. *Matematicamente possível* — composições de R_i com os valores que existem no jogo;
2. *Executável* — alvos em jogo + dano alcançável + recursos conhecidos (só para quem exportou: a mão é conhecida);
3. *Robusta* — executável considerando respostas plausíveis do adversário (precisa de modelo do adversário);
4. *Executada* — a sequência de "took N" do log (**a única observada**).
**Medido (p0):** nas 35 vitórias por prêmios, 16 rotas executadas diferentes: 3-3 (5), 2-2-2 (3), 3-1-2 (3), 1-1-2-2 (3),
1-1-2-1-1 (3)… A rota executada é **observável**; a atribuição de prêmios a cada nocaute no resumo do Coletor é **inferida** e só bate
com o valor pelo nome em 76% dos 372 nocautes (nocautes duplos/efeitos) — use a sequência de "took N".
**Risco de expor multi-prêmio:** P(Y nocauteia P no próximo turno) × V(P). Precisa de dano esperado de Y (modelo do deck de Y) — I.

## 2. Prize racing (corrida)
**Indicadores (do mais observável ao mais modelado):**
- D(t) = R_B(t) − R_A(t) (vantagem de A em prêmios ao fim do turno t). **O.**
- Ritmo: prêmios pegos por turno com ataque, por jogador (média móvel). **O.**
- Turnos estimados até 6: T_i(t) ≈ menor n tal que a soma dos n maiores valores de nocaute alcançáveis ≥ R_i(t). Exige dano por turno
  e PS dos alvos. **I.**
- "Relógio" (clock): P(i nocauteia o Ativo do outro no próximo turno). **I** (dano e Energia conhecidos; buscas do adversário não).
- Contradição contagem × capacidade: D(t) > 0 mas P(A nocauteia no próximo turno) baixa e P(B nocauteia) alta. **I.**
**Medido (p0, descritivo):** o líder em prêmios ao fim do turno venceu: T3 10/22, T4 15/38, T5 25/46, T6 27/50 (≈ moeda);
T7 34/50 (68%), T9 39/49 (80%), T11 28/28. A contagem cedo quase não informa; a desistência (55%) entra aqui como fim.
**Modelagem adequada:** tempo até evento (vencer por prêmios) com **censura** pela desistência (Kaplan-Meier por grupo; modelo de
riscos proporcionais só com centenas de partidas); previsão do vencedor por turno com regressão logística em D(t), ritmo e "relógio",
avaliada **fora da amostra no tempo** (treinar em partidas antigas, testar nas novas), log-loss/Brier com `sa_tools`,
comparação pareada (`sa_tools.diferenca_pareada`, grupo = jogador/partida) contra o modelo "só D(t)".

## 3. Prize checking (cartas presas nos prêmios)
**Fórmula** (sorteio sem reposição): P(X ≥ 1) = 1 − C(N − m, k) / C(N, k). Usar `probabilidades.hipergeometrica(total=N,
sucessos=m, amostra=k, k=0)` para P(X = 0). **Definir N, m e k para cada estado** — e não usar se as zonas não forem estas:
| Estado (do ponto de vista de quem exportou, com a lista conhecida) | N | m | k | Premissas |
|---|---|---|---|---|
| Depois da mão inicial, antes de qualquer compra | 53 (60 − 7 da mão) | cópias da carta fora da mão | 6 | sem mulligan (a mão nova não aparece no log); prêmios separados ao acaso |
| Turno t, nenhum efeito que revele o baralho | cartas no baralho + prêmios restantes = 60 − (todas as cartas vistas: mão, mesa, descarte, prêmios já pegos, fora de jogo) | cópias ainda não vistas | prêmios restantes R(t) | toda carta não vista está no baralho OU nos prêmios, uniformemente; buscas que falharam não ficam no log (perderia informação, não erra) |
| Chance de tirar X ao pegar j prêmios agora | o mesmo N | o mesmo m | **j** | os prêmios pegos são escolhidos virados (amostra dos restantes) → X entre os j pegos ~ HG(N, m, j) por simetria |
| Adversário | — | — | — | **Não usar**: lista desconhecida; só como probabilidade sob modelo (NB2 + lista típica do deck), dita como tal |
**Quando NÃO vale:** mulligan de quem exportou (mão nova escondida); cartas que embaralham a mão no baralho com nomes não listados;
cartas que olham/trocam prêmios (não vistas nos logs até 06/11); lista de "Meus decks" diferente da usada na partida.
**Utilidade estratégica da carta premiada** (classificação do analista, não do log): *essencial* (sem substituto no deck: única
cópia de um Pokémon da linha principal, ACE SPEC, única Energia especial necessária), *substituível* (outra carta faz o mesmo
serviço — ex.: Nest Ball / Ultra Ball / Poffin, ver G15), *pouco relevante*. P(alguma essencial premiada) = 1 − P(nenhuma), com m =
soma das cópias das essenciais (cartas distintas do mesmo grupo somam cópias).
**Medido (p0):** 14 partidas de 1 deck (lista ligada, sem mulligan), 54 prêmios revelados; por classe de cópias restantes K = 1..4:
observado 3/20/22/9 × esperado 8,0/16,1/20,7/9,2 (z ≈ −1,9; +1,0; +0,3; −0,1). "Ao menos uma cópia premiada" (3 partidas com os 6
prêmios revelados, 71 cartas): previsto 23,4% × real 22,5%, Brier 0,171. **Sem contradição, mas amostra pequena e de um deck**
(o total observado = esperado por construção; só a divisão por classe testa algo). Classe: **C + D (exploratório)**.

## 4. Prize trade (troca de prêmios)
**Definição:** em cada sequência nocaute → resposta, prêmios ganhos − prêmios cedidos. Atacante de 1 prêmio que derruba um ex
"ganha" a troca por 1; Mega ex (3) que derruba um Pokémon de 1 "perde" por 2 se for derrubado em seguida.
**Indicadores:** (a) eficiência acumulada E_i(t) = prêmios pegos por i ÷ prêmios cedidos por i até t (O, com a sequência de "took N");
(b) saldo por troca (I: "troca" = par consecutivo de nocautes de lados opostos — definição escolhida, registrar); (c) proporção de
atacantes de 1 prêmio (I, pelo nome); (d) "troca sustentável": quantos atacantes prontos (com Energia) cada lado tem (I, mesa).
**Cuidados:** o saldo é consequência do jogo inteiro (quem está ganhando escolhe trocas melhores) — associação com vitória é
**esperada por construção** e não prova que "buscar boas trocas" causa vitória.

## 5. Experimentos propostos (P1–P4) — não modificam o Coletor
Todos: só leitura pela `tools/ponte.py`; registro por `sa_tools.registrar`; saída sem nicks; amostra pessoal pequena → exploratório.
| | Pergunta | Hipótese | Dados e inclusão | Método | Métricas | Separação / vazamento | Limitações |
|---|---|---|---|---|---|---|---|
| **P1** | Dá para reconstruir as rotas executadas e as possíveis? | A executada é exata; as possíveis são enumeráveis pela mesa | partidas com vencedor; replay | executada = "took N"; possíveis = composições de R com alvos em jogo (mesa) e dano alcançável | % rotas executadas reconstruídas (100% esperado); % nocautes com valor coerente (hoje 76%); nº de rotas possíveis por estado | — (descritivo) | intenção não observada; efeitos de carta no valor |
| **P2** | O ritmo explica o resultado além da contagem? | "Relógio" + D(t) prevê melhor que D(t) | partidas não terminadas por desistência no turno avaliado; ≥ 200 partidas para conclusão | logística por turno; Kaplan-Meier com censura | log-loss, Brier, calibração (`calibracao_detalhada`), diferença pareada | treino = partidas mais antigas; teste = novas; jogadores do teste fora do treino quando possível | desistência; poucos jogadores; Energia por habilidade às vezes ausente |
| **P3** | A hipergeométrica condicional acerta as cartas premiadas? | Calibrada nos estados em que N, m, k estão corretos | quem exportou, lista ligada, sem mulligan; prêmios revelados como gabarito | HG por estado (tabela §3); comparação previsto × revelado | contagens por classe, Brier/log-loss de "ao menos uma", calibração | não há treino (fórmula fixa) → sem vazamento | só o lado de quem exportou; 1 deck hoje |
| **P4** | Eficiência de troca está associada ao resultado? | Sim, mas por construção; interessa o *quanto* depois de controlar D(t) | partidas com ≥ 2 nocautes de cada lado | saldo por troca, eficiência acumulada; logística com controle de D(t) e decks | razão de chances com faixa por bootstrap agrupado (`bootstrap_agrupado`) | se usado para prever: separação no tempo | associação, não causa; definição de troca é escolha |
