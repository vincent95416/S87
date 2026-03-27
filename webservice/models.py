from pydantic import BaseModel, Field
from typing import Optional, Literal
from typing import List

class TestRequest(BaseModel):
    """測試請求參數模型"""
    env: Literal["dev", "uat"] = Field(
        ...,
        description="測試環境"
    )
    site: Literal["new20", "spg"] = Field(
        ...,
        description="測試站點"
    )
    username: Optional[str] = Field(
        None,
        description="自訂帳號 (可選,不填則預設值)"
    )
    password: Optional[str] = Field(
        None,
        description="自訂密碼 (可選,不填預設值)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "env": "dev",
                "site": "new20",
                "username": "custom_user",
                "password": "custom_pass"
            }
        }

class TestResponse(BaseModel):
    """測試任務回應（立即返回）"""
    status: str
    message: str
    site: str
    env: str
    hint: str


class TestResultResponse(BaseModel):
    """測試結果模型"""
    success: bool = Field(
        ...,
        description="測試是否成功"
    )
    exit_code: int = Field(
        ...,
        description="pytest 退出代碼"
    )
    duration: float = Field(
        ...,
        description="執行時間 (秒)"
    )
    summary: dict = Field(
        ...,
        description="測試摘要 (passed/failed/skipped)"
    )
    html_report: Optional[str] = Field(
        None,
        description="HTML 報告檔名"
    )
    allure_report: Optional[str] = Field(
        None,
        description="Allure 報告路徑"
    )
    video_path: Optional[str] = Field(
        None,
        description="測試影片檔名"
    )
    message: str = Field(
        ...,
        description="執行訊息"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "exit_code": 0,
                "duration": 45.32,
                "summary": {
                    "passed": 1,
                    "failed": 0,
                    "skipped": 0
                },
                "html_report": "reports/html_report.html",
                "allure_report": "reports/allure-results",
                "message": "測試執行成功"
            }
        }

class TraceFile(BaseModel):
    name: str
    size: int

class TraceSession(BaseModel):
    session_id: str
    count: int
    traces: List[TraceFile]

class FailedTestAnalysis(BaseModel):
    test_name: str
    root_cause: str
    category: str
    confidence: float
    api_errors: List[dict] = []
    last_screenshot_desc: str = ""
    suggested_action: str
    is_env_issue: bool

class AIAnalysisResult(BaseModel):
    analyzed_at: str
    failed_tests: List[FailedTestAnalysis]
    summary: str