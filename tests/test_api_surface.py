from pathlib import Path

from app.config import AppConfig
from app.main import create_app


def test_required_routes_are_exposed():
    app = create_app(
        AppConfig(
            database_name="luxtime",
            database_user="luxtime",
            database_password="unused",
            database_host="127.0.0.1",
            database_port=54329,
            web_dist=Path("does-not-exist"),
            allowed_origins=("http://127.0.0.1:52022",),
        )
    )
    operations = {
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
    }
    required = {
        ("GET", "/api/health"),
        ("GET", "/api/status"),
        ("GET", "/api/projects"),
        ("POST", "/api/projects"),
        ("PATCH", "/api/projects/{project_id}"),
        ("GET", "/api/sessions"),
        ("POST", "/api/sessions/start"),
        ("POST", "/api/sessions/{session_id}/pause"),
        ("POST", "/api/sessions/{session_id}/resume"),
        ("POST", "/api/sessions/{session_id}/stop"),
        ("POST", "/api/active/stop-all"),
        ("POST", "/api/active/pause-all"),
        ("POST", "/api/active/resume-all"),
        ("GET", "/api/insights"),
        ("GET", "/api/settings"),
        ("PATCH", "/api/settings"),
    }
    assert required <= operations
