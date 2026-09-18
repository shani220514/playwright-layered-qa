from pathlib import Path

import pytest

from src.interceptors.network_interceptor import NetworkInterceptor
from src.pages.baidu_home_page import BaiduHomePage
from src.yaml_runner.schema import load_cases

pytestmark = [pytest.mark.example, pytest.mark.ui, pytest.mark.smoke, pytest.mark.intercept]

CASES = Path(__file__).resolve().parents[2] / "assets" / "cases" / "baidu_home.yaml"


def test_open_baidu_home(page, config):
    """TC-BAIDU-001: 打开百度首页，搜索框可见。"""
    case = load_cases(CASES)[0]
    assert case["case_id"] == "TC-BAIDU-001"

    interceptor = NetworkInterceptor()
    interceptor.start_capture(page)

    home = BaiduHomePage(page)
    home.open(config.base_url)

    assert "百度" in home.title()
    captured = interceptor.save("baidu_home.json")
    assert captured.exists()
    assert isinstance(interceptor.records(), list)
