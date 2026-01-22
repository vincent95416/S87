import json
import allure
import pytest
import requests
from src.config import Config
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
    payload = {"SetJson": json.dumps(settings, separators=(",", ":"))}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    try:
        response_json = response.json()
    except ValueError:
        raise RuntimeError(f"回傳內容非有效Json: {response.text}")
    if response_json['code'] != 200:
        raise ValueError(f"設定失敗，{response_json}")
    return True

@pytest.mark.e2e
@allure.step("測試大廳的賠率顯示")
def test_check_odd(e2e_main_page: Page, e2e_auth_token: str, config, request):
    game = request.config.getoption("--game")
    base_url = config.get('new20', 'base_url')
    username = config.get('new20', 'username')
    lobby_page = LobbyPage(e2e_main_page, config)
    lobby_page.wait_for_load_state()
    _set_principal_display(base_url, username, e2e_auth_token, include_principal=True)
    lobby_page.reload()
    # 比較賠率
    before_odd = lobby_page.extract_odd()
    lobby_page.switch_principal()
    after_odd = lobby_page.extract_odd()
    assert abs(after_odd - (before_odd - 1)) < 0.0001
    lobby_page.is_element_visible("div.games-menu")
    lobby_page.select_game(game)

@pytest.mark.e2e
def test_betting(e2e_main_page: Page, config):
    lobby_page = LobbyPage(e2e_main_page, config)
    betting_odd, betting_payout = lobby_page.bet()
    record_page = lobby_page.navigate_to_betting_records()
    record_page.wait_for_load_state("networkidle")
    record_odd = record_page.extract_record_odd()
    record_payout = record_page.extract_record_payout()
    assert betting_odd == record_odd, f"bet: {betting_odd}, record: {record_odd}"
    assert betting_payout == record_payout, f"bet: {betting_payout}, record: {record_payout}"

    ticket_id = record_page.extract_record_ticket()
    # 管端驗證
    ag_base_url = config.get('ag', 'base_url')
    ag_session = BettingRecordPage.get_agent_session(config)
    ag_payload = {"ticketid": ticket_id}
    ag_response = ag_session.post(url=f"{ag_base_url}/bill/billTicketQ", data=ag_payload)
    ag_response_json = ag_response.json()
    assert ag_response.status_code == 200
    assert len(ag_response_json['Data']) > 0, "管端注單搜尋的Data List為空"
    assert str(ag_response_json['Data'][0]['TicketID']) == ticket_id, f"注單 :{ticket_id}無法在管端查詢到"
    # 控端驗證
    ct_base_url = config.get('ct', 'base_url')
    ct_session = BettingRecordPage.get_controller_session(config)
    ct_payload = {"RptDate":"TDate","Status":"Y","finish":"0","DateS":Config.Testdata.FORMATTED_DATE,"DateE":Config.Testdata.TOMORROW,"SiteID":-1,"BetNo":ticket_id,"Span":1}
    ct_response = ct_session.post(url=f"{ct_base_url}/api/ballen/ticketquery", json=ct_payload)
    ct_response_json = ct_response.json()
    assert ct_response.status_code == 200
    assert len(ct_response_json['Data']) > 0, "控端注單搜尋的Data List為空"
    assert str(ct_response_json['Data'][0]['ticketid']) == ticket_id, f"注單 :{ticket_id}無法在控端查詢到"