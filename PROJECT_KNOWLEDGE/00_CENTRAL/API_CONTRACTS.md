# Contratos entre as partes do programa

> Atualizado em 07/11/2026. O que cada parte promete às outras. Mudou um contrato → atualizar aqui no mesmo PR
> (COLLABORATION, seção 6). Formato do banco e de `dados_json`: [`DATA_MODEL.md`](DATA_MODEL.md).

## 1. Camadas (nomes usados nas conversas → módulos que existem)
Nenhum arquivo muda de lugar por causa destes nomes; eles só ajudam a combinar quem mexe onde.
| Camada | Módulos | Promete |
|---|---|---|
| Core | `app.py`, `bandeja`, `atalhos`, `janela` | Servidor só local com proteção de origem (D-003), rotas da seção 3, tarefas em segundo plano |
| Collector | `coletor`, `auto_export`, `cobertura`, `diagnostico`, `compartilhar` | Entrega o texto do log a `banco.inserir_partida(texto, origem, regras, dono=...)` |
| Reader | `leitor`, `regras_padrao.json`, `revisao`, `replay` | `leitor.ler_partida` → `dados_json`; `replay` monta a mesa a partir do texto e de `dados_json` |
| Data Layer | `banco`, `config` | Esquema e migrações; funções `listar_partidas`, `obter_partida`, `inserir_partida`, `salvar_torneio`, `consultar`...; `config.ler_config()`/`salvar_config()` e caminhos de `dados/` |
| Analytics | `analises`, `estrategia`, `regressao`, `variantes`, `probabilidades`, `decks` | Funções que devolvem dicionários prontos para virar JSON nas rotas |
| Fontes externas | `limitless`, `cartas`, `colecoes`, `regras_jogo`, `atualizador`, `novidades`, `lista_oficial` | Gravam no banco ou em `dados/`; nunca são chamadas pelo painel diretamente |
| Shared | `config`, `avisos` | Usados por quase todos |
| Painel | `web/index.html`, `web/js/*.js` | Só fala com o servidor pelas rotas da seção 3 |

## 2. Imports em círculo (não "arrumar")
Alguns módulos se usam mutuamente; o círculo é quebrado com `import` **dentro da função** (não no topo do arquivo):
`banco ↔ cartas`, `banco ↔ decks`, `decks ↔ analises`, `analises ↔ variantes`, `atualizador ↔ novidades`, `regras_jogo ↔ atualizador`.
Levar um desses imports para o topo do arquivo faz o programa parar de abrir. Os 4 testes pegam isso.

## 3. Rotas do servidor (`app.py`)
Gerada do código em 06/11/2026 (81 rotas). "Usado por" = arquivos do painel onde o caminho aparece (busca de texto; rotas com o
mesmo caminho e métodos diferentes aparecem com os mesmos arquivos). Toda rota passa pela proteção de origem
(`so_pedidos_do_painel`, coberta por `testes/teste_seguranca.py`). Respostas em JSON, salvo `/exportar/*` (CSV/ZIP), `/cartas/imagem`,
`/icone/*`, `/modelos/*` (imagens) e `/web/*` (CSS/JS).

