# Evidências: medições que sustentam as decisões

> Atualizado em 10/11/2026. Antes de trocar um algoritmo, repita a medição correspondente e compare (D-017).
> Resultados completos dos experimentos 1 a 9 e da análise de ACE SPEC: `MISSION_REPORT_2026-11-02.md` (não repetidos aqui).

## Experimentos em `testes/experimentos/` (rodar numa cópia; os que gravam no banco, só com dados de teste)
| Exp. | Pergunta | Resultado / decisão |
|---|---|---|
| e1 `probabilidades` | As contas exatas da Consistência batem com uma simulação? | Batem (inclui carta com 9 cópias) → D-031 |
| e2 `identificar_deck` | Método por ícones × Naive Bayes nas listas reais | NB2 melhor, com reserva pelos ícones → D-019 |
| e3 `matchups` | Como estimar "A vence B" com poucos jogos (prevendo torneios novos com os antigos)? | Confronto ajustado, k = 24 → D-018 |
| e4 `desempenho` | Tempo das análises com muitos dados | Decisões ~2,7 s com mil partidas (limite conhecido) |
| e5 `variantes` | Agrupar listas parecidas (k-medoides, silhueta) | Grupos nítidos nos decks mais jogados; modelo mantido como alternativa |
| e6 `uso_cartas` | A versão rápida de Uso de cartas dá o mesmo resultado? | Idêntica e mais rápida (a lenta fica para conferência) |
| e7 `inserir` | Tempo para gravar uma partida conforme o banco cresce | Ver relatório da missão |
| e8 `analise_rapida` | Análises pessoais mais rápidas sem mudar o resultado? | Resultados idênticos (inclui NB2 com e sem índice) |
| e9 `ace_spec` | A ACE SPEC separa versões? Qual agrupamento prevê melhor? | Modelo M5 (por ACE SPEC); sub-versões pioram → D-020 |
| e10 `regressao_cartas` | Efeito de cada carta prevê melhor que o método atual? | log-loss 0,6665 (L2 = 300) × 0,6674 só com o deck × 0,857 bruto com/sem → D-021 |

## Replay nas partidas reais (02/11/2026, versões -6 → -7)
**Método:** montar o replay de todas as partidas gravadas no computador do Pedro (dois bancos, 31 partidas) com a versão antiga e a
nova, e contar (a) momentos em que um Pokémon **continua em jogo com dano ≥ PS** (estado impossível; não conta o quadro logo antes
de um nocaute) e (b) **nocautes com dano menor que os PS**. Os PS vêm da versão da carta escolhida pelo replay.
| Medida | Antes (2026.11.02-6) | Depois |
|---|---|---|
| Momentos com Pokémon em jogo e dano ≥ PS | 96 | **0** |
| Nocautes com dano < PS | 41 | **14** — todos corretos: Dusclops/Dusknoir que se nocauteiam com Cursed Blast (0 de dano) e Terminal Period do Mega Absol ex (6 contadores) |
A escolha de versão das cartas só mudou onde devia (o Dunsparce de 60 PS nocauteado com 60 de dano). → D-010, D-011, D-012.

## Mão dos jogadores (03/11/2026, versão 2026.11.03-1)
**Método:** cada vez que Judge, Lillie's Determination ou Unfair Stamp manda a mão inteira para o baralho, o log diz o tamanho real
da mão; comparar com a mão montada pelo replay. Também contar jogadas de quem exportou que a mão montada não explicava.
| Medida | Resultado |
|---|---|
| Mão de quem exportou | **51 de 51** conferências exatas |
| Mão do adversário | **58 de 58** conferências exatas |
| Jogadas de quem exportou sem a carta na mão montada | **0** |
Para chegar aí foram corrigidos: "shuffled <carta> into their deck" (uma carta com nome), Seek Inspiration e Brilliant Blender
(descartam do baralho), uso de Estádio em jogo ("played Academy at Night.") e o Estádio antigo descartado. → D-013.

