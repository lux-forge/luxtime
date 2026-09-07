"""Per-user singleton and control signal for the native tray process."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import threading
from typing import Callable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PID_FILE = REPOSITORY_ROOT / ".runtime" / "tray.pid"
MUTEX_NAME = r"Local\LuxTimeTray"
EXIT_EVENT_NAME = r"Local\LuxTimeTrayExit"
ERROR_ALREADY_EXISTS = 183
INFINITE = 0xFFFFFFFF


class TrayAlreadyRunningError(RuntimeError):
    pass


class TrayRuntime:
    def __init__(self) -> None:
        if os.name != "nt":
            raise RuntimeError("LuxTime tray requires Windows")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        self.kernel32.CreateMutexW.restype = wintypes.HANDLE
        self.kernel32.CreateEventW.argtypes = (
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        )
        self.kernel32.CreateEventW.restype = wintypes.HANDLE
        self.kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self.kernel32.CloseHandle.restype = wintypes.BOOL

        ctypes.set_last_error(0)
        self.mutex = self.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            self.kernel32.CloseHandle(self.mutex)
            raise TrayAlreadyRunningError("LuxTime tray is already running")

        self.exit_event = self.kernel32.CreateEventW(None, True, False, EXIT_EVENT_NAME)
        if not self.exit_event:
            self.kernel32.CloseHandle(self.mutex)
            raise ctypes.WinError(ctypes.get_last_error())
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding="ascii")

    def watch_for_exit(self, callback: Callable[[], None]) -> None:
        def wait() -> None:
            self.kernel32.WaitForSingleObject(self.exit_event, INFINITE)
            callback()

        threading.Thread(target=wait, name="luxtime-tray-exit", daemon=True).start()

    def close(self) -> None:
        try:
            if PID_FILE.is_file() and PID_FILE.read_text(encoding="ascii").strip() == str(os.getpid()):
                PID_FILE.unlink()
        except OSError:
            pass
        self.kernel32.CloseHandle(self.exit_event)
        self.kernel32.CloseHandle(self.mutex)
