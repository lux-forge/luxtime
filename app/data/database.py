"""Small application adapter over Foundry's PostgreSQL infrastructure."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID

from foundry.postgres import PostgresManager

from app.config import AppConfig


class Database:
    def __init__(self, manager: PostgresManager) -> None:
        self.manager = manager

    @classmethod
    def from_config(cls, config: AppConfig) -> "Database":
        return cls(
            PostgresManager(
                dbname=config.database_name,
                user=config.database_user,
                password=config.database_password,
                host=config.database_host,
                port=config.database_port,
            )
        )

    def ping(self) -> bool:
        return self.manager.test_connection()

    @staticmethod
    def _adapt_values(values: object) -> object:
        """Keep domain UUIDs driver-agnostic at the Foundry adapter boundary."""
        if isinstance(values, UUID):
            return str(values)
        if isinstance(values, tuple):
            return tuple(Database._adapt_values(value) for value in values)
        if isinstance(values, list):
            return [Database._adapt_values(value) for value in values]
        return values

    def fetch_all(self, statement: object, values: object = None) -> list[dict[str, Any]]:
        return self.manager.data.query_dicts(
            statement, values=self._adapt_values(values)
        )

    def fetch_one(self, statement: object, values: object = None) -> dict[str, Any] | None:
        rows = self.fetch_all(statement, values)
        return rows[0] if rows else None

    def execute(self, statement: object, values: object = None, *, commit: bool = True) -> None:
        self.manager.execute_required(
            statement, values=self._adapt_values(values), commit=commit
        )

    @contextmanager
    def transaction(self) -> Iterator["Database"]:
        with self.manager.transaction():
            yield self

    def close(self) -> None:
        self.manager.close()
