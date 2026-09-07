from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.core.insights import IntervalRecord, calculate_insights


def interval(session_id, project_id, start, end, project="Project", rate="50"):
    return IntervalRecord(
        session_id=session_id,
        start=start,
        end=end,
        project_id=project_id,
        project=project,
        project_color="#22D3EE",
        work_type="Development",
        hourly_rate=Decimal(rate),
    )


def test_concurrent_time_distinguishes_elapsed_and_attributed_work():
    day = datetime(2026, 1, 5, 10, tzinfo=timezone.utc)
    session_a, session_b = uuid4(), uuid4()
    project_a, project_b = uuid4(), uuid4()

    result = calculate_insights(
        [
            interval(session_a, project_a, day, day + timedelta(hours=2), "A"),
            interval(
                session_b,
                project_b,
                day + timedelta(hours=1),
                day + timedelta(hours=2),
                "B",
            ),
        ]
    )

    assert result["elapsed_seconds"] == 2 * 3600
    assert result["project_attributed_seconds"] == 3 * 3600
    assert result["concurrent_attribution_seconds"] == 3600
    assert result["session_count"] == 2


def test_session_duration_is_sum_of_segments_and_not_pause_gap():
    day = datetime(2026, 1, 5, 9, tzinfo=timezone.utc)
    session_id, project_id = uuid4(), uuid4()

    result = calculate_insights(
        [
            interval(session_id, project_id, day, day + timedelta(hours=1, minutes=17)),
            interval(
                session_id,
                project_id,
                day + timedelta(hours=1, minutes=31),
                day + timedelta(hours=2, minutes=42),
            ),
        ]
    )

    assert result["elapsed_seconds"] == (77 + 71) * 60
    assert result["project_attributed_seconds"] == (77 + 71) * 60
    assert result["session_count"] == 1
    assert result["days"][0]["date"] == "2026-01-05"
