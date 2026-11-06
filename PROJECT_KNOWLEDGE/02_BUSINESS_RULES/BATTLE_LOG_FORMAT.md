# Formato do Battle Log (e como o programa interpreta cada linha)

> Atualizado em 06/11/2026. Conhecimento tirado dos logs reais do Pedro e dos amigos (dezenas de partidas, 02–05/11/2026).
> Usado por `tracker/leitor.py`, `tracker/replay.py` (mesa e mãos) e `tracker/decks.py`. Nos exemplos, **Ana exportou o log**
> e **Bia é a adversária** (nomes fictícios). Achou uma linha nova ou uma "mania" nova? Registre aqui.

## 1. Forma geral
- O log é o texto que o botão de exportar do Battle Log copia. O jogo precisa estar **em inglês**.
- **Linha principal:** uma ação ("Ana played Ultra Ball."). **Sublinha:** começa com `- ` e é efeito da linha principal anterior
  ("- Ana discarded 2 cards."). **Lista:** começa com `•` e dá nomes ("   • Dreepy, Basic Fire Energy").
- O jogo às vezes usa o apóstrofo curvo (`Bia’s Budew`), principalmente em "used ... on <jogador>’s ...". O leitor troca pelo reto.
- Começa com `Setup`; cada turno começa com `Ana's Turn` (logs antigos: `Turn # 1 - Ana's Turn`); turno termina com `Ana ended their turn.`
- Ataques podem vir com `- Damage breakdown:` e uma lista de parcelas (`• Base damage: 60 damage`, `• Total damage: 230 damage`).
- Fim: `Opponent conceded. Ana wins.`, `All Prize cards taken. Ana wins.`, `Opponent took all of their Prize cards. Bia wins.` e
  parecidos. Pode haver texto depois do resultado (não é erro).

## 2. Quem exportou vê mais (base de `resumo.exportou` e da mão)
| Situação | Quem exportou (Ana) | Adversária (Bia) |
|---|---|---|
| Mão inicial | `Ana drew 7 cards for the opening hand.` / `- 7 drawn cards.` / `• <7 cartas>` | Mesmas duas linhas, **sem** a lista |
| Compra do turno | `Ana drew Dudunsparce.` | `Bia drew a card.` |
| Comprar várias | `- Ana drew 4 cards.` + `• <cartas>` | `- Bia drew 4 cards.` (sem lista) |
| Devolver a mão ao baralho | `- Ana shuffled 6 cards into their deck.` + `• <cartas>` | `- Bia shuffled 7 cards into their deck.` (sem lista) |
| Prêmio pego | `Boss's Orders was added to Ana's hand.` | `A card was added to Bia's hand.` (nunca com nome) |
Prêmios: uma linha "was added to ... hand" **por carta**, em geral logo depois de `Ana took 2 Prize cards.` / `took a Prize card.`
**Exceção (jogada que vale 3 prêmios):** o jogo pode escrever parte dessas linhas **antes** do `took` (logo depois do ataque) e
o resto **depois** do nocaute, até depois de outras linhas (`Battle Cage was activated.`); visto em 2 partidas:
```
Ana's Dragapult ex used Phantom Dive on Bia’s Mega Froslass ex for 200 damage.
Crispin was added to Ana's hand.            <- prêmio escrito antes do "took"
Night Stretcher was added to Ana's hand.
Ana took 3 Prize cards.
Bia's Mega Froslass ex was Knocked Out!
Battle Cage was activated.
Buddy-Buddy Poffin was added to Ana's hand. <- o 3º prêmio, depois do nocaute
```
Conferido em 05/11/2026 nas 78 partidas gravadas: **toda** linha "was added to ... hand" é carta de prêmio; 253 de 253 prêmios de
quem exportou com nome; 0 de 235 do adversário. Nenhuma outra linha do log fala de prêmios (não há carta que olhe ou troque
prêmios nos logs): por isso o replay mostra o prêmio pego por quem exportou **desde o começo da partida**
(`../01_MODULES/REPLAY.md`, D-032).

