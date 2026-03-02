from src.apicheck.api_client import APIClient
from src.services.admin import AdminService
from src.services.agent import AgentService

class APIManager:
    """統一管理所有服務"""
    def __init__(self, client: APIClient):
        self.client = client
        self._admin = None
        self._agent = None

    def authenticate(self):
        return self.client.authenticate()

    @property
    def admin(self):
        if self._admin is None:
            self._admin = AdminService(self.client, self.client.base_url)
        return self._admin

    @property
    def agent(self):
        if self._agent is None:
            self._agent = AgentService(self.client, self.client.base_url)
        return self._agent