# Coletor de Partidas TCG Live

Programa que roda no seu computador enquanto você joga Pokémon TCG Live:

- **Captura sozinho** o histórico (Battle Log) de cada partida e guarda num banco local.
- **Importa campeonatos** do Limitless Labs (classificação, decks, listas) com o resultado de cada mesa vindo do RK9.
- **Mostra análises** num painel no navegador: seu desempenho, meta, matchups, perfil de deck, uso de cartas e comparação de listas.
- **Exporta para o Excel** (CSV com ponto e vírgula, abre direto no Excel em português).

Nada sai do seu computador, a não ser os pedidos que o importador faz aos sites do Limitless e do RK9.

---

## 1. Instalar (uma vez)

**Baixar:** nesta página do GitHub, clique no botão verde **Code > Download ZIP** e descompacte onde quiser.
Cada pessoa tem os próprios dados (pasta `dados/`, que nunca vai para o GitHub), então dá para compartilhar o link
com amigos: cada um instala, informa o próprio nick em Ajustes e usa no seu computador.
Atualizações: em **Ajustes > Atualizações** o programa avisa quando há versão nova aqui e se atualiza com um clique.

**Windows, jeito mais fácil (sem Python):** peça o `ColetorTCG-Instalador-<versão>.exe` a quem já usa o programa
(ele ainda não fica disponível aqui no GitHub), dê dois cliques e siga as telas. Se o Windows mostrar "O Windows protegeu o
computador", clique em **Mais informações > Executar assim mesmo**. O programa vai para
`%LOCALAPPDATA%\Programs\ColetorTCG`, cria o atalho na Área de Trabalho e já vem com o modo automático.
Para montar o instalador: `python instalador/montar.py` (precisa do Inno Setup 6; veja o começo do script).

**Windows, pelo código**
1. Instale o Python 3.11 ou mais novo em https://www.python.org/downloads/ e marque **"Add python.exe to PATH"** na primeira tela.
2. Descompacte esta pasta onde quiser (ex.: `Documentos\tcg-tracker`).
3. Dê dois cliques em `instalar_windows.bat`. Ele cria um ambiente isolado (`.venv`) e instala as dependências.
   Ele pergunta se você quer o modo automático; pode responder depois rodando o instalador de novo.

**macOS**
1. Instale o Python 3 (python.org).
2. No Terminal, dentro da pasta: `bash instalar_mac.command`.

## 2. Usar

1. Abra pelo atalho **Coletor TCG Live** da Área de Trabalho (o instalador cria; ou use `iniciar_windows.bat`).
   No Windows o programa fica num **ícone perto do relógio** (bolinha verde = captura ligada) e o painel abre em
   http://127.0.0.1:8765. Clique no ícone para abrir o painel; botão direito para ligar/desligar a captura ou sair.
   No Mac: `iniciar_mac.command` (deixe a janela do Terminal aberta).
2. Em **Ajustes e captura**, informe seu nick do TCG Live.
3. Jogue normalmente. No fim da partida, clique em **Battle Log** e no botão de **exportar** (canto superior direito).
   O programa percebe o log na área de transferência e grava na hora. Aparece o aviso "Nova partida registrada".
4. Para fechar: botão direito no ícone > **Sair** (fechar a aba do navegador não fecha o programa).
   Quer a janela preta antiga? `python app.py --janela`.

Logs repetidos são ignorados, então pode exportar a mesma partida duas vezes sem problema.
Cada log também é salvo como `.txt` em `dados/logs/` (backup).

## 3. Juntar partidas com amigos

Cada pessoa usa o próprio programa e vocês trocam um arquivo .zip (WhatsApp, e-mail, Drive):

1. **Quem manda:** Programa ⚙ > **Amigos (trocar logs)** > **Exportar meus logs**. O arquivo vai para a pasta
   Downloads, que abre com ele selecionado. Só vão as suas partidas (as recebidas de outros amigos ficam de fora).
2. **Quem recebe:** na mesma tela, em **Receber logs de um amigo**, escolha o .zip e clique em **Importar**.
   O nick do dono vem dentro do arquivo. Partidas repetidas são ignoradas, então pode mandar tudo de novo quando quiser.
