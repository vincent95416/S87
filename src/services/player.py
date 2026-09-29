from src.services.base_service import BaseService
from src.apicheck.api_client import PlayerAuthStrategy
from src.config import Config

class PlayerService(BaseService):
    auth_strategy_class = PlayerAuthStrategy
    def front_config(self):
        url = f"{self.base_url}/api/GameInfo/FrontEvn/Config"
        return self.client.post(url)

    def front_save(self, string):
        url = f"{self.base_url}/api/GameInfo/FrontEvn/save"
        payload = {"SetJson": string}
        return self.client.post(url, json=payload)

    def front_layout(self):
        url = f"{self.base_url}/api/mb/info/setfrontlayout"
        payload = {"FrontLayout":1}
        return self.client.post(url, json=payload)

    def member_profile(self):
        url = f"{self.base_url}/api/mb/info/about"
        return self.client.post(url)

    def query_cash(self):
        url = f"{self.base_url}/api/mb/info/cash"
        return self.client.post(url)

    def query_nickname(self):
        url = f"{self.base_url}/api/mb/info/setNickname"
        payload = {"NickName":""}
        return self.client.post(url, json=payload)

    def get_menu(self):
        url = f"{self.base_url}/api/GameInfo/Menu"
        return self.client.post(url)

    def get_menu_v1(self):
        url = f"{self.base_url}/api/V1/GameInfo/Menu"
        return self.client.post(url)

    def get_game(self):
        url = f"{self.base_url}/api/GameInfo/GameDetail"
        payload = {"CatID":888888,"WagerTypeKey":888888,"show":0}
        return self.client.post(url, json=payload)

    def get_game_v1(self):
        url = f"{self.base_url}/api/v1/GameInfo/GameDetail"
        payload = {"CatID":888888,"WagerTypeKey":888888,"show":0}
        return self.client.post(url, json=payload)

    def get_list_small(self, game_type, cat_id):
        url = f"{self.base_url}/api/GameInfo/GamelistSmall"
        payload = {"GameType":game_type,"CatID":cat_id,"WagerTypeKey":1}
        return self.client.post(url, json=payload)

    def get_max_win(self):
        url = f"{self.base_url}/api/GameInfo/GetParlayLevelMaxWin"
        return self.client.post(url)

    def get_bet_history(self, is_set: bool):
        url = f"{self.base_url}/api/GameInfo/Ticket/betHistory"
        payload = {"isset":is_set,"page":1,"pagesize":50,"starttime":Config.Testdata.FORMATTED_DATE,"endtime":Config.Testdata.FORMATTED_DATE}
        return self.client.post(url, json=payload)

    def get_game_result(self):
        url = f"{self.base_url}/api/GameInfo/GameResult"
        payload = {"CatID":1,"LeagueIDs":"","ScheduleTime":Config.Testdata.FORMATTED_DATE}
        return self.client.post(url, json=payload)

    def get_game_result_v1(self):
        url = f"{self.base_url}/api/v1/GameInfo/GameResult"
        payload = {"CatID":1,"LeagueIDs":"","ScheduleTime":Config.Testdata.FORMATTED_DATE}
        return self.client.post(url, json=payload)

    def get_live_link(self):
        url = f"{self.base_url}/api/GameInfo/LiveLinkGame"
        payload = {}
        return self.client.post(url, json=payload)