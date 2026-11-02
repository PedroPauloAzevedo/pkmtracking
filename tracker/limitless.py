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
        info["fonte"], info["formato"] = "labs", formato_labs(tid)
        banco.salvar_torneio(info, jogadores, partidas, listas if listas_top else None)
        com_arq = sum(1 for p in partidas if p["arq1"] and p["arq2"])
        progresso["resumo"] = (f"{info['nome']}: {len(jogadores)} jogadores, {len(partidas)} partidas "
                               f"({com_arq} com os dois decks conhecidos), {len({c['labs_id'] for c in listas})} listas. Fonte: {fonte}."
                               + (f" Formato {info['formato']}: fica fora das contas (o programa só usa Standard)."
                                  if info["formato"] not in ("", "standard") else ""))
        ao_progredir("Concluído", 1)
    except ErroImportacao as e:
        progresso["erro"] = str(e)
    except Exception as e:  # erro inesperado: mostra no painel em vez de travar
        progresso["erro"] = f"Erro inesperado: {e}"
    finally:
        progresso["ativo"] = False


# ------------------------------------------------------------------ formato dos torneios do Labs (só Standard)
#
# O Labs não diz o formato do torneio. O índice do site principal (limitlesstcg.com/tournaments)
# diz (data-format: standard, standard-jp, expanded...), e a página de cada evento tem o link
# para o Labs. Guardamos o que já foi descoberto em dados/limitless_formatos.json para não
# abrir a página de cada evento de novo.

INDICE = "https://limitlesstcg.com"


def _arq_formatos():
    from . import config
    return config.PASTA_DADOS / "limitless_formatos.json"


