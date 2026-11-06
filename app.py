"""
Coletor de Partidas TCG Live
----------------------------
Como usar:  python app.py
Depois abra http://localhost:8765 (o navegador abre sozinho).

O que acontece quando ele está rodando:
  1. O coletor vigia a área de transferência. Ao exportar o Battle Log no fim da
     partida, o log é gravado sozinho no banco (dados/tracker.db).
  2. Se você ligar o modo automático (e configurar as imagens em modelos/), o programa
     também clica em "Battle Log" e "Exportar" por você.
  3. O painel no navegador mostra suas estatísticas e os dados dos campeonatos.

Outros comandos:
  python app.py --diagnostico     procura arquivos de log do jogo no disco
  python app.py --importar 0078   importa um torneio do Limitless Labs sem abrir o painel
  python app.py --sincronizar     importa os torneios recentes que ainda faltam e sai
"""
import argparse
import csv
import io
import socket
import sys
import threading

from flask import Flask, Response, jsonify, request, send_from_directory

from tracker import (analises, atalhos, atualizador, avisos, bandeja, banco, cartas, colecoes, compartilhar, config,
                     decks, diagnostico, janela, leitor, limitless, lista_oficial, novidades, regras_jogo, replay, revisao)
from tracker.auto_export import auto
from tracker.coletor import coletor

app = Flask(__name__, static_folder=None)
app.json.sort_keys = False  # mantém a ordem dos dados (ex.: Top 8, Top 16, ...)
app.json.ensure_ascii = False
PASTA_WEB = config.RAIZ / "web"
VERSAO = atualizador.versao_local()  # vem de versao.txt; aparece no painel e na janela preta
MODO = {"bandeja": False}  # True quando o programa roda com o ícone perto do relógio (sem janela preta)


# ------------------------------------------------------------------ proteção
# O painel só aceita pedidos dele mesmo. Sem isto, qualquer site aberto no navegador poderia mandar
# comandos para 127.0.0.1 (por exemplo, trocar o repositório de atualização e mandar "atualizar").
#   - Host: só 127.0.0.1/localhost (evita o truque de "DNS rebinding");
#   - Origin / Sec-Fetch-Site: o navegador diz de que site veio o pedido; outro site = recusado.
# Programas locais (scripts, o atualizador, o desinstalador) não mandam Origin e continuam funcionando.
HOSTS_LOCAIS = {"127.0.0.1", "localhost", "::1"}


@app.before_request
def so_pedidos_do_painel():
    from urllib.parse import urlsplit
    proprio = urlsplit("//" + (request.host or ""))
    if (proprio.hostname or "") not in HOSTS_LOCAIS:
        return jsonify({"erro": "Endereço não permitido."}), 403
    origem = request.headers.get("Origin")
    if origem:
        o = urlsplit(origem)
        if o.scheme != "http" or (o.hostname or "") not in HOSTS_LOCAIS or o.port != proprio.port:
            return jsonify({"erro": "Pedido de outro site recusado."}), 403
    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        return jsonify({"erro": "Pedido de outro site recusado."}), 403
    if request.method != "GET":
        analises._memoria_listas["t"] = 0.0  # algo pode ter mudado em Meus decks: relê na próxima análise


# ------------------------------------------------------------------ páginas
@app.get("/")
def inicio():
    return send_from_directory(PASTA_WEB, "index.html")


@app.get("/api/exemplo-log")
def exemplo_log():
    """Log de exemplo para o teste do primeiro uso (o coletor reconhece e não grava)."""
    return Response((config.RAIZ / "exemplos" / "log_de_exemplo.txt").read_text(encoding="utf-8"), mimetype="text/plain")


@app.get("/icone.ico")
def icone_aba():
    return send_from_directory(PASTA_WEB, "icone.ico")


@app.get("/web/<path:arquivo>")
def arquivo_painel(arquivo):
    """Partes do painel (estilo.css e web/js/*.js). Só CSS e JS de dentro de web/; sem cache,
    para a versão nova aparecer logo depois de atualizar."""
    if not arquivo.endswith((".css", ".js")):
        return Response(status=404)
    resp = send_from_directory(PASTA_WEB, arquivo, max_age=0)
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ------------------------------------------------------------------ status e configurações
@app.get("/api/status")
def status():
    cfg = config.ler_config()
    return jsonify({
        "versao": VERSAO,
        "coletor": {"ativo": coletor.ativo, "erro": coletor.erro, "ultima": coletor.ultima, "capturadas": coletor.capturadas,
                    "teste_em": coletor.teste_em},
        "automatico": {"ligado": cfg["modo_automatico"], "status": auto.status, "erro": auto.erro,
                       "cliques": auto.cliques, "perdidas": auto.perdidas, "faltando": auto.faltando()},
        "aviso": avisos.ultimo(),
        "importacao": limitless.progresso,
        "sincronizacao": limitless.estado_sync,
        "biblioteca": cartas.progresso,
        "atualizacao": atualizador.estado,
        "linhas_pendentes": _contar_pendentes(),
        "bandeja": MODO["bandeja"],
        "windows": atalhos.disponivel(),
        "janela_propria": janela.disponivel(),
        "config": cfg,
    })


# ------------------------------------------------------------------ atalhos do Windows
@app.get("/api/atalhos")
def ver_atalhos():
    return jsonify({"disponivel": atalhos.disponivel(), "area": atalhos.existe("area"),
                    "inicializar": atalhos.existe("inicializar")})


@app.post("/api/atalhos")
def mudar_atalhos():
    """{"area": true} cria o atalho na Área de Trabalho; {"inicializar": false} tira do início do Windows."""
    corpo = request.get_json(force=True) or {}
    try:
        for onde in ("area", "inicializar"):
            if onde in corpo:
                atalhos.criar(onde) if corpo[onde] else atalhos.remover(onde)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400
    return ver_atalhos()


_cache_pendentes = {"t": 0, "n": 0}


