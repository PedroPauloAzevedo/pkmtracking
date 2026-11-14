/* =====================================================================
   PROGRAMA
   ===================================================================== */
// Ajustes > Como abrir o programa: atalho na Área de Trabalho e abrir junto com o Windows.
async function desenharAtalhos() {
  const el = $('#a-atalhos'); if (!el) return;
  try { S.atalhos = await api('/api/atalhos'); } catch (e) { el.innerHTML = `<span class="aviso erro">${esc(e.message)}</span>`; return; }
  const a = S.atalhos;
  el.innerHTML = `
    <span><span class="luz ${a.area ? 'on' : ''}"></span>Atalho na Área de Trabalho</span>
    <button id="at-area">${a.area ? 'Refazer atalho' : 'Criar atalho'}</button>
    <span style="margin-left:12px"><span class="luz ${a.inicializar ? 'on' : ''}"></span>Abrir sozinho quando o Windows liga</span>
    <button id="at-ini">${a.inicializar ? 'Desligar' : 'Ligar'}</button>`;
  const mudar = async (corpo, msg) => {
    try { await api('/api/atalhos', { method: 'POST', body: JSON.stringify(corpo) }); toast(msg); }
    catch (e) { toast(e.message); }
    desenharAtalhos();
  };
  // el.querySelector, não $(): se a tela foi redesenhada enquanto a resposta vinha, os botões são os deste quadro
  el.querySelector('#at-area').onclick = () => mudar({ area: true }, 'Atalho criado na Área de Trabalho');
  el.querySelector('#at-ini').onclick = () => mudar({ inicializar: !a.inicializar }, a.inicializar ? 'O Coletor não abre mais com o Windows' : 'O Coletor vai abrir sozinho quando o Windows ligar');
}