## 3. Mulligan
```
Ana drew 7 cards for the opening hand.
- 7 drawn cards.
   • Judge, Poké Pad, Ultra Ball, Crispin, Boss's Orders, Night Stretcher, Rare Candy     <- a mão SEM Básico (a descartada)
Ana took a mulligan.
- Cards revealed from Mulligan 1
   • Judge, Poké Pad, Ultra Ball, Crispin, Boss's Orders, Night Stretcher, Rare Candy
Bia drew 1 more card because Ana took at least 1 mulligan.
- Bia drew a card.
```
**A mão nova de quem exportou não aparece no log.** O replay põe 7 cartas viradas e revela cada uma, desde o começo, quando ela é
jogada (todas as outras compras de quem exportou têm nome).

## 4. Buscar no baralho × comprar
- Sublinha com nome depois de uma carta ou habilidade = **busca no baralho**, visível para os dois: `- Bia drew Meowth ex.`
  (Ultra Ball, Poké Pad, Last-Ditch Catch...). Por isso a carta buscada aparece com a face na mão da adversária.
- Direto para a mesa, sem passar pela mão: `- Bia drew 2 cards and played them to the Bench.` + `• Dreepy, Dreepy` e
  `- Bia drew Dunsparce and played it to the Bench.`

## 5. Jogar cartas
| Linha | Significado |
|---|---|
| `Ana played Ultra Ball.` | Carta jogada **da mão** (Treinador) |
| `Ana played Budew to the Active Spot.` / `to the Bench.` / `Risky Ruins to the Stadium spot.` | Da mão para a mesa |
| `Ana played Dudunsparce.` com um Dudunsparce **em jogo** | **Habilidade** daquele Pokémon, não carta da mão |
| `Ana played Academy at Night.` com esse Estádio **em jogo** | **Usou o efeito do Estádio** (o que ele faz vem na sublinha, ex.: `- Ana put a card on top of their deck.`) |
| `Ana evolved Dreepy to Drakloak on the Bench.` | Evolução da mão. Em **sublinha** é Rare Candy (a evolução também sai da mão) |
| `Ana attached Basic Psychic Energy to Budew in the Active Spot.` | Linha principal = da mão. Em **sublinha** é efeito (descarte/baralho), exceto Teal Dance e Ripening Charge, que ligam da mão |
| `Ana retreated Munkidori to the Bench.` / `Bia's Budew is now in the Active Spot.` | Recuo e novo Ativo |
| `- Ana's Latias ex was switched with Ana's Mega Audino ex to become the Active Pokémon.` | Troca de Ativo por efeito |

## 6. Ataques, habilidades e dano
- Ataque: `Ana's Dragapult ex used Phantom Dive on Bia’s Mega Lopunny ex for 200 damage.` (sempre do Ativo, no Ativo).
- Habilidade: `Ana's Dusclops used Cursed Blast.` (pode vir do Banco).
- **Contadores — o jogo escreve o DONO ERRADO quando o alvo é do adversário:**
  `- Ana put 5 damage counters on Ana's Budew.` seguido de `Bia's Budew was Knocked Out!` → o Budew era da **Bia**.
  Acontece com Cursed Blast (Dusclops/Dusknoir), Phantom Dive (Dragapult ex, contadores no Banco) e outros.
  Quando o dono escrito é o próprio jogador, o programa decide assim: (1) se esse Pokémon é nocauteado logo depois, o dono é quem
  o perdeu; (2) se veio de um ataque/habilidade do jogador e o adversário tem um Pokémon com esse nome, é do adversário;
  (3) senão vale o escrito.
- `- 3 cards were discarded from Ana's Metagross.` + `   • Basic Metal Energy, Basic Metal Energy, Basic Metal Energy`: cartas que
  saíram de um Pokémon, com o nome de cada uma (efeito de ataque, ex.: Metallic Hammer; ou depois do nocaute, quando a lista traz também
  as pré-evoluções: `• Basic Metal Energy, Metang, Beldum`). A lista vem para os dois jogadores.
