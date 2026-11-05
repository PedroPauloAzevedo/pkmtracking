# Painel, ícone na bandeja, atalhos e janela própria

> Atualizado em 05/11/2026. Código: `web/index.html`, `web/estilo.css`, `web/js/*.js` (divisão explicada em `web/LEIA-ME.md`),
> `tracker/bandeja.py`, `tracker/atalhos.py`, `tracker/janela.py`, `tracker/novidades.py`. Decisões: D-002, D-003, D-030.

## Painel
- Página única sem frameworks, dividida em `index.html` (esqueleto e **ordem dos scripts**), `estilo.css` e 14 arquivos em `web/js/`
  (um por área). Servidos por `/web/<arquivo>` (só .css/.js, sem cache). A tabela de qual arquivo faz o quê está em `web/LEIA-ME.md`.
- Cada tela é uma função `render<Nome>()`; rotas em `ROTAS` (no `inicio.js`, o último script), menu de 4 seções em `SECAO`,
  abas internas em `ABAS` (desenhadas por `trilha()`); rotas com id: `partida-N`, `replay-N`, `meudeck-N`, `lista-N`.
  Estado global `S` (ex.: `S.fonte`, `S.deck`, `S.rp` do replay, `S.jogadorSel` do filtro Jogador).
- Componentes: `mostrarGuia()` (primeiro uso: aparece sem nick, sem partidas e sem `guia_visto`), `abrirBusca()` (Ctrl+K),
  `seletorJogador()` (caixa de opções `details.multi` para marcar vários; ver `MATCHES_AND_PERFORMANCE.md`),
  `desenharConsistencia()`, `desenharQualDeck()`, `desenharVariantes()`, janela de novidades depois de atualizar.
- Visual: tema claro/escuro por `prefers-color-scheme`; tokens CSS em `:root` (acento amarelo `#E8B321`/`#F2C443`, azul `#2B63D9`);
  fontes Bricolage Grotesque e IBM Plex Sans/Mono. Textos curtos, em português simples, explicando o porquê ("provável entre",
  "diferença provável", "formato não confirmado"); avisos por toast e notificação do Windows.
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
depois marca e desmarca jogadores no filtro Jogador (combinação, não desmarcar todos, "Marcar todos", outra aba, recarregar).
