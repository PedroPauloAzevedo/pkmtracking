# Experimentos de auditoria

> Atualizado em 06/11/2026. Todos só leem o banco. Rodar a partir da pasta de uma CÓPIA do programa (porta 8799):
> `python -I <este diretório>/a1_dados_e_selecao.py <pasta da cópia>`.

| Script | Pergunta | Achado |
|---|---|---|
| `a1_dados_e_selecao.py` | Quem tem lista vence mais? Empates, lado do jogador 1, dependência (ICC) | 1, 6, 10 |
| `a2_confronto_k.py` | k do confronto ajustado; poucos jogos × 50%; calibração | 2, 3 |
| `a3_efeito_cartas.py` | O efeito das cartas acrescenta previsão ao deck sozinho? | 1, 8 |
| `a4_identificacao.py` | Regra combinada de identificação × NB2 × ícones, sem vazamento; calibração | 4, 9 |
| `a5_muitos_testes.py` | Comparações múltiplas nas variantes e nas cartas | 5 |
| `a6_melhor_de_3.py` | Quanto a partida melhor de 3 se afasta do jogo único | 7 |
| `a7_independencia.py` | Até onde vale o ICC ≈ 0? (com faixa, por recorte; mão quente; Ladder) | 6 (revisto) |
| `a8_identificacao_cartas_vistas.py` | Identificação com cartas vistas, sem nada do teste no treino; métricas para classes desbalanceadas | 4, 9 (revisto) |
| `a9_calibracao.py` | Calibração do confronto ajustado a fundo (faixas, piso, inclinação, grupos, períodos) e comparação de modelos | 2, 3 (revisto) |

| `a10_limiar_incerto.py` | Limiar do deck "incerto" (D-042), reaproveitando o a8 sem alterá-lo | 4 (D-042) |
| `a11_faixas_dependencia.py` | Faixas do Meta/Matchups estreitas demais? Qual correção acerta (metades por jogador) | 6 (D-041) |
| `a12_etapas_ataque.py` | O roteiro do ataque dos juízes (ordem do dano, prêmios em nocautes simultâneos) aparece nos logs? | — (Judge Ball, 06/11) |
| `p_estrategia.py` | P1–P7 (rota, corrida, prêmios checados, troca, disrupção, stall/mill, sequência) — **pronto, não aplicado** | — (trava de amostra: P1 50, P3 100, demais 300 partidas) |
| `p0_viabilidade_estrategica.py` | O que os logs permitem na análise estratégica (rota, corrida, prêmios checados, disrupção, mill)? | — (estratégia; `knowledge/STRATEGIC_CONCEPTS.md`) |

a7–a9 são da rodada de hardening (`PROJECT_KNOWLEDGE/03_DECISIONS/STATISTICAL_HARDENING_2026-11-06.md`) e gravam o registro completo
(formato 2). a1–a6 e seus resultados ficaram como estavam (rodam com a ponte nova; o a4 refeito reproduziu os números de 06/11).

Achados descritos em `PROJECT_KNOWLEDGE/03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md`.

**`resultados/`**: cada execução grava um JSON novo (nunca sobrescreve) com data, semente, parâmetros, versão do código e uma
impressão dos dados (contagens das tabelas e datas, sem dado pessoal). Os de 06/11/2026 são a evidência da auditoria.
Para rodar sem deixar arquivo no repositório (exploração, teste), defina a variável `SA_SAIDA` com uma pasta do rascunho.

Padrão para um experimento novo: cabeçalho com pergunta, desenho (separação no tempo, o que é calculado só com o treino), semente e
uso; funções do Coletor pela `ponte`; contas novas pelo `sa_tools`; resultado por `sa_tools.registrar`; nada de nick ou caminho do
computador do Pedro na saída.
