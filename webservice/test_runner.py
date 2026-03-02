import logging
import signal
import subprocess
import time
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class TestRunner:
    """pytest 測試執行器"""

    def __init__(
            self,
            test_path: str,
            env: str,
            site: str,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        self.project_root = Path(__file__).resolve().parent.parent
        self.test_path = test_path
        self.env = env
        self.site = site
        self.username = username
        self.password = password

        self.reports_dir = self.project_root / "reports"
        self.xml_report_path = self.reports_dir / "results.xml"
        #其他掛載檔案目錄
        self.html_dir = self.reports_dir / "html_report.html"
        self.allure_dir = self.reports_dir / "allure-results"
        # 時間戳記
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _kill_process(process: subprocess.Popen) -> None:
        try:
            if os.name != 'nt': #linux
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    logger.info(f"已終止{process.pid}")
                except ProcessLookupError:
                    logger.warning(f"{process.pid}已不存在")
            else: #windows做法
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                    logger.info(f"已終止{process.pid}")
                except Exception as e:
                    process.kill()
        except Exception as e:
            logger.error(f"終止process失敗: {e}")

    def _build_command(self) -> list:
        """建立 pytest 指令"""
        cmd = [
            "pytest",
            self.test_path,
            f"--env={self.env}",
            f"--site={self.site}"
        ]
        return cmd

    def run(self) -> Dict:
        """
        執行測試並回傳結果

        Returns:
            dict: 測試結果資訊
        """
        cmd = self._build_command()
        start_time = time.time()

        logger.info(f"開始執行: {' '.join(cmd)}")

        current_env = os.environ.copy()
        if self.username and self.password:
            current_env["TEST_USERNAME"] = self.username
            current_env["TEST_PASSWORD"] = self.password

        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root),
                env=current_env,
                preexec_fn=os.setsid if os.name != 'nt' else None #linux，建立新process組
            )

            try:
                stdout, stderr = process.communicate(timeout=600)
                exit_code = process.returncode
                logger.info(f"測試完成，exit_code={exit_code}")
            except subprocess.TimeoutExpired:
                logger.warning(f"執行超時，開始終止process...")
                self._kill_process(process)
                return self._create_error_response(start_time, "測試執行超時，強制終止進程。")

            # allure generate後的html報表
            allure_html_dir = self.reports_dir / "allure-report-html"

            if self.allure_dir.exists():
                try:
                    gen_cmd = f"allure generate {self.allure_dir} -o {allure_html_dir} --clean"
                    result = subprocess.run(gen_cmd, shell=True, capture_output=True, check=True, cwd=str(self.project_root), text=True)
                    logger.info(f"Allure 報告產生成功")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Allure 產師失敗: {e.stderr}")
                except Exception as e:
                    logger.error(f"Allure 產生失敗: {str(e)}")

            duration = round(time.time() - start_time, 2)
            # 解析測試結果
            summary = self._get_summary_from_xml()

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "duration": duration,
                "summary": summary,
                "html_report": "html_report.html",
                "allure_report": "/allure/index.html",
                "message": "測試完成" if exit_code == 0 else "測試執行失敗",
                "output": (stdout + stderr)[-5000:]
            }

        except Exception as e:
            logger.exception(f"執行時發生異常")
            return self._create_error_response(start_time, f"Runner異常: {str(e)}")

        finally:
            if process and process.poll() is None:
                logger.warning("process未正常結束，強制停止")
                self._kill_process(process)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.error("process無法終止")

    @staticmethod
    def _create_error_response(start_time: float, message: str) -> Dict:
        """統一錯誤回傳格式"""
        return {
            "success": False,
            "exit_code": -1,
            "duration": round(time.time() - start_time, 2),
            "summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
            "message": message,
        }

    def _get_summary_from_xml(self) -> Dict:
        """從 JUnit XML 檔案中提取數據"""
        summary = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
        try:
            if not self.xml_report_path.exists():
                logger.warning(f"XML 報告不存在: {self.xml_report_path}")
                return summary

            tree = ET.parse(self.xml_report_path)
            root = tree.getroot()

            # 處理單個 testsuite 或多個 testsuites
            testsuites = root.findall('.//testsuite')
            if not testsuites:
                # 如果 root 本身就是 testsuite
                testsuites = [root] if root.tag == 'testsuite' else []

            total_tests = 0
            total_failures = 0
            total_errors = 0
            total_skipped = 0

            for testsuite in testsuites:
                total_tests += int(testsuite.get('tests', 0))
                total_failures += int(testsuite.get('failures', 0))
                total_errors += int(testsuite.get('errors', 0))
                total_skipped += int(testsuite.get('skipped', 0))

            # 計算 passed = 總數 - 失敗 - 錯誤 - 跳過
            summary["passed"] = max(0, total_tests - total_failures - total_errors - total_skipped)
            summary["failed"] = total_failures
            summary["errors"] = total_errors
            summary["skipped"] = total_skipped

            logger.info(f"測試摘要: {summary}")
            return summary

        except ET.ParseError as e:
            logger.error(f"XML 報告格式錯誤: {e}")
            return summary
        except Exception as e:
            logger.error(f"解析 XML 報告失敗: {e}")
            return summary