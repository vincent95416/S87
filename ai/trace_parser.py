import base64
import json
import zipfile
from pathlib import Path


def extract_last_screenshot(zip_path: Path) -> bytes | None:
    """從 trace zip 取最後一張截圖（按時間戳排序）"""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = [
                n for n in zf.namelist()
                if n.startswith("resources/page@") and n.endswith(".jpeg")
            ]
            if not names:
                return None
            # 檔名格式：resources/page@{hash}-{timestamp}.jpeg
            last = max(names, key=lambda n: int(n.rsplit("-", 1)[-1].split(".")[0]))
            return zf.read(last)
    except Exception:
        return None


def extract_last_screenshot_b64(zip_path: Path) -> str | None:
    """回傳 base64 編碼的截圖，供 Claude vision 使用"""
    data = extract_last_screenshot(zip_path)
    if data is None:
        return None
    return base64.standard_b64encode(data).decode("utf-8")


def extract_api_errors(zip_path: Path) -> list[dict]:
    """
    解析 trace.network（NDJSON 格式），回傳 4xx/5xx 的 API 請求。
    每筆格式：{url, method, status}
    """
    errors = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if "trace.network" not in zf.namelist():
                return errors
            raw = zf.read("trace.network").decode("utf-8", errors="replace")
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "resource-snapshot":
                    continue
                snapshot = obj.get("snapshot", {})
                status = snapshot.get("response", {}).get("status", 0)
                if status >= 400:
                    errors.append({
                        "url": snapshot.get("request", {}).get("url", ""),
                        "method": snapshot.get("request", {}).get("method", ""),
                        "status": status,
                    })
    except Exception:
        pass
    return errors