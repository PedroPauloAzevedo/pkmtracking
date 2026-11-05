# Replay da partida

> Atualizado em 05/11/2026. Código: `tracker/replay.py` (montagem), `tracker/decks.py` (`resolver_versoes`, `_limites_ps`),
> `web/js/replay.js` (desenho). Rota: `/api/partidas/<id>/replay`. Tela: `#replay-<id>`.
> Regras do log: `../02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md`. Decisões: D-010 a D-013 e D-032. Medições: `../03_DECISIONS/EVIDENCE.md`.

## O que faz
Para cada linha do log guarda uma "foto" (quadro): Pokémon Ativo e Banco de cada jogador (com dano, energias e ferramentas),
prêmios restantes (**com a face os que o log revela**), Estádio, nocauteados, **a mão de cada jogador** e o destaque daquela linha.
O painel só desenha os quadros.
O replay é montado na hora em que a tela abre: corrigir o replay vale também para as partidas antigas (não precisa reler nada).

## Mesa e dano
- Pokémon com o mesmo nome do mesmo lado são diferenciados por um número interno (`uid`).
- **Dono dos contadores:** o log escreve "X put N damage counters on X's Y" mesmo quando Y é do adversário. O dono certo é
  descoberto pelo nocaute que vem logo depois ou pelo ataque/habilidade que causou o dano (`dono_dos_contadores`).
- "moved N damage counters" (ex.: Munkidori): tira de um Pokémon e põe no do adversário, com a mesma correção de dono.
- "took N damage" (dano extra no Banco) e cura nos dois formatos ("healed N damage from X's Y" e "X's Y healed N damage").
- **Mesmo nome, mesmo lado:** se o ataque acertou o Ativo com esse nome, os contadores extras vão para o do Banco
  (Phantom Dive só põe no Banco); no nocaute, cai o que tem mais dano; num golpe que acerta vários ("took N damage" repetido),
  cada linha vai para um Pokémon diferente.
- **Contadores ambíguos:** quando o log não diz qual de dois Pokémon de mesmo nome recebeu contadores, o replay anota a
  escolha; se um nocaute depois fica com falta exatamente desse valor (pelos PS mínimos da carta, considerando os golpes que
  ela usou), o replay é montado de novo com a escolha corrigida (`_correcoes`, segunda passada).
