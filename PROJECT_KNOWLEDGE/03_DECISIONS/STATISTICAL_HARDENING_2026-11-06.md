# Auditoria corretiva e "hardening" da Skill Statistical Analyst — rodada de 06/11/2026

> Atualizado em 06/11/2026. Continuação de `STATISTICAL_AUDIT_2026-11-06.md` (que fica como estava; aqui só se acrescenta).
> Ramo `icones-painel`, commit de base `76a2005` (a Skill é idêntica à da `main`, `55a000f`, mas neste ramo está **sem commit**).
> Cópias usadas: uma cópia com os dados do Pedro de 06/11 (porta 8799, marcada como cópia de teste) para as análises; outra igual
> para os agentes "sem a Skill"; uma terceira, sem dados, para os 4 testes de entrega. **Nenhum código do Coletor mudou.**

## A. Resumo
| Item pedido | Situação | Prova |
|---|---|---|
| Ponte só leitura, com trava na execução | **Corrigido** | `tests/test_ponte.py` (22 testes, OK; 1 pulado por permissão do Windows, coberto pelo da junção) |
| Registro reprodutível dos experimentos | **Corrigido** | `tests/test_sa_tools.py` (classe `Reprodutibilidade`, 9 testes, OK); a4 refeito = 06/11 |
| Afirmações sobre independência | **Corrigido** (com medição nova) | a7: ICC ≈ 0 só vale para quem tem lista; todos os jogadores: +0,063 |
| Identificação do deck com cartas vistas | **Parcialmente corrigido** | a8: parte real com 18 partidas de 1 deck; parte sintética realista |
| Avaliação da Skill A–H | **Feito** (1 execução por cenário; C e F repetidos) | seção E |
| Calibração a fundo | **Feito** (ferramentas + a8 + a9) | seção D.3 |
| Matriz de validação | **Atualizada** | `knowledge/KNOWN_METHODS.md` |

Três conclusões novas que mudam a leitura de números do programa (nada foi mudado nele):
1. **Independência:** o "ICC ≈ 0" da auditoria valia só para jogadores **com lista** (o topo). Com todos os jogadores o ICC é
   +0,063 [+0,059; +0,068] (Labs +0,096): faixas que juntam partidas de todos os jogadores ficam até ~25% estreitas demais.
   *(Corrigido em 06/11 pelo a11: nas telas de Meta/Matchups — decks dos dois lados conhecidos, empate = não-vitória — o ICC é
  0,015 (Labs 0,032) e as faixas antigas cobriam 93–96% em vez de 95%; o "até ~25%" valia só para o recorte do a7.)*
2. **Identificação:** com cartas vistas de forma realista, o NB2 sozinho ganha da regra do programa em **acurácia** nos turnos 1–2
   (5,9 e 1,7 pp, prováveis), mas a regra do programa ganha em **F1 macro** (decks raros): 0,58 × 0,53 no turno 2. A escolha
   depende do que se quer otimizar.
3. **Calibração:** ECE baixo enganou duas vezes. O NB2 tem ECE 0,031 (piso de ruído 0,006) e inclinação 0,56: **confiança exagerada**.
   No confronto ajustado, a força geral tem o menor ECE (0,006) e quase não prevê; o k = 24 tem inclinação 0,81 e foi **pior que o
   chute de 50% em 4 de 10 torneios de teste** (todos online pequenos).

## B. Segurança da ponte com o Coletor
**Problema (antes):** `ponte.carregar()` importava `banco` e os outros módulos sem trava; a checagem da porta era pulada se faltasse
`dados/config.json`; nada impedia `INSERT`, `banco.apagar_torneio` ou gravar arquivos na cópia — ou, por engano de caminho, na
instalação real.

