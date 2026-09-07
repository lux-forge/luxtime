"""Valid work-session state transitions."""

from __future__ import annotations

from typing import Literal

from app.core.errors import ConflictError

SessionStatus = Literal["running", "paused", "stopped"]
SessionAction = Literal["pause", "resume", "stop"]

_TRANSITIONS: dict[tuple[SessionStatus, SessionAction], SessionStatus] = {
    ("running", "pause"): "paused",
    ("running", "stop"): "stopped",
    ("paused", "resume"): "running",
    ("paused", "stop"): "stopped",
}


def next_status(current: SessionStatus, action: SessionAction) -> SessionStatus:
    try:
        return _TRANSITIONS[(current, action)]
    except KeyError as error:
        raise ConflictError(f"Cannot {action} a {current} session") from error
