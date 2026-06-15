import pytest
from src.config import Config

ACCOUNTS = {
    "sub":      {"username": "a3666", "password": "qwer1234"},  #subagent子代理
    "invalid_2": {"username": "a366",  "password": "test1234"}, #下層
    "wrong_pw": {"username": "a953",   "password": "!@#$"},     #錯誤密碼
}

TOGGLE_ACCOUNTS = {
    "alpha": {"username": "a533",  "password": "test1234"},  # 初始狀態: 停用
    "beta":  {"username": "a536", "password": "test1234"},    # 初始狀態: 啟用
}

@pytest.fixture(scope="session")
def disabled_account(api_manager):
    """偵測目前哪個 toggle 帳號為停用狀態"""
    for key, creds in TOGGLE_ACCOUNTS.items():
        response = api_manager.agent.login_flow(**creds)
        if response.json().get("status") == -1:
            return key
    pytest.fail("找不到已停用帳號，請確認 alpha/beta 其中一個為停用狀態")

@pytest.mark.apicheck
def test_transfer(api_manager):
    response_in = api_manager.agent.add_cash(1)
    assert response_in.status_code == 200
    assert response_in.json()["Status"] == 0
    response_out = api_manager.agent.add_cash(-1)
    assert response_out.status_code == 200
    assert response_out.json()["Status"] == 0

@pytest.mark.apicheck
def test_subadmin(api_manager):
    api_manager.agent.add_subadmin()
    api_manager.agent.del_subadmin()


@pytest.mark.apicheck
def test_ssapi_create(api_manager):
    user = api_manager.agent.ss_create_user()
    response = api_manager.agent.query_member(user)
    assert response['Status'] == 1
    assert response['Message'] == "操作成功"
    assert response['Data']['MemID'] == user
    assert response['Data']['arylv'] == [Config.Testdata.ssapi_vendor, Config.Testdata.ssapi_upaccount]

@pytest.mark.apicheck
def test_level_data_query(api_manager):
    member_id = api_manager.agent.add_member()
    response = api_manager.agent.del_member(member_id)
    assert response.json()['Status'] == 3
    query_res = api_manager.agent.query_level_data()
    assert query_res.json()['draw'] == 1

@pytest.mark.apicheck
def test_query_game(api_manager):
    response = api_manager.agent.query_game()
    assert response.status_code == 200
    assert 'L' in response.json()

@pytest.mark.apicheck
def test_query_bill(api_manager):
    response = api_manager.agent.query_bill()
    assert response.status_code == 200
    response_type = api_manager.agent.query_billType()
    assert response_type.status_code == 200
    assert 'Data' in response_type.json()
    response_game = api_manager.agent.query_billGame()
    assert response_game.status_code == 200
    assert 'Data' in response_game.json()
    response_alert = api_manager.agent.query_billAlert()
    assert response_alert.status_code == 200
    assert 'Data' in response_alert.json()
    response_cancel = api_manager.agent.query_billCancel()
    assert response_cancel.status_code == 200
    assert 'Data' in response_cancel.json()
    response_pending = api_manager.agent.query_billPending()
    assert response_pending.status_code == 200
    assert 'Data' in response_pending.json()

@pytest.mark.apicheck
def test_login_success(api_manager):
    response = api_manager.agent.login_flow(**ACCOUNTS["sub"])
    assert response.status_code == 200

@pytest.mark.apicheck
def test_login_invalid_account(api_manager, disabled_account):
    response = api_manager.agent.login_flow(**TOGGLE_ACCOUNTS[disabled_account])
    assert response.json()["status"] == -1
    assert response.json()["msg"] == "帳號已被停用，請聯絡管理員!"

@pytest.mark.apicheck
def test_login_enable_account(api_manager, disabled_account, reset_agent_client):
    other_slot = "beta" if disabled_account == "alpha" else "alpha"

    # 先完成所有需要主 session 的操作，再呼叫 login_flow
    api_manager.agent.disable(TOGGLE_ACCOUNTS[disabled_account]["username"])  # 啟用
    api_manager.agent.disable(TOGGLE_ACCOUNTS[other_slot]["username"])          # 停用（為下次準備）

    response = api_manager.agent.login_flow(**TOGGLE_ACCOUNTS[disabled_account])
    assert response.status_code == 200

@pytest.mark.apicheck
def test_login_wrong_password(api_manager):
    response = api_manager.agent.login_flow(**ACCOUNTS["wrong_pw"])
    assert response.json()["status"] == -1
    assert response.json()["msg"] in ["【登入密碼錯誤】第1/3次，連續錯誤將會鎖定帳號", "【登入密碼錯誤】第2/3次，連續錯誤將會鎖定帳號", "【登入密碼錯誤】第3/3次，連續錯誤將會鎖定帳號", "帳號已被鎖定，請管理員!"]

@pytest.mark.apicheck
def test_kickout(api_manager):
    response = api_manager.agent.kickout_member('superag')
    assert response.status_code == 200
    assert response.json()["Status"] == 1