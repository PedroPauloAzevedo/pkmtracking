# Evidências: medições que sustentam as decisões

> Atualizado em 05/11/2026. Antes de trocar um algoritmo, repita a medição correspondente e compare (D-017).
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

## Onde estão os scripts dessas medições
Os experimentos e1–e10 estão no repositório. Os scripts das medições do replay, das mãos e da simulação do modo automático foram
escritos durante as sessões e ficaram **fora do repositório** (no computador do Pedro; ver `CLAUDE.local.md`). O método está descrito
acima para poder refazê-los; trazê-los para `testes/experimentos/` está no `BACKLOG.md`.
