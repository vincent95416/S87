# 專案架構文件

本文件面向開發者，說明框架設計、擴展方式與最佳實踐。

## 核心設計理念

1. **站點隔離**: 每個 e2e 測試目標（new20/spg）獨立 Page Object 與配置
2. **服務 vs 站點分離**: apicheck 以「後端服務」為單位（admin/agent），不受 e2e `--site` 影響；env ini 檔同時存在 `[new20]`/`[spg]` 等站點 section 與 `[admin]`/`[agent]` 服務 section
3. **Fixture 分層**: Session 級別共享登入狀態，Function 級別處理 Trace
4. **失敗即錄**: Trace 只在測試失敗時保存，節省儲存空間
5. **Web 驅動**: FastAPI 提供 RESTful API 觸發測試與查看結果

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
│   │   └── api_manager.py       # Service Lazy-Build：section → service 映射
│   │
│   └── services/                 # API 服務層（高階封裝）
│       ├── base_service.py
│       ├── admin.py
│       └── agent.py
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
│       ├── test_admin.py
│       └── test_agent.py
│
├── webservice/                   # Web 控制台（後端 + 前端資產）
│   ├── main.py                  # FastAPI 應用（API 路由）
│   ├── test_runner.py           # Pytest 執行器封裝
│   ├── lock_manager.py          # 並發鎖管理（防止同時執行）
│   ├── models.py                # Pydantic 模型定義
│   └── static/                  # 前端資產（透過 /assets 對外服務）
│       ├── dashboard.html       # Web 控制台主頁
│       ├── dashboard.css
│       └── dashboard.js
│
├── reports/                      # 測試報告輸出
│   ├── allure-results/          # Allure JSON 原始資料
│   ├── html_report.html
│   └── results.xml              # JUnit XML 格式
│
└── traces/                       # Playwright Trace 儲存
    └── YYYYMMDD_HHMMSS/         # 每次測試 Session
        └── test_*.zip
