"""
TRAVA DO MOUSE: enquanto o modo automático copia o log, os SEUS cliques dentro da janela do jogo não chegam ao jogo.

Por quê: no fim da partida, um clique seu em Continue (ou no Battle Log, ou em qualquer lugar) no meio da cópia fazia o
modo automático perder a partida ou clicar onde já não havia botão (relato do Pedro, 13/11/2026).

Como: um "gancho" do Windows (WH_MOUSE_LL) vê cada clique antes do jogo. O Windows marca os cliques feitos por programas
(os do modo automático) como "injetados"; só os cliques físicos são segurados, e só dentro da janela do jogo.
Fora do jogo o mouse funciona normal, e mexer o mouse (sem clicar) também.

Para nunca prender ninguém:
  - solta sozinha depois de `maximo` segundos (padrão 20);
  - clicar no quadrinho vermelho (área `livre`) solta na hora;
  - não precisa de administrador; se o programa fechar ou travar, o Windows tira o gancho.
Fora do Windows não faz nada (o modo automático continua sem a trava).
"""
import sys
import threading
import time

BOTAO_DESCE = {0x0201: "esq", 0x0204: "dir", 0x0207: "meio", 0x020B: "x"}
BOTAO_SOBE = {0x0202: "esq", 0x0205: "dir", 0x0208: "meio", 0x020C: "x"}
INJETADO = 0x01 | 0x02  # LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED


def _dentro(r, x, y):
    return bool(r) and r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]


class TravaMouse:
    """jogo e livre: (x, y, largura, altura) na tela. ao_liberar: chamada quando a pessoa clica na área livre."""

    def __init__(self, jogo, livre=None, maximo=20.0, ao_liberar=None, instalar=True):
        self.jogo, self.livre, self.ao_liberar = jogo, livre, ao_liberar
        self.seguradas = 0           # cliques seus que a trava segurou (vai para o registro)
        self._presos = set()          # botões cujo "apertar" foi segurado: o "soltar" também é segurado
        self._ativa = True
        self._fim = time.time() + maximo
        self._tid = None
        self.instalada = False
        if instalar and sys.platform == "win32":
            pronta = threading.Event()
            threading.Thread(target=self._rodar, args=(pronta,), daemon=True, name="trava_mouse").start()
            pronta.wait(2)

    def ativa(self):
        if self._ativa and time.time() >= self._fim:
            self.soltar()
        return self._ativa

    def decidir(self, msg, x, y, injetado):
        """True = segurar este evento. Separado do Windows para poder ser testado."""
        if injetado or not self.ativa():
            return False
        if msg in BOTAO_DESCE:
            if _dentro(self.livre, x, y):
                self.soltar()  # clicou no quadrinho vermelho: solta tudo (o quadrinho recebe o clique e fecha)
                if self.ao_liberar:
                    self.ao_liberar()
                return False
            if _dentro(self.jogo, x, y):
                self._presos.add(BOTAO_DESCE[msg])
                self.seguradas += 1
                return True
            return False
        if msg in BOTAO_SOBE and BOTAO_SOBE[msg] in self._presos:
            self._presos.discard(BOTAO_SOBE[msg])
            return True  # o "soltar" de um clique segurado também não chega ao jogo
        return False

    def soltar(self):
        self._ativa = False
        if self._tid:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)  # WM_QUIT: tira o gancho
            self._tid = None

    # ------------------------------------------------------------------ Windows
    def _rodar(self, pronta):
        import ctypes
        from ctypes import wintypes
        u = ctypes.WinDLL("user32", use_last_error=True)  # instância própria: não mexe nas funções de outros módulos
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        LRESULT = ctypes.c_ssize_t

        class MSLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("pt", wintypes.POINT), ("mouseData", wintypes.DWORD), ("flags", wintypes.DWORD),
                        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        u.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        u.SetWindowsHookExW.restype = wintypes.HHOOK
        u.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        u.CallNextHookEx.restype = LRESULT
        u.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        u.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        k.GetModuleHandleW.restype = wintypes.HMODULE
        gancho = None

        def proc(n, wp, lp):
            try:
                if n == 0:
                    info = ctypes.cast(lp, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    if self.decidir(int(wp), info.pt.x, info.pt.y, bool(info.flags & INJETADO)):
                        return 1
            except Exception:
                pass  # na dúvida, deixa o clique passar
            return u.CallNextHookEx(gancho, n, wp, lp)

        self._proc = HOOKPROC(proc)  # guardado para o Python não apagar a função
        try:
            self._tid = k.GetCurrentThreadId()
            gancho = u.SetWindowsHookExW(14, self._proc, k.GetModuleHandleW(None), 0)  # 14 = WH_MOUSE_LL
            self.instalada = bool(gancho)
            pronta.set()
            if not gancho:
                self._ativa = False
                return
            msg = wintypes.MSG()
            # GetMessage acorda a cada evento; o tempo máximo é conferido pelo timer abaixo
            threading.Timer(max(0.0, self._fim - time.time()) + 0.05, self.soltar).start()
            while self._ativa and u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                pass
        except Exception as e:
            print("[trava do mouse]", e)
        finally:
            if gancho:
                u.UnhookWindowsHookEx(gancho)
            self._ativa = False
            pronta.set()
