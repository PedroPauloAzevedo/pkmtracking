# Conceitos estratégicos do Pokémon TCG e o que os logs permitem medir

> Atualizado em 06/11/2026. Porta de entrada da análise estratégica. Detalhe matemático: `PRIZE_ANALYSIS.md` (prêmios),
> `CONTROL_AND_DISRUPTION.md` (stall, lock, disrupção, mill), `DECISION_ANALYSIS.md` (sequência, recursos, decisões).
> Evidência de viabilidade: `experiments/p0_viabilidade_estrategica.py` (83 partidas do Coletor, 06/11). Fontes: `RESEARCH_REGISTER.md`.

> **Ferramentas prontas, não aplicadas (decisão do Pedro em 06/11/2026: poucos jogos):** funções em `tools/estrategia.py`,
> roteiro `experiments/p_estrategia.py <cópia> <p1..p7|todos>`, com trava de amostra mínima (MINIMOS no roteiro); testes em
> `tests/test_estrategia.py` (dados sintéticos).

## 1. Quatro níveis de afirmação (nunca misturar)
| Nível | O que é | Exemplo | Pode virar número de tela? |
|---|---|---|---|
| **Definição** | O que o termo significa na comunidade | "Prize map = sequência de nocautes planejada até 6 prêmios" | Não (é vocabulário) |
| **Estratégia recomendada** | Conselho de jogadores/guias | "Use atacantes de 1 prêmio contra decks de ex" | Não — opinião, não evidência |
| **Hipótese matemática** | Formalização testável | "Diferença de prêmios no turno T prevê o vencedor" | Só depois de medida |
| **Evidência nos dados** | Medido nos logs/torneios do Coletor, com método e incerteza | "Líder no turno 9 venceu 39 de 49 (p0)" | Sim, com classe A–F e limites |
Classe (como em `KNOWN_METHODS.md`): A documentado · B implementado · C testado · D validado em experimento · E validado em dados
reais com método adequado · F informação insuficiente. **Calcular certo não é validar:** um indicador correto pode não prever nada.

