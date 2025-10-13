from time import sleep
from playwright.sync_api import Page
from typing import Optional

class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.timeout = 5000

    def goto(self, url: str) -> None:
        self.page.goto(url)

    def wait_for_load_state(self, state: str = "networkidle") -> None:
        self.page.wait_for_load_state(state)

    def is_element_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def reload(self):
        self.page.reload(wait_until="domcontentloaded")
        from time import sleep
        sleep(1)

    def get_auth_token(self):
        self.page.wait_for_load_state('domcontentloaded')
        #token = self.page.evaluate("() => sessionStorage.getItem('token')")
        for i in range(10):
            token = self.page.evaluate("() => sessionStorage.getItem('token') || localStorage.getItem('token')")
            if token:
                return token
            sleep(1)

        raise ValueError("Token not found in session/local storage after multiple attempts")