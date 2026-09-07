"""Application settings stored as one PostgreSQL row."""

from __future__ import annotations

from foundry.logger import logger

from app.data.database import Database
from app.models.api import SettingsPatch

log = logger.bind(component="luxtime.settings")

_SETTINGS_SELECT = """
SELECT default_rate, stop_on_lock, stop_on_sleep, resume_prompt,
       idle_detection, idle_threshold, engine_starts_with_windows,
       startup_behaviour, updated_at
FROM luxtime.settings
WHERE singleton = TRUE
"""


class SettingsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self) -> dict:
        row = self.database.fetch_one(_SETTINGS_SELECT)
        if row is None:
            raise RuntimeError("LuxTime settings defaults have not been applied")
        return row

    def update(self, payload: SettingsPatch) -> dict:
        requested = payload.model_dump(exclude_unset=True)
        columns = {
            "default_rate": "default_rate",
            "stop_on_lock": "stop_on_lock",
            "stop_on_sleep": "stop_on_sleep",
            "resume_prompt": "resume_prompt",
            "idle_detection": "idle_detection",
            "idle_threshold": "idle_threshold",
            "engine_starts_with_windows": "engine_starts_with_windows",
            "startup_behaviour": "startup_behaviour",
        }
        assignments = [f"{columns[field]} = %s" for field in requested]
        with self.database.transaction():
            self.database.execute(
                f"UPDATE luxtime.settings SET {', '.join(assignments)} WHERE singleton = TRUE",
                tuple(requested.values()),
                commit=False,
            )
        log.info("Settings updated", fields=tuple(requested))
        return self.get()
