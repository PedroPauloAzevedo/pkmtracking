# Visão geral do Coletor TCG Live

> Atualizado em 06/11/2026. O estado do momento (versão, pendências) fica em `../05_SESSION_CONTROL/CURRENT_STATE.md`.

## O que é
Programa **local** que **grava e analisa as partidas de Pokémon TCG Live** e **importa campeonatos** para estudar o meta.
Roda no computador de quem joga, ao lado do jogo, com um painel no navegador (ou numa janela própria).

- Captura o Battle Log que o jogo exporta no fim de cada partida (vigia a área de transferência; um modo automático
  opcional clica nos botões do jogo).
- Estatísticas pessoais, replay da partida (com a mão dos dois jogadores e os prêmios que o log revela), decisões de abertura, consistência das listas.
- Campeonatos: meta, matchups, "Qual deck jogar?", perfil de deck (ACE SPEC e versões), uso de cartas e efeito de cada carta.
- Lista no formato oficial da Play! Pokémon em PDF, troca de logs entre amigos, atualização em um clique pelo GitHub.

## Para quem
- **Dono:** Pedro (GitHub `PedroPauloAzevedo`). Trabalha com finanças, usa Excel, está aprendendo a programar:
  **toda explicação para ele é em português do Brasil, simples, sem jargão**, dizendo o que foi feito e por quê.
- **Usuários:** o Pedro e cerca de 3 amigos, todos no Windows. O programa também roda no Mac, sem os extras do Windows.
- **Desenvolvedores (desde 06/11/2026):** o Pedro e um segundo desenvolvedor, no Mac, cuja prioridade é o programa funcionar por
  inteiro no Mac (D-044). Fluxo a dois: `COLLABORATION.md`.
- Interface, mensagens e documentação em português do Brasil. O jogo é usado **em inglês** (o leitor depende disso).

## Limites de escopo (decisões firmes; ver `../03_DECISIONS/DECISIONS.md`)
- **Só formato Standard.** Nada de Expanded, Unlimited ou formatos limitados; torneio de outro formato fica fora das contas.
- **Só computador.** Nada para celular (nem layout, nem testes, nem acesso pela rede).
- **Só local.** O servidor do painel atende apenas o próprio computador (127.0.0.1) e recusa pedidos de outros sites.
- **Os dados de cada pessoa ficam com ela** (pasta `dados/`), nunca vão para o GitHub nem são tocados pelo atualizador.

## Funcionalidades (todas implementadas e testadas, salvo indicação)
- **Abrir:** ícone perto do relógio (clique abre o painel; botão direito liga/desliga a captura e Sai; bolinha verde =
  captura ligada; aviso do Windows a cada partida), atalho na Área de Trabalho, abrir com o Windows, painel em janela
  própria ou aba do navegador, instalador .exe que não precisa de Python.
- **Menu:** Início · Minhas partidas (Partidas, Desempenho, Decisões) · Meus decks · Meta e torneios (Meta, Matchups,
  Perfil de deck, Uso de cartas, Cartas x matchups, Torneios) · Programa (Regras do Standard, Ajustes e captura, Amigos,
  Biblioteca de cartas, Linhas não lidas, Regras de leitura). Busca com Ctrl+K.
- **Primeiro uso guiado:** nick, jogo em inglês e teste da captura com o log de exemplo.
- **Partidas:** captura pela área de transferência; colar log à mão; aviso de log incompleto; detecção de quem exportou;
  partidas em que o seu nick não joga vão para Amigos; detalhe, replay, notas e correção de deck.
- **Modo automático (experimental):** reconhece a tela de resultado, abre o Battle Log e exporta sozinho.
  Funcionou com o jogo real em 02–03/11; a correção de 05/11 (jogo mudando de tamanho) ainda precisa ser confirmada numa
  partida real (ver `CURRENT_STATE.md`).
- **Desempenho e Decisões:** taxas com faixa de confiança, começando × indo em segundo, por adversário, aberturas.
- **Meus decks:** listas, conferência do Standard, Consistência (probabilidades exatas), Lista oficial em PDF.
- **Campeonatos:** grandes eventos (Limitless Labs + RK9) e torneios online (API do Limitless); seletor de Fonte;
  Qual deck jogar?; taxa real ou ajustada nos matchups; ACE SPEC e versões; uso e efeito de cada carta; tendência.
- **Amigos:** filtro Jogador; exportar/importar .zip; pasta compartilhada do Google Drive automática.
- **Atualização:** aviso de versão nova, atualização em um clique, janela com as novidades.

## Glossário
| Termo | Significado |
|---|---|
| Battle Log / log | Texto da partida que o jogo exporta (copia para a área de transferência) no fim de cada partida |
| Quem exportou | Jogador de cujo computador o log saiu: vê o nome de tudo o que compra (`resumo.exportou`) |
| Dono da partida | `''` = partida sua; nick de um amigo = partida dele (coluna `partidas.dono`) |
| Impressão digital | Resumo do jogo (vencedor, perdedor, turnos, motivo, prêmios) igual nos dois lados: o mesmo jogo exportado por dois amigos conta uma vez |
| Arte básica | A impressão de menor raridade de uma carta; todas as artes de uma carta funcional viram ela (conversor) |
| Carta funcional | Mesmo nome + mesmos ataques/habilidades (+ PS, se Pokémon) |
| Arquétipo | Nome do deck como o Limitless usa (ex.: `dragapult-ex`) |
| NB2 | Identificação do deck pelas cartas reveladas (classificador Naive Bayes, com reserva pelos ícones) |
| Confronto ajustado | Taxa de A contra B que mistura o resultado real com a previsão pela força geral (k = 24) |
| Versões do deck | Grupos de listas de um deck separados pela ACE SPEC |
| Labs / RK9 | Limitless Labs (classificação, decks, listas) e RK9 (resultado de cada mesa) dos grandes eventos |
| Linha não lida | Frase do log que nenhuma regra de leitura reconhece |
| Cópia de teste | Cópia do programa numa pasta curta, na porta 8799, onde todo teste é feito |
