# Arquitetura

> Atualizado em 06/11/2026. Mapa de onde cada coisa está. O "como" de cada função está na explicação no topo do arquivo de código.

## Tecnologia
- **Python 3.11+** (testado com 3.15) + **Flask** (servidor só em 127.0.0.1) + **SQLite** + painel **HTML/CSS/JS sem frameworks**.
- Dependências em `requirements.txt` (programa), `requirements-auto.txt` (modo automático: pyautogui, opencv-python, pillow)
  e `requirements-dev.txt` (só testes de tela: playwright). Todas com teto de versão (ex.: `flask<4`), ver D-022.

## Como o programa roda (`app.py`)
- Rotas `/api/...` (cerca de 80), arquivos do painel em `/web/<arquivo>` (só .css e .js, sem cache), imagens de cartas em
  `/cartas/imagem`, exportações CSV/ZIP em `/exportar/...`.
- **Proteção de origem** (`so_pedidos_do_painel`): pedido com Host que não é local, ou com `Origin`/`Sec-Fetch-Site` de outro
  site, recebe 403. Coberto por `testes/teste_seguranca.py`.
- Ao iniciar, liga as tarefas em segundo plano (threads): coletor da área de transferência, modo automático, sincronizador
  de torneios, biblioteca de cartas, atualizador, base de regras e pasta compartilhada dos amigos.
- **Modo de execução no Windows:** com `pystray` disponível roda com **ícone na bandeja via `pythonw`** (se aberto pelo
  `python.exe`, reabre a si mesmo com `pythonw`); `--janela` força a janela preta.
- **Um Coletor por vez:** se já houver um aberto na mesma porta, o novo fecha o antigo. Por isso todo teste usa a porta 8799.
- Opções de linha de comando: `--sem-navegador`, `--janela`, `--criar-atalho`, `--diagnostico`, `--importar <id>`, `--sincronizar`.

## Pastas do repositório
| Pasta / arquivo | Conteúdo |
|---|---|
| `app.py` | Servidor, rotas, inicialização |
| `tracker/` | Toda a lógica, um módulo por assunto (tabela abaixo) |
| `tracker/regras_padrao.json` | Regras de leitura do log (27 regras regex); a cópia editável de cada pessoa fica em `dados/regras.json` |
| `web/` | Painel: `index.html` (esqueleto e ordem dos scripts), `estilo.css`, `js/*.js` (14 arquivos, um por área; ver `web/LEIA-ME.md`), `icone.ico` |
| `docs/regras-standard.md` | Base de regras do Standard (lida pelo programa; ver `../01_MODULES/RULES_BASE.md`) |
| `modelos/` | Imagens dos botões do modo automático (`LEIA-ME.txt`) |
| `exemplos/log_de_exemplo.txt` | Log usado no primeiro uso guiado (o coletor reconhece e não grava) |
| `instalador/` | `montar.py` (monta o programa com Python próprio) e `coletor.iss` (Inno Setup 6) |
| `.github/` | Modelo de Pull Request e `CODEOWNERS` (fluxo a dois, [`COLLABORATION.md`](COLLABORATION.md)) |
| `.gitattributes`, `.gitignore` | Fins de linha fixos (LF; `.bat` e `COMECE_AQUI.txt` guardados como estão, em CRLF) e o que nunca vai para o Git |
| `testes/` | `teste_tracker.py`, `teste_seguranca.py`, `teste_replay.py`, `teste_telas.py`, `leitor-tcg-live.html`, `experimentos/e1..e10` |
| `PROJECT_KNOWLEDGE/` | Esta documentação |
| `*.bat`, `*.command`, `COMECE_AQUI.txt` | Instalar/abrir no Windows e no Mac (os `.bat` e o `COMECE_AQUI.txt` ficam em CRLF) |
| `versao.txt`, `novidades.json`, `repositorio.txt` | Versão publicada, novidades de cada versão, repositório do atualizador |

