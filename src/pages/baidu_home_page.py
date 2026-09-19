from src.core.base_page import BasePage


class BaiduHomePage(BasePage):
    SEARCH_BOX = "#chat-textarea"
    HOT_SEARCH = "a.hot-title"

    def open(self, url: str) -> None:
        self.navigate(url)
        self.page.locator("#chat-textarea").or_(self.page.locator("#kw")).first.wait_for(
            state="visible",
            timeout=15_000,
        )

    def title(self) -> str:
        return self.page.title()

    def open_hot_search(self):
        hot = self.page.locator(self.HOT_SEARCH)
        hot.wait_for(state="attached", timeout=15_000)
        with self.page.expect_popup() as popup_info:
            hot.click(force=True)
        board = popup_info.value
        board.wait_for_load_state("domcontentloaded")
        return board
