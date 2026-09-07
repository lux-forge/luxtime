"""Boundary for later native Windows event delivery.

The service/tray may eventually submit lock, unlock, suspend, resume, and idle
events here. Detection is intentionally not implemented in this foundation.
"""

from typing import Literal

SystemEventType = Literal[
    "session_locked",
    "session_unlocked",
    "system_suspend",
    "system_resume",
    "idle_detected",
]