**Correção (só em `.claude/skills/statistical-analyst/tools/`):**
1. `validar_copia` roda **antes** de importar qualquer módulo: pasta com `tracker/`; `config.json` presente, legível, porta 8799
   (faltou = falha); marca `dados/COPIA_DE_TESTE.json` (identificação positiva; criada por `tools/marcar_copia.py`, que confere
   tudo antes e nunca sobrescreve); recusa pasta com `.venv` (instalação em uso) ou `.git` (o repositório); recusa pastas listadas em
   `SA_PASTAS_PROTEGIDAS`; `tracker.db` arquivo comum, dentro da cópia (link ou junção para fora = recusa), cabeçalho SQLite, abre em
   modo leitura e tem as tabelas do Coletor.
2. Banco: `banco.conectar` é trocado por conexão `file:...?mode=ro` + `PRAGMA query_only=ON` + **autorizador do SQLite**
   (`set_authorizer`: só SELECT/READ/FUNCTION e PRAGMA de consulta). Não é filtro de texto: o SQLite decide comando por comando.
3. Funções que gravam (`FUNCOES_ESCRITA`: 11 de `banco`, 4 de `config`, 7 de `decks`, 8 de `cartas`) viram bloqueio com erro claro.
   Toda função pública de `banco` precisa estar classificada como leitura ou escrita (o teste falha se aparecer uma nova sem classe).
4. Vigia do Python (`sys.addaudithook`), ligado antes do import e impossível de desligar no processo: bloqueia abrir arquivo para
   gravar e criar/apagar/renomear dentro da cópia e das pastas protegidas; qualquer conexão SQLite que não seja `mode=ro` (em qualquer
   lugar); rede; programas externos (menos `git` de consulta); `ctypes`. `sys.dont_write_bytecode` evita `__pycache__` na cópia.
5. `sa_tools.CLASSE`: cada ferramenta marcada como `leitura` ou `escrita` (só `registrar` grava, e só na pasta de resultados).

**Testes que pedem escrita de propósito (`tests/test_ponte.py`):** SELECT e PRAGMA de consulta passam; INSERT, UPDATE, DELETE,
REPLACE, CREATE TABLE/INDEX/TEMP, DROP, ALTER, ATTACH, VACUUM, `PRAGMA x = y` e `executescript` bloqueados, banco idêntico depois;
cada uma das três travas do SQLite segura sozinha; funções de escrita do Coletor bloqueadas (inclusive o caminho interno
`banco.conectar`); sem `config.json`, `config.json` ilegível, porta 8765, sem marca, banco ausente/pasta/texto/fora da cópia
(junção) → recusa; `.venv`, `.git` e pasta protegida → recusa; gravar arquivo, `os.open`, remover, renomear, `mkdir`, `rmtree`,
copiar, SQLite de escrita (na cópia e em outro lugar), rede, `subprocess` e `os.system` → bloqueados; ler arquivo, SQLite em memória,
`git` de consulta e funções de análise reais → permitidos; nenhum arquivo da cópia muda e nenhum `__pycache__` é criado.
**Em uso real:** depois de todas as análises desta rodada (a4, a7, a8, a9 e 8 agentes com a Skill), os arquivos de `dados/` da cópia
eram idênticos aos da origem, e nenhum arquivo da cópia era mais novo que a marca.
**Limite conhecido:** código que chame o sistema operacional sem passar pelo Python (extensão em C) escapa do vigia; o banco continua
protegido pelo `mode=ro`. Não existe "modo escrita" na ponte de propósito (e4/e7 rodam à parte, em banco descartável).

