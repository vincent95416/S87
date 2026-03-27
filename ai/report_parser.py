import json
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit_failures(xml_path: Path) -> list[dict]:
    """
    解析 JUnit XML，回傳失敗的測試清單。
    每筆格式：{test_name, classname, error_message, stack_trace}
    """
    failures = []
    if not xml_path.exists():
        return failures
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        testcases = root.findall(".//testcase")
        for tc in testcases:
            failure = tc.find("failure")
            if failure is None:
                continue
            failures.append({
                "test_name": tc.get("name", ""),
                "classname": tc.get("classname", ""),
                "error_message": failure.get("message", ""),
                "stack_trace": (failure.text or "").strip(),
            })
    except Exception:
        pass
    return failures


def parse_allure_failures(allure_dir: Path) -> list[dict]:
    """
    掃描 allure-results/*.json，找 status == "failed" 的 result 檔案。
    每筆格式：{test_name, failed_step, duration_ms}
    """
    failures = []
    if not allure_dir.exists():
        return failures
    for json_file in allure_dir.glob("*-result.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status") != "failed":
            continue
        # 找第一個 failed step
        failed_step = _find_failed_step(data.get("steps", []))
        duration_ms = data.get("stop", 0) - data.get("start", 0)
        failures.append({
            "test_name": data.get("name", ""),
            "failed_step": failed_step,
            "duration_ms": duration_ms,
        })
    return failures


def _find_failed_step(steps: list) -> str:
    """遞迴找第一個 failed step 的名稱"""
    for step in steps:
        if step.get("status") == "failed":
            return step.get("name", "")
        nested = _find_failed_step(step.get("steps", []))
        if nested:
            return nested
    return ""
