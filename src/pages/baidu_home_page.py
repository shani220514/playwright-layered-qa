from src.core.base_page import BasePage


class BaiduHomePage(BasePage):
    SEARCH_BOX = "#chat-textarea, #kw"
    HOT_SEARCH = '[aria-label="百度热搜"]'

    def open(self, url: str) -> None:
        self.navigate(url)
        self.wait_for_selector(self.SEARCH_BOX, timeout=15_000)

    def title(self) -> str:
        return self.page.title()

    def open_hot_search(self):
        hot = self.page.locator(self.HOT_SEARCH).first
        hot.wait_for(state="visible", timeout=15_000)
        with self.page.expect_popup() as popup_info:
            hot.click()
        board = popup_info.value
        board.wait_for_load_state("domcontentloaded")
        return board
