from time import sleep
import allure
import requests
from new20.pages.lobby_page import LobbyPage
from new20.pages.betting_record_page import BettingRecordPage

@allure.step("測試大廳的賠率顯示")
def test_check_odd(main_page: LobbyPage, auth_token: str, config):
    base_url = config.get('2.0', 'base_url')
    username = config.get('2.0', 'username')
    lobby_page = LobbyPage(main_page)
    lobby_page.wait_for_load_state()
    lobby_page.is_element_visible("div.games-menu")

    # 先初始化狀態為"含本金顯示"
    headers = {"Content-Type": "application/json", "sssmbid": username, "ssstoken": auth_token}
    url = f"{base_url}/api/GameInfo/FrontEvn/save"
    payload = {"SetJson": "{\"includePrincipal\":true,\"tableSort\":0,\"acceptBetter\":true,\"showBetConfirm\":true,\"autoSwitchToStrayMode\":true,\"defaultAmount\":{\"type\":0,\"amount\":100},\"defaultStrayAmount\":{\"type\":0,\"amount\":100},\"preferChips\":[100,500,1000,2000],\"i18nLocale\":\"tw\",\"theme\":\"\",\"tableLines\":1}"}
    response = requests.post(url, headers=headers, json=payload)
    assert response.status_code == 200
    sleep(1)
    lobby_page.reload()
    lobby_page.select_game("棒球")
    # 比較賠率
    before_odd = lobby_page.extract_odd()
    lobby_page.switch_principal()
    after_odd = lobby_page.extract_odd()
    assert abs(after_odd - (before_odd - 1)) < 0.0001

def test_betting(main_page: BettingRecordPage, config):
    lobby_page = LobbyPage(main_page)
    betting_odd, betting_payout = lobby_page.bet()
    record_page = lobby_page.navigate_to_betting_records()
    record_page.wait_for_load_state("networkidle")
    record_odd = record_page.get_record_odd()
    record_payout = record_page.get_record_payout()
    assert betting_odd == record_odd, f"bet: {betting_odd}, record: {record_odd}"
    assert betting_payout == record_payout, f"bet: {betting_payout}, record: {record_payout}"
