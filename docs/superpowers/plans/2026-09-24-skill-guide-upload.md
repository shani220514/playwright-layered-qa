# Skill 流程介绍页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本机提供一个页面，介绍 8 个 Skill 的用法，并把上传文件归档到 `uploads/`，同时返回下一步该在 Cursor 里说的 Skill。

**Architecture:** 逻辑全部放在 `src/web/server.py`，用标准库 `http.server` 只绑定 `127.0.0.1:8765`。页面是 `web/` 下的静态文件。单测直接调用纯函数，不监听端口、不打开浏览器。

**Tech Stack:** Python 3.10 标准库、HTML、CSS、无构建步骤的浏览器脚本。不新增依赖。

## Global Constraints

- 不新增 Flask、FastAPI 或其他 Web 依赖
- 不调用 Skill，不生成 Markdown、YAML 或 pytest
- 不解析 docx、json、log 的内容；`.log` 不做堆栈检测
- 不提供目录浏览、下载、删除，不执行上传文件，响应不回显文件内容
- 只绑定 `127.0.0.1`，端口 `8765`
- 启动命令是仓库根目录的 `python -m src.web.server`
- 单文件上限 `5 * 1024 * 1024` 字节
- 保存名格式：`YYYYMMDD-HHMMSS-` 加清洗后的原名；同一秒重名时改为 `YYYYMMDD-HHMMSS-2-原名`、`YYYYMMDD-HHMMSS-3-原名`
- 响应路径固定为 `uploads/<文件名>`，使用正斜杠
- 扩展名判断不区分大小写
- 未知扩展名的 `skill_name` 与 `skill_label` 为空字符串
- 现有代码没有 `__init__.py`。只有 `python -m src.web.server` 因此失败时，才补空的 `src/web/__init__.py`
- 单测文件是 `tests/unit/test_skill_guide_server.py`，离线，不启动浏览器，不监听端口

---

### Task 1: 文件名清洗与 Skill 建议

**Files:**
- Create: `src/web/server.py`
- Test: `tests/unit/test_skill_guide_server.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `sanitize_filename(raw_name: str) -> str`。合法时返回清洗后的基名，否则返回 `""`
  - `suggest_skill(filename: str) -> dict[str, str]`。键为 `skill_name`、`skill_label`、`hint`

- [ ] **Step 1: Write the failing test**

把下面内容写入 `tests/unit/test_skill_guide_server.py`：

```python
import pytest

from src.web.server import sanitize_filename, suggest_skill


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (r"..\..\foo:bar*.md", "foobar.md"),
        ("../../secret.txt", "secret.txt"),
        ("..", ""),
        ("", ""),
        ("   ", ""),
        ('bad"name?.md', "badname.md"),
        ("需求.md", "需求.md"),
    ],
)
def test_sanitize_filename_strips_directories_and_illegal_characters(raw, expected):
    assert sanitize_filename(raw) == expected


@pytest.mark.parametrize(
    ("name", "skill_name", "skill_label"),
    [
        ("A.MD", "parse-requirements", "需求解析"),
        ("note.txt", "parse-requirements", "需求解析"),
        ("note.docx", "parse-requirements", "需求解析"),
        ("cases.yaml", "structure-cases", "用例结构化"),
        ("cases.YML", "structure-cases", "用例结构化"),
        ("capture.json", "probe-apis", "接口探针"),
        ("pytest.log", "fix-scripts", "脚本修复"),
        ("screenshot.png", "", ""),
    ],
)
def test_suggest_skill_maps_extension(name, skill_name, skill_label):
    got = suggest_skill(name)
    assert got["skill_name"] == skill_name
    assert got["skill_label"] == skill_label
    if skill_name == "fix-scripts":
        assert "缺陷分析" in got["hint"]
        assert got["hint"].startswith("在 Cursor 中打开该文件，并说：脚本修复")
    elif skill_name == "":
        assert got["hint"] == "文件已归档，请按页面上的流程自行选择 Skill"
    else:
        assert got["hint"] == f"在 Cursor 中打开该文件，并说：{skill_label}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_guide_server.py -q`

Expected: FAIL，`ModuleNotFoundError` 或 `ImportError`，因为 `src.web.server` 还不存在。

- [ ] **Step 3: Write minimal implementation**

