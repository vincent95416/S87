# 專案架構文件

本文件面向開發者，說明框架設計、擴展方式與最佳實踐。

## 核心設計理念

1. **站點隔離**: 每個測試目標（new20/spg/ct）獨立 Page Object 與配置
2. **Fixture 分層**: Session 級別共享登入狀態，Function 級別處理 Trace
3. **失敗即錄**: Trace 只在測試失敗時保存，節省儲存空間
4. **Web 驅動**: FastAPI 提供 RESTful API 觸發測試與查看結果

## 完整目錄結構

```
.
├── conftest.py                   # 註冊命令列參數 (--env, --site, --game)
├── pytest.ini                    # Pytest 配置（markers, default options）
├── requirements.txt              # Python 依賴
├── docker-compose.yml            # Web 服務 + CI Tester 雙角色
├── Dockerfile                    # 容器映像定義
│
├── env/                          # 環境配置
│   ├── dev.ini
│   └── uat.ini
│
├── src/
│   ├── config.py                 # 配置載入邏輯
│   │
│   ├── pages/                    # Page Object Models
│   │   ├── base_page.py         # 全域 BasePage（所有站點共享）
│   │   ├── new20/
│   │   │   ├── base_page.py     # new20 專用 BasePage（繼承全域）
│   │   │   ├── login_page.py
│   │   │   ├── lobby_page.py
│   │   │   └── betting_record_page.py
│   │   └── spg/
│   │       ├── base_page.py
│   │       └── lobby_page.py
│   │
│   ├── apicheck/                 # API 測試模組
│   │   ├── api_client.py        # HTTP 請求封裝
│   │   └── api_manager.py       # 業務邏輯管理（登入、Token 等）
│   │
│   └── services/                 # API 服務層（高階封裝）
│       ├── base_service.py
│       └── admin.py
│
├── tests/
│   ├── conftest.py               # 核心 Fixtures（詳見下節）
│   │
│   ├── new20/
│   │   ├── test_login.py
│   │   └── test_lobby.py
│   │
│   ├── spg/
│   │   ├── conftest.py          # 覆寫 e2e_logged_in_page（spg 登入流程不同）
│   │   └── test_spg_lobby.py
│   │
│   └── apicheck/
│       └── test_admin.py
│
├── webservice/                   # Web 控制台後端
│   ├── main.py                  # FastAPI 應用（API 路由）
│   ├── test_runner.py           # Pytest 執行器封裝
│   ├── lock_manager.py          # 並發鎖管理（防止同時執行）
│   └── models.py                # Pydantic 模型定義
│
├── reports/                      # 測試報告輸出
│   ├── html_report.html
│   └── results.xml
│
├── traces/                       # Playwright Trace 儲存
│   └── YYYYMMDD_HHMMSS/         # 每次測試 Session
│       └── test_*.zip
│
└── viewer/                       # Playwright Trace Viewer 靜態檔案
    └── index.html
```

## Fixture 架構

### Fixture 繼承關係

```
config (session)
    │
    ├─> api_client (session) ──> api_manager (session)
    │
    └─> context (session) ──> page (session)
            │
            └─> e2e_logged_in_page (session)
                    │
                    ├─> e2e_auth_token (session)
                    └─> e2e_main_page (session)
```

### 核心 Fixtures 說明

**1. config** (tests/conftest.py)
- 讀取 `env/{env}.ini` 配置檔
- 依據 `--env` 和 `--site` 參數載入對應配置
- 所有 Fixture 的配置來源

**2. context** (tests/conftest.py)
- Playwright BrowserContext，session 級別
- 啟動 Trace 錄製（screenshots, snapshots, sources）
- 設定 viewport 為 2560x1440

**3. page** (tests/conftest.py)
- 單一 Page 實例，session 級別共享
- 預設 timeout 5000ms
- Trace 錄製已在 context 層啟動，這裡不再處理