def _ler_formatos():
    import json
    try:
        return json.loads(_arq_formatos().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def formatos_labs(nav=None, dias=120):
    """{id do Labs: formato} dos eventos do índice do Limitless dos últimos `dias` dias."""
    import json
    from datetime import date as _date, timedelta
    nav = nav or Navegador()
    eventos = _ler_formatos()
    limite = (_date.today() - timedelta(days=dias)).isoformat()
    sopa = nav.sopa(f"{INDICE}/tournaments?show=100")
    for tr in sopa.select("tr[data-format]"):
        a = tr.find("a", href=re.compile(r"^/tournaments/\d+/?$"))
        if not a:
            continue
        principal = re.search(r"\d+", a["href"]).group(0)
        ev = eventos.setdefault(principal, {})
        ev.update(formato=tr.get("data-format", ""), data=tr.get("data-date"), nome=tr.get("data-name"))
        if "labs" not in ev and (ev.get("data") or "") >= limite:
            try:  # uma página por evento, só na primeira vez
                m = re.search(r"labs\.limitlesstcg\.com/(\d{4})", str(nav.sopa(f"{INDICE}/tournaments/{principal}")))
                ev["labs"] = m.group(1) if m else None
            except ErroImportacao:
                continue
    _arq_formatos().write_text(json.dumps(eventos, ensure_ascii=False, indent=1), encoding="utf-8")
    return {ev["labs"]: ev["formato"] for ev in eventos.values() if ev.get("labs")}


def formato_labs(tid):
    """Formato já descoberto de um torneio do Labs ('' se ainda não se sabe)."""
    return next((ev["formato"] for ev in _ler_formatos().values() if ev.get("labs") == tid), "")


# ------------------------------------------------------------------ torneios online (play.limitlesstcg.com)
#
# A plataforma de torneios online do Limitless tem uma API pública (docs.limitlesstcg.com):
# lista de torneios por jogo e formato, classificação com o deck e a lista de cada jogador,
# e o resultado de cada mesa. Sem chave, o limite é de 50 pedidos a cada 5 minutos;
# por isso esperamos PAUSA_API segundos entre os pedidos.

API = "https://play.limitlesstcg.com/api"
PAUSA_API = 6.5
PREFIXO_ONLINE = "on-"   # ids dos torneios online no banco (os do Labs são números como 0078)


class ApiLimitless:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "TCGLiveTracker/1.0 (uso pessoal)"
        self._ultimo = 0.0

    def get(self, caminho, **params):
        for tentativa in range(3):
            espera = PAUSA_API - (time.time() - self._ultimo)
            if espera > 0:
                time.sleep(espera)
            try:
                r = self.s.get(API + caminho, params=params, timeout=40)
            except requests.RequestException as e:
                raise ErroImportacao(f"Não consegui acessar a API do Limitless: {e}")
            self._ultimo = time.time()
            if r.status_code == 429:  # passou do limite: espera o que o site pedir
                time.sleep(min(int(r.headers.get("Retry-After", "60") or 60), 300))
                continue
            if r.status_code != 200:
                raise ErroImportacao(f"A API do Limitless respondeu com o código {r.status_code} ({caminho}).")
            return r.json()
        raise ErroImportacao("A API do Limitless continua pedindo para esperar. Tente mais tarde.")


def listar_online(api, dias=21, minimo=64, hoje=None):
    """Torneios online Standard terminados nos últimos `dias` dias, com pelo menos `minimo` jogadores."""
    from datetime import date as _date, timedelta
    hoje = hoje or _date.today()
    limite = (hoje - timedelta(days=dias)).isoformat()
    achados = []
    for pagina in range(1, 6):
        lote = api.get("/tournaments", game="PTCG", format="STANDARD", limit=500, page=pagina)
        if not lote:
            break
        for t in lote:
            data = (t.get("date") or "")[:10]
            # só os que já terminaram (o torneio de hoje pode estar em andamento)
            if limite <= data < hoje.isoformat() and (t.get("players") or 0) >= minimo:
                achados.append({"id": t["id"], "nome": t.get("name", ""), "data": data, "jogadores": t.get("players")})
        if min((t.get("date") or "")[:10] for t in lote) < limite:
            break
    return sorted(achados, key=lambda t: t["data"], reverse=True)


def importar_online(api, t, listas_top=64):
    """Importa um torneio online: classificação com deck, resultado de cada mesa e as listas do topo."""
    from . import decks
    classificacao = api.get(f"/tournaments/{t['id']}/standings")
    mesas = api.get(f"/tournaments/{t['id']}/pairings")
    jogadores, arq_de, novos = [], {}, {}
    for j in classificacao:
        deck = j.get("deck") or {}
        rec = j.get("record") or {}
        chave = str(j.get("player") or "").lower()
        arq_de[chave] = deck.get("id") or ""
        if deck.get("id"):
            novos.setdefault(deck["id"], {"slug": deck["id"], "nome": deck.get("name") or deck["id"], "icones": deck.get("icons") or []})
        jogadores.append({"labs_id": chave, "nome": j.get("name") or chave, "nome_norm": chave,
                          "pais": j.get("country") or "", "posicao": j.get("placing"), "pontos": None,
                          "v": rec.get("wins"), "d": rec.get("losses"), "e": rec.get("ties"), "arquetipo": deck.get("id") or "",
                          "_lista": j.get("decklist")})
    partidas = []
    for m in mesas:
        j1, j2, venc = str(m.get("player1") or "").lower(), str(m.get("player2") or "").lower(), m.get("winner")
        if not j1 or not j2 or venc in (None, -1, "-1"):
            continue  # folga, atraso ou derrota dupla: não é partida jogada
        venc = str(venc).lower()
        res = "T" if venc == "0" else "W" if venc == j1 else "L" if venc == j2 else None
        if res:
            partidas.append({"rodada": m.get("round"), "mesa": str(m.get("table") or m.get("match") or ""),
                             "j1": j1, "j2": j2, "res1": res, "arq1": arq_de.get(j1, ""), "arq2": arq_de.get(j2, "")})
    listas = []
    alvo = sorted((j for j in jogadores if j["_lista"]), key=lambda j: j["posicao"] or 99999)[:listas_top] if listas_top else []
    for j in alvo:
        for secao in ("pokemon", "trainer", "energy"):
            for c in j["_lista"].get(secao) or []:
                listas.append({"labs_id": j["labs_id"], "carta": c.get("name", ""), "set": (c.get("set") or "").upper(),
                               "numero": str(c.get("number") or "").lstrip("0") or "", "qtd": c.get("count") or 1})
    for j in jogadores:
        j.pop("_lista", None)
    conhecidos = {r["slug"] for r in banco.consultar("SELECT slug FROM arquetipos")}  # nomes do Labs têm preferência
    faltam = [d for s, d in novos.items() if s not in conhecidos]
    if faltam:
        decks.salvar_arquetipos(faltam)
    info = {"id": PREFIXO_ONLINE + t["id"], "nome": t["nome"], "data": t["data"], "jogadores": t.get("jogadores") or len(jogadores),
            "rk9": None, "fonte": "online", "formato": "standard",
            "info": {"fonte_partidas": "Limitless (torneio online)", "api_id": t["id"], "listas_top": listas_top}}
    banco.salvar_torneio(info, jogadores, partidas, listas if listas_top else None)
    return f"{t['nome']}: {len(jogadores)} jogadores, {len(partidas)} partidas"


def sincronizar_online(cfg, parar, ao_progredir):
    """Importa os torneios online que faltam. Devolve a lista do que foi feito."""
    if not cfg.get("online_ativo", True):
        return []
    api = ApiLimitless()
    ao_progredir("Procurando torneios online no Limitless…")
    disponiveis = listar_online(api, int(cfg.get("online_dias", 21)), int(cfg.get("online_min_jogadores", 64)))
    ja = {t["id"] for t in banco.listar_torneios()}
    faltam = [t for t in disponiveis if PREFIXO_ONLINE + t["id"] not in ja][:int(cfg.get("online_por_vez", 40))]
    feitos = []
    for n, t in enumerate(faltam, 1):
        if parar.is_set():
            break
        ao_progredir(f"Torneios online: {n} de {len(faltam)} ({t['nome'][:40]})")
        try:
            feitos.append({"id": PREFIXO_ONLINE + t["id"], "ok": True, "resumo": importar_online(api, t, int(cfg.get("listas_top", 64)))})
        except ErroImportacao as e:
            feitos.append({"id": PREFIXO_ONLINE + t["id"], "ok": False, "resumo": str(e)})
            break  # a API está recusando: tenta na próxima verificação
    return feitos


# ------------------------------------------------------------------ atualização automática
#
# Nem o RK9 nem o Limitless Labs oferecem API ou aviso (webhook) para os campeonatos
# oficiais. Então o próprio programa verifica de tempos em tempos se há torneio novo
# e importa sozinho. Regras:
#   - torneio que ainda não está no banco e começou nos últimos N dias -> importa
#   - torneio importado enquanto acontecia (ou logo depois) -> importa de novo até
#     3 dias após o início, para pegar o resultado final e as listas publicadas depois

def escolher_para_importar(eventos, importados, hoje, dias=45, max_sem_data=3, formatos=None):
    """eventos: lista do Labs; importados: {id: {"data":..., "importado_em":...}}. Devolve ids em ordem.
    formatos: {id do Labs: formato}; torneios que não são Standard ficam de fora."""
    from datetime import date as _date, timedelta
    escolhidos = []
    eventos = [e for e in eventos if (formatos or {}).get(e["id"], "standard") == "standard"]
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
            try:  # formato de cada evento (só Standard entra nas contas)
                formatos = formatos_labs(dias=max(120, int(cfg.get("sincronizar_dias", 45))))
                banco.marcar_formatos(formatos)
            except ErroImportacao as e:
                formatos = {}
                print("[limitless] não consegui confirmar os formatos:", e)
            importados = {t["id"]: t for t in banco.listar_torneios()}
            alvo = escolher_para_importar(eventos, importados, _date.today(), int(cfg.get("sincronizar_dias", 45)),
                                          formatos=formatos)
            for tid in alvo:
                if self._parar.is_set():
                    break
                estado_sync["mensagem"] = f"Importando {tid}…"
                importar(tid, int(cfg.get("listas_top", 64)))
                feitos.append({"id": tid, "ok": not progresso["erro"] or bool(progresso["resumo"]),
                               "resumo": progresso["resumo"] or progresso["erro"]})
            online = []
            if not self._parar.is_set():
                try:
                    online = sincronizar_online(cfg, self._parar, lambda m: estado_sync.update(mensagem=m))
                except ErroImportacao as e:
                    online = [{"id": "", "ok": False, "resumo": f"Torneios online: {e}"}]
            feitos += online
            novos_online = sum(1 for f in online if f["ok"])
            estado_sync["mensagem"] = ((f"{len(feitos) - len(online)} grande(s) evento(s) e {novos_online} torneio(s) online "
                                        "importado(s) ou atualizado(s).") if feitos else "Nenhum torneio novo.")
            erro_online = next((f["resumo"] for f in online if not f["ok"]), "")
            if erro_online:
                estado_sync["mensagem"] += f" Torneios online pararam: {erro_online}"
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
