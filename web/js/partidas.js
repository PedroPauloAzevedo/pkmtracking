/* =====================================================================
   SUAS PARTIDAS
   ===================================================================== */
// ---- jogador: você e/ou amigos de quem você importou logs, em qualquer combinação.
// S.jogadorSel = ids marcados ('' = você). Vale para Início, Partidas, Desempenho e Decisões; fica guardado no navegador.
S.jogadores = [];
function lerSelecaoJogador() {
  try {
    const salvo = JSON.parse(localStorage.getItem('jogadores') || 'null');
    if (Array.isArray(salvo) && salvo.length) return salvo.map(String);
    const antigo = localStorage.getItem('jogador');  // versões até 2026.11.05-2: um só ('' = você, '*' = todos)
    if (antigo) return [antigo];
  } catch (e) {}
  return [''];
}
S.jogadorSel = lerSelecaoJogador();
function salvarSelecaoJogador() {
  try { localStorage.setItem('jogadores', JSON.stringify(S.jogadorSel)); localStorage.removeItem('jogador'); } catch (e) {}
}
async function carregarJogadores() {
  try { S.jogadores = await api('/api/jogadores-locais'); } catch (e) { S.jogadores = []; }
  const ids = S.jogadores.map(j => j.id);
  if (S.jogadorSel.includes('*')) S.jogadorSel = ids;  // "Todos os jogadores" da versão antiga
  S.jogadorSel = S.jogadorSel.filter(id => ids.includes(id));
  if (!S.jogadorSel.length) S.jogadorSel = [''];
}
const soEu = () => S.jogadorSel.length === 1 && S.jogadorSel[0] === '';
const qJog = () => soEu() ? '' : S.jogadorSel.map(id => 'jogadores=' + encodeURIComponent(id)).join('&');
const comJog = url => { const q = qJog(); return q ? url + (url.includes('?') ? '&' : '?') + q : url; };
const variosJogadores = () => S.jogadores.length > 1;
const todosMarcados = () => variosJogadores() && S.jogadores.every(j => S.jogadorSel.includes(j.id));
const rotuloJogador = j => j.voce ? 'Eu' + (j.nome && j.nome !== 'Você' ? ` (${j.nome})` : '') : j.nome;
const juntarNomes = l => l.length > 1 ? l.slice(0, -1).join(', ') + ' e ' + l[l.length - 1] : (l[0] || '');
const nomeJogadorSel = () => todosMarcados() ? 'todos os jogadores'
  : juntarNomes(S.jogadores.filter(j => S.jogadorSel.includes(j.id)).map(j => j.voce ? 'você' : j.nome)) || 'você';