def _contar_pendentes():
    """Quantas partidas têm linhas não lidas (recalcula no máximo a cada 20 s)."""
    import time
    if time.time() - _cache_pendentes["t"] > 20:
        _cache_pendentes.update(t=time.time(), n=sum(1 for p in banco.listar_partidas() if p["qtd_nao_lidas"]))
    return _cache_pendentes["n"]


def _jogador_pedido():
    """Filtro Jogador do pedido: vários (?jogadores=&jogadores=Fulano; vazio = você), como manda a caixa de opções
    do painel; ou um só (?jogador=, como nas versões antigas: vazio = você, * = todos)."""
    a = request.args
    return a.getlist("jogadores") if "jogadores" in a else a.get("jogador", "")


@app.get("/api/decisoes")
def api_decisoes():
    a = request.args
    return jsonify(analises.decisoes(config.ler_config()["nick"], a.get("de"), a.get("ate"), a.get("deck"),
                                     a.get("lista"), a.get("adv"), int(a.get("min", 3)), _jogador_pedido(),
                                     a.get("ordem", ""), a.get("antes")))


# ------------------------------------------------------------------ regras do Standard (base de regras)
@app.get("/api/regras-standard")
def regras_standard():
    return jsonify(regras_jogo.status())


@app.post("/api/regras-standard/atualizar")
def regras_standard_atualizar():
    regras_jogo.verificar_atualizacao()
    return jsonify(regras_jogo.status())


# ------------------------------------------------------------------ novidades de cada versão
@app.get("/api/novidades")
def ver_novidades():
    return jsonify(novidades.para_mostrar())


@app.post("/api/novidades/vista")
def novidades_vista():
    novidades.marcar_vista()
    return jsonify({"ok": True})


@app.get("/api/revisao")
def revisao_lista():
    return jsonify(revisao.pendentes())


@app.post("/api/revisao/regra")
def revisao_regra():
    corpo = request.get_json(force=True) or {}
    try:
        r = revisao.adicionar_regra(corpo.get("id"), corpo.get("tipo", "outro"), corpo.get("re", ""), corpo.get("exemplos", []))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    _cache_pendentes["t"] = 0
    return jsonify(r)


@app.post("/api/config")
def salvar_config():
    cfg = config.ler_config()
    novo = request.get_json(force=True) or {}
    for chave in ("nick", "modo_automatico", "confianca_imagem", "intervalo_coletor", "coletor_ativo",
                  "cobrir_continuar", "abrir_em", "guia_visto",
                  "online_ativo", "online_min_jogadores", "online_dias",
                  "sincronizar_auto", "sincronizar_horas", "sincronizar_dias", "listas_top",
                  "github_repo", "github_ramo", "github_token", "pasta_compartilhada", "pasta_auto", "pasta_minutos"):
        if chave in novo:
            cfg[chave] = novo[chave]
    config.salvar_config(cfg)
    if cfg["coletor_ativo"]:
        coletor.iniciar()
    else:
        coletor.parar()
    if cfg["modo_automatico"]:
        auto.iniciar()
    else:
        auto.parar()
    if cfg["sincronizar_auto"]:
        limitless.sincronizador.iniciar()
    else:
        limitless.sincronizador.parar()
    if cfg.get("pasta_auto"):
        compartilhar.sincronizador_pasta.iniciar()
        if novo.get("pasta_auto") or novo.get("pasta_compartilhada"):
            compartilhar.sincronizador_pasta.agora()
    else:
        compartilhar.sincronizador_pasta.parar()
    if "nick" in novo:  # nick novo: partidas em que você não joga passam para Amigos
        banco.separar_partidas_de_outros()
    return jsonify(cfg)


# ------------------------------------------------------------------ partidas pessoais
@app.get("/api/partidas")
def partidas():
    a = request.args
    return jsonify(analises.analise_pessoal(config.ler_config()["nick"], a.get("de"), a.get("ate"), a.get("deck"), a.get("tag"),
                                            a.get("lista"), a.get("adv"), _jogador_pedido(), a.get("antes")))


# ------------------------------------------------------------------ amigos: trocar logs
@app.get("/api/jogadores-locais")
def jogadores_locais():
    return jsonify(analises.jogadores(config.ler_config()["nick"]))


def _seguro(func, padrao):
    try:
        return func()
    except Exception as e:
        print("[amigos]", e)
        return padrao


@app.get("/api/amigos")
def lista_amigos():
    cfg = config.ler_config()
    return jsonify({"amigos": compartilhar.amigos(), "exportacao": compartilhar.resumo_exportacao(),
                    "downloads": str(compartilhar.pasta_downloads()),
                    "pasta": {"caminho": cfg.get("pasta_compartilhada", ""), "auto": bool(cfg.get("pasta_auto")),
                              "minutos": cfg.get("pasta_minutos", 30), "sugestoes": _seguro(compartilhar.sugestoes_pasta, []),
                              **compartilhar.estado_pasta}})


@app.post("/api/amigos/pasta/escolher")
def escolher_pasta():
    return jsonify(compartilhar.escolher_pasta_dialogo())


@app.post("/api/amigos/pasta/sincronizar")
def sincronizar_pasta_agora():
    compartilhar.sincronizador_pasta.rodar_uma_vez()
    _cache_pendentes["t"] = 0
    return jsonify(compartilhar.estado_pasta)


@app.post("/api/amigos/exportar")
def exportar_logs():
    corpo = request.get_json(force=True) or {}
    try:
        return jsonify(compartilhar.exportar_para_downloads(bool(corpo.get("so_novas"))))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except OSError as e:
        return jsonify({"erro": f"Não consegui salvar o arquivo: {e}"}), 500


@app.get("/exportar/meus-logs.zip")
def baixar_logs():
    try:
        nome, conteudo, _ = compartilhar.montar_zip(request.args.get("so_novas") == "1")
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    return Response(conteudo, mimetype="application/zip", headers={"Content-Disposition": f'attachment; filename="{nome}"'})


