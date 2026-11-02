/* =====================================================================
   REVISÃO DE LINHAS NÃO LIDAS
   ===================================================================== */
async function renderRevisao() {
  const [lista, regs] = await Promise.all([api('/api/revisao'), api('/api/regras')]);
  const realce = m => esc(m).replace(/\{([JCN])\}/g, (_, k) => `<b title="${{ J: 'nome de jogador', C: 'nome de carta', N: 'número' }[k]}">{${k}}</b>`);
  main.innerHTML = `
    <header><h1>Linhas não lidas</h1><p class="sub">Frases do log que nenhuma regra reconhece, agrupadas por modelo: <b>{J}</b> é um jogador, <b>{C}</b> uma carta e <b>{N}</b> um número. Para cada uma, diga se ela pode ser ignorada (não muda nenhum resultado) ou crie uma regra para lê-la. Depois de salvar, todas as partidas são relidas.</p></header>
    ${lista.length ? lista.map((g, i) => `
      <section class="panel" data-i="${i}">
        <div class="row"><span class="tag-sug ${g.sugestao.acao}">${g.sugestao.acao === 'ignorar' ? 'Sugestão: ignorar' : 'Sugestão: criar regra'}</span>
          <span class="muted">${g.vezes} vez(es) em ${g.partidas.length} partida(s) · ${esc(g.sugestao.motivo)}</span></div>
        <div class="modelo">${realce(g.modelo)}</div>
        <details><summary class="muted" style="cursor:pointer">Exemplos</summary>
          <ul class="mono" style="margin:6px 0 0;padding-left:18px">${g.exemplos.map(x => `<li><a href="#partida-${x.partida}">#${x.partida}</a> linha ${x.linha}: ${esc(x.texto)}</li>`).join('')}</ul></details>
        <div class="row">
          <button class="${g.sugestao.acao === 'ignorar' ? 'primary' : ''}" data-ignorar="${i}">Ignorar: não impacta</button>
          <button class="${g.sugestao.acao === 'regra' ? 'primary' : ''}" data-regra="${i}">Criar regra de leitura…</button>
        </div>
        <div class="form-regra" hidden style="display:flex;flex-direction:column;gap:8px">
          <div class="row" style="flex-wrap:nowrap"><span class="label" style="width:130px;flex:none">Tipo de evento</span>
            <select class="r-tipo grow">${Object.entries(regs.tipos).filter(([k]) => k !== 'ignorar').map(([k, n]) => `<option value="${k}" ${k === 'outro' ? 'selected' : ''}>${esc(n)}</option>`).join('')}</select></div>
          <div class="row" style="flex-wrap:nowrap"><span class="label" style="width:130px;flex:none">Expressão regular</span><input class="r-re grow mono" value="${esc(g.regex)}" spellcheck="false"></div>
          <p class="muted" style="font-size:.8rem">Montada a partir do modelo: o 1º jogador vira <span class="mono">player</span>, a 1ª carta <span class="mono">card</span>, a 2ª <span class="mono">target</span> e o 1º número <span class="mono">qtd</span>. Você pode editar.</p>
          <div class="teste r-teste">Testando…</div>
          <div class="row"><button class="primary r-salvar">Salvar regra e reler partidas</button></div>
        </div>
      </section>`).join('') : '<p class="vazio">Nenhuma linha não lida. Todas as frases dos seus logs são reconhecidas.</p>'}`;
  const testar = async (sec, g) => {
    const re = sec.querySelector('.r-re').value, tipo = sec.querySelector('.r-tipo').value;
    const regras = [{ id: 'teste', tipo, ativa: true, re }];
    const res = await Promise.all(g.exemplos.map(x => api('/api/regras/testar', { method: 'POST', body: JSON.stringify({ linha: x.texto, regras }) }).catch(e => ({ erro: e.message }))));
    sec.querySelector('.r-teste').textContent = res.map((r, k) => r.erro ? `✗ ${r.erro}` : r.length ? `✓ ${g.exemplos[k].texto}\n` + Object.entries(r[0].grupos).map(([a, b]) => `    ${a} = "${b}"`).join('\n') : `✗ não leu: ${g.exemplos[k].texto}`).join('\n\n');
  };
  const salvar = async (g, tipo, re) => {
    try {
      const r = await api('/api/revisao/regra', { method: 'POST', body: JSON.stringify({ tipo, re, id: tipo === 'ignorar' ? 'ign_usuario' : tipo + '_usuario', exemplos: g.exemplos.map(x => x.texto) }) });
      toast(`Regra "${r.id}" salva. ${r.relidas} partida(s) relida(s).`); renderRevisao(); atualizarStatus();
    } catch (e) { toast(e.message); }
  };
  document.querySelectorAll('[data-ignorar]').forEach(b => b.onclick = () => { const g = lista[b.dataset.ignorar]; salvar(g, 'ignorar', g.regex.replace(/\(\?P<[a-z]+>/g, '(?:')); });
  document.querySelectorAll('[data-regra]').forEach(b => b.onclick = () => {
    const sec = b.closest('section'), g = lista[b.dataset.regra], form = sec.querySelector('.form-regra');
    form.hidden = !form.hidden;
    if (!form.hidden) {
      testar(sec, g);
      sec.querySelector('.r-re').oninput = () => testar(sec, g);
      sec.querySelector('.r-tipo').onchange = () => testar(sec, g);
      sec.querySelector('.r-salvar').onclick = () => salvar(g, sec.querySelector('.r-tipo').value, sec.querySelector('.r-re').value);
    }
  });
}