**Automático (recomendado):** todos usam a mesma pasta compartilhada do Google Drive para computador.
Em **Amigos (trocar logs) > Automático**, escolha a pasta e ligue "Enviar e receber sozinho". A cada 30 minutos
(ou o intervalo escolhido) o programa grava `logs-tcg_<seu nick>.zip` nessa pasta e importa os arquivos dos outros.
Quem recebeu o convite da pasta precisa, no drive.google.com, ir em *Compartilhados comigo* > botão direito na pasta >
*Organizar > Adicionar atalho* ao Meu Drive; sem isso a pasta não aparece no computador.

3. Em Painel, Partidas, Desempenho e Decisões aparece o filtro **Jogador**, uma caixa de opções: marque você, um ou
   vários amigos, em qualquer combinação (cada partida vista do lado de quem jogou; um jogo entre dois jogadores
   marcados conta uma vez só, pela "impressão digital" da partida). A escolha vale em todas essas telas e fica
   guardada. Meus decks continua só com as suas partidas.

## 4. Modo automático (opcional, experimental)

Jeito rápido: **Programa > Ajustes e captura > Modo automático > Usar imagens prontas** (imagens dos botões do
projeto [Full Bench](https://github.com/heatfireash/FullBench), licença MIT) e **Ligar modo automático**.
O programa descobre sozinho o tamanho dos botões no seu monitor, cobre o botão Continue com um quadrinho vermelho
enquanto copia (clique nele para liberar), tenta de novo se o log não chegar e avisa quando uma partida foi perdida.

Faz os dois cliques do passo 3 por você: termina a partida, e ela já está registrada.

1. Instale o extra (`instalar_windows.bat` e responda `s`, ou `pip install -r requirements-auto.txt` no ambiente).
2. Recorte as imagens dos botões e envie em **Ajustes > Modo automático** (ou salve em `modelos/`; veja `modelos/LEIA-ME.txt`).
3. Em **Ajustes e captura**, clique em **Ligar modo automático**.

Ele reconhece os botões comparando a tela com as suas imagens e clica neles. Não lê a memória do jogo, não mexe
nos arquivos do jogo e não toma decisões de jogo. Ainda assim é automação de cliques no cliente oficial,
algo que os termos de uso de jogos online costumam restringir: use por sua conta e risco.
No macOS é preciso liberar o Terminal em Privacidade e Segurança > Gravação de Tela e Acessibilidade.

**Sobre "ler a tela e montar o próprio log":** não foi implementado. Reconhecer cartas, ataques e dano por imagem
durante a partida exigiria visão computacional treinada para o jogo, erraria com animações e mudanças de layout,
e geraria um log pior do que o que o próprio jogo já entrega pronto. Reconhecer só dois botões no fim da partida
é simples e confiável, por isso esse foi o caminho escolhido.

**O jogo grava o log em algum arquivo?** Até onde se sabe, não. Em **Ajustes > Procurar o log nos arquivos do jogo**
(ou `python app.py --diagnostico`) o programa vasculha as pastas do TCG Live. Se achar, dá para ler direto do disco.

## 5. Importar campeonatos

Duas fontes, escolhidas em **Fonte** nas telas de Meta e torneios:
- **Grandes eventos** (Regionais, Internacionais, Mundial): Limitless Labs + RK9, como abaixo. O programa confere no
  índice do limitlesstcg.com o formato de cada evento; o que não é Standard fica fora das contas.
- **Torneios online** (play.limitlesstcg.com): a API pública do Limitless traz deck, lista e resultado de cada mesa.
  A atualização automática importa os Standard com 64+ jogadores dos últimos 21 dias (ajustável em **Torneios**),
  no máximo 40 por verificação, porque o site aceita 50 pedidos a cada 5 minutos sem chave.

**Automático (padrão):** o RK9 e o Limitless Labs não têm API nem aviso de torneio novo para os campeonatos oficiais,
então o próprio programa verifica a cada 6 horas (ajustável) enquanto estiver aberto. Ele importa os torneios que
começaram nos últimos 45 dias e ainda não estão no banco, e reimporta os que foram baixados durante o evento,
até 3 dias depois do início, para pegar o resultado final e as listas publicadas depois.
Configure em **Importar torneios > Atualização automática**, ou rode `python app.py --sincronizar`.

**Para não precisar abrir nada:** em **Programa > Ajustes e captura > Como abrir o programa**, ligue
"Abrir sozinho quando o Windows liga" (ou rode `iniciar_com_o_windows.bat` uma vez). O coletor abre com o computador,
fica no ícone perto do relógio, captura as partidas e atualiza os torneios em segundo plano.
Para desfazer: o mesmo botão (Desligar) ou `nao_iniciar_com_o_windows.bat`.

**Manual:** em **Importar torneios**:
- **Buscar torneios no Limitless Labs** lista os eventos; clique em **Importar**.
- Ou digite o número do torneio (o número na URL do Labs, ex.: `labs.limitlesstcg.com/0078/standings` → `0078`).
- **Listas do topo**: quantas listas de cartas baixar (padrão 64). Cada lista é uma página; 0 = nenhuma.

O importador espera um pouco entre cada página e respeita o robots.txt dos sites. Um Regional grande leva alguns minutos.
Se o RK9 estiver fora do ar, ele usa as páginas de cada jogador no Labs (só para o top 256).
Por linha de comando: `python app.py --importar 0078`.

Os sites não têm API pública para esses dados; o importador lê as páginas. Se o layout mudar, a importação pode falhar
e o erro aparece no painel. Uso pessoal.

## 6. Replay e biblioteca de cartas

**Replay:** abra uma partida e clique em **▶ Ver replay**. A mesa é reconstruída linha a linha a partir do log:
Pokémon Ativo e Banco de cada jogador com as imagens das cartas, dano, energias e ferramentas ligadas, prêmios
restantes, Estádio, nocauteados e a mão de cada jogador. Avance com as setas do teclado, os botões ou o botão
Reproduzir; dá para pular direto para um turno e clicar em qualquer linha do log. Só aparece com a face o que o log
revela: a sua mão inteira; da mão do adversário, as cartas que ele buscou no baralho; e os prêmios que você pegou,
que aparecem desde o começo da partida (os outros prêmios ficam virados).

**Biblioteca de cartas** (menu Programa): dados e imagens vêm do TCGdex (base aberta e gratuita). Só a arte
básica de cada carta é guardada; as imagens são baixadas na primeira vez que aparecem (ou todas de uma vez,
para usar sem internet). O **conversor** troca qualquer arte alternativa pela arte básica da mesma carta
(mesmo nome e mesmos ataques), no replay, nas listas dos torneios e nas análises, então as artes diferentes
deixam de virar "cartas diferentes" nas contas.

**Coleções novas:** nenhuma fonte gratuita de cartas oferece aviso (webhook) de lançamento. O TCGdex não tem;
o Scrydex (sucessor pago do pokemontcg.io) só avisa mudança de preço. Por isso o programa confere uma vez por
dia e baixa só o que mudou; também há o botão **Verificar agora**.

**Imagem que não carrega ou carta nova demais:** em Biblioteca de cartas > Adicionar imagem à mão, envie o
arquivo ou cole o link da imagem, com coleção e número (ex.: Mew ex 30C 152). Marque "arte padrão" para usá-la
sempre que a carta aparecer pelo nome.

**Meus decks:** cadastre as listas que você joga (no TCG Live, abra o deck e use Exportar; cole a lista).
Cada partida capturada é ligada sozinha à lista que contém todas as cartas que você revelou, e cada lista tem
seu próprio histórico (taxa de vitória, contra cada deck, partidas). Para testar mudanças, use "Criar nova versão".

**Deck de cada jogador:** identificado comparando as cartas reveladas no log (inclusive as listas de compra e
descarte) com os decks do Limitless: Pokémon do ícone de cada deck e cartas típicas das listas dos torneios
importados. Na tela da partida dá para escolher outro deck numa lista com os nomes do Limitless.

**Cartas com o mesmo nome** (ex.: Dunsparce TEF 128 e JTG 120): o log só traz o nome. O programa escolhe a
versão pelo ataque ou habilidade usado no log, depois pela sua lista em Meus decks, depois pela versão mais usada
nos torneios.

## 7. O que cada aba mostra

O menu tem 4 seções: **Início**, **Minhas partidas** (abas Partidas, Desempenho e Decisões), **Meus decks**
(com a Lista oficial em PDF) e **Meta e torneios** (abas Meta, Matchups, Perfil de deck, Uso de cartas,
Cartas x matchups e Torneios). Embaixo, **Programa** reúne Regras do Standard, Ajustes e captura, Amigos,
Biblioteca de cartas, Linhas não lidas e Regras de leitura.

| Aba | Conteúdo |
|---|---|
| Início | Se a captura está pronta, partidas, taxa de vitória com faixa de confiança, começando x segundo, últimas partidas, colar log à mão |
| Partidas | Lista com filtros; detalhe com corrida de prêmios, nocautes, eventos; corrigir nome dos decks, tags e notas; "Log original" para copiar ou baixar o log como veio do jogo |
| Decisões | Aberturas e ritmo, separados por quem começou (filtro Todas / Começando / Indo em segundo) |
| Meus decks | Suas listas, conferência do Standard (selo Standard ✓) e Lista oficial (PDF) no formulário da Play! Pokémon |
| Desempenho | Taxa contra cada deck (comparada com os campeonatos), com cada deck seu, ordem, 1º nocaute, mulligan, como termina, evolução no tempo |
| Meta | % do campo, taxa de vitória sem espelhos, conversão para o Top X e fator de conversão, tendência entre torneios |
| Matchups | Matriz deck x deck com cor por taxa e número de partidas |
| Perfil de deck | Matchups contra o campo, taxa esperada contra o meta, melhores colocações, presença por torneio, esqueleto da lista |
| Cartas | % das listas, média e distribuição de cópias, taxa de vitória com/sem a carta; comparar duas listas carta a carta |
| Regras do Standard | Resumo em português das regras oficiais, com índice e busca |
| Regras de leitura | Editar as expressões regulares que leem o log e testar linhas |

**Época (coleção nova):** cada coleção nova pode mudar o meta. Em Partidas, Desempenho, Decisões e nas telas de
Meta e torneios, o campo **Época** mostra só o que aconteceu durante a época de uma coleção (ou "Todas as épocas").
Nas suas partidas a época começa quando a coleção chega ao TCG Live (na véspera do lançamento nas lojas, às 10h do
horário do Pacífico, ou seja, 14h ou 15h em Brasília); nos torneios, quando ela passa a valer (segunda sexta-feira
depois do lançamento). A lista de partidas mostra uma linha onde começa cada época, e os gráficos de evolução, uma linha
tracejada.

**Taxa de vitória** = vitórias ÷ (vitórias + derrotas + empates), como no Limitless.
**Faixa de confiança (95%)**: com poucas partidas a taxa engana; a faixa mostra onde ela provavelmente está.
**Fator de conversão**: participação do deck no Top X dividida pela participação no campo. Acima de 1, converte melhor que a média.
**Taxa esperada contra o campo**: média dos matchups do deck, pesada pela presença de cada adversário.

Para comparar seus resultados com os campeonatos, use nos seus decks o mesmo nome que o Limitless usa (ex.: "Dragapult ex").

## 8. Arquivos

O mapa completo do programa (cada pasta e cada módulo) está em
[`PROJECT_KNOWLEDGE/00_CENTRAL/ARCHITECTURE.md`](PROJECT_KNOWLEDGE/00_CENTRAL/ARCHITECTURE.md); toda a documentação de quem
desenvolve começa em [`PROJECT_KNOWLEDGE/00_CENTRAL/INDEX.md`](PROJECT_KNOWLEDGE/00_CENTRAL/INDEX.md).
Para aprender como o log vira dados, comece por `tracker/leitor.py`.

Os seus dados ficam na pasta `dados/`, criada ao rodar: `tracker.db` (banco), `logs/` (cópia de cada partida), `config.json`
(suas configurações) e `regras.json` (regras de leitura). Ela nunca vai para o GitHub e as atualizações não mexem nela.

O banco `dados/tracker.db` é SQLite: dá para abrir no DB Browser for SQLite ou ligar no Power BI.
Para fazer backup, copie a pasta `dados`.

## 9. Problemas comuns

- **A partida não foi registrada**: confira se o ícone do Coletor está perto do relógio (se não aparecer, olhe na setinha ^)
  e se a bolinha está verde (captura ligada). O Início do painel também mostra isso.
  Teste copiando um log antigo (Ctrl+C) com o programa aberto.
- **Venceu/perdeu aparece como "?"**: informe seu nick em Ajustes exatamente como aparece no log.
- **Linhas não lidas**: o TCG Live pode escrever alguma frase diferente. Copie a linha, cole em Regras de leitura > Testar e ajuste/crie uma regra.
- **Porta ocupada**: troque `"porta"` em `dados/config.json`.
