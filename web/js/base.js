/* =====================================================================
   Painel do Coletor. Conversa com o app.py pelos endereços /api/...
   Cada aba tem uma função render<Nome>() que busca os dados e desenha.
   ===================================================================== */
const $ = s => document.querySelector(s);
const main = $('#main');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (x, d = 1) => x == null ? '–' : Number(x).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = x => x == null ? '–' : fmt(x) + '%';
const CORES = ['--c1','--c2','--c3','--c4','--c5','--c6','--c7','--c8'].map(v => `var(${v})`);

const AJUDA_CONEXAO = 'Não consegui falar com o programa. Confira: 1) o Coletor está aberto: o ícone dele aparece perto do relógio do Windows (se não estiver, abra pelo atalho Coletor TCG Live da Área de Trabalho ou pelo iniciar_windows.bat); 2) o endereço no navegador é http://127.0.0.1:8765, e não um arquivo aberto com dois cliques; 3) se o Coletor estiver com a janela preta aberta e você clicou dentro dela, aperte Esc nela. Depois recarregue esta página (F5).';
async function api(url, opts = {}) {
  if (location.protocol === 'file:') throw new Error('Esta página foi aberta como arquivo. Ela só funciona pelo programa: abra pelo atalho Coletor TCG Live (ou pelo iniciar_windows.bat) e use o endereço http://127.0.0.1:8765.');
  let r;
  try { r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts }); }
  catch (e) { throw new Error(AJUDA_CONEXAO); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.erro || (j.erros ? Object.values(j.erros).join('; ') : `Erro ${r.status}`));
  return j;
}
let toastT;
function toast(msg, link, rotulo) {
  const t = $('#toast'); t.textContent = msg;
  if (link) { const a = document.createElement('a'); a.href = '#' + link; a.textContent = rotulo || 'Ver'; t.appendChild(a); }
  t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => t.hidden = true, link ? 7000 : 2600);
}

const S = { status: null, ultimaVista: null, selTorneios: [], top: 0, corte: 32, deck: '', partida: null, importando: false };

