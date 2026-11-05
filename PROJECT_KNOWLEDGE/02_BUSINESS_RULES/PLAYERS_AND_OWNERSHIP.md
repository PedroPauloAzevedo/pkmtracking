# Jogadores, "você" e o dono de cada partida

> Atualizado em 05/11/2026. Código: `tracker/analises.py` (`descobrir_eu`, `perspectiva`, `sem_repetidas`, `do_jogador`),
> `tracker/banco.py` (`inserir_partida`, `dono_provavel`, `separar_partidas_de_outros`, `hash_log`), `tracker/compartilhar.py` (`importar`),
> `tracker/leitor.py` (`quem_exportou`, `impressao_digital`). Decisões: D-008, D-009.

## Quem é "você"
- **Seu nick** = o configurado em Ajustes (`nick`). Sem nick: quem exportou a maioria dos SEUS logs; por último, quem mais aparece neles.
- **Ponto de vista de cada partida** (`perspectiva`): quem exportou o log (`resumo.exportou`), se o log mostrar; senão, o seu nick.
  Assim uma segunda conta sua também é lida do seu lado. Em log de amigo: o nick dele (se ele não estiver no log, quem exportou).
- **Quem exportou** (`quem_exportou`): o jogo só mostra o nome das cartas compradas por quem exportou e só lista a mão inicial
  dele; sublinhas "- " de efeito (buscas) não contam, porque aparecem para os dois.

## De quem é a partida (`partidas.dono`)
- `''` = sua; nick de um amigo = dele. Partidas de amigos ficam em `dados/logs_amigos/<nick>/` e nunca entram no .zip que você exporta.
- **Partida em que o seu nick não joga é de outra pessoa** (desde 2026.11.02-4): ao gravar uma partida sem dono, se o nick
  configurado não está entre os jogadores, ela vai para o amigo — o amigo já conhecido no programa; senão, quem exportou o log;
  senão, o primeiro jogador. Isso cobre o caso de colar ou copiar no seu computador o log de um amigo.
- Partidas antigas nessa situação são separadas sozinhas ao abrir o programa e quando o nick muda (`separar_partidas_de_outros`:
  só troca o dono, não apaga nada). Sem nick configurado, nada é separado.
- **Importar logs de um amigo:** o dono é o nick informado (ou o do arquivo exportado); precisa aparecer em pelo menos metade dos
  logs. Sem nick informado, vale quem exportou ≥ 80% dos logs (ou quem aparece em ≥ 80%). Logs seus não podem ser importados como
  de amigo.

## Partidas repetidas
- **Mesmo texto** (hash do log normalizado: linhas sem espaços nas pontas, sem linhas vazias) é ignorado: pode colar/importar de novo.
- **Mesmo jogo pelos dois lados** (você e um amigo exportaram a mesma partida): os textos diferem, mas a **impressão digital**
  (vencedor, perdedor, turnos, motivo, prêmios) é igual. Com **mais de um jogador marcado** no filtro, conta uma vez só (fica o
  seu log; entre dois amigos, o primeiro). Desde 2026.11.05-3 só se juntam logs de **donos diferentes**: dois logs do mesmo dono
  com a mesma impressão são jogos diferentes (ex.: duas vitórias de 6 a 3 em 12 turnos contra o mesmo amigo) — antes um deles
  sumia em "Todos os jogadores" (D-033).

## Filtro Jogador
- No painel é uma **caixa de opções** (desde 2026.11.05-3): marca-se qualquer combinação de você e dos amigos. A escolha vale em
  Início, Partidas, Desempenho e Decisões e fica guardada no navegador (`localStorage` "jogadores"). Não dá para desmarcar todos.
- No servidor (`analises.do_jogador`, `varios_jogadores`; `app._jogador_pedido`): `?jogadores=&jogadores=Fulano` (vazio = você)
  manda a lista; o formato antigo `?jogador=` continua valendo (`''` = só você, `'*'` = todos, ou o nick de um amigo).
- Cada partida é vista do lado de quem jogou (`perspectiva`). Com mais de um jogador marcado, a lista de partidas ganha a coluna
  Jogador.
