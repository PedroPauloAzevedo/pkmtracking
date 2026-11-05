# Amigos: troca de logs

> Atualizado em 05/11/2026. Código: `tracker/compartilhar.py`, `web/js/amigos.js`. Rotas: `/api/amigos...`, `/exportar/meus-logs.zip`.
> Regras de dono: `../02_BUSINESS_RULES/PLAYERS_AND_OWNERSHIP.md`. Tela: Programa → Amigos.

## Arquivo .zip (manual)
- **Exportar (quem manda):** junta as SUAS partidas num .zip (`logs/<data>_<hash>.txt` com o log exato e `coletor-logs.json` com o
  nick do dono, a versão do programa e, para cada log, a data e as suas correções: decks, tags, notas). Logs de outros amigos
  nunca entram. O botão salva o arquivo na pasta Downloads e abre o Explorer com ele selecionado (pronto para WhatsApp/e-mail).
- **Importar (quem recebe):** aceita o .zip exportado, um .zip da pasta `dados/logs` ou .txt soltos. Cada partida é gravada com o
  nick do dono (origem `amigo`); logs repetidos são ignorados (pode importar de novo sem contar duas vezes).

## Pasta compartilhada do Google Drive (automático)
- Todos usam a **mesma pasta** do Google Drive para computador (uma pasta local sincronizada). Cada programa grava ali
  `logs-tcg_<nick>.zip` quando tem partidas novas e importa os arquivos dos outros, a cada `pasta_minutos` (30) e na hora
  em que a opção é ligada.
- A tela sugere onde o Google Drive costuma aparecer (unidades fixas, ex.: `G:\Meu Drive\...`) e tem um botão para escolher a
  pasta. A busca de unidades evita disquete/CD (antes travava a tela; corrigido em 2026.10.29-9).
- **O instalador do Coletor não instala o Google Drive:** cada amigo instala o "Google Drive para computador"
  (google.com/drive/download), entra na conta, aceita o convite da pasta e, no drive.google.com, em *Compartilhados comigo*,
  clica com o botão direito na pasta → *Organizar → Adicionar atalho ao Drive* (sem isso a pasta não aparece no computador).
  Depois informa o caminho em Programa → Amigos e liga o envio automático. O passo a passo para usuários está no `README.md`
  e no `COMECE_AQUI.txt`.
- **Permissão:** quem precisa **enviar** os próprios logs tem de ter acesso de **Editor** na pasta; "Leitor" só recebe.
  Recomendação: compartilhar só com o e-mail de cada amigo, não por link aberto.

## Na tela
Filtro **Jogador** em todas as telas pessoais (você, um amigo ou todos); jogos entre amigos contam uma vez em "Todos"
(impressão digital); lista de amigos com número de partidas, primeira e última; apagar um amigo apaga só as partidas dele.
