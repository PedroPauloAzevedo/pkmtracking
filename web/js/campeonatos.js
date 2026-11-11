/* =====================================================================
   CAMPEONATOS
   ===================================================================== */
async function renderMeta() {
  const vez = novaTela();
  await carregarTorneios();
  if (telaVelha(vez)) return;
  if (!S.torneios.filter(daFonte).length) { main.innerHTML = `${trilha()}<header><h1>Meta</h1></header>${seletorTorneios()}`; ligarSeletor(render); return; }
  const m = await api(`/api/meta?${qsTorneios()}&top=${S.top}&corte=${S.corte}`);
  const tend = await api(`/api/tendencia?k=8&${qsTorneios()}`);
  if (telaVelha(vez)) return;
  const maxPct = Math.max(...m.divisao.map(d => d.pct), 1);
  main.innerHTML = `
    ${trilha()}<header><h1>Meta</h1><p class="sub">Quanto cada deck aparece, quanto vence (sem contar mirrors) e quanto converte para o topo.</p></header>
    ${seletorTorneios()}
    ${quadroDispersao(m)}
    ${quadroCartoes(m)}
    <div class="row">
      <label class="label" for="m-top">Considerar</label>
      <select id="m-top">${[[0,'Todos os jogadores'],[512,'Top 512'],[256,'Top 256'],[128,'Top 128'],[64,'Top 64'],[32,'Top 32'],[16,'Top 16'],[8,'Top 8']].map(([v, t]) => `<option value="${v}" ${S.top == v ? 'selected' : ''}>${t}</option>`).join('')}</select>
      <label class="label" for="m-corte">Conversão para o</label>
      <select id="m-corte">${[8,16,32,64,128].map(v => `<option value="${v}" ${S.corte == v ? 'selected' : ''}>Top ${v}</option>`).join('')}</select>
      <span class="grow"></span><a class="btn" href="/exportar/meta.csv?${qsTorneios()}&top=${S.top}">Baixar para Excel</a>
    </div>
    <section class="panel">
      <p class="muted num">${m.jogadores_considerados} jogadores com deck conhecido${m.sem_deck ? `, ${m.sem_deck} sem deck informado` : ''}.</p>
      <div class="tabela alta"><table><thead><tr><th>Deck</th><th class="n">Jogadores</th><th>% do campo</th><th>Taxa de vitória</th><th class="n">V–D–E</th><th class="n">No Top ${m.corte}</th><th class="n">Conversão</th><th class="n" title="Pontos no suíço (3V + E) ÷ pontos possíveis; desistência conta como rodada perdida. Nos grandes eventos, só o Dia 1.">Aproveit.</th><th class="n" title="Participação no corte dividida pela participação no campo. Acima de 1 = converte melhor que a média.">Fator</th></tr></thead><tbody>
      ${m.divisao.map(d => `<tr class="clicavel" data-arq="${esc(d.arquetipo)}"><td><span class="cel-carta">${icones(d.arquetipo)}<b>${esc(d.nome)}</b></span></td><td class="n">${d.jogadores}</td>
        <td><div class="row" style="flex-wrap:nowrap"><div class="barra grow"><span style="width:${100 * d.pct / maxPct}%"></span></div><span class="num" style="width:52px;text-align:right">${pct(d.pct)}</span></div></td>
        <td>${taxaHtml(d)}</td><td class="n">${d.v}–${d.d}–${d.e}</td><td class="n">${d.no_corte}</td><td class="n">${pct(d.conversao)}</td><td class="n" title="${d.jogadores_aprov} jogadores; faixa provável ${fmt(d.aprov_baixo, 0)}–${fmt(d.aprov_alto, 0)}%">${pct(d.aproveitamento)}</td>
        <td class="n" style="${d.fator_conversao != null ? corTaxa(50 + (d.fator_conversao - 1) * 30) : ''}">${d.fator_conversao != null ? fmt(d.fator_conversao, 2) : '–'}</td></tr>`).join('')}
      </tbody></table></div>
    </section>
    <section class="panel"><h2>Tendência do meta</h2><p class="explica">Participação dos 8 decks mais jogados em cada torneio importado, em ordem de data. O ícone à direita marca onde cada linha termina; passe o mouse numa linha ou num ícone para destacar só aquele deck.</p>
      ${tend.torneios.length > 1 ? graficoLinhas(tend.series.map(s => ({ nome: s.nome, icone: (S.arq[s.arquetipo] ? S.arq[s.arquetipo].icones : [pokeId(s.arquetipo)])[0] || '', valores: tend.torneios.map(t => t.pct[s.arquetipo]) })), tend.torneios.map(t => (t.data || '').slice(5).split('-').reverse().join('/')), { max: Math.max(10, Math.ceil(Math.max(...tend.torneios.flatMap(t => Object.values(t.pct))) / 5) * 5), marcas: marcasEpoca(tend.torneios.map(t => t.data || ''), tipoMeta()) }) : '<p class="muted">Importe pelo menos dois torneios para ver a tendência.</p>'}
      ${tend.torneios.length > 1 && marcasEpoca(tend.torneios.map(t => t.data || ''), tipoMeta()).length ? `<p class="muted" style="font-size:.82rem">A linha tracejada marca onde uma coleção nova passou a valer ${S.fonte === 'grandes' ? 'nos grandes eventos' : 'nos torneios online'}: dali em diante o meta pode ser outro. Para ver uma época só, escolha em <b>Época</b>, acima.</p>` : ''}
    </section>
    <section class="panel" id="qual-deck"><h2>Qual deck jogar?</h2><p class="muted">Calculando…</p></section>`;
  ligarSeletor(render);
  desenharQualDeck();
  $('#m-top').onchange = e => { S.top = Number(e.target.value); render(); };
  $('#m-corte').onchange = e => { S.corte = Number(e.target.value); render(); };
  document.querySelectorAll('tr[data-arq], [data-arq].pt, .cartao-meta[data-arq]').forEach(el => el.onclick = () => { S.deck = el.dataset.arq; location.hash = 'deck'; });
  document.querySelectorAll('[data-eixo]').forEach(b => b.onclick = () => { S.metaEixo = b.dataset.eixo; render(); });
}

// ---- Visual inspirado no painel Indigo Plateau (v2026.11.11-1): cor de cada deck pelo tipo do Pokémon principal
// (campo "tipo" de /api/meta, tirado da biblioteca de cartas), dispersão "Quem vale a pena jogar" e cartões de participação.
const COR_TIPO = { Grass: '#4BA14B', Fire: '#E0703A', Water: '#3A86D0', Lightning: '#D9A514', Psychic: '#9B59C6', Fighting: '#C0653A',
  Darkness: '#4A4F6A', Metal: '#7C8C99', Dragon: '#B08A2E', Colorless: '#8A93A6', Fairy: '#D2649A' };
const corDeck = d => COR_TIPO[d.tipo] || 'var(--muted)';
const DECKS_QUADRO = 15;

