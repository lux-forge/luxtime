"""Project creation and lifecycle operations."""

from __future__ import annotations

from uuid import UUID

from foundry.logger import logger

from app.core.errors import ConflictError, NotFoundError
from app.data.database import Database
from app.models.api import ProjectCreate, ProjectPatch

log = logger.bind(component="luxtime.projects")

_PROJECT_SELECT = """
SELECT id, name, code, color, total_seconds, active, created_at, updated_at
FROM luxtime.project_totals
"""


class ProjectService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list(self) -> list[dict]:
        return self.database.fetch_all(_PROJECT_SELECT + " ORDER BY active DESC, name")

    def get(self, project_id: UUID) -> dict:
        project = self.database.fetch_one(_PROJECT_SELECT + " WHERE id = %s", (project_id,))
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def create(self, payload: ProjectCreate) -> dict:
        name = payload.name.strip()
        if self.database.fetch_one(
            "SELECT id FROM luxtime.projects WHERE lower(name) = lower(%s)", (name,)
        ):
            raise ConflictError("A project with that name already exists")
        with self.database.transaction():
            row = self.database.fetch_one(
                """
                INSERT INTO luxtime.projects (name, code, color)
                VALUES (%s, NULLIF(%s, ''), %s)
                RETURNING id
                """,
                (name, payload.code.strip().upper() if payload.code else None, payload.color),
            )
        assert row is not None
        log.info("Project created", project_id=str(row["id"]))
        return self.get(row["id"])

    def update(self, project_id: UUID, payload: ProjectPatch) -> dict:
        requested = payload.model_dump(exclude_unset=True)
        if isinstance(requested.get("name"), str):
            requested["name"] = requested["name"].strip()
            duplicate = self.database.fetch_one(
                "SELECT id FROM luxtime.projects WHERE lower(name) = lower(%s) AND id <> %s",
                (requested["name"], project_id),
            )
            if duplicate:
                raise ConflictError("A project with that name already exists")
        columns = {
            "name": "name",
            "code": "code",
            "color": "color",
            "active": "active",
        }
        assignments: list[str] = []
        values: list[object] = []
        for field, value in requested.items():
            assignments.append(f"{columns[field]} = %s")
            if field == "code" and isinstance(value, str):
                value = value.strip().upper() or None
            values.append(value)
        values.append(project_id)
        with self.database.transaction():
            row = self.database.fetch_one(
                f"UPDATE luxtime.projects SET {', '.join(assignments)} WHERE id = %s RETURNING id",
                tuple(values),
            )
            if row is None:
                raise NotFoundError("Project not found")
        log.info("Project updated", project_id=str(project_id), fields=tuple(requested))
        return self.get(project_id)
