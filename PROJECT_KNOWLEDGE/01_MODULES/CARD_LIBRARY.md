# Biblioteca de cartas

> Atualizado em 05/11/2026. Código: `tracker/cartas.py`, `web/js/biblioteca.js`. Rotas: `/api/cartas...`, `/cartas/imagem`.
> Tela: Programa → Biblioteca de cartas.

## O que faz
Dados e imagens das cartas a partir do **TCGdex** (api.tcgdex.net, aberto, sem chave), sempre na **arte básica**.
- Guarda em `dados/cartas/`: `sets/<id>.json` (texto de cada coleção), `indice.json` (busca por nome e por coleção/número),
  `img/<id>.webp` (imagem, baixada só quando a carta aparece pela primeira vez).
- **Carta funcional** = mesmo nome + mesmos ataques/habilidades (+ PS, se Pokémon). **Arte básica** = a impressão de menor
  raridade dessa carta, preferindo a coleção mais recente. O **conversor** troca qualquer impressão pela arte básica
  (ex.: Dragapult ex TWM 214 → TWM 130): replay, listas e análises usam sempre a mesma imagem e o mesmo código.
- Cada carta do índice traz categoria, tipos, estágio, PS, marca de regulamento, raridade (ACE SPEC) e a "chave funcional"
  (`nome|PS|habilidades|ataques`), usada no replay para escolher a versão pelos PS e pelos golpes.
- `por_nome`: entre cartas de mesmo nome, prefere as que valem no Standard (marca válida, depois desconhecida, depois inválida).
- Atualização: nenhuma fonte gratuita avisa coleção nova; uma vez por dia o programa confere se o TCGdex tem coleção nova ou
  cartas novas numa coleção recente e baixa só o que mudou. Mudou o formato do índice → aumentar `cartas.VERSAO_INDICE` (hoje 2).
- Falha do TCGdex numa carta (3 tentativas em `_get`): desde a 2026.11.05-4 só aquela coleção fica como estava (o arquivo antigo
  é mantido), as outras seguem, e a tela mostra um aviso amarelo (`progresso["aviso"]`) com o nome dela. Com falha, `estado.json`
  guarda `falhas` e **não avança** `ultima_verificacao`, para o verificador tentar de novo na hora seguinte (D-034). Falha ao listar
  as séries continua parando tudo (erro em vermelho). "Baixar tudo de novo" faz milhares de pedidos: é onde a falha costuma aparecer.
- Imagem que não existe no TCGdex pode ser enviada à mão (arquivo ou link), por impressão ou como "arte padrão" pelo nome.
- A tela mostra as coleções baixadas e as cartas pedidas que não existem na biblioteca (`nao_encontradas`).

## Limites conhecidos
- O TCGdex não informa a marca de regulamento de algumas coleções novas (ex.: 30th Celebration → "confira na carta") e marca
  várias Energias Especiais como "Normal"; por isso **Energia Básica é reconhecida pelo nome**.
- Códigos de coleção do TCG Live são mapeados para os ids do TCGdex numa tabela no começo de `cartas.py`.
