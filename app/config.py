"""Environment-backed LuxTime configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _integer(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class AppConfig:
    database_name: str
    database_user: str
    database_password: str
    database_host: str
    database_port: int
    web_dist: Path
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "AppConfig":
        origins = os.getenv(
            "LUXTIME_ALLOWED_ORIGINS",
            "http://127.0.0.1:52022,http://localhost:52022",
        )
        return cls(
            database_name=os.getenv("LUXTIME_DB_NAME", os.getenv("POSTGRES_DB", "luxtime")),
            database_user=os.getenv("LUXTIME_DB_USER", os.getenv("POSTGRES_USER", "luxtime")),
            database_password=os.getenv(
                "LUXTIME_DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "luxtime_dev")
            ),
            database_host=os.getenv("LUXTIME_DB_HOST", "127.0.0.1"),
            database_port=_integer("LUXTIME_DB_PORT", 5432),
            web_dist=Path(os.getenv("LUXTIME_WEB_DIST", "web/dist")).resolve(),
            allowed_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        )
