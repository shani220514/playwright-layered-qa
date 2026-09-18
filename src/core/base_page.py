from __future__ import annotations


class BasePage:
    def __init__(self, page):
        self.page = page

    def navigate(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded")

    def click(self, selector: str) -> None:
        self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        self.page.fill(selector, value)

    def wait_for_selector(self, selector: str, timeout: int = 10_000) -> None:
        self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
