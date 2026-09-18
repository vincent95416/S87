import pytest
from src.config import Config
from itertools import product

all_history_games = list(product(Config.Testdata.CAT_ID, Config.Testdata.HIS_GTYPE))
all_games = list(product(Config.Testdata.CAT_ID, Config.Testdata.GTYPE))
all_tournament = list(product(Config.Testdata.CAT_ID, Config.Testdata.LEAGUE_LEVEL))
all_oddsdefault_match = list(product(Config.Testdata.LEAGUE_LEVEL, Config.Testdata.SITE))

@pytest.mark.apicheck
def test_menu(api_manager):
    response = api_manager.admin.get_menu()
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id, game_type", all_history_games)
def test_history_games(api_manager, cat_id, game_type):
    response = api_manager.admin.get_history(cat_id, game_type)
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id, game_type", all_games)
def test_games(api_manager, cat_id, game_type):
    response = api_manager.admin.get_games(cat_id, game_type)
    assert response.status_code == 200

@pytest.mark.apicheck
def test_reports(api_manager):
    response = api_manager.admin.get_report()
    assert response.status_code == 200

@pytest.mark.apicheck
def test_orders(api_manager):
    response = api_manager.admin.query_order()
    assert response.status_code == 200

@pytest.mark.apicheck
def test_create_game(api_manager):
    response = api_manager.admin.create_game()
    assert response.status_code == 200
    assert response.json().get("result") == 1

@pytest.mark.apicheck
@pytest.mark.parametrize("endpoint, expected", [
    ("event_open",  "全開"),
    ("event_close", "全關"),
    ("event_start", "全收"),
    ("event_stop",  "全停"),
])
def test_contest(api_manager, endpoint, expected):
    event_id = api_manager.admin.query_contest()
    res_event = getattr(api_manager.admin, endpoint)(event_id)
    assert res_event.json().get("info") == expected

    res_margin_close = api_manager.admin.margin_toggle(event_id, 0)
    res_margin_open = api_manager.admin.margin_toggle(event_id, 1)
    assert res_margin_close.json().get("result") == 1
    assert res_margin_open.json().get("result") == 1

    game_id = api_manager.admin.query_game_id(event_id)
    res_adjustment = api_manager.admin.adjustment_odds(event_id, game_id, 1)
    assert res_adjustment.json().get("result") == 1

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id, level", all_tournament)
def test_tournament(api_manager, cat_id, level):
    response = api_manager.admin.query_tournament(cat_id, level)
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id", Config.Testdata.CAT_ID)
def test_teams(api_manager, cat_id):
    response = api_manager.admin.query_teams(cat_id)
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("level, site", all_oddsdefault_match)
def test_odds_default(api_manager, level, site):
    response = api_manager.admin.query_odds_default(level, site)
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("currency, is_currency", [
    ("TWD", True),
    ("USD", True),
    ("VND", True),
    ("TWD", False),
])
def test_currency_page(api_manager, currency, is_currency):
    response = api_manager.admin.query_currency(currency, is_currency)
    assert response.json().get("code") == 1

@pytest.mark.apicheck
@pytest.mark.parametrize(
    "cat_id, level, gametype",
    list(product(Config.Testdata.CAT_ID, Config.Testdata.LEAGUE_LEVEL, [1, 2]))
)
def test_margin_list(api_manager, cat_id, level, gametype):
    response = api_manager.admin.query_margin_list(cat_id, level, gametype)
    assert response.status_code == 200

@pytest.mark.apicheck
def test_light_rules(api_manager):
    response = api_manager.admin.query_light_rules()
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize(
    "member_id, level, locker_type",
    list(zip(Config.Testdata.LOCKER, Config.Testdata.LOCKER_LEVEL, Config.Testdata.LOCKER_TYPE))
)
def test_locker_list(api_manager, member_id, level, locker_type):
    response = api_manager.admin.query_locker(member_id, level)
    assert response.json()["Data"][0]["MemType"] == locker_type

def test_locker_setting(api_manager):
    res_locker = api_manager.admin.query_locker_type()
    res_danger = api_manager.admin.query_danger_type()
    assert res_locker.status_code == 200
    assert res_danger.status_code == 200

def test_system_config(api_manager):
    response = api_manager.admin.query_system_config()
    assert response.status_code == 200
