from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when required runtime config is missing or invalid."""


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class Config:
    base_url: str
    db: DbConfig | None = None

    @classmethod
    def from_env(cls, *, load_env: bool = True) -> "Config":
        if load_env:
            load_dotenv()
        base_url = os.getenv("BASE_URL", "").strip()
        if not base_url:
            raise ConfigError(
                "Missing BASE_URL. Copy env.example to .env and set BASE_URL, "
                "for example https://www.baidu.com/"
            )
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigError(
                "BASE_URL must be an absolute http(s) URL, "
                f"for example https://www.baidu.com/ (got {base_url!r})"
            )
        return cls(base_url=base_url, db=_load_db_config())


def _load_db_config() -> DbConfig | None:
    host = os.getenv("DB_HOST", "").strip()
    user = os.getenv("DB_USER", "").strip()
    database = os.getenv("DB_NAME", "").strip()
    password = os.getenv("DB_PASSWORD", "")
    port_raw = os.getenv("DB_PORT", "3306").strip() or "3306"

    present = [name for name, value in (("DB_HOST", host), ("DB_USER", user), ("DB_NAME", database)) if value]
    missing = [name for name, value in (("DB_HOST", host), ("DB_USER", user), ("DB_NAME", database)) if not value]

    if not present:
        return None
    if missing:
        raise ConfigError(
            "Incomplete database config. Missing "
            + ", ".join(missing)
            + ". Set DB_HOST, DB_USER, and DB_NAME together, or omit all of them."
        )
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ConfigError(f"DB_PORT must be a positive integer (got {port_raw!r})") from exc
    if port <= 0:
        raise ConfigError(f"DB_PORT must be a positive integer (got {port_raw!r})")

    return DbConfig(host=host, port=port, user=user, password=password, database=database)
