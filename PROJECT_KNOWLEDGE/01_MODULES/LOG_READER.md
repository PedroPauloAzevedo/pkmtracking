# Leitor do log e regras de leitura

> Atualizado em 05/11/2026. Código: `tracker/leitor.py`, `tracker/regras_padrao.json`, `tracker/revisao.py`.
> Formato do log e suas "manias": `../02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md`.

## O que faz
Transforma o texto do Battle Log em dados: jogadores, eventos (turno, compra, jogada, evolução, energia, ataque, nocaute,
prêmio, recuo, vitória...) e um **resumo** guardado em `partidas.dados_json`. Tudo o que as telas de partidas mostram vem daqui.

## Regras de leitura
- Cada regra é uma expressão regular com grupos nomeados: `(?P<player>)` jogador, `(?P<card>)` carta, `(?P<target>)` alvo,
  `(?P<dano>\d+)`/`(?P<qtd>)` número, `(?P<n>)` turno. A sintaxe do JavaScript `(?<nome>...)` também é aceita.
- Padrão do programa: `tracker/regras_padrao.json` (27 regras: turno, moeda, ordem, mulligan, compra, jogada, evolução,
  energia, ataque, nocaute, prêmio, recuo, fim de turno, vitória e 11 regras "ignorar" para frases que não mudam números).
- Cada pessoa tem uma cópia editável em `dados/regras.json` (tela Programa → Regras de leitura, com "Testar linha").
  Ao salvar regras, todas as partidas são relidas.
- Antes de ler, cada linha passa por `limpar_linha`: troca o apóstrofo curvo (’) pelo reto e tira o "- " das sublinhas.

## Resumo de cada partida (`resumo` em `dados_json`)
`primeiro` (quem começou), `vencedor`, `motivo`, `turnos`, `por_jogador` (prêmios, nocautes, dano, ataques, mulligans,
jogadas, energias, evoluções), `cartas` reveladas por jogador, `nocautes`, `serie`, `deck_palpite`, `primeiro_nocaute`,
`linha_final`, e mais três campos:
- **`exportou`** — quem exportou o log (pontua quem tem compras com nome e mão inicial listada; linhas "- " de efeito não contam).
- **`problemas`** — avisos de log incompleto: não achou os dois jogadores; falta a linha final com o resultado; falta a mão
  inicial de um jogador; mais de 6 prêmios para um jogador; mais de 80 turnos. ("Texto depois do resultado" **não** é
  problema: logs reais têm.)
- **`digital`** — impressão digital do jogo (vencedor, perdedor, turnos, motivo, prêmios), igual nos logs dos dois lados.
Quando falta a linha de cara/coroa, quem começou = quem joga o 1º turno; quando falta a linha final, vencedor = quem completou 6 prêmios.

## Reler partidas
Aumentar `banco.VERSAO_LEITOR` (hoje 3) quando o leitor passar a tirar informação nova: na abertura seguinte todas as
partidas gravadas são relidas a partir do texto guardado. Mudar as regras de leitura também relê tudo.

## Linhas não lidas (`revisao.py`, tela Programa → Linhas não lidas)
Frases que nenhuma regra reconhece viram "linhas não lidas". São agrupadas em modelos (`{J}` jogador, `{C}` carta, `{N}` número),
e para cada modelo a pessoa escolhe **Ignorar** (vira regra "ignorar") ou **Criar regra** (a expressão é montada a partir do
modelo). Depois de salvar, as partidas são relidas.

## Testes
`testes/teste_tracker.py` lê o log de exemplo de `testes/leitor-tcg-live.html` e confere jogadores, vencedor, motivo, turnos,
prêmios, palpite de deck e linhas não lidas.
