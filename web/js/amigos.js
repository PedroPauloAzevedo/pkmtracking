/* ---- AMIGOS: mandar os seus logs e receber os deles */
async function renderAmigos() {
  if (!$('#pa-caminho')) main.innerHTML = '<header><h1>Amigos (trocar logs)</h1></header><p class="muted">Carregando…</p>';
  const r = await api('/api/amigos');
  const ex = r.exportacao, ult = ex.ultima_exportacao, pa = r.pasta;
  main.innerHTML = `
    <header><h1>Amigos (trocar logs)</h1><p class="sub">Junte as partidas de vários jogadores para ter mais dados nos matchups e nas Decisões. Cada um continua com o próprio programa; vocês trocam um arquivo .zip pelo WhatsApp, e-mail ou Drive. Nas telas de Minhas partidas, o filtro <b>Jogador</b> escolhe de quem ver: você, um amigo ou todos juntos.</p></header>
    <section class="panel" style="border-left:3px solid var(--accent)"><h2>Automático: pasta compartilhada no Google Drive</h2>
      <p>Todos apontam o programa para a <b>mesma pasta</b> do Google Drive. De tempos em tempos cada programa grava ali um arquivo com as próprias partidas e importa os arquivos dos outros. Ninguém precisa mandar nada à mão e nenhuma senha fica no programa.</p>
      <details ${pa.caminho ? '' : 'open'}><summary><b>Como configurar (uma vez)</b></summary>
        <ol style="margin:.5em 0 0 1.2em;line-height:1.6">
          <li>Cada um instala o <b>Google Drive para computador</b> (google.com/drive/download) e entra com a própria conta Google.</li>
          <li>Uma pessoa cria no drive.google.com uma pasta, por exemplo <b>Logs TCG</b>, e compartilha com os outros como <b>Editor</b>.</li>
          <li>Quem recebeu o convite abre <b>Compartilhados comigo</b>, clica com o botão direito na pasta e escolhe <b>Organizar &gt; Adicionar atalho</b> para o "Meu Drive". Sem esse atalho, a pasta não aparece no computador.</li>
          <li>Aqui embaixo, escolha a pasta (normalmente <span class="mono">G:\\Meu Drive\\Logs TCG</span>), ligue o automático e salve.</li>
        </ol></details>
      <div class="row" style="margin-top:10px"><input id="pa-caminho" value="${esc(pa.caminho)}" placeholder="Ex.: G:\\Meu Drive\\Logs TCG" style="flex:1;min-width:280px" list="pa-sugestoes">
        <datalist id="pa-sugestoes">${pa.sugestoes.map(x => `<option value="${esc(x)}">`).join('')}</datalist>
        <button id="pa-escolher">Escolher pasta…</button></div>
      ${!pa.caminho && pa.sugestoes.length ? `<p class="muted" style="font-size:.85rem">Achei o Google Drive em: ${pa.sugestoes.map(x => `<span class="mono">${esc(x)}</span>`).join(', ')}. Escolha a pasta compartilhada dentro dele.</p>` : ''}
      <div class="row"><label class="row" style="gap:6px"><input type="checkbox" id="pa-auto" ${pa.auto ? 'checked' : ''}> Enviar e receber sozinho a cada</label>
        <select id="pa-minutos">${[15, 30, 60, 180].map(m => `<option value="${m}" ${Number(pa.minutos) === m ? 'selected' : ''}>${m < 60 ? m + ' minutos' : m / 60 + ' hora' + (m > 60 ? 's' : '')}</option>`).join('')}</select>
        <button class="primary" id="pa-salvar">Salvar</button><button id="pa-agora" ${pa.caminho ? '' : 'disabled'}>Sincronizar agora</button></div>
      <div id="pa-estado">${pa.rodando ? '<p class="muted">Sincronizando…</p>' : ''}${pa.ultima ? `<p class="muted" style="font-size:.85rem">Última sincronização: ${fmtData(pa.ultima, true)}. ${esc(pa.mensagem || '')}</p>` : ''}${pa.erro ? `<div class="aviso erro">${esc(pa.erro)}</div>` : ''}</div>
    </section>
    <section class="panel"><h2>1. Enviar os meus logs (manual)</h2>
      <p>Jogador: <b>${esc(ex.nick || '(informe seu nick no Painel)')}</b> · ${ex.total} partida(s) suas${ult ? ` · último envio com partidas até ${fmtData(ult, true)}` : ''}.
      Só vão as <b>suas</b> partidas; as que você recebeu de amigos ficam de fora.</p>
      ${ult ? `<label class="row" style="gap:6px"><input type="checkbox" id="am-novas" ${ex.novas ? 'checked' : ''}> Só as partidas novas desde o último envio (${ex.novas})</label>` : ''}
      <div class="row"><button class="primary" id="am-exportar">Exportar meus logs</button>
        <a class="btn" id="am-baixar" href="/exportar/meus-logs.zip">ou baixar pelo navegador</a></div>
      <p class="muted" style="font-size:.85rem">O arquivo é salvo em <span class="mono">${esc(r.downloads)}</span> e a pasta abre com ele selecionado: é só arrastar para a conversa. Pode mandar tudo de novo sempre que quiser: quem recebe ignora as partidas repetidas.</p>
      <div id="am-feito"></div>
    </section>
    <section class="panel"><h2>2. Receber logs de um amigo (manual)</h2>
      <p>Escolha o .zip que ele mandou (pode escolher vários de uma vez). Também aceita os .txt da pasta <span class="mono">dados\\logs</span> do programa dele.</p>
      <div class="row"><input type="file" id="am-arquivos" accept=".zip,.txt" multiple>
        <input id="am-nome" placeholder="Nick dele (só se o arquivo não for do botão Exportar)" style="width:320px">
        <button class="primary" id="am-importar">Importar</button></div>
      <div id="am-resultado"></div>
    </section>
    <section class="panel"><h2>Jogadores importados</h2>
      ${r.amigos.length ? `<div class="tabela"><table><thead><tr><th>Jogador</th><th class="n">Partidas</th><th>Primeira</th><th>Última</th><th></th></tr></thead><tbody>
        ${r.amigos.map(a => `<tr><td><b>${esc(a.nome)}</b></td><td class="n">${a.partidas}</td><td>${fmtData(a.primeira)}</td><td>${fmtData(a.ultima)}</td>
          <td style="text-align:right;white-space:nowrap"><button data-ver="${esc(a.nome)}">Ver partidas</button> <button class="perigo" data-apagar="${esc(a.nome)}">Apagar</button></td></tr>`).join('')}
        </tbody></table></div>` : '<p class="muted">Nenhum amigo importado ainda.</p>'}
    </section>`;
  $('#pa-escolher').onclick = async () => {
    toast('Abrindo a janela para escolher a pasta (pode aparecer atrás do navegador)…');
    const x = await api('/api/amigos/pasta/escolher', { method: 'POST' }).catch(e => ({ erro: e.message }));
    if (x.pasta) $('#pa-caminho').value = x.pasta;
    else if (x.erro) toast('Não consegui abrir a janela: cole o caminho da pasta no campo.');
  };
  $('#pa-salvar').onclick = async () => {
    const caminho = $('#pa-caminho').value.trim();
    if ($('#pa-auto').checked && !caminho) { toast('Escolha a pasta primeiro'); return; }
    await api('/api/config', { method: 'POST', body: JSON.stringify({ pasta_compartilhada: caminho, pasta_auto: $('#pa-auto').checked, pasta_minutos: Number($('#pa-minutos').value) }) });
    toast($('#pa-auto').checked ? 'Salvo. Vou sincronizar agora e depois de tempos em tempos.' : 'Salvo');
    setTimeout(renderAmigos, 2500);
  };
  $('#pa-agora').onclick = async () => {
    $('#pa-agora').disabled = true; $('#pa-estado').innerHTML = '<p class="muted">Sincronizando…</p>';
    try { await api('/api/amigos/pasta/sincronizar', { method: 'POST' }); } catch (e) { toast(e.message); }
    await carregarJogadores(); renderAmigos();
  };
  const novas = () => $('#am-novas') && $('#am-novas').checked;
  const linkBaixar = () => { $('#am-baixar').href = '/exportar/meus-logs.zip' + (novas() ? '?so_novas=1' : ''); };
  if ($('#am-novas')) $('#am-novas').onchange = linkBaixar; linkBaixar();
  $('#am-baixar').onclick = () => setTimeout(renderAmigos, 1500);
  $('#am-exportar').onclick = async () => {
    try { const x = await api('/api/amigos/exportar', { method: 'POST', body: JSON.stringify({ so_novas: novas() }) });
      await renderAmigos();
      $('#am-feito').innerHTML = `<div class="aviso">Pronto: ${x.partidas} partida(s) em <span class="mono">${esc(x.arquivo)}</span>. Mande esse arquivo para o seu amigo.</div>`; }
    catch (e) { $('#am-feito').innerHTML = `<div class="aviso erro">${esc(e.message)}</div>`; }
  };
  $('#am-importar').onclick = async () => {
    const inp = $('#am-arquivos');
    if (!inp.files.length) { toast('Escolha o arquivo que o seu amigo mandou'); return; }
    const fd = new FormData(); [...inp.files].forEach(f => fd.append('arquivos', f)); fd.append('nome', $('#am-nome').value.trim());
    $('#am-importar').disabled = true; $('#am-resultado').innerHTML = '<p class="muted">Lendo os logs…</p>';
    const resp = await fetch('/api/amigos/importar', { method: 'POST', body: fd }).catch(() => null);
    const j = resp ? await resp.json().catch(() => ({})) : { erro: AJUDA_CONEXAO };
    $('#am-importar').disabled = false;
    if (!resp || !resp.ok) { $('#am-resultado').innerHTML = `<div class="aviso erro">${esc(j.erro || 'Não consegui importar.')}</div>`; return; }
    await carregarJogadores(); await renderAmigos();
    $('#am-resultado').innerHTML = `<div class="aviso">Logs de <b>${esc(j.nome)}</b>: ${j.novas} partida(s) nova(s)${j.repetidas ? `, ${j.repetidas} já estavam aqui` : ''}${j.invalidos ? `, ${j.invalidos} arquivo(s) não eram log` : ''}. <a href="#partidas" id="am-ver-novo">Ver partidas dele</a></div>`;
    $('#am-ver-novo').onclick = () => { S.jogador = j.nome; try { localStorage.setItem('jogador', j.nome); } catch (e) {} };
  };
  document.querySelectorAll('[data-ver]').forEach(b => b.onclick = () => { S.jogador = b.dataset.ver; try { localStorage.setItem('jogador', S.jogador); } catch (e) {} location.hash = 'partidas'; });
  document.querySelectorAll('[data-apagar]').forEach(b => b.onclick = async () => {
    if (b.dataset.confirmar !== '1') { b.dataset.confirmar = '1'; b.textContent = 'Confirmar: apagar todas as partidas dele'; return; }
    const x = await api('/api/amigos/' + encodeURIComponent(b.dataset.apagar), { method: 'DELETE' });
    if (S.jogador === b.dataset.apagar) S.jogador = '';
    toast(`${x.apagadas} partida(s) apagada(s)`); await carregarJogadores(); renderAmigos();
  });
}
