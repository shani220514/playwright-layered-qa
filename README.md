# playwright-layered-qa

Pytest + Playwright 分层测试**框架**。默认 CI 只跑离线单测，不访问内网、不带业务系统。

公开样例站点：[百度首页](https://www.baidu.com/)：打开页面、拦截 XHR/fetch，以及从首页进入[百度热搜榜](https://top.baidu.com/board?platform=pc&sa=pcindex_entry)。可选把拦截到的响应 JSON 与 MySQL 一行结果比对。业务 Page Object 请放你自己的项目里，不要往本仓拷贝内部系统。
<img width="3072" height="1315" alt="image" src="https://github.com/user-attachments/assets/5bcd68f7-be05-4a15-be31-e0dffff7c4bd" />

## 能做什么

- `Config`：只读环境变量。`BASE_URL` 必填且须为绝对 http(s) 地址；`DB_*` 可选，未配时 `config.db` 为 `None`
- `BasePage`：goto / click / fill / 等待
- `NetworkInterceptor`：默认捕获 XHR/fetch，需要时再纳入 document。导出前把 Cookie、Authorization 等敏感头写成 `***`
- YAML schema：校验 `assets/` 里的用例、需求和待确认问题，并核对需求与用例的引用。步骤是给人读的，不会被执行
- 8 个 Skill 样例：需求解析 → 用例结构化 → 脚本编织，以及修复 / 探针 / 回归 / 缺陷 / 日报
- 可选 MySQL：配齐 `DB_HOST` / `DB_USER` / `DB_NAME` 后，可用 `MySQLClient` 查库，并用 `assert_response_matches_db` 把拦截到的响应 JSON 字段与一行 SQL 结果比对

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env
python -m pytest tests/unit -q
```

默认不跑活站点。先安装浏览器，再按需选一条 example（都需要 `.env` 里的 `BASE_URL`，缺少时不会偷偷改用百度）：

```bash
python -m playwright install chromium

# 首页 + 接口拦截 → reports/api-captures/baidu_home.json
python -m pytest tests/examples/test_baidu_home.py -m example --headed

# 热搜入口：点击「百度热搜」，断言到达 top.baidu.com/board
python -m pytest tests/examples/test_baidu_hot_entry.py -m example --headed
```

活站点失败时，截图和 trace 留在 `test-results/`。

## 可选：拦截响应与 MySQL 比对

不配 `DB_*` 时 `config.db` 为 `None`，现有用例不受影响。需要时在 `.env` 中取消注释并填写 `DB_HOST` / `DB_USER` / `DB_NAME` 等。

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

## 目录

```text
src/core/              Config、BasePage
src/interceptors/      接口拦截
src/db/                只读 MySQLClient
src/assertions/        响应 JSON 与库行比对
src/yaml_runner/       YAML schema
src/pages/             样例 POM（首页、热搜入口）
assets/                结构化用例（baidu_home、baidu_hot_entry）
examples/baidu/        需求解析 Human Doc
tests/unit/            离线单测（CI）
tests/examples/        打开百度：拦截 / 热搜入口
docs/superpowers/      规格与实现计划
.cursor/skills/        8 个 Skill 样例
```

## Skill 流水线（百度样例）

当前 Human Doc 主体是「从首页进入热搜」。首页拦截那条线仍保留。

1. **parse-requirements** 需求解析 → `examples/baidu/requirement.md`
2. **structure-cases** 用例结构化 → `assets/` 下的 YAML（热搜入口：`baidu_hot_entry`；首页拦截：`baidu_home`）
3. **weave-scripts** 脚本编织：Agent 对照 YAML 写出 pytest 骨架（`test_baidu_hot_entry.py` / `test_baidu_home.py`），不是仓库里有程序把 YAML 编译成脚本
4. **fix-scripts** 脚本修复
5. **probe-apis** 接口探针：接口文档 / 抓包 / OAS → 给人评审的 Human Doc（拦截 JSON 只是输入之一），再交给「用例结构化」
6. **manage-regression** 回归管理
7. **analyze-defects** 缺陷分析
8. **write-daily-report** 日报生成

在 Cursor 里提到这些中文名或英文 skill 名即可调用。Skill 需要可用的大模型；没有模型时只能跑已提交的 pytest，不能生成新的 Markdown / YAML / 脚本。

## YAML 的角色

`assets/cases`、`assets/requirements`、`assets/questions` 只做追溯和校验，例如：

- 必填字段是否齐全
- `case_id` / `req_id` / `question_id` 是否唯一
- 用例的 `requirement_ids` 是否指向已有需求
- 已自动化用例是否写了 `pytest_nodeid`（`manual` / `pending` 则为 `null`）

`steps` 是给人读的自然语言。本仓库没有 YAML 执行器，pytest 也不会去读这些步骤。跑起来的是编织（或手改）后的 `.py` 文件。当前样例模块是 `baidu_home` 与 `baidu_hot_entry`。
