/* =====================================================================
   REPLAY
   ===================================================================== */
const COR_ENERGIA = { Grass: '#3f9b4b', Fire: '#e2552b', Water: '#2f86d6', Lightning: '#f0c419', Psychic: '#9a55c4', Fighting: '#b8692c',
  Darkness: '#2f3540', Metal: '#9aa5b1', Fairy: '#e07bb5', Dragon: '#b0912a', Colorless: '#e9ecef', Special: '#ffffff' };
const ROTULO = { ataque: 'Ataque', habilidade: 'Habilidade', jogada: 'Carta jogada', evolucao: 'Evolução', anexo: 'Ligou à mesa',
  nocaute: 'Nocaute', premio: 'Prêmio', entrou: 'Entrou em jogo', recuo: 'Recuo', troca: 'Novo Pokémon Ativo', compra: 'Comprou',
  turno: 'Novo turno', fim: 'Fim de partida', banco: 'Para o Banco', dano: 'Dano', descarte: 'Descarte', info: '' };

function anexoHtml(a) {
  if (a.tipo === 'energia' && a.energia !== 'Special') return `<i class="en" style="background:${COR_ENERGIA[a.energia] || '#fff'}" title="${esc(a.nome)}"></i>`;
  return `<img class="fer" src="${imgNome(a.nome)}" title="${esc(a.nome)}" alt="${esc(a.nome)}">`;
}
function imgMesa(j, nome) {
  const id = S.rp?.r?.versoes?.[j]?.[nome];
  return id ? imgId(id) : imgNome(nome);
}
function cartaMesa(p, tam, d, j) {
  if (!p) return `<div class="carta vazia" title="Sem Pokémon Ativo"></div>`;
  const cls = ['carta', tam, d.uid === p.uid ? 'foco' : '', d.alvo_uid === p.uid ? 'alvo' : ''].join(' ');
  return `<div class="${cls}" title="${esc(p.nome)}${p.dano ? ` · ${p.dano} de dano` : ''}"><img src="${imgMesa(j, p.nome)}" alt="${esc(p.nome)}">
    ${p.dano ? `<span class="dano">${p.dano}</span>` : ''}<div class="anexos">${p.anexos.map(anexoHtml).join('')}</div></div>`;
}
// Prêmios restantes: com a face = prêmio que o log revela (quem exportou vê o nome de cada prêmio que pega).
// Como os prêmios são separados na preparação, ele aparece desde o começo, com a borda tracejada; os outros ficam virados.
function premiosHtml(j, m) {
  const conhecidos = m.premios_conhecidos || [];
  const slots = Array.from({ length: 6 }, (_, i) => {
    if (i >= m.premios) return '<span class="premio-carta" title="Prêmio já pego"></span>';
    const c = conhecidos[i];
    if (!c) return '<span class="premio-carta verso" title="Prêmio virado: o log não diz qual é"></span>';
    const dica = `${c.nome} · estava nos prêmios desde o começo (${j} pegou no turno ${c.turno})`;
    return `<span class="premio-carta face" title="${esc(dica)}"><img src="${imgMesa(j, c.nome)}" alt="${esc(c.nome)}" loading="lazy"></span>`;
  }).join('');
  const n = conhecidos.length;
  return `<div class="premios" aria-label="Prêmios de ${esc(j)}">${slots}</div>
    <span>${m.premios} prêmio${m.premios === 1 ? '' : 's'} restante${m.premios === 1 ? '' : 's'}${n ? `, ${n} conhecido${n === 1 ? '' : 's'}` : ''}</span>`;
}
function ladoMesa(j, m, q, cima, cor) {
  const d = q.destaque;
  const info = `<div class="lado-info"><span class="rp-nome ${cor}">${esc(j)}${q.vez === j ? '<span class="rp-vez">vez</span>' : ''}</span>
    ${premiosHtml(j, m)}
    ${m.nocauteados.length ? `<span class="ko-lista">Nocauteados: ${m.nocauteados.map(esc).join(', ')}</span>` : ''}</div>`;
  const banco = `<div class="banco">${m.banco.map(p => cartaMesa(p, 'peq', d, j)).join('') || '<span style="opacity:.6;font-size:.8rem">Banco vazio</span>'}</div>`;
  const ativo = cartaMesa(m.ativo, 'grande', d, j);
  return `<div class="lado-mesa">${info}<div class="campo">${cima ? banco + ativo : ativo + banco}</div></div>`;
}

