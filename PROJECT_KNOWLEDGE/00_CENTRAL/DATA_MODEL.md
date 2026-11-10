# Modelo de dados (banco, formato do leitor e registro de migrações)

> Atualizado em 10/11/2026. Fonte: `tracker/banco.py` (`ESQUEMA` e `iniciar()`) e `tracker/leitor.py`. Esta seção saiu do
> [`ARCHITECTURE.md`](ARCHITECTURE.md) para ter um lugar único onde registrar mudança de banco e de formato (COLLABORATION, seção 6).
> Pasta `dados/` e `config.json`: ver `ARCHITECTURE.md`.

## 1. Banco `dados/tracker.db` (SQLite, um por pessoa, nunca no Git)
Esquema em `banco.ESQUEMA`; colunas em **negrito** foram acrescentadas por migração em `banco.iniciar()` (registro na seção 3).
- `partidas` (id, hash UNIQUE, capturada_em, origem [area_transferencia/automatico/manual/amigo], arquivo, texto, dados_json,
  meu_deck, deck_adv, notas, tags, **deck_id**, **dono**). `dados_json` = saída do leitor (seção 2), relida quando
  `banco.VERSAO_LEITOR` (hoje **3**) muda ou quando as regras de leitura mudam. `dono` vazio = de quem usa o programa; senão, o nick do amigo.
- `torneios` (id: Labs `0078` ou online `on-<id>`, nome, data, jogadores, rk9, importado_em, info_json, **fonte** labs/online, **formato**).
- `t_jogadores` (torneio, labs_id, nome, nome_norm, pais, posicao, pontos, v, d, e, arquetipo, **ace_spec**); nos online,
  labs_id = nome_norm = usuário em minúsculas. `ace_spec` NULL = sem lista; `''` = lista sem ACE SPEC.
- `t_partidas` (torneio, rodada, mesa, j1, j2, res1 W/L/T, arq1, arq2); j1/j2 casam com `t_jogadores.nome_norm`.
- `t_listas` (torneio, labs_id, carta, set_code, numero, qtd, **carta_id**, **carta_base**); carta_id/carta_base = arte básica.
- `arquetipos` (slug, nome, icones JSON, atualizado_em).
- `meus_decks` (id, nome, arquetipo, lista, notas, ativo, criado_em, versao_de, **favorito**, **icones_manual**, **lista_oficial**);
  `meus_decks_cartas` (deck_id, qtd, nome, set_code, numero, secao, carta_id, carta_base).
- Índices: `ix_tj`, `ix_tp`, `ix_tl` (por torneio).
- Quem grava: quase todo SQL está em `banco.py`; também há SQL em `decks.py`, `lista_oficial.py`, `compartilhar.py` e em poucas
  rotas do `app.py`. Leitura genérica: `banco.consultar(sql, params)`.

## 2. Formato `dados_json` (contrato do leitor)
`leitor.ler_partida(texto, regras)` devolve `{jogadores, eventos, nao_lidas, resumo}`. É lido por `banco` (dono, impressão digital),
`analises`, `decks` (identificação), `replay` e pelo painel (via `/api/partidas`).
- `jogadores`: os dois nomes, na ordem em que aparecem.
- `eventos`: uma entrada por linha reconhecida, com `linha`, `turno`, `jogador`/`dono`, `tipo`, `regra`, `carta`, `valor`, ...
- `nao_lidas`: `{linha, texto}` das linhas que nenhuma regra reconheceu (alimentam a tela de Revisão).
- `resumo`: `primeiro`, `vencedor`, `motivo`, `turnos`, `por_jogador` (prêmios, nocautes, ... de cada um), `cartas`, `nocautes`,
  `serie`, `deck_palpite`, `primeiro_nocaute`, `linha_final`, `vistas` (cartas reveladas por jogador), `exportou` (quem exportou),
  `problemas` (avisos de log estranho), `digital` (impressão digital para achar o mesmo jogo pelos dois lados), `codigos`
  (desde 2026.11.10-1: `{jogador: {código da carta: vezes}}`, vazio em logs sem código; D-049).
- Regra: **acrescentar** campo é seguro (quem não conhece ignora); mudar o significado de um campo existente exige procurar todos os
  usuários (`grep` do nome do campo em `tracker/`, `app.py` e `web/js/`). Campo novo tirado do log → aumentar `banco.VERSAO_LEITOR`.
- Linhas do log e suas "manias": [`../02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md`](../02_BUSINESS_RULES/BATTLE_LOG_FORMAT.md).

## 3. Registro de migrações (acrescente uma linha a cada mudança)
Regra (COLLABORATION, seção 6): só acrescentar coluna ou tabela; migração em `banco.iniciar()` conferindo se a coluna existe;
`INSERT` com nome das colunas; testar abrindo um banco de versão anterior. "Desde" = primeira versão do GitHub em que a mudança aparece.

| Desde | Mudança | Observação |
|---|---|---|
| 2026.10.29-3 | `t_listas.carta_id`, `t_listas.carta_base` | Bancos da versão anterior ganham as colunas vazias |
| 2026.10.29-3 | `partidas.deck_id` | Lista de Meus decks usada na partida |
| 2026.10.29-3 | `meus_decks.favorito` | |
| 2026.10.29-5 | `meus_decks.icones_manual` | Ícones corrigidos à mão |
| 2026.10.29-7 | `partidas.dono` | Partidas de amigos (D-008) |
| 2026.11.02-2 | `meus_decks.lista_oficial` | Lista oficial editada |
| 2026.11.02-2 | `torneios.fonte`, `torneios.formato` | Torneios online; só Standard nas contas (D-001) |
| 2026.11.02-2 | `t_jogadores.ace_spec` | Calculada uma vez para as listas já importadas (D-020) |
| 2026.11.02-2 | `banco.VERSAO_LEITOR` = 3 | Partidas relidas na abertura |
| 2026.11.10-1 | `banco.VERSAO_LEITOR` = 4; `dados_json.resumo.codigos` | Partidas relidas na abertura (códigos das cartas, D-049) |
| 2026.11.10-7 | `config.versao_regras_arq` = 1 (`banco.VERSAO_REGRAS_ARQ`) | `t_jogadores.arquetipo` e `t_partidas.arq1/arq2` refeitos uma vez pela regra D-052 |

Outros números que forçam refazer dados guardados: `cartas.VERSAO_INDICE` (hoje **2**; remonta o índice em `dados/cartas/`).