function resumoJogadores() {
  if (todosMarcados()) return 'Todos os jogadores';
  const marcados = S.jogadores.filter(j => S.jogadorSel.includes(j.id));
  if (marcados.length > 2) return `${marcados.length} jogadores`;
  return marcados.map(j => j.voce ? 'Eu' : j.nome).join(' + ') || 'Eu';
}
// Caixa de opções: cada jogador com uma marca; qualquer combinação. Muda na hora e a caixa continua aberta.
function seletorJogador() {
  if (!variosJogadores()) return '';
  // sem total no resumo: a soma contaria duas vezes o jogo que chegou pelos dois lados (a tela mostra o número certo)
  return `<details class="multi" id="sel-jogador" ${S.jogadorAberto ? 'open' : ''}>
    <summary title="Escolha de quais jogadores ver as partidas"><span class="label">Jogador</span><b>${esc(resumoJogadores())}</b><span class="seta" aria-hidden="true">▾</span></summary>
    <div class="multi-opcoes" role="group" aria-label="Jogadores">
      ${S.jogadores.map(j => `<label><input type="checkbox" value="${esc(j.id)}" ${S.jogadorSel.includes(j.id) ? 'checked' : ''}><span class="multi-nome">${esc(rotuloJogador(j))}</span><span class="muted num">${j.partidas}</span></label>`).join('')}
      <div class="multi-acoes"><button type="button" data-jog="todos">Marcar todos</button><button type="button" data-jog="eu">Só eu</button></div>
    </div></details>`;
}
function ligarSeletorJogador(aoMudar) {
  const el = $('#sel-jogador'); if (!el) return;
  el.ontoggle = () => { S.jogadorAberto = el.open; };
  const aplicar = (sel, foco) => {
    S.jogadorSel = sel; S.jogadorAberto = true; salvarSelecaoJogador();
    Promise.resolve(aoMudar()).then(() => {  // a tela foi desenhada de novo: devolve o foco à mesma marca
      const cb = foco != null && [...document.querySelectorAll('#sel-jogador input[type=checkbox]')].find(x => x.value === foco);
      if (cb) cb.focus();
    });
  };
  el.querySelectorAll('input[type=checkbox]').forEach(cb => cb.onchange = () => {
    const sel = [...el.querySelectorAll('input[type=checkbox]:checked')].map(x => x.value);
    if (!sel.length) { cb.checked = true; toast('Marque pelo menos um jogador'); return; }
    aplicar(sel, cb.value);
  });
  el.querySelector('[data-jog="todos"]').onclick = () => aplicar(S.jogadores.map(j => j.id));
  el.querySelector('[data-jog="eu"]').onclick = () => aplicar(['']);
}
// Clicar fora da caixa (ou Esc) fecha.
document.addEventListener('click', e => {
  const el = document.getElementById('sel-jogador');
  if (el && el.open && !el.contains(e.target)) { el.open = false; S.jogadorAberto = false; }
});
document.addEventListener('keydown', e => {
  const el = document.getElementById('sel-jogador');
  if (e.key === 'Escape' && el && el.open) { el.open = false; S.jogadorAberto = false; }
});
function trilha() {
  const r = aba(), sec = SECAO[r] || 'programa', abas = ABAS[sec];
  if (abas && abas.some(([k]) => k === r))
    return `<div class="abas" role="tablist">${abas.map(([k, n]) => `<a href="#${k}" role="tab" aria-selected="${k === r}">${esc(n)}</a>`).join('')}</div>`;
  return NOME_SECAO[sec] ? `<span class="trilha">${NOME_SECAO[sec]}</span>` : '';
}
async function renderPainel() {
  const vez = novaTela();
  await carregarJogadores();
  const [d, st] = await Promise.all([api(comJog('/api/partidas')), api('/api/status'), carregarEpocas()]); const cfg = st.config || {};
  const pend = S.status?.linhas_pendentes || 0;
  const boasVindas = cfg.nick || d.eu ? '' : `<section class="panel" style="border-left:3px solid var(--accent)"><h2>Bem-vindo! Primeiro passo</h2>
    <p>Digite seu nick do TCG Live <b>exatamente como aparece no jogo</b> (maiúsculas e minúsculas contam). É assim que o programa sabe quais partidas são vitórias suas. Se preferir, deixe em branco: ele descobre sozinho na primeira partida capturada.</p>
    <div class="row"><input id="bv-nick" placeholder="Seu nick no TCG Live" style="width:260px"><button class="primary" id="bv-salvar">Salvar</button></div>
    <p class="muted" style="font-size:.85rem">Depois: deixe o programa aberto, jogue com o jogo em <b>inglês</b> e, no fim de cada partida, clique em Battle Log e no botão de exportar. A partida aparece aqui sozinha.</p></section>`;
  const t = d.total, ordem = Object.fromEntries(d.ordem.map(g => [g.grupo, g]));
  const ult = d.partidas.slice(0, 8), c = st.coletor;
  const captura = `<section class="panel captura"><span class="luz ${c.ativo ? 'on' : 'off'}"></span>
    <div class="txt"><b>${c.ativo ? 'Pronto para capturar' : 'Captura desligada'}</b>
      <span class="muted">${c.ativo ? 'No fim da partida, clique em Battle Log e no botão de exportar: a partida entra aqui sozinha.'
        + (c.ultima ? ` Última captura às ${esc(c.ultima.quando)}.` : '') : 'As partidas exportadas no TCG Live não estão sendo guardadas.'}
      ${st.bandeja ? ' O Coletor continua rodando no ícone perto do relógio, mesmo com esta aba fechada.' : ''}</span></div>
    ${c.ativo ? '' : '<button class="primary" id="in-ligar">Ligar captura</button>'}</section>`;
  if (telaVelha(vez)) return;
  main.innerHTML = `
    ${trilha()}<header><h1>Início</h1><p class="sub">${!soEu() ? `Estatísticas de <b>${esc(nomeJogadorSel())}</b>.` : d.eu ? `Estatísticas de <b>${esc(d.eu)}</b>.` : 'Informe seu nick em Ajustes para separar suas vitórias e derrotas.'} Com o programa aberto, toda partida que você exportar no TCG Live entra aqui sozinha.</p></header>
    ${variosJogadores() ? `<div class="row">${seletorJogador()}</div>` : ''}
    ${boasVindas}
    ${captura}
    <div id="in-atalho"></div>
    ${pend ? `<div class="aviso">${pend} partida(s) com linhas que o leitor não reconheceu. <a href="#revisao">Revisar agora</a></div>` : ''}
    <div class="kpis">
      <div class="kpi"><span class="label">Partidas</span><span class="v">${t.n}</span><span class="d">${d.sem_resultado ? `${d.sem_resultado} sem resultado identificado` : 'com resultado'}</span></div>
      <div class="kpi"><span class="label">Taxa de vitória</span><span class="v">${pct(t.taxa)}</span><span class="d">${t.ic_baixo != null ? `provável entre ${fmt(t.ic_baixo, 0)}% e ${fmt(t.ic_alto, 0)}%` : '–'}</span></div>
      <div class="kpi"><span class="label">Começando</span><span class="v">${pct(ordem['Começando']?.taxa)}</span><span class="d">${ordem['Começando']?.n ?? 0} partidas</span></div>
      <div class="kpi"><span class="label">Indo em segundo</span><span class="v">${pct(ordem['Indo em segundo']?.taxa)}</span><span class="d">${ordem['Indo em segundo']?.n ?? 0} partidas</span></div>
    </div>
    <section class="panel">
      <div class="row"><h2 class="grow">Últimas partidas</h2><a class="btn" href="#partidas">Ver todas</a></div>
      ${ult.length ? tabelaPartidas(ult) : '<p class="vazio">Nenhuma partida ainda. Jogue uma partida e exporte o Battle Log, ou cole um log abaixo.</p>'}
    </section>
    <details class="panel manual">
      <summary>Colar um log à mão</summary>
      <p class="sub">Para logs antigos ou copiados no celular. Logs repetidos são ignorados.</p>
      <textarea id="manual" rows="5" placeholder="Cole aqui o log (Setup, Turn # 1 - ...)"></textarea>
      <div class="row"><button class="primary" id="btn-manual">Registrar partida</button></div>
    </details>`;
  ligarLinhasPartidas();
  ligarSeletorJogador(renderPainel);
  if ($('#in-ligar')) $('#in-ligar').onclick = async () => {
    await api('/api/config', { method: 'POST', body: JSON.stringify({ coletor_ativo: true }) }); toast('Captura ligada');
    setTimeout(() => { atualizarStatus(); render(); }, 600); };
  sugerirAtalho(st);
  if ($('#bv-salvar')) $('#bv-salvar').onclick = async () => { const n = $('#bv-nick').value.trim(); if (!n) return;
    await api('/api/config', { method: 'POST', body: JSON.stringify({ nick: n }) }); toast('Nick salvo'); render(); };
  $('#btn-manual').onclick = async () => {
    try { const r = await api('/api/partidas', { method: 'POST', body: JSON.stringify({ texto: $('#manual').value }) });
      if (r.nova && r.dono) toast(`Partida #${r.id} registrada como de ${r.dono}: seu nick não joga nela. Ela fica em Amigos, fora das suas estatísticas.`, 'partida-' + r.id, 'Ver');
      else if (r.nova && r.problemas?.length) toast(`Partida #${r.id} registrada, mas o log parece incompleto: ${r.problemas.join('; ')}. Confira se copiou o log inteiro.`, 'partida-' + r.id, 'Ver');
      else if (r.nova && r.nao_lidas) toast(`Partida #${r.id} registrada com ${r.nao_lidas} linha(s) não lida(s).`, 'revisao', 'Revisar');
      else toast(r.nova ? `Partida #${r.id} registrada` : 'Esse log já estava registrado');
      render(); }
    catch (e) { toast(e.message); }
  };
}

