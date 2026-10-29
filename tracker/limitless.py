"""
IMPORTADOR DE CAMPEONATOS (Limitless Labs + RK9).

O Limitless Labs (labs.limitlesstcg.com) não tem API pública; os dados estão nas páginas.
Então combinamos duas fontes:
  1. Limitless Labs  -> classificação final e o ARQUÉTIPO (deck) de cada jogador
                        + listas de cartas (opcional, só para o topo da classificação)
  2. RK9 (rk9.gg)    -> resultado de cada mesa, rodada por rodada (é de onde o próprio
                        Labs tira os dados). O link do RK9 aparece na página do Labs.

Juntando as duas, sabemos quem jogou contra quem, com qual deck, e quem venceu.
Isso alimenta meta, matchups, conversão e uso de cartas.

Boas maneiras: respeitamos o robots.txt, nos identificamos e esperamos um pouco entre
cada página para não sobrecarregar os sites. Uso pessoal.
"""
import re
import time
import unicodedata
import urllib.robotparser
from datetime import date

import requests
from bs4 import BeautifulSoup

from . import banco

LABS = "https://labs.limitlesstcg.com"
RK9 = "https://rk9.gg"
PAUSA = 0.6  # segundos entre páginas
MESES = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
MESES_CURTOS = {k[:3]: v for k, v in MESES.items()}

progresso = {"ativo": False, "torneio": None, "etapa": "", "pct": 0, "erro": "", "resumo": ""}


class ErroImportacao(Exception):
    pass


# ------------------------------------------------------------------ utilidades

class Navegador:
    """Baixa páginas com pausa entre pedidos e respeitando o robots.txt."""

    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "TCGLiveTracker/1.0 (uso pessoal)"
        self._robots = {}
        self._ultimo = 0.0

    def _pode(self, url):
        base = re.match(r"https?://[^/]+", url).group(0)
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(base + "/robots.txt", timeout=15)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse([])
            self._robots[base] = rp
        return self._robots[base].can_fetch(self.s.headers["User-Agent"], url)

    def sopa(self, url):
        if not self._pode(url):
            raise ErroImportacao(f"O robots.txt do site não permite baixar {url}.")
        espera = PAUSA - (time.time() - self._ultimo)
        if espera > 0:
            time.sleep(espera)
        try:
            r = self.s.get(url, timeout=30)
        except requests.RequestException as e:
            raise ErroImportacao(f"Não consegui acessar {url}: {e}")
        self._ultimo = time.time()
        if r.status_code != 200:
            raise ErroImportacao(f"{url} respondeu com o código {r.status_code}.")
        return BeautifulSoup(r.content, "html.parser")


def normalizar_nome(nome):
    """'José  Silva [BR]' -> 'jose silva' (para cruzar nomes entre Labs e RK9)."""
    nome = re.sub(r"\s*\[[A-Za-z]{2}\]\s*$", "", nome or "")
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", nome).strip().lower()


def _corrigir_codificacao(txt):
    # Alguns nomes no RK9 vêm com acentos "quebrados"; esta é a correção usada por outros leitores do RK9.
    try:
        return txt.encode("mac-roman").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return txt


def _data_iso(texto):
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})"
                  r"(?:\s*[–-]\s*(?:[A-Za-z]+\s+)?\d{1,2})?,\s*(\d{4})", texto)
    if m:
        return date(int(m.group(3)), MESES[m.group(1).lower()], int(m.group(2))).isoformat()
    m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2})"
                  r"(?:\s*[–-]\s*(?:[A-Za-z]+\s+)?\d{1,2})?,\s*(\d{4})", texto)
    if m:
        return date(int(m.group(3)), MESES_CURTOS[m.group(1).lower()[:3]], int(m.group(2))).isoformat()
    return None


# ------------------------------------------------------------------ Limitless Labs

def listar_eventos(nav=None):
    """Lista os torneios da página inicial do Labs: [{id, titulo, data}]."""
    nav = nav or Navegador()
    sopa = nav.sopa(LABS + "/")
    eventos, vistos = [], set()
    for a in sopa.find_all("a", href=True):
        m = re.search(r"(?:^|labs\.limitlesstcg\.com)/(\d{4})(?:/standings)?/?$", a["href"])
        if not m or m.group(1) in vistos:
            continue
        vistos.add(m.group(1))
        bloco = a.find_parent(["tr", "li"]) or a
        texto = re.sub(r"\s+", " ", bloco.get_text(" ", strip=True))
        eventos.append({"id": m.group(1), "titulo": texto, "data": _data_iso(texto)})
    return sorted(eventos, key=lambda e: e["id"], reverse=True)