## C. Reprodutibilidade
`sa_tools.registrar` (formato 2) grava, em arquivo novo aberto em modo exclusivo (nunca sobrescreve): `id` único, data e hora com
fuso; commit e hash de `tracker/*.py` do Coletor; commit da Skill, aviso de mudanças sem commit e hash das ferramentas; nome e SHA-256
do script; Python, SQLite, pacotes (`ausente` quando falta) e se a ordem dos conjuntos é aleatória; semente, parâmetros e filtros;
**impressão dos dados** = SHA-256 de todas as linhas de cada tabela ordenadas por todas as colunas (manifesto por tabela, sem copiar
dado nenhum; independe da ordem de inserção); período (torneios e partidas); descrição do conjunto efetivamente usado; resultado,
SHA-256 do resultado e SHA-256 com 12 algarismos; arquivos de saída (nome, tamanho, SHA-256); lista de **limitações** (tudo o que não
pôde ser registrado aparece aqui). Mantém os campos antigos (inclusive a impressão antiga, "só contagens", como `impressao_contagens`).

Testes (`tests/test_sa_tools.py`): mesmos dados e parâmetros → mesmo hash de resultado e dos dados, arquivos e ids diferentes;
mesma tabela inserida em outra ordem → mesma impressão; um nome trocado (mesma contagem e datas) → impressão nova diferente (a antiga
não via: limitação demonstrada); semente/parâmetro/filtro registrados; script diferente → hash diferente; `versao.txt`, script,
pacote e tabela ausentes → registrados em `limitacoes`; nenhum dado da tabela nem caminho no arquivo.

**Reprodução real:** o a4 refeito com a ponte nova (código 2026.11.06-1, mesmos dados) deu os mesmos números de 06/11; o hash exato
diferiu numa única casa (17º algarismo de um valor de calibração) porque o Python sorteia a ordem dos conjuntos de texto a cada
processo e `-I` ignora `PYTHONHASHSEED`; com 12 algarismos os hashes são iguais. A impressão antiga dos dados bateu (`02e41a162acc`).
Por isso o registro agora guarda `resultado_sha256_12alg` e avisa a limitação. Os experimentos a1–a6 e seus resultados não foram
alterados (rodam com a ponte nova; os novos a7–a9 usam o registro completo).

## D. Validação estatística
### D.1 Independência entre partidas (a7)
| Recorte (torneios, W/L) | Jogadores | Partidas/jog. | ICC [faixa 95%, bootstrap por jogador] | Efeito de desenho (limite sup.) |
|---|---|---|---|---|
| Com lista (= a1) | 5.513 | 7,6 | −0,015 [−0,020; −0,011] | 1,00 |
| Sem lista | 7.291 | 4,7 | +0,034 [+0,029; +0,041] | 1,15 |
| Todos | 12.804 | 5,9 | **+0,063 [+0,059; +0,068]** | 1,34 |
| Labs (grandes eventos) | 7.902 | 6,5 | **+0,096 [+0,090; +0,102]** | 1,56 |
| Online | 4.902 | 5,0 | −0,010 [−0,018; −0,001] | 1,00 |
"Mão quente" (vencer a rodada seguinte depois de vitória − depois de derrota): com lista −2,0 pp; sem lista +8,4 pp; todos +7,6 pp.
Partidas pessoais (Ladder, 3 donos de log, 47/21/15 partidas): teste de sequências sem sinal (p 0,96; 0,13; 0,11) — **sem poder**
para afirmar nada. Não mensurável: jogos dentro de uma partida melhor de 3 (só o resultado da partida é guardado).
**Leitura:** o ICC negativo dos jogadores com lista é o que se espera de uma amostra escolhida pelo resultado final (quem chegou ao
topo tem um total alto "fixo"). Com todos os jogadores, partidas do mesmo jogador andam juntas (habilidade, abandono depois de
derrotas). Contexto de validade de cada afirmação: **com lista (análises de cartas, versões, regressão):** independência razoável;
**todas as partidas de torneio (meta, matchups, Wilson do meta, confronto ajustado):** não independentes, efeito de desenho 1,3–1,6;
**Ladder (jogo único, mesmo jogador):** não medido com poder suficiente; **melhor de 3 (jogos dentro da partida):** não mensurável;
**jogadores diferentes:** é o que as taxas por deck agregam — a dependência é por jogador, não entre jogadores. Ausência de evidência
(p alto no Ladder) não prova independência.