@app.post("/api/amigos/importar")
def importar_logs():
    arquivos = [(f.filename or "", f.read()) for f in request.files.getlist("arquivos")]
    if not arquivos:
        return jsonify({"erro": "Escolha o arquivo .zip que o seu amigo mandou."}), 400
    try:
        r = compartilhar.importar(arquivos, request.form.get("nome", ""))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    _cache_pendentes["t"] = 0
    return jsonify(r)


@app.delete("/api/amigos/<path:nome>")
def apagar_amigo(nome):
    return jsonify({"apagadas": compartilhar.apagar_amigo(nome)})


@app.post("/api/partidas")
def nova_partida():
    texto = (request.get_json(force=True) or {}).get("texto", "")
    if not leitor.parece_log(texto):
        return jsonify({"erro": "Isso não parece um log do TCG Live. Confira se copiou o log inteiro, começando em \"Setup\" e com as linhas \"Fulano's Turn\"."}), 400
    pid, nova = banco.inserir_partida(texto, "manual", config.ler_regras())
    p = banco.obter_partida(pid)
    _cache_pendentes["t"] = 0
    return jsonify({"id": pid, "nova": nova, "nao_lidas": len(p["nao_lidas"]) if p else 0,
                    "problemas": p["resumo"].get("problemas", []) if p else [], "dono": p["dono"] if p else ""})


@app.get("/api/partidas/<int:pid>")
def partida(pid):
    p = banco.obter_partida(pid)
    if not p:
        return jsonify({"erro": "Partida não encontrada."}), 404
    todas = banco.listar_partidas()
    p["visao"] = analises.visao(p, analises.perspectiva(p, analises.descobrir_eu(todas, config.ler_config()["nick"])))
    return jsonify(p)


@app.get("/api/partidas/<int:pid>/replay")
def replay_partida(pid):
    p = banco.obter_partida(pid)
    if not p:
        return jsonify({"erro": "Partida não encontrada."}), 404
    r = replay.gerar(p["texto"], config.ler_regras())
    r["eu"] = analises.perspectiva(p, analises.descobrir_eu(banco.listar_partidas(), config.ler_config()["nick"]))
    r["id"] = pid
    r["versoes"] = decks.resolver_versoes(r, p, r["eu"])  # versão certa de cartas com o mesmo nome
    return jsonify(r)


# ------------------------------------------------------------------ biblioteca de cartas
@app.get("/cartas/imagem")
def imagem_carta():
    """Imagem da arte básica, por id (?id=sv06-130) ou por nome (?nome=Dragapult ex)."""
    q = "high" if request.args.get("q") == "high" else "low"
    e = None
    if request.args.get("id") and request.args.get("exata"):
        e = cartas.indice()["cartas"].get(request.args["id"])  # aquela impressão exata (ex.: imagem enviada à mão)
    elif request.args.get("id"):
        e = cartas._basica_de(request.args["id"]) or cartas.indice()["cartas"].get(request.args["id"])
    elif request.args.get("nome"):
        e = cartas.por_nome(request.args["nome"])
    caminho = cartas.caminho_imagem(e["id"], q) if e else None
    if caminho:
        tipo = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(caminho.suffix.lower(), "image/webp")
        resp = send_from_directory(caminho.parent, caminho.name, mimetype=tipo)
        resp.headers["Cache-Control"] = "public, max-age=604800"
        return resp
    return Response(cartas.imagem_reserva(request.args.get("nome") or (e or {}).get("nome") or "?"),
                    mimetype="image/svg+xml", headers={"Cache-Control": "no-cache"})


@app.get("/icone/<nome>")
def icone(nome):
    """Ícone do Pokémon (PokémonDB). Aceita o id do ícone (lopunny-mega) ou o nome da carta."""
    caminho = decks.caminho_icone(decks.pokemon_id(nome) if " " in nome or nome[:1].isupper() else nome)
    if caminho:
        resp = send_from_directory(caminho.parent, caminho.name, mimetype="image/png")
        resp.headers["Cache-Control"] = "public, max-age=604800"
        return resp
    return Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 56"><circle cx="34" cy="30" r="14" fill="none" stroke="#95A0B5" stroke-width="3"/><line x1="20" y1="30" x2="48" y2="30" stroke="#95A0B5" stroke-width="3"/></svg>',
                    mimetype="image/svg+xml")


@app.get("/api/arquetipos")
def lista_arquetipos():
    lista = sorted(decks.arquetipos().values(), key=lambda a: (-a.get("jogadores", 0), a["nome"]))
    aprendidos = decks.icones_aprendidos()   # suas correções de ícone valem em todas as telas
    lista = [{**x, "icones": aprendidos.get(x["slug"], x["icones"])} for x in lista]
    return jsonify(lista)


# ------------------------------------------------------------------ meus decks
@app.get("/api/decks")
def meus_decks():
    nick = config.ler_config()["nick"]
    saida = []
    for d in decks.listar_decks():
        dados = analises.analise_pessoal(nick, lista=d["id"])
        d["placar"] = dados["total"]
        d.pop("lista_oficial", None)
        cartas_deck = banco.consultar("SELECT * FROM meus_decks_cartas WHERE deck_id=? ORDER BY rowid", (d["id"],))
        d["standard_ok"] = lista_oficial.validar(lista_oficial.gerar({"cartas": cartas_deck}))["valida"]
        saida.append(d)
    return jsonify(saida)


@app.post("/api/decks")
def novo_deck():
    try:
        did, avisos = decks.salvar_deck(request.get_json(force=True) or {})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    vinculadas = sum(1 for p in banco.listar_partidas() if not p.get("deck_id") and decks.vincular_automatico(p["id"]) == did)
    return jsonify({"id": did, "avisos": avisos, "vinculadas": vinculadas})


