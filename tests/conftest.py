import os

import pytest

from src.core.config import Config


@pytest.fixture(scope="session")
def config() -> Config:
    os.environ.setdefault("BASE_URL", "https://www.baidu.com/")
    return Config.from_env()
