/* =====================================================================
   LISTA OFICIAL: o formulário Deck List da Play! Pokémon (Standard), editável e em PDF
   ===================================================================== */
const MIN_LINHAS = { pokemon: 12, trainer: 20, energy: 7 };
const SEC_LO = [['pokemon', 'Pokémon'], ['trainer', 'Trainer'], ['energy', 'Energy']];
function papelSalvo() { try { return localStorage.getItem('papel') || 'a4'; } catch (e) { return 'a4'; } }
async function renderListaOficial(id) {
  const r = await api('/api/decks/' + id + '/lista-oficial');
  S.lo = { id, r, linhas: JSON.parse(JSON.stringify(r.linhas)), jogador: { ...r.jogador }, divisao: '', papel: papelSalvo(), salvo: r.salvo_em };
  desenharListaOficial();
}
function divisaoAuto(L) {
  const ano = (L.jogador.nascimento || '').split('-')[0], dv = L.r.divisoes;
  if (!/^\d{4}$/.test(ano)) return '';
  return Number(ano) >= dv.junior ? 'junior' : Number(ano) >= dv.senior[0] ? 'senior' : 'masters';
}
function divisoesHtml(L) {
  const dv = L.r.divisoes, marcada = L.divisao || divisaoAuto(L);
  const anos = []; for (let a = dv.senior[0]; a <= dv.senior[1]; a++) anos.push(a);
  const op = [['junior', `Junior Division (born in ${dv.junior} or later)`], ['senior', `Senior Division (born in ${anos.slice(0, -1).join(', ')}, or ${anos[anos.length - 1]})`],
              ['masters', `Masters Division (born in ${dv.masters} or earlier)`]];
  return `<span><b>Age Division</b> (check one):</span>${op.map(([k, t]) => `<button type="button" data-div="${k}"><span class="caixa ${marcada === k ? 'x' : ''}"></span>${t}</button>`).join('')}`;
}
function desenharListaOficial() {
  const L = S.lo, r = L.r;
  const [ano, mes, dia] = (L.jogador.nascimento || '').split('-');
  const linhasSec = k => { const ls = L.linhas[k] || (L.linhas[k] = []); const extra = Math.max(0, MIN_LINHAS[k] - ls.length);
    return [...ls.map((c, i) => [c, i]), ...Array.from({ length: extra }, (_, j) => [null, ls.length + j])]; };
  const nLinhas = SEC_LO.reduce((a, [k]) => a + Math.max(MIN_LINHAS[k], (L.linhas[k] || []).length), 0);
  const aperto = nLinhas > 50 ? 'muito-apertada' : nLinhas > 42 ? 'apertada' : '';
  const linha = (k, c, i) => {
    c = c || {};
    const campo = (nome, cls, rot) => `<td class="${cls}"><input data-sec="${k}" data-i="${i}" data-campo="${nome}" value="${esc(c[nome] ?? '')}" aria-label="${rot}"${nome === 'qtd' ? ' inputmode="numeric"' : ''}></td>`;
    return `<tr>${campo('qtd', 'qtd', 'Quantidade')}${campo('nome', 'nm', 'Nome')}${k === 'pokemon' ? campo('set', 'set', 'Coleção') + campo('numero', 'num', 'Número') + campo('reg', 'reg', 'Marca') : ''}
      <td class="tira"><button type="button" data-tirar="${k}:${i}" title="Apagar esta linha" tabindex="-1">×</button></td></tr>`;
  };
  const tabela = (k, rot) => `<div><table><colgroup><col style="width:11mm"><col>${k === 'pokemon' ? '<col style="width:15mm"><col style="width:16mm"><col style="width:11mm">' : ''}<col style="width:6mm"></colgroup>
      <thead><tr><th class="sec" colspan="${k === 'pokemon' ? 5 : 2}">${rot}<small data-soma="${k}"></small></th><th style="background:none;border:none"></th></tr>
      <tr><th>QTY</th><th style="text-align:left">NAME</th>${k === 'pokemon' ? '<th>SET</th><th>COLL. #</th><th>REG</th>' : ''}<th style="background:none;border:none"></th></tr></thead>
      <tbody>${linhasSec(k).map(([c, i]) => linha(k, c, i)).join('')}</tbody></table>
      <button type="button" class="mais" data-mais="${k}">+ linha</button></div>`;
  const grupos = {}; r.colecoes.forEach(c => (grupos[c.grupo] = grupos[c.grupo] || []).push(c));
  const dv = r.divisoes;
  main.innerHTML = `
    <div class="lo-barra no-print"><div class="row">
      <a class="btn" href="#meudeck-${L.id}">← ${esc(r.deck.nome)}</a>
      <span class="grow"></span>
      <span class="muted lo-salvo" id="lo-salvo">${L.salvo ? `Edições salvas ${fmtData(L.salvo, true)}` : 'Gerada a partir do deck'}</span>
      ${r.editada ? '<button id="lo-refazer" title="Descarta as suas edições e gera de novo a partir da lista do deck">Refazer a partir do deck</button>' : ''}
      <label class="label" for="lo-papel">Papel</label><select id="lo-papel"><option value="a4" ${L.papel === 'a4' ? 'selected' : ''}>A4</option><option value="carta" ${L.papel === 'carta' ? 'selected' : ''}>Carta (EUA)</option></select>
      <button class="primary" id="lo-pdf">Salvar em PDF</button></div></div>
    <header class="no-print"><h1>Lista oficial</h1><p class="sub">O formulário de lista de deck da Play! Pokémon, só Standard. Clique em qualquer campo da folha para editar: tudo fica salvo sozinho neste deck. Para o PDF, clique em <b>Salvar em PDF</b> e, na janela de impressão, escolha <b>Salvar como PDF</b> em Destino. Nome, Player ID e data de nascimento ficam só neste computador.</p></header>
    ${r.deck_mudou ? '<div class="aviso no-print">A lista do deck mudou depois que você editou esta lista oficial. Use "Refazer a partir do deck" se quiser trazer as cartas novas.</div>' : ''}
    <div id="lo-validacao" class="no-print">${conferenciaStandard(r.validacao, true)}</div>
    <div class="folha-wrap"><div class="folha ${L.papel === 'carta' ? 'carta' : ''} ${aperto}" id="folha">
      <div class="topo">
        <div><h2>Pokémon TCG Deck List</h2><div class="temporada">${dv.temporada_inicio}–${dv.temporada_inicio + 1} Tournament Season${r.ultima_colecao ? ` · through ${esc(r.ultima_colecao)}` : ''}</div></div>
        <div class="formato"><b>Format</b> (check one):<span class="caixa x"></span>Standard<span class="caixa"></span>Expanded</div>
      </div>
      <div class="jogador">
        <label>Player Name:<input data-jog="nome" value="${esc(L.jogador.nome)}" aria-label="Nome do jogador"></label>
        <label>Player ID:<input data-jog="id" value="${esc(L.jogador.id)}" aria-label="Player ID"></label>
        <label class="nasc">Date of Birth (MM/DD/YYYY):<input data-jog="mes" value="${esc(mes || '')}" maxlength="2" inputmode="numeric" aria-label="Mês de nascimento">/<input data-jog="dia" value="${esc(dia || '')}" maxlength="2" inputmode="numeric" aria-label="Dia de nascimento">/<input class="ano" data-jog="ano" value="${esc(ano || '')}" maxlength="4" inputmode="numeric" aria-label="Ano de nascimento"></label>
      </div>
      <div class="divisoes" id="lo-div">${divisoesHtml(L)}</div>
      <div class="corpo">
        <div class="legenda-sets">
          <div><h4>Standard Format Regulation Marks</h4><div class="marcas-std">${r.validacao.marcas.map(m => `<span>${esc(m)}</span>`).join('')}</div></div>
          ${Object.entries(grupos).map(([g, cs]) => `<div><h4>${esc(g)}</h4><div class="sets">${cs.map(c => `<b>${esc(c.codigo)}</b><span>${esc(c.nome)}</span>`).join('')}</div></div>`).join('')}
          <div class="admin">ADMINISTRATIVE USE ONLY</div>
        </div>
        <div class="secoes">${SEC_LO.map(([k, rot]) => tabela(k, rot)).join('')}</div>
      </div>
      <div class="rodape"><span>List the set abbreviation, collector number and regulation mark of every Pokémon; Trainer and Energy cards need only quantity and name. For a Pokémon from an older set that was reprinted in a listed set, write NA as the set. The list must match the deck exactly.</span>
        <b>TOTAL CARDS: <span data-soma="total"></span></b></div>
    </div></div>`;
  atualizarSomasLO();
  ligarListaOficial();
}
function atualizarSomasLO() {
  const L = S.lo; if (!L) return;
  const soma = k => (L.linhas[k] || []).reduce((a, c) => a + (c && c.nome && c.nome.trim() ? Number(c.qtd) || 0 : 0), 0);
  let total = 0;
  SEC_LO.forEach(([k]) => { const v = soma(k); total += v; const el = document.querySelector(`[data-soma="${k}"]`); if (el) el.textContent = v ? `${v} carta${v === 1 ? '' : 's'}` : ''; });
  const t = document.querySelector('[data-soma="total"]'); if (t) { t.textContent = total; t.style.color = total === 60 ? '' : '#c0392b'; }
}
function ligarListaOficial() {
  const L = S.lo, r = L.r;
  let tSalvar, tValidar;
  const salvar = async () => {
    clearTimeout(tSalvar);
    $('#lo-salvo') && ($('#lo-salvo').textContent = 'Salvando…');
    try {
      const x = await api('/api/decks/' + L.id + '/lista-oficial', { method: 'PUT', body: JSON.stringify({ linhas: L.linhas, jogador: L.jogador }) });
      L.salvo = x.salvo_em; L.r.editada = true;
      if (S.lo === L && $('#lo-salvo')) $('#lo-salvo').textContent = `Edições salvas ${fmtData(x.salvo_em, true).replace(/<[^>]+>/g, '')}`;
    } catch (e) { if ($('#lo-salvo')) $('#lo-salvo').textContent = 'Não consegui salvar: ' + e.message; }
  };
  const validar = async () => {
    try { const v = await api('/api/lista-oficial/validar', { method: 'POST', body: JSON.stringify({ linhas: L.linhas }) });
      if (S.lo === L) $('#lo-validacao').innerHTML = conferenciaStandard(v, true); } catch (e) {}
  };
  L.salvarJa = salvar;
  const mudou = () => { atualizarSomasLO(); clearTimeout(tSalvar); clearTimeout(tValidar); tSalvar = setTimeout(salvar, 900); tValidar = setTimeout(validar, 400); };
  document.querySelectorAll('.folha [data-campo]').forEach(inp => inp.oninput = () => {
    const k = inp.dataset.sec, i = Number(inp.dataset.i), ls = L.linhas[k];
    while (ls.length <= i) ls.push(k === 'pokemon' ? { qtd: '', nome: '', set: '', numero: '', reg: '' } : { qtd: '', nome: '' });
    ls[i][inp.dataset.campo] = inp.dataset.campo === 'qtd' ? inp.value.replace(/\D/g, '').slice(0, 2) : inp.value;
    if (inp.dataset.campo === 'qtd' && inp.value !== ls[i].qtd) inp.value = ls[i].qtd;
    mudou();
  });
  document.querySelectorAll('.folha [data-jog]').forEach(inp => inp.oninput = () => {
    const campo = inp.dataset.jog;
    if (['nome', 'id'].includes(campo)) L.jogador[campo] = inp.value;
    else {
      inp.value = inp.value.replace(/\D/g, '');
      const v = Object.fromEntries(['ano', 'mes', 'dia'].map(c => [c, document.querySelector(`.folha [data-jog="${c}"]`).value]));
      L.jogador.nascimento = [v.ano, v.mes, v.dia].join('-').replace(/^-+$/, '');
      $('#lo-div').innerHTML = divisoesHtml(L); ligarDivisoes();
    }
    clearTimeout(tSalvar); tSalvar = setTimeout(salvar, 900);
  });
  const ligarDivisoes = () => document.querySelectorAll('[data-div]').forEach(b => b.onclick = () => {
    L.divisao = (L.divisao || divisaoAuto(L)) === b.dataset.div && L.divisao ? '' : b.dataset.div; $('#lo-div').innerHTML = divisoesHtml(L); ligarDivisoes(); });
  ligarDivisoes();
  document.querySelectorAll('[data-tirar]').forEach(b => b.onclick = () => {
    const [k, i] = b.dataset.tirar.split(':'); const ls = L.linhas[k];
    if (Number(i) < ls.length) ls.splice(Number(i), 1);
    desenharListaOficial(); mudou();
  });
  document.querySelectorAll('[data-mais]').forEach(b => b.onclick = () => {
    const k = b.dataset.mais, ls = L.linhas[k];
    const alvo = Math.max(ls.length, MIN_LINHAS[k]) + 1;
    while (ls.length < alvo) ls.push(k === 'pokemon' ? { qtd: '', nome: '', set: '', numero: '', reg: '' } : { qtd: '', nome: '' });
    desenharListaOficial();
    const ins = document.querySelectorAll(`.folha [data-sec="${k}"][data-campo="qtd"]`); ins[ins.length - 1]?.focus();
  });
  $('#lo-papel').onchange = e => { L.papel = e.target.value; try { localStorage.setItem('papel', L.papel); } catch (er) {} $('#folha').classList.toggle('carta', L.papel === 'carta'); };
  if ($('#lo-refazer')) $('#lo-refazer').onclick = async () => {
    if (!confirm('Descartar as suas edições e gerar a lista oficial de novo a partir do deck? Nome, Player ID e data de nascimento continuam.')) return;
    await api('/api/decks/' + L.id + '/lista-oficial', { method: 'DELETE' }); toast('Lista refeita a partir do deck'); renderListaOficial(L.id);
  };
  $('#lo-pdf').onclick = async () => {
    if (tSalvar) await salvar();
    let st = document.getElementById('estilo-pagina');
    if (!st) { st = document.createElement('style'); st.id = 'estilo-pagina'; document.head.appendChild(st); }
    st.textContent = `@page { size: ${L.papel === 'carta' ? 'letter' : 'A4'} portrait; margin: 8mm; }`;
    const titulo = document.title;
    document.title = `Lista oficial - ${r.deck.nome}`;
    document.activeElement?.blur();
    document.body.classList.add('imprimindo');
    const fim = () => { document.body.classList.remove('imprimindo'); document.title = titulo; window.removeEventListener('afterprint', fim); };
    window.addEventListener('afterprint', fim);
    window.print();
  };
}
