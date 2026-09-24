from unittest.mock import MagicMock

import pytest

from src.core.config import ConfigError, DbConfig
from src.db.mysql_client import MySQLClient


def _db() -> DbConfig:
    return DbConfig(host="127.0.0.1", port=3306, user="qa", password="", database="app")


def test_mysql_client_rejects_missing_db_config():
    with pytest.raises(ConfigError, match="DB_HOST"):
        MySQLClient(None)


def test_fetch_one_returns_single_row(monkeypatch):
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"id": 1, "name": "Ada"}]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.cursor.return_value.__exit__.return_value = None

    monkeypatch.setattr("src.db.mysql_client.pymysql.connect", lambda **kwargs: connection)

    client = MySQLClient(_db())
    row = client.fetch_one("SELECT id, name FROM t WHERE id=%s", (1,))
    assert row == {"id": 1, "name": "Ada"}
    cursor.execute.assert_called_once_with("SELECT id, name FROM t WHERE id=%s", (1,))
    client.close()


def test_fetch_one_zero_rows_raises(monkeypatch):
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.cursor.return_value.__exit__.return_value = None
    monkeypatch.setattr("src.db.mysql_client.pymysql.connect", lambda **kwargs: connection)

    client = MySQLClient(_db())
    with pytest.raises(LookupError, match="0"):
        client.fetch_one("SELECT 1")
    client.close()


def test_fetch_one_multiple_rows_raises(monkeypatch):
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.cursor.return_value.__exit__.return_value = None
    monkeypatch.setattr("src.db.mysql_client.pymysql.connect", lambda **kwargs: connection)

    client = MySQLClient(_db())
    with pytest.raises(LookupError, match="2"):
        client.fetch_one("SELECT 1")
    client.close()


def test_fetch_all_returns_list(monkeypatch):
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.cursor.return_value.__exit__.return_value = None
    monkeypatch.setattr("src.db.mysql_client.pymysql.connect", lambda **kwargs: connection)

    with MySQLClient(_db()) as client:
        rows = client.fetch_all("SELECT id FROM t")
    assert rows == [{"id": 1}, {"id": 2}]
