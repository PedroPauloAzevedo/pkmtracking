<!-- Preencha em português simples. Regras em PROJECT_KNOWLEDGE/00_CENTRAL/COLLABORATION.md. Só o Pedro junta na main (no computador dele, o "publicar" dele autoriza o Claude a juntar; D-047). -->

## Objetivo
<!-- O que este PR resolve e por quê (1 a 3 frases). -->

## Arquivos e módulos
<!-- Arquivos mudados e área: captura, leitor, replay, banco, análises, torneios, cartas, amigos, atualizador, painel, Skill, docs. -->
- 

## Impactos
- [ ] Muda o que o programa faz (então traz `versao.txt` + topo de `novidades.json` + `DONE.md`)
- [ ] Muda o banco (migração em `banco.iniciar()`, linha no registro de `DATA_MODEL.md`, testado com banco antigo)
- [ ] Muda um contrato (rota `/api`, formato de `dados_json`, `config.json`, `docs/regras-standard.md`) — `API_CONTRACTS.md`/`DATA_MODEL.md` atualizados
- [ ] Muda o leitor (`banco.VERSAO_LEITOR`) ou o índice de cartas (`cartas.VERSAO_INDICE`)
- [ ] Muda algoritmo de análise (medição antes/depois nos mesmos dados, D-017, registrada em `EVIDENCE.md`)
- [ ] Código só de uma plataforma (Windows / Mac)
- [ ] Nenhum dos itens acima (só documentação, teste ou Skill)

## Testes
<!-- Cole o fim da saída de cada teste. Diga em qual sistema rodou (Windows / Mac) e o que NÃO foi testado. -->
- [ ] `python -I testes/teste_tracker.py <cópia> testes/leitor-tcg-live.html` → OK
- [ ] `python testes/teste_seguranca.py <cópia>` → OK
- [ ] `python -I testes/teste_replay.py <cópia>` → OK
- [ ] `python -I testes/teste_telas.py <cópia>` → OK
- Sistema: 
- Não testado: 

## Riscos
<!-- O que pode quebrar, para quem (você, os amigos, Windows/Mac) e como desfazer. -->

## Documentação
- [ ] Documento do módulo em `PROJECT_KNOWLEDGE/01_MODULES/`
- [ ] Decisão nova em `DECISIONS.md` (número livre) / medição em `EVIDENCE.md`
- [ ] `CURRENT_STATE.md`, `NEXT_STEPS.md`, `IN_PROGRESS.md`/`DONE.md`
- [ ] Nada pessoal no PR (caminhos, nicks reais, e-mail, links privados, tokens)