// Mão de um jogador: carta com nome = face; sem nome = verso. "nova" = entrou na mão neste passo.
// "inferida" = carta da mão inicial descoberta depois, quando foi jogada (mulligan de quem exportou o log).
function maoHtml(j, mao, anterior) {
  if (!mao) return '';
  const antes = new Set((anterior || []).map(c => c.id));
  const viradas = mao.filter(c => !c.nome).length;
  const cartas = mao.map(c => {
    const cls = ['mao-carta', antes.has(c.id) ? '' : 'nova', c.inferida ? 'inferida' : ''].join(' ');
    if (!c.nome) return `<div class="${cls} verso" title="Carta virada"></div>`;
    const dica = c.inferida ? `${c.nome} · estava na mão desde o começo (descoberta quando foi jogada)` : c.nome;
    return `<div class="${cls}" title="${esc(dica)}"><img src="${imgNome(c.nome)}" alt="${esc(c.nome)}" loading="lazy"></div>`;
  }).join('');
  return `<div class="mao" aria-label="Mão de ${esc(j)}">
    <span class="mao-rotulo">Mão · ${mao.length} carta${mao.length === 1 ? '' : 's'}${viradas && viradas < mao.length ? ` (${viradas} virada${viradas === 1 ? '' : 's'})` : ''}</span>
    <div class="mao-cartas">${cartas || '<span class="mao-vazia">Sem cartas</span>'}</div></div>`;
}

// Melhores momentos (ideia do Dead Draw, desde 2026.11.10-5): ataques, nocautes, prêmios e o fim. Os botões ◆ pulam entre
// eles (Shift + seta também) e, com "Só os melhores momentos" marcado, o Reproduzir passa só por eles.
const TIPOS_MOMENTO = new Set(['ataque', 'nocaute', 'premio', 'fim']);
const momentosDo = r => r.quadros.map((q, i) => TIPOS_MOMENTO.has(q.destaque.tipo) ? i : -1).filter(i => i >= 0);
function irMomento(direcao) {
  if (!S.rp) return;
  const m = S.rp.momentos, i = S.rp.i;
  const alvo = direcao > 0 ? m.find(x => x > i) : [...m].reverse().find(x => x < i);
  if (alvo != null) { S.rp.i = alvo; desenharQuadro(); }
}

