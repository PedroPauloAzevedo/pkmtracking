# Métodos conhecidos e matriz de validação

> Atualizado em 06/11/2026 (código `76a2005`, versão 2026.11.05-6; revisto na rodada de hardening, `STATISTICAL_HARDENING_2026-11-06.md`,
> com a7–a9). Classe depois da auditoria. Nenhuma linha virou "validada" só por documentação: cada mudança cita o experimento. Referências no formato
> `arquivo::nome` são conferidas por `tests/test_referencias.py` (falha se a função ou constante sumir ou mudar de nome).
> Ficha completa de cada método: `PROJECT_KNOWLEDGE/03_DECISIONS/STATISTICAL_INVENTORY_2026-11-06.md` (M1–M18).
> Achados: `PROJECT_KNOWLEDGE/03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md`.

Classes: A documentado · B implementado · C testado · D validado em experimento · E validado em dados reais · F insuficiente.

## Motor do programa (reutilizar; não reimplementar)
| Método | Onde | Parâmetros (motivo) | Classe | Evidência | Não demonstrado / cuidado |
|---|---|---|---|---|---|
| Hipergeométrica, mulligan, compras, prêmios | `tracker/probabilidades.py::carta`, `tracker/probabilidades.py::hipergeometrica`, `tracker/probabilidades.py::mulligan`, `tracker/probabilidades.py::mulligans_esperados`, `tracker/probabilidades.py::_maos` | 60/7/6; compras (1, 2, 3) | C + D | e1 (≤ 0,10 pp, 06/11) | Sem efeitos de cartas (piso); entrada impossível devolve zeros |
| Duas cartas juntas | `tracker/probabilidades.py::combo` | inclusão-exclusão | C + D | e1 | A ≠ B |
| Resumo da lista | `tracker/probabilidades.py::resumo_lista` | — | C | e1 | — |
| Taxa e faixa de Wilson | `tracker/analises.py::wilson`, `tracker/analises.py::placar` | z = 1,96; empate = não-vitória | C | valores de referência (06/11); ICC com lista ≈ 0 (a1/a7) | Sem correção de comparações múltiplas; com todos os jogadores de torneio o ICC é +0,063 (a7), mas nas partidas das telas (decks conhecidos, empate = não-vitória) é **0,015**: faixas antigas cobriam 93–96% (a11); **corrigido na v2026.11.06-2** (D-041, efeito de desenho) |
| Força dos decks (Bradley-Terry, MM) | `tracker/estrategia.py::forcas` | 200 iterações; prior 2 | C + D | forças sintéticas recuperadas (06/11) | Sozinha quase não prevê (0,6921 × 0,6931) |
| Confronto ajustado | `tracker/estrategia.py::confrontos_ajustados`, `tracker/estrategia.py::K_PADRAO` | k = 24 (e3; 12–32 empatam, a2) | **E** | e3, a2, a9 (log-loss 0,6778; ECE10 0,015 [0,007; 0,030], piso 0,009; inclinação 0,81 ± 0,05) | Com < 10 jogos empata com 50% (a2); **pior que 50% em 4 de 10 torneios de teste** (online pequenos; a9); descalibrado por grupo de jogador (com lista vence 56,6% × 50,3% previstos) — é modelo de deck, não de jogador |
| Qual deck jogar / campo | `tracker/estrategia.py::qual_deck` | 12 decks; campo = presença em partidas | B | — | Sem faixa; peso por partidas favorece quem vai longe |
| Equilíbrio do meta | `tracker/estrategia.py::equilibrio` | fictitious play, 20.000 rodadas | C | jogos de resposta conhecida (06/11) | Valor preditivo nunca medido; incerteza não propagada |
| Efeito de cada carta | `tracker/regressao.py::efeito_cartas`, `tracker/regressao.py::ajustar`, `tracker/regressao.py::PESO`, `tracker/regressao.py::MIN_LISTAS` | L2 = 300 (e10); ≥ 12 listas | C + E (contra o bruto) | e10, a3 | **Sem ganho sobre o deck sozinho** (−0,0007 [−0,0020; +0,0003]); 0 de 392 cartas "prováveis"; listas do topo |
| Identificação do deck (NB2) | `tracker/decks.py::identificar_nb`, `tracker/decks.py::_identificar_nb_direto`, `tracker/decks.py::BETA_NB`, `tracker/decks.py::MINIMO_LISTAS_NB` | β = 2; ≥ 3 listas; ≥ 200 listas | **E** (acurácia) | a4 (63,6–91,8%); a8 com cartas vistas realistas (63,4% no turno 1 → 92,5% no 8; real: 18 partidas, 1 deck, 66,7% → 88,9%) | **Confiança exagerada** (inclinação 0,56; ECE 3 pp × piso 0,6 pp, a8); prior do topo ajuda (uniforme é pior, a8); F1 macro menor que a regra combinada nos turnos 1–2 |
| Regra combinada (NB2 ≥ 0,5, senão ícones) | `tracker/decks.py::identificar`, `tracker/decks.py::CONFIANCA_NB`, `tracker/decks.py::_identificar_por_icones` | limiar 0,5 (sem medição) | D | a4, a8 | **Pior que o NB2 na acurácia** nos turnos 1–2 (−5,9 e −1,7 pp, a8; 51,2% × 63,6% com 2 cartas sorteadas, a4); **melhor no F1 macro** (0,58 × 0,53, turno 2): ajuda decks raros |
| Versões pela ACE SPEC | `tracker/variantes.py::variantes`, `tracker/variantes.py::DISTANCIA_JUNTAR`, `tracker/variantes.py::MIN_JOGOS_DIFERENCA` | 8% / 8 listas; 0,12; p < 0,05 e ≥ 30 jogos | E (descreve; não prevê) | e9 (todas a ±0,3 milésimo do deck inteiro) | Sem correção múltipla (7 marcas, 2 sobrevivem a Holm); listas do topo |
| Teste de duas proporções | `tracker/variantes.py::_valor_p` | bilateral | C | 60/100 × 50/100 → 0,155 | — |
| k-medoides + silhueta | `tracker/variantes.py::variantes_por_semelhanca`, `tracker/variantes.py::SILHUETA_MINIMA` | k 2–4; silhueta ≥ 0,25; semente 42 | C + D | e5 (silhueta 0,33–0,53) | Não prevê (e9) |
| Uso de cartas (com/sem) | `tracker/analises.py::_uso_cartas`, `tracker/analises.py::_uso_cartas_lento` | — | C | e6 (idêntico, 47× mais rápido) | Leitura com/sem é a pior previsão (log-loss 1,06); listas do topo |
| Carta × matchup | `tracker/analises.py::cartas_matchups` | aviso < 5 partidas | B | — | Mesmos cuidados do Uso de cartas |
| Meta, conversão, matriz | `tracker/analises.py::meta`, `tracker/analises.py::matchups_por_slug` | aviso < 10 partidas | B | contagem em `teste_tracker.py` | Partidas melhor de 3 (Labs) |
| Tendência | `tracker/analises.py::tendencia` | semana se > 20 torneios | B | — | Sem incerteza |
| Desempenho pessoal | `tracker/analises.py::analise_pessoal` | — | B | — | `meta_taxa` compara 1 jogo com melhor de 3 (achado 7); amostra pequena |
| Decisões | `tracker/analises.py::decisoes` | mínimo 3 partidas | B (F para causa) | — | Causalidade reversa, viés de duração, muitos testes |
| Replay (estado da mesa e das mãos) | `tracker/replay.py` | — | E | `EVIDENCE.md` (mãos 109/109, prêmios 253/253, descartes 182/182) | Mão/prêmios do adversário pouco observáveis |
| Épocas do meta | `tracker/colecoes.py::epocas`, `tracker/colecoes.py::epoca_de` | chegada ao Live, validade em torneio | C | `teste_tracker.py` (seções 6–7) | Hora de liberação pela regra, não por anúncio (D-036) |