### D.2 Identificação do deck
**Auditoria do a4 (o a4 fica como está):** (1) seleção das cartas: sorteio uniforme entre cartas distintas da lista — um "tech" de
1 cópia tem a mesma chance de aparecer que uma carta de 4, e Pokémon e Treinadores aparecem igual; não é o que um log mostra.
(2) Treino/teste: 70/30 por data de torneio, correto, mas o corte podia dividir uma data (não dividiu nestes dados).
(3) Vazamento: as **assinaturas** e o NB2 eram só do treino (o filtro pega toda consulta com a coluna `lista`); o **cadastro de
arquétipos e a contagem de jogadores** (desempate dos ícones) vinham de todos os torneios. Medido no a8: o efeito é desprezível
(ícones com cadastro de todos × só do treino: −0,3 a 0,0 pp, sem diferença clara), mas existe: 4 listas de teste têm deck que não
existe no treino; com o cadastro de todos os torneios os ícones acertam 8,3% delas (o NB2, 0%). (4) Cálculo: só acurácia; amostras
diferentes por nº de cartas (comparações válidas só dentro da mesma linha); nenhuma métrica para classes desbalanceadas.

**a8 (novo):** parte S = 1.408 listas de 10 torneios de teste (26/10 a 01/11), modelos com 23 torneios até 25/10, nada do teste no
treino (listas, contagem de jogadores, cadastro). Cartas "vistas até o turno T" sorteadas com a chance de revelação **medida nos logs**
(por categoria, cópias e turno, em 18 partidas com lista conhecida), reescalada ao nº médio de cartas reveladas em todos os 83 logs.
| Turno (cartas vistas, média) | Ícones | NB2 | Programa | NB2 com abstenção | NB2 prior uniforme |
|---|---|---|---|---|---|
| 1 (2,1) | 31,7% | **63,4%** | 57,5% | 55,8% | 59,7% |
| 2 (3,9) | 53,1% | **81,0%** | 79,3% | 77,8% | 76,2% |
| 4 (7,1) | 71,5% | 89,1% | 88,6% | 88,1% | 86,1% |
| 6 (9,4) | 78,1% | 91,0% | **91,3%** | 90,9% | 87,2% |
Programa − NB2 (erro, bootstrap por torneio): T1 +5,9 pp [+4,1; +7,2], T2 +1,7 [+0,5; +2,7], T3–T4 sem diferença clara, T6 −0,3
[−0,5; −0,1]. Turno 2: F1 macro ícones 0,50 / NB2 0,53 / **programa 0,58**; acurácia balanceada 0,52 / 0,51 / **0,56**; inconclusivo
11% / 1% / 5%. O "prior" do meta ajuda (prior uniforme é pior em todos os turnos, ~3–5 pp, provável). Por deck: NB2 ≥ 92% nos
7 mais comuns, mas dragapult-blaziken 68%. Matriz de confusão (turno 2) no JSON do a8.
**Parte R (real):** 18 partidas do Pedro com a lista ligada (gabarito independente da identificação), **um só arquétipo**; modelos com
os 33 torneios (todos anteriores às partidas). Revocação: turno 2 — ícones 16,7%, NB2/programa 66,7%; turno 3 — 33,3% / 83,3%;
fim — 77,8% / 88,9%. NB2 e programa empataram em todas as partidas. **Limitação:** 1 deck, 1 jogador; não mede precisão nem decks
do adversário. Os logs não trazem o deck do adversário com gabarito (só haveria com o mesmo jogo exportado pelos dois lados).
**Conclusão:** o achado 4 se confirma na acurácia, mas trocar a regra não é "ganho sem custo": piora os decks raros. Qualquer mudança
precisa escolher a métrica com o Pedro e medir de novo (D-017). A regra do Coletor não foi mudada.

