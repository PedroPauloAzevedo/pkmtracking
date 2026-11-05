# Meus decks: listas, conferência do Standard, Consistência e Lista oficial

> Atualizado em 05/11/2026. Código: `tracker/decks.py` (Meus decks), `tracker/probabilidades.py` (Consistência),
> `tracker/lista_oficial.py`, `web/js/decks.js`, `web/js/deck_detalhe.js`, `web/js/lista_oficial.js`.
> Rotas: `/api/decks...`, `/api/lista-oficial`. Telas: `#meudeck-<id>`, `#lista-<id>`.

## Listas
Cadastro de listas (texto no formato do TCG Live/Limitless), versões de uma lista (`versao_de`), favorito, ativo, ícones
corrigíveis à mão (`icones_manual`). As cartas são convertidas para a arte básica (`carta_id`, `carta_base`). Listas com código
de coleção começando por número (ex.: `30C 152`) são lidas corretamente desde 2026.11.01-1.

## Conferência do Standard
60 cartas; até 4 com o mesmo nome (versões diferentes somam; Energia Básica livre); 1 ACE SPEC; pelo menos 1 Pokémon Básico;
só cartas com marca de regulamento válida (ou reimpressas com marca válida, mesmo nome e mesmo texto). O selo do deck mostra
"Standard ✓" ou "Fora do Standard". Regras em `../02_BUSINESS_RULES/STANDARD_AND_GAME_RULES.md`.

## Consistência (probabilidades exatas)
Mostra, para a lista: chance de mulligan, mulligans esperados por partida (e o observado nas suas partidas com essa lista),
e por carta: na mão inicial, até o 1º/2º/3º turno, alguma cópia nos prêmios, todas presas nos prêmios; e "duas cartas juntas".
Método (detalhe em `STATISTICS.md`): hipergeométrica exata; a mão que vale é sempre uma mão com **pelo menos 1** Básico
(o mulligan é condição); compras e prêmios saem das 53 cartas restantes. **Não considera efeitos de cartas** (Ultra Ball,
Buddy-Buddy Poffin...): os números são um piso, só pela sorte da compra.

### Exemplo conferido (02/11/2026) — use para validar mudanças na conta
Lista de 60 cartas com **11 Pokémon Básicos** (4 Dreepy, 2 Munkidori, 1 Fezandipiti ex, 1 Dunsparce, 1 Meowth ex, 2 Budew).
- Mulligan: C(49,7)/C(60,7) = **22,24%**; mão válida 77,76%; mulligans esperados por partida **0,29**.
- **Dreepy (4 cópias, Básico):** na mão **51,38%**; até o 1º/2º/3º turno **55,05% / 58,50% / 61,76%**; algum nos prêmios
  **34,02%**; todos nos prêmios ~0,00% (0,0051% × peso).
- **Judge (1 cópia, não Básico):** na mão **10,92%**; até o 1º/2º/3º turno **12,60% / 14,28% / 15,96%**; nos prêmios
  (algum = todos) **10,08%**.
- Dreepy **e** Judge juntos: mão 5,35%; até o 1º/2º/3º turno 6,64% / 8,03% / 9,51%.
Repare: o mulligan **aumenta** a chance de uma carta Básica estar na mão (as mãos descartadas são justamente as sem Básico) e
**diminui** a de uma carta que não é Básica.

## Lista oficial (PDF)
Formulário Deck List da Play! Pokémon: Standard marcado, nome, Player ID, nascimento e divisão de idade (calculada pela
temporada), Pokémon com coleção/número/marca, Treinadores, Energias, legenda das coleções e marcas. Tudo editável, salva sozinho
no deck (`lista_oficial`), "Refazer a partir do deck", papel A4 ou Carta, "Salvar em PDF" pela impressão do navegador
(cabe em 1 página A4). Nome, Player ID e nascimento ficam só em `dados/config.json` (D-029).

## Testes
`testes/teste_tracker.py` (listas e conferência), `testes/experimentos/e1_probabilidades.py` (conta exata × simulação, inclui
carta com 9 cópias), `testes/teste_telas.py` (telas `#meudeck` e `#lista`).
