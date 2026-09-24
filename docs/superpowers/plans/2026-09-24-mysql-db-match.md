# MySQL 配置与拦截响应比对 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 可选 MySQL 环境变量配置 + 只读查询客户端 + 将拦截到的响应 JSON 与 SQL 一行结果比对。

**Architecture:** `Config` 可选挂载 `DbConfig`；`MySQLClient` 用 PyMySQL + DictCursor 做只读查询；`assert_response_matches_db` 纯函数完成同名/映射比对。默认 CI 不连真实库，单测用 monkeypatch / mock。

**Tech Stack:** Python 3.10+、python-dotenv、PyMySQL、pytest。

## Global Constraints

- 只支持 MySQL；不引入 ORM；不提供写库 API
- 不改 YAML 执行约定；不改百度 example 为必连库
- `BASE_URL` 仍必填；`DB_*` 可选
- `DB_HOST` / `DB_USER` / `DB_NAME` 全有 → `Config.db`；全无 → `None`；只配一部分 → `ConfigError`
- `DB_PORT` 默认 `3306`；非法非正整数 → `ConfigError`
- `DB_PASSWORD` 未设置按空字符串；允许为空
- `fetch_one` 必须恰好 1 行，否则抛错并说明行数
- 无 `field_map` 时同名键交集为空 → 失败；有映射时只比映射项；响应路径支持点号
- 值规范化：`Decimal` 整则 `int` 否则 `float`；`date` → `YYYY-MM-DD`；`datetime` → `isoformat()`；不做数字与字符串宽松互转
- 拦截 body 路径：`record["response"]["body"]`
- 离线单测不连真实 MySQL；CI 只跑 `tests/unit`
- 规格：`docs/superpowers/specs/2026-09-24-mysql-db-match-design.md`

## File Structure

| 文件 | 职责 |
| --- | --- |
| `src/core/config.py` | `DbConfig` + `Config.db` 可选解析 |
| `src/db/mysql_client.py` | MySQL 只读客户端 |
| `src/assertions/db_match.py` | 响应与库行断言 |
| `tests/unit/test_config.py` | 扩展 DB 配置用例 |
| `tests/unit/test_db_match.py` | 比对逻辑单测 |
| `tests/unit/test_mysql_client.py` | mock 测行数与未配置错误 |
| `requirements.txt` | 增加 `PyMySQL` |
| `env.example` / `README.md` | 可选 DB 说明与用法 |

---

### Task 1: 可选 DbConfig 接入 Config

**Files:**
- Modify: `src/core/config.py`
- Modify: `tests/unit/test_config.py`
- Modify: `env.example`

**Interfaces:**
- Consumes: 现有 `Config`、`ConfigError`、`from_env`
- Produces:
  - `DbConfig(host: str, port: int, user: str, password: str, database: str)` frozen dataclass
  - `Config(base_url: str, db: DbConfig | None = None)`

- [ ] **Step 1: Write the failing tests**

在 `tests/unit/test_config.py` 追加：

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_config.py -q`
Expected: FAIL（`Config` 尚无 `db` / `DbConfig`）

- [ ] **Step 3: Implement Config + DbConfig**

将 `src/core/config.py` 替换为：

```python
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
```

- [ ] **Step 4: Update env.example**

将 `env.example` 写成：

```text
BASE_URL=https://www.baidu.com/

# Optional MySQL. Omit all of DB_HOST/DB_USER/DB_NAME → config.db is None.
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_USER=qa
# DB_PASSWORD=
# DB_NAME=app
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_config.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/core/config.py tests/unit/test_config.py env.example
git commit -m "$(cat <<'EOF'
feat: add optional MySQL DbConfig to Config

EOF
)"
```

---

### Task 2: assert_response_matches_db

**Files:**
- Create: `src/assertions/db_match.py`
- Create: `tests/unit/test_db_match.py`

**Interfaces:**
- Consumes: 无（纯函数）
- Produces:
  - `assert_response_matches_db(response_json, db_row: dict, field_map: dict[str, str] | None = None) -> None`
  - 失败时抛 `AssertionError`，信息含字段、期望（库）、实际（响应）

- [ ] **Step 1: Write the failing tests**

创建 `tests/unit/test_db_match.py`：

```python
from datetime import date, datetime
from decimal import Decimal

