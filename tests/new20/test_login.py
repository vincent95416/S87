import allure
import pytest
from src.pages.new20.login_page import LoginPage

@allure.step("完整登入後驗證")
@pytest.mark.order(1)
def test_login(e2e_logged_in_page: LoginPage) -> None:
    e2e_logged_in_page.verify_login_success()