# Regras do Standard e do jogo usadas pelo programa

> Atualizado em 05/11/2026. O texto completo das regras está em `docs/regras-standard.md` (lido pelo programa; não repetido aqui).
> Código: `tracker/regras_jogo.py`, `tracker/lista_oficial.py`, `tracker/probabilidades.py`, `tracker/replay.py`. Decisão: D-001.

## Escopo
**Só formato Standard.** Torneio de outro formato fica no banco mas fora das contas (entram formato `''` — não confirmado — ou
`'standard'`). Nada de Expanded, Unlimited, limitados ou formatos alternativos.

## Lista (deck)
- 60 cartas; até **4 com o mesmo nome** (versões diferentes da mesma carta **somam**; Energia Básica não tem limite);
  **1 ACE SPEC** no máximo; pelo menos **1 Pokémon Básico**.
- Só cartas com **marca de regulamento válida** (lidas da tabela da base de regras; em 05/11/2026: H, I e J) ou reimpressões com
  marca válida, mesmo nome e mesmo texto; promos antigos liberados pelo nome (item "Promos já liberados" da base).

## Partida
- Mão inicial de 7; mão **sem nenhum Pokémon Básico** = mulligan (embaralha e compra 7 de novo); cada mulligan dá 1 carta extra ao rival.
- **6 prêmios** por partida; nocautear Pokémon **ex** dá 2 prêmios e **Mega Evolution ex** dá 3 (efeitos de outras cartas à parte).
- Os dois jogadores compram 1 carta no começo do próprio turno, **inclusive quem começa** no 1º turno.
- Primeiro turno: quem começa não ataca nem joga Apoiador; ninguém evolui no próprio primeiro turno nem evolui um Pokémon que
  entrou em jogo (ou evoluiu) naquele turno. O replay respeita isso ao escolher qual Pokémon evoluiu.
- Taxa de vitória conta empates no denominador (como o Limitless; ver `STATISTICS.md`).

## Divisões de idade (Lista oficial)
A temporada começa em 1º de setembro. Temporada iniciada no ano A: Junior = nascidos em A-11 ou depois; Senior = de A-15 a A-12;
Masters = A-16 ou antes.

## Onde cada regra é usada
| Regra | Usada em |
|---|---|
| Marcas e promos válidos | Conferência de listas, escolha da versão de cartas de mesmo nome, Lista oficial |
| 60 / 4 / ACE SPEC / Básico | Conferência do Standard (Meus decks) |
| Mulligan, mão de 7, compras, 6 prêmios | Consistência (probabilidades), replay, leitor (problemas: "mais de 6 prêmios") |
| Prêmios por tipo de Pokémon | Replay e análises de prêmios |
| Primeiro turno e evolução | Decisões (aberturas por quem começou) e replay |
