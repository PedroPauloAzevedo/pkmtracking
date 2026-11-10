"""
COBERTURA: um quadrinho vermelho por cima do botão Continue do jogo enquanto o log é copiado.

Depois que a pessoa clica em Continue, o TCG Live descarta o Battle Log e a partida não pode
mais ser capturada. A cobertura segura esse clique por um ou dois segundos.
Clicar no quadrinho tira ele da frente na hora. (Ideia do Full Bench, licença MIT.)

Feita com as funções de janela do próprio Windows (ctypes), sem biblioteca extra: funciona
igual no Python instalado à mão e no instalador. Fora do Windows, não aparece.
"""
import itertools
import sys
import threading

_contador = itertools.count(1)

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _u = ctypes.WinDLL("user32", use_last_error=True)
    _g = ctypes.WinDLL("gdi32")
    _k = ctypes.WinDLL("kernel32")
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                    ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                    ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [("hdc", wintypes.HDC), ("fErase", wintypes.BOOL), ("rcPaint", wintypes.RECT),
                    ("fRestore", wintypes.BOOL), ("fIncUpdate", wintypes.BOOL), ("rgbReserved", ctypes.c_byte * 32)]

    _u.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    _u.DefWindowProcW.restype = LRESULT
    _u.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    _u.RegisterClassW.restype = wintypes.ATOM
    _u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    _u.CreateWindowExW.restype = wintypes.HWND
    _u.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    _u.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    _u.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    _u.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    _u.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]
    _u.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
    _u.BeginPaint.restype = wintypes.HDC
    _u.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
    _u.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _u.DrawTextW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.RECT), wintypes.UINT]
    _u.InvalidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
    _u.DestroyWindow.argtypes = [wintypes.HWND]
    _u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    _u.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
    _g.CreateSolidBrush.restype = wintypes.HBRUSH
    _g.CreateFontW.restype = wintypes.HFONT
    _g.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
    _g.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    _g.SelectObject.restype = wintypes.HGDIOBJ
    _g.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
    _g.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
    _g.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    _k.GetModuleHandleW.restype = wintypes.HMODULE
    _u.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
    _u.LoadCursorW.restype = wintypes.HANDLE

    WM_DESTROY, WM_PAINT, WM_CLOSE, WM_LBUTTONDOWN, WM_MOUSEACTIVATE = 0x0002, 0x000F, 0x0010, 0x0201, 0x0021
    WS_POPUP, WS_EX_TOPMOST, WS_EX_TOOLWINDOW, WS_EX_LAYERED, WS_EX_NOACTIVATE = 0x80000000, 0x8, 0x80, 0x80000, 0x08000000
    VERMELHO, BRANCO = 0x002B38C2, 0x00FFFFFF  # cores no formato do Windows (0x00BBGGRR)


class Cobertura:
    def __init__(self, x, y, largura, altura, texto="Copiando o log…"):
        self._fechada = threading.Event()
        self._texto = texto
        self._hwnd = None
        self.disponivel = sys.platform == "win32"
        if not self.disponivel:
            self._fechada.set()
            return
        folga = 8  # cobre um pouco além do botão
        self._geo = (int(x - folga), int(y - folga), int(largura + 2 * folga), int(altura + 2 * folga))
        pronta = threading.Event()
        threading.Thread(target=self._rodar, args=(pronta,), daemon=True, name="cobertura").start()
        pronta.wait(2)

    def _rodar(self, pronta):
        try:
            inst = _k.GetModuleHandleW(None)
            classe = f"ColetorCobertura{next(_contador)}"
            fonte = _g.CreateFontW(-max(14, self._geo[3] // 4), 0, 0, 0, 700, 0, 0, 0, 0, 0, 0, 0, 0, "Segoe UI")
            fundo = _g.CreateSolidBrush(VERMELHO)

            def proc(hwnd, msg, wp, lp):
                if msg == WM_PAINT:
                    ps = PAINTSTRUCT()
                    hdc = _u.BeginPaint(hwnd, ctypes.byref(ps))
                    r = wintypes.RECT()
                    _u.GetClientRect(hwnd, ctypes.byref(r))
                    r.left += 6
                    r.right -= 6
                    _g.SelectObject(hdc, fonte)
                    _g.SetTextColor(hdc, BRANCO)
                    _g.SetBkMode(hdc, 1)  # texto sem fundo próprio
                    # centraliza na vertical calculando a altura do texto quebrado em linhas
                    medida = wintypes.RECT(r.left, r.top, r.right, r.bottom)
                    _u.DrawTextW(hdc, self._texto, -1, ctypes.byref(medida), 0x0001 | 0x0010 | 0x0400)  # CENTER|WORDBREAK|CALCRECT
                    folga = max(0, ((r.bottom - r.top) - (medida.bottom - medida.top)) // 2)
                    r.top += folga
                    _u.DrawTextW(hdc, self._texto, -1, ctypes.byref(r), 0x0001 | 0x0010)
                    _u.EndPaint(hwnd, ctypes.byref(ps))
                    return 0
                if msg == WM_MOUSEACTIVATE:
                    return 3  # MA_NOACTIVATE: o clique não tira o foco do jogo
                if msg in (WM_LBUTTONDOWN, WM_CLOSE):
                    _u.DestroyWindow(hwnd)
                    return 0
                if msg == WM_DESTROY:
                    _u.PostQuitMessage(0)
                    return 0
                return _u.DefWindowProcW(hwnd, msg, wp, lp)

            self._proc = WNDPROC(proc)  # guardado para o Python não apagar a função
            wc = WNDCLASSW(lpfnWndProc=self._proc, hInstance=inst, lpszClassName=classe, hbrBackground=fundo,
                           hCursor=_u.LoadCursorW(None, ctypes.c_void_p(32649)))  # cursor de mão
            _u.RegisterClassW(ctypes.byref(wc))
            x, y, w, h = self._geo
            self._hwnd = _u.CreateWindowExW(WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE,
                                            classe, "Coletor", WS_POPUP, x, y, w, h, None, None, inst, None)
            _u.SetLayeredWindowAttributes(self._hwnd, 0, 235, 0x2)  # um pouco transparente
            _u.ShowWindow(self._hwnd, 4)  # SW_SHOWNOACTIVATE
            pronta.set()
            msg = wintypes.MSG()
            while _u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                _u.TranslateMessage(ctypes.byref(msg))
                _u.DispatchMessageW(ctypes.byref(msg))
            _u.UnregisterClassW(classe, inst)
            _g.DeleteObject(fonte)
            _g.DeleteObject(fundo)
        except Exception as e:
            print("[cobertura]", e)
        finally:
            pronta.set()
            self._fechada.set()

    def texto(self, novo):
        self._texto = novo
        if self._hwnd and not self._fechada.is_set():
            _u.InvalidateRect(self._hwnd, None, True)

    def fechar(self):
        if self._hwnd and not self._fechada.is_set():
            _u.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

    def fechada(self):
        """A pessoa já clicou no quadrinho (ou ele já foi fechado)?"""
        return self._fechada.is_set()

    def esperar_fechar(self, segundos):
        """Espera a pessoa clicar no quadrinho ou o tempo acabar."""
        if not self._fechada.wait(segundos):
            self.fechar()