把下面内容写入 `src/web/server.py`：

```python
from __future__ import annotations

import re
from pathlib import PurePosixPath

_ILLEGAL = re.compile(r'[\\/:*?"<>|]')

_HINT = "在 Cursor 中打开该文件，并说：{label}"
_LOG_HINT = (
    "在 Cursor 中打开该文件，并说：脚本修复。"
    "若内容是失败现象而不是脚本报错，改说「缺陷分析」"
)
_UNKNOWN_HINT = "文件已归档，请按页面上的流程自行选择 Skill"

_BY_EXT: dict[str, tuple[str, str, str]] = {
    ".md": ("parse-requirements", "需求解析", _HINT.format(label="需求解析")),
    ".txt": ("parse-requirements", "需求解析", _HINT.format(label="需求解析")),
    ".docx": ("parse-requirements", "需求解析", _HINT.format(label="需求解析")),
    ".yaml": ("structure-cases", "用例结构化", _HINT.format(label="用例结构化")),
    ".yml": ("structure-cases", "用例结构化", _HINT.format(label="用例结构化")),
    ".json": ("probe-apis", "接口探针", _HINT.format(label="接口探针")),
    ".log": ("fix-scripts", "脚本修复", _LOG_HINT),
}


def sanitize_filename(raw_name: str) -> str:
    if not raw_name or not raw_name.strip():
        return ""
    base = raw_name.replace("\\", "/").split("/")[-1]
    cleaned = _ILLEGAL.sub("", base).strip()
    if cleaned in {"", ".", ".."}:
        return ""
    return cleaned


def suggest_skill(filename: str) -> dict[str, str]:
    ext = PurePosixPath(filename).suffix.lower()
    skill_name, skill_label, hint = _BY_EXT.get(ext, ("", "", _UNKNOWN_HINT))
    return {
        "skill_name": skill_name,
        "skill_label": skill_label,
        "hint": hint,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_guide_server.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/web/server.py tests/unit/test_skill_guide_server.py
git commit -m "增加文件名清洗和 Skill 建议"
```

---

### Task 2: 归档上传文件

**Files:**
- Modify: `src/web/server.py`
- Modify: `tests/unit/test_skill_guide_server.py`

**Interfaces:**
- Consumes: `sanitize_filename`，`suggest_skill`
- Produces:
  - `MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024`
  - `handle_upload(upload_dir: Path, filename: str | None, content: bytes | None, now: datetime | None = None) -> tuple[int, dict]`
  - 成功体：`ok`、`saved_as`、`skill_name`、`skill_label`、`hint`
  - 失败体：`{"ok": False, "error": "<原因>"}`，状态码 `400`
  - 错误文案只有这五句：`缺少文件`、`文件名为空`、`文件内容为空`、`文件超过 5MB 上限`、`文件名不合法`

检查顺序固定为：缺少文件、文件名为空、内容为空、超过 5MB、清洗后的文件名。任一步失败都不创建目录、不写文件。`saved_as` 始终是 `uploads/<保存名>`，文件字节写到调用方传入的 `upload_dir`。

- [ ] **Step 1: Write the failing test**

把 `tests/unit/test_skill_guide_server.py` 顶部的 import 换成：

```python
from datetime import datetime
from pathlib import Path

import pytest

from src.web.server import handle_upload, sanitize_filename, suggest_skill
```

然后在文件末尾追加这些测试，不要再写 import：