@app.get("/api/decks/<int:did>")
def ver_deck(did):
    d = decks.obter_deck(did)
    if not d:
        return jsonify({"erro": "Deck não encontrado."}), 404
    d["analise"] = analises.analise_pessoal(config.ler_config()["nick"], lista=did)
    d["standard"] = lista_oficial.validar(lista_oficial.gerar(d))
    d["lista_oficial_editada"] = bool(d.pop("lista_oficial", ""))
    return jsonify(d)


def _cartas_para_probabilidade(did):
    """Cartas do deck com a marcação de Pokémon Básico (vem da biblioteca de cartas). None se o deck não existe."""
    d = decks.obter_deck(did)
    if not d:
        return None, 0
    ind = cartas.indice().get("cartas", {})
    lista, sem_info = [], 0
    for c in d["cartas"]:
        e = ind.get(c.get("carta_id") or "") or {}
        if c["secao"] == "Pokémon" and not e.get("estagio"):
            sem_info += c["qtd"]
        lista.append({"nome": c.get("carta_base") or c["nome"], "qtd": c["qtd"], "secao": c["secao"],
                      "basico": c["secao"] == "Pokémon" and (e.get("estagio") or "").lower() == "basic"})
    return lista, sem_info


@app.get("/api/decks/<int:did>/consistencia")
def consistencia_deck(did):
    """Probabilidades da lista (mulligan, carta na mão, nos prêmios) e o mulligan real das suas partidas."""
    from tracker import probabilidades
    lista, sem_info = _cartas_para_probabilidade(did)
    if lista is None:
        return jsonify({"erro": "Deck não encontrado."}), 404
    r = probabilidades.resumo_lista(lista)
    r["sem_estagio"] = sem_info  # Pokémon sem estágio conhecido (biblioteca de cartas incompleta)
    jogadas = [l for l in analises.analise_pessoal(config.ler_config()["nick"], lista=did)["partidas"] if l["resultado"]]
    r["observado"] = {"partidas": len(jogadas), "com_mulligan": sum(1 for l in jogadas if l["mulligan_eu"])}
    return jsonify(r)


@app.get("/api/decks/<int:did>/combo")
def combo_deck(did):
    """Chance de ter as cartas A e B juntas até o 1º, 2º e 3º turno."""
    from tracker import probabilidades
    lista, _ = _cartas_para_probabilidade(did)
    if lista is None:
        return jsonify({"erro": "Deck não encontrado."}), 404
    a, b = request.args.get("a", ""), request.args.get("b", "")
    ca = [c for c in lista if c["nome"] == a]
    cb = [c for c in lista if c["nome"] == b]
    if not ca or not cb or a == b:
        return jsonify({"erro": "Escolha duas cartas diferentes da lista."}), 400
    basicos = sum(c["qtd"] for c in lista if c["basico"])
    qa, qb, deck = sum(c["qtd"] for c in ca), sum(c["qtd"] for c in cb), sum(c["qtd"] for c in lista)
    return jsonify({"turnos": [probabilidades.combo(qa, qb, basicos, ca[0]["basico"], cb[0]["basico"], t, deck)
                               for t in (0, 1, 2, 3)]})


@app.put("/api/decks/<int:did>")
def editar_deck(did):
    corpo = request.get_json(force=True) or {}
    if "icones" in corpo and set(corpo) == {"icones"}:
        icones = decks.salvar_icones(did, corpo["icones"])
        if icones is None:
            return jsonify({"erro": "Deck não encontrado."}), 404
        return jsonify({"ok": True, "icones": decks.obter_deck(did)["icones"]})
    if corpo and set(corpo) <= {"ativo", "favorito"}:
        with banco.conectar() as con:
            for campo in ("ativo", "favorito"):
                if campo in corpo:
                    con.execute(f"UPDATE meus_decks SET {campo}=? WHERE id=?", (1 if corpo[campo] else 0, did))
        return jsonify({"ok": True})
    try:
        _, avisos = decks.salvar_deck(corpo, did)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    return jsonify({"ok": True, "avisos": avisos})


@app.get("/api/decks/<int:did>/lista-oficial")
def lista_oficial_ver(did):
    r = lista_oficial.obter(did)
    return (jsonify(r), 200) if r else (jsonify({"erro": "Deck não encontrado."}), 404)


@app.put("/api/decks/<int:did>/lista-oficial")
def lista_oficial_salvar(did):
    corpo = request.get_json(force=True) or {}
    r = lista_oficial.salvar(did, corpo.get("linhas") or {}, corpo.get("jogador"))
    return (jsonify(r), 200) if r else (jsonify({"erro": "Deck não encontrado."}), 404)


@app.delete("/api/decks/<int:did>/lista-oficial")
def lista_oficial_descartar(did):
    r = lista_oficial.descartar(did)
    return (jsonify(r), 200) if r else (jsonify({"erro": "Deck não encontrado."}), 404)


@app.post("/api/lista-oficial/validar")
def lista_oficial_validar():
    corpo = request.get_json(force=True) or {}
    return jsonify(lista_oficial.validar(corpo.get("linhas") or {}))


@app.delete("/api/decks/<int:did>")
def apagar_deck(did):
    with banco.conectar() as con:
        con.execute("DELETE FROM meus_decks_cartas WHERE deck_id=?", (did,))
        con.execute("DELETE FROM meus_decks WHERE id=?", (did,))
        con.execute("UPDATE partidas SET deck_id=NULL WHERE deck_id=?", (did,))
    banco.marcar_mudanca()
    return jsonify({"ok": True})


@app.post("/api/decks/vincular")
def vincular_todas():
    """Procura, nas partidas sem lista, as que batem com alguma lista de Meus decks."""
    n = sum(1 for p in banco.listar_partidas() if not p.get("deck_id") and decks.vincular_automatico(p["id"]))
    return jsonify({"vinculadas": n})


