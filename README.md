# E2E 自動化測試框架

基於 Pytest + Playwright 的測試解決方案，支援 UI 自動化、API 驗證，並提供 Web 控制台執行測試與查看報告。

## 核心功能

- **多站點架構**: 支援多個測試目標，獨立 Page Object Models
- **服務/站點分離**: apicheck 以「後端服務」（admin、agent）為單位，與 e2e 的「前端站點」（new20、spg）解耦
- **Web 控制台**: 透過瀏覽器觸發測試、查看 Allure 報告、播放 Trace
- **失敗追蹤**: 自動錄製失敗測試的 Playwright Trace
- **CI/CD 整合**: Docker Compose 支援自動化流程

## 技術棧

| 用途 | 技術 |
|------|------|
| 測試框架 | Pytest |
| UI 自動化 | Playwright |
| API 測試 | Requests |
| 報告生成 | Allure |
| Web 服務 | FastAPI |
| 容器化 | Docker + Docker Compose |

## 快速開始

### 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt
playwright install chromium

# 執行測試
pytest --env=dev --site={site}

# 只跑 UI 測試
pytest -m e2e

# 只跑 API 測試
pytest -m apicheck
```

### Web 控制台部署

```bash
# Build 並啟動服務
docker-compose build
docker-compose up -d webservice

# 訪問控制台
http://localhost:8000
```

**功能**
- 選擇站點、環境執行測試
- 查看 Allure 報告：`/allure/`
- 播放 Trace：`/traces/`

### CI/CD 整合

```yaml
# GitLab CI 範例
test:
  script:
    - docker-compose run --rm tester
  artifacts:
    paths:
      - reports/
    when: always
```

## 環境配置

配置檔位於 `env/` 目錄：

```ini
# env/uat.ini
[site_name]
base_url = https://example.com
username = test_user
password = test_pass
```

## 目錄結構

```
├── env/              # 環境配置
├── src/
│   ├── pages/        # Page Object Models
│   ├── apicheck/     # API 測試客戶端
│   └── services/     # API 服務封裝
├── tests/            # 測試案例
├── webservice/       # Web 控制台後端
├── reports/          # 測試報告輸出
└── traces/           # 失敗測試 Trace
```

更多架構細節與開發指南請參考 [PROJECT.md](PROJECT.md)。

## 授權

本專案為個人學習與作品展示用途。