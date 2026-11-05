# Atualização, instalação e entrega para os amigos

> Atualizado em 05/11/2026. Código: `tracker/atualizador.py`, `tracker/novidades.py` + `novidades.json`, `instalador/montar.py`,
> `instalador/coletor.iss`, `instalar_windows.bat`, `iniciar_windows.bat`, `iniciar_com_o_windows.bat`, `nao_iniciar_com_o_windows.bat`,
> `instalar_mac.command`, `iniciar_mac.command`. Decisões: D-004, D-023, D-024, D-025.

## Atualizador (`atualizador.py`)
1. Lê `versao.txt` da `main` no GitHub (repositório em `repositorio.txt`, ou `github_repo` em Ajustes) e compara com a local.
2. Se for mais nova, o painel mostra "Nova versão disponível" e, em Ajustes → Atualizações, o "Como atualizar" da versão.
3. Ao confirmar: baixa o zip da `main`, substitui os arquivos do programa e **nunca** toca em `dados/`, `.venv/`, `.git/` nem
   nas imagens que já existem em `modelos/`; roda `pip install -r requirements.txt` no Python do programa e reinicia sozinho.
4. Depois de reiniciar, a janela de novidades mostra as versões que a pessoa ainda não viu (`passos`); "Entendi" guarda no config.
- Repositório privado precisaria de token de leitura (`github_token`), mas o repositório é público e não usa token.
- Tudo o que está na `main` vai para os computadores dos amigos, inclusive esta documentação (inofensivo, ~100 KB).
- Risco conhecido: o zip não tem conferência de assinatura/hash (ver `BACKLOG.md`).

## Novidades (`novidades.json`)
Uma entrada por versão, da mais nova para a mais antiga: `versao`, `data`, `titulo`, `mudancas` (o que mudou), `como_atualizar`
(aparece ANTES, em Ajustes → Atualizações) e `passos` (aparece DEPOIS, numa janela no painel). É o histórico do ponto de vista de
quem usa; o técnico fica em `../04_IMPLEMENTATIONS/DONE.md`.

## Instalação pelo código (quem tem Python)
- Windows: `instalar_windows.bat` cria a `.venv`, instala `requirements.txt`, pergunta se quer o modo automático
  (`requirements-auto.txt`) e cria o atalho. `iniciar_windows.bat` abre pelo `pythonw.exe` (ícone na bandeja) quando o pystray
  está disponível. `iniciar_com_o_windows.bat`/`nao_iniciar_com_o_windows.bat` ligam/desligam abrir com o Windows.
- Mac: `instalar_mac.command` e `iniciar_mac.command` (sem os extras do Windows).

## Instalador .exe (quem não tem Python)
- `python instalador/montar.py` (numa cópia em pasta curta) baixa o **Python oficial do NuGet 3.15.2** (sha256 conferido), instala as
  bibliotecas (inclusive as do modo automático), monta `build/ColetorTCG` (fora: dados, testes, instalador, caches) e chama o
  **Inno Setup 6** → `dist/ColetorTCG-Instalador-<versão>.exe` (~58 MB; a pasta montada tem ~235 MB, metade é o OpenCV).
- Instala **por usuário** em `%LOCALAPPDATA%\Programs\ColetorTCG`, sem administrador (para o atualizador conseguir trocar arquivos),
  e cria o atalho na Área de Trabalho. O Python do NuGet não tem tkinter: por isso a cobertura do Continue é Win32 puro.
- Desinstalar fecha **só** o Coletor da própria pasta (o desinstalador é 32 bits: usa CIM para ver o caminho dos processos) e
  mantém `dados/`.
- Sem assinatura digital: o Windows mostra "O Windows protegeu o computador" → *Mais informações* → *Executar assim mesmo*.
- Não há Release no GitHub. O único .exe gerado até hoje é o da **2026.11.02-2**, guardado no computador do Pedro (caminho em
  `CLAUDE.local.md`); quem instala por ele se atualiza sozinho para a versão mais nova.

## Entregar o programa a um amigo
1. Mandar o `ColetorTCG-Instalador-<versão>.exe` (de preferência pelo Google Drive, é grande).
2. O amigo dá dois cliques, passa pelo aviso do Windows (acima) e avança as telas; o Coletor abre sozinho.
3. No primeiro uso, informar o **nick exatamente como no jogo**.
4. Atualizar pelo aviso amarelo ou em Programa → Ajustes e captura → Atualizações → Verificar agora.
5. Modo automático: Ajustes → Modo automático → "Usar imagens prontas" → "Ligar modo automático".
6. Troca de logs: Programa → Amigos (.zip) ou pasta do Google Drive (ver `FRIENDS.md`).
Quem já instalou pelo `instalar_windows.bat` não deve instalar o .exe por cima: basta atualizar pelo programa.
