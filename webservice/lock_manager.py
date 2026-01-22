from threading import Lock
from typing import Optional


class LockManager:
    """測試執行鎖管理器 - 確保同時只有一個測試在執行"""

    def __init__(self):
        self._lock = Lock()
        self._current_test: Optional[str] = None
        self._is_locked = False

    def acquire(self, test_name: str) -> bool:
        """
        取得程式鎖

        Args:
            test_name: 測試名稱
        Returns:
            bool: 是否成功取得鎖
        """
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self._current_test = test_name
            self._is_locked = True
        return acquired

    def release(self):
        """釋放程式鎖"""
        if self._is_locked:
            self._current_test = None
            self._is_locked = False
            self._lock.release()

    def is_locked(self) -> bool:
        """檢查是否有測試正在執行"""
        return self._is_locked

    def get_current_test(self) -> Optional[str]:
        """取得目前執行的測試名稱"""
        return self._current_test