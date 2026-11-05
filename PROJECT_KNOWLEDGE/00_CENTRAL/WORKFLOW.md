# Como trabalhar no projeto

> Atualizado em 05/11/2026. Testar, medir, versionar, publicar e manter esta documentação.
> Caminhos e detalhes do computador do Pedro ficam em `CLAUDE.local.md` (fora do GitHub).

## 1. Onde mexer e onde testar
- **Código e documentos:** na pasta do projeto (repositório git com o histórico do GitHub; `core.autocrlf=false`).
- **Testes: sempre numa CÓPIA do programa, numa pasta de caminho curto**, com `"porta": 8799` em `dados/config.json` da cópia.
  - Na porta 8765 o programa novo **fecha o Coletor aberto do Pedro** (um Coletor por vez).
  - **Nunca** mexer na instalação que o Pedro usa (nem nos dados dela). Para olhar o banco real, abrir só para leitura
    (`sqlite3.connect("file:<caminho>?mode=ro", uri=True)`) ou copiar o arquivo para a cópia de teste.
  - **Não copiar logs para a área de transferência** enquanto o Coletor do Pedro estiver aberto: ele grava na hora.
  - Rodar os scripts **a partir da pasta da cópia**: `python -c` de dentro da pasta do projeto importa o `tracker` dela e cria `dados/` ali.
  - Caminhos longos impedem o Pillow de carregar: use pastas curtas para a cópia e para o ambiente Python de teste.
- **Diagnóstico na máquina do Pedro:** imagens de tela só da **janela do jogo** e só quando o jogo está na frente; nunca
  fotografar a tela inteira (pode pegar janelas pessoais). Apague as imagens quando o diagnóstico acabar. Ver D-016.

## 2. Testes antes de entregar qualquer mudança
Na cópia de teste (o `teste_tracker` **apaga `dados/` da cópia**):
```
python -I testes/teste_tracker.py <cópia> testes/leitor-tcg-live.html   -> OK   (regressão)
python testes/teste_seguranca.py <cópia>                                -> OK   (proteção de origem)
python -I testes/teste_replay.py <cópia>                                -> OK   (cenários do replay e das mãos)
python -I testes/teste_telas.py <cópia>                                 -> OK   (todas as telas no Edge, porta 8799; depois do teste_tracker;
                                                                                   precisa de pip install -r requirements-dev.txt)
```
- Mudou probabilidade → `testes/experimentos/e1_probabilidades.py`. Mudou análise → o experimento correspondente (ver `../03_DECISIONS/EVIDENCE.md`).
- Mudou o replay → além do `teste_replay.py`, repetir as medições nas partidas reais (estados impossíveis, nocautes curtos,
  tamanho da mão) descritas em `EVIDENCE.md`.
- Mudou tela → olhar no navegador da cópia (largura de computador; janela estreita até 900px também deve funcionar).

## 3. Melhorias com medição (D-017)
Trocar um algoritmo só depois de comparar com o atual **nos mesmos dados** (experimento em `testes/experimentos/`
ou medição descrita em `EVIDENCE.md`). Manter a versão antiga quando útil (ex.: `_uso_cartas_lento`,
`_identificar_nb_direto`, `variantes_por_semelhanca`). Registrar o resultado em `EVIDENCE.md` e a decisão em `DECISIONS.md`.

## 4. Cuidados de código que já causaram erro
- Coluna nova no banco: migração em `banco.iniciar()` e INSERT com o nome das colunas.
- Leitor passou a tirar informação nova dos logs → aumentar `banco.VERSAO_LEITOR` (as partidas são relidas na abertura).
- Índice de cartas ganhou campo → aumentar `cartas.VERSAO_INDICE`.
- Painel: o que roda ao carregar só pode usar o que veio antes na lista de scripts do `index.html` (por isso `ROTAS` fica no
  `inicio.js`, o último). Depois de um `await`, procurar elementos dentro do próprio quadro (`el.querySelector`), não com `$()`.
- Arquivos de texto em **LF** (as ferramentas do Windows às vezes gravam CRLF); os `.bat` e o `COMECE_AQUI.txt` em **CRLF**.
- PowerShell 5.1 manda texto com acento quebrado em `Invoke-RestMethod`: testar rotas com Python.
- Inno Setup: só a chave de abrir é dobrada (`{{`); o desinstalador é 32 bits (usar CIM para achar processos).

