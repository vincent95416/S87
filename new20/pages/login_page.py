import allure
from new20.pages.base_page import BasePage
from playwright.sync_api import Page

class LoginPage(BasePage):
    def __init__(self, page: Page, config):
        super().__init__(page)
        base_url = config.get('2.0', 'base_url')
        self.url = base_url

    @allure.step("導航至login page")
    def navigate(self, url: str) -> None:
        self.goto(self.url)
        self.wait_for_load_state()

    @allure.step("填入帳號")
    def fill_username(self, username: str) -> None:
        self.page.get_by_role("textbox", name="帳號").click()
        self.page.get_by_role("textbox", name="帳號").fill(username)

    @allure.step("填入密碼")
    def fill_password(self, password: str) -> None:
        self.page.get_by_role("textbox", name="密碼").click()
        self.page.get_by_role("textbox", name="密碼").fill(password)

    @allure.step("點擊登入")
    def click_login_button(self) -> None:
        self.page.get_by_role("button", name="會員登入").click()

    @allure.step("完整登入流程")
    def login(self, username: str, password: str) -> None:
        self.navigate(self.url)
        self.fill_username(username)
        self.fill_password(password)
        self.click_login_button()

    @allure.step("驗證登入成功，時間元素可視")
    def verify_login_success(self) -> None:
        self.page.locator("div.datetime").wait_for(state="visible", timeout=10000)
        self.page.wait_for_load_state()