| Método e caminho | Função em `app.py` | Usado por | Descrição |
|---|---|---|---|
| `GET /` | `inicio` | navegador (abre o `index.html`) |  |
| `GET /api/exemplo-log` | `exemplo_log` | inicio.js | Log de exemplo para o teste do primeiro uso (o coletor reconhece e não grava). |
| `GET /icone.ico` | `icone_aba` | index.html |  |
| `GET /web/<path:arquivo>` | `arquivo_painel` | index.html | Partes do painel (estilo.css e web/js/*.js). Só CSS e JS de dentro de web/; sem cache, |
| `GET /api/status` | `status` | base.js, campeonatos.js, inicio.js, partidas.js, programa.js |  |
| `GET /api/atalhos` | `ver_atalhos` | inicio.js, partidas.js, programa.js |  |
| `POST /api/atalhos` | `mudar_atalhos` | inicio.js, partidas.js, programa.js | {"area": true} cria o atalho na Área de Trabalho; {"inicializar": false} tira do início do Windows. |
| `GET /api/decisoes` | `api_decisoes` | decisoes.js | Cada carta (aberturas e cartas jogadas) traz `n`, `v`, `d`, `taxa`, `taxa_sem`, `sem_n`, `sem_v` (desde 2026.11.07-1) e `diferenca`. |
| `GET /api/regras-standard` | `regras_standard` | regras_standard.js |  |
| `POST /api/regras-standard/atualizar` | `regras_standard_atualizar` | regras_standard.js |  |
| `GET /api/novidades` | `ver_novidades` | inicio.js |  |
| `POST /api/novidades/vista` | `novidades_vista` | inicio.js |  |
| `GET /api/revisao` | `revisao_lista` | revisao.js |  |
| `POST /api/revisao/regra` | `revisao_regra` | revisao.js |  |
| `POST /api/config` | `salvar_config` | amigos.js, campeonatos.js, inicio.js, partidas.js, programa.js |  |
| `GET /api/partidas` | `partidas` | decisoes.js, inicio.js, partidas.js, replay.js |  |
| `GET /api/jogadores-locais` | `jogadores_locais` | partidas.js |  |
| `GET /api/amigos` | `lista_amigos` | amigos.js |  |
| `POST /api/amigos/pasta/escolher` | `escolher_pasta` | amigos.js |  |
| `POST /api/amigos/pasta/sincronizar` | `sincronizar_pasta_agora` | amigos.js |  |
| `POST /api/amigos/exportar` | `exportar_logs` | amigos.js |  |
| `GET /exportar/meus-logs.zip` | `baixar_logs` | amigos.js |  |
| `POST /api/amigos/importar` | `importar_logs` | amigos.js |  |
| `DELETE /api/amigos/<path:nome>` | `apagar_amigo` | amigos.js |  |
| `POST /api/partidas` | `nova_partida` | decisoes.js, inicio.js, partidas.js, replay.js |  |
| `GET /api/partidas/<int:pid>` | `partida` | partidas.js, replay.js |  |
| `GET /api/partidas/<int:pid>/replay` | `replay_partida` | partidas.js, replay.js |  |
| `GET /cartas/imagem` | `imagem_carta` | base.js | Imagem da arte básica, por id (?id=sv06-130) ou por nome (?nome=Dragapult ex). |
| `GET /icone/<nome>` | `icone` | base.js, deck_detalhe.js, decks.js | Ícone do Pokémon (PokémonDB). Aceita o id do ícone (lopunny-mega) ou o nome da carta. |
| `GET /api/arquetipos` | `lista_arquetipos` | base.js |  |
| `GET /api/decks` | `meus_decks` | decisoes.js, deck_detalhe.js, decks.js, inicio.js, lista_oficial.js, partidas.js |  |
| `POST /api/decks` | `novo_deck` | decisoes.js, deck_detalhe.js, decks.js, inicio.js, lista_oficial.js, partidas.js |  |
| `GET /api/decks/<int:did>` | `ver_deck` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `GET /api/decks/<int:did>/consistencia` | `consistencia_deck` | deck_detalhe.js, decks.js, lista_oficial.js | Probabilidades da lista (mulligan, carta na mão, nos prêmios) e o mulligan real das suas partidas. |
| `GET /api/decks/<int:did>/combo` | `combo_deck` | deck_detalhe.js, decks.js, lista_oficial.js | Chance de ter as cartas A e B juntas até o 1º, 2º e 3º turno. |
| `PUT /api/decks/<int:did>` | `editar_deck` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `GET /api/decks/<int:did>/lista-oficial` | `lista_oficial_ver` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `PUT /api/decks/<int:did>/lista-oficial` | `lista_oficial_salvar` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `DELETE /api/decks/<int:did>/lista-oficial` | `lista_oficial_descartar` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `POST /api/lista-oficial/validar` | `lista_oficial_validar` | lista_oficial.js |  |
| `DELETE /api/decks/<int:did>` | `apagar_deck` | deck_detalhe.js, decks.js, lista_oficial.js |  |
| `POST /api/decks/vincular` | `vincular_todas` | decks.js | Procura, nas partidas sem lista, as que batem com alguma lista de Meus decks. |
| `POST /api/atualizacao/verificar` | `verificar_atualizacao` | programa.js |  |
| `POST /api/atualizacao/instalar` | `instalar_atualizacao` | programa.js |  |
| `GET /api/cartas/matchups` | `cartas_matchups` | campeonatos.js |  |
| `GET /api/cartas/status` | `cartas_status` | biblioteca.js |  |
| `GET /api/cartas/buscar` | `cartas_buscar` | biblioteca.js | Mostra o que o conversor faz: nome, ou coleção + número -> arte básica. |
| `POST /api/cartas/atualizar` | `cartas_atualizar` | biblioteca.js |  |
| `GET /api/cartas/manuais` | `cartas_manuais` | biblioteca.js |  |
| `POST /api/cartas/manuais` | `cartas_manual_nova` | biblioteca.js | Adiciona uma imagem de carta à mão (arquivo enviado ou link da imagem). |
| `DELETE /api/cartas/manuais/<arquivo>` | `cartas_manual_apagar` | biblioteca.js |  |
| `POST /api/modelos/<nome>` | `enviar_modelo` | programa.js | Recebe as imagens dos botões usadas pelo modo automático. |
| `POST /api/modelos-prontos` | `usar_modelos_prontos` | programa.js | Baixa as imagens dos botões do projeto Full Bench (licença MIT). |
| `POST /api/automatico/instalar` | `instalar_automatico` | programa.js | Instala as bibliotecas do modo automático no mesmo Python que roda o programa (veja auto_export.instalar). |
| `GET /modelos/<nome>` | `ver_modelo` | programa.js |  |
| `POST /api/cartas/imagens` | `cartas_imagens` | biblioteca.js |  |
| `DELETE /api/partidas/<int:pid>` | `apagar_partida` | partidas.js, replay.js |  |
| `GET /api/regras` | `regras` | programa.js, revisao.js |  |
| `POST /api/regras` | `salvar_regras` | programa.js, revisao.js |  |
| `POST /api/regras/testar` | `testar_regra` | programa.js, revisao.js |  |
| `GET /api/torneios` | `torneios` | base.js, campeonatos.js |  |
| `GET /api/limitless/eventos` | `eventos_limitless` | campeonatos.js |  |
| `POST /api/limitless/importar` | `importar` | campeonatos.js |  |
| `POST /api/sincronizar` | `sincronizar_agora` | campeonatos.js | Procura torneios novos agora, sem esperar o próximo horário. |
| `DELETE /api/torneios/<tid>` | `apagar_torneio` | campeonatos.js |  |
| `GET /api/epocas` | `epocas` | base.js | Épocas do meta (uma por coleção): pela chegada ao TCG Live (suas partidas) e pela validade em torneio. |
| `GET /api/meta` | `meta` | campeonatos.js |  |
| `GET /api/variantes/<arq>` | `variantes_deck` | campeonatos.js | Variantes do deck (listas agrupadas por semelhança) com a taxa de vitória de cada uma. |
| `GET /api/qual-deck` | `qual_deck` | campeonatos.js | Taxa esperada contra o campo, pior confronto e equilíbrio do meta (tracker/estrategia.py). |
| `GET /api/tendencia` | `tendencia` | campeonatos.js |  |
| `GET /api/deck/<arq>` | `deck` | campeonatos.js |  |
| `GET /api/cartas` | `api_cartas` | biblioteca.js, campeonatos.js |  |
| `GET /api/efeito-cartas` | `api_efeito_cartas` | campeonatos.js | Efeito de cada carta na chance de vencer, descontados os confrontos (regressão logística, tracker/regressao.py |
| `GET /api/jogadores` | `jogadores_torneio` | campeonatos.js |  |
| `GET /api/comparar` | `comparar` | campeonatos.js |  |
| `GET /exportar/minhas_partidas.csv` | `exportar_partidas` | partidas.js, programa.js |  |
| `GET /exportar/eventos.csv` | `exportar_eventos` | partidas.js, programa.js |  |
| `GET /exportar/torneios.csv` | `exportar_torneios` | campeonatos.js, programa.js |  |
| `GET /exportar/meta.csv` | `exportar_meta` | campeonatos.js, programa.js |  |
| `POST /api/encerrar` | `encerrar` | programa.js | Fecha o programa (útil quando ele roda sem janela, iniciado com o Windows). |
| `GET /api/diagnostico` | `diag` | programa.js |  |

## 4. Outros contratos
- `dados/config.json`: chaves e padrões em `config.CONFIG_PADRAO`; o painel só grava as chaves listadas em `salvar_config()` (`app.py`).
  Chave nova → padrão em `CONFIG_PADRAO` (quem já tem `config.json` recebe o padrão ao abrir).
- `docs/regras-standard.md`: lido pelo programa (`regras_jogo.py`); não mudar de lugar nem o formato da tabela de marcas e do item
  de promos ([`../01_MODULES/RULES_BASE.md`](../01_MODULES/RULES_BASE.md)).
- `versao.txt` + `novidades.json`: lidos pelo atualizador dos amigos na `main` do GitHub (D-024;
  [`../01_MODULES/UPDATE_AND_INSTALL.md`](../01_MODULES/UPDATE_AND_INSTALL.md)).
- `tracker/regras_padrao.json` → `dados/regras.json`: regras de leitura (regex com grupos nomeados, sintaxe de JS aceita).