```python
def test_handle_upload_saves_file_and_returns_skill_hint(tmp_path: Path):
    when = datetime(2026, 9, 24, 22, 30, 15)
    status, body = handle_upload(tmp_path, "requirement.md", b"# req", now=when)
    assert status == 200
    assert body == {
        "ok": True,
        "saved_as": "uploads/20260924-223015-requirement.md",
        "skill_name": "parse-requirements",
        "skill_label": "需求解析",
        "hint": "在 Cursor 中打开该文件，并说：需求解析",
    }
    assert "\\" not in body["saved_as"]
    assert (tmp_path / "20260924-223015-requirement.md").read_bytes() == b"# req"


def test_handle_upload_suffixes_same_second_duplicate(tmp_path: Path):
    when = datetime(2026, 9, 24, 22, 30, 15)
    first = handle_upload(tmp_path, "requirement.md", b"one", now=when)
    second = handle_upload(tmp_path, "requirement.md", b"two", now=when)
    third = handle_upload(tmp_path, "requirement.md", b"three", now=when)
    assert first[1]["saved_as"] == "uploads/20260924-223015-requirement.md"
    assert second[1]["saved_as"] == "uploads/20260924-223015-2-requirement.md"
    assert third[1]["saved_as"] == "uploads/20260924-223015-3-requirement.md"
    assert (tmp_path / "20260924-223015-2-requirement.md").read_bytes() == b"two"


def test_handle_upload_rejects_oversize_without_writing(tmp_path: Path):
    content = b"x" * (5 * 1024 * 1024 + 1)
    status, body = handle_upload(tmp_path, "big.md", content)
    assert status == 400
    assert body == {"ok": False, "error": "文件超过 5MB 上限"}
    assert list(tmp_path.iterdir()) == []


def test_handle_upload_rejects_missing_file_without_writing(tmp_path: Path):
    status, body = handle_upload(tmp_path, None, None)
    assert status == 400
    assert body == {"ok": False, "error": "缺少文件"}
    assert list(tmp_path.iterdir()) == []


def test_handle_upload_rejects_empty_name_and_empty_content(tmp_path: Path):
    empty_name = handle_upload(tmp_path, "   ", b"abc")
    empty_body = handle_upload(tmp_path, "note.md", b"")
    illegal = handle_upload(tmp_path, "???", b"abc")
    assert empty_name == (400, {"ok": False, "error": "文件名为空"})
    assert empty_body == (400, {"ok": False, "error": "文件内容为空"})
    assert illegal == (400, {"ok": False, "error": "文件名不合法"})
    assert list(tmp_path.iterdir()) == []


def test_handle_upload_creates_missing_directory(tmp_path: Path):
    target = tmp_path / "nested" / "uploads"
    when = datetime(2026, 9, 24, 22, 30, 15)
    status, body = handle_upload(target, r"..\需求.md", "你好".encode("utf-8"), now=when)
    assert status == 200
    assert body["saved_as"] == "uploads/20260924-223015-需求.md"
    assert (target / "20260924-223015-需求.md").read_text(encoding="utf-8") == "你好"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_guide_server.py::test_handle_upload_saves_file_and_returns_skill_hint -q`

Expected: FAIL，`ImportError: cannot import name 'handle_upload'`

- [ ] **Step 3: Write minimal implementation**

在 `src/web/server.py` 的 import 区改为：

```python
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path, PurePosixPath
```

在 `_BY_EXT` 之前增加：

```python
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
```

在文件末尾追加：

```python
def _saved_name(upload_dir: Path, safe_name: str, now: datetime) -> str:
    stamp = now.strftime("%Y%m%d-%H%M%S")
    candidate = f"{stamp}-{safe_name}"
    if not (upload_dir / candidate).exists():
        return candidate
    index = 2
    while (upload_dir / f"{stamp}-{index}-{safe_name}").exists():
        index += 1
    return f"{stamp}-{index}-{safe_name}"


def handle_upload(
    upload_dir: Path,
    filename: str | None,
    content: bytes | None,
    now: datetime | None = None,
) -> tuple[int, dict]:
    if filename is None or content is None:
        return 400, {"ok": False, "error": "缺少文件"}
    if filename.strip() == "":
        return 400, {"ok": False, "error": "文件名为空"}
    if len(content) == 0:
        return 400, {"ok": False, "error": "文件内容为空"}
    if len(content) > MAX_UPLOAD_BYTES:
        return 400, {"ok": False, "error": "文件超过 5MB 上限"}
    safe_name = sanitize_filename(filename)
    if not safe_name:
        return 400, {"ok": False, "error": "文件名不合法"}

    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_name = _saved_name(upload_dir, safe_name, now or datetime.now())
    (upload_dir / saved_name).write_bytes(content)
    suggestion = suggest_skill(safe_name)
    return 200, {
        "ok": True,
        "saved_as": f"uploads/{saved_name}",
        **suggestion,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_guide_server.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/web/server.py tests/unit/test_skill_guide_server.py
git commit -m "上传后按扩展名归档并返回 Skill 提示"
```

---

### Task 3: 静态文件与上传路由

