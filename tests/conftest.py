import pytest
import datetime
import os
import configparser
import importlib
from playwright.sync_api import Page, sync_playwright

from src.pages.base_page import BasePage
from src.apicheck.api_client import APIClient
from src.apicheck.api_manager import APIManager

# ====================================================================
# A. 核心配置 Fixtures (superTesting 和 API 共用)
# ====================================================================

@pytest.fixture(scope="session")
def config(request):
    """
    讀取環境設定檔 (.ini)，此 Fixture 依賴於根目錄 conftest.py 註冊的 --env 和 --site 選項。
    """
    env = request.config.getoption("--env")
    site = request.config.getoption("--site")

    # 透過 __file__ 向上兩層 (dirname(dirname(__file__))) 找到專案根目錄
    project_root = os.path.dirname(os.path.dirname(__file__))

    # 組合路徑： 專案根目錄 + /env/ + {env}.ini
    env_path = os.path.join(project_root, "env", f"{env}.ini")

    if not os.path.exists(env_path):
        pytest.skip(f"Not found environment file: {env_path}")

    config_parser = configparser.ConfigParser()
    config_parser.read(env_path)
    config_parser['DEFAULT'] = {'site': site}

    return config_parser

# ====================================================================
# B. superTesting 專用 Fixtures (Playwright)
# ====================================================================

@pytest.fixture(scope="session")
def page():
    """
    Playwright Page Fixture：設定 viewport, slow_mo, 視訊錄製等。
    這個 Fixture 是 superTesting 測試的核心。
    """
    with sync_playwright() as p:
        video_dir = "videos"
        os.makedirs(video_dir, exist_ok=True)

        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 2560, "height": 1440},
            record_video_dir=video_dir,
            record_video_size={"width": 2560, "height": 1440}
        )
        page = context.new_page()
        page.set_default_timeout(5000)

        yield page

        # 清理和錄影檔重新命名
        if page.video:
            video_path = page.video.path()
            context.close()
            browser.close()

            now = datetime.datetime.now()
            new_filename = now.strftime("%Y%m%d_%H%M%S") + ".webm"

            if os.path.exists(video_path):
                new_path = os.path.join(video_dir, new_filename)
                os.rename(video_path, new_path)


@pytest.fixture(scope="session")
def e2e_logged_in_page(page: Page, config):
    site = config.get('DEFAULT', 'site')

    if site == 'spg':
        pytest.skip("spg uses its own login fixture")

    try:
        module = importlib.import_module(f"src.pages.{site}.login_page")
        LoginPage = getattr(module, "LoginPage")
    except (ImportError, AttributeError) as e:
        pytest.fail(f"無法載入 {site} 的 LoginPage: {e}")

    base_url = config.get(site, "base_url")
    username = config.get(site, 'username')
    password = config.get(site, 'password')

    login_page = LoginPage(page, config)
    login_page.login(username, password)
    login_page.verify_login_success()
    yield login_page


@pytest.fixture(scope="session")
def e2e_auth_token(e2e_logged_in_page: "BasePage"):
    token = e2e_logged_in_page.get_auth_token()
    return token

@pytest.fixture(scope="session")
def e2e_main_page(e2e_logged_in_page):
    return e2e_logged_in_page.page


# ====================================================================
# C. API 專用 Fixtures
# ====================================================================

@pytest.fixture(scope="session")
def api_client(config):
    """
    提供一個未認證的 APIClient 實例
    所有環境參數都從 config Fixture (即 .ini 檔案) 中讀取。
    """
    site = config.get('DEFAULT', 'site')

    base_url = config.get(site, "base_url")
    api_username = config.get(site, 'test_username')
    api_password = config.get(site, 'test_password')

    # 實例化 APIClient
    return APIClient(base_url, api_username, api_password)

@pytest.fixture(scope="session")
def api_manager(api_client):
    manager = APIManager(api_client)
    manager.authenticate()
    return manager