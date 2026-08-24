"""執行 pytest 並在結束後發送 Google Chat 通知。

用法：把原本要傳給 pytest 的參數全數轉發即可，例如
    python scripts/notify.py -m apicheck --color=no

測試選項：
    --dry-run  跳過跑 pytest 與發送 webhook，只讀既有的 JUnit XML 並把
               要送的 JSON payload 印到 stdout；用來檢查訊息格式

環境變數：
    WEBHOOK_URL      Google Chat incoming webhook URL；未設定則跳過發送
    JUNIT_XML_PATH   JUnit XML 路徑，預設 reports/results.xml
    REPORT_BASE_URL  webservice 的對外網址（如 http://host:8000）；
                     設定後訊息會加上「查看完整報告」按鈕，連到
                     ${REPORT_BASE_URL}/static/cicd_report.html
"""
import configparser
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip()
JUNIT_PATH = Path(os.environ.get("JUNIT_XML_PATH", "reports/results.xml"))
REPORT_BASE_URL = os.environ.get("REPORT_BASE_URL", "").strip().rstrip("/")


def parse_junit(path: Path):
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {"parse_error": str(exc)}
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    total = failed = errors = skipped = 0
    duration = 0.0
    failed_cases = []
    for suite in suites:
        total += int(suite.get("tests", 0))
        failed += int(suite.get("failures", 0))
        errors += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
        duration += float(suite.get("time", 0.0))
        for case in suite.findall("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                node = case.find("failure")
                if node is None:
                    node = case.find("error")
                if node is not None:
                    classname = case.get("classname", "")
                    name = case.get("name", "")
                    message = (node.get("message", "") or (node.text or "")).strip()
                    message = " ".join(message.split())
                    props = {}
                    props_node = case.find("properties")
                    if props_node is not None:
                        for prop in props_node.findall("property"):
                            pname = prop.get("name", "")
                            if pname:
                                props[pname] = prop.get("value", "")
                    failed_cases.append({
                        "classname": classname,
                        "name": name,
                        "message": message[:200],
                        "api_call": props.get("api_call"),
                    })

    return {
        "total": total,
        "passed": total - failed - errors - skipped,
        "failed": failed + errors,
        "skipped": skipped,
        "duration": round(duration, 2),
        "failed_cases": failed_cases,
    }


def resolve_env(cli_args):
    """CLI 參數優先，其次讀 pytest.ini 的 addopts 當 fallback。"""
    ini_args = []
    try:
        cp = configparser.ConfigParser()
        cp.read("pytest.ini", encoding="utf-8")
        ini_args = cp.get("pytest", "addopts", fallback="").split()
    except (configparser.Error, OSError, UnicodeDecodeError):
        pass

    env = None
    for token in ini_args + list(cli_args):
        if token.startswith("--env="):
            env = token.split("=", 1)[1]
    return env


def build_payload(stats, exit_code, env):
    if stats is None:
        title = "⚠️ 找不到 JUnit 報告"
        summary = f"pytest exit code: {exit_code}"
    elif stats.get("parse_error"):
        title = "⚠️ JUnit XML 解析失敗"
        summary = f"{stats['parse_error']}\npytest exit code: {exit_code}"
    elif stats["total"] == 0:
        title = "⚠️ 未執行到任何測試"
        summary = f"沒有 test case 被收集到（pytest exit code: {exit_code}）"
    else:
        ok = stats["failed"] == 0 and exit_code == 0
        icon = "✅" if ok else "❌"
        title = f"{icon} 測試{'通過' if ok else '失敗'}"
        d = stats["duration"]
        dur = f"{int(d // 60)}m {int(d % 60)}s" if d >= 60 else f"{d:.1f}s"
        summary = (
            f"✅ {stats['passed']} passed　"
            f"❌ {stats['failed']} failed　"
            f"⚠️ {stats['skipped']} skipped　"
            f"(total {stats['total']}, 耗時 {dur})"
        )
        if not ok and exit_code not in (0, 1):
            summary += f"\npytest exit code: {exit_code}"

    main_widgets = [{"textParagraph": {"text": summary}}]
    if env:
        main_widgets.append({"textParagraph": {"text": f"env=<b>{env}</b>"}})
    if REPORT_BASE_URL:
        url = f"{REPORT_BASE_URL}/static/cicd_report.html"
        main_widgets.append({
            "textParagraph": {"text": f"📊 完整報告（請直接複製網址到瀏覽器）：<br>{url}"}
        })

    sections = [{"widgets": main_widgets}]

    if stats and stats.get("failed_cases"):
        total_failed = len(stats["failed_cases"])
        shown = stats["failed_cases"][:10]
        lines = []
        for i, case in enumerate(shown, 1):
            if case.get("api_call"):
                lines.append(f"{i}. {case['api_call']}")
            else:
                msg = case.get("message") or "(無錯誤訊息)"
                lines.append(f"{i}. {case['classname']}::{case['name']} — {msg[:100]}")
        remaining = total_failed - len(shown)
        if remaining > 0:
            lines.append(f"…及其餘 {remaining} 個")
        sections.append({
            "header": f"失敗清單（{total_failed} 個）",
            "collapsible": True,
            "uncollapsibleWidgetsCount": 0,
            "widgets": [{"textParagraph": {"text": "<br>".join(lines)}}],
        })

    return {
        "cardsV2": [{
            "cardId": "tester-result",
            "card": {
                "header": {"title": title},
                "sections": sections,
            },
        }]
    }


def send_message(payload):
    if not WEBHOOK_URL:
        print("[notify] WEBHOOK_URL 未設定，略過通知", file=sys.stderr)
        return
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()[:500].decode("utf-8", errors="replace")
        print(f"[notify] webhook 拒收 (HTTP {exc.code}): {body}", file=sys.stderr)
    except urllib.error.URLError as exc:
        print(f"[notify] webhook 發送失敗: {exc}", file=sys.stderr)


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    pytest_args = [a for a in args if a != "--dry-run"]

    if dry_run:
        stats = parse_junit(JUNIT_PATH)
        env = resolve_env(pytest_args)
        exit_code = 1 if (stats and stats.get("failed", 0) > 0) else 0
        payload = build_payload(stats, exit_code, env)
        sys.stdout.buffer.write(
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        )
        return

    exit_code = subprocess.call(["pytest", *pytest_args])
    stats = parse_junit(JUNIT_PATH)
    env = resolve_env(pytest_args)
    send_message(build_payload(stats, exit_code, env))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