- Night Stretcher (e Super Rod, Lillie's Determination) pegam do descarte/mão: não tiram o Pokémon da mesa.
- Regra do jogo respeitada: não se evolui um Pokémon que entrou em jogo (ou evoluiu) no mesmo turno.

## Mão dos jogadores (`_Maos`, desde 2026.11.03-1)
- **Quem exportou:** mão conhecida carta a carta (mão inicial listada, compras com nome, listas dos "drew N cards").
- **Adversário:** cartas viradas ("drew a card"); aparecem com a face só as que ele **buscou no baralho** ou recebeu com nome
  (ex.: Night Stretcher). Ao jogar uma carta conhecida, ela sai; ao jogar uma desconhecida, sai uma virada. O prêmio que o
  adversário pega entra virado (o log escreve "A card").
- Saem da mão: jogar, ligar (linha principal; em sublinha só Teal Dance e Ripening Charge ligam da mão), evoluir (inclusive
  Rare Candy), descartar ("discarded", menos Brilliant Blender e Seek Inspiration, que descartam do baralho, e o Estádio
  trocado), embaralhar no baralho ("shuffled N cards / a card / <carta> into their deck") e pôr no topo/fundo do baralho.
- **Mulligan de quem exportou:** o log lista a primeira mão (a descartada), não a nova. As 7 cartas novas começam viradas; as
  que ele joga depois são reveladas **desde o começo da partida** (borda tracejada, `inferida`), porque todas as outras compras
  dele têm nome. Isso não vale para o adversário (não dá para saber quando a carta entrou).
- **Conferência:** quando Judge, Lillie's Determination, Unfair Stamp ou Iono fazem a mão inteira voltar ao baralho, o log diz
  quantas cartas eram; o replay compara com a mão montada (`conferencia_maos`) e esvazia a mão (lista `MAO_INTEIRA` no código).
- Na tela: mão do adversário em cima, a sua embaixo; carta que acabou de entrar destacada; mouse em cima aumenta a carta.

## Prêmios (`_premios_conhecidos`, desde 2026.11.05-2)
- Depois de `X took N Prize cards.` vem uma linha `<carta> was added to X's hand.` por carta. Para **quem exportou** ela traz o
  nome; para o adversário vem sempre `A card` (nenhuma exceção nos logs conferidos; `EVIDENCE.md`).
- Os 6 prêmios são separados na preparação e nenhuma linha do log os troca depois. Por isso **o prêmio pego estava lá desde o
  começo**: em cada quadro, `mesa[jogador]["premios_conhecidos"]` lista (nome, turno em que foi pego) os prêmios que o jogador
  **ainda vai pegar**. Os demais prêmios restantes ficam virados.
- O quadro do "took" já tira os prêmios pegos; cada linha "was added" vira destaque `premio` com a carta (com nome) e põe a carta na
  mão (`_Maos`).
- **Fora de ordem (jogada de 3 prêmios):** a carta escrita **antes** do "took" (achada por `premio_logo_adiante`, que procura o
  "took" do mesmo jogador nas próximas linhas do turno) sai dos prêmios na hora, e o "took" tira só o que faltava (`adiantados`); a
  escrita **depois** do nocaute ainda conta para aquele "took" (`premio_aberto` fica aberto até completar ou até o turno acabar).
  Só conta como prêmio a linha "was added" com um "took" aberto ou logo adiante.
- Se o log não trouxer o nome de um prêmio, ele fica virado (não aconteceu nos logs conferidos).
- **Não** se tenta descobrir os prêmios restantes pela lista do deck: as cartas que não apareceram podem estar no baralho ou nos
  prêmios (D-032).
- Na tela: grade de 6 espaços (3 × 2) ao lado do nome; com a face e borda tracejada = conhecido (mouse em cima aumenta e diz o turno
  em que foi pego); verso = virado; tracejado vazio = já pego. Classe `premio-carta` (a classe `premio` já é usada na tabela de
  eventos da partida).

## Versão de cartas com o mesmo nome (`decks.resolver_versoes`)
Ordem: (0) só versões válidas no Standard; (0b) **PS compatíveis com o replay** — nocauteado com D de dano tem no máximo D PS,
quem ficou em jogo com D tem mais de D (o dano fatal, mostrado antes do nocaute, não conta; nocaute sem dano não diz nada);
(1) ataque/habilidade usado que só uma versão tem; (2) a versão da sua lista de Meus decks ligada à partida, se tiver os PS
compatíveis; (3) a mais usada nas listas dos torneios; (4) a mais recente.

## Testes e medições
- `testes/teste_replay.py`: logs curtos com cada armadilha (Cursed Blast, Phantom Dive, Munkidori, cura, Night Stretcher,
  dois de mesmo nome, contador ambíguo, versão pelo nocaute), 7 cenários de mão e 12 conferências de prêmios (conhecidos desde o
  começo, saída no "took", destaque e mão, prêmio do adversário virado, prêmio sem nome, jogada de 3 prêmios fora de ordem, nunca
  mais conhecidos que restantes).
- Medições nas partidas reais (estados impossíveis, nocautes curtos, tamanho da mão, prêmios): `EVIDENCE.md`.

## Limites conhecidos
- Energia ligada a Pokémon de mesmo nome no Banco pode cair no Pokémon errado (o log não diferencia).
- A mão do adversário só mostra o que o log revela; a ordem das cartas na mão não é a do jogo.
- Prêmios do adversário e prêmios que ninguém pegou nunca aparecem (o log não os mostra). Se um dia aparecer no log uma carta que
  olha ou troca prêmios (nenhuma até 05/11/2026), a regra "desde o começo" precisa ser revista para ela.
