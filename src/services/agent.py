from src.services.base_service import BaseService
from src.apicheck.api_client import AgentAuthStrategy
from src.config import Config
import re
import json
import base64
import requests
from pathlib import Path

class AgentService(BaseService):
    auth_strategy_class = AgentAuthStrategy
    def __init__(self, client, base_url):
        super().__init__(client, base_url)
        self.endpoint = f"{base_url}"

    def login_flow(self, username, password):
        session = requests.Session()    #獨立session
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })

        login_url = f"{self.endpoint}/Home/Login"
        response_get = session.get(login_url, verify=False)

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
        return session.post(auth_url, data=payload, verify=False)

    def add_cash(self, cash: int):
        url = f"{self.endpoint}/Mem/addCash"
        payload = {"pmid": Config.Testdata.ag_account, "mid": Config.Testdata.transfer_member, "cash": cash}
        return self.client.post(url, data=payload)

    def disable(self, agent_id):
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

    def add_subadmin(self):
        url = f"{self.endpoint}/Mem/subAdd"
        payload = {
            "pmid": Config.Testdata.up_account,
            "mid": Config.Testdata.ts,
            "mname": Config.Testdata.ts,
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

    def del_subadmin(self):
        url = f"{self.endpoint}/Mem/del"
        payload = {
            "mid": Config.Testdata.ts
        }
        response =  self.client.post(url, data=payload)
        if response.json().get("Status") == 0:
            return True
        else:
            raise Exception("子帳號刪除失敗，請手動重現")

    def query_member(self, member_id):
        url = f"{self.endpoint}/Mem/QueryMem"
        payload = {"mid": member_id}
        response = self.client.post(url, data=payload)
        return response.json()

    def add_member(self):
        url = f"{self.endpoint}/Mem/SaveMemID2"
        payload_path = Path(__file__).parent / "add_member_payload.json"
        with payload_path.open(encoding="utf-8") as f:
            data = json.load(f)
        data["PMemID"] = Config.Testdata.up_account
        body = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload = {"pars": base64.b64encode(body).decode("ascii")}
        response = self.client.post(url, data=payload)
        if response.json().get("MemID"):
            return response.json()["MemID"]
        else:
            raise Exception("建立失敗，請手動重現")

    def del_member(self, mid):
        url = f"{self.endpoint}/Mem/del"
        payload = {"mid": mid}
        return  self.client.post(url, data=payload)

    def query_level_data(self):
        url = f"{self.endpoint}/Mem/LevelDataQuery"
        columns = [
            "MemID", "MemName", "ChildCount", "DirectCount", "Level0Count",
            "DepositType", "CreditLimitSport", "CreditUsedSport", "DelayType",
            "LockFlag", "LockBetFlag", "11", "share", "Remarks",
        ]
        payload = {
            "draw": 1,
            "start": 0,
            "length": 100,
            "search[value]": "",
            "search[regex]": "false",
            "pid": Config.Testdata.up_account,
            "enable": -1,
            "mid": "",
        }
        for i, col in enumerate(columns):
            payload[f"columns[{i}][data]"] = col
            payload[f"columns[{i}][name]"] = ""
            payload[f"columns[{i}][searchable]"] = "true"
            payload[f"columns[{i}][orderable]"] = "false"
            payload[f"columns[{i}][search][value]"] = ""
            payload[f"columns[{i}][search][regex]"] = "false"
        return self.client.post(url, data=payload)

    def query_game(self):
        url = f"{self.endpoint}/Ball/query"
        return self.client.post(url)

    def query_bill(self):
        url = f"{self.endpoint}/bill/billQ"
        return self.client.post(url)

    def query_billType(self):
        url = f"{self.endpoint}/bill/billTypeQ"
        payload = {
          "ticketTime": "acctime",
          "ballType": "-1",
          "acqType": "-1",
          "dateS": Config.Testdata.FORMATTED_DATE,
          "dateE": Config.Testdata.FORMATTED_DATE,
          "memAID": "-1",
          "finished": "-1"
        }
        return self.client.post(url, data=payload)

    def query_billGame(self):
        url = f"{self.endpoint}/bill/billGameQ"
        payload = {
          "ticketTime": "acctime",
          "ballType": "-1",
          "acqType": "-1",
          "dateS": Config.Testdata.FORMATTED_DATE,
          "dateE": Config.Testdata.FORMATTED_DATE,
          "memAID": "-1",
          "memID": "-1",
          "finished": "-1"
        }
        return self.client.post(url, data=payload)

    def query_billAlert(self):
        url = f"{self.endpoint}/bill/billAlertQ"
        payload = {
          "ticketTime": "acctime",
          "ballType": "-1",
          "acqType": "-1",
          "dateS": Config.Testdata.FORMATTED_DATE,
          "dateE": Config.Testdata.FORMATTED_DATE,
          "memAID": "-1",
          "memID": "-1",
          "finished": "-1"
        }
        return self.client.post(url, data=payload)

    def query_billCancel(self):
        url = f"{self.endpoint}/bill/billCancelQ"
        payload = {
          "ticketTime": "acctime",
          "ballType": "-1",
          "acqType": "-1",
          "dateS": Config.Testdata.FORMATTED_DATE,
          "dateE": Config.Testdata.FORMATTED_DATE,
          "memAID": "-1",
          "memID": "-1",
          "finished": "-1"
        }
        return self.client.post(url, data=payload)

    def query_billPending(self):
        url = f"{self.endpoint}/bill/billPendingQ"
        payload = {
          "ticketTime": "acctime",
          "ballType": "-1",
          "acqType": "-1",
          "dateS": Config.Testdata.FORMATTED_DATE,
          "dateE": Config.Testdata.FORMATTED_DATE,
          "memAID": "-1",
          "memID": "-1",
          "finished": "-1"
        }
        return self.client.post(url, data=payload)

    def kickout_member(self, member_id):
        url = f"{self.endpoint}/Mem/kickMem"
        payload = {"mid": member_id}
        return self.client.post(url, data=payload)

    def ss_create_user(self):
        url = f"{Config.Testdata.ssapi_url}/api/Sport"
        payload = {
            "Cmd": "CreateUser",
            "VendorId": Config.Testdata.ssapi_vendor,
            "Signature": Config.Testdata.ssapi_sign,
            "User": "test" + Config.Testdata.FORMATTED_TIME,
            "Password": "a12345",
            "Name": "R_test",
            "Upaccount": Config.Testdata.ssapi_upaccount
            }
        response = self.client.post(url, data=payload)
        user = Config.Testdata.ssapi_upaccount + "_" + str(response.json()["Data"]["User"])
        return user

    # def ss_login_url(self):
    #     url = f"{Config.Testdata.ssapi_url}/api/Sport"
    #     payload = {
    #         "Cmd": "LoginGame",
    #         "VendorId": Config.Testdata.ssapi_vendor,
    #         "Signature": Config.Testdata.ssapi_sign,
    #         "User": "test" + Config.Testdata.FORMATTED_TIME,
    #         }
    #     response = self.client.post(url, data=payload)
    #     response_json = response.json()
    #     if response_json.get("Message") != "登入成功" and response_json.get("Code") == 200:
    #         raise Exception("登入失敗，請檢查訪問參數")
    #
    #     url_data = response_json.get("Data")
    #     pc_url = url_data.get("RedirectUrl")
    #     m_url = url_data.get("MobileRedirectUrl")
    #     return pc_url, m_url
    #
    # def ss_transfer(self, type):
    #     url = f"{Config.Testdata.ssapi_url}/api/Sport"
    #     payload = {
    #         "Cmd": "TransferPoint",
    #         "VendorId": Config.Testdata.ssapi_vendor,
    #         "Signature": Config.Testdata.ssapi_sign,
    #         "User": "test" + Config.Testdata.FORMATTED_TIME,
    #         "Point": "1",
    #         "TType": type,
    #         "OrderId": Config.Testdata.ts
    #         }
    #     return self.client.post(url, data=payload)
    #
    # def ss_get_point(self):
    #     url = f"{Config.Testdata.ssapi_url}/api/Sport"
    #     payload = {
    #         "Cmd": "GetUserBalance",
    #         "VendorId": Config.Testdata.ssapi_vendor,
    #         "Signature": Config.Testdata.ssapi_sign,
    #         "User": "test" + Config.Testdata.FORMATTED_TIME
    #     }
    #     return self.client.post(url, data=payload)