**Files:**
- Modify: `src/web/server.py`
- Modify: `tests/unit/test_skill_guide_server.py`

**Interfaces:**
- Consumes: `handle_upload`
- Produces:
  - `resolve_static(web_root: Path, url_path: str) -> Path | None`。`/` 指向 `index.html`；路径含 `..`、绝对路径、或文件不存在时返回 `None`；目录也返回 `None`
  - `parse_upload(content_type: str, body: bytes) -> tuple[str | None, bytes | None]`。只读取字段名 `file`。没有该字段时返回 `(None, None)`
  - `route_post(path: str, content_type: str, body: bytes, upload_dir: Path, now: datetime | None = None) -> tuple[int, dict]`。仅 `path` 的路径部分等于 `/upload` 时调用 `handle_upload`，否则 `404` 且 `error` 为 `未找到文件`
  - `SkillGuideHandler`、`main()`。`HOST = "127.0.0.1"`，`PORT = 8765`。仓库根目录是 `Path(__file__).resolve().parents[2]`

单测不实例化 socket。

- [ ] **Step 1: Write the failing test**

在 `tests/unit/test_skill_guide_server.py` 的 import 中补上 `parse_upload, resolve_static, route_post`，并追加：

```python
def test_resolve_static_serves_index_and_rejects_escape(tmp_path: Path):
    (tmp_path / "index.html").write_text("home", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    assert resolve_static(tmp_path, "/") == (tmp_path / "index.html").resolve()
    assert resolve_static(tmp_path, "/app.js") == (tmp_path / "app.js").resolve()
    assert resolve_static(tmp_path, "/../server.py") is None
    assert resolve_static(tmp_path, "/assets") is None
    assert resolve_static(tmp_path, "/missing.css") is None


def test_parse_upload_reads_only_the_file_field():
    boundary = "bound"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="note"\r\n\r\n'
        f"ignore\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="需求.md"\r\n'
        f"Content-Type: text/markdown\r\n\r\n"
        f"# hello\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    filename, content = parse_upload(f"multipart/form-data; boundary={boundary}", body)
    assert filename == "需求.md"
    assert content == "# hello".encode("utf-8")
    assert parse_upload("text/plain", b"nope") == (None, None)


def test_route_post_archives_multipart_and_rejects_other_paths(tmp_path: Path):
    boundary = "bound"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="capture.json"\r\n'
        f"Content-Type: application/json\r\n\r\n"
        f"{{}}\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    when = datetime(2026, 9, 24, 22, 30, 15)
    status, payload = route_post(
        "/upload?from=page",
        f"multipart/form-data; boundary={boundary}",
        body,
        tmp_path,
        now=when,
    )
    assert status == 200
    assert payload["saved_as"] == "uploads/20260924-223015-capture.json"
    assert payload["skill_name"] == "probe-apis"
    assert (tmp_path / "20260924-223015-capture.json").read_bytes() == b"{}"
    missing = route_post("/upload", "text/plain", b"", tmp_path, now=when)
    assert missing == (400, {"ok": False, "error": "缺少文件"})
    other = route_post("/files", "text/plain", b"", tmp_path, now=when)
    assert other == (404, {"ok": False, "error": "未找到文件"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_guide_server.py::test_resolve_static_serves_index_and_rejects_escape -q`

Expected: FAIL，`ImportError: cannot import name 'resolve_static'`

- [ ] **Step 3: Write minimal implementation**

把 `src/web/server.py` 的 import 区扩展为：

```python
from __future__ import annotations

import json
import re
from datetime import datetime
from email import message_from_bytes
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
```

在 `MAX_UPLOAD_BYTES` 下方增加：

```python
HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "web"
UPLOAD_DIR = ROOT / "uploads"

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
```

在文件末尾、`handle_upload` 之后追加：

