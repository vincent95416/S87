from src.apicheck.api_client import APIClient
from src.services.admin import AdminService
from src.services.agent import AgentService

class APIManager:
    def __init__(self, base_url: str, credentials: dict):
        self.base_url = base_url
        self.credentials = credentials
        self._admin = None
        self._agent = None

    def _build_client(self, service_class):
        if service_class.auth_strategy_class is None:
            raise ValueError(f"{service_class.__name__} 未定義 auth_strategy_class")
        strategy = service_class.auth_strategy_class()
        client = APIClient(self.base_url, strategy, self.credentials)
        client.authenticate()
        return client

    @property
    def admin(self):
        if self._admin is None:
            client = self._build_client(AdminService)
            self._admin = AdminService(client, self.base_url)
        return self._admin

    @property
    def agent(self):
        if self._agent is None:
            client = self._build_client(AgentService)
            self._agent = AgentService(client, self.base_url)
        return self._agent