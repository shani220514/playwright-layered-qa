from src.interceptors.network_interceptor import NetworkInterceptor


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