// Sugere (uma vez) o atalho na Área de Trabalho, para abrir o programa com dois cliques.
async function sugerirAtalho(st) {
  let dispensado = false;
  try { dispensado = localStorage.getItem('atalho-dispensado') === '1'; } catch (e) {}
  if (!st.windows || dispensado) return;
  if (!S.atalhos) { try { S.atalhos = await api('/api/atalhos'); } catch (e) { return; } }
  const el = $('#in-atalho');
  if (!el || S.atalhos.area) return;
  el.innerHTML = `<div class="aviso row" style="gap:10px"><span class="grow">Abra o Coletor com dois cliques: crie o atalho <b>Coletor TCG Live</b> na Área de Trabalho.</span>
    <button class="primary" id="in-criar-atalho">Criar atalho</button><button id="in-dispensar">Agora não</button></div>`;
  $('#in-criar-atalho').onclick = async () => {
    try { S.atalhos = await api('/api/atalhos', { method: 'POST', body: JSON.stringify({ area: true }) }); el.innerHTML = ''; toast('Atalho criado na Área de Trabalho'); }
    catch (e) { toast(e.message); }
  };
  $('#in-dispensar').onclick = () => { try { localStorage.setItem('atalho-dispensado', '1'); } catch (e) {} el.innerHTML = ''; };
}

