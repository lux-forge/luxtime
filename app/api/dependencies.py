"""Request-scoped infrastructure dependencies."""

from collections.abc import Iterator

from fastapi import Request

from app.config import AppConfig
from app.data.database import Database


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_database(request: Request) -> Iterator[Database]:
    database = Database.from_config(get_config(request))
    try:
        yield database
    finally:
        database.close()
