from src.services.base_service import BaseService
from src.apicheck.api_client import AdminAuthStrategy
from src.config import Config

class AdminService(BaseService):
    auth_strategy_class = AdminAuthStrategy
    def __init__(self, client, base_url):
        super().__init__(client, base_url)
        self.endpoint = f"{base_url}"

    def get_menu(self):
        url = f"{self.endpoint}/api/users/menu"
        return self.client.get(url)

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
        url = f"{self.endpoint}/api/Trader/queryCommMargin"
        payload = {
            "pageSize":1, "CatId":cat_id, "GameType":game_type, "Sort":0,
            "AcqFSites":Config.Testdata.SITE
        }
        return self.client.post(url,json=payload)

    def get_report(self):
        url = f"{self.endpoint}/api/rptbill/bill"
        payload = {"AL":"","SiteID":-1}
        return self.client.post(url, json=payload)

    def query_order(self):
        url = f"{self.endpoint}/api/ballen/ticketquery"
        payload = {"RptDate":"SDate","Status":"","finish":"",
            "DateS":Config.Testdata.FORMATTED_DATE+" 00:00","DateE":Config.Testdata.FORMATTED_DATE+" 23:59",
            "SiteID":-1,"Member":"","BetNo":"","EvtID":"","Span":1,"betIP":"","ballType":"-1","wagerType":"-1","RowNum":0
        }
        return self.client.post(url, json=payload)

    def query_contest(self):
        url = f"{self.endpoint}/api/game/Query"
        payload = {"qryBy":"date","siteID":1,"ballType":1,"ADate":Config.Testdata.TOMORROW,"TourName":"測試","Span":1}
        response = self.client.post(url, json=payload).json()
        event_id = response["Data"][0]["Data"][0]["children"][0]["AcquEvtID"]
        return event_id

    def create_game(self):
        url = f"{self.endpoint}/api/game/saveGame"
        payload = {
          "type": "game",
          "CatID": 1,
          "GameType": 0,
          "ScheduleDate": Config.Testdata.TOMORROW,
          "ScheduleTime": "00:00",
          "EvtType": 0,
          "TeamIDs": [],
          "title": "新增",
          "LeagueID": 20333,
          "LeagueName": "測試",
          "HomeID": 50255,
          "Home": "河床",
          "AwayID": 50215,
          "Away": "海牙",
          "HomePtid": 0,
          "AwayPtid": 0,
          "EvtTypes": [
            0
          ]
        }
        return self.client.post(url, json=payload)

    def settle_game(self):
        pass

    def event_open(self, event_id):
        url = f"{self.endpoint}/api/BallEn/evtOpen"
        payload = {"CatID":1,"GameType":0,"EvtID":event_id}
        return self.client.post(url, json=payload)
    def event_close(self, event_id):
        url = f"{self.endpoint}/api/BallEn/evtClose"
        payload = {"CatID":1,"GameType":0,"EvtID":event_id}
        return self.client.post(url, json=payload)
    def event_start(self, event_id):
        url = f"{self.endpoint}/api/BallEn/evtStart"
        payload = {"CatID":1,"GameType":0,"EvtID":event_id}
        return self.client.post(url, json=payload)
    def event_stop(self, event_id):
        url = f"{self.endpoint}/api/BallEn/evtStop"
        payload = {"CatID":1,"GameType":0,"EvtID":event_id}
        return self.client.post(url, json=payload)

    def margin_toggle(self, event_id, is_use: int):
        url = f"{self.endpoint}/api/BallEn/toggleUseMargin"
        payload = {"EvtID":event_id,"UseMargin":is_use,"GameType":0}
        return self.client.post(url, json=payload)

    def query_game_id(self, event_id):
        url = f"{self.endpoint}/api/BallEn/gameLogHdp"
        payload = {"EvtID":event_id,"CatID":"1","GameTypes":[0]}
        response = self.client.post(url, json=payload).json()
        return response["Data"]["All"]["Data"][0]["hdps"][0]["GameID"]

    def adjustment_odds(self, event_id, game_id, value):
        url = f"{self.endpoint}/api/BallEn/oddsAdjMargin"
        payload = {"EvtID":event_id,"CatID":1,"isThreeWay":False,"GameID":game_id,"val":value}
        return self.client.post(url, json=payload)

    def query_tournament(self, cat_id, level):
        url = f"{self.endpoint}/api/setting/tourQuery"
        payload = {"ballType":cat_id ,"modid":level ,"Span":1}
        return self.client.post(url, json=payload)

    def query_teams(self, cat_id):
        url = f"{self.endpoint}/api/setting/teamQuery"
        payload = {"ballType": cat_id, "Span": 1}
        return self.client.post(url, json=payload)

    def query_parlay_config(self):
        url = f"{self.endpoint}/api/setting/oddsConfigQuery"
        return self.client.post(url)

    def query_parlay_max(self):
        url = f"{self.endpoint}/api/setting/parlayMaxWinQuery"
        return self.client.post(url)

    def query_odds_default(self, level, site):
        url = f"{self.endpoint}/api/setting/oddsDefaultQuery"
        payload = {"lv":level,"site":site,"play":"full"}
        return self.client.post(url, json=payload)

    def query_currency(self, currency, is_currency: bool):
        url = f"{self.endpoint}/api/setting/currencyList"
        payload = {"StartRow":0,"PageSize":20,"Filter":{"Keyword":"","BaseType":currency,"IsCurrency":is_currency}}
        return self.client.post(url, json=payload)

    def query_margin_list(self, cat_id, level, gametype):
        url = f"{self.endpoint}/api/setting/marginList"
        payload = {"CatID":cat_id,"Lv":level,"GameType":gametype}
        return self.client.post(url, json=payload)

    def query_light_rules(self):
        url = f"{self.endpoint}/api/setting/liveScoutLightRuleQuery"
        payload = {"CommentaryID":"","Span":1}
        return self.client.post(url, json=payload)

    def query_locker(self, member_id, member_level):
        url = f"{self.endpoint}/api/member/memQuery"
        payload = {"memType":-1,"memName":member_id,"level":member_level,"Span":1}
        return self.client.post(url, json=payload)

    def query_locker_type(self):
        url = f"{self.endpoint}/api/member/memTypeQuery"
        payload = {"typeName":"","Span":1}
        return self.client.post(url, json=payload)

    def query_danger_type(self):
        url = f"{self.endpoint}/api/member/dangerTypeQuery"
        payload = {"option":True}
        return self.client.post(url, json=payload)

    def query_system_config(self):
        url = f"{self.endpoint}/api/SysConfig/query"
        payload = {"Category":None}
        return self.client.post(url, json=payload)