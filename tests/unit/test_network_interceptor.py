import asyncio
import re
import time

from src.interceptors.network_interceptor import NetworkInterceptor, rewrite_query


class FakePage:
    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, event, payload):
        for handler in self.handlers.get(event, []):
            handler(payload)


class FakeRequest:
    def __init__(self, url, method="GET", resource_type="xhr", headers=None, post_data=None):
        self.url = url
        self.method = method
        self.resource_type = resource_type
        self.headers = headers or {"accept": "application/json"}
        self.post_data = post_data

    @property
    def post_data_json(self):
        raise ValueError("not json")


class FakeResponse:
    def __init__(self, request, status=200, body=None, headers=None):
        self.request = request
        self.status = status
        self.url = request.url
        self.headers = headers or {"content-type": "application/json"}
        self._body = body if body is not None else {"ok": True}

    def json(self):
        if isinstance(self._body, dict):
            return self._body
        raise ValueError("not json")

    def text(self):
        return str(self._body)


def test_interceptor_captures_xhr_and_pairs_response(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)

    request = FakeRequest("https://www.baidu.com/sugrec?wd=qa")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body={"g": []}))

    records = interceptor.records()
    assert len(records) == 1
    assert records[0]["method"] == "GET"
    assert records[0]["path"] == "/sugrec"
    assert records[0]["response"]["status"] == 200
    assert records[0]["response"]["body"] == {"g": []}


def test_interceptor_ignores_static_assets(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)

    request = FakeRequest(
        "https://www.baidu.com/img/logo.png",
        resource_type="image",
    )
    page.emit("request", request)

    assert interceptor.records() == []


def test_interceptor_exports_json(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest("https://www.baidu.com/s?wd=qa", resource_type="fetch")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body={"q": "qa"}))

    path = interceptor.save("baidu.json")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "/s" in text
    assert "200" in text


def test_save_appends_timestamp_to_filename(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest("https://top.baidu.com/api/board?platform=pc")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body={"success": True}))

    path = interceptor.save("baidu_hot_entry.json", timestamp=True)
    assert path.parent == tmp_path
    assert re.fullmatch(r"baidu_hot_entry_\d{8}_\d{6}\.json", path.name)
    assert "/api/board" in path.read_text(encoding="utf-8")


def test_rewrite_query_overrides_tab():
    url = "https://top.baidu.com/api/board?platform=pc&tab=realtime"
    out = rewrite_query(url, {"tab": "novel"})
    assert "tab=novel" in out
    assert "platform=pc" in out
    assert "tab=realtime" not in out


def test_find_returns_latest_matching_path(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)

    first = FakeRequest("https://top.baidu.com/api/board?tab=realtime")
    second = FakeRequest("https://www.baidu.com/sugrec?wd=qa")
    page.emit("request", first)
    page.emit("response", FakeResponse(first, status=200, body={"success": True}))
    page.emit("request", second)
    page.emit("response", FakeResponse(second, status=200, body={"g": []}))

    record = interceptor.find("/api/board")
    assert record is not None
    assert record["path"] == "/api/board"
    assert record["response"]["status"] == 200
    assert interceptor.find("/missing") is None


def test_save_failure_writes_request_and_response(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest("https://top.baidu.com/api/board?platform=pc")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body={"success": True}))

    path = interceptor.save_failure("baidu_hot_search")
    assert path.name == "baidu_hot_search_req_resp.json"
    text = path.read_text(encoding="utf-8")
    assert "/api/board" in text
    assert "success" in text


class FakeRoute:
    def __init__(self, url):
        self.request = FakeRequest(url)
        self.continued = None

    def continue_(self, **kwargs):
        self.continued = kwargs


class FakeRoutable:
    def __init__(self):
        self.handlers = {}
        self.routes = []

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def route(self, url_glob, handler):
        self.routes.append((url_glob, handler))

    def unroute(self, url_glob):
        self.routes = [(glob, handler) for glob, handler in self.routes if glob != url_glob]