## Prêmios no replay (05/11/2026, versão 2026.11.05-2)
**Método:** todas as partidas gravadas no computador do Pedro (dois bancos abertos só para leitura: 127 registros, 78 partidas
diferentes) montadas com a versão publicada (2026.11.05-1) e a nova; comparar quadro a quadro e contar os prêmios com nome.
| Medida | Resultado |
|---|---|
| Linhas com "Prize" no log | só `took a Prize card` / `took N Prize cards` e as linhas de fim de partida: nenhuma carta olha ou troca prêmios |
| Linhas "<carta> was added to X's hand." | **todas** são cartas de prêmio; 482 logo depois do `took`, 4 logo antes e 2 depois do nocaute (2 jogadas de 3 prêmios) |
| Prêmios pegos por quem exportou que aparecem desde o começo | **253 de 253** (a 1ª versão do código, que só olhava as linhas logo depois do `took`, achava 247) |
| Prêmios pegos pelo adversário com nome | **0 de 235** (sempre "A card") |
| Partidas com algum prêmio conhecido desde o começo | 64 de 78 (nas outras 14 quem exportou não pegou prêmio) |
| Quadros com mesa ou mão diferente da versão publicada | **0** (mudou só o destaque das 781 linhas de carta de prêmio, nos 127 registros) |
| Quadros com a contagem de prêmios restantes diferente | 4 por banco, só nas cartas escritas antes do `took` (agora saem dos prêmios na hora) |
| Quadros com mais prêmios conhecidos que restantes | **0** |
→ D-032.

## Partidas repetidas pela impressão digital (05/11/2026, versão 2026.11.05-3)
**Método:** no banco atual do Pedro (76 partidas, todas com impressão digital; aberto só para leitura), contar as impressões que
aparecem mais de uma vez, separando donos diferentes (o mesmo jogo pelos dois lados) e o mesmo dono (jogos diferentes com o
mesmo resumo, que a regra antiga escondia em "Todos os jogadores").
| Medida | Resultado |
|---|---|
| Mesmo jogo pelos dois lados (donos diferentes) | 3 (1 entre o Pedro e um amigo; 2 entre dois amigos): continuam contando uma vez |
| Mesma impressão no mesmo dono | **0**: a regra nova (D-033) não muda nada nos dados de hoje; evita sumir partida no futuro |
Nos dados de teste (`teste_tracker.py`: 14 partidas suas parecidas entre si, 1 da amiga e o outro lado de uma das suas) a regra
antiga deixava **6 de 16** em "Todos"; a nova deixa **15** (as 14 + a da amiga; o outro lado do mesmo jogo conta uma vez). → D-033.

## Energias ambíguas e listas de descarte no replay (06/11/2026, versão 2026.11.06-5)
`main` (com o Risky Ruins) × nova, 154 partidas (banco do Pedro só leitura + instalação antiga):
| Conferência | `main` | Nova |
|---|---|---|
| Ataques em que o atacante tinha menos Energia que o custo (custo pela biblioteca) | 82 de 840 | 42 de 840 (nenhum caso novo) |
| Ataques com 3 ou mais Energias a mais que o custo (Energia empilhada no Pokémon errado) | 5 | 4 |
| Nocautes em que as cartas presas no replay batem com a lista do log | 178 de 221 | 204 de 221 |
| Descartes de ataque com lista: o Pokémon tinha as cartas listadas | 16 de 21 | 18 de 21 |
| Descartes de uma carta ("X was discarded from"): sublinhas que tiram de quem está em jogo / soltas depois de nocaute que tiram (errado) | 200 de 202 / 0 | igual |
As duas primeiras linhas usam provas que a correção também usa (custo do ataque, lista do nocaute): a melhora é em parte esperada; a
2ª e a 5ª são independentes. 117 partidas mudam (a maioria só por as Energias descartadas saírem da mesa). → D-046.