// Cada deck é um ponto: x = % do campo (escala logarítmica, para separar os pequenos), y = a métrica escolhida: taxa de vitória sem
// mirrors, conversão para o corte ou aproveitamento no suíço (D-053). Linha vertical = mediana do % do campo dos decks mostrados;
// horizontal = a média do campo naquela métrica. Entram só decks com 20 partidas (taxa) ou 20 jogadores (conversão e aproveitamento):
// menos que isso a posição do ponto é quase só sorte.
const METRICAS_META = {
  taxa: { rotulo: 'Taxa de vitória', y: d => d.taxa, ok: d => d.taxa != null && d.n >= 20, minimo: '20 partidas',
    sobe: 'vence mais (sem contar mirrors)',
    media: (m) => { const v = m.divisao.reduce((a, d) => a + d.v, 0), n = m.divisao.reduce((a, d) => a + d.n, 0); return n ? 100 * v / n : 50; },
    textoMedia: r => `a taxa média do campo (${fmt(r, 1)}%; fica abaixo de 50% porque empate conta como não-vitória)`,
    dica: d => `Taxa de vitória: ${pct(d.taxa)}, faixa provável ${fmt(d.ic_baixo, 0)}–${fmt(d.ic_alto, 0)}%\n${d.v}–${d.d}–${d.e} em ${d.n} partidas, sem mirrors` },
  conversao: { rotulo: m => `Conversão para o Top ${m.corte}`, y: d => d.conversao, ok: d => d.conversao != null && d.jogadores >= 20, minimo: '20 jogadores',
    sobe: 'converte mais para o corte',
    media: (m) => { const c = m.divisao.reduce((a, d) => a + d.no_corte, 0), j = m.divisao.reduce((a, d) => a + d.jogadores, 0); return j ? 100 * c / j : 0; },
    textoMedia: r => `a conversão média do campo (${pct(r)})`,
    dica: (d, m) => `Conversão para o Top ${m.corte}: ${pct(d.conversao)} (${d.no_corte} jogadores)` },
  aprov: { rotulo: 'Aproveitamento no suíço', y: d => d.aproveitamento, ok: d => d.aproveitamento != null && d.jogadores_aprov >= 20, minimo: '20 jogadores',
    sobe: 'faz mais pontos no suíço',
    media: (m) => { let s = 0, n = 0; m.divisao.forEach(d => { if (d.aproveitamento != null) { s += d.aproveitamento * d.jogadores_aprov; n += d.jogadores_aprov; } }); return n ? s / n : 0; },
    textoMedia: r => `o aproveitamento médio do campo (${fmt(r, 1)}%)`,
    dica: d => `Aproveitamento no suíço: ${pct(d.aproveitamento)}, faixa provável ${fmt(d.aprov_baixo, 0)}–${fmt(d.aprov_alto, 0)}%\n${d.jogadores_aprov} jogadores (desistência conta como rodada perdida)` },
};
function quadroDispersao(m) {
  const chave = METRICAS_META[S.metaEixo] ? S.metaEixo : 'taxa', mt = METRICAS_META[chave];
  const rot = x => typeof x.rotulo === 'function' ? x.rotulo(m) : x.rotulo;
  const decks = m.divisao.slice(0, DECKS_QUADRO).filter(mt.ok);
  const pilulas = `<div class="chips-periodo" role="group" aria-label="Métrica"><span class="label">Métrica</span>
    ${Object.entries(METRICAS_META).map(([k, x]) => `<button data-eixo="${k}" aria-pressed="${k === chave}">${rot(x)}</button>`).join('')}</div>`;
  const cab = `<div class="cab-quadro"><h2>Quem vale a pena jogar</h2>${pilulas}</div>`;
  if (decks.length < 3) return `<section class="panel">${cab}<p class="muted">Poucos decks com ${mt.minimo} ou mais nesta seleção para desenhar o gráfico.</p></section>`;
  const yv = mt.y, refY = mt.media(m);
  const ps = decks.map(d => d.pct).sort((a, b) => a - b), med = ps[Math.floor(ps.length / 2)];
  const W = 1000, H = 600, L = 56, R = 24, T = 30, B = 48;
  const xMin = Math.log(Math.max(0.3, Math.min(...ps) * 0.8)), xMax = Math.log(Math.max(...ps) * 1.25);
  const ys = decks.map(yv).concat(refY), yMin = Math.floor((Math.min(...ys) - 2) / 2) * 2, yMax = Math.ceil((Math.max(...ys) + 2) / 2) * 2;
  const x = v => L + (Math.log(v) - xMin) / (xMax - xMin) * (W - L - R), y = v => T + (yMax - v) / (yMax - yMin) * (H - T - B);
  let g = `<rect class="quad" x="${x(med)}" y="${T}" width="${W - R - x(med)}" height="${Math.max(0, y(refY) - T)}" rx="8"/>`;
  const passo = Math.max(2, Math.ceil((yMax - yMin) / 6 / 2) * 2);
  for (let v = yMin; v <= yMax; v += passo) g += `<line class="grade" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke-dasharray="2 4"/><text class="rot" x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${v}%</text>`;
  g += `<line class="grade" x1="${L}" x2="${W - R}" y1="${y(refY)}" y2="${y(refY)}" style="stroke:var(--muted)"/>`;
  g += `<line class="grade" x1="${x(med)}" x2="${x(med)}" y1="${T}" y2="${H - B}" stroke-dasharray="5 4" style="stroke:var(--muted)"/>`;
  [0.5, 1, 2, 3, 5, 8, 12, 20, 30].filter(v => Math.log(v) >= xMin && Math.log(v) <= xMax).forEach(v => g += `<text class="rot" x="${x(v)}" y="${H - B + 18}" text-anchor="middle">${fmt(v, v < 1 ? 1 : 0)}%</text>`);
  g += `<text class="rot" x="${(W + L) / 2}" y="${H - 8}" text-anchor="middle">% do campo (escala logarítmica)</text>`;
  g += `<text x="${W - R - 10}" y="${T + 18}" text-anchor="end" style="fill:var(--good);font-size:12px;font-weight:700">Boas escolhas: populares e acima da média</text>`;
  g += `<text x="${L + 10}" y="${T + 18}" style="fill:var(--muted);font-size:12px;font-weight:700">Apostas: menos jogados, acima da média</text>`;
  // Cada deck: círculo meio transparente na cor do tipo, o Pokémon recortado no círculo sempre do mesmo tamanho e o nome logo
  // abaixo, centralizado (como no painel Indigo Plateau). Os decks menores são desenhados por último e ficam por cima.
  let nomes = '';
  const RP = 18, usados = [];
  // nome embaixo do círculo; só se encostar num nome já escrito vai para logo acima do mesmo círculo (continua colado nele)
  const yNome = (cx, cy, nome) => {
    const w = nome.length * 6.4 + 6;
    const bate = ly => usados.some(u => Math.abs(u.y - ly) < 14 && Math.abs(u.x - cx) < (u.w + w) / 2);
    const ly = !bate(cy + RP + 14) || bate(cy - RP - 6) ? cy + RP + 14 : cy - RP - 6;
    usados.push({ x: cx, y: ly, w });
    return ly;
  };
  [...decks].sort((a, b) => b.pct - a.pct).forEach((d, i) => {
    const cx = x(d.pct), cy = y(yv(d)), ic = (S.arq[d.arquetipo] ? S.arq[d.arquetipo].icones : [pokeId(d.arquetipo)])[0];
    const dica = `${d.nome}\n% do campo: ${pct(d.pct)} (${d.jogadores} jogadores)\n` + mt.dica(d, m);
    const cor = corDeck(d), clip = `rec-${i}`;
    g += `<g class="pt" data-arq="${esc(d.arquetipo)}"><title>${esc(dica)}</title>
      <clipPath id="${clip}"><circle cx="${cx}" cy="${cy}" r="${RP - 2}"/></clipPath>
      <circle cx="${cx}" cy="${cy}" r="${RP}" fill="${cor}" fill-opacity=".28" stroke="${cor}" stroke-width="2"/>
      ${ic ? `<image href="/icone/${encodeURIComponent(ic)}" x="${cx - RP + 3}" y="${cy - RP + 3}" width="${2 * RP - 6}" height="${2 * RP - 6}" preserveAspectRatio="xMidYMid meet" clip-path="url(#${clip})"/>` : ''}
    </g>`;
    nomes += `<text class="nome" x="${cx}" y="${yNome(cx, cy, d.nome)}" text-anchor="middle">${esc(d.nome)}</text>`;
  });
  g += nomes;  // nomes por último: nenhum círculo cobre um nome
  const extra = chave === 'aprov' ? ' Aproveitamento = pontos no suíço (3 por vitória, 1 por empate) ÷ pontos possíveis; quem desistiu perde as rodadas que faltaram, por isso nos torneios online (com muitas desistências) ele fica bem abaixo da taxa. Nos grandes eventos conta só o Dia 1, que todos jogam.' : '';
  return `<section class="panel">${cab}
    <p class="explica">Cada ponto é um deck: mais para a direita, mais jogado; mais para cima, ${mt.sobe}. A linha tracejada vertical é o % do campo mediano destes decks; a horizontal, ${mt.textoMedia(refY)}. Em cima à direita ficam as <b>boas escolhas</b> (muito testados e indo bem); em cima à esquerda, as <b>apostas</b> (vão bem, mas com pouca amostra). Passe o mouse num deck para ver os números; clique para abrir o perfil. Só entram decks com ${mt.minimo} ou mais.${extra}</p>
    <svg class="dispersao" viewBox="0 0 ${W} ${H}" role="img" aria-label="Gráfico de % do campo por ${esc(rot(mt).toLowerCase())}">${g}</svg></section>`;
}

// Cartões de participação: % do campo grande e, embaixo, a participação entre os jogadores do corte (▲ quando é maior: o deck converte bem).
function quadroCartoes(m) {
  if (!m.divisao.length) return '';
  const top = m.divisao.slice(0, DECKS_QUADRO), resto = m.divisao.slice(DECKS_QUADRO);
  const outros = resto.length ? { nome: `Outros (${resto.length} decks)`, pct: resto.reduce((a, d) => a + d.pct, 0), pct_corte: resto.reduce((a, d) => a + (d.pct_corte || 0), 0) } : null;
  const cartao = d => { const dif = (d.pct_corte ?? 0) - d.pct, seta = Math.abs(dif) < 0.05 ? '' : dif > 0 ? ' ▲' : ' ▼';
    return `<div class="cartao-meta" ${d.arquetipo ? `data-arq="${esc(d.arquetipo)}"` : ''} style="--cor:${d.arquetipo ? corDeck(d) : 'var(--muted)'}${d.arquetipo ? '' : ';cursor:default'}">
      <div class="t">${d.arquetipo ? icones(d.arquetipo) : ''}<span>${esc(d.nome)}</span></div><div class="v">${pct(d.pct)}</div>
      <div class="d">No Top ${m.corte}: <b style="color:${!seta ? 'var(--muted)' : dif > 0 ? 'var(--good)' : 'var(--bad)'}">${pct(d.pct_corte)}${seta}</b></div></div>`; };
  return `<section class="panel"><div class="cab-quadro"><h2>Participação no meta</h2></div>
    <p class="explica">Porcentagem dos jogadores com cada deck. Embaixo, a participação entre os jogadores do Top ${m.corte}: se for maior (▲), o deck está chegando ao corte mais do que o tamanho dele sugere. A faixa colorida segue o tipo do Pokémon principal.</p>
    <div class="cartoes-deck">${top.map(cartao).join('')}${outros ? cartao({ ...outros, pct: Math.round(outros.pct * 10) / 10, pct_corte: Math.round(outros.pct_corte * 10) / 10 }) : ''}</div></section>`;
}