@app.post("/api/atualizacao/verificar")
def verificar_atualizacao():
    return jsonify(atualizador.verificar())


@app.post("/api/atualizacao/instalar")
def instalar_atualizacao():
    if atualizador.estado["atualizando"]:
        return jsonify({"erro": "Já está atualizando."}), 409
    threading.Thread(target=atualizador.atualizar, daemon=True).start()
    return jsonify({"ok": True})


@app.get("/api/cartas/matchups")
def cartas_matchups():
    a = request.args
    r = analises.cartas_matchups(a.get("arq", ""), a.get("carta", ""), _lista_torneios(), int(a.get("k", 8)), int(a.get("min", 5)))
    return (jsonify(r), 200) if r else (jsonify({"erro": "Nenhum jogador com esse deck nos torneios escolhidos."}), 404)


@app.get("/api/cartas/status")
def cartas_status():
    return jsonify(cartas.status())


@app.get("/api/cartas/buscar")
def cartas_buscar():
    """Mostra o que o conversor faz: nome, ou coleção + número -> arte básica."""
    a = request.args
    e = cartas.converter(a.get("codigo"), a.get("numero"), a.get("nome")) if a.get("codigo") else cartas.por_nome(a.get("nome"))
    return jsonify(cartas.info_publica(e) or {"erro": "Carta não encontrada na biblioteca."})


@app.post("/api/cartas/atualizar")
def cartas_atualizar():
    if cartas.progresso["ativo"]:
        return jsonify({"erro": "A biblioteca já está sendo atualizada."}), 409
    threading.Thread(target=cartas.atualizar, kwargs={"forcar": bool((request.get_json(silent=True) or {}).get("forcar"))}, daemon=True).start()
    return jsonify({"ok": True})


@app.get("/api/cartas/manuais")
def cartas_manuais():
    return jsonify(cartas.listar_manuais())


@app.post("/api/cartas/manuais")
def cartas_manual_nova():
    """Adiciona uma imagem de carta à mão (arquivo enviado ou link da imagem)."""
    f = request.form
    conteudo = request.files["arquivo"].read() if "arquivo" in request.files else b""
    if not conteudo and f.get("url"):
        import requests as rq
        try:
            r = rq.get(f["url"], timeout=20, headers={"User-Agent": "TCGLiveTracker/1.0"})
            conteudo = r.content if r.status_code == 200 else b""
        except rq.RequestException:
            conteudo = b""
        if not conteudo:
            return jsonify({"erro": "Não consegui baixar a imagem desse link."}), 400
    if not conteudo:
        return jsonify({"erro": "Escolha um arquivo de imagem ou cole o link da imagem."}), 400
    try:
        cartas.adicionar_manual(f.get("nome", ""), f.get("codigo", ""), f.get("numero", ""), conteudo,
                                f.get("preferida") in ("1", "true", "on"))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    banco.reconverter_listas()
    return jsonify({"ok": True})


@app.delete("/api/cartas/manuais/<arquivo>")
def cartas_manual_apagar(arquivo):
    cartas.remover_manual(arquivo)
    banco.reconverter_listas()
    return jsonify({"ok": True})


@app.post("/api/modelos/<nome>")
def enviar_modelo(nome):
    """Recebe as imagens dos botões usadas pelo modo automático."""
    from tracker.auto_export import MODELOS
    if nome not in MODELOS or "arquivo" not in request.files:
        return jsonify({"erro": "Envie o arquivo PNG do botão."}), 400
    conteudo = request.files["arquivo"].read()
    if conteudo[:4] != b"\x89PNG":
        return jsonify({"erro": "A imagem precisa estar em PNG."}), 400
    config.PASTA_MODELOS.mkdir(parents=True, exist_ok=True)
    (config.PASTA_MODELOS / MODELOS[nome]).write_bytes(conteudo)
    cfg = config.ler_config()  # imagem sua: o tamanho dela no monitor é descoberto de novo
    cfg["modelos_prontos"] = [k for k in cfg.get("modelos_prontos") or [] if k != nome]
    config.salvar_config(cfg)
    from tracker.auto_export import esquecer_escala
    esquecer_escala()
    return jsonify({"ok": True, "arquivo": MODELOS[nome]})


@app.post("/api/modelos-prontos")
def usar_modelos_prontos():
    """Baixa as imagens dos botões do projeto Full Bench (licença MIT)."""
    from tracker.auto_export import baixar_prontas
    try:
        return jsonify({"ok": True, "arquivos": baixar_prontas()})
    except Exception as e:
        return jsonify({"erro": f"Não consegui baixar as imagens prontas: {e}"}), 400


@app.post("/api/automatico/instalar")
def instalar_automatico():
    """Instala as bibliotecas do modo automático no mesmo Python que roda o programa (veja auto_export.instalar)."""
    auto.instalar()
    return jsonify({"ok": True})


@app.get("/modelos/<nome>")
def ver_modelo(nome):
    from tracker.auto_export import MODELOS
    if nome in MODELOS and (config.PASTA_MODELOS / MODELOS[nome]).exists():
        return send_from_directory(config.PASTA_MODELOS, MODELOS[nome], mimetype="image/png")
    return Response(status=404)


@app.post("/api/cartas/imagens")
def cartas_imagens():
    if cartas.progresso["ativo"]:
        return jsonify({"erro": "A biblioteca está ocupada. Tente quando terminar."}), 409
    threading.Thread(target=cartas.baixar_todas_imagens, daemon=True).start()
    return jsonify({"ok": True})


@app.patch("/api/partidas/<int:pid>")
def editar_partida(pid):
    banco.atualizar_partida(pid, request.get_json(force=True) or {})
    return jsonify({"ok": True})


@app.delete("/api/partidas/<int:pid>")
def apagar_partida(pid):
    banco.apagar_partida(pid)
    return jsonify({"ok": True})