## Risky Ruins no replay (06/11/2026, versão 2026.11.06-3)
- Logs do Pedro e dos amigos: 145 linhas de contadores logo depois de `Risky Ruins was activated.`; em 55 o dono escrito é o outro
  jogador (quem jogou o Estádio), e em todas o Básico é de quem pôs o Pokémon no Banco na linha anterior.
- Replay da `main` × corrigido, 154 partidas (banco do Pedro só leitura + instalação antiga): 15 partidas mudam (935 quadros);
  quadros com Pokémon em jogo com dano ≥ PS mínimo (impossível, inclui o quadro do golpe fatal antes da linha do nocaute):
  1742 → 1660. → D-045.

## Carta presa descartada no replay (05/11/2026, versão 2026.11.05-5)
135 partidas reais (o banco do Pedro, com as dos amigos, e a instalação antiga), versão publicada (2026.11.05-3) × nova:
| Conferência | Antes | Depois |
|---|---|---|
| Sublinhas (recuo, Crushing Hammer, Ignition Energy): a carta saiu de um Pokémon em jogo | 141 de 182 (41 não tiraram nada) | 182 de 182 |
| Linhas soltas depois de nocaute: tiraram a carta de um Pokémon que continuava em jogo (errado) | 2 de 150 | 0 de 150 |
| Ataques em que o atacante tinha menos Energia presa que o custo do golpe (custo pela biblioteca) | 78 de 754 | 73 de 754 (nenhum caso novo) |
31 partidas mudaram (4.626 quadros), sempre a partir de uma linha "was discarded from". Os 73 ataques que sobram vêm de Energias
que o log não mostra ligando (habilidades, cartas que aceleram) ou de custos reduzidos; não têm relação com o descarte. → D-035.

## Lista de partidas e "Ver todas" (05/11/2026, versão 2026.11.05-5)
- **Registro do Coletor do Pedro:** o primeiro pedido da lista depois de um tempo parado levava de 3 a 10 s (e 0 s logo depois);
  duas telas eram desenhadas ao mesmo tempo (pedidos repetidos no mesmo segundo).
- **Cópia com os dados do Pedro** (`/api/partidas` com ele e um amigo, 80 partidas únicas): versão publicada 2,24 s no 1º pedido,
  0,14 s logo depois e 2,21 s com as contas 3 minutos mais velhas; versão nova 2,65 s no 1º (feito em segundo plano ao abrir),
  0,10 s logo depois e 0,08 s com as contas 3 minutos mais velhas. Deck identificado igual nas 80 partidas, nas duas versões.
- **"Ver todas" com o Início atrasado 1,5 s de propósito:** versão publicada: endereço `#partidas`, tela do Início; versão nova:
  tela de Partidas. → D-037.

## Ícones dos decks (05/11/2026, versão 2026.11.05-6)
- Cadastro do Pedro: 122 de 134 decks sem ícone, todos regravados em 05/11 às 19:55 (reimportação de um torneio do Labs).
- Página `/0078/decks` do Labs: leitura antiga 0 ícones; nova 81 de 81 decks com ícone.
- Cópia com os dados do Pedro, ao abrir a versão nova: 32 de 134 decks sem ícone (os que não estão nos 2 torneios mais recentes) e
  as 67 partidas da lista (ele e um amigo) com ícone nos dois decks. → D-038.

## Modo automático
- **Jogo real (02/11/2026):** jogo em janela 1600×900 num monitor 1920×1080 → tamanho dos botões 0,62. Notas na tela de resultado:
  Battle Log 0,86–0,87 na cópia reduzida (precisão exigida 0,85), Continue 0,94, exportar 0,95. Falhas observadas só com outra
  janela ativa no clique (→ D-014).
