"""
BIBLIOTECA DE CARTAS: dados e imagens das cartas, sempre na ARTE BÁSICA.

Fonte: TCGdex (api.tcgdex.net), base aberta e gratuita, sem chave.
O que guardamos (em dados/cartas/):
  sets/<id>.json   dados de cada coleção (nomes, raridade, ataques...) — só texto, leve
  indice.json      índice montado a partir dos sets (busca por nome e por coleção/número)
  img/<id>.webp    imagem de cada carta, baixada só quando é usada pela primeira vez

ARTE BÁSICA E CONVERSOR
Uma mesma carta pode ter várias artes: a normal, a "full art", a ilustração especial,
a dourada... Para o jogo, todas são a mesma carta. Aqui definimos:
  - carta "funcional" = mesmo nome + mesmos ataques/habilidades (+ PS, se for Pokémon)
  - arte básica       = a impressão de menor raridade dessa carta (comum, incomum, rara,
                        dupla rara...), preferindo a coleção mais recente.
O conversor troca qualquer impressão (ex.: TWM 214, a arte especial do Dragapult ex)
pela arte básica (TWM 130). Assim replay, listas e análises usam sempre a mesma imagem
e o mesmo código, e as artes alternativas não viram "cartas diferentes" nas contas.

ATUALIZAÇÃO
Nenhuma fonte gratuita de cartas oferece aviso (webhook) de coleção nova. Então o
programa confere uma vez por dia se o TCGdex tem coleção nova ou cartas novas numa
coleção recente, e baixa só o que mudou.
"""
import json
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from pathlib import Path

import requests

from . import config

API = "https://api.tcgdex.net/v2/en"
ASSETS = "https://assets.tcgdex.net"
LIMITLESS_IMG = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/tpci"
PASTA = config.PASTA_DADOS / "cartas"
PASTA_SETS = PASTA / "sets"
PASTA_IMG = PASTA / "img"
ARQ_INDICE = PASTA / "indice.json"
ARQ_ESTADO = PASTA / "estado.json"
ARQ_CODIGOS = PASTA / "codigos_aprendidos.json"
PASTA_MANUAIS = PASTA / "manuais"          # imagens que você adicionou à mão
ARQ_MANUAIS = PASTA / "manuais.json"

# Séries baixadas: Escarlate e Violeta (sv) e Mega Evolução (me) cobrem o formato Padrão atual.
SERIES = ("sv", "me")

# Códigos de coleção usados pelo Limitless/TCG Live. Quando o TCGdex informa o código, ele vale;
# esta tabela é só reserva. Códigos desconhecidos são aprendidos comparando nome + número.
CODIGOS_RESERVA = {
    "sv01": "SVI", "sv02": "PAL", "sv03": "OBF", "sv03.5": "MEW", "sv04": "PAR", "sv04.5": "PAF",
    "sv05": "TEF", "sv06": "TWM", "sv06.5": "SFA", "sv07": "SCR", "sv08": "SSP", "sv08.5": "PRE",
    "sv09": "JTG", "sv10": "DRI", "sv10.5b": "BLK", "sv10.5w": "WHT", "svp": "SVP", "sve": "SVE",
    "me01": "MEG", "me02": "PFL", "me02.5": "ASC", "30th": "30C", "mep": "MEP",
}

TIPOS_ENERGIA = ["Grass", "Fire", "Water", "Lightning", "Psychic", "Fighting", "Darkness", "Metal", "Fairy", "Dragon", "Colorless"]

progresso = {"ativo": False, "etapa": "", "pct": 0, "erro": "", "resumo": "", "ultima_verificacao": None}
_indice = None
_trava = threading.Lock()
_falhas = {}


# ------------------------------------------------------------------ utilidades

def normalizar(nome):
    nome = (nome or "").replace("’", "'").strip()
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", nome).lower()


def _num(n):
    return (str(n or "").lstrip("0") or "0").lower()


def rank_raridade(r):
    """Quanto menor, mais "básica" é a arte."""
    r = (r or "").lower()
    if any(x in r for x in ("illustration", "ultra", "hyper", "shiny", "secret", "full art", "gold", "rainbow", "black white")):
        return 9
    for i, nome in enumerate(["common", "uncommon", "rare", "double rare", "ace spec", "rare holo"]):
        if r == nome or r.startswith(nome):
            return {"common": 1, "uncommon": 2, "rare": 3, "rare holo": 3, "double rare": 4, "ace spec": 4}[nome]
    if r in ("none", "", "promo"):
        return 6
    return 7


