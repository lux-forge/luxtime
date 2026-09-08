"""Native Windows lock and unlock notifications for the interactive tray."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import threading
from typing import Callable, Literal

SessionEvent = Literal["lock", "unlock"]

NOTIFY_FOR_THIS_SESSION = 0
WM_QUIT = 0x0012
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x0007
WTS_SESSION_UNLOCK = 0x0008

_CALLBACK_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
_LRESULT = ctypes.c_ssize_t
_WNDPROC = _CALLBACK_FACTORY(
    _LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class _WNDCLASSW(ctypes.Structure):
    _fields_ = (
        ("style", wintypes.UINT),
        ("lpfnWndProc", _WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    )


class WindowsSessionMonitor:
    """Receive this user's Windows lock and unlock events on a hidden window."""

    def __init__(self, callback: Callable[[SessionEvent], None]) -> None:
        self.callback = callback
        self._native_window_proc = _WNDPROC(self._window_proc)
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._startup_error: BaseException | None = None
        self._user32 = None

    def _dispatch(self, event_type: int) -> None:
        if event_type == WTS_SESSION_LOCK:
            self.callback("lock")
        elif event_type == WTS_SESSION_UNLOCK:
            self.callback("unlock")

    def _window_proc(self, hwnd, message: int, wparam, lparam):
        if message == WM_WTSSESSION_CHANGE:
            try:
                self._dispatch(int(wparam))
            except Exception:
                pass
            return 0
        return self._user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def start(self) -> None:
        if os.name != "nt":
            raise RuntimeError("Windows session monitoring requires Windows")
        if self._thread is not None and self._thread.is_alive():
            return

        self._ready.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._message_loop,
            name="luxtime-session-events",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("Windows session monitor did not start within five seconds")
        if self._startup_error is not None:
            raise RuntimeError("Windows session monitor could not start") from self._startup_error

    def _message_loop(self) -> None:
        class_name = f"LuxTimeSessionMonitor_{os.getpid()}_{id(self):x}"
        instance = None
        window = None
        registered = False
        class_registered = False
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            wtsapi32 = ctypes.WinDLL("wtsapi32", use_last_error=True)
            self._user32 = user32

            kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
            kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD
            user32.RegisterClassW.argtypes = (ctypes.POINTER(_WNDCLASSW),)
            user32.RegisterClassW.restype = wintypes.WORD
            user32.CreateWindowExW.argtypes = (
                wintypes.DWORD,
                wintypes.LPCWSTR,
                wintypes.LPCWSTR,
                wintypes.DWORD,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.HWND,
                wintypes.HMENU,
                wintypes.HINSTANCE,
                wintypes.LPVOID,
            )
            user32.CreateWindowExW.restype = wintypes.HWND
            user32.DefWindowProcW.argtypes = (
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            )
            user32.DefWindowProcW.restype = _LRESULT
            user32.GetMessageW.argtypes = (
                ctypes.POINTER(wintypes.MSG),
                wintypes.HWND,
                wintypes.UINT,
                wintypes.UINT,
            )
            user32.GetMessageW.restype = wintypes.BOOL
            user32.TranslateMessage.argtypes = (ctypes.POINTER(wintypes.MSG),)
            user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)
            user32.DestroyWindow.argtypes = (wintypes.HWND,)
            user32.UnregisterClassW.argtypes = (wintypes.LPCWSTR, wintypes.HINSTANCE)
            wtsapi32.WTSRegisterSessionNotification.argtypes = (
                wintypes.HWND,
                wintypes.DWORD,
            )
            wtsapi32.WTSRegisterSessionNotification.restype = wintypes.BOOL
            wtsapi32.WTSUnRegisterSessionNotification.argtypes = (wintypes.HWND,)
            wtsapi32.WTSUnRegisterSessionNotification.restype = wintypes.BOOL

            instance = kernel32.GetModuleHandleW(None)
            window_class = _WNDCLASSW(
                lpfnWndProc=self._native_window_proc,
                hInstance=instance,
                lpszClassName=class_name,
            )
            if not user32.RegisterClassW(ctypes.byref(window_class)):
                raise ctypes.WinError(ctypes.get_last_error())
            class_registered = True

            window = user32.CreateWindowExW(
                0,
                class_name,
                "LuxTime session events",
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                instance,
                None,
            )
            if not window:
                raise ctypes.WinError(ctypes.get_last_error())
            if not wtsapi32.WTSRegisterSessionNotification(window, NOTIFY_FOR_THIS_SESSION):
                raise ctypes.WinError(ctypes.get_last_error())
            registered = True
            self._thread_id = int(kernel32.GetCurrentThreadId())
            self._ready.set()

            message = wintypes.MSG()
            while True:
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    raise ctypes.WinError(ctypes.get_last_error())
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except BaseException as error:
            if not self._ready.is_set():
                self._startup_error = error
        finally:
            if registered and window:
                wtsapi32.WTSUnRegisterSessionNotification(window)
            if window:
                user32.DestroyWindow(window)
            if class_registered:
                user32.UnregisterClassW(class_name, instance)
            self._thread_id = None
            self._ready.set()

    def close(self) -> None:
        thread = self._thread
        thread_id = self._thread_id
        if thread is None or thread_id is None:
            return

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PostThreadMessageW.argtypes = (
            wintypes.DWORD,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        user32.PostThreadMessageW.restype = wintypes.BOOL
        user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)
        thread.join(timeout=5)
        self._thread = None