- **Simulação (05/11/2026):** tela de resultado montada com as imagens dos botões no tamanho que o jogo desenha (altura/1440), partindo
  do tamanho guardado 0,62, 20 s de vigia:
| Tamanho do jogo | Antes (tamanho preso) | Depois (2026.11.05-1) |
|---|---|---|
| Janela 1600×900 | não achou (0,84) | achou (0,90) |
| Tela cheia 1920×1080 | não achou (0,43) | achou (0,91) |
| Janela 1280×720 | não achou (0,42) | achou (0,88) |
  Custo: ~0,1 s a cada 2 s na vigia normal; busca ampla ~0,5 s (a cada 30 s com tamanho conhecido); confirmação em tela inteira
  só no tamanho que chegou perto. → D-015. **Falta confirmar com o jogo real.**

## Auditoria estatística (06/11/2026, código `76a2005`)
Cópia de teste com os dados do Pedro (33 torneios, 44.651 partidas, 5.695 listas). Scripts em
`.claude/skills/statistical-analyst/experiments/a1..a6`, resultados em `experiments/resultados/*.json`. Detalhes e leitura em
`STATISTICAL_AUDIT_2026-11-06.md`.
| Medida | Resultado |
|---|---|
| Taxa de quem tem lista × sem lista (Labs / online) | 61,9% × 50,3% / 52,1% × 27,9%; +4,0 a +6,1 pp nos 12 decks mais jogados |
| Confronto ajustado: log-loss no teste, k = 16 × 24 | 0,6776 × 0,6778; diferença −0,0002 [−0,0010; +0,0010]; calibração ±1,5 pp |
| Confronto ajustado com < 10 jogos × chute 50% | +0,0053 [−0,0083; +0,0214] (sem diferença clara) |
| Efeito das cartas (L2 = 300) × deck sozinho | −0,0007 [−0,0020; +0,0003]; 0 de 392 cartas "prováveis" |
| Identificação, 2 / 5 / 12 cartas: ícones, NB2, regra do programa | 19,0 / 52,3 / 74,4%; 63,6 / 84,4 / 91,8%; 51,2 / 83,3 / 92,0% |
| Variantes: marcas da tela × Holm × BH (q < 0,10) | 7 × 2 × 7 (de 87 testes) |
| ICC das partidas de um jogador nos torneios | −0,015 (efeito de desenho 1,00) |
| Partida melhor de 3 × jogo único (Labs, 128 confrontos) | 4,35 pp mais longe de 50% em média |
Os experimentos e1, e3, e5, e6, e9 e e10 foram refeitos no mesmo dia (`STATISTICAL_INVENTORY_2026-11-06.md`, seção 4); o e2 tem a
coluna "atual" com vazamento (achado 9). → D-039.

### Rodada de hardening da Skill (06/11/2026) — `STATISTICAL_HARDENING_2026-11-06.md`
Experimentos `a7`–`a9` (só leem; registro completo em `.claude/skills/statistical-analyst/experiments/resultados/`). Revisões, não
substituições: as linhas acima continuam valendo no recorte em que foram medidas.
| Medição | Resultado |
|---|---|
| ICC por recorte (torneios, W/L; faixa por bootstrap de jogadores) | com lista −0,015 [−0,020; −0,011]; sem lista +0,034; **todos +0,063 [+0,059; +0,068]**; Labs +0,096; online −0,010 |
| Identificação com cartas vistas realistas (a8), turno 1 / 2 / 6: ícones, NB2, programa | 31,7 / 53,1 / 78,1%; 63,4 / 81,0 / 91,0%; 57,5 / 79,3 / 91,3% |
| Programa − NB2 (erro), turnos 1 e 2 | +5,9 pp [+4,1; +7,2]; +1,7 pp [+0,5; +2,7] — mas F1 macro no turno 2: programa 0,58 × NB2 0,53 |
| Vazamento do cadastro de ícones no a4 (ícones: cadastro de todos − só treino) | −0,3 a 0,0 pp (sem diferença clara) |
| Identificação real (18 partidas, 1 deck), turno 2 / fim: ícones, NB2 = programa | 16,7 / 77,8%; 66,7 / 88,9% |
| Calibração do NB2 (a8) | ECE10 0,031 [0,024; 0,043], piso 0,006; inclinação 0,56 ± 0,02 (confiança exagerada) |
| Calibração do confronto ajustado k = 24 (a9) | ECE10 0,015 [0,007; 0,030], piso 0,009; inclinação 0,81 ± 0,05; pior que 50% em 4 de 10 torneios de teste |
| Força geral (Bradley-Terry) × chute | ECE10 0,006 (o menor) com log-loss 0,6921 × 0,6931: ECE baixo sem poder de previsão |
| a4 refeito com a ponte só leitura e a versão 2026.11.06-1 | mesmos números de 06/11 (hash igual com 12 algarismos) |

