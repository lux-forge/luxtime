"""Vocabulary for native Windows event delivery.

The interactive tray handles idle input, lock/unlock, and suspend/resume detection.
"""

from typing import Literal

SystemEventType = Literal[
    "session_locked",
    "session_unlocked",
    "system_suspend",
    "system_resume",
    "idle_detected",
]
