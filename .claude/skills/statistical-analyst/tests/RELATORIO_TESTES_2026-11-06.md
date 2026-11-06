# Relatório de testes da Skill (Fase 6) — 06/11/2026

## 1. Testes automáticos
| Teste | O que confere | Resultado |
|---|---|---|
| `tests/test_sa_tools.py` (16 testes) | valores conhecidos, extremos, entradas inválidas, consistência (simetria e inversa da melhor de 3; ajuste de Holm/BH nunca diminui), simulações (ICC teórico 1/11; melhor de 3 por 100 mil sorteios; calibração), reprodutibilidade com semente, `registrar` não sobrescreve e respeita `SA_SAIDA` | OK |
| `tests/test_referencias.py` (4 testes) | toda função/constante citada em `KNOWN_METHODS.md` existe no código (mais de 40 referências); todo arquivo citado existe; `SKILL.md` com nome e descrição; nenhum nick, e-mail ou caminho do computador do Pedro na Skill | OK |
| 4 testes de entrega do programa (`teste_tracker`, `teste_seguranca`, `teste_replay`, `teste_telas`) numa cópia do diretório de trabalho | o programa continua inteiro (a Skill não muda código) | OK (a cópia incluía também as mudanças, sem commit, da 2026.11.06-1 de outra sessão) |

## 2. Cenários (cada um rodado por um agente independente, com e sem a Skill)
Os cenários estão em `evals/` (pergunta em `prompt.md`, o que se espera em `case.yaml`, um critério por arquivo em `graders/`). O
agente sem a Skill tinha acesso ao mesmo repositório, inclusive ao inventário e à auditoria em `PROJECT_KNOWLEDGE/` — então a
comparação mede o que a **Skill** acrescenta além da documentação. Nenhum dos 8 agentes alterou arquivo do projeto.

| Cenário (o que testa) | Com a Skill | Sem a Skill | Diferença observada |
|---|---|---|---|
| `reaproveita-k-confronto` — achar conhecimento pronto e não refazer pesquisa | 4/4 | 3/4 | sem a Skill escreveu um script novo que repete o a2; com a Skill reaproveitou o a2 |
| `amostra-pequena-matchup` — amostra pequena; 1 jogo × melhor de 3 | 4/4 | 3/4 | sem a Skill recalculou o Wilson à mão em vez de usar a função do programa |
| `nao-muda-sem-aprovacao` — não mudar o programa sem aprovação; detectar falsos positivos | 4/4 | 4/4 | os dois recusaram e mediram; com a Skill acrescentou faixa da diferença e Holm/BH |
| `consistencia-piso` — explicar uma fórmula; não chamar limitação de erro | 4/4 | 2/4 | sem a Skill não separou conta exata de simulação com efeitos e não citou a lacuna conhecida |
| **Total** | **16/16 (100%)** | **12/16 (75%)** | +25 pontos |

Tempo médio: ~226 s com a Skill, ~185 s sem (a Skill lê mais documentos antes de responder); tokens parecidos (~104 mil × ~100 mil).

## 3. O que os testes ensinaram (já aplicado)
- Os experimentos gravavam resultado sempre dentro do repositório; um agente teve de copiar o a2 para não sujar o projeto →
  `registrar` agora respeita `SA_SAIDA`.
- Os dois agentes do cenário de Consistência notaram que Nest Ball, Ultra Ball e Poffin **buscam Pokémon** (uma não traz a outra) e
  que a pergunta real é "pelo menos uma destas cartas" → `POKEMON_TCG_MODEL.md` e lacuna G15.
- O agente sem a Skill mostrou que o k escolhido pelo e3 muda com o corte no tempo (64/32/16/16) → registrado no achado 2.

## 4. Limitações destes testes
- 4 cenários, uma execução de cada: a diferença de 25 pontos é indicativa, não uma medida precisa.
- A nota foi dada por mim (quem escreveu a Skill), lendo as respostas; os critérios estavam escritos antes das execuções.
- Os cenários usam a cópia de teste com os dados do Pedro em 06/11; números citados podem mudar quando os dados crescerem.
- Não testado: comportamento com o programa em outra versão (as referências do `test_referencias.py` pegam renomeações, não
  mudanças de significado — como a que invalidou o e2).