## Etapas do ataque nos logs (06/11/2026, experimento a12 da Skill)
Roteiro dos juízes (Judge Ball, rev. nov/2024) conferido em 83 partidas reais (cópia marcada, só leitura).
| Medida | Resultado |
|---|---|
| Blocos `Damage breakdown` | 170 (128 com `Total damage`; 35 com a parcela `Damage` repetida) |
| Fraqueza = dobro do subtotal com os efeitos do atacante | 36 de 36 (6 depois de bônus do atacante) |
| Resistência −30 ou até 0, depois dos efeitos do atacante | 7 de 7 (3 depois de bônus) |
| Efeitos do lado do defensor no breakdown | 0 |
| Nocautes ao mesmo tempo dos dois jogadores: o adversário de quem joga pega prêmio primeiro | 8 de 8 (9 casos, 1 sem as duas linhas) |
| Vários nocautes do mesmo dono juntos → um só "took N" | 10 de 12 |
Resultado em `.claude/skills/statistical-analyst/experiments/resultados/a12_*.json`.

## Onde estão os scripts dessas medições
Os experimentos e1–e10 estão no repositório. Os scripts das medições do replay, das mãos e da simulação do modo automático foram
escritos durante as sessões e ficaram **fora do repositório** (no computador do Pedro; ver `CLAUDE.local.md`). O método está descrito
acima para poder refazê-los; trazê-los para `testes/experimentos/` está no `BACKLOG.md`.

## Torneios online na chegada da Delta Reign (09/11/2026, D-048)
API de play.limitlesstcg.com, torneios Standard de 05 a 09/11/2026. Maior: 07/11, 494 jogadores, deck mais jogado Mega Rayquaza (70),
Talonflame Dusknoir com 10; vários com "DELTA REIGN LEGAL" no nome desde 06/11. Numa cópia com os dados do Pedro, os 7 torneios com
100 ou mais jogadores de 05 a 08/11 importados: com a época Delta Reign e a fonte Todos entram os 5 de 06 a 08/11 (987 jogadores,
792 com deck; Mega Rayquaza 13,0% do campo, Talonflame Dusknoir 19 jogadores); os 2 de 05/11 (01h30 e 17h10 UTC, antes da chegada às
18h UTC) ficam na 30th Celebration; nos grandes eventos a Delta Reign ainda não tem torneio.

## Códigos das cartas no log (10/11/2026, D-049)
Leitor de antes × de depois nas 137 partidas da cópia com os dados do Pedro (logs sem código): 0 leituras diferentes (script
`cmp_leitor.py` fora do repositório, comparando `ler_partida` campo a campo, sem `resumo.codigos`). Log público com códigos
(Training Court, 19 turnos): os nomes saem limpos; 50 de 61 códigos acham a carta na biblioteca (os outros são reimpressões de
coleções antigas, `sm`/`swsh`, que seguem pelo nome); o replay monta os 423 quadros e `resolver_versoes` usa os códigos.
