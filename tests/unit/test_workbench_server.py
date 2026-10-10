import json
from pathlib import Path

import pytest

from src.web.server import (
    HOST,
    PORT,
    config_status,
    config_status_from_file,
    handle_get,
    list_captures,
    list_reports,
    load_index,
    module_detail,
    script_catalog,
    summarize,
    valid_module_name,
)

REPO_ASSETS = Path(__file__).resolve().parents[2] / "assets"


def test_server_listens_on_loopback_only():
    assert HOST == "127.0.0.1"
    assert PORT == 8765


def test_catalog_groups_modules_and_counts(tmp_path):
    assets = tmp_path / "assets"
    _write_requirement(assets, "one.yaml", "REQ-A-001", "alpha", "打开首页")
    _write_requirement(assets, "two.yaml", "REQ-A-002", "alpha", "点击热搜")
    _write_requirement(assets, "beta.yaml", "REQ-B-001", "beta", "登录")
    _write_case(assets, "cases.yaml", "TC-A-001", "alpha", "REQ-A-001", "automated", "tests/a.py::test_a")
    _write_case(assets, "manual.yaml", "TC-A-002", "alpha", "REQ-A-002", "manual", None)
    _write_question(assets, "open.yaml", "Q-A-001", "alpha", "open", None)
    _write_question(assets, "closed.yaml", "Q-B-001", "beta", "closed", "已确认")

    index, errors = load_index(assets)
    catalog = summarize(index, errors)

    assert errors == []
    by_name = {item["module"]: item for item in catalog["modules"]}
    assert by_name["alpha"]["requirement_count"] == 2
    assert by_name["alpha"]["case_count"] == 2
    assert by_name["alpha"]["open_question_count"] == 1
    assert by_name["alpha"]["automation"] == {"automated": 1, "pending": 0, "manual": 1}
    assert by_name["beta"]["requirement_count"] == 1
    assert by_name["beta"]["question_count"] == 1
    assert by_name["beta"]["open_question_count"] == 0


def test_invalid_yaml_is_reported_without_dropping_other_files(tmp_path):
    assets = tmp_path / "assets"
    _write_requirement(assets, "ok.yaml", "REQ-A-001", "alpha", "打开首页")
    bad = assets / "requirements" / "bad.yaml"
    bad.write_text("requirements:\n  - title: broken\n", encoding="utf-8")

    index, errors = load_index(assets)

    assert "alpha" in index
    assert len(errors) == 1
    assert "requirements/bad.yaml" in errors[0]


def test_script_catalog_groups_nodeids_and_leaves_unscripted_cases(tmp_path):
    assets = tmp_path / "assets"
    _write_requirement(assets, "req.yaml", "REQ-A-001", "alpha", "打开首页")
    _write_case(assets, "auto.yaml", "TC-A-001", "alpha", "REQ-A-001", "automated", "tests/examples/test_a.py::test_open")
    _write_case(assets, "manual.yaml", "TC-A-002", "alpha", "REQ-A-001", "manual", None)

    index, _errors = load_index(assets)
    catalog = script_catalog(index)

    assert catalog["files"] == [
        {
            "path": "tests/examples/test_a.py",
            "tests": [
                {
                    "module": "alpha",
                    "case_id": "TC-A-001",
                    "title": "用例",
                    "status": "automated",
                    "pytest_nodeid": "tests/examples/test_a.py::test_open",
                    "test_name": "test_open",
                }
            ],
        }
    ]
    assert catalog["unscripted"][0]["case_id"] == "TC-A-002"
    assert catalog["unscripted"][0]["pytest_nodeid"] is None


def test_module_detail_flags_unknown_links(tmp_path):
    assets = tmp_path / "assets"
    _write_requirement(assets, "req.yaml", "REQ-A-001", "alpha", "打开首页", linked="TC-MISSING")
    _write_case(assets, "case.yaml", "TC-A-001", "alpha", "REQ-MISSING", "manual", None)

    index, _errors = load_index(assets)
    detail = module_detail(index, "alpha")

    assert detail is not None
    assert detail["cases"][0]["automation"]["pytest_nodeid"] is None
    assert "TC-A-001 指向了不存在的需求 REQ-MISSING" in detail["link_warnings"]
    assert "REQ-A-001 指向了不存在的用例 TC-MISSING" in detail["link_warnings"]
    assert module_detail(index, "missing") is None


def test_config_status_hides_values():
    secret = "super-secret-password"
    url = "https://www.baidu.com/"
    status = config_status(
        {
            "BASE_URL": url,
            "DB_HOST": "10.0.0.8",
            "DB_USER": "root",
            "DB_NAME": "qa",
            "DB_PASSWORD": secret,
        }
    )
    blob = json.dumps(status)
    assert secret not in blob
    assert "10.0.0.8" not in blob
    assert url not in blob
    assert status == {"base_url_configured": True, "db": "configured"}
    assert config_status({"DB_HOST": "db.internal"})["db"] == "partial"
    assert config_status({})["db"] == "absent"


