from src.core.base_page import BasePage


class BaiduHomePage(BasePage):
    SEARCH_BOX = "#chat-textarea"

    def open(self, url: str) -> None:
        self.navigate(url)
        self.page.locator("#chat-textarea").or_(self.page.locator("#kw")).first.wait_for(
            state="visible",
            timeout=15_000,
        )

    def title(self) -> str:
        return self.page.title()
