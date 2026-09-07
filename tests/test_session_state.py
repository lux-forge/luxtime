import pytest

from app.core.errors import ConflictError
from app.core.session_state import next_status


@pytest.mark.parametrize(
    ("current", "action", "expected"),
    [
        ("running", "pause", "paused"),
        ("running", "stop", "stopped"),
        ("paused", "resume", "running"),
        ("paused", "stop", "stopped"),
    ],
)
def test_valid_session_transitions(current, action, expected):
    assert next_status(current, action) == expected


@pytest.mark.parametrize(
    ("current", "action"),
    [("running", "resume"), ("paused", "pause"), ("stopped", "resume")],
)
def test_invalid_session_transitions_raise_conflict(current, action):
    with pytest.raises(ConflictError):
        next_status(current, action)
