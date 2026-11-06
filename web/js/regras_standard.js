/* =====================================================================
   REGRAS DO STANDARD: a base de regras (markdown) com índice e busca
   ===================================================================== */
const semAcento = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
function mdInline(s) {
  return esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (m, txt, url) => `<a href="${url}" target="_blank" rel="noopener">${txt}</a>`);
}
function mdTabela(linhas) {
  const cel = r => r.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
  const temSep = linhas[1] && /^\s*\|?\s*:?-{2,}/.test(linhas[1]);
  const cab = cel(linhas[0]), corpo = linhas.slice(temSep ? 2 : 1).map(cel);
  return `<div class="tabela"><table><thead><tr>${cab.map(c => `<th>${mdInline(c)}</th>`).join('')}</tr></thead>
    <tbody>${corpo.map(r => `<tr>${r.map(c => `<td>${mdInline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function mdLista(linhas) {
  let h = ''; const pilha = [];
  for (const l of linhas) {
    const m = l.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
    if (!m) { h += ' ' + mdInline(l.trim()); continue; }
    const ind = m[1].length, tag = /\d/.test(m[2]) ? 'ol' : 'ul';
    while (pilha.length && ind < pilha[pilha.length - 1].ind) h += `</li></${pilha.pop().tag}>`;
    if (!pilha.length || ind > pilha[pilha.length - 1].ind) { h += `<${tag}>`; pilha.push({ ind, tag }); } else h += '</li>';
    h += `<li>${mdInline(m[3])}`;
  }
  while (pilha.length) h += `</li></${pilha.pop().tag}>`;
  return h;
}
// Markdown simples (títulos, parágrafos, listas, tabelas, negrito e links), em seções para a busca.
function mdHtml(md) {
  const L = String(md || '').replace(/\r/g, '').split('\n'), out = [], indice = [];
  const ehLista = l => /^\s*([-*]|\d+\.)\s+/.test(l);
  let i = 0, aberta = false, n = 0;
  while (i < L.length) {
    const l = L[i];
    if (!l.trim()) { i++; continue; }
    const t = l.match(/^(#{1,4})\s+(.*)$/);
    if (t) {
      const nivel = t[1].length, id = 'rg-' + (++n);
      if (nivel <= 3) { if (aberta) out.push('</section>'); out.push(`<section class="rg-sec" data-nivel="${nivel}">`); aberta = true; }
      if (nivel >= 2) indice.push({ nivel, texto: t[2], id });
      out.push(`<h${nivel} id="${id}">${mdInline(t[2])}</h${nivel}>`); i++; continue;
    }
    if (l.trim().startsWith('|')) { const rs = []; while (i < L.length && L[i].trim().startsWith('|')) rs.push(L[i++]); out.push(mdTabela(rs)); continue; }
    if (ehLista(l)) { const it = []; while (i < L.length && (ehLista(L[i]) || (/^\s{2,}\S/.test(L[i])))) it.push(L[i++]); out.push(mdLista(it)); continue; }
    const par = [];
    while (i < L.length && L[i].trim() && !/^#{1,4}\s/.test(L[i]) && !L[i].trim().startsWith('|') && !ehLista(L[i])) par.push(L[i++].trim());
    out.push(`<p>${mdInline(par.join(' '))}</p>`);
  }
  if (aberta) out.push('</section>');
  return { html: out.join('\n'), indice };
}
// destaca as ocorrências (sem diferenciar acentos e maiúsculas) dentro de um elemento
function destacar(el, termo) {
  const alvo = semAcento(termo); if (!alvo) return 0;
  let total = 0;
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, { acceptNode: n => n.parentElement.closest('mark,script,style') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  const nos = []; while (w.nextNode()) nos.push(w.currentNode);
  for (const no of nos) {
    const txt = no.nodeValue; let norm = '', mapa = [];
    for (let k = 0; k < txt.length; k++) { const c = semAcento(txt[k]); for (let q = 0; q < c.length; q++) { norm += c[q]; mapa.push(k); } }
    let pos = norm.indexOf(alvo); if (pos < 0) continue;
    const frag = document.createDocumentFragment(); let ult = 0;
    while (pos >= 0) {
      const ini = mapa[pos], fim = mapa[pos + alvo.length - 1] + 1;
      frag.append(txt.slice(ult, ini)); const mk = document.createElement('mark'); mk.textContent = txt.slice(ini, fim); frag.append(mk);
      ult = fim; total++; pos = norm.indexOf(alvo, pos + alvo.length);
    }
    frag.append(txt.slice(ult)); no.replaceWith(frag);
  }
  return total;
}
async function renderRegrasStandard() {
  const vez = novaTela();
  const r = await api('/api/regras-standard');
  if (telaVelha(vez)) return;
  const g = r.regras, est = r.estado || {};
  if (!r.texto) { main.innerHTML = `${trilha()}<header><h1>Regras do Standard</h1></header><div class="aviso erro">A base de regras não foi encontrada na pasta docs do programa. Atualize o programa em Ajustes.</div>`; return; }
  const { html, indice } = mdHtml(r.texto);
  const data = r.atualizada_em ? fmtData(r.atualizada_em) : 'sem data';
  main.innerHTML = `
    ${trilha()}<header><h1>Regras do Standard</h1><p class="sub">Resumo em português das regras oficiais da Play! Pokémon, só do formato Standard (o único que o programa analisa). Atualizada em <b>${data}</b>${r.fonte === 'baixada' ? ' (baixada do GitHub)' : ''}. A base é revisada todo mês e chega aqui sozinha, sem precisar atualizar o programa.</p></header>
    <section class="panel"><h2>O que o programa usa destas regras</h2>
      <div class="rg-usa">
        <div><b><span class="marcas-reg">${g.marcas.map(m => `<span>${esc(m)}</span>`).join('')}</span></b>Marcas de regulamento válidas hoje. Com cartas de mesmo nome, o leitor e o replay escolhem a versão que vale no Standard.</div>
        <div><b>${g.tamanho_deck} cartas · até ${g.max_copias} · ${g.max_ace_spec} ACE SPEC</b>Conferência de cada lista em Meus decks e na Lista oficial (versões diferentes com o mesmo nome somam).</div>
        <div><b>${g.premios} prêmios</b>Quem pega o último vence: o leitor usa isso quando o log não traz a linha final. ex vale 2 e Mega ex vale 3.</div>
        <div><b>1º turno</b>Quem começa não ataca nem joga Apoiador, e ninguém evolui no próprio 1º turno. Por isso as Decisões separam as aberturas por quem começou, e o replay não evolui um Pokémon que acabou de entrar.</div>
      </div>
      <div class="row"><input id="rg-busca" placeholder="Buscar nas regras (ex.: mulligan, empate, Apoiador)" style="flex:1;min-width:240px"><span class="muted" id="rg-cont"></span>
        <button id="rg-atualizar">Procurar atualização</button><a class="btn" href="${esc(r.pagina_oficial)}" target="_blank" rel="noopener">Documentos oficiais ↗</a></div>
      ${est.erro ? `<div class="aviso erro">${esc(est.erro)}</div>` : est.mensagem ? `<p class="muted" style="font-size:.85rem">${esc(est.mensagem)}</p>` : ''}
      ${est.verificado_em ? `<p class="muted" style="font-size:.8rem">Última verificação no GitHub: ${fmtData(est.verificado_em, true)}</p>` : ''}
    </section>
    <div class="rg-layout">
      <aside class="panel rg-indice" aria-label="Índice das regras">${indice.map(x => `<button class="n${x.nivel}" data-alvo="${x.id}">${esc(x.texto)}</button>`).join('')}</aside>
      <article class="panel rg-doc" id="rg-doc">${html}</article>
    </div>`;
  document.querySelectorAll('[data-alvo]').forEach(b => b.onclick = () => document.getElementById(b.dataset.alvo)?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  const doc = $('#rg-doc'), original = doc.innerHTML;
  let t;
  $('#rg-busca').oninput = e => { clearTimeout(t); t = setTimeout(() => {
    const q = e.target.value.trim();
    doc.innerHTML = original;
    if (q.length < 2) { $('#rg-cont').textContent = ''; return; }
    let achados = 0, secoes = 0;
    doc.querySelectorAll('.rg-sec').forEach(sec => { const n = destacar(sec, q); sec.hidden = !n; achados += n; secoes += n ? 1 : 0; });
    $('#rg-cont').textContent = achados ? `${achados} ocorrência${achados === 1 ? '' : 's'} em ${secoes} trecho${secoes === 1 ? '' : 's'}` : 'Nada encontrado';
    doc.querySelector('mark')?.scrollIntoView({ block: 'center' });
  }, 200); };
  $('#rg-atualizar').onclick = async () => {
    $('#rg-atualizar').disabled = true;
    const x = await api('/api/regras-standard/atualizar', { method: 'POST' }).catch(e => ({ estado: { erro: e.message } }));
    toast(x.estado?.erro || x.estado?.mensagem || 'Verificado'); renderRegrasStandard();
  };
}
