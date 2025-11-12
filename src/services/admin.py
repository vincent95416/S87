from src.services.base_service import BaseService
from src.config import Config

class AdminService(BaseService):
    def __init__(self, client, base_url):
        super().__init__(client, base_url)
        self.endpoint = f"{base_url}"

    def get_menu(self):
        url = f"{self.endpoint}/api/users/menu"
        response = self.client.get(url)
        return response

    def get_history(self, cat_id, game_type):
        url = f"{self.endpoint}/api/Trader/queryCommHis"
        payload = {
          "pageSize": 1,
          "ADate": Config.Testdata.FORMATTED_DATE,
          "CatID": cat_id,
          "GameType": game_type,
          "Idx": 0,
          "Sort": 0
        }
        return self.client.post(url, json=payload)

    def get_games(self, cat_id, game_type):
        url = f"{self.endpoint}/api/Trader/queryComm"
        payload = {
            "pageSize":1, "CatId":cat_id, "GameType":game_type, "Sort":0,
            "AcqFSites":Config.Testdata.ACQSITE
        }
        response = self.client.post(url,json=payload)
        return response

    def get_report(self):
        url = f"{self.endpoint}/api/rptbill/bill"
        payload = {"AL":"","SiteID":-1}
        response = self.client.post(url, json=payload)
        return response

