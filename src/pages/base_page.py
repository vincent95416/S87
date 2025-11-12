from playwright.sync_api import Page

class BasePage:
    def __init__(self, page: Page, config=None):
        self.page = page
        self.config = config
        self.timeout = 5000

    def goto(self, url: str) -> None:
        self.page.goto(url)

    def wait_for_load_state(self, state: str = "networkidle") -> None:
        self.page.wait_for_load_state(state)

    def is_element_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded")
        from time import sleep
        sleep(1)

    def get_auth_token(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_auth_token() method"
        )