# ------------------------------------------------------------------ regras de leitura
@app.get("/api/regras")
def regras():
    return jsonify({"regras": config.ler_regras(), "tipos": leitor.TIPOS,
                    "erros": leitor.compilar_regras(config.ler_regras())[1]})


@app.post("/api/regras")
def salvar_regras():
    corpo = request.get_json(force=True) or {}
    regras_novas = config.regras_padrao() if corpo.get("restaurar") else corpo.get("regras", [])
    _, erros = leitor.compilar_regras(regras_novas)
    if erros:
        return jsonify({"erros": erros}), 400
    config.salvar_regras(regras_novas)
    n = banco.reprocessar_partidas(regras_novas)
    return jsonify({"ok": True, "reprocessadas": n})


@app.post("/api/regras/testar")
def testar_regra():
    corpo = request.get_json(force=True) or {}
    return jsonify(leitor.testar_linha(corpo.get("linha", ""), corpo.get("regras") or config.ler_regras()))


# ------------------------------------------------------------------ campeonatos
@app.get("/api/torneios")
def torneios():
    return jsonify(banco.listar_torneios())


@app.get("/api/limitless/eventos")
def eventos_limitless():
    try:
        return jsonify(limitless.listar_eventos())
    except limitless.ErroImportacao as e:
        return jsonify({"erro": str(e)}), 502


@app.post("/api/limitless/importar")
def importar():
    if limitless.progresso["ativo"]:
        return jsonify({"erro": "Já existe uma importação em andamento."}), 409
    corpo = request.get_json(force=True) or {}
    tid = str(corpo.get("id", "")).strip()
    if not tid.isdigit():
        return jsonify({"erro": "Informe o número do torneio no Labs (ex.: 0078)."}), 400
    threading.Thread(target=limitless.importar, args=(tid, int(corpo.get("listas_top", 64))), daemon=True).start()
    return jsonify({"ok": True})


@app.post("/api/sincronizar")
def sincronizar_agora():
    """Procura torneios novos agora, sem esperar o próximo horário."""
    if limitless.estado_sync["rodando"] or limitless.progresso["ativo"]:
        return jsonify({"erro": "Já existe uma verificação ou importação em andamento."}), 409
    limitless.sincronizador.verificar_agora()
    return jsonify({"ok": True})


@app.delete("/api/torneios/<tid>")
def apagar_torneio(tid):
    banco.apagar_torneio(tid)
    return jsonify({"ok": True})


def _lista_torneios():
    """Torneios escolhidos no painel; sem escolha, todos os Standard da fonte (grandes eventos, online ou todos).
    ?de=&ate= (época do meta escolhida no painel) deixa só os torneios dessas datas."""
    a = request.args
    de, ate = a.get("de") or None, a.get("ate") or None
    t = [x for x in a.get("torneios", "").split(",") if x]
    if t:
        return analises.torneios_da_fonte("todos", de, ate, ids=t) if (de or ate) else t
    return analises.torneios_da_fonte(a.get("fonte", "grandes"), de, ate)


@app.get("/api/epocas")
def epocas():
    """Épocas do meta (uma por coleção): pela chegada ao TCG Live (suas partidas) e pela validade em torneio."""
    primeira = banco.consultar("SELECT MIN(capturada_em) AS d FROM partidas")[0]["d"]
    primeiro_t = banco.consultar("SELECT MIN(data) AS d FROM torneios WHERE COALESCE(formato, '') IN ('', 'standard')")[0]["d"]
    return jsonify({"live": colecoes.epocas("live"), "torneios": colecoes.epocas("torneios"),
                    "proxima": {"live": colecoes.proxima("live"), "torneios": colecoes.proxima("torneios")},
                    "primeira_partida": (primeira or "")[:10], "primeiro_torneio": (primeiro_t or "")[:10]})


@app.get("/api/meta")
def meta():
    a = request.args
    torneios = _lista_torneios()
    m = analises.meta(torneios, int(a.get("top", 0)), int(a.get("corte", 32)), int(a.get("k", 12)), int(a.get("min", 10)))
    # taxa ajustada de cada confronto (completa os de poucos jogos pela força geral dos decks; ver tracker/estrategia.py)
    from tracker import estrategia
    principais = [c["arquetipo"] for c in m["colunas"]]
    ajust = estrategia.confrontos_ajustados(estrategia._partidas(torneios, com_empates=True), principais)
    for linha in m["matriz"]:
        for col, cel in zip(principais, linha["celulas"]):
            cel["ajustada"] = round(100 * ajust[(linha["arquetipo"], col)]["p"], 1)
    return jsonify(m)


@app.get("/api/variantes/<arq>")
def variantes_deck(arq):
    """Variantes do deck (listas agrupadas por semelhança) com a taxa de vitória de cada uma."""
    from tracker import variantes
    return jsonify(variantes.variantes(arq, _lista_torneios()))


@app.get("/api/qual-deck")
def qual_deck():
    """Taxa esperada contra o campo, pior confronto e equilíbrio do meta (tracker/estrategia.py)."""
    from tracker import estrategia
    return jsonify(estrategia.qual_deck(_lista_torneios(), int(request.args.get("k", 12))))


@app.get("/api/tendencia")
def tendencia():
    return jsonify(analises.tendencia(int(request.args.get("k", 8)), _lista_torneios()))


@app.get("/api/deck/<arq>")
def deck(arq):
    p = analises.perfil(arq, _lista_torneios())
    return (jsonify(p), 200) if p else (jsonify({"erro": "Deck não encontrado nos torneios escolhidos."}), 404)


@app.get("/api/cartas")
def api_cartas():
    return jsonify(analises.cartas(_lista_torneios(), request.args.get("arq") or None))


@app.get("/api/efeito-cartas")
def api_efeito_cartas():
    """Efeito de cada carta na chance de vencer, descontados os confrontos (regressão logística, tracker/regressao.py)."""
    from tracker import regressao
    arq = request.args.get("arq") or ""
    if not arq:
        return jsonify({"erro": "Escolha um deck."}), 400
    return jsonify(regressao.efeito_cartas(arq, _lista_torneios()))


