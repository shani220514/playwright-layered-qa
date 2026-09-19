from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class NetworkInterceptor:
    """Capture XHR/fetch requests and pair them with responses."""

    def __init__(self, output_dir: str | Path = "reports/api-captures"):
        self.output_dir = Path(output_dir)
        self.captured = []
        self._pending = {}
        self.last_forwarded_url = None

    def start_capture(self, target) -> None:
        target.on("request", self._on_request)
        target.on("response", self._on_response)

    def records(self) -> list[dict]:
        return list(self.captured)

    def clear(self) -> None:
        self.captured = []
        self._pending = {}
        self.last_forwarded_url = None

    def find(self, path_substr: str) -> dict | None:
        for record in reversed(self.captured):
            if path_substr in record.get("path", "") or path_substr in record.get("url", ""):
                return record
        return None

    def save(self, filename: str = "captured_apis.json") -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        path.write_text(
            json.dumps(self.captured, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def save_failure(self, stem: str = "failure") -> Path:
        return self.save(f"{stem}_req_resp.json")

    def intercept_route(
        self,
        target,
        url_glob: str,
        *,
        delay_ms: int = 0,
        query_overrides: dict[str, str] | None = None,
    ) -> None:
        def handle(route) -> None:
            if delay_ms:
                time.sleep(delay_ms / 1000)
            url = route.request.url
            if query_overrides:
                url = rewrite_query(url, query_overrides)
            self.last_forwarded_url = url
            if url != route.request.url:
                route.continue_(url=url)
            else:
                route.continue_()

        target.route(url_glob, handle)

    def stop_intercept(self, target, url_glob: str) -> None:
        target.unroute(url_glob)

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


def rewrite_query(url: str, query_overrides: dict[str, str]) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    for key, value in query_overrides.items():
        params[key] = [str(value)]
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


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
