E2E/
├── 📄 conftest.py                          # Pytest 全域配置 (註冊 --env, --site 選項)
├── 📄 pytest.ini                           # Pytest 配置檔
├── 📄 PROJECT.md                           
├── 📄 requirements.txt                     # Python 套件依賴
│
├── 📂 env/                                 # 環境配置檔
│   ├── 📄 uat.ini                         # UAT 環境設定
│   ├── 📄 prod.ini                        # Production 環境設定
│   └── 📄 dev.ini                         # Dev 環境設定
│
└── 📂 src/                                 # 原始碼目錄
    │
    ├── 📂 tests/                           # 測試目錄
    │   ├── 📄 conftest.py                 # 測試層級 Fixtures
    │   │
    │   ├── 📂 new20/                      # new20 站點測試
    │   │   ├── 📄 test_login.py
    │   │   ├── 📄 test_lobby.py
    │   │   └── 📄 test_betting.py
    │   │
    │   └── 📂 spg/                        # spg 站點測試
    │       ├── 📄 conftest.py             # spg 專用 Fixtures (覆寫 e2e_logged_in_page)
    │       ├── 📄 test_lobby.py
    │       └── 📄 test_betting.py
    │
    ├── 📂 pages/                           # Page Object Models (POM)
    │   ├── 📄 base_page.py                # 共用基礎 BasePage 類別
    │   │
    │   ├── 📂 new20/                      # new20 站點 Pages
    │   │   ├── 📄 __init__.py
    │   │   ├── 📄 base_page.py            # new20 專用 BasePage (繼承共用 BasePage)
    │   │   ├── 📄 login_page.py           # 登入頁面
    │   │   ├── 📄 lobby_page.py           # 大廳頁面
    │   │   └── 📄 betting_record_page.py  # 投注記錄頁面
    │   │
    │   └── 📂 spg/                        # spg 站點 Pages
    │       ├── 📄 __init__.py
    │       ├── 📄 base_page.py            # spg 專用 BasePage (繼承共用 BasePage)
    │       └── 📄 lobby_page.py           # 大廳頁面
    │
    └── 📂 apicheck/                        # API 測試模組
        ├── 📄 api_client.py               # API 客戶端基礎類別
        └── 📄 api_manager.py              # API 管理器 (認證、請求)