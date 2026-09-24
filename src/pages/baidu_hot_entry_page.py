from urllib.parse import parse_qs, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from src.core.base_page import BasePage


class BaiduHotEntryPage(BasePage):
    """Q-ENTRY-001：点击 aria-label 为「百度热搜」的标题。"""

    HOT_SEARCH = '[aria-label="百度热搜"]'

    def open(self, url: str) -> None:
        self.navigate(url)
        self.page.get_by_role("textbox").first.wait_for(state="visible", timeout=15_000)

    def title(self) -> str:
        return self.page.title()

    def search_entry_visible(self) -> bool:
        return self.page.get_by_role("textbox").first.is_visible()

    def open_hot_board(self):
        hot = self.page.locator(self.HOT_SEARCH).first
        hot.wait_for(state="visible", timeout=15_000)
        try:
            with self.page.expect_popup(timeout=15_000) as popup_info:
                hot.click()
            board = popup_info.value
        except PlaywrightTimeout:
            board = self.page
        board.wait_for_load_state("domcontentloaded")
        return board

    @staticmethod
    def hot_words(board) -> list[str]:
        words = []
        for text in board.locator("a").all_inner_texts():
            cleaned = " ".join(text.split())
            if len(cleaned) >= 6:
                words.append(cleaned)
        return words


def board_matches_entry(url: str) -> bool:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return (
        parsed.hostname == "top.baidu.com"
        and parsed.path.rstrip("/") == "/board"
        and "pc" in query.get("platform", [])
        and "pcindex_entry" in query.get("sa", [])
    )