```python
def resolve_static(web_root: Path, url_path: str) -> Path | None:
    raw_path = unquote(urlparse(url_path).path)
    if raw_path in {"", "/"}:
        index = (web_root / "index.html").resolve()
        return index if index.is_file() else None
    relative = raw_path.lstrip("/\\")
    if not relative or ":" in relative:
        return None
    parts = PurePosixPath(relative).parts
    if ".." in parts:
        return None
    candidate = (web_root / relative).resolve()
    try:
        candidate.relative_to(web_root.resolve())
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def parse_upload(content_type: str, body: bytes) -> tuple[str | None, bytes | None]:
    if "multipart/form-data" not in content_type.lower():
        return None, None
    header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
    message = message_from_bytes(header + body, policy=default)
    if not message.is_multipart():
        return None, None
    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") != "file":
            continue
        payload = part.get_payload(decode=True)
        return part.get_filename(), b"" if payload is None else payload
    return None, None


def route_post(
    path: str,
    content_type: str,
    body: bytes,
    upload_dir: Path,
    now: datetime | None = None,
) -> tuple[int, dict]:
    if urlparse(path).path != "/upload":
        return 404, {"ok": False, "error": "未找到文件"}
    filename, content = parse_upload(content_type, body)
    return handle_upload(upload_dir, filename, content, now=now)


class SkillGuideHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        target = resolve_static(WEB_ROOT, self.path)
        if target is None:
            self._send_json(404, {"ok": False, "error": "未找到文件"})
            return
        payload = target.read_bytes()
        content_type = _CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_UPLOAD_BYTES + 1024 * 1024:
            self._send_json(400, {"ok": False, "error": "文件超过 5MB 上限"})
            return
        raw = self.rfile.read(length) if length else b""
        status, payload = route_post(
            self.path,
            self.headers.get("Content-Type", ""),
            raw,
            UPLOAD_DIR,
        )
        self._send_json(status, payload)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), SkillGuideHandler)
    print(f"http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_guide_server.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/web/server.py tests/unit/test_skill_guide_server.py
git commit -m "增加本机流程介绍服务"
```

---

### Task 4: 介绍页

**Files:**
- Create: `web/index.html`
- Create: `web/styles.css`
- Create: `web/app.js`
- Modify: `tests/unit/test_skill_guide_server.py`

**Interfaces:**
- Consumes: `POST /upload` 的 JSON 字段 `ok`、`saved_as`、`skill_name`、`skill_label`、`hint`、`error`
- Produces: `GET /` 可返回的介绍页。上传控件字段名是 `file`，没有 `multiple`。窄屏断点是 `720px`

页头这句话必须原样出现：`这是给人看的流程介绍，脚本仍由人在 Cursor 里让 Skill 去写。`

主路径只放前三步，并标成第 1、2、3 步。后五步放在「旁路」里，卡片上不写 4 到 8。每张卡片都包含：做什么、输入、输出、在 Cursor 里怎么说、Skill 名。

- [ ] **Step 1: Write the failing test**

在 `tests/unit/test_skill_guide_server.py` 末尾追加：

```python
ROOT = Path(__file__).resolve().parents[2]


def test_guide_page_lists_skills_and_upload_field():
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert "这是给人看的流程介绍，脚本仍由人在 Cursor 里让 Skill 去写。" in html
    for label in (
        "需求解析",
        "用例结构化",
        "脚本编织",
        "脚本修复",
        "接口探针",
        "回归管理",
        "缺陷分析",
        "日报生成",
    ):
        assert label in html
    for skill_name in (
        "parse-requirements",
        "structure-cases",
        "weave-scripts",
        "fix-scripts",
        "probe-apis",
        "manage-regression",
        "analyze-defects",
        "write-daily-report",
    ):
        assert skill_name in html
    assert 'name="file"' in html
    assert "multiple" not in html
    assert 'href="/styles.css"' in html
    assert 'src="/app.js"' in html
    assert "@media (max-width: 720px)" in css
    assert "/upload" in script
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_guide_server.py::test_guide_page_lists_skills_and_upload_field -q`

Expected: FAIL，`FileNotFoundError`，因为 `web/index.html` 还不存在。

- [ ] **Step 3: Write minimal implementation**

