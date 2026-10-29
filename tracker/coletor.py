"""
COLETOR: vigia a área de transferência (Ctrl+C) e grava todo log do TCG Live que aparecer.

No fim da partida, o TCG Live mostra o botão "Battle Log"; dentro dele, o botão de
exportar copia o log inteiro para a área de transferência. Este coletor percebe isso
na hora e grava a partida, sem você precisar colar em lugar nenhum.
(O modo automático, em auto_export.py, aperta esses dois botões por você.)

Lemos a área de transferência sem bibliotecas extras:
  Windows -> API do próprio Windows (ctypes)
  macOS   -> comando pbpaste
  Linux   -> xclip ou xsel, se instalados
"""
import platform
import subprocess
import threading
import time

from . import banco, config, leitor

SISTEMA = platform.system()


# ------------------------------------------------------------ leitura da área de transferência
if SISTEMA == "Windows":
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _user32.OpenClipboard.argtypes = [wintypes.HWND]
    _user32.OpenClipboard.restype = wintypes.BOOL
    _user32.GetClipboardData.argtypes = [wintypes.UINT]
    _user32.GetClipboardData.restype = wintypes.HANDLE
    _user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    _user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
    _kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalLock.restype = wintypes.LPVOID
    _kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    CF_UNICODETEXT = 13

    def versao_area():
        """Número que muda toda vez que algo é copiado (evita reler à toa)."""
        return int(_user32.GetClipboardSequenceNumber())

    def ler_area():
        if not _user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""
        for _ in range(5):  # outro programa pode estar usando; tenta de novo
            if _user32.OpenClipboard(None):
                break
            time.sleep(0.1)
        else:
            return None
        try:
            h = _user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ""
            p = _kernel32.GlobalLock(h)
            if not p:
                return ""
            try:
                return ctypes.wstring_at(p)
            finally:
                _kernel32.GlobalUnlock(h)
        finally:
            _user32.CloseClipboard()
else:
    def versao_area():
        return None  # sem contador: comparamos o texto

    def ler_area():
        comandos = [["pbpaste"]] if SISTEMA == "Darwin" else [["xclip", "-selection", "clipboard", "-o"], ["xsel", "-b", "-o"]]
        for cmd in comandos:
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=3)
                if r.returncode == 0:
                    return r.stdout.decode("utf-8", errors="replace")
            except (OSError, subprocess.TimeoutExpired):
                continue
        return None


# ------------------------------------------------------------ o vigia
class Coletor:
    def __init__(self):
        self.ativo = False
        self.erro = ""
        self.ultima = None          # {"id":..., "quando":...} da última partida capturada
        self.capturadas = 0
        self.origem_proxima = "area_transferencia"   # o modo automático muda isso antes de clicar
        self._thread = None
        self._parar = threading.Event()

    def iniciar(self):
        if self._thread and self._thread.is_alive():
            return
        self._parar.clear()
        self._thread = threading.Thread(target=self._loop, name="coletor", daemon=True)
        self._thread.start()

    def parar(self):
        self._parar.set()

    def _loop(self):
        self.ativo = True
        ultima_versao, ultimo_texto = None, None
        if ler_area() is None and SISTEMA not in ("Windows", "Darwin"):
            self.erro = "Não consegui ler a área de transferência. No Linux, instale o xclip."
        while not self._parar.is_set():
            cfg = config.ler_config()
            try:
                v = versao_area()
                if v is None or v != ultima_versao:
                    ultima_versao = v
                    texto = ler_area()
                    if texto and texto != ultimo_texto:
                        ultimo_texto = texto
                        if leitor.parece_log(texto):
                            pid, nova = banco.inserir_partida(texto, self.origem_proxima, config.ler_regras())
                            self.origem_proxima = "area_transferencia"
                            if nova:
                                self.capturadas += 1
                                p = banco.obter_partida(pid)
                                self.ultima = {"id": pid, "quando": time.strftime("%H:%M:%S"),
                                               "nao_lidas": len(p["nao_lidas"]) if p else 0}
                                print(f"[coletor] Partida #{pid} registrada.")
                self.erro = ""
            except Exception as e:  # nunca deixa o vigia morrer
                self.erro = f"Erro no coletor: {e}"
            self._parar.wait(float(cfg.get("intervalo_coletor", 1.0)))
        self.ativo = False


coletor = Coletor()