async function renderAjustes() {
  const vez = novaTela();
  const st = await api('/api/status');
  if (telaVelha(vez)) return;
  const cfg = st.config, a = st.automatico;
  main.innerHTML = `
    ${trilha()}<header><h1>Ajustes e captura</h1></header>
    <section class="panel"><h2>Quem é você</h2>
      <div class="row"><label class="label" for="a-nick">Seu nick no TCG Live</label><input id="a-nick" value="${esc(cfg.nick)}" placeholder="exatamente como aparece no log"><button class="primary" id="a-salvar-nick">Salvar</button></div>
      <p class="muted">Sem o nick, o programa assume que você é o jogador que mais aparece nos logs.</p>
    </section>
    <section class="panel"><h2>Captura pela área de transferência</h2>
      <p>Com o programa aberto, ao fim da partida clique em <b>Battle Log</b> e no botão de exportar (canto superior direito). O log é gravado na hora.</p>
      <div class="row"><span><span class="luz ${st.coletor.ativo ? 'on' : 'off'}"></span>${st.coletor.ativo ? 'Ligada' : 'Desligada'}</span>
        <button id="a-coletor">${cfg.coletor_ativo ? 'Desligar' : 'Ligar'}</button>
        <span class="muted">${st.coletor.capturadas} capturadas nesta sessão</span></div>
      ${st.coletor.erro ? `<p class="aviso erro">${esc(st.coletor.erro)}</p>` : ''}
    </section>
    <section class="panel"><h2>Modo automático <span class="pill n">experimental</span></h2>
      <p>O programa reconhece a tela de resultado e clica em <b>Battle Log</b> e em <b>exportar</b> por você. Ele não lê a memória do jogo nem joga por você, mas é automação de cliques no cliente do jogo: use por sua conta e risco.</p>
      <ol class="sub" style="margin:0;padding-left:20px">
        <li>Instale o extra com o botão <b>Instalar o modo automático</b> (aparece abaixo quando falta). No instalador .exe já vem.</li>
        <li>Clique em <b>Usar imagens prontas</b>: baixa as imagens dos botões do projeto Full Bench (licença MIT), que servem em qualquer resolução. As suas, se houver, ficam guardadas em <span class="mono">modelos/minhas</span>.</li>
        <li>Ou recorte as suas (Windows: Win+Shift+S) e envie abaixo: o botão "Battle Log", o botão de exportar do log e, se quiser, o "Continue" e o de fechar o log.</li>
      </ol>
      <p class="muted" style="font-size:.85rem">Enquanto copia, um quadrinho vermelho cobre o botão Continue por um ou dois segundos (clique nele para liberar). Se o log não chegar, o programa tenta de novo e, se não der, avisa para você copiar à mão antes de continuar.</p>
      <div class="row">
        <button class="${cfg.modo_automatico ? '' : 'primary'}" id="a-auto">${cfg.modo_automatico ? 'Desligar modo automático' : 'Ligar modo automático'}</button>
        <label class="label" for="a-conf">Precisão</label>
        <select id="a-conf">${[0.75, 0.8, 0.85, 0.9, 0.95].map(v => `<option value="${v}" ${cfg.confianca_imagem == v ? 'selected' : ''}>${Math.round(v * 100)}%</option>`).join('')}</select>
        <span class="muted">Status: ${esc(a.status)} · ${a.cliques} exportações automáticas${a.perdidas ? ` · <b style="color:var(--bad)">${a.perdidas} perdida(s)</b>` : ''}</span>
      </div>
      ${['indisponível', 'instalando'].includes(a.status) ? `<div class="row">
        <button class="primary" id="a-instalar" ${a.status === 'instalando' ? 'disabled' : ''}>${a.status === 'instalando' ? 'Instalando… (alguns minutos)' : 'Instalar o modo automático'}</button>
        <span class="muted">Instala as bibliotecas no Python do próprio programa (pasta .venv).</span></div>` : ''}
      <div class="row">
        <button id="a-prontas">Usar imagens prontas</button>
        <label class="row" style="gap:6px"><input type="checkbox" id="a-cobrir" ${cfg.cobrir_continuar !== false ? 'checked' : ''}> Cobrir o botão Continue enquanto copia</label>
        <label class="row" style="gap:6px" title="Por até 20 segundos, os seus cliques dentro do jogo não chegam ao jogo; clique no quadrinho vermelho para soltar."><input type="checkbox" id="a-travar" ${cfg.travar_mouse !== false ? 'checked' : ''}> Segurar meus cliques no jogo enquanto copia</label>
      </div>
      <div class="grid4">${[['battle_log', 'Botão "Battle Log" (obrigatório)'], ['exportar', 'Botão de exportar (obrigatório)'], ['continuar', 'Botão "Continue" (recomendado)'], ['fechar', 'Botão de fechar o log (opcional)']].map(([k, rot]) => `
        <div class="panel" style="padding:12px;gap:8px"><span class="label">${rot}</span>
          <img src="/modelos/${k}?t=${Date.now()}" alt="" style="max-height:60px;max-width:100%;object-fit:contain;align-self:flex-start" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'muted',textContent:'Ainda não enviada'}))">
          <label class="btn" style="position:relative;overflow:hidden;align-self:flex-start">Enviar PNG<input type="file" accept="image/png" data-modelo="${k}" style="position:absolute;inset:0;opacity:0;cursor:pointer"></label></div>`).join('')}</div>
      ${a.faltando.length ? `<p class="aviso">Faltam as imagens: ${a.faltando.map(esc).join(', ')}</p>` : ''}
      ${a.erro ? `<p class="aviso erro">${esc(a.erro)}</p>` : ''}
    </section>
    <section class="panel"><h2>Procurar o log nos arquivos do jogo</h2>
      <p class="sub">Verifica se o TCG Live também grava o log em algum arquivo do computador. Só lê, não altera nada.</p>
      <div class="row"><button id="a-diag">Procurar</button></div><div id="a-diag-out"></div>
    </section>
    <section class="panel"><h2>Exportar para o Excel</h2>
      <div class="row"><a class="btn" href="${comJog('/exportar/minhas_partidas.csv')}">Minhas partidas</a><a class="btn" href="/exportar/eventos.csv">Todos os eventos dos logs</a><a class="btn" href="/exportar/torneios.csv">Partidas dos torneios</a><a class="btn" href="/exportar/meta.csv">Meta</a></div>
      <p class="muted">Arquivos .csv com ponto e vírgula, que abrem direto no Excel em português. O banco completo fica em <span class="mono">dados/tracker.db</span>.</p>
    </section>
    <section class="panel"><h2>Atualizações</h2>
      <p class="sub">O programa confere no GitHub se há versão nova e se atualiza com um clique, sem mexer nas suas partidas e decks.</p>
      <div class="grid2">
        <label class="row" style="flex-wrap:nowrap"><span class="label" style="width:110px;flex:none">Repositório</span><input id="u-repo" class="grow" value="${esc(cfg.github_repo || '')}" placeholder="usuario/tcg-tracker"></label>
        <label class="row" style="flex-wrap:nowrap"><span class="label" style="width:110px;flex:none">Token</span><input id="u-token" type="password" class="grow" value="${esc(cfg.github_token || '')}" placeholder="só se o repositório for privado"></label>
      </div>
      <div class="row"><button id="u-salvar">Salvar</button><button id="u-verificar">Verificar agora</button>
        ${st.atualizacao?.disponivel ? `<button class="primary" id="u-instalar">Atualizar para ${esc(st.atualizacao.remota)}</button>` : ''}
        <span class="muted">Instalada: ${esc(st.versao)}${st.atualizacao?.remota ? ` · No GitHub: ${esc(st.atualizacao.remota)}` : ''}${st.atualizacao?.verificado_em ? ` · verificado ${esc(st.atualizacao.verificado_em)}` : ''}</span></div>
      ${st.atualizacao?.erro ? `<p class="aviso erro">${esc(st.atualizacao.erro)}</p>` : ''}
      ${st.atualizacao?.mensagem ? `<p class="aviso">${esc(st.atualizacao.mensagem)}</p>` : ''}
      ${st.atualizacao?.disponivel && st.atualizacao.novidades?.length ? `<div class="panel" style="background:var(--sunken)">
        ${st.atualizacao.novidades.map(x => `<h3>Versão ${esc(x.versao)}: ${esc(x.titulo || '')}</h3>
          ${x.mudancas?.length ? `<ul style="margin:0;padding-left:20px">${x.mudancas.map(m => `<li>${esc(m)}</li>`).join('')}</ul>` : ''}
          ${x.como_atualizar?.length ? `<p class="label" style="margin-top:6px">Como atualizar</p><ol style="margin:0;padding-left:20px">${x.como_atualizar.map(m => `<li>${esc(m)}</li>`).join('')}</ol>` : ''}`).join('')}</div>` : ''}
      <div class="row"><button id="u-novidades">Ver as novidades de cada versão</button></div>
    </section>
    <section class="panel"><h2>Como abrir o programa</h2>
      ${st.windows ? `<p class="sub">${st.bandeja ? 'O Coletor está rodando com o ícone perto do relógio. Clique nele para abrir o painel; com o botão direito, você liga ou desliga a captura e fecha o programa.'
        : 'O Coletor está rodando com a janela preta. Se o ícone perto do relógio não aparece, atualize o programa ou rode o instalar_windows.bat de novo.'}</p>
      <div id="a-atalhos" class="row"><span class="muted">Conferindo os atalhos…</span></div>`
      : '<p class="sub">Abra pelo <span class="mono">iniciar_mac.command</span>. Deixe a janela do Terminal aberta enquanto joga.</p>'}
      ${st.janela_propria ? `<div class="row"><label class="label" for="a-abrir-em">Abrir o painel</label>
        <select id="a-abrir-em"><option value="janela" ${cfg.abrir_em !== 'navegador' ? 'selected' : ''}>Numa janela própria</option>
        <option value="navegador" ${cfg.abrir_em === 'navegador' ? 'selected' : ''}>Numa aba do navegador</option></select></div>` : ''}
      <div class="row"><button id="a-guia">Refazer o primeiro uso</button><button class="perigo" id="a-encerrar">Encerrar o programa</button></div>
    </section>`;
  const salvar = async obj => { await api('/api/config', { method: 'POST', body: JSON.stringify(obj) }); setTimeout(() => { atualizarStatus(); if (aba() === 'ajustes') renderAjustes(); }, 400); };
  $('#u-salvar').onclick = () => salvar({ github_repo: $('#u-repo').value.trim(), github_token: $('#u-token').value.trim() }).then(() => toast('Salvo'));
  $('#u-verificar').onclick = async () => { const r = await api('/api/atualizacao/verificar', { method: 'POST' }); toast(r.erro || (r.disponivel ? `Versão ${r.remota} disponível` : 'Você já está na versão mais nova')); renderAjustes(); };
  if ($('#u-instalar')) $('#u-instalar').onclick = async () => {
    if (!confirm('Atualizar agora? O programa vai se reiniciar sozinho; esta página volta a funcionar em alguns segundos.')) return;
    await api('/api/atualizacao/instalar', { method: 'POST' });
    toast('Atualizando… a página recarrega sozinha');
    const espera = setInterval(async () => { try { const s = await api('/api/status'); if (s.versao === st.atualizacao.remota) { clearInterval(espera); location.reload(); } } catch (e) {} }, 3000);
  };
  $('#u-novidades').onclick = () => mostrarNovidades(true);
  $('#a-salvar-nick').onclick = () => salvar({ nick: $('#a-nick').value.trim() }).then(() => toast('Nick salvo'));
  $('#a-coletor').onclick = () => salvar({ coletor_ativo: !cfg.coletor_ativo });
  $('#a-auto').onclick = () => salvar({ modo_automatico: !cfg.modo_automatico });
  if ($('#a-instalar')) $('#a-instalar').onclick = async () => {
    await api('/api/automatico/instalar', { method: 'POST' }); toast('Instalando o modo automático… pode levar alguns minutos.');
    const espera = setInterval(async () => { const s = await api('/api/status');
      if (s.automatico.status !== 'instalando') { clearInterval(espera); toast(s.automatico.erro || 'Modo automático instalado.'); if (location.hash === '#ajustes') render(); } }, 3000);
    render(); };
  $('#a-conf').onchange = e => salvar({ confianca_imagem: Number(e.target.value) });
  $('#a-cobrir').onchange = e => salvar({ cobrir_continuar: e.target.checked });
  $('#a-travar').onchange = e => salvar({ travar_mouse: e.target.checked });
  $('#a-prontas').onclick = async () => {
    if (!confirm('Baixar as imagens prontas dos botões (projeto Full Bench, licença MIT)? Suas imagens atuais ficam guardadas em modelos/minhas.')) return;
    try { await api('/api/modelos-prontos', { method: 'POST' }); toast('Imagens prontas salvas em modelos/'); }
    catch (e) { toast(e.message); }
    renderAjustes();
  };
  document.querySelectorAll('[data-modelo]').forEach(inp => inp.onchange = async () => {
    const fd = new FormData(); fd.append('arquivo', inp.files[0]);
    const r = await fetch('/api/modelos/' + inp.dataset.modelo, { method: 'POST', body: fd });
    const j = await r.json().catch(() => ({}));
    toast(r.ok ? 'Imagem salva em modelos/' + j.arquivo : (j.erro || 'Não consegui salvar a imagem'));
    renderAjustes();
  });
  if (st.windows) desenharAtalhos();
  if ($('#a-abrir-em')) $('#a-abrir-em').onchange = e => salvar({ abrir_em: e.target.value }).then(() => toast('Vale na próxima vez que o painel abrir'));
  $('#a-guia').onclick = () => mostrarGuia();
  $('#a-encerrar').onclick = async () => {
    if (!confirm('Encerrar o coletor? As partidas deixam de ser capturadas até você abrir o programa de novo.')) return;
    await api('/api/encerrar', { method: 'POST' }).catch(() => {});
    main.innerHTML = '<p class="vazio">Programa encerrado. Abra pelo atalho Coletor TCG Live na Área de Trabalho quando quiser.</p>';
  };
  $('#a-diag').onclick = async () => {
    $('#a-diag-out').innerHTML = '<p class="muted">Procurando… pode levar um minuto.</p>';
    const r = await api('/api/diagnostico');
    $('#a-diag-out').innerHTML = `<p class="muted">${r.arquivos_olhados} arquivos verificados em ${r.pastas.length} pastas do jogo.</p>
      ${r.encontrados.length ? `<p class="aviso">Arquivos que parecem conter o log:</p><ul class="mono">${r.encontrados.map(x => `<li>${esc(x.arquivo)} (${x.tamanho_kb} KB)</li>`).join('')}</ul>`
        : '<p>Nenhum arquivo com o log. A captura pela área de transferência continua sendo o caminho.</p>'}`;
  };
}

