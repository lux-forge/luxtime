from tray.power import (
    ERROR_SUCCESS,
    PBT_APMRESUMEAUTOMATIC,
    PBT_APMSUSPEND,
    WindowsPowerMonitor,
)


def test_power_monitor_maps_native_suspend_and_resume_events():
    events = []
    monitor = WindowsPowerMonitor(events.append)

    assert monitor._dispatch(None, PBT_APMSUSPEND, None) == ERROR_SUCCESS
    assert monitor._dispatch(None, PBT_APMRESUMEAUTOMATIC, None) == ERROR_SUCCESS

    assert events == ["suspend", "resume"]
