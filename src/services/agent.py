from src.services.base_service import BaseService
from src.config import Config

class AgentService(BaseService):
    def __init__(self, client, base_url):
        super().__init__(client, base_url)
        self.endpoint = f"{base_url}"

    def get_info(self):
        url = f"{self.endpoint}/Home/MemStatus"