async function renderRegras() {
  const vez = novaTela();
  const d = await api('/api/regras');
  if (telaVelha(vez)) return;
  S.regras = S.regras || d.regras;
  main.innerHTML = `
    ${trilha()}<header><h1>Regras de leitura</h1><p class="sub">Cada linha do log é comparada com estas expressões regulares. Grupos nomeados viram colunas: <span class="mono">(?P&lt;player&gt;…)</span>, <span class="mono">(?P&lt;card&gt;…)</span>, <span class="mono">(?P&lt;target&gt;…)</span>, <span class="mono">(?P&lt;dano&gt;\\d+)</span>. Ao salvar, todas as partidas são relidas.</p></header>
    <section class="panel">
      <div class="tabela"><table class="regras"><thead><tr><th>Ativa</th><th>Nome</th><th>Tipo</th><th style="width:60%">Expressão regular</th><th></th></tr></thead><tbody>
      ${S.regras.map((r, i) => `<tr><td><input type="checkbox" data-i="${i}" class="r-ativa" ${r.ativa ? 'checked' : ''}></td>
        <td><input type="text" data-i="${i}" class="r-id" value="${esc(r.id)}" style="width:120px"></td>
        <td><select data-i="${i}" class="r-tipo">${Object.entries(d.tipos).map(([k, t]) => `<option value="${k}" ${r.tipo === k ? 'selected' : ''}>${t}</option>`).join('')}</select></td>
        <td><input type="text" data-i="${i}" class="r-re" value="${esc(r.re)}" spellcheck="false">${d.erros[r.id] ? `<div class="aviso erro">${esc(d.erros[r.id])}</div>` : ''}</td>
        <td><button class="perigo r-del" data-i="${i}">Remover</button></td></tr>`).join('')}
      </tbody></table></div>
      <div class="row"><button class="primary" id="r-salvar">Salvar e reler partidas</button><button id="r-nova">Nova regra</button><button id="r-padrao">Restaurar padrão</button></div>
    </section>
    <section class="panel"><h2>Testar uma linha</h2>
      <input id="r-teste" placeholder="Cole uma linha do log" spellcheck="false"><div class="teste" id="r-out">Nenhuma linha testada.</div>
    </section>`;
  const set = (cls, campo, conv = x => x) => document.querySelectorAll(cls).forEach(el => el.oninput = el.onchange = () => { S.regras[el.dataset.i][campo] = conv(el); });
  set('.r-ativa', 'ativa', el => el.checked); set('.r-id', 'id', el => el.value); set('.r-tipo', 'tipo', el => el.value); set('.r-re', 're', el => el.value);
  document.querySelectorAll('.r-del').forEach(b => b.onclick = () => { S.regras.splice(Number(b.dataset.i), 1); renderRegras(); });
  $('#r-nova').onclick = () => { S.regras.push({ id: 'regra_' + (S.regras.length + 1), tipo: 'outro', ativa: true, re: '^(?P<player>.+?) ' }); renderRegras(); };
  $('#r-salvar').onclick = async () => {
    try { const r = await api('/api/regras', { method: 'POST', body: JSON.stringify({ regras: S.regras }) }); toast(`Regras salvas. ${r.reprocessadas} partidas relidas.`); S.regras = null; renderRegras(); }
    catch (e) { toast(e.message); }
  };
  $('#r-padrao').onclick = async () => { if (!confirm('Voltar às regras originais?')) return; await api('/api/regras', { method: 'POST', body: JSON.stringify({ restaurar: true }) }); S.regras = null; toast('Regras padrão restauradas'); renderRegras(); };
  $('#r-teste').oninput = async e => {
    const r = await api('/api/regras/testar', { method: 'POST', body: JSON.stringify({ linha: e.target.value, regras: S.regras }) }).catch(err => ({ erro: err.message }));
    $('#r-out').textContent = r.erro ? r.erro : r.length ? r.map(x => `✓ ${x.id} (${x.tipo})\n` + Object.entries(x.grupos).map(([k, v]) => `    ${k} = "${v}"`).join('\n')).join('\n\n') : 'Nenhuma regra leu esta linha.';
  };
}