def ler_classificacao(nav, tid):
    """Classificação final (Masters) com o arquétipo de cada jogador."""
    sopa = nav.sopa(f"{LABS}/{tid}/standings")
    texto_pagina = re.sub(r"\s+", " ", sopa.get_text(" ", strip=True))
    titulo = sopa.find(["h1", "h2"])
    nome = titulo.get_text(" ", strip=True) if titulo else (sopa.title.get_text(strip=True) if sopa.title else f"Torneio {tid}")
    m_jog = re.search(r"(\d[\d,.]*)\s+players", texto_pagina)
    rk9 = None
    for a in sopa.find_all("a", href=True):
        m = re.search(r"rk9\.gg/pairings/([A-Za-z0-9-]+)", a["href"])
        if m:
            rk9 = m.group(1)
            break

    padrao_jog = re.compile(rf"/{tid}/player/([^/?#]+)/?$")
    jogadores, vistos = [], set()
    for tr in sopa.find_all("tr"):
        a = tr.find("a", href=padrao_jog)
        if not a:
            continue
        labs_id = padrao_jog.search(a["href"]).group(1)
        if labs_id in vistos:
            continue
        vistos.add(labs_id)
        celulas = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        texto = " ".join(celulas)
        rec = re.search(r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", texto)
        pos = re.match(r"\s*(\d+)", celulas[0]) if celulas else None
        pontos = None
        nome_cel = a.find_parent("td")
        if nome_cel:
            for td in nome_cel.find_next_siblings("td"):
                t = td.get_text(strip=True)
                if t.isdigit():
                    pontos = int(t)
                    break
        deck = tr.find("a", href=re.compile(r"/decks/[^/?#]+"))
        arq = re.search(r"/decks/([^/?#]+)", deck["href"]).group(1) if deck else ""
        bandeira = tr.find("img", title=re.compile(r"^[A-Z]{2}$"))
        jogadores.append({
            "labs_id": labs_id, "nome": a.get_text(" ", strip=True),
            "nome_norm": normalizar_nome(a.get_text(" ", strip=True)),
            "pais": bandeira["title"] if bandeira else "",
            "posicao": int(pos.group(1)) if pos else len(jogadores) + 1, "pontos": pontos,
            "v": int(rec.group(1)) if rec else None, "d": int(rec.group(2)) if rec else None,
            "e": int(rec.group(3)) if rec else None, "arquetipo": arq,
        })
    if not jogadores:
        raise ErroImportacao("Não encontrei a tabela de classificação no Limitless Labs. O layout do site pode ter mudado.")
    info = {
        "id": tid, "nome": nome, "data": _data_iso(texto_pagina), "rk9": rk9,
        "jogadores": int(re.sub(r"\D", "", m_jog.group(1))) if m_jog else len(jogadores),
    }
    return info, jogadores


def ler_lista(nav, tid, labs_id):
    """Lista de cartas de um jogador no Labs: [{carta, set, numero, qtd}]."""
    sopa = nav.sopa(f"{LABS}/{tid}/player/{labs_id}/decklist")
    padrao = re.compile(r"limitlesstcg\.com/cards/(?:[a-z]{2}/)?([A-Za-z0-9-]+)/([A-Za-z0-9-]+)")
    ancoras = [a for a in sopa.find_all("a", href=True) if padrao.search(a["href"])]
    cartas, vistos = [], set()
    for i, a in enumerate(ancoras):
        set_code, numero = padrao.search(a["href"]).groups()
        if (set_code, numero) in vistos:
            continue
        alts = [img.get("alt", "").strip() for img in a.find_all("img")]
        nome = next((x for x in alts if x and not x.isdigit()), a.get_text(" ", strip=True))
        qtd = next((int(x) for x in alts if x.isdigit()), None)
        if qtd is None:  # o número pode estar logo depois do link
            prox = a.find_next(lambda t: t.name == "img" and t.get("alt", "").strip().isdigit())
            limite = ancoras[i + 1] if i + 1 < len(ancoras) else None
            if prox and (limite is None or (prox.sourceline, prox.sourcepos) < (limite.sourceline, limite.sourcepos)):
                qtd = int(prox["alt"].strip())
        if not nome:
            continue
        vistos.add((set_code, numero))
        cartas.append({"carta": nome, "set": set_code.upper(), "numero": numero.lstrip("0") or "0", "qtd": qtd or 1})
    return cartas


def partidas_via_labs(nav, tid, jogadores, limite, ao_progredir):
    """Plano B (se o RK9 falhar): rodadas pela página de cada jogador no Labs."""
    por_id = {j["labs_id"]: j for j in jogadores}
    padrao = re.compile(rf"/{tid}/player/([^/?#]+)/?$")
    partidas, vistas = [], set()
    alvo = sorted(jogadores, key=lambda j: j["posicao"])[:limite]
    for n, j in enumerate(alvo, 1):
        ao_progredir(f"Rodadas de {j['nome']} ({n}/{len(alvo)})", n / len(alvo))
        sopa = nav.sopa(f"{LABS}/{tid}/player/{j['labs_id']}")
        for tr in sopa.find_all("tr"):
            celulas = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(celulas) < 3 or not celulas[0].isdigit():
                continue
            res = next((c for c in celulas if c in ("Win", "Loss", "Tie")), None)
            a = tr.find("a", href=padrao)
            if not res or not a:
                continue
            adv = por_id.get(padrao.search(a["href"]).group(1))
            adv_norm = adv["nome_norm"] if adv else normalizar_nome(a.get_text(" ", strip=True))
            rodada = int(celulas[0])
            chave = (rodada, *sorted([j["nome_norm"], adv_norm]))
            if chave in vistas:
                continue
            vistas.add(chave)
            partidas.append({"rodada": rodada, "j1": j["nome_norm"], "j2": adv_norm,
                             "res1": {"Win": "W", "Loss": "L", "Tie": "T"}[res]})
    return partidas


# ------------------------------------------------------------------ RK9

def _status(div):
    classes = " ".join(div.get("class", []))
    for chave, res in (("winner", "W"), ("loser", "L"), ("tie", "T")):
        if chave in classes:
            return res
    return None


def ler_rodadas_rk9(nav, codigo, ao_progredir):
    """Todas as mesas da categoria Masters no RK9: [{rodada, mesa, j1, j2, res1}]."""
    base = nav.sopa(f"{RK9}/pairings/{codigo}")
    pod, total = None, 0
    for a in base.select("ul.nav-pills a"):
        controla = a.get("aria-controls", "") or ""
        texto = a.get_text(" ", strip=True).lower()
        if re.fullmatch(r"P\d+", controla) and (texto.startswith("ma") or "master" in texto):
            pod = controla[1:]
            nums = re.findall(r"\d+", texto)
            total = int(nums[-1]) if nums else 0
    if pod is None:
        pod, total = "2", 0  # padrão do RK9 para Masters
    partidas = []
    rodada = 1
    while rodada <= (total or 25):
        ao_progredir(f"Rodada {rodada}" + (f" de {total}" if total else ""), rodada / (total or 18))
        sopa = nav.sopa(f"{RK9}/pairings/{codigo}?pod={pod}&rnd={rodada}")
        mesas = sopa.find_all("div", class_="match")
        if not mesas and not total:
            break
        for m in mesas:
            p1, p2 = m.find("div", class_="player1"), m.find("div", class_="player2")
            n1 = p1.find("span", class_="name") if p1 else None
            n2 = p2.find("span", class_="name") if p2 else None
            if not n1 or not n2 or not n1.get_text(strip=True) or not n2.get_text(strip=True):
                continue  # bye (folga)
            res = _status(p1)
            if res is None:
                r2 = _status(p2)
                res = {"W": "L", "L": "W", "T": "T"}.get(r2)
            if res is None:
                continue  # mesa ainda em andamento
            mesa = m.find("span", class_="tablenumber")
            partidas.append({
                "rodada": rodada, "mesa": mesa.get_text(strip=True) if mesa else "",
                "j1": normalizar_nome(_corrigir_codificacao(n1.get_text(" ", strip=True))),
                "j2": normalizar_nome(_corrigir_codificacao(n2.get_text(" ", strip=True))),
                "res1": res,
            })
        rodada += 1
    return partidas


# ------------------------------------------------------------------ importação completa

def importar(tid, listas_top=64, fallback_top=256):
    """Importa um torneio do Labs para o banco local. Roda em segundo plano."""
    tid = str(tid).zfill(4)
    progresso.update({"ativo": True, "torneio": tid, "etapa": "Começando", "pct": 0, "erro": "", "resumo": ""})

    def ao_progredir(msg, frac, ini=0.0, fim=1.0):
        progresso["etapa"] = msg
        progresso["pct"] = round(100 * (ini + (fim - ini) * min(max(frac, 0), 1)))

    try:
        nav = Navegador()
        ao_progredir("Lendo classificação no Limitless Labs", 0)
        info, jogadores = ler_classificacao(nav, tid)
        try:  # nomes e ícones dos decks deste torneio
            from . import decks
            decks.salvar_arquetipos(decks.ler_pagina_decks(nav.sopa(f"{LABS}/{tid}/decks"), tid))
        except Exception as e:
            print("[limitless] não consegui ler os decks do torneio:", e)
        arq_por_nome = {}
        for j in jogadores:
            arq_por_nome.setdefault(j["nome_norm"], j["arquetipo"])

        partidas, fonte = [], ""
        if info.get("rk9"):
            try:
                partidas = ler_rodadas_rk9(nav, info["rk9"], lambda m, f: ao_progredir("RK9: " + m, f, 0.05, 0.7))
                fonte = "RK9"
            except ErroImportacao as e:
                progresso["erro"] = f"RK9 indisponível ({e}); usando as páginas do Labs."
        if not partidas:
            partidas = partidas_via_labs(nav, tid, jogadores, fallback_top,
                                         lambda m, f: ao_progredir("Labs: " + m, f, 0.05, 0.7))
            fonte = f"Labs (top {fallback_top})"
        for p in partidas:
            p["arq1"] = arq_por_nome.get(p["j1"], "")
            p["arq2"] = arq_por_nome.get(p["j2"], "")

        listas = []
        if listas_top:
            alvo = [j for j in sorted(jogadores, key=lambda j: j["posicao"]) if j["arquetipo"]][:listas_top]
            for n, j in enumerate(alvo, 1):
                ao_progredir(f"Lista de {j['nome']} ({n}/{len(alvo)})", n / len(alvo), 0.7, 0.98)
                try:
                    for c in ler_lista(nav, tid, j["labs_id"]):
                        listas.append({**c, "labs_id": j["labs_id"]})
                except ErroImportacao:
                    continue

        info["info"] = {"fonte_partidas": fonte, "listas_top": listas_top}
        banco.salvar_torneio(info, jogadores, partidas, listas if listas_top else None)
        com_arq = sum(1 for p in partidas if p["arq1"] and p["arq2"])
        progresso["resumo"] = (f"{info['nome']}: {len(jogadores)} jogadores, {len(partidas)} partidas "
                               f"({com_arq} com os dois decks conhecidos), {len({c['labs_id'] for c in listas})} listas. Fonte: {fonte}.")
        ao_progredir("Concluído", 1)
    except ErroImportacao as e:
        progresso["erro"] = str(e)
    except Exception as e:  # erro inesperado: mostra no painel em vez de travar
        progresso["erro"] = f"Erro inesperado: {e}"
    finally:
        progresso["ativo"] = False


# ------------------------------------------------------------------ atualização automática
#
# Nem o RK9 nem o Limitless Labs oferecem API ou aviso (webhook) para os campeonatos
# oficiais. Então o próprio programa verifica de tempos em tempos se há torneio novo
# e importa sozinho. Regras:
#   - torneio que ainda não está no banco e começou nos últimos N dias -> importa
#   - torneio importado enquanto acontecia (ou logo depois) -> importa de novo até
#     3 dias após o início, para pegar o resultado final e as listas publicadas depois

def escolher_para_importar(eventos, importados, hoje, dias=45, max_sem_data=3):
    """eventos: lista do Labs; importados: {id: {"data":..., "importado_em":...}}. Devolve ids em ordem."""
    from datetime import date as _date, timedelta
    escolhidos = []
    com_data = [e for e in eventos if e.get("data")]
    for e in com_data:
        inicio = _date.fromisoformat(e["data"])
        if inicio > hoje or (hoje - inicio).days > dias:
            continue
        ja = importados.get(e["id"])
        if not ja:
            escolhidos.append(e["id"])
            continue
        importado = _date.fromisoformat((ja.get("importado_em") or "1970-01-01")[:10])
        if (importado - inicio).days < 3 and importado < hoje:
            escolhidos.append(e["id"])  # importado cedo demais: atualiza uma vez por dia
    if not com_data:  # não deu para ler as datas: pega só os mais recentes que faltam
        recentes = sorted(eventos, key=lambda e: e["id"], reverse=True)[:max_sem_data]
        escolhidos = [e["id"] for e in recentes if e["id"] not in importados]
    return sorted(escolhidos)


def atualizar_arquetipos(eventos=None):
    """Lista de decks (nomes e ícones) a partir do torneio mais recente do Labs."""
    from . import decks
    nav = Navegador()
    eventos = eventos or listar_eventos(nav)
    for e in sorted(eventos, key=lambda x: x["id"], reverse=True)[:2]:
        try:
            lista = decks.ler_pagina_decks(nav.sopa(f"{LABS}/{e['id']}/decks"), e["id"])
            if lista:
                decks.salvar_arquetipos(lista)
        except ErroImportacao:
            continue


estado_sync = {"ligado": False, "rodando": False, "ultima": None, "proxima": None, "mensagem": "", "importados": []}


class Sincronizador:
    def __init__(self):
        import threading
        self._parar = threading.Event()
        self._agora = threading.Event()
        self._thread = None

    def iniciar(self):
        import threading
        if self._thread and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="sincronizador", daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()
        self._agora.set()
        estado_sync["ligado"] = False
        estado_sync["proxima"] = None

    def verificar_agora(self):
        if self._thread and self._thread.is_alive():
            self._agora.set()
        else:
            import threading
            threading.Thread(target=self.rodar_uma_vez, daemon=True).start()

    def rodar_uma_vez(self):
        from datetime import date as _date
        from . import config
        if estado_sync["rodando"] or progresso["ativo"]:
            return
        cfg = config.ler_config()
        estado_sync["rodando"] = True
        estado_sync["mensagem"] = "Procurando torneios novos no Limitless Labs…"
        feitos = []
        try:
            eventos = listar_eventos()
            atualizar_arquetipos(eventos)
            importados = {t["id"]: t for t in banco.listar_torneios()}
            alvo = escolher_para_importar(eventos, importados, _date.today(), int(cfg.get("sincronizar_dias", 45)))
            for tid in alvo:
                if self._parar.is_set():
                    break
                estado_sync["mensagem"] = f"Importando {tid}…"
                importar(tid, int(cfg.get("listas_top", 64)))
                feitos.append({"id": tid, "ok": not progresso["erro"] or bool(progresso["resumo"]),
                               "resumo": progresso["resumo"] or progresso["erro"]})
            estado_sync["mensagem"] = (f"{len(feitos)} torneio(s) importado(s) ou atualizado(s)." if feitos
                                       else "Nenhum torneio novo.")
        except ErroImportacao as e:
            estado_sync["mensagem"] = f"Não consegui verificar: {e}"
        except Exception as e:
            estado_sync["mensagem"] = f"Erro inesperado na verificação: {e}"
        finally:
            estado_sync["rodando"] = False
            estado_sync["ultima"] = time.strftime("%d/%m %H:%M")
            estado_sync["importados"] = feitos

    def _loop(self):
        from . import config
        estado_sync["ligado"] = True
        self._parar.wait(15)  # deixa o programa terminar de abrir
        while not self._parar.is_set():
            self.rodar_uma_vez()
            horas = float(config.ler_config().get("sincronizar_horas", 6))
            estado_sync["proxima"] = time.strftime("%d/%m %H:%M", time.localtime(time.time() + horas * 3600))
            self._agora.clear()
            self._agora.wait(horas * 3600)
        estado_sync["ligado"] = False


sincronizador = Sincronizador()