/* ---------------- componentes reutilizáveis ---------------- */
function taxaHtml(g) {
  if (!g || g.taxa == null) return '<span class="muted">–</span>';
  return `<span class="wr">${pct(g.taxa)}</span> <span class="ic">${g.ic_baixo != null ? `${fmt(g.ic_baixo, 0)}–${fmt(g.ic_alto, 0)}%` : ''}</span>`;
}
function barraDivergente(taxa) {
  if (taxa == null) return '<div class="div-barra"></div>';
  const d = Math.max(-50, Math.min(50, taxa - 50));
  const cor = d >= 0 ? 'var(--good)' : 'var(--bad)';
  const esq = d >= 0 ? 50 : 50 + d;
  return `<div class="div-barra" title="${pct(taxa)}"><span style="left:${esq}%;width:${Math.abs(d)}%;background:${cor}"></span></div>`;
}
function corTaxa(taxa) {
  if (taxa == null) return '';
  const d = Math.max(-30, Math.min(30, taxa - 50)) / 30;
  const base = d >= 0 ? 'var(--good)' : 'var(--bad)';
  return `background: color-mix(in srgb, ${base} ${Math.round(Math.abs(d) * 55)}%, var(--surface));`;
}
function tabelaGrupos(lista, titulo, extra, formato) {
  if (!lista.length) return `<p class="muted">Sem dados ainda.</p>`;
  return `<div class="tabela"><table><thead><tr><th>${titulo}</th><th class="n">Partidas</th><th class="n">V–D</th><th>Taxa de vitória</th><th></th>${extra ? '<th>Nos campeonatos</th>' : ''}</tr></thead><tbody>
    ${lista.map(g => `<tr><td>${formato ? formato(g.grupo) : esc(g.grupo)}</td><td class="n">${g.n}</td><td class="n">${g.v}–${g.d}</td><td>${taxaHtml(g)}</td><td style="width:30%">${barraDivergente(g.taxa)}</td>
      ${extra ? `<td>${g.meta_taxa != null ? `${pct(g.meta_taxa)} <span class="ic">${g.meta_n} partidas</span>` : '<span class="muted">–</span>'}</td>` : ''}</tr>`).join('')}
  </tbody></table></div>`;
}
function graficoLinhas(series, rotulosX, { min = 0, max = 100, sufixo = '%', altura = 240, marcas = [] } = {}) {
  const W = 640, H = altura, m = { l: 40, r: 14, t: 12, b: 34 };
  const n = Math.max(rotulosX.length - 1, 1);
  const x = i => m.l + (rotulosX.length === 1 ? (W - m.l - m.r) / 2 : (i / n) * (W - m.l - m.r));
  const y = v => H - m.b - ((v - min) / (max - min || 1)) * (H - m.t - m.b);
  let g = '';
  const passoY = (max - min) / 4;
  for (let k = 0; k <= 4; k++) { const v = min + k * passoY; g += `<line class="grade" x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}"/><text x="${m.l - 6}" y="${y(v) + 4}" text-anchor="end">${fmt(v, 0)}${sufixo}</text>`; }
  const pulo = Math.ceil(rotulosX.length / 8);
  rotulosX.forEach((r, i) => { if (i % pulo === 0 || i === rotulosX.length - 1) g += `<text x="${x(i)}" y="${H - 10}" text-anchor="middle">${esc(r)}</text>`; });
  // separador de época: linha tracejada onde começa a época de uma coleção nova (marcas = [{i, rotulo}], ver marcasEpoca)
  marcas.forEach(mk => { const xm = (x(mk.i - 1) + x(mk.i)) / 2, perto_do_fim = xm > W * 0.7;  // nome à esquerda da linha no fim
    g += `<line class="marca-epoca" x1="${xm}" x2="${xm}" y1="${m.t}" y2="${H - m.b}"/><text class="marca-epoca" x="${perto_do_fim ? xm - 4 : xm + 4}" y="${m.t + 10}" text-anchor="${perto_do_fim ? 'end' : 'start'}">${esc(mk.rotulo)}</text>`; });
  const linhas = series.map((s, k) => {
    const pts = s.valores.map((v, i) => v == null ? null : [x(i), y(v)]).filter(Boolean);
    if (!pts.length) return '';
    const cor = s.cor || CORES[k % CORES.length];
    const ultimo = pts[pts.length - 1];
    return `<polyline points="${pts.map(p => p.join(',')).join(' ')}" fill="none" stroke="${cor}" stroke-width="2.2" stroke-linejoin="round"/>
      <circle cx="${ultimo[0]}" cy="${ultimo[1]}" r="3.5" fill="${cor}"/>`;
  }).join('');
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img">${g}${linhas}</svg></div>
    <div class="legenda">${series.map((s, k) => `<span><i style="background:${s.cor || CORES[k % CORES.length]}"></i>${esc(s.nome)}</span>`).join('')}</div>`;
}
// Fonte dos dados de campeonato: grandes eventos (Limitless Labs), torneios online (play.limitlesstcg.com) ou todos.
// Só entram torneios Standard: os que o Limitless marca com outro formato ficam de fora das contas.
try { S.fonte = localStorage.getItem('fonte') || 'grandes'; } catch (e) { S.fonte = 'grandes'; }
const FONTES = [['grandes', 'Grandes eventos'], ['online', 'Torneios online'], ['todos', 'Todos']];
const ehStandard = t => !t.formato || t.formato === 'standard';
const naEpocaMeta = t => { const e = epocaEscolhida('torneios'); const d = (t.data || '').slice(0, 10); return !e || (d >= e.de && (!e.fim || d < e.fim)); };
const daFonte = t => ehStandard(t) && (S.fonte === 'todos' || (S.fonte === 'online') === (t.fonte === 'online')) && naEpocaMeta(t);
function seletorTorneios() {
  if (!S.torneios || !S.torneios.length) return `<div class="aviso">Nenhum torneio importado ainda. Vá em <a href="#torneios">Importar torneios</a>.</div>`;
  const lista = S.torneios.filter(daFonte), prox = S.epocas?.proxima?.torneios;
  const fontes = `<div class="row"><span class="label">Fonte</span><div class="chips">${FONTES.map(([k, n]) =>
    `<button class="chip ch-fonte" data-fonte="${k}" aria-pressed="${S.fonte === k}">${n}</button>`).join('')}</div>
    <span class="grow"></span>${seletorEpoca('torneios')}</div>
    ${prox ? `<p class="muted" style="font-size:.85rem;margin:0">A coleção <b>${esc(prox.nome)}</b> passa a valer nos torneios em ${dataCurta(prox.de)}: até lá, os torneios ainda são da época anterior.</p>` : ''}`;
  if (!lista.length) return fontes + `<div class="aviso">Nenhum torneio desta fonte${epocaEscolhida('torneios') ? ' nesta época' : ' ainda'}.${S.fonte !== 'grandes' ? ' Os torneios online chegam pela atualização automática em <a href="#torneios">Torneios</a>.' : ''}</div>`;
  if (S.fonte !== 'grandes') {  // dezenas de torneios por semana: mostra um resumo em vez de um botão para cada
    const datas = lista.map(t => t.data).filter(Boolean).sort();
    const jog = lista.reduce((a, t) => a + (t.jogadores || 0), 0);
    return fontes + `<p class="muted" style="font-size:.85rem">${lista.length} torneios${datas.length ? `, de ${fmtData(datas[0])} a ${fmtData(datas[datas.length - 1])}` : ''}, ${jog.toLocaleString('pt-BR')} jogadores.</p>`;
  }
  return fontes + `<div class="row"><span class="label">Torneios</span>
    <div class="chips">${lista.map(t => `<button class="chip ch-torneio" data-id="${t.id}" aria-pressed="${!S.selTorneios.length || S.selTorneios.includes(t.id)}">${esc(t.nome)}</button>`).join('')}</div></div>`;
}
function ligarSeletor(recarregar) {
  ligarSeletorEpoca('torneios', () => { S.selTorneios = []; recarregar(); });
  document.querySelectorAll('.ch-fonte').forEach(b => b.onclick = () => {
    S.fonte = b.dataset.fonte; S.selTorneios = [];
    try { localStorage.setItem('fonte', S.fonte); } catch (e) {}
    recarregar();
  });
  document.querySelectorAll('.ch-torneio').forEach(b => b.onclick = () => {
    const id = b.dataset.id, todos = S.torneios.filter(daFonte).map(t => t.id);
    let sel = S.selTorneios.length ? [...S.selTorneios] : todos;
    sel = sel.includes(id) ? sel.filter(x => x !== id) : [...sel, id];
    S.selTorneios = sel.length === todos.length ? [] : sel;
    recarregar();
  });
}
const qsTorneios = () => {
  const { de, ate } = comEpoca('', '', 'torneios');
  return `fonte=${S.fonte}` + (S.fonte === 'grandes' && S.selTorneios.length ? `&torneios=${S.selTorneios.join(',')}` : '')
    + (de ? `&de=${de}` : '') + (ate ? `&ate=${ate}` : '');
};
async function carregarTorneios() { await carregarEpocas(); S.torneios = await api('/api/torneios'); }

/* ---------------- épocas do meta: uma por coleção (tracker/colecoes.py) ---------------- */
// Cada coleção nova pode mudar o meta. "live" = suas partidas (a coleção chega ao TCG Live na véspera do lançamento,
// às 10h do Pacífico: aqui a hora conta); "torneios" = validade em torneio (segunda sexta-feira depois do lançamento).
// Cada época: de (incluído), fim (começo da seguinte, não incluído; null na atual) e ate (último dia, para mostrar).
// S.epoca (Minhas partidas) e S.epocaMeta (Meta e torneios) guardam a época escolhida ('' = todas) no navegador.
try { S.epoca = localStorage.getItem('epoca') || ''; S.epocaMeta = localStorage.getItem('epoca-meta') || ''; } catch (e) { S.epoca = ''; S.epocaMeta = ''; }
async function carregarEpocas() {
  if (S.epocas && Date.now() - S.epocas.lido < 10 * 60e3) return;
  try { S.epocas = { ...(await api('/api/epocas')), lido: Date.now() }; }
  catch (e) { S.epocas = S.epocas || { live: [], torneios: [], proxima: {}, lido: 0 }; }
}
const chaveEpoca = tipo => tipo === 'live' ? 'epoca' : 'epocaMeta';
function epocasVisiveis(tipo) {  // só as épocas em que há dados: desde a primeira partida (ou o primeiro torneio)
  const eps = S.epocas?.[tipo] || [], ini = tipo === 'live' ? S.epocas?.primeira_partida : S.epocas?.primeiro_torneio;
  return eps.filter(e => !ini || !e.ate || e.ate >= ini);
}
function epocaEscolhida(tipo) {
  const id = S[chaveEpoca(tipo)];
  return id ? epocasVisiveis(tipo).find(e => e.id === id) || null : null;
}
const dataCurta = iso => iso ? iso.slice(0, 10).split('-').reverse().join('/') : '';
const rotuloEpoca = e => `${e.nome} · ${e.ate ? `${dataCurta(e.de)} a ${dataCurta(e.ate)}` : `desde ${dataCurta(e.de)} (atual)`}`;
function seletorEpoca(tipo) {
  const eps = epocasVisiveis(tipo); if (!eps.length) return '';
  const sel = epocaEscolhida(tipo)?.id || '';
  const dica = tipo === 'live' ? 'Cada coleção nova pode mudar o meta. A época de uma coleção vai da chegada dela ao TCG Live (na véspera do lançamento, às 10h do horário do Pacífico: 14h ou 15h em Brasília) até a chegada da seguinte.'
    : 'Cada coleção nova pode mudar o meta. Nos torneios, uma coleção vale a partir da segunda sexta-feira depois do lançamento.';
  return `<span class="par-epoca"><label class="label" for="sel-epoca" title="${dica}">Época</label><select id="sel-epoca" title="${dica}"><option value="">Todas as épocas</option>${eps.map(e => `<option value="${esc(e.id)}" ${e.id === sel ? 'selected' : ''}>${esc(rotuloEpoca(e))}</option>`).join('')}</select></span>`;
}
function ligarSeletorEpoca(tipo, aoMudar) {
  const el = $('#sel-epoca'); if (!el) return;
  el.onchange = () => {
    S[chaveEpoca(tipo)] = el.value;
    try { localStorage.setItem(tipo === 'live' ? 'epoca' : 'epoca-meta', el.value); } catch (e) {}
    aoMudar();
  };
}
// Junta o período da tela (De/Até, 7D...) com a época escolhida: vale o pedaço em comum.
// Devolve { de, ate, antes }: de = começo (dia, ou dia e hora); ate = último dia (incluído); antes = fim da época
// no TCG Live (dia e hora, não incluído). As datas são comparadas como texto (AAAA-MM-DDTHH:MM:SS).
function comEpoca(de, ate, tipo) {
  const e = epocaEscolhida(tipo), r = { de: de || '', ate: ate || '', antes: '' };
  if (!e) return r;
  if (!r.de || e.de > r.de) r.de = e.de;
  if (e.fim && tipo === 'live') r.antes = e.fim;
  else if (e.ate && (!r.ate || e.ate < r.ate)) r.ate = e.ate;
  return r;
}
// A partida (data e hora) está dentro desse período?
const noPeriodo = (data, p) => (!p.de || data >= p.de) && (!p.ate || data.slice(0, 10) <= p.ate) && (!p.antes || data < p.antes);
// Época em que cai um momento (para os separadores da lista de partidas). No TCG Live a hora conta.
const epocaDe = (iso, tipo) => (S.epocas?.[tipo] || []).find(e => e.de <= (iso || '')) || null;
// Onde começa cada época numa sequência de dias em ordem crescente (para o separador nos gráficos): [{i, rotulo}].
function marcasEpoca(datas, tipo) {
  if (datas.length < 2) return [];
  return (S.epocas?.[tipo] || []).map(e => ({ ...e, dia: e.de.slice(0, 10) }))
    .filter(e => e.dia > (datas[0] || '') && e.dia <= (datas[datas.length - 1] || ''))
    .map(e => ({ i: datas.findIndex(d => (d || '') >= e.dia), rotulo: e.nome })).filter(mk => mk.i > 0);
}
// "05/11/2026 às 15:00" (a hora só quando o começo tem hora, como no TCG Live)
const quandoEpoca = iso => dataCurta(iso) + (iso && iso.length > 10 && iso.slice(11, 16) !== '00:00' ? ` às ${iso.slice(11, 16)}` : '');

/* ---------------- status (canto da navegação) ---------------- */
async function atualizarStatus() {
  try {
    const st = await api('/api/status');
    const anterior = S.status;
    S.status = st;
    const c = st.coletor, a = st.automatico;
    $('#estado').innerHTML = `
      <span><span class="luz ${c.ativo ? 'on' : 'off'}"></span>Captura ${c.ativo ? 'ligada' : 'desligada'}</span>
      <span><span class="luz ${a.ligado ? (a.erro ? 'warn' : 'on') : ''}"></span>Modo automático ${a.ligado ? esc(a.status) : 'desligado'}</span>
      <span><span class="luz ${st.sincronizacao.ligado ? 'on' : ''}"></span>Torneios: ${st.sincronizacao.rodando ? 'verificando…' : st.sincronizacao.ligado ? 'atualização automática' : 'atualização manual'}</span>
      ${c.ultima ? `<span>Última captura: ${esc(c.ultima.quando)}</span>` : ''}
      <span class="muted">Versão ${esc(st.versao || '?')}</span>
      ${st.atualizacao?.disponivel ? `<div class="aviso-versao">Nova versão ${esc(st.atualizacao.remota)} disponível<button onclick="location.hash='ajustes'">Ver atualização</button></div>` : ''}
      ${st.importacao.ativo ? `<span><span class="luz warn"></span>Importando ${esc(st.importacao.torneio)}: ${st.importacao.pct}%</span>` : ''}`;
    if (c.ultima && S.ultimaVista !== null && c.ultima.id !== S.ultimaVista) {
      if (c.ultima.dono) toast(`Partida #${c.ultima.id} registrada como de ${c.ultima.dono}: seu nick não joga nela. Ela fica em Amigos, fora das suas estatísticas.`, 'partida-' + c.ultima.id, 'Ver');
      else if (c.ultima.problemas?.length) toast(`Partida #${c.ultima.id} registrada, mas o log parece incompleto: ${c.ultima.problemas.join('; ')}.`, 'partida-' + c.ultima.id, 'Ver');
      else if (c.ultima.nao_lidas) toast(`Nova partida registrada (#${c.ultima.id}) com ${c.ultima.nao_lidas} linha(s) não lida(s).`, 'revisao', 'Revisar');
      else toast(`Nova partida registrada (#${c.ultima.id})`);
      if (['painel', 'partidas', 'desempenho'].includes(aba())) render();
    }
    S.ultimaVista = c.ultima ? c.ultima.id : S.ultimaVista ?? 0;
    if (st.aviso && S.avisoVisto !== undefined && st.aviso.id !== S.avisoVisto) toast(st.aviso.texto);
    S.avisoVisto = st.aviso ? st.aviso.id : null;
    if (aba() === 'torneios') { atualizarProgresso(st.importacao); atualizarSync(st.sincronizacao); }
    const bd = $('#badge-revisao'); bd.hidden = !st.linhas_pendentes; bd.textContent = st.linhas_pendentes || '';
    // cadastro de decks refeito no servidor (ex.: ícones buscados ao abrir): busca de novo e redesenha a tela
    if (S.arqVersao !== undefined && st.versao_arquetipos !== S.arqVersao) { S.arqVersao = st.versao_arquetipos; await carregarArquetipos(); render(); }
    S.arqVersao = st.versao_arquetipos;
    if (anterior && anterior.importacao.ativo && !st.importacao.ativo) {
      await carregarTorneios();
      toast(st.importacao.erro && !st.importacao.resumo ? 'Importação falhou' : 'Importação concluída');
      if (aba() === 'torneios') render();
    }
  } catch (e) { $('#estado').innerHTML = `<span><span class="luz off"></span>Programa fechado</span>`; }
}

