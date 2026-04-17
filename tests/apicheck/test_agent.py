import pytest
from src.config import Config
from itertools import product

ACCOUNTS = {
    "sub":    {"username": "a3666", "password": "qwer1234"},  #subagent子代理
    "invalid": {"username": "a533", "password": "test1234"},   #可停用帳號
    "invalid_2": {"username": "a366", "password": "test1234"}, #被停用的下層
    "wrong_pw": {"username": "a366", "password": "!@#$"},      #錯誤密碼
}

@pytest.mark.apicheck
def test_login_success(api_manager):
    response = api_manager.agent.login_flow(**ACCOUNTS["sub"])
    assert response.status_code == 200

@pytest.mark.apicheck
def test_login_invalid_account_and_reset(api_manager):
    api_manager.agent.ss_disable(ACCOUNTS["invalid"]["username"])
    response = api_manager.agent.login_flow(**ACCOUNTS["invalid"])
    response_2 = api_manager.agent.login_flow(**ACCOUNTS["invalid_2"])
    assert response.json()["status"] == -1 and response_2.json()["status"] == -1
    assert response.json()["msg"] == "帳號已被停用，請聯絡管理員!" and response_2.json()["msg"] == "帳號已被停用，請聯絡上層!"

    # api_manager.agent.ss_disable(ACCOUNTS["invalid"]["username"])
    # response = api_manager.agent.login_flow(**ACCOUNTS["invalid"])
    # response_2 = api_manager.agent.login_flow(**ACCOUNTS["invalid_2"])
    # assert response.status_code == 200 and response_2.status_code == 200

@pytest.mark.apicheck
def test_login_wrong_password(api_manager):
    response = api_manager.agent.login_flow(**ACCOUNTS["wrong_pw"])
    assert response.json()["status"] == -1
    assert response.json()["msg"] in ["【登入密碼錯誤】第1/3次，連續錯誤將會鎖定帳號", "【登入密碼錯誤】第2/3次，連續錯誤將會鎖定帳號", "【登入密碼錯誤】第3/3次，連續錯誤將會鎖定帳號", "帳號已被鎖定，請管理員!"]

@pytest.mark.apicheck
def test_transfer_in(api_manager):
    response = api_manager.agent.ss_transfer(1)
    assert response.json()["Message"] == "Ok"

@pytest.mark.apicheck
def test_transfer_out(api_manager):
    response = api_manager.agent.ss_transfer(0)
    assert response.json()["Message"] == "Ok"