"""Validated API request and response models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.session_state import SessionStatus

WorkType = Literal["Development", "Design", "Research", "Operations", "Admin", "Business"]
StopReason = Literal["manual", "lock", "sleep", "idle", "shutdown", "correction", "system"]
StartupBehaviour = Literal["tray", "compact", "window"]
InsightPeriod = Literal["week", "month", "quarter", "year", "all"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HealthResponse(StrictModel):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "unavailable"]


class StatusResponse(StrictModel):
    app_status: Literal["ready", "tracking", "paused", "degraded"]
    database_connected: bool
    active_sessions: int
    running_sessions: int
    paused_sessions: int


class ProjectCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=16)
    color: str = Field(default="#22D3EE", pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectPatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=16)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    active: bool | None = None

    @model_validator(mode="after")
    def has_update(self) -> "ProjectPatch":
        if not self.model_fields_set:
            raise ValueError("At least one project field is required")
        return self


class ProjectResponse(StrictModel):
    id: UUID
    name: str
    code: str | None
    color: str
    total_seconds: int
    active: bool
    created_at: datetime
    updated_at: datetime


class SessionStart(StrictModel):
    project_id: UUID
    work_type: WorkType = "Development"
    description: str = Field(default="", max_length=2000)
    hourly_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    started_at: datetime | None = None


class SessionPatch(StrictModel):
    project_id: UUID | None = None
    work_type: WorkType | None = None
    description: str | None = Field(default=None, max_length=2000)
    hourly_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def has_update(self) -> "SessionPatch":
        if not self.model_fields_set:
            raise ValueError("At least one session field is required")
        return self


class SessionAction(StrictModel):
    at: datetime | None = None


class SessionStop(SessionAction):
    reason: StopReason = "manual"


class ResumeSelected(StrictModel):
    session_ids: list[UUID] = Field(min_length=1)
    at: datetime | None = None


class SegmentPatch(StrictModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @model_validator(mode="after")
    def has_update(self) -> "SegmentPatch":
        if not self.model_fields_set:
            raise ValueError("At least one segment field is required")
        if "started_at" in self.model_fields_set and self.started_at is None:
            raise ValueError("started_at cannot be null")
        if "ended_at" in self.model_fields_set and self.ended_at is None:
            raise ValueError("ended_at cannot be null when correcting a segment")
        if self.started_at and self.ended_at and self.ended_at <= self.started_at:
            raise ValueError("ended_at must be later than started_at")
        return self


class SegmentResponse(StrictModel):
    id: UUID
    session_id: UUID
    started_at: datetime
    ended_at: datetime | None


class SessionResponse(StrictModel):
    id: UUID
    project_id: UUID
    project: str
    project_color: str
    work_type: WorkType
    description: str
    hourly_rate: Decimal
    status: SessionStatus
    started_at: datetime
    stopped_at: datetime | None
    stop_reason: StopReason | None
    total_seconds: int
    concurrent: bool
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentResponse] | None = None


class BulkActionResponse(StrictModel):
    sessions: list[SessionResponse]


class SettingsResponse(StrictModel):
    default_rate: Decimal
    stop_on_lock: bool
    stop_on_sleep: bool
    resume_prompt: bool
    idle_detection: bool
    idle_threshold: int
    engine_starts_with_windows: bool
    startup_behaviour: StartupBehaviour
    updated_at: datetime


class SettingsPatch(StrictModel):
    default_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    stop_on_lock: bool | None = None
    stop_on_sleep: bool | None = None
    resume_prompt: bool | None = None
    idle_detection: bool | None = None
    idle_threshold: int | None = Field(default=None, ge=1, le=1440)
    engine_starts_with_windows: bool | None = None
    startup_behaviour: StartupBehaviour | None = None

    @model_validator(mode="after")
    def has_update(self) -> "SettingsPatch":
        if not self.model_fields_set:
            raise ValueError("At least one setting is required")
        return self


class InsightProject(StrictModel):
    project_id: UUID
    project: str
    color: str
    seconds: int
    value: float


class InsightWorkType(StrictModel):
    name: str
    seconds: int


class InsightDayProject(StrictModel):
    project_id: UUID
    project: str
    color: str
    seconds: int


class InsightDay(StrictModel):
    date: str
    total_seconds: int
    projects: list[InsightDayProject]


class SessionLengthBucket(StrictModel):
    label: str
    count: int


class InsightsResponse(StrictModel):
    period: InsightPeriod
    range_start: datetime | None
    range_end: datetime
    elapsed_seconds: int
    project_attributed_seconds: int
    concurrent_attribution_seconds: int
    notional_labour_value: float
    session_count: int
    average_session_seconds: int
    projects: list[InsightProject]
    work_types: list[InsightWorkType]
    days: list[InsightDay]
    session_lengths: list[SessionLengthBucket]
