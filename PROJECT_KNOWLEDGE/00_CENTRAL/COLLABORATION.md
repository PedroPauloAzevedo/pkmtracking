# Trabalho a dois (colaboração)

> Atualizado em 06/11/2026. Regras para mais de um desenvolvedor no mesmo repositório, cada um com o próprio Claude Code e a
> própria instalação. Complementa o [`WORKFLOW.md`](WORKFLOW.md) (como testar, medir, versionar) sem repetir o que está lá.
> Decisões: D-043 (fluxo por PR) e D-044 (Mac). Ver [`../03_DECISIONS/DECISIONS.md`](../03_DECISIONS/DECISIONS.md).

## 1. Quem é quem
- **Pedro** (dono do repositório): único que junta Pull Requests na `main` e publica versão para os amigos.
- **Segundo desenvolvedor:** trabalha no Mac; a prioridade dele é fazer o programa funcionar por inteiro no Mac (D-044).
  Lista do que falta em [`../04_IMPLEMENTATIONS/BACKLOG.md`](../04_IMPLEMENTATIONS/BACKLOG.md), seção "Paridade no Mac".
- Cada um tem: a própria conta do GitHub, os próprios dados (`dados/`, nunca no Git, D-004), o próprio `CLAUDE.local.md`
  (modelo em [`CLAUDE.local.example.md`](../../CLAUDE.local.example.md)), as próprias cópias de teste e credenciais.

## 2. Primeiro dia (para quem chega)
1. Clonar o repositório e conferir que `git config core.autocrlf` **não** é `true` (o `.gitattributes` protege, mas é melhor `false`
   ou `input`).
2. Copiar `CLAUDE.local.example.md` para `CLAUDE.local.md` e preencher com os dados da sua máquina (o `.gitignore` já o mantém fora
   do GitHub).
3. Criar o ambiente: Windows `instalar_windows.bat`; Mac `bash instalar_mac.command`. Para os testes de tela, também
   `pip install -r requirements-dev.txt`; o teste de telas usa o Edge ou o Chrome já instalados (no Mac, instale o Google Chrome).
4. Ler `CLAUDE.md`, depois `05_SESSION_CONTROL/CURRENT_STATE.md`, `NEXT_STEPS.md` e este arquivo.
5. Fazer uma cópia de teste numa pasta curta, com `"porta": 8799` em `dados/config.json` (a 8765 é a do seu Coletor de uso), e rodar
   os 4 testes de entrega ([`WORKFLOW.md`](WORKFLOW.md), seção 2). Tudo `OK` = ambiente pronto.

## 3. Ramos e Pull Requests
- **`main` = o que os amigos recebem.** O atualizador baixa a `main` quando `versao.txt` muda. Nada vai direto para a `main`:
  tudo entra por Pull Request, e **só o Pedro junta** (D-043).
- **No computador do Pedro (D-047):** quando o Pedro pede "publicar", o Claude dele faz o commit, envia o ramo, abre o PR com o
  modelo e **junta ele mesmo** (`gh pr merge <nº> --merge`), sem esperar o clique — os testes de entrega rodam antes, como sempre.
  O PR fica registrado no GitHub do mesmo jeito. **PR do segundo desenvolvedor não muda:** espera o Pedro revisar e juntar.
- Um ramo por tarefa, criado a partir da `main` atualizada:
  | Prefixo | Para quê | Exemplo |
  |---|---|---|
  | `feature/` | Funcionalidade nova | `feature/mac-janela-propria` |
  | `fix/` | Correção de erro | `fix/replay-energia-banco` |
  | `refactor/` | Reorganizar sem mudar comportamento (precisa provar que nada mudou) | `refactor/rotas-por-area` |
  | `docs/` | Só documentação | `docs/contratos-api` |
  | `chore/` | Arrumação do repositório (Git, testes, scripts) | `chore/medicoes-no-repo` |
- Antes de abrir o PR: trazer a `main` nova para o ramo, rodar os testes da tabela da seção 5 e preencher o modelo de PR
  (`.github/pull_request_template.md`).
- PR pequeno e de um assunto só. Mudança no programa e mudança na Skill vão em PRs separados.
- Commit e push: só quando a pessoa daquele computador pedir; push só para o próprio ramo, nunca para a `main`.
  Autor dos commits feitos pelo Claude: `Claude <noreply@anthropic.com>` (D-025).

## 4. Arquivos que todo mundo edita (como evitar conflito)
| Arquivo | Regra |
|---|---|
| `versao.txt`, topo de `novidades.json`, `DONE.md` | Todo PR que muda o que o programa faz traz os três (D-024), para nada ir "de carona" na versão de outra pessoa. Se dois PRs pegaram o mesmo número, quem entra depois passa para o `-N` seguinte ao trazer a `main` nova. PR só de documentação, teste ou Skill não muda a versão. |
| `03_DECISIONS/DECISIONS.md` | Use o próximo número livre. Se outro PR entrou antes com o mesmo número, renumere no seu ramo. Nunca reaproveitar número. |
| `05_SESSION_CONTROL/CURRENT_STATE.md` | Descreve **a `main`**. Só muda no PR que vai entrar, e só no que esse PR muda. |
| `05_SESSION_CONTROL/NEXT_STEPS.md` | Só acrescentar ou riscar o próprio item; não reescrever o dos outros. |
| `04_IMPLEMENTATIONS/IN_PROGRESS.md` | Cada item em curso com **ramo e responsável** (`— ramo feature/x, Pedro`). |
| `app.py` (rotas) | Rota nova no fim do grupo da mesma área; linha nova em [`API_CONTRACTS.md`](API_CONTRACTS.md) no mesmo PR. |
| `tracker/banco.py` | Ver seção 6. |

