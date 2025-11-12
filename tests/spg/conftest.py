import pytest
import requests
from playwright.sync_api import Page
from src.pages.spg.lobby_page import LobbyPage

@pytest.fixture(scope="session")
def e2e_logged_in_page(page: Page, config):
    """
    spg 專用登入流程：透過 API 取得 RedirectUrl
    """
    site = config.get('DEFAULT', 'site')

    if site != 'spg':
        pytest.skip(f"This fixture is only for bsite, current site: {site}")

    base_url = config.get(site, 'base_url')

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
        assert message == "登入成功", f"登入失敗: {message}"
        redirect_url = response_json['Data']['RedirectUrl']
        # 載入頁面到空白的page中，再封裝回自定義的page
        page.goto(redirect_url)
        lobby_page = LobbyPage(page, config)

        return lobby_page

    except requests.exceptions.RequestException as e:
        pytest.fail(f"請求失敗，無法取得登入 URL: {e}")
    except (KeyError, AssertionError) as e:
        pytest.fail(f"回應格式錯誤或驗證失敗: {e}")

@pytest.fixture(scope="session")
def e2e_auth_token(e2e_logged_in_page: LobbyPage):
    token = e2e_logged_in_page.get_auth_token()
    return token