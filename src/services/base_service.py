class BaseService:
    def __init__(self, client, base_url):
        self.client = client
        self.base_url = base_url