def chave_funcional(c):
    """Cartas com a mesma chave são a mesma carta no jogo (só muda a arte)."""
    nome = normalizar(c.get("name"))
    if (c.get("category") or "").lower() != "pokemon":
        return nome
    golpes = sorted(normalizar(a.get("name")) for a in (c.get("attacks") or []))
    habs = sorted(normalizar(a.get("name")) for a in (c.get("abilities") or []))
    return f"{nome}|{c.get('hp') or ''}|{','.join(habs)}|{','.join(golpes)}"


def _codigo_do_set(s):
    for campo in ("tcgOnline",):
        if isinstance(s.get(campo), str) and s[campo]:
            return s[campo].upper()
    for campo in ("abbreviation", "abbreviations"):
        v = s.get(campo)
        if isinstance(v, dict) and v.get("official"):
            return v["official"].upper()
        if isinstance(v, str) and v:
            return v.upper()
    return CODIGOS_RESERVA.get(s.get("id"), "")


def _ler_json(caminho, padrao):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    tmp.replace(caminho)


# ------------------------------------------------------------------ índice

def montar_indice():
    """Lê todos os sets baixados e monta as buscas por nome e por coleção/número."""
    aprendidos = _ler_json(ARQ_CODIGOS, {})
    cartas, por_codigo, grupos = {}, {}, {}
    for arq in sorted(PASTA_SETS.glob("*.json")):
        dados = _ler_json(arq, None)
        if not dados:
            continue
        s = dados["set"]
        codigo = _codigo_do_set(s) or aprendidos.get(s["id"], "")
        serie = (s.get("serie") or {}).get("id") or ""
        for c in dados["cards"]:
            local = c.get("localId") or c["id"].split("-")[-1]
            e = {
                "id": c["id"], "nome": c.get("name", ""), "set": s["id"], "set_nome": s.get("name", ""),
                "serie": serie, "codigo": codigo, "numero": _num(local), "local": local,
                "raridade": c.get("rarity") or "", "categoria": c.get("category") or "",
                "data": s.get("releaseDate") or "", "img": c.get("image") or f"{ASSETS}/en/{serie}/{s['id']}/{local}",
                "tem_img": bool(c.get("image")),
                "tipos": c.get("types") or [], "chave": chave_funcional(c),
                "estagio": c.get("stage") or "", "ps": c.get("hp"),
            }
            cartas[e["id"]] = e
            if codigo:
                por_codigo[f"{codigo}|{e['numero']}"] = e["id"]
            grupos.setdefault(e["chave"], []).append(e["id"])

    # Imagens adicionadas à mão: substituem a imagem de uma impressão conhecida, ou criam a carta
    # se ela ainda não existir no TCGdex (ex.: coleção recém-lançada).
    for m in _ler_json(ARQ_MANUAIS, []):
        arq = PASTA_MANUAIS / m["arquivo"]
        if not arq.exists():
            continue
        codigo, numero = (m.get("codigo") or "").upper(), _num(m.get("numero"))
        id_ = por_codigo.get(f"{codigo}|{numero}") if codigo else None
        if id_:
            cartas[id_]["img_local"] = str(arq)
            cartas[id_]["tem_img"] = True
        else:
            nome = m["nome"]
            chaves_nome = [k for k, ids in grupos.items() if normalizar(cartas[ids[0]]["nome"]) == normalizar(nome)]
            chave = chaves_nome[0] if chaves_nome else normalizar(nome)
            id_ = f"manual-{codigo or 'X'}-{numero}"
            cartas[id_] = {"id": id_, "nome": nome, "set": "manual", "set_nome": "Adicionada à mão", "serie": "", "codigo": codigo,
                           "numero": numero, "local": numero, "raridade": "Manual", "categoria": m.get("categoria") or "",
                           "data": datetime.now().strftime("%Y-%m-%d"), "img": "", "img_local": str(arq), "tem_img": True,
                           "tipos": [], "chave": chave, "estagio": "", "ps": None}
            if codigo:
                por_codigo[f"{codigo}|{numero}"] = id_
            grupos.setdefault(chave, []).append(id_)
        if m.get("preferida"):
            cartas[id_]["preferida"] = True

    basica = {}  # chave funcional -> id da arte básica
    for chave, ids in grupos.items():
        melhor = min(ids, key=lambda i: (not cartas[i].get("preferida"), not cartas[i].get("tem_img", True), rank_raridade(cartas[i]["raridade"]),
                                         -int((cartas[i]["data"] or "0").replace("-", "") or 0)))
        basica[chave] = melhor
    por_nome = {}  # nome -> chaves (da mais recente para a mais antiga)
    for chave, id_ in basica.items():
        por_nome.setdefault(normalizar(cartas[id_]["nome"]), []).append(chave)
    for nome, chaves in por_nome.items():
        chaves.sort(key=lambda k: max(cartas[i]["data"] for i in grupos[k]), reverse=True)

    indice = {"cartas": cartas, "por_codigo": por_codigo, "basica": basica, "por_nome": por_nome, "grupos": grupos,
              "montado_em": datetime.now().isoformat(timespec="seconds")}
    _gravar_json(ARQ_INDICE, indice)
    global _indice
    with _trava:
        _indice = indice
    return indice


