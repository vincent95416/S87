import pytest

@pytest.mark.apicheck
def test_front_config(api_manager):
    res_config = api_manager.player.front_config()
    assert res_config.status_code == 200

    string = res_config.text
    res_save = api_manager.player.front_save(string)
    assert res_save.json()["code"] == 200

    res_layout = api_manager.player.front_layout()
    assert res_layout.json()["code"] == 200

@pytest.mark.apicheck
def test_member_info(api_manager):
    res_profile = api_manager.player.member_profile()
    assert res_profile.json()["code"] == 200

    res_cash = api_manager.player.query_cash()
    assert res_cash.json()["code"] == 200

    res_nickname = api_manager.player.query_nickname()
    assert res_nickname.json()["code"] == -107

@pytest.mark.apicheck
def test_menu(api_manager):
    response = api_manager.player.get_menu()
    assert response.json()["code"] == 200

    response_v1 = api_manager.player.get_menu_v1()
    assert response_v1.json()["code"] == 200

@pytest.mark.apicheck
def test_game(api_manager):
    response = api_manager.player.get_game()
    assert response.json()["code"] == 200

    response_v1 = api_manager.player.get_game_v1()
    assert response_v1.json()["code"] == 200

    response_list = api_manager.player.get_list_small(3, 1)
    assert response_list.json()["code"] == 200

@pytest.mark.apicheck
def test_max_win(api_manager):
    response = api_manager.player.get_max_win()
    assert response.json()["code"] == 200

@pytest.mark.apicheck
def test_bet_history(api_manager):
    response = api_manager.player.get_bet_history(False)
    assert response.json()["code"] == 200

    response_set = api_manager.player.get_bet_history(True)
    assert response_set.json()["code"] == 200

@pytest.mark.apicheck
def test_game_result(api_manager):
    response = api_manager.player.get_game_result()
    assert response.json()["code"] == 200

    response_v1 = api_manager.player.get_game_result()
    assert response_v1.json()["code"] == 200

@pytest.mark.apicheck
def test_live_link(api_manager):
    response = api_manager.player.get_live_link()
    assert response.json()["code"] == 200