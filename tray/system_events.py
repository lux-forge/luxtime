"""Native Windows lock/sleep/idle detection for the tray.

The tray is the only LuxTime component that runs continuously inside the
user's interactive session, which is what session-lock notifications and
idle-input detection both require - a Windows service (session 0) can't see
either reliably. This module only detects; it has no opinion on what should
happen when locked, asleep, or idle. `TrayApplication` decides that by
checking the user's settings (`stop_on_lock`, `stop_on_sleep`,
`idle_detection`, `resume_prompt`) before acting on a callback.

Lock/unlock and suspend/resume arrive as window messages
(WM_WTSSESSION_CHANGE, WM_POWERBROADCAST), so a hidden message-only window is
created on its own thread with a Win32 message pump. Idle detection has no
equivalent push notification - it's polled via GetLastInputInfo on a second
thread, gated by `idle_threshold_seconds` (read live so a settings change
takes effect without restarting the tray).
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import threading
from typing import Callable

import win32api
import win32con
import win32gui
import win32ts

# Not exposed by pywin32's win32con.
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8

IDLE_POLL_SECONDS = 15
ACTIVE_AGAIN_SECONDS = 5.0


class _LastInputInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def _idle_seconds() -> float:
    info = _LastInputInfo()
    info.cbSize = ctypes.sizeof(_LastInputInfo)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0


class SystemEventMonitor:
    def __init__(
        self,
        *,
        on_lock: Callable[[], None],
        on_unlock: Callable[[], None],
        on_suspend: Callable[[], None],
        on_resume: Callable[[], None],
        on_idle: Callable[[], None],
        on_idle_ended: Callable[[], None],
        idle_enabled: Callable[[], bool],
        idle_threshold_seconds: Callable[[], float],
    ) -> None:
        self._on_lock = on_lock
        self._on_unlock = on_unlock
        self._on_suspend = on_suspend
        self._on_resume = on_resume
        self._on_idle = on_idle
        self._on_idle_ended = on_idle_ended
        self._idle_enabled = idle_enabled
        self._idle_threshold_seconds = idle_threshold_seconds
        self._thread_id = 0
        self._stopping = threading.Event()
        self._is_idle = False

    def start(self) -> None:
        ready = threading.Event()
        threading.Thread(
            target=self._run_window, args=(ready,), name="luxtime-tray-events", daemon=True
        ).start()
        ready.wait(timeout=5)
        threading.Thread(
            target=self._run_idle_poll, name="luxtime-tray-idle", daemon=True
        ).start()

    def stop(self) -> None:
        self._stopping.set()
        if self._thread_id:
            win32api.PostThreadMessage(self._thread_id, win32con.WM_QUIT, 0, 0)

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_WTSSESSION_CHANGE:
            if wparam == WTS_SESSION_LOCK:
                self._on_lock()
            elif wparam == WTS_SESSION_UNLOCK:
                self._on_unlock()
            return 0
        if msg == win32con.WM_POWERBROADCAST:
            if wparam == win32con.PBT_APMSUSPEND:
                self._on_suspend()
            elif wparam in (win32con.PBT_APMRESUMEAUTOMATIC, win32con.PBT_APMRESUMESUSPEND):
                self._on_resume()
            return 1
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _run_window(self, ready: threading.Event) -> None:
        self._thread_id = win32api.GetCurrentThreadId()
        instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = instance
        window_class.lpszClassName = "LuxTimeTraySystemEvents"
        window_class.lpfnWndProc = self._wnd_proc
        atom = win32gui.RegisterClass(window_class)

        hwnd = win32gui.CreateWindow(
            atom, window_class.lpszClassName, 0, 0, 0, 0, 0, 0, 0, instance, None
        )
        win32ts.WTSRegisterSessionNotification(hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
        ready.set()
        win32gui.PumpMessages()

    def _run_idle_poll(self) -> None:
        while not self._stopping.wait(IDLE_POLL_SECONDS):
            if not self._idle_enabled():
                self._is_idle = False
                continue
            idle_for = _idle_seconds()
            if not self._is_idle and idle_for >= self._idle_threshold_seconds():
                self._is_idle = True
                self._on_idle()
            elif self._is_idle and idle_for < ACTIVE_AGAIN_SECONDS:
                self._is_idle = False
                self._on_idle_ended()
