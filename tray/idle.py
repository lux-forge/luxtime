"""Windows mouse/keyboard idle detection for the interactive tray session."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = (("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD))


def windows_idle_seconds() -> float:
    """Return seconds since input in the current interactive Windows session."""

    if os.name != "nt":
        raise RuntimeError("Windows idle detection requires Windows")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.GetLastInputInfo.argtypes = (ctypes.POINTER(_LASTINPUTINFO),)
    user32.GetLastInputInfo.restype = wintypes.BOOL
    kernel32.GetTickCount64.argtypes = ()
    kernel32.GetTickCount64.restype = ctypes.c_ulonglong

    last_input = _LASTINPUTINFO(cbSize=ctypes.sizeof(_LASTINPUTINFO))
    if not user32.GetLastInputInfo(ctypes.byref(last_input)):
        raise ctypes.WinError(ctypes.get_last_error())

    current_tick = int(kernel32.GetTickCount64()) & 0xFFFFFFFF
    idle_milliseconds = (current_tick - int(last_input.dwTime)) & 0xFFFFFFFF
    return idle_milliseconds / 1000


@dataclass(frozen=True)
class IdleTrigger:
    idle_seconds: float
    cutoff_at: datetime


class IdleDetector:
    """Edge-trigger an idle action once for each period without user input."""

    def __init__(self) -> None:
        self._handled = False

    def check(
        self,
        *,
        enabled: bool,
        threshold_minutes: int,
        has_running_sessions: bool,
        idle_seconds: float,
        now: datetime | None = None,
    ) -> IdleTrigger | None:
        threshold_seconds = threshold_minutes * 60
        if not enabled or idle_seconds < threshold_seconds:
            self._handled = False
            return None
        if self._handled or not has_running_sessions:
            return None

        checked_at = now or datetime.now(timezone.utc)
        return IdleTrigger(
            idle_seconds=idle_seconds,
            cutoff_at=checked_at - timedelta(seconds=idle_seconds - threshold_seconds),
        )

    def mark_handled(self) -> None:
        self._handled = True