### D.3 Calibração
Novas ferramentas: `ece` (faixas por largura ou por massa), `recalibracao_logistica` (inclinação e intercepto), `calibracao_detalhada`
(ECE com 5/10/15/20 faixas, observações por faixa, **piso de ruído** simulado e faixa de 95% por bootstrap agrupado),
`calibracao_por_grupo` (por arquétipo, período ou grupo, com faixa de Wilson). Testes mostram, entre outros, um modelo com ECE ≈ 0
no total e 20 pp de erro em cada grupo.
- **NB2 (a8, 8.275 previsões):** log-loss 0,324, Brier 0,086; ECE10 0,031 [0,024; 0,043] contra piso 0,006; inclinação **0,56 ± 0,02**
  (confiança exagerada); por deck, dragapult-ex é subconfiante (diz 83%, acerta 97%) e os decks raros, superconfiantes (diz 87%, acerta
  74%); a partir do turno 3, superconfiante.
- **Confronto ajustado (a9, 10.212 previsões, as duas pontas):**
  | Modelo | log-loss | Brier | ECE10 [95%] | piso | inclinação |
  |---|---|---|---|---|---|
  | k = 24 (programa) | 0,6778 | 0,2418 | 0,015 [0,007; 0,030] | 0,009 | 0,81 ± 0,05 |
  | k = 16 | 0,6776 | 0,2417 | 0,017 | 0,009 | 0,77 ± 0,04 |
  | k = 1 (≈ taxa bruta) | 0,6950 | 0,2476 | 0,051 | 0,010 | 0,46 ± 0,03 |
  | Força geral | 0,6921 | 0,2489 | **0,006** | 0,008 | 0,54 ± 0,07 |
  | Chute 50% | 0,6931 | 0,2500 | — | — | — |
  k24 − 50% −0,0153 [−0,0229; −0,0041]; k24 − força geral −0,0142 (provável); k24 − k16 +0,0002 (empate). ECE sensível às faixas
  (5: 0,007; 10: 0,015; 15: 0,012; 20: 0,015, com faixas de 1–2 observações). Por período: 4 de 10 torneios de teste com log-loss
  **pior que 50%** e inclinação 0,35–0,49. Por fonte: online inclinação 0,72; Labs 1,16. Por grupo de jogadores: **com lista** vence
  56,6% contra 50,3% previstos; **sem lista** 28,5% contra 48,9% (o modelo é de deck, não de jogador). Por arquétipo: 1 de 11 fora.
- **Conclusão:** nenhuma métrica foi trocada. A Skill passa a exigir, para dizer "calibrado": ECE contra o piso, inclinação, e quebra
  por grupo. O k = 24 continua o melhor medido; a instabilidade por torneio online pequeno é nova e merece acompanhamento.

