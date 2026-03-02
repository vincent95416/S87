import pytest
import os
import configparser
import importlib
from datetime import datetime
from playwright.sync_api import Page, BrowserContext, sync_playwright

from src.pages.base_page import BasePage
from src.apicheck.api_client import APIClient
from src.apicheck.api_manager import APIManager

# ====================================================================
# Pytest Hook - 捕捉及追蹤測試結果
# ====================================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def test_report(item, call):
    """
    讓 fixture 可以知道測試是否失敗
    """
    outcome = yield
    rep = outcome.get_result()      #把item.rep_call測試本體的結果附加到request.node上，讓fixture讀取
    setattr(item, f"rep_{rep.when}", rep)

@pytest.fixture(scope="function", autouse=True)
def trace_handler(request, context, trace_session_dir):
    """
    自動處理每個測試的 trace 錄製（autouse=True 表示自動應用到所有測試）
    """
    # 測試開始前：啟動 trace chunk
    context.tracing.start_chunk()

    yield
    # 測試結束後：檢查是否失敗
    test_failed = (
            (hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed) or
            (hasattr(request.node, 'rep_call') and request.node.rep_call.failed) or
            (hasattr(request.node, 'rep_teardown') and request.node.rep_teardown.failed)
    )

    if test_failed:
        os.makedirs(trace_session_dir, exist_ok=True)
        test_name = request.node.name
        trace_path = os.path.join(trace_session_dir, f"{test_name}.zip")
        context.tracing.stop_chunk(path=trace_path)
    else:
        context.tracing.stop_chunk()

@pytest.fixture(scope="session")
def trace_session_dir():
    """測試失敗時才建立的traces資料夾"""
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_dir = os.path.join("traces", session_time)
    return trace_dir

# ====================================================================
# A. 核心配置 Fixtures (e2e 和 API 共用)
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
# B. e2e 專用 Fixtures
# ====================================================================

@pytest.fixture(scope="session")
def context():
    """
    Browser Context，保持登入狀態，設定 viewport, slow_mo, 視訊錄製等。
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        context = browser.new_context(
            #viewport={"width": 2560, "height": 1440}
        )
        # 開始 trace 錄製
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

        yield context
        # 停止並保存 trace
        context.tracing.stop()
        context.close()
        browser.close()

@pytest.fixture(scope="session")
def page(context: BrowserContext, request, trace_session_dir):
    page = context.new_page()
    page.set_default_timeout(5000)

    context.tracing.start_chunk()   #每個測試用start_chunk保存為獨立片段
    yield page
    # # 檢查測試是否失敗（檢查所有階段）
    # failed = False
    #
    # # 檢查 setup 階段
    # if hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed:
    #     failed = True
    # # 檢查 call 階段（測試本體）
    # if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
    #     failed = True
    # # 檢查 teardown 階段
    # if hasattr(request.node, 'rep_teardown') and request.node.rep_teardown.failed:
    #     failed = True
    #
    # if failed:
    #     # 只有在測試失敗時才建立 session 資料夾
    #     os.makedirs(trace_session_dir, exist_ok=True)
    #     test_name = request.node.name
    #     trace_path = os.path.join(trace_session_dir, f"{test_name}.zip")
    #     context.tracing.stop_chunk(path=trace_path)
    # else:
    #     context.tracing.stop_chunk()
    page.close()

@pytest.fixture(scope="session")
def e2e_logged_in_page(page: Page, config):
    """
    依賴context fixture，執行一次性登入
    """
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
    return e2e_logged_in_page.get_auth_token()

@pytest.fixture(scope="session")
def e2e_main_page(e2e_logged_in_page, page):
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
    api_username = config.get(site, 'username')
    api_password = config.get(site, 'password')

    # 實例化 APIClient
    return APIClient(base_url, api_username, api_password)

@pytest.fixture(scope="session")
def api_manager(api_client):
    manager = APIManager(api_client)
    manager.authenticate()
    return manager