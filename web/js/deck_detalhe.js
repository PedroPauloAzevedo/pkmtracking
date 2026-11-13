// Conferência da lista com as regras do Standard (60 cartas, 4 cópias, ACE SPEC, Básico, marcas)
function conferenciaStandard(v, compacta) {
  if (!v) return '';
  const ok = !v.problemas.length;
  return `<div class="aviso lo-validacao ${ok ? 'ok' : 'erro'}">
    <b>${ok ? `✓ Lista válida no Standard: ${v.total} cartas, marcas ${v.marcas.join(', ')}.` : `A lista não vale no Standard (${v.problemas.length} problema${v.problemas.length === 1 ? '' : 's'}):`}</b>
    ${v.problemas.length ? `<ul>${v.problemas.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
    ${v.avisos.length ? `${compacta ? '' : `<p style="margin-top:6px">Para conferir:</p>`}<ul class="muted">${v.avisos.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
  </div>`;
}

// Lista do deck: reimpressões da MESMA carta (ex.: 2 Duskull de Shrouded Fable + 1 de Prismatic Evolutions) viram um quadrinho só,
// com a quantidade somada; o mouse mostra cada versão. "Mesma carta" = mesmo carta_id (a biblioteca dá o mesmo id às reimpressões,
// pela chave funcional: nome, PS, habilidades e ataques). Cartas diferentes com o mesmo nome (ex.: Dunsparce de Journey Together
// e de Temporal Forces) continuam separadas, lado a lado. Sem carta_id (carta fora da biblioteca), junta pelo nome + coleção + número.
function juntarIguais(cartas) {
  const por = new Map();
  for (const c of cartas) {
    const k = c.carta_id || `${(c.nome || '').trim().toLowerCase()}|${c.set_code}|${c.numero}`;
    const g = por.get(k) || por.set(k, { ...c, qtd: 0, versoes: [] }).get(k);
    g.versoes.push(c);
    g.qtd += c.qtd;
    const maior = g.versoes.reduce((a, b) => (b.qtd > a.qtd ? b : a));
    g.set_code = maior.set_code; g.numero = maior.numero;
  }
  // cartas de mesmo nome (mas diferentes) ficam vizinhas, na ordem em que o nome aparece pela primeira vez
  const grupos = [...por.values()], primeiro = new Map();
  grupos.forEach((g, i) => { const n = (g.nome || '').trim().toLowerCase(); if (!primeiro.has(n)) primeiro.set(n, i); });
  return grupos.map((g, i) => [primeiro.get((g.nome || '').trim().toLowerCase()), i, g]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map(x => x[2]);
}

async function renderMeuDeck(id) {
  const vez = novaTela();
  const d = await api('/api/decks/' + id);
  if (telaVelha(vez)) return;
  const a = d.analise, t = a.total;
  const ordem = Object.fromEntries(a.ordem.map(g => [g.grupo, g]));
  const minhas = a.partidas.filter(l => l.deck_id === id);
  const secoes = ['Pokémon', 'Trainer', 'Energy'].map(s => [s, juntarIguais(d.cartas.filter(c => c.secao === s))]).filter(([, cs]) => cs.length);
  main.innerHTML = `
    <div class="row"><a class="btn" href="#decks">← Meus decks</a></div>
    ${trilha()}<header class="row" style="gap:10px"><span class="cel-carta">${(d.icones || []).map(i => `<img class="ico" src="/icone/${encodeURIComponent(i)}" alt="">`).join('')}</span><div><h1>${esc(d.nome)}</h1>
      <p class="sub">${esc(d.nome_arquetipo || 'Deck não identificado')} · criado em ${fmtData(d.criado_em)}${d.ativo ? '' : ' · arquivado'}${d.notas ? ` · ${esc(d.notas)}` : ''}</p></div></header>
    <div class="row"><a class="btn primary" href="#lista-${d.id}" style="background:var(--accent);color:var(--on-accent);border-color:var(--accent);font-weight:600">Lista oficial (PDF)</a><button id="editar">Editar</button><button id="ed-icones">Corrigir ícones</button><button id="versao">Criar nova versão</button><button id="arquivar">${d.ativo ? 'Arquivar' : 'Reativar'}</button><span class="grow"></span><button class="perigo" id="apagar-deck">Apagar</button></div>
    ${conferenciaStandard(d.standard)}
    <div id="area-form"></div>
    <div class="kpis">
      <div class="kpi"><span class="label">Partidas</span><span class="v">${t.n}</span><span class="d">${t.v} vitórias</span></div>
      <div class="kpi"><span class="label">Taxa de vitória</span><span class="v">${pct(t.taxa)}</span><span class="d">${t.ic_baixo != null ? `provável entre ${fmt(t.ic_baixo, 0)}% e ${fmt(t.ic_alto, 0)}%` : '–'}</span></div>
      <div class="kpi"><span class="label">Começando</span><span class="v">${pct(ordem['Começando']?.taxa)}</span><span class="d">${ordem['Começando']?.n ?? 0} partidas</span></div>
      <div class="kpi"><span class="label">Indo em segundo</span><span class="v">${pct(ordem['Indo em segundo']?.taxa)}</span><span class="d">${ordem['Indo em segundo']?.n ?? 0} partidas</span></div>
    </div>
    <section class="panel"><h2>Contra cada deck</h2>${tabelaGrupos(a.por_adversario, 'Deck do adversário', true, deckHtml)}</section>
    <section class="panel"><h2>Lista (${d.cartas.reduce((s, c) => s + c.qtd, 0)} cartas)</h2>
      ${secoes.map(([s, cs]) => `<h3>${s} (${cs.reduce((x, c) => x + c.qtd, 0)})</h3><div class="deck-cards">${cs.map(c => `<figure title="${esc(c.nome)}: ${c.versoes.map(v => `${v.qtd}× ${esc(v.set_code)} ${esc(v.numero)}`).join(' + ')}"><img src="${imgId(c.carta_id, c.nome)}" alt="${esc(c.nome)}" loading="lazy"><span class="qtd">${c.qtd}</span><figcaption>${esc(c.nome)}</figcaption></figure>`).join('')}</div>`).join('')}
    </section>
    <section class="panel" id="consistencia"><h2>Consistência</h2><p class="muted">Calculando…</p></section>
    <section class="panel"><h2>Partidas com esta lista</h2>${minhas.length ? tabelaPartidas(minhas) : '<p class="muted">Nenhuma partida ligada ainda. Elas são ligadas sozinhas quando as cartas reveladas batem com a lista, ou escolha a lista na tela da partida.</p>'}</section>`;
  ligarLinhasPartidas();
  desenharConsistencia(id);
  $('#editar').onclick = () => { $('#area-form').innerHTML = formularioDeck(d); ligarFormularioDeck(d, () => renderMeuDeck(id)); };
  $('#ed-icones').onclick = () => editarIcones(d, () => renderMeuDeck(id));
  $('#versao').onclick = () => { $('#area-form').innerHTML = formularioDeck({ ...d, id: null, nome: d.nome + ' (nova versão)', versao_de: d.id }); ligarFormularioDeck({ versao_de: d.id }, nid => { location.hash = 'meudeck-' + nid; }); };
  $('#arquivar').onclick = async () => { await api('/api/decks/' + id, { method: 'PUT', body: JSON.stringify({ ativo: !d.ativo }) }); renderMeuDeck(id); };
  $('#apagar-deck').onclick = async () => { if (!confirm('Apagar este deck? As partidas continuam, só perdem o vínculo com a lista.')) return; await api('/api/decks/' + id, { method: 'DELETE' }); location.hash = 'decks'; };
}

// Meus decks > deck: probabilidades exatas da lista (tracker/probabilidades.py).
async function desenharConsistencia(id) {
  const el = $('#consistencia'); if (!el) return;
  let r; try { r = await api(`/api/decks/${id}/consistencia`); } catch (e) { el.innerHTML = `<h2>Consistência</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  const p = x => fmt(100 * x, 1) + '%';
  const ob = r.observado;
  const esperadoComMull = r.mulligan;  // chance de pelo menos 1 mulligan na partida = chance da 1ª mão sem Básico
  const ordenadas = [...r.cartas].sort((a, b) => b.qtd - a.qtd || a.nome.localeCompare(b.nome));
  el.innerHTML = `<h2>Consistência</h2>
    <p class="sub">Contas exatas com as regras do Standard: mão de 7, mulligan sem Pokémon Básico, 6 prêmios e 1 compra por turno (quem começa também compra). Valem igual começando ou indo em segundo.</p>
    ${r.deck !== 60 ? `<p class="aviso">A lista tem ${r.deck} cartas; as contas usam esse total.</p>` : ''}
    ${r.sem_estagio ? `<p class="aviso">${r.sem_estagio} Pokémon sem o estágio na biblioteca de cartas: o mulligan pode estar errado. Atualize a biblioteca em Programa &gt; Biblioteca de cartas.</p>` : ''}
    <div class="kpis">
      <div class="kpi"><span class="label">Pokémon Básicos</span><span class="v">${r.basicos}</span><span class="d">na lista de ${r.deck}</span></div>
      <div class="kpi"><span class="label">Chance de mulligan</span><span class="v">${p(r.mulligan)}</span><span class="d">${r.mulligans_esperados == null ? 'sem Pokémon Básico na lista: toda mão é mulligan' : `${fmt(r.mulligans_esperados, 2)} mulligans por partida, em média`}</span></div>
      <div class="kpi"><span class="label">Suas partidas com mulligan</span><span class="v">${ob.partidas ? p(ob.com_mulligan / ob.partidas) : '–'}</span><span class="d">${ob.partidas ? `${ob.com_mulligan} de ${ob.partidas} (esperado ${p(esperadoComMull)})` : 'nenhuma partida ligada ainda'}</span></div>
    </div>
    <div class="tabela alta"><table><thead><tr><th>Carta</th><th class="n">Cópias</th><th class="n">Na mão inicial</th><th class="n">Até o 1º turno</th><th class="n">Até o 2º</th><th class="n">Até o 3º</th><th class="n">Alguma nos prêmios</th><th class="n">Todas nos prêmios</th></tr></thead><tbody>
      ${ordenadas.map(c => `<tr><td>${esc(c.nome)}${c.basico ? ' <span class="pill n">Básico</span>' : ''}</td><td class="n">${c.qtd}</td>
        <td class="n">${p(c.na_mao)}</td>${c.ate_turno.map(x => `<td class="n">${p(x)}</td>`).join('')}
        <td class="n">${p(c.alguma_premio)}</td><td class="n" style="${c.todas_premio >= 0.05 ? 'color:var(--bad);font-weight:600' : ''}">${p(c.todas_premio)}</td></tr>`).join('')}
    </tbody></table></div>
    <h3>Duas cartas juntas</h3>
    <div class="row"><select id="cb-a">${ordenadas.map(c => `<option>${esc(c.nome)}</option>`).join('')}</select>
      <span>e</span><select id="cb-b">${ordenadas.map((c, i) => `<option ${i === 1 ? 'selected' : ''}>${esc(c.nome)}</option>`).join('')}</select>
      <span id="cb-res" class="muted"></span></div>`;
  // el.querySelector, não $(): se a tela foi redesenhada enquanto as contas chegavam, os campos são os deste quadro
  const q = s => el.querySelector(s);
  const combo = async () => {
    const a = q('#cb-a').value, b = q('#cb-b').value;
    if (a === b) { q('#cb-res').textContent = 'Escolha duas cartas diferentes.'; return; }
    try { const c = await api(`/api/decks/${id}/combo?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
      q('#cb-res').innerHTML = `Na mão inicial: <b>${p(c.turnos[0])}</b> · até o 1º turno: <b>${p(c.turnos[1])}</b> · 2º: <b>${p(c.turnos[2])}</b> · 3º: <b>${p(c.turnos[3])}</b>`; }
    catch (e) { q('#cb-res').textContent = e.message; }
  };
  q('#cb-a').onchange = combo; q('#cb-b').onchange = combo;
  if (ordenadas.length > 1) combo();
}
