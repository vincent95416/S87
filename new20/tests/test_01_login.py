import allure
from new20.pages.login_page import LoginPage

@allure.step("完整登入後驗證")
def test_login(logged_page: LoginPage) -> None:
    logged_page.verify_login_success()