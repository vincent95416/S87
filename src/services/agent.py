from src.services.base_service import BaseService
from src.apicheck.api_client import AgentAuthStrategy
from src.config import Config
import re

class AgentService(BaseService):
    auth_strategy_class = AgentAuthStrategy
    def __init__(self, client, base_url):
        super().__init__(client, base_url)
        self.endpoint = f"{base_url}"

    def login_flow(self, username, password):
        login_url = f"{self.endpoint}/Home/Logout"
        response_get = self.client.get(login_url)

        if response_get.status_code != 200:
            raise Exception(f"無法訪問 Agent 登入頁面: {response_get.status_code}")
        # 取得 CSRD Token
        token = r'name=__RequestVerificationToken type=hidden value=([a-zA-Z0-9_-]+)'
        match = re.search(token, response_get.text)

        if not match:
            raise Exception("無法從 HTML 中擷取 Token", response_get.text)
        verification_token = match.group(1)
        # 觸發登入api
        payload = {
            "__RequestVerificationToken": verification_token,
            "txtac": username,
            "txtpd": password
        }
        auth_url = f"{self.endpoint}/Home/Authenticate"
        return self.client.post(auth_url, data=payload)

    def add_cash(self, up_mb, mb, cash: int):
        url = f"{self.endpoint}/Home/addCash"
        payload = {"pmid": up_mb, "mb": mb, "cash": cash}
        return self.client.post(url, data=payload).json()

    def ss_create_user(self):
        url = f"{Config.Testdata.ssapi_url}/api/Sport"
        payload = {
            "Cmd": "CreateUser",
            "VendorId": Config.Testdata.ssapi_vendor,
            "Signature": Config.Testdata.ssapi_sign,
            "User": "test" + Config.Testdata.FORMATTED_TIME,
            "Password": "a12345",
            "Name": "R_test",
            "Upaccount": Config.Testdata.ssapi_up_account
            }
        return self.client.post(url, data=payload)

    def ss_login_url(self):
        url = f"{Config.Testdata.ssapi_url}/api/Sport"
        payload = {
            "Cmd": "LoginGame",
            "VendorId": Config.Testdata.ssapi_vendor,
            "Signature": Config.Testdata.ssapi_sign,
            "User": "test" + Config.Testdata.FORMATTED_TIME,
            }
        response = self.client.post(url, data=payload)
        response_json = response.json()
        if response_json.get("Message") != "登入成功" and response_json.get("Code") == 200:
            raise Exception("登入失敗，請檢查訪問參數")

        url_data = response_json.get("Data")
        pc_url = url_data.get("RedirectUrl")
        m_url = url_data.get("MobileRedirectUrl")
        return pc_url, m_url

    def ss_transfer(self, type):
        url = f"{Config.Testdata.ssapi_url}/api/Sport"
        payload = {
            "Cmd": "TransferPoint",
            "VendorId": Config.Testdata.ssapi_vendor,
            "Signature": Config.Testdata.ssapi_sign,
            "User": "test" + Config.Testdata.FORMATTED_TIME,
            "Point": "1",
            "TType": type,
            "OrderId": Config.Testdata.ts
            }
        return self.client.post(url, data=payload)

    def ss_add_cash(self):
        pass

    def ss_get_point(self):
        url = f"{Config.Testdata.ssapi_url}/api/Sport"
        payload = {
            "Cmd": "GetUserBalance",
            "VendorId": Config.Testdata.ssapi_vendor,
            "Signature": Config.Testdata.ssapi_sign,
            "User": "test" + Config.Testdata.FORMATTED_TIME
        }
        return self.client.post(url, data=payload)

    def ss_disable(self, agent_id):
        url = f"{self.endpoint}/Mem/disable"
        payload = {
            "mid": agent_id,
            "value": -1
        }
        response = self.client.post(url, data=payload)
        if response.json().get("Status") == 1:
            return True
        else:
            raise Exception("啟用/禁用失敗，請手動重現")

    def add_subadmin(self, up_account):
        url = f"{self.endpoint}/Mem/subAdd"
        payload = {
            "pmid": up_account,
            "mid": "super_robot",
            "mname": "super_robot",
            "mpw": "a12345",
            "mcpw": "a12345",
            "memPerms": 0,
            "LockFlag": 0,
            "OTPEnabled": "false"
        }
        response =  self.client.post(url, data=payload)
        if response.json().get("Status") == 1:
            return True
        else:
            raise Exception("子帳號建立失敗，請手動重現")

    def del_subadmin(self, sub_id):
        url = f"{self.endpoint}/Mem/del"
        payload = {
            "mid": sub_id
        }
        response =  self.client.post(url, data=payload)
        if response.json().get("Status") == 1:
            return True
        else:
            raise Exception("子帳號刪除失敗，請手動重現")