写入 `web/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Skill 流程介绍</title>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <header class="page-header">
    <p class="eyebrow">playwright-layered-qa</p>
    <h1>Skill 流程介绍</h1>
    <p class="lede">这是给人看的流程介绍，脚本仍由人在 Cursor 里让 Skill 去写。</p>
  </header>

  <main>
    <section>
      <h2>主路径</h2>
      <ol class="steps">
        <li class="card">
          <p class="kicker">第 1 步</p>
          <h3>需求解析</h3>
          <p class="skill-name">parse-requirements</p>
          <p>把需求文档或一句话整理成给人评审的 Markdown，不写自动化脚本。</p>
          <dl>
            <div><dt>输入</dt><dd>需求文档或一句话</dd></div>
            <div><dt>输出</dt><dd>examples/&lt;site&gt;/requirement.md</dd></div>
            <div><dt>怎么说</dt><dd>需求解析、/需求</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">第 2 步</p>
          <h3>用例结构化</h3>
          <p class="skill-name">structure-cases</p>
          <p>把评审过的 Markdown 收成 assets/ 下的 YAML。步骤仍是自然语言，不会被执行。</p>
          <dl>
            <div><dt>输入</dt><dd>上一步的 Markdown</dd></div>
            <div><dt>输出</dt><dd>assets/ 下的 YAML</dd></div>
            <div><dt>怎么说</dt><dd>用例结构化、/结构化</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">第 3 步</p>
          <h3>脚本编织</h3>
          <p class="skill-name">weave-scripts</p>
          <p>按 YAML 用例生成 pytest + Playwright 脚本骨架，沿用 BasePage、Config 和 NetworkInterceptor。</p>
          <dl>
            <div><dt>输入</dt><dd>assets/cases</dd></div>
            <div><dt>输出</dt><dd>pytest + Playwright 脚本骨架</dd></div>
            <div><dt>怎么说</dt><dd>脚本编织、/编织</dd></div>
          </dl>
        </li>
      </ol>
    </section>

    <section>
      <h2>旁路</h2>
      <p class="section-note">这五步按手头的材料选用，没有固定先后。</p>
      <ul class="steps side">
        <li class="card">
          <p class="kicker">旁路</p>
          <h3>脚本修复</h3>
          <p class="skill-name">fix-scripts</p>
          <p>根据 traceback 判断定位器、断言、时序或环境问题，只做最小修复。</p>
          <dl>
            <div><dt>输入</dt><dd>traceback、失败截图</dd></div>
            <div><dt>输出</dt><dd>最小修复说明</dd></div>
            <div><dt>怎么说</dt><dd>脚本修复</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">旁路</p>
          <h3>接口探针</h3>
          <p class="skill-name">probe-apis</p>
          <p>把接口文档或抓包整理成给人评审的接口报告，不直接生成脚本。</p>
          <dl>
            <div><dt>输入</dt><dd>接口文档或抓包 JSON</dd></div>
            <div><dt>输出</dt><dd>给人评审的接口报告</dd></div>
            <div><dt>怎么说</dt><dd>/探针、接口探针</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">旁路</p>
          <h3>回归管理</h3>
          <p class="skill-name">manage-regression</p>
          <p>按这次改动列出优先要回归的检查项和执行顺序。</p>
          <dl>
            <div><dt>输入</dt><dd>变更说明</dd></div>
            <div><dt>输出</dt><dd>回归清单</dd></div>
            <div><dt>怎么说</dt><dd>回归管理、/回归</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">旁路</p>
          <h3>缺陷分析</h3>
          <p class="skill-name">analyze-defects</p>
          <p>根据失败日志、截图或拦截 JSON 写缺陷报告，并说明原因判断。</p>
          <dl>
            <div><dt>输入</dt><dd>失败日志、截图、拦截 JSON</dd></div>
            <div><dt>输出</dt><dd>缺陷报告</dd></div>
            <div><dt>怎么说</dt><dd>缺陷分析</dd></div>
          </dl>
        </li>
        <li class="card">
          <p class="kicker">旁路</p>
          <h3>日报生成</h3>
          <p class="skill-name">write-daily-report</p>
          <p>把当天的需求、YAML、脚本和示例运行收成一份测试日报。</p>
          <dl>
            <div><dt>输入</dt><dd>当日工作笔记</dd></div>
            <div><dt>输出</dt><dd>测试日报</dd></div>
            <div><dt>怎么说</dt><dd>日报生成</dd></div>
          </dl>
        </li>
      </ul>
    </section>

    <section class="upload-panel">
      <h2>归档一个文件</h2>
      <p class="section-note">文件只保存在本机 uploads/。页面不读取内容，也不执行 Skill。</p>
      <form id="upload-form">
        <label class="dropzone" id="dropzone">
          <input id="file" name="file" type="file">
          <span id="drop-label">点击选择，或把文件拖到这里</span>
        </label>
        <button type="submit">上传并查看建议</button>
      </form>
      <div id="result" class="result" hidden></div>
    </section>
  </main>
  <script src="/app.js"></script>
</body>
</html>
```

