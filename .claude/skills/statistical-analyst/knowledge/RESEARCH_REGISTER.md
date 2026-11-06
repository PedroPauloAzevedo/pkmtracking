# Registro de pesquisas

> Atualizado em 06/11/2026 (pesquisa de conceitos estratégicos, seção "Estratégia"). Antes de pesquisar fora: procure aqui, em `PROJECT_KNOWLEDGE/03_DECISIONS/MISSION_REPORT_2026-11-02.md`
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

## Estratégia do Pokémon TCG (06/11/2026) — buscas na web, resumos dos resultados (páginas não abertas por inteiro)
Pergunta: o projeto não tinha nada sobre prize mapping/racing/checking/trade, stall, lock, disrupção, mill e sequência (conferido em
`knowledge/`, `PROJECT_KNOWLEDGE/`, `MISSION_REPORT_2026-11-02.md`). Regras oficiais **não** foram pesquisadas: já estão no projeto
(`docs/regras-standard.md`, `STANDARD_AND_GAME_RULES.md`). Tipo: **def** = definição reconhecida; **op** = estratégia/opinião de
jogador (não é evidência); **mat** = matemática/método. Nenhuma fonte abaixo é evidência estatística; a evidência é o p0.
| Data | Conceito | Fonte (URL) | Tipo | Conclusão usada |
|---|---|---|---|---|
| 06/11/2026 | Prize mapping | TCG Protectors, "Thinking Two Turns Ahead – Prize Mapping Guide (2026)" https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-mapping-guide-2026 | def + op | Rota = sequência planejada de nocautes; 2-2-2 e 1-1-2-2 como mapas comuns. Página de loja, texto solto: só vocabulário |
| 06/11/2026 | Prize trade / racing | TCG Protectors, "Winning the Prize Race – Prize Trade" https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-prize-trade-guide-advanced-prize-mapping | def + op | Troca favorável = pegar mais prêmios do que ceder; atacantes de 1 prêmio forçam o adversário a mudar a rota. Opinião |
| 06/11/2026 | Prize trade | PokéBeach, "Small is Good – The Beauty of Single-Prize Attackers" https://www.pokebeach.com/?p=232566 | op | Tese "1 prêmio sempre vence multi-prêmio" — **opinião forte**, não regra; vira hipótese a medir (P4) |
| 06/11/2026 | Multi-prêmio | PokéJungle, "ex and Beyond – A History of Multi-Prize Pokémon" https://pokejungle.net/2019/10/08/ex-and-beyond-a-history-of-multi-prize-pokemon/ | def | Valores de prêmio por tipo de Pokémon ao longo das eras (conferir com as regras do projeto: ex 2, Mega ex 3) |
| 06/11/2026 | Prize checking | lastlegume, "Prize Card Probability in the Pokémon TCG" https://lastlegume.github.io/blog/prize_probability | mat | P(premiada) = P(fora da mão)·P(nos prêmios | fora da mão); 1 cópia → 10%. Igual à hipergeométrica do projeto |
| 06/11/2026 | Prize checking | X-act, "Odds in Pokemon" (Pojo, 2005) https://www.pojo.com/Features/X-Act/2005/Odds%20in%20Pokemon%203.htm | mat | Chance de premiar não depende da mão inicial (por simetria); prêmios inferidos pelo que falta no baralho mudam as chances seguintes |
| 06/11/2026 | Abertura (já usada) | Six Prizes, "TheMathTCG" https://sixprizes.com/2013/01/13/themathtcg-the-probabilities-behind/ | mat | Já registrada (MISSION_REPORT); não repetida |
| 06/11/2026 | Stall, lock, mill | Bulbapedia, "Snorlax Stall (TCG)" https://bulbapedia.bulbagarden.net/wiki/Snorlax_Stall_(TCG) ; PokéBeach "Run of the Mill – Control and Mill in Standard" https://pokebeach.com/?p=245131 ; Six Prizes "The Key to Lock Decks" https://sixprizes.com/2014/08/13/the-key-to-lock-decks/ | def + op | Stall = impedir prêmios; mill = esvaziar o baralho; lock = restringir itens/habilidades. Exemplos de eras passadas: confirmar o meta atual pelos torneios do Coletor |
| 06/11/2026 | Arquétipos | TCG Protectors, "Deck Archetypes – Aggro, Control, Combo & More" https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-deck-archetypes-guide-aggro-control-combo-midrange | def | Controle = desacelerar para executar um segundo plano; ferramentas: negação de recurso, lock de itens/habilidades |
| 06/11/2026 | Sequencing | ChannelFireball, "The Definitive Guide to Sequencing in Pokemon TCG — Applying Mathematics" https://strategy.channelfireball.com/all-strategy/channelpokemon/the-definitive-guide-to-sequencing-in-pokemon-tcg-applying-mathematics-more/ ; TCG Protectors "Advanced Sequencing" https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-advanced-sequencing-guide-grandmaster-playbook | def + op | Sequência dentro do turno é otimizável ("comprar antes de buscar"); vira padrão observável (P7), não regra |
| 06/11/2026 | Recursos, thinning | TCG Protectors "Resource Management" https://tcgprotectors.com/blogs/pokemon-blog/pokemon-tcg-resource-management-master-guide-2026 ; Pokémon-Zone "Thin to Win" https://www.pokemon-zone.com/articles/thin-to-win/ | op + mat | Thinning dá ganho pequeno (~1–2 pp no 1º turno, segundo a fonte); o projeto calcula pela hipergeométrica |
| 06/11/2026 | Decisão com informação escondida | Cowling, Powley e Whitehouse (2012), "Information Set Monte Carlo Tree Search", IEEE TCIAIG 4(2):120–143 https://eprints.whiterose.ac.uk/75048/ ; Cowling, Ward e Powley (2012), Magic: The Gathering https://eprints.whiterose.ac.uk/75050/ | mat | Busca sobre conjuntos de informação; determinização tem viés (fusão de estratégias). Base para "rota robusta" (`DECISION_ANALYSIS.md`) |
| (livro-texto, sem busca) | Tempo até evento, causalidade | Kaplan e Meier (1958); Cox (1972); Hernán e Robins, "Causal Inference: What If" (2020) | mat | Censura pela desistência; associação × causa nos experimentos P2, P5, P7 |
Descartadas: páginas geradas automaticamente (afirmavam limite de 7 cartas na mão — falso), páginas de Pokémon TCG Pocket (outras
regras) e calculadoras que tratam prêmios como parte do baralho sem dizer.

## Lacunas que podem pedir pesquisa externa (ainda não pesquisadas)
- Modelos de habilidade com mudança no tempo (ex.: Bradley-Terry dinâmico, Glicko) para épocas do meta — só se G3 for priorizada.
- Avaliação de decisões com informação escondida em jogos de cartas (modelagem de crença sobre a mão do adversário) — G6.
- Formato (melhor de 1 ou 3) dos torneios na API do Limitless — documentação da API (G8).
