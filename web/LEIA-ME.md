# Painel do Coletor

O painel é uma página só (`index.html`) dividida em arquivos menores, sem frameworks:

- `index.html`: o esqueleto (menu lateral, área principal, aviso) e a lista de scripts, **na ordem em que carregam**.
- `estilo.css`: todo o visual (tema claro/escuro, menu, tabelas, replay, lista oficial).
- `js/`: um arquivo por área. São scripts comuns (não módulos): uma função criada num arquivo pode ser usada em
  qualquer outro, e o que roda ao carregar só pode usar o que veio **antes** na lista.

| Arquivo | O que tem |
|---|---|
| `base.js` | estado global `S`, `api()`, `esc()`, componentes reutilizáveis (gráfico com o separador de época), status da captura, rotas (`SECAO`, `ABAS`, `trilha()`, `render()` com `novaTela`/`telaVelha` e o "Carregando…"), seletor de época (`seletorEpoca`, `comEpoca`), ícones dos decks |
| `partidas.js` | Início, Partidas, detalhe da partida, Desempenho, filtro Jogador |
| `campeonatos.js` | Meta, Qual deck jogar?, Matchups, Perfil de deck, Uso de cartas, Cartas x matchups, Torneios |
| `programa.js` | Ajustes e captura, Regras de leitura |
| `replay.js` | Replay da partida |
| `revisao.js` | Linhas não lidas |
| `decks.js` | Meus decks (lista, cadastro, ícones) |
| `decisoes.js` | Decisões |
| `amigos.js` | Amigos (trocar logs) |
| `deck_detalhe.js` | página de um deck: conferência do Standard, Consistência |
| `biblioteca.js` | Biblioteca de cartas |
| `lista_oficial.js` | Lista oficial (PDF) |
| `regras_standard.js` | Regras do Standard |
| `inicio.js` | novidades, primeiro uso guiado, busca (Ctrl+K) e a partida do painel (fica por último) |

Toda tela (`render...()`) começa com `const vez = novaTela();` e, depois de esperar os dados, só desenha se a vez ainda for
dela: `if (telaVelha(vez)) return;`. Assim uma tela lenta que termina depois não cobre a tela que a pessoa abriu em seguida.

Arquivo novo em `js/`: acrescente a linha `<script src="/web/js/NOME.js"></script>` no `index.html`, antes do `inicio.js`.
Os testes de tela (`testes/teste_telas.py`) abrem cada tela no navegador e avisam se alguma der erro.
