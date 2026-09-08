from tray.session_events import (
    WTS_SESSION_LOCK,
    WTS_SESSION_UNLOCK,
    WindowsSessionMonitor,
)


def test_session_monitor_maps_native_lock_and_unlock_events():
    events = []
    monitor = WindowsSessionMonitor(events.append)

    monitor._dispatch(WTS_SESSION_LOCK)
    monitor._dispatch(WTS_SESSION_UNLOCK)

    assert events == ["lock", "unlock"]