/* ---------------- roteamento ---------------- */
// A lista de telas (ROTAS) fica no fim do inicio.js: ela aponta para funções de todos os outros arquivos.
// Cada tela pertence a uma seção do menu; as seções com várias telas mostram abas no topo (trilha()).
const SECAO = { painel: 'inicio', partidas: 'partidas', desempenho: 'partidas', decisoes: 'partidas', partida: 'partidas', replay: 'partidas',
  decks: 'decks', meudeck: 'decks', lista: 'decks',
  meta: 'meta', matchups: 'meta', deck: 'meta', cartas: 'meta', 'cartas-mu': 'meta', torneios: 'meta' };
const NOME_SECAO = { partidas: 'Minhas partidas', decks: 'Meus decks', meta: 'Meta e torneios', programa: 'Programa' };
const ABAS = {
  partidas: [['partidas', 'Partidas'], ['desempenho', 'Desempenho'], ['decisoes', 'Decisões']],
  meta: [['meta', 'Meta'], ['matchups', 'Matchups'], ['deck', 'Perfil de deck'], ['cartas', 'Uso de cartas'], ['cartas-mu', 'Cartas x matchups'], ['torneios', 'Torneios']],
};
function rota() {
  const h = location.hash.slice(1);
  const m = h.match(/^(partida|replay|meudeck|lista)-(\d+)$/);
  if (m) return { nome: m[1], id: Number(m[2]) };
  return { nome: (h in ROTAS && !['partida', 'replay', 'meudeck', 'lista'].includes(h)) ? h : 'painel' };
}
const aba = () => rota().nome;
// Cada tela desenhada ganha um número. Uma tela que demorou a receber os dados e terminou depois que você já pediu
// outra não pode cobrir a nova: as funções render...() guardam o número no começo (const vez = novaTela()) e, depois
// de esperar os dados, só desenham se ainda for a vez delas (if (telaVelha(vez)) return). Sem isso, o Início (mais
// lento) podia terminar depois e cobrir a tela de Partidas, e o "Ver todas" parecia não fazer nada.
let telaN = 0;
const novaTela = () => ++telaN;
const telaVelha = vez => vez !== telaN;
let renderN = 0;
async function render() {
  const r = aba(), n = ++renderN;
  document.querySelectorAll('nav a').forEach(a => a.classList.toggle('ativo',
    a.dataset.secao ? a.dataset.secao === SECAO[r] : a.getAttribute('href') === '#' + r));
  $('#nav-programa').open = ['ajustes', 'amigos', 'biblioteca', 'regras', 'revisao', 'regras-standard'].includes(r);
  document.body.classList.toggle('rota-lista', r === 'lista');
  if (S.lo && r !== 'lista') S.lo = null;
  if (S.rp?.timer) { clearInterval(S.rp.timer); S.rp.timer = null; }
  document.querySelectorAll('.janela-fundo').forEach(j => j.remove());
  // Tela que demora: depois de 0,3 s a tela anterior fica apagada com "Carregando…", para mostrar que o clique valeu.
  const aviso = setTimeout(() => { if (n === renderN) document.body.classList.add('carregando'); }, 300);
  try { await ROTAS[r](); }
  catch (e) { if (n === renderN) main.innerHTML = `<div class="aviso erro">${esc(e.message)}</div>`; }
  finally { clearTimeout(aviso); if (n === renderN) document.body.classList.remove('carregando'); }
}
window.addEventListener('hashchange', render);
const imgNome = (nome, alta) => `/cartas/imagem?nome=${encodeURIComponent(nome || '')}${alta ? '&q=high' : ''}`;
const imgId = (id, nome) => id ? `/cartas/imagem?id=${encodeURIComponent(id)}` : imgNome(nome);
// ---- decks: nome do Limitless + ícone do Pokémon (PokémonDB)
S.arq = {}; S.arqLista = [];
async function carregarArquetipos() {
  try { S.arqLista = await api('/api/arquetipos'); S.arq = Object.fromEntries(S.arqLista.map(a => [a.slug, a])); } catch (e) {}
}
function pokeId(nome) {
  let s = (nome || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/\u2019/g, "'").toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  s = s.replace(/-(ex|v|vstar|vmax|gx)$/, '').replace(/^(team-rocket-s|[a-z]+-s|n)-/, '');
  const mega = s.startsWith('mega-'); if (mega) s = s.slice(5);
  return s + (mega ? '-mega' : '');
}
const nomeDeck = v => (S.arq[v] && S.arq[v].nome) || v || '';
function icones(v) {
  if (!v) return '';
  const ics = S.arq[v] ? S.arq[v].icones : [pokeId(v)];
  return ics.map(i => `<img class="ico" src="/icone/${encodeURIComponent(i)}" alt="" loading="lazy">`).join('');
}
const deckHtml = v => v ? `<span class="cel-carta">${icones(v)}${esc(nomeDeck(v))}</span>` : '<span class="muted">—</span>';
function seletorDeck(id, valor, palpite) {
  const conhecido = !valor || S.arq[valor];
  return `<div class="row" style="flex-wrap:nowrap;gap:6px;min-width:0"><span id="${id}-ico" class="cel-carta">${icones(valor || palpite)}</span>
    <select id="${id}" class="grow" style="min-width:0">
      <option value="">Automático${palpite ? ` (${esc(nomeDeck(palpite))})` : ''}</option>
      ${S.arqLista.map(a => `<option value="${esc(a.slug)}" ${a.slug === valor ? 'selected' : ''}>${esc(a.nome)}</option>`).join('')}
      ${!conhecido ? `<option value="${esc(valor)}" selected>${esc(valor)}</option>` : ''}
      <option value="__outro">Outro (digitar)…</option>
    </select><input id="${id}-outro" placeholder="Nome do deck" hidden></div>`;
}
function ligarSeletorDeck(id, palpite) {
  const sel = $('#' + id), outro = $('#' + id + '-outro');
  sel.onchange = () => { outro.hidden = sel.value !== '__outro'; $('#' + id + '-ico').innerHTML = icones(sel.value === '__outro' ? '' : (sel.value || palpite)); };
  return () => sel.value === '__outro' ? outro.value.trim() : sel.value;
}
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function fmtData(iso, hora) {
  if (!iso) return '';
  const [d, tm] = iso.split('T'); const [a, m, dd] = d.split('-');
  return `${dd}/${MESES[Number(m) - 1]}/${a.slice(2)}` + (hora && tm ? ` <span class="muted">${tm.slice(0, 5)}</span>` : '');
}
const mini = (nome, id) => nome ? `<img class="mini" src="${imgId(id, nome)}" alt="" loading="lazy">` : '';