// Separador de época: quando a lista atravessa a chegada de uma coleção ao TCG Live, uma linha marca onde começa cada época.
function separadorEpoca(e, colunas) {
  return `<tr class="sep-epoca"><td colspan="${colunas}">${e ? `Época <b>${esc(e.nome)}</b> · ${e.fim ? `${quandoEpoca(e.de)} a ${quandoEpoca(e.fim)}` : `desde ${quandoEpoca(e.de)}, quando a coleção chegou ao TCG Live`}` : 'Antes das coleções conhecidas'}</td></tr>`;
}
function tabelaPartidas(lista) {
  const cj = lista.some(l => l.dono) || S.jogadorSel.length > 1;
  const separar = new Set(lista.map(l => epocaDe(l.data, 'live')?.id || '')).size > 1;
  let epocaAnterior;
  const sep = l => { if (!separar) return ''; const e = epocaDe(l.data, 'live'), id = e?.id || '';
    if (id === epocaAnterior) return ''; epocaAnterior = id; return separadorEpoca(e, cj ? 10 : 9); };
  return `<div class="tabela alta"><table><thead><tr><th>Data</th>${cj ? '<th>Jogador</th>' : ''}<th>Resultado</th><th>Adversário</th><th>${cj ? 'Deck do jogador' : 'Seu deck'}</th><th>Deck do adversário</th><th class="n">Prêmios</th><th class="n">Turnos</th><th>Ordem</th><th>Motivo</th></tr></thead><tbody>
    ${lista.map(l => sep(l) + `<tr class="clicavel ${l.resultado === 'V' ? 'res-v' : l.resultado === 'D' ? 'res-d' : ''}" data-id="${l.id}">
      <td class="num" style="white-space:nowrap">${fmtData(l.data, true)}</td>${cj ? `<td>${l.dono ? esc(l.dono) : '<b>Eu</b>'}</td>` : ''}
      <td>${l.resultado === 'V' ? '<span class="pill v">Vitória</span>' : l.resultado === 'D' ? '<span class="pill d">Derrota</span>' : '<span class="pill n">?</span>'}${l.problemas?.length ? ` <span class="pill n" title="${esc(l.problemas.join('; '))}">⚠ incompleto?</span>` : ''}</td>
      <td>${esc(l.adversario)}</td><td>${deckHtml(l.meu_deck)}${l.lista_nome ? `<div class="muted" style="font-size:.74rem">lista: ${esc(l.lista_nome)}</div>` : ''}</td><td>${deckHtml(l.deck_adv)}${incertoHtml(l)}</td>
      <td class="n">${l.premios_eu}–${l.premios_adv}</td><td class="n">${l.turnos}</td>
      <td>${l.comecei == null ? '' : l.comecei ? '1º' : '2º'}</td><td class="muted">${esc(l.motivo)}</td></tr>`).join('')}
  </tbody></table></div>`;
}
function ligarLinhasPartidas() {
  document.querySelectorAll('tr.clicavel[data-id]').forEach(tr => tr.onclick = () => { location.hash = 'partida-' + tr.dataset.id; });
}

