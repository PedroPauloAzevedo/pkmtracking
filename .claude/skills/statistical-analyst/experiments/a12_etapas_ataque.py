"""
A12 — O "roteiro do ataque" dos juízes (Judge Ball, Karin Siehs, rev. nov/2024) aparece nos logs do TCG Live?
Fonte: https://www.judgeball.com/guidebook/tcg/attack-steps/ (resumo em knowledge/POKEMON_TCG_MODEL.md, seção 8).
Três perguntas, só com o texto dos logs (tabela `partidas`), sem mudar nada:
  1. Ordem do cálculo de dano: nas linhas "Damage breakdown", a Fraqueza vale o dobro do subtotal ANTES dela (depois dos efeitos
     do atacante) e a Resistência vem depois dos efeitos do atacante e não deixa o dano abaixo de 0?
  2. Nocautes simultâneos dos dois jogadores: quem pega prêmio primeiro? (roteiro: o adversário de quem joga o turno)
  3. Vários nocautes do mesmo dono no mesmo momento: o log escreve um "took N" só (prêmios juntos)? Isso explica parte da
     atribuição imperfeita de prêmios a cada nocaute em `leitor.resumo.nocautes` (lacuna G20).
Só lê (ponte em modo leitura). Resultado só com contagens (sem nick). Uso:  python -I a12_etapas_ataque.py <CÓPIA marcada>
"""
import collections
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "tools"))
import sa_tools as T  # noqa: E402
from ponte import carregar  # noqa: E402

t = carregar(sys.argv[1])
textos = [r["texto"] for r in t.banco.consultar("SELECT texto FROM partidas") if r["texto"]]
TURNO = re.compile(r"(?:Turn # \d+ - )?(.+?)'s Turn$")
TOOK = re.compile(r"(.+?) took (a|\d+) Prize cards?\.")

# 1. Damage breakdown
dano = collections.Counter()
for texto in textos:
    L = [l.strip() for l in texto.splitlines()]
    for i, l in enumerate(L):
        if "Damage breakdown" not in l:
            continue
        dano["blocos"] += 1
        parc = []
        for m in L[i + 1:i + 15]:
            if not m.startswith("•"):
                break
            nome, val = m.lstrip("• ").rsplit(":", 1)
            num = re.search(r"-?\d+", val)
            parc.append((nome.strip(), int(num.group()) if num else 0))
        nomes = [n for n, _ in parc]
        if "Total damage" in nomes:
            dano["com total"] += 1
        if "Damage" in nomes:
            dano["com parcela 'Damage' (aparece repetida: ver BATTLE_LOG_FORMAT)"] += 1
        corpo = [(n, v) for n, v in parc if n != "Total damage"]
        vistos_damage = False
        sub = 0
        for k, (n, v) in enumerate(corpo):
            if n == "Damage":          # o jogo repete a mesma parcela "Damage": conta uma vez só
                if not vistos_damage:
                    sub += v
                vistos_damage = True
                continue
            if n.startswith("Weakness"):
                dano["Fraqueza"] += 1
                dano["Fraqueza = subtotal anterior (dobro)"] += v == sub
                dano["Fraqueza depois de efeito do atacante"] += k > 1
            elif n.startswith("Resistance"):
                dano["Resistência"] += 1
                dano["Resistência = -30 ou leva a 0"] += v == -30 or sub + v == 0
                dano["Resistência depois de efeito do atacante"] += k > 1
            elif n != "Base damage" and any(x.startswith(("Weakness", "Resistance")) for x, _ in corpo[:k]):
                dano["efeito DEPOIS de Fraqueza/Resistência (lado do defensor)"] += 1
            sub += v

# 2 e 3. Nocautes e prêmios
ko = collections.Counter()
for texto in textos:
    L = [l.strip() for l in texto.splitlines()]
    dono_turno = None
    i = 0
    while i < len(L):
        m = TURNO.match(L[i])
        if m:
            dono_turno = m.group(1)
            i += 1
            continue
        if "was Knocked Out" not in L[i]:
            i += 1
            continue
        donos = []
        while i < len(L) and "was Knocked Out" in L[i]:
            donos.append(L[i].split("'s ")[0])
            i += 1
        took = []
        while i < len(L) and (L[i].startswith(("-", "•")) or " was discarded from " in L[i] or " were discarded" in L[i]
                              or (" took " in L[i] and "Prize" in L[i]) or " was added to " in L[i]):
            mm = TOOK.match(L[i])
            if mm:
                took.append(mm.group(1))
            i += 1
        cont = collections.Counter(donos)
        if len(cont) >= 2:
            ko["nocautes simultâneos dos dois jogadores"] += 1
            if len(took) >= 2 and dono_turno:
                ko["  o adversário de quem joga pegou primeiro"] += took[0] != dono_turno
                ko["  quem joga pegou primeiro"] += took[0] == dono_turno
        for dono, q in cont.items():
            if q >= 2:
                ko["2+ nocautes do mesmo dono juntos"] += 1
                n_took = sum(1 for x in took if x != dono)
                ko[f"  seguidos de {n_took} linha(s) 'took' do outro jogador"] += 1

res = {"partidas": len(textos), "dano": dict(dano), "nocautes": dict(ko)}
print(f"{len(textos)} partidas")
print("\n1. Damage breakdown"); [print(f"   {q:4}  {k}") for k, q in dano.items()]
print("\n2/3. Nocautes e prêmios"); [print(f"   {q:4}  {k}") for k, q in ko.items()]
arq = T.registrar("a12_etapas_ataque", res, t.pasta, AQUI / "resultados", copia=t.identificacao,
                  dados_usados={"n_registros": len(textos)},
                  filtros={"fonte": "tabela partidas (logs pessoais e de amigos)"})
print(f"\nresultado gravado em {arq.name}")
