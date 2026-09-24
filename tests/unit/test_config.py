import os

import pytest

from src.core.config import Config, ConfigError


def test_config_reads_base_url_from_env(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    cfg = Config.from_env()
    assert cfg.base_url == "https://www.baidu.com/"


def test_config_missing_base_url_raises_readable_error(monkeypatch):
    monkeypatch.delenv("BASE_URL", raising=False)
    with pytest.raises(ConfigError, match="BASE_URL"):
        Config.from_env(load_env=False)


def test_config_rejects_non_http_base_url(monkeypatch):
    monkeypatch.setenv("BASE_URL", "www.baidu.com")
    with pytest.raises(ConfigError, match="http"):
        Config.from_env(load_env=False)


def test_config_db_none_when_all_db_vars_missing(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    cfg = Config.from_env(load_env=False)
    assert cfg.db is None


def test_config_reads_db_when_host_user_name_present(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_USER", "qa")
    monkeypatch.setenv("DB_NAME", "app")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("DB_PORT", "3307")
    cfg = Config.from_env(load_env=False)
    assert cfg.db is not None
    assert cfg.db.host == "127.0.0.1"
    assert cfg.db.port == 3307
    assert cfg.db.user == "qa"
    assert cfg.db.password == "secret"
    assert cfg.db.database == "app"


def test_config_db_password_defaults_to_empty(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_USER", "qa")
    monkeypatch.setenv("DB_NAME", "app")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    cfg = Config.from_env(load_env=False)
    assert cfg.db is not None
    assert cfg.db.password == ""


def test_config_db_port_defaults_to_3306(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_USER", "qa")
    monkeypatch.setenv("DB_NAME", "app")
    monkeypatch.delenv("DB_PORT", raising=False)
    cfg = Config.from_env(load_env=False)
    assert cfg.db is not None
    assert cfg.db.port == 3306


def test_config_partial_db_vars_raise(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    with pytest.raises(ConfigError, match="DB_USER"):
        Config.from_env(load_env=False)


def test_config_invalid_db_port_raises(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://www.baidu.com/")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_USER", "qa")
    monkeypatch.setenv("DB_NAME", "app")
    monkeypatch.setenv("DB_PORT", "abc")
    with pytest.raises(ConfigError, match="DB_PORT"):
        Config.from_env(load_env=False)
