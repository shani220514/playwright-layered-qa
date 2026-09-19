from pathlib import Path
import time

import pytest

from src.pages.baidu_home_page import BaiduHomePage
from src.yaml_runner.schema import load_cases

pytestmark = [pytest.mark.example, pytest.mark.ui, pytest.mark.smoke, pytest.mark.intercept]

CASES = Path(__file__).resolve().parents[2] / "assets" / "cases" / "baidu_home.yaml"
BOARD_API = "**/api/board**"
DELAY_MS = 1500


def test_open_baidu_home(page, config, interceptor):
    """TC-BAIDU-001: 打开百度首页，搜索框可见。"""
    case = load_cases(CASES)[0]
    assert case["case_id"] == "TC-BAIDU-001"

    home = BaiduHomePage(page)
    home.open(config.base_url)

    assert "百度" in home.title()
    captured = interceptor.save("baidu_home.json")
    assert captured.exists()
    assert isinstance(interceptor.records(), list)
    _print_result("打开首页", title=home.title(), capture=str(captured))


def test_click_baidu_hot_search(page, config):
    """TC-BAIDU-002: 点击百度热搜，进入热搜榜页面。"""
    board = _open_board(page, config)
    _print_result("点击百度热搜", url=board.url, title=board.title())
    assert "top.baidu.com" in board.url


def test_get_hot_search_api(page, config, interceptor):
    """TC-BAIDU-003: 进入热搜页后获取 /api/board 数据。"""
    board = _open_board(page, config)
    record = _request_board_api(interceptor, board)
    assert record is not None, "未捕获到 /api/board"
    _print_result("获取 API 数据", **_record_fields(record))


def test_validate_hot_search_api(page, config, interceptor):
    """TC-BAIDU-004: 拦截 /api/board 并校验返回。"""
    board = _open_board(page, config)
    record = _request_board_api(interceptor, board)
    assert record is not None, "未捕获到 /api/board"
    response = record["response"]
    assert response is not None
    assert response["status"] == 200
    body = response["body"]
    assert isinstance(body, dict)
    assert body.get("success") is True or "data" in body
    _print_result("拦截校验返回", **_record_fields(record), check="PASS")


def test_weak_network_delay(page, config, interceptor):
    """TC-BAIDU-005: 弱网模拟，延迟 /api/board 返回。"""
    board = _open_board(page, config)
    interceptor.intercept_route(page.context, BOARD_API, delay_ms=DELAY_MS)
    started = time.perf_counter()
    record = _request_board_api(interceptor, board)
    elapsed_ms = (time.perf_counter() - started) * 1000
    interceptor.stop_intercept(page.context, BOARD_API)
    assert record is not None
    assert record["response"]["status"] == 200
    assert elapsed_ms >= DELAY_MS
    _print_result(
        "弱网延迟返回",
        elapsed_ms=int(elapsed_ms),
        delay_ms=DELAY_MS,
        status=record["response"]["status"],
    )


def test_modify_request_params(page, config, interceptor):
    """TC-BAIDU-006: 修改 /api/board 请求参数后再转发。"""
    board = _open_board(page, config)
    interceptor.intercept_route(
        page.context,
        BOARD_API,
        query_overrides={"tab": "novel"},
    )
    mutated = _request_board_api(interceptor, board)
    interceptor.stop_intercept(page.context, BOARD_API)
    assert mutated is not None
    forwarded = interceptor.last_forwarded_url or mutated["url"]
    assert "tab=novel" in forwarded
    assert mutated["response"]["status"] == 200
    _print_result(
        "修改请求参数",
        original_tab="realtime",
        forwarded=forwarded,
        status=mutated["response"]["status"],
    )


def test_save_request_response(page, config, interceptor):
    """TC-BAIDU-007: 保存请求和响应；失败时 conftest 会额外留痕。"""
    board = _open_board(page, config)
    record = _request_board_api(interceptor, board)
    assert record is not None
    saved = interceptor.save("baidu_hot_search.json")
    assert saved.exists()
    _print_result(
        "保存请求和响应",
        path=str(saved),
        records=len(interceptor.records()),
        **_record_fields(record),
    )


def _open_board(page, config):
    home = BaiduHomePage(page)
    home.open(config.base_url)
    board = home.open_hot_search()
    assert "top.baidu.com" in board.url
    return board


def _print_result(step: str, **fields) -> None:
    parts = " | ".join(f"{key}={value}" for key, value in fields.items())
    print(f"\n[结果] {step}: {parts}", flush=True)


def _record_fields(record: dict) -> dict:
    response = record.get("response") or {}
    body = response.get("body")
    cards = None
    if isinstance(body, dict):
        cards = ((body.get("data") or {}).get("cards") or None)
    return {
        "url": record.get("url"),
        "status": response.get("status"),
        "success": body.get("success") if isinstance(body, dict) else None,
        "cards": len(cards) if isinstance(cards, list) else None,
    }


def _request_board_api(interceptor, board):
    with board.expect_response(lambda response: "/api/board" in response.url, timeout=20_000):
        board.evaluate(
            """async () => {
                await fetch('/api/board?platform=pc&tab=realtime', {credentials: 'include'});
            }"""
        )
    return interceptor.find("/api/board")
