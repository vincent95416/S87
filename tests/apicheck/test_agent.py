import pytest
from src.config import Config
from itertools import product

ACCOUNTS = {
    "sub":      {"username": "a3666", "password": "qwer1234"},  #subagent子代理
    "invalid_2": {"username": "a366",  "password": "test1234"}, #下層
    "wrong_pw": {"username": "a366",   "password": "!@#$"},     #錯誤密碼
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
    assert response_in.status_code == 200, f"addCash +1 HTTP {response_in.status_code}: {response_in.text[:300]}"
    assert response_in.json()["Status"] == 0, f"addCash +1 回應: {response_in.text[:300]}"
    response_out = api_manager.agent.add_cash(-1)
    assert response_out.status_code == 200, f"addCash -1 HTTP {response_out.status_code}: {response_out.text[:300]}"
    assert response_out.json()["Status"] == 0, f"addCash -1 回應: {response_out.text[:300]}"

@pytest.mark.apicheck
def test_subadmin(api_manager):
    api_manager.agent.add_subadmin()
    api_manager.agent.del_subadmin()

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
def test_ssapi_create(api_manager):
    user = api_manager.agent.ss_create_user()
    response = api_manager.agent.query_member(user)
    assert response['Status'] == 1
    assert response['Message'] == "操作成功"
    assert response['Data']['MemID'] == user
    assert response['Data']['arylv'] == [Config.Testdata.ssapi_vendor, Config.Testdata.ssapi_upaccount]

