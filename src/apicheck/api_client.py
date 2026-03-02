import requests
import re
from abc import ABC, abstractmethod

class AuthStrategy(ABC):
    """子類別必須實作其抽象方法，無法直接實例"""
    @abstractmethod
    def authenticate(self, session, base_url, credentials):
        pass

    @abstractmethod
    def login_url(self, base_url):
        pass

class AdminAuthStrategy(AuthStrategy):
    def login_url(self, base_url):
        return f"{base_url}/api/users/authenticate"

    def authenticate(self, session, base_url, credentials):
        payload = {
            "username": credentials.get("username"),
            "password": credentials.get("password")
        }
        login_url = self.login_url(base_url)
        response = session.post(login_url, json=payload, allow_redirects=False, verify=False)

        if response.status_code != 200:
            raise Exception(f"Admin 登入失敗: {response.text}")

        if ".AspNetCore.Cookies" not in session.cookies:
            raise Exception("Admin 登入成功但沒有儲存cookies")

        return True

class AgentAuthStrategy(AuthStrategy):
    def login_url(self, base_url):
        return f"{base_url}/Home/Login"

    def authenticate(self, session, base_url, credentials):
        """
        1. GET 登入頁面取得CSRF Token
        2. POST 表單資料進行登入
        3. 驗證 JSON 回應
        """
        # 設定 Agent 專用 Headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })
        # 取得登入頁面
        login_url = self.login_url(base_url)
        response_get = session.get(login_url, verify=False)

        if response_get.status_code != 200:
            raise Exception(f"無法訪問 Agent 登入頁面: {response_get.status_code}")
        # 取得 CSRD Token
        token = r'name=__RequestVerificationToken type=hidden value=([a-zA-Z0-9_-]+)'
        match = re.search(token, response_get.text)

        if not match:
            raise Exception("無法從 HTML 中擷取 Token")
        verification_token = match.group(1)
        # 觸發登入api
        payload = {
            "__RequestVerificationToken": verification_token,
            "txtac": credentials.get("username"),
            "txtpd": credentials.get("password")
        }
        auth_url = f"{base_url}/Home/Authenticate"
        response = session.post(auth_url, data=payload)

        try:
            result = response.json()
            if result.get("status") == 1:
                return True
            else:
                raise Exception(f"Agent 登入失敗: {result.get('msg')}")
        except ValueError:
            raise Exception(f"Agent 登入回應格式異常: {response.text}")

class APIClient:
    def __init__(self, base_url, auth_strategy: AuthStrategy, credentials: dict):
        """
        Args:
            base_url: API基礎URL
            auth_strategy: 認證的策略物件
            credentials: 認證物件
        """
        self.base_url = base_url
        self.auth_strategy = auth_strategy
        self.credentials = credentials
        self.session = requests.Session()
        self._authenticated = False

    def authenticate(self):
        if self._authenticated:
            return True

        self._authenticated = self.auth_strategy.authenticate(
            self.session, self.base_url, self.credentials
        )
        return self._authenticated

    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs, verify=False)

    def post(self, url, **kwargs):
        return self.session.post(url, **kwargs, verify=False)

    def put(self, url, **kwargs):
        return self.session.put(url, **kwargs, verify=False)

    def delete(self, url, **kwargs):
        return self.session.delete(url, **kwargs, verify=False)