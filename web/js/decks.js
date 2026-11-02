/* =====================================================================
   MEUS DECKS
   ===================================================================== */
const EXEMPLO_LISTA = `Pokémon: 3
4 Dreepy TWM 128
4 Drakloak TWM 129
3 Dragapult ex TWM 130

Trainer: 2
4 Arven SVI 166
4 Buddy-Buddy Poffin TEF 144

Energy: 2
3 Basic {R} Energy SVE 2
3 Basic {P} Energy SVE 5

Total Cards: ...`;

function formularioDeck(d) {
  d = d || {};
  return `<section class="panel" id="form-deck">
    <h2>${d.id ? 'Editar deck' : d.versao_de ? 'Nova versão do deck' : 'Adicionar deck'}</h2>
    <p class="sub">No TCG Live, abra o deck e use <b>Exportar</b>: a lista vai para a área de transferência. Cole aqui. A lista do Limitless também funciona.</p>
    <div class="grid2">
      <label class="row" style="flex-wrap:nowrap"><span class="label" style="width:90px;flex:none">Nome</span><input id="d-nome" class="grow" value="${esc(d.nome || '')}" placeholder="ex.: Lopunny v2 (2 Hilda)"></label>
      <div class="row" style="flex-wrap:nowrap"><span class="label" style="width:90px;flex:none">Deck</span>${seletorDeck('d-arq', d.arquetipo || '', '')}</div>
    </div>
    <textarea id="d-lista" rows="12" placeholder="${esc(EXEMPLO_LISTA)}">${esc(d.lista || '')}</textarea>
    <input id="d-notas" placeholder="Notas (opcional)" value="${esc(d.notas || '')}">
    <div class="row"><button class="primary" id="d-salvar">Salvar deck</button><button id="d-cancelar">Cancelar</button>
      <span class="muted">Deixe o Deck em "Automático" para identificar pelo conteúdo da lista.</span></div>
  </section>`;
}
function ligarFormularioDeck(d, depois) {
  const valorArq = ligarSeletorDeck('d-arq', '');
  $('#d-cancelar').onclick = () => { $('#form-deck').remove(); };
  $('#d-salvar').onclick = async () => {
    const corpo = { nome: $('#d-nome').value, arquetipo: valorArq(), lista: $('#d-lista').value, notas: $('#d-notas').value, versao_de: d?.versao_de || null };
    try {
      const r = d?.id ? await api('/api/decks/' + d.id, { method: 'PUT', body: JSON.stringify(corpo) })
                      : await api('/api/decks', { method: 'POST', body: JSON.stringify(corpo) });
      toast([d?.id ? 'Deck atualizado' : 'Deck salvo', ...(r.avisos || []), r.vinculadas ? `${r.vinculadas} partida(s) ligada(s) a ele` : ''].filter(Boolean).join(' · '));
      depois(r.id || d.id);
    } catch (e) { toast(e.message); }
  };
}

async function renderMeusDecks() {
  const lista = await api('/api/decks');
  main.innerHTML = `
    ${trilha()}<header><h1>Meus decks</h1><p class="sub">Cadastre as listas que você joga. Cada partida capturada é ligada sozinha à lista que contém todas as cartas que você revelou, e o histórico de cada lista fica separado. Para testar mudanças, crie uma nova versão.</p></header>
    <div class="row"><input id="busca-deck" placeholder="Buscar decks…" style="width:260px"><button id="vincular">Ligar partidas antigas</button></div>
    <div id="area-form"></div>
    <div class="grade-decks">
      <button class="deck-novo" id="novo"><span><span style="font-size:1.8rem">⇪</span><br><b style="color:var(--ink)">Importar deck</b><br><span style="font-size:.85rem">Cole a lista exportada do TCG Live</span></span></button>
      ${lista.map(d => {
        const p = d.placar, ics = d.icones && d.icones.length ? d.icones : (d.capa ? [pokeId(d.capa.nome)] : []);
        const dias = Math.max(0, Math.round((Date.now() - new Date(d.criado_em)) / 864e5));
        return `<a class="deck-card ${d.ativo ? '' : 'arquivado'}" href="#meudeck-${d.id}" data-nome="${esc((d.nome + ' ' + (d.nome_arquetipo || '')).toLowerCase())}">
          <div class="deck-capa">
            <span class="selo" ${d.ativo && !d.standard_ok ? 'style="color:var(--bad);background:color-mix(in srgb,var(--bad) 14%,transparent)" title="A lista não passa nas regras do Standard: abra o deck para ver o motivo"' : ''}>${!d.ativo ? 'Arquivado' : d.standard_ok ? 'Standard ✓' : 'Fora do Standard'}</span>
            <button class="estrela ${d.favorito ? 'on' : ''}" data-fav="${d.id}" title="${d.favorito ? 'Tirar dos favoritos' : 'Favoritar'}">${d.favorito ? '★' : '☆'}</button>
            <div class="icones-grandes">${ics.map(i => `<img src="/icone/${encodeURIComponent(i)}" alt="${esc(i)}" title="${esc(i)}">`).join('')}</div>
            ${d.icones_corrigidos ? '<span class="corrigido">ícones corrigidos por você</span>' : ''}
            <button class="lapis" data-icones="${d.id}" title="Corrigir os ícones deste deck">✎</button></div>
          <div class="deck-corpo"><b>${esc(d.nome)}</b><span class="muted" style="font-size:.8rem">${esc(d.nome_arquetipo || 'Deck não identificado')} · criado ${dias === 0 ? 'hoje' : `há ${dias} dia${dias === 1 ? '' : 's'}`}</span>
            <div class="deck-nums"><div><span class="label">Taxa de vitória</span><div class="v" style="color:${p.taxa == null ? 'var(--muted)' : p.taxa >= 50 ? 'var(--good)' : 'var(--bad)'}">${p.taxa == null ? '–' : fmt(p.taxa, 0) + '%'}</div></div>
              <div><span class="label">Partidas</span><div class="v">${p.n}</div></div></div></div></a>`; }).join('')}
    </div>`;
  $('#busca-deck').oninput = e => { const q = e.target.value.toLowerCase(); document.querySelectorAll('.deck-card').forEach(c => c.hidden = q && !c.dataset.nome.includes(q)); };
  document.querySelectorAll('[data-fav]').forEach(b => b.onclick = async ev => { ev.preventDefault(); ev.stopPropagation();
    const atual = b.classList.contains('on'); await api('/api/decks/' + b.dataset.fav, { method: 'PUT', body: JSON.stringify({ favorito: !atual }) }); renderMeusDecks(); });
  document.querySelectorAll('[data-icones]').forEach(b => b.onclick = ev => { ev.preventDefault(); ev.stopPropagation();
    const d = lista.find(x => x.id === Number(b.dataset.icones)); editarIcones(d, renderMeusDecks); });
  $('#novo').onclick = () => { $('#area-form').innerHTML = formularioDeck(); ligarFormularioDeck(null, id => { location.hash = 'meudeck-' + id; }); $('#area-form').scrollIntoView({ behavior: 'smooth' }); };
  $('#vincular').onclick = async () => { const r = await api('/api/decks/vincular', { method: 'POST' }); toast(`${r.vinculadas} partida(s) ligada(s)`); renderMeusDecks(); };
}