def indice():
    global _indice
    with _trava:
        if _indice is None:
            _indice = _ler_json(ARQ_INDICE, {"cartas": {}, "por_codigo": {}, "basica": {}, "por_nome": {}})
        return _indice


def _basica_de(id_):
    ind = indice()
    e = ind["cartas"].get(id_)
    if not e:
        return None
    return ind["cartas"].get(ind["basica"].get(e["chave"], id_), e)


def por_nome(nome):
    """Arte básica de uma carta pelo nome (como aparece no log do TCG Live)."""
    ind = indice()
    n = normalizar(nome)
    tentativas = [n, re.sub(r"^basic ", "", n), "basic " + n, re.sub(r" energy$", "", n) + " energy"]
    for t in tentativas:
        chaves = ind["por_nome"].get(t)
        if chaves:
            return ind["cartas"].get(ind["basica"][chaves[0]])
    if ind["cartas"]:
        nao_encontradas[nome] = nao_encontradas.get(nome, 0) + 1
    return None


nao_encontradas = {}  # nomes pedidos que não existem na biblioteca (mostrados na tela da Biblioteca)
falhas_imagem = {}    # cartas da biblioteca cuja imagem não foi possível baixar


def converter(codigo, numero, nome=None):
    """CONVERSOR: qualquer impressão (coleção + número) -> arte básica da mesma carta."""
    ind = indice()
    id_ = ind["por_codigo"].get(f"{(codigo or '').upper()}|{_num(numero)}")
    if id_:
        e = ind["cartas"][id_]
        if not nome or normalizar(e["nome"]) == normalizar(nome) or normalizar(nome) in normalizar(e["nome"]):
            return _basica_de(id_)
    if nome:
        # código desconhecido: procura um set sem código com o mesmo nome e número e aprende o código
        if codigo:
            for e in ind["cartas"].values():
                if not e["codigo"] and e["numero"] == _num(numero) and normalizar(e["nome"]) == normalizar(nome):
                    aprendidos = _ler_json(ARQ_CODIGOS, {})
                    aprendidos[e["set"]] = codigo.upper()
                    _gravar_json(ARQ_CODIGOS, aprendidos)
                    return _basica_de(e["id"])
        return por_nome(nome)
    return None


def info_publica(e):
    if not e:
        return None
    return {k: e[k] for k in ("id", "nome", "codigo", "numero", "set_nome", "raridade", "categoria", "tipos", "estagio", "ps")}


# ------------------------------------------------------------------ imagens

def caminho_imagem(id_, qualidade="low"):
    """Caminho local da imagem (baixa na primeira vez). None se não der para baixar."""
    ind = indice()
    e = ind["cartas"].get(id_)
    if not e:
        return None
    if e.get("img_local") and Path(e["img_local"]).exists():
        return Path(e["img_local"])
    for ext in ("webp", "png"):
        destino = PASTA_IMG / f"{id_}_{qualidade}.{ext}"
        if destino.exists() and destino.stat().st_size > 0:
            return destino
    chave_falha = f"{id_}_{qualidade}"
    if time.time() - _falhas.get(chave_falha, 0) < 600:
        return None  # falhou há pouco (sem internet?): não tenta de novo por 10 minutos
    # Ordem de tentativa: TCGdex (webp e png, nas duas qualidades), outras impressões da
    # mesma carta no TCGdex, e por fim a imagem do Limitless pela coleção e número.
    urls = []
    outras = [ind["cartas"][i] for i in ind.get("grupos", {}).get(e["chave"], []) if i != id_]
    for x in [e] + sorted(outras, key=lambda c: rank_raridade(c["raridade"])):
        for q in (qualidade, "high" if qualidade == "low" else "low"):
            urls += [f"{x['img']}/{q}.webp", f"{x['img']}/{q}.png"]
    for x in [e] + outras:
        if x.get("codigo") and x.get("numero", "").isdigit():
            urls.append(f"{LIMITLESS_IMG}/{x['codigo']}/{x['codigo']}_{int(x['numero']):03d}_R_EN_{'LG' if qualidade == 'high' else 'SM'}.png")
    for url in urls:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "TCGLiveTracker/1.0"})
        except requests.RequestException:
            continue
        if r.status_code == 200 and len(r.content) > 500:
            ext = "png" if r.content[:4] == b"\x89PNG" else "webp" if r.content[:4] == b"RIFF" else None
            if not ext:
                continue
            destino = PASTA_IMG / f"{id_}_{qualidade}.{ext}"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(r.content)
            falhas_imagem.pop(e["nome"], None)
            return destino
    _falhas[chave_falha] = time.time()
    falhas_imagem[e["nome"]] = f"{e.get('codigo') or e['set']} {e['numero']}"
    return None


