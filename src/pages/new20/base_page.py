from src.pages.base_page import BasePage as CommonBasePage
from playwright.sync_api import Page

class BasePage(CommonBasePage):
    def get_auth_token(self) -> str:
        self.page.wait_for_load_state()
        token = self.page.evaluate("() => sessionStorage.getItem('Token')")
        if not token:
            raise ValueError("Token not found in session storage")
        return token
