"""
DIAGNÓSTICO: procura, nas pastas do TCG Live, algum arquivo que contenha o log da partida.

Até onde sabemos, o jogo só entrega o log pela área de transferência. Mas se algum
arquivo do jogo também guardar as linhas do log, o coletor poderia ler direto do disco.
Este teste só LÊ arquivos; não altera nada.
"""
import os
import platform
import re
from pathlib import Path

SINAIS = [re.compile(rb"Turn # \d+ - .+'s Turn"), re.compile(rb"Knocked Out"), re.compile(rb"opening hand")]


def pastas_candidatas():
    casa = Path.home()
    if platform.system() == "Windows":
        bases = [casa / "AppData" / "LocalLow", casa / "AppData" / "Local", casa / "AppData" / "Roaming",
                 Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
                 Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
                 casa / "Documents"]
    else:
        bases = [casa / "Library" / "Logs", casa / "Library" / "Application Support",
                 casa / "Library" / "Containers", casa / ".config", Path("/Applications")]
    achadas = []
    for b in bases:
        if not b.exists():
            continue
        try:
            for filho in b.iterdir():
                nome = filho.name.lower()
                if filho.is_dir() and ("pok" in nome or "tcg" in nome):
                    achadas.append(filho)
        except OSError:
            continue
    return achadas


def procurar(limite_mb=80):
    resultados, olhados = [], 0
    for pasta in pastas_candidatas():
        for raiz, _, arquivos in os.walk(pasta):
            for a in arquivos:
                caminho = Path(raiz) / a
                try:
                    if caminho.stat().st_size > limite_mb * 1024 * 1024:
                        continue
                    dados = caminho.read_bytes()
                except OSError:
                    continue
                olhados += 1
                acertos = sum(1 for s in SINAIS if s.search(dados))
                if acertos >= 2:
                    resultados.append({"arquivo": str(caminho), "sinais": acertos,
                                       "tamanho_kb": round(len(dados) / 1024)})
    return {"pastas": [str(p) for p in pastas_candidatas()], "arquivos_olhados": olhados, "encontrados": resultados}


if __name__ == "__main__":
    r = procurar()
    print("Pastas do jogo encontradas:", *r["pastas"], sep="\n  ")
    print(f"Arquivos verificados: {r['arquivos_olhados']}")
    if r["encontrados"]:
        print("Arquivos que parecem conter o log:")
        for x in r["encontrados"]:
            print(f"  {x['arquivo']} ({x['tamanho_kb']} KB)")
    else:
        print("Nenhum arquivo com o log. A captura pela área de transferência continua sendo o caminho.")