## 5. Testes conforme o risco
| O que mudou | Testes obrigatórios | Quem revisa |
|---|---|---|
| Só documentação | Nenhum (conferir `git diff --stat`: nenhum documento apagado sem querer) | Pedro |
| Uma tela do painel (`web/`) | `teste_telas` + olhar a tela na cópia | Pedro |
| Uma análise (`analises`, `estrategia`, `regressao`, `variantes`, `probabilidades`, `decks`) | Os 4 testes + o experimento dela (D-017) | Pedro |
| Código só de uma plataforma (dentro de `if sys.platform == ...`) | Os 4 testes **nas duas plataformas** quando possível; anotar no PR em qual não foi testado | Pedro |
| Leitor, replay, banco, atualizador, proteção de origem, `config.CONFIG_PADRAO`, instalador | Os 4 testes + medição antes/depois nos mesmos dados + teste com um banco antigo | Pedro, com atenção |

Os 4 testes e como rodá-los: [`WORKFLOW.md`](WORKFLOW.md), seção 2. No Mac, os comandos são iguais (`python3` se `python` não existir).

## 6. Mudança no banco e mudança de contrato
- **Banco:** só **acrescentar** coluna ou tabela (nunca apagar nem renomear: as pessoas têm bancos antigos que o programa abre).
  Migração em `banco.iniciar()` conferindo se a coluna existe, `INSERT` com nome das colunas, linha nova no registro de migrações do
  [`DATA_MODEL.md`](DATA_MODEL.md) e teste abrindo um banco de uma versão anterior. `banco.VERSAO_LEITOR` e `cartas.VERSAO_INDICE`:
  se dois PRs aumentaram para o mesmo número, quem entra depois aumenta mais um.
- **Contrato** = o que um pedaço do programa promete a outro: rotas `/api` (o painel depende delas), o formato de `dados_json` (saída
  do leitor, lida por banco, análises, replay e painel), `dados/config.json`, o formato de `docs/regras-standard.md`.
  Mudou um contrato → atualizar [`API_CONTRACTS.md`](API_CONTRACTS.md) ou [`DATA_MODEL.md`](DATA_MODEL.md) no mesmo PR e dizer no PR
  quem usa o que mudou. Preferir acrescentar campo a mudar o significado de um campo existente.

## 7. Partes que pedem um de cada vez
Podem andar em paralelo com pouco risco: cada tela de `web/js/`, cada análise, `limitless.py`, `replay.py`, a Skill, documentos de
módulo e o código só do Mac. Pedem **um de cada vez** (combinar antes no `IN_PROGRESS.md`): `tracker/banco.py`, `tracker/leitor.py`
+ `regras_padrao.json`, `tracker/atualizador.py`, a proteção de origem em `app.py`, `tracker/config.py`, `docs/regras-standard.md`,
`instalador/`.

## 8. Segurança entre os dois
- Credenciais são de cada um e ficam fora do Git: token do GitHub (se houver) só em `dados/config.json`; senha nunca em arquivo,
  commit, PR ou chat.
- O repositório é **público** (D-026): nada de caminhos pessoais, nicks reais, e-mail, links privados (D-027). Isso vai no
  `CLAUDE.local.md` de cada um. Antes do PR, procurar nicks reais nos arquivos alterados ([`WORKFLOW.md`](WORKFLOW.md), seção 7).
- Logs e bancos de outra pessoa só com autorização dela, e nunca no Git.
- Como a `main` roda nos computadores dos amigos sem conferência de assinatura (BACKLOG, item 3), a proteção da `main` no GitHub
  é o que impede código não revisado de chegar a eles.

## 9. Configurações do GitHub (só o Pedro faz; recomendadas em 06/11/2026)
- **Regra para a `main`** (Settings → Rules → Rulesets, ou Branches → Branch protection): exigir Pull Request com 1 aprovação e
  revisão do dono do código (`.github/CODEOWNERS`); bloquear force push e apagar a `main`; se a opção "Restrict updates" existir,
  ligar e deixar só o Pedro (administrador) na lista de exceção — é o que garante que só ele junta.
- Convidar o segundo desenvolvedor como colaborador com permissão **Write** (nunca Admin).
- Os dois com verificação em duas etapas (2FA) ligada na conta do GitHub.
- Settings → General: ligar "Automatically delete head branches".
- Conta do Pedro: Settings → Emails → "Keep my email addresses private" e "Block command line pushes that expose my email".