- `- Ana attached Basic Metal Energy to Metang on the Bench.` em sublinha de habilidade (ex.: Metal Maker) não diz **qual** Metang
  quando há vários no Banco; o replay decide pelas provas seguintes (D-046).
- **Estádio Risky Ruins** (`Risky Ruins was activated.` + `- X put 2 damage counters on <dono do Estádio>'s Y.`): os contadores vão
  no Básico Y que **X** acabou de pôr no Banco, mas o jogo escreve como dono **quem jogou o Estádio**. Ex.: com o Risky Ruins da
  Ana, `Bia played Budew to the Bench.` → `- Bia put 2 damage counters on Ana's Budew.` — o Budew é da Bia. O dono é sempre X
  (visto em todas as ocorrências de uma partida real de 06/11/2026; corrigido no replay, D-045).
- `- Ana put a damage counter on Ana's Latias ex.` = **1** contador ("a", não número).
- `- Ana moved 3 damage counters from Ana's Munkidori to Ana's Dhelmise.` (Adrena-Brain do Munkidori): tira de um Pokémon do
  jogador e põe num do **adversário**; o dono do destino vem errado do mesmo jeito.
- `- Bia's Buneary took 120 damage.` = dano extra de um ataque em outro Pokémon (Torrential Pump do Ogerpon ex, Trifrost copiado
  pelo Slowking). O dono vem certo. Várias linhas seguidas com o mesmo nome = Pokémon diferentes atingidos pelo mesmo golpe.
- Cura em dois formatos: `Ana healed 30 damage from Ana's X.` e `- Ana's Hydrapple ex healed 30 damage.`
- Sem efeito: `- Damage to Fan Rotom was prevented.`, `- Effects of Phantom Dive did not affect Team Rocket's Mimikyu.`
- **`- Damage breakdown:`** (170 blocos em 83 partidas, 06/11/2026; o programa ainda não lê): parcelas na **ordem do cálculo de dano
  das regras** — `• Base damage`, depois o que vem do atacante (`• (Supporter) Black Belt's Training: 40 damage`, `• (Item) Premium
  Power Pro`, `• 3 attached Energy: 120 damage`, `• Pokémon ex: 90 damage`, `• 2 heads: 100 damage`), depois `• Weakness to Grass: X`
  (X = o subtotal até ali, isto é, o dobro: 36 de 36) e `• Resistance to Fighting: -30 damage` (ou o que leva a 0: 7 de 7), e
  `• Total damage`. Manias: a parcela `• Damage: 170 damage` às vezes vem **repetida** (conte uma vez); 42 blocos não têm
  `Total damage` (só `• 4 Pokémon: 240 damage`, dano "por alguma coisa"); a linha do ataque pode trazer
  `... took 10 more damage because of Grass Weakness.` Efeito do lado do defensor ("recebe 20 a menos") não apareceu nenhuma vez.

## 7. Nocaute
- `Bia's Budew was Knocked Out!` (às vezes "is now Knocked Out"). Dois Pokémon de mesmo nome podem cair em linhas seguidas.
- **Nocaute com pouco ou nenhum dano pode estar certo:** Cursed Blast nocauteia o próprio Dusclops/Dusknoir (0 de dano);
  Terminal Period (Mega Absol ex) nocauteia o Ativo que tem exatamente 6 contadores.
- Depois do nocaute, em **linhas soltas** (sem "-"): `Basic Psychic Energy was discarded from Bia's Munkidori.`, uma por carta presa
  (às vezes `- 3 cards were discarded from Bia's Mega Lopunny ex.`), inclusive depois do "took N Prize cards" (pré-evoluções
  embaixo de um Mega, ex.: `Snorunt was discarded from Bia's Mega Froslass ex.`).
