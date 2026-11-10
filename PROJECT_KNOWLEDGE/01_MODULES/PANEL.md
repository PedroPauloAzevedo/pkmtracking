# Painel, ícone na bandeja, atalhos e janela própria

> Atualizado em 09/11/2026. Código: `web/index.html`, `web/estilo.css`, `web/js/*.js` (divisão explicada em `web/LEIA-ME.md`),
> `tracker/bandeja.py`, `tracker/atalhos.py`, `tracker/janela.py`, `tracker/novidades.py`. Decisões: D-002, D-003, D-030, D-037.

## Painel
- Página única sem frameworks, dividida em `index.html` (esqueleto e **ordem dos scripts**), `estilo.css` e 14 arquivos em `web/js/`
  (um por área). Servidos por `/web/<arquivo>` (só .css/.js, sem cache). A tabela de qual arquivo faz o quê está em `web/LEIA-ME.md`.
- Cada tela é uma função `render<Nome>()`; rotas em `ROTAS` (no `inicio.js`, o último script), menu de 4 seções em `SECAO`,
  abas internas em `ABAS` (desenhadas por `trilha()`); rotas com id: `partida-N`, `replay-N`, `meudeck-N`, `lista-N`.
  Estado global `S` (ex.: `S.fonte`, `S.deck`, `S.rp` do replay, `S.jogadorSel` do filtro Jogador).
- **Tela velha não cobre a nova** (desde 2026.11.05-5; D-037): cada `render<Nome>()` começa com `const vez = novaTela()` e,
  depois de esperar os dados, só desenha se `!telaVelha(vez)`. Atualizações atrasadas (`setTimeout`) conferem `aba()`. Se a tela
  demora mais de 0,3 s, `render()` apaga a anterior e mostra "Carregando…" (`body.carregando`). Era o "Ver todas" que não fazia nada.
- Componentes: `mostrarGuia()` (primeiro uso: aparece sem nick, sem partidas e sem `guia_visto`), `abrirBusca()` (Ctrl+K),
  `seletorJogador()` (caixa de opções `details.multi` para marcar vários; ver `MATCHES_AND_PERFORMANCE.md`),
  `desenharConsistencia()`, `desenharQualDeck()`, `desenharVariantes()`, janela de novidades depois de atualizar,
  `seletorEpoca()` (campo Época; ver `MATCHES_AND_PERFORMANCE.md` e `TOURNAMENTS.md`) e `graficoLinhas(..., { marcas })`
  (linha tracejada onde começa uma época).
- Visual: tema claro/escuro por `prefers-color-scheme`; tokens CSS em `:root` (acento amarelo `#E8B321`/`#F2C443`, azul `#2B63D9`);
  fontes Bricolage Grotesque e IBM Plex Sans/Mono. Textos curtos, em português simples, explicando o porquê ("provável entre",
  "diferença provável", "formato não confirmado"); avisos por toast e notificação do Windows.
- **Início** (desde 2026.11.09-4; `renderPainel` em `partidas.js`): cabeçalho com o tema; "Hoje" (`contasHoje`/`painelHoje`:
  placar do dia, sessão = partidas com menos de `SESSAO_MIN` = 60 min entre uma e outra, última partida, sequência atual, V–D dos
  últimos 14 dias com partidas; segue o filtro Jogador); números gerais; últimas partidas; "Dados coletados" (`painelDados`, rota
  `/api/resumo-geral`, contagens do banco inteiro); colar log à mão.
- **Tema** (desde 2026.11.09-3; no Início desde 2026.11.09-4): botões Claro / Automático / Escuro no topo do Início (`#tema`,
  `seletorTema`/`ligarTema` em `base.js`). Automático segue o Windows
  (`prefers-color-scheme`); Claro e Escuro ficam em `<html data-tema>` e valem por cima dele. A escolha fica no `localStorage`
  (`tema`), aplicada por um script curto no `<head>` do `index.html` (a tela não pisca) e pelos botões em `base.js` (`aplicarTema`).
  Cor nova no `estilo.css`: dar o valor escuro nos dois lugares (media query e `:root[data-tema="escuro"]`).
- **Tabela de colunas iguais** (`table.matriz.iguais`, desde 2026.11.09-2; Cartas x matchups): `table-layout: fixed`, as 3
  primeiras colunas com 80px e as de deck dividindo o resto por igual; o nome do deck quebra em linhas. A tabela tem `min-width` de
  ~112px por deck (com muitos decks, rola para o lado).
- **Largura e altura** (desde 2026.11.06-6): `main` vai até 2000px (antes 1240px, que deixava faixa vazia em telas largas); as
  listas `.tabela.alta` têm altura máxima `max(520px, 100vh − 300px)`, o log do replay `max(380px, 100vh − 420px)` e a coluna
  lateral do replay `clamp(300px, 22vw, 420px)`. Textos longos continuam com largura própria (`.sub` 70ch, `.rg-doc` 82ch).
- **Só computador** (D-002): sem regras de celular. As regras de **janela estreita** ficam (até 900px o menu vira faixa superior;
  até 1100px o replay fica numa coluna), porque servem à janela do Coletor em meia tela ao lado do jogo.
- Segurança: todas as rotas passam pela proteção de origem (`app.so_pedidos_do_painel`).

## Ícone perto do relógio (`bandeja.py`, só Windows, precisa de pystray + pillow)
Clique abre o painel; botão direito: Abrir painel, Captura ligada/desligada, Sair; bolinha verde = captura ligada, cinza =
desligada; aviso do Windows a cada partida nova. Sem pystray, volta à janela preta.

## Atalhos (`atalhos.py`, só Windows)
"Coletor TCG Live" na Área de Trabalho e na pasta Inicializar (abrir com o Windows), apontando para o `pythonw.exe` da `.venv`, com
`web/icone.ico`. A pasta vem da API do Windows (o PowerShell devolvia "Área de Trabalho" com acento quebrado). O instalador cria o
da Área de Trabalho; o Início sugere uma vez; Ajustes → Como abrir o programa liga/desliga os dois.

## Janela própria (`janela.py`)
Painel no modo "aplicativo" do Edge (ou Chrome), sem abas nem barra de endereço, com perfil próprio em `dados/janela`.
Sem Edge/Chrome, ou com `abrir_em` = "navegador", abre uma aba no navegador padrão.

## Testes
`testes/teste_telas.py` abre todas as telas no Edge (porta 8799, largura 1366) e falha com erro de JavaScript ou resposta 5xx;
depois marca e desmarca jogadores no filtro Jogador (combinação, não desmarcar todos, "Marcar todos", outra aba, recarregar),
clica em "Ver todas" com o Início atrasado de propósito (tem que abrir Partidas) e confere o campo Época e os separadores.
