# Captura de partidas (área de transferência e modo automático)

> Atualizado em 05/11/2026. Código: `tracker/coletor.py`, `tracker/auto_export.py`, `tracker/cobertura.py`, `tracker/avisos.py`,
> `tracker/diagnostico.py`. Regras relacionadas: `../02_BUSINESS_RULES/PLAYERS_AND_OWNERSHIP.md`. Decisões: D-005, D-006, D-007, D-014, D-015, D-016.

## Como uma partida entra no programa
O TCG Live não grava o log em arquivo (o `diagnostico.py` procura e, até hoje, não achou). No fim da partida, o botão
**Battle Log** abre o log e o botão de **exportar** copia o texto para a área de transferência. Três caminhos:
1. **Coletor da área de transferência** (`coletor.py`, sempre ligado por padrão): a cada `intervalo_coletor` (1 s) olha a
   área de transferência (Windows: API do próprio Windows; Mac: `pbpaste`; Linux: xclip/xsel). Texto que parece log
   (`leitor.parece_log`) é gravado por `banco.inserir_partida`. O log de exemplo do primeiro uso é reconhecido pelo hash e
   não é gravado (serve para testar a captura).
2. **Colar à mão** (tela Partidas → colar log): mesma gravação, origem `manual`.
3. **Modo automático** (abaixo): clica nos dois botões e o coletor grava (origem `automatico`).
Toda partida nova passa pela regra de dono: se o nick configurado não joga a partida, ela vai para o amigo.

## Modo automático (`auto_export.py`) — experimental, desligado por padrão
**O que faz:** a cada 2 s olha a tela; ao ver a tela de resultado, abre o Battle Log e clica em exportar.
Não lê a memória nem os arquivos do jogo e não joga: só reconhece botões e clica depois que a partida acabou
(ainda assim é automação de cliques no cliente; o README avisa "por sua conta e risco").

**Como reconhece os botões** (OpenCV, comparação de imagens em tons de cinza):
- Imagens em `modelos/`: `botao_battle_log.png` e `botao_exportar.png` (obrigatórias), `botao_continuar.png` (recomendada:
  confirma a tela de resultado e é coberta enquanto copia), `botao_fechar.png` (opcional).
- "Usar imagens prontas" baixa as do projeto Full Bench (MIT) de um commit fixo; elas foram recortadas numa tela de 1440 de
  altura. As suas antigas vão para `modelos/minhas/`.
- **Tamanho dos botões:** o esperado é `altura da área da janela do jogo / 1440` (ou da tela, se a janela não for achada).
  O tamanho que funcionou é guardado por botão em `escala_modelos`, junto com o tamanho da tela e da janela do jogo.
  **Se a tela ou a janela do jogo mudar de tamanho, o programa esquece e aprende de novo** (e anota no `programa.log`).
- **Busca:** numa cópia da tela com metade da resolução (leve: ~0,1 s a cada 2 s), testando o tamanho conhecido e os vizinhos;
  a **busca ampla** (16 tamanhos ao redor do esperado, entre 0,36 e 1,60) roda a cada 10 s enquanto o tamanho não é conhecido
  e a cada 30 s depois, por segurança.
- **Confirmação em tela inteira:** se a busca reduzida chega perto (nota ≥ 0,70) sem passar da precisão (`confianca_imagem`,
  padrão 0,85), confere na tela inteira no mesmo tamanho. O botão Battle Log é pequeno e na cópia reduzida passava raspando.
- O processo usa coordenadas em pixels reais (`SetProcessDPIAware`), para tela com zoom de 125%, 150%...

**Como captura** (`_capturar`):
1. Cobre o botão Continue com um quadro vermelho (`cobertura.py`, Win32 puro; clicar nele libera).
2. **Põe o jogo na frente** se outra janela estiver ativa (tecla Alt + `SetForegroundWindow`): com outra janela ativa o clique
   caía no lugar errado ou só "acordava" o jogo.
3. Clica em Battle Log, espera até ~10 s o botão de exportar aparecer e clica nele; espera o log chegar no coletor (até 4 s).
4. Se não chegou, tenta mais uma vez. Se ainda não chegou: conta como **perdida**, avisa (notificação do Windows) e segura o
   Continue mais 20 s para a pessoa copiar à mão.
5. Depois de tratar uma tela de resultado, só trata a próxima quando a tela some por 12 s.
Cada tentativa fica no `dados/programa.log`: `[auto] tentativa N: jogo na frente=..., botão de exportar achado=... (nota ...), log chegou=...`.

**Instalação das bibliotecas:** precisa de `requirements-auto.txt` **no Python do próprio programa** (pasta `.venv`). Um
`pip install` num terminal comum instala em outro Python e o modo continua "indisponível". O botão "Instalar o modo
automático" (Ajustes) roda o pip certo e liga o modo sem reiniciar. O instalador .exe já vem com as bibliotecas.

## Problemas já vistos e como foram resolvidos
| Data | Sintoma | Causa | Correção |
|---|---|---|---|
| 02/11 | Modo "indisponível" mesmo depois do pip | Bibliotecas instaladas em outro Python | Botão de instalar e mensagem com o comando exato (2026.11.02-4) |
| 02/11 | Reconhecia a tela, mas "perdia" a partida | Outra janela ativa na hora do clique | Põe o jogo na frente; tentativas no `programa.log` (2026.11.02-5) |
| 03/11 a 05/11 | "Vigiando a tela" sem nunca reconhecer | Tamanho dos botões preso ao da 1ª partida; jogo mudou de tamanho | Mede a janela do jogo, reaprende, busca ampla de segurança, confirmação em tela inteira (2026.11.05-1) |
Medições de cada caso: `../03_DECISIONS/EVIDENCE.md`. Referência real: jogo em janela 1600×900 num monitor 1920×1080 →
tamanho 0,62; notas Battle Log ~0,87 (reduzida), Continue ~0,94, exportar ~0,95.

## Como investigar quando "não coletou sozinho"
1. Painel → Início/Ajustes: captura ligada? Modo automático "vigiando a tela" ou "indisponível"/"sem modelos"?
2. `dados/programa.log`: tem `[auto] tentativa`? (Se não tem, a tela de resultado nem foi reconhecida.) Tem `[aviso]` de partida perdida?
3. `dados/config.json` → `escala_modelos`: tamanho guardado de cada botão e da tela/janela.
4. Para ver o que o programa "enxerga", use um script que roda a mesma busca (`AutoExport._achar`) **só sobre a área da
   janela do jogo** e sem gravar no config (D-016). Nunca fotografe a tela inteira.

## Limites conhecidos
- Depende das imagens dos botões: se o jogo mudar o visual da tela de resultado, é preciso imagens novas.
- Só Windows tem a cobertura e o "pôr na frente"; no Mac o modo precisa de permissões de Gravação de Tela e Acessibilidade.
- A correção de 05/11 ainda não foi confirmada numa partida real (ver `CURRENT_STATE.md`).