写入 `web/styles.css`：

```css
:root {
  color-scheme: light;
  --ink: #1c1917;
  --muted: #57534e;
  --line: #d6d3d1;
  --paper: #f6f3ee;
  --card: #fffdf8;
  --accent: #0f6e56;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  background: var(--paper);
  line-height: 1.5;
}

.page-header,
main {
  width: min(1080px, calc(100% - 32px));
  margin: 0 auto;
}

.page-header { padding: 40px 0 8px; }

.eyebrow {
  margin: 0;
  color: var(--accent);
  font-size: 0.85rem;
  letter-spacing: 0.04em;
}

h1 { margin: 8px 0; font-size: 2rem; }

h2 { margin: 28px 0 12px; font-size: 1.25rem; }

.lede,
.section-note { color: var(--muted); }

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.side { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }

.card {
  padding: 16px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
}

.kicker,
.skill-name {
  margin: 0;
  color: var(--accent);
  font-size: 0.85rem;
}

.card h3 { margin: 4px 0 8px; }

.card dl { margin: 12px 0 0; }

.card dl div { margin-top: 6px; }

.card dt {
  display: inline;
  color: var(--muted);
}

.card dt::after { content: "："; }

.card dd { display: inline; margin: 0; }

.upload-panel { padding-bottom: 48px; }

.dropzone {
  display: grid;
  place-items: center;
  min-height: 140px;
  margin-bottom: 12px;
  border: 1.5px dashed var(--accent);
  border-radius: 12px;
  background: var(--card);
  cursor: pointer;
}

.dropzone.drag { background: #e7f5f0; }

.dropzone input { max-width: 100%; }

button {
  border: 0;
  border-radius: 999px;
  padding: 10px 18px;
  background: var(--accent);
  color: white;
  font: inherit;
  cursor: pointer;
}

.result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 12px;
  background: var(--card);
  border: 1px solid var(--line);
}

.result.error { border-color: #b45309; }

.result p { margin: 6px 0; }

@media (max-width: 720px) {
  .steps { grid-template-columns: 1fr; }
}
```

写入 `web/app.js`：

```javascript
const form = document.querySelector("#upload-form");
const input = document.querySelector("#file");
const dropzone = document.querySelector("#dropzone");
const dropLabel = document.querySelector("#drop-label");
const result = document.querySelector("#result");

function showResult(html, isError) {
  result.hidden = false;
  result.classList.toggle("error", isError);
  result.innerHTML = html;
}

function escapeText(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

input.addEventListener("change", () => {
  const file = input.files && input.files[0];
  dropLabel.textContent = file ? file.name : "点击选择，或把文件拖到这里";
});

["dragenter", "dragover"].forEach((name) => {
  dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.add("drag");
  });
});

["dragleave", "drop"].forEach((name) => {
  dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.remove("drag");
  });
});

dropzone.addEventListener("drop", (event) => {
  const files = event.dataTransfer && event.dataTransfer.files;
  if (!files || files.length === 0) {
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(files[0]);
  input.files = transfer.files;
  dropLabel.textContent = files.length > 1
    ? files[0].name + "（一次只能上传一个文件，已使用第一个）"
    : files[0].name;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = input.files && input.files[0];
  if (!file) {
    showResult("<p>请先选择一个文件。</p>", true);
    return;
  }
  const body = new FormData();
  body.append("file", file);
  let response;
  try {
    response = await fetch("/upload", { method: "POST", body });
  } catch (error) {
    showResult("<p>上传失败，请确认页面是从本机服务打开的。</p>", true);
    return;
  }
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    showResult("<p>" + escapeText(payload.error || "上传失败") + "</p>", true);
    return;
  }
  const skill = payload.skill_label
    ? escapeText(payload.skill_label) + "（" + escapeText(payload.skill_name) + "）"
    : "未匹配到 Skill";
  showResult(
    "<p>已保存：" + escapeText(payload.saved_as) + "</p>" +
      "<p>建议：" + skill + "</p>" +
      "<p id='hint'>" + escapeText(payload.hint) + "</p>" +
      "<button type='button' id='copy-hint'>复制提示</button>",
    false
  );
  document.querySelector("#copy-hint").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(payload.hint);
      document.querySelector("#copy-hint").textContent = "已复制";
    } catch (error) {
      document.querySelector("#copy-hint").textContent = "复制失败，请手动选择文字";
    }
  });
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_guide_server.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/styles.css web/app.js tests/unit/test_skill_guide_server.py
git commit -m "增加 Skill 流程介绍页"
```