## Análise estratégica (06/11/2026; nada implementado no programa — usa funções existentes)
| Método | Onde | Classe | Evidência | Não demonstrado / cuidado |
|---|---|---|---|---|
| Prêmios checados: hipergeométrica condicional ao estado (N, m, k por estado) | `tracker/probabilidades.py::hipergeometrica` + `knowledge/PRIZE_ANALYSIS.md` (§3) | C + D (exploratório) | p0: 14 partidas, 1 deck; "ao menos uma premiada" previsto 23,4% × real 22,5% | Só o lado de quem exportou, sem mulligan; amostra pequena |
| Rota de prêmios executada (sequência de "took N") | replay (`mesa[j].premios` por quadro) + p0 | C | observado (é o log) | A rota planejada não é observável |
| Corrida: vantagem em prêmios por turno × vencedor | p0 | B (descritivo) | líder no T9 venceu 39/49; T3–T6 ≈ moeda | Desistência (55%) é censura; não validado como previsão |
| Disrupção por categoria | p0 (lista de trabalho de cartas) | B (contagem) | mão em 47 de 83 partidas | Lista incompleta; efeito causal não identificável |
| Ferramentas P1–P7 (prontas, **não aplicadas**) | `tools/estrategia.py::tomadas`, `tools/estrategia.py::rotas_possiveis`, `tools/estrategia.py::corrida`, `tools/estrategia.py::premio_checado`, `tools/estrategia.py::zonas_desconhecidas`, `tools/estrategia.py::trocas`, `tools/estrategia.py::categorias_disrupcao`, `tools/estrategia.py::ngramas`, `tools/estrategia.py::kaplan_meier`, `tools/estrategia.py::diferenca_por_estrato` | C | `tests/test_estrategia.py` (casos à mão, simulação da hipergeométrica, igualdade com `probabilidades.hipergeometrica`, roteiro de ponta a ponta em dados sintéticos e trava de amostra) | Nenhum indicador validado: falta aplicar com amostra suficiente |

