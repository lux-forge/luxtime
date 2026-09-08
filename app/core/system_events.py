"""Vocabulary for native Windows event delivery.

The interactive tray handles idle input plus suspend and resume detection.
Lock and unlock delivery remain future work.
"""

from typing import Literal

SystemEventType = Literal[
    "session_locked",
    "session_unlocked",
    "system_suspend",
    "system_resume",
    "idle_detected",
]
