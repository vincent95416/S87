class BaseService:
    auth_strategy_class = None

    def __init__(self, client, base_url):
        self.client = client
        self.base_url = base_url