## E. Testes da Skill (cenários A–H)
Gabarito escrito **antes** das execuções e guardado fora do repositório até a correção (agora em `evals/<cenário>/graders/`).
Agentes independentes (modelo menor), mesmo repositório; "sem a Skill" proibido de ler `.claude/` mas com acesso a
`PROJECT_KNOWLEDGE/` (inclusive a auditoria), usando outra cópia. Nota por critério 0 / 0,5 / 1 (4 por cenário), dada por quem
escreveu os critérios — avalia a fundamentação, não só a conclusão.
| Cenário (pasta em `evals/`) | Com a Skill | Sem a Skill | O que separou os dois |
|---|---|---|---|
| A erro matemático (`a-erro-matematico`) | 4 | 3,5 | com: rodou `probabilidades` e `bo3_de_jogo` pela ponte, disse "exata, piso", empates; sem: conta certa à mão |
| B vazamento temporal (`b-vazamento-temporal`) | 3,5 | 3,5 | os dois acharam o vazamento e o 92% do a4; nenhum falou de classes desbalanceadas |
| C amostra insuficiente (`c-amostra-insuficiente`, 2 execuções) | 4 / 3,5 | 2,5 / 2,5 | sem: Wilson à mão e nenhuma menção a jogo único × melhor de 3 (nas duas vezes) |
| D correlação confundida (`d-correlacao-confundida`) | 4 | 3,5 | com: citou 0 de 392 cartas (a3) e achado 1; sem: sugeriu a regressão sem dizer o resultado |
| E logs incompletos (`e-logs-incompletos`) | 3,5 | 3,5 | os dois rodaram o NB2 (alakazam-dusknoir ~40%, "Dragapult" ~23%); com a Skill disse que 23% "tende a ser generoso" — direção errada (a8: confiança baixa do NB2 subestima) |
| F pesquisa redundante (`f-pesquisa-redundante`, 2 execuções) | 4 / 4 | 3 / 3 | com: leu o projeto antes, pesquisou só a lacuna e avisou que as fontes são fracas; sem: pesquisou primeiro ou sem dizer por quê |
| G comparação pareada (`g-comparacao-pareada`) | 4 | 4 | empate: a auditoria em `PROJECT_KNOWLEDGE/` já responde |
| H observado × inferido × desconhecido (`h-observado-inferido`) | 4 | 4 | empate; os dois separaram fato do log, parcial, palpite e probabilidade |
| **Total** (média das repetições) | **31,25 / 32 (98%)** | **27,5 / 32 (86%)** | +12 pontos |

- **Repetição:** C e F (maior diferença) rodaram 2 vezes em cada condição; a diferença se manteve (variação de 0,5 ponto só em C com a Skill).
- **Fundamentação:** com a Skill, 7 de 8 respostas usaram funções do programa/Skill pela ponte ou citaram o experimento exato; sem
  ela, 4 de 8 fizeram contas à mão ou citaram só documentos. A ponte travada funcionou para os agentes (nenhum bloqueio indevido) e
  nenhum arquivo do projeto ou das cópias foi alterado.
- **Erros comuns às duas condições:** ninguém tratou classes desbalanceadas (B); a direção da descalibração do NB2 ainda não estava na
  Skill quando os agentes rodaram (E) — agora está (`KNOWN_METHODS.md`, `SKILL.md` §4).
- **Limitações:** 1 execução por cenário (2 em C e F); modelo menor que o desta sessão; nota dada por quem escreveu os critérios; o
  grupo "sem a Skill" lia a auditoria em `PROJECT_KNOWLEDGE/`, então a diferença mede o que a Skill acrescenta além dos documentos.

## F. Integridade do Coletor
- Nenhum arquivo do Coletor alterado (`git status`: as mudanças em código são as da 2026.11.06-1, de outra sessão, intocadas).
- Banco real não aberto nesta rodada; a cópia de dados veio de uma cópia anterior. Dados da cópia idênticos depois de tudo.
- 4 testes de entrega numa cópia nova do diretório de trabalho (inclui a 2026.11.06-1 sem commit): `teste_tracker`, `teste_seguranca`,
  `teste_replay`, `teste_telas` → **OK**.
- Testes da Skill: `test_ponte.py` (22), `test_sa_tools.py` (31), `test_referencias.py` (4) → OK.

