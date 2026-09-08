import pytest
from pydantic import ValidationError

from app.models.api import SessionPause


@pytest.mark.parametrize("mode", ["manual", "away", "sleep", "lock"])
def test_session_pause_accepts_supported_modes(mode):
    assert SessionPause(mode=mode).mode == mode


def test_session_pause_rejects_unknown_mode():
    with pytest.raises(ValidationError):
        SessionPause(mode="offline")