@app.get("/api/jogadores")
def jogadores_torneio():
    t = request.args.get("torneio")
    return jsonify(banco.consultar(
        "SELECT j.labs_id, j.nome, j.posicao, j.arquetipo, "
        "(SELECT COUNT(*) FROM t_listas l WHERE l.torneio=j.torneio AND l.labs_id=j.labs_id) AS cartas "
        "FROM t_jogadores j WHERE torneio=? ORDER BY posicao", (t,)))


@app.get("/api/comparar")
def comparar():
    a = request.args
    return jsonify(analises.comparar_listas(a["ta"], a["ia"], a["tb"], a["ib"]))


# ------------------------------------------------------------------ exportar para o Excel
def _csv(cabecalho, linhas, nome):
    """CSV com ';' e vírgula decimal: abre direto no Excel em português."""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(cabecalho)
    for l in linhas:
        w.writerow([str(x).replace(".", ",") if isinstance(x, float) else ("" if x is None else x) for x in l])
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nome}"})


@app.get("/exportar/minhas_partidas.csv")
def exportar_partidas():
    dados = analises.analise_pessoal(config.ler_config()["nick"], jogador=_jogador_pedido())
    campos = ["id", "data", "dono", "eu", "adversario", "resultado", "comecei", "meu_deck", "deck_adv",
              "premios_eu", "premios_adv", "turnos", "motivo", "primeiro_ko_meu", "mulligan_eu", "tags", "notas"]
    return _csv(campos, [[l[c] for c in campos] for l in dados["partidas"]], "minhas_partidas.csv")


@app.get("/exportar/eventos.csv")
def exportar_eventos():
    linhas = []
    for p in banco.listar_partidas():
        for e in banco.obter_partida(p["id"])["eventos"]:
            linhas.append([p["id"], e["linha"], e["turno"], e["dono"], e["tipo"], e["jogador"], e["carta"],
                           e["alvo"], e["golpe"], e["valor"], e["texto"]])
    return _csv(["partida", "linha", "turno", "dono_do_turno", "tipo", "jogador", "carta", "alvo", "golpe", "valor", "texto"],
                linhas, "eventos.csv")


@app.get("/exportar/torneios.csv")
def exportar_torneios():
    rows = banco.consultar("SELECT p.*, t.nome AS nome_torneio, t.data FROM t_partidas p JOIN torneios t ON t.id=p.torneio")
    campos = ["torneio", "nome_torneio", "data", "rodada", "mesa", "j1", "arq1", "res1", "j2", "arq2"]
    return _csv(campos, [[r[c] for c in campos] for r in rows], "partidas_torneios.csv")


@app.get("/exportar/meta.csv")
def exportar_meta():
    m = analises.meta(_lista_torneios(), int(request.args.get("top", 0)))
    campos = ["nome", "jogadores", "pct", "taxa", "v", "d", "e", "no_corte", "conversao", "fator_conversao"]
    return _csv(campos, [[d[c] for c in campos] for d in m["divisao"]], "meta.csv")


@app.post("/api/encerrar")
def encerrar():
    """Fecha o programa (útil quando ele roda sem janela, iniciado com o Windows)."""
    import os
    threading.Timer(0.5, lambda: os._exit(0)).start()
    return jsonify({"ok": True})


@app.get("/api/diagnostico")
def diag():
    return jsonify(diagnostico.procurar())


# ------------------------------------------------------------------ início
class _Duplicar:
    """Escreve ao mesmo tempo na janela preta e em dados/programa.log (para diagnosticar erros)."""
    def __init__(self, *saidas):
        self.saidas = [x for x in saidas if x is not None]

    def write(self, texto):
        for x in self.saidas:
            try:
                x.write(texto)
                x.flush()
            except Exception:
                pass

    def flush(self):
        pass


