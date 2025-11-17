from time import sleep
import allure
import pytest
import requests
from src.pages.spg.lobby_page import LobbyPage

@pytest.mark.e2e
@allure.step("測試大廳的賠率顯示")
def test_check_odd(logged_page: LobbyPage, auth_token: str, config):
    logged_page.wait_for_load_state('domcontentloaded')
    logged_page.is_element_visible("div.p-new20")

    base_url = config.get('spg', 'base_url')
    username = config.get('spg', 'username')
    # 先初始化狀態為"含本金顯示"
    headers = {"Content-Type": "application/json", "sssmbid": username, "ssstoken": auth_token}
    url = f"https://{base_url}/api/GameInfo/FrontEvn/save"
    payload = {"SetJson": "{\"includePrincipal\":true,\"tableSort\":0,\"acceptBetter\":true,\"showBetConfirm\":true,\"autoSwitchToStrayMode\":true,\"defaultAmount\":{\"type\":0,\"amount\":100},\"defaultStrayAmount\":{\"type\":0,\"amount\":100},\"preferChips\":[100,500,1000,2000],\"i18nLocale\":\"tw\",\"theme\":\"\",\"tableLines\":1}"}
    response = requests.post(url, headers=headers, json=payload)
    assert response.status_code == 200
    sleep(1)
    logged_page.reload()
    logged_page.select_game("足球")
    # 比較賠率
    before_odd = logged_page.extract_odd()
    logged_page.switch_principal()
    after_odd = logged_page.extract_odd()
    assert abs(after_odd - (before_odd - 1)) < 0.0001

def test_betting(logged_page: LobbyPage):
    betting_odd = logged_page.bet()
    record_odd = logged_page.get_record()
    assert betting_odd == record_odd, f"bet: {betting_odd}, record: {record_odd}"