def imagem_reserva(nome):
    """Desenho simples com o nome, usado enquanto a imagem real não está disponível."""
    from html import escape
    palavras, linhas, atual = (nome or "?").split(), [], ""
    for p in palavras:
        if len(atual) + len(p) > 12 and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    linhas.append(atual)
    textos = "".join(f'<text x="122" y="{150 + i * 30}" text-anchor="middle">{escape(l)}</text>' for i, l in enumerate(linhas[:5]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 245 337">'
            '<rect x="2" y="2" width="241" height="333" rx="14" fill="#2a3447" stroke="#E8B321" stroke-width="4"/>'
            f'<g fill="#E6EBF3" font-family="sans-serif" font-size="24" font-weight="600">{textos}</g></svg>')


# ------------------------------------------------------------------ download / atualização

def _get(sessao, caminho):
    for tentativa in range(3):
        try:
            r = sessao.get(API + caminho, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1.5 * (tentativa + 1))
    raise RuntimeError(f"O TCGdex não respondeu para {caminho}.")


def atualizar(forcar=False):
    """Baixa coleções novas ou que ganharam cartas. Roda em segundo plano."""
    if progresso["ativo"]:
        return
    progresso.update({"ativo": True, "etapa": "Consultando coleções no TCGdex", "pct": 0, "erro": "", "resumo": ""})
    novos = []
    try:
        s = requests.Session()
        s.headers["User-Agent"] = "TCGLiveTracker/1.0"
        # Coleções de cada série (o id nem sempre começa com a sigla da série: ex. "30th").
        alvo, vistos = [], set()
        for serie in SERIES:
            dados_serie = _get(s, f"/series/{serie}") or {}
            for b in dados_serie.get("sets") or []:
                if b.get("id") and b["id"] not in vistos:
                    vistos.add(b["id"])
                    alvo.append(b)
        if not alvo:  # reserva: filtra pela sigla
            alvo = [b for b in (_get(s, "/sets") or []) if re.match(rf"^({'|'.join(SERIES)})", b.get("id", ""))]
        for n, b in enumerate(alvo, 1):
            progresso["etapa"] = f"Coleção {b.get('name')} ({n}/{len(alvo)})"
            progresso["pct"] = round(100 * (n - 1) / max(len(alvo), 1))
            arq = PASTA_SETS / f"{b['id']}.json"
            atual = _ler_json(arq, None)
            total = (b.get("cardCount") or {}).get("total") or 0
            if atual and not forcar and len(atual["cards"]) >= total:
                continue
            detalhe = _get(s, f"/sets/{b['id']}")
            if not detalhe:
                continue
            ids = [c["id"] for c in detalhe.get("cards", [])]
            with ThreadPoolExecutor(max_workers=6) as ex:
                cartas = [c for c in ex.map(lambda i: _get(s, f"/cards/{i}"), ids) if c]
            detalhe.pop("cards", None)
            _gravar_json(arq, {"set": detalhe, "cards": cartas})
            novos.append(f"{b.get('name')} ({len(cartas)} cartas)")
        progresso["etapa"] = "Montando o índice"
        ind = montar_indice()
        progresso["resumo"] = (f"{len(ind['cartas'])} cartas em {len(list(PASTA_SETS.glob('*.json')))} coleções. "
                               + (f"Novidades: {', '.join(novos)}." if novos else "Nenhuma coleção nova."))
        progresso["pct"] = 100
        progresso["etapa"] = "Concluído"
        _gravar_json(ARQ_ESTADO, {"ultima_verificacao": datetime.now().isoformat(timespec="seconds"), "novos": novos})
        if novos:
            from . import banco
            banco.reconverter_listas()
    except Exception as e:
        progresso["erro"] = f"Não consegui atualizar a biblioteca: {e}"
    finally:
        progresso["ativo"] = False
        progresso["ultima_verificacao"] = _ler_json(ARQ_ESTADO, {}).get("ultima_verificacao")


def baixar_todas_imagens():
    """Opcional: baixa a arte básica de todas as cartas (para usar sem internet)."""
    if progresso["ativo"]:
        return
    progresso.update({"ativo": True, "etapa": "Baixando imagens", "pct": 0, "erro": "", "resumo": ""})
    try:
        ids = sorted(set(indice()["basica"].values()))
        feitos = 0
        with ThreadPoolExecutor(max_workers=6) as ex:
            for n, _ in enumerate(ex.map(caminho_imagem, ids), 1):
                feitos += 1
                progresso["pct"] = round(100 * n / max(len(ids), 1))
                progresso["etapa"] = f"Imagens {n}/{len(ids)}"
        progresso["resumo"] = f"{feitos} imagens de arte básica disponíveis."
    except Exception as e:
        progresso["erro"] = str(e)
    finally:
        progresso["ativo"] = False


def status():
    ind = indice()
    estado = _ler_json(ARQ_ESTADO, {})
    return {
        "cartas": len(ind["cartas"]), "artes_basicas": len(set(ind["basica"].values())),
        "colecoes": len(list(PASTA_SETS.glob("*.json"))) if PASTA_SETS.exists() else 0,
        "imagens": len([x for x in PASTA_IMG.glob("*_*.*") if x.suffix in (".webp", ".png")]) if PASTA_IMG.exists() else 0,
        "ultima_verificacao": estado.get("ultima_verificacao"), "novos": estado.get("novos", []),
        "nao_encontradas": sorted(nao_encontradas), "sem_imagem": falhas_imagem,
        "progresso": progresso,
    }


class Verificador:
    """Confere uma vez por dia se saiu coleção nova."""

    def __init__(self):
        self._thread = None

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="cartas", daemon=True)
        self._thread.start()

    def _loop(self):
        time.sleep(5)
        while True:
            ultima = _ler_json(ARQ_ESTADO, {}).get("ultima_verificacao")
            vencida = not ultima or datetime.fromisoformat(ultima) < datetime.now() - timedelta(hours=24)
            if vencida or not ARQ_INDICE.exists():
                atualizar()
            time.sleep(3600)


