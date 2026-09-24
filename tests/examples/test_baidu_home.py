from pathlib import Path
import time

import pytest

from src.pages.baidu_home_page import BaiduHomePage
from src.yaml_runner.schema import load_cases

pytestmark = [pytest.mark.example, pytest.mark.ui, pytest.mark.smoke, pytest.mark.intercept]

CASES = Path(__file__).resolve().parents[2] / "assets" / "cases" / "baidu_home.yaml"
BOARD_URL = "**/*board*"
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
    """TC-BAIDU-003: 进入热搜页后捕获页面自己打开的 /board 文档请求。"""
    board = _open_board(page, config, interceptor)
    record = interceptor.find("/board")
    assert record is not None, "未捕获到 /board"
    assert "top.baidu.com" in board.url
    _print_result("获取页面请求", **_record_fields(record))


def test_validate_hot_search_api(page, config, interceptor):
    """TC-BAIDU-004: 校验热搜页自然打开的 /board 响应。"""
    board = _open_board(page, config, interceptor)
    record = interceptor.find("/board")
    assert record is not None, "未捕获到 /board"
    response = record["response"]
    assert response is not None
    assert response["status"] == 200
    assert "热搜" in board.title()
    _print_result("拦截校验返回", **_record_fields(record), title=board.title(), check="PASS")


def test_weak_network_delay(page, config, interceptor):
    """TC-BAIDU-005: 弱网模拟，延迟热搜页 /board 文档请求。"""
    home = BaiduHomePage(page)
    home.open(config.base_url)
    interceptor.include_resource_types({"document"})
    interceptor.intercept_route(page.context, BOARD_URL, delay_ms=DELAY_MS)
    started = time.perf_counter()
    board = home.open_hot_search()
    elapsed_ms = (time.perf_counter() - started) * 1000
    interceptor.stop_intercept(page.context, BOARD_URL)
    assert "top.baidu.com" in board.url
    record = interceptor.find("/board")
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
    """TC-BAIDU-006: 改写热搜页 /board 的查询参数后再打开。"""
    home = BaiduHomePage(page)
    home.open(config.base_url)
    interceptor.include_resource_types({"document"})
    interceptor.intercept_route(
        page.context,
        BOARD_URL,
        query_overrides={"tab": "novel"},
    )
    board = home.open_hot_search()
    interceptor.stop_intercept(page.context, BOARD_URL)
    mutated = interceptor.find("/board")
    assert mutated is not None
    forwarded = interceptor.last_forwarded_url or mutated["url"]
    assert "tab=novel" in forwarded
    assert "tab=novel" in board.url
    assert mutated["response"]["status"] == 200
    _print_result(
        "修改请求参数",
        forwarded=forwarded,
        landed=board.url,
        status=mutated["response"]["status"],
    )


def test_save_request_response(page, config, interceptor):
    """TC-BAIDU-007: 保存热搜页自然请求和响应；失败时 conftest 会额外留痕。"""
    _open_board(page, config, interceptor)
    record = interceptor.find("/board")
    assert record is not None
    saved = interceptor.save("baidu_hot_search.json")
    assert saved.exists()
    assert "/board" in saved.read_text(encoding="utf-8")
    _print_result(
        "保存请求和响应",
        path=str(saved),
        records=len(interceptor.records()),
        **_record_fields(record),
    )


def _open_board(page, config, interceptor=None):
    home = BaiduHomePage(page)
    home.open(config.base_url)
    if interceptor is not None:
        interceptor.include_resource_types({"document"})
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
