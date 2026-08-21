"""執行 pytest 並在結束後發送 Google Chat 通知。

用法：把原本要傳給 pytest 的參數全數轉發即可，例如
    python scripts/notify.py -m apicheck --color=no

測試選項：
    --dry-run  跳過跑 pytest 與發送 webhook，只讀既有的 JUnit XML 並把
               要送的 JSON payload 印到 stdout；用來檢查訊息格式

環境變數：
    WEBHOOK_URL      Google Chat incoming webhook URL；未設定則跳過發送
    JUNIT_XML_PATH   JUnit XML 路徑，預設 reports/results.xml
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


def parse_junit(path: Path):
    if not path.exists():
        return None
    root = ET.parse(path).getroot()
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
                    failed_cases.append({
                        "classname": classname,
                        "name": name,
                        "message": message[:200]
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
        title = "⚠️ 測試執行完成（找不到 JUnit 報告）"
        summary = f"pytest exit code: {exit_code}"
    elif stats["total"] == 0:
        title = "⚠️ 未執行到任何測試"
        summary = f"沒有 test case 被收集到（pytest exit code: {exit_code}）"
    else:
        ok = stats["failed"] == 0 and exit_code == 0
        icon = "✅" if ok else "❌"
        title = f"{icon} 測試{'通過' if ok else '失敗'}"
        summary = (
            f"✅ {stats['passed']} passed　"
            f"❌ {stats['failed']} failed　"
            f"⚠️ {stats['skipped']} skipped　"
            f"(total {stats['total']})"
        )
        if not ok and exit_code not in (0, 1):
            summary += f"\npytest exit code: {exit_code}"

    widgets = [{"textParagraph": {"text": summary}}]

    tags = []
    if env:
        tags.append(f"env=<b>{env}</b>")
    if tags:
        widgets.append({"textParagraph": {"text": "　".join(tags)}})

    if stats and stats["failed_cases"]:
        shown = stats["failed_cases"][:10]
        body = "\n".join(f"• {case['classname']}::{case['name']} — {case['message'] or '(無錯誤訊息)'}" for case in shown)
        remaining = len(stats["failed_cases"]) - len(shown)
        if remaining > 0:
            body += f"\n…及其餘 {remaining} 個"
        widgets.append({
            "decoratedText": {
                "topLabel": "失敗清單",
                "text": body,
                "wrapText": True,
            }
        })

    return {
        "cardsV2": [{
            "cardId": "tester-result",
            "card": {
                "header": {"title": title},
                "sections": [{"widgets": widgets}],
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
    except urllib.error.URLError as exc:
        print(f"[notify] webhook 發送失敗: {exc}", file=sys.stderr)


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    pytest_args = [a for a in args if a != "--dry-run"]

    if dry_run:
        stats = parse_junit(JUNIT_PATH)
        env = resolve_env(pytest_args)
        exit_code = 1 if (stats and stats["failed"] > 0) else 0
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