## 5. Versão nova (D-024)
1. Aumentar `versao.txt` (`AAAA.MM.DD-N`, sem quebra de linha no fim).
2. Entrada no topo de `novidades.json` com `versao`, `data`, `titulo`, `mudancas`, `como_atualizar` e `passos` (o programa mostra isso).
3. Registrar o lado técnico em `../04_IMPLEMENTATIONS/DONE.md`.
4. Entregar ao Pedro, no chat, o passo a passo resumido para os amigos.
- Mudança só de documentação não muda a versão (os amigos não veem nada de diferente).

## 6. Git e publicação (D-025)
- Cada tarefa num **ramo próprio** (`git switch -c <nome>`), criado antes da primeira edição.
- **Commit e push só quando o Pedro pedir.** Publicar = levar o ramo para a `main` (`git merge --ff-only`) e `git push origin main`.
  Os programas dos amigos olham `versao.txt` da `main`: publicar uma versão dispara o aviso de atualização neles.
- Autor dos commits: `Claude <noreply@anthropic.com>` (`git -c user.name=Claude -c user.email=noreply@anthropic.com commit ...`),
  com a linha `Co-Authored-By` pedida pelo app. Nunca expor o e-mail do Pedro.
- Antes do commit: `git status` e `git diff --cached --name-only` (só os arquivos da tarefa) e conferir que nenhum dado pessoal entrou (seção 7).
- Depois do push: conferir pela API do GitHub que `versao.txt` da `main` mudou e quem é o autor.
- `.git/info/exclude` mantém fora do GitHub: `dados/`, `.venv/`, `__pycache__/`, `ferramentas/`, `CLAUDE.local.md`, `_arquivo_docs_antigos/`.

## 7. Privacidade (o repositório é PÚBLICO; D-026 e D-027)
Nunca no GitHub (nem em documentos, commits ou exemplos): caminhos do computador do Pedro, nomes de pastas pessoais, e-mail,
nicks reais de jogadores (dele e dos amigos), endereço e situação da pasta compartilhada do Drive, links e códigos de recursos
privados (Claude Docs, tarefas agendadas), tokens e senhas. Tudo isso vai em `CLAUDE.local.md`.
Em exemplos de log, usar nomes fictícios (Ana, Bia, Ana_TCG). Dados reais do Pedro nunca em vídeos ou demonstrações.
Antes de publicar, procurar os nicks reais (dos bancos, abertos só para leitura) em **todos** os arquivos que vão para o GitHub,
inclusive código e testes: em 05/11/2026 dois comentários de exemplo no código traziam nicks reais (trocados por Ana/Bia).
Senhas e tokens nunca no chat (o token do GitHub, se houver, fica só em `dados/config.json`).

## 8. Gerar o instalador .exe
`python instalador/montar.py` numa cópia em pasta curta: baixa o Python oficial do NuGet (sha256 conferido), instala as
bibliotecas e chama o Inno Setup 6 → `dist/ColetorTCG-Instalador-<versão>.exe`. Testar: instalar numa pasta à parte com
`/VERYSILENT /TASKS="" /DIR=...`, abrir na porta 8799, desinstalar com o programa aberto e conferir que o Coletor do Pedro
continua aberto. Detalhes em `../01_MODULES/UPDATE_AND_INSTALL.md`.

## 9. Manter esta documentação (regra de toda sessão)
| Aconteceu | Atualizar |
|---|---|
| Qualquer trabalho | `../05_SESSION_CONTROL/CURRENT_STATE.md` e `NEXT_STEPS.md`, no fim da sessão |
| Mudou um módulo | O documento do módulo em `01_MODULES/` (e a explicação no topo do arquivo de código) |
| Regra nova ou alterada (inclusive descoberta sobre o formato do log) | O documento em `02_BUSINESS_RULES/` |
| Decisão técnica (inclusive "pesquisado e descartado") | `../03_DECISIONS/DECISIONS.md` (número novo, nunca reaproveitar) |
| Medição feita | `../03_DECISIONS/EVIDENCE.md` |
| Ideia ou pendência nova / começou / terminou | `BACKLOG.md` → `IN_PROGRESS.md` → `DONE.md` |
| Versão publicada | `DONE.md` (técnico), `novidades.json` (quem usa), `CURRENT_STATE.md` |
Cada documento começa com "Atualizado em dd/mm/aaaa": troque a data ao editar. Não repita informação de um documento em
outro: aponte para ele. Não use conversas antigas nem a memória automática do Claude como fonte; se algo importante só
existir numa conversa, traga para cá.
