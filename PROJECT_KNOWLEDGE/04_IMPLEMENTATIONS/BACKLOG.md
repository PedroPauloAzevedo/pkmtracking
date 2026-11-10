# Backlog: ideias e pendências

> Atualizado em 09/11/2026. Em ordem de prioridade dentro de cada grupo. Ao começar um item, mova para `IN_PROGRESS.md`;
> ao terminar, registre em `DONE.md`. Sempre pergunte ao Pedro antes de começar algo grande.

## Prioridade alta
1. **Scripts de medição no repositório:** trazer para `testes/experimentos/` as medições do replay (estados impossíveis, nocautes
   curtos), das mãos (tamanho real no Judge/Lillie's/Unfair Stamp), dos prêmios (versão publicada × nova) e a simulação do
   modo automático (`EVIDENCE.md`). Hoje estão só no computador do Pedro. É código de teste (não muda o programa): pedir
   autorização.

## Paridade no Mac (prioridade do segundo desenvolvedor; D-044)
Levantado no código em 06/11/2026, sem teste num Mac (tabela "Windows × Mac" em `../00_CENTRAL/ARCHITECTURE.md`). Cada item é um PR
próprio, com o código do Mac dentro de `if sys.platform == ...` e os 4 testes no Mac **e** no Windows.
- **M1. Conferir o básico no Mac:** instalar por `instalar_mac.command`, rodar os 4 testes, capturar uma partida real pela área de
  transferência (`pbpaste`) e anotar o que falhou. Primeiro passo: diz quais dos itens abaixo são reais.
- **M2. Ícone na barra de menus** (`bandeja.py`; hoje `app.py` só liga no Windows). O `pystray` tem suporte a Mac, mas precisa rodar
  na thread principal.
- **M3. Janela própria do painel** (`janela.py` só procura Edge/Chrome no Windows; no Mac, o Chrome fica em `/Applications`).
- **M4. Abrir sozinho ao ligar o Mac e atalho** (`atalhos.py`; no Mac seria um item de login ou um `.app`/LaunchAgent).
- **M5. Modo automático no Mac** (`auto_export.py`): achar a janela do jogo e pô-la na frente; telas Retina (escala 2×) mudam o
  tamanho dos botões; a cobertura do Continue (`cobertura.py`) é Win32. Depende de medição com o jogo real (D-017; imagens só da
  janela do jogo, D-016).
- **M6. Instalação mais simples no Mac** (hoje: Terminal + Python instalado à parte; não há equivalente do instalador .exe).
- **M7. Diagnóstico** (`diagnostico.py`): confirmar onde o TCG Live do Mac guarda arquivos.

## Vindos da pesquisa de outros apps (09/11/2026; detalhes em `../03_DECISIONS/REFERENCE_TOOLS.md`, seção 2)
- **R1. Códigos das cartas no log** (`(sv6_200) Dragapult ex`, opção *Hide card IDs from export* desmarcada): hoje o leitor guarda
  o código como parte do nome. Tirar do nome e usar para a versão exata da carta (medição + `VERSAO_LEITOR`). Alta.
- **R2. Nome provisório para deck sem listas de torneio** (pelo Pokémon que mais causou dano, à moda do Full Bench). Alta.
- **R3. Segunda fonte para coleção nova** antes do TCGdex (exportação do TCG Live do malie.io; conferir termos). Média.
- **R4. Modo automático:** começar/parar com o jogo, segunda tentativa de cópia e pedido de clique, espera de 12 s, repetida em 10 min. Média.
- **R5. Replay:** alvo dos contadores pelo texto do ataque; casos de teste no estilo do Training Court; "melhores momentos". Média/baixa.
- **R6. Log em português** (decisão do Pedro). **R7. Skills** "coach de partida" e "importar coleção" (ver seção 3). A decidir.

## Prioridade média
2. **Instalador como Release no GitHub** (hoje só existe o .exe da 2026.11.02-2, no computador do Pedro). Gerar um .exe novo e publicar
   como Release; o README já não promete Releases (corrigido em 05/11/2026).
3. **Atualizador com tag de versão e conferência do hash do zip** (hoje baixa a `main` sem conferir assinatura: risco se a conta do
   GitHub for comprometida).
4. **Peso maior para torneios recentes no confronto ajustado** (testar com `e3_matchups.py` antes de trocar).
5. **Ligar a partida à lista de Meus decks pelo NB2**; "minha lista × versões do deck"; alerta semanal de meta.
6. **Decisões mais rápida** quando passar de algumas centenas de partidas (~2,7 s com mil hoje, exp. 4).
7. **Base de regras:** quando a tarefa mensal avisar, atualizar `docs/regras-standard.md` (rotina em `../01_MODULES/RULES_BASE.md`);
   confirmar a marca da coleção 30th Celebration; acompanhar a rotação de 2027.

## Prioridade baixa
8. Consistência: simulação de abertura considerando cartas de busca (hoje os números são um piso).
9. Replay: energia ligada a Pokémon de mesmo nome no Banco pode cair no Pokémon errado (o log não diferencia; investigar se o
   contexto permite decidir, como foi feito com os contadores).
10. README (seção 4): o passo 1 do modo automático ainda manda rodar `pip install -r requirements-auto.txt` "no ambiente", sem citar o
    botão "Instalar o modo automático" (que instala no Python certo); revisar também o `COMECE_AQUI.txt`.

## Arrumação para trabalho a dois (06/11/2026; ver `../00_CENTRAL/COLLABORATION.md`)
- **Rotas do `app.py` por área** (Flask Blueprints: partidas, torneios, cartas, decks, amigos, sistema): é o arquivo que os dois mais
  editam. Só como `refactor/`, provando que a lista de rotas (`API_CONTRACTS.md`) e a proteção de origem ficam idênticas e com os
  4 testes.
- **Testes automáticos no GitHub (Actions) em Windows e Mac** a cada PR: `teste_tracker`, `teste_seguranca` e `teste_replay` não
  precisam de dados pessoais; `teste_telas` precisa de navegador. Repositório público = minutos gratuitos. Pedir autorização.
- **Teste que confere `API_CONTRACTS.md`** contra as rotas do `app.py` (falha se surgir rota sem documentação).

## Ideias da comparação com o Pokemon Champions Battle Logger (09/11/2026; o app dele é de código fechado: só ideias)
Feitas: "Hoje" no Início (5) e tema escolhido à mão (9), na 2026.11.09-4. Esperam o Pedro:
- **Ficha do adversário** (1) no detalhe da partida e no replay: seu placar contra o deck, o matchup nos torneios (melhor de 3), as
  cartas típicas marcando as vistas e a lista de torneio mais parecida com link para o Limitless. Também mostra quando o deck foi mal
  identificado (cartas vistas que não estão nas listas daquele deck).
- **Consulta rápida "contra quem estou jogando?"** (2): digitar o Pokémon visto e ver deck provável, cartas a esperar e matchup.
- **"Copiar para IA"** (3) no detalhe da partida (texto pronto para colar; a versão com chave de API manda dados para fora: D-003).
- **Sequências e horário** (6): taxa depois de derrotas seguidas, por período e por posição na sessão, com faixa de 95% e trava de
  amostra (com 52 partidas nada se conclui); corrigir para várias comparações (Holm).
- **Época por banimento ou rotação** (7), **"Relatar problema"** (8) e atualização assinada (item 3 acima).

## Em estudo, sem decisão
- **Servidor central para análises coletivas** (o grupo enxergar as análises de todos). Estudado numa sessão de 02–03/11/2026 que foi
  **apagada**; o texto completo se perdeu. O que sobrou do relatório: se as análises coletivas ficarem liberadas para todos os
  participantes, "o projeto encolhe bastante" (some a parte de esconder análises por nível de acesso e de dar permissões diferentes a
  cada administrador); continuaria sendo preciso um **servidor central simples, com HTTPS e banco PostgreSQL**, com conta criada pelo
  Pedro. Atenção: isso contraria D-003 (servidor só local) e D-004 (dados só com cada pessoa); qualquer passo exige decisão nova do
  Pedro. Pedir a ele o texto completo, se tiver guardado.
- **Analista estratégico** (treinador que analisa os logs das partidas do Pedro): foi tratado numa conversa separada em 01/11/2026,
  fora deste projeto. Não há nada implementado aqui.
