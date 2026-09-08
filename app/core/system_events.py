"""Vocabulary for native Windows lifecycle events.

Detection itself lives in `tray/system_events.py`, the only LuxTime component
that runs continuously inside the user's interactive session (required for
both session-lock notifications and idle-input detection). The tray acts
directly against the existing sessions API (stop-all with a reason, then
start) rather than submitting through a dedicated endpoint - this module just
names the vocabulary those stop reasons and any future consumer share.
"""

from typing import Literal

SystemEventType = Literal[
    "session_locked",
    "session_unlocked",
    "system_suspend",
    "system_resume",
    "idle_detected",
]
