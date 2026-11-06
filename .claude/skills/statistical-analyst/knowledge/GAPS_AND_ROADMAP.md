# Lacunas e roteiro (Fase 4)

> Atualizado em 06/11/2026. Cada lacuna foi conferida no código antes de entrar aqui (nada presumido ausente). Prioridade pesa impacto,
> esforço, risco e evidência. **Tudo que muda o programa precisa de decisão do Pedro e de medição contra o atual (D-017).**
> Impacto: o quanto melhora uma decisão real do Pedro ou dos amigos. Esforço: P (horas), M (1–2 sessões), G (várias).

## Matriz
| # | Lacuna / oportunidade | Situação verificada no código | Impacto | Esforço | Risco | Evidência | Prioridade |
|---|---|---|---|---|---|---|---|
| G0 | Corrigir o e2 (coluna "atual" vaza o teste) | `e2.atual` chama `decks.identificar` com o banco inteiro | Médio (evidência errada) | P | Nenhum (teste) | achado 9 | **1** |
| G1a | Regra de identificação: NB2 também abaixo de 0,5 | `decks.identificar` cai para ícones abaixo de 0,5 | Médio (deck do adversário em todas as telas pessoais) | P | Baixo (medir com cartas reais antes) | achado 4 | **2** |
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

Itens verificados e que **não** são lacuna: validação fora da amostra (existe: e3, e9, e10, a2–a4); interações carta × adversário
(existe, descritivo: `cartas_matchups`); desempenho por jogador (existe: filtro Jogador, D-033); consistência exata (existe: M1).

## Roteiro sugerido
1. **Já, sem mexer no programa:** G0 e G5 (código de teste; pedir ao Pedro porque fica em `testes/`), G6 com os jogos vistos pelos
   dois lados.
2. **Próxima versão, mudanças pequenas de tela (decisão do Pedro):** G2, G3, G4; G1a depois de G6 confirmar.
3. **Estudos com medição:** G7 (e3/a2 com pesos no tempo), G10, G8.
4. **Projetos maiores:** G9 (com o e1 como base de conferência), G11, depois G12/G13 quando houver volume de partidas.
