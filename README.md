# E2E 自動化測試框架

基於 Pytest + Playwright 的全方位測試解決方案，支援 UI 自動化、API 驗證，並提供 Web 控制台讓團隊成員輕鬆執行測試、查看報告與 Trace。

## 核心功能

- **多站點架構**: 支援多個測試目標，高度擴展性
- **環境隔離**: 環境配置分離
- **Web 控制台**: 團隊成員可透過瀏覽器觸發測試、查看報告、播放 Trace
- **失敗追蹤**: 自動錄製失敗測試的 Playwright Trace，直接線上回放
- **CI/CD 整合**: Docker Compose 支援 GitLab CI 自動化檢測

## 技術棧

| 用途 | 技術 |
|------|------|
| 測試框架 | Pytest |
| UI 自動化 | Playwright |
| API 測試 | Requests |
| 報告生成 | pytest-html, Allure |
| Web 服務 | FastAPI + Uvicorn |
| 容器化 | Docker + Docker Compose |

## 快速開始

### 本地開發

**1. 環境準備**
```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝瀏覽器驅動
playwright install chromium
```

**2. 執行測試**
```bash
# 指定站點與環境
pytest --env=dev --site={site}

# 只跑 UI 測試
pytest -m e2e

# 只跑 API 測試
pytest -m apicheck
```

**3. 查看報告**
```bash
# HTML 報告
open reports/html_report.html

# Allure 報告（需先安裝 Allure）
allure serve reports/allure-results
```

### Web 控制台部署

**啟動 Web 服務**
```bash
# 使用 Docker Compose
docker-compose up -d webservice

# 瀏覽器訪問
http://localhost:8000
```

**功能說明**
- **觸發測試**: 選擇站點、環境、輸入帳密後執行
- **查看報告**: HTML 報告即時生成
- **Trace 回放**: 失敗測試的 Trace 可直接線上播放（無需下載）
- **執行狀態**: 即時顯示測試是否正在執行

### CI/CD 整合

**GitLab CI 範例**
```yaml
test:
  script:
    - docker-compose run --rm tester
  artifacts:
    paths:
      - reports/
    when: always
```

`tester` 服務設定為 `profiles: ["task"]`，不會在 `docker-compose up` 時自動啟動，只在 CI 流程中手動觸發。

## 環境配置

配置檔位於 `env/` 目錄：

```ini
# env/uat.ini
[site1]
base_url = https://uat.example1.com
username = username
password = password

[site2]
base_url = https://uat.example2.com
username = username
password = password
```

## 常見問題

**Q: Trace 在哪裡？**  
只有失敗的測試會生成 Trace，位於 `traces/YYYYMMDD_HHMMSS/` 目錄。

**Q: Web 服務顯示「系統忙碌中」？**  
同一站點同時只能執行一個測試任務，等待當前任務完成即可。

**Q: 如何新增測試站點？**  
1. 在 `env/*.ini` 新增站點配置
2. 在 `src/pages/` 建立站點目錄與 Page Objects
3. 在 `tests/` 建立對應測試案例

**Q: Docker 容器權限問題？**  
檢查 `docker-compose.yml` 中的 `user: "1000:1000"` 是否與宿主機使用者 UID/GID 一致。

## 目錄結構

```
├── env/              # 環境配置（dev.ini, uat.ini）
├── src/
│   ├── pages/        # Page Object Models
│   ├── apicheck/     # API 測試客戶端
│   └── services/     # API 服務封裝
├── tests/            # 測試案例
├── webservice/       # Web 控制台後端
├── reports/          # 測試報告輸出
├── traces/           # 失敗測試 Trace
└── viewer/           # Trace Viewer 靜態檔案
```

更多架構細節與開發指南請參考 [PROJECT.md](PROJECT.md)。

## 授權

本專案為個人學習與作品展示用途，已移除敏感業務邏輯與公司資訊。