```

## 設定與 Conftest 溯源地圖

一支測試跑起來時，設定會從三個來源匯流：**CLI 參數**、**`pytest.ini` addopts**、**`env/*.ini`**；另外 Python 端的常數則走 **`src/config.py`**。Conftest 分成 4 層，職責各異。若一時分不清「這個 fixture / 這個常數是哪來的」，先看這一節。

### 一、Conftest 分佈（共 4 支）

| 檔案 | 行數 | 職責 | 何時載入 | 誰依賴誰 |
|------|------|------|----------|----------|
| `conftest.py`（rootdir） | 7 | **只註冊 CLI 選項**：`pytest_addoption` 加上 `--env`、`--site`、`--game` | pytest 啟動時最先掃 rootdir conftest；`pytest_addoption` 依 pytest 規範只能寫在最上層 conftest | 無依賴，是最上游 |
| `tests/conftest.py` | 181 | **核心層**：<br>• pytest hook `test_report`（把測試結果附加到 request.node）<br>• trace fixture（`trace_handler` autouse、`trace_session_dir`）<br>• 共用 fixture：`config`、`context`、`page`、`e2e_logged_in_page`、`e2e_auth_token`、`e2e_main_page`、`api_manager` | 掃到 `tests/` 底下任一測試時載入 | 讀取 rootdir 註冊的 CLI 選項；讀取 `env/*.ini` |
| `tests/spg/conftest.py` | 48 | **站點層覆寫**：`e2e_logged_in_page`（spg 走 API 拿 RedirectUrl，非表單登入）＋ `e2e_auth_token` | 只在 `tests/spg/` 底下的測試套用 | 依賴 `page`、`config`（由核心層提供） |
| `tests/apicheck/conftest.py` | 8 | **測試類型層**：僅 `reset_agent_client` fixture（清掉 agent client session，讓後續 api_manager 從乾淨狀態重連） | 只在 `tests/apicheck/` 底下的測試套用 | 依賴 `api_manager`（由核心層提供） |

**要點**：
- 根目錄那份 conftest 只做 `pytest_addoption` 這一件事——這是 pytest 規範強制的位置，不能搬進 `tests/conftest.py`。
- 「登入」這件事的入口散在三處：`tests/conftest.py`（通用邏輯 + 動態 import site LoginPage）→ `src/pages/{site}/login_page.py`（實作）→ `tests/spg/conftest.py`（覆寫特例）。

### 二、設定檔分類（共 3 種）

| 檔案 | 內容類型 | 讀取方式 | 主要消費者 |
|------|----------|----------|------------|
| `pytest.ini` | pytest 執行設定 | pytest 自動載入 | pytest CLI 本身。內含 `markers`（`e2e`、`apicheck`）與 `addopts`（預設 `-s -ra --env=uat --site=new20 --html=reports/html_report.html --self-contained-html --junitxml=reports/results.xml --alluredir=reports/allure-results --clean-alluredir`） |
| `env/uat.ini`、`env/dev.ini` | 環境設定：`base_url`、帳密（依 site/service section 分） | `configparser` 讀入，包在 `tests/conftest.py::config` fixture 裡 | 幾乎所有 e2e / apicheck fixture 都間接依賴 |
| `src/config.py` | Python hardcode 常數（`Config.Testdata` class） | 直接 `from src.config import Config` | 測試檔中需要「資料常數」或「共用測試帳號」的地方 |

### 三、env/*.ini 的 section 結構

每份 env ini 混合兩類 section，功能互不相關：

**e2e 用（以「前端站點」為單位，受 `--site` 影響）**
- `[new20]`：`base_url` / `username` / `password`
- `[spg]`：同上
- `env/dev.ini` 目前用 `[2.0]` 作為對應（`[DEFAULT] current_site = 2.0`），是命名歷史遺留

**apicheck 用（以「後端服務」為單位，不受 `--site` 影響）**
- `[admin]`：admin 服務的 `base_url` / `username` / `password`
- `[agent]`：agent 服務的 `base_url` / `username` / `password`

**隱含機關**：`tests/conftest.py:82` 有一行 side-effect：`config_parser['DEFAULT'] = {'site': site}`——把 `--site` 值塞進 `[DEFAULT]` section，讓下游（例如 `tests/spg/conftest.py`）能用 `config.get('DEFAULT', 'site')` 反查目前 site。乍看像多此一舉，實際上是站點 conftest 判斷「這個 fixture 該不該生效」的唯一入口。

### 四、src/config.py 的內容分類

`Config.Testdata` 目前混雜四類資料：

1. **e2e 測試帳號（ag 站專用）**
   - `ag_account`（代理）、`up_account`（總代理）、`transfer_member`（額轉測試帳號）
2. **ssapi 環境 hardcode（uat 專用，跨環境即技術債，見底部技術債清單）**
   - `ssapi_url`、`ssapi_vendor`、`ssapi_sign`、`ssapi_upaccount`
3. **測試資料常數 / 枚舉**
   - `ACQSITE`（來源網站列表）、`GTYPE`（賽事類型代碼）、`HIS_GTYPE`（歷史賽事類型）、`CAT_ID`（運動類別 ID）
4. **模組 import 時計算的時間戳（有副作用）**
   - `_now`、`ts`、`FORMATTED_TIME`、`FORMATTED_DATE`、`TOMORROW`——每次 import 都會重新計算，所以「跑一個測試 session 內 `Config.Testdata.FORMATTED_TIME` 保持不變」是實作巧合、不是保證

### 五、設定流向圖（一個測試跑起來時）

```
pytest CLI                                    src/config.py
    │                                              │
    │ --env=uat --site=new20                       │ 純 hardcode 常數
    ↓                                              │ 測試檔直接 import
conftest.py::pytest_addoption                      │ (Config.Testdata.xxx)
    │                                              │
    │ pytest 解析 & 合併                            │
    ↓                                              │
pytest.ini::addopts (補上預設值)                    │
    │                                              │
    ↓                                              │
tests/conftest.py::config fixture                  │
    │ configparser.read(env/{env}.ini)             │
    │ config_parser['DEFAULT'] = {'site': site}    │
    ↓                                              │
下游 fixture:                                       │
  • api_manager       ── 讀 [admin]、[agent]       │
  • e2e_logged_in_page ── site 決定 import 誰      │
  • e2e_auth_token                                  │
    │                                              │
    ↓                                              ↓
                    測試 function
       (fixture 注入 + Config.Testdata 常數)
```

### 六、常見「這個東西哪來的？」對照表

| 你看到 | 它其實是 | 定義在 |
|--------|----------|--------|
| `def test_x(config)` 參數 | ConfigParser 物件（環境設定） | `tests/conftest.py:63` |
| `from src.config import Config` | Python hardcode 常數 class | `src/config.py:4` |
| `config.get('DEFAULT', 'site')` | 從 `--site` CLI 反查目前站點 | `tests/conftest.py:82` 手動塞進 `[DEFAULT]` |
| `config.get('new20', 'base_url')` | env/{env}.ini 的 `[new20]` section | `env/uat.ini`、`env/dev.ini` |
| `config.get('admin', 'base_url')` | env/{env}.ini 的 `[admin]` section | 同上 |
| `--env`、`--site`、`--game` | pytest CLI 選項 | `conftest.py`（rootdir） |
| `-m e2e` / `-m apicheck` | pytest marker | `pytest.ini` |
| `--html=... --alluredir=...` 預設值 | pytest addopts | `pytest.ini` |
| `Config.Testdata.ACQSITE` | 純資料常數 | `src/config.py:17` |
| `Config.Testdata.ssapi_*` | uat 環境 hardcode（技術債） | `src/config.py:12-15` |

## Fixture 架構

### Fixture 繼承關係

```
config (session)
    │
    ├─> api_manager (session)   # 內部 lazy-build AdminService / AgentService
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
- 預設 headless=True, slow_mo=100

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

**6. api_manager** (tests/conftest.py)
- API 測試專用 Fixture，直接傳入整個 `config` 物件
- APIManager 內部 lazy-build `.admin` / `.agent`，各自從 ini 的 `[admin]`、`[agent]` section 讀 `base_url` 和帳密
- **不受 `--site` 影響**：apicheck 跟 e2e 的「站點」概念解耦

## 設計模式

### 1. Page Object Model (POM)

**基礎結構**
```python
# src/pages/base_page.py (全域)
from playwright.sync_api import Page

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def get_auth_token(self):
        # 從 localStorage 取得 Token
        pass

# src/pages/new20/base_page.py (站點專用)
from src.pages.base_page import BasePage

class BasePage(BasePage):  # 繼承全域 BasePage
    def __init__(self, page):
        super().__init__(page)

# src/pages/new20/login_page.py
from src.pages.new20.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: Page, config):
        super().__init__(page)
        self.url = config.get('new20', 'base_url')

    def login(self, username, password):
        self.navigate(self.url)
        self.fill_username(username)
        self.fill_password(password)
        self.click_login_button()
```

**繼承層級**
```
src/pages/base_page.py (全域 BasePage)
    ├─> src/pages/new20/base_page.py (new20.BasePage)
    │      ├─> LoginPage
    │      ├─> LobbyPage
    │      └─> BettingRecordPage
    │
    └─> src/pages/spg/base_page.py (spg.BasePage)
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
# src/apicheck/api_client.py
class APIClient:
    def __init__(self, base_url, auth_strategy, credentials):
        self.base_url = base_url
        self.session = requests.Session()

    def authenticate(self):
        return self.auth_strategy.authenticate(self.session, self.base_url, self.credentials)

    def post(self, url, **kwargs):
        return self.session.post(url, **kwargs, verify=False)

# src/apicheck/api_manager.py
class APIManager:
    """每個 service 從 config 對應 section 各自讀 base_url 和帳密"""
    def __init__(self, config):
        self.config = config
        self._admin = None
        self._agent = None

    def _build_service(self, service_class, section):
        base_url = self.config.get(section, "base_url")
        credentials = {
            "username": self.config.get(section, "username"),
            "password": self.config.get(section, "password"),
        }
        strategy = service_class.auth_strategy_class()
        client = APIClient(base_url, strategy, credentials)
        client.authenticate()
        return service_class(client, base_url)

    @property
    def admin(self):
        if self._admin is None:
            self._admin = self._build_service(AdminService, "admin")
        return self._admin

# tests/apicheck/test_admin.py
def test_menu(api_manager):
    response = api_manager.admin.get_menu()  # 第一次存取才登入 + 建 client
    assert response.status_code == 200
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
| `/api/reports/allure` | GET | 取得 Allure 報告連結 |
| `/static/*` | GET | 靜態檔案（reports 目錄） |
| `/assets/*` | GET | 前端資產（`webservice/static/` 目錄） |
| `/traces/*` | GET | Trace 檔案靜態存取 |
| `/allure/*` | GET | Allure 報告靜態檔案 |

### 並發控制

**LockManager** 確保同時只能執行一個測試：

```python
# webservice/lock_manager.py
class LockManager:
    def __init__(self):
        self._lock = Lock()
        self._current_test: Optional[str] = None
        self._is_locked = False

    def acquire(self, test_name: str) -> bool:
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self._current_test = test_name
            self._is_locked = True
        return acquired

    def release(self):
        if self._is_locked:
            self._current_test = None
            self._is_locked = False
            self._lock.release()
```

### 背景任務

使用 FastAPI 的 `BackgroundTasks` 執行測試：

```python
# webservice/main.py
@app.post("/api/tests/regression")
async def run_regression_test(request: TestRequest, background_tasks: BackgroundTasks):
    if lock_manager.is_locked():
        raise HTTPException(status_code=409, detail="測試正在執行中")

    if not lock_manager.acquire(request.site):
        raise HTTPException(status_code=409, detail="無法取得執行鎖")

    background_tasks.add_task(_execute_flow, request, target_path, site_name)
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
def e2e_logged_in_page(page: Page, config):
    """demo_site 專用登入流程：透過 API 取得 RedirectUrl"""
    site = config.get('DEFAULT', 'site')
    base_url = config.get(site, 'base_url')

    # 呼叫 API 取得登入 URL
    url = f'api.url'
    payload = f'payload'
    response = requests.post(url=url, data=payload)
    redirect_url = response.json()['Data']['RedirectUrl']

    # 導航到登入後頁面
    page.goto(redirect_url)
    lobby_page = LobbyPage(page, config)
    return lobby_page
```

### 新增 API 測試

API 測試走「APIManager → service (admin/agent) → 方法」三層。要新增一支 API：

**1. 在對應 service 加方法**
```python
# src/services/agent.py
class AgentService(BaseService):
    def create_user(self, data):
        url = f"{self.endpoint}/users"
        return self.client.post(url, data=data)
```

若要新增整個服務（例如 `report`），步驟為：
- `src/services/report.py` 繼承 `BaseService`，並指定 `auth_strategy_class`
- `src/apicheck/api_manager.py` 加上 `report` property，呼叫 `_build_service(ReportService, "report")`
- `env/{env}.ini` 補上 `[report]` section（base_url / username / password）

**2. 編寫測試**
```python
# tests/apicheck/test_agent.py
@pytest.mark.apicheck
def test_create_user(api_manager):
    response = api_manager.agent.create_user({"name": "Test"})
    assert response.status_code == 200
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
- **Artifacts 保存**: 報告與 Trace 作為 CI Artifacts 上傳

## 常見問題

**Q: 為什麼 spg 要覆寫 e2e_logged_in_page？**  
A: spg 的登入流程與其他站點不同（可能是 OAuth 或特殊驗證），因此在站點層級覆寫 Fixture。

**Q: Trace 為什麼只錄失敗測試？**  
A: 節省儲存空間。成功測試通常不需回放，失敗測試才需要 Trace 輔助除錯。

**Q: 如何在本地除錯時也保存成功測試的 Trace？**  
A: 修改 `trace_handler` Fixture，移除 `if test_failed` 判斷即可。

**Q: Web 服務的測試執行是同步還是異步？**
A: 異步。透過 `BackgroundTasks` 在背景執行，API 立即回傳 `accepted` 狀態。

**Q: 為什麼 apicheck 不受 `--site` 影響？**
A: apicheck 測的是「後端服務」（admin、agent），不是「前端站點」。`api_manager` fixture 直接吃整個 config，admin/agent 各自從 ini 的 `[admin]`、`[agent]` section 讀 base_url 和帳密。`--site` 只用於 e2e 站點切換。

**Q: 在新環境（例如 dev）跑 apicheck 失敗、噴 `NoOptionError` 怎麼辦？**
A: 那個 env 的 ini 檔還沒填 `[admin]` / `[agent]` section 的內容。補上 base_url、username、password 就好。

## 技術債務與未來改進

- [ ] 支援並行測試（Pytest-xdist）
- [ ] Trace 自動過期清理機制
- [ ] Web 服務新增測試排程功能
- [ ] 整合 Slack 通知（測試完成/失敗）
- [ ] 支援 Allure Report 在 Web 介面直接查看
- [ ] `src/pages/new20/betting_record_page.py:57` 硬寫死 `https://ag.supers168.com/Home/Authenticate`，應改為從 `base_url` 組合
- [ ] `src/config.py` 的 `Config.Testdata.ssapi_*` 為 uat 專用 hardcode，跨環境跑 ssapi 測試前需搬進 `env/*.ini`

---

**維護者**: V
**更新日期**: 2026-06-15