---

### Task 5: 仓库说明与启动核对

**Files:**
- Create: `uploads/.gitkeep`
- Modify: `.gitignore`
- Modify: `README.md`

**Interfaces:**
- Consumes: `python -m src.web.server` 与 `GET /`
- Produces: 忽略 `uploads/*` 但保留 `uploads/.gitkeep`；README 写明启动方式和页面边界

- [ ] **Step 1: Write the failing test**

在 `tests/unit/test_skill_guide_server.py` 末尾追加：

```python
def test_uploads_are_ignored_except_gitkeep():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "uploads/*" in gitignore
    assert "!uploads/.gitkeep" in gitignore
    assert (ROOT / "uploads" / ".gitkeep").is_file()
    assert "python -m src.web.server" in readme
    assert "http://127.0.0.1:8765" in readme
    assert "GUI Runner" not in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_guide_server.py::test_uploads_are_ignored_except_gitkeep -q`

Expected: FAIL，断言 `uploads/*` 不在 `.gitignore` 中。

- [ ] **Step 3: Write minimal implementation**

创建空文件 `uploads/.gitkeep`。

在 `.gitignore` 的 `reports/` 下一行插入：

```
uploads/*
!uploads/.gitkeep
```

在 `README.md` 的「## 目录」之前插入：

```markdown
## 流程介绍页

```bash
python -m src.web.server
```

浏览器打开 http://127.0.0.1:8765 。页面介绍 8 个 Skill 怎么用。上传的文件归档到 `uploads/`，并提示下一步在 Cursor 里说什么。页面不执行 Skill，不跑测试。
```

把「后续可补」里的 `- GUI Runner` 换成：

```markdown
- 流程介绍页已提供（`python -m src.web.server`）。它只介绍 Skill 并归档上传文件，不执行 YAML，不跑测试
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit -q`

Expected: PASS，包含原有单测和 `test_skill_guide_server.py`。

启动服务后在浏览器里核对页面，而不是只看单测：

```bash
python -m src.web.server
```

Expected: 终端打印 `http://127.0.0.1:8765`。

打开该地址，确认主路径三张卡片和旁路五张卡片都在。选择一个小于 5MB 的 `.md` 文件并上传，页面仍停在原地址，结果区出现 `uploads/` 开头的路径、`需求解析` 和 `parse-requirements`。再拖入一个 `.json` 文件，结果改为 `接口探针`。用浏览器开发者工具或页面结果确认失败时不会跳转：不选文件就点上传，上传区显示「请先选择一个文件。」把窗口缩到 720px 以下，步骤卡片变成一列。核对完成后停掉服务。

然后在仓库根目录执行：

```bash
python -c "import src.web.server"
```

Expected: 进程退出码 0，没有输出。若失败且原因是找不到包，只新增空文件 `src/web/__init__.py`，再执行一次上面的命令。不要给其他目录补 `__init__.py`。

- [ ] **Step 5: Commit**

```bash
git add .gitignore README.md uploads/.gitkeep src/web/__init__.py
git commit -m "说明如何打开流程介绍页"
```

`src/web/__init__.py` 只有在上一步实际创建时才加入。没有这个文件时不要把它写进 `git add`。

---

## Spec coverage

- 本机介绍页和 8 步文案：Task 4
- 上传归档、5MB、文件名清洗、重名后缀、扩展名建议：Task 1、Task 2
- multipart、`/upload`、静态文件和 `..` 拒绝：Task 3
- 只绑定本机、不回显内容、不执行文件：Task 3 的 handler
- `.gitignore`、`.gitkeep`、README：Task 5
- 不解析文件内容、不新增依赖：没有对应实现任务，计划中也没有这些行为
