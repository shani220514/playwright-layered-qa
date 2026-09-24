from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

_SECRET_HEADERS = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
}
_MAX_BODY_CHARS = 65_536


class NetworkInterceptor:
    """Capture XHR/fetch requests and pair them with responses."""

    def __init__(self, output_dir: str | Path = "reports/api-captures"):
        self.output_dir = Path(output_dir)
        self.captured = []
        self.resource_types = {"xhr", "fetch"}
        self._by_id: dict[str, dict] = {}
        self._by_url: dict[tuple[str, str], list[dict]] = {}
        self._by_path: dict[tuple[str, str], list[dict]] = {}
        self._body_sources: list[tuple[dict, object]] = []
        self.last_forwarded_url = None

    def start_capture(self, target) -> None:
        target.on("request", self._on_request)
        target.on("response", self._on_response)

    def include_resource_types(self, resource_types: set[str]) -> None:
        self.resource_types.update(resource_types)

    def records(self) -> list[dict]:
        self._materialize_bodies()
        return [_public_record(record) for record in self.captured]

    def clear(self) -> None:
        self.captured = []
        self._by_id = {}
        self._by_url = {}
        self._by_path = {}
        self._body_sources = []
        self.last_forwarded_url = None

    def find(self, path_substr: str) -> dict | None:
        self._materialize_bodies()
        for record in reversed(self.captured):
            if path_substr in record.get("path", "") or path_substr in record.get("url", ""):
                return _public_record(record)
        return None

    def save(self, filename: str = "captured_apis.json", *, timestamp: bool = False) -> Path:
        self._materialize_bodies()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if timestamp:
            filename = _stamp_filename(filename)
        path = self.output_dir / filename
        payload = [_public_record(record) for record in self.captured]
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
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
        def handle(route, _request=None):
            url = route.request.url
            if query_overrides:
                url = rewrite_query(url, query_overrides)
            self.last_forwarded_url = url
            if url != route.request.url and getattr(route.request, "resource_type", "") == "document":
                return _redirect(route, url, delay_ms)
            overrides = {}
            if url != route.request.url:
                overrides["url"] = url
            if delay_ms:
                impl = getattr(route, "_impl_obj", None)
                if impl is not None:
                    return _continue_after_delay(impl, delay_ms, overrides)
            if overrides:
                route.continue_(**overrides)
            else:
                route.continue_()

        target.route(url_glob, handle)

    def stop_intercept(self, target, url_glob: str) -> None:
        target.unroute(url_glob)

    def _on_request(self, request) -> None:
        if getattr(request, "resource_type", "") not in self.resource_types:
            return
        parsed = urlparse(request.url)
        record = {
            "method": request.method,
            "url": request.url,
            "path": parsed.path,
            "query_params": parse_qs(parsed.query),
            "body": _limit_body(_request_body(request)),
            "headers": redact_headers(getattr(request, "headers", {}) or {}),
            "request_time": datetime.now().isoformat(timespec="seconds"),
            "response": None,
        }
        self.captured.append(record)
        self._remember(request, record)

    def _on_response(self, response) -> None:
        request = response.request
        record = self._pop_record(request)
        if record is None:
            return
        record["response"] = {
            "status": response.status,
            "headers": redact_headers(getattr(response, "headers", {}) or {}),
            "body": None,
        }
        self._body_sources.append((record, response))

    def _remember(self, request, record: dict) -> None:
        identity = _request_identity(request)
        if identity:
            record["_identity"] = identity
            self._by_id[identity] = record
        method = request.method
        parsed = urlparse(request.url)
        self._by_url.setdefault((method, request.url), []).append(record)
        self._by_path.setdefault((method, parsed.path), []).append(record)

    def _pop_record(self, request) -> dict | None:
        identity = _request_identity(request)
        if identity and identity in self._by_id:
            return self._detach(self._by_id[identity])
        method = getattr(request, "method", "GET")
        exact = self._by_url.get((method, request.url))
        if exact:
            return self._detach(exact[0])
        path = urlparse(request.url).path
        same_path = self._by_path.get((method, path))
        if same_path:
            return self._detach(same_path[0])
        return None

    def _detach(self, record: dict) -> dict:
        identity = record.pop("_identity", None)
        if identity:
            self._by_id.pop(identity, None)
        for bucket in (self._by_url, self._by_path):
            for key, queue in list(bucket.items()):
                kept = [item for item in queue if item is not record]
                if kept:
                    bucket[key] = kept
                else:
                    del bucket[key]
        return record

    def _materialize_bodies(self) -> None:
        pending, self._body_sources = self._body_sources, []
        for record, response in pending:
            response_record = record.get("response")
            if not isinstance(response_record, dict):
                continue
            response_record["body"] = _limit_body(_response_body(response))


def _stamp_filename(filename: str) -> str:
    path = Path(filename)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = path.suffix or ".json"
    return f"{path.stem}_{stamp}{suffix}"


def rewrite_query(url: str, query_overrides: dict[str, str]) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    for key, value in query_overrides.items():
        params[key] = [str(value)]
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


def redact_headers(headers: dict) -> dict:
    cleaned = {}
    for key, value in dict(headers or {}).items():
        if str(key).lower() in _SECRET_HEADERS:
            cleaned[key] = "***"
        else:
            cleaned[key] = value
    return cleaned


def _redirect(route, url: str, delay_ms: int):
    impl = getattr(route, "_impl_obj", None)
    if delay_ms and impl is not None:
        async def delayed():
            await asyncio.sleep(delay_ms / 1000)
            await impl.fulfill(status=302, headers={"location": url})

        return delayed()
    route.fulfill(status=302, headers={"location": url})


def _continue_after_delay(impl, delay_ms: int, overrides: dict):
    async def delayed():
        await asyncio.sleep(delay_ms / 1000)
        await impl.continue_(**overrides)

    return delayed()


def _request_identity(request) -> str | None:
    impl = getattr(request, "_impl_obj", None)
    guid = getattr(impl, "_guid", None)
    if isinstance(guid, str) and guid:
        return guid
    return None


def _public_record(record: dict) -> dict:
    return {key: value for key, value in record.items() if not str(key).startswith("_")}


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
            text = response.text()
        except Exception:
            return None
        embedded = _embedded_s_data(text)
        if embedded is not None:
            return embedded
        return text


def _embedded_s_data(text: str):
    marker = "<!--s-data:"
    start = text.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = text.find("-->", start)
    if end < 0:
        return None
    try:
        payload = json.loads(text[start:end])
    except json.JSONDecodeError:
        return None
    if isinstance(payload, (dict, list)):
        return payload
    return None


def _limit_body(body):
    if body is None:
        return None
    if isinstance(body, str):
        if len(body) <= _MAX_BODY_CHARS:
            return body
        return body[:_MAX_BODY_CHARS] + "...[truncated]"
    try:
        encoded = json.dumps(body, ensure_ascii=False)
    except TypeError:
        encoded = str(body)
    if len(encoded) <= _MAX_BODY_CHARS:
        return body
    return {"_truncated": True, "preview": encoded[:200]}