verificador = Verificador()


# ------------------------------------------------------------------ imagens adicionadas à mão

def adicionar_manual(nome, codigo, numero, conteudo, preferida=False, categoria=""):
    """Guarda uma imagem enviada por você e refaz o índice. conteudo = bytes da imagem."""
    if conteudo[:4] == b"\x89PNG":
        ext = "png"
    elif conteudo[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        ext = "webp"
    else:
        raise ValueError("O arquivo precisa ser uma imagem PNG, JPG ou WEBP.")
    if not (nome or "").strip():
        raise ValueError("Informe o nome da carta, como aparece no jogo.")
    codigo = (codigo or "").strip().upper()
    numero = _num(numero) if numero else ""
    base = re.sub(r"[^A-Za-z0-9-]", "_", f"{codigo or 'X'}_{numero or normalizar(nome)}")
    PASTA_MANUAIS.mkdir(parents=True, exist_ok=True)
    for antigo in PASTA_MANUAIS.glob(base + ".*"):
        antigo.unlink()
    (PASTA_MANUAIS / f"{base}.{ext}").write_bytes(conteudo)
    lista = [m for m in _ler_json(ARQ_MANUAIS, []) if not (m.get("codigo", "").upper() == codigo and _num(m.get("numero")) == numero and normalizar(m["nome"]) == normalizar(nome))]
    lista.append({"nome": nome.strip(), "codigo": codigo, "numero": numero, "arquivo": f"{base}.{ext}",
                  "preferida": bool(preferida), "categoria": categoria, "adicionada_em": datetime.now().isoformat(timespec="seconds")})
    _gravar_json(ARQ_MANUAIS, lista)
    montar_indice()
    _falhas.clear()
    falhas_imagem.pop(nome.strip(), None)
    nao_encontradas.pop(nome.strip(), None)


def listar_manuais():
    ind = indice()
    saida = []
    for m in _ler_json(ARQ_MANUAIS, []):
        id_ = ind["por_codigo"].get(f"{m.get('codigo', '').upper()}|{_num(m.get('numero'))}") if m.get("codigo") else None
        saida.append({**m, "id": id_})
    return saida


def remover_manual(arquivo):
    lista = _ler_json(ARQ_MANUAIS, [])
    _gravar_json(ARQ_MANUAIS, [m for m in lista if m["arquivo"] != arquivo])
    alvo = PASTA_MANUAIS / Path(arquivo).name
    if alvo.exists():
        alvo.unlink()
    montar_indice()
