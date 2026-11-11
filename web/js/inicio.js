/* ---------------- novidades depois de atualizar ---------------- */
async function mostrarNovidades(todas) {
  let n; try { n = await api('/api/novidades'); } catch (e) { return; }
  const lista = todas ? n.todas : n.pendentes;
  if (!lista.length) { if (todas) toast('Nenhuma novidade registrada ainda'); return; }
  const fundo = document.createElement('div');
  fundo.className = 'janela-fundo';
  fundo.innerHTML = `<div class="janela" role="dialog" aria-label="Novidades" style="width:min(640px,100%);max-height:86vh;overflow-y:auto">
    <h2 style="margin-top:0">${todas ? 'Novidades de cada versão' : `Programa atualizado: versão ${esc(n.versao)}`}</h2>
    ${lista.map(x => `<section style="margin-top:12px"><h3>${esc(x.versao)}${x.titulo ? ` · ${esc(x.titulo)}` : ''}</h3>
      ${x.mudancas?.length ? `<p class="label" style="margin-top:8px">O que mudou</p><ul style="margin:4px 0;padding-left:20px">${x.mudancas.map(m => `<li>${esc(m)}</li>`).join('')}</ul>` : ''}
      ${x.passos?.length ? `<p class="label" style="margin-top:8px">O que fazer agora</p><ol style="margin:4px 0;padding-left:20px">${x.passos.map(m => `<li>${esc(m)}</li>`).join('')}</ol>` : ''}</section>`).join('')}
    <div class="row" style="margin-top:14px"><span class="grow"></span><button class="primary" id="nv-ok">Entendi</button></div></div>`;
  document.body.appendChild(fundo);
  const fechar = async () => { fundo.remove(); if (!todas) await api('/api/novidades/vista', { method: 'POST' }).catch(() => {}); };
  fundo.querySelector('#nv-ok').onclick = fechar;
  fundo.onclick = e => { if (e.target === fundo) fechar(); };
  fundo.querySelector('#nv-ok').focus();
}

