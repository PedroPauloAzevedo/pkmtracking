# Captura de partidas (área de transferência e modo automático)

> Atualizado em 13/11/2026. Código: `tracker/coletor.py`, `tracker/auto_export.py`, `tracker/cobertura.py`, `tracker/avisos.py`,
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

**Leve com o jogo fechado** (desde 2026.11.10-4; ideia do Full Bench): no Windows, antes de cada olhada, `estado_do_jogo()` procura
a janela "Pokemon TCG Live". Fechada ou minimizada: nada de foto da tela, só nova conferência em 5 s (`ESPERA_SEM_JOGO`), status
"esperando o jogo abrir"/"jogo minimizado". Medido em 10/11/2026 no computador do Pedro: cada olhada (foto da tela + redução) custa
~120 ms a cada 2 s; a conferência da janela, ~7 ms. Fora do Windows, olha a tela como antes.

**Como captura** (desde 2026.11.13-3: `_comecar`, `_passo`, `_encerrar`). Não segue mais uma sequência fixa de cliques: a cada
volta (0,7 s durante um fim de partida) olha a tela e faz **só o passo que falta**. Motivo: a pessoa também mexe no jogo nessa hora
(abre o Battle Log antes, copia sozinha, fecha o log, clica em Continue) e a sequência fixa clicava onde já não havia botão.
1. **Começa** quando vê a tela de resultado (Battle Log + Continue). Também começa com o log já aberto por você (botão de exportar
   em 2 voltas seguidas e, havendo `botao_fechar.png`, com o X junto), porque o ícone de exportar pode existir em outras telas.
   O log aberto só é procurado perto de um fim de partida.
2. Cobre o botão Continue com o quadro vermelho (`cobertura.py`) e liga a **trava do mouse** (`trava_mouse.py`, opção
   `travar_mouse`, padrão ligada): por até 20 s os **seus** cliques dentro da janela do jogo não chegam ao jogo. Os cliques do
   programa passam (o Windows os marca como "injetados", `LLMHF_INJECTED`). Fora do jogo o mouse funciona; mexer o mouse também.
   Clicar no quadro vermelho solta tudo. Gancho `WH_MOUSE_LL`, sem administrador; se o programa fechar, o Windows tira o gancho.
   Por que não "desligar o mouse" do computador inteiro: `BlockInput` exige administrador e trava o teclado junto.
3. A cada volta, pelo que está na tela **agora**:
   - o log chegou na área de transferência (por você ou por ele) → pronto: não clica mais nada, solta o mouse, tira o quadro e
     fecha o log se foi ele quem abriu;
   - log aberto (exportar na tela) → clica em exportar (no máximo 3 vezes, 5 s entre uma e outra);
   - tela de resultado com o log fechado → clica em Battle Log (no máximo 8 vezes, 6 s entre uma e outra; um aviso do jogo por
     cima engole o clique, e a busca dos botões não percebe porque ignora o brilho).
   **Antes de cada clique**, tira uma foto nova só em volta do botão e confere se ele ainda está ali (`_confirmar`).
   Só clica com o jogo na frente; puxa o jogo para a frente uma vez só por fim de partida, depois espera você voltar.
4. **Desiste de clicar** depois dos limites ou de 75 s: avisa (notificação do Windows), solta o mouse e segura o Continue mais 20 s
   para você copiar à mão. Se o log chegar, conta como capturada.
5. **Encerra** quando a tela de resultado e o log somem por 12 s (você clicou em Continue, por exemplo). Se o log não veio, conta como
   **perdida** e avisa. Jogo minimizado no meio: pausa (solta o mouse) e continua quando você voltar, por até 3 minutos.
   Jogo fechado: encerra.
Registro em `dados/programa.log`: `[auto] fim de partida detectado`, `clique em Battle Log (Nª vez; brilho do botão ...; nota ...)`,
`clique em exportar (Nª vez)`, `log chegou (pelo botão de exportar | copiado por você) em N s`, `trava do mouse segurou N clique(s)`,
`não consegui copiar sozinho (...)`, `partida NÃO copiada: <motivo>`. Brilho bem mais baixo que o normal = algo escurecendo a tela.

**Mesmo log copiado de novo:** o coletor não grava outra vez, mas marca que o log chegou (o contador da área de transferência do
Windows mudou). Antes, o modo automático achava que a cópia tinha falhado.
**Janela do jogo que some por um instante:** com a mesma tela, o modo fica com o tamanho de janela já conhecido em vez de apagar
os tamanhos aprendidos dos botões.

**Instalação das bibliotecas:** precisa de `requirements-auto.txt` **no Python do próprio programa** (pasta `.venv`). Um
`pip install` num terminal comum instala em outro Python e o modo continua "indisponível". O botão "Instalar o modo
automático" (Ajustes) roda o pip certo e liga o modo sem reiniciar. O instalador .exe já vem com as bibliotecas.

## Problemas já vistos e como foram resolvidos
| Data | Sintoma | Causa | Correção |
|---|---|---|---|
| 02/11 | Modo "indisponível" mesmo depois do pip | Bibliotecas instaladas em outro Python | Botão de instalar e mensagem com o comando exato (2026.11.02-4) |
| 02/11 | Reconhecia a tela, mas "perdia" a partida | Outra janela ativa na hora do clique | Põe o jogo na frente; tentativas no `programa.log` (2026.11.02-5) |
| 03/11 a 05/11 | "Vigiando a tela" sem nunca reconhecer | Tamanho dos botões preso ao da 1ª partida; jogo mudou de tamanho | Mede a janela do jogo, reaprende, busca ampla de segurança, confirmação em tela inteira (2026.11.05-1) |
| 02/11 a 13/11 | 43 de 76 partidas: "botão de exportar achado=False", 2ª tentativa com a mesma nota | Clique em Battle Log não abre o log (provável aviso do jogo por cima; a busca ignora o brilho); 2ª tentativa fechava log aberto; tamanhos apagados quando a janela "sumia" | Novas tentativas enquanto a tela fica aberta, confere o log aberto antes de clicar, brilho no registro, guarda o tamanho da janela (ramo `fix/modo-automatico-captura`, 13/11) |
| 13/11 | Clicava em botões avulsos depois que você clicou em Continue; ficava esperando quando você abria o log antes | Sequência fixa de cliques, sem olhar a tela antes de cada clique; o log aberto não era reconhecido como fim de partida | Passo a passo pelo que está na tela, confirmação antes de cada clique, trava dos seus cliques no jogo, limites de tempo em todos os passos (2026.11.13-3) |
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