import pytest

from src.assertions.db_match import assert_response_matches_db


def test_same_name_keys_match():
    assert_response_matches_db({"id": 1, "name": "a"}, {"id": 1, "name": "a", "extra": 9})


def test_same_name_empty_intersection_fails():
    with pytest.raises(AssertionError, match="intersection"):
        assert_response_matches_db({"a": 1}, {"b": 2})


def test_field_map_matches_nested_path():
    assert_response_matches_db(
        {"data": {"user": {"name": "Ada"}}},
        {"user_name": "Ada"},
        {"data.user.name": "user_name"},
    )


def test_field_map_missing_path_fails():
    with pytest.raises(AssertionError, match="data.missing"):
        assert_response_matches_db({"data": {}}, {"x": 1}, {"data.missing": "x"})


def test_value_mismatch_message_includes_expected_and_actual():
    with pytest.raises(AssertionError, match="name") as exc:
        assert_response_matches_db({"name": "a"}, {"name": "b"})
    message = str(exc.value)
    assert "b" in message
    assert "a" in message


def test_json_string_body_is_parsed():
    assert_response_matches_db('{"id": 1}', {"id": 1})


def test_invalid_json_string_fails():
    with pytest.raises(AssertionError, match="JSON"):
        assert_response_matches_db("{bad", {"id": 1})


def test_normalize_decimal_and_date():
    assert_response_matches_db(
        {"amount": 10, "day": "2026-09-24", "ts": "2026-09-24T12:00:00"},
        {
            "amount": Decimal("10"),
            "day": date(2026, 9, 24),
            "ts": datetime(2026, 9, 24, 12, 0, 0),
        },
    )


def test_no_loose_string_number_coercion():
    with pytest.raises(AssertionError):
        assert_response_matches_db({"id": "1"}, {"id": 1})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_db_match.py -q`
Expected: FAIL（模块不存在）

- [ ] **Step 3: Implement db_match**

创建 `src/assertions/db_match.py`：

```python
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def assert_response_matches_db(
    response_json: Any,
    db_row: dict,
    field_map: dict[str, str] | None = None,
) -> None:
    response = _as_mapping(response_json)
    if not isinstance(db_row, dict):
        raise AssertionError(f"db_row must be a dict (got {type(db_row).__name__})")

    if field_map:
        pairs = []
        for response_path, column in field_map.items():
            actual = _dig(response, response_path)
            if column not in db_row:
                raise AssertionError(f"db column missing: {column}")
            pairs.append((response_path, column, actual, db_row[column]))
    else:
        shared = sorted(set(response) & set(db_row))
        if not shared:
            raise AssertionError(
                "No shared keys between response and db_row "
                f"(response keys={sorted(response)}, db keys={sorted(db_row)}); "
                "intersection is empty"
            )
        pairs = [(key, key, response[key], db_row[key]) for key in shared]

    mismatches = []
    for label, column, actual, expected in pairs:
        norm_actual = _normalize(actual)
        norm_expected = _normalize(expected)
        if norm_actual != norm_expected:
            mismatches.append(
                f"{label} (column {column}): expected {norm_expected!r} from db, "
                f"got {norm_actual!r} from response"
            )
    if mismatches:
        raise AssertionError("response/db mismatch:\n" + "\n".join(mismatches))


def _as_mapping(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"response body is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise AssertionError(
                f"response JSON must be an object (got {type(parsed).__name__})"
            )
        return parsed
    raise AssertionError(
        f"response_json must be a dict or JSON object string (got {type(value).__name__})"
    )