// ---- corrigir os ícones de um deck (a correção vale para o arquétipo inteiro daqui em diante)
async function editarIcones(d, aoSalvar) {
  const det = d.cartas ? d : await api('/api/decks/' + d.id);
  const pokes = [...new Set(det.cartas.filter(c => c.secao === 'Pokémon').map(c => pokeId(c.nome)))];
  let atuais = [...(d.icones || [])].slice(0, 2);
  const fundo = document.createElement('div');
  fundo.className = 'janela-fundo';
  fundo.innerHTML = `<div class="janela" role="dialog" aria-label="Corrigir ícones">
    <h2 style="margin-top:0">Ícones de “${esc(d.nome)}”</h2>
    <p class="muted" style="font-size:.85rem">Escolha até 2 Pokémon. A correção fica guardada e passa a valer para todo deck ${esc(d.nome_arquetipo || '')} (novas listas, matchups e meta).</p>
    <div class="previa" id="ic-previa"></div>
    <div class="row"><input id="ic-1" placeholder="1º Pokémon (ex.: Dragapult)" style="flex:1"><input id="ic-2" placeholder="2º Pokémon (opcional)" style="flex:1"></div>
    <span class="label">Pokémon da lista (clique para usar)</span>
    <div class="chips-poke">${pokes.map(p => `<button data-poke="${esc(p)}"><img src="/icone/${encodeURIComponent(p)}" alt="">${esc(p)}</button>`).join('')}</div>
    <div class="row"><button id="ic-sugestao" title="Apaga a correção e volta à sugestão automática">Voltar à sugestão</button><span class="grow"></span><button id="ic-cancelar">Cancelar</button><button class="primary" id="ic-salvar">Salvar</button></div>
  </div>`;
  document.body.appendChild(fundo);
  const i1 = fundo.querySelector('#ic-1'), i2 = fundo.querySelector('#ic-2');
  i1.value = atuais[0] || ''; i2.value = atuais[1] || '';
  const previa = () => { const v = [i1.value, i2.value].map(x => pokeId(x)).filter(Boolean);
    fundo.querySelector('#ic-previa').innerHTML = v.map(p => `<img src="/icone/${encodeURIComponent(p)}" alt="${esc(p)}" title="${esc(p)}">`).join('') || '<span class="muted">sem ícone</span>'; };
  i1.oninput = i2.oninput = previa; previa();
  fundo.querySelectorAll('[data-poke]').forEach(b => b.onclick = () => {
    if (!i1.value || (i2.value && document.activeElement !== i2)) { i1.value = b.dataset.poke; } else { i2.value = b.dataset.poke; }
    if (i1.value === i2.value) i2.value = ''; previa(); });
  const fechar = () => fundo.remove();
  const salvar = async lista => {
    try { await api('/api/decks/' + d.id, { method: 'PUT', body: JSON.stringify({ icones: lista }) }); }
    catch (e) { toast(e.message); return; }
    fechar(); await carregarArquetipos(); toast(lista.length ? 'Ícones corrigidos — vou usar nos próximos decks deste tipo' : 'Voltou à sugestão automática'); aoSalvar && aoSalvar();
  };
  fundo.onclick = e => { if (e.target === fundo) fechar(); };
  fundo.querySelector('#ic-cancelar').onclick = fechar;
  fundo.querySelector('#ic-sugestao').onclick = () => salvar([]);
  fundo.querySelector('#ic-salvar').onclick = () => salvar([i1.value, i2.value].map(x => x.trim()).filter(Boolean));
  i1.focus();
}
