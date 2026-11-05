# Estatísticas e análises: fórmulas, limites e números

> Atualizado em 05/11/2026. Cada número aqui foi escolhido por medição (`../03_DECISIONS/EVIDENCE.md`); mudar exige medir de novo (D-017).
> Código: `tracker/analises.py`, `tracker/estrategia.py`, `tracker/decks.py`, `tracker/variantes.py`, `tracker/regressao.py`,
> `tracker/probabilidades.py`.

## Taxas
- **Taxa de vitória = V / (V + D + E)** (empates contam, como no Limitless). Vale também para o confronto ajustado.
- **Faixa de confiança de 95%** pelo método de Wilson (z = 1,96): onde a taxa "verdadeira" provavelmente está.
- Começando × indo em segundo sempre separados nas aberturas e no ritmo (o 1º turno de quem começa é outro jogo).
- Decisões são correlações: mostram padrões para investigar, não provam causa.

## Campeonatos (`estrategia.py`)
- **Força de cada deck (Bradley-Terry):** chance de A vencer B = forçaA / (forçaA + forçaB), usando todas as partidas.
- **Confronto ajustado:** p = (vitórias + k × previsão_pela_força) / (jogos + k), com **k = 24** ("jogos imaginários", exp. 3).
  Na tela de Matchups a **taxa real é o padrão**; a ajustada é opção (D-018).
- **Taxa esperada contra o campo:** média dos confrontos ajustados, pesada pela presença de cada deck.
- **Equilíbrio do meta:** mistura de decks que nenhum outro explora (jogo de soma zero), por *fictitious play*.
- **Tendência:** participação por torneio; agrupa por semana quando há mais de 20 torneios.

## Identificação do deck pelas cartas reveladas (`decks.py`, D-019)
1. **NB2** (Naive Bayes sobre as cartas das listas dos torneios): decide se houver pelo menos **200 listas** de torneio e
   confiança **≥ 0,5**; suavização pela frequência geral da carta (β = 2); decks com menos de **3 listas** não entram.
2. Senão, **método por ícones** (Pokémon do ícone do arquétipo + cartas típicas, pesando as exclusivas do deck).
3. Senão, **palpite pelo dano** (leitor). Partida ligada a uma lista de Meus decks usa o arquétipo da lista.

## Versões de um deck (`variantes.py`, D-020)
- Separadas pela **ACE SPEC** (modelo M5 do exp. 9). ACE SPEC usada por poucas listas (**< 8% ou < 8 listas**) entra na versão mais
  parecida; duas ACE SPEC com listas quase iguais (**distância < 0,12**) viram uma versão só.
- **"Diferença provável"** só com **p < 0,05** e **≥ 30 jogos**.
- Distância entre listas: 1 − (cartas em comum, contando cópias) / (cartas das duas juntas) (Jaccard ponderado). Até 300 listas
  por deck (acima, sorteia). O modelo antigo por semelhança (k-medoides, silhueta ≥ 0,25) continua em `variantes_por_semelhanca`.

## Efeito de cada carta (`regressao.py`, D-021)
chance de vencer = logística(confronto ajustado [fixo] + ajuste do deck + Σ efeito_c × (cópias_c − cópias mais comuns_c)).
Só cartas cujo número de cópias muda em pelo menos **12 listas**; todas juntas; freio **L2 = 300** (exp. 10: log-loss 0,6665 contra
0,6674 só com o deck e 0,857 do método bruto com/sem). "Efeito provável" só quando o efeito passa de 2 vezes a incerteza.
Leitura: associação, não prova.

## Consistência da lista (`probabilidades.py`, D-031)
- Contas **exatas** (hipergeométrica: sorteio sem reposição), não simulação. C(a, b) = número de jeitos de escolher b cartas de a.
- O deck é dividido em categorias (a carta, outros Básicos, o resto); percorrem-se todas as divisões da mão de 7.
- **A mão que vale tem pelo menos 1 Pokémon Básico:** as divisões sem Básico são descartadas e as outras somam 100% (o mulligan é
  condição). Mulligans esperados por partida = p / (1 − p).
- Compras e prêmios saem das 53 cartas restantes; por simetria tanto faz a ordem (prêmios não precisam ser separados das compras).
- "Duas cartas juntas": inclusão-exclusão nas compras (1 − sem A − sem B + sem as duas).
- **Não considera o efeito das cartas** (buscas e compras extras): os números são um piso. Exemplo conferido em `../01_MODULES/MY_DECKS.md`.
