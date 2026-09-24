from __future__ import annotations

from typing import Any, Sequence

import pymysql
from pymysql.cursors import DictCursor

from src.core.config import ConfigError, DbConfig


class MySQLClient:
    """Read-only MySQL helper. Callers pass SQL; this class does not rewrite it."""

    def __init__(self, db: DbConfig | None):
        if db is None:
            raise ConfigError(
                "Database is not configured. Set DB_HOST, DB_USER, and DB_NAME "
                "(see env.example), or omit MySQLClient when config.db is None."
            )
        self._db = db
        self._conn: pymysql.Connection | None = None

    def __enter__(self) -> "MySQLClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> dict:
        rows = self.fetch_all(sql, params)
        if len(rows) != 1:
            raise LookupError(
                f"fetch_one expected exactly 1 row, got {len(rows)} "
                f"(sql={sql!r})"
            )
        return rows[0]

    def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict]:
        conn = self._connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return list(rows)

    def _connection(self) -> pymysql.Connection:
        if self._conn is None:
            self._conn = pymysql.connect(
                host=self._db.host,
                port=self._db.port,
                user=self._db.user,
                password=self._db.password,
                database=self._db.database,
                cursorclass=DictCursor,
                autocommit=True,
            )
        return self._conn