def test_intercept_route_rewrites_query_then_continues(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    target = FakeRoutable()
    interceptor.intercept_route(
        target,
        "**/api/board**",
        query_overrides={"tab": "novel"},
    )

    assert len(target.routes) == 1
    glob, handler = target.routes[0]
    assert glob == "**/api/board**"
    route = FakeRoute("https://top.baidu.com/api/board?platform=pc&tab=realtime")
    handler(route)
    assert "tab=novel" in route.continued["url"]
    assert "tab=novel" in interceptor.last_forwarded_url

    interceptor.stop_intercept(target, "**/api/board**")
    assert target.routes == []


def test_interceptor_redacts_secret_headers(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest(
        "https://www.baidu.com/sugrec",
        headers={"cookie": "sid=secret", "accept": "application/json", "Authorization": "Bearer token"},
    )
    page.emit("request", request)
    page.emit(
        "response",
        FakeResponse(request, headers={"set-cookie": "sid=secret", "content-type": "application/json"}),
    )

    record = interceptor.records()[0]
    assert record["headers"]["cookie"] == "***"
    assert record["headers"]["Authorization"] == "***"
    assert record["headers"]["accept"] == "application/json"
    assert record["response"]["headers"]["set-cookie"] == "***"
    saved = interceptor.save("redacted.json").read_text(encoding="utf-8")
    assert "secret" not in saved
    assert "Bearer token" not in saved


def test_interceptor_pairs_response_when_request_wrapper_differs(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    page.emit("request", FakeRequest("https://top.baidu.com/api/board?tab=realtime"))
    other = FakeRequest("https://top.baidu.com/api/board?tab=novel")
    page.emit("response", FakeResponse(other, status=200, body={"success": True}))

    record = interceptor.records()[0]
    assert record["response"]["status"] == 200
    assert record["response"]["body"] == {"success": True}


def test_document_response_keeps_embedded_s_data_json(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    interceptor.include_resource_types({"document"})
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest("https://top.baidu.com/board?platform=pc", resource_type="document")
    html = '<html><!--s-data:{"data":{"cards":[{"component":"hotList"}]}}--></html>'
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body=html))

    body = interceptor.records()[0]["response"]["body"]
    assert body["data"]["cards"][0]["component"] == "hotList"


def test_document_requests_stay_hidden_until_included(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    page.emit("request", FakeRequest("https://top.baidu.com/board", resource_type="document"))
    assert interceptor.records() == []

    interceptor.include_resource_types({"document"})
    request = FakeRequest("https://top.baidu.com/board?platform=pc", resource_type="document")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, status=200, body="<html>热搜</html>"))
    records = interceptor.records()
    assert len(records) == 1
    assert records[0]["path"] == "/board"
    assert records[0]["response"]["status"] == 200


def test_interceptor_truncates_large_response_body(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    page = FakePage()
    interceptor.start_capture(page)
    request = FakeRequest("https://www.baidu.com/sugrec")
    page.emit("request", request)
    page.emit("response", FakeResponse(request, body="x" * 70_000))

    body = interceptor.records()[0]["response"]["body"]
    assert isinstance(body, str)
    assert len(body) < 70_000
    assert "truncated" in body


def test_document_query_override_redirects(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    target = FakeRoutable()
    interceptor.intercept_route(target, "**/*board*", query_overrides={"tab": "novel"})
    _glob, handler = target.routes[0]
    route = FakeRoute("https://top.baidu.com/board?platform=pc")
    route.request.resource_type = "document"
    route.fulfilled = None

    def fulfill(**kwargs):
        route.fulfilled = kwargs

    route.fulfill = fulfill
    handler(route)
    assert route.fulfilled["status"] == 302
    assert "tab=novel" in route.fulfilled["headers"]["location"]
    assert "tab=novel" in interceptor.last_forwarded_url


def test_intercept_route_delay_returns_without_blocking(tmp_path):
    interceptor = NetworkInterceptor(output_dir=tmp_path)
    target = FakeRoutable()
    interceptor.intercept_route(target, "**/api/board**", delay_ms=80)
    _glob, handler = target.routes[0]

    class _Impl:
        def __init__(self):
            self.kwargs = None

        async def continue_(self, **kwargs):
            self.kwargs = kwargs

    route = FakeRoute("https://top.baidu.com/api/board?platform=pc&tab=realtime")
    route._impl_obj = _Impl()
    started = time.perf_counter()
    pending = handler(route)
    assert time.perf_counter() - started < 0.3
    assert asyncio.iscoroutine(pending)
    asyncio.run(pending)
    assert time.perf_counter() - started >= 0.08
    assert route._impl_obj.kwargs is not None
