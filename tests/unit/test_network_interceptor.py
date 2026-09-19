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