## Ferramentas da Skill (novas; só o que o programa não tem)
| Ferramenta | Onde | Classe | Evidência |
|---|---|---|---|
| log-loss, Brier, calibração | `tools/sa_tools.py::logloss`, `tools/sa_tools.py::brier`, `tools/sa_tools.py::calibracao` | C | `tests/test_sa_tools.py` (chute = ln 2; calibrado × exagerado) |
| Bootstrap agrupado, diferença pareada | `tools/sa_tools.py::bootstrap_agrupado`, `tools/sa_tools.py::diferenca_pareada` | C | testes: reprodutível com semente; mais largo com dependência |
| ICC, efeito de desenho, z com n efetivo | `tools/sa_tools.py::icc_binario`, `tools/sa_tools.py::efeito_desenho`, `tools/sa_tools.py::z_duas_proporcoes_efetivo` | C + D | ICC teórico 1/11 recuperado por simulação; z igual a `_valor_p` com efeito 1 |
| Holm, Benjamini-Hochberg | `tools/sa_tools.py::holm`, `tools/sa_tools.py::benjamini_hochberg` | C | exemplo conhecido |
| Melhor de 3 ↔ jogo | `tools/sa_tools.py::bo3_de_jogo`, `tools/sa_tools.py::jogo_de_bo3` | C + D | fórmula, inversa, simulação (100 mil) |
| Calibração a fundo | `tools/sa_tools.py::ece`, `tools/sa_tools.py::recalibracao_logistica`, `tools/sa_tools.py::calibracao_detalhada`, `tools/sa_tools.py::calibracao_por_grupo` | C + D | testes: inclinação recuperada (1 e 0,5); ECE ≈ 0 com 20 pp de erro por grupo detectado; piso cresce com as faixas |
| Registro de experimento (formato 2) | `tools/sa_tools.py::registrar`, `tools/sa_tools.py::impressao_banco`, `tools/sa_tools.py::impressao_objeto`, `tools/sa_tools.py::ambiente` | C + D | 9 testes de reprodutibilidade; a4 refeito = 06/11 até 12 algarismos |
| Ponte só leitura | `tools/ponte.py::carregar`, `tools/ponte.py::validar_copia`, `tools/ponte.py::FUNCOES_ESCRITA`, `tools/marcar_copia.py::marcar` | C | `tests/test_ponte.py` (22 testes pedem escrita de propósito); cópia real intacta depois de a4, a7–a9 e 8 agentes |

