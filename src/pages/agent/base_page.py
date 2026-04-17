from src.pages.base_page import BasePage as CommonBasePage
from playwright.sync_api import Page
import requests

class BasePage(CommonBasePage):
    def get_auth_token(self):
        self.page.wait_for_load_state()
        self.page.wait_for_load_state('domcontentloaded')

        cookies = self.page.context.cookies()
        # 由cookie的list of dict中取出符合的name
        antiforgery = next(
            (c for c in cookies if 'Antiforgery' in c['name']), None
        )
        auth_cookie = next(
            (c for c in cookies if '.AspNetCore.Cookies' in c['name']), None
        )
        if not antiforgery or not auth_cookie:
            raise Exception("找不到必要的 Cookie，請確認登入狀態")

        session = requests.Session()
        session.cookies.set(antiforgery['name'], antiforgery['value'])
        session.cookies.set(auth_cookie['name'], auth_cookie['value'])

        return session