# Backlog: ideias e pendências

> Atualizado em 05/11/2026. Em ordem de prioridade dentro de cada grupo. Ao começar um item, mova para `IN_PROGRESS.md`;
> ao terminar, registre em `DONE.md`. Sempre pergunte ao Pedro antes de começar algo grande.

## Prioridade alta
1. **Scripts de medição no repositório:** trazer para `testes/experimentos/` as medições do replay (estados impossíveis, nocautes
   curtos), das mãos (tamanho real no Judge/Lillie's/Unfair Stamp), dos prêmios (versão publicada × nova) e a simulação do
   modo automático (`EVIDENCE.md`). Hoje estão só no computador do Pedro. É código de teste (não muda o programa): pedir
   autorização.

## Prioridade média
2. **Instalador como Release no GitHub** (hoje só existe o .exe da 2026.11.02-2, no computador do Pedro). Gerar um .exe novo e publicar
   como Release; o README já não promete Releases (corrigido em 05/11/2026).
3. **Atualizador com tag de versão e conferência do hash do zip** (hoje baixa a `main` sem conferir assinatura: risco se a conta do
   GitHub for comprometida).
4. **Peso maior para torneios recentes no confronto ajustado** (testar com `e3_matchups.py` antes de trocar).
5. **Ligar a partida à lista de Meus decks pelo NB2**; "minha lista × versões do deck"; alerta semanal de meta.
6. **Decisões mais rápida** quando passar de algumas centenas de partidas (~2,7 s com mil hoje, exp. 4).
7. **Base de regras:** quando a tarefa mensal avisar, atualizar `docs/regras-standard.md` (rotina em `../01_MODULES/RULES_BASE.md`);
   confirmar a marca da coleção 30th Celebration; acompanhar a rotação de 2027.

## Prioridade baixa
8. Consistência: simulação de abertura considerando cartas de busca (hoje os números são um piso).
9. Replay: energia ligada a Pokémon de mesmo nome no Banco pode cair no Pokémon errado (o log não diferencia; investigar se o
   contexto permite decidir, como foi feito com os contadores).
10. README (seção 4): o passo 1 do modo automático ainda manda rodar `pip install -r requirements-auto.txt` "no ambiente", sem citar o
    botão "Instalar o modo automático" (que instala no Python certo); revisar também o `COMECE_AQUI.txt`.

## Em estudo, sem decisão
- **Servidor central para análises coletivas** (o grupo enxergar as análises de todos). Estudado numa sessão de 02–03/11/2026 que foi
  **apagada**; o texto completo se perdeu. O que sobrou do relatório: se as análises coletivas ficarem liberadas para todos os
  participantes, "o projeto encolhe bastante" (some a parte de esconder análises por nível de acesso e de dar permissões diferentes a
  cada administrador); continuaria sendo preciso um **servidor central simples, com HTTPS e banco PostgreSQL**, com conta criada pelo
  Pedro. Atenção: isso contraria D-003 (servidor só local) e D-004 (dados só com cada pessoa); qualquer passo exige decisão nova do
  Pedro. Pedir a ele o texto completo, se tiver guardado.
- **Analista estratégico** (treinador que analisa os logs das partidas do Pedro): foi tratado numa conversa separada em 01/11/2026,
  fora deste projeto. Não há nada implementado aqui.
