from src.core.base_page import BasePage


class FakePage:
    def __init__(self):
        self.opened = None
        self.clicks = []
        self.fills = []
        self.waited = []

    def goto(self, url, **kwargs):
        self.opened = url

    def click(self, selector, **kwargs):
        self.clicks.append(selector)

    def fill(self, selector, value, **kwargs):
        self.fills.append((selector, value))

    def locator(self, selector):
        return FakeLocator(self, selector)


class FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    def wait_for(self, **kwargs):
        self.page.waited.append(self.selector)


def test_base_page_navigate_opens_url():
    page = FakePage()
    BasePage(page).navigate("https://www.baidu.com/")
    assert page.opened == "https://www.baidu.com/"


def test_base_page_fill_and_click():
    page = FakePage()
    pom = BasePage(page)
    pom.fill("#kw", "playwright")
    pom.click("#su")
    assert page.fills == [("#kw", "playwright")]
    assert page.clicks == ["#su"]


def test_base_page_wait_for_selector():
    page = FakePage()
    BasePage(page).wait_for_selector("#kw")
    assert page.waited == ["#kw"]
