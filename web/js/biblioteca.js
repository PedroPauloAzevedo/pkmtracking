/* =====================================================================
   BIBLIOTECA DE CARTAS
   ===================================================================== */
async function renderBiblioteca() {
  const b = await api('/api/cartas/status');
  const pr = b.progresso;
  main.innerHTML = `
    ${trilha()}<header><h1>Biblioteca de cartas</h1><p class="sub">Dados e imagens das cartas vêm do TCGdex, uma base aberta. Guardamos só a arte básica de cada carta; artes alternativas são convertidas para ela no replay, nas listas e nas análises.</p></header>
    <div class="kpis">
      <div class="kpi"><span class="label">Coleções</span><span class="v">${b.colecoes}</span><span class="d">Escarlate e Violeta e Mega Evolução</span></div>
      <div class="kpi"><span class="label">Impressões conhecidas</span><span class="v">${b.cartas}</span><span class="d">todas as artes</span></div>
      <div class="kpi"><span class="label">Cartas (arte básica)</span><span class="v">${b.artes_basicas}</span><span class="d">depois do conversor</span></div>
      <div class="kpi"><span class="label">Imagens no computador</span><span class="v">${b.imagens}</span><span class="d">baixadas ao usar</span></div>
    </div>
    <section class="panel"><h2>Atualização</h2>
      <p class="sub">Nenhuma fonte gratuita de cartas avisa quando sai coleção nova (não há webhook). O programa confere sozinho uma vez por dia e baixa só o que mudou. Última verificação: <b>${b.ultima_verificacao ? esc(b.ultima_verificacao.replace('T', ' ').slice(0, 16)) : 'nunca'}</b>${b.novos?.length ? ` · novidades: ${b.novos.map(esc).join(', ')}` : ''}.</p>
      <div class="row"><button class="primary" id="b-atualizar">Verificar agora</button><button id="b-forcar">Baixar tudo de novo</button><button id="b-imagens">Baixar todas as imagens (uso sem internet)</button></div>
      <div ${pr.ativo || pr.erro || pr.resumo ? '' : 'hidden'} id="b-prog">
        <div class="row"><span class="grow">${esc(pr.etapa || '')}</span><span class="num">${pr.pct || 0}%</span></div>
        <div class="progresso"><span style="width:${pr.pct || 0}%"></span></div>
        <p class="muted">${esc(pr.resumo || '')}</p>${pr.erro ? `<p class="aviso erro">${esc(pr.erro)}</p>` : ''}
      </div>
    </section>
    ${b.sem_imagem && Object.keys(b.sem_imagem).length ? `<section class="panel"><h2>Imagens que não carregaram</h2>
      <p class="sub">Tentamos o TCGdex (outras artes da mesma carta inclusive) e o Limitless. Clique em "Baixar tudo de novo" mais tarde: coleções recentes costumam ganhar imagens alguns dias depois do lançamento.</p>
      <p class="mono">${Object.entries(b.sem_imagem).map(([n, c]) => `${esc(n)} (${esc(c)})`).join(' · ')}</p></section>` : ''}
    ${b.nao_encontradas && b.nao_encontradas.length ? `<section class="panel"><h2>Cartas que não estão na biblioteca</h2>
      <p class="sub">Aparecem nos logs ou listas mas não existem no TCGdex com esse nome (carta muito nova, promo ou nome diferente). Aparecem como um retângulo com o nome.</p>
      <p class="mono">${b.nao_encontradas.map(esc).join(' · ')}</p></section>` : ''}
    <section class="panel"><h2>Coleções na biblioteca</h2>
      <p class="sub">Se uma coleção recente não aparece aqui, clique em "Verificar agora". Coleções novas costumam ganhar imagens no TCGdex alguns dias depois do lançamento; o programa tenta de novo sozinho.</p>
      ${b.lista_colecoes && b.lista_colecoes.length ? `<div class="tabela alta"><table><thead><tr><th>Coleção</th><th>Código</th><th>Lançamento</th><th class="n">Cartas</th><th class="n">Sem imagem no TCGdex</th></tr></thead><tbody>
        ${b.lista_colecoes.map(c => `<tr><td>${esc(c.nome)}</td><td class="mono">${esc(c.codigo || '?')}</td><td class="num">${fmtData(c.data)}</td><td class="n">${c.cartas}</td><td class="n" style="${c.sem_imagem ? 'color:var(--bad);font-weight:600' : ''}">${c.sem_imagem}</td></tr>`).join('')}</tbody></table></div>` : '<p class="muted">Nenhuma coleção baixada ainda.</p>'}
    </section>
    <section class="panel"><h2>Adicionar imagem à mão</h2>
      <p class="sub">Para cartas que ainda não estão no TCGdex ou cuja imagem não carrega. Envie o arquivo (PNG, JPG ou WEBP) ou cole o link da imagem. Com coleção e número, a imagem vale para aquela impressão (ex.: 30C 152). Marque "arte padrão" para que ela seja usada sempre que a carta aparecer pelo nome, no replay e nas análises.</p>
      <div class="row"><input id="m-nome" placeholder="Nome (ex.: Mew ex)" class="grow"><input id="m-codigo" placeholder="Coleção (ex.: 30C)" style="width:140px"><input id="m-numero" placeholder="Número" style="width:100px"></div>
      <div class="row"><input type="file" id="m-arquivo" accept="image/png,image/jpeg,image/webp"><span class="muted">ou</span><input id="m-url" placeholder="Link da imagem (https://...)" class="grow"></div>
      <div class="row"><label class="row" style="gap:6px"><input type="checkbox" id="m-pref"> Usar como arte padrão desta carta</label><span class="grow"></span><button class="primary" id="m-salvar">Adicionar imagem</button></div>
      <div id="m-lista"></div>
    </section>
    <section class="panel"><h2>Testar o conversor</h2>
      <p class="sub">Digite o nome como aparece no log, ou a coleção e o número de uma arte alternativa (ex.: TWM 214).</p>
      <div class="row"><input id="b-nome" placeholder="Nome (ex.: Dragapult ex)" class="grow"><input id="b-codigo" placeholder="Coleção (ex.: TWM)" style="width:150px"><input id="b-numero" placeholder="Número" style="width:100px"><button id="b-buscar">Converter</button></div>
      <div id="b-saida"></div>
    </section>`;
  const acao = async (url, corpo) => { try { await api(url, { method: 'POST', body: JSON.stringify(corpo || {}) }); toast('Começou. Acompanhe o progresso aqui.'); setTimeout(renderBiblioteca, 800); } catch (e) { toast(e.message); } };
  $('#b-atualizar').onclick = () => acao('/api/cartas/atualizar');
  $('#b-forcar').onclick = () => acao('/api/cartas/atualizar', { forcar: true });
  $('#b-imagens').onclick = () => acao('/api/cartas/imagens');
  const listarManuais = async () => {
    const ms = await api('/api/cartas/manuais');
    $('#m-lista').innerHTML = ms.length ? `<div class="deck-cards">${ms.map(m => `<figure><img src="${m.id ? imgId(m.id) + '&exata=1' : imgNome(m.nome)}" alt="">
      <figcaption>${esc(m.nome)} ${esc(m.codigo)} ${esc(m.numero)}${m.preferida ? ' · padrão' : ''}</figcaption>
      <button class="perigo" data-rm="${esc(m.arquivo)}" style="margin-top:4px;padding:3px 8px;font-size:.75rem">Remover</button></figure>`).join('')}</div>` : '<p class="muted">Nenhuma imagem adicionada à mão.</p>';
    document.querySelectorAll('[data-rm]').forEach(b => b.onclick = async () => { await api('/api/cartas/manuais/' + encodeURIComponent(b.dataset.rm), { method: 'DELETE' }); toast('Imagem removida'); listarManuais(); });
  };
  listarManuais();
  $('#m-salvar').onclick = async () => {
    const fd = new FormData();
    fd.append('nome', $('#m-nome').value.trim()); fd.append('codigo', $('#m-codigo').value.trim()); fd.append('numero', $('#m-numero').value.trim());
    fd.append('url', $('#m-url').value.trim()); fd.append('preferida', $('#m-pref').checked ? '1' : '');
    if ($('#m-arquivo').files[0]) fd.append('arquivo', $('#m-arquivo').files[0]);
    const r = await fetch('/api/cartas/manuais', { method: 'POST', body: fd });
    const j = await r.json().catch(() => ({}));
    toast(r.ok ? 'Imagem adicionada' : (j.erro || 'Não consegui adicionar'));
    if (r.ok) { ['m-nome', 'm-codigo', 'm-numero', 'm-url'].forEach(i => $('#' + i).value = ''); $('#m-arquivo').value = ''; listarManuais(); }
  };
  $('#b-buscar').onclick = async () => {
    const q = new URLSearchParams({ nome: $('#b-nome').value.trim(), codigo: $('#b-codigo').value.trim(), numero: $('#b-numero').value.trim() });
    const c = await api('/api/cartas/buscar?' + q).catch(e => ({ erro: e.message }));
    $('#b-saida').innerHTML = c.erro ? `<p class="aviso erro">${esc(c.erro)}</p>` : `<div class="row" style="align-items:flex-start;flex-wrap:nowrap;gap:16px">
      <img src="${imgId(c.id)}&q=high" style="width:160px;border-radius:9px" alt="${esc(c.nome)}">
      <div><h3>${esc(c.nome)}</h3><p class="muted">Arte básica: ${esc(c.codigo || c.id)} ${esc(c.numero)} · ${esc(c.set_nome)} · ${esc(c.raridade)}</p>
      <p class="muted">${esc(c.categoria)}${c.ps ? ` · ${c.ps} PS` : ''}${c.estagio ? ` · ${esc(c.estagio)}` : ''}</p></div></div>`;
  };
  if (pr.ativo) setTimeout(() => { if (aba() === 'biblioteca') renderBiblioteca(); }, 2000);
}
