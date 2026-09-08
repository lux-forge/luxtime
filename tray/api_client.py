"""The tray's only business-state interface: the local LuxTime API."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class LuxTimeApi:
    def __init__(self, base_url: str = "http://127.0.0.1:52020") -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, *, method: str = "GET", payload: dict | None = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode("utf-8"))

    def status(self) -> dict:
        return self.request("/api/status")

    def projects(self) -> list[dict]:
        return self.request("/api/projects")

    def active(self) -> list[dict]:
        return self.request("/api/active")

    def settings(self) -> dict:
        return self.request("/api/settings")

    def start(self, project_id: str) -> dict:
        return self.request(
            "/api/sessions/start",
            method="POST",
            payload={"project_id": project_id, "work_type": "Development", "description": ""},
        )

    def action(self, session_id: str, action: str) -> dict:
        return self.request(
            f"/api/sessions/{session_id}/{action}", method="POST", payload={}
        )

    def action_all(self, action: str) -> dict:
        return self.request(f"/api/active/{action}-all", method="POST", payload={})