## Experimentos
| Experimento | Valida | Desenho | Situação |
|---|---|---|---|
| `testes/experimentos/e1_probabilidades.py` | conta exata da Consistência | simulação, semente 42 | válido |
| `testes/experimentos/e2_identificar_deck.py` | identificação | 70/30 no tempo, semente 7 | **coluna "atual" vaza o teste** (achado 9); usar `a4` |
| `testes/experimentos/e3_matchups.py` | confronto ajustado | 70/30 + validação interna de k | válido; `a2` acrescenta faixas |
| `testes/experimentos/e5_variantes.py` | grupos por semelhança | descritivo | válido |
| `testes/experimentos/e6_uso_cartas.py` | rápido = lento | igualdade | válido |
| `testes/experimentos/e9_ace_spec.py` | versões | 70/30 (parte 3) | válido |
| `testes/experimentos/e10_regressao_cartas.py` | efeito das cartas | 70/30; confronto só do treino | válido; `a3` acrescenta faixas |
| `testes/experimentos/e4_desempenho.py`, `e7_inserir.py`, `e8_analise_rapida.py` | tempo / igualdade entre versões | gravam no banco (e4, e7) | só em banco descartável |
| `experiments/a1_dados_e_selecao.py` | seleção das listas, empates, lado, ICC | contagem | 06/11 |
| `experiments/a2_confronto_k.py` | k, poucos jogos, calibração | 70/30; bootstrap por torneio | 06/11 |
| `experiments/a3_efeito_cartas.py` | cartas × deck sozinho | 70/30; bootstrap por torneio e jogador | 06/11 |
| `experiments/a4_identificacao.py` | regra combinada; calibração do NB2 | 70/30 sem vazamento | 06/11 |
| `experiments/a5_muitos_testes.py` | comparações múltiplas | Holm/BH | 06/11 |
| `experiments/a6_melhor_de_3.py` | 1 jogo × melhor de 3 | fórmula nos confrontos do Labs | 06/11 |
| `experiments/a10_limiar_incerto.py` | limiar do "incerto" (D-042) | linhas do a8; critério fixado antes | 06/11 → 0,6 |
| `experiments/a11_faixas_dependencia.py` | cobertura das faixas do meta (D-041) | metades independentes por jogador, 200 sorteios | 06/11 → ICC dos dados |
| `experiments/p0_viabilidade_estrategica.py` | o que os logs permitem na análise estratégica (rota, corrida, prêmios checados, disrupção, mill) | descritivo; hipergeométrica condicional contra prêmios revelados | 06/11 (estratégia; exploratório) |
| `experiments/a7_independencia.py` | ICC por recorte, com faixa; mão quente; Ladder | bootstrap por jogador | 06/11 (hardening) |
| `experiments/a8_identificacao_cartas_vistas.py` | identificação com cartas vistas; vazamento do a4; métricas desbalanceadas; calibração do NB2 | 70/30 sem nada do teste no treino; parte real com 18 partidas | 06/11 (hardening) |
| `experiments/a9_calibracao.py` | calibração do confronto ajustado por faixas, grupo, período; comparação de modelos | igual ao a2, as duas pontas | 06/11 (hardening) |