## 2. Os conceitos, em uma linha cada
- **Prize mapping** — planejar a sequência de nocautes (valores 1, 2 ou 3 prêmios) que soma 6; escolher alvos e rotas alternativas.
- **Prize racing** — a corrida: quem chega a 6 primeiro, considerando ritmo e capacidade de atacar, não só a contagem atual.
- **Prize checking** — saber/estimar quais cartas estão presas nos próprios prêmios (as 6 cartas viradas no começo).
- **Prize trade** — prêmios ganhos × prêmios cedidos em cada troca de nocautes (1 prêmio que derruba um ex ganha a troca).
- **Stall** — atrasar a corrida: impedir nocautes, tirar alvos, sobreviver; pode vencer por deck acabado do adversário.
- **Control / lock** — restringir as opções do adversário (habilidades, itens, recuo, recursos) por vários turnos.
- **Disruption** — interferência pontual: mão (Iono, Judge, Unfair Stamp), Energia (Crushing Hammer), banco (Boss's Orders), etc.
- **Mill** — tirar cartas do baralho do adversário para vencer por deck acabado.
- **Sequencing / resource management** — ordem das ações no turno, uso de buscas e compras, Energia, recursos descartáveis, thinning.

## 3. O que os registros dão (medido no p0, 83 partidas de 29/10 a 05/11/2026)
- **Fim da partida:** 46 desistências (55%), 35 por prêmios, 2 sem Pokémon em jogo, **0 por deck acabado**. Desistência corta a
  corrida: quase metade das partidas não chega ao fim "natural" → toda análise de fim de partida tem de tratar a desistência como
  censura (o resultado é conhecido, o caminho até o fim não).
- **Prêmios pegos** ("took N") e o turno: observados exatamente para os dois lados. Nomes dos prêmios: só de quem exportou
  (253/253; adversário 0/235, `EVIDENCE.md`).
- **Atribuição de prêmios a cada nocaute** (`resumo.nocautes`): **inferida** e imperfeita — bate com o valor pelo nome do Pokémon em
  76% dos 372 nocautes (erra em nocautes duplos e efeitos de carta). Use os "took N", não esta atribuição.
- **Mão de quem exportou:** conhecida (exceto a mão nova depois de mulligan); do adversário só o tamanho (58/58) e as cartas reveladas.
- **Ações por turno:** mediana 8, p90 19 (jogadas, compras, Energia, evoluções, ataques, recuos) — há material para padrões de ordem,
  mas **não** as alternativas que o jogador tinha.

## 4. Matriz de observabilidade
Classificação: **O** observável (está no log), **I** inferível (reconstruído com premissas), **N** não observável (não está nos dados).
"Valida?" = existe gabarito independente nos dados para conferir o indicador.

| Conceito | Indicador | Evento / informação necessária | Origem | No Coletor hoje | Reconstrução | Premissas | Limitações | Classe | Valida? |
|---|---|---|---|---|---|---|---|---|---|
| Prize mapping | Rota executada (ex.: 2-2-2, 3-3) | "took N" por jogador, em ordem | log | sim (`replay` → `mesa[j].premios` por quadro) | queda dos prêmios entre quadros | — | não diz a rota *planejada* | **O** | sim (é o próprio log) |
| Prize mapping | Valor de prêmio do Pokémon nocauteado | nome do nocauteado + regra (ex 2, Mega ex 3, resto 1) | log + regra | parcial (`resumo.nocautes`, 76% coerente) | nome → valor; efeitos alteram | sem cartas que mudam prêmios | nocaute duplo mal atribuído | **I** | sim, contra os "took N" |
| Prize mapping | Rotas possíveis no estado (quantas, quais) | Pokémon em jogo dos dois lados, PS, dano, valor | replay | sim (mesa por quadro) | busca em estados / enumeração | alvos só os que estão em jogo | Pokémon que ainda vão entrar: desconhecidos | **I** | só a rota executada |
| Prize mapping | Rota executável com os recursos | + mão, Energia, buscas disponíveis | replay + mão | só para quem exportou | modelo de dano + recursos | mão do adversário não conta | intenção e deck restante desconhecidos | **I** (exportou) / **N** (adv.) | não |
| Prize mapping | Rota planejada | intenção | — | não | — | — | o log não registra intenção | **N** | não |
| Prize racing | Prêmios restantes por turno, diferença | "took N", turno | log | sim | contagem | — | desistência corta | **O** | sim |
| Prize racing | Turnos até 6 prêmios (cada lado) | ritmo, dano por turno, PS em jogo | replay | sim (dano, PS mínimos) | simulação simples / tempo até evento | dano repetível | ignora disrupção futura | **I** | sim, contra o fim real (quando não há desistência) |
| Prize racing | "À frente na contagem, atrás no ataque" | prêmios + capacidade de nocautear no próximo turno | replay + modelo | parcial | regra de dano vs PS do alvo | Energia/ataque conhecidos | Energia por habilidade às vezes some (73/754) | **I** | parcial |
| Prize checking | Cópias da carta X nos prêmios | lista + mão inicial + cartas vistas | Meus decks + log | só para quem exportou com lista ligada | hipergeométrica com N, m, k do estado | prêmios separados ao acaso; sem efeitos que olhem prêmios | mulligan esconde a mão nova; adversário sem lista | **I** | **sim**: prêmios pegos revelados (p0: previsto 23,4% × real 22,5%) |
| Prize checking | Prêmios do adversário | — | — | não | NB2 + lista típica do deck (só probabilidade) | lista do adversário ≈ listas do torneio | nunca revelados (0/235) | **N** (I fraco) | não |
| Prize trade | Prêmios ganhos − cedidos por troca | nocautes com valores, dos dois lados, em ordem | log | sim ("took N" + nocautes) | pareamento de trocas consecutivas | troca = nocaute seguido da resposta | definição de "troca" é escolha do analista | **O/I** | resultado da partida (associação) |
| Prize trade | Atacantes de 1 prêmio × multi-prêmio | valor de cada atacante | log + regra | sim (nome → valor) | regra de valor | idem | — | **I** | associação |
| Stall | Turnos sem nocaute / nocautes evitados | nocautes, dano, cura, "prevented" | log | sim (linhas de cura e "prevented") | contagem | — | não sabe se o adversário *podia* nocautear | **O** (fatos) / **I** (efeito) | não há casos de deck-out |
| Control / lock | Duração de um bloqueio | carta/estádio de bloqueio em jogo, turnos | log + texto da carta | parcial (estádio em jogo é observado; efeito é regra da carta) | lista de cartas de bloqueio + turnos em jogo | o efeito valeu enquanto a carta esteve em jogo | não registra o que o adversário *deixou* de fazer | **I** | não |
| Disruption | Eventos por categoria (mão, Energia, banco, habilidade) | jogadas com nome | log | sim (p0: mão em 47 de 83 partidas) | lista curada de cartas → categoria | lista de cartas atualizada por coleção | lista incompleta = subcontagem | **O** | sim (contagem) |
| Disruption | Desenvolvimento do adversário depois | jogadas/ataques do adversário nos turnos seguintes | log | sim | antes × depois, com controle | — | causalidade reversa e seleção | **I** | só associação |
| Mill | Cartas tiradas do baralho do adversário; vitórias por deck acabado | "discarded ... from deck" do adversário; fim | log | sim (linhas), mas 0 casos | contagem | — | **sem casos** nos dados atuais | **O** | não (sem casos) |
| Sequencing | Ordem das ações no turno | sequência de linhas | log | sim | padrões de sequência | — | não mostra alternativas nem a mão do adversário | **O** | associação |
| Sequencing | Thinning, preservação de recursos | cartas buscadas/descartadas, mão e deck restantes | log + lista | só quem exportou | contagem + lista | lista ligada | — | **I** | associação |
| Qualquer decisão | "Jogada X foi melhor que Y" | estado completo + alternativas + resultado contrafactual | — | não | modelo de crença + simulação | mão/deck do adversário modelados | resposta condicional ao modelo | **N** (I sob modelo) | não |

## 5. Regras de leitura (valem para toda análise estratégica)
1. O log registra **o que aconteceu**, não **o que o jogador quis** nem **o que ele podia fazer**. Não atribua plano ou erro sem prova.
2. Mão e prêmios do adversário **não são conhecidos**; qualquer conta sobre eles é probabilidade condicionada a um modelo (NB2 +
   listas de torneio) — diga o modelo.
3. Quatro "rotas" diferentes (ver `DECISION_ANALYSIS.md`): matematicamente possível · executável com os recursos conhecidos ·
   robusta às respostas plausíveis do adversário · efetivamente executada. Só a última é observada.
4. Associação temporal (disrupção → adversário trava) **não é causa**: quem joga Iono costuma estar atrás; quem trava costuma ter
   mão ruim antes. Ver `CONTROL_AND_DISRUPTION.md` §5.
5. Desistência (55%) é censura: medir "tempo até 6 prêmios" ignorando desistências enviesa para partidas equilibradas.
6. Amostra: 83 partidas pessoais, de poucos jogadores e poucos decks; torneios não têm log de jogadas (só resultado). Qualquer
   achado estratégico é, por enquanto, **exploratório** (classe D no máximo) até haver centenas de partidas.
