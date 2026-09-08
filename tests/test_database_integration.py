import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.data.database import Database
from app.main import create_app
from app.models.api import ProjectCreate, ProjectPatch, SessionStart, SettingsPatch
from app.services.projects import ProjectService
from app.services.sessions import SessionService
from app.services.settings import SettingsService


pytestmark = pytest.mark.integration


@pytest.fixture
def database():
    if os.getenv("LUXTIME_RUN_INTEGRATION") != "1":
        pytest.skip("set LUXTIME_RUN_INTEGRATION=1 to use the local PostgreSQL container")
    db = Database.from_config(AppConfig.from_environment())
    assert db.ping()
    yield db
    db.close()


def test_health_projects_and_concurrent_session_lifecycle(database):
    config = AppConfig.from_environment()
    with TestClient(create_app(config)) as client:
        assert client.get("/api/health").json() == {
            "status": "healthy",
            "database": "connected",
        }

    suffix = uuid4().hex[:10]
    projects = ProjectService(database)
    sessions = SessionService(database)
    created_ids = []
    try:
        first = projects.create(ProjectCreate(name=f"Integration A {suffix}", code="ITA"))
        created_ids.append(first["id"])
        second = projects.create(ProjectCreate(name=f"Integration B {suffix}", code="ITB"))
        created_ids.append(second["id"])

        renamed = projects.update(first["id"], ProjectPatch(name=f"Renamed A {suffix}"))
        assert renamed["name"] == f"Renamed A {suffix}"
        assert projects.update(first["id"], ProjectPatch(active=False))["active"] is False
        assert projects.update(first["id"], ProjectPatch(active=True))["active"] is True

        base = datetime.now(timezone.utc) - timedelta(hours=4)
        first_session = sessions.start(SessionStart(project_id=first["id"], started_at=base))
        second_session = sessions.start(
            SessionStart(project_id=second["id"], started_at=base + timedelta(hours=1))
        )

        stopped_second = sessions.stop(second_session["id"], at=base + timedelta(hours=2))
        active_ids = {row["id"] for row in sessions.active()}
        assert stopped_second["total_seconds"] == 3600
        assert first_session["id"] in active_ids
        assert second_session["id"] not in active_ids

        paused_first = sessions.pause(first_session["id"], at=base + timedelta(hours=2))
        assert paused_first["status"] == "paused"
        resumed_first = sessions.resume(first_session["id"], at=base + timedelta(hours=2, minutes=30))
        assert len(resumed_first["segments"]) == 2
        stopped_first = sessions.stop(first_session["id"], at=base + timedelta(hours=3))
        assert stopped_first["total_seconds"] == 2 * 3600 + 30 * 60
        assert stopped_first["concurrent"] is True
    finally:
        for project_id in created_ids:
            database.execute(
                "DELETE FROM luxtime.work_sessions WHERE project_id = %s", (project_id,)
            )
            database.execute("DELETE FROM luxtime.projects WHERE id = %s", (project_id,))


def test_branding_settings_are_persisted(database):
    settings = SettingsService(database)
    original = settings.get()
    try:
        updated = settings.update(
            SettingsPatch(application_name="My Timer", accent_color="#A855F7")
        )
        assert updated["application_name"] == "My Timer"
        assert updated["accent_color"] == "#A855F7"
        assert settings.get()["application_name"] == "My Timer"
    finally:
        settings.update(
            SettingsPatch(
                application_name=original["application_name"],
                accent_color=original["accent_color"],
            )
        )
