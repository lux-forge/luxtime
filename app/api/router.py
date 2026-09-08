"""Local REST API. Business state remains in application services and PostgreSQL."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_database
from app.data.database import Database
from app.models.api import (
    BulkActionResponse,
    HealthResponse,
    InsightPeriod,
    InsightsResponse,
    ProjectCreate,
    ProjectPatch,
    ProjectResponse,
    ResumeSelected,
    SegmentPatch,
    SessionAction,
    SessionPatch,
    SessionPause,
    SessionResponse,
    SessionStart,
    SessionStatus,
    SessionStop,
    SettingsPatch,
    SettingsResponse,
    StatusResponse,
)
from app.services.insights import InsightsService
from app.services.projects import ProjectService
from app.services.sessions import SessionService
from app.services.settings import SettingsService

router = APIRouter(prefix="/api")
DatabaseDependency = Annotated[Database, Depends(get_database)]


@router.get("/health", response_model=HealthResponse)
def health(database: DatabaseDependency) -> HealthResponse | JSONResponse:
    if database.ping():
        return HealthResponse(status="healthy", database="connected")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unhealthy", "database": "unavailable"},
    )


@router.get("/status", response_model=StatusResponse)
def application_status(database: DatabaseDependency) -> StatusResponse:
    database_connected = database.ping()
    if not database_connected:
        return StatusResponse(
            app_status="degraded",
            database_connected=False,
            active_sessions=0,
            running_sessions=0,
            paused_sessions=0,
        )
    counts = database.fetch_one(
        """
        SELECT COUNT(*) FILTER (WHERE status = 'running')::INT AS running,
               COUNT(*) FILTER (WHERE status = 'paused')::INT AS paused
        FROM luxtime.work_sessions
        WHERE status IN ('running', 'paused')
        """
    ) or {"running": 0, "paused": 0}
    running = counts["running"]
    paused = counts["paused"]
    app_status = "tracking" if running else "paused" if paused else "ready"
    return StatusResponse(
        app_status=app_status,
        database_connected=True,
        active_sessions=running + paused,
        running_sessions=running,
        paused_sessions=paused,
    )


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(database: DatabaseDependency) -> list[dict]:
    return ProjectService(database).list()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, database: DatabaseDependency) -> dict:
    return ProjectService(database).create(payload)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, payload: ProjectPatch, database: DatabaseDependency) -> dict:
    return ProjectService(database).update(project_id, payload)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    database: DatabaseDependency,
    session_status: SessionStatus | None = Query(default=None, alias="status"),
    project_id: UUID | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
) -> list[dict]:
    return SessionService(database).list(
        status=session_status, project_id=project_id, limit=limit
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, database: DatabaseDependency) -> dict:
    return SessionService(database).get(session_id, include_segments=True)


@router.post("/sessions/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: SessionStart, database: DatabaseDependency) -> dict:
    return SessionService(database).start(payload)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: UUID, payload: SessionPatch, database: DatabaseDependency) -> dict:
    return SessionService(database).update(session_id, payload)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, database: DatabaseDependency) -> Response:
    SessionService(database).delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/sessions/{session_id}/segments/{segment_id}", response_model=SessionResponse
)
def correct_segment(
    session_id: UUID,
    segment_id: UUID,
    payload: SegmentPatch,
    database: DatabaseDependency,
) -> dict:
    return SessionService(database).correct_segment(session_id, segment_id, payload)


@router.post("/sessions/{session_id}/pause", response_model=SessionResponse)
def pause_session(session_id: UUID, payload: SessionPause, database: DatabaseDependency) -> dict:
    return SessionService(database).pause(session_id, payload.at, payload.mode)


@router.post("/sessions/{session_id}/resume", response_model=SessionResponse)
def resume_session(session_id: UUID, payload: SessionAction, database: DatabaseDependency) -> dict:
    return SessionService(database).resume(session_id, payload.at)


@router.post("/sessions/{session_id}/stop", response_model=SessionResponse)
def stop_session(session_id: UUID, payload: SessionStop, database: DatabaseDependency) -> dict:
    return SessionService(database).stop(session_id, at=payload.at, reason=payload.reason)


@router.get("/active", response_model=list[SessionResponse])
def active_sessions(database: DatabaseDependency) -> list[dict]:
    return SessionService(database).active()


@router.post("/active/pause-all", response_model=BulkActionResponse)
def pause_all(payload: SessionPause, database: DatabaseDependency) -> dict:
    return {"sessions": SessionService(database).pause_all(payload.at, payload.mode)}


@router.post("/active/resume-all", response_model=BulkActionResponse)
def resume_all(payload: SessionAction, database: DatabaseDependency) -> dict:
    return {"sessions": SessionService(database).resume_all(payload.at)}


@router.post("/active/resume-selected", response_model=BulkActionResponse)
def resume_selected(payload: ResumeSelected, database: DatabaseDependency) -> dict:
    return {
        "sessions": SessionService(database).resume_all(payload.at, payload.session_ids)
    }


@router.post("/active/stop-all", response_model=BulkActionResponse)
def stop_all(payload: SessionStop, database: DatabaseDependency) -> dict:
    return {
        "sessions": SessionService(database).stop_all(payload.at, payload.reason)
    }


@router.get("/insights", response_model=InsightsResponse)
def insights(
    database: DatabaseDependency,
    period: InsightPeriod = Query(default="week"),
) -> dict:
    return InsightsService(database).calculate(period)


@router.get("/settings", response_model=SettingsResponse)
def get_settings(database: DatabaseDependency) -> dict:
    return SettingsService(database).get()


@router.patch("/settings", response_model=SettingsResponse)
def update_settings(payload: SettingsPatch, database: DatabaseDependency) -> dict:
    return SettingsService(database).update(payload)
