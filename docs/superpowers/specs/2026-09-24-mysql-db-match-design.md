# MySQL 配置与拦截响应比对

## 目标

在框架中增加可选的 MySQL 连接配置，以及把页面拦截到的接口响应 JSON 字段与一条 SQL 查询结果列做校验的能力。业务用例可在手写 pytest 里调用；默认 CI 与百度样例不连真实库。

## 范围

做：

- `Config` 可选挂载 `DbConfig`（环境变量）
- `MySQLClient`：只读查询（`fetch_one`，可选 `fetch_all`）
- `assert_response_matches_db`：响应 JSON 与库行比对（同名或显式映射）
- `env.example` / README 说明
- 离线单测（配置解析、比对逻辑、行数错误）；不连真实 MySQL

不做：

- PostgreSQL / SQLite 或其他驱动（预留扩展，本期只接 MySQL）
- YAML 步骤执行器里声明 SQL 并自动跑
- 写库 API（insert / update / delete）
- 改百度活站点 example 为必连库
- ORM

## 架构

```text
.env / 环境变量
    → Config.from_env()  →  Config(base_url, db: DbConfig | None)
                              ↓
                         MySQLClient(db)
                              ↓ fetch_one(sql, params)
NetworkInterceptor.find(...)  →  response body (dict)
                              ↓
                    assert_response_matches_db(response, db_row, field_map?)
```

分层：

| 模块 | 路径 | 职责 |
| --- | --- | --- |
| 配置 | `src/core/config.py` | 读环境变量；可选构建 `DbConfig` |
| 客户端 | `src/db/mysql_client.py` | 连接 MySQL；只读查询 |
| 断言 | `src/assertions/db_match.py` | 响应 JSON 与一行 dict 比对 |

依赖：`requirements.txt` 增加 `PyMySQL`。连接失败时的错误信息保持可读，不吞异常。

## 配置

环境变量：

| 变量 | 含义 | 默认 |
| --- | --- | --- |
| `DB_HOST` | MySQL 主机 | 无 |
| `DB_PORT` | 端口 | `3306` |
| `DB_USER` | 用户名 | 无 |
| `DB_PASSWORD` | 密码 | 空字符串（未设置时） |
| `DB_NAME` | 库名 | 无 |

规则：

1. `DB_HOST`、`DB_USER`、`DB_NAME` 均有非空值 → `Config.db = DbConfig(...)`
2. 三者均缺（或均为空）→ `Config.db is None`，合法
3. 只配置了其中一部分 → 抛 `ConfigError`，列出缺失项
4. `DB_PORT` 非正整数 → `ConfigError`
5. `DB_PASSWORD` 允许为空；不单独要求必须设置
6. `BASE_URL` 规则不变，仍为必填

`DbConfig` 为 frozen dataclass，字段：`host`, `port`, `user`, `password`, `database`。

`env.example` 增加上述变量，并注释「可选；不配则 `config.db` 为 None」。

## MySQLClient

```python
client = MySQLClient(config.db)  # config.db 为 None 时立即抛清晰错误
row = client.fetch_one("SELECT id, name FROM t WHERE id=%s", (1,))
```

行为：

- `config.db is None`（或传入 `None`）→ 抛错：未配置数据库，请设置 `DB_HOST` / `DB_USER` / `DB_NAME`
- `fetch_one`：0 行或多于 1 行 → 抛错，说明实际行数；恰好 1 行 → 返回 `dict`（列名 → 值），使用 `DictCursor`
- 可选提供 `fetch_all`，返回 `list[dict]`；默认断言路径只用 `fetch_one`
- 不提供写操作方法
- 连接在客户端实例上按需建立；测试结束由用例或 fixture 关闭（实现时可用 context manager 或显式 `close()`）

SQL 与参数由调用方传入。框架不对 SQL 做解析或改写。

## 断言

```python
assert_response_matches_db(
    response_json,
    db_row,
    field_map=None,
)
```

输入：

- `response_json`：优先为 `dict`。若为 `str`，先 `json.loads`；解析失败则断言失败并说明原因。若为 `None` 或其他类型 → 失败
- `db_row`：一行 `dict`
- `field_map`：可选 `dict[str, str]`，键为响应侧路径，值为 SQL 列名

比对：

1. **有 `field_map`**：只比对映射中的项。响应侧支持点路径（如 `data.user.name`）；路径不存在 → 失败并指出路径
2. **无 `field_map`**：取两边键名交集比对；交集为空 → 失败（避免静默通过）
3. 值不相等 → 失败，信息中列出字段、期望（库侧）、实际（响应侧）
4. **值规范化（固定规则，单测锁死）**：
   - `Decimal`：若等于整数则转为 `int`，否则转为 `float`
   - `datetime` / `date`：转为 ISO 格式字符串（`date` → `YYYY-MM-DD`，`datetime` → `datetime.isoformat()`）
   - 其余类型保持原样后用 `==` 比较
   - 不做「数字字符串与数字」的宽松互转，避免隐式通过；需要时由调用方在 SQL 或 `field_map` 侧对齐类型

从拦截记录取 body（与现有 `NetworkInterceptor` 结构一致）：

```python
record = interceptor.find("/api/user")
assert record and record.get("response")
body = record["response"]["body"]
row = MySQLClient(config.db).fetch_one("SELECT ...", (...))
assert_response_matches_db(body, row, {"data.name": "name"})
```

本期不强制在 `conftest` 增加 `db` fixture；需要时业务仓自行加。README 给最小用法示例即可。
## 测试

`tests/unit/` 离线，不连真实 MySQL：

- 配置：全缺 → `db is None`；齐全 → 字段正确；部分缺失 → `ConfigError`；非法 port → `ConfigError`
- 比对：同名成功 / 同名交集为空失败 / 映射成功 / 映射路径缺失失败 / 值不一致信息可读
- `fetch_one` 行数：用假连接或 mock cursor 测 0/1/多行

CI 继续只跑 `tests/unit`，不要求配置 `DB_*`。

## 文档

- `README.md`：在「能做什么」或单独小节说明可选 MySQL 配置，以及拦截响应与库行比对的用法；「后续可补」可写「更多数据库驱动」
- `env.example`：列出 `DB_*` 并标注可选

## 成功标准

1. 未配 `DB_*` 时现有单测与 example 行为不变
2. 配齐后可用 `MySQLClient.fetch_one` + `assert_response_matches_db` 完成「响应字段 ↔ 库列」校验
3. 同名与显式映射两种模式均有单测覆盖
4. 默认 CI 不依赖真实 MySQL