async function renderReplay(id) {
  const vez = novaTela();
  main.innerHTML = '<p class="vazio">Montando o replay…</p>';
  const r = await api(`/api/partidas/${id}/replay`);
  if (telaVelha(vez)) return;
  if (!r.quadros.length) { main.innerHTML = '<div class="aviso erro">Não consegui montar o replay desta partida.</div>'; return; }
  const eu = r.jogadores.includes(r.eu) ? r.eu : r.jogadores[0];
  const adv = r.jogadores.find(j => j !== eu) || '';
  S.rp = { r, i: 0, eu, adv, timer: null, vel: S.rp?.vel || 900, momentos: momentosDo(r), soMomentos: S.rp?.soMomentos || false };
  const turnos = r.quadros.map((q, i) => ({ q, i })).filter(x => x.q.destaque.tipo === 'turno' && x.q.vez);
  main.innerHTML = `
    <div class="row"><a class="btn" href="#partida-${id}">← Detalhes da partida</a></div>
    ${trilha()}<header><h1>Replay: ${esc(eu)} x ${esc(adv)}</h1><p class="sub">${r.vencedor ? `Vitória de <b>${esc(r.vencedor)}</b>. ` : ''}${r.turnos} turnos. Use as setas do teclado ou os botões para avançar.</p></header>
    <div class="controles">
      <button id="rp-ini" title="Início">⏮</button><button id="rp-ant" title="Anterior (←)">◀</button>
      <button id="rp-play" class="primary" title="Reproduzir (espaço)">▶ Reproduzir</button>
      <button id="rp-prox" title="Próximo (→)">▶</button><button id="rp-fim" title="Fim">⏭</button>
      <span class="rp-momentos"><button id="rp-mom-ant" title="Momento anterior: ataque, nocaute ou prêmio (Shift + ←)">◆ ◀</button><button id="rp-mom-prox" title="Próximo momento: ataque, nocaute ou prêmio (Shift + →)">▶ ◆</button>
        <label class="row" style="gap:5px;font-size:.82rem" title="O Reproduzir passa só pelos ataques, nocautes e prêmios"><input type="checkbox" id="rp-so-mom" ${S.rp.soMomentos ? 'checked' : ''}>Só os melhores momentos</label></span>
      <input type="range" id="rp-barra" min="0" max="${r.quadros.length - 1}" value="0" aria-label="Posição no replay">
      <select id="rp-turno" aria-label="Ir para o turno"><option value="">Ir para o turno…</option>${turnos.map((t, k) => `<option value="${t.i}">Turno ${k + 1} · ${esc(t.q.vez)}</option>`).join('')}</select>
      <select id="rp-vel" aria-label="Velocidade">${[[1600, 'Lento'], [900, 'Normal'], [450, 'Rápido']].map(([v, t]) => `<option value="${v}" ${S.rp.vel == v ? 'selected' : ''}>${t}</option>`).join('')}</select>
    </div>
    <div class="replay">
      <div class="mesa" id="rp-mesa"></div>
      <aside class="rp-lateral">
        <section class="panel" id="rp-destaque"></section>
        <div class="rp-log" id="rp-log">${r.quadros.map((q, i) => `<div data-i="${i}" class="${q.destaque.tipo === 'turno' ? 'turno' : TIPOS_MOMENTO.has(q.destaque.tipo) ? 'momento' : ''}">${q.destaque.tipo === 'turno' && q.vez ? `Turno ${turnos.findIndex(t => t.i === i) + 1} · ` : ''}${esc(q.texto)}</div>`).join('')}</div>
      </aside>
    </div>`;
  const ir = i => { S.rp.i = Math.max(0, Math.min(r.quadros.length - 1, i)); desenharQuadro(); };
  $('#rp-ini').onclick = () => ir(0); $('#rp-fim').onclick = () => ir(r.quadros.length - 1);
  $('#rp-ant').onclick = () => ir(S.rp.i - 1); $('#rp-prox').onclick = () => ir(S.rp.i + 1);
  $('#rp-barra').oninput = e => ir(Number(e.target.value));
  $('#rp-turno').onchange = e => { if (e.target.value !== '') ir(Number(e.target.value)); e.target.value = ''; };
  $('#rp-vel').onchange = e => { S.rp.vel = Number(e.target.value); if (S.rp.timer) { alternarPlay(); alternarPlay(); } };
  $('#rp-play').onclick = alternarPlay;
  $('#rp-mom-ant').onclick = () => irMomento(-1); $('#rp-mom-prox').onclick = () => irMomento(1);
  $('#rp-so-mom').onchange = e => { S.rp.soMomentos = e.target.checked; };
  $('#rp-log').onclick = e => { const d = e.target.closest('[data-i]'); if (d) ir(Number(d.dataset.i)); };
  desenharQuadro();
}
function alternarPlay() {
  if (!S.rp) return;
  if (S.rp.timer) { clearInterval(S.rp.timer); S.rp.timer = null; }
  else {
    if (S.rp.i >= S.rp.r.quadros.length - 1) S.rp.i = 0;
    if (S.rp.soMomentos && !S.rp.momentos.some(x => x > S.rp.i)) S.rp.i = 0;
    S.rp.timer = setInterval(() => {
      if (S.rp.soMomentos) {  // só os melhores momentos: pula direto para o próximo
        const prox = S.rp.momentos.find(x => x > S.rp.i);
        if (prox == null) { alternarPlay(); return; }
        S.rp.i = prox; desenharQuadro(); return;
      }
      if (S.rp.i >= S.rp.r.quadros.length - 1) { alternarPlay(); return; }
      S.rp.i++; desenharQuadro();
    }, S.rp.vel);
  }
  const b = $('#rp-play'); if (b) b.textContent = S.rp.timer ? '⏸ Pausar' : '▶ Reproduzir';
}
function desenharQuadro() {
  const { r, i, eu, adv } = S.rp;
  const q = r.quadros[i], e = q.estado, d = q.destaque;
  const est = e.estadio;
  const maoAntes = (r.quadros[i - 1] || q).estado.maos || {};
  const maos = e.maos || {};
  $('#rp-mesa').innerHTML = `
    ${adv ? maoHtml(adv, maos[adv], i ? maoAntes[adv] : maos[adv]) : ''}
    ${adv ? ladoMesa(adv, e.mesa[adv], q, true, 'p2') : ''}
    <div class="centro-mesa">
      <span>Turno ${Math.max(q.turno, 0)}${q.vez ? ` · vez de <b>${esc(q.vez)}</b>` : ''}</span>
      <span class="estadio">${est ? `<img src="${imgNome(est.nome)}" alt="">Estádio: <b>${esc(est.nome)}</b>` : 'Sem Estádio'}</span>
      ${e.resultado ? `<span class="rp-vez">${esc(e.resultado)} venceu</span>` : ''}
    </div>
    ${ladoMesa(eu, e.mesa[eu], q, false, 'p1')}
    ${maoHtml(eu, maos[eu], i ? maoAntes[eu] : maos[eu])}`;
  const carta = d.carta || (d.tipo === 'turno' ? null : null);
  $('#rp-destaque').innerHTML = `<div class="rp-destaque">
      ${carta ? `<img src="${imgNome(carta, true)}" alt="${esc(carta)}">` : '<div></div>'}
      <div style="min-width:0"><span class="label">${esc(ROTULO[d.tipo] || '')}${d.dano ? ` · ${d.dano} de dano` : ''}</span>
        <p style="margin-top:4px">${esc(q.texto)}</p>
        ${q.detalhes ? `<p class="muted" style="margin-top:6px;font-size:.8rem">${q.detalhes.map(esc).join('<br>')}</p>` : ''}
        <p class="muted num" style="margin-top:6px;font-size:.75rem">Passo ${i + 1} de ${r.quadros.length} · linha ${q.linha} do log</p></div></div>`;
  $('#rp-barra').value = i;
  document.querySelectorAll('#rp-log div').forEach(el => el.classList.toggle('atual', Number(el.dataset.i) === i));
  const atual = document.querySelector('#rp-log div.atual');
  if (atual) atual.scrollIntoView({ block: 'nearest' });
}
document.addEventListener('keydown', e => {
  if (aba() !== 'replay' || !S.rp || ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
  if (e.shiftKey && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) { irMomento(e.key === 'ArrowRight' ? 1 : -1); e.preventDefault(); return; }
  if (e.key === 'ArrowRight') { S.rp.i = Math.min(S.rp.i + 1, S.rp.r.quadros.length - 1); desenharQuadro(); e.preventDefault(); }
  if (e.key === 'ArrowLeft') { S.rp.i = Math.max(S.rp.i - 1, 0); desenharQuadro(); e.preventDefault(); }
  if (e.key === ' ') { alternarPlay(); e.preventDefault(); }
});