## G. Pendências
**Corrigidos:** ponte só leitura com trava de execução; falha segura; classificação leitura/escrita; registro completo e nunca
sobrescrito; impressão robusta dos dados; afirmações de independência (com contexto); calibração a fundo; matriz de validação.
**Parcialmente corrigidos:** identificação com cartas vistas (real = 18 partidas de 1 deck; o resto é sintético calibrado em 1 deck);
reprodução exata (até 12 algarismos por causa da ordem aleatória dos conjuntos); avaliação A–H (1 execução, C e F repetidos).
**Não corrigidos (fora do escopo ou exigem o Pedro):** e2 continua vazando (código em `testes/`); regra de identificação do programa;
avisos de "listas do topo" e da conversão melhor de 3; faixas do meta sem efeito de desenho; nenhuma métrica de tela mudou.
**Testes reprovados:** nenhum ao final. Durante o trabalho, 3 falhas de teste foram de erros meus (PRAGMA de consulta barrado, `git`
no Windows, um teste de calibração mal desenhado) e foram corrigidas antes da entrega.
**Recomendações (todas precisam de decisão do Pedro):** (1) definir `SA_PASTAS_PROTEGIDAS` com a pasta da instalação real no
computador dele (camada extra; a recusa por `.venv` e porta já cobre o caso conhecido); (2) escolher a métrica antes de mudar a
identificação (acurácia × decks raros) e medir de novo com partidas exportadas pelos dois lados; (3) mostrar a confiança do deck do
adversário como "incerta" quando baixa — e não tratá-la como probabilidade (NB2 confiante demais); (4) faixas de Wilson do meta com
efeito de desenho (~1,3–1,6) ou aviso; (5) acompanhar o confronto ajustado em torneios online pequenos; (6) corrigir o e2.

## H. Git
- Ramo: `icones-painel` (base `76a2005`). Nenhum commit, push ou troca de ramo.
- Arquivos desta rodada (todos sem commit): na Skill — `tools/ponte.py`, `tools/sa_tools.py`, `tools/marcar_copia.py` (novo),
  `tools/README.md`, `tests/test_ponte.py` (novo), `tests/test_sa_tools.py`, `experiments/a7_independencia.py`,
  `experiments/a8_identificacao_cartas_vistas.py`, `experiments/a9_calibracao.py` (novos), 3 resultados novos em
  `experiments/resultados/`, `experiments/README.md`, `evals/` (8 cenários novos), `SKILL.md`, `knowledge/*.md`;
  em `PROJECT_KNOWLEDGE/03_DECISIONS/` — este relatório (novo) e acréscimos datados em `STATISTICAL_AUDIT_2026-11-06.md`,
  `STATISTICAL_INVENTORY_2026-11-06.md` e `EVIDENCE.md`; acréscimos em `CURRENT_STATE.md`, `NEXT_STEPS.md` e `IN_PROGRESS.md`.
- Estado final: a Skill continua igual à da `main` exceto por esta rodada; para publicar, o commit deve ir num ramo a partir da `main`
  (a Skill já está lá) e não misturar com a 2026.11.06-1.

## Depois da rodada (06/11/2026): decisões do Pedro e versão 2026.11.06-2
O Pedro decidiu: identificação pelo NB2 (D-040), faixas das telas de torneio com a dependência (D-041), deck do adversário "incerto"
(D-042) e proteção da instalação real na ponte (arquivo pessoal `~/.sa_pastas_protegidas`, fora do repositório; feito e testado).
Antes de implementar, dois experimentos novos (registro completo):
- **a10** (limiar do "incerto"): critério fixado antes — menor limiar com acerto ≥ 90% nas não marcadas → **0,6** (marca ~10%, que
  acertam ~37%; as não marcadas, ~91%). Nas 18 partidas reais, as 10 identificações marcadas estavam erradas.
- **a11** (faixas, metades independentes por jogador): nas partidas das telas o ICC é **0,015** (Labs 0,032, online 0) — bem menor
  que o 0,063 do a7, que contava só W/L e incluía adversários de deck desconhecido. Cobertura das faixas antigas 93,1–96,3%; fator
  fixo ×1,25 exagera (98%); ICC calculado nos dados da tela acerta (94,8–95,3%). **O efeito real é pequeno:** faixas dos decks ~2%
  mais largas (máx. 6%), a matriz quase não muda. A frase "até ~25% estreitas" desta rodada valia só para o recorte do a7.
Implementação em ramo próprio (`nb2-faixas-incerto`, a partir da `main` 9c6519b), **publicada como 2026.11.06-2 (`101da5f`)**; detalhes em
`DONE.md` daquele ramo. a8 com o código novo: a regra do programa ficou idêntica ao NB2 em todos os turnos.