- A mesma frase vem em **sublinha** no recuo (`Ana retreated Dreepy to the Bench.` + `- Basic Darkness Energy was discarded from
  Ana's Dreepy.`), em cartas como Crushing Hammer e na Ignition Energy. Nos logs reais (05/11/2026): 136 depois de nocaute (soltas),
  4 depois do "took 3 Prize cards" (soltas), 129 de recuo, 44 de cartas como Crushing Hammer e 5 da Ignition Energy (sublinhas).
  Com dois Pokémon de mesmo nome o log não diz de qual saiu: o replay decide pelo contexto (`../01_MODULES/REPLAY.md`, D-035).
- **Nocautes ao mesmo tempo** (ex.: Cursed Blast derruba o alvo e o próprio Dusknoir): as linhas de nocaute vêm juntas, depois os
  descartes, depois os prêmios — **primeiro o adversário de quem joga o turno**, depois quem joga (8 de 8 casos com as duas linhas,
  06/11/2026), como no roteiro do ataque dos juízes (Judge Ball). Vários nocautes do mesmo dono juntos viram **um**
  `took N Prize cards` com a soma (10 de 12): só pela linha não dá para dividir esse N entre os nocauteados (`resumo.nocautes`).

## 8. Mão ↔ baralho e descarte
| Linha | Significado |
|---|---|
| `- Ana shuffled 6 cards into their deck.` (+ lista só para quem exportou) | Da mão para o baralho (Judge, Lillie's Determination, Unfair Stamp...) |
| `- Ana shuffled a card into their deck.` | 1 carta, sem nome |
| `- Ana shuffled Rosa's Encouragement into their deck.` | 1 carta, **com nome** |
| `- Ana put a card on top of their deck.` / `- Ana put 4 cards on the bottom of their deck.` | Da mão para o topo/fundo do baralho |
| `- Ana shuffled 2 cards into their deck.` logo depois de `Ana's Dudunsparce used Run Away Draw.` | É o **próprio Pokémon** (e a pré-evolução) voltando da mesa, não a mão |
| `- Ana shuffled their deck.` / `- Ana shuffled their hand.` | Não muda a mão |
| `- Ana discarded 2 cards.` + lista / `- Ana discarded Kyurem.` | Da mão (custo de Ultra Ball, Trade...). **Exceções:** Brilliant Blender e Seek Inspiration descartam do **baralho**; `- Ana discarded Nighttime Mine.` logo depois de outro Estádio entrar é o **Estádio antigo** saindo da mesa |
| `- Bia discarded 8 cards.` depois de `Ana played Xerosic's Machinations.` | Bia descarta da própria mão |
| `- Ana moved Ana's Dragapult ex to their hand.` depois de **Night Stretcher** | Do **descarte** para a mão (o Pokémon de mesmo nome que está em jogo continua lá) |
| `... and all attached cards to their hand` | Da mesa para a mão |
O número de cartas embaralhadas por Judge, Lillie's Determination, Unfair Stamp e Iono é o **tamanho real da mão**: serve para
conferir a mão montada pelo replay (`EVIDENCE.md`).

## 9. Outras linhas
Moeda (`Ana chose heads for the opening coin flip.`, `Ana won the coin toss.`, `Ana decided to go first.`, `- Ana flipped a coin and
it landed on heads.`, `- Ana flipped 3 coins, and 2 landed on heads.`), escolha de golpe copiado (`- Ana chose Trifrost`),
energias e Estádios ativados (`Enriching Energy was activated.`, `Battle Cage was activated.`). As que não mudam números estão como
"ignorar" nas regras de leitura.

## 10. Onde cada regra está no código e nos testes
`replay.py`: `dono_dos_contadores`, `achar_alvo_dos_contadores`, `achar_nocauteado`, `_Maos`, `_premios_conhecidos`,
`CARTAS_FORA_DA_MESA`, `DESCARTA_DO_BARALHO`, `LIGA_DA_MAO`, `MAO_INTEIRA`. `leitor.py`: `quem_exportou`, `conferir`, `impressao_digital`.
Cada armadilha tem um cenário em `testes/teste_replay.py`.