/* ---------------- primeiro uso guiado ---------------- */
async function copiarTexto(texto) {
  try { await navigator.clipboard.writeText(texto); return true; } catch (e) {}
  const ta = Object.assign(document.createElement('textarea'), { value: texto });
  ta.style.cssText = 'position:fixed;opacity:0'; document.body.appendChild(ta); ta.select();
  const ok = document.execCommand('copy'); ta.remove(); return ok;
}
async function mostrarGuia() {
  const st = await api('/api/status'), cfg = st.config;
  let atalhos = null;
  if (st.windows) { try { atalhos = await api('/api/atalhos'); } catch (e) {} }
  let passo = 0, nick = cfg.nick || '';
  const fundo = document.createElement('div');
  fundo.className = 'janela-fundo';
  document.body.appendChild(fundo);
  const passos = [
    () => `<h2 style="margin-top:0">Quem é você no TCG Live?</h2>
      <p>Digite seu nick <b>exatamente como aparece no jogo</b>. É assim que o programa separa suas vitórias e derrotas.</p>
      <div class="row"><input id="g-nick" value="${esc(nick)}" placeholder="Seu nick no TCG Live" style="flex:1"></div>
      <p class="muted" style="font-size:.85rem">Pode deixar em branco: o programa descobre sozinho na primeira partida, porque o log mostra o nome das cartas que <i>você</i> comprou.</p>`,
    () => `<h2 style="margin-top:0">No jogo</h2>
      <ol><li>Deixe o Pokémon TCG Live em <b>inglês</b>: Settings &gt; Language &gt; English. Em português o log não é lido.</li>
        <li>No fim de cada partida, clique em <b>Battle Log</b> e no botão de <b>exportar</b> (canto superior direito). O Coletor pega o log sozinho.</li>
        <li>Quer que o programa clique por você? Depois, veja o <b>Modo automático</b> em Programa &gt; Ajustes e captura.</li></ol>
      ${atalhos && !atalhos.area ? `<div class="row" style="margin-top:8px"><button id="g-atalho">Criar o atalho na Área de Trabalho</button><span class="muted" id="g-atalho-ok"></span></div>` : ''}`,
    () => `<h2 style="margin-top:0">Teste a captura</h2>
      <p>Clique no botão: ele copia um log de exemplo, como o jogo faz. Se o Coletor perceber, está tudo pronto.</p>
      <div class="row"><button class="primary" id="g-testar">Copiar um log de exemplo</button><span id="g-teste"></span></div>
      <p class="muted" style="font-size:.85rem">O log de exemplo não entra nas suas partidas.</p>`,
  ];
  const desenhar = () => {
    fundo.innerHTML = `<div class="janela guia" role="dialog" aria-label="Primeiro uso" style="width:min(560px,100%)">
      <div class="guia-passos">${passos.map((_, i) => `<span class="${i <= passo ? 'feito' : ''}"></span>`).join('')}</div>
      <p class="label" style="margin:0 0 4px">Passo ${passo + 1} de ${passos.length}</p>
      ${passos[passo]()}
      <div class="row" style="margin-top:16px"><button id="g-pular" style="border:none;background:none;color:var(--muted)">Pular</button><span class="grow"></span>
        ${passo ? '<button id="g-voltar">Voltar</button>' : ''}
        <button class="primary" id="g-seguir">${passo === passos.length - 1 ? 'Concluir' : 'Próximo'}</button></div></div>`;
    const guardarNick = () => { if ($('#g-nick')) nick = $('#g-nick').value.trim(); };
    const terminar = async () => {
      await api('/api/config', { method: 'POST', body: JSON.stringify({ guia_visto: true, ...(nick ? { nick } : {}) }) }).catch(() => {});
      fundo.remove();
    };
    $('#g-seguir').onclick = async () => {
      guardarNick();
      if (passo < passos.length - 1) { passo++; desenhar(); return; }
      await terminar(); toast('Tudo pronto. Boas partidas!'); render();
    };
    if ($('#g-voltar')) $('#g-voltar').onclick = () => { guardarNick(); passo--; desenhar(); };
    $('#g-pular').onclick = () => { guardarNick(); terminar(); };
    if ($('#g-atalho')) $('#g-atalho').onclick = async () => {
      try { atalhos = await api('/api/atalhos', { method: 'POST', body: JSON.stringify({ area: true }) }); $('#g-atalho').remove(); $('#g-atalho-ok').innerHTML = '<span class="ok">✓ Atalho criado</span>'; }
      catch (e) { toast(e.message); }
    };
    if ($('#g-testar')) $('#g-testar').onclick = async () => {
      const saida = $('#g-teste');
      saida.textContent = 'Copiando…';
      const antes = (await api('/api/status')).coletor.teste_em;
      const texto = await fetch('/api/exemplo-log').then(r => r.text());
      if (!await copiarTexto(texto)) { saida.innerHTML = '<span style="color:var(--bad)">Não consegui copiar. Tente de novo.</span>'; return; }
      saida.textContent = 'Esperando o Coletor perceber…';
      for (let i = 0; i < 12; i++) {
        await new Promise(r => setTimeout(r, 700));
        const s2 = await api('/api/status').catch(() => null);
        if (s2 && s2.coletor.teste_em > antes) { saida.innerHTML = '<span class="ok">✓ A captura está funcionando.</span>'; return; }
      }
      saida.innerHTML = `<span style="color:var(--bad)">O Coletor não percebeu a cópia.</span> ${st.coletor.ativo ? 'Feche e abra o programa e tente de novo.' : 'A captura está desligada: ligue no Início ou em Ajustes.'}`;
    };
    ($('#g-nick') || $('#g-seguir')).focus();
  };
  desenhar();
}

/* ---------------- busca rápida (Ctrl+K) ---------------- */
const TELAS_BUSCA = [['painel', 'Início'], ['partidas', 'Partidas'], ['desempenho', 'Desempenho'], ['decisoes', 'Decisões'],
  ['decks', 'Meus decks'], ['meta', 'Meta'], ['matchups', 'Matchups'], ['deck', 'Perfil de deck'], ['cartas', 'Uso de cartas'],
  ['cartas-mu', 'Cartas x matchups'], ['torneios', 'Torneios'], ['metodologia', 'Metodologia'], ['regras-standard', 'Regras do Standard'],
  ['ajustes', 'Ajustes e captura'], ['amigos', 'Amigos (trocar logs)'], ['biblioteca', 'Biblioteca de cartas'],
  ['revisao', 'Linhas não lidas'], ['regras', 'Regras de leitura']];
