def pytest_addoption(parser):
    """
    讀取環境設定黨，全域性的框架設定
    """
    parser.addoption("--env", action="store", default="uat", help="Specify environment: dev or uat")
    parser.addoption("--site", action="store", default="new20", help="Specify site name: new20 or spg")
    parser.addoption("--game", action="store", default="足球", help="下注菜單種類")