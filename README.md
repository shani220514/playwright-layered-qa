# playwright-layered-qa

Pytest + Playwright 分层测试**框架**。默认 CI 只跑离线单测，不访问内网、不带业务系统。

公开样例站点：[百度首页](https://www.baidu.com/)（打开 URL + 接口拦截）。业务 Page Object 请放你自己的项目里，不要往本仓拷贝内部系统。

## 能做什么

- `Config`：只读环境变量。缺 `BASE_URL`，或不是绝对 http(s) 地址时，给出可读错误
- `BasePage`：goto / click / fill / 等待
- `NetworkInterceptor`：默认捕获 XHR/fetch，需要时再纳入 document。导出前把 Cookie、Authorization 等敏感头写成 `***`
- YAML schema：校验 `assets/` 里的用例、需求和待确认问题，并核对需求与用例的引用。步骤是给人读的，不会被执行
- 8 个 Skill 样例：需求解析 → 用例结构化 → 脚本编织，以及修复 / 探针 / 回归 / 缺陷 / 日报

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env
python -m pytest tests/unit -q
```

默认不跑活站点：

```bash
python -m playwright install chromium
python -m pytest tests/examples/test_baidu_home.py -m example
```

该用例会打开 https://www.baidu.com/ ，等待搜索框，并把拦截到的 XHR/fetch 写到 `reports/api-captures/baidu_home.json`。活站点失败时，截图和 trace 留在 `test-results/`。请先复制 `env.example` 为 `.env`，示例不会在缺少 `BASE_URL` 时偷偷改用百度。

## 目录

```text
src/core/              配置与 BasePage
src/interceptors/      接口拦截
src/yaml_runner/       YAML schema
src/pages/             样例 POM（百度首页）
assets/                结构化用例
examples/baidu/        需求解析 Human Doc
tests/unit/            离线单测（CI）
tests/examples/        打开百度 + 拦截
.cursor/skills/        8 个 Skill 样例
```

## Skill 流水线（百度样例）

1. **parse-requirements** 需求解析 → `examples/baidu/requirement.md`
2. **structure-cases** 用例结构化 → `assets/cases/baidu_home.yaml`
3. **weave-scripts** 脚本编织 → `tests/examples/test_baidu_home.py`
4. **fix-scripts** 脚本修复
5. **probe-apis** 接口探针（读拦截 JSON，勿把响应正文提交进 git）
6. **manage-regression** 回归管理
7. **analyze-defects** 缺陷分析
8. **write-daily-report** 日报生成

在 Cursor 里提到这些中文名或英文 skill 名即可调用。

## YAML 的角色

`assets/cases`、`assets/requirements`、`assets/questions` 用来追溯：字段是否齐全、`case_id` 是否唯一、`requirement_ids` 是否指向已有需求、自动化用例的 `pytest_nodeid` 是否写明。步骤是自然语言，本仓库不解释、不执行这些步骤。脚本仍是手写的 pytest。

## 后续可补

- YAML 步骤执行器（若以后要让 YAML 真正跑起来）
- API Mock / Golden（当前只支持延迟和改 query）
- GUI Runner
- 你自己的业务 `pages/` 与用例（请放私有仓）
