import pytest
from src.config import Config
from itertools import product

all_history_games = list(product(Config.Testdata.CAT_ID, Config.Testdata.HIS_GTYPE))
all_games = list(product(Config.Testdata.CAT_ID, Config.Testdata.GTYPE))

@pytest.mark.apicheck
def test_menu(api_manager):
    response = api_manager.admin.get_menu()
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id, game_type", all_history_games)
def test_history_games(api_manager, cat_id, game_type):
    response = api_manager.admin.get_games(cat_id, game_type)
    assert response.status_code == 200

@pytest.mark.apicheck
@pytest.mark.parametrize("cat_id, game_type", all_games)
def test_games(api_manager, cat_id, game_type):
    response = api_manager.admin.get_games(cat_id, game_type)
    assert response.status_code == 200