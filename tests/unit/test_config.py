import os

import pytest

from src.core.config import Config, ConfigError


def test_config_reads_base_url_from_env(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    cfg = Config.from_env()
    assert cfg.base_url == "https://www.baidu.com/"


def test_config_missing_base_url_raises_readable_error(monkeypatch):
    monkeypatch.delenv("BASE_URL", raising=False)
    with pytest.raises(ConfigError, match="BASE_URL"):
        Config.from_env()
