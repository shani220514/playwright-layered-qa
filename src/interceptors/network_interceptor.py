from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class NetworkInterceptor:
    """Capture XHR/fetch requests and pair them with responses."""

    def __init__(self, output_dir: str | Path = "reports/api-captures"):
        self.output_dir = Path(output_dir)
        self.captured = []
        self._pending = {}

    def start_capture(self, page) -> None:
        page.on("request", self._on_request)
        page.on("response", self._on_response)

    def records(self) -> list[dict]:
        return list(self.captured)

    def clear(self) -> None:
        self.captured = []
        self._pending = {}

    def save(self, filename: str = "captured_apis.json") -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        path.write_text(
            json.dumps(self.captured, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def _on_request(self, request) -> None:
        if getattr(request, "resource_type", "") not in {"xhr", "fetch"}:
            return
        parsed = urlparse(request.url)
        record = {
            "method": request.method,
            "url": request.url,
            "path": parsed.path,
            "query_params": parse_qs(parsed.query),
            "body": _request_body(request),
            "headers": dict(getattr(request, "headers", {}) or {}),
            "request_time": datetime.now().isoformat(timespec="seconds"),
            "response": None,
        }
        self.captured.append(record)
        self._pending[id(request)] = record

    def _on_response(self, response) -> None:
        request = response.request
        record = self._pending.pop(id(request), None)
        if record is None:
            return
        record["response"] = {
            "status": response.status,
            "headers": dict(getattr(response, "headers", {}) or {}),
            "body": _response_body(response),
        }


def _request_body(request):
    try:
        return request.post_data_json
    except Exception:
        return getattr(request, "post_data", None)


def _response_body(response):
    try:
        return response.json()
    except Exception:
        try:
            return response.text()
        except Exception:
            return None
