"""
敏感詞過濾 Processor

過濾敏感字眼並檢測高風險詞彙。
"""

import logging
from typing import Optional, List
from .base import Processor
from .registry import register

logger = logging.getLogger(__name__)

SENSITIVE_WORDS = ["賭博", "情色"]
RISK_WORDS = ["歧視", "仇恨", "暴力", "未成年", "色情", "赌博", "情色"]


class SensitiveFilterProcessor(Processor):
    """敏感詞過濾 Processor

    注意：此 Processor 會過濾敏感詞並記錄風險警告。
    風險檢測結果透過 logger 輸出。
    """

    processor_name = "sensitive_filter"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        # 敏感詞過濾
        filtered = text
        for word in SENSITIVE_WORDS:
            filtered = filtered.replace(word, "***")

        # 風險檢測
        risks = self._detect_risks(text)
        for risk in risks:
            logger.warning(f"[SensitiveFilter] {risk}")

        return filtered

    @staticmethod
    def _detect_risks(text: str) -> List[str]:
        """檢測高風險字眼"""
        risks = []
        text = text or ""
        text_lower = text.lower()
        for word in RISK_WORDS:
            if word in text_lower:
                risks.append(f"包含可能高風險字眼: {word}")
        return risks


register(SensitiveFilterProcessor)