// Meta > "Qual deck jogar?": taxa esperada contra o campo e equilíbrio do meta (tracker/estrategia.py).
async function desenharQualDeck() {
  const el = $('#qual-deck'); if (!el) return;
  let q; try { q = await api(`/api/qual-deck?${qsTorneios()}`); } catch (e) { el.innerHTML = `<h2>Qual deck jogar?</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  if (!q.decks.length) { el.innerHTML = '<h2>Qual deck jogar?</h2><p class="muted">Sem partidas com os dois decks conhecidos nesta fonte.</p>'; return; }
  el.innerHTML = `<h2>Qual deck jogar?</h2>
    <p class="sub">Para os ${q.decks.length} decks mais jogados, a taxa de vitória esperada contra o campo atual (cada confronto pesado pela presença do adversário).
      Confrontos com poucos jogos são completados pela força geral de cada deck, para não confiar em 3 ou 4 partidas. ${q.partidas.toLocaleString('pt-BR')} partidas.</p>
    <div class="tabela alta"><table><thead><tr><th>Deck</th><th class="n">% do campo</th><th class="n">Esperada contra o campo</th><th>Pior confronto</th>
      <th class="n" title="Mistura de decks que nenhum outro consegue explorar (teoria dos jogos)">No equilíbrio</th><th class="n" title="Taxa esperada se o campo jogasse a mistura de equilíbrio">Contra o equilíbrio</th></tr></thead><tbody>
      ${q.decks.map(d => `<tr class="clicavel" data-arq="${esc(d.arquetipo)}"><td><span class="cel-carta">${icones(d.arquetipo)}<b>${esc(nomeDeck(d.arquetipo))}</b></span></td>
        <td class="n">${pct(d.campo)}</td><td class="n" style="${corTaxa(d.esperada)}"><b>${pct(d.esperada)}</b></td>
        <td>${d.pior ? `${deckHtml(d.pior)} <span class="muted">${pct(d.pior_p)} · ${d.pior_n} jogos</span>` : ''}</td>
        <td class="n">${d.equilibrio ? pct(d.equilibrio) : '<span class="muted">0%</span>'}</td><td class="n">${pct(d.contra_equilibrio)}</td></tr>`).join('')}
    </tbody></table></div>
    <p class="muted" style="font-size:.85rem">"No equilíbrio" mostra a mistura de decks que nenhum outro deck consegue explorar. Um deck muito jogado com 0% ali está sendo superestimado pelo campo; um pouco jogado com peso alto pode ser uma boa surpresa. São estimativas a partir dos campeonatos importados, não garantias.</p>`;
  el.querySelectorAll('tr[data-arq]').forEach(tr => tr.onclick = () => { S.deck = tr.dataset.arq; location.hash = 'deck'; });
}

// Perfil de deck > Versões pela ACE SPEC (tracker/variantes.py): tabela de cada ACE SPEC e as versões do deck.
async function desenharVariantes(arq) {
  const alvo = $('#variantes') || (() => { const s = document.createElement('section'); s.className = 'panel'; s.id = 'variantes'; main.appendChild(s); return s; })();
  alvo.innerHTML = '<h2>ACE SPEC e versões</h2><p class="muted">Separando as listas…</p>';
  let v; try { v = await api(`/api/variantes/${encodeURIComponent(arq)}?${qsTorneios()}`); } catch (e) { alvo.innerHTML = `<h2>ACE SPEC e versões</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  if (S.deck !== arq || !$('#variantes')) return;
  if (!v.listas) { alvo.innerHTML = '<h2>ACE SPEC e versões</h2><p class="muted">Nenhuma lista importada deste deck.</p>'; return; }
  const marca = g => g.diferenca ? ` <span class="pill ${g.taxa >= (v.aces.reduce((a, x) => a + x.v, 0) / Math.max(1, v.aces.reduce((a, x) => a + x.n, 0)) * 100) ? 'v' : 'd'}" title="A taxa desta escolha é diferente do resto do deck com p = ${g.p_valor}: dificilmente é sorte">diferença provável</span>` : '';
  alvo.innerHTML = `<h2>ACE SPEC e versões</h2>
    <p class="sub">Cada deck leva 1 ACE SPEC, e essa escolha costuma definir a versão. ${v.listas} listas deste deck.</p>
    <div class="tabela"><table><thead><tr><th>ACE SPEC</th><th class="n">Listas</th><th class="n">% do deck</th><th>Taxa de vitória</th><th class="n">V–D–E</th></tr></thead><tbody>
      ${v.aces.map(a => `<tr><td><b>${esc(a.ace)}</b>${marca(a)}</td><td class="n">${a.listas}</td><td class="n">${pct(a.pct)}</td><td>${taxaHtml(a)}</td><td class="n">${a.v}–${a.d}–${a.e}</td></tr>`).join('')}
    </tbody></table></div>
    ${v.grupos.length ? `<h3>Versões</h3>
      <p class="muted" style="font-size:.85rem">ACE SPEC usadas por poucas listas entram na versão com o resto da lista mais parecido; duas ACE SPEC com listas quase iguais viram uma versão só.</p>
      <div class="grid2">${v.grupos.map(g => `<div class="panel" style="padding:12px;gap:6px">
        <div class="row"><b class="grow">${esc(g.aces[0].ace)}${g.aces.length > 1 ? ` <span class="muted" style="font-weight:400">+ ${g.aces.slice(1).map(a => `${esc(a.ace)} (${a.listas})`).join(', ')}</span>` : ''}</b><span class="muted">${g.listas} listas</span></div>
        <div>${taxaHtml(g)} <span class="muted">${g.v}–${g.d}–${g.e}</span>${marca(g)}</div>
        <ul style="margin:0;padding-left:18px;font-size:.88rem">${g.marcas.map(m => `<li>${esc(m.carta)}: <b>${fmt(m.media, 1)}</b> cópias <span class="muted">(média do deck ${fmt(m.geral, 1)})</span></li>`).join('')}</ul></div>`).join('')}</div>`
      : `<p class="muted">${v.aces.length > 1 ? 'Uma versão principal: as outras ACE SPEC são usadas por poucas listas (veja a tabela acima).' : 'Todas as listas usam a mesma ACE SPEC.'}</p>`}
    <p class="muted" style="font-size:.85rem">"Diferença provável": a taxa daquela escolha é diferente da do resto do deck com menos de 5% de chance de ser só sorte. Com várias ACE SPEC comparadas ao mesmo tempo, uma ou outra pode aparecer por acaso; confira o número de jogos.</p>`;
}

async function renderMatchups() {
  const vez = novaTela();
  await carregarTorneios();
  if (telaVelha(vez)) return;
  if (!S.torneios.filter(daFonte).length) { main.innerHTML = `${trilha()}<header><h1>Matchups</h1></header>${seletorTorneios()}`; ligarSeletor(render); return; }
  S.k = S.k || 12; S.minMu = S.minMu ?? 10;
  const m = await api(`/api/meta?${qsTorneios()}&top=${S.top}&k=${S.k}&min=${S.minMu}`);
  if (telaVelha(vez)) return;
  main.innerHTML = `
    ${trilha()}<header><h1>Matchups</h1><p class="sub">Leia pela linha: taxa de vitória do deck da linha contra o deck da coluna.</p></header>
    ${seletorTorneios()}
    <div class="row">
      <label class="label" for="mu-k">Decks na tabela</label><select id="mu-k">${[6,8,10,12,15,20].map(v => `<option ${S.k == v ? 'selected' : ''}>${v}</option>`).join('')}</select>
      <div class="chips-periodo" role="group" aria-label="Taxa"><span class="label">Taxa</span><button data-mu="real" aria-pressed="${S.muTipo !== 'ajustada'}">Real</button><button data-mu="ajustada" aria-pressed="${S.muTipo === 'ajustada'}">Ajustada (estimativa)</button></div>
      <label class="label" for="mu-min">Mínimo de partidas</label><select id="mu-min">${[0,5,10,20,50].map(v => `<option ${S.minMu == v ? 'selected' : ''}>${v}</option>`).join('')}</select>
      <span class="grow"></span><a class="btn" href="/exportar/torneios.csv">Baixar partidas dos torneios</a>
    </div>
    ${S.muTipo === 'ajustada' ? '<p class="muted" style="font-size:.85rem">Taxa ajustada: com muitos jogos vale o resultado real do confronto; com poucos, ele é completado pela força geral de cada deck contra todo o campo. Prevê os torneios seguintes melhor que a taxa real (testado). Passe o mouse para ver a taxa real.</p>' : ''}
    <section class="panel"><div class="cab-quadro"><h2>Mapa de confrontos</h2><span class="legenda-calor"><span>desfavorável</span><span class="barra-cor"></span><span>favorável</span></span></div>
      <p class="explica">Linha = deck analisado, coluna = adversário. Quanto mais longe de 50%, mais forte a cor. ${S.muTipo === 'ajustada' ? '' : `Confrontos com menos de ${S.minMu} partidas aparecem como “—” (passe o mouse para ver mesmo assim). `}O número pequeno é a quantidade de partidas; passe o mouse para ver V–D–E.</p>
      <div class="tabela"><table class="matriz">
      <thead><tr><th></th>${m.colunas.map(c => `<th>${icones(c.arquetipo)}<br>${esc(c.nome)}</th>`).join('')}</tr></thead>
      <tbody>${m.matriz.map(l => `<tr><td class="cab"><span class="cel-carta">${icones(l.arquetipo)}${esc(l.nome)}</span></td>${l.celulas.map((c, i) => c.espelho ? '<td class="espelho">mirror</td>'
        : S.muTipo === 'ajustada'
          ? `<td style="${corCalor(c.ajustada)}" title="${esc(l.nome)} contra ${esc(m.colunas[i].nome)}: ajustada ${pct(c.ajustada)}; real ${c.n ? pct(c.taxa) : '–'} em ${c.n} partidas (${c.v}-${c.d}-${c.e})">${pct(c.ajustada)}<small>${c.n || ''}</small></td>`
          : c.pouco || !c.n ? `<td class="pouco" title="${esc(l.nome)} contra ${esc(m.colunas[i].nome)}: ${c.n ? `${pct(c.taxa)}, ${c.v}-${c.d}-${c.e}` : 'sem partidas'} (${c.n} partidas: poucas para confiar)">—<small>${c.n || ''}</small></td>`
          : `<td style="${corCalor(c.taxa)}" title="${esc(l.nome)} contra ${esc(m.colunas[i].nome)}: ${c.v}-${c.d}-${c.e} (${c.n} partidas); faixa provável ${fmt(c.ic_baixo, 0)}–${fmt(c.ic_alto, 0)}%">${pct(c.taxa)}<small>${c.n}</small></td>`).join('')}</tr>`).join('')}</tbody>
    </table></div></section>`;
  ligarSeletor(render);
  $('#mu-k').onchange = e => { S.k = Number(e.target.value); render(); };
  $('#mu-min').onchange = e => { S.minMu = Number(e.target.value); render(); };
  document.querySelectorAll('[data-mu]').forEach(b => b.onclick = () => { S.muTipo = b.dataset.mu; render(); });
}
// Mapa de calor: mais forte quanto mais longe de 50% (satura em 25 pontos de distância), mais intenso que o corTaxa das tabelas.
function corCalor(taxa) {
  if (taxa == null) return '';
  const d = Math.max(-25, Math.min(25, taxa - 50)) / 25;
  return `background: color-mix(in srgb, ${d >= 0 ? 'var(--good)' : 'var(--bad)'} ${Math.round(8 + Math.abs(d) * 67)}%, var(--surface)); font-weight: 600;`;
}

async function renderDeck() {
  const vez = novaTela();
  await carregarTorneios();
  if (telaVelha(vez)) return;
  if (!S.torneios.filter(daFonte).length) { main.innerHTML = `${trilha()}<header><h1>Perfil de deck</h1></header>${seletorTorneios()}`; ligarSeletor(render); return; }
  const m = await api(`/api/meta?${qsTorneios()}`);
  if (!S.deck || !m.divisao.some(d => d.arquetipo === S.deck)) S.deck = m.divisao[0]?.arquetipo || '';
  const p = S.deck ? await api(`/api/deck/${encodeURIComponent(S.deck)}?${qsTorneios()}`) : null;
  if (telaVelha(vez)) return;
  main.innerHTML = `
    ${trilha()}<header><h1>Perfil de deck</h1><p class="sub">Participação, matchups contra o campo, colocações e esqueleto da lista.</p></header>
    ${seletorTorneios()}
    <div class="row"><label class="label" for="p-deck">Deck</label>
      <select id="p-deck">${m.divisao.map(d => `<option value="${esc(d.arquetipo)}" ${d.arquetipo === S.deck ? 'selected' : ''}>${esc(d.nome)} (${pct(d.pct)})</option>`).join('')}</select></div>
    ${p ? `
    <div class="row perfil-topo" style="align-items:flex-start;gap:16px;flex-wrap:nowrap">
    <img src="${imgNome(p.carta_capa || p.nome, true)}" alt="${esc(p.nome)}" style="width:150px;border-radius:9px;flex:none" onerror="this.hidden=true">
    <div class="kpis grow" style="grid-template-columns:repeat(2,minmax(0,1fr))">
      <div class="kpi"><span class="label">Jogadores</span><span class="v">${p.jogadores}</span><span class="d">${pct(p.pct)} do campo</span></div>
      <div class="kpi"><span class="label">Taxa esperada contra o campo</span><span class="v">${pct(p.taxa_esperada)}</span><span class="d">matchups ponderados pela presença de cada deck</span></div>
      <div class="kpi"><span class="label">No Top 8</span><span class="v">${p.colocacoes['Top 8']}</span><span class="d">${p.colocacoes['Top 32']} no Top 32</span></div>
      <div class="kpi"><span class="label">Listas analisadas</span><span class="v">${p.listas}</span><span class="d">importadas do Labs</span></div>
    </div></div>
    <section class="panel"><h2>Matchups contra o campo</h2>
      <div class="tabela alta"><table><thead><tr><th>Contra</th><th class="n">% do campo</th><th>Taxa de vitória</th><th></th><th class="n">V–D–E</th></tr></thead><tbody>
      ${p.spread.filter(s => s.n).map(s => `<tr><td><span class="cel-carta">${icones(s.arquetipo)}${esc(s.nome)}</span>${s.arquetipo === p.arquetipo ? ' <span class="muted">(mirror)</span>' : ''}</td><td class="n">${pct(s.pct_campo)}</td><td>${taxaHtml(s)}</td><td style="width:28%">${barraDivergente(s.taxa)}</td><td class="n">${s.v}–${s.d}–${s.e}</td></tr>`).join('')}
      </tbody></table></div></section>
    <div class="grid2">
      <section class="panel"><h2>Melhores colocações</h2>
        <div class="tabela"><table><thead><tr><th class="n">Pos.</th><th>Jogador</th><th>Torneio</th><th>ACE SPEC</th><th class="n">V–D–E</th></tr></thead><tbody>
        ${p.melhores.map(j => `<tr><td class="n">${j.posicao}</td><td>${esc(j.nome)}</td><td class="muted">${esc((S.torneios.find(t => t.id === j.torneio) || {}).nome || j.torneio)}</td><td>${j.ace_spec == null ? '<span class="muted">sem lista</span>' : j.ace_spec ? esc(j.ace_spec) : '<span class="muted">nenhuma</span>'}</td><td class="n">${j.v}–${j.d}–${j.e}</td></tr>`).join('')}
        </tbody></table></div></section>
      <section class="panel"><h2>Presença por torneio</h2>
        ${p.por_torneio.length > 1 ? graficoLinhas([{ nome: p.nome, valores: p.por_torneio.map(t => t.pct), cor: 'var(--p1)' }], p.por_torneio.map(t => (t.data || '').slice(5).split('-').reverse().join('/')), { max: Math.max(10, Math.ceil(Math.max(...p.por_torneio.map(t => t.pct)) / 5) * 5), marcas: marcasEpoca(p.por_torneio.map(t => t.data || ''), tipoMeta()) }) : '<p class="muted">Importe mais torneios para ver a evolução.</p>'}
        <table><tbody>${Object.entries(p.colocacoes).map(([k, v]) => `<tr><td>${k}</td><td class="n">${v}</td></tr>`).join('')}</tbody></table>
      </section>
    </div>
    <section class="panel" id="p-base"></section>
    <section class="panel" id="p-inov"></section>
    <section class="panel" id="p-listas"></section>
    <section class="panel"><h2>Esqueleto da lista</h2>
      ${p.esqueleto.length ? tabelaCartas(p.esqueleto) : '<p class="muted">Nenhuma lista importada para este deck. Ao importar um torneio, escolha quantas listas do topo baixar.</p>'}
    </section>` : ''}`;
  ligarSeletor(render);
  if (S.deck) { desenharVariantes(S.deck); desenharListas(S.deck); desenharListaBase(S.deck); desenharInovacoes(S.deck); }
  $('#p-deck').onchange = e => { S.deck = e.target.value; render(); };
}

// Perfil de deck > Lista base (D-053): cada lista pesa os pontos do jogador (3V + E), então quem foi mais longe pesa mais.
async function desenharListaBase(arq) {
  const el = $('#p-base'); if (!el) return;
  el.innerHTML = '<h2>Lista base</h2><p class="muted">Calculando…</p>';
  let b; try { b = await api(`/api/lista-base/${encodeURIComponent(arq)}?${qsTorneios()}`); } catch (e) { el.innerHTML = `<h2>Lista base</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  if (S.deck !== arq || !document.body.contains(el)) return;
  const tab = (xs, vazio) => xs.length ? `<div class="tabela"><table><thead><tr><th class="n">Cópias</th><th>Carta</th><th>Peso</th><th class="n">Listas</th></tr></thead><tbody>
    ${xs.map(c => `<tr><td class="n"><b>${c.copias}</b></td><td><span class="cel-carta">${mini(c.carta)}${esc(c.carta)}</span></td>
      <td><div class="row" style="flex-wrap:nowrap"><div class="barra grow"><span style="width:${c.peso}%"></span></div><span class="num" style="width:52px;text-align:right">${pct(c.peso)}</span></div></td><td class="n">${c.listas}</td></tr>`).join('')}</tbody></table></div>` : `<p class="muted">${vazio}</p>`;
  const total = b.nucleo.reduce((a, c) => a + c.copias, 0);
  el.innerHTML = `<div class="cab-quadro"><h2>Lista base</h2><span class="muted" style="font-size:.85rem">${b.listas} listas</span></div>
    <p class="explica">Cada lista pesa os pontos que o jogador fez no torneio (3 por vitória, 1 por empate): uma 10-3-1 pesa quase o dobro de uma 5-4-0, e lista sem pontos não pesa. <b>Núcleo</b> = carta em pelo menos 75% do peso; <b>opções</b> = de 10% a 75%. Cópias = a quantidade mais comum (pesada) entre as listas que usam a carta; versões diferentes da mesma carta contam juntas. São só as listas do topo de cada torneio (as que o Limitless publica e o Coletor baixa).</p>
    ${b.listas < b.minimo ? `<p class="muted">Precisa de pelo menos ${b.minimo} listas deste deck na seleção.</p>` : `<div class="grid2">
      <div><h3>Núcleo <span class="muted" style="font-weight:400">(${total} cartas)</span></h3>${tab(b.nucleo, 'Nenhuma carta em 75% do peso.')}</div>
      <div><h3>Opções</h3>${tab(b.opcoes, 'Nenhuma carta entre 10% e 75% do peso.')}</div></div>`}`;
}

// Perfil de deck > Mudanças nas listas (D-053): inovações (últimas 2 semanas × 4 semanas antes) e estabilidade da lista média.
async function desenharInovacoes(arq) {
  const el = $('#p-inov'); if (!el) return;
  el.innerHTML = '<h2>Mudanças nas listas</h2><p class="muted">Comparando os períodos…</p>';
  let r; try { r = await api(`/api/inovacoes/${encodeURIComponent(arq)}?${qsTorneios()}`); } catch (e) { el.innerHTML = `<h2>Mudanças nas listas</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  if (S.deck !== arq || !document.body.contains(el)) return;
  const dm = s => s ? s.slice(8, 10) + '/' + s.slice(5, 7) : '';
  const per = r.periodos, est = r.estabilidade;
  const estHtml = !est ? `<p class="muted" style="font-size:.85rem">Estabilidade: precisa de 15 listas em cada período.</p>`
    : `<div class="kpis" style="grid-template-columns:repeat(3,minmax(0,1fr))">
        <div class="kpi"><span class="label">Lista média mudou</span><span class="v">${fmt(est.mudou, 1)}</span><span class="d">cartas entre os dois períodos</span></div>
        <div class="kpi"><span class="label">Variação natural</span><span class="v">${fmt(est.ruido, 1)}</span><span class="d">o que muda só por serem jogadores diferentes</span></div>
        <div class="kpi"><span class="label">Além do ruído</span><span class="v" style="color:${est.estavel ? 'var(--good)' : 'var(--accent)'}">${fmt(Math.max(0, est.alem_do_ruido), 1)}</span><span class="d">${est.estavel ? 'lista <b>estável</b> (menos de 1 carta)' : 'a lista <b>está mudando</b>'}</span></div></div>`;
  const pac = p => `<div class="panel" style="padding:12px;gap:6px;background:var(--sunken)">
      <div class="row"><b class="grow">${p.mudancas.length > 1 ? `Pacote de ${p.mudancas.length} mudanças` : 'Mudança'}</b><span class="muted" style="font-size:.85rem">${p.listas} listas recentes com tudo junto</span></div>
      ${p.mudancas.map(x => `<div class="row" style="gap:8px"><span class="cel-carta">${mini(x.carta)}<b>${esc(x.carta)}</b></span>
        <span>${x.op === '<' ? `cortou para menos de ${x.k}` : `${x.k}+ cópias`} <span class="muted">(${x.de} → ${x.para})</span></span>
        <span class="grow"></span><span class="num">${pct(x.antes)} → <b>${pct(x.agora)}</b> das listas</span>
        <span class="num muted" title="Aproveitamento por partida das listas recentes com a mudança × sem ela">aprov. ${pct(x.aprov_com)} × ${pct(x.aprov_sem)}</span></div>`).join('')}</div>`;
  el.innerHTML = `<div class="cab-quadro"><h2>Mudanças nas listas</h2>${per ? `<span class="muted" style="font-size:.85rem">${dm(per.recente_de)}–${dm(per.recente_ate)} (${r.listas_recentes} listas) × ${dm(per.antes_de)}–${dm(per.antes_ate)} (${r.listas_antes} listas)</span>` : ''}</div>
    <p class="explica">Compara as listas das últimas 2 semanas da seleção com as das 4 semanas antes. Uma mudança aparece quando: ficou pelo menos 25 pontos mais comum, com teste rigoroso (cada deck testa centenas de cartas e contagens, então só passa o que dificilmente é acaso); as listas com ela fizeram mais pontos por partida do que as sem ela (deu resultado, não é só moda); e pelo menos 5 listas a têm. Mudanças que aparecem nas mesmas listas formam um pacote. A estabilidade diz quantas cartas a lista média mudou além do que muda só por serem jogadores diferentes (sorteio das listas, 200 vezes).</p>
    ${estHtml}
    ${r.motivo ? `<p class="muted">Sem comparação: ${esc(r.motivo)}.</p>` : r.pacotes.length ? r.pacotes.map(pac).join('') : '<p class="muted">Nenhuma mudança passou nos critérios: a lista do deck está parecida com a das semanas anteriores.</p>'}
    <p class="muted" style="font-size:.8rem">São só as listas do topo de cada torneio: mostram o que quem foi bem mudou, não o deck inteiro.</p>`;
}

// Perfil de deck > Listas: as listas de torneio mais recentes do deck, completas, com link do Limitless e "Copiar" no formato que o
// TCG Live importa. Busca por cartas: só as listas que têm TODAS as cartas escolhidas (ex.: Mega Rayquaza com Unfair Stamp e Tapu
// Koko ex). S.listasCom guarda as cartas escolhidas de cada deck.
S.listasCom = S.listasCom || {};
function textoListaTCGLive(l) {
  const grupos = [['Pokémon', 'Pokémon'], ['Treinador', 'Trainer'], ['Energia', 'Energy']];
  return grupos.map(([sec, rot]) => { const cs = l.cartas.filter(c => c.secao === sec); if (!cs.length) return '';
    return `${rot}: ${cs.reduce((a, c) => a + c.qtd, 0)}\n` + cs.map(c => `${c.qtd} ${c.carta}${c.set ? ` ${c.set} ${c.numero}` : ''}`).join('\n'); })
    .filter(Boolean).join('\n\n') + `\n\nTotal Cards: ${l.total_cartas}`;
}
async function desenharListas(arq, limite = 20) {
  const el = $('#p-listas'); if (!el) return;
  const com = S.listasCom[arq] || [];
  el.innerHTML = '<h2>Listas</h2><p class="muted">Buscando as listas…</p>';
  const qs = [qsTorneios(), ...com.map(c => 'com=' + encodeURIComponent(c)), 'limite=' + limite].join('&');
  let r; try { r = await api(`/api/deck/${encodeURIComponent(arq)}/listas?${qs}`); } catch (e) { el.innerHTML = `<h2>Listas</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  if (S.deck !== arq || !$('#p-listas')) return;
  const secoes = l => ['Pokémon', 'Treinador', 'Energia'].map(sec => { const cs = l.cartas.filter(c => c.secao === sec); if (!cs.length) return '';
    return `<div><span class="label">${sec} · ${cs.reduce((a, c) => a + c.qtd, 0)}</span>${cs.map(c => `<div class="lista-linha"><b>${c.qtd}</b> <span class="cel-carta">${mini(c.carta, c.carta_id)}${esc(c.carta)}</span> <span class="muted">${esc(c.set)} ${esc(c.numero)}</span></div>`).join('')}</div>`; }).join('');
  el.innerHTML = `<h2>Listas</h2>
    <p class="sub">As listas de torneio deste deck, das mais recentes para as mais antigas, com todas as cartas. Para achar uma combinação, junte cartas abaixo: aparecem só as listas que têm todas elas.</p>
    <div class="row" style="gap:8px">
      <label class="label" for="l-carta">Com as cartas</label>
      <input id="l-carta" list="l-sugestoes" placeholder="Digite uma carta e aperte Enter" style="width:260px" autocomplete="off">
      <datalist id="l-sugestoes">${r.cartas.map(c => `<option value="${esc(c)}">`).join('')}</datalist>
      <button id="l-add">Adicionar</button>
      ${com.map((c, i) => `<button class="chip" data-tirar="${i}" title="Tirar esta carta da busca">${esc(c)} ✕</button>`).join('')}
      ${com.length ? '<button id="l-limpar">Limpar</button>' : ''}
    </div>
    <p class="muted num">${com.length ? `<b>${r.achadas}</b> de ${r.total} listas têm ${com.map(esc).join(' + ')}.` : `${r.total} listas deste deck nos torneios escolhidos.`}</p>
    ${r.listas.length ? `<div class="listas-deck">${r.listas.map((l, i) => `<details class="lista-deck">
      <summary><span class="num">${fmtData(l.data)}</span> <b>${l.posicao ? l.posicao + 'º' : '–'}</b>${l.jogadores_torneio ? `<span class="muted"> de ${l.jogadores_torneio}</span>` : ''} · ${esc(l.jogador)} <span class="muted">· ${esc(l.torneio_nome)} · ${l.v ?? 0}–${l.d ?? 0}–${l.e ?? 0}</span></summary>
      <div class="row" style="gap:8px;margin:8px 0"><button data-copiar="${i}">Copiar lista (TCG Live)</button>${l.link ? `<a class="btn" href="${esc(l.link)}" target="_blank" rel="noopener">Abrir no Limitless ↗</a>` : ''}</div>
      <div class="lista-secoes">${secoes(l)}</div></details>`).join('')}</div>
      ${r.achadas > r.listas.length ? `<div class="row"><button id="l-mais">Mostrar mais (${r.achadas - r.listas.length} restantes)</button></div>` : ''}`
      : `<p class="muted">${com.length ? 'Nenhuma lista com essa combinação de cartas.' : 'Nenhuma lista importada deste deck. Ao importar um torneio, escolha quantas listas do topo baixar.'}</p>`}`;
  const adicionar = () => { const v = el.querySelector('#l-carta').value.trim(); if (!v) return;
    S.listasCom[arq] = [...com.filter(c => c.toLowerCase() !== v.toLowerCase()), v]; desenharListas(arq); };
  el.querySelector('#l-add').onclick = adicionar;
  el.querySelector('#l-carta').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); adicionar(); } };
  el.querySelectorAll('[data-tirar]').forEach(b => b.onclick = () => { S.listasCom[arq] = com.filter((_, i) => i !== Number(b.dataset.tirar)); desenharListas(arq); });
  if (el.querySelector('#l-limpar')) el.querySelector('#l-limpar').onclick = () => { S.listasCom[arq] = []; desenharListas(arq); };
  if (el.querySelector('#l-mais')) el.querySelector('#l-mais').onclick = () => desenharListas(arq, limite + 30);
  el.querySelectorAll('[data-copiar]').forEach(b => b.onclick = async () => {
    try { await navigator.clipboard.writeText(textoListaTCGLive(r.listas[Number(b.dataset.copiar)])); toast('Lista copiada: no TCG Live, Decks > Importar'); }
    catch (e) { toast('Não consegui copiar a lista'); } });
}

// Uso de cartas > Efeito de cada carta: regressão logística com o confronto como ponto de partida (tracker/regressao.py).
async function desenharEfeitoCartas(arq) {
  const el = $('#efeito-cartas'); if (!el) return;
  let r; try { r = await api(`/api/efeito-cartas?${qsTorneios()}&arq=${encodeURIComponent(arq)}`); }
  catch (e) { el.innerHTML = `<h2>Efeito de cada carta</h2><p class="aviso erro">${esc(e.message)}</p>`; return; }
  const sinal = x => (x > 0 ? '+' : '') + fmt(x, 1);
  const intro = `<h2>Efeito de cada carta</h2>
    <p class="sub">Com os mesmos confrontos, quanto <b>uma cópia a mais</b> de cada carta muda a chance de vencer uma partida, a partir do número de cópias mais comum. Diferente de "Vitória com / sem" acima, a conta desconta os adversários que cada lista enfrentou e as outras cartas que costumam vir junto. Com poucos jogos, o efeito fica perto de zero de propósito: só aparece o que os dados sustentam.</p>`;
  if (!r.cartas.length) { el.innerHTML = intro + `<p class="muted">${esc(r.aviso || 'Nenhuma carta muda de número de cópias em listas suficientes deste deck.')}</p>`; return; }
  const provaveis = r.cartas.filter(c => c.provavel).length;
  el.innerHTML = intro + `
    <p class="muted">${r.listas} listas e ${r.partidas} partidas. Este deck venceu ${fmt(r.taxa_real, 1)}% das partidas; pelos confrontos que enfrentou, o esperado era ${fmt(r.taxa_pelos_confrontos, 1)}%.
      ${r.taxa_real - r.taxa_pelos_confrontos > 10 ? 'A diferença vem, em boa parte, de as listas importadas serem das melhores colocações (quem tem lista costuma ter vencido mais); a conta compara as listas entre si, então isso não vira efeito de carta.' : ''}
      ${provaveis ? `<b>${provaveis}</b> carta(s) com efeito provável.` : 'Nenhuma carta com efeito provável: com estes dados, as variações das listas não mudam o resultado de forma que dê para separar da sorte.'}</p>
    <div class="tabela alta"><table><thead><tr><th>Carta</th><th class="n">Cópias mais comuns</th><th class="n">Listas com outro número</th><th title="Listas com cada número de cópias">Cópias: listas</th><th class="n">Efeito por cópia a mais</th><th class="n">Faixa provável</th></tr></thead><tbody>
    ${r.cartas.map(c => `<tr><td><span class="cel-carta">${mini(c.carta)}${esc(c.carta)}</span>${c.provavel ? ' <span class="pill v" title="O efeito é maior que duas vezes a incerteza: dificilmente é sorte (ainda assim é associação, não prova)">efeito provável</span>' : ''}</td>
      <td class="n">${c.comum}</td><td class="n">${c.fora_do_comum}</td>
      <td class="num" style="font-size:.8rem">${Object.entries(c.distribuicao).map(([q, n]) => `<span style="white-space:nowrap"><b>${q}×</b> ${n}</span>`).join(' · ')}</td>
      <td class="n" style="${c.provavel ? `color:${c.efeito_pp > 0 ? 'var(--good)' : 'var(--bad)'};font-weight:600` : ''}">${sinal(c.efeito_pp)} p.p.</td>
      <td class="n muted">${sinal(c.faixa_pp[0])} a ${sinal(c.faixa_pp[1])}</td></tr>`).join('')}
    </tbody></table></div>
    <p class="muted" style="font-size:.85rem">p.p. = pontos percentuais na taxa de vitória. Leia como associação, não como prova: quem escolhe uma carta pode também ser um jogador mais forte. O freio da conta foi escolhido medindo a previsão em torneios novos (testes/experimentos/e10_regressao_cartas.py).</p>`;
}

function tabelaCartas(cartas) {
  return `<div class="tabela alta"><table><thead><tr><th>Carta</th><th class="n">% das listas</th><th class="n">Média de cópias</th><th title="Para cada número de cópias: quantas listas e a taxa de vitória delas (0× = listas sem a carta)">Cópias: listas (vitória)</th><th class="n">Vitória com</th><th class="n">Vitória sem</th></tr></thead><tbody>
    ${cartas.map(c => `<tr><td><span class="cel-carta">${mini(c.carta, c.carta_id)}${esc(c.carta)}</span></td><td class="n">${pct(c.pct)}</td><td class="n">${fmt(c.media_copias, 2)}</td>
      <td class="num" style="font-size:.8rem">${Object.entries(c.por_copias || {}).map(([q, x]) => `<span title="${x.listas} listas com ${q} cópia(s)" style="white-space:nowrap"><b>${q}×</b> ${x.listas} <span style="${x.taxa != null ? 'color:' + (x.taxa >= 50 ? 'var(--good)' : 'var(--bad)') : ''}">(${pct(x.taxa)})</span></span>`).join(' · ')}</td>
      <td class="n">${pct(c.taxa_com)}</td><td class="n">${pct(c.taxa_sem)}</td></tr>`).join('')}
  </tbody></table></div>`;
}

async function renderCartas() {
  const vez = novaTela();
  await carregarTorneios();
  if (telaVelha(vez)) return;
  if (!S.torneios.filter(daFonte).length) { main.innerHTML = `${trilha()}<header><h1>Cartas</h1></header>${seletorTorneios()}`; ligarSeletor(render); return; }
  const m = await api(`/api/meta?${qsTorneios()}`);
  const c = await api(`/api/cartas?${qsTorneios()}&arq=${encodeURIComponent(S.deckCartas || '')}`);
  if (telaVelha(vez)) return;
  const com = S.torneios.filter(t => t.qtd_listas);
  main.innerHTML = `
    ${trilha()}<header><h1>Cartas</h1><p class="sub">Quanto cada carta é usada e o desempenho de quem a usa ("Vitória com") contra quem não usa ("Vitória sem"). Diferença grande pode ser sinal, mas não prova causa.</p></header>
    ${seletorTorneios()}
    <div class="row"><label class="label" for="c-deck">Deck</label>
      <select id="c-deck"><option value="">Todos os decks</option>${m.divisao.map(d => `<option value="${esc(d.arquetipo)}" ${d.arquetipo === S.deckCartas ? 'selected' : ''}>${esc(d.nome)}</option>`).join('')}</select>
      <span class="muted num">${c.listas} listas</span></div>
    <section class="panel">${c.cartas.length ? tabelaCartas(c.cartas) : '<p class="muted">Nenhuma lista importada. Ao importar um torneio, deixe "listas do topo" maior que zero.</p>'}</section>
    ${S.deckCartas ? '<section class="panel" id="efeito-cartas"><h2>Efeito de cada carta</h2><p class="muted">Calculando…</p></section>' : ''}
    <section class="panel"><h2>Comparar duas listas</h2>
      ${com.length ? `<div class="grid2">
        <div class="row"><select id="cmp-ta">${com.map(t => `<option value="${t.id}">${esc(t.nome)}</option>`).join('')}</select><select id="cmp-ia" class="grow"></select></div>
        <div class="row"><select id="cmp-tb">${com.map(t => `<option value="${t.id}">${esc(t.nome)}</option>`).join('')}</select><select id="cmp-ib" class="grow"></select></div>
      </div><div class="row"><button class="primary" id="cmp-ir">Comparar</button></div><div id="cmp-out"></div>` : '<p class="muted">Importe listas para comparar.</p>'}
    </section>`;
  ligarSeletor(render);
  $('#c-deck').onchange = e => { S.deckCartas = e.target.value; render(); };
  if (S.deckCartas) desenharEfeitoCartas(S.deckCartas);
  if (com.length) {
    const preencher = async lado => {
      const js = (await api('/api/jogadores?torneio=' + $('#cmp-t' + lado).value)).filter(j => j.cartas);
      $('#cmp-i' + lado).innerHTML = js.map(j => `<option value="${esc(j.labs_id)}">${j.posicao}º ${esc(j.nome)} (${esc(j.arquetipo)})</option>`).join('');
    };
    $('#cmp-ta').onchange = () => preencher('a'); $('#cmp-tb').onchange = () => preencher('b');
    await preencher('a'); await preencher('b');
    $('#cmp-ir').onclick = async () => {
      const dif = await api(`/api/comparar?ta=${$('#cmp-ta').value}&ia=${$('#cmp-ia').value}&tb=${$('#cmp-tb').value}&ib=${$('#cmp-ib').value}`);
      $('#cmp-out').innerHTML = `<div class="tabela alta"><table><thead><tr><th>Carta</th><th class="n">Lista A</th><th class="n">Lista B</th><th class="n">Diferença</th></tr></thead><tbody>
        ${dif.map(l => `<tr><td>${esc(l.carta)}</td><td class="n">${l.a}</td><td class="n">${l.b}</td><td class="n" style="color:${l.dif > 0 ? 'var(--good)' : l.dif < 0 ? 'var(--bad)' : 'var(--muted)'}">${l.dif > 0 ? '+' : ''}${l.dif}</td></tr>`).join('')}</tbody></table></div>`;
    };
  }
}

async function renderCartasMatchups() {
  const vez = novaTela();
  await carregarTorneios();
  if (telaVelha(vez)) return;
  if (!S.torneios.filter(daFonte).length) { main.innerHTML = `${trilha()}<header><h1>Cartas x matchups</h1></header>${seletorTorneios()}`; ligarSeletor(render); return; }
  const m = await api(`/api/meta?${qsTorneios()}`);
  S.cmuDeck = S.cmuDeck && m.divisao.some(d => d.arquetipo === S.cmuDeck) ? S.cmuDeck : (m.divisao[0]?.arquetipo || '');
  const uso = S.cmuDeck ? await api(`/api/cartas?${qsTorneios()}&arq=${encodeURIComponent(S.cmuDeck)}`) : { cartas: [] };
  // cartas que variam de quantidade entre as listas (as que todo mundo joga 4 não dizem nada)
  const candidatas = uso.cartas.filter(c => Object.keys(c.por_copias || {}).length > 1);
  if (!S.cmuCarta || !candidatas.some(c => c.chave === S.cmuCarta)) S.cmuCarta = candidatas[0]?.chave || '';
  const r = S.cmuCarta ? await api(`/api/cartas/matchups?${qsTorneios()}&arq=${encodeURIComponent(S.cmuDeck)}&carta=${encodeURIComponent(S.cmuCarta)}&min=${S.minMu ?? 5}`).catch(() => null) : null;
  if (telaVelha(vez)) return;
  const carta = candidatas.find(c => c.chave === S.cmuCarta);
  main.innerHTML = `
    ${trilha()}<header><h1>Cartas x matchups</h1><p class="sub">Para um deck, compara a taxa de vitória contra cada adversário conforme quantas cópias de uma carta a lista tinha. Ajuda a decidir se uma carta de tech ou uma cópia a mais vale o espaço. Mirrors não contam.</p></header>
    ${seletorTorneios()}
    <div class="row">
      <span class="cel-carta">${icones(S.cmuDeck)}</span>
      <select id="cmu-deck">${m.divisao.map(d => `<option value="${esc(d.arquetipo)}" ${d.arquetipo === S.cmuDeck ? 'selected' : ''}>${esc(d.nome)}</option>`).join('')}</select>
      <select id="cmu-carta" class="grow">${candidatas.map(c => `<option value="${esc(c.chave)}" ${c.chave === S.cmuCarta ? 'selected' : ''}>${esc(c.carta)} · em ${pct(c.pct)} das listas</option>`).join('') || '<option>Nenhuma carta com quantidade variável</option>'}</select>
      <label class="label" for="cmu-min">Mínimo de partidas</label><select id="cmu-min">${[0, 3, 5, 10, 20].map(v => `<option ${(S.minMu ?? 5) == v ? 'selected' : ''}>${v}</option>`).join('')}</select>
    </div>
    ${carta ? `<div class="row" style="align-items:flex-start;flex-wrap:nowrap;gap:16px"><img src="${imgId(carta.carta_id, carta.carta)}" alt="" style="width:110px;border-radius:7px;flex:none">
      <section class="panel grow" style="min-width:0">
      ${r && r.linhas.length ? `<p class="muted">${r.listas} listas de ${esc(r.nome)} com resultado. Células apagadas têm menos de ${S.minMu ?? 5} partidas.</p>
      <div class="tabela"><table class="matriz iguais" style="min-width:${3 * 80 + r.colunas.length * 112}px"><colgroup><col class="fixa"><col class="fixa"><col class="fixa">${r.colunas.map(() => '<col>').join('')}</colgroup><thead><tr><th>Cópias</th><th>Listas</th><th>Geral</th>${r.colunas.map(c => `<th>${icones(c.arquetipo)}<br>${esc(c.nome)}</th>`).join('')}</tr></thead>
      <tbody>${r.linhas.map(l => `<tr><td class="cab">${l.copias}×</td><td>${l.listas}</td><td style="${l.geral.n ? corTaxa(l.geral.taxa) : ''}">${l.geral.n ? pct(l.geral.taxa) : '–'}<small>${l.geral.n || ''}</small></td>
        ${l.celulas.map((c, i) => `<td class="${c.pouco ? 'pouco' : ''}" style="${c.n ? corTaxa(c.taxa) : ''}" title="${l.copias}× contra ${esc(r.colunas[i].nome)}: ${c.v}-${c.d}-${c.e}">${c.n ? pct(c.taxa) : '–'}<small>${c.n || ''}</small></td>`).join('')}</tr>`).join('')}</tbody></table></div>`
      : '<p class="muted">Sem partidas suficientes para esta combinação.</p>'}
      </section></div>` : '<p class="muted">Importe torneios com listas (Listas do topo maior que zero) para usar esta análise.</p>'}`;
  ligarSeletor(render);
  $('#cmu-deck').onchange = e => { S.cmuDeck = e.target.value; S.cmuCarta = ''; render(); };
  $('#cmu-carta').onchange = e => { S.cmuCarta = e.target.value; render(); };
  $('#cmu-min').onchange = e => { S.minMu = Number(e.target.value); render(); };
}

function seloFormato(t) {
  if (t.formato === 'standard') return '<span class="pill v" title="O Limitless marca este torneio como Standard">Standard ✓</span>';
  if (t.formato) return `<span class="pill d" title="Fica fora das contas: o programa só usa Standard">${esc(t.formato)}: fora das contas</span>`;
  return '<span class="pill n" title="Ainda não deu para confirmar o formato no Limitless; entra nas contas">formato não confirmado</span>';
}
async function renderTorneios() {
  const vez = novaTela();
  await carregarTorneios();
  const grandes = S.torneios.filter(t => t.fonte !== 'online'), online = S.torneios.filter(t => t.fonte === 'online');
  const st = await api('/api/status');
  if (telaVelha(vez)) return;
  S.status = st;
  const imp = st.importacao, cfg = st.config;
  main.innerHTML = `
    ${trilha()}<header><h1>Importar torneios</h1><p class="sub">Grandes eventos: classificação, decks e listas vêm do Limitless Labs; o resultado de cada mesa vem do RK9, a fonte oficial que o Labs também usa. Um Regional grande leva alguns minutos.</p></header>
    <section class="panel"><h2>Atualização automática</h2>
      <p class="sub">O RK9 e o Limitless Labs não avisam quando sai um torneio novo. Por isso o programa verifica sozinho enquanto estiver aberto, importa os torneios que faltam e atualiza os que foram importados antes do resultado final.</p>
      <div class="row">
        <button id="s-toggle" class="${cfg.sincronizar_auto ? '' : 'primary'}">${cfg.sincronizar_auto ? 'Desligar' : 'Ligar'} atualização automática</button>
        <label class="label" for="s-horas">Verificar a cada</label>
        <select id="s-horas">${[1, 3, 6, 12, 24].map(v => `<option value="${v}" ${cfg.sincronizar_horas == v ? 'selected' : ''}>${v} h</option>`).join('')}</select>
        <label class="label" for="s-dias">Torneios dos últimos</label>
        <select id="s-dias">${[15, 30, 45, 90, 180, 365].map(v => `<option value="${v}" ${cfg.sincronizar_dias == v ? 'selected' : ''}>${v} dias</option>`).join('')}</select>
        <span class="grow"></span><button id="s-agora">Verificar agora</button>
      </div>
      <div class="row">
        <label class="row" style="gap:6px"><input type="checkbox" id="s-online" ${cfg.online_ativo !== false ? 'checked' : ''}> Importar também torneios online Standard do Limitless</label>
        <label class="label" for="s-online-min">com pelo menos</label>
        <select id="s-online-min">${[32, 64, 128, 256].map(v => `<option value="${v}" ${(cfg.online_min_jogadores ?? 64) == v ? 'selected' : ''}>${v} jogadores</option>`).join('')}</select>
        <label class="label" for="s-online-dias">dos últimos</label>
        <select id="s-online-dias">${[7, 14, 21, 30, 45].map(v => `<option value="${v}" ${(cfg.online_dias ?? 21) == v ? 'selected' : ''}>${v} dias</option>`).join('')}</select>
      </div>
      <p class="muted" style="font-size:.85rem">Os torneios online (play.limitlesstcg.com) são dezenas por semana, com o deck, a lista e o resultado de cada mesa. O site limita os pedidos, então eles chegam aos poucos, até ${cfg.online_por_vez ?? 40} por verificação. Nas telas de Meta, escolha a <b>Fonte</b>: grandes eventos, torneios online ou todos.</p>
      <p class="muted" id="s-info"></p>
    </section>
    <section class="panel"><h2>Importar um torneio específico</h2>
      <div class="row">
        <button class="primary" id="t-buscar">Buscar torneios no Limitless Labs</button>
        <span class="grow"></span>
        <label class="label" for="t-listas">Listas do topo</label>
        <input id="t-listas" type="number" min="0" max="512" value="${cfg.listas_top ?? 64}" style="width:80px" title="Quantas listas de cartas baixar (0 = nenhuma)">
        <input id="t-id" placeholder="Nº do torneio (ex.: 0078)" style="width:200px">
        <button id="t-importar-id">Importar</button>
      </div>
      <div id="t-prog" ${imp.ativo || imp.erro || imp.resumo ? '' : 'hidden'}>
        <div class="row"><span class="grow" id="t-etapa">${esc(imp.etapa || '')}</span><span class="num" id="t-pct">${imp.pct || 0}%</span></div>
        <div class="progresso"><span id="t-barra" style="width:${imp.pct || 0}%"></span></div>
        <p id="t-msg" class="muted">${esc(imp.resumo || '')}</p>
        <p id="t-erro" class="aviso erro" ${imp.erro ? '' : 'hidden'}>${esc(imp.erro || '')}</p>
      </div>
      <div id="t-lista"></div>
    </section>
    <section class="panel"><h2>Grandes eventos importados</h2>
      ${grandes.length ? `<div class="tabela"><table><thead><tr><th>Torneio</th><th>Data</th><th class="n">Jogadores</th><th class="n">Partidas</th><th class="n">Listas</th><th>Importado em</th><th></th></tr></thead><tbody>
        ${grandes.map(t => `<tr><td><b>${esc(t.nome)}</b> <span class="muted mono">${t.id}</span> ${seloFormato(t)}</td><td class="num">${fmtData(t.data)}</td><td class="n">${t.jogadores ?? ''}</td><td class="n">${t.qtd_partidas}</td><td class="n">${t.qtd_listas}</td><td class="muted num">${esc((t.importado_em || '').replace('T', ' ').slice(0, 16))}</td>
          <td class="row" style="flex-wrap:nowrap"><button data-reimp="${t.id}">Atualizar</button><button class="perigo" data-del="${t.id}">Apagar</button></td></tr>`).join('')}
      </tbody></table></div>` : '<p class="vazio">Nenhum torneio importado ainda.</p>'}
    </section>
    <section class="panel"><h2>Torneios online importados</h2>
      ${online.length ? `<p class="muted">${online.length} torneios, ${online.reduce((a, t) => a + (t.jogadores || 0), 0).toLocaleString('pt-BR')} jogadores, ${online.reduce((a, t) => a + (t.qtd_partidas || 0), 0).toLocaleString('pt-BR')} partidas.</p>
        <details><summary class="label" style="cursor:pointer">Ver a lista</summary><div class="tabela alta"><table><thead><tr><th>Torneio</th><th>Data</th><th class="n">Jogadores</th><th class="n">Partidas</th><th class="n">Listas</th><th></th></tr></thead><tbody>
        ${online.map(t => `<tr><td>${esc(t.nome)}</td><td class="num">${fmtData(t.data)}</td><td class="n">${t.jogadores ?? ''}</td><td class="n">${t.qtd_partidas}</td><td class="n">${t.qtd_listas}</td>
          <td><button class="perigo" data-del="${t.id}">Apagar</button></td></tr>`).join('')}</tbody></table></div></details>`
        : '<p class="vazio">Nenhum ainda. Eles chegam pela atualização automática (ou em Verificar agora).</p>'}
    </section>`;
  const salvarCfg = obj => api('/api/config', { method: 'POST', body: JSON.stringify(obj) }).then(() => setTimeout(() => { if (aba() === 'torneios') renderTorneios(); }, 300));
  $('#s-toggle').onclick = () => salvarCfg({ sincronizar_auto: !cfg.sincronizar_auto });
  $('#s-horas').onchange = e => salvarCfg({ sincronizar_horas: Number(e.target.value) });
  $('#s-dias').onchange = e => salvarCfg({ sincronizar_dias: Number(e.target.value) });
  $('#s-online').onchange = e => salvarCfg({ online_ativo: e.target.checked });
  $('#s-online-min').onchange = e => salvarCfg({ online_min_jogadores: Number(e.target.value) });
  $('#s-online-dias').onchange = e => salvarCfg({ online_dias: Number(e.target.value) });
  $('#t-listas').onchange = e => api('/api/config', { method: 'POST', body: JSON.stringify({ listas_top: Number(e.target.value) || 0 }) });
  $('#s-agora').onclick = async () => {
    try { await api('/api/sincronizar', { method: 'POST' }); toast('Verificando torneios novos…'); setTimeout(atualizarStatus, 800); }
    catch (e) { toast(e.message); }
  };
  atualizarSync(st.sincronizacao);
  const importar = async id => {
    S.listasTop = Number($('#t-listas').value) || 0;
    try { await api('/api/limitless/importar', { method: 'POST', body: JSON.stringify({ id, listas_top: S.listasTop }) });
      $('#t-prog').hidden = false; toast(`Importando ${id}…`); setTimeout(atualizarStatus, 500); }
    catch (e) { toast(e.message); }
  };
  $('#t-importar-id').onclick = () => importar($('#t-id').value.trim());
  document.querySelectorAll('[data-reimp]').forEach(b => b.onclick = () => importar(b.dataset.reimp));
  document.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
    if (!confirm('Apagar este torneio do banco local?')) return;
    await api('/api/torneios/' + b.dataset.del, { method: 'DELETE' }); toast('Torneio apagado'); renderTorneios();
  });
  $('#t-buscar').onclick = async () => {
    $('#t-lista').innerHTML = '<p class="muted">Buscando…</p>';
    try {
      const evs = await api('/api/limitless/eventos');
      const ja = new Set(S.torneios.map(t => t.id));
      $('#t-lista').innerHTML = `<div class="tabela alta"><table><thead><tr><th>Nº</th><th>Torneio</th><th></th></tr></thead><tbody>
        ${evs.map(e => `<tr><td class="mono">${e.id}</td><td>${esc(e.titulo)}</td><td>${ja.has(e.id) ? '<span class="pill v">importado</span>' : `<button data-imp="${e.id}">Importar</button>`}</td></tr>`).join('')}</tbody></table></div>`;
      document.querySelectorAll('[data-imp]').forEach(b => b.onclick = () => importar(b.dataset.imp));
    } catch (e) { $('#t-lista').innerHTML = `<p class="aviso erro">${esc(e.message)}</p>`; }
  };
}
function atualizarSync(s) {
  const el = $('#s-info'); if (!el) return;
  el.textContent = [s.rodando ? 'Verificando agora…' : '', s.ultima ? `Última verificação: ${s.ultima}` : 'Ainda não verificou nesta sessão',
    s.proxima && s.ligado ? `próxima: ${s.proxima}` : '', s.mensagem && !s.rodando ? s.mensagem : ''].filter(Boolean).join(' · ');
}
function atualizarProgresso(imp) {
  if (!$('#t-prog')) return;
  if (imp.ativo || imp.erro || imp.resumo) $('#t-prog').hidden = false;
  $('#t-etapa').textContent = imp.etapa || ''; $('#t-pct').textContent = (imp.pct || 0) + '%';
  $('#t-barra').style.width = (imp.pct || 0) + '%'; $('#t-msg').textContent = imp.resumo || '';
  $('#t-erro').hidden = !imp.erro; $('#t-erro').textContent = imp.erro || '';
}

// ---- Metodologia (D-053): como cada número das telas de torneio é calculado, em linguagem simples. Fonte: PROJECT_KNOWLEDGE/
// 02_BUSINESS_RULES/STATISTICS.md e tracker/evolucao_listas.py. Mudou uma conta? Atualize aqui no mesmo PR.
const METODOLOGIA = [
  ['Fontes', `<ul>
    <li><b>Grandes eventos:</b> Limitless Labs (classificação, rodadas e listas) e RK9 (rodadas). Só a divisão Masters e só o formato Standard.</li>
    <li><b>Torneios online:</b> play.limitlesstcg.com (classificação, mesas e listas publicadas).</li>
    <li><b>Listas:</b> o Coletor baixa as listas do topo de cada torneio (64 por padrão). Por isso as contas de cartas descrevem quem foi bem, não o deck inteiro.</li>
    <li><b>Nome do deck:</b> o que o Limitless dá à lista; Dragapult com Dunsparce vira Dragapult Dudunsparce (D-052).</li>
    <li><b>Época:</b> cada coleção nova começa uma época: nos grandes eventos, no dia em que passa a valer em torneio; nos online, no lançamento.</li></ul>`],
  ['O que conta como partida', `<ul>
    <li>Folga (bye), atraso e derrota dupla (W.O., quando ninguém aparece) <b>não</b> são partidas: os importadores descartam.</li>
    <li>Entram todas as rodadas importadas, inclusive as do corte final (top cut). Os grandes eventos são melhor de 3; o ladder do TCG Live é jogo único: compare com cuidado.</li></ul>`],
  ['Taxas', `<ul>
    <li><b>Taxa de vitória</b> = vitórias ÷ (vitórias + derrotas + empates), como no Limitless: empate conta como não-vitória. Por isso o deck médio fica um pouco abaixo de 50%.</li>
    <li>"Contra o campo" deixa de fora os mirrors (o deck contra ele mesmo).</li>
    <li><b>Faixa provável de 95%</b> (método de Wilson): onde a taxa verdadeira provavelmente está. Com poucas partidas ela é larga. Nas telas de torneio a faixa considera que as várias partidas de um mesmo jogador andam juntas (D-041).</li>
    <li><b>Mínimos:</b> no gráfico "Quem vale a pena jogar", 20 partidas (taxa) ou 20 jogadores (conversão e aproveitamento); na tabela de matchups, o mínimo que você escolher.</li></ul>`],
  ['Participação, conversão e aproveitamento', `<ul>
    <li><b>% do campo</b> = jogadores do deck ÷ jogadores com deck conhecido.</li>
    <li><b>Conversão</b> = jogadores do deck que terminaram no Top escolhido ÷ jogadores do deck. <b>Fator</b> = participação no corte ÷ participação no campo (acima de 1 = converte melhor que a média).</li>
    <li><b>Aproveitamento no suíço</b> = pontos (3 por vitória, 1 por empate) ÷ pontos possíveis (3 × rodadas suíças). Quem desistiu perde as rodadas que faltaram. O top cut fica fora (reconhecido pelas mesas que caem pela metade no fim) e, nos grandes eventos, só conta o Dia 1, que todos jogam. Folgas não estão no banco: quem teve folga perde 3 pontos possíveis.</li></ul>`],
  ['Matchups e "qual deck jogar"', `<ul>
    <li><b>Taxa real:</b> o resultado do confronto. <b>Ajustada:</b> com poucos jogos, o confronto é completado pela força geral de cada deck (como se houvesse 24 jogos "imaginários" com a força geral); prevê os torneios seguintes melhor que a real (testado).</li>
    <li><b>Força dos decks:</b> modelo de Bradley-Terry (chance de A vencer B = força de A ÷ (força de A + força de B)).</li>
    <li><b>Esperada contra o campo:</b> média dos confrontos ajustados, pesada pela presença de cada adversário. <b>Equilíbrio:</b> mistura de decks que nenhum outro consegue explorar (teoria dos jogos).</li></ul>`],
  ['Listas', `<ul>
    <li><b>Esqueleto e Uso de cartas:</b> % das listas que usam cada carta e a taxa de vitória com e sem ela (associação, não causa).</li>
    <li><b>Lista base:</b> cada lista pesa os pontos finais do jogador (3V + E). Núcleo = carta em ≥ 75% do peso; opções = 10% a 75%; cópias = a quantidade mais comum (pesada). Precisa de 5 listas.</li>
    <li><b>Mudanças nas listas:</b> últimas 2 semanas × 4 semanas antes. Cada contagem vira "pelo menos k cópias" (e "menos de k" para cartas que eram padrão). Conta como mudança quando fica ≥ 25 pontos mais comum com teste binomial p &lt; 0,005, as listas com ela fazem mais pontos por partida que as sem ela, e ≥ 5 listas a têm. Mudanças nas mesmas listas formam um pacote, ordenado por a · ln(a ÷ b) (comum agora, rara antes).</li>
    <li><b>Estabilidade:</b> quantas cartas a lista média mudou entre os dois períodos, menos a variação natural (listas sorteadas 200 vezes entre os períodos; 95º percentil). Menos de 1 carta além disso = estável. Precisa de 15 listas em cada período.</li>
    <li><b>Versões pela ACE SPEC</b> e <b>efeito de cada carta</b> (regressão com freio): ver a ajuda de cada tela.</li></ul>`],
  ['Identificação do deck do adversário (suas partidas)', `<ul>
    <li>Modelo Naive Bayes sobre as cartas que o adversário mostrou, treinado nas listas de torneio. Com poucas cartas ou cartas de vários decks, o palpite é marcado como <b>incerto</b> (acerta cerca de 1 em 3).</li></ul>`],
  ['Limites', `<ul>
    <li>Os números descrevem o que aconteceu; não provam causa. Uma carta pode aparecer mais nas vitórias porque só é jogada quando a partida já está boa.</li>
    <li>Listas só do topo (puxam as taxas de cartas e versões para cima); torneios melhor de 3 × ladder de jogo único; nomes de deck dependem do Limitless.</li>
    <li>Toda conta nova é comparada com a atual nos mesmos dados antes de mudar (D-017).</li></ul>`],
];
function renderMetodologia() {
  novaTela();
  main.innerHTML = `${trilha()}<header><h1>Metodologia</h1><p class="sub">Como cada número das telas de Meta e torneios é calculado. Detalhes técnicos no repositório: <span class="mono">PROJECT_KNOWLEDGE/02_BUSINESS_RULES/STATISTICS.md</span>.</p></header>
    ${METODOLOGIA.map(([t, h]) => `<section class="panel metodologia"><h2>${t}</h2>${h}</section>`).join('')}`;
}
