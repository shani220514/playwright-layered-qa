# Skill 流程介绍页与文件归档

## 目标

在本仓库增加一个只监听本机的页面：上半部分介绍 8 个 Skill 的用法，下半部分接收文件并归档到 `uploads/`，同时告诉用户下一步在 Cursor 里调用哪个 Skill。页面不解析文件内容，不生成需求报告、YAML 或测试脚本。

## 做法

使用 Python 标准库 `http.server`。不新增依赖。

- 页面静态文件放在 `web/`
- 服务放在 `src/web/server.py`
- 启动：在仓库根目录执行 `python -m src.web.server`
- 地址：`http://127.0.0.1:8765`
- 只绑定 `127.0.0.1`

## 页面

单页，桌面优先，窄屏时步骤卡片改为单列。

上半部分是流水线说明。主路径三步连在一起，其余五步作为旁路，不暗示必须按 4 到 8 的顺序执行。

| 顺序 | 中文名 | Skill 名 | 输入 | 输出 | 在 Cursor 里怎么说 |
| --- | --- | --- | --- | --- | --- |
| 1 | 需求解析 | parse-requirements | 需求文档或一句话 | `examples/<site>/requirement.md` | 需求解析、/需求 |
| 2 | 用例结构化 | structure-cases | 上一步的 Markdown | `assets/` 下的 YAML | 用例结构化、/结构化 |
| 3 | 脚本编织 | weave-scripts | `assets/cases` | pytest + Playwright 脚本骨架 | 脚本编织、/编织 |
| 旁路 | 脚本修复 | fix-scripts | traceback、失败截图 | 最小修复说明 | 脚本修复 |
| 旁路 | 接口探针 | probe-apis | 接口文档或抓包 JSON | 给人评审的接口报告 | /探针、接口探针 |
| 旁路 | 回归管理 | manage-regression | 变更说明 | 回归清单 | 回归管理、/回归 |
| 旁路 | 缺陷分析 | analyze-defects | 失败日志、截图、拦截 JSON | 缺陷报告 | 缺陷分析 |
| 旁路 | 日报生成 | write-daily-report | 当日工作笔记 | 测试日报 | 日报生成 |

每张卡片写清：这一步做什么、典型输入、典型输出、触发说法。页头用一句话说明：这是给人看的流程介绍，脚本仍由人在 Cursor 里让 Skill 去写。

下半部分是上传区：

- 点击选择和拖拽都可
- 一次一个文件
- 提交后展示保存后的相对路径、建议的 Skill 中文名、Skill 名、以及可复制的调用提示
- 失败时在上传区显示原因，页面不跳转

## 上传接口

`POST /upload`，`multipart/form-data`，字段名 `file`。

成功时返回 JSON：

```json
{
  "ok": true,
  "saved_as": "uploads/20260924-223015-requirement.md",
  "skill_name": "parse-requirements",
  "skill_label": "需求解析",
  "hint": "在 Cursor 中打开该文件，并说：需求解析"
}
```

失败时 HTTP 4xx，正文为 `{"ok": false, "error": "<原因>"}`。

规则：

- 缺少文件、空文件名、空内容：400
- 超过 5MB：400，提示上限
- 文件名只保留基名。去掉目录、`..`，以及 Windows 非法字符 `\ / : * ? " < > |`
- 清洗后没有合法名字：400
- 保存名格式：`YYYYMMDD-HHMMSS-` 加清洗后的原名。同一秒内重名时在时间戳后追加 `-2`、`-3`，直到不冲突
- 写入 `uploads/`。目录不存在时创建
- `GET /` 返回 `web/index.html`。其余 GET 只从 `web/` 读取静态文件，拒绝 `..` 和绝对路径。找不到文件时 404
- 扩展名判断不区分大小写

扩展名与建议 Skill：

| 扩展名 | Skill |
| --- | --- |
| `.md` `.txt` `.docx` | 需求解析 `parse-requirements` |
| `.yaml` `.yml` | 用例结构化 `structure-cases` |
| `.json` | 接口探针 `probe-apis` |
| `.log` | 脚本修复 `fix-scripts`。提示中补一句：若内容是失败现象而不是脚本报错，改说「缺陷分析」 |
| 其他 | `skill_name` 与 `skill_label` 为空字符串。`hint` 说明文件已归档，请按页面上的流程自行选择 Skill |

`.log` 不读取内容，不做堆栈检测。

## 安全边界

- 不提供目录浏览、下载、删除
- 不执行上传文件
- 不把文件内容回显到响应里
- 响应里的路径使用正斜杠相对路径，例如 `uploads/20260924-223015-requirement.md`

## 仓库约定

- `uploads/*` 加入 `.gitignore`，保留 `uploads/.gitkeep`
- `README.md` 增加启动说明，并在「后续可补」里把 GUI Runner 改成指向这个介绍页：它只介绍流程和归档文件，不执行 YAML、不跑测试
- 仓库根目录执行 `python -m src.web.server`。现有代码没有 `__init__.py`，按命名空间包启动。若因此无法启动，只补空的 `src/web/__init__.py`，不改其他目录

## 测试

`tests/unit/test_skill_guide_server.py`，离线，不启动浏览器，不监听端口。直接调用处理函数：

- 合法文件名清洗掉目录和非法字符
- `.md` `.yaml` `.json` `.log` 以及未知扩展名映射正确
- 保存成功时文件出现在临时 `uploads` 目录，响应字段完整
- 超过 5MB、缺少文件时返回 400，且不写入文件

## 不做

- 不调用 Skill，不生成 Markdown、YAML 或 pytest
- 不解析 docx、json、log 的内容
- 不增加 Flask、FastAPI 或其他 Web 依赖
- 不对外网监听
