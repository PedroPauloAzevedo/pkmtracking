"""
REGRAS DO STANDARD dentro do programa (o programa só trabalha com o formato Standard).

1. A BASE DE REGRAS: resumo em português dos documentos oficiais da Play! Pokémon.
     docs/regras-standard.md   cópia que vem com o programa
     dados/regras-standard.md  cópia mais nova, baixada do GitHub (confere 1 vez por dia)
   A base é revisada todo mês. Quando muda, a cópia no GitHub é atualizada e o programa
   baixa sozinho, sem precisar instalar versão nova. A tela "Regras do Standard" mostra o texto.

2. As regras que o LEITOR DE LOGS, o replay e as análises usam. Sempre que dá, elas são
   lidas da própria base (assim uma rotação de marcas chega sem atualizar o programa):
     - marcas de regulamento válidas: tabela "Marcas de regulamento do Standard";
     - deck de 60 cartas, até 4 com o mesmo nome (fora Energia Básica), 1 ACE SPEC, 1 Básico;
     - 6 prêmios por partida; nocaute de Pokémon ex vale 2 e de Mega Evolution ex vale 3;
     - primeiro turno: quem começa não ataca nem joga Apoiador; ninguém evolui no próprio
       primeiro turno nem evolui um Pokémon que entrou em jogo naquele turno.
"""
import json
import re
import threading
import time
from datetime import date, datetime, timedelta

import requests

from . import config

ARQ_EMBUTIDO = config.RAIZ / "docs" / "regras-standard.md"
ARQ_BAIXADO = config.PASTA_DADOS / "regras-standard.md"
ARQ_ESTADO = config.PASTA_DADOS / "regras-standard.json"
CAMINHO_GITHUB = "docs/regras-standard.md"
PAGINA_OFICIAL = "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources"

TAMANHO_DECK = 60
MAX_COPIAS = 4
MAX_ACE_SPEC = 1
PREMIOS_PARTIDA = 6
MARCAS_RESERVA = ("H", "I", "J")  # usadas só se a base não puder ser lida
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}

estado = {"verificado_em": None, "erro": "", "mensagem": "", "verificando": False}
_cache = {}


# ------------------------------------------------------------------ texto da base

def data_pt(texto):
    """'05/abr/2024' ou '5/abr/2024' -> date. None se não entender."""
    m = re.search(r"(\d{1,2})º?/([a-zç]{3})/(\d{4})", (texto or "").lower())
    if not m or m.group(2) not in MESES:
        return None
    try:
        return date(int(m.group(3)), MESES[m.group(2)], int(m.group(1)))
    except ValueError:
        return None


def _data_do_texto(t):
    """Data da base: linha 'Atualizada em 30/out/2026.' (ou a data mais recente do histórico)."""
    m = re.search(r"^Atualizada em (.+?)\.?\s*$", t[:600], re.M)
    if m and data_pt(m.group(1)):
        return data_pt(m.group(1))
    hist = t.split("### Histórico de atualizações")[-1] if "### Histórico de atualizações" in t else ""
    datas = [d for d in (data_pt(x) for x in re.findall(r"^\|\s*([^|]+?)\s*\|", hist, re.M)) if d]
    return max(datas) if datas else None


def _ler(arq):
    try:
        return arq.read_text(encoding="utf-8")
    except OSError:
        return ""


def _candidatos():
    saida = []
    for arq, fonte in ((ARQ_BAIXADO, "baixada"), (ARQ_EMBUTIDO, "programa")):
        t = _ler(arq)
        if t.strip().startswith("#"):
            saida.append({"arq": arq, "fonte": fonte, "texto": t, "data": _data_do_texto(t),
                          "mtime": arq.stat().st_mtime})
    return saida


def base():
    """A cópia mais nova da base: {texto, fonte ('programa' ou 'baixada'), atualizada_em}."""
    try:
        chave = tuple((a.stat().st_mtime if a.exists() else 0) for a in (ARQ_BAIXADO, ARQ_EMBUTIDO))
    except OSError:
        chave = None
    if chave and _cache.get("base_chave") == chave:
        return _cache["base"]
    cands = _candidatos()
    if not cands:
        b = {"texto": "", "fonte": "", "atualizada_em": None}
    else:
        melhor = max(cands, key=lambda c: (c["data"] or date.min, c["mtime"]))
        b = {"texto": melhor["texto"], "fonte": melhor["fonte"],
             "atualizada_em": melhor["data"].isoformat() if melhor["data"] else None}
    _cache.update(base_chave=chave, base=b)
    _cache.pop("marcas", None)
    return b


def secao(titulo):
    """Texto de uma seção (### ou ##) da base, sem o título."""
    t = base()["texto"]
    m = re.search(rf"^#{{2,3}}\s+{re.escape(titulo)}\s*$(.*?)(?=^#{{1,3}}\s|\Z)", t, re.M | re.S)
    return m.group(1).strip() if m else ""


# ------------------------------------------------------------------ regras usadas pelo programa

def marcas_standard(hoje=None):
    """Marcas de regulamento que valem hoje, lidas da tabela da base (ex.: ('H', 'I', 'J'))."""
    hoje = hoje or date.today()
    b = base()
    if "marcas" in _cache and _cache["marcas"][0] == hoje:
        return _cache["marcas"][1]
    marcas = []
    for linha in secao("Marcas de regulamento do Standard").splitlines():
        c = [x.strip() for x in linha.strip().strip("|").split("|")]
        if len(c) >= 2 and re.fullmatch(r"[A-Z]", c[0]):
            d = data_pt(c[1])
            if d is None or d <= hoje:   # marca anunciada para o futuro só vale a partir da data
                marcas.append(c[0])
    marcas = tuple(marcas) or MARCAS_RESERVA
    if b["texto"]:
        _cache["marcas"] = (hoje, marcas)
    return marcas