**4. trace_handler** (tests/conftest.py)
- Function 級別，autouse=True
- 在每個測試前呼叫 `context.tracing.start_chunk()`
- 測試失敗時儲存 Trace 到 `traces/{timestamp}/{test_name}.zip`
- 測試成功時丟棄 Trace chunk

**5. e2e_logged_in_page** (tests/conftest.py)
- Session 級別，一次性登入
- 動態載入對應站點的 LoginPage（透過 importlib）
- spg 站點在 `tests/spg/conftest.py` 中覆寫此 Fixture

**6. api_client / api_manager** (tests/conftest.py)
- API 測試專用 Fixtures
- `api_client`: 封裝 HTTP 請求（requests）
- `api_manager`: 業務邏輯層（處理登入、Token 管理等）

## 設計模式

### 1. Page Object Model (POM)

**基礎結構**
```python
# src/pages/base_page.py (全域)
class BasePage:
    def __init__(self, page: Page, config):
        self.page = page
        self.config = config
    
    def get_auth_token(self):
        # 從 localStorage 取得 Token
        pass

# src/pages/new20/base_page.py (站點專用)
class BasePage(共用BasePage):
    def __init__(self, page, config):
        super().__init__(page, config)
        self.base_url = config.get('new20', 'base_url')
```

**繼承層級**
```
共用 BasePage
    ├─> new20.BasePage
    │      ├─> LoginPage
    │      ├─> LobbyPage
    │      └─> BettingRecordPage
    │
    └─> spg.BasePage
           └─> LobbyPage
```

### 2. API 測試分層

```
api_client.py (HTTP 層)
    ↓
api_manager.py (業務邏輯層)
    ↓
services/ (高階封裝層，可選)
```

**範例**
```python
# api_client.py
class APIClient:
    def post(self, endpoint, data):
        return requests.post(f"{self.base_url}{endpoint}", json=data)

# api_manager.py
class APIManager:
    def authenticate(self):
        response = self.client.post('/auth/login', {...})
        self.token = response.json()['token']

# tests/apicheck/test_admin.py
def test_login(api_manager):
    api_manager.authenticate()
    assert api_manager.token is not None
```

### 3. Trace 錄製機制

**流程**
1. **Session 開始**: `context.tracing.start()` 啟動全域錄製
2. **每個測試前**: `start_chunk()` 開始新的片段
3. **測試結束**:
   - 失敗 → `stop_chunk(path="...")` 儲存 Trace
   - 成功 → `stop_chunk()` 丟棄片段
4. **Session 結束**: `context.tracing.stop()` 關閉錄製

**Hook 機制**
```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def test_report(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)  # 附加到 request.node
```

透過 `request.node.rep_call.failed` 判斷測試是否失敗。

## Web 服務架構

### API 端點

| 端點 | 方法 | 功能 |
|------|------|------|
| `/` | GET | Dashboard 頁面 |
| `/status` | GET | 取得執行狀態 |
| `/api/tests/regression` | POST | 觸發測試 |
| `/api/traces/sessions` | GET | 列出所有 Trace Sessions |
| `/api/traces/{session}/{name}` | GET | 下載特定 Trace |
| `/api/reports/html` | GET | 取得 HTML 報告 |
| `/viewer/*` | GET | Trace Viewer 靜態檔案 |

### 並發控制

**LockManager** 確保同一站點同時只能執行一個測試：

```python
# webservice/lock_manager.py
class LockManager:
    def acquire(self, site: str) -> bool:
        if self.current_test == site:
            return False
        self.current_test = site
        return True
    
    def release(self):
        self.current_test = None
```

### 背景任務

使用 FastAPI 的 `BackgroundTasks` 執行測試：

```python
@app.post("/api/tests/regression")
def run_test(request: TestRequest, task: BackgroundTasks):
    if not lock_manager.acquire(request.site):
        raise HTTPException(409, "系統忙碌中")
    
    task.add_task(_execute_flow, request, ...)
    return {"status": "accepted"}
```

## Docker 多角色設計

