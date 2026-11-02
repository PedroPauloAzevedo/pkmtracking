/* ---- DECISÕES: o que anda junto com vencer nas suas partidas (só a partir dos logs) */
async function renderDecisoes() {
  const f = S.filtroDec || (S.filtroDec = { de: '', ate: '', deck: '', lista: '', adv: '', periodo: 0, min: 3, ordem: '' });
  if (f.periodo) { const d0 = new Date(Date.now() - (f.periodo - 1) * 864e5); f.de = d0.toISOString().slice(0, 10); f.ate = ''; }
  const qs = new URLSearchParams(Object.entries({ de: f.de, ate: f.ate, deck: f.deck, lista: f.lista, adv: f.adv, min: f.min, ordem: f.ordem || '' }).filter(([, v]) => v !== '' && v != null)).toString();
  await carregarJogadores();
  const [r, todos, listas] = await Promise.all([api(comJog('/api/decisoes?' + qs)), api(comJog('/api/partidas')), api('/api/decks')]);
  const decks = [...new Set(todos.partidas.map(l => l.meu_deck).filter(Boolean))].sort();
  const advs = [...new Set(todos.partidas.map(l => l.deck_adv).filter(Boolean))].sort();
  const dif = x => x == null ? '<span class="muted">–</span>' : `<b style="color:${x > 0 ? 'var(--good)' : x < 0 ? 'var(--bad)' : 'var(--muted)'}">${x > 0 ? '+' : ''}${fmt(x, 0)} p.p.</b>`;
  const tabelaCartas = (lista, vazio) => {
    const l = lista.filter(c => c.n >= f.min && c.sem_n > 0);
    if (!l.length) return `<p class="muted">${vazio}</p>`;
    return `<div class="tabela"><table><thead><tr><th>Carta</th><th class="n">Partidas</th><th class="n">V–D</th><th>Vitória quando jogou</th><th>Quando não jogou</th><th>Diferença</th></tr></thead><tbody>
      ${l.map(c => `<tr><td><span class="cel-carta">${mini(c.carta)}${esc(c.carta)}</span></td><td class="n">${c.n}</td><td class="n">${c.v}–${c.d}</td><td>${taxaHtml(c)}</td>
        <td>${pct(c.taxa_sem)} <span class="ic">${c.sem_n} partidas</span></td><td>${dif(c.diferenca)}</td></tr>`).join('')}</tbody></table></div>`;
  };
  // versão compacta para as duas colunas (começando × indo em segundo)
  const tabelaCompacta = (lista, vazio) => {
    const l = lista.filter(c => c.n >= f.min && c.sem_n > 0);
    if (!l.length) return `<p class="muted" style="font-size:.85rem">${vazio}</p>`;
    return `<div class="tabela"><table><thead><tr><th>Carta</th><th class="n">Partidas</th><th>Vitória quando jogou</th><th>Diferença</th></tr></thead><tbody>
      ${l.map(c => `<tr><td><span class="cel-carta">${mini(c.carta)}${esc(c.carta)}</span></td><td class="n">${c.n}</td><td>${taxaHtml(c)}</td><td title="sem ela: ${pct(c.taxa_sem)} em ${c.sem_n} partidas">${dif(c.diferenca)}</td></tr>`).join('')}</tbody></table></div>`;
  };
  const po = r.por_ordem || {};
  const ROT_ORDEM = { primeiro: 'Começando', segundo: 'Indo em segundo' };
  const colunaOrdem = k => { const o = po[k] || { partidas: 0, aberturas: [], ritmo: {} };
    return `<div class="panel" style="padding:12px;gap:8px;background:var(--sunken)">
      <div class="ordem-cab"><h3>${ROT_ORDEM[k]}</h3><span class="muted" style="font-size:.85rem">${o.partidas} partida${o.partidas === 1 ? '' : 's'}${o.partidas ? ` · vitória ${pct(o.taxa)}` : ''}</span></div>
      ${o.partidas ? `<p class="muted" style="font-size:.8rem">Seu turno do 1º prêmio, vitórias × derrotas: <b>${fmt(o.ritmo.V?.premio)} × ${fmt(o.ritmo.D?.premio)}</b> · 1º ataque: ${fmt(o.ritmo.V?.ataque)} × ${fmt(o.ritmo.D?.ataque)}</p>` : ''}
      ${tabelaCompacta(o.aberturas, `Nenhuma carta de abertura com pelo menos ${f.min} partidas ${ROT_ORDEM[k].toLowerCase()} (e alguma partida sem ela).`)}</div>`; };
  const vi = r.viradas, rv = r.ritmo, pc = r.perdeu_controle;
  const maxPc = Math.max(1, ...pc.map(x => x.derrotas));
  main.innerHTML = `
    ${trilha()}<header><h1>Decisões</h1><p class="sub">${S.jogador ? `Mostrando: <b>${esc(nomeJogadorSel())}</b> (cada partida do ponto de vista de quem jogou). ` : ''}O que, nas suas partidas, anda junto com vencer ou perder: jogadas de abertura, corrida de prêmios, o turno em que o jogo escapou e o seu ritmo. Tudo vem dos logs.</p></header>
    <div class="aviso">São <b>correlações</b>, não causas: uma carta pode aparecer mais nas vitórias porque você só consegue jogá-la quando a partida já está boa. Use como pista para revisar replays. Com poucas partidas, a faixa provável (passe o mouse na taxa) é larga.</div>
    <div class="row">
      <div class="chips-periodo">${PERIODOS.map(([v, rt]) => `<button data-periodo="${v}" aria-pressed="${f.periodo === v && !(v === 0 && (f.de || f.ate))}">${rt}</button>`).join('')}</div>
      <div class="chips-periodo" role="group" aria-label="Quem começou">${[['', 'Todas'], ['primeiro', 'Começando'], ['segundo', 'Indo em segundo']].map(([v, rt]) => `<button data-ordem="${v}" aria-pressed="${(f.ordem || '') === v}">${rt}</button>`).join('')}</div>
      <label class="label" for="x-de">De</label><input type="date" id="x-de" value="${f.de}">
      <label class="label" for="x-ate">Até</label><input type="date" id="x-ate" value="${f.ate}">
      <span class="grow"></span>
      ${seletorJogador()}
      <select id="x-deck"><option value="">Todos os seus decks</option>${decks.map(x => `<option value="${esc(x)}" ${f.deck === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select>
      <select id="x-lista"><option value="">Todas as listas</option>${listas.map(x => `<option value="${x.id}" ${String(f.lista) === String(x.id) ? 'selected' : ''}>${esc(x.nome)}</option>`).join('')}</select>
      <select id="x-adv"><option value="">Todos os adversários</option>${advs.map(x => `<option value="${esc(x)}" ${f.adv === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select>
      <label class="label" for="x-min">Mín. partidas</label><input type="number" id="x-min" min="1" max="50" value="${f.min}" style="width:64px">
    </div>
    ${!r.partidas ? '<p class="muted">Nenhuma partida com resultado nesse filtro.</p>' : `
    <div class="kpis">
      <div class="kpi"><span class="label">Partidas analisadas</span><span class="v">${r.partidas}</span><span class="d">${r.vitorias} vitórias</span></div>
      <div class="kpi"><span class="label">Viradas</span><span class="v">${pct(vi.taxa_virada)}</span><span class="d">venceu ${vi.perdendo_e_venceu} de ${vi.perdendo} em que ficou atrás nos prêmios</span></div>
      <div class="kpi"><span class="label">Vantagem entregue</span><span class="v">${pct(vi.taxa_entregou)}</span><span class="d">perdeu ${vi.ganhando_e_perdeu} de ${vi.ganhando} em que esteve à frente</span></div>
      <div class="kpi"><span class="label">Ritmo (vitórias × derrotas)</span><span class="v">${fmt(rv.V?.premio)} × ${fmt(rv.D?.premio)}</span><span class="d">seu turno médio do 1º prêmio · 1º ataque: ${fmt(rv.V?.ataque)} × ${fmt(rv.D?.ataque)}</span></div>
    </div>
    <div class="grid2">
      <section class="panel"><h2>Peso do primeiro prêmio</h2>${tabelaGrupos(r.primeiro_premio, 'Quem pegou primeiro')}</section>
      <section class="panel"><h2>Turno em que você perdeu o controle</h2>
        <p class="muted" style="font-size:.85rem">Nas derrotas: o seu turno a partir do qual o adversário ficou à frente nos prêmios e não foi mais alcançado.</p>
        ${pc.length ? pc.map(x => `<div class="row" style="gap:8px;margin:4px 0"><span style="width:70px">${x.turno}º turno</span><div style="flex:1;background:rgba(127,127,127,.15);border-radius:4px;height:14px"><div style="width:${100 * x.derrotas / maxPc}%;background:var(--bad);height:100%;border-radius:4px"></div></div><span class="n" style="width:80px;text-align:right">${x.derrotas} derrota${x.derrotas === 1 ? '' : 's'}</span></div>`).join('') : '<p class="muted">Sem derrotas com placar de prêmios nesse filtro.</p>'}
      </section>
    </div>
    <section class="panel"><h2>${f.ordem ? `Aberturas ${ROT_ORDEM[f.ordem].toLowerCase()}` : 'Aberturas por quem começou'} <span class="muted" style="font-weight:400;font-size:.85rem">(seus 2 primeiros turnos)</span></h2>
      <p class="muted" style="font-size:.85rem">Cartas que você jogou, ligou ou evoluiu nos seus dois primeiros turnos. Regra do Standard: quem começa não ataca nem joga Apoiador no 1º turno, e ninguém evolui no próprio 1º turno. Por isso a abertura de quem começa é outro jogo, e cada lado só compara partidas com a mesma ordem. Diferença = taxa quando jogou − taxa quando não jogou.</p>
      ${f.ordem ? tabelaCartas(r.aberturas, `Nenhuma carta de abertura com pelo menos ${f.min} partidas (e alguma partida sem ela).`)
        : `<div class="grid2">${colunaOrdem('primeiro')}${colunaOrdem('segundo')}</div>`}
      ${r.sem_ordem && !f.ordem ? `<p class="muted" style="font-size:.8rem">${r.sem_ordem} partida(s) sem a informação de quem começou ficaram fora da separação.</p>` : ''}</section>
    <section class="panel"><h2>Cartas jogadas em qualquer momento</h2>
      ${tabelaCartas(r.cartas_jogadas, `Nenhuma carta com pelo menos ${f.min} partidas (e alguma partida sem ela).`)}</section>`}`;
  const re = () => renderDecisoes();
  ligarSeletorJogador(re);
  $('#x-deck').onchange = e => { f.deck = e.target.value; re(); };
  $('#x-lista').onchange = e => { f.lista = e.target.value; re(); };
  $('#x-adv').onchange = e => { f.adv = e.target.value; re(); };
  $('#x-min').onchange = e => { f.min = Math.max(1, Number(e.target.value) || 1); re(); };
  $('#x-de').onchange = e => { f.de = e.target.value; f.periodo = 0; re(); };
  $('#x-ate').onchange = e => { f.ate = e.target.value; f.periodo = 0; re(); };
  document.querySelectorAll('[data-periodo]').forEach(b => b.onclick = () => { f.periodo = Number(b.dataset.periodo); if (!f.periodo) { f.de = ''; f.ate = ''; } re(); });
  document.querySelectorAll('[data-ordem]').forEach(b => b.onclick = () => { f.ordem = b.dataset.ordem; re(); });
}