## Módulos de `tracker/`
| Área | Módulo | O que faz |
|---|---|---|
| Captura | `coletor.py` | Vigia a área de transferência e grava todo log do TCG Live (ignora o log de exemplo) |
| | `auto_export.py` | Modo automático: reconhece a tela de resultado por imagem e clica em Battle Log e exportar |
| | `cobertura.py` | Quadro vermelho (Win32) sobre o botão Continue enquanto o log é copiado |
| | `avisos.py` | Recados para a pessoa (notificação do ícone, último aviso no painel) |
| | `diagnostico.py` | Procura, nas pastas do jogo, algum arquivo com o log (só lê) |
| Leitura | `leitor.py` | Transforma o log em dados (eventos, resumo, quem exportou, problemas, impressão digital) |
| | `replay.py` | Reconstrói a mesa e as mãos linha a linha |
| | `revisao.py` | Junta as linhas não lidas em modelos para virar regra ou ser ignoradas |
| Dados | `banco.py` | SQLite, migrações, gravação de partidas, dono das partidas |
| | `config.py` | Caminhos e configurações (`CONFIG_PADRAO`) |
| Análise | `analises.py` | Contas de todas as telas (pessoal, meta, matchups, perfil, cartas, decisões) |
| | `estrategia.py` | Força dos decks (Bradley-Terry), confronto ajustado, taxa esperada, equilíbrio |
| | `regressao.py` | Efeito de cada carta (regressão logística com freio) |
| | `variantes.py` | Versões de um deck (por ACE SPEC; modelo antigo por semelhança mantido) |
| | `probabilidades.py` | Consistência da lista (hipergeométrica exata) |
| | `decks.py` | Arquétipos, ícones, Meus decks, identificação do deck, versão certa de cartas com o mesmo nome |
| | `colecoes.py` | Coleções do Standard e as épocas do meta (chegada ao TCG Live, validade em torneio); rota `/api/epocas` |
| Fontes externas | `limitless.py` | Importa campeonatos (Labs + RK9) e torneios online (API) |
| | `cartas.py` | Biblioteca de cartas (TCGdex), arte básica, marcas de regulamento, ACE SPEC |
| | `regras_jogo.py` | Base de regras do Standard e as regras que o programa usa |
| | `compartilhar.py` | Logs de amigos (.zip e pasta do Google Drive) |
| | `atualizador.py` | Atualização pelo GitHub |
| | `novidades.py`, `lista_oficial.py` | Novidades de cada versão; formulário oficial de lista |
| Windows | `bandeja.py`, `atalhos.py`, `janela.py` | Ícone perto do relógio; atalhos; painel em janela própria (Edge/Chrome `--app`) |

## Pasta `dados/` (de cada pessoa; nunca no GitHub, nunca tocada pelo atualizador)
`tracker.db` (banco), `logs/` (cópia .txt de cada log), `logs_amigos/`, `config.json`, `regras.json`, `cartas/`
(sets, índice, imagens), `icones/`, `janela/` (perfil do navegador), `limitless_formatos.json`, `regras-standard.md`
(cópia mais nova baixada do GitHub), `programa.log` (registro do programa, inclusive as tentativas do modo automático).
Também ficam fora do GitHub: `.venv/`, `modelos/minhas/` e `modelos/CREDITOS-FullBench.txt` (criados ao usar "Usar imagens prontas").

## Banco de dados (`dados/tracker.db`)
Tabelas, formato `dados_json` (saída do leitor) e o registro de migrações: [`DATA_MODEL.md`](DATA_MODEL.md).
Contratos entre as camadas, imports em círculo e a lista das rotas `/api`: [`API_CONTRACTS.md`](API_CONTRACTS.md).

## Configurações (`dados/config.json`, padrões em `config.CONFIG_PADRAO`)
Captura (`nick`, `coletor_ativo`, `intervalo_coletor`), modo automático (`modo_automatico`, `confianca_imagem` 0,85,
`cobrir_continuar`, `escala_modelos`, `modelos_prontos`), painel (`abrir_em`, `guia_visto`, `porta` 8765), torneios
(`sincronizar_auto`, `sincronizar_horas` 6, `sincronizar_dias` 45, `listas_top` 64, `online_ativo`, `online_min_jogadores` 64,
`online_dias` 21, `online_por_vez` 40), atualização (`github_repo`, `github_ramo`, `github_token`), amigos
(`pasta_compartilhada`, `pasta_auto`, `pasta_minutos` 30). Nome, Player ID e nascimento da Lista oficial também ficam só ali.

