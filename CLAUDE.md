# CLAUDE.md

## Language Preference
- Always respond to the user in **Traditional Chinese**.
- All documentation and explanations should be provided in Traditional Chinese.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E2E 自動化測試框架，基於 Pytest + Playwright，支援 UI 自動化與 API 驗證。提供 Web 控制台讓團隊成員透過瀏覽器執行測試、查看 Allure 報告與 Playwright Trace 回放。

## Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install browser drivers
playwright install chromium

# Run tests for specific site and environment
pytest --env=dev --site={site}

# Run UI tests only
pytest -m e2e

# Run API tests only
pytest -m apicheck

# Run specific test file
pytest tests/{site}/test_*.py --env=uat --site={site}
```

### Web Service (Docker)

```bash
# Start web service
docker-compose up -d webservice

# Run CI/CD test task (does not auto-start)
docker-compose run --rm tester

# Access web console
http://localhost:8000

# View Allure reports
http://localhost:8000/allure/

# View Playwright traces
http://localhost:8000/traces/
```

## Architecture

### Multi-Site Structure

The framework supports multiple test targets with isolated Page Object Models:

- **Site-specific POM**: Each site has its own directory under `src/pages/{site}/` containing `base_page.py`, `login_page.py`, `lobby_page.py`, etc.
- **Dynamic import**: `conftest.py` uses `importlib` to dynamically load the correct LoginPage based on `--site` parameter
- **Environment configs**: Site credentials and URLs stored in `env/{env}.ini` files with `[site_name]` sections

### Test Execution Flow

1. **Pytest fixtures** (`tests/conftest.py`):
   - `config`: Reads `env/{env}.ini` based on `--env` and `--site` CLI options
   - `context`: Creates Playwright browser context with tracing enabled
   - `page`: Session-scoped page fixture
   - `e2e_logged_in_page`: Dynamically imports site-specific LoginPage and performs login
   - `api_manager`: Provides authenticated API client for API tests

2. **Trace recording** (`trace_handler` fixture):
   - Automatically starts trace chunk for each test
   - Only saves trace file (to `traces/{timestamp}/{test_name}.zip`) if test fails
   - Uses pytest hook `test_report` to detect test failure in setup/call/teardown phases

3. **Web service** (`webservice/main.py`):
   - FastAPI service with lock manager to prevent concurrent test execution per site
   - Accepts test requests via `/api/tests/regression` endpoint
   - Runs pytest in background task using `TestRunner`
   - Auto-generates Allure HTML report after test completion
   - Mounts static directories: `/allure/`, `/traces/`, `/static/`

### API Testing Architecture

- **APIClient** (`src/apicheck/api_client.py`): Base HTTP client with authentication
- **APIManager** (`src/apicheck/api_manager.py`): Lazy-loads service instances (AdminService, AgentService)
- **Service classes** (`src/services/`): Inherit from `BaseService`, encapsulate API endpoints
- **Fixtures**: `api_client` and `api_manager` fixtures provide authenticated clients to tests

### Key Design Patterns

- **Page Object Model**: All UI interactions encapsulated in page classes under `src/pages/{site}/`
- **Service Layer**: API calls abstracted into service classes under `src/services/`
- **Fixture-based auth**: Login performed once per session via `e2e_logged_in_page` fixture
- **Conditional tracing**: Traces only recorded on failure to save disk space
- **Lock mechanism**: `LockManager` prevents concurrent test runs for same site

## Configuration

### Environment Files (`env/*.ini`)

```ini
[site_name]
base_url = https://example.com
username = test_user
password = test_pass
```

### Pytest Configuration (`pytest.ini`)

- Default options: `-s -ra --html --junitxml --alluredir`
- Markers: `e2e` (UI tests), `apicheck` (API tests)
- Default env: `uat`, default site: `ct`

## Adding New Test Sites

1. Create environment config in `env/*.ini` with `[new_site]` section
2. Create POM directory: `src/pages/new_site/` with `base_page.py`, `login_page.py`, etc.
3. Implement `login()`, `verify_login_success()`, and `get_auth_token()` methods in LoginPage
4. Create test directory: `tests/new_site/` with test files
5. Add site-specific conftest if needed: `tests/new_site/conftest.py`

## Docker Notes

- `webservice` service: Long-running FastAPI server with `restart: always`
- `tester` service: One-shot test runner with `profiles: ["task"]` (manual trigger only)
- Both services use same image: `test-image:latest`
- Volumes mounted: `/app/reports`, `/app/traces` for persistent test artifacts
