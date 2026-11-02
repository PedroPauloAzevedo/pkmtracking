"""
BANDEJA: ícone do programa perto do relógio do Windows (no lugar da janela preta).

  - Clique no ícone: abre o painel no navegador.
  - Botão direito: Abrir painel, Captura ligada/desligada, Sair.
  - Bolinha verde no ícone = captura ligada; cinza = desligada.
  - Quando uma partida nova entra, aparece um aviso do Windows.

Precisa de pystray e pillow (requirements.txt). Sem eles, o programa volta a usar a
janela preta como antes (ver disponivel() e app.py).
"""
import threading
import time

from . import avisos, config, janela
from .coletor import coletor

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:  # biblioteca ausente ou quebrada: app.py usa a janela preta
    pystray = None

NOME = "Coletor TCG Live"


def disponivel():
    return pystray is not None


def desenhar(ligada=True, tamanho=64):
    """Desenha o ícone: quadrado azul com duas cartas e a bolinha de estado da captura."""
    s = tamanho / 64
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, tamanho - 1, tamanho - 1], radius=int(14 * s), fill=(37, 78, 160, 255))
    d.rounded_rectangle([int(13 * s), int(14 * s), int(35 * s), int(46 * s)], radius=int(4 * s),
                        fill=(170, 195, 240, 255))  # carta de trás
    d.rounded_rectangle([int(22 * s), int(10 * s), int(44 * s), int(42 * s)], radius=int(4 * s),
                        fill=(255, 255, 255, 255), outline=(37, 78, 160, 255), width=max(1, int(2 * s)))
    d.ellipse([int(28 * s), int(20 * s), int(38 * s), int(30 * s)], fill=(37, 78, 160, 255))
    cor = (46, 180, 90, 255) if ligada else (150, 150, 150, 255)
    d.ellipse([int(38 * s), int(38 * s), int(60 * s), int(60 * s)], fill=cor, outline=(255, 255, 255, 255),
              width=max(1, int(3 * s)))
    return img


def salvar_ico(destino):
    """Grava o ícone em .ico (usado pelos atalhos da Área de Trabalho e do Windows)."""
    desenhar(True, 256).save(destino, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])


def rodar(url, ao_sair):
    """Mostra o ícone e só volta quando a pessoa escolhe Sair. Roda na thread principal."""
    def abrir(icone=None, item=None):
        janela.abrir(url)

    def alternar_captura(icone, item):
        cfg = config.ler_config()
        cfg["coletor_ativo"] = not cfg["coletor_ativo"]
        config.salvar_config(cfg)
        coletor.iniciar() if cfg["coletor_ativo"] else coletor.parar()

    def sair(icone, item):
        icone.visible = False
        icone.stop()

    icone = pystray.Icon("coletor_tcg_live", desenhar(coletor.ativo), NOME, menu=pystray.Menu(
        pystray.MenuItem("Abrir painel", abrir, default=True),
        pystray.MenuItem("Captura de partidas ligada", alternar_captura,
                         checked=lambda item: config.ler_config()["coletor_ativo"]),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair (para de capturar)", sair),
    ))

    def vigiar(icone):
        """Troca a cor da bolinha e avisa quando entra partida nova."""
        icone.visible = True
        ligada, vista = None, coletor.ultima["id"] if coletor.ultima else None
        while icone.visible:
            if coletor.ativo != ligada:
                ligada = coletor.ativo
                icone.icon = desenhar(ligada)
                icone.title = f"{NOME}: captura {'ligada' if ligada else 'desligada'}"
            u = coletor.ultima
            if u and u["id"] != vista:
                vista = u["id"]
                try:
                    extra = f" ({u['nao_lidas']} linha(s) não lida(s))" if u.get("nao_lidas") else ""
                    icone.notify(f"Partida #{u['id']} registrada{extra}.", NOME)
                except Exception:
                    pass
            time.sleep(1)

    avisos.ouvintes.append(lambda texto: icone.notify(texto, NOME))  # ex.: partida perdida no modo automático
    icone.run(setup=vigiar)
    ao_sair()


def em_segundo_plano(url, ao_sair):
    """Para quando o programa não pode usar a thread principal (não é o caso hoje)."""
    threading.Thread(target=rodar, args=(url, ao_sair), daemon=True, name="bandeja").start()
