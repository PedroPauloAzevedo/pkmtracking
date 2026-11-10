# Ferramentas de referência (outros apps de Battle Log do Pokémon TCG Live)

> Atualizado em 09/11/2026. Lista dos aplicativos e projetos usados como pesquisa, o que cada um ensina ao Coletor e o que já foi
> verificado. Uma rotina mensal (tarefa agendada no computador do Pedro; detalhes em `CLAUDE.local.md`) confere cada item, registra
> as novidades num relatório fora do GitHub (`ferramentas/pesquisa/`) e propõe o que vale implementar. Mudanças no programa só
> com o pedido do Pedro. Código de outros projetos **não** é copiado: só ideias (vários têm licença fechada).
>
> Origem: documento de contexto do Pedro (09/11/2026) + verificação nos repositórios e sites. "Não confirmado" = não verificado
> por nós.

## 1. Lista (verificada em 09/11/2026)
| Ferramenta | Onde | Tipo | Captura automática | Log detalhado | O que olhar todo mês |
|---|---|---|---|---|---|
| Full Bench | fullbench.gg · github.com/heatfireash/FullBench (Python, licença própria) | Desktop Windows (+ Mac beta) e site | Sim (tela de resultado + cópia do log) | Sim | `FULLBENCH.md`, commits, versão |
| PTCGL Tracker / PTCGL Replayer (PTCG Tools) | replay.ptcgtools.com · github.com/1ulce/PTCGL-Tracker-Releases (só executáveis) | Desktop Windows/Mac + site | Sim | Sim; partidas públicas compartilhadas | Notas de versão (v3.2.0 em 06/11/2026) |
| Dead Draw | deaddraw.app (fechado) | Site | Não (colar o log) | Sim; galeria pública "Explore" | Página "What's new" |
| PTCGL Replay | ptcglreplay.com (fechado; v0.4.5) | Site; processa no navegador | Não | Sim | "what's new" da página inicial |
| TCGX Replay | tcgx.pl/en/replay (fechado; beta, só Standard) | Site/PWA | Não | Sim | Página de replay e FAQ |
| TrainerLog | trainerlog.app (fechado; testes fechados) | Site em português e inglês | Não (colar o log) | Sim (replay turno a turno; aceita log em português) | Página inicial |
| Training Court | trainingcourt.app · github.com/jlgrimes/training-court (TypeScript) | Site | Não | Sim | Testes em `__tests__/battle-logs/` (casos de replay) |
| I.R.I.S | github.com/Huang-Frederic/I.R.I.S (TypeScript; logs em francês) | PWA própria | Não | Sim | Skill `.claude/skills/ptcg-coach`, modelo de dados |
| TCG Review Playmat (`tcgreplay`) | github.com/nicholasjackson/tcgreplay (Go) · tcgreplay.demo.gs | Playmat guiado por IA (MCP) | Não | Sim, por importação | Skill `skills/card-set-import`, changelog `.spektacular/` |
| Battle Replay Parser | github.com/kagd/pokemon-tcg-battle-replay (TypeScript; parado desde 04/2025) | Parser com IA (Azure OpenAI) | Não | Processa | Só se voltar a ter atividade |
| PokeBuddy | lojas App Store / Google Play (fechado) | Celular | Não comprovada | Por importação | Ficha da loja (fora do nosso escopo: D-002) |
| Pokemon Champions Battle Logger | fufufukakaka.github.io/pokemon_champions_battle_logger (fechado; outro jogo) | Desktop, lê vídeo | Sim (vídeo) | Não é TCG | Notas de versão (ideias de tela; comparação de 09/11/2026) |

Nenhuma oferece download em massa ou API pública de Battle Logs (não confirmada em nenhuma). Partidas públicas de terceiros só
com termos e autorização (D-026/D-027 para os nossos dados).

## 2. O que aprendemos e vale para o Coletor (prioridade)
1. **Códigos das cartas no log (alta).** Todos os apps recomendam desmarcar *Hide card IDs from export* (Battle Log Settings do
   jogo): o log passa a trazer `(sv6_200) Dragapult ex`. **O Coletor ainda não entende isso:** num log assim (exemplo público do
   Training Court) o nome das cartas vira `(sv6_200) Dragapult ex` nas cartas vistas, o que atrapalharia identificação do deck, uso
   de cartas e replay, e 46 linhas ficaram "não lidas". Fazer: tirar o código do nome no leitor e no replay, e usar o código para
   saber a versão exata da carta (hoje adivinhada por `resolver_versoes`). Precisa de medição (D-017) e de `VERSAO_LEITOR`.
