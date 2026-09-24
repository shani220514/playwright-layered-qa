import pytest

from src.pages.baidu_hot_entry_page import BaiduHotEntryPage, board_matches_entry

pytestmark = [pytest.mark.example, pytest.mark.ui]


def test_open_baidu_for_hot_entry(page, config):
    """TC-ENTRY-001 requirement_ids: REQ-ENTRY-001。未登录打开 BASE_URL。"""
    home = BaiduHotEntryPage(page)
    home.open(config.base_url)

    assert "百度" in home.title()
    assert home.search_entry_visible()


def test_click_hot_entry_to_board(page, config):
    """TC-ENTRY-002 requirement_ids: REQ-ENTRY-002, REQ-ENTRY-003, REQ-ENTRY-004。"""
    home = BaiduHotEntryPage(page)
    home.open(config.base_url)
    board = home.open_hot_board()

    assert board_matches_entry(board.url)
    assert "热搜" in board.title()
    assert home.hot_words(board)


@pytest.mark.skip(reason="TC-ENTRY-003 是手工用例：不自动构造热搜入口缺失")
def test_missing_hot_entry_is_failure():
    """TC-ENTRY-003 requirement_ids: REQ-ENTRY-005。入口不可点击时不得判成功。"""