def promos_liberados():
    """Cartas de séries antigas que a base lista como promos liberados no Standard
    (ex.: Professor's Research SWSH152). Valem pelo nome, como qualquer reimpressão idêntica."""
    t = secao("Quando uma carta nova passa a valer")
    m = re.search(r"\*\*Promos já liberados:\*\*(.+)", t)
    if not m:
        return set()
    return {n.strip() for n, _ in re.findall(r"([A-Z][^,()]*?)\s*\(([A-Z]{2,6}\d{1,4}[^)]*)\)", m.group(1))}


def premios_do_nocaute(nome):
    """Prêmios que o rival pega ao nocautear este Pokémon (efeitos de outras cartas à parte)."""
    n = (nome or "").strip()
    if re.search(r" ex$", n):
        return 3 if n.startswith("Mega ") else 2
    return 1


def resumo():
    b = base()
    return {
        "marcas": list(marcas_standard()), "tamanho_deck": TAMANHO_DECK, "max_copias": MAX_COPIAS,
        "max_ace_spec": MAX_ACE_SPEC, "premios": PREMIOS_PARTIDA, "atualizada_em": b["atualizada_em"],
    }


def divisoes_idade(hoje=None):
    """Divisões de idade da temporada atual (a temporada começa em 1º de setembro).
    Temporada iniciada no ano A: Junior nasceu em A-11 ou depois; Senior de A-15 a A-12; Masters A-16 ou antes."""
    hoje = hoje or date.today()
    a = hoje.year if hoje.month >= 9 else hoje.year - 1
    return {"temporada_inicio": a, "junior": a - 11, "senior": (a - 15, a - 12), "masters": a - 16}


def divisao_por_ano(ano, hoje=None):
    d = divisoes_idade(hoje)
    try:
        ano = int(ano)
    except (TypeError, ValueError):
        return ""
    if ano >= d["junior"]:
        return "junior"
    if ano >= d["senior"][0]:
        return "senior"
    return "masters"


# ------------------------------------------------------------------ atualização pela cópia do GitHub

def _ler_estado():
    try:
        return json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def verificar_atualizacao():
    """Baixa a cópia do GitHub e guarda em dados/ se for mais nova que a atual."""
    from . import atualizador
    cfg = config.ler_config()
    repo, ramo = (cfg.get("github_repo") or "").strip(), cfg.get("github_ramo") or "main"
    estado.update(verificando=True, erro="")
    try:
        if not repo:
            raise RuntimeError("Sem repositório do GitHub configurado (Ajustes > Atualizações).")
        r = requests.get(f"https://api.github.com/repos/{repo}/contents/{CAMINHO_GITHUB}?ref={ramo}",
                         headers={**atualizador._cabecalhos(cfg), "Accept": "application/vnd.github.raw"}, timeout=20)
        if r.status_code == 404:
            raise RuntimeError("A base de regras ainda não está no GitHub.")
        r.raise_for_status()
        r.encoding = "utf-8"
        remoto = r.text
        if not remoto.strip().startswith("#"):
            raise RuntimeError("O arquivo baixado não parece a base de regras.")
        atual = base()
        d_rem = _data_do_texto(remoto)
        d_atual = date.fromisoformat(atual["atualizada_em"]) if atual["atualizada_em"] else None
        if remoto.strip() == (atual["texto"] or "").strip():
            estado["mensagem"] = "A base de regras já está na versão mais nova."
        elif d_atual and d_rem and d_rem < d_atual:
            estado["mensagem"] = "A cópia do programa é mais nova que a do GitHub."
        else:
            ARQ_BAIXADO.parent.mkdir(parents=True, exist_ok=True)
            tmp = ARQ_BAIXADO.with_suffix(".tmp")
            tmp.write_text(remoto, encoding="utf-8")
            tmp.replace(ARQ_BAIXADO)
            _cache.clear()
            estado["mensagem"] = f"Base de regras atualizada ({d_rem.strftime('%d/%m/%Y') if d_rem else 'data não informada'})."
        estado["verificado_em"] = datetime.now().isoformat(timespec="seconds")
        ARQ_ESTADO.write_text(json.dumps({"verificado_em": estado["verificado_em"]}), encoding="utf-8")
    except (requests.RequestException, RuntimeError, OSError) as e:
        estado["erro"] = f"Não consegui procurar atualização da base de regras: {e}"
    finally:
        estado["verificando"] = False
    return estado


def status():
    """Para a tela Regras do Standard: texto, de onde veio, data e a última verificação."""
    if not estado["verificado_em"]:
        estado["verificado_em"] = _ler_estado().get("verificado_em")
    b = base()
    return {**b, "estado": estado, "regras": resumo(), "pagina_oficial": PAGINA_OFICIAL}


class Verificador:
    """Confere a cópia do GitHub uma vez por dia."""

    def __init__(self):
        self._thread = None

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="regras-standard", daemon=True)
        self._thread.start()

    def _loop(self):
        time.sleep(30)
        while True:
            ultima = _ler_estado().get("verificado_em")
            try:
                vencida = not ultima or datetime.fromisoformat(ultima) < datetime.now() - timedelta(hours=24)
            except ValueError:
                vencida = True
            if vencida and config.ler_config().get("github_repo"):
                verificar_atualizacao()
            time.sleep(3600)


verificador = Verificador()
