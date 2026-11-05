# Base de regras do Standard

> Atualizado em 05/11/2026. Código: `tracker/regras_jogo.py`, `web/js/regras_standard.js`. Texto: `docs/regras-standard.md`.
> Rotas: `/api/regras-standard...`. Tela: Programa → Regras do Standard. Regras usadas: `../02_BUSINESS_RULES/STANDARD_AND_GAME_RULES.md`.

## O que é
Resumo em português dos documentos oficiais da Play! Pokémon, **só do formato Standard**, dentro do programa.
- `docs/regras-standard.md`: cópia que vem com o programa (**o caminho é fixo no código; não mover**).
- `dados/regras-standard.md`: cópia mais nova baixada do GitHub (o programa confere uma vez por dia). Assim uma mudança na base
  chega aos amigos **sem versão nova do programa**.
- A data vem da primeira linha depois do título: `Atualizada em dd/mmm/aaaa.` (ex.: `Atualizada em 30/out/2026.`).

## O que o programa lê da base (não mudar estes formatos)
- A tabela da seção `### Marcas de regulamento do Standard` (colunas `| Marca | Vale desde |`) → marcas válidas hoje
  (`marcas_standard`). Uma rotação de marcas chega sem atualizar o programa.
- O item `**Promos já liberados:**` → cartas antigas liberadas pelo nome (ex.: Professor's Research SWSH152, Poké Ball SWSH146,
  Boss's Orders SWSH251).
- A tela mostra o texto com índice, busca sem acento e o quadro "O que o programa usa destas regras".

## Rotina mensal
1. Uma tarefa agendada na conta do Pedro (todo dia 2, à noite; precisa do PC ligado) revisa a base e avisa quando a cópia do
   programa precisa ser atualizada. O documento vivo da base fica no Claude Docs do Pedro (link e códigos em `CLAUDE.local.md`).
2. Quando avisar: exportar o documento em Markdown, trocar a linha da data por `Atualizada em dd/mmm/aaaa.`, salvar em
   `docs/regras-standard.md`, conferir que a tabela de marcas e o item de promos mantiveram o formato e publicar (commit e push;
   não precisa mudar `versao.txt`).

## Pendências
- Confirmar a marca de regulamento da coleção 30th Celebration (o TCGdex não informa).
- Acompanhar a rotação de 2027 pela tabela de marcas.
