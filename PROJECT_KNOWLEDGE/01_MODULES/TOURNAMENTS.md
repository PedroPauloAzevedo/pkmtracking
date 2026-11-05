# Campeonatos: importação e análises de meta

> Atualizado em 05/11/2026. Código: `tracker/limitless.py` (importação), `tracker/analises.py` (meta, matchups, perfil, cartas),
> `tracker/estrategia.py`, `tracker/variantes.py`, `tracker/regressao.py`, `tracker/decks.py` (arquétipos, ícones),
> `web/js/campeonatos.js`. Fórmulas e limites: `../02_BUSINESS_RULES/STATISTICS.md`. Decisões: D-018 a D-021.

## Importação
- **Grandes eventos:** Limitless Labs (classificação, arquétipo de cada jogador, listas do topo — `listas_top`, padrão 64) +
  RK9 (resultado de cada mesa, rodada a rodada; o link vem da página do Labs). Labs não tem API: leitura do HTML, respeitando
  robots.txt e com pausa de 0,6 s entre páginas.
- **Formato do evento:** o Labs não mostra; vem do índice `limitlesstcg.com/tournaments?show=100` (`tr[data-format]`) e da página
  do evento (id do Labs). Cache em `dados/limitless_formatos.json`. Evento que não aparece no índice fica "formato não
  confirmado" e **entra** nas contas; outro formato fica no banco e **fora** das contas.
- **Torneios online:** API pública de play.limitlesstcg.com (`/tournaments?game=PTCG&format=STANDARD`, `/standings` com deck e
  lista, `/pairings`). Sem chave: 50 pedidos a cada 5 min (pausa de 6,5 s, trata 429; ~14 s por torneio). Ids `on-<id>`;
  só torneios com pelo menos `online_min_jogadores` (64) dos últimos `online_dias` (21), no máximo `online_por_vez` (40) por vez.
- **Sincronização automática:** a cada `sincronizar_horas` (6) importa os eventos dos últimos `sincronizar_dias` (45) que faltam,
  e depois os online. Também por `python app.py --sincronizar` ou `--importar <id>`.
- ACE SPEC de cada lista gravada em `t_jogadores.ace_spec` na importação (e recalculada quando a biblioteca de cartas muda).

## Análises (Meta e torneios)
- **Fonte:** Grandes eventos / Online / Todos (`S.fonte` no painel, `torneios_da_fonte` no código). Só torneios Standard.
- **Meta:** participação, taxa de vitória, conversão para o corte, matriz de matchups, tendência (por semana quando há mais de 20 torneios).
- **Qual deck jogar?:** força de cada deck (Bradley-Terry), taxa esperada contra o campo, pior confronto, equilíbrio do meta.
- **Matchups:** taxa real (padrão) ou ajustada (opção).
- **Perfil de deck:** participação, matchups, melhores colocações (com a ACE SPEC de cada jogador), esqueleto, taxa esperada,
  **ACE SPEC e versões** (tabela com cada ACE SPEC e "diferença provável").
- **Uso de cartas:** % das listas, média de cópias, distribuição, vitória com/sem; **Efeito de cada carta** (regressão
  logística, desde 2026.11.02-7) quando um deck é escolhido; comparação de duas listas.
- **Cartas x matchups:** para um deck, a taxa contra cada adversário conforme o número de cópias de uma carta (só jogadores
  com lista importada).
- Exportações CSV: `/exportar/meta.csv`, `/exportar/torneios.csv`, `/exportar/eventos.csv`.

## Limites conhecidos
- Labs e o índice do Limitless são HTML: mudança de layout quebra a importação dos grandes eventos.
- Nenhuma divisão do deck em versões prevê o resultado individual melhor que o deck inteiro: versões servem para descrever (exp. 9).
- "Efeito de cada carta" é associação, não prova (quem usa a carta pode ser um jogador melhor).

## Testes
`testes/teste_tracker.py` monta um torneio sintético no formato do Labs e do RK9 e confere meta, matchups e CSV.
Experimentos: e2 (identificar deck), e3 (matchups), e5/e9 (variantes e ACE SPEC), e6 (uso de cartas), e10 (efeito de cada carta).