def preparar_registro():
    import time
    log = open(config.PASTA_DADOS / "programa.log", "a", encoding="utf-8", buffering=1)
    log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} programa iniciado =====\n")
    sys.stdout = _Duplicar(sys.stdout, log)
    sys.stderr = _Duplicar(sys.stderr, log)

    def erro_em_thread(args):  # erros em segundo plano vão para o log em vez de sumir
        import traceback
        print("[erro em segundo plano]", "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
    threading.excepthook = erro_em_thread

    if sys.platform == "win32":
        # Desliga a "Edição Rápida" da janela preta: clicar nela pausava o programa inteiro
        # e o painel deixava de responder até apertar Enter/Esc na janela.
        try:
            import ctypes
            k = ctypes.windll.kernel32
            h = k.GetStdHandle(-10)
            modo = ctypes.c_uint32()
            if k.GetConsoleMode(h, ctypes.byref(modo)):
                k.SetConsoleMode(h, (modo.value | 0x80) & ~0x40)  # ENABLE_EXTENDED_FLAGS, sem QUICK_EDIT
        except Exception:
            pass


def _tentar(func):
    try:
        func()
    except Exception as e:
        print("[aviso]", e)


def _tratar_instancia_antiga(url, porta, sem_navegador):
    """Se já existe um coletor rodando: mesma versão -> só abre o painel; versão antiga -> fecha e segue."""
    import json
    import time
    import urllib.request
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", porta)) != 0:
            return True  # nada rodando: pode iniciar
    try:
        with urllib.request.urlopen(url + "/api/status", timeout=5) as r:
            versao = json.load(r).get("versao")
    except Exception:
        versao = None
    if versao == VERSAO:
        print(f"O programa já está rodando. Abrindo o painel: {url}")
        if not sem_navegador:
            janela.abrir(url)
        return False
    print(f"Encontrei uma versão anterior do coletor rodando ({versao or 'desconhecida'}). Fechando para usar a nova…")
    try:
        urllib.request.urlopen(urllib.request.Request(url + "/api/encerrar", method="POST"), timeout=5)
    except Exception:
        pass
    for _ in range(20):
        time.sleep(0.5)
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", porta)) != 0:
                return True
    print("Não consegui fechar a versão antiga. Feche o pythonw.exe pelo Gerenciador de Tarefas e abra de novo.")
    return False


def _reabrir_sem_janela():
    """Aberto pelo python.exe (com janela preta)? Abre de novo pelo pythonw.exe (sem janela) e fecha este.

    Assim a janela preta só pisca e some, inclusive quando quem abre é o atualizador de versões antigas.
    """
    import os
    import subprocess
    exe = os.path.basename(sys.executable).lower()
    w = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if exe != "python.exe" or not os.path.exists(w):
        return False
    try:
        subprocess.Popen([w, str(config.RAIZ / "app.py"), *sys.argv[1:]], cwd=str(config.RAIZ),
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    except OSError:
        return False
    print("Abrindo o Coletor com o ícone perto do relógio. Esta janela pode ser fechada.")
    return True


def main():
    ap = argparse.ArgumentParser(description="Coletor de Partidas TCG Live")
    ap.add_argument("--diagnostico", action="store_true", help="procura arquivos de log do jogo no disco")
    ap.add_argument("--importar", metavar="ID", help="importa um torneio do Limitless Labs (ex.: 0078)")
    ap.add_argument("--sincronizar", action="store_true", help="importa os torneios recentes que faltam e sai")
    ap.add_argument("--sem-navegador", action="store_true", help="não abrir o navegador ao iniciar")
    ap.add_argument("--janela", action="store_true", help="usar a janela preta em vez do ícone perto do relógio")
    ap.add_argument("--criar-atalho", action="store_true", help="cria o atalho na Área de Trabalho (Windows) e sai")
    args = ap.parse_args()

    if args.criar_atalho:
        try:
            print("Atalho criado:", atalhos.criar("area"))
        except Exception as e:
            print(e)
        return
    usar_bandeja = (sys.platform == "win32" and not args.janela and bandeja.disponivel()
                    and not (args.diagnostico or args.sincronizar or args.importar))
    if usar_bandeja and _reabrir_sem_janela():
        return

    banco.iniciar()
    preparar_registro()
    cfg = config.ler_config()
    if cfg.get("versao_listas") != 2:  # listas de Meus decks lidas de novo (códigos como 30C)
        _tentar(decks.reler_listas)
        cfg["versao_listas"] = 2
        config.salvar_config(cfg)
    if args.diagnostico:
        r = diagnostico.procurar()
        print("Pastas do jogo encontradas:", *(r["pastas"] or ["(nenhuma)"]), sep="\n  ")
        print(f"Arquivos verificados: {r['arquivos_olhados']}")
        for x in r["encontrados"]:
            print(f"  Parece conter o log: {x['arquivo']} ({x['tamanho_kb']} KB)")
        if not r["encontrados"]:
            print("Nenhum arquivo com o log. A captura pela área de transferência continua sendo o caminho.")
        return
    if args.sincronizar:
        limitless.sincronizador.rodar_uma_vez()
        print(limitless.estado_sync["mensagem"])
        for t in limitless.estado_sync["importados"]:
            print(" ", t["id"], t["resumo"])
        return
    if args.importar:
        limitless.importar(args.importar)
        print(limitless.progresso["resumo"] or limitless.progresso["erro"])
        return

    cfg = config.ler_config()
    url = f"http://127.0.0.1:{cfg['porta']}"
    if not _tratar_instancia_antiga(url, cfg["porta"], args.sem_navegador):
        return
    if cfg["coletor_ativo"]:
        coletor.iniciar()
    if cfg["modo_automatico"]:
        auto.iniciar()
    if cfg["sincronizar_auto"]:
        limitless.sincronizador.iniciar()
    cartas.verificador.iniciar()
    atualizador.verificador.iniciar()
    regras_jogo.verificador.iniciar()
    if cfg.get("pasta_auto"):
        compartilhar.sincronizador_pasta.iniciar()
    total, sem_icone = decks.icones_sem_cadastro()
    if not total or sem_icone > total / 2:  # primeira vez, ou ícones apagados (layout novo do Labs em 11/2026): refaz a lista
        threading.Thread(target=lambda: _tentar(limitless.atualizar_arquetipos), daemon=True).start()
    # Deixa pronta a identificação do deck de cada partida (usa as listas dos torneios e leva alguns segundos):
    # assim a primeira tela de partidas abre sem esperar.
    threading.Thread(target=lambda: _tentar(lambda: analises.analise_pessoal(cfg.get("nick", ""), jogador="*")),
                     daemon=True, name="aquecer").start()
    print(f"\nColetor de Partidas TCG Live (versão {VERSAO}) rodando. Painel: {url}")
    if not args.sem_navegador:
        threading.Timer(1.2, lambda: janela.abrir(url)).start()
    if usar_bandeja:
        # o painel roda em segundo plano; a thread principal fica com o ícone até a pessoa escolher Sair
        import os
        print("Rodando com o ícone perto do relógio (sem janela preta).\n")
        MODO["bandeja"] = True
        threading.Thread(target=lambda: app.run(host="127.0.0.1", port=cfg["porta"], debug=False, threaded=True),
                         daemon=True, name="painel").start()
        try:
            bandeja.rodar(url, ao_sair=lambda: os._exit(0))
        except Exception as e:  # ícone não abriu: segue sem ele, como quando inicia com o Windows
            MODO["bandeja"] = False
            print("[aviso] Não consegui mostrar o ícone perto do relógio:", e)
            threading.Event().wait()
        return
    print("Deixe esta janela aberta enquanto joga. Para sair, feche-a ou aperte Ctrl+C.\n")
    app.run(host="127.0.0.1", port=cfg["porta"], debug=False, threaded=True)


if __name__ == "__main__":
    main()
