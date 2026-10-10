"""Local read-only workbench for requirements, cases, and questions."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Mapping
from urllib.parse import unquote, urlparse

from dotenv import dotenv_values

from src.yaml_runner.schema import (
    CaseSchemaError,
    load_cases,
    load_questions,
    load_requirements,
)

HOST = "127.0.0.1"
PORT = 8765

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = REPO_ROOT / "web"
ASSETS_DIR = REPO_ROOT / "assets"
REPORTS_DIR = REPO_ROOT / "reports"
CAPTURES_DIR = REPORTS_DIR / "api-captures"
REPORT_SUFFIXES = {".html", ".md"}
ENV_PATH = REPO_ROOT / ".env"

_LOADERS = {
    "requirements": load_requirements,
    "cases": load_cases,
    "questions": load_questions,
}

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


def valid_module_name(name: str) -> bool:
    if not name or name in {".", ".."}:
        return False
    return not any(char in name for char in "/\\:\0")


def config_status(env: Mapping[str, str]) -> dict[str, object]:
    """Report whether runtime settings exist, without returning their values."""

    def present(name: str) -> bool:
        return bool(str(env.get(name) or "").strip())

    db_flags = [present("DB_HOST"), present("DB_USER"), present("DB_NAME")]
    if all(db_flags):
        db_state = "configured"
    elif any(db_flags):
        db_state = "partial"
    else:
        db_state = "absent"
    return {"base_url_configured": present("BASE_URL"), "db": db_state}


def config_status_from_file(
    env_path: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    merged: dict[str, str] = {}
    if env_path.is_file():
        for key, value in dotenv_values(env_path).items():
            if key and value is not None:
                merged[key] = value
    source = os.environ if environ is None else environ
    for key, value in source.items():
        if value:
            merged[key] = value
    return config_status(merged)


def list_reports(directory: Path) -> list[dict[str, str]]:
    if not directory.is_dir():
        return []
    items = []
    for path in directory.iterdir():
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in REPORT_SUFFIXES:
            continue
        items.append({"name": path.name, "kind": _report_kind(path.name)})
    return sorted(items, key=lambda item: item["name"])


def resolve_report(reports_dir: Path, url_path: str) -> Path | None:
    prefix = "/reports/"
    if not url_path.startswith(prefix) or "\\" in url_path:
        return None
    name = url_path[len(prefix):]
    if not name or "/" in name or name in {".", ".."}:
        return None
    if Path(name).suffix.lower() not in REPORT_SUFFIXES:
        return None
    root = reports_dir.resolve()
    candidate = (root / name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.parent != root or not candidate.is_file():
        return None
    return candidate


def list_captures(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    names = [
        path.name
        for path in directory.iterdir()
        if path.is_file() and not path.name.startswith(".")
    ]
    return sorted(names)


def load_index(assets_dir: Path) -> tuple[dict[str, dict[str, list[dict]]], list[str]]:
    buckets: dict[str, dict[str, list[dict]]] = {}
    errors: list[str] = []

    def bucket(module: str) -> dict[str, list[dict]]:
        if module not in buckets:
            buckets[module] = {"requirements": [], "cases": [], "questions": []}
        return buckets[module]

    for kind, loader in _LOADERS.items():
        directory = assets_dir / kind
        if not directory.is_dir():
            continue
        files = sorted(
            (
                path
                for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
            ),
            key=lambda path: path.name,
        )
        for path in files:
            try:
                items = loader(path)
            except CaseSchemaError as exc:
                errors.append(f"{_display_path(path, assets_dir)}: {exc}")
                continue
            for item in items:
                bucket(item["module"])[kind].append(_public_item(kind, item))

    for data in buckets.values():
        data["requirements"].sort(key=lambda item: item["req_id"])
        data["cases"].sort(key=lambda item: item["case_id"])
        data["questions"].sort(key=lambda item: item["question_id"])
    return buckets, errors


def summarize(index: dict[str, dict[str, list[dict]]], errors: list[str]) -> dict:
    modules = []
    for name in sorted(index):
        data = index[name]
        automation = {"automated": 0, "pending": 0, "manual": 0}
        for case in data["cases"]:
            status = case["automation"]["status"]
            if status in automation:
                automation[status] += 1
        modules.append(
            {
                "module": name,
                "requirement_count": len(data["requirements"]),
                "case_count": len(data["cases"]),
                "question_count": len(data["questions"]),
                "open_question_count": sum(
                    1 for item in data["questions"] if item["status"] == "open"
                ),
                "automation": automation,
            }
        )
    return {"modules": modules, "errors": errors}


def script_catalog(index: dict[str, dict[str, list[dict]]]) -> dict:
    grouped: dict[str, list[dict]] = {}
    unscripted: list[dict] = []
    for module in sorted(index):
        for case in index[module]["cases"]:
            nodeid = case["automation"].get("pytest_nodeid")
            record = {
                "module": module,
                "case_id": case["case_id"],
                "title": case["title"],
                "status": case["automation"]["status"],
                "pytest_nodeid": nodeid if isinstance(nodeid, str) and nodeid.strip() else None,
            }
            if record["pytest_nodeid"] and "::" in record["pytest_nodeid"]:
                path, test_name = record["pytest_nodeid"].split("::", 1)
                record["test_name"] = test_name
                grouped.setdefault(path, []).append(record)
            else:
                unscripted.append(record)
    return {
        "files": [{"path": path, "tests": grouped[path]} for path in sorted(grouped)],
        "unscripted": unscripted,
    }


def module_detail(
    index: dict[str, dict[str, list[dict]]],
    module: str,
) -> dict | None:
    data = index.get(module)
    if data is None:
        return None
    return {
        "module": module,
        "requirements": data["requirements"],
        "cases": data["cases"],
        "questions": data["questions"],
        "link_warnings": _link_warnings(module, index),
    }


def resolve_static(web_dir: Path, url_path: str) -> Path | None:
    if url_path in {"", "/"}:
        url_path = "/index.html"
    if not url_path.startswith("/") or "\\" in url_path:
        return None
    parts = Path(url_path.lstrip("/")).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None
    root = web_dir.resolve()
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def handle_get(
    raw_path: str,
    *,
    assets_dir: Path,
    web_dir: Path,
    captures_dir: Path,
    reports_dir: Path,
    env_path: Path,
    environ: Mapping[str, str] | None = None,
) -> tuple[int, str, bytes]:
    path = unquote(urlparse(raw_path).path)
    if path == "/api/catalog":
        index, errors = load_index(assets_dir)
        return _json(200, summarize(index, errors))
    if path == "/api/config":
        return _json(200, config_status_from_file(env_path, environ))
    if path == "/api/captures":
        return _json(200, {"files": list_captures(captures_dir)})
    if path == "/api/reports":
        return _json(200, {"files": list_reports(reports_dir)})
    report_path = resolve_report(reports_dir, path)
    if report_path is not None:
        content_type = _CONTENT_TYPES.get(report_path.suffix.lower(), "text/plain; charset=utf-8")
        if report_path.suffix.lower() == ".md":
            content_type = "text/plain; charset=utf-8"
        return 200, content_type, report_path.read_bytes()
    if path == "/api/scripts":
        index, _errors = load_index(assets_dir)
        return _json(200, script_catalog(index))
    if path.startswith("/api/modules/"):
        module = path.removeprefix("/api/modules/")
        if "/" in module or not valid_module_name(module):
            return _json(400, {"ok": False, "error": "模块名无效"})
        index, _errors = load_index(assets_dir)
        detail = module_detail(index, module)
        if detail is None:
            return _json(404, {"ok": False, "error": "没有这个模块"})
        return _json(200, detail)

    static_path = resolve_static(web_dir, path)
    if static_path is None:
        return 404, "text/plain; charset=utf-8", "未找到页面".encode("utf-8")
    content_type = _CONTENT_TYPES.get(static_path.suffix.lower(), "application/octet-stream")
    return 200, content_type, static_path.read_bytes()


class WorkbenchHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        status, content_type, body = handle_get(
            self.path,
            assets_dir=ASSETS_DIR,
            web_dir=WEB_DIR,
            captures_dir=CAPTURES_DIR,
            reports_dir=REPORTS_DIR,
            env_path=ENV_PATH,
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError):
            return

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), WorkbenchHandler)
    print(f"分层测试台  http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _json(status: int, payload: dict) -> tuple[int, str, bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return status, "application/json; charset=utf-8", body


def _report_kind(name: str) -> str:
    if name.lower().endswith(".html"):
        return "pytest"
    if name.startswith("测试日报"):
        return "daily"
    if name.startswith("缺陷报告"):
        return "defect"
    if name.startswith("脚本修复"):
        return "fix"
    if name.startswith("回归"):
        return "regression"
    return "markdown"


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _public_item(kind: str, item: dict) -> dict:
    if kind == "requirements":
        return _public_requirement(item)
    if kind == "cases":
        return _public_case(item)
    return _public_question(item)


def _public_requirement(item: dict) -> dict:
    payload: dict = {
        "req_id": item["req_id"],
        "module": item["module"],
        "title": item["title"],
        "type": item["type"],
        "description": item["description"],
        "source_ref": item["source_ref"],
        "linked_case_ids": list(item.get("linked_case_ids") or []),
    }
    priority = item.get("priority")
    if isinstance(priority, str) and priority.strip():
        payload["priority"] = priority.strip()
    tags = item.get("tags")
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        payload["tags"] = tags
    return payload


def _public_case(item: dict) -> dict:
    automation = item["automation"]
    return {
        "case_id": item["case_id"],
        "module": item["module"],
        "title": item["title"],
        "type": item["type"],
        "preconditions": list(item["preconditions"]),
        "steps": list(item["steps"]),
        "expected_results": list(item["expected_results"]),
        "source_ref": item["source_ref"],
        "requirement_ids": list(item["requirement_ids"]),
        "automation": {
            "status": automation["status"],
            "pytest_nodeid": automation.get("pytest_nodeid"),
        },
    }


def _public_question(item: dict) -> dict:
    payload = {
        "question_id": item["question_id"],
        "module": item["module"],
        "description": item["description"],
        "suggested_confirmation": item["suggested_confirmation"],
        "status": item["status"],
        "source_ref": item["source_ref"],
    }
    resolution = item.get("resolution")
    if isinstance(resolution, str) and resolution.strip():
        payload["resolution"] = resolution.strip()
    return payload


def _link_warnings(module: str, index: dict[str, dict[str, list[dict]]]) -> list[str]:
    known_reqs = {
        item["req_id"]
        for data in index.values()
        for item in data["requirements"]
    }
    known_cases = {
        item["case_id"] for data in index.values() for item in data["cases"]
    }
    warnings: list[str] = []
    data = index[module]
    for case in data["cases"]:
        for req_id in case["requirement_ids"]:
            if req_id not in known_reqs:
                warnings.append(f"{case['case_id']} 指向了不存在的需求 {req_id}")
    for requirement in data["requirements"]:
        for case_id in requirement["linked_case_ids"]:
            if case_id not in known_cases:
                warnings.append(f"{requirement['req_id']} 指向了不存在的用例 {case_id}")
    return warnings


if __name__ == "__main__":
    main()
