import requests

class APIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticated = False

    def authenticate(self):
        if self._authenticated:
            return True

        payload = {
            "username": self.username,
            "password": self.password
        }

        login_url = f"{self.base_url}/api/users/authenticate"
        response = self.session.post(login_url, json=payload, allow_redirects=False, verify=False)

        if response.status_code != 200:
            raise Exception(f"登入失敗, {response.text}")

        if ".AspNetCore.Cookies" not in self.session.cookies:
            raise Exception("登入成功但沒有儲存cookies")

        self._authenticated = True
        return True

    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs, verify=False)

    def post(self, url, **kwargs):
        return self.session.post(url, **kwargs, verify=False)

    def put(self, url, **kwargs):
        return self.session.put(url, **kwargs, verify=False)

    def delete(self, url, **kwargs):
        return self.session.delete(url, **kwargs, verify=False)