def _dig(data: dict, path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise AssertionError(f"response path missing: {path}")
        current = current[part]
    return current


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_db_match.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/assertions/db_match.py tests/unit/test_db_match.py
git commit -m "$(cat <<'EOF'
feat: assert response JSON fields against a DB row

EOF
)"
```

---

### Task 3: MySQLClient（mock，不连真实库）

**Files:**
- Create: `src/db/mysql_client.py`
- Create: `tests/unit/test_mysql_client.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `DbConfig` from `src.core.config`
- Produces:
  - `MySQLClient(db: DbConfig | None)` — `db is None` 立即抛 `ConfigError`
  - `fetch_one(sql: str, params=None) -> dict`
  - `fetch_all(sql: str, params=None) -> list[dict]`
  - `close() -> None`
  - 支持 `with MySQLClient(...) as client:`

- [ ] **Step 1: Add dependency**

在 `requirements.txt` 末尾追加一行：

```text
PyMySQL>=1.1.0
```

- [ ] **Step 2: Write the failing tests**

创建 `tests/unit/test_mysql_client.py`：

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_mysql_client.py -q`
Expected: FAIL（模块不存在）

- [ ] **Step 4: Implement MySQLClient**

创建 `src/db/mysql_client.py`：

```python
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
```

- [ ] **Step 5: Install dependency and run tests**

Run:

```bash
pip install "PyMySQL>=1.1.0"
python -m pytest tests/unit/test_mysql_client.py tests/unit/test_config.py tests/unit/test_db_match.py -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/db/mysql_client.py tests/unit/test_mysql_client.py requirements.txt
git commit -m "$(cat <<'EOF'
feat: add read-only MySQLClient with fetch_one/fetch_all

EOF
)"
```

---

### Task 4: README 用法说明

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1–3 的公开 API
- Produces: 文档中的最小用法示例（不新增代码路径）

- [ ] **Step 1: Update README**

在「能做什么」列表中增加一条：

```markdown
- 可选 MySQL：环境变量配置 `DB_*` 后，可用 `MySQLClient` 查库，并用 `assert_response_matches_db` 把拦截到的响应 JSON 字段与一行 SQL 结果比对
```

在「快速开始」中 `copy env.example .env` 之后补一小段：

```markdown
可选数据库（不配则 `config.db` 为 `None`，现有用例不受影响）：

```bash
# 在 .env 中取消注释并填写 DB_HOST / DB_USER / DB_NAME 等
```

手写用例中的最小比对示例：

```python
from src.assertions.db_match import assert_response_matches_db
from src.db.mysql_client import MySQLClient

record = interceptor.find("/api/user")
body = record["response"]["body"]
with MySQLClient(config.db) as db:
    row = db.fetch_one("SELECT id, name FROM users WHERE id=%s", (body["id"],))
assert_response_matches_db(body, row)  # 同名键
# 或：assert_response_matches_db(body, row, {"data.name": "name"})
```
```

注意：插入时保持 README 现有 Markdown 围栏合法，避免嵌套围栏破坏渲染；若冲突，把示例改成缩进代码块或拆成独立 fenced block。

在「后续可补」增加：

```markdown
- 更多数据库驱动（当前仅 MySQL）
```

- [ ] **Step 2: Run full unit suite**

Run: `python -m pytest tests/unit -q`
Expected: PASS（无 DB 环境变量时行为与原先一致）

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs: document optional MySQL response/db matching

EOF
)"
```

---

## Self-Review

| Spec 要求 | 对应任务 |
| --- | --- |
| 可选 `DbConfig` / 部分缺失报错 / port 校验 | Task 1 |
| `env.example` 注释可选 | Task 1 |
| `MySQLClient` 只读 `fetch_one` / `fetch_all` / None 报错 | Task 3 |
| `assert_response_matches_db` 同名 + 映射 + 规范化 | Task 2 |
| 离线单测、不连真实库 | Task 1–3 |
| README 用法 | Task 4 |
| 不改百度 example / YAML 执行器 | 全计划未触碰 |

无 TBD/TODO。接口名在任务间一致：`DbConfig`、`MySQLClient.fetch_one`、`assert_response_matches_db`。
