"""Signal a running LuxTime tray process without touching application state."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import os

from tray.runtime import EXIT_EVENT_NAME

EVENT_MODIFY_STATE = 0x0002


def request_exit() -> bool:
    if os.name != "nt":
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenEventW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.OpenEventW.restype = wintypes.HANDLE
    kernel32.SetEvent.argtypes = (wintypes.HANDLE,)
    kernel32.SetEvent.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, EXIT_EVENT_NAME)
    if not event:
        return False
    try:
        return bool(kernel32.SetEvent(event))
    finally:
        kernel32.CloseHandle(event)


def main() -> int:
    parser = argparse.ArgumentParser(description="Control the LuxTime tray process")
    parser.add_argument("action", choices=("exit",))
    parser.parse_args()
    if request_exit():
        print("LuxTime tray exit requested")
        return 0
    print("LuxTime tray is not running")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
