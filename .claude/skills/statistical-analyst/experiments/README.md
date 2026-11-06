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

Achados descritos em `PROJECT_KNOWLEDGE/03_DECISIONS/STATISTICAL_AUDIT_2026-11-06.md`.

**`resultados/`**: cada execução grava um JSON novo (nunca sobrescreve) com data, semente, parâmetros, versão do código e uma
impressão dos dados (contagens das tabelas e datas, sem dado pessoal). Os de 06/11/2026 são a evidência da auditoria.
Para rodar sem deixar arquivo no repositório (exploração, teste), defina a variável `SA_SAIDA` com uma pasta do rascunho.

Padrão para um experimento novo: cabeçalho com pergunta, desenho (separação no tempo, o que é calculado só com o treino), semente e
uso; funções do Coletor pela `ponte`; contas novas pelo `sa_tools`; resultado por `sa_tools.registrar`; nada de nick ou caminho do
computador do Pedro na saída.
