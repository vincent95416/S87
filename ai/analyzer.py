import json
import logging
from datetime import datetime
from pathlib import Path

import anthropic

from ai.report_parser import parse_allure_failures, parse_junit_failures
from ai.trace_parser import extract_api_errors, extract_last_screenshot_b64

logger = logging.getLogger(__name__)

CATEGORIES = ["TIMEOUT", "UI_SELECTOR_CHANGE", "API_ERROR", "ENV_ISSUE", "DATA_ISSUE", "ASSERTION_FAIL", "UNKNOWN"]

SYSTEM_PROMPT = """你是一位資深 QA 自動化工程師，專門分析 E2E 測試失敗原因。
請根據提供的測試資訊（錯誤訊息、截圖、API 錯誤），給出結構化的診斷報告。
必須以 JSON 格式回覆，不要加任何 markdown 包裝。"""


class AIAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze(
        self,
        trace_session_dir: Path | None,
        xml_path: Path,
        allure_dir: Path,
    ) -> dict:
        """
        整合三個資料來源，呼叫 Claude API，回傳結構化診斷結果。
        """
        logger.info(f"🔍 開始 AI 分析: xml={xml_path}, allure={allure_dir}, trace={trace_session_dir}")
        junit_failures = parse_junit_failures(xml_path)
        logger.info(f"從 JUnit XML 解析到 {len(junit_failures)} 個失敗測試")
        allure_failures = parse_allure_failures(allure_dir)
        logger.info(f"從 Allure JSON 解析到 {len(allure_failures)} 個失敗測試")

        # 合併 allure 的 failed_step 資訊到 junit failures
        allure_map = {f["test_name"]: f for f in allure_failures}
        for f in junit_failures:
            allure_info = allure_map.get(f["test_name"], {})
            f["failed_step"] = allure_info.get("failed_step", "")
            f["duration_ms"] = allure_info.get("duration_ms", 0)

        if not junit_failures:
            logger.info("無失敗測試，跳過 AI 分析")
            return {"analyzed_at": datetime.now().isoformat(), "failed_tests": [], "summary": "無失敗測試"}

        logger.info(f"準備分析 {len(junit_failures)} 個失敗測試")
        analyzed = []
        for i, failure in enumerate(junit_failures, 1):
            logger.info(f"分析第 {i}/{len(junit_failures)} 個測試: {failure['test_name']}")
            result = self._analyze_single(failure, trace_session_dir)
            analyzed.append(result)

        summary = self._build_summary(analyzed)
        logger.info(f"✅ AI 分析完成，摘要: {summary}")
        return {
            "analyzed_at": datetime.now().isoformat(),
            "failed_tests": analyzed,
            "summary": summary,
        }

    def _analyze_single(self, failure: dict, trace_session_dir: Path | None) -> dict:
        test_name = failure["test_name"]

        # 嘗試找對應的 trace zip
        api_errors = []
        screenshot_b64 = None
        if trace_session_dir and trace_session_dir.exists():
            zip_path = self._find_trace_zip(trace_session_dir, test_name)
            if zip_path:
                logger.info(f"  找到 trace 檔案: {zip_path.name}")
                api_errors = extract_api_errors(zip_path)
                screenshot_b64 = extract_last_screenshot_b64(zip_path)
                logger.info(f"  提取到 {len(api_errors)} 個 API 錯誤，截圖: {'有' if screenshot_b64 else '無'}")
            else:
                logger.warning(f"  未找到 {test_name} 的 trace 檔案")
        else:
            logger.warning(f"  trace session 目錄不存在: {trace_session_dir}")

        messages = self._build_messages(failure, api_errors, screenshot_b64)
        try:
            logger.info(f"  呼叫 Claude API (model=claude-sonnet-4-6)...")
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            raw = response.content[0].text.strip()
            logger.info(f"  收到 API 回應，長度: {len(raw)} 字元")
            parsed = json.loads(raw)
            parsed["test_name"] = test_name
            parsed["api_errors"] = api_errors
            logger.info(f"  ✅ 分析完成: {parsed.get('category', 'UNKNOWN')}")
            return parsed
        except Exception as e:
            logger.error(f"  ❌ AI 分析 {test_name} 失敗: {e}", exc_info=True)
            return {
                "test_name": test_name,
                "root_cause": failure["error_message"][:200],
                "category": "UNKNOWN",
                "api_errors": api_errors,
                "last_screenshot_desc": "",
                "suggested_action": "請手動查看 trace 和 report",
                "is_env_issue": False,
            }

    def _build_messages(self, failure: dict, api_errors: list, screenshot_b64: str | None) -> list:
        api_errors_text = ""
        if api_errors:
            lines = [f"  - [{e['method']}] {e['url']} → HTTP {e['status']}" for e in api_errors[:10]]
            api_errors_text = "API 錯誤（4xx/5xx）：\n" + "\n".join(lines)
        else:
            api_errors_text = "API 錯誤：無"

        prompt_text = f"""請分析以下 E2E 測試失敗，回傳 JSON 格式診斷報告。

測試名稱：{failure['test_name']}
失敗 Step：{failure.get('failed_step', '未知')}
錯誤訊息：{failure['error_message']}
Stack Trace（節錄）：
{failure['stack_trace'][:800]}

{api_errors_text}

請回傳以下 JSON 格式（不要加 markdown）：
{{
  "root_cause": "一句話說明根本原因",
  "category": "{'/'.join(CATEGORIES)} 其中一個",
  "last_screenshot_desc": "截圖描述（若有提供截圖）",
  "suggested_action": "建議的修復或調查方向",
  "is_env_issue": true/false
}}"""

        content: list = []
        if screenshot_b64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": screenshot_b64,
                },
            })
        content.append({"type": "text", "text": prompt_text})
        return [{"role": "user", "content": content}]

    @staticmethod
    def _find_trace_zip(trace_session_dir: Path, test_name: str) -> Path | None:
        """根據 test_name 找對應的 zip 檔案"""
        candidate = trace_session_dir / f"{test_name}.zip"
        if candidate.exists():
            return candidate
        # 模糊比對（test_name 可能含參數化後綴）
        for p in trace_session_dir.glob("*.zip"):
            if test_name in p.stem:
                return p
        return None

    @staticmethod
    def _build_summary(analyzed: list) -> str:
        total = len(analyzed)
        env_issues = sum(1 for a in analyzed if a.get("is_env_issue"))
        categories = [a.get("category", "UNKNOWN") for a in analyzed]
        cat_str = "、".join(set(categories))
        if env_issues == total:
            return f"{total} 個測試失敗，疑似環境問題（{cat_str}）"
        return f"{total} 個測試失敗，類型：{cat_str}"