## Integrações externas
| Serviço | Uso | Cuidados |
|---|---|---|
| Limitless Labs (labs.limitlesstcg.com) | Classificação, decks, listas dos grandes eventos | HTML, sem API; respeita robots.txt; pausa de 0,6 s |
| RK9 (rk9.gg/pairings) | Resultado de cada mesa | Link vem da página do Labs |
| limitlesstcg.com/tournaments?show=100 | Formato de cada evento (`tr[data-format]`) e id do Labs | Cache em `dados/limitless_formatos.json` |
| API play.limitlesstcg.com | Torneios online (`/tournaments?game=PTCG&format=STANDARD`, `/standings`, `/pairings`) | Sem chave, 50 pedidos a cada 5 min: pausa de 6,5 s, trata 429 |
| TCGdex (api.tcgdex.net) | Biblioteca de cartas | Algumas coleções novas vêm sem marca de regulamento |
| PokémonDB / Limitless | Ícones dos decks | Guardados em `dados/icones/` |
| GitHub (API de `versao.txt` e zip da `main`) | Atualizador e cópia nova da base de regras | Repositório em `repositorio.txt`; público |
| Full Bench (MIT) | Imagens prontas dos botões, num commit fixo (`FULLBENCH` em `auto_export.py`) | Créditos em `modelos/CREDITOS-FullBench.txt` |
| Google Drive para computador | Pasta compartilhada dos amigos (pasta local sincronizada) | Instalado à parte, não vem no instalador |
| Edge/Chrome | Janela própria do painel (`--app`) e testes de tela | Já vêm no Windows (Edge) |
| NuGet | Python oficial embutido no instalador (com sha256 conferido) | Só ao montar o instalador |

## Windows × Mac (levantado no código em 06/11/2026; nada disto foi testado num Mac ainda)
O código separa as plataformas com `sys.platform`/`platform.system()`. Prioridade do segundo desenvolvedor: paridade no Mac (D-044);
o que falta está em `../04_IMPLEMENTATIONS/BACKLOG.md`, seção "Paridade no Mac".
| Parte | Windows | Mac (pelo código) |
|---|---|---|
| Instalar / abrir | `instalar_windows.bat`, `iniciar_windows.bat`, instalador .exe (Inno Setup) | `instalar_mac.command`, `iniciar_mac.command` (Terminal aberto); sem instalador |
| Captura pela área de transferência (`coletor.py`) | API do Windows | `pbpaste` (sem contador de mudança: compara o texto) |
| Painel | Janela própria (Edge/Chrome `--app`, `janela.py`) | Aba do navegador padrão (`janela.py` só procura Edge/Chrome no Windows) |
| Ícone perto do relógio (`bandeja.py`) | Sim (`pystray`, via `pythonw`) | Não: `app.py` só liga a bandeja no Windows |
| Atalhos e iniciar com o sistema (`atalhos.py`) | Sim | Não (`disponivel()` só no Windows) |
| Modo automático (`auto_export.py`) | Acha a janela do jogo, põe na frente, cobre o Continue | Sem achar a janela nem pôr na frente; busca na tela inteira; sem cobertura (`cobertura.py` é Win32); pede permissões de Gravação de Tela e Acessibilidade |
| Pasta do Drive dos amigos (`compartilhar.py`) | Procura nas unidades fixas (`G:` etc.) | Procura em `~/Library/CloudStorage/GoogleDrive-*`; escolher pasta usa `tkinter` |
| Atualizador (`atualizador.py`) | Reabre com janela nova | Reabre com `Popen` simples |
| Diagnóstico (`diagnostico.py`) | Pastas do jogo no Windows | Conferir caminhos do jogo no Mac |
| Teste de telas (`teste_telas.py`) | Edge ou Chrome | Chrome (canal `chrome` do Playwright) |
