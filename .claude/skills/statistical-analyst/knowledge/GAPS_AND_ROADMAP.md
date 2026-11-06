# Lacunas e roteiro (Fase 4)

> Atualizado em 06/11/2026 (G16–G19 e situação de G5/G6 na rodada de hardening). Cada lacuna foi conferida no código antes de entrar aqui (nada presumido ausente). Prioridade pesa impacto,
> esforço, risco e evidência. **Tudo que muda o programa precisa de decisão do Pedro e de medição contra o atual (D-017).**
> Impacto: o quanto melhora uma decisão real do Pedro ou dos amigos. Esforço: P (horas), M (1–2 sessões), G (várias).

## Matriz
| # | Lacuna / oportunidade | Situação verificada no código | Impacto | Esforço | Risco | Evidência | Prioridade |
|---|---|---|---|---|---|---|---|
| G0 | Corrigir o e2 (coluna "atual" vaza o teste) | `e2.atual` chama `decks.identificar` com o banco inteiro | Médio (evidência errada) | P | Nenhum (teste) | achado 9 | — (feito na v2026.11.06-2) |
| G1a | Regra de identificação: NB2 também abaixo de 0,5 | `decks.identificar` cai para ícones abaixo de 0,5 | Médio (deck do adversário em todas as telas pessoais) | P | Baixo (medir com cartas reais antes) | achado 4 | — (feito: D-040, v2026.11.06-2) |
| G2 | Aviso "só listas do topo" e taxa do campo ao lado | telas de cartas/versões não dizem a população | Alto (evita leitura errada) | P | Baixo (texto) | achado 1 | **3** |
| G3 | Converter "meta" para por jogo antes de comparar com o Ladder | `analise_pessoal.meta_taxa` usa partida melhor de 3 | Médio | P | Baixo | achado 7 | **4** |
| G4 | Benjamini-Hochberg nas "diferenças prováveis" das versões | `variantes._valor_p` sem correção | Médio | P | Baixo | achado 5 | 5 |
| G5 | Resultados dos experimentos guardados e versionados | e1–e10 só imprimem | Médio (reprodutibilidade) | P | Nenhum | inventário §4 | 6 |
| G6 | Validar a identificação com cartas vistas de verdade | e2/a4 sorteiam cartas | Médio | M | Nenhum | achado 4 | 7 |
| G7 | Peso maior para torneios recentes / por época no confronto ajustado e no prior do NB2 | sem decaimento; só filtro de datas | Médio (meta muda a cada coleção) | M | Médio | BACKLOG 4; recomendado em 02/11 | 8 |
| G8 | Formato (melhor de 1/3) dos torneios online | `info_json` não guarda | Baixo–médio | P–M | Baixo | a6 | 9 |
| G9 | Simulação de abertura com efeitos (Nest Ball, Poffin, Apoiadores de compra) | não existe (`probabilidades` é piso) | Médio (Consistência mais real) | G | Médio (cada carta = premissa) | BACKLOG 8 | 10 |
| G10 | Listas de todos os jogadores de alguns torneios online, para medir o viés por carta | importação limita a `listas_top` | Médio | M | Baixo (mais dados) | achado 1 | 11 |
| G11 | Desempenho pessoal com incerteza por época e com "força do adversário" | `analise_pessoal` só taxa + Wilson | Médio para o Pedro | M | Baixo | M15 | 12 |
| G12 | Decisões com comparação "situações parecidas" (pareamento por estado) em vez de com/sem | `decisoes` só correlação | Alto a longo prazo | G | Alto (causalidade, amostra pequena) | M16, `POKEMON_TCG_MODEL` §6 | 13 (depois de haver centenas de partidas) |
| G13 | Modelo do estado escondido (mão/deck do adversário) para avaliar jogadas | replay reconstrói o visível; NB2 identifica o deck | Alto a longo prazo | G | Alto | `POKEMON_TCG_MODEL` §5 | 14 (pesquisa) |
| G15 | Quadro "pelo menos uma destas cartas" na Consistência (cartas que fazem o mesmo serviço, ex.: Poffin, Nest Ball, Ultra Ball) | só existe "duas cartas juntas" (A **e** B); a conta sai de `probabilidades.carta` somando as cópias | Médio (responde a pergunta real do jogador) | P | Baixo | testes da Skill (cenário consistencia-piso) | 6 |
| G14 | Incerteza propagada no "Qual deck jogar" e no equilíbrio | sem faixa | Baixo–médio | M | Baixo | M5, M6 | 15 |
| G16 | Efeito de desenho nas faixas que juntam todas as partidas de torneio (Meta, Matchups) | **feito na v2026.11.06-2 (D-041), sem commit**; efeito real pequeno (ICC 0,015, a11) | Baixo | P | Baixo | a7, a11 | — |
| G17 | Confiança do deck do adversário: mostrar "incerto" e não tratar como probabilidade | NB2 com inclinação 0,56 (a8) | Médio | P | Baixo | a8, a10 | — (feito: D-042, v2026.11.06-2) |
| G18 | Escolher a métrica da identificação antes de mudar a regra (acurácia × decks raros) | NB2 ganha na acurácia, regra atual no F1 macro | Médio | P | Baixo | a8 | — (Pedro escolheu acurácia: D-040) |
| G20 | Atribuição de prêmios a cada nocaute no resumo do Coletor (`resumo.nocautes`) | coerente com o valor pelo nome em só 76% de 372 nocautes (nocautes duplos; a12: vários nocautes do mesmo dono viram um só "took N", e `leitor.resumo` dá o N inteiro a um nocaute) | Médio (base de prize trade/mapping) | P–M | Baixo | p0 | 7 (mudança no Coletor: pedir ao Pedro) |
| G21 | Experimentos estratégicos P1–P4 (rota, corrida, prêmios checados, troca) na Skill | **ferramentas e roteiro prontos** (`p_estrategia.py`), não aplicados (poucos jogos) | Médio | M | Nenhum (só leitura) | p0 | 8 (aplicar quando houver ≥ 100–300 partidas) |
| G22 | P5–P7 (disrupção, stall/mill, sequência) | **ferramentas prontas**, não aplicadas; p0 contou eventos; sem casos de deck-out | Baixo–médio (exploratório até haver centenas de partidas) | M | Nenhum | p0 | 12 |
| G23 | Tabela de cartas por categoria estratégica (disrupção, lock, puxar, cura) mantida por coleção | lista de trabalho no p0 (incompleta) | Médio para P5/P6 | P | Baixo | p0 | 9 |
| G24 | Ler o `Damage breakdown` dos logs (bônus de dano usados, Fraqueza/Resistência reais do defensor) | o leitor ignora as linhas `•` do breakdown | Médio (rotas de prêmio; efeito de cartas de dano observado em vez de inferido) | P–M | Baixo, mas muda o leitor (`VERSAO_LEITOR`): pedir ao Pedro | a12 | 10 |
| G24 | Registrar no Coletor a mão nova depois de mulligan e o "valor de prêmio" alterado por cartas | o log não traz; o replay não tem | Baixo (limita P3 e P1) | — (o jogo não escreve) | — | `BATTLE_LOG_FORMAT.md` §3 | sem ação possível hoje |
| G19 | Acompanhar o confronto ajustado em torneios online pequenos (pior que 50% em 4 de 10) | sem peso por tamanho/qualidade do torneio | Médio | M | Médio | a9 | 9 |

**Movidos na rodada de hardening (06/11):** G5 **feito para os experimentos da Skill** (registro completo, a7–a9; os e1–e10 do
programa continuam só imprimindo); G6 **parcial** (a8: real com 18 partidas de 1 deck + sintético realista; falta o mesmo jogo
exportado pelos dois lados para ter o deck do adversário com gabarito).

Itens verificados e que **não** são lacuna: validação fora da amostra (existe: e3, e9, e10, a2–a4); interações carta × adversário
(existe, descritivo: `cartas_matchups`); desempenho por jogador (existe: filtro Jogador, D-033); consistência exata (existe: M1).

## Roteiro sugerido
1. **Já, sem mexer no programa:** G0 e G5 (código de teste; pedir ao Pedro porque fica em `testes/`), G6 com os jogos vistos pelos
   dois lados.
2. **Próxima versão, mudanças pequenas de tela (decisão do Pedro):** G2, G3, G4; G1a depois de G6 confirmar.
3. **Estudos com medição:** G7 (e3/a2 com pesos no tempo), G10, G8.
4. **Projetos maiores:** G9 (com o e1 como base de conferência), G11, depois G12/G13 quando houver volume de partidas.
