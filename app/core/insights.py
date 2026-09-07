"""Deterministic elapsed and attributed-time calculations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Iterable
from uuid import UUID


@dataclass(frozen=True)
class IntervalRecord:
    session_id: UUID
    start: datetime
    end: datetime
    project_id: UUID
    project: str
    project_color: str
    work_type: str
    hourly_rate: Decimal

    @property
    def seconds(self) -> int:
        return max(0, round((self.end - self.start).total_seconds()))


def _merge_elapsed(intervals: Iterable[tuple[datetime, datetime]]) -> int:
    ordered = sorted(intervals, key=lambda item: (item[0], item[1]))
    if not ordered:
        return 0
    elapsed = 0.0
    current_start, current_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
            continue
        elapsed += (current_end - current_start).total_seconds()
        current_start, current_end = start, end
    elapsed += (current_end - current_start).total_seconds()
    return max(0, round(elapsed))


def _split_days(record: IntervalRecord) -> Iterable[tuple[str, int]]:
    cursor = record.start
    while cursor < record.end:
        next_midnight = datetime.combine(
            cursor.date() + timedelta(days=1), time.min, tzinfo=timezone.utc
        )
        boundary = min(record.end, next_midnight)
        yield cursor.date().isoformat(), round((boundary - cursor).total_seconds())
        cursor = boundary


def calculate_insights(records: Iterable[IntervalRecord]) -> dict:
    intervals = [record for record in records if record.end > record.start]
    attributed = sum(record.seconds for record in intervals)
    elapsed = _merge_elapsed((record.start, record.end) for record in intervals)

    project_seconds: dict[UUID, int] = defaultdict(int)
    project_values: dict[UUID, Decimal] = defaultdict(Decimal)
    project_meta: dict[UUID, tuple[str, str]] = {}
    type_seconds: dict[str, int] = defaultdict(int)
    session_seconds: dict[UUID, int] = defaultdict(int)
    day_projects: dict[str, dict[UUID, int]] = defaultdict(lambda: defaultdict(int))

    for record in intervals:
        project_seconds[record.project_id] += record.seconds
        project_values[record.project_id] += (
            Decimal(record.seconds) * record.hourly_rate / Decimal(3600)
        )
        project_meta[record.project_id] = (record.project, record.project_color)
        type_seconds[record.work_type] += record.seconds
        session_seconds[record.session_id] += record.seconds
        for day, seconds in _split_days(record):
            day_projects[day][record.project_id] += seconds

    projects = [
        {
            "project_id": project_id,
            "project": project_meta[project_id][0],
            "color": project_meta[project_id][1],
            "seconds": seconds,
            "value": round(float(project_values[project_id]), 2),
        }
        for project_id, seconds in sorted(
            project_seconds.items(), key=lambda item: item[1], reverse=True
        )
    ]
    work_types = [
        {"name": name, "seconds": seconds}
        for name, seconds in sorted(type_seconds.items(), key=lambda item: item[1], reverse=True)
    ]

    days = []
    for day, values in day_projects.items():
        day_items = [
            {
                "project_id": project_id,
                "project": project_meta[project_id][0],
                "color": project_meta[project_id][1],
                "seconds": seconds,
            }
            for project_id, seconds in values.items()
        ]
        days.append({"date": day, "total_seconds": sum(values.values()), "projects": day_items})

    length_specs = (
        ("< 30m", 0, 1800),
        ("30m–1h", 1800, 3600),
        ("1h–2h", 3600, 7200),
        ("2h–4h", 7200, 14400),
        ("4h+", 14400, None),
    )
    length_buckets = [
        {
            "label": label,
            "count": sum(
                1
                for seconds in session_seconds.values()
                if seconds >= minimum and (maximum is None or seconds < maximum)
            ),
        }
        for label, minimum, maximum in length_specs
    ]

    sessions = len(session_seconds)
    value = sum(project_values.values(), Decimal())
    return {
        "elapsed_seconds": elapsed,
        "project_attributed_seconds": attributed,
        "concurrent_attribution_seconds": max(0, attributed - elapsed),
        "notional_labour_value": round(float(value), 2),
        "session_count": sessions,
        "average_session_seconds": round(attributed / sessions) if sessions else 0,
        "projects": projects,
        "work_types": work_types,
        "days": days,
        "session_lengths": length_buckets,
    }
