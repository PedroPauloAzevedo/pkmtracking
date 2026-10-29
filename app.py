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
import webbrowser

from flask import Flask, Response, jsonify, request, send_from_directory

from tracker import analises, atualizador, banco, cartas, config, decks, diagnostico, leitor, limitless, replay, revisao
from tracker.auto_export import auto
from tracker.coletor import coletor

app = Flask(__name__, static_folder=None)
app.json.sort_keys = False  # mantém a ordem dos dados (ex.: Top 8, Top 16, ...)
app.json.ensure_ascii = False
PASTA_WEB = config.RAIZ / "web"
VERSAO = atualizador.versao_local()  # vem de versao.txt; aparece no painel e na janela preta


# ------------------------------------------------------------------ páginas
@app.get("/")
def inicio():
    return send_from_directory(PASTA_WEB, "index.html")


# ------------------------------------------------------------------ status e configurações
@app.get("/api/status")
def status():
    cfg = config.ler_config()
    return jsonify({
        "versao": VERSAO,
        "coletor": {"ativo": coletor.ativo, "erro": coletor.erro, "ultima": coletor.ultima, "capturadas": coletor.capturadas},
        "automatico": {"ligado": cfg["modo_automatico"], "status": auto.status, "erro": auto.erro,
                       "cliques": auto.cliques, "faltando": auto.faltando()},
        "importacao": limitless.progresso,
        "sincronizacao": limitless.estado_sync,
        "biblioteca": cartas.progresso,
        "atualizacao": atualizador.estado,
        "linhas_pendentes": _contar_pendentes(),
        "config": cfg,
    })


_cache_pendentes = {"t": 0, "n": 0}


def _contar_pendentes():
    """Quantas partidas têm linhas não lidas (recalcula no máximo a cada 20 s)."""
    import time
    if time.time() - _cache_pendentes["t"] > 20:
        _cache_pendentes.update(t=time.time(), n=sum(1 for p in banco.listar_partidas() if p["qtd_nao_lidas"]))
    return _cache_pendentes["n"]


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
                  "sincronizar_auto", "sincronizar_horas", "sincronizar_dias", "listas_top",
                  "github_repo", "github_ramo", "github_token"):
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
    return jsonify(cfg)


# ------------------------------------------------------------------ partidas pessoais
@app.get("/api/partidas")
def partidas():
    a = request.args
    return jsonify(analises.analise_pessoal(config.ler_config()["nick"], a.get("de"), a.get("ate"), a.get("deck"), a.get("tag"), a.get("lista"), a.get("adv")))


@app.post("/api/partidas")
def nova_partida():
    texto = (request.get_json(force=True) or {}).get("texto", "")
    if not leitor.parece_log(texto):
        return jsonify({"erro": "Isso não parece um log do TCG Live. Confira se copiou o log inteiro, começando em \"Setup\" e com as linhas \"Fulano's Turn\"."}), 400
    pid, nova = banco.inserir_partida(texto, "manual", config.ler_regras())
    p = banco.obter_partida(pid)
    _cache_pendentes["t"] = 0
    return jsonify({"id": pid, "nova": nova, "nao_lidas": len(p["nao_lidas"]) if p else 0})


@app.get("/api/partidas/<int:pid>")
def partida(pid):
    p = banco.obter_partida(pid)
    if not p:
        return jsonify({"erro": "Partida não encontrada."}), 404
    todas = banco.listar_partidas()
    p["visao"] = analises.visao(p, analises.descobrir_eu(todas, config.ler_config()["nick"]))
    return jsonify(p)


@app.get("/api/partidas/<int:pid>/replay")
def replay_partida(pid):
    p = banco.obter_partida(pid)
    if not p:
        return jsonify({"erro": "Partida não encontrada."}), 404
    r = replay.gerar(p["texto"], config.ler_regras())
    r["eu"] = analises.descobrir_eu(banco.listar_partidas(), config.ler_config()["nick"])
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
    return jsonify(lista)


# ------------------------------------------------------------------ meus decks
@app.get("/api/decks")
def meus_decks():
    nick = config.ler_config()["nick"]
    saida = []
    for d in decks.listar_decks():
        dados = analises.analise_pessoal(nick, lista=d["id"])
        d["placar"] = dados["total"]
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
    return jsonify(d)


@app.put("/api/decks/<int:did>")
def editar_deck(did):
    corpo = request.get_json(force=True) or {}
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


@app.delete("/api/decks/<int:did>")
def apagar_deck(did):
    with banco.conectar() as con:
        con.execute("DELETE FROM meus_decks_cartas WHERE deck_id=?", (did,))
        con.execute("DELETE FROM meus_decks WHERE id=?", (did,))
        con.execute("UPDATE partidas SET deck_id=NULL WHERE deck_id=?", (did,))
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
    return jsonify({"ok": True, "arquivo": MODELOS[nome]})


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
    t = request.args.get("torneios", "")
    return [x for x in t.split(",") if x] or None


@app.get("/api/meta")
def meta():
    a = request.args
    return jsonify(analises.meta(_lista_torneios(), int(a.get("top", 0)), int(a.get("corte", 32)),
                                 int(a.get("k", 12)), int(a.get("min", 10))))


@app.get("/api/tendencia")
def tendencia():
    return jsonify(analises.tendencia(int(request.args.get("k", 8))))


@app.get("/api/deck/<arq>")
def deck(arq):
    p = analises.perfil(arq, _lista_torneios())
    return (jsonify(p), 200) if p else (jsonify({"erro": "Deck não encontrado nos torneios escolhidos."}), 404)


@app.get("/api/cartas")
def api_cartas():
    return jsonify(analises.cartas(_lista_torneios(), request.args.get("arq") or None))


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
    dados = analises.analise_pessoal(config.ler_config()["nick"])
    campos = ["id", "data", "eu", "adversario", "resultado", "comecei", "meu_deck", "deck_adv",
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
            webbrowser.open(url)
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


def main():
    ap = argparse.ArgumentParser(description="Coletor de Partidas TCG Live")
    ap.add_argument("--diagnostico", action="store_true", help="procura arquivos de log do jogo no disco")
    ap.add_argument("--importar", metavar="ID", help="importa um torneio do Limitless Labs (ex.: 0078)")
    ap.add_argument("--sincronizar", action="store_true", help="importa os torneios recentes que faltam e sai")
    ap.add_argument("--sem-navegador", action="store_true", help="não abrir o navegador ao iniciar")
    args = ap.parse_args()

    banco.iniciar()
    preparar_registro()
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
    if not banco.consultar("SELECT 1 FROM arquetipos LIMIT 1"):  # primeira vez: busca a lista de decks
        threading.Thread(target=lambda: _tentar(limitless.atualizar_arquetipos), daemon=True).start()
    print(f"\nColetor de Partidas TCG Live (versão {VERSAO}) rodando. Painel: {url}")
    print("Deixe esta janela aberta enquanto joga. Para sair, feche-a ou aperte Ctrl+C.\n")
    if not args.sem_navegador:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=cfg["porta"], debug=False, threaded=True)


if __name__ == "__main__":
    main()