def test_config_status_reads_dotenv_without_exporting_it(tmp_path, monkeypatch):
    monkeypatch.delenv("BASE_URL", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("BASE_URL=https://www.baidu.com/\nDB_PASSWORD=secret\n", encoding="utf-8")

    status = config_status_from_file(env_path, environ={})

    assert status["base_url_configured"] is True
    assert "secret" not in json.dumps(status)
    assert "BASE_URL" not in __import__("os").environ


def test_list_reports_keeps_html_and_markdown_only(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "baidu-examples-report.html").write_text("<html>ok</html>", encoding="utf-8")
    (reports / "缺陷报告_20261010.md").write_text("# 缺陷", encoding="utf-8")
    (reports / "note.txt").write_text("no", encoding="utf-8")
    (reports / "api-captures").mkdir()
    (reports / "api-captures" / "a.json").write_text("{}", encoding="utf-8")

    listed = list_reports(reports)

    assert [item["name"] for item in listed] == ["baidu-examples-report.html", "缺陷报告_20261010.md"]
    assert listed[0]["kind"] == "pytest"
    assert listed[1]["kind"] == "defect"


def test_report_download_rejects_paths_outside_reports(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "ok.html").write_text("<p>报告</p>", encoding="utf-8")
    (tmp_path / "secret.html").write_text("TOP-SECRET", encoding="utf-8")

    status, content_type, body = _get("/reports/ok.html", tmp_path)
    assert status == 200
    assert "text/html" in content_type
    assert "报告".encode() in body

    status, _, body = _get("/reports/../secret.html", tmp_path)
    assert status == 404
    assert b"TOP-SECRET" not in body

    payload = json.loads(_get("/api/reports", tmp_path)[2])
    assert payload["files"][0]["name"] == "ok.html"


def test_list_captures_returns_file_names_only(tmp_path):
    captures = tmp_path / "api-captures"
    captures.mkdir()
    (captures / "b.har").write_text('{"cookie":"secret"}', encoding="utf-8")
    (captures / "a.json").write_text("{}", encoding="utf-8")
    (captures / ".hidden").write_text("nope", encoding="utf-8")
    (captures / "subdir").mkdir()

    assert list_captures(captures) == ["a.json", "b.har"]
    assert list_captures(tmp_path / "missing") == []


def test_handle_get_serves_index_and_catalog(tmp_path):
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<!doctype html><title>分层测试台</title>", encoding="utf-8")
    assets = tmp_path / "assets"
    _write_requirement(assets, "req.yaml", "REQ-A-001", "alpha", "打开首页")

    status, content_type, body = _get("/", tmp_path)
    assert status == 200
    assert "text/html" in content_type
    assert "分层测试台".encode() in body

    status, content_type, body = _get("/api/catalog", tmp_path)
    payload = json.loads(body)
    assert status == 200
    assert "application/json" in content_type
    assert payload["modules"][0]["module"] == "alpha"

    status, _, body = _get("/api/modules/alpha", tmp_path)
    assert status == 200
    assert json.loads(body)["requirements"][0]["req_id"] == "REQ-A-001"

    status, _, body = _get("/api/modules/missing", tmp_path)
    assert status == 404
    assert json.loads(body)["ok"] is False


@pytest.mark.parametrize(
    "raw",
    ["/../secret.txt", "/api/modules/../secret", "/api/modules/a/b", r"/api/modules/a\b"],
)
def test_handle_get_rejects_path_escape(tmp_path, raw):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET", encoding="utf-8")
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("ok", encoding="utf-8")

    status, _, body = _get(raw, tmp_path)

    assert status in {400, 404}
    assert b"TOP-SECRET" not in body


def test_real_assets_catalog_loads_known_modules():
    index, errors = load_index(REPO_ASSETS)
    catalog = summarize(index, errors)
    names = {item["module"] for item in catalog["modules"]}
    assert errors == []
    assert {"baidu_home", "baidu_hot_entry", "baidu_login"} <= names


@pytest.mark.parametrize("name,expected", [("baidu_home", True), ("", False), ("..", False), ("a/b", False)])
def test_valid_module_name(name, expected):
    assert valid_module_name(name) is expected


def _get(path: str, root: Path):
    return handle_get(
        path,
        assets_dir=root / "assets",
        web_dir=root / "web",
        captures_dir=root / "captures",
        reports_dir=root / "reports",
        env_path=root / ".env",
        environ={},
    )


def _write_requirement(assets: Path, filename: str, req_id: str, module: str, title: str, linked: str | None = None):
    directory = assets / "requirements"
    directory.mkdir(parents=True, exist_ok=True)
    linked_yaml = ""
    if linked:
        linked_yaml = f"\n    linked_case_ids:\n      - {linked}"
    (directory / filename).write_text(
        f"""
requirements:
  - req_id: {req_id}
    module: {module}
    title: {title}
    type: positive
    description: 说明
    source_ref: examples/demo/requirement.md{linked_yaml}
""".strip(),
        encoding="utf-8",
    )


def _write_case(assets, filename, case_id, module, req_id, status, nodeid):
    directory = assets / "cases"
    directory.mkdir(parents=True, exist_ok=True)
    node = "null" if nodeid is None else nodeid
    (directory / filename).write_text(
        f"""
cases:
  - case_id: {case_id}
    module: {module}
    title: 用例
    type: positive
    preconditions:
      - 无
    steps:
      - 打开页面
    expected_results:
      - 页面可用
    source_ref: examples/demo/requirement.md
    requirement_ids:
      - {req_id}
    automation:
      status: {status}
      pytest_nodeid: {node}
""".strip(),
        encoding="utf-8",
    )


def _write_question(assets, filename, question_id, module, status, resolution):
    directory = assets / "questions"
    directory.mkdir(parents=True, exist_ok=True)
    resolution_yaml = f"\n    resolution: {resolution}" if resolution else ""
    (directory / filename).write_text(
        f"""
questions:
  - question_id: {question_id}
    module: {module}
    description: 需要确认的点
    suggested_confirmation: 请确认
    status: {status}
    source_ref: examples/demo/requirement.md{resolution_yaml}
""".strip(),
        encoding="utf-8",
    )
