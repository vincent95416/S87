import pytest
import datetime
import os
import configparser
import requests
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import Page
from spg.pages.lobby_page import LobbyPage

@pytest.fixture(scope="session")
def config(request):
    """
    讀取環境設定黨，傳遞到測試入口
    """
    env = request.config.getoption("--env")
    site = request.config.getoption("--site")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "env", f"{env}.ini")

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
        os.makedirs(video_dir, exist_ok=True)

        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 2560, "height": 1440}, record_video_dir = video_dir, record_video_size ={"width": 2560, "height": 1440})
        page = context.new_page()
        page.set_default_timeout(5000)
        yield page

        video_path = page.video.path()

        context.close()
        browser.close()

        now = datetime.datetime.now()
        new_filename = now.strftime("%Y%m%d_%H%M%S") + ".webm"
        new_path = os.path.join(video_dir, new_filename)
        os.rename(video_path, new_path)

@pytest.fixture(scope="session")
def logged_page(page: Page, config):

    site = config['spg']
    base_url = site['base_url']
    username = site['username']
    password = site['password']

    url = f'https://ssapi.{base_url}/api/Sport'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        'Cmd': 'LoginGame',
        'VendorId': 'bc55',
        'Signature': 'B97BA6FA8B997E7245835B5AE587DA0E',
        'User': 'p09'
    }
    try:
        response = requests.post(url=url, headers=headers, data=payload, timeout=30, allow_redirects=True)
        response.raise_for_status()
        response_json = response.json()
        message = response_json['Message']
        assert message == "登入成功"
        redirect_url = response_json['Data']['RedirectUrl']
        # 載入頁面到空白的page中，再封裝回自定義的page
        page.goto(redirect_url)
        return LobbyPage(page)

    except requests.exceptions.RequestException as e:
        pytest.fail(f"請求失敗，無法取得登入 URL: {e}")
    except (KeyError, AssertionError) as e:
        pytest.fail(f"回應格式錯誤或驗證失敗: {e}")

@pytest.fixture(scope="session")
def auth_token(logged_page: Page):
    """
    執行登入流程並返回 Session Storage 中的 token。
    這個夾具會自動被 Pytest 調用，並在整個測試會話中只執行一次。
    """
    token = logged_page.get_auth_token()
    return token

# @pytest.fixture(scope="session")
# def main_page(logged_page: LoginPage):
#     """提供已登入的原始 Page 物件"""
#     return logged_page.page