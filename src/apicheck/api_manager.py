from src.apicheck.api_client import APIClient
from src.services.admin import AdminService
from src.services.agent import AgentService

class APIManager:
    """
    每個 service 從 config 對應 section 各自讀 base_url 和帳密。
    section 名稱即 service 名稱（admin、agent）。
    """
    def __init__(self, config):
        self.config = config
        self._admin = None
        self._agent = None

    def _build_service(self, service_class, section):
        if service_class.auth_strategy_class is None:
            raise ValueError(f"{service_class.__name__} 未定義 auth_strategy_class")
        base_url = self.config.get(section, "base_url")
        credentials = {
            "username": self.config.get(section, "username"),
            "password": self.config.get(section, "password"),
        }
        strategy = service_class.auth_strategy_class()
        client = APIClient(base_url, strategy, credentials)
        client.authenticate()
        return service_class(client, base_url)

    @property
    def admin(self):
        if self._admin is None:
            self._admin = self._build_service(AdminService, "admin")
        return self._admin

    @property
    def agent(self):
        if self._agent is None:
            self._agent = self._build_service(AgentService, "agent")
        return self._agent

    def reset_agent_client(self):
        self._agent = None