async function renderPartidas() {
  const vez = novaTela();
  const f = S.filtroPartidas || (S.filtroPartidas = { deck: '', adv: '', tag: '', de: '', ate: '' });
  await carregarJogadores();
  await carregarEpocas();
  const per = comEpoca(f.de, f.ate, 'live'), ep = epocaEscolhida('live');
  const qs = new URLSearchParams(Object.entries({ deck: f.deck, adv: f.adv, tag: f.tag, ...per }).filter(([, v]) => v)).toString();
  const d = await api(comJog('/api/partidas?' + qs));
  if (telaVelha(vez)) return;
  // opções em ordem do nome que aparece (o valor guardado é o código do deck, ex.: dragapult-ex)
  const opcoes = campo => [...new Set(d.partidas.map(l => l[campo]).filter(Boolean))].sort((a, b) => nomeDeck(a).localeCompare(nomeDeck(b), 'pt-BR'));
  const decks = opcoes('meu_deck'), advs = opcoes('deck_adv');
  const lista = d.partidas.filter(l => (!f.deck || l.meu_deck === f.deck) && (!f.adv || l.deck_adv === f.adv)
    && (!f.tag || (l.tags || '').toLowerCase().includes(f.tag.toLowerCase())) && noPeriodo(l.data, per));
  main.innerHTML = `
    ${trilha()}<header><h1>Partidas</h1><p class="sub">Clique numa partida para ver o detalhe, corrigir o nome dos decks e anotar. Quando uma coleção nova chega ao TCG Live, uma linha na lista marca onde começa a época dela.</p></header>
    <div class="row">
      ${seletorJogador()}
      ${seletorEpoca('live')}
      <span class="par-epoca"><label class="label" for="f-deck">Deck do jogador</label><select id="f-deck"><option value="">Todos</option>${decks.map(x => `<option value="${esc(x)}" ${f.deck === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select></span>
      <span class="par-epoca"><label class="label" for="f-adv">Deck do adversário</label><select id="f-adv"><option value="">Todos</option>${advs.map(x => `<option value="${esc(x)}" ${f.adv === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select></span>
      <input id="f-tag" placeholder="Tag (ex.: liga)" value="${esc(f.tag)}">
      <label class="label" for="f-de">De</label><input type="date" id="f-de" value="${f.de}">
      <label class="label" for="f-ate">Até</label><input type="date" id="f-ate" value="${f.ate}">
      <span class="grow"></span>
      <a class="btn" href="${comJog('/exportar/minhas_partidas.csv')}">Baixar para Excel</a>
      <a class="btn" href="/exportar/eventos.csv">Baixar eventos</a>
    </div>
    <p class="muted num">${lista.length} partidas${ep ? ` na época ${esc(ep.nome)}` : ''}</p>
    ${lista.length ? tabelaPartidas(lista) : '<p class="vazio">Nenhuma partida com esses filtros.</p>'}`;
  ['deck', 'adv', 'tag', 'de', 'ate'].forEach(k => $('#f-' + k).onchange = e => { f[k] = e.target.value; renderPartidas(); });
  ligarSeletorJogador(renderPartidas);
  ligarSeletorEpoca('live', renderPartidas);
  ligarLinhasPartidas();
}

function graficoPremios(r, a, b) {
  const W = 520, H = 220, m = { l: 30, r: 12, t: 12, b: 28 };
  const n = Math.max(r.turnos, 1);
  const x = t => m.l + (t / n) * (W - m.l - m.r), y = v => H - m.b - (v / 6) * (H - m.t - m.b);
  const deg = s => { if (!s) return ''; let d = `M${x(0)},${y(s[0])}`; for (let t = 1; t < s.length; t++) d += ` H${x(t)} V${y(s[t])}`; return d; };
  let g = '';
  for (let v = 0; v <= 6; v += 2) g += `<line class="grade" x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}"/><text x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
  const passo = n > 12 ? 2 : 1;
  for (let t = 0; t <= n; t += passo) g += `<text x="${x(t)}" y="${H - 8}" text-anchor="middle">${t === 0 ? 'Setup' : 'T' + t}</text>`;
  const fim = (s, cor) => s ? `<circle cx="${x(s.length - 1)}" cy="${y(s[s.length - 1])}" r="4" fill="${cor}"/>` : '';
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img">${g}
    <path d="${deg(r.serie[a])}" fill="none" stroke="var(--p1)" stroke-width="2.5"/><path d="${deg(r.serie[b])}" fill="none" stroke="var(--p2)" stroke-width="2.5"/>
    ${fim(r.serie[a], 'var(--p1)')}${fim(r.serie[b], 'var(--p2)')}</svg></div>
    <div class="legenda"><span><i style="background:var(--p1)"></i>${esc(a)}</span><span><i style="background:var(--p2)"></i>${esc(b)}</span></div>`;
}

async function renderDetalhe(id) {
  const vez = novaTela();
  const [p, listas] = await Promise.all([api('/api/partidas/' + id), api('/api/decks').catch(() => [])]);
  if (telaVelha(vez)) return;
  const v = p.visao, r = p.resumo;
  const a = v.eu, b = v.adversario;
  const pa = r.por_jogador[a] || {}, pb = r.por_jogador[b] || {};
  const pill = j => r.vencedor ? (r.vencedor === j ? '<span class="pill v">Venceu</span>' : '<span class="pill n">Perdeu</span>') : '';
  const linhas = [['Prêmios pegos','premios'],['Nocautes causados','nocautes'],['Dano total','dano'],['Ataques','ataques'],['Cartas jogadas','jogadas'],['Energias ligadas','energias'],['Evoluções','evolucoes'],['Mulligans','mulligans']];
  main.innerHTML = `
    <div class="row"><button id="voltar">← Partidas</button><a class="btn primary" href="#replay-${p.id}" style="background:var(--accent);color:var(--on-accent);border-color:var(--accent);font-weight:600">▶ Ver replay</a><span class="grow"></span><span class="muted num">#${p.id} · ${fmtData(p.capturada_em, true)} · origem: ${esc(p.origem)}${p.dono ? ` · partida de <b>${esc(p.dono)}</b>` : ''}</span></div>
    ${r.problemas?.length ? `<div class="aviso erro">Este log parece incompleto: ${esc(r.problemas.join('; '))}. Se você ainda tem o log no jogo, copie de novo; senão, apague esta partida ou deixe assim (ela fica fora das contas se faltar o resultado).</div>` : ''}
    <section class="panel">
      <div class="resultado">
        <div class="lado"><span class="label">${a === r.primeiro ? 'Começou' : 'Segundo'}</span><span class="nome p1">${esc(a)}</span>${pill(a)}</div>
        <div class="placar">${pa.premios ?? 0}–${pb.premios ?? 0}<small>prêmios · ${r.turnos} turnos</small></div>
        <div class="lado dir"><span class="label">${b === r.primeiro ? 'Começou' : 'Segundo'}</span><span class="nome p2">${esc(b)}</span>${pill(b)}</div>
      </div>
      <p class="muted">${fmtData(p.capturada_em, true)} · Motivo: <b>${esc(r.motivo)}</b>${r.motivo === 'Não identificado' && r.linha_final ? ` <span class="mono">("${esc(r.linha_final)}")</span>` : ''}${p.qtd_nao_lidas ? ` · <a href="#revisao">${p.qtd_nao_lidas} linha(s) não lida(s): revisar</a>` : ''}</p>
    </section>
    <section class="panel">
      <h2>Classificar esta partida</h2>
      <div class="grid2">
        <div class="row" style="flex-wrap:nowrap"><span class="label" style="width:110px;flex:none">Seu deck</span>${seletorDeck('e-meu', p.meu_deck, p.meu_deck ? '' : v.meu_deck)}</div>
        <div class="row" style="flex-wrap:nowrap"><span class="label" style="width:110px;flex:none">Deck dele</span>${seletorDeck('e-adv', p.deck_adv, p.deck_adv ? '' : v.deck_adv)}${p.deck_adv ? '' : incertoHtml(v)}</div>
        <label class="row" style="flex-wrap:nowrap"><span class="label" style="width:110px;flex:none">Lista usada</span>
          <select id="e-lista" class="grow"><option value="">Nenhuma</option>${listas.map(d => `<option value="${d.id}" ${d.id === p.deck_id ? 'selected' : ''}>${esc(d.nome)}${d.ativo ? '' : ' (arquivada)'}</option>`).join('')}</select></label>
        <label class="row"><span class="label" style="width:110px">Tags</span><input class="grow" id="e-tags" value="${esc(p.tags)}" placeholder="ex.: liga, teste-lista-2"></label>
        <label class="row"><span class="label" style="width:110px">Notas</span><input class="grow" id="e-notas" value="${esc(p.notas)}"></label>
      </div>
      <div class="row"><button class="primary" id="salvar">Salvar</button><span class="grow"></span><button class="perigo" id="apagar">Apagar partida</button></div>
      <p class="muted">"Automático" usa o deck identificado pelas cartas reveladas, comparadas com os decks do Limitless. A lista usada vem de <a href="#decks">Meus decks</a> e é ligada sozinha quando as cartas batem.</p>
    </section>
    <div class="grid2">
      <section class="panel"><h2>Corrida de prêmios</h2>${graficoPremios(r, a, b)}</section>
      <section class="panel"><h2>Comparativo</h2>
        <table><thead><tr><th></th><th class="n p1">${esc(a)}</th><th class="n p2">${esc(b)}</th></tr></thead>
        <tbody>${linhas.map(([n, k]) => `<tr><td>${n}</td><td class="n">${pa[k] ?? 0}</td><td class="n">${pb[k] ?? 0}</td></tr>`).join('')}</tbody></table></section>
    </div>
    <section class="panel"><h2>Nocautes</h2>
      ${r.nocautes.length ? `<table><tbody>${r.nocautes.map(k => `<tr><td class="mono" style="width:60px">T${k.turno}</td><td><span class="${k.autor === a ? 'p1' : 'p2'}">${esc(k.autor)}</span> nocauteou ${esc(k.carta)}</td><td class="n"><span class="dots">${'<span></span>'.repeat(k.premios)}</span></td></tr>`).join('')}</tbody></table>` : '<p class="muted">Nenhum nocaute.</p>'}
    </section>
    <section class="panel"><h2>Eventos</h2>
      <div class="tabela alta"><table><thead><tr><th class="n">Linha</th><th class="n">Turno</th><th>Tipo</th><th>Jogador</th><th>Carta</th><th>Alvo</th><th class="n">Valor</th><th>Texto</th></tr></thead><tbody>
      ${p.eventos.map(e => `<tr><td class="n">${e.linha}</td><td class="n">${e.turno}</td><td><span class="tipo ${e.tipo}">${esc(e.tipo)}</span></td><td>${esc(e.jogador)}</td><td>${esc(e.carta)}</td><td>${esc(e.alvo)}</td><td class="n">${e.valor ?? ''}</td><td class="mono">${esc(e.texto)}</td></tr>`).join('')}
      </tbody></table></div></section>`;
  $('#voltar').onclick = () => { location.hash = 'partidas'; };
  const valorMeu = ligarSeletorDeck('e-meu', v.meu_deck), valorAdv = ligarSeletorDeck('e-adv', v.deck_adv);
  $('#salvar').onclick = async () => {
    const lista = $('#e-lista').value;
    await api('/api/partidas/' + id, { method: 'PATCH', body: JSON.stringify({ meu_deck: valorMeu(), deck_adv: valorAdv(),
      deck_id: lista ? Number(lista) : null, tags: $('#e-tags').value.trim(), notas: $('#e-notas').value.trim() }) });
    toast('Partida atualizada'); renderDetalhe(id);
  };
  $('#apagar').onclick = async () => {
    if (!confirm('Apagar esta partida do banco? A cópia em dados/logs continua guardada.')) return;
    await api('/api/partidas/' + id, { method: 'DELETE' }); toast('Partida apagada'); location.hash = 'partidas';
  };
}

function barrasMatchup(lista, extra) {
  if (!lista.length) return '<p class="muted">Sem partidas ainda.</p>';
  return `<div class="mu-lista">${lista.map(g => `<div class="mu-linha" title="${g.ic_baixo != null ? `Provável entre ${fmt(g.ic_baixo, 0)}% e ${fmt(g.ic_alto, 0)}%` : ''}${extra && g.meta_taxa != null ? ` · nos campeonatos: ${pct(g.meta_taxa)}` : ''}">
      <span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${deckHtml(g.grupo)}</span>
      <div class="mu-barra"><span class="${g.taxa >= 50 ? 'bom' : 'ruim'}" style="width:${Math.max(g.taxa || 0, 1)}%">${fmt(g.taxa, 0)}%</span></div>
      <span class="wl">${g.v}V-${g.d}D</span><span class="nn">n=${g.n}</span></div>`).join('')}</div>`;
}
const PERIODOS = [[1, '1D'], [7, '7D'], [30, '30D'], [90, '90D'], [0, 'Tudo']];
async function renderDesempenho() {
  const vez = novaTela();
  const f = S.filtroDes || (S.filtroDes = { de: '', ate: '', deck: '', adv: '', periodo: 0 });
  if (f.periodo) { const d0 = new Date(Date.now() - (f.periodo - 1) * 864e5); f.de = d0.toISOString().slice(0, 10); f.ate = ''; }
  await carregarJogadores();
  await carregarEpocas();
  const per = comEpoca(f.de, f.ate, 'live'), ep = epocaEscolhida('live');
  const qs = new URLSearchParams(Object.entries({ ...per, deck: f.deck, adv: f.adv }).filter(([, v]) => v)).toString();
  const d = await api(comJog('/api/partidas?' + qs));
  const todos = await api(comJog('/api/partidas'));
  if (telaVelha(vez)) return;
  const decks = [...new Set(todos.partidas.map(l => l.meu_deck).filter(Boolean))].sort();
  const advs = [...new Set(todos.partidas.map(l => l.deck_adv).filter(Boolean))].sort();
  const ordem = Object.fromEntries(d.ordem.map(g => [g.grupo, g]));
  const kpi = (ico, cls, rotulo, v, det) => `<div class="kpi2"><span class="ico-kpi ${cls}">${ico}</span><div><span class="label">${rotulo}</span><div class="v">${v}</div><span class="d">${det}</span></div></div>`;
  const classe = g => g && g.taxa != null ? (g.taxa >= 50 ? 'bom' : 'ruim') : 'neutro';
  main.innerHTML = `
    ${trilha()}<header><h1>Desempenho</h1><p class="sub">${!soEu() ? `Mostrando: <b>${esc(nomeJogadorSel())}</b>. ` : ''}${ep ? `Época <b>${esc(ep.nome)}</b>. ` : ''}Suas taxas de vitória, matchups e evolução. Passe o mouse numa barra para ver a faixa provável da taxa (com poucas partidas ela ainda muda bastante).</p></header>
    <div class="row">
      <div class="chips-periodo">${PERIODOS.map(([v, r]) => `<button data-periodo="${v}" aria-pressed="${f.periodo === v && !(v === 0 && (f.de || f.ate))}">${r}</button>`).join('')}</div>
      <label class="label" for="d-de">De</label><input type="date" id="d-de" value="${f.de}">
      <label class="label" for="d-ate">Até</label><input type="date" id="d-ate" value="${f.ate}">
      ${seletorEpoca('live')}
      <span class="grow"></span>
      ${seletorJogador()}
      <select id="d-deck"><option value="">Todos os seus decks</option>${decks.map(x => `<option value="${esc(x)}" ${f.deck === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select>
      <select id="d-adv"><option value="">Todos os adversários</option>${advs.map(x => `<option value="${esc(x)}" ${f.adv === x ? 'selected' : ''}>${esc(nomeDeck(x))}</option>`).join('')}</select>
    </div>
    <div class="kpis">
      ${kpi('◎', classe(d.total), 'Geral', pct(d.total.taxa), `${d.total.v}V - ${d.total.d}D - ${d.total.e}E`)}
      ${kpi('↗', classe(ordem['Começando']), 'Começando', pct(ordem['Começando']?.taxa), `${ordem['Começando']?.v ?? 0}V / ${ordem['Começando']?.n ?? 0} partidas`)}
      ${kpi('↘', classe(ordem['Indo em segundo']), 'Indo em segundo', pct(ordem['Indo em segundo']?.taxa), `${ordem['Indo em segundo']?.v ?? 0}V / ${ordem['Indo em segundo']?.n ?? 0} partidas`)}
      ${kpi('#', 'neutro', 'Total de partidas', d.total.n, `turnos médios: ${fmt(d.turnos_medios.vitorias)} nas vitórias, ${fmt(d.turnos_medios.derrotas)} nas derrotas`)}
    </div>
    <section class="panel"><span class="label">Matchups pessoais</span>${barrasMatchup(d.por_adversario, true)}</section>
    <section class="panel"><span class="label">Com cada deck seu</span>${barrasMatchup(d.por_meu_deck)}</section>
    ${d.por_lista.length ? `<section class="panel"><h2>Com cada lista (Meus decks)</h2>${tabelaGrupos(d.por_lista, 'Lista')}</section>` : ''}
    <div class="grid2">
      <section class="panel"><h2>Ordem de jogo</h2>${tabelaGrupos(d.ordem, 'Ordem')}</section>
      <section class="panel"><h2>Primeiro nocaute</h2>${tabelaGrupos(d.primeiro_nocaute, 'Quem nocauteou primeiro')}</section>
      <section class="panel"><h2>Mulligan</h2>${tabelaGrupos(d.mulligan, 'Mão inicial')}</section>
      <section class="panel"><h2>Como as partidas terminam</h2>${tabelaGrupos(d.motivos, 'Motivo')}</section>
    </div>
    <section class="panel"><h2>Evolução da taxa de vitória</h2>
      ${d.tendencia.length > 1 ? graficoLinhas([{ nome: 'Taxa acumulada', valores: d.tendencia.map(t => t.taxa_acumulada), cor: 'var(--p1)' }], d.tendencia.map(t => t.dia.slice(5).split('-').reverse().join('/')),
        { marcas: marcasEpoca(d.tendencia.map(t => t.dia), 'live') }) : '<p class="muted">Precisa de partidas em pelo menos dois dias.</p>'}
      ${marcasEpoca(d.tendencia.map(t => t.dia), 'live').length ? '<p class="muted" style="font-size:.82rem">A linha tracejada marca o dia em que uma coleção nova chegou ao TCG Live: dali em diante o meta pode ser outro.</p>' : ''}
    </section>`;
  $('#d-deck').onchange = e => { f.deck = e.target.value; renderDesempenho(); };
  ligarSeletorJogador(renderDesempenho);
  ligarSeletorEpoca('live', renderDesempenho);
  $('#d-adv').onchange = e => { f.adv = e.target.value; renderDesempenho(); };
  $('#d-de').onchange = e => { f.de = e.target.value; f.periodo = 0; renderDesempenho(); };
  $('#d-ate').onchange = e => { f.ate = e.target.value; f.periodo = 0; renderDesempenho(); };
  document.querySelectorAll('[data-periodo]').forEach(b => b.onclick = () => { f.periodo = Number(b.dataset.periodo); if (!f.periodo) { f.de = ''; f.ate = ''; } renderDesempenho(); });
}
