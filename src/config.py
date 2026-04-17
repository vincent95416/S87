from datetime import datetime, timedelta
import random

class Config:

    class Testdata:
        ssapi_url = "https://ssapi.supers168.com"
        ssapi_vendor = "d5235"
        ssapi_sign = "F6D2E6EC20EBFC9EDEB38985462A84FC"
        ssapi_account = "a366"
        ssapi_up_account = "a533"
        ssapi_account = random.randint

        ACQSITE = ["0", "TX", "KU", "CTX", "PIN", "SB", "PM", "DB_ESPORT", "BET365", "188BET", "1XBET"]

        _now = datetime.now()
        _tomorrow = _now + timedelta(days=1)
        ts = _now.timestamp()
        FORMATTED_TIME = _now.strftime("%Y%m%d%H%M%S")
        FORMATTED_DATE = _now.strftime("%Y-%m-%d")
        TOMORROW = _tomorrow.strftime("%Y-%m-%d")

        HIS_GTYPE = [-1, -2, -3, 0, 1, 2, 4, 8, 13, 14, 31, 35] #搶首/尾 單隊總得分 波膽 早餐 單式 滾球 37局 安打總數 優先得分 單節(網) 節(籃球) 下半場
        GTYPE = [-3, -4, -5, -6, -7, 0, 1, 2, 6] #波膽 波膽半 半全場 入球 入球半 早餐 單式 滾球 冠軍
        CAT_ID = [1, 3, 4, 5, 11, 12, 13, 14, 16, 21, 22, 23, 31, 55, 82, 83, 84, 85] #足球 美籃 美棒 美足 台棒 日棒 其他棒球 韓棒 其他籃球 乒乓球 羽毛球 排球 冠軍聯賽 網球 冰球 彩球 指數 電競