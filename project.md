project/
├── conftest.py                     # 全域 fixtures & pytest hooks
├── pytest.ini                      # pytest 配置檔
├── env/                         # 網站與環境組態檔
│   ├── dev.ini
│   └── prod.ini
│
├── tests/
│   ├── site_a/                     # A 網站的測試用例
│   │   ├── test_login.py
│   │   └── conftest.py             # A 網站專屬的 fixtures
│   │
│   ├── site_b/                     # B 網站的測試用例
│   │   ├── test_checkout.py
│   │   └── conftest.py             # B 網站專屬的 fixtures
│   │
│   └── __init__.py
│
├── pages/
│   ├── base_page.py
│   ├── site_a_login_page.py        # 專屬 A 網站的頁面物件
│   ├── site_b_checkout_page.py     # 專屬 B 網站的頁面物件
│   └── ...
│
└── utils/                          # 讀取組態檔的工具 (尚未開發)
    ├── helpers.py
    ├── config_reader.py
    └── ...