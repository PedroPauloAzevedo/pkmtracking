# Registro de pesquisas

> Atualizado em 06/11/2026. Antes de pesquisar fora: procure aqui, em `PROJECT_KNOWLEDGE/03_DECISIONS/MISSION_REPORT_2026-11-02.md`
> (seção 3) e em `DECISIONS.md` ("Pesquisado e descartado"). Pesquise só a lacuna; registre fonte, data e conclusão.

## Protocolo
1. Qual é a pergunta técnica? 2. O que o projeto já sabe (documentos, código, experimentos)? 3. O que exatamente falta?
4. Pesquisar só isso, em fontes técnicas (artigos, livros, documentação oficial de bibliotecas, regras oficiais do Pokémon TCG).
5. Registrar abaixo; se a literatura diverge da prática do projeto, registrar a divergência antes de propor mudança.

## Pesquisas internas já feitas (não repetir)
| Data | Pergunta | Onde | Conclusão |
|---|---|---|---|
| 01–02/11/2026 | Ferramentas parecidas, técnicas para meta e decks | `MISSION_REPORT_2026-11-02.md`, seção 3 | BT, empirical Bayes, NB, k-medoides, fictitious play adotados |
| 02/11/2026 | ACE SPEC separa versões? | `MISSION_REPORT`, adendo; e9 | Descreve, não prevê (D-020) |
| 02/11/2026 | Regressão por carta | e10 | Melhor que o bruto (D-021) |
| 02/11/2026 | Montar listas por otimização | `DECISIONS.md` | Descartado: sem modelo causal, otimizaria correlação |
| 02/11/2026 | Equilíbrio por programação linear | `DECISIONS.md` | Descartado: exigiria SciPy; fictitious play basta |
| 06/11/2026 | Inventário e auditoria do motor | `STATISTICAL_INVENTORY_2026-11-06.md`, `STATISTICAL_AUDIT_2026-11-06.md` | 10 achados |

## Fontes externas já usadas
| Fonte | Usada para | Registrada em |
|---|---|---|
| arXiv 2607.08692 (equilíbrio de Nash do meta do Pokémon TCG) | equilíbrio | MISSION_REPORT, seção 3 |
| HSReplay, "Game Theory and Deck Choice" (2020) | escolha de deck | idem |
| Six Prizes, "TheMathTCG" (2013) | probabilidades de abertura | idem |
| Counterwatch, encolhimento bayesiano de taxas | confronto ajustado | idem |
| Métodos clássicos usados na auditoria de 06/11, sem pesquisa nova (livro-texto): Wilson (1927); Hunter (2004), algoritmos MM para Bradley-Terry; Robinson (1951), fictitious play; Holm (1979); Benjamini & Hochberg (1995); Kish (1965), efeito de desenho; Efron & Tibshirani (1993), bootstrap | conferência das fórmulas e ferramentas novas | este arquivo, `FORMULAS.md` |

## Lacunas que podem pedir pesquisa externa (ainda não pesquisadas)
- Modelos de habilidade com mudança no tempo (ex.: Bradley-Terry dinâmico, Glicko) para épocas do meta — só se G3 for priorizada.
- Avaliação de decisões com informação escondida em jogos de cartas (modelagem de crença sobre a mão do adversário) — G6.
- Formato (melhor de 1 ou 3) dos torneios na API do Limitless — documentação da API (G8).
