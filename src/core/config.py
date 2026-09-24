from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when required runtime config is missing or invalid."""


@dataclass(frozen=True)
class Config:
    base_url: str

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
        return cls(base_url=base_url)
