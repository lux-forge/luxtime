"""Authoritative work-session and segment operations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundry.logger import logger

from app.core.errors import ConflictError, NotFoundError
from app.core.session_state import SessionStatus, next_status
from app.data.database import Database
from app.models.api import PauseMode, SegmentPatch, SessionPatch, SessionStart

log = logger.bind(component="luxtime.sessions")

_SESSION_SELECT = """
SELECT s.id, s.project_id, p.name AS project, p.color AS project_color,
       s.work_type, s.description, s.hourly_rate, s.status, s.pause_mode,
       s.started_at, s.stopped_at, s.stop_reason,
       COALESCE((
           SELECT ROUND(SUM(EXTRACT(EPOCH FROM (COALESCE(seg.ended_at, CURRENT_TIMESTAMP) - seg.started_at))))::BIGINT
           FROM luxtime.work_session_segments seg
           WHERE seg.session_id = s.id
       ), 0) AS total_seconds,
       EXISTS (
           SELECT 1
           FROM luxtime.work_session_segments own_seg
           JOIN luxtime.work_session_segments other_seg
             ON other_seg.session_id <> own_seg.session_id
            AND tstzrange(own_seg.started_at, COALESCE(own_seg.ended_at, CURRENT_TIMESTAMP), '[)')
                && tstzrange(other_seg.started_at, COALESCE(other_seg.ended_at, CURRENT_TIMESTAMP), '[)')
           WHERE own_seg.session_id = s.id
       ) AS concurrent,
       s.created_at, s.updated_at
