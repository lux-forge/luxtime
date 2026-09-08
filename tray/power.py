"""Native Windows suspend/resume notifications for the interactive tray."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Callable, Literal

PowerEvent = Literal["suspend", "resume"]

DEVICE_NOTIFY_CALLBACK = 2
ERROR_SUCCESS = 0
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMECRITICAL = 0x0006
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012

_CALLBACK_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
_POWER_CALLBACK = _CALLBACK_FACTORY(
    wintypes.ULONG,
    wintypes.LPVOID,
    wintypes.ULONG,
    wintypes.LPVOID,
)


class _DEVICE_NOTIFY_SUBSCRIBE_PARAMETERS(ctypes.Structure):
    _fields_ = (("Callback", _POWER_CALLBACK), ("Context", wintypes.LPVOID))


class WindowsPowerMonitor:
    """Register a lightweight callback for Windows sleep and wake events."""

    def __init__(self, callback: Callable[[PowerEvent], None]) -> None:
        self.callback = callback
        self._native_callback = _POWER_CALLBACK(self._dispatch)
        self._parameters = _DEVICE_NOTIFY_SUBSCRIBE_PARAMETERS(
            Callback=self._native_callback,
            Context=None,
        )
        self._library = None
        self._registration = wintypes.HANDLE()

    def _dispatch(self, _context, event_type: int, _setting) -> int:
        try:
            if event_type == PBT_APMSUSPEND:
                self.callback("suspend")
            elif event_type in {
                PBT_APMRESUMECRITICAL,
                PBT_APMRESUMESUSPEND,
                PBT_APMRESUMEAUTOMATIC,
            }:
                self.callback("resume")
        except Exception:
            return 1
        return ERROR_SUCCESS

    def start(self) -> None:
        if os.name != "nt":
            raise RuntimeError("Windows power monitoring requires Windows")
        if self._registration:
            return

        library = ctypes.WinDLL("PowrProf", use_last_error=True)
        library.PowerRegisterSuspendResumeNotification.argtypes = (
            wintypes.DWORD,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.HANDLE),
        )
        library.PowerRegisterSuspendResumeNotification.restype = wintypes.DWORD
        library.PowerUnregisterSuspendResumeNotification.argtypes = (wintypes.HANDLE,)
        library.PowerUnregisterSuspendResumeNotification.restype = wintypes.DWORD
        result = library.PowerRegisterSuspendResumeNotification(
            DEVICE_NOTIFY_CALLBACK,
            ctypes.byref(self._parameters),
            ctypes.byref(self._registration),
        )
        if result != ERROR_SUCCESS:
            raise ctypes.WinError(result)
        self._library = library

    def close(self) -> None:
        if self._library is None or not self._registration:
            return
        self._library.PowerUnregisterSuspendResumeNotification(self._registration)
        self._registration = wintypes.HANDLE()
        self._library = None

