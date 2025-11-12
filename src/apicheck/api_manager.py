from src.apicheck.api_client import APIClient
from src.services.admin import AdminService

class APIManager:
    """統一管理所有服務"""
    def __init__(self, client: APIClient):
        self.client = client
        self._admin = None

    def authenticate(self):
        return self.client.authenticate()

    @property
    def admin(self):
        if self._admin is None:
            self._admin = AdminService(self.client, self.client.base_url)
        return self._admin