from datetime import datetime, timedelta, timezone

from tray.api_client import LuxTimeApi
from tray.idle import IdleDetector


def test_idle_detector_fires_once_at_threshold_and_uses_threshold_cutoff():
    detector = IdleDetector()
    now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)

    trigger = detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=2 * 60 * 60,
        now=now,
    )

    assert trigger is not None
    assert trigger.cutoff_at == now - timedelta(minutes=100)
    detector.mark_handled()
    assert detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=2 * 60 * 60 + 5,
        now=now + timedelta(seconds=5),
    ) is None


def test_idle_detector_resets_after_new_input():
    detector = IdleDetector()
    now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    first = detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=1200,
        now=now,
    )
    assert first is not None
    detector.mark_handled()

    assert detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=1,
        now=now + timedelta(hours=1),
    ) is None
    assert detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=1200,
        now=now + timedelta(hours=1, minutes=20),
    ) is not None


def test_idle_detector_requires_enabled_policy_and_running_session():
    detector = IdleDetector()

    assert detector.check(
        enabled=False,
        threshold_minutes=20,
        has_running_sessions=True,
        idle_seconds=3600,
    ) is None
    assert detector.check(
        enabled=True,
        threshold_minutes=20,
        has_running_sessions=False,
        idle_seconds=3600,
    ) is None


def test_tray_api_sends_away_pause_timestamp_and_mode(monkeypatch):
    api = LuxTimeApi()
    captured = {}

    def fake_request(path, *, method="GET", payload=None):
        captured.update(path=path, method=method, payload=payload)
        return {}

    monkeypatch.setattr(api, "request", fake_request)
    api.action(
        "running-id",
        "pause",
        at="2026-09-08T12:20:00+00:00",
        mode="away",
    )

    assert captured == {
        "path": "/api/sessions/running-id/pause",
        "method": "POST",
        "payload": {
            "at": "2026-09-08T12:20:00+00:00",
            "mode": "away",
        },
    }
