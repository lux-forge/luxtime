"""Insights query and period selection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.core.insights import IntervalRecord, calculate_insights
from app.data.database import Database
from app.models.api import InsightPeriod


def _period_start(period: InsightPeriod, now: datetime) -> datetime | None:
    if period == "all":
        return None
    if period == "week":
        return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=now.weekday()
        )
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "quarter":
        month = ((now.month - 1) // 3) * 3 + 1
        return now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


class InsightsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def calculate(self, period: InsightPeriod) -> dict:
        now = datetime.now(timezone.utc)
        start = _period_start(period, now)
        filters = ["seg.started_at < %s", "COALESCE(seg.ended_at, %s) > seg.started_at"]
        values: list[object] = [now, now]
        if start is not None:
            filters.append("COALESCE(seg.ended_at, %s) > %s")
            values.extend([now, start])
        rows = self.database.fetch_all(
            f"""
            SELECT s.id AS session_id,
                   GREATEST(seg.started_at, %s) AS interval_start,
                   LEAST(COALESCE(seg.ended_at, %s), %s) AS interval_end,
                   p.id AS project_id, p.name AS project, p.color AS project_color,
                   s.work_type, s.hourly_rate
            FROM luxtime.work_session_segments seg
            JOIN luxtime.work_sessions s ON s.id = seg.session_id
            JOIN luxtime.projects p ON p.id = s.project_id
            WHERE {' AND '.join(filters)}
            ORDER BY interval_start
            """,
            tuple([start or datetime.min.replace(tzinfo=timezone.utc), now, now, *values]),
        )
        records = [
            IntervalRecord(
                session_id=UUID(str(row["session_id"])),
                start=row["interval_start"],
                end=row["interval_end"],
                project_id=UUID(str(row["project_id"])),
                project=row["project"],
                project_color=row["project_color"],
                work_type=row["work_type"],
                hourly_rate=Decimal(row["hourly_rate"]),
            )
            for row in rows
            if row["interval_end"] > row["interval_start"]
        ]
        return {
            "period": period,
            "range_start": start,
            "range_end": now,
            **calculate_insights(records),
        }
