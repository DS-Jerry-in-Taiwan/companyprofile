"""
RetryManager - 重試管理器

控制重試次數、簡化 Prompt 策略、記錄重試原因。
"""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class RetryManager:
    """重試管理器"""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.attempts: List[dict] = []

    def should_retry(self, attempt: int) -> bool:
        """是否應該重試"""
        return attempt < self.max_retries

    def record_attempt(self, attempt: int, issues: List[str], success: bool):
        """記錄一次重試結果"""
        record = {
            "attempt": attempt,
            "issues": issues,
            "success": success,
        }
        self.attempts.append(record)
        logger.info(
            f"重試記錄 [#{attempt}]: {'成功' if success else '失敗'}, "
            f"問題: {issues}"
        )

    def get_retry_prompt_kwargs(self, attempt: int) -> dict:
        """取得重試時使用的簡化版 Prompt 參數

        重試策略：關閉隨機多樣化，用最保守的固定模板
        """
        return {
            "structure_key": "traditional",  # 固定框架
            "opening_key": "industry",       # 固定開頭
            "sentence_key": "service",       # 固定句型
        }

    def get_summary(self) -> dict:
        """取得重試摘要"""
        return {
            "total_attempts": len(self.attempts),
            "max_retries": self.max_retries,
            "history": self.attempts,
        }