async function abrirBusca() {
  if ($('#busca-fundo')) return;
  const fundo = document.createElement('div');
  fundo.className = 'janela-fundo'; fundo.id = 'busca-fundo';
  fundo.innerHTML = `<div class="janela busca" role="dialog" aria-label="Buscar">
    <input id="busca-q" placeholder="Buscar telas, seus decks, decks do meta, adversários…" autocomplete="off">
    <ul id="busca-lista" role="listbox"></ul></div>`;
  document.body.appendChild(fundo);
  const q = $('#busca-q'); q.focus();
  const fechar = () => fundo.remove();
  fundo.onclick = e => { if (e.target === fundo) fechar(); };
  let itens = TELAS_BUSCA.map(([h, n]) => ({ tipo: 'Tela', nome: n, ir: () => { location.hash = h; } }));
  let achados = [], sel = 0;
  const escolher = k => { const i = achados[k]; if (!i) return; fechar(); i.ir(); };
  const desenhar = () => {
    const termos = semAcento(q.value).split(/\s+/).filter(Boolean);
    achados = itens.filter(i => termos.every(t => semAcento(i.nome + ' ' + (i.extra || '') + ' ' + i.tipo).includes(t))).slice(0, 14);
    sel = Math.min(sel, Math.max(achados.length - 1, 0));
    $('#busca-lista').innerHTML = achados.length ? achados.map((i, k) => `<li role="option" data-k="${k}" aria-selected="${k === sel}">
      <span class="b-tipo">${esc(i.tipo)}</span>${i.ico || ''}<span>${esc(i.nome)}</span>${i.extra ? `<span class="extra">${esc(i.extra)}</span>` : ''}</li>`).join('')
      : '<li class="muted">Nada encontrado</li>';
    document.querySelectorAll('#busca-lista li[data-k]').forEach(li => li.onclick = () => escolher(Number(li.dataset.k)));
  };
  q.oninput = () => { sel = 0; desenhar(); };
  q.onkeydown = e => {
    if (e.key === 'ArrowDown') { sel = Math.min(sel + 1, achados.length - 1); desenhar(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); desenhar(); e.preventDefault(); }
    else if (e.key === 'Enter') escolher(sel);
    else if (e.key === 'Escape') fechar();
  };
  desenhar();
  const [meus, ps] = await Promise.all([api('/api/decks').catch(() => []), api(comJog('/api/partidas')).catch(() => ({ partidas: [] }))]);
  itens = itens.concat(
    meus.map(d => ({ tipo: 'Meu deck', nome: d.nome, ico: icones(d.arquetipo), ir: () => { location.hash = 'meudeck-' + d.id; } })),
    S.arqLista.map(a => ({ tipo: 'Perfil de deck', nome: a.nome, ico: icones(a.slug),
      ir: () => { S.deck = a.slug; if (location.hash === '#deck') render(); else location.hash = 'deck'; } })),
    ps.partidas.slice(0, 400).map(p => ({ tipo: 'Partida', nome: `${p.resultado === 'V' ? 'Vitória' : p.resultado === 'D' ? 'Derrota' : '?'} contra ${p.adversario}`,
      extra: `${nomeDeck(p.meu_deck)} x ${nomeDeck(p.deck_adv)} · ${(p.data || '').slice(0, 10).split('-').reverse().join('/')}`,
      ir: () => { location.hash = 'partida-' + p.id; } })));
  if ($('#busca-fundo')) desenhar();
}
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); abrirBusca(); }
});
$('#abrir-busca').onclick = abrirBusca;

/* ---------------- telas (rotas) ---------------- */
// Fica aqui, no último arquivo, porque aponta para as funções render...() de todos os outros.
const ROTAS = { painel: renderPainel, partidas: renderPartidas, desempenho: renderDesempenho, meta: renderMeta,
  matchups: renderMatchups, deck: renderDeck, cartas: renderCartas, torneios: renderTorneios, ajustes: renderAjustes,
  regras: renderRegras, biblioteca: renderBiblioteca,
  decks: renderMeusDecks, partida: () => renderDetalhe(rota().id), replay: () => renderReplay(rota().id),
  meudeck: () => renderMeuDeck(rota().id), decisoes: renderDecisoes, amigos: renderAmigos, 'cartas-mu': renderCartasMatchups, revisao: renderRevisao,
  'regras-standard': renderRegrasStandard, metodologia: renderMetodologia, lista: () => renderListaOficial(rota().id) };

/* ---------------- início ---------------- */
(async () => {
  await carregarArquetipos();
  await carregarJogadores();
  await atualizarStatus();
  await render();
  setInterval(atualizarStatus, 4000);
  // primeiro uso: sem nick, sem partidas e sem ter passado pelo guia
  const cfg = S.status?.config || {};
  const partidas = S.jogadores.reduce((a, j) => a + j.partidas, 0);
  if (!cfg.guia_visto && !cfg.nick && !partidas) mostrarGuia();
  else mostrarNovidades(false);
})();