FROM luxtime.work_sessions s
JOIN luxtime.projects p ON p.id = s.project_id
"""


class SessionService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list(
        self,
        *,
        status: SessionStatus | None = None,
        project_id: UUID | None = None,
        limit: int = 500,
    ) -> list[dict]:
        filters: list[str] = []
        values: list[object] = []
        if status is not None:
            filters.append("s.status = %s")
            values.append(status)
        if project_id is not None:
            filters.append("s.project_id = %s")
            values.append(project_id)
        where = f" WHERE {' AND '.join(filters)}" if filters else ""
        values.append(limit)
        return self.database.fetch_all(
            _SESSION_SELECT + where + " ORDER BY s.started_at DESC LIMIT %s",
            tuple(values),
        )

    def active(self) -> list[dict]:
        return self.database.fetch_all(
            _SESSION_SELECT + " WHERE s.status IN ('running', 'paused') ORDER BY s.started_at"
        )

    def get(self, session_id: UUID, *, include_segments: bool = False) -> dict:
        session = self.database.fetch_one(_SESSION_SELECT + " WHERE s.id = %s", (session_id,))
        if session is None:
            raise NotFoundError("Session not found")
        if include_segments:
            session["segments"] = self.database.fetch_all(
                """
                SELECT id, session_id, started_at, ended_at
                FROM luxtime.work_session_segments
                WHERE session_id = %s
                ORDER BY started_at
                """,
                (session_id,),
            )
        return session

    def start(self, payload: SessionStart) -> dict:
        started_at = payload.started_at or datetime.now(timezone.utc)
        with self.database.transaction():
            project = self.database.fetch_one(
                "SELECT id FROM luxtime.projects WHERE id = %s AND active = TRUE",
                (payload.project_id,),
            )
            if project is None:
                raise NotFoundError("Active project not found")
            hourly_rate = payload.hourly_rate
            if hourly_rate is None:
                settings = self.database.fetch_one(
                    "SELECT default_rate FROM luxtime.settings WHERE singleton = TRUE"
                )
                if settings is None:
                    raise RuntimeError("LuxTime settings defaults have not been applied")
                hourly_rate = settings["default_rate"]
            session = self.database.fetch_one(
                """
                INSERT INTO luxtime.work_sessions
                    (project_id, work_type, description, hourly_rate, status, started_at)
                VALUES (%s, %s, %s, %s, 'running', %s)
                RETURNING id
                """,
                (
                    payload.project_id,
                    payload.work_type,
                    payload.description.strip(),
                    hourly_rate,
                    started_at,
                ),
            )
            assert session is not None
            self.database.execute(
                "INSERT INTO luxtime.work_session_segments (session_id, started_at) VALUES (%s, %s)",
                (session["id"], started_at),
                commit=False,
            )
        log.info("Session started", session_id=str(session["id"]), project_id=str(payload.project_id))
        return self.get(session["id"], include_segments=True)

    def _locked_status(self, session_id: UUID) -> SessionStatus:
        row = self.database.fetch_one(
            "SELECT status FROM luxtime.work_sessions WHERE id = %s FOR UPDATE",
            (session_id,),
        )
        if row is None:
            raise NotFoundError("Session not found")
        return row["status"]

    def pause(
        self,
        session_id: UUID,
        at: datetime | None = None,
        mode: PauseMode = "manual",
    ) -> dict:
        paused_at = at or datetime.now(timezone.utc)
        with self.database.transaction():
            current = self._locked_status(session_id)
            next_status(current, "pause")
            segment = self.database.fetch_one(
                """
                UPDATE luxtime.work_session_segments
                SET ended_at = %s
                WHERE session_id = %s AND ended_at IS NULL AND started_at < %s
                RETURNING id
                """,
                (paused_at, session_id, paused_at),
            )
            if segment is None:
                raise ConflictError("Session has no open segment before the pause time")
            self.database.execute(
                "UPDATE luxtime.work_sessions SET status = 'paused', pause_mode = %s WHERE id = %s",
                (mode, session_id),
                commit=False,
            )
        log.info("Session paused", session_id=str(session_id), pause_mode=mode)
        return self.get(session_id, include_segments=True)

    def resume(self, session_id: UUID, at: datetime | None = None) -> dict:
        resumed_at = at or datetime.now(timezone.utc)
        with self.database.transaction():
            current = self._locked_status(session_id)
            next_status(current, "resume")
            latest = self.database.fetch_one(
                "SELECT MAX(ended_at) AS ended_at FROM luxtime.work_session_segments WHERE session_id = %s",
                (session_id,),
            )
            if latest and latest["ended_at"] and resumed_at < latest["ended_at"]:
                raise ConflictError("Resume time cannot precede the previous segment")
            self.database.execute(
                "INSERT INTO luxtime.work_session_segments (session_id, started_at) VALUES (%s, %s)",
                (session_id, resumed_at),
                commit=False,
            )
            self.database.execute(
                "UPDATE luxtime.work_sessions SET status = 'running', pause_mode = NULL WHERE id = %s",
                (session_id,),
                commit=False,
            )
        log.info("Session resumed", session_id=str(session_id))
        return self.get(session_id, include_segments=True)

    def stop(
        self,
        session_id: UUID,
        *,
        at: datetime | None = None,
        reason: str = "manual",
    ) -> dict:
        stopped_at = at or datetime.now(timezone.utc)
        with self.database.transaction():
            current = self._locked_status(session_id)
            next_status(current, "stop")
            if current == "running":
                segment = self.database.fetch_one(
                    """
                    UPDATE luxtime.work_session_segments
                    SET ended_at = %s
                    WHERE session_id = %s AND ended_at IS NULL AND started_at < %s
                    RETURNING id
                    """,
                    (stopped_at, session_id, stopped_at),
                )
                if segment is None:
                    raise ConflictError("Session has no open segment before the stop time")
            latest = self.database.fetch_one(
                "SELECT MAX(ended_at) AS ended_at FROM luxtime.work_session_segments WHERE session_id = %s",
                (session_id,),
            )
            if latest and latest["ended_at"] and stopped_at < latest["ended_at"]:
                raise ConflictError("Stop time cannot precede the last tracked segment")
            self.database.execute(
                """
                UPDATE luxtime.work_sessions
                SET status = 'stopped', stopped_at = %s, stop_reason = %s, pause_mode = NULL
                WHERE id = %s
                """,
                (stopped_at, reason, session_id),
                commit=False,
            )
        log.info("Session stopped", session_id=str(session_id), reason=reason)
        return self.get(session_id, include_segments=True)

    def update(self, session_id: UUID, payload: SessionPatch) -> dict:
        requested = payload.model_dump(exclude_unset=True)
        columns = {
            "project_id": "project_id",
            "work_type": "work_type",
            "description": "description",
            "hourly_rate": "hourly_rate",
        }
        assignments = [f"{columns[field]} = %s" for field in requested]
        values = list(requested.values()) + [session_id]
        with self.database.transaction():
            row = self.database.fetch_one(
                f"UPDATE luxtime.work_sessions SET {', '.join(assignments)} WHERE id = %s RETURNING id",
                tuple(values),
            )
            if row is None:
                raise NotFoundError("Session not found")
        log.info("Session updated", session_id=str(session_id), fields=tuple(requested))
        return self.get(session_id, include_segments=True)

    def correct_segment(self, session_id: UUID, segment_id: UUID, payload: SegmentPatch) -> dict:
        requested = payload.model_dump(exclude_unset=True)
        assignments = [f"{field} = %s" for field in requested]
        values = list(requested.values()) + [segment_id, session_id]
        with self.database.transaction():
            row = self.database.fetch_one(
                f"""
                UPDATE luxtime.work_session_segments
                SET {', '.join(assignments)}
                WHERE id = %s AND session_id = %s
                RETURNING id
                """,
                tuple(values),
            )
            if row is None:
                raise NotFoundError("Session segment not found")
            self.database.execute(
                """
                UPDATE luxtime.work_sessions s
                SET started_at = bounds.first_start,
                    stopped_at = CASE WHEN s.status = 'stopped' THEN bounds.last_end ELSE s.stopped_at END
                FROM (
                    SELECT MIN(started_at) AS first_start, MAX(ended_at) AS last_end
                    FROM luxtime.work_session_segments
                    WHERE session_id = %s
                ) bounds
                WHERE s.id = %s
                """,
                (session_id, session_id),
                commit=False,
            )
        log.info(
            "Session segment corrected",
            session_id=str(session_id),
            segment_id=str(segment_id),
        )
        return self.get(session_id, include_segments=True)

    def delete(self, session_id: UUID) -> None:
        with self.database.transaction():
            row = self.database.fetch_one(
                "DELETE FROM luxtime.work_sessions WHERE id = %s RETURNING id",
                (session_id,),
            )
            if row is None:
                raise NotFoundError("Session not found")
        log.info("Session deleted", session_id=str(session_id))

    def pause_all(
        self,
        at: datetime | None = None,
        mode: PauseMode = "manual",
    ) -> list[dict]:
        action_at = at or datetime.now(timezone.utc)
        sessions = self.list(status="running")
        return [self.pause(session["id"], action_at, mode) for session in sessions]

    def resume_all(self, at: datetime | None = None, session_ids: list[UUID] | None = None) -> list[dict]:
        action_at = at or datetime.now(timezone.utc)
        sessions = self.list(status="paused")
        allowed = set(session_ids) if session_ids is not None else None
        return [
            self.resume(session["id"], action_at)
            for session in sessions
            if allowed is None or session["id"] in allowed
        ]

    def stop_all(self, at: datetime | None = None, reason: str = "manual") -> list[dict]:
        action_at = at or datetime.now(timezone.utc)
        return [
            self.stop(session["id"], at=action_at, reason=reason)
            for session in self.active()
        ]
