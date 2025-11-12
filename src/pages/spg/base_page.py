from src.pages.base_page import BasePage as CommonBasePage
from playwright.sync_api import Page
from time import sleep

class BasePage(CommonBasePage):
    def get_auth_token(self) -> str:
        self.page.wait_for_load_state()
        self.page.wait_for_load_state('domcontentloaded')

        for attempt in range(10):
            token = self.page.evaluate(
                "() => sessionStorage.getItem('token') || localStorage.getItem('token')"
            )
            if token:
                return token
            if attempt < 9:  # 最後一次不用 sleep
                sleep(1)
        raise ValueError("Token not found in session/local storage after multiple attempts")