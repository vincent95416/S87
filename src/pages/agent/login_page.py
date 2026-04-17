import allure
from src.pages.new20.base_page import BasePage
from playwright.sync_api import Page

class LoginPage(BasePage):
    def __init__(self, page: Page, config):
        super().__init__(page)
        base_url = config.get('agent', 'base_url')
        self.url = base_url

    @allure.step("導航至login page")
    def navigate(self, url: str) -> None:
        self.goto(self.url)
        self.wait_for_load_state()

    @allure.step("填入帳號")
    def fill_username(self, username: str) -> None:
        self.page.get_by_role("input", name="txtac").click()
        self.page.get_by_role("input", name="txtac").fill(username)

    @allure.step("填入密碼")
    def fill_password(self, password: str) -> None:
        self.page.get_by_role("input", name="txtpd").click()
        self.page.get_by_role("input", name="txtpd").fill(password)

    @allure.step("點擊登入")
    def click_login_button(self) -> None:
        self.page.get_by_role("button", id="btnLogin").click()

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

    @allure.step("")
    def modal_context(self) -> str:
        self.page.locator("div.modal-body.text-center").wait_for(state="visible", timeout=5000)
        text = self.page.locator("div.modal-body.text-center").inner_text()
        return text