### webservice（常駐）
- 長期運行的 Web 服務
- 提供測試觸發 API 與報告查看
- `restart: always` 確保掛掉自動重啟

### tester（任務）
- 用於 CI/CD 流程
- `profiles: ["task"]` 標記為任務模式
- 執行指令: `docker-compose run --rm tester`

### 共享 Volume
```yaml
volumes:
  - /host/path:/app/reports  # 兩個容器共享同一報告目錄
```

## 擴展指南

### 新增測試站點

**1. 環境配置**
```ini
# env/uat.ini
[new_site]
base_url = https://uat.newsite.com
username = user
password = pass
```

**2. Page Objects**
```
src/pages/new_site/
    ├── base_page.py       # 繼承共用 BasePage
    ├── login_page.py
    └── lobby_page.py
```

**3. 測試案例**
```
tests/new_site/
    ├── conftest.py        # 如需覆寫 Fixture
    └── test_lobby.py
```

**4. 執行**
```bash
pytest --site=new_site
```

### 自訂 Fixture（站點級別）

若某站點登入流程特殊，可在 `tests/{site}/conftest.py` 中覆寫：

```python
# tests/spg/conftest.py
@pytest.fixture(scope="session")
def e2e_logged_in_page(page, config):
    # spg 專屬登入邏輯
    ...
    return lobby_page
```

### 新增 API 測試

**1. 定義 API Client 方法**
```python
# src/apicheck/api_manager.py
def create_user(self, data):
    return self.client.post('/users', data)
```

**2. 編寫測試**
```python
# tests/apicheck/test_users.py
def test_create_user(api_manager):
    response = api_manager.create_user({"name": "Test"})
    assert response['id'] is not None
```

## 最佳實踐

### 1. Page Object 設計
- **單一職責**: 每個 Page 只處理該頁面的元素與操作
- **封裝 Locator**: 不要在測試中直接寫選擇器
- **回傳 Page**: 方法鏈式調用，例如 `login().goto_lobby()`

### 2. Fixture 使用
- **避免過度共享**: 只有真正需要跨測試共享的資源才用 `scope="session"`
- **明確依賴**: Fixture 的依賴關係要清晰，避免循環依賴

### 3. 測試組織
- **按站點分類**: `tests/{site}/` 結構
- **使用 Markers**: `-m e2e` 或 `-m apicheck` 分類執行
- **清晰命名**: `test_login_success`, `test_invalid_credentials`

### 4. Trace 管理
- **定期清理**: Trace 檔案會累積，建議定期刪除舊 Session
- **關鍵測試**: 重要流程測試失敗時優先查看 Trace

### 5. CI/CD 整合
- **獨立報告**: CI 環境的報告路徑與本地分開
- **錯誤通知**: 測試失敗時通知 Slack/Email
- **Artifacts 保存**: 報告與 Trace 作為 GitLab Artifacts 上傳

## 常見問題

**Q: 為什麼 spg 要覆寫 e2e_logged_in_page？**  
A: spg 的登入流程與其他站點不同（可能是 OAuth 或特殊驗證），因此在站點層級覆寫 Fixture。

**Q: Trace 為什麼只錄失敗測試？**  
A: 節省儲存空間。成功測試通常不需回放，失敗測試才需要 Trace 輔助除錯。

**Q: 如何在本地除錯時也保存成功測試的 Trace？**  
A: 修改 `trace_handler` Fixture，移除 `if test_failed` 判斷即可。

**Q: Web 服務的測試執行是同步還是異步？**  
A: 異步。透過 `BackgroundTasks` 在背景執行，API 立即回傳 `accepted` 狀態。

## 技術債務與未來改進

- [ ] 支援並行測試（Pytest-xdist）
- [ ] Trace 自動過期清理機制
- [ ] Web 服務新增測試排程功能
- [ ] 整合 Slack 通知（測試完成/失敗）
- [ ] 支援 Allure Report 在 Web 介面直接查看

---

**維護者**: V
**更新日期**: 2025-01-23