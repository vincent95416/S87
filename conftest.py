import datetime
import os
import pytest
import configparser
from playwright.sync_api import Page, sync_playwright
from new20.pages.login_page import LoginPage

def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="指定測試環境: dev 或 prod")
    parser.addoption("--site", action="store", default="new20", help="指定站點: new20 或 spg")

@pytest.fixture(scope="session")
def config(request):
    """
    讀取環境設定黨，傳遞到測試入口
    """
    env = request.config.getoption("--env")
    site = request.config.getoption("--site")
    env_path = os.path.join(os.path.dirname(__file__), "env", f"{env}.ini")

    if not os.path.exists(env_path):
        pytest.skip(f"Not found :{env_path}")

    config = configparser.ConfigParser()
    config.read(env_path)
    config['DEFAULT'] = {'site': site}
    return config

@pytest.fixture(scope="session")
def page():
    with sync_playwright() as p:
        video_dir = "videos"
        lastest_dir = os.path.join(video_dir, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(video_dir, exist_ok=True)

        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(viewport={"width": 2560, "height": 1440}, record_video_dir = lastest_dir, record_video_size ={"width": 2560, "height": 1440})
        page = context.new_page()
        page.set_default_timeout(5000)
        yield page

        context.close()
        browser.close()

@pytest.fixture(scope="session")
def logged_page(page: Page, config):

    site = config.get('DEFAULT', 'site')
    base_url = config.get(site, "base_url")
    username = config.get(site, 'username')
    password = config.get(site, 'password')

    login_page = LoginPage(page, config)
    login_page.login(username, password)
    login_page.verify_login_success()
    yield login_page

@pytest.fixture(scope="session")
def auth_token(logged_page: Page):
    """
    執行登入流程並返回 Session Storage 中的 token。
    這個夾具會自動被 Pytest 調用，並在整個測試會話中只執行一次。
    """
    token = logged_page.get_auth_token()
    return token

@pytest.fixture(scope="session")
def main_page(logged_page: LoginPage):
    """提供已登入的原始 Page 物件"""
    return logged_page.page