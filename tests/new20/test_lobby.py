import json
from time import sleep
import allure
import requests
from playwright.sync_api import Page
from src.pages.new20.lobby_page import LobbyPage
from src.pages.new20.betting_record_page import BettingRecordPage

def _set_principal_display(base_url: str, username: str, auth_token: str, include_principal: bool) -> bool:
    """
        內部輔助函數：設定賠率顯示方式

        Args:
            base_url: 站點 URL
            username: 用戶名
            auth_token: 認證 token
            include_principal: True=含本金, False=不含本金

        Returns:
            bool: 是否設定成功
    """
    headers = {"Content-Type": "application/json", "sssmbid": username, "ssstoken": auth_token}
    settings = {
        "includePrincipal": include_principal,
        "tableSort": 0,
        "acceptBetter": True,
        "showBetConfirm": True,
        "autoSwitchToStrayMode": True,
        "defaultAmount": {"type": 0, "amount": 100},
        "defaultStrayAmount": {"type": 0, "amount": 100},
        "preferChips": [100, 500, 1000, 2000],
        "i18nLocale": "tw",
        "theme": "",
        "tableLines": 1
    }
    url = f"{base_url}/api/GameInfo/FrontEvn/save"
    payload = {"SetJson": json.dumps(settings)}

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except requests.RequestException as e:
        return False

@allure.step("測試大廳的賠率顯示")
def test_check_odd(e2e_main_page: Page, e2e_auth_token: str, game, config, request):
    game = request.config.getoption("--game")
    base_url = config.get('new20', 'base_url')
    username = config.get('new20', 'username')
    lobby_page = LobbyPage(e2e_main_page, config)
    lobby_page.wait_for_load_state()
    assert lobby_page.is_element_visible("div.games-menu"), "遊戲選單沒顯示"
    assert _set_principal_display(base_url, username, e2e_auth_token, include_principal=True), "設定含本金顯示失敗"
    sleep(1)
    lobby_page.reload()

    lobby_page.select_game(game)
    lobby_page.select_game("棒球")
    # 比較賠率
    before_odd = lobby_page.extract_odd()
    lobby_page.switch_principal()
    after_odd = lobby_page.extract_odd()
    assert abs(after_odd - (before_odd - 1)) < 0.0001

def test_betting(e2e_main_page: Page, config):
    lobby_page = LobbyPage(e2e_main_page, config)
    betting_odd, betting_payout = lobby_page.bet()
    record_page = lobby_page.navigate_to_betting_records()
    record_page.wait_for_load_state("networkidle")
    record_odd = record_page.get_record_odd()
    record_payout = record_page.get_record_payout()
    assert betting_odd == record_odd, f"bet: {betting_odd}, record: {record_odd}"
    assert betting_payout == record_payout, f"bet: {betting_payout}, record: {record_payout}"