2. **Deck novo sem listas de torneio (alta).** O Full Bench dá nome ao deck pelo Pokémon que causou mais dano (+ um segundo se fizer
   ≥ 25% do dano ou usar Habilidade 2+ vezes) e descarta "motores" que aparecem em vários decks. Serve de reserva para o NB2 quando
   o deck ainda não tem listas (caso Talonflame Dusknoir chamado de Tera Box em 09/11/2026).
3. **Coleção nova antes do TCGdex (média).** O `tcgreplay` monta as coleções juntando TCGdex com a exportação de dados do TCG Live
   do malie.io (projeto de fã), com correções registradas com motivo. Seria a segunda fonte da biblioteca quando o TCGdex atrasa
   (Delta Reign, 05/11/2026). Conferir termos antes.
4. **Modo automático (média).** Full Bench: começa a acompanhar sozinho quando o jogo abre e para quando fecha; se a cópia falha,
   tenta de novo e depois pede o clique à pessoa, com o Continue coberto por até 20 s; espera 12 s fora da tela de resultado antes
   de capturar de novo; trata como repetida a partida com o mesmo resultado, turnos e prêmios em 10 minutos. Comparar com
   `auto_export.py`/`cobertura.py`.
5. **Replay (média).** Dead Draw usa o texto do ataque/Habilidade para achar o alvo dos contadores de dano e deixa sem aplicar a
   transferência ambígua (mesma linha da D-046); conta dano em área. Training Court tem casos de teste de transferência de dano,
   Phantom Dive, ligação de Energia e "o que se sabe da mão": bons modelos para `teste_replay.py`.
6. **Replay "melhores momentos" (baixa).** Dead Draw pula direto entre ataques, nocautes e prêmios. Leve de fazer e deixa a revisão
   mais rápida.
7. **Log em português (decisão do Pedro).** TrainerLog aceita logs em português e o PTCGL Tracker 3.0 aceita todos os idiomas do
   jogo. Hoje o Coletor exige o jogo em inglês; amigos que jogam em português perderiam as partidas.
8. **Modelo de dados (conferido).** I.R.I.S guarda o log bruto, hash SHA-256, versão do parser e linhas desconhecidas: o Coletor já
   faz o equivalente (`hash`, `VERSAO_LEITOR`, linhas não lidas, cópia em `dados/logs`). Ideia: marcar cada evento do replay como
   observado ou deduzido.

## 3. Skills que eles têm e nós não
- **Coach de partida** (I.R.I.S, `ptcg-coach`): lê um log e faz o debrief turno a turno, com um perfil do jogador que cresce a cada
  partida (erros que se repetem), regras com fonte num arquivo próprio e três recusas: não julgar com certeza um estado incerto, nunca
  usar texto de carta de memória e não dizer "devia ter jogado X" sem provar que X estava na mão. Cada comentário aponta a linha do
  log. A nossa Skill `statistical-analyst` tem os conceitos de estratégia, mas não esse fluxo de debrief por partida nem o perfil.
- **Importar coleção** (`tcgreplay`, `card-set-import`): passo a passo para montar e conferir uma coleção nova com relatório de
  dúvidas e correções com motivo. Nós fazemos isso à mão (`tracker/colecoes.py` + biblioteca).
- Sem utilidade para nós: as Skills de processo `spek-*` (planejamento) e as instruções de tradução do Training Court.

## 4. Rotina mensal (o que conferir)
1. Repositórios abertos: commits e versões desde a última verificação (`gh api repos/<dono>/<repo>/commits?since=`, releases).
2. Sites fechados: página de novidades ou a página inicial (versão, recursos novos).
3. Para cada novidade: vale para o Coletor? É leve? Respeita o escopo (Standard, computador, servidor local, D-001 a D-004)?
4. Relatório em `ferramentas/pesquisa/verificacao-AAAA-MM.md` (fora do GitHub), com a lista do que pode ser implementado em ordem.
   Atualizar este arquivo (datas, itens da seção 2) só por PR, quando o Pedro pedir.
