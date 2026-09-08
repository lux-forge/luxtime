from tray.dialogs import _session_summary


def test_locked_session_summary_lists_tasks_and_limits_long_sets():
    sessions = [
        {
            "project": f"Project {index}",
            "description": "Focused work" if index == 1 else "",
        }
        for index in range(1, 11)
    ]

    summary = _session_summary(sessions)

    assert "• Project 1 — Focused work" in summary
    assert "• Project 8" in summary
    assert "• and 2 more" in summary
    assert "Project 9" not in summary
