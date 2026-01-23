from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import mimetypes

from .test_runner import TestRunner
from .lock_manager import LockManager
from .models import TestRequest, TestResponse, TestResultResponse, TraceFile, TraceSession


app = FastAPI(
    title="E2E Test Service",
    description="E2E 測試的 Web Service",
    version="1.0.0"
)

# 初始化鎖管理器
lock_manager = LockManager()
# 最新的一次測試
latest_test_result = None

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
TRACE_DIR = BASE_DIR / "traces"
VIEW_DIR = BASE_DIR / "viewer"
REPORTS_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_obj = BASE_DIR / "dashboard.html"
    with open(html_obj, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/status")
def get_status():
    """取得目前執行狀態"""
    return {
        "is_busy": lock_manager.is_locked(),
        "current_test": lock_manager.get_current_test(),
        "latest": latest_test_result
    }

def _execute_flow(request: TestRequest, target_path: str, site_name: str):
    """
    Args:
        request: 來自API的驗證請求
        target_path: 根據專案結構拼接完成的測試檔案路徑
    """
    global latest_test_result
    try:
        runner = TestRunner(
            test_path=target_path,
            env=request.env,
            site=site_name,
            username=request.username,
            password=request.password
        )
        result = runner.run()
        latest_test_result = {
            "site": site_name,
            "env": request.env,
            "result": result
        }
    except Exception as e:
        latest_test_result = {
            "site": site_name,
            "env": request.env,
            "result": {
                "success": False,
                "message": f"測試執行異常: {str(e)}"
            }
        }
    finally:
        lock_manager.release()

@app.post("/api/tests/regression", response_model=TestResponse)
def run_regression_test(request: TestRequest, task: BackgroundTasks):
    """
    測試觸發接口，結合request.site自動對齊POM
    Args:
        request: site, env, username, password
        task: BackgroundTasks 背景任務管理
    """
    global latest_test_result

    if not lock_manager.acquire(request.site):
        raise HTTPException(
            status_code=409,
            detail=f"系統忙碌中：正在執行 {request.site} 測試項目，請稍後再試。"
        )

    try:
        latest_test_result = None   #啟動前重置結果
        test_path = f"tests/{request.site}"
        full_path = BASE_DIR / test_path
        if not full_path.exists() or not full_path.is_dir():
            lock_manager.release()
            raise HTTPException(
                status_code=404,
                detail=f"站點{request.site}中找不到測試檔案"
            )
        task.add_task(_execute_flow, request, test_path, request.site)
        return TestResponse(
            status="accepted",
            message=f"測試任務已啟動：{request.site}",
            site=request.site,
            env=request.env,
            hint="請使用 GET /status 查詢執行狀態"
        )
    except Exception as e:
        lock_manager.release()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(500, str(e))


@app.get("/api/traces/sessions", response_model=List[TraceSession])
def get_sessions():
    """列出traces中所有sessions及其包含的檔案"""
    if not TRACE_DIR.exists():
        return []

    sessions = []
    for session_dir in sorted(TRACE_DIR.iterdir(), key=lambda x: x.name, reverse=True):
        if not session_dir.is_dir():
            continue

        traces = list(session_dir.glob("*.zip"))
        sessions.append(
            TraceSession(
                session_id=session_dir.name,
                count=len(traces),
                traces=[
                    TraceFile(name=t.name ,size=t.stat().st_size
                    )
                    for t in traces
                ]
            )
        )
    return sessions

@app.get("/api/traces/{session_id}/{trace_name}")
def get_trace(session_id: str, trace_name: str) -> FileResponse:
    """
    取得trace檔案供Viewer使用
    """
    if not trace_name.endswith(".zip"):
        trace_name = f"{trace_name}.zip"

    trace_path = TRACE_DIR / session_id / trace_name

    if not trace_path.exists():
        raise HTTPException(status_code=404, detail=f"{trace_name} not found in session {session_id}")
    return FileResponse(trace_path, media_type="application/zip", filename=trace_name)

@app.get("/api/reports/html")
def get_html_report():
    """下載 HTML 報告"""
    file_path = REPORTS_DIR / "html_report.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="報告不存在")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return FileResponse(file_path, headers=headers, media_type="text/html")

@app.get("/api/reports/allure")
def get_allure_report():
    """取得 Allure 報告連結"""
    allure_dir = REPORTS_DIR / "allure-results"
    if not allure_dir.exists():
        raise HTTPException(status_code=404, detail="Allure 報告不存在")

    return {
        "message": "Allure 報告已生成",
        "path": str(allure_dir),
        "hint": "請執行 'allure serve' 查看報告"
    }
# 強制讓系統認識 .zip 格式
mimetypes.add_type('application/zip', '.zip')

app.mount("/static", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/traces", StaticFiles(directory=str(TRACE_DIR)), name="traces")
app.mount("/viewer", StaticFiles(directory=str(VIEW_DIR